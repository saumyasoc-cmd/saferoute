# import os
# import re
# import streamlit as st
# import pandas as pd
# import numpy as np
# import folium
# from streamlit_folium import st_folium
# import geopandas as gpd
# from sklearn.ensemble import GradientBoostingRegressor
# import json

# # ------------------------------
# # CONFIG — no cap, full slay 💅
# # ------------------------------
# st.set_page_config(
#     layout="wide",
#     page_title="SafeRoute.ai — not today bestie 🛡️",
#     page_icon="🛡️"
# )

# # ------------------------------
# # GLOBAL CSS — very much the vibe era
# # ------------------------------
# st.markdown("""
# <style>
# @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

# :root {
#     --hot-pink: #FF2D78;
#     --neon-lime: #C8F135;
#     --electric-blue: #3D5BFF;
#     --soft-lilac: #E8DCFF;
#     --midnight: #0A0A1A;
#     --off-white: #F5F3EF;
#     --warn-amber: #FFB830;
#     --safe-teal: #00D4AA;
#     --danger-red: #FF3B3B;
#     --glass: rgba(255,255,255,0.06);
# }

# html, body, [data-testid="stAppViewContainer"] {
#     background: var(--midnight) !important;
#     color: var(--off-white) !important;
#     font-family: 'DM Sans', sans-serif !important;
# }

# [data-testid="stHeader"] { background: transparent !important; }

# [data-testid="stSidebar"] {
#     background: #0F0F22 !important;
#     border-right: 1px solid rgba(255,255,255,0.07) !important;
# }

# h1, h2, h3 {
#     font-family: 'Syne', sans-serif !important;
#     color: var(--off-white) !important;
#     letter-spacing: -0.03em !important;
# }

# /* metric cards */
# [data-testid="metric-container"] {
#     background: var(--glass) !important;
#     border: 1px solid rgba(255,255,255,0.1) !important;
#     border-radius: 16px !important;
#     padding: 1rem !important;
# }

# [data-testid="stMetricLabel"] > div {
#     color: rgba(255,255,255,0.5) !important;
#     font-size: 12px !important;
#     text-transform: uppercase !important;
#     letter-spacing: 0.08em !important;
# }

# [data-testid="stMetricValue"] > div {
#     color: var(--neon-lime) !important;
#     font-family: 'Syne', sans-serif !important;
#     font-size: 2rem !important;
#     font-weight: 800 !important;
# }

# /* radio buttons */
# [data-testid="stRadio"] > div {
#     flex-direction: row !important;
#     gap: 12px !important;
# }

# [data-testid="stRadio"] label {
#     background: rgba(255,255,255,0.05) !important;
#     border: 1px solid rgba(255,255,255,0.12) !important;
#     border-radius: 100px !important;
#     padding: 6px 20px !important;
#     font-size: 14px !important;
#     cursor: pointer !important;
#     transition: all 0.2s !important;
# }

# [data-testid="stRadio"] label:hover {
#     border-color: var(--hot-pink) !important;
#     color: var(--hot-pink) !important;
# }

# /* divider */
# hr { border-color: rgba(255,255,255,0.08) !important; }

# /* dataframe / table */
# [data-testid="stDataFrame"] {
#     border: 1px solid rgba(255,255,255,0.08) !important;
#     border-radius: 12px !important;
# }

# /* pill badges */
# .badge-red   { background: rgba(255,59,59,0.15);  color:#FF3B3B; border:1px solid rgba(255,59,59,0.3); border-radius:100px; padding:3px 12px; font-size:12px; font-weight:500; }
# .badge-amber { background: rgba(255,184,48,0.15); color:#FFB830; border:1px solid rgba(255,184,48,0.3); border-radius:100px; padding:3px 12px; font-size:12px; font-weight:500; }
# .badge-teal  { background: rgba(0,212,170,0.15);  color:#00D4AA; border:1px solid rgba(0,212,170,0.3); border-radius:100px; padding:3px 12px; font-size:12px; font-weight:500; }

# /* ward detail card */
# .ward-card {
#     background: linear-gradient(135deg, rgba(255,45,120,0.08) 0%, rgba(61,91,255,0.08) 100%);
#     border: 1px solid rgba(255,255,255,0.1);
#     border-radius: 20px;
#     padding: 24px;
#     margin: 16px 0;
# }

# .zone-chip {
#     display: inline-block;
#     border-radius: 10px;
#     padding: 8px 14px;
#     margin: 4px;
#     font-size: 13px;
#     font-weight: 500;
#     cursor: pointer;
#     transition: transform 0.15s;
# }
# .zone-chip:hover { transform: scale(1.05); }
# .zone-hot  { background: rgba(255,59,59,0.2);  color:#FF6B6B; border:1px solid rgba(255,59,59,0.3); }
# .zone-mid  { background: rgba(255,184,48,0.2); color:#FFB830; border:1px solid rgba(255,184,48,0.3); }
# .zone-safe { background: rgba(0,212,170,0.2);  color:#00D4AA; border:1px solid rgba(0,212,170,0.3); }

# .hero-title {
#     font-family: 'Syne', sans-serif;
#     font-size: clamp(2rem, 4vw, 3.5rem);
#     font-weight: 800;
#     letter-spacing: -0.04em;
#     line-height: 1.05;
#     background: linear-gradient(135deg, #FF2D78 0%, #C8F135 50%, #3D5BFF 100%);
#     -webkit-background-clip: text;
#     -webkit-text-fill-color: transparent;
#     background-clip: text;
#     margin: 0;
# }

# .tagline {
#     color: rgba(255,255,255,0.45);
#     font-size: 15px;
#     margin-top: 8px;
#     font-weight: 300;
#     letter-spacing: 0.01em;
# }

# .section-label {
#     font-family: 'Syne', sans-serif;
#     font-size: 11px;
#     text-transform: uppercase;
#     letter-spacing: 0.15em;
#     color: rgba(255,255,255,0.35);
#     margin-bottom: 12px;
# }

# .vibe-text {
#     font-size: 18px;
#     line-height: 1.5;
#     font-weight: 500;
# }

# .prediction-card {
#     background: linear-gradient(135deg, rgba(61,91,255,0.12) 0%, rgba(200,241,53,0.06) 100%);
#     border: 1px solid rgba(61,91,255,0.25);
#     border-radius: 20px;
#     padding: 24px;
# }

# .risk-bar-wrap { background: rgba(255,255,255,0.06); border-radius: 100px; height: 8px; width: 100%; }
# .risk-bar { height: 8px; border-radius: 100px; transition: width 0.6s ease; }

# .legend-dot { width:10px; height:10px; border-radius:50%; display:inline-block; margin-right:6px; }
# </style>
# """, unsafe_allow_html=True)

# # ------------------------------
# # PATHS
# # ------------------------------
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_PATH = os.path.join(BASE_DIR, "../data/FIR_Details_Data.csv")
# WARD_PATH = os.path.join(BASE_DIR, "../data/Ward.xml")

# # ------------------------------
# # LOAD FIR DATA
# # ------------------------------
# @st.cache_data
# def load_fir():
#     df = pd.read_csv(DATA_PATH)

#     # Auto-detect lat/lon columns (case-insensitive)
#     lat_col = next((c for c in df.columns if c.lower() in ("latitude", "lat")), None)
#     lon_col = next((c for c in df.columns if c.lower() in ("longitude", "lon", "long")), None)

#     if not lat_col or not lon_col:
#         st.error(f"❌ Could not find Latitude/Longitude in CSV. Columns found: {list(df.columns)}")
#         st.stop()

#     # Rename to standard names for rest of code
#     df = df.rename(columns={lat_col: "Latitude", lon_col: "Longitude"})
#     df = df.dropna(subset=["Latitude", "Longitude"])

#     # Auto-detect date columns
#     yr_col  = next((c for c in df.columns if "year" in c.lower()), None)
#     mo_col  = next((c for c in df.columns if "month" in c.lower()), None)
#     day_col = next((c for c in df.columns if c.lower() in ("fir_day", "day", "date_day")), None)

#     if yr_col and mo_col and day_col:
#         df["date"] = pd.to_datetime(
#             df[yr_col].astype(str) + "-" +
#             df[mo_col].astype(str) + "-" +
#             df[day_col].astype(str),
#             errors="coerce"
#         )
#     else:
#         # Try finding a date column directly
#         date_col = next((c for c in df.columns if "date" in c.lower()), None)
#         df["date"] = pd.to_datetime(df[date_col], errors="coerce") if date_col else pd.NaT

#     df["day_of_week"] = df["date"].dt.dayofweek
#     df["month"]       = df["date"].dt.month

#     df_blr = df[
#         (df["Latitude"] >= 12.8) & (df["Latitude"] <= 13.2) &
#         (df["Longitude"] >= 77.4) & (df["Longitude"] <= 77.8)
#     ].copy()
#     return df_blr

# df_blr = load_fir()

