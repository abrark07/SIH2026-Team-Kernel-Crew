"""
POST /api/v1/analysis/run           — start an analysis
GET  /api/v1/analysis/runs/{run_id} — check status of a run
"""

from fastapi import APIRouter, HTTPException, status

from app.schemas.analysis import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisRunStatus,
    RunNotFoundError,
)
from app.services.analysis_service import AnalysisService
from app.services.firms_service import FirmsService
from app.repositories.analysis_repository import AnalysisRepository

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# ── Singleton instances (shared across requests) ───────────────
# In a production app these would be managed via dependency injection.
_analysis_repo = AnalysisRepository()
_firms_service = FirmsService()
_analysis_service = AnalysisService(_analysis_repo, _firms_service)


@router.post(
    "/run",
    response_model=AnalysisResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start an analysis run",
    description=(
        "Submit a bounding box and date range to begin thermal-anomaly "
        "analysis.  Returns immediately with a run ID.  The ML pipeline "
        "integration is pending — this endpoint is integration-ready."
    ),
)
async def run_analysis(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return await _analysis_service.start_analysis(request)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while starting the analysis.",
        ) from exc


@router.get(
    "/runs/{run_id}",
    response_model=AnalysisRunStatus,
    responses={404: {"model": RunNotFoundError}},
    summary="Get analysis run status",
    description=(
        "Returns the current status of an analysis run.  "
        "Use the run_id returned by POST /analysis/run."
    ),
)
async def get_run_status(run_id: str) -> AnalysisRunStatus:
    run = await _analysis_repo.get_run(run_id)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis run '{run_id}' not found.",
        )
    return AnalysisRunStatus(
        run_id=run["run_id"],
        status=run["status"],
        created_at=run.get("created_at"),
        bbox=run.get("bbox"),
        start_date=run.get("start_date"),
        end_date=run.get("end_date"),
        result=run.get("result"),
    )

