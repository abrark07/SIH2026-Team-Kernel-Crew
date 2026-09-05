"""
Pydantic models for thermal-event endpoints.

Schema aligned to the frozen ML contract output fields:
  event_id, centroid_lat/lon, behavior_cluster, behavior_type,
  final_prediction, active_days, duration_days, detection_count,
  mean_frp, max_frp, spatial_diameter_km, nearest_*_km OSM distances.

Removed invented fields: confidence, risk_level, priority_score.
"""

from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── GeoJSON Feature Collection (GET /api/v1/events) ─────────────

class EventProperties(BaseModel):
    """Properties block inside a GeoJSON Feature — driven by ML output."""

    event_id: str

    # Classification driven by final_prediction field in ML output
    classification: Optional[str] = Field(
        None, description="'Industrial' or 'Uncertain' per domain decision rule"
    )

    # Behavior from frozen K-Means model
    behavior_type: Optional[str] = Field(
        None, description="'Persistent' or 'Transient' — from frozen KMeans cluster"
    )
    behavior_cluster: Optional[int] = Field(
        None, description="Raw cluster index from KMeans (0 or 1)"
    )

    # Temporal features from feature engineering
    active_days: Optional[int] = None
    duration_days: Optional[int] = None
    detection_count: Optional[int] = None
    activity_frequency: Optional[float] = None

    # Thermal features from VIIRS
    mean_frp: Optional[float] = Field(None, description="Mean Fire Radiative Power (MW)")
    max_frp: Optional[float] = Field(None, description="Max Fire Radiative Power (MW)")
    mean_bright_ti4: Optional[float] = Field(None, description="Mean brightness temp channel I4 (K)")
    max_bright_ti4: Optional[float] = Field(None, description="Max brightness temp channel I4 (K)")

    # Spatial
    spatial_diameter_km: Optional[float] = None

    # OSM context distances (km) — None when OSM data not available
    nearest_industrial_zone_km: Optional[float] = None
    nearest_factory_km: Optional[float] = None
    nearest_works_km: Optional[float] = None
    nearest_mine_km: Optional[float] = None
    nearest_brick_km: Optional[float] = None
    nearest_depot_km: Optional[float] = None
    nearest_power_km: Optional[float] = None
    nearest_other_industry_km: Optional[float] = None
    osm_industrial_evidence: Optional[bool] = None


class EventGeometry(BaseModel):
    """GeoJSON Point geometry."""

    type: str = "Point"
    coordinates: List[float] = Field(
        ...,
        min_length=2,
        max_length=2,
        description="[longitude, latitude]",
    )


class EventFeature(BaseModel):
    """A single GeoJSON Feature."""

    type: str = "Feature"
    geometry: EventGeometry
    properties: EventProperties


class EventFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection returned by GET /api/v1/events."""

    type: str = "FeatureCollection"
    features: List[EventFeature] = Field(default_factory=list)


# ── Detail model (GET /api/v1/events/{event_id}) ─────────────────

class EventTemporal(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    active_days: Optional[int] = None
    duration_days: Optional[int] = None
    detection_count: Optional[int] = None
    activity_frequency: Optional[float] = None
    detections_per_active_day: Optional[float] = None


class EventThermal(BaseModel):
    mean_frp: Optional[float] = None
    max_frp: Optional[float] = None
    std_frp: Optional[float] = None
    mean_bright_ti4: Optional[float] = None
    max_bright_ti4: Optional[float] = None
    mean_bright_ti5: Optional[float] = None
    max_bright_ti5: Optional[float] = None
    spatial_diameter_km: Optional[float] = None


class OSMContext(BaseModel):
    osm_industrial_evidence: Optional[bool] = None
    nearest_industrial_zone_km: Optional[float] = None
    nearest_factory_km: Optional[float] = None
    nearest_works_km: Optional[float] = None
    nearest_mine_km: Optional[float] = None
    nearest_brick_km: Optional[float] = None
    nearest_depot_km: Optional[float] = None
    nearest_power_km: Optional[float] = None
    nearest_other_industry_km: Optional[float] = None


class EventDetail(BaseModel):
    """Full detail response for a single thermal event."""

    event_id: str
    classification: Optional[str] = None
    behavior_type: Optional[str] = None
    behavior_cluster: Optional[int] = None
    location: Dict[str, float]   # {"latitude": ..., "longitude": ...}
    temporal: EventTemporal
    thermal: EventThermal
    osm_context: OSMContext


# ── Error model ──────────────────────────────────────────────────

class EventNotFoundError(BaseModel):
    """Body returned when an event_id does not exist."""
    detail: str = "Event not found"