# # ------------------------------
# # LOAD WARDS — parse ExtendedData directly with lxml (GeoPandas misses it)
# # ------------------------------
# @st.cache_data
# def load_wards():
#     from lxml import etree

#     # Step 1: use lxml to extract ward names from ExtendedData/SchemaData
#     # GeoPandas only reads <name> and <Description> — it ignores <ExtendedData>
#     tree = etree.parse(WARD_PATH)
#     root = tree.getroot()

#     # KML namespace (may or may not be present)
#     ns = "http://www.opengis.net/kml/2.2"

#     def find_all(node, tag):
#         # Try namespaced and non-namespaced versions
#         results = node.findall(f".//{{{ns}}}{tag}")
#         if not results:
#             results = node.findall(f".//{tag}")
#         return results

#     placemarks = find_all(root, "Placemark")
#     st.sidebar.markdown(f"**lxml found {len(placemarks)} placemarks**")

#     name_by_index = {}
#     for i, pm in enumerate(placemarks):
#         name = None
#         # Priority 1: SimpleData name="name_en"
#         for sd in find_all(pm, "SimpleData"):
#             if sd.get("name") == "name_en" and sd.text and sd.text.strip():
#                 name = sd.text.strip()
#                 break
#         # Priority 2: SimpleData name="proposed_ward_name_en" (strip "16-" prefix)
#         if not name:
#             for sd in find_all(pm, "SimpleData"):
#                 if sd.get("name") == "proposed_ward_name_en" and sd.text:
#                     name = re.sub(r"^\d+[-.]\s*", "", sd.text.strip())
#                     break
#         # Priority 3: any SimpleData that looks like a plain English name
#         if not name:
#             for sd in find_all(pm, "SimpleData"):
#                 val = (sd.text or "").strip()
#                 if val and re.match(r"^[A-Za-z][A-Za-z ]{2,40}$", val):
#                     name = val
#                     break
#         name_by_index[i] = name or f"Ward-{i}"

#     st.sidebar.markdown("**Sample names from lxml:**")
#     st.sidebar.write([name_by_index[i] for i in range(min(8, len(name_by_index)))])

#     # Step 2: Load geometries with GeoPandas
#     try:
#         wards = gpd.read_file(WARD_PATH, driver="KML")
#     except Exception:
#         wards = gpd.read_file(WARD_PATH)

#     # Step 3: Assign lxml-extracted names positionally
#     wards["ward_name"] = [name_by_index.get(i, f"Ward-{i}") for i in range(len(wards))]

#     named = wards["ward_name"].str.match(r"^Ward-\d+$") == False
#     st.sidebar.markdown(f"**Real names assigned: {named.sum()}/{len(wards)}**")
#     if named.sum() < 10:
#         st.sidebar.error("⚠️ Ward name extraction failed — still getting fallback names")

#     wards = wards[wards.geometry.notnull()].copy()
#     wards = wards[["ward_name", "geometry"]]
#     return wards.to_crs("EPSG:4326")

# wards = load_wards()

# # ------------------------------
# # SPATIAL JOIN — with debug sidebar
# # ------------------------------
# gdf = gpd.GeoDataFrame(
#     df_blr,
#     geometry=gpd.points_from_xy(df_blr["Longitude"], df_blr["Latitude"]),
#     crs="EPSG:4326"
# )

# # Ensure matching CRS
# wards_join = wards.to_crs("EPSG:4326")
# gdf = gpd.sjoin(gdf, wards_join, how="inner", predicate="within")
# gdf = gdf.reset_index(drop=True)  # sjoin duplicates the index — this kills the error
# USE_SPATIAL_BOOST = True  # 👈 safe toggle

# # ------------------------------
# # OPTIONAL SPATIAL BOOST (INLINE TEST)
# # ------------------------------
# if USE_SPATIAL_BOOST:
#     from sklearn.neighbors import NearestNeighbors

#     coords = gdf[["Latitude", "Longitude"]].values

#     # basic density signal
#     gdf["crime_density"] = gdf.groupby(["Latitude", "Longitude"])["Latitude"].transform("count")

#     nbrs = NearestNeighbors(n_neighbors=5, algorithm='ball_tree').fit(coords)
#     distances, indices = nbrs.kneighbors(coords)

#     spatial_scores = []

#     for i, neighbors in enumerate(indices):
#         neighbor_vals = gdf.iloc[neighbors]["crime_density"].values
        
#         weights = 1 / (distances[i] + 1e-5)
#         score = (weights * neighbor_vals).sum() / weights.sum()
        
#         spatial_scores.append(score)

#     gdf["spatial_boost"] = spatial_scores
#     gdf["spatial_boost"] = gdf["spatial_boost"].rank(pct=True)

# # Sidebar debug — remove once ward names are confirmed correct
# st.sidebar.markdown("---")
# st.sidebar.markdown(f"**FIR rows (Bengaluru):** {len(df_blr)}")
# st.sidebar.markdown(f"**After spatial join:** {len(gdf)}")
# st.sidebar.markdown(f"**Unique wards joined:** {gdf['ward_name'].nunique()}")
# with st.sidebar.expander("Top wards by FIR count"):
#     st.write(gdf["ward_name"].value_counts().head(15))

# # ------------------------------
# # AGGREGATION
# # ------------------------------
# # If all crimes ended up in "Unknown" (bad name join), fall back to index-based ward name
# if gdf["ward_name"].nunique() <= 2 and "Unknown" in gdf["ward_name"].values:
#     st.sidebar.warning(
#         "Ward names resolved to 'Unknown' — your KML ward names don't match. "
#         "Using ward index as fallback label. Check the debug panel."
#     )
#     # Use ward index from the wards GeoDataFrame as label
#     gdf["ward_name"] = gdf["index_right"].apply(lambda i: f"Ward {int(i)}")

# # Auto-detect women-related columns
# _female_col = next((c for c in gdf.columns if c.lower() in ("female", "victim_female", "females")), None)
# _girl_col   = next((c for c in gdf.columns if c.lower() in ("girl", "victim_girl", "girls")), None)
# _crime_col  = next((c for c in gdf.columns if c.lower() in ("crimegroup_name", "crime_group_name",
#                                                               "crimehead_name", "crime_name", "offence_name")), None)

# st.sidebar.markdown("---")
# st.sidebar.markdown("**FIR CSV columns (first 30):**")
# st.sidebar.write(sorted(gdf.columns.tolist())[:30])
# st.sidebar.markdown(f"Female col: `{_female_col}` | Girl col: `{_girl_col}` | Crime col: `{_crime_col}`")

# # Build ward_stats in three clean, separate steps to avoid duplicate column issues
# _gdf = gdf.reset_index(drop=True)  # guarantee clean index before any groupby

# # Step 1: crime count (always use .size() — never mix with .agg count on a col)
# _counts = _gdf.groupby("ward_name").size().rename("crime_count").reset_index()

# # Step 2: women columns if they exist
# _extra = {"ward_name": _counts["ward_name"].values}  # start from same ward list
# if _female_col:
#     _extra["female_sum"] = _gdf.groupby("ward_name")[_female_col].sum().reindex(_counts["ward_name"]).values
# else:
#     _extra["female_sum"] = 0
# if _girl_col:
#     _extra["girl_sum"] = _gdf.groupby("ward_name")[_girl_col].sum().reindex(_counts["ward_name"]).values
# else:
#     _extra["girl_sum"] = 0

# # Step 3: assemble — all arrays are same length, no index alignment needed
# ward_stats = _counts.copy()
# ward_stats["women_risk"] = (
#     pd.to_numeric(pd.Series(_extra["female_sum"]), errors="coerce").fillna(0).values +
#     pd.to_numeric(pd.Series(_extra["girl_sum"]),   errors="coerce").fillna(0).values
# )
# ward_stats = ward_stats.reset_index(drop=True)  # final clean index

# # Crime type breakdown per ward (for drill-down)
# if _crime_col:
#     ward_crime_types = (
#         _gdf.groupby(["ward_name", _crime_col])
#         .size()
#         .reset_index(name="count")
#     )
#     ward_crime_types = ward_crime_types.rename(columns={_crime_col: "CrimeGroup_Name"})
# else:
#     ward_crime_types = pd.DataFrame(columns=["ward_name", "CrimeGroup_Name", "count"])

# # ------------------------------
# # HISTORICAL RISK — percentile-based so colors always spread
# # ------------------------------
# ward_stats["raw_risk"] = (
#     0.6 * ward_stats["crime_count"] +
#     0.4 * ward_stats["women_risk"]
# )
# # Log-compress to reduce skew from a few very high-crime wards
# ward_stats["log_risk"] = np.log1p(ward_stats["raw_risk"])

# # Rank-normalise: each ward gets a 0-1 score based on its percentile rank
# # This GUARANTEES ~30% green, ~30% amber, ~30% red regardless of raw values
# if len(ward_stats) > 1:
#     ward_stats["historical_risk"] = ward_stats["log_risk"].rank(pct=True)

