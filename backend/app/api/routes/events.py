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
        "Returns a GeoJSON FeatureCollection of thermal events.  "
        "Supports optional filters for run_id, classification, risk level, "
        "date range, and minimum confidence.  "
        "Currently returns an empty collection because the database and "
        "ML pipeline are not yet integrated."
    ),
)
async def list_events(
    run_id: Optional[str] = Query(None, description="Filter by analysis run ID"),
    classification: Optional[str] = Query(
        None, description="Filter by classification (e.g. industrial-like)"
    ),
    risk_level: Optional[str] = Query(
        None, description="Filter by risk level (high, medium, low)"
    ),
    start_date: Optional[str] = Query(
        None, description="Filter events detected on or after this date (YYYY-MM-DD)"
    ),
    end_date: Optional[str] = Query(
        None, description="Filter events detected on or before this date (YYYY-MM-DD)"
    ),
    min_confidence: Optional[float] = Query(
        None, ge=0.0, le=1.0, description="Minimum classification confidence"
    ),
) -> EventFeatureCollection:
    return await _event_service.get_events(
        run_id=run_id,
        classification=classification,
        risk_level=risk_level,
        start_date=start_date,
        end_date=end_date,
        min_confidence=min_confidence,
    )


@router.get(
    "/{event_id}",
    response_model=EventDetail,
    responses={404: {"model": EventNotFoundError}},
    summary="Get event detail",
    description=(
        "Returns full detail for a single thermal event.  "
        "Returns 404 if the event ID does not exist."
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
