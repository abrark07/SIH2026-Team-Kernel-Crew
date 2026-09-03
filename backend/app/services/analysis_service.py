"""
Analysis orchestration service.

This is the main integration point between the API layer and the
ML/data-processing pipeline.  For now it:

    1. Validates the request (already done by Pydantic schemas).
    2. Creates a run record via the repository.
    3. Optionally fetches FIRMS data.
    4. Returns a structured response.

When the ML teammate's pipeline is ready, plug it into
``_run_ml_pipeline()`` without changing the route layer.
"""

import logging
from typing import Any, Dict, List, Optional

from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.firms_service import FirmsService, FirmsServiceError

logger = logging.getLogger(__name__)


class AnalysisService:
    """Orchestrates an end-to-end analysis run."""

    def __init__(
        self,
        analysis_repo: AnalysisRepository,
        firms_service: FirmsService,
    ) -> None:
        self._repo = analysis_repo
        self._firms = firms_service

    async def start_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Accept an analysis request and kick off the pipeline.

        Returns immediately with a run_id so the frontend can poll
        for progress later.
        """
        # 1. Persist the run
        run = await self._repo.create_run(
            bbox=request.bbox,
            start_date=request.start_date.isoformat(),
            end_date=request.end_date.isoformat(),
        )
        run_id = run["run_id"]

        # 2. Attempt to fetch FIRMS data (best-effort for POC)
        firms_data: Optional[List[Dict[str, Any]]] = None
        try:
            firms_data = await self._firms.fetch_firms_data(
                bbox=request.bbox,
                start_date=request.start_date,
                end_date=request.end_date,
            )
            logger.info(
                "Run %s: fetched %d FIRMS detections",
                run_id, len(firms_data),
            )
        except FirmsServiceError as exc:
            # FIRMS fetch is optional at this stage — log and continue.
            logger.warning("Run %s: FIRMS fetch failed — %s", run_id, exc)

        # 3. ML pipeline integration point
        await self._run_ml_pipeline(run_id, firms_data)

        # 4. Return the acknowledgement
        return AnalysisResponse(
            run_id=run_id,
            status="started",
            message="Analysis request accepted. "
                    "ML pipeline integration pending.",
        )

    # ── ML integration point ────────────────────────────────────

    async def _run_ml_pipeline(
        self,
        run_id: str,
        firms_data: Optional[List[Dict[str, Any]]],
    ) -> None:
        """
        **Integration point for the ML teammate's pipeline.**

        When the pipeline is ready, call it here.  Expected steps:

            1. Event formation (DBSCAN clustering)
            2. Temporal feature extraction
            3. Thermal feature extraction
            4. Spatial / OSM context features
            5. XGBoost classification
            6. Confidence & priority scoring
            7. Store results via repository

        For now this is a no-op.
        """
        # TODO: Plug in the ML pipeline here.
        #
        # Example future usage:
        #
        #   from ml_pipeline import process_analysis
        #   result = await process_analysis(run_id, firms_data)
        #   await self._repo.update_run(run_id, {
        #       "status": "completed",
        #       "result": result,
        #   })
        #
        logger.info(
            "Run %s: ML pipeline not yet integrated (no-op).", run_id,
        )