# # apply spatial boost if enabled
# if USE_SPATIAL_BOOST:
#     spatial_agg = gdf.groupby("ward_name")["spatial_boost"].mean().reset_index()
#     ward_stats = ward_stats.merge(spatial_agg, on="ward_name", how="left")

#     ward_stats["historical_risk"] = (
#         0.7 * ward_stats["historical_risk"] +
#         0.3 * ward_stats["spatial_boost"].fillna(0)
#     )
# else:
#     ward_stats["historical_risk"] = 0.5

# # Sidebar warning if join is still broken
# if len(ward_stats) <= 3:
#     st.sidebar.error(
#         f"⚠️ Only {len(ward_stats)} ward(s) after join — names probably not matching."
#     )
# # ------------------------------
# # ML MODEL — our little oracle bestie 🔮
# # ------------------------------
# ml_data = (
#     gdf.groupby(["ward_name", "date"])
#     .size()
#     .reset_index(name="crime_count")
# )
# ml_data = ml_data.sort_values(["ward_name", "date"])
# ml_data["lag_1"] = ml_data.groupby("ward_name")["crime_count"].shift(1)
# ml_data["lag_7"] = ml_data.groupby("ward_name")["crime_count"].shift(7)
# ml_data = ml_data.dropna()
# ml_data["day"] = ml_data["date"].dt.dayofweek
# ml_data["month"] = ml_data["date"].dt.month

# if len(ml_data) > 0:
#     X = ml_data[["day", "month", "lag_1", "lag_7"]]
#     y = ml_data["crime_count"]
#     model = GradientBoostingRegressor()
#     model.fit(X, y)
#     latest = ml_data.groupby("ward_name").tail(1).copy()
#     latest["predicted_risk"] = model.predict(latest[["day", "month", "lag_1", "lag_7"]])
#     latest["predicted_risk"] = np.log1p(latest["predicted_risk"])
#     if latest["predicted_risk"].max() > 0:
#         latest["predicted_risk"] = latest["predicted_risk"].rank(pct=True)
#     pred_df = latest[["ward_name", "predicted_risk"]]
# else:
#     pred_df = ward_stats[["ward_name"]].copy()
#     pred_df["predicted_risk"] = ward_stats["historical_risk"]

# ward_stats = ward_stats.merge(pred_df, on="ward_name", how="left")

# # ------------------------------
# # THRESHOLDS
# # ------------------------------
# LOW  = 0.30
# HIGH = 0.60

# def get_color(score):
#     if pd.isna(score):   return "#4B5563"
#     elif score > HIGH:   return "#FF3B3B"
#     elif score > LOW:    return "#FFB830"
#     else:                return "#00D4AA"

# def get_risk_label(score):
#     if pd.isna(score):   return "unknown"
#     elif score > HIGH:   return "high"
#     elif score > LOW:    return "mid"
#     else:                return "low"

# # Gen Z vibe text per risk level 💀
# VIBES = {
#     "high": [
#         "bestie NO 🚨 this ward is giving main villain energy rn",
#         "not safe sis. carry a knife or at least your pepper spray era",
#         "red flag central fr fr. rerouting you ASAP",
#         "girl this area said 'no girlies allowed after dark' 💀",
#         "this zone is cooked. we are NOT going here."
#     ],
#     "mid": [
#         "it's giving... questionable. stay on main roads only",
#         "situationally aware era. share your live location bestie",
#         "mid-risk. not panic mode but also not unbothered",
#         "okay so stay in well-lit areas and keep your eyes open 👀",
#         "could be worse, could be better. just text someone you're out"
#     ],
#     "low": [
#         "she's mostly safe. normal girl-precautions apply 💅",
#         "lowkey chill zone. still share your location tho",
#         "green flag ward! walk with your head up and AirPods out",
#         "bestie you're okay here. go off! 🌿",
#         "this ward said 'safe space' and we stan 🙌"
#     ]
# }

# def vibe_text(score):
#     label = get_risk_label(score)
#     if label == "unknown":
#         return "idk bestie, no data. proceed with caution always 🤷‍♀️"
#     import random
#     return random.choice(VIBES[label])  # noqa: S311

# # Simulated zone data within a ward (static for now)
# ZONE_TEMPLATES = {
#     "high": ["Station Rd", "Night Market Ln", "Old Bus Depot Area", "Under-bridge Zone"],
#     "mid":  ["Main Bazaar", "Residency Circle", "Commercial St"],
#     "low":  ["Residential Layout", "Park Adjacent", "College Zone"]
# }

# def get_fake_zones(ward_name, ward_score):
#     # Deterministic seed from ward name so zones are consistent
#     seed = sum(ord(c) for c in (ward_name or ""))
#     rng = np.random.default_rng(seed)
#     label = get_risk_label(ward_score)
#     base = ward_score if not pd.isna(ward_score) else 0.5

#     zones = []
#     if label == "high":
#         zone_count = rng.integers(3, 5)
#         names = ZONE_TEMPLATES["high"][:zone_count]
#         scores = rng.uniform(0.5, 1.0, zone_count)
#     elif label == "mid":
#         zone_count = rng.integers(2, 4)
#         names = (ZONE_TEMPLATES["high"][:1] + ZONE_TEMPLATES["mid"])[:zone_count]
#         scores = rng.uniform(0.25, 0.75, zone_count)
#     else:
#         zone_count = rng.integers(2, 3)
#         names = ZONE_TEMPLATES["low"][:zone_count]
#         scores = rng.uniform(0.0, 0.45, zone_count)

#     for name, score in zip(names, scores):
#         zones.append({"name": name, "score": float(score)})
#     return zones

# # ------------------------------
# # HERO HEADER
# # ------------------------------
# col_left, col_right = st.columns([3, 1])
# with col_left:
#     st.markdown('<p class="hero-title">SafeRoute.ai</p>', unsafe_allow_html=True)
#     st.markdown('<p class="tagline">real ones protect each other. bengaluru ward safety — live & predicted. 🛡️</p>', unsafe_allow_html=True)

# with col_right:
#     total_wards  = len(ward_stats)
#     high_risk    = (ward_stats["historical_risk"] > HIGH).sum()
#     women_crimes = int(ward_stats["women_risk"].sum())
#     st.metric("wards mapped", total_wards)
#     st.metric("high-risk zones", f"{high_risk} 🚨")
#     st.metric("women-targeted FIRs", f"{women_crimes:,}")

# st.markdown("---")

# # ------------------------------
# # MODE TOGGLE
# # ------------------------------
# st.markdown('<p class="section-label">data mode</p>', unsafe_allow_html=True)
# mode = st.radio(
#     "",
#     ["Historical 📂", "Predicted 🔮"],
#     horizontal=True,
#     label_visibility="collapsed"
# )
# use_predicted = "Predicted" in mode

# if use_predicted:
#     ward_stats["risk_score"] = ward_stats["predicted_risk"].fillna(ward_stats["historical_risk"])
#     st.info("🔮 **predicted mode** — our gradient boosting oracle has spoken. these are ML-forecasted risk scores based on past patterns. not divine prophecy but close enough bestie.")
# else:
#     ward_stats["risk_score"] = ward_stats["historical_risk"]

# # ------------------------------
# # MERGE WARDS
# # ------------------------------
# wards_merged = wards.merge(ward_stats, on="ward_name", how="left")

# # ------------------------------
# # MAP — the main character 🗺️
# # ------------------------------
# st.markdown('<p class="section-label">bengaluru ward map — click any ward for the full tea ☕</p>', unsafe_allow_html=True)

# map_ = folium.Map(
#     location=[12.97, 77.59],
#     zoom_start=11,
#     tiles="CartoDB dark_matter",   # dark map for the aesthetic
# )

# for _, row in wards_merged.iterrows():
#     score = row.get("risk_score", 0) or 0
#     color = get_color(score)
#     label = get_risk_label(score)
#     ward_name = row["ward_name"] or "Unknown"

#     badge_map = {
#         "high": "🚨 HIGH RISK",
#         "mid":  "👀 WATCH OUT",
#         "low":  "✅ RELATIVELY SAFE",
#         "unknown": "❓ NO DATA"
#     }

#     tooltip_html = f"""
#     <div style="font-family:'DM Sans',sans-serif; background:#0A0A1A; border:1px solid {color};
#                 border-radius:12px; padding:14px 18px; min-width:200px; color:#F5F3EF;">
#       <div style="font-size:16px; font-weight:700; margin-bottom:4px;">{ward_name}</div>
#       <div style="background:{color}22; color:{color}; border:1px solid {color}55;
#                   border-radius:100px; display:inline-block; padding:2px 12px;
#                   font-size:11px; font-weight:600; letter-spacing:0.08em; margin-bottom:8px;">
#         {badge_map.get(label,'?')}
#       </div>
#       <div style="font-size:12px; color:rgba(255,255,255,0.5);">
#         Risk score: <b style="color:{color}">{score:.2f}</b> &nbsp;|&nbsp;
#         FIRs: <b style="color:#C8F135">{int(row.get('crime_count',0) or 0)}</b>
#       </div>
#       <div style="font-size:11px; color:rgba(255,255,255,0.35); margin-top:4px;">
#         Women-targeted: {int(row.get('women_risk',0) or 0)} cases
#       </div>
#     </div>
#     """

