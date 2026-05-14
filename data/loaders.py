"""
SafeRoute.ai — Data Loaders
============================
Pure data-loading functions. No Streamlit imports here — keeps
the module testable in isolation and reusable by future pipelines.

Caching (@st.cache_data) is applied at the call-site in app.py.
"""

import os
import re
import pandas as pd
import geopandas as gpd
import numpy as np


# ── FIR / Crime data ───────────────────────────────────────────────────────

def load_fir(data_path: str) -> pd.DataFrame:
    """
    Load Karnataka FIR CSV, auto-detect lat/lon and date columns,
    filter to Bengaluru bounding box.

    Returns a clean DataFrame ready for spatial join.
    """
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"FIR CSV not found: {data_path}")

    df = pd.read_csv(data_path)

    # ── auto-detect lat/lon ────────────────────────────────────────────────
    lat_col = next((c for c in df.columns if c.lower() in
                    ("latitude", "lat")), None)
    lon_col = next((c for c in df.columns if c.lower() in
                    ("longitude", "lon", "long")), None)

    if not lat_col or not lon_col:
        raise ValueError(
            f"No lat/lon columns found in FIR CSV. "
            f"Columns present: {list(df.columns)}"
        )

    df = df.rename(columns={lat_col: "Latitude", lon_col: "Longitude"})
    df = df.dropna(subset=["Latitude", "Longitude"])

    # ── auto-detect date ───────────────────────────────────────────────────
    yr  = next((c for c in df.columns if "year"  in c.lower()), None)
    mo  = next((c for c in df.columns if "month" in c.lower()), None)
    day = next((c for c in df.columns
                if c.lower() in ("fir_day", "day", "date_day")), None)

    if yr and mo and day:
        df["date"] = pd.to_datetime(
            df[yr].astype(str) + "-" +
            df[mo].astype(str) + "-" +
            df[day].astype(str),
            errors="coerce"
        )
    else:
        dc = next((c for c in df.columns if "date" in c.lower()), None)
        df["date"] = pd.to_datetime(df[dc], errors="coerce") if dc else pd.NaT

    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"]       = df["date"].dt.month

    # ── filter to Bengaluru bbox ───────────────────────────────────────────
    df = df[
        (df["Latitude"]  >= 12.8) & (df["Latitude"]  <= 13.2) &
        (df["Longitude"] >= 77.4) & (df["Longitude"] <= 77.8)
    ].copy()

    print(f"[Loader] FIR data: {len(df):,} rows after Bengaluru filter")
    return df.reset_index(drop=True)


# ── Ward boundaries ────────────────────────────────────────────────────────

def load_wards(ward_path: str) -> gpd.GeoDataFrame:
    """
    Load Bengaluru ward KML, extract English ward names from
    ExtendedData (which GeoPandas silently ignores).

    Returns GeoDataFrame with columns: ward_name, geometry (EPSG:4326).
    """
    if not os.path.exists(ward_path):
        raise FileNotFoundError(f"Ward KML not found: {ward_path}")

    from lxml import etree

    tree = etree.parse(ward_path)
    root = tree.getroot()
    ns   = "http://www.opengis.net/kml/2.2"

    def find_all(node, tag):
        r = node.findall(f".//{{{ns}}}{tag}")
        return r if r else node.findall(f".//{tag}")

    placemarks = find_all(root, "Placemark")
    name_map   = {}

    for i, pm in enumerate(placemarks):
        name = None
        # Priority 1: name_en field
        for sd in find_all(pm, "SimpleData"):
            if sd.get("name") == "name_en" and sd.text and sd.text.strip():
                name = sd.text.strip()
                break
        # Priority 2: proposed_ward_name_en (strip numeric prefix like "16-")
        if not name:
            for sd in find_all(pm, "SimpleData"):
                if sd.get("name") == "proposed_ward_name_en" and sd.text:
                    name = re.sub(r"^\d+[-.\s]+", "", sd.text.strip())
                    break
        name_map[i] = name or f"Ward-{i}"

    # Load geometry via GeoPandas
    try:
        wards = gpd.read_file(ward_path, driver="KML")
    except Exception:
        wards = gpd.read_file(ward_path)

    wards["ward_name"] = [name_map.get(i, f"Ward-{i}")
                          for i in range(len(wards))]
    wards = wards[wards.geometry.notnull()].copy()

    named = (~wards["ward_name"].str.match(r"^Ward-\d+$")).sum()
    print(f"[Loader] Wards: {len(wards)} total, "
          f"{named} with real English names")

    return wards[["ward_name", "geometry"]].to_crs("EPSG:4326")


# ── Spatial join ───────────────────────────────────────────────────────────

def spatial_join(df_fir: pd.DataFrame,
                 wards_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Attach ward_name to each FIR point via spatial join.

    Returns GeoDataFrame with ward_name column added.
    Drops points that don't fall inside any ward polygon.
    """
    gdf = gpd.GeoDataFrame(
        df_fir,
        geometry=gpd.points_from_xy(df_fir["Longitude"], df_fir["Latitude"]),
        crs="EPSG:4326"
    )

    joined = gpd.sjoin(
        gdf,
        wards_gdf.to_crs("EPSG:4326"),
        how="inner",
        predicate="within"
    )
    joined = joined.reset_index(drop=True)

    print(f"[Loader] Spatial join: {len(df_fir):,} FIRs → "
          f"{len(joined):,} matched | "
          f"{joined['ward_name'].nunique()} unique wards")

    return joined


# ── Crime type breakdown ───────────────────────────────────────────────────

def ward_crime_breakdown(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    """
    Returns per-ward crime type counts for the drill-down table.
    Handles missing or NaN crime column gracefully.
    """
    crime_col = next((c for c in gdf.columns if c.lower() in
                      ("crimegroup_name", "crime_group_name",
                       "crimehead_name")), None)

    if not crime_col:
        return pd.DataFrame(columns=["ward_name", "CrimeGroup_Name", "count"])

    clean = gdf.dropna(subset=[crime_col])
    breakdown = (
        clean.groupby(["ward_name", crime_col])
             .size()
             .reset_index(name="count")
             .rename(columns={crime_col: "CrimeGroup_Name"})
    )
    return breakdown
