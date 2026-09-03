"""
Data-access abstraction for thermal events.

Currently returns empty results because there is no database yet.
Replace the method bodies with real DB queries (e.g. PostGIS) when the
database layer is integrated.
"""

from typing import Any, Dict, List, Optional


class EventRepository:
    """
    Thin data-access layer for thermal events.

    Every public method returns plain dicts (or None) so the service
    layer can map them to Pydantic schemas.  When a real database is
    added, swap the implementations here — no route changes required.
    """

    # TODO: Replace with actual database connection / session.

    async def get_events(
        self,
        *,
        run_id: Optional[str] = None,
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Return a list of event dicts matching the given filters.

        Each dict should contain at minimum:
            event_id, latitude, longitude, classification, confidence,
            active_days, detection_count, priority_score, risk_level

        Currently returns an empty list (no database).
        """
        # TODO: query the database with filters
        return []

    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        """
        Return a single event dict or None if not found.

        The dict should contain all detail fields:
            event_id, classification, confidence, latitude, longitude,
            first_detected, last_detected, active_days, duration_days,
            detection_count, mean_frp, max_frp, mean_brightness,
            nearest_facility, facility_type, distance_m,
            priority_score, risk_level

        Currently returns None (no database).
        """
        # TODO: query the database by event_id
        return None

    async def get_summary_stats(self) -> Dict[str, Any]:
        """
        Return aggregate statistics for the dashboard.

        Expected keys:
            total_detections, total_events, industrial_events,
            non_industrial_events, uncertain_events, high_risk_events,
            average_confidence

        Currently returns zeros (no database).
        """
        # TODO: aggregate query on the database
        return {
            "total_detections": 0,
            "total_events": 0,
            "industrial_events": 0,
            "non_industrial_events": 0,
            "uncertain_events": 0,
            "high_risk_events": 0,
            "average_confidence": 0.0,
        }
