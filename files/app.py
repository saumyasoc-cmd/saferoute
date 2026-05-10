"""
SafeRoute.ai — Main Dashboard
Full ensemble model: XGBoost + Infra IDW + DBSCAN IoT + Time combiner
"""

import os, re, sys
import streamlit as st
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
from streamlit_folium import st_folium
from datetime import datetime

# Add models directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from models.crime_model import build_crime_features, train_xgboost
from models.infra_model  import compute_infra_scores
from models.iot_model    import simulate_iot_pings, detect_male_clusters, compute_live_threat_scores
from models.ensemble     import combine_scores, should_reroute, time_penalty

# ──────────────────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="SafeRoute.ai — not today bestie 🛡️",
    page_icon="🛡️"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root {
    --hot-pink:#FF2D78; --neon-lime:#C8F135; --electric-blue:#3D5BFF;
    --midnight:#0A0A1A; --off-white:#F5F3EF;
    --warn-amber:#FFB830; --safe-teal:#00D4AA; --danger-red:#FF3B3B;
    --glass:rgba(255,255,255,0.06);
}
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
.zone-chip{display:inline-block;border-radius:10px;padding:8px 14px;margin:4px;font-size:13px;font-weight:500;}
.zone-hot{background:rgba(255,59,59,0.2);color:#FF6B6B;border:1px solid rgba(255,59,59,0.3);}
.zone-mid{background:rgba(255,184,48,0.2);color:#FFB830;border:1px solid rgba(255,184,48,0.3);}
.zone-safe{background:rgba(0,212,170,0.2);color:#00D4AA;border:1px solid rgba(0,212,170,0.3);}
.factor-pill{display:inline-block;background:rgba(61,91,255,0.15);color:#7B8FFF;border:1px solid rgba(61,91,255,0.3);border-radius:100px;padding:3px 12px;font-size:11px;margin-left:8px;}
.iot-chip{display:inline-block;border-radius:8px;padding:4px 12px;font-size:12px;margin:3px;background:rgba(255,45,120,0.1);color:#FF2D78;border:1px solid rgba(255,45,120,0.2);}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "../data/FIR_Details_Data.csv")
WARD_PATH = os.path.join(BASE_DIR, "../data/Ward.xml")
DATA_DIR  = os.path.join(BASE_DIR, "../data")

# ──────────────────────────────────────────────────────────────────────────
# SIDEBAR — controls + debug
# ──────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<p class="section-label">model controls</p>', unsafe_allow_html=True)

    sim_hour = st.slider("simulate hour of day 🕐", 0, 23,
                         value=datetime.now().hour, step=1)
    is_festival = st.toggle("festival/event day 🎉", value=False)
    use_simulated_bbmp = st.toggle("use simulated BBMP data", value=True,
                                   help="Turn off when you have real CCTV/lights/police CSVs")
    use_simulated_iot  = st.toggle("use simulated IoT data",  value=True,
                                   help="Turn off when connected to real device stream")

    st.markdown("---")
    st.markdown('<p class="section-label">model weights</p>', unsafe_allow_html=True)
    w_hist  = st.slider("historical crime", 0.0, 1.0, 0.35, 0.05)
    w_infra = st.slider("infrastructure",   0.0, 1.0, 0.30, 0.05)
    w_live  = st.slider("live IoT threat",  0.0, 1.0, 0.25, 0.05)
    w_time  = 1.0 - w_hist - w_infra - w_live
    w_time  = max(0.0, min(1.0, w_time))
    st.markdown(f"**time penalty (auto):** {w_time:.2f}")

    WEIGHTS = {"historical": w_hist, "infra": w_infra,
               "live": w_live, "time": w_time}

    st.markdown("---")
    st.markdown('<p class="section-label">debug</p>', unsafe_allow_html=True)
    show_debug = st.toggle("show debug info", value=False)

# ──────────────────────────────────────────────────────────────────────────
# LOAD FIR DATA
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_fir():
    df = pd.read_csv(DATA_PATH)
    lat_col = next((c for c in df.columns if c.lower() in ("latitude","lat")), None)
    lon_col = next((c for c in df.columns if c.lower() in ("longitude","lon","long")), None)
    if not lat_col or not lon_col:
        st.error(f"❌ No Lat/Lon columns. Found: {list(df.columns)}")
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
    return df[
        (df["Latitude"]  >= 12.8) & (df["Latitude"]  <= 13.2) &
        (df["Longitude"] >= 77.4) & (df["Longitude"] <= 77.8)
    ].copy()

df_blr = load_fir()

# ──────────────────────────────────────────────────────────────────────────
# LOAD WARDS (lxml for ExtendedData)
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data
def load_wards():
    from lxml import etree
    tree  = etree.parse(WARD_PATH)
    root  = tree.getroot()
    ns    = "http://www.opengis.net/kml/2.2"

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
                    name = re.sub(r"^\d+[-.]\\s*","", sd.text.strip()); break
        name_map[i] = name or f"Ward-{i}"

    try:    wards = gpd.read_file(WARD_PATH, driver="KML")
    except: wards = gpd.read_file(WARD_PATH)

    wards["ward_name"] = [name_map.get(i, f"Ward-{i}") for i in range(len(wards))]
    wards = wards[wards.geometry.notnull()].copy()
    return wards[["ward_name","geometry"]].to_crs("EPSG:4326")

wards = load_wards()

# ──────────────────────────────────────────────────────────────────────────
# SPATIAL JOIN
# ──────────────────────────────────────────────────────────────────────────
gdf = gpd.GeoDataFrame(
    df_blr,
    geometry=gpd.points_from_xy(df_blr["Longitude"], df_blr["Latitude"]),
    crs="EPSG:4326"
)
gdf = gpd.sjoin(gdf, wards.to_crs("EPSG:4326"), how="inner", predicate="within")
gdf = gdf.reset_index(drop=True)

if show_debug:
    with st.sidebar.expander("Spatial join debug"):
        st.write(f"FIR rows: {len(df_blr)} → after join: {len(gdf)}")
        st.write(f"Unique wards: {gdf['ward_name'].nunique()}")
        st.write(gdf["ward_name"].value_counts().head(10))

# ──────────────────────────────────────────────────────────────────────────
# LAYER 1 — XGBoost historical risk
# ──────────────────────────────────────────────────────────────────────────
with st.spinner("🔮 XGBoost oracle is thinking..."):
    feats         = build_crime_features(gdf)
    historical_df, xgb_model, importances = train_xgboost(feats)

# ──────────────────────────────────────────────────────────────────────────
# LAYER 2 — Infrastructure safety score
# ──────────────────────────────────────────────────────────────────────────
with st.spinner("🏙️ Scanning BBMP infrastructure..."):
    infra_df = compute_infra_scores(
        wards,
        data_dir=DATA_DIR,
        use_simulated=use_simulated_bbmp
    )

# ──────────────────────────────────────────────────────────────────────────
# LAYER 3 — DBSCAN live IoT threat
# ──────────────────────────────────────────────────────────────────────────
with st.spinner("📡 Scanning IoT device clusters..."):
    if use_simulated_iot:
        pings_df = simulate_iot_pings(wards, n_devices=600, hour=sim_hour)
    else:
        # Replace with your real IoT stream reader
        pings_df = simulate_iot_pings(wards, n_devices=600, hour=sim_hour)

    clusters_df = detect_male_clusters(
        pings_df,
        night_only=(22 <= sim_hour or sim_hour <= 5),
        eps_m=200,
        min_samples=8
    )
    live_df = compute_live_threat_scores(wards, clusters_df)

# ──────────────────────────────────────────────────────────────────────────
# LAYER 4 — Ensemble combiner
# ──────────────────────────────────────────────────────────────────────────
scores_df = combine_scores(
    historical_df, infra_df, live_df,
    hour=sim_hour,
    is_festival=is_festival,
    weights=WEIGHTS
)

# Crime type breakdown for drill-down
_crime_col = next((c for c in gdf.columns if c.lower() in
                   ("crimegroup_name","crime_group_name","crimehead_name")), None)
ward_crime_types = (
    gdf.groupby(["ward_name", _crime_col]).size().reset_index(name="count")
    .rename(columns={_crime_col: "CrimeGroup_Name"})
) if _crime_col else pd.DataFrame(columns=["ward_name","CrimeGroup_Name","count"])

# ──────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ──────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1])
with col_left:
    st.markdown('<p class="hero-title">SafeRoute.ai</p>', unsafe_allow_html=True)
    night_str = "🌙 night mode active" if (22<=sim_hour or sim_hour<=5) else f"☀️ {sim_hour:02d}:00"
    st.markdown(f'<p class="tagline">real ones protect each other · bengaluru · {night_str}</p>',
                unsafe_allow_html=True)

with col_right:
    high_count  = (scores_df["risk_level"] == "high").sum()
    women_total = int(historical_df.get("women_firs", pd.Series([0])).sum()) \
                  if "women_firs" in historical_df.columns else 0
    cluster_cnt = len(clusters_df)
    st.metric("high-risk wards",    f"{high_count} 🚨")
    st.metric("live IoT clusters",  f"{cluster_cnt} 📡")
    st.metric("women FIRs tracked", f"{women_total:,}")

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# MODEL BREAKDOWN — explainability strip
# ──────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">model weights active right now</p>',
            unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
t_pen = time_penalty(sim_hour, is_festival)
with c1:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);">XGBoost crime</div>
    <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#C8F135;">{w_hist:.0%}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px;">historical FIRs</div>
    </div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);">Infra IDW</div>
    <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#3D5BFF;">{w_infra:.0%}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px;">CCTV · lights · police</div>
    </div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);">DBSCAN IoT</div>
    <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#FF2D78;">{w_live:.0%}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px;">{cluster_cnt} live clusters</div>
    </div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
    <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);">Time penalty</div>
    <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:#FFB830;">{t_pen:.0%}</div>
    <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px;">hour {sim_hour:02d}:00</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# MAP
# ──────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">bengaluru ward map — tap any ward for the full tea ☕</p>',
            unsafe_allow_html=True)

