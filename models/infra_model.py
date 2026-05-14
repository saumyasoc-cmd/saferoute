"""
SafeRoute.ai — Layer 2: Infrastructure Safety Score
=====================================================
Rule-based spatial formula — no ML training needed.
Uses inverse-distance weighting from:
    - CCTV cameras   (closer = safer)
    - Street lights  (closer = safer)
    - Police stations(closer = safer)

Input CSVs (get from BBMP open data / RTI):
    bbmp_cctv.csv           → columns: latitude, longitude
    bbmp_streetlights.csv   → columns: latitude, longitude
    bbmp_police_stations.csv→ columns: latitude, longitude, [name]

Output: infra_score (0-1) per ward centroid
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree
from shapely.ops import unary_union
import os


# ── Inverse-distance weighting ─────────────────────────────────────────────

def idw_score(query_points: np.ndarray,
              source_points: np.ndarray,
              k: int = 5,
              power: float = 2.0,
              decay_m: float = 500.0) -> np.ndarray:
    """
    For each query point, compute a 0-1 safety contribution
    from the k nearest source points using inverse-distance weighting.

    Parameters
    ----------
    query_points  : (N, 2) array of [lat, lon] ward centroids
    source_points : (M, 2) array of [lat, lon] infra locations
    k             : number of nearest neighbours to consider
    power         : IDW power (higher = faster decay with distance)
    decay_m       : distance in metres where score ≈ 0.5 (sigmoid-like)

    Returns
    -------
    scores : (N,) array of values in [0, 1]
    """
    if len(source_points) == 0:
        return np.zeros(len(query_points))

    # Convert lat/lon to approximate metres (Bengaluru ~12.97°N)
    # 1 degree lat ≈ 111_000 m, 1 degree lon ≈ 111_000 * cos(lat) m
    def to_meters(pts):
        lat_m = pts[:, 0] * 111_000
        lon_m = pts[:, 1] * 111_000 * np.cos(np.radians(12.97))
        return np.column_stack([lat_m, lon_m])

    q_m = to_meters(query_points)
    s_m = to_meters(source_points)

    k_actual = min(k, len(s_m))
    tree = cKDTree(s_m)
    dists, _ = tree.query(q_m, k=k_actual)

    if k_actual == 1:
        dists = dists[:, np.newaxis]

    # Sigmoid decay: score approaches 1 as distance → 0, 0 as distance → ∞
    scores = np.mean(1.0 / (1.0 + (dists / decay_m) ** power), axis=1)
    return scores


# ── Load infra datasets ────────────────────────────────────────────────────

def load_infra(data_dir: str) -> dict:
    """
    Load BBMP infrastructure CSVs from data_dir.
    Missing files are handled gracefully — returns empty arrays.
    """
    infra = {}

    specs = {
        "cctv":    ("bbmp_cctv.csv",            "CCTV cameras"),
        "lights":  ("bbmp_streetlights.csv",     "Street lights"),
        "police":  ("bbmp_police_stations.csv",  "Police stations"),
    }

    for key, (fname, label) in specs.items():
        path = os.path.join(data_dir, fname)
        if os.path.exists(path):
            df = pd.read_csv(path)
            # normalise column names
            df.columns = [c.lower().strip() for c in df.columns]
            lat = next((c for c in df.columns if "lat" in c), None)
            lon = next((c for c in df.columns if "lon" in c or "lng" in c), None)
            if lat and lon:
                pts = df[[lat, lon]].dropna().values
                infra[key] = pts
                print(f"[Infra] Loaded {len(pts)} {label}")
            else:
                print(f"[Infra] ⚠️  {fname} missing lat/lon columns")
                infra[key] = np.empty((0, 2))
        else:
            print(f"[Infra] ⚠️  {fname} not found — using zeros for {label}")
            infra[key] = np.empty((0, 2))

    return infra


# ── Simulate BBMP data (until you get the real CSVs) ──────────────────────

def simulate_bbmp_data(wards_gdf: gpd.GeoDataFrame,
                       seed: int = 42) -> dict:
    """
    Generates plausible fake BBMP infrastructure points
    distributed across Bengaluru wards.
    Replace with real data when available.
    """
    rng = np.random.default_rng(seed)
    bounds = wards_gdf.total_bounds  # minx, miny, maxx, maxy

    def random_pts(n):
        lats = rng.uniform(bounds[1], bounds[3], n)
        lons = rng.uniform(bounds[0], bounds[2], n)
        return np.column_stack([lats, lons])

    # Realistic counts for Bengaluru
    return {
        "cctv":   random_pts(1200),   # ~1200 BBMP CCTV cameras
        "lights": random_pts(8000),   # street lights (sparse sample)
        "police": random_pts(110),    # ~110 police stations/outposts
    }


# ── Main scoring function ─────────────────────────────────────────────────

def compute_infra_scores(wards_gdf: gpd.GeoDataFrame,
                         data_dir: str,
                         use_simulated: bool = False) -> pd.DataFrame:
    """
    Compute infrastructure safety score for each ward.

    Parameters
    ----------
    wards_gdf      : GeoDataFrame with ward_name + geometry
    data_dir       : path to directory containing BBMP CSVs
    use_simulated  : if True, use synthetic data (dev mode)

    Returns
    -------
    DataFrame with columns: ward_name, infra_score,
                            cctv_score, light_score, police_score
    """
    # Ward centroids
    centroids = wards_gdf.copy()
    centroids["centroid"] = centroids.geometry.centroid
    centroids["lat"] = centroids["centroid"].y
    centroids["lon"] = centroids["centroid"].x
    query_pts = centroids[["lat", "lon"]].values

    # Load or simulate infra
    if use_simulated:
        print("[Infra] Using SIMULATED BBMP data — replace with real CSVs!")
        infra = simulate_bbmp_data(wards_gdf)
    else:
        infra = load_infra(data_dir)

    # Score each infra type independently
    # decay_m: distance in metres where contribution halves
    cctv_scores   = idw_score(query_pts, infra["cctv"],
                               k=5, power=2, decay_m=300)
    light_scores  = idw_score(query_pts, infra["lights"],
                               k=10, power=1.5, decay_m=150)
    police_scores = idw_score(query_pts, infra["police"],
                               k=3, power=2, decay_m=800)

    # Weighted combination (tune these weights based on domain knowledge)
    WEIGHTS = {"cctv": 0.35, "lights": 0.40, "police": 0.25}
    combined = (
        WEIGHTS["cctv"]   * cctv_scores   +
        WEIGHTS["lights"] * light_scores  +
        WEIGHTS["police"] * police_scores
    )

    # Percentile rank within Bengaluru context
    combined_ranked = pd.Series(combined).rank(pct=True).values

    result = pd.DataFrame({
        "ward_name":    centroids["ward_name"].values,
        "infra_score":  combined_ranked,
        "cctv_score":   cctv_scores,
        "light_score":  light_scores,
        "police_score": police_scores,
    })

    print(f"[Infra] Score range: {combined_ranked.min():.3f} – "
          f"{combined_ranked.max():.3f}, mean={combined_ranked.mean():.3f}")

    return result
