import pandas as pd
import numpy as np
import sys
sys.path.append('.')
from app.ML.context import load_and_normalize_osm

def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    return R * c

df = pd.read_csv('data/osm_points.csv')
osm_norm = load_and_normalize_osm(df)

event_lat = 23.76965925072046
event_lon = 86.39422256484148

categories = [
    ('industrial_zone', 'entity_industrial_zone'),
    ('factory', 'entity_factory'),
    ('works', 'entity_works'),
    ('mine', 'entity_mine'),
    ('brick', 'entity_brick'),
    ('depot', 'entity_depot'),
    ('power', 'entity_power'),
    ('other_industry', 'entity_other_industry')
]

for api_cat, flag_col in categories:
    cat_df = osm_norm[osm_norm[flag_col] == True].copy()
    if len(cat_df) == 0:
        print(f'{api_cat}: NULL')
        continue
    
    cat_df['dist'] = haversine_dist(event_lat, event_lon, cat_df['latitude'], cat_df['longitude'])
    min_idx = cat_df['dist'].idxmin()
    min_row = cat_df.loc[min_idx]
    
    # Try to grab name or description, but use osm_id as fallback
    name = min_row.get('description', 'Unnamed')
    dist = min_row['dist']
    print(f'{api_cat}: {dist:.6f} km | Feature: ID {min_row["osm_id"]} (lat: {min_row["latitude"]:.5f}, lon: {min_row["longitude"]:.5f})')
