# ML/config.py

# Number of behavior clusters
N_CLUSTERS = 2
RANDOM_STATE = 42

# OSM Geographic Threshold
OSM_EVIDENCE_RADIUS_KM = 5.0

# V11 Event Formation Parameters
EARTH_RADIUS_KM = 6371.0088
SPATIAL_RADIUS_KM = 0.375
TEMPORAL_GAP_DAYS = 3

# Frozen Behavior Features
BEHAVIOR_FEATURES = [
    "mean_frp",
    "max_frp",
    "mean_bright_ti4",
    "max_bright_ti4",
    "mean_bright_ti5",
    "max_bright_ti5",
    "active_days",
    "duration_days",
    "activity_frequency",
    "detections_per_active_day",
    "spatial_diameter_km"
]

# OSM Entities Definitions
OSM_ENTITIES = [
    "industrial_zone",
    "factory",
    "works",
    "mine",
    "brick",
    "depot",
    "power",
    "other_industry"
]