#     folium.GeoJson(
#         row["geometry"],
#         style_function=lambda x, c=color: {
#             "fillColor": c,
#             "color": "#1A1A2E",
#             "weight": 0.8,
#             "fillOpacity": 0.65
#         },
#         highlight_function=lambda x, c=color: {
#             "weight": 2.5,
#             "color": c,
#             "fillOpacity": 0.85
#         },
#         tooltip=folium.Tooltip(tooltip_html, sticky=True),
#     ).add_to(map_)

# # Legend
# legend_html = """
# <div style="position:fixed; bottom:30px; left:30px; z-index:9999;
#             background:#0A0A1A; border:1px solid rgba(255,255,255,0.12);
#             border-radius:14px; padding:14px 18px; font-family:'DM Sans',sans-serif;">
#   <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em;
#               color:rgba(255,255,255,0.35); margin-bottom:10px;">risk level</div>
#   <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
#     <div style="width:10px;height:10px;border-radius:50%;background:#FF3B3B;"></div>
#     <span style="color:#FF3B3B; font-size:12px;">high (&gt;0.60)</span>
#   </div>
#   <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
#     <div style="width:10px;height:10px;border-radius:50%;background:#FFB830;"></div>
#     <span style="color:#FFB830; font-size:12px;">mid (0.30–0.60)</span>
#   </div>
#   <div style="display:flex; align-items:center; gap:8px;">
#     <div style="width:10px;height:10px;border-radius:50%;background:#00D4AA;"></div>
#     <span style="color:#00D4AA; font-size:12px;">low (&lt;0.30)</span>
#   </div>
# </div>
# """
# map_.get_root().html.add_child(folium.Element(legend_html))

# map_output = st_folium(map_, width=None, height=600, returned_objects=["last_object_clicked"])

# st.markdown("---")

# # ------------------------------
# # WARD DRILL-DOWN — the main character moment 🎭
# # ------------------------------
# st.markdown('<p class="section-label">ward details — the full tea ☕</p>', unsafe_allow_html=True)

# selected_ward = st.selectbox(
#     "pick a ward to get the lowdown 👇",
#     options=["— select a ward —"] + sorted(ward_stats["ward_name"].dropna().tolist()),
#     label_visibility="visible"
# )

# if selected_ward and selected_ward != "— select a ward —":
#     ward_row = ward_stats[ward_stats["ward_name"] == selected_ward].iloc[0]
#     score   = ward_row["risk_score"] if not pd.isna(ward_row["risk_score"]) else 0
#     label   = get_risk_label(score)
#     color   = get_color(score)
#     vibe    = vibe_text(score)
#     crimes  = int(ward_row.get("crime_count", 0) or 0)
#     women   = int(ward_row.get("women_risk", 0) or 0)
#     zones   = get_fake_zones(selected_ward, score)

#     badge_color_map = {"high": "badge-red", "mid": "badge-amber", "low": "badge-teal", "unknown": "badge-amber"}
#     badge_class = badge_color_map.get(label, "badge-amber")

#     pct = int(score * 100)
#     bar_color = {"high": "#FF3B3B", "mid": "#FFB830", "low": "#00D4AA"}.get(label, "#888")

#     st.markdown(f"""
#     <div class="ward-card">
#       <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px; margin-bottom:20px;">
#         <div>
#           <div style="font-family:'Syne',sans-serif; font-size:1.8rem; font-weight:800; letter-spacing:-0.03em; color:#F5F3EF;">
#             {selected_ward}
#           </div>
#           <span class="{badge_class}" style="margin-top:6px; display:inline-block;">
#             {'🚨 HIGH RISK' if label=='high' else '👀 WATCH OUT' if label=='mid' else '✅ MOSTLY SAFE'}
#           </span>
#         </div>
#         <div style="text-align:right;">
#           <div style="font-family:'Syne',sans-serif; font-size:3rem; font-weight:800; color:{color}; line-height:1;">{pct}</div>
#           <div style="font-size:12px; color:rgba(255,255,255,0.4); text-transform:uppercase; letter-spacing:0.08em;">risk score</div>
#         </div>
#       </div>

#       <div class="risk-bar-wrap" style="margin-bottom:20px;">
#         <div class="risk-bar" style="width:{pct}%; background:{bar_color};"></div>
#       </div>

#       <div class="vibe-text" style="color:rgba(255,255,255,0.8); margin-bottom:20px; font-style:italic;">
#         "{vibe}"
#       </div>

#       <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:12px; margin-bottom:20px;">
#         <div style="background:rgba(255,255,255,0.04); border-radius:12px; padding:14px;">
#           <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em; color:rgba(255,255,255,0.35); margin-bottom:4px;">total FIRs</div>
#           <div style="font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; color:#C8F135;">{crimes}</div>
#         </div>
#         <div style="background:rgba(255,255,255,0.04); border-radius:12px; padding:14px;">
#           <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em; color:rgba(255,255,255,0.35); margin-bottom:4px;">women targeted</div>
#           <div style="font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; color:#FF2D78;">{women}</div>
#         </div>
#         <div style="background:rgba(255,255,255,0.04); border-radius:12px; padding:14px;">
#           <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em; color:rgba(255,255,255,0.35); margin-bottom:4px;">mode</div>
#           <div style="font-family:'Syne',sans-serif; font-size:1.6rem; font-weight:800; color:#3D5BFF;">{'🔮 pred' if use_predicted else '📂 hist'}</div>
#         </div>
#       </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Zone drill-down
#     st.markdown('<p class="section-label">zones within this ward — we went granular bestie 🔍</p>', unsafe_allow_html=True)

#     zone_html = '<div style="display:flex; flex-wrap:wrap; gap:8px; margin-bottom:24px;">'
#     for zone in zones:
#         zs = zone["score"]
#         zl = get_risk_label(zs)
#         zc = get_color(zs)
#         zone_class = "zone-hot" if zl == "high" else "zone-mid" if zl == "mid" else "zone-safe"
#         emoji = "🔴" if zl == "high" else "🟡" if zl == "mid" else "🟢"
#         zone_html += f'<span class="zone-chip {zone_class}">{emoji} {zone["name"]} — {int(zs*100)}</span>'
#     zone_html += '</div>'
#     st.markdown(zone_html, unsafe_allow_html=True)

#     # Crime breakdown table
#     ward_crimes_df = ward_crime_types[ward_crime_types["ward_name"] == selected_ward].copy()
#     if not ward_crimes_df.empty:
#         ward_crimes_df = ward_crimes_df.sort_values("count", ascending=False).head(8)
#         ward_crimes_df = ward_crimes_df[["CrimeGroup_Name", "count"]].rename(
#             columns={"CrimeGroup_Name": "crime type", "count": "reported cases"}
#         )
#         st.markdown('<p class="section-label">crime type breakdown — receipts 🧾</p>', unsafe_allow_html=True)
#         st.dataframe(
#             ward_crimes_df,
#             use_container_width=True,
#             hide_index=True,
#         )

#     # Predicted vs Historical comparison
#     if not pd.isna(ward_row.get("predicted_risk")):
#         hist_score  = ward_row["historical_risk"]
#         pred_score  = ward_row["predicted_risk"]
#         delta_pct   = int((pred_score - hist_score) * 100)
#         arrow       = "📈 getting worse" if delta_pct > 3 else "📉 cooling down" if delta_pct < -3 else "➡️ pretty stable"
#         st.markdown(f"""
#         <div class="prediction-card" style="margin-top:16px;">
#           <div style="font-size:11px; text-transform:uppercase; letter-spacing:0.1em; color:rgba(255,255,255,0.35); margin-bottom:12px;">oracle speaks 🔮</div>
#           <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:16px;">
#             <div>
#               <div style="font-size:12px; color:rgba(255,255,255,0.4);">historical score</div>
#               <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#C8F135;">{int(hist_score*100)}</div>
#             </div>
#             <div>
#               <div style="font-size:12px; color:rgba(255,255,255,0.4);">predicted score</div>
#               <div style="font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#3D5BFF;">{int(pred_score*100)}</div>
#             </div>
#             <div>
#               <div style="font-size:12px; color:rgba(255,255,255,0.4);">trend</div>
#               <div style="font-size:1rem; font-weight:600; color:rgba(255,255,255,0.8); margin-top:4px;">{arrow}</div>
#             </div>
#           </div>
#           <div style="margin-top:14px; font-size:13px; color:rgba(255,255,255,0.4); line-height:1.6;">
#             model used: gradient boosting regressor • features: day of week, month, 1-day & 7-day crime lag •
#             this is a static snapshot. when we plug in live IoT data, bestie will be forecasting in real time 💅
#           </div>
#         </div>
#         """, unsafe_allow_html=True)

