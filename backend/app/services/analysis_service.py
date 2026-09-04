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
        import pandas as pd
        from pathlib import Path
        from app.ML.pipeline import MLPipeline

        if not firms_data:
            logger.info("Run %s: No FIRMS data available, skipping ML.", run_id)
            return

        try:
            logger.info("Run %s: Starting ML pipeline integration", run_id)
            artifacts_dir = Path(__file__).parent.parent / "ML" / "artifacts"
            pipeline = MLPipeline(artifacts_dir=artifacts_dir)

            df = pd.DataFrame(firms_data)
            # Ensure numeric columns are properly typed since CSV parsing yields strings
            numeric_cols = ["latitude", "longitude", "frp", "bright_ti4", "bright_ti5"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # --- OSM Integration Boundary ---
            # The ML pipeline requires OSM contextual data to elevate Transient
            # events to Industrial when they fall within 5km of known entities.
            # Currently, the backend lacks a live OSM database or Overpass API service.
            # We look for a static CSV fallback (e.g. osm_points_v7.csv).
            # If not found, osm_data remains None, and the pipeline gracefully falls back 
            # to purely thermal/temporal behavior classification (Persistent vs Uncertain).
            osm_file = Path(__file__).parent.parent.parent / "data" / "osm_points.csv"
            if hasattr(AnalysisService, "_test_osm_file_override"):
                osm_file = getattr(AnalysisService, "_test_osm_file_override")
                
            osm_data = None
            if osm_file.exists():
                logger.info("Run %s: Found static OSM dataset at %s", run_id, osm_file)
                osm_data = pd.read_csv(osm_file)
            else:
                logger.info("Run %s: No OSM data available. Contextual evidence will be disabled.", run_id)
            
            results_df = pipeline.predict(df, osm_data=osm_data)

            if results_df is None or len(results_df) == 0:
                logger.info("Run %s: ML produced no events.", run_id)
                results = []
            else:
                results = []
                import math
                for _, row in results_df.iterrows():
                    osm_dict = {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in row.items() if 'nearest' in k}
                    
                    # Map to frontend properties
                    prediction = str(row.get("final_prediction", ""))
                    classification = "Industrial Source" if prediction == "Industrial" else "Anomaly"
                    
                    # Persistence %
                    active = float(row.get("active_days", 0.0))
                    duration = float(row.get("duration_days", 1.0))
                    persistence = int((active / max(duration, 1.0)) * 100)
                    
                    event = {
                        "id": int(row.get("event_id", 0)),
                        "name": f"Event {int(row.get('event_id', 0))}",
                        "lat": float(row.get("centroid_lat", 0.0)),
                        "lng": float(row.get("centroid_lon", 0.0)),
                        "classification": classification,
                        "confidence": 95, 
                        "brightness": int(row.get("max_bright_ti4", 300)),
                        "persistence": persistence,
                        "observedDays": int(active),
                        "priorityScore": 75 if classification == "Industrial Source" else 40,
                        "behaviorStatus": "Normal",
                        "behaviorEvidence": [f"{str(row.get('behavior_type', ''))} signature (Cluster {int(row.get('behavior_cluster', -1))})"],
                        
                        # Extra fields requested
                        "event_id": int(row.get("event_id", 0)),
                        "latitude": float(row.get("centroid_lat", 0.0)),
                        "longitude": float(row.get("centroid_lon", 0.0)),
                        "behavior_cluster": int(row.get("behavior_cluster", -1)),
                        "behavior_type": str(row.get("behavior_type", "")),
                        "prediction": prediction,
                        "active_days": float(row.get("active_days", 0.0)),
                        "duration_days": float(row.get("duration_days", 0.0)),
                        "detection_count": int(row.get("detection_count", 0)),
                        "mean_frp": float(row.get("mean_frp", 0.0)),
                        "max_frp": float(row.get("max_frp", 0.0)),
                        "nearest_osm": osm_dict
                    }
                    results.append(event)

            await self._repo.update_run(run_id, {
                "status": "completed",
                "result": {"events": results, "hotspots": results},
            })
            logger.info("Run %s: ML pipeline completed successfully.", run_id)

        except Exception as e:
            logger.exception("Run %s: ML pipeline failed.", run_id)
            await self._repo.update_run(run_id, {
                "status": "failed",
                "error": str(e)
            })
