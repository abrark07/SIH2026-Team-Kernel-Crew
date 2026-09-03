"""
NASA FIRMS API communication service.

Responsibilities:
    • Build FIRMS API URLs
    • Handle the 5-day query limitation by splitting date ranges
    • Execute HTTP requests (via httpx)
    • Return raw detection data to the caller

The FIRMS MAP_KEY is read from Settings and is NEVER exposed
in any response or log output.
"""

import logging
from datetime import date, timedelta
from typing import Any, Dict, List

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# FIRMS limits area-queries to at most 5 days per request.
_MAX_DAYS_PER_REQUEST = 5


class FirmsServiceError(Exception):
    """Raised when the FIRMS API returns an unexpected response."""


class FirmsService:
    """Thin wrapper around the NASA FIRMS REST API."""

    def __init__(self) -> None:
        self._settings = get_settings()

    # ── public ──────────────────────────────────────────────────

    async def fetch_firms_data(
        self,
        bbox: List[float],
        start_date: date,
        end_date: date,
    ) -> List[Dict[str, Any]]:
        """
        Fetch FIRMS thermal detections for *bbox* between *start_date*
        and *end_date* (inclusive).

        Automatically splits the request into ≤5-day windows to comply
        with the FIRMS API limitation.

        Returns a list of raw detection dicts (one per hotspot row).
        Raises ``FirmsServiceError`` on API / network failures.
        """
        if not self._settings.FIRMS_MAP_KEY:
            raise FirmsServiceError(
                "FIRMS_MAP_KEY is not configured. "
                "Set the FIRMS_MAP_KEY environment variable."
            )

        windows = self._split_date_range(start_date, end_date)
        all_detections: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(
            timeout=self._settings.FIRMS_TIMEOUT_SECONDS,
        ) as client:
            for window_start, window_end in windows:
                detections = await self._fetch_window(
                    client, bbox, window_start, window_end,
                )
                all_detections.extend(detections)

        logger.info(
            "FIRMS fetch complete: %d detections for bbox=%s, %s→%s",
            len(all_detections), bbox, start_date, end_date,
        )
        return all_detections

    # ── internals ───────────────────────────────────────────────

    async def _fetch_window(
        self,
        client: httpx.AsyncClient,
        bbox: List[float],
        window_start: date,
        window_end: date,
    ) -> List[Dict[str, Any]]:
        """Fetch a single ≤5-day window from the FIRMS API."""
        day_range = (window_end - window_start).days + 1
        west, south, east, north = bbox
        area_str = f"{west},{south},{east},{north}"

        url = (
            f"{self._settings.FIRMS_BASE_URL}/api/area/csv/"
            f"{self._settings.FIRMS_MAP_KEY}/"
            f"{self._settings.FIRMS_SOURCE}/"
            f"{area_str}/{day_range}/{window_start.isoformat()}"
        )

        logger.info(
            "FIRMS request: source=%s, bbox=%s, days=%d, start=%s",
            self._settings.FIRMS_SOURCE, area_str, day_range, window_start,
        )

        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise FirmsServiceError(
                f"FIRMS API timed out for window {window_start}→{window_end}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise FirmsServiceError(
                f"FIRMS API returned {exc.response.status_code} "
                f"for window {window_start}→{window_end}"
            ) from exc
        except httpx.HTTPError as exc:
            raise FirmsServiceError(
                f"FIRMS API request failed for window {window_start}→{window_end}"
            ) from exc

        # FIRMS sometimes returns error text with HTTP 200
        body = response.text.strip()
        if not body:
            return []
        first_line_lower = body.splitlines()[0].lower()
        if any(kw in first_line_lower for kw in ("error", "invalid", "unauthorized")):
            raise FirmsServiceError(
                f"FIRMS API returned an error for window "
                f"{window_start}→{window_end}: {body[:200]}"
            )

        return self._parse_csv(response.text)

    @staticmethod
    def _split_date_range(
        start: date, end: date,
    ) -> List[tuple]:
        """
        Split [start, end] into windows of at most
        ``_MAX_DAYS_PER_REQUEST`` days.

        Returns list of (window_start, window_end) tuples.
        """
        windows = []
        current = start
        while current <= end:
            window_end = min(current + timedelta(days=_MAX_DAYS_PER_REQUEST - 1), end)
            windows.append((current, window_end))
            current = window_end + timedelta(days=1)
        return windows

    @staticmethod
    def _parse_csv(csv_text: str) -> List[Dict[str, Any]]:
        """
        Parse the CSV text returned by FIRMS into a list of dicts.

        Each row becomes a dict keyed by the CSV header columns.
        """
        lines = csv_text.strip().splitlines()
        if len(lines) < 2:
            return []

        headers = [h.strip() for h in lines[0].split(",")]
        results: List[Dict[str, Any]] = []
        for line in lines[1:]:
            values = [v.strip() for v in line.split(",")]
            if len(values) == len(headers):
                results.append(dict(zip(headers, values)))
        return results
