from pathlib import Path
from .preprocessing import load_and_preprocess_viirs
from .event_formation import form_events
from .feature_engineering import calculate_event_features
from .context import enrich_with_context
from .model import BehaviorModel
from .decision import apply_domain_decision

class MLPipeline:
    def __init__(self, artifacts_dir=None):
        """
        Initialize the ML pipeline with the frozen behavior model.
        """
        self.model = BehaviorModel(artifacts_dir)
        
    def predict(self, viirs_data, osm_data=None):
        """
        Run the complete prediction pipeline.
        
        Args:
            viirs_data: Path to VIIRS CSV or a pandas DataFrame
            osm_data: Path to OSM points CSV or a pandas DataFrame
            
        Returns:
            A pandas DataFrame containing the final predictions and event features.
        """
        # 1. Preprocessing
        detections = load_and_preprocess_viirs(viirs_data)
        if len(detections) == 0:
            return None # No valid detections
            
        # 2. Event Formation
        event_mapping = form_events(detections)
        if len(event_mapping) == 0:
            return None
            
        # 3. Feature Engineering
        events_df = calculate_event_features(detections, event_mapping)
        
        # 4. Context Enrichment
        events_df = enrich_with_context(events_df, osm_data)
        
        # 5. Behavior Prediction
        events_df = self.model.predict(events_df)
        
        # 6. Domain Decision
        final_events = apply_domain_decision(events_df)
        
        return final_events
