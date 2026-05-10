"""
SafeRoute.ai — Layer 3: DBSCAN Live Threat Detection
=====================================================
Real-time male-concentration clustering from IoT GPS pings.

How it works:
1. Receive GPS pings from registered IoT devices with gender tag
2. Filter to male devices active during night hours (9pm–5am)
3. Run DBSCAN to find dense male clusters
4. For each ward/route segment, compute threat score based on
   proximity and density of nearby clusters

Runs every 60 seconds in production (Redis caches results).
For now: simulates realistic IoT data for development.
"""

import numpy as np
import pandas as pd
import geopandas as gpd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from shapely.geometry import Point
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")


# ── Simulate IoT data (replace with real stream in production) ─────────────

def simulate_iot_pings(wards_gdf: gpd.GeoDataFrame,
                       n_devices: int = 500,
                       male_ratio: float = 0.55,
                       hour: int | None = None,
                       seed: int | None = None) -> pd.DataFrame:
    """
    Simulate GPS pings from registered IoT devices in Bengaluru.
    In production, replace this with your Kafka/MQTT stream reader.

    Parameters
    ----------
    wards_gdf   : ward geometries for spatial bounds
    n_devices   : total active devices to simulate
    male_ratio  : fraction of male-tagged devices
    hour        : hour of day (0–23), defaults to current hour
    seed        : random seed (None = truly random each call)
    """
    if hour is None:
        hour = datetime.now().hour

    rng = np.random.default_rng(seed)
    bounds = wards_gdf.total_bounds  # minx, miny, maxx, maxy

    # Night hours: more clustering (people congregate at dhabas, roads, etc.)
    is_night = (hour >= 21) or (hour <= 5)
    cluster_strength = 0.7 if is_night else 0.3

    pings = []
    # Create some hotspot cluster centres (simulating known congregation spots)
    n_hotspots = rng.integers(5, 15)
    hotspot_lats = rng.uniform(bounds[1] + 0.02, bounds[3] - 0.02, n_hotspots)
    hotspot_lons = rng.uniform(bounds[0] + 0.02, bounds[2] - 0.02, n_hotspots)

    for i in range(n_devices):
        gender = "male" if rng.random() < male_ratio else "female"

        # Cluster some devices around hotspots, scatter the rest
        if rng.random() < cluster_strength and gender == "male":
            # Clustered around a hotspot (sigma ~200m in degrees)
            hspot = rng.integers(0, n_hotspots)
            lat = rng.normal(hotspot_lats[hspot], 0.002)
            lon = rng.normal(hotspot_lons[hspot], 0.002)
        else:
            # Uniformly distributed
            lat = rng.uniform(bounds[1], bounds[3])
            lon = rng.uniform(bounds[0], bounds[2])

        pings.append({
            "device_id": f"device_{i:04d}",
            "gender":    gender,
            "latitude":  float(np.clip(lat, bounds[1], bounds[3])),
            "longitude": float(np.clip(lon, bounds[0], bounds[2])),
            "hour":      hour,
            "timestamp": pd.Timestamp.now(),
        })

    return pd.DataFrame(pings)


# ── DBSCAN clustering ──────────────────────────────────────────────────────

