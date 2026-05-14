"""
SafeRoute.ai — Live Data Connectors
=====================================
Real connectors for live data feeds.

Overpass API note:
  OSM surveillance/lamp coverage in Bengaluru is sparse.
  We query broader categories that ARE well-mapped:
    - amenity=police, amenity=hospital, amenity=bank (footfall proxies)
    - highway=street_lamp (some coverage)
    - man_made=surveillance
  These give real spatial signal even if not exhaustive.

For IoT pings: simulate until Kafka is wired in.
"""

import requests
import pandas as pd
import numpy as np
from typing import Optional
from datetime import datetime


# ── Overpass ───────────────────────────────────────────────────────────────

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
BLR_BBOX     = (12.83, 77.46, 13.14, 77.78)   # south, west, north, east


def fetch_overpass_infrastructure(
        bbox: tuple = BLR_BBOX,
        timeout: int = 45) -> dict:
    """
    Pull real infrastructure from OSM Overpass API.

    What we query (all well-mapped in Bengaluru):
      - man_made=surveillance  → CCTV cameras
      - highway=street_lamp    → street lights
      - amenity=police         → police stations / outposts

    Returns dict: {cctv, lights, police} each a DataFrame
    with latitude, longitude columns.
    Falls back to empty DataFrames on any error.
    """
    s, w, n, e = bbox

    # Single combined query — one round-trip is faster than three
    query = f"""
[out:json][timeout:{timeout}];
(
  node["man_made"="surveillance"]({s},{w},{n},{e});
  node["highway"="street_lamp"]({s},{w},{n},{e});
  way["highway"="street_lamp"]({s},{w},{n},{e});
  node["amenity"="police"]({s},{w},{n},{e});
  way["amenity"="police"]({s},{w},{n},{e});
);
out center;
"""

    print("[Live] Querying Overpass API for Bengaluru infrastructure...")
    try:
        resp = requests.post(
            OVERPASS_URL,
            data={"data": query},
            timeout=timeout,
            headers={"User-Agent": "SafeRoute.ai/1.0 (safety-research)"}
        )
        resp.raise_for_status()
        elements = resp.json().get("elements", [])
    except requests.exceptions.Timeout:
        print("[Live] Overpass timeout — returning empty infra")
        elements = []
    except Exception as ex:
        print(f"[Live] Overpass error: {ex}")
        elements = []

    cctv, lights, police = [], [], []

    for el in elements:
        lat = el.get("lat") or (el.get("center") or {}).get("lat")
        lon = el.get("lon") or (el.get("center") or {}).get("lon")
        if not lat or not lon:
            continue
        tags = el.get("tags", {})
        pt   = {"latitude": float(lat), "longitude": float(lon)}

        mm = tags.get("man_made", "")
        hw = tags.get("highway",  "")
        am = tags.get("amenity",  "")

        if mm == "surveillance":  cctv.append(pt)
        elif hw == "street_lamp": lights.append(pt)
        elif am == "police":      police.append(pt)

    def _df(rows):
        return pd.DataFrame(rows) if rows \
               else pd.DataFrame(columns=["latitude", "longitude"])

    result = {"cctv": _df(cctv), "lights": _df(lights), "police": _df(police)}

    print(f"[Live] Overpass results → "
          f"CCTV: {len(cctv)} | lights: {len(lights)} | police: {len(police)}")

    return result


def check_overpass() -> bool:
    """Quick connectivity check — returns True if Overpass is reachable."""
    try:
        r = requests.head(
            "https://overpass-api.de/api/interpreter",
            timeout=4,
            headers={"User-Agent": "SafeRoute.ai/1.0"}
        )
        return r.status_code < 500
    except Exception:
        return False


# ── Simulated IoT GPS pings ────────────────────────────────────────────────

