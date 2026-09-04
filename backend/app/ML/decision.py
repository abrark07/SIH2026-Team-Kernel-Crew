import pandas as pd
from .config import OSM_ENTITIES, OSM_EVIDENCE_RADIUS_KM

def apply_domain_decision(events_df):
    """
    Apply final domain decision logic to classify events.
    Logic:
    - Persistent behavior -> Industrial
    - Transient behavior + OSM industrial evidence (<=5km) -> Industrial
    - Otherwise -> Uncertain
    """
    df = events_df.copy()
    
    # Check for OSM evidence within threshold radius
    osm_dist_cols = [f"nearest_{entity}_km" for entity in OSM_ENTITIES]
    
    # Filter only columns that actually exist in the dataframe
    available_dist_cols = [c for c in osm_dist_cols if c in df.columns]
    
    if available_dist_cols:
        # True if ANY entity is within radius
        df["osm_industrial_evidence"] = df[available_dist_cols].le(OSM_EVIDENCE_RADIUS_KM).any(axis=1)
    else:
        df["osm_industrial_evidence"] = False
        
    def decide(row):
        if row["behavior_type"] == "Persistent":
            return "Industrial"
        if row["behavior_type"] == "Transient" and row["osm_industrial_evidence"]:
            return "Industrial"
        return "Uncertain"
        
    df["final_prediction"] = df.apply(decide, axis=1)
    
    return df
