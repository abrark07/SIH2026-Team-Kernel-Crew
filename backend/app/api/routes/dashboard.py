"""
GET /api/v1/dashboard/summary
"""

from fastapi import APIRouter

from app.repositories.event_repository import EventRepository
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

# ── Singleton instances ─────────────────────────────────────────
_event_repo = EventRepository()
_dashboard_service = DashboardService(_event_repo)


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Dashboard summary statistics",
    description=(
        "Returns aggregate statistics for the frontend dashboard.  "
        "Values are currently zero because the database and ML pipeline "
        "are not yet integrated."
    ),
)
async def get_summary() -> DashboardSummary:
    return await _dashboard_service.get_summary()
