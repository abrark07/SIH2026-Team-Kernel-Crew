import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.neighbors import BallTree
from .config import EARTH_RADIUS_KM, OSM_ENTITIES

def load_and_normalize_osm(osm_path_or_df):
    """
    Load and normalize OSM points data into specific domain entity flags.
    """
    if isinstance(osm_path_or_df, (str, Path)):
        osm = pd.read_csv(osm_path_or_df)
    else:
        osm = osm_path_or_df.copy()
        
    for col in [
        "industrial", "landuse", "power", "man_made", "building", 
        "product", "plant_source", "plant_method", "resource", "description"
    ]:
        if col in osm.columns:
            osm[col] = osm[col].fillna("").astype(str).str.strip().str.lower()
            
    # Domain entity flags
    osm["entity_industrial_zone"] = osm.get("landuse", pd.Series()) == "industrial"
    
    osm["entity_factory"] = osm.get("industrial", pd.Series()).isin([
        "factory", "concrete_plant", "machine_shop", "food_industry", 
        "biotechnology company", "biotechnology_company", "pharmaceutical company", 
        "pharmaceutical_company", "research company", "research institute", 
        "laboratory", "agrochemical company", "refractory_supplier", "oil", 
        "oil_mill", "rice_mill", "grinding_mill", "sawmill", "mill"
    ])
    
    osm["entity_mine"] = (
        (osm.get("industrial", pd.Series()) == "mine") | 
        (osm.get("landuse", pd.Series()) == "quarry")
    )
    
    osm["entity_brick"] = (
        osm.get("industrial", pd.Series()).isin(["brickyard", "brickworks"]) | 
        (osm.get("man_made", pd.Series()) == "kiln")
    )
    
    osm["entity_works"] = osm.get("man_made", pd.Series()) == "works"
    
    osm["entity_depot"] = osm.get("industrial", pd.Series()).isin(["depot", "bus_depot"])
    
    osm["entity_power"] = osm.get("power", pd.Series()) == "plant"
    
    osm["entity_other_industry"] = osm.get("industrial", pd.Series()).isin([
        "slaughterhouse", "scrap_yard", "warehouse", "port", 
        "cooling", "distributor", "business"
    ])
    
    return osm

def enrich_with_context(events_df, osm_df):
    """
    Calculate distance to nearest OSM domain entities for each event.
    Missing OSM data is handled safely by returning np.nan or 9999 for nearest distance.
    """
    if osm_df is None or len(osm_df) == 0:
        for entity in OSM_ENTITIES:
            events_df[f"nearest_{entity}_km"] = np.nan
        return events_df
        
    osm = load_and_normalize_osm(osm_df)
    osm_coords = np.radians(osm[["latitude", "longitude"]].values)
    event_coords = np.radians(events_df[["centroid_lat", "centroid_lon"]].values)
    
    entity_trees = {}
    for entity in OSM_ENTITIES:
        col_name = f"entity_{entity}"
        if col_name in osm.columns:
            mask = osm[col_name].values
            if mask.sum() > 0:
                entity_trees[entity] = BallTree(osm_coords[mask], metric="haversine")
                
    enriched = events_df.copy()
    
    for entity in OSM_ENTITIES:
        dist_col = f"nearest_{entity}_km"
        if entity not in entity_trees:
            enriched[dist_col] = np.nan
            continue
            
        tree = entity_trees[entity]
        dist, _ = tree.query(event_coords, k=1)
        enriched[dist_col] = dist[:, 0] * EARTH_RADIUS_KM
        
    return enriched
