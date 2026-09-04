import pandas as pd
from pathlib import Path

def load_and_preprocess_viirs(df_or_path, start_date=None, end_date=None):
    """
    Load and preprocess VIIRS detections as validated in V11.
    Expected columns: acq_date, latitude, longitude, daynight, frp, bright_ti4, bright_ti5.
    """
    if isinstance(df_or_path, (str, Path)):
        df = pd.read_csv(df_or_path, parse_dates=["acq_date"])
    else:
        df = df_or_path.copy()
        if not pd.api.types.is_datetime64_any_dtype(df["acq_date"]):
            df["acq_date"] = pd.to_datetime(df["acq_date"])
            
    # Apply nighttime filtering (critical as per V11)
    if "daynight" in df.columns:
        night = df[df["daynight"].astype(str).str.lower() == "n"].copy()
    else:
        night = df.copy()
        
    if start_date is not None:
        night = night[night["acq_date"] >= pd.to_datetime(start_date)]
    if end_date is not None:
        night = night[night["acq_date"] <= pd.to_datetime(end_date)]
        
    # Remove any invalid records for essential thermal attributes
    essential_cols = ["latitude", "longitude", "acq_date", "frp", "bright_ti4", "bright_ti5"]
    night = night.dropna(subset=[c for c in essential_cols if c in night.columns])
        
    # Sort detections as per V11 requirement
    night = night.sort_values(["acq_date", "latitude", "longitude"]).reset_index(drop=True)
    
    return night
