"""
Pydantic models for thermal-event endpoints.

Includes GeoJSON-compatible models for the list endpoint and a rich
detail model for the single-event endpoint.
"""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field


# ── GeoJSON models (GET /api/v1/events) ────────────────────────


class EventProperties(BaseModel):
    """Properties block inside a GeoJSON Feature."""

    event_id: str
    classification: Optional[str] = Field(
        None, description="e.g. industrial-like, non-industrial, uncertain"
    )
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    active_days: Optional[int] = None
    detection_count: Optional[int] = None
    priority_score: Optional[float] = None
    risk_level: Optional[str] = Field(
        None, description="e.g. high, medium, low"
    )


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


# ── Detail models (GET /api/v1/events/{event_id}) ──────────────


class EventLocation(BaseModel):
    latitude: float
    longitude: float


class EventTemporal(BaseModel):
    first_detected: Optional[date] = None
    last_detected: Optional[date] = None
    active_days: Optional[int] = None
    duration_days: Optional[int] = None
    detection_count: Optional[int] = None


class EventThermal(BaseModel):
    mean_frp: Optional[float] = None
    max_frp: Optional[float] = None
    mean_brightness: Optional[float] = None


class IndustrialContext(BaseModel):
    nearest_facility: Optional[str] = None
    facility_type: Optional[str] = None
    distance_m: Optional[float] = None


class EventPriority(BaseModel):
    score: Optional[float] = None
    risk_level: Optional[str] = None


class EventDetail(BaseModel):
    """Full detail response for a single thermal event."""

    event_id: str
    classification: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    location: EventLocation
    temporal: EventTemporal
    thermal: EventThermal
    industrial_context: IndustrialContext
    priority: EventPriority


# ── Error model ─────────────────────────────────────────────────


class EventNotFoundError(BaseModel):
    """Body returned when an event_id does not exist."""

    detail: str = "Event not found"
