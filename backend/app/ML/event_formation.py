import time
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.neighbors import BallTree
from .config import EARTH_RADIUS_KM, SPATIAL_RADIUS_KM, TEMPORAL_GAP_DAYS

def create_complete_linkage_objects(df, radius_km):
    """
    Create spatial objects independently for each acquisition day using complete linkage.
    Prevents chain growth by requiring max pairwise distance within cluster to be <= radius.
    """
    object_records = []
    object_id = 0

    for date, day_data in df.groupby("acq_date", sort=True):
        day_indices = day_data.index.to_numpy()
        coords_rad = np.radians(day_data[["latitude", "longitude"]].values)

        if len(day_indices) == 1:
            object_records.append({
                "daily_object_id": object_id,
                "acq_date": date,
                "detection_count": 1,
                "detection_indices": day_indices.tolist()
            })
            object_id += 1
            continue

        # Pairwise haversine distance matrix
        lat = coords_rad[:, 0][:, None]
        lon = coords_rad[:, 1][:, None]
        dlat = lat - lat.T
        dlon = lon - lon.T

        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(lat) * np.cos(lat.T) * np.sin(dlon / 2) ** 2
        )
        distance_matrix_km = 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))

        model = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=radius_km,
            metric="precomputed",
            linkage="complete"
        )
        labels = model.fit_predict(distance_matrix_km)

        for label in np.unique(labels):
            detection_indices = day_indices[labels == label]
            object_records.append({
                "daily_object_id": object_id,
                "acq_date": date,
                "detection_count": len(detection_indices),
                "detection_indices": detection_indices.tolist()
            })
            object_id += 1

    return pd.DataFrame(object_records)


def temporal_link_complete_linkage(detections, daily_objects, spatial_radius_km, temporal_gap_days):
    """
    Link daily spatial objects temporally based on their centroids using Union-Find.
    """
    objects = daily_objects.copy()
    objects["acq_date"] = pd.to_datetime(objects["acq_date"])

    centroids = []
    for _, row in objects.iterrows():
        idx = row["detection_indices"]
        pts = detections.loc[idx, ["latitude", "longitude"]]
        centroids.append([pts["latitude"].mean(), pts["longitude"].mean()])

    objects["centroid_lat"] = [x[0] for x in centroids]
    objects["centroid_lon"] = [x[1] for x in centroids]

    coords = np.radians(objects[["centroid_lat", "centroid_lon"]].values)
    tree = BallTree(coords, metric="haversine")
    radius_rad = spatial_radius_km / EARTH_RADIUS_KM

    n = len(objects)
    parent = np.arange(n)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        neighbours = tree.query_radius(coords[i:i+1], r=radius_rad)[0]
        date_i = objects.iloc[i]["acq_date"]
        for j in neighbours:
            if j <= i:
                continue
            date_j = objects.iloc[j]["acq_date"]
            gap = abs((date_j - date_i).days)
            if gap <= temporal_gap_days:
                union(i, j)

    roots = np.array([find(i) for i in range(n)])
    root_to_event = {}
    event_ids = []
    next_event_id = 0
    for root in roots:
        if root not in root_to_event:
            root_to_event[root] = next_event_id
            next_event_id += 1
        event_ids.append(root_to_event[root])

    objects["event_id"] = event_ids
    return objects


def form_events(detections):
    """
    Complete V11 event formation pipeline mapping VIIRS detections to thermal events.
    """
    daily_objects = create_complete_linkage_objects(detections, SPATIAL_RADIUS_KM)
    events_df = temporal_link_complete_linkage(
        detections, 
        daily_objects, 
        SPATIAL_RADIUS_KM, 
        TEMPORAL_GAP_DAYS
    )
    return events_df
