"""
EventRepository — reads ML pipeline output from backend/data/db.json.

The db.json file is written by the ML pipeline (via analysis_service or
the process_new_dataset script) and contains raw ML output fields:
  event_id, centroid_lat, centroid_lon, behavior_cluster, behavior_type,
  final_prediction (or prediction), active_days, duration_days,
  detection_count, mean_frp, max_frp, mean_bright_ti4, max_bright_ti4,
  mean_bright_ti5, max_bright_ti5, spatial_diameter_km, activity_frequency,
  detections_per_active_day, nearest_*_km OSM distances,
  osm_industrial_evidence.

This layer performs ZERO invention — it reads and passes through what the
ML pipeline produced. The service layer maps to API schema.
"""

import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).parent.parent.parent / "data" / "db.json"


def _safe(v):
    """Return None for NaN/Inf floats; pass everything else through."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def _load_db() -> List[Dict[str, Any]]:
    if not DB_PATH.exists():
        return []
    try:
        with open(DB_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"[EventRepository] Failed to load db.json: {e}")
        return []


def _normalize_row(r: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize a raw db.json row to a stable internal dict.

    Handles both the old format (from earlier scripts that used
    'classification'/'lat'/'lng' keys) and the canonical ML format
    (centroid_lat/centroid_lon/final_prediction/behavior_type).
    """
    # ── Coordinates ─────────────────────────────────────────────
    lat = _safe(r.get("centroid_lat") or r.get("latitude") or r.get("lat"))
    lon = _safe(r.get("centroid_lon") or r.get("longitude") or r.get("lng"))

    # ── Classification from ML final_prediction ──────────────────
    # ML produces "Industrial" or "Uncertain" via apply_domain_decision.
    # If old data used different keys, fall back gracefully.
    raw_pred = (
        r.get("final_prediction")
        or r.get("prediction")
        or r.get("classification")
        or "Uncertain"
    )
    # Normalise old UI-specific strings to ML canonical values
    _pred_map = {
        "Industrial Source": "Industrial",
        "Anomaly": "Uncertain",
        "Wildfire": "Uncertain",          # ML has no Wildfire class
        "industrial-like": "Industrial",
        "non-industrial": "Uncertain",
        "uncertain": "Uncertain",
    }
    classification = _pred_map.get(raw_pred, raw_pred)  # keep "Industrial"/"Uncertain" as-is

    # ── Behavior from frozen KMeans ──────────────────────────────
    behavior_type = r.get("behavior_type")  # "Persistent" or "Transient"
    behavior_cluster = r.get("behavior_cluster")

    # ── Temporal ─────────────────────────────────────────────────
    active_days_raw = r.get("active_days", r.get("observedDays"))
    duration_days_raw = r.get("duration_days")
    active_days = int(active_days_raw) if active_days_raw is not None else None
    duration_days = int(duration_days_raw) if duration_days_raw is not None else None
    detection_count_raw = r.get("detection_count")
    detection_count = int(detection_count_raw) if detection_count_raw is not None else None

    activity_frequency = _safe(r.get("activity_frequency"))
    detections_per_active_day = _safe(r.get("detections_per_active_day"))

    start_date = r.get("start_date")
    end_date = r.get("end_date")

    # ── Thermal ──────────────────────────────────────────────────
    mean_frp = _safe(r.get("mean_frp"))
    max_frp = _safe(r.get("max_frp"))
    std_frp = _safe(r.get("std_frp"))
    mean_bright_ti4 = _safe(r.get("mean_bright_ti4") or r.get("brightness"))
    max_bright_ti4 = _safe(r.get("max_bright_ti4"))
    mean_bright_ti5 = _safe(r.get("mean_bright_ti5"))
    max_bright_ti5 = _safe(r.get("max_bright_ti5"))
    spatial_diameter_km = _safe(r.get("spatial_diameter_km"))

    # ── OSM Context ───────────────────────────────────────────────
    osm_evidence = r.get("osm_industrial_evidence")
    nearest = {}
    for entity in [
        "industrial_zone", "factory", "works", "mine",
        "brick", "depot", "power", "other_industry"
    ]:
        key = f"nearest_{entity}_km"
        # Also check nested nearest_osm dict from old format
        val = r.get(key)
        if val is None and isinstance(r.get("nearest_osm"), dict):
            val = r["nearest_osm"].get(key)
        nearest[key] = _safe(val)

    return {
        "event_id": str(r.get("event_id", r.get("id", ""))),
        "latitude": lat,
        "longitude": lon,
        "classification": classification,
        "behavior_type": behavior_type,
        "behavior_cluster": behavior_cluster,
        "active_days": active_days,
        "duration_days": duration_days,
        "detection_count": detection_count,
        "activity_frequency": activity_frequency,
        "detections_per_active_day": detections_per_active_day,
        "start_date": start_date,
        "end_date": end_date,
        "mean_frp": mean_frp,
        "max_frp": max_frp,
        "std_frp": std_frp,
        "mean_bright_ti4": mean_bright_ti4,
        "max_bright_ti4": max_bright_ti4,
        "mean_bright_ti5": mean_bright_ti5,
        "max_bright_ti5": max_bright_ti5,
        "spatial_diameter_km": spatial_diameter_km,
        "osm_industrial_evidence": osm_evidence,
        **nearest,
    }


class EventRepository:
    """
    Data-access layer for thermal events.

    Reads from backend/data/db.json which is written by the ML pipeline.
    All filtering is performed in-memory (acceptable for POC scale).
    """

    async def get_events(
        self,
        *,
        run_id: Optional[str] = None,          # reserved for future DB migration
        classification: Optional[str] = None,
        risk_level: Optional[str] = None,       # deprecated — not in ML contract
        start_date: Optional[str] = None,       # reserved
        end_date: Optional[str] = None,         # reserved
        min_confidence: Optional[float] = None, # deprecated — not in ML contract
    ) -> List[Dict[str, Any]]:
        rows = [_normalize_row(r) for r in _load_db()]

        if classification:
            rows = [r for r in rows if r["classification"] == classification]

        return rows

    async def get_event_by_id(self, event_id: str) -> Optional[Dict[str, Any]]:
        for r in _load_db():
            row = _normalize_row(r)
            if row["event_id"] == event_id:
                return row
        return None

    async def get_summary_stats(self) -> Dict[str, Any]:
        rows = [_normalize_row(r) for r in _load_db()]
        total = len(rows)
        industrial = sum(1 for r in rows if r["classification"] == "Industrial")
        uncertain = sum(1 for r in rows if r["classification"] == "Uncertain")
        persistent = sum(1 for r in rows if r.get("behavior_type") == "Persistent")
        transient = sum(1 for r in rows if r.get("behavior_type") == "Transient")
        total_detections = sum(r.get("detection_count") or 0 for r in rows)
        return {
            "total_detections": total_detections,
            "total_events": total,
            "industrial_events": industrial,
            "uncertain_events": uncertain,
            "persistent_events": persistent,
            "transient_events": transient,
        }
