# SIH Production ML Pipeline

## Purpose
This package contains the self-contained, finalized production ML pipeline for classifying VIIRS nighttime thermal detections into Industrial and Uncertain events. It implements the exact methodology frozen and validated in the V11 and Validation notebooks.

## Architecture
1. **VIIRS** data loading and preprocessing (nighttime filtering, valid thermal attributes).
2. **Event Formation** (daily complete-linkage spatial clustering + 3-day temporal union-find).
3. **Feature Engineering** (temporal duration, activity frequency, thermal intensities, spatial diameters).
4. **Behavior K-Means** (Robust scaling + K-Means K=2 clustering to identify Transient vs Persistent behavior).
5. **OSM Context** (Calculation of distance to nearest domain-specific OSM industrial infrastructure).
6. **Domain Decision**:
   - `Persistent` → `Industrial`
   - `Transient` + industrial OSM evidence ≤5 km → `Industrial`
   - Otherwise → `Uncertain`

## Installation
The backend developer should install the dependencies required by this module:
```bash
pip install -r requirements.txt
```

## Usage
Minimal example to instantiate and call the `MLPipeline`:

```python
import pandas as pd
from ML.pipeline import MLPipeline

# Instantiate the pipeline (it will automatically load artifacts/ models)
pipeline = MLPipeline()

# Predict on raw data (file paths or DataFrames)
results_df = pipeline.predict(
    viirs_data="path/to/viirs.csv",
    osm_data="path/to/osm_points.csv"
)

# results_df contains the final events and their predictions
print(results_df[["event_id", "behavior_type", "final_prediction", "centroid_lat", "centroid_lon"]])
```

## Inputs
- **VIIRS Data**: Requires columns `acq_date`, `latitude`, `longitude`, `daynight`, `frp`, `bright_ti4`, `bright_ti5`.
- **OSM Data**: Requires columns `latitude`, `longitude`, `industrial`, `landuse`, `power`, `man_made`, `building` etc. (formatted identically to the project's `osm_points.csv`).

## Outputs
Returns a single DataFrame with one row per event. Key output fields include:
- `event_id`: Unique identifier for the merged thermal event.
- `centroid_lat`, `centroid_lon`: Geographic center of the event.
- `behavior_cluster`, `behavior_type`: `Transient` or `Persistent`.
- `final_prediction`: `Industrial` or `Uncertain`.
- Temporal stats: `active_days`, `duration_days`, `detection_count`.
- Thermal stats: `mean_frp`, `max_frp`, etc.
- OSM context: `nearest_industrial_zone_km`, `nearest_factory_km`, etc.

## Frozen Model
- **Scaler**: `RobustScaler`
- **Model**: `KMeans(n_clusters=2, random_state=42)`
- The models are pre-fitted and loaded from `artifacts/`. They do not train or fit during prediction.

## Decision Logic
- **Persistent** → `Industrial`
- **Transient** + industrial OSM evidence ≤5 km → `Industrial`
- **Otherwise** → `Uncertain`