def generate_simulated_pings(
        bounds: tuple,
        n_devices: int = 600,
        male_ratio: float = 0.55,
        hour: Optional[int] = None) -> pd.DataFrame:
    """
    Generate fresh GPS pings every call (no fixed seed = movement).

    Key fix vs previous version:
      - Clustering happens regardless of night_only flag here.
        The DBSCAN caller decides whether to filter by hour.
      - More devices + tighter clusters = more realistic cluster detection.
    """
    if hour is None:
        hour = datetime.now().hour

    rng = np.random.default_rng()   # truly random each call
    minx, miny, maxx, maxy = bounds

    # Night = denser clusters (people at dhabas, roads, etc)
    is_night       = (hour >= 21) or (hour <= 5)
    cluster_str    = 0.80 if is_night else 0.55   # raised from 0.30 → more clusters
    n_hotspots     = int(rng.integers(8, 20))      # more hotspots
    hotspot_lats   = rng.uniform(miny + 0.02, maxy - 0.02, n_hotspots)
    hotspot_lons   = rng.uniform(minx + 0.02, maxx - 0.02, n_hotspots)

    rows = []
    for i in range(n_devices):
        gender = "male" if rng.random() < male_ratio else "female"
        if rng.random() < cluster_str and gender == "male":
            h   = rng.integers(0, n_hotspots)
            lat = float(np.clip(rng.normal(hotspot_lats[h], 0.0015), miny, maxy))
            lon = float(np.clip(rng.normal(hotspot_lons[h], 0.0015), minx, maxx))
        else:
            lat = float(rng.uniform(miny, maxy))
            lon = float(rng.uniform(minx, maxx))

        rows.append({
            "device_id": f"sim_{i:04d}",
            "gender":    gender,
            "latitude":  lat,
            "longitude": lon,
            "hour":      hour,
            "timestamp": pd.Timestamp.now(),
            "source":    "simulated",
        })

    return pd.DataFrame(rows)


# ── IoT stream reader ──────────────────────────────────────────────────────

def read_iot_stream(
        source: str = "simulate",
        bounds: Optional[tuple] = None,
        hour: Optional[int] = None,
        kafka_topic:  str = "iot.device.pings",
        kafka_broker: str = "localhost:9092") -> pd.DataFrame:
    """
    Read the latest IoT GPS pings.

    source : "simulate" | "kafka" | "redis"
    bounds : (minx, miny, maxx, maxy) — required for simulate
    """
    if source == "simulate":
        if bounds is None:
            raise ValueError("bounds=(minx,miny,maxx,maxy) required for simulate")
        return generate_simulated_pings(bounds, hour=hour)

    elif source == "kafka":
        # TODO — uncomment when docker-compose up
        # from kafka import KafkaConsumer
        # import json
        # consumer = KafkaConsumer(
        #     kafka_topic,
        #     bootstrap_servers=kafka_broker,
        #     auto_offset_reset="latest",
        #     consumer_timeout_ms=5000,
        #     value_deserializer=lambda m: json.loads(m.decode())
        # )
        # rows = [msg.value for msg in consumer]
        # consumer.close()
        # return pd.DataFrame(rows)
        raise NotImplementedError("Kafka not running — start with docker-compose up")

    elif source == "redis":
        # TODO — uncomment when docker-compose up
        # import redis, json
        # r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        # raw = r.lrange("saferoute:pings:latest", 0, -1)
        # return pd.DataFrame([json.loads(x) for x in raw])
        raise NotImplementedError("Redis not running — start with docker-compose up")

    raise ValueError(f"Unknown source: {source!r}")


# ── Connection health ──────────────────────────────────────────────────────

def check_connections() -> dict:
    status = {
        "kafka":    False,
        "redis":    False,
        "overpass": check_overpass(),
        "bbmp_api": False,
    }
    try:
        from kafka import KafkaAdminClient
        a = KafkaAdminClient(bootstrap_servers="localhost:9092",
                             request_timeout_ms=2000)
        a.close()
        status["kafka"] = True
    except Exception:
        pass

    try:
        import redis
        redis.Redis(host="localhost", port=6379,
                    socket_timeout=2).ping()
        status["redis"] = True
    except Exception:
        pass

    return status