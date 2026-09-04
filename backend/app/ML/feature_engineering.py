import numpy as np
import pandas as pd
from .config import EARTH_RADIUS_KM

def calculate_event_features(detections, event_mapping):
    """
    Calculate event-level features based on the V11 implementation.
    
    Args:
        detections: Raw preprocessed VIIRS DataFrame
        event_mapping: DataFrame mapping from temporal_link_complete_linkage containing 
                       event_id, daily_object_id, acq_date, and detection_indices.
    """
    event_stats = []
    
    for event_id, obj_group in event_mapping.groupby("event_id"):
        all_indices = []
        for indices in obj_group["detection_indices"]:
            all_indices.extend(indices)
            
        pts_df = detections.loc[all_indices]
        
        # Spatial properties
        coords = pts_df[["latitude", "longitude"]].values
        centroid_lat = coords[:, 0].mean()
        centroid_lon = coords[:, 1].mean()
        
        # Spatial diameter
        rad = np.radians(coords)
        lat1 = rad[:, None, 0]
        lat2 = rad[None, :, 0]
        dlat = lat2 - lat1
        dlon = rad[None, :, 1] - rad[:, None, 1]
        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        distances = 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1))) * EARTH_RADIUS_KM
        spatial_diameter_km = distances.max()
        
        # Temporal properties
        start_date = pts_df["acq_date"].min()
        end_date = pts_df["acq_date"].max()
        active_days = pts_df["acq_date"].nunique()
        duration_days = (end_date - start_date).days + 1
        detection_count = len(all_indices)
        daily_object_count = len(obj_group)
        
        # Activity features
        activity_frequency = active_days / duration_days if duration_days > 0 else 0
        detections_per_active_day = detection_count / active_days if active_days > 0 else 0
        
        # Thermal properties
        frp_vals = pts_df["frp"]
        ti4_vals = pts_df["bright_ti4"]
        ti5_vals = pts_df["bright_ti5"]
        
        stat_dict = {
            "event_id": event_id,
            "centroid_lat": centroid_lat,
            "centroid_lon": centroid_lon,
            
            "start_date": start_date,
            "end_date": end_date,
            "active_days": active_days,
            "duration_days": duration_days,
            "detection_count": detection_count,
            "daily_object_count": daily_object_count,
            "activity_frequency": activity_frequency,
            "detections_per_active_day": detections_per_active_day,
            "spatial_diameter_km": spatial_diameter_km,
            
            "mean_frp": frp_vals.mean(),
            "max_frp": frp_vals.max(),
            "std_frp": frp_vals.std() if len(frp_vals) > 1 else 0.0,
            
            "mean_bright_ti4": ti4_vals.mean(),
            "max_bright_ti4": ti4_vals.max(),
            "std_bright_ti4": ti4_vals.std() if len(ti4_vals) > 1 else 0.0,
            
            "mean_bright_ti5": ti5_vals.mean(),
            "max_bright_ti5": ti5_vals.max(),
            "std_bright_ti5": ti5_vals.std() if len(ti5_vals) > 1 else 0.0,
            
            "frp_range": frp_vals.max() - frp_vals.min(),
            "ti4_range": ti4_vals.max() - ti4_vals.min(),
            "ti5_range": ti5_vals.max() - ti5_vals.min()
        }
        
        event_stats.append(stat_dict)
        
    features_df = pd.DataFrame(event_stats)
    # Fill any remaining NaNs in std features for single-detection events
    features_df = features_df.fillna(0)
    
    return features_df
