# spatial_model.py
import numpy as np
from sklearn.neighbors import NearestNeighbors

def spatial_risk_model(df, k=5):
    """
    df must have:
    Latitude, Longitude, crime_count (or risk)
    """

    coords = df[["Latitude", "Longitude"]].values

    # Find nearest neighbors
    nbrs = NearestNeighbors(n_neighbors=k, algorithm='ball_tree').fit(coords)
    distances, indices = nbrs.kneighbors(coords)

    spatial_scores = []

    for i, neighbors in enumerate(indices):
        neighbor_risk = df.iloc[neighbors]["crime_count"].values
        
        # Weighted average (closer = more influence)
        weights = 1 / (distances[i] + 1e-5)
        score = np.sum(weights * neighbor_risk) / np.sum(weights)
        
        spatial_scores.append(score)

    df["spatial_risk"] = spatial_scores

    # Normalize 0–1
    df["spatial_risk"] = df["spatial_risk"].rank(pct=True)

    return df