"""
GET /api/v1/events          — list events (GeoJSON FeatureCollection)
GET /api/v1/events/{id}     — single event detail
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.repositories.event_repository import EventRepository
from app.schemas.events import EventDetail, EventFeatureCollection, EventNotFoundError
from app.services.event_service import EventService

router = APIRouter(prefix="/events", tags=["Events"])

# ── Singleton instances ─────────────────────────────────────────
_event_repo = EventRepository()
_event_service = EventService(_event_repo)


@router.get(
    "",
    response_model=EventFeatureCollection,
    summary="List thermal events (GeoJSON)",
    description=(
        "Returns a GeoJSON FeatureCollection of thermal events. "
        "Properties driven by frozen ML output: classification (Industrial/Uncertain), "
        "behavior_type (Persistent/Transient), VIIRS thermal metrics, OSM distances."
    ),
)
async def list_events(
    run_id: Optional[str] = Query(None, description="Filter by analysis run ID"),
    classification: Optional[str] = Query(
        None, description="Filter by classification: 'Industrial' or 'Uncertain'"
    ),
    start_date: Optional[str] = Query(
        None, description="Reserved — not yet applied server-side"
    ),
    end_date: Optional[str] = Query(
        None, description="Reserved — not yet applied server-side"
    ),
) -> EventFeatureCollection:
    return await _event_service.get_events(
        run_id=run_id,
        classification=classification,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{event_id}",
    response_model=EventDetail,
    responses={404: {"model": EventNotFoundError}},
    summary="Get event detail",
    description=(
        "Returns full ML output detail for a single thermal event, including "
        "temporal, thermal, behavior, and OSM context fields. Returns 404 if not found."
    ),
)
async def get_event(event_id: str) -> EventDetail:
    result = await _event_service.get_event_detail(event_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Event '{event_id}' not found.",
        )
    return result
