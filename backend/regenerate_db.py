"""
regenerate_db.py — Regenerate backend/data/db.json from the frozen ML pipeline.

This script:
  1. Loads the raw VIIRS CSV (viirs_jan2024_night.csv)
  2. Loads the OSM points CSV (osm_points.csv) for context enrichment
  3. Runs the frozen MLPipeline (predict → feature engineering → KMeans → decision)
  4. Saves the FULL pipeline DataFrame to db.json using canonical ML column names

NO field renaming, NO invented values, NO UI-facing aliases.
The saved columns are exactly what the ML pipeline produces:
  event_id, centroid_lat, centroid_lon,
  active_days, duration_days, detection_count,
  activity_frequency, detections_per_active_day,
  mean_frp, max_frp, std_frp,
  mean_bright_ti4, max_bright_ti4,
  mean_bright_ti5, max_bright_ti5,
  spatial_diameter_km,
  behavior_cluster, behavior_type,
  osm_industrial_evidence,
  nearest_industrial_zone_km, nearest_factory_km,
  nearest_works_km, nearest_mine_km, nearest_brick_km,
  nearest_depot_km, nearest_power_km, nearest_other_industry_km,
  final_prediction,
  start_date, end_date
"""

import json
import math
import sys
from pathlib import Path

# Ensure imports resolve from backend/
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR))

import pandas as pd
from app.ML.pipeline import MLPipeline

# ── Paths ─────────────────────────────────────────────────────────
VIIRS_CSV = BACKEND_DIR / "data" / "viirs_jan2024_night.csv"
OSM_CSV   = BACKEND_DIR / "data" / "osm_points.csv"
OUT_JSON  = BACKEND_DIR / "data" / "db.json"

# ── Column sets to preserve ───────────────────────────────────────
# All canonical ML output columns. Any column NOT in this list is dropped.
CANONICAL_COLUMNS = [
    "event_id",
    "centroid_lat",
    "centroid_lon",
    "start_date",
    "end_date",
    "active_days",
    "duration_days",
    "detection_count",
    "daily_object_count",
    "activity_frequency",
    "detections_per_active_day",
    "mean_frp",
    "max_frp",
    "std_frp",
    "mean_bright_ti4",
    "max_bright_ti4",
    "std_bright_ti4",
    "mean_bright_ti5",
    "max_bright_ti5",
    "std_bright_ti5",
    "frp_range",
    "ti4_range",
    "ti5_range",
    "spatial_diameter_km",
    "behavior_cluster",
    "behavior_type",
    "osm_industrial_evidence",
    "nearest_industrial_zone_km",
    "nearest_factory_km",
    "nearest_works_km",
    "nearest_mine_km",
    "nearest_brick_km",
    "nearest_depot_km",
    "nearest_power_km",
    "nearest_other_industry_km",
    "final_prediction",
]


def _safe_val(v):
    """Replace NaN/Inf with None for JSON serialisation."""
    if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
        return None
    return v


def main():
    print(f"[1/5] Loading VIIRS data from {VIIRS_CSV}")
    if not VIIRS_CSV.exists():
        print(f"ERROR: {VIIRS_CSV} not found.")
        sys.exit(1)
    viirs_df = pd.read_csv(VIIRS_CSV)
    print(f"      {len(viirs_df):,} raw detections loaded.")

    print(f"[2/5] Loading OSM data from {OSM_CSV}")
    if OSM_CSV.exists():
        osm_df = pd.read_csv(OSM_CSV)
        print(f"      {len(osm_df):,} OSM entities loaded.")
    else:
        osm_df = None
        print("      OSM file not found — context enrichment will be disabled.")

    print("[3/5] Running frozen ML pipeline…")
    artifacts_dir = BACKEND_DIR / "app" / "ML" / "artifacts"
    pipeline = MLPipeline(artifacts_dir=artifacts_dir)
    results_df = pipeline.predict(viirs_df, osm_data=osm_df)

    if results_df is None or len(results_df) == 0:
        print("ERROR: ML pipeline produced no events.")
        sys.exit(1)
    print(f"      Pipeline produced {len(results_df):,} events.")
    print(f"      Columns: {list(results_df.columns)}")

    print("[4/5] Selecting canonical columns and serialising…")
    # Keep only canonical columns that actually exist in the output
    cols_present = [c for c in CANONICAL_COLUMNS if c in results_df.columns]
    missing_from_ml = [c for c in CANONICAL_COLUMNS if c not in results_df.columns]
    if missing_from_ml:
        print(f"      WARNING: These canonical columns were not produced by the pipeline:")
        for c in missing_from_ml:
            print(f"        - {c}")

    out_df = results_df[cols_present].copy()

    # Convert dates to ISO strings for JSON
    for col in ["start_date", "end_date"]:
        if col in out_df.columns:
            out_df[col] = out_df[col].astype(str).replace("NaT", None)

    # Convert to records and sanitise NaN/Inf
    records = []
    for row in out_df.to_dict(orient="records"):
        clean = {k: _safe_val(v) for k, v in row.items()}
        # Ensure event_id is a string (JSON-safe)
        clean["event_id"] = str(int(clean["event_id"])) if clean.get("event_id") is not None else None
        records.append(clean)

    print(f"[5/5] Writing {len(records):,} records to {OUT_JSON}")
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, default=str)

    # ── Verification summary ───────────────────────────────────────
    print("\n=== VERIFICATION ===")
    r0 = records[0]
    check_fields = [
        "event_id", "centroid_lat", "centroid_lon",
        "behavior_cluster", "behavior_type", "final_prediction",
        "active_days", "duration_days", "detection_count",
        "mean_frp", "max_frp", "spatial_diameter_km",
        "activity_frequency", "mean_bright_ti4", "osm_industrial_evidence",
        "nearest_factory_km",
    ]
    for f in check_fields:
        val = r0.get(f, "MISSING")
        status = "✓" if val != "MISSING" and val is not None else ("NULL" if val is None else "MISSING")
        print(f"  [{status}] {f}: {val}")

    industrial = sum(1 for r in records if r.get("final_prediction") == "Industrial")
    uncertain  = sum(1 for r in records if r.get("final_prediction") == "Uncertain")
    persistent = sum(1 for r in records if r.get("behavior_type") == "Persistent")
    transient  = sum(1 for r in records if r.get("behavior_type") == "Transient")
    print(f"\n  Total events:  {len(records):,}")
    print(f"  Industrial:    {industrial:,}")
    print(f"  Uncertain:     {uncertain:,}")
    print(f"  Persistent:    {persistent:,}")
    print(f"  Transient:     {transient:,}")
    print("\nDone.")


if __name__ == "__main__":
    main()