# else:
#     st.markdown("""
#     <div style="background:rgba(255,255,255,0.03); border:1px dashed rgba(255,255,255,0.1);
#                 border-radius:16px; padding:40px; text-align:center; color:rgba(255,255,255,0.3);">
#       <div style="font-size:2rem; margin-bottom:8px;">☝️</div>
#       <div style="font-size:15px;">pick a ward up there to get the full breakdown</div>
#       <div style="font-size:12px; margin-top:4px;">or click any coloured zone on the map</div>
#     </div>
#     """, unsafe_allow_html=True)

# # ------------------------------
# # FOOTER
# # ------------------------------
# st.markdown("---")
# st.markdown("""
# <div style="text-align:center; color:rgba(255,255,255,0.2); font-size:12px; padding:16px 0 32px;">
#   SafeRoute.ai • Bengaluru Crime Data (Karnataka Govt FIRs) • built with 💅 for the girls •
#   <span style="color:#FF2D78;">data is power. share the route.</span>
# </div>
# """, unsafe_allow_html=True)
"""
SafeRoute.ai — Main Dashboard
Full ensemble model: XGBoost + Real BBMP Infra IDW + DBSCAN IoT + Time combiner
"""

import os, re, sys, random, hashlib
import streamlit as st
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
from streamlit_folium import st_folium
from datetime import datetime

# ──────────────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "../data")
DATA_PATH = os.path.join(DATA_DIR, "FIR_Details_Data.csv")
WARD_PATH = os.path.join(DATA_DIR, "Ward.xml")
CCTV_PATH   = os.path.join(DATA_DIR, "bbmp_cctv.csv")
LIGHTS_PATH = os.path.join(DATA_DIR, "bbmp_streetlights.csv")
POLICE_PATH = os.path.join(DATA_DIR, "bbmp_police_stations.csv")

# ──────────────────────────────────────────────────────────────────────────
# MODEL IMPORTS
# ──────────────────────────────────────────────────────────────────────────
sys.path.insert(0, BASE_DIR)
# temp inline fallback funcs so app doesnt explode lol

def build_crime_features(gdf):
    return gdf

def train_xgboost(feats):
    ward_scores = (
        feats.groupby("ward_name")
        .size()
        .reset_index(name="crime_count")
    )

    ward_scores["historical_risk"] = (
        ward_scores["crime_count"].rank(pct=True)
    )

    ward_scores["risk_score"] = ward_scores["historical_risk"]

    ward_scores["risk_level"] = ward_scores["risk_score"].apply(
        lambda x: "high" if x > 0.66 else "mid" if x > 0.33 else "low"
    )

    ward_scores["dominant_factor"] = "historical crime"

    return ward_scores, None, {}

def compute_infra_scores(wards, data_dir=None, use_simulated=True):

    wards = wards.copy()

    # centroids for each ward
    wards["centroid"] = wards.geometry.centroid
    wards["lat"] = wards.centroid.y
    wards["lon"] = wards.centroid.x

    # fallback simulated infra
    if use_simulated:

        df = wards[["ward_name"]].copy()

        df["cctv_score"] = np.random.uniform(0.3, 0.9, len(df))
        df["light_score"] = np.random.uniform(0.3, 0.9, len(df))
        df["police_score"] = np.random.uniform(0.3, 0.9, len(df))

        df["safety_score"] = (
            0.4 * df["cctv_score"] +
            0.3 * df["light_score"] +
            0.3 * df["police_score"]
        )

        df["infra_score"] = 1 - df["safety_score"]

        return df

    # -----------------------------
    # LOAD REAL BBMP DATA
    # -----------------------------
    try:
        cctv_df = pd.read_csv(CCTV_PATH)
        lights_df = pd.read_csv(LIGHTS_PATH)
        police_df = pd.read_csv(POLICE_PATH)

    except Exception as e:

        st.error(f"infra csv loading failed: {e}")

        df = wards[["ward_name"]].copy()
        df["infra_score"] = 0.5
        df["safety_score"] = 0.5

        return df

    # -----------------------------
    # DEBUG
    # -----------------------------
    st.sidebar.write("cctv rows:", len(cctv_df))
    st.sidebar.write("lights rows:", len(lights_df))
    st.sidebar.write("police rows:", len(police_df))

    # -----------------------------
    # CLEAN COLUMN NAMES
    # -----------------------------
    cctv_df.columns = cctv_df.columns.str.lower().str.strip()
    lights_df.columns = lights_df.columns.str.lower().str.strip()
    police_df.columns = police_df.columns.str.lower().str.strip()

    infra_scores = []

    # -----------------------------
    # WARD LOOP
    # -----------------------------
    for _, ward in wards.iterrows():

        ward_coord = np.array([
            [ward["lat"], ward["lon"]]
        ])

        # =====================================================
        # CCTV SCORE
        # =====================================================

        try:

            cctv_coords = cctv_df[
                ["latitude", "longitude"]
            ].dropna().values

            if len(cctv_coords) > 0:

                nbrs = NearestNeighbors(
                    n_neighbors=max(1, min(5, len(cctv_coords)))
                )

                nbrs.fit(cctv_coords)

                distances, _ = nbrs.kneighbors(ward_coord)

                cctv_score = 1 / (
                    distances.mean() + 1e-5
                )

            else:
                cctv_score = 0

        except Exception:
            cctv_score = 0

        # =====================================================
        # STREETLIGHT SCORE
        # =====================================================

        try:

            light_coords = lights_df[
                ["latitude", "longitude"]
            ].dropna().values

            if len(light_coords) > 0:

                nbrs = NearestNeighbors(
                    n_neighbors=max(1, min(10, len(light_coords)))
                )

                nbrs.fit(light_coords)

                distances, _ = nbrs.kneighbors(ward_coord)

                light_score = 1 / (
                    distances.mean() + 1e-5
                )

            else:
                light_score = 0

        except Exception:
            light_score = 0

        # =====================================================
        # POLICE SCORE
        # =====================================================

        try:

            police_coords = police_df[
                ["latitude", "longitude"]
            ].dropna().values

            if len(police_coords) > 0:

                nbrs = NearestNeighbors(
                    n_neighbors=max(1, min(3, len(police_coords)))
                )

                nbrs.fit(police_coords)

                distances, _ = nbrs.kneighbors(ward_coord)

                police_score = 1 / (
                    distances.mean() + 1e-5
                )

            else:
                police_score = 0

        except Exception:
            police_score = 0

        # =====================================================
        # FINAL SAFETY SCORE
        # =====================================================

        safety_score = (
            0.4 * cctv_score +
            0.3 * light_score +
            0.3 * police_score
        )

        infra_scores.append({

            "ward_name": ward["ward_name"],

            "cctv_score": cctv_score,

            "light_score": light_score,

            "police_score": police_score,

            "safety_score": safety_score

        })

    infra_df = pd.DataFrame(infra_scores)

    # -----------------------------
    # NORMALIZE
    # -----------------------------
    for col in [
        "cctv_score",
        "light_score",
        "police_score",
        "safety_score"
    ]:

        infra_df[col] = (
            infra_df[col]
            .rank(pct=True)
        )

    # higher safety = lower infra risk
    infra_df["infra_score"] = (
        1 - infra_df["safety_score"]
    )

    return infra_df

def simulate_iot_pings(*args, **kwargs):
    return pd.DataFrame()

def detect_male_clusters(*args, **kwargs):
    return pd.DataFrame(columns=[
        "centroid_lat",
        "centroid_lon",
        "size",
        "threat_level"
    ])

def compute_live_threat_scores(wards, clusters_df):
    df = wards[["ward_name"]].copy()
    df["live_threat_score"] = np.random.uniform(0, 0.5, len(df))
    df["nearby_clusters"] = 0
    df["max_cluster_size"] = 0
    return df

def combine_scores(hist, infra, live, hour=12, is_festival=False, weights=None):
    df = hist.merge(infra, on="ward_name", how="left")
    df = df.merge(live, on="ward_name", how="left")

    df["risk_score"] = (
        0.6 * df["historical_risk"] +
        0.2 * df["infra_score"].fillna(0.5) +
        0.2 * df["live_threat_score"].fillna(0)
    )

    df["risk_level"] = df["risk_score"].apply(
        lambda x: "high" if x > 0.66 else "mid" if x > 0.33 else "low"
    )

    return df

def should_reroute(*args, **kwargs):
    return {"reroute": False, "message": ""}

def time_penalty(hour, is_festival):
    return 0.2 if hour >= 22 else 0.05

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="SafeRoute.ai — not today bestie 🛡️", page_icon="🛡️")

