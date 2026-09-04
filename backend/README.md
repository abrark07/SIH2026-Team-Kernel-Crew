# Backend - SIH 2026 Industrial Fire Detection

This backend powers the AI-based detection and classification of industrial fires and persistent thermal sources using NASA FIRMS and OSM context.

## ML Integration & Required Runtime Asset

The core ML classification logic is integrated and frozen in `app/ML/`. 

**Required runtime asset:**
`backend/data/osm_points.csv`

**Source:**
You must provide the authoritative preprocessed `osm_points_v7.csv` from the ML research pipeline and place it in the `backend/data/` directory named as `osm_points.csv`.

**Required minimum columns:**
* `latitude`
* `longitude`
* `industrial`
* `landuse`
* `power`
* `man_made`

**Behavior if missing:**
If this file is omitted, the ML pipeline will log a startup warning ("OSM contextual dataset not found; predictions will run without OSM evidence.") and gracefully fallback to classifying events strictly on thermal/temporal persistence. Transient events without OSM evidence will default to `Uncertain` (Anomaly).