wards_merged = wards.merge(scores_df, on="ward_name", how="left")
map_ = folium.Map(location=[12.97,77.59], zoom_start=11, tiles="CartoDB dark_matter")

for _, row in wards_merged.iterrows():
    score   = float(row.get("risk_score", 0.5) or 0.5)
    color   = row.get("map_color", "#4B5563") or "#4B5563"
    label   = row.get("risk_level", "unknown") or "unknown"
    wname   = row["ward_name"] or "Unknown"
    factor  = row.get("dominant_factor", "—") or "—"
    safety  = float(row.get("safety_score", 0.5) or 0.5)
    clusters_near = int(row.get("nearby_clusters", 0) or 0)

    badge = {"high":"🚨 HIGH RISK","mid":"👀 WATCH OUT","low":"✅ SAFE","unknown":"❓ NO DATA"}

    tt = f"""
    <div style="font-family:'DM Sans',sans-serif;background:#0A0A1A;border:1px solid {color};
                border-radius:12px;padding:14px 18px;min-width:220px;color:#F5F3EF;">
      <div style="font-size:16px;font-weight:700;margin-bottom:4px;">{wname}</div>
      <div style="background:{color}22;color:{color};border:1px solid {color}55;
                  border-radius:100px;display:inline-block;padding:2px 12px;
                  font-size:11px;font-weight:600;margin-bottom:8px;">{badge.get(label,'?')}</div>
      <div style="font-size:12px;color:rgba(255,255,255,0.5);">
        Risk: <b style="color:{color}">{score:.2f}</b> &nbsp;|&nbsp;
        Safety: <b style="color:#C8F135">{safety:.2f}</b>
      </div>
      <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-top:4px;">
        Driven by: <b style="color:#7B8FFF">{factor}</b>
      </div>
      {"<div style='font-size:11px;color:#FF2D78;margin-top:4px;'>📡 "+str(clusters_near)+" IoT cluster(s) nearby</div>" if clusters_near > 0 else ""}
    </div>"""

    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, c=color: {
            "fillColor":c, "color":"#1A1A2E", "weight":0.8, "fillOpacity":0.65},
        highlight_function=lambda x, c=color: {
            "weight":2.5, "color":c, "fillOpacity":0.85},
        tooltip=folium.Tooltip(tt, sticky=True),
    ).add_to(map_)