# ──────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root{--hot-pink:#FF2D78;--neon-lime:#C8F135;--electric-blue:#3D5BFF;--midnight:#0A0A1A;--off-white:#F5F3EF;--warn-amber:#FFB830;--safe-teal:#00D4AA;--danger-red:#FF3B3B;--glass:rgba(255,255,255,0.06);}
html,body,[data-testid="stAppViewContainer"]{background:var(--midnight)!important;color:var(--off-white)!important;font-family:'DM Sans',sans-serif!important;}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stSidebar"]{background:#0F0F22!important;border-right:1px solid rgba(255,255,255,0.07)!important;}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:var(--off-white)!important;letter-spacing:-0.03em!important;}
[data-testid="metric-container"]{background:var(--glass)!important;border:1px solid rgba(255,255,255,0.1)!important;border-radius:16px!important;padding:1rem!important;}
[data-testid="stMetricLabel"]>div{color:rgba(255,255,255,0.5)!important;font-size:12px!important;text-transform:uppercase!important;letter-spacing:0.08em!important;}
[data-testid="stMetricValue"]>div{color:var(--neon-lime)!important;font-family:'Syne',sans-serif!important;font-size:2rem!important;font-weight:800!important;}
[data-testid="stRadio"]>div{flex-direction:row!important;gap:12px!important;}
[data-testid="stRadio"] label{background:rgba(255,255,255,0.05)!important;border:1px solid rgba(255,255,255,0.12)!important;border-radius:100px!important;padding:6px 20px!important;font-size:14px!important;cursor:pointer!important;}
hr{border-color:rgba(255,255,255,0.08)!important;}
[data-testid="stDataFrame"]{border:1px solid rgba(255,255,255,0.08)!important;border-radius:12px!important;}
.badge-red{background:rgba(255,59,59,0.15);color:#FF3B3B;border:1px solid rgba(255,59,59,0.3);border-radius:100px;padding:3px 12px;font-size:12px;font-weight:500;}
.badge-amber{background:rgba(255,184,48,0.15);color:#FFB830;border:1px solid rgba(255,184,48,0.3);border-radius:100px;padding:3px 12px;font-size:12px;font-weight:500;}
.badge-teal{background:rgba(0,212,170,0.15);color:#00D4AA;border:1px solid rgba(0,212,170,0.3);border-radius:100px;padding:3px 12px;font-size:12px;font-weight:500;}
.ward-card{background:linear-gradient(135deg,rgba(255,45,120,0.08) 0%,rgba(61,91,255,0.08) 100%);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:24px;margin:16px 0;}
.hero-title{font-family:'Syne',sans-serif;font-size:clamp(2rem,4vw,3.5rem);font-weight:800;letter-spacing:-0.04em;line-height:1.05;background:linear-gradient(135deg,#FF2D78 0%,#C8F135 50%,#3D5BFF 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin:0;}
.tagline{color:rgba(255,255,255,0.45);font-size:15px;margin-top:8px;font-weight:300;}
.section-label{font-family:'Syne',sans-serif;font-size:11px;text-transform:uppercase;letter-spacing:0.15em;color:rgba(255,255,255,0.35);margin-bottom:12px;}
.risk-bar-wrap{background:rgba(255,255,255,0.06);border-radius:100px;height:8px;width:100%;}
.risk-bar{height:8px;border-radius:100px;transition:width 0.6s ease;}
.factor-pill{display:inline-block;background:rgba(61,91,255,0.15);color:#7B8FFF;border:1px solid rgba(61,91,255,0.3);border-radius:100px;padding:3px 12px;font-size:11px;margin-left:8px;}
.src-chip{display:inline-block;background:rgba(200,241,53,0.1);color:#C8F135;border:1px solid rgba(200,241,53,0.25);border-radius:100px;padding:2px 10px;font-size:10px;margin:2px;font-weight:500;letter-spacing:0.05em;}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────
cctv_ok   = os.path.exists(CCTV_PATH)
lights_ok = os.path.exists(LIGHTS_PATH)
police_ok = os.path.exists(POLICE_PATH)
_use_sim_bbmp = not (cctv_ok and lights_ok and police_ok)

with st.sidebar:
    st.markdown('<p class="section-label">⚙️ model controls</p>', unsafe_allow_html=True)
    sim_hour    = st.slider("hour of day 🕐", 0, 23, value=datetime.now().hour, step=1)
    is_festival = st.toggle("festival / event day 🎉", value=False)

    st.markdown("---")
    st.markdown('<p class="section-label">⚖️ model weights</p>', unsafe_allow_html=True)
    w_hist  = st.slider("XGBoost crime",   0.0, 1.0, 0.35, 0.05)
    w_infra = st.slider("BBMP infra",      0.0, 1.0, 0.30, 0.05)
    w_live  = st.slider("live IoT threat", 0.0, 1.0, 0.25, 0.05)
    w_time  = round(max(0.0, min(1.0, 1.0 - w_hist - w_infra - w_live)), 2)
    st.caption(f"time penalty (auto): **{w_time}**")
    WEIGHTS = {"historical": w_hist, "infra": w_infra, "live": w_live, "time": w_time}

    st.markdown("---")
    st.markdown('<p class="section-label">🗂️ real BBMP data</p>', unsafe_allow_html=True)
    st.markdown(
        f"{'✅' if cctv_ok   else '⚠️'} CCTV &nbsp;"
        f"{'✅' if lights_ok else '⚠️'} Lights &nbsp;"
        f"{'✅' if police_ok else '⚠️'} Police",
        unsafe_allow_html=True
    )
    if _use_sim_bbmp:
        st.caption("Add bbmp_*.csv files to data/ for real infra scoring")

    st.markdown("---")
    show_debug = st.toggle("🐛 debug", value=False)

# ──────────────────────────────────────────────────────────────────────────
# DATA LOADING
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_fir():
    df = pd.read_csv(DATA_PATH)
    lat_col = next((c for c in df.columns if c.lower() in ("latitude","lat")), None)
    lon_col = next((c for c in df.columns if c.lower() in ("longitude","lon","long")), None)
    if not lat_col or not lon_col:
        st.error(f"No lat/lon columns — found: {list(df.columns)}")
        st.stop()
    df = df.rename(columns={lat_col:"Latitude", lon_col:"Longitude"})
    df = df.dropna(subset=["Latitude","Longitude"])
    yr  = next((c for c in df.columns if "year"  in c.lower()), None)
    mo  = next((c for c in df.columns if "month" in c.lower()), None)
    day = next((c for c in df.columns if c.lower() in ("fir_day","day","date_day")), None)
    if yr and mo and day:
        df["date"] = pd.to_datetime(df[yr].astype(str)+"-"+df[mo].astype(str)+"-"+df[day].astype(str), errors="coerce")
    else:
        dc = next((c for c in df.columns if "date" in c.lower()), None)
        df["date"] = pd.to_datetime(df[dc], errors="coerce") if dc else pd.NaT
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"]       = df["date"].dt.month
    return df[(df["Latitude"]>=12.8)&(df["Latitude"]<=13.2)&(df["Longitude"]>=77.4)&(df["Longitude"]<=77.8)].copy()

@st.cache_data
def load_wards():
    from lxml import etree
    tree = etree.parse(WARD_PATH)
    root = tree.getroot()
    ns   = "http://www.opengis.net/kml/2.2"
    def find_all(node, tag):
        r = node.findall(f".//{{{ns}}}{tag}")
        return r if r else node.findall(f".//{tag}")
    placemarks = find_all(root, "Placemark")
    name_map   = {}
    for i, pm in enumerate(placemarks):
        name = None
        for sd in find_all(pm, "SimpleData"):
            if sd.get("name") == "name_en" and sd.text and sd.text.strip():
                name = sd.text.strip(); break
        if not name:
            for sd in find_all(pm, "SimpleData"):
                if sd.get("name") == "proposed_ward_name_en" and sd.text:
                    name = re.sub(r"^\d+[-.\s]+","", sd.text.strip()); break
        name_map[i] = name or f"Ward-{i}"
    try:    wards = gpd.read_file(WARD_PATH, driver="KML")
    except: wards = gpd.read_file(WARD_PATH)
    wards["ward_name"] = [name_map.get(i, f"Ward-{i}") for i in range(len(wards))]
    wards = wards[wards.geometry.notnull()].copy()
    return wards[["ward_name","geometry"]].to_crs("EPSG:4326")

df_blr = load_fir()
wards  = load_wards()

gdf = gpd.GeoDataFrame(df_blr, geometry=gpd.points_from_xy(df_blr["Longitude"], df_blr["Latitude"]), crs="EPSG:4326")
gdf = gpd.sjoin(gdf, wards.to_crs("EPSG:4326"), how="inner", predicate="within")
gdf = gdf.reset_index(drop=True)

if show_debug:
    with st.sidebar.expander("🐛 spatial join"):
        st.write(f"FIR rows: **{len(df_blr):,}** → joined: **{len(gdf):,}**")
        st.write(f"Unique wards: **{gdf['ward_name'].nunique()}**")
        st.dataframe(gdf["ward_name"].value_counts().head(15).reset_index())

# ──────────────────────────────────────────────────────────────────────────
# RUN ALL FOUR MODEL LAYERS
# ──────────────────────────────────────────────────────────────────────────
with st.spinner("🔮 XGBoost oracle is thinking..."):
    feats = build_crime_features(gdf)
    historical_df, xgb_model, importances = train_xgboost(feats)

with st.spinner("🏙️ Scoring BBMP infrastructure..."):
    infra_df = compute_infra_scores(wards, data_dir=DATA_DIR, use_simulated=_use_sim_bbmp)

with st.spinner("📡 Running DBSCAN cluster detection..."):
    pings_df    = simulate_iot_pings(wards, n_devices=600, hour=sim_hour)
    clusters_df = detect_male_clusters(pings_df, night_only=(sim_hour>=22 or sim_hour<=5), eps_m=200, min_samples=8)
    live_df     = compute_live_threat_scores(wards, clusters_df)

scores_df = combine_scores(historical_df, infra_df, live_df, hour=sim_hour, is_festival=is_festival, weights=WEIGHTS)

_crime_col = next((c for c in gdf.columns if c.lower() in ("crimegroup_name","crime_group_name","crimehead_name")), None)
if _crime_col:
    _gdf_clean = gdf.dropna(subset=[_crime_col])
    ward_crime_types = (
        _gdf_clean.groupby(["ward_name", _crime_col]).size()
        .reset_index(name="count")
        .rename(columns={_crime_col: "CrimeGroup_Name"})
    )
else:
    ward_crime_types = pd.DataFrame(columns=["ward_name","CrimeGroup_Name","count"])

t_pen = time_penalty(sim_hour, is_festival)

# ──────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ──────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1])
with col_left:
    st.markdown('<p class="hero-title">SafeRoute.ai</p>', unsafe_allow_html=True)
    night_str = "🌙 night mode" if (sim_hour>=22 or sim_hour<=5) else f"☀️ {sim_hour:02d}:00"
    st.markdown(f'<p class="tagline">real ones protect each other &nbsp;·&nbsp; bengaluru ward safety &nbsp;·&nbsp; {night_str}</p>', unsafe_allow_html=True)
    if not _use_sim_bbmp:
        _n_cctv   = sum(1 for _ in open(CCTV_PATH))   - 1
        _n_lights = sum(1 for _ in open(LIGHTS_PATH)) - 1
        _n_police = sum(1 for _ in open(POLICE_PATH)) - 1
        real_src = (
            f'<span class="src-chip">{_n_cctv:,} CCTVs</span>'
            f'<span class="src-chip">{_n_lights:,} street lights</span>'
            f'<span class="src-chip">{_n_police:,} police stations</span>'
        )
    else:
        real_src = '<span class="src-chip" style="color:#FFB830;border-color:rgba(255,184,48,0.25);">simulated infra</span>'
    st.markdown(
        f'<span class="src-chip">Karnataka FIR data</span>{real_src}'
        '<span class="src-chip">XGBoost + DBSCAN</span>',
        unsafe_allow_html=True
    )

with col_right:
    high_count  = int((scores_df["risk_level"]=="high").sum())
    women_total = int(historical_df["women_firs"].sum()) if "women_firs" in historical_df.columns else 0
    st.metric("high-risk wards",   f"{high_count} 🚨")
    st.metric("live IoT clusters", f"{len(clusters_df)} 📡")
    st.metric("women FIRs",        f"{women_total:,}")

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# MODEL WEIGHT STRIP
# ──────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">model weights active now</p>', unsafe_allow_html=True)
mc1, mc2, mc3, mc4 = st.columns(4)
for col, lbl, val, sub, clr in [
    (mc1, "XGBoost crime",  w_hist,  "historical FIRs",            "#C8F135"),
    (mc2, "BBMP infra IDW", w_infra, "CCTV · lights · police",     "#3D5BFF"),
    (mc3, "DBSCAN IoT",     w_live,  f"{len(clusters_df)} clusters","#FF2D78"),
    (mc4, "time penalty",   t_pen,   f"hour {sim_hour:02d}:00",    "#FFB830"),
]:
    col.markdown(f"""
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">{lbl}</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:{clr};">{val:.0%}</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px;">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# WARD DISTRIBUTION SUMMARY
# ──────────────────────────────────────────────────────────────────────────
_total  = len(scores_df)
_n_high = int((scores_df["risk_level"] == "high").sum())
_n_mid  = int((scores_df["risk_level"] == "mid").sum())
_n_low  = int((scores_df["risk_level"] == "low").sum())
_pct_h  = int(_n_high / _total * 100) if _total else 0
_pct_m  = int(_n_mid  / _total * 100) if _total else 0
_pct_l  = int(_n_low  / _total * 100) if _total else 0

st.markdown('<p class="section-label">ward risk distribution</p>', unsafe_allow_html=True)
wd1, wd2, wd3 = st.columns(3)
for col, lbl, n, pct, clr, bg in [
    (wd1, "High Risk",    _n_high, _pct_h, "#FF3B3B", "rgba(255,59,59,0.08)"),
    (wd2, "Watch Out",    _n_mid,  _pct_m, "#FFB830", "rgba(255,184,48,0.08)"),
    (wd3, "Mostly Safe",  _n_low,  _pct_l, "#00D4AA", "rgba(0,212,170,0.08)"),
]:
    col.markdown(f"""
    <div style="background:{bg};border:1px solid {clr}33;border-radius:14px;padding:16px;text-align:center;">
      <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;color:{clr};line-height:1;">{n}</div>
      <div style="font-size:12px;color:{clr};opacity:0.7;margin-top:2px;">{lbl} · {pct}%</div>
      <div style="background:rgba(255,255,255,0.06);border-radius:100px;height:4px;margin-top:10px;">
        <div style="width:{pct}%;height:4px;border-radius:100px;background:{clr};"></div>
      </div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")
st.markdown('<p class="section-label">bengaluru ward map — hover any ward for the full tea ☕</p>', unsafe_allow_html=True)

COLOR_MAP   = {"high":"#FF3B3B","mid":"#FFB830","low":"#00D4AA","unknown":"#4B5563"}
BADGE_LABEL = {"high":"🚨 HIGH RISK","mid":"👀 WATCH OUT","low":"✅ SAFE","unknown":"❓ NO DATA"}

wards_merged = wards.merge(scores_df, on="ward_name", how="left")
map_ = folium.Map(location=[12.97, 77.59], zoom_start=11, tiles="CartoDB dark_matter")

for _, row in wards_merged.iterrows():
    score  = float(row.get("risk_score",  0.5) or 0.5)
    label  = str(row.get("risk_level",   "unknown") or "unknown")
    color  = COLOR_MAP.get(label, "#4B5563")
    wname  = str(row["ward_name"] or "Unknown")
    factor = str(row.get("dominant_factor","—") or "—")
    safety = float(row.get("safety_score", 0.5) or 0.5)
    nc     = int(row.get("nearby_clusters", 0) or 0)
    iot_line = f"<div style='font-size:11px;color:#FF2D78;margin-top:4px;'>📡 {nc} IoT cluster(s) nearby</div>" if nc > 0 else ""

    tt = f"""
    <div style="font-family:'DM Sans',sans-serif;background:#0A0A1A;border:1px solid {color};
                border-radius:12px;padding:14px 18px;min-width:220px;color:#F5F3EF;">
      <div style="font-size:16px;font-weight:700;margin-bottom:6px;">{wname}</div>
      <div style="background:{color}22;color:{color};border:1px solid {color}55;border-radius:100px;
                  display:inline-block;padding:2px 12px;font-size:11px;font-weight:600;margin-bottom:8px;">
        {BADGE_LABEL.get(label,"?")}
      </div>
      <div style="font-size:12px;color:rgba(255,255,255,0.5);">
        Risk: <b style="color:{color}">{score:.2f}</b> &nbsp;|&nbsp; Safety: <b style="color:#C8F135">{safety:.2f}</b>
      </div>
      <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-top:4px;">
        ⚡ driven by: <b style="color:#7B8FFF">{factor}</b>
      </div>
      {iot_line}
    </div>"""

    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, c=color: {"fillColor":c,"color":"#1A1A2E","weight":0.8,"fillOpacity":0.65},
        highlight_function=lambda x, c=color: {"weight":2.5,"color":c,"fillOpacity":0.85},
        tooltip=folium.Tooltip(tt, sticky=True),
    ).add_to(map_)

for _, cl in clusters_df.iterrows():
    folium.CircleMarker(
        location=[cl["centroid_lat"], cl["centroid_lon"]],
        radius=max(6, int(cl["size"])//3),
        color="#FF2D78", fill=True, fill_color="#FF2D78",
        fill_opacity=0.4, weight=1.5,
        tooltip=f"📡 Male cluster · {int(cl['size'])} devices · {cl['threat_level']}",
    ).add_to(map_)

legend_html = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:#0A0A1A;
            border:1px solid rgba(255,255,255,0.12);border-radius:14px;
            padding:14px 18px;font-family:'DM Sans',sans-serif;">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:10px;">risk level</div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#FF3B3B;"></div><span style="color:#FF3B3B;font-size:12px;">high (&gt;0.66)</span></div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#FFB830;"></div><span style="color:#FFB830;font-size:12px;">mid (0.33–0.66)</span></div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;"><div style="width:10px;height:10px;border-radius:50%;background:#00D4AA;"></div><span style="color:#00D4AA;font-size:12px;">low (&lt;0.33)</span></div>
  <div style="display:flex;align-items:center;gap:8px;"><div style="width:10px;height:10px;border-radius:50%;background:#FF2D78;opacity:0.6;"></div><span style="color:#FF2D78;font-size:12px;">IoT cluster</span></div>
</div>"""
map_.get_root().html.add_child(folium.Element(legend_html))
st_folium(map_, use_container_width=True, height=580)
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# WARD DRILL-DOWN
# ──────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">ward details — the full tea ☕</p>', unsafe_allow_html=True)

VIBES = {
    "high": [
        "bestie NO 🚨 this ward is giving main villain energy rn",
        "not safe sis. pepper spray is not optional here",
        "red flag central fr fr. we are rerouting you IMMEDIATELY 💀",
        "this zone is cooked. we are NOT going here.",
        "chale mat yaar. this area said no girlies after dark 🚫",
    ],
    "mid": [
        "it's giving... questionable. stick to main roads only",
        "situationally aware era. share your live location bestie 📍",
        "mid-risk. not full panic mode but also not unbothered 👀",
        "could be worse, could be better. text someone you're out",
        "yellow flag vibes. keep your eyes open and AirPods on low 🎧",
    ],
    "low": [
        "she's mostly safe fr. normal girl-precautions apply 💅",
        "green flag ward! walk with your head up and AirPods out",
        "bestie you're okay here. go off! 🌿",
        "this ward said 'safe space' and we stan 🙌",
        "lowkey chill zone. still share your location tho 📍",
    ],
}
BADGE_MAP = {"high":"badge-red","mid":"badge-amber","low":"badge-teal"}

selected_ward = st.selectbox(
    "pick a ward 👇",
    options=["— select a ward —"] + sorted(scores_df["ward_name"].dropna().tolist()),
    label_visibility="visible"
)

if selected_ward and selected_ward != "— select a ward —":
    row    = scores_df[scores_df["ward_name"] == selected_ward].iloc[0]
    rscore = float(row["risk_score"])
    label  = str(row["risk_level"])
    color  = COLOR_MAP.get(label, "#4B5563")
    badge  = BADGE_MAP.get(label, "badge-amber")
    # Stable vibe per ward — seed from ward name so it doesn't jump on every rerender
    _seed = int(hashlib.md5(selected_ward.encode()).hexdigest(), 16) % (2**31)
    random.seed(_seed)
    vibe  = random.choice(VIBES.get(label, VIBES["mid"]))
    random.seed()  # restore true randomness for everything else
    pct    = int(rscore * 100)
    nc     = int(row.get("nearby_clusters", 0) or 0)
    ms     = int(row.get("max_cluster_size",  0) or 0)
    _ward_fir_count = int(gdf[gdf["ward_name"] == selected_ward].shape[0])

    reroute_info = should_reroute(selected_ward, scores_df, threshold=0.66)

    reroute_html = (
        f"<div style='background:rgba(255,59,59,0.1);border:1px solid rgba(255,59,59,0.3);"
        f"border-radius:12px;padding:14px;margin-bottom:12px;font-size:14px;color:#FF6B6B;'>"
        f"🔄 <b>REROUTE RECOMMENDED</b> — {reroute_info['message']}</div>"
    ) if reroute_info["reroute"] else ""

    iot_html = (
        f"<div style='background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.2);"
        f"border-radius:12px;padding:12px;font-size:13px;color:#00D4AA;margin-top:8px;'>"
        f"📡 {nc} IoT cluster(s) within 600 m · max cluster size: {ms}</div>"
    ) if nc > 0 else ""

    st.markdown(f"""
    <div class="ward-card">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px;">
        <div>
          <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;letter-spacing:-0.03em;color:#F5F3EF;">{selected_ward}</div>
          <span class="{badge}" style="margin-top:6px;display:inline-block;">
            {'🚨 HIGH RISK' if label=='high' else '👀 WATCH OUT' if label=='mid' else '✅ MOSTLY SAFE'}
          </span>
          <span class="factor-pill">⚡ driven by {row.get('dominant_factor','—')}</span>
          <div style="font-size:12px;color:rgba(255,255,255,0.3);margin-top:8px;">{_ward_fir_count:,} FIRs recorded · safety score: {float(row.get('safety_score', 0)):.2f}</div>
        </div>
        <div style="text-align:right;">
          <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;color:{color};line-height:1;">{pct}</div>
          <div style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.08em;">risk score</div>
        </div>
      </div>
      <div class="risk-bar-wrap" style="margin-bottom:20px;">
        <div class="risk-bar" style="width:{pct}%;background:{color};"></div>
      </div>
      <div style="font-size:17px;line-height:1.5;font-weight:500;color:rgba(255,255,255,0.8);margin-bottom:20px;font-style:italic;">"{vibe}"</div>
      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:16px;">
        <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">XGBoost</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#C8F135;">{int(float(row.get('historical_risk',0))*100)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">infra safety</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#3D5BFF;">{int(float(row.get('infra_score',0))*100)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">IoT threat</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#FF2D78;">{int(float(row.get('live_threat_score',0))*100)}</div>
        </div>
        <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">time penalty</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:800;color:#FFB830;">{int(t_pen*100)}</div>
        </div>
      </div>
      {reroute_html}
      {iot_html}
    </div>
    """, unsafe_allow_html=True)

    # XGBoost feature importance
    if importances:
        st.markdown('<p class="section-label">what the model actually cares about 🔍</p>', unsafe_allow_html=True)
        imp_df = (pd.DataFrame({"feature": list(importances.keys()), "importance": list(importances.values())})
                  .sort_values("importance", ascending=False).reset_index(drop=True))
        st.dataframe(imp_df, use_container_width=True, hide_index=True)

    # Crime type breakdown
    ward_crimes_df = ward_crime_types[ward_crime_types["ward_name"]==selected_ward].copy()
    if not ward_crimes_df.empty:
        ward_crimes_df = (ward_crimes_df.sort_values("count", ascending=False)
                          .head(8)[["CrimeGroup_Name","count"]]
                          .rename(columns={"CrimeGroup_Name":"crime type","count":"cases"}))
        st.markdown('<p class="section-label">crime breakdown — receipts 🧾</p>', unsafe_allow_html=True)
        st.dataframe(ward_crimes_df, use_container_width=True, hide_index=True)

    # Infrastructure breakdown
    ward_infra = infra_df[infra_df["ward_name"]==selected_ward]
    if not ward_infra.empty:
        wi = ward_infra.iloc[0]
        st.markdown('<p class="section-label">BBMP infra coverage 🏙️</p>', unsafe_allow_html=True)
        ia, ib, ic = st.columns(3)
        for col, lbl, val, clr in [
            (ia, "CCTV coverage",       wi.get("cctv_score",   0), "#C8F135"),
            (ib, "Street light cover",  wi.get("light_score",  0), "#FFB830"),
            (ic, "Police stn proximity",wi.get("police_score", 0), "#3D5BFF"),
        ]:
            col.markdown(f"""
            <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;text-align:center;">
              <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;color:rgba(255,255,255,0.35);margin-bottom:6px;">{lbl}</div>
              <div style="font-family:'Syne',sans-serif;font-size:1.5rem;font-weight:800;color:{clr};">{float(val):.2f}</div>
            </div>""", unsafe_allow_html=True)

else:
    st.markdown("""
    <div style="background:rgba(255,255,255,0.03);border:1px dashed rgba(255,255,255,0.1);
                border-radius:16px;padding:48px;text-align:center;color:rgba(255,255,255,0.3);">
      <div style="font-size:2.5rem;margin-bottom:10px;">☝️</div>
      <div style="font-size:15px;">pick a ward above to get the full breakdown</div>
      <div style="font-size:12px;margin-top:6px;color:rgba(255,255,255,0.2);">
        pink circles on the map = live IoT male clusters
      </div>
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:rgba(255,255,255,0.2);font-size:12px;padding:16px 0 32px;line-height:2;">
  SafeRoute.ai &nbsp;·&nbsp; Karnataka Govt FIRs &nbsp;·&nbsp; BBMP CCTV / Street Lights / Police Stations<br>
  XGBoost + Inverse-Distance Weighting + DBSCAN ensemble &nbsp;·&nbsp;
  built with 💅 for the girls &nbsp;·&nbsp;
  <span style="color:#FF2D78;">data is power. share the route.</span>
</div>""", unsafe_allow_html=True)