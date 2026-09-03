"""
Business logic for thermal-event queries.

Translates repository data into the Pydantic schemas expected by
the route layer.
"""

from typing import Optional

from app.repositories.event_repository import EventRepository
from app.schemas.events import (
    EventDetail,
    EventFeature,
    EventFeatureCollection,
    EventGeometry,
    EventLocation,
    EventPriority,
    EventProperties,
    EventTemporal,
    EventThermal,
    IndustrialContext,
)


class EventService:
    """Transforms raw event data into API response models."""

    def __init__(self, event_repo: EventRepository) -> None:
        self._repo = event_repo

    async def get_events(
        self,
        *,
        run_id: Optional[str] = None,
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        min_confidence: Optional[float] = None,
    ) -> EventFeatureCollection:
        """
        Fetch filtered events and return a GeoJSON FeatureCollection.
        """
        rows = await self._repo.get_events(
            run_id=run_id,
            classification=classification,
            risk_level=risk_level,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
        )

        features = [
            EventFeature(
                geometry=EventGeometry(
                    coordinates=[row["longitude"], row["latitude"]],
                ),
                properties=EventProperties(
                    event_id=row["event_id"],
                    classification=row.get("classification"),
                    confidence=row.get("confidence"),
                    active_days=row.get("active_days"),
                    detection_count=row.get("detection_count"),
                    priority_score=row.get("priority_score"),
                    risk_level=row.get("risk_level"),
                ),
            )
            for row in rows
        ]

        return EventFeatureCollection(features=features)

    async def get_event_detail(self, event_id: str) -> Optional[EventDetail]:
        """
        Fetch full detail for one event.  Returns ``None`` when the
        event does not exist (the route layer maps this to 404).
        """
        row = await self._repo.get_event_by_id(event_id)
        if row is None:
            return None

        return EventDetail(
            event_id=row["event_id"],
            classification=row.get("classification"),
            confidence=row.get("confidence"),
            location=EventLocation(
                latitude=row["latitude"],
                longitude=row["longitude"],
            ),
            temporal=EventTemporal(
                first_detected=row.get("first_detected"),
                last_detected=row.get("last_detected"),
                active_days=row.get("active_days"),
                duration_days=row.get("duration_days"),
                detection_count=row.get("detection_count"),
            ),
            thermal=EventThermal(
                mean_frp=row.get("mean_frp"),
                max_frp=row.get("max_frp"),
                mean_brightness=row.get("mean_brightness"),
            ),
            industrial_context=IndustrialContext(
                nearest_facility=row.get("nearest_facility"),
                facility_type=row.get("facility_type"),
                distance_m=row.get("distance_m"),
            ),
            priority=EventPriority(
                score=row.get("priority_score"),
                risk_level=row.get("risk_level"),
            ),
        )