# IoT cluster markers
for _, cl in clusters_df.iterrows():
    folium.CircleMarker(
        location=[cl["centroid_lat"], cl["centroid_lon"]],
        radius=max(6, cl["size"] / 3),
        color="#FF2D78", fill=True, fill_color="#FF2D78",
        fill_opacity=0.4, weight=1.5,
        tooltip=f"📡 Male cluster · {int(cl['size'])} devices · {cl['threat_level']}",
    ).add_to(map_)

legend_html = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;
            background:#0A0A1A;border:1px solid rgba(255,255,255,0.12);
            border-radius:14px;padding:14px 18px;font-family:'DM Sans',sans-serif;">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;
              color:rgba(255,255,255,0.35);margin-bottom:10px;">risk level</div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FF3B3B;"></div>
    <span style="color:#FF3B3B;font-size:12px;">high (&gt;0.66)</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FFB830;"></div>
    <span style="color:#FFB830;font-size:12px;">mid (0.33–0.66)</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#00D4AA;"></div>
    <span style="color:#00D4AA;font-size:12px;">low (&lt;0.33)</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FF2D78;opacity:0.6;"></div>
    <span style="color:#FF2D78;font-size:12px;">IoT cluster</span>
  </div>
</div>"""
map_.get_root().html.add_child(folium.Element(legend_html))
st_folium(map_, width=None, height=600)

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# WARD DRILL-DOWN
# ──────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">ward details — the full tea ☕</p>', unsafe_allow_html=True)

selected_ward = st.selectbox(
    "pick a ward 👇",
    options=["— select a ward —"] + sorted(scores_df["ward_name"].dropna().tolist()),
    label_visibility="visible"
)

VIBES = {
    "high":["bestie NO 🚨 this ward is giving main villain energy rn",
            "not safe sis. carry your pepper spray era",
            "red flag central fr fr. rerouting you ASAP 💀",
            "this zone is cooked. we are NOT going here."],
    "mid": ["it's giving... questionable. stay on main roads only",
            "situationally aware era. share your live location bestie",
            "mid-risk. not panic mode but also not unbothered 👀",
            "could be worse. just text someone you're out"],
    "low": ["she's mostly safe. normal girl-precautions apply 💅",
            "green flag ward! walk with your head up and AirPods out",
            "bestie you're okay here. go off! 🌿",
            "this ward said 'safe space' and we stan 🙌"]
}

COLOR_MAP = {"high":"#FF3B3B","mid":"#FFB830","low":"#00D4AA","unknown":"#4B5563"}
BADGE_MAP = {"high":"badge-red","mid":"badge-amber","low":"badge-teal"}

if selected_ward and selected_ward != "— select a ward —":
    row   = scores_df[scores_df["ward_name"] == selected_ward].iloc[0]
    rscore = float(row["risk_score"])
    label  = row["risk_level"]
    color  = COLOR_MAP.get(label,"#4B5563")
    badge  = BADGE_MAP.get(label,"badge-amber")
    import random; vibe = random.choice(VIBES.get(label, VIBES["mid"]))
    pct    = int(rscore * 100)
    bar_c  = color

    # Reroute decision
    reroute_info = should_reroute(selected_ward, scores_df, threshold=0.66)

    st.markdown(f"""
    <div class="ward-card">
      <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:20px;">
        <div>
          <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;letter-spacing:-0.03em;color:#F5F3EF;">{selected_ward}</div>
          <span class="{badge}" style="margin-top:6px;display:inline-block;">
            {'🚨 HIGH RISK' if label=='high' else '👀 WATCH OUT' if label=='mid' else '✅ MOSTLY SAFE'}
          </span>
          <span class="factor-pill">driven by: {row.get('dominant_factor','—')}</span>
        </div>
        <div style="text-align:right;">
          <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;color:{color};line-height:1;">{pct}</div>
          <div style="font-size:12px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.08em;">risk score</div>
        </div>
      </div>
      <div class="risk-bar-wrap" style="margin-bottom:20px;">
        <div class="risk-bar" style="width:{pct}%;background:{bar_c};"></div>
      </div>
      <div style="font-size:17px;line-height:1.5;font-weight:500;color:rgba(255,255,255,0.8);margin-bottom:20px;font-style:italic;">"{vibe}"</div>

      <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:10px;margin-bottom:20px;">
        <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:12px;">
          <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">XGBoost score</div>
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

      {"<div style='background:rgba(255,59,59,0.1);border:1px solid rgba(255,59,59,0.3);border-radius:12px;padding:14px;margin-bottom:12px;font-size:14px;color:#FF6B6B;'>🔄 <b>REROUTE RECOMMENDED</b> — " + reroute_info['message'] + "</div>" if reroute_info['reroute'] else ""}

      {"<div style='background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.2);border-radius:12px;padding:12px;font-size:13px;color:#00D4AA;'>" + "📡 " + str(int(row.get('nearby_clusters',0))) + " IoT cluster(s) within 600m · max cluster size: " + str(int(row.get('max_cluster_size',0))) + "</div>" if int(row.get('nearby_clusters',0)) > 0 else ""}
    </div>
    """, unsafe_allow_html=True)

    # XGBoost feature importance
    if importances:
        st.markdown('<p class="section-label">what the model actually cares about 🔍</p>',
                    unsafe_allow_html=True)
        imp_df = (pd.DataFrame({"feature": list(importances.keys()),
                                "importance": list(importances.values())})
                    .sort_values("importance", ascending=False))
        st.dataframe(imp_df, use_container_width=True, hide_index=True)

    # Crime breakdown
    ward_crimes_df = ward_crime_types[ward_crime_types["ward_name"]==selected_ward].copy()
    if not ward_crimes_df.empty:
        ward_crimes_df = (ward_crimes_df.sort_values("count", ascending=False)
                                        .head(8)[["CrimeGroup_Name","count"]]
                                        .rename(columns={"CrimeGroup_Name":"crime type",
                                                         "count":"cases"}))
        st.markdown('<p class="section-label">crime breakdown — receipts 🧾</p>',
                    unsafe_allow_html=True)
        st.dataframe(ward_crimes_df, use_container_width=True, hide_index=True)

else:
    st.markdown("""
    <div style="background:rgba(255,255,255,0.03);border:1px dashed rgba(255,255,255,0.1);
                border-radius:16px;padding:40px;text-align:center;color:rgba(255,255,255,0.3);">
      <div style="font-size:2rem;margin-bottom:8px;">☝️</div>
      <div style="font-size:15px;">pick a ward above to get the full breakdown</div>
      <div style="font-size:12px;margin-top:4px;">pink circles on the map = live IoT clusters</div>
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center;color:rgba(255,255,255,0.2);font-size:12px;padding:16px 0 32px;">
  SafeRoute.ai · Bengaluru Crime Data (Karnataka Govt FIRs) · XGBoost + IDW + DBSCAN ensemble ·
  built with 💅 for the girls · <span style="color:#FF2D78;">data is power. share the route.</span>
</div>""", unsafe_allow_html=True)