def detect_male_clusters(pings_df: pd.DataFrame,
                         night_only: bool = True,
                         eps_m: float = 200.0,
                         min_samples: int = 8) -> pd.DataFrame:
    """
    Run DBSCAN on male device locations to find dense clusters.

    Parameters
    ----------
    pings_df    : output of simulate_iot_pings or real stream
    night_only  : only flag clusters during night hours (21-05)
    eps_m       : cluster radius in metres
    min_samples : minimum devices to form a cluster

    Returns
    -------
    clusters_df : DataFrame with cluster_id, centroid lat/lon,
                  size, density, threat_level
    """
    df = pings_df.copy()

    # Filter to male devices
    male = df[df["gender"] == "male"].copy()

    # Optionally restrict to night hours
    if night_only:
        male = male[(male["hour"] >= 21) | (male["hour"] <= 5)]

    if len(male) < min_samples:
        return pd.DataFrame(columns=[
            "cluster_id", "centroid_lat", "centroid_lon",
            "size", "density_score", "threat_level"
        ])

    # Convert lat/lon to metres for DBSCAN (haversine approx)
    lat_m = male["latitude"].values  * 111_000
    lon_m = male["longitude"].values * 111_000 * np.cos(np.radians(12.97))
    coords_m = np.column_stack([lat_m, lon_m])

    # DBSCAN — eps in metres, metric='euclidean' (already in metres)
    eps_deg = eps_m / 111_000
    db = DBSCAN(eps=eps_m, min_samples=min_samples, metric="euclidean")
    labels = db.fit_predict(coords_m)

    male = male.copy()
    male["cluster_id"] = labels

    # Summarise each cluster (ignore noise label -1)
    valid = male[male["cluster_id"] >= 0]
    if valid.empty:
        return pd.DataFrame(columns=[
            "cluster_id", "centroid_lat", "centroid_lon",
            "size", "density_score", "threat_level"
        ])

    clusters = (valid.groupby("cluster_id")
                     .agg(
                         centroid_lat=("latitude",  "mean"),
                         centroid_lon=("longitude", "mean"),
                         size=("device_id", "count"),
                     )
                     .reset_index())

    # Density score: normalised cluster size → threat contribution
    clusters["density_score"] = (
        np.log1p(clusters["size"]) /
        np.log1p(clusters["size"].max() + 1)
    )

    # Threat level labels
    def label(s):
        if s > 0.7:   return "critical"
        elif s > 0.4: return "high"
        elif s > 0.2: return "moderate"
        else:         return "low"

    clusters["threat_level"] = clusters["density_score"].apply(label)

    print(f"[DBSCAN] Found {len(clusters)} male cluster(s) "
          f"from {len(male)} male pings")

    return clusters.reset_index(drop=True)


# ── Ward-level threat score ────────────────────────────────────────────────

def compute_live_threat_scores(wards_gdf: gpd.GeoDataFrame,
                                clusters_df: pd.DataFrame,
                                influence_radius_m: float = 600.0) -> pd.DataFrame:
    """
    For each ward, compute a live threat score based on proximity
    and density of male clusters within influence_radius_m.

    Parameters
    ----------
    wards_gdf          : ward geometries
    clusters_df        : output of detect_male_clusters
    influence_radius_m : radius within which a cluster affects a ward

    Returns
    -------
    DataFrame: ward_name, live_threat_score (0-1, percentile-ranked),
               nearby_clusters, max_cluster_size
    """
    centroids = wards_gdf.copy()
    centroids["c_lat"] = centroids.geometry.centroid.y
    centroids["c_lon"] = centroids.geometry.centroid.x

    results = []

    if clusters_df.empty:
        for _, row in centroids.iterrows():
            results.append({
                "ward_name":         row["ward_name"],
                "live_threat_score": 0.0,
                "nearby_clusters":   0,
                "max_cluster_size":  0,
            })
        return pd.DataFrame(results)

    # Cluster centroids in metres
    cl_lat_m = clusters_df["centroid_lat"].values * 111_000
    cl_lon_m = clusters_df["centroid_lon"].values * 111_000 * np.cos(np.radians(12.97))
    cl_pts   = np.column_stack([cl_lat_m, cl_lon_m])

    for _, ward in centroids.iterrows():
        w_lat_m = ward["c_lat"] * 111_000
        w_lon_m = ward["c_lon"] * 111_000 * np.cos(np.radians(12.97))
        w_pt    = np.array([w_lat_m, w_lon_m])

        dists = np.linalg.norm(cl_pts - w_pt, axis=1)
        nearby_mask = dists < influence_radius_m
        nearby = clusters_df[nearby_mask]

        if nearby.empty:
            threat = 0.0
            max_size = 0
            n_clusters = 0
        else:
            # Threat = sum of (density_score / distance) for nearby clusters
            # Closer + denser = more threatening
            d_near = dists[nearby_mask] + 1.0  # avoid div/0
            threat = float(
                (nearby["density_score"].values / d_near).sum() *
                influence_radius_m  # normalise by radius
            )
            threat = min(threat, 1.0)
            max_size   = int(nearby["size"].max())
            n_clusters = len(nearby)

        results.append({
            "ward_name":         ward["ward_name"],
            "live_threat_score": threat,
            "nearby_clusters":   n_clusters,
            "max_cluster_size":  max_size,
        })

    result_df = pd.DataFrame(results)

    # Percentile rank (only if there's variance)
    if result_df["live_threat_score"].std() > 1e-6:
        result_df["live_threat_score"] = (
            result_df["live_threat_score"].rank(pct=True)
        )

    return result_df
