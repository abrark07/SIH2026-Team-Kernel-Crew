"""
EventService — maps normalized repository rows to API Pydantic schemas.

All field mappings here are driven by the frozen ML contract.
No values are invented.
"""

from typing import Optional

from app.repositories.event_repository import EventRepository
from app.schemas.events import (
    EventDetail,
    EventFeature,
    EventFeatureCollection,
    EventGeometry,
    EventProperties,
    EventTemporal,
    EventThermal,
    OSMContext,
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
        """Fetch filtered events and return a GeoJSON FeatureCollection."""
        rows = await self._repo.get_events(
            run_id=run_id,
            classification=classification,
            risk_level=risk_level,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
        )

        features = []
        for row in rows:
            lat = row.get("latitude")
            lon = row.get("longitude")
            if lat is None or lon is None:
                continue
            features.append(
                EventFeature(
                    geometry=EventGeometry(coordinates=[lon, lat]),
                    properties=EventProperties(
                        event_id=row["event_id"],
                        classification=row.get("classification"),
                        behavior_type=row.get("behavior_type"),
                        behavior_cluster=row.get("behavior_cluster"),
                        active_days=row.get("active_days"),
                        duration_days=row.get("duration_days"),
                        detection_count=row.get("detection_count"),
                        activity_frequency=row.get("activity_frequency"),
                        mean_frp=row.get("mean_frp"),
                        max_frp=row.get("max_frp"),
                        mean_bright_ti4=row.get("mean_bright_ti4"),
                        max_bright_ti4=row.get("max_bright_ti4"),
                        spatial_diameter_km=row.get("spatial_diameter_km"),
                        nearest_industrial_zone_km=row.get("nearest_industrial_zone_km"),
                        nearest_factory_km=row.get("nearest_factory_km"),
                        nearest_works_km=row.get("nearest_works_km"),
                        nearest_mine_km=row.get("nearest_mine_km"),
                        nearest_brick_km=row.get("nearest_brick_km"),
                        nearest_depot_km=row.get("nearest_depot_km"),
                        nearest_power_km=row.get("nearest_power_km"),
                        nearest_other_industry_km=row.get("nearest_other_industry_km"),
                        osm_industrial_evidence=row.get("osm_industrial_evidence"),
                    ),
                )
            )

        return EventFeatureCollection(features=features)

    async def get_event_detail(self, event_id: str) -> Optional[EventDetail]:
        """Fetch full detail for one event. Returns None when not found."""
        row = await self._repo.get_event_by_id(event_id)
        if row is None:
            return None

        lat = row.get("latitude")
        lon = row.get("longitude")

        return EventDetail(
            event_id=row["event_id"],
            classification=row.get("classification"),
            behavior_type=row.get("behavior_type"),
            behavior_cluster=row.get("behavior_cluster"),
            location={"latitude": lat, "longitude": lon},
            temporal=EventTemporal(
                start_date=row.get("start_date"),
                end_date=row.get("end_date"),
                active_days=row.get("active_days"),
                duration_days=row.get("duration_days"),
                detection_count=row.get("detection_count"),
                activity_frequency=row.get("activity_frequency"),
                detections_per_active_day=row.get("detections_per_active_day"),
            ),
            thermal=EventThermal(
                mean_frp=row.get("mean_frp"),
                max_frp=row.get("max_frp"),
                std_frp=row.get("std_frp"),
                mean_bright_ti4=row.get("mean_bright_ti4"),
                max_bright_ti4=row.get("max_bright_ti4"),
                mean_bright_ti5=row.get("mean_bright_ti5"),
                max_bright_ti5=row.get("max_bright_ti5"),
                spatial_diameter_km=row.get("spatial_diameter_km"),
            ),
            osm_context=OSMContext(
                osm_industrial_evidence=row.get("osm_industrial_evidence"),
                nearest_industrial_zone_km=row.get("nearest_industrial_zone_km"),
                nearest_factory_km=row.get("nearest_factory_km"),
                nearest_works_km=row.get("nearest_works_km"),
                nearest_mine_km=row.get("nearest_mine_km"),
                nearest_brick_km=row.get("nearest_brick_km"),
                nearest_depot_km=row.get("nearest_depot_km"),
                nearest_power_km=row.get("nearest_power_km"),
                nearest_other_industry_km=row.get("nearest_other_industry_km"),
            ),
        )
