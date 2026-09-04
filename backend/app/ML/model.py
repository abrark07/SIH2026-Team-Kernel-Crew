import joblib
import pandas as pd
from pathlib import Path
from .config import BEHAVIOR_FEATURES

class BehaviorModel:
    def __init__(self, artifacts_dir=None):
        """
        Load the frozen model artifacts. 
        Will not retrain or fit during normal operations.
        """
        if artifacts_dir is None:
            artifacts_dir = Path(__file__).parent / "artifacts"
        else:
            artifacts_dir = Path(artifacts_dir)
            
        self.scaler = joblib.load(artifacts_dir / "scaler.joblib")
        self.kmeans = joblib.load(artifacts_dir / "kmeans.joblib")
        
    def predict(self, events_df):
        """
        Predict behavior clusters and semantic types for events.
        Requires events_df to contain all BEHAVIOR_FEATURES.
        """
        # Ensure all required features are present
        missing = [f for f in BEHAVIOR_FEATURES if f not in events_df.columns]
        if missing:
            raise ValueError(f"Missing required behavior features: {missing}")
            
        X = events_df[BEHAVIOR_FEATURES].copy()
        
        # Fill any missing feature values with 0 before scaling for robustness
        X = X.fillna(0)
        
        # Predict using frozen models
        X_scaled = self.scaler.transform(X)
        clusters = self.kmeans.predict(X_scaled)
        
        # In validation, Cluster 1 is Persistent and Cluster 0 is Transient
        # We enforce this frozen semantic mapping
        behavior_types = ["Persistent" if c == 1 else "Transient" for c in clusters]
        
        result_df = events_df.copy()
        result_df["behavior_cluster"] = clusters
        result_df["behavior_type"] = behavior_types
        
        return result_df
