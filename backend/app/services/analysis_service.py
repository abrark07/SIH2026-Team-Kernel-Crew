"""
Analysis orchestration service.

This is the main integration point between the API layer and the
ML/data-processing pipeline.  For now it:

    1. Validates the request (already done by Pydantic schemas).
    2. Creates a run record via the repository.
    3. Fetches FIRMS data (bypassed for demo to use static dataset).
    4. Returns a structured response.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.firms_service import FirmsService

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

        # 2. SIH DEMO: Bypass live FIRMS fetch.
        firms_data: Optional[List[Dict[str, Any]]] = None
        import pandas as pd
        csv_path = Path(__file__).parent.parent.parent / "data" / "viirs_jan2024_night.csv"
        if csv_path.exists():
            logger.info("Run %s: Loading demo dataset %s", run_id, csv_path.name)
            df = pd.read_csv(csv_path)
            # Pass the FULL dataset to ML pipeline to preserve global event IDs
            # Spatial bounding box filtering will happen after ML processing
            firms_data = df.to_dict(orient="records")
        else:
            logger.warning("Run %s: Demo dataset not found.", run_id)

        # 3. ML pipeline integration point
        await self._run_ml_pipeline(run_id, firms_data, request)

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
        request,
    ) -> None:
        import pandas as pd
        from app.ML.pipeline import MLPipeline

        if not firms_data:
            logger.info("Run %s: No data available, skipping ML.", run_id)
            return

        try:
            logger.info("Run %s: Starting ML pipeline integration", run_id)
            artifacts_dir = Path(__file__).parent.parent / "ML" / "artifacts"
            pipeline = MLPipeline(artifacts_dir=artifacts_dir)

            df = pd.DataFrame(firms_data)
            numeric_cols = ["latitude", "longitude", "frp", "bright_ti4", "bright_ti5"]
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            osm_file = Path(__file__).parent.parent.parent / "data" / "osm_points.csv"
            if hasattr(AnalysisService, "_test_osm_file_override"):
                osm_file = getattr(AnalysisService, "_test_osm_file_override")
                
            osm_data = None
            if osm_file.exists():
                logger.info("Run %s: Found static OSM dataset at %s", run_id, osm_file)
                osm_data = pd.read_csv(osm_file)
            else:
                logger.info("Run %s: No OSM data available.", run_id)
            
            # Run ML pipeline on the FULL, UNFILTERED dataset to preserve global V11 event IDs
            # Then apply the spatial bounding box filter on the resulting events.
            results_df = pipeline.predict(df, osm_data=osm_data)

            if results_df is not None and not results_df.empty:
                # Apply bbox filter to the formed events
                if request.bbox:
                    results_df = results_df[
                        (results_df["centroid_lat"] >= request.bbox[1]) &
                        (results_df["centroid_lat"] <= request.bbox[3]) &
                        (results_df["centroid_lon"] >= request.bbox[0]) &
                        (results_df["centroid_lon"] <= request.bbox[2])
                    ]

            if results_df is None or len(results_df) == 0:
                logger.info("Run %s: ML produced no events.", run_id)
                results = []
            else:
                results = []
                import math
                for _, row in results_df.iterrows():
                    osm_distances = {}
                    for col in results_df.columns:
                        if col.startswith("nearest_") and col.endswith("_km"):
                            v = row.get(col)
                            osm_distances[col] = None if (isinstance(v, float) and math.isnan(v)) else v

                    def _safe(v):
                        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                            return None
                        return v

                    event = {
                        "event_id": str(int(row.get("event_id", 0))) if pd.notnull(row.get("event_id")) else None,
                        "centroid_lat": _safe(float(row.get("centroid_lat", 0.0))),
                        "centroid_lon": _safe(float(row.get("centroid_lon", 0.0))),
                        "final_prediction": str(row.get("final_prediction", "Uncertain")),
                        "behavior_cluster": int(row.get("behavior_cluster", -1)),
                        "behavior_type": str(row.get("behavior_type", "")),
                        "active_days": _safe(float(row.get("active_days", 0.0))),
                        "duration_days": _safe(float(row.get("duration_days", 0.0))),
                        "detection_count": int(row.get("detection_count", 0)),
                        "activity_frequency": _safe(float(row.get("activity_frequency", 0.0))),
                        "detections_per_active_day": _safe(float(row.get("detections_per_active_day", 0.0))),
                        "start_date": str(row["start_date"]) if "start_date" in row else None,
                        "end_date": str(row["end_date"]) if "end_date" in row else None,
                        "mean_frp": _safe(float(row.get("mean_frp", 0.0))),
                        "max_frp": _safe(float(row.get("max_frp", 0.0))),
                        "std_frp": _safe(float(row.get("std_frp", 0.0))),
                        "mean_bright_ti4": _safe(float(row.get("mean_bright_ti4", 0.0))),
                        "max_bright_ti4": _safe(float(row.get("max_bright_ti4", 0.0))),
                        "mean_bright_ti5": _safe(float(row.get("mean_bright_ti5", 0.0))),
                        "max_bright_ti5": _safe(float(row.get("max_bright_ti5", 0.0))),
                        "spatial_diameter_km": _safe(float(row.get("spatial_diameter_km", 0.0))),
                        "osm_industrial_evidence": bool(row.get("osm_industrial_evidence", False)),
                        **osm_distances,
                    }
                    results.append(event)

            await self._repo.update_run(run_id, {
                "status": "completed",
                "result": {"events": results},
                "completed_at": datetime.utcnow().isoformat(),
            })

            # SIH DEMO: Persist events to db.json so EventRepository picks them up
            db_path = Path(__file__).parent.parent.parent / "data" / "db.json"
            import json
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, default=str)
            logger.info("Run %s: Wrote %d events to db.json", run_id, len(results))

        except Exception as exc:
            logger.exception("Run %s: ML pipeline integration failed", run_id)
            await self._repo.update_run(run_id, {
                "status": "failed",
                "error": str(exc),
                "completed_at": datetime.utcnow().isoformat(),
            })
