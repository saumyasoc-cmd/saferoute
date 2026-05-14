"""
SafeRoute.ai — Main Dashboard (UI only)
========================================
This file is intentionally thin.
All logic lives in models/ and data/.

Layout:
  sidebar        → controls & weights
  hero + metrics → summary numbers
  weight strip   → active model weights
  distribution   → ward risk breakdown
  map            → folium choropleth
  drill-down     → per-ward detail
  footer
"""

import os
import sys
import random
import hashlib

import streamlit as st
import pandas as pd
import numpy as np
import folium
import geopandas as gpd
from streamlit_folium import st_folium
from datetime import datetime

# ── resolve paths ──────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
DATA_PATH   = os.path.join(DATA_DIR, "FIR_Details_Data.csv")
WARD_PATH   = os.path.join(DATA_DIR, "Ward.xml")
CCTV_PATH   = os.path.join(DATA_DIR, "bbmp_cctv.csv")
LIGHTS_PATH = os.path.join(DATA_DIR, "bbmp_streetlights.csv")
POLICE_PATH = os.path.join(DATA_DIR, "bbmp_police_stations.csv")

# ── module imports ─────────────────────────────────────────────────────────
sys.path.insert(0, BASE_DIR)

from data.loaders import load_fir, load_wards, spatial_join, ward_crime_breakdown
from data.live    import read_iot_stream, fetch_overpass_infrastructure, check_connections
from models.crime_model import build_crime_features, train_xgboost
from models.infra_model  import compute_infra_scores
from models.iot_model    import detect_male_clusters, compute_live_threat_scores
from models.ensemble     import combine_scores, should_reroute, time_penalty

# ──────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="SafeRoute.ai — not today bestie 🛡️",
    page_icon="🛡️"
)

# ──────────────────────────────────────────────────────────────────────────
# CSS
# ──────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');
:root{
  --hot-pink:#FF2D78; --neon-lime:#C8F135; --electric-blue:#3D5BFF;
  --midnight:#0A0A1A; --off-white:#F5F3EF; --warn-amber:#FFB830;
  --safe-teal:#00D4AA; --danger-red:#FF3B3B; --glass:rgba(255,255,255,0.06);
}
html,body,[data-testid="stAppViewContainer"]{
  background:var(--midnight)!important;color:var(--off-white)!important;
  font-family:'DM Sans',sans-serif!important;}
[data-testid="stHeader"]{background:transparent!important;}
[data-testid="stSidebar"]{background:#0F0F22!important;border-right:1px solid rgba(255,255,255,0.07)!important;}
h1,h2,h3{font-family:'Syne',sans-serif!important;color:var(--off-white)!important;letter-spacing:-0.03em!important;}
[data-testid="metric-container"]{background:var(--glass)!important;border:1px solid rgba(255,255,255,0.1)!important;border-radius:16px!important;padding:1rem!important;}
[data-testid="stMetricLabel"]>div{color:rgba(255,255,255,0.5)!important;font-size:12px!important;text-transform:uppercase!important;letter-spacing:0.08em!important;}
[data-testid="stMetricValue"]>div{color:var(--neon-lime)!important;font-family:'Syne',sans-serif!important;font-size:2rem!important;font-weight:800!important;}
hr{border-color:rgba(255,255,255,0.08)!important;}
[data-testid="stDataFrame"]{border:1px solid rgba(255,255,255,0.08)!important;border-radius:12px!important;}
.badge-red  {background:rgba(255,59,59,0.15); color:#FF3B3B;border:1px solid rgba(255,59,59,0.3); border-radius:100px;padding:3px 12px;font-size:12px;font-weight:500;}
.badge-amber{background:rgba(255,184,48,0.15);color:#FFB830;border:1px solid rgba(255,184,48,0.3);border-radius:100px;padding:3px 12px;font-size:12px;font-weight:500;}
.badge-teal {background:rgba(0,212,170,0.15); color:#00D4AA;border:1px solid rgba(0,212,170,0.3); border-radius:100px;padding:3px 12px;font-size:12px;font-weight:500;}
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
# DATA SOURCE FLAGS  (computed once, before sidebar renders)
# ──────────────────────────────────────────────────────────────────────────
cctv_ok   = os.path.exists(CCTV_PATH)
lights_ok = os.path.exists(LIGHTS_PATH)
police_ok = os.path.exists(POLICE_PATH)
_use_sim_bbmp = not (cctv_ok and lights_ok and police_ok)

# ──────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────
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
    WEIGHTS = {"historical": w_hist, "infra": w_infra,
               "live": w_live, "time": w_time}

    st.markdown("---")
    st.markdown('<p class="section-label">🗂️ data sources</p>', unsafe_allow_html=True)
    st.markdown(
        f"{'✅' if cctv_ok   else '⚠️'} CCTV &nbsp;"
        f"{'✅' if lights_ok else '⚠️'} Lights &nbsp;"
        f"{'✅' if police_ok else '⚠️'} Police",
        unsafe_allow_html=True
    )
    if _use_sim_bbmp:
        st.caption("Place bbmp_*.csv in data/ for real infra scoring")

    st.markdown("---")
    st.markdown('<p class="section-label">📡 IoT source</p>', unsafe_allow_html=True)
    iot_source = st.radio(
        "", ["simulate", "kafka", "redis"],
        horizontal=True, label_visibility="collapsed",
        help="simulate = fresh random pings every 60s | kafka/redis = real devices"
    )
    if iot_source != "simulate":
        conn = check_connections()
        st.caption(
            f"kafka {'✅' if conn['kafka'] else '❌'} &nbsp;"
            f"redis {'✅' if conn['redis'] else '❌'} &nbsp;"
            f"overpass {'✅' if conn['overpass'] else '❌'}",
        )

    st.markdown("---")
    show_debug = st.toggle("🐛 debug", value=False)

    st.markdown("---")
    st.markdown('<p class="section-label">⏱️ cache status</p>', unsafe_allow_html=True)
    st.caption("XGBoost + Infra: refreshes every **60 min**")
    st.caption("IoT clusters: refreshes every **60 sec**")
    st.caption(f"Last render: **{datetime.now().strftime('%H:%M:%S')}**")
    iot_status_placeholder = st.empty()   # filled after _run_iot() below

# ──────────────────────────────────────────────────────────────────────────
# CACHED DATA LOADING  (@st.cache_data lives here, not in loaders.py)
# ──────────────────────────────────────────────────────────────────────────
@st.cache_data
def _load_fir():
    return load_fir(DATA_PATH)

@st.cache_data
def _load_wards():
    return load_wards(WARD_PATH)

df_blr = _load_fir()
wards  = _load_wards()
gdf    = spatial_join(df_blr, wards)

if show_debug:
    with st.sidebar.expander("🐛 spatial join"):
        st.write(f"FIR rows: **{len(df_blr):,}** → joined: **{len(gdf):,}**")
        st.write(f"Unique wards matched: **{gdf['ward_name'].nunique()}**")
        st.dataframe(gdf["ward_name"].value_counts().head(15).reset_index())

# ──────────────────────────────────────────────────────────────────────────
# MODEL PIPELINE
# Each layer is cached with a TTL:
#   - XGBoost + Infra: 1 hour  (static data, no point rerunning)
#   - DBSCAN IoT     : 60 secs (simulated for now, will be live data later)
#   - Ensemble       : 60 secs (depends on IoT + hour slider)
# Changing the hour/festival/weight sliders still triggers a rerun but
# only the ensemble (fast) recombines — the heavy models stay cached.
# ──────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def _run_xgboost(_gdf):
    feats = build_crime_features(_gdf)
    return train_xgboost(feats)

@st.cache_data(ttl=3600, show_spinner=False)
def _run_infra(_wards, use_simulated):
    return compute_infra_scores(_wards, data_dir=DATA_DIR, use_simulated=use_simulated)

@st.cache_data(ttl=60, show_spinner=False)
def _run_iot(_wards, hour, source="simulate"):
    bounds = tuple(_wards.total_bounds)  # (minx, miny, maxx, maxy)
    try:
        pings = read_iot_stream(source=source, bounds=bounds, hour=hour)
    except NotImplementedError as e:
        st.sidebar.warning(f"IoT source unavailable: {e}\nFalling back to simulate.")
        pings = read_iot_stream(source="simulate", bounds=bounds, hour=hour)

    clusters = detect_male_clusters(
        pings,
        night_only=False,   # always cluster; time_penalty in ensemble handles night weighting
        eps_m=200, min_samples=5   # lowered min_samples: easier to form clusters
    )
    live = compute_live_threat_scores(_wards, clusters)
    return clusters, live, len(pings), pings["source"].iloc[0] if len(pings) else "simulate"

@st.cache_data(ttl=60, show_spinner=False)
def _run_ensemble(_hist, _infra, _live, hour, is_festival, weights_tuple):
    # weights passed as tuple so it's hashable for the cache key
    weights = dict(weights_tuple)
    return combine_scores(
        _hist, _infra, _live,
        hour=hour, is_festival=is_festival, weights=weights
    )

with st.spinner("🔮 XGBoost is thinking..."):
    historical_df, xgb_model, importances = _run_xgboost(gdf)

with st.spinner("🏙️ Scoring BBMP infrastructure..."):
    infra_df = _run_infra(wards, _use_sim_bbmp)

with st.spinner("📡 DBSCAN cluster detection..."):
    clusters_df, live_df, n_pings, active_source = _run_iot(wards, sim_hour, iot_source)

iot_status_placeholder.caption(f"IoT: **{active_source}** · {n_pings:,} pings")

scores_df = _run_ensemble(
    historical_df, infra_df, live_df,
    sim_hour, is_festival,
    tuple(sorted(WEIGHTS.items()))   # dict → hashable tuple for cache key
)

ward_crime_types = ward_crime_breakdown(gdf)
t_pen = time_penalty(sim_hour, is_festival)

# ──────────────────────────────────────────────────────────────────────────
# CONSTANTS used by UI
# ──────────────────────────────────────────────────────────────────────────
COLOR_MAP   = {"high": "#FF3B3B", "mid": "#FFB830",
               "low": "#00D4AA", "unknown": "#4B5563"}
BADGE_LABEL = {"high": "🚨 HIGH RISK", "mid": "👀 WATCH OUT",
               "low": "✅ SAFE", "unknown": "❓ NO DATA"}
BADGE_CLS   = {"high": "badge-red", "mid": "badge-amber", "low": "badge-teal"}

VIBES = {
    "high": [
        "bestie NO 🚨 this ward is giving main villain energy rn",
        "not safe sis. pepper spray is not optional here",
        "red flag central fr fr. rerouting you IMMEDIATELY 💀",
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

# ──────────────────────────────────────────────────────────────────────────
# HERO HEADER
# ──────────────────────────────────────────────────────────────────────────
col_left, col_right = st.columns([3, 1])
with col_left:
    st.markdown('<p class="hero-title">SafeRoute.ai</p>', unsafe_allow_html=True)
    night_str = "🌙 night mode" if (sim_hour >= 22 or sim_hour <= 5) else f"☀️ {sim_hour:02d}:00"
    st.markdown(
        f'<p class="tagline">real ones protect each other &nbsp;·&nbsp;'
        f' bengaluru ward safety &nbsp;·&nbsp; {night_str}</p>',
        unsafe_allow_html=True
    )
    if not _use_sim_bbmp:
        _n_cctv   = sum(1 for _ in open(CCTV_PATH))   - 1
        _n_lights = sum(1 for _ in open(LIGHTS_PATH)) - 1
        _n_police = sum(1 for _ in open(POLICE_PATH)) - 1
        src_chips = (
            f'<span class="src-chip">{_n_cctv:,} CCTVs</span>'
            f'<span class="src-chip">{_n_lights:,} street lights</span>'
            f'<span class="src-chip">{_n_police:,} police stations</span>'
        )
    else:
        src_chips = '<span class="src-chip" style="color:#FFB830;border-color:rgba(255,184,48,0.25);">simulated infra</span>'
    st.markdown(
        f'<span class="src-chip">Karnataka FIR data</span>'
        f'{src_chips}'
        f'<span class="src-chip">XGBoost + DBSCAN</span>',
        unsafe_allow_html=True
    )

with col_right:
    high_count  = int((scores_df["risk_level"] == "high").sum())
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
    (mc1, "XGBoost crime",  w_hist,  "historical FIRs",             "#C8F135"),
    (mc2, "BBMP infra IDW", w_infra, "CCTV · lights · police",      "#3D5BFF"),
    (mc3, "DBSCAN IoT",     w_live,  f"{len(clusters_df)} clusters", "#FF2D78"),
    (mc4, "time penalty",   t_pen,   f"hour {sim_hour:02d}:00",     "#FFB830"),
]:
    col.markdown(f"""
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:14px;">
      <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.1em;color:rgba(255,255,255,0.35);margin-bottom:4px;">{lbl}</div>
      <div style="font-family:'Syne',sans-serif;font-size:1.4rem;font-weight:800;color:{clr};">{val:.0%}</div>
      <div style="font-size:11px;color:rgba(255,255,255,0.3);margin-top:2px;">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# WARD DISTRIBUTION STRIP
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
    (wd1, "High Risk",   _n_high, _pct_h, "#FF3B3B", "rgba(255,59,59,0.08)"),
    (wd2, "Watch Out",   _n_mid,  _pct_m, "#FFB830", "rgba(255,184,48,0.08)"),
    (wd3, "Mostly Safe", _n_low,  _pct_l, "#00D4AA", "rgba(0,212,170,0.08)"),
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

# ──────────────────────────────────────────────────────────────────────────
# MAP
# ──────────────────────────────────────────────────────────────────────────
st.markdown(
    '<p class="section-label">bengaluru ward map — double-click any ward to zoom into IoT view ☕</p>',
    unsafe_allow_html=True
)

wards_merged = wards.merge(scores_df, on="ward_name", how="left")
map_ = folium.Map(location=[12.97, 77.59], zoom_start=11,
                  tiles="CartoDB dark_matter")

# ── Ward polygons (city-overview layer) ────────────────────────────────────
ward_group = folium.FeatureGroup(name="wards", show=True)

for _, row in wards_merged.iterrows():
    score  = float(row.get("risk_score",  0.5) or 0.5)
    label  = str(row.get("risk_level",   "unknown") or "unknown")
    color  = COLOR_MAP.get(label, "#4B5563")
    wname  = str(row["ward_name"] or "Unknown")
    factor = str(row.get("dominant_factor", "—") or "—")
    safety = float(row.get("safety_score", 0.5) or 0.5)
    nc     = int(row.get("nearby_clusters", 0) or 0)
    iot_line = (
        f"<div style='font-size:11px;color:#FF2D78;margin-top:4px;'>"
        f"📡 {nc} IoT cluster(s) nearby</div>"
    ) if nc > 0 else ""

    tt = f"""
    <div style="font-family:'DM Sans',sans-serif;background:#0A0A1A;
                border:1px solid {color};border-radius:12px;
                padding:14px 18px;min-width:220px;color:#F5F3EF;">
      <div style="font-size:16px;font-weight:700;margin-bottom:6px;">{wname}</div>
      <div style="background:{color}22;color:{color};border:1px solid {color}55;
                  border-radius:100px;display:inline-block;padding:2px 12px;
                  font-size:11px;font-weight:600;margin-bottom:8px;">
        {BADGE_LABEL.get(label, "?")}
      </div>
      <div style="font-size:12px;color:rgba(255,255,255,0.5);">
        Risk: <b style="color:{color}">{score:.2f}</b>
        &nbsp;|&nbsp;
        Safety: <b style="color:#C8F135">{safety:.2f}</b>
      </div>
      <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-top:4px;">
        ⚡ driven by: <b style="color:#7B8FFF">{factor}</b>
      </div>
      {iot_line}
    </div>"""

    folium.GeoJson(
        row["geometry"],
        style_function=lambda x, c=color: {
            "fillColor": c, "color": "#1A1A2E",
            "weight": 0.8, "fillOpacity": 0.65,
            "className": "ward-poly",
        },
        highlight_function=lambda x, c=color: {
            "weight": 2.5, "color": c, "fillOpacity": 0.85
        },
        tooltip=folium.Tooltip(tt, sticky=True),
    ).add_to(ward_group)

ward_group.add_to(map_)

# ── IoT clusters (always present, more visible when zoomed in) ─────────────
iot_group = folium.FeatureGroup(name="iot_clusters", show=True)

for _, cl in clusters_df.iterrows():
    size   = int(cl["size"])
    threat = cl["threat_level"]
    # colour by threat level
    dot_color = {
        "critical": "#FF2D78",
        "high":     "#FF6B35",
        "moderate": "#FFB830",
        "low":      "#C8F135",
    }.get(threat, "#FF2D78")

    folium.CircleMarker(
        location=[cl["centroid_lat"], cl["centroid_lon"]],
        radius=max(7, size // 3),
        color=dot_color, fill=True, fill_color=dot_color,
        fill_opacity=0.5, weight=1.5,
        tooltip=folium.Tooltip(f"""
        <div style="font-family:'DM Sans',sans-serif;background:#0A0A1A;
                    border:1px solid {dot_color};border-radius:10px;
                    padding:10px 14px;color:#F5F3EF;font-size:12px;">
          <b style="color:{dot_color}">📡 IoT cluster</b><br>
          {size} male devices · <b>{threat}</b><br>
          <span style="color:rgba(255,255,255,0.4);">
            {cl['centroid_lat']:.4f}, {cl['centroid_lon']:.4f}
          </span>
        </div>""", sticky=True),
        class_name="iot-cluster-dot",
    ).add_to(iot_group)

iot_group.add_to(map_)

# ── JS: zoom-fade + double-click clean mode ────────────────────────────────
# All JS runs inside the map iframe via MacroElement — this is the correct
# way to reach Leaflet's map object from within Folium.
#
# Behaviour:
#   zoom < 13  → wards visible (opacity fades as you zoom in), clusters shown
#   zoom >= 13 → ward fill opacity very low (0.12), clusters more prominent
#   double-click anywhere → if zoom >= 13, hide wards entirely, show ONLY
#                           IoT clusters ("street view" mode)
#                           double-click again → back to normal
from branca.element import MacroElement
from jinja2 import Template

zoom_js = MacroElement()
zoom_js._template = Template("""
{% macro script(this, kwargs) %}
(function() {
  var map = {{ this._parent.get_name() }};
  var wardGroup   = null;
  var iotGroup    = null;
  var cleanMode   = false;

  // Find our named feature groups
  map.eachLayer(function(layer) {
    if (layer.options && layer.options.name === 'wards')       wardGroup = layer;
    if (layer.options && layer.options.name === 'iot_clusters') iotGroup = layer;
  });

  // ── opacity by zoom ───────────────────────────────────────────────────
  function applyZoomStyle() {
    if (cleanMode) return;   // don't fight clean mode
    var z = map.getZoom();
    var opacity;
    if      (z >= 14) opacity = 0.12;
    else if (z >= 13) opacity = 0.28;
    else if (z >= 12) opacity = 0.45;
    else              opacity = 0.65;

    if (wardGroup) {
      wardGroup.eachLayer(function(l) {
        if (l.setStyle) l.setStyle({ fillOpacity: opacity });
      });
    }
  }

  // ── double-click → clean / restore ───────────────────────────────────
  map.on('dblclick', function(e) {
    // prevent default zoom-on-dblclick fighting us
    map.doubleClickZoom.disable();

    cleanMode = !cleanMode;

    if (cleanMode) {
      // hide ward fills, keep borders faint for orientation
      if (wardGroup) {
        wardGroup.eachLayer(function(l) {
          if (l.setStyle) l.setStyle({ fillOpacity: 0, opacity: 0.15, weight: 0.4 });
        });
      }
      // make IoT clusters pop
      if (iotGroup) {
        iotGroup.eachLayer(function(l) {
          if (l.setRadius) {
            l.setStyle({ fillOpacity: 0.85, opacity: 1, weight: 2 });
          }
        });
      }
    } else {
      // restore
      map.doubleClickZoom.enable();
      applyZoomStyle();
      if (iotGroup) {
        iotGroup.eachLayer(function(l) {
          if (l.setRadius) {
            l.setStyle({ fillOpacity: 0.5, opacity: 1, weight: 1.5 });
          }
        });
      }
    }
  });

  map.on('zoomend', applyZoomStyle);
  applyZoomStyle();
})();
{% endmacro %}
""")
zoom_js.add_to(map_)

legend_html = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:#0A0A1A;
            border:1px solid rgba(255,255,255,0.12);border-radius:14px;
            padding:14px 18px;font-family:'DM Sans',sans-serif;">
  <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.1em;
              color:rgba(255,255,255,0.35);margin-bottom:10px;">risk level</div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FF3B3B;"></div>
    <span style="color:#FF3B3B;font-size:12px;">high (&gt;0.66)</span></div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FFB830;"></div>
    <span style="color:#FFB830;font-size:12px;">mid (0.33–0.66)</span></div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#00D4AA;"></div>
    <span style="color:#00D4AA;font-size:12px;">low (&lt;0.33)</span></div>
  <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#FF2D78;"></div>
    <span style="color:#FF2D78;font-size:12px;">critical cluster</span></div>
  <div style="display:flex;align-items:center;gap:8px;">
    <div style="width:10px;height:10px;border-radius:50%;background:#C8F135;opacity:0.8;"></div>
    <span style="color:#C8F135;font-size:12px;">low cluster</span></div>
  <div style="margin-top:10px;font-size:10px;color:rgba(255,255,255,0.25);
              border-top:1px solid rgba(255,255,255,0.08);padding-top:8px;">
    double-click → IoT-only view<br>double-click again → restore
  </div>
</div>"""
map_.get_root().html.add_child(folium.Element(legend_html))
st_folium(map_, use_container_width=True, height=580)
st.markdown("---")

# ──────────────────────────────────────────────────────────────────────────
# WARD DRILL-DOWN
# ──────────────────────────────────────────────────────────────────────────
st.markdown('<p class="section-label">ward details — the full tea ☕</p>',
            unsafe_allow_html=True)

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
    badge  = BADGE_CLS.get(label, "badge-amber")
    pct    = int(rscore * 100)
    nc     = int(row.get("nearby_clusters", 0) or 0)
    ms     = int(row.get("max_cluster_size",  0) or 0)
    fir_count = int(gdf[gdf["ward_name"] == selected_ward].shape[0])

    # Stable vibe text — deterministic per ward name
    _seed = int(hashlib.md5(selected_ward.encode()).hexdigest(), 16) % (2 ** 31)
    random.seed(_seed)
    vibe = random.choice(VIBES.get(label, VIBES["mid"]))
    random.seed()

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
          <div style="font-family:'Syne',sans-serif;font-size:1.8rem;font-weight:800;letter-spacing:-0.03em;color:#F5F3EF;">
            {selected_ward}
          </div>
          <span class="{badge}" style="margin-top:6px;display:inline-block;">
            {'🚨 HIGH RISK' if label=='high' else '👀 WATCH OUT' if label=='mid' else '✅ MOSTLY SAFE'}
          </span>
          <span class="factor-pill">⚡ driven by {row.get('dominant_factor','—')}</span>
          <div style="font-size:12px;color:rgba(255,255,255,0.3);margin-top:8px;">
            {fir_count:,} FIRs recorded &nbsp;·&nbsp;
            safety score: {float(row.get('safety_score', 0)):.2f}
          </div>
        </div>
        <div style="text-align:right;">
          <div style="font-family:'Syne',sans-serif;font-size:3rem;font-weight:800;color:{color};line-height:1;">{pct}</div>
          <div style="font-size:11px;color:rgba(255,255,255,0.4);text-transform:uppercase;letter-spacing:0.08em;">risk score</div>
        </div>
      </div>

      <div class="risk-bar-wrap" style="margin-bottom:20px;">
        <div class="risk-bar" style="width:{pct}%;background:{color};"></div>
      </div>

      <div style="font-size:17px;line-height:1.5;font-weight:500;color:rgba(255,255,255,0.8);margin-bottom:20px;font-style:italic;">
        "{vibe}"
      </div>

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
        st.markdown('<p class="section-label">what the model cares about 🔍</p>',
                    unsafe_allow_html=True)
        imp_df = (pd.DataFrame({"feature": list(importances.keys()),
                                "importance": list(importances.values())})
                  .sort_values("importance", ascending=False)
                  .reset_index(drop=True))
        st.dataframe(imp_df, use_container_width=True, hide_index=True)

    # Crime type breakdown
    ward_crimes = ward_crime_types[ward_crime_types["ward_name"] == selected_ward].copy()
    if not ward_crimes.empty:
        ward_crimes = (
            ward_crimes.sort_values("count", ascending=False)
            .head(8)[["CrimeGroup_Name", "count"]]
            .rename(columns={"CrimeGroup_Name": "crime type", "count": "cases"})
        )
        st.markdown('<p class="section-label">crime breakdown 🧾</p>',
                    unsafe_allow_html=True)
        st.dataframe(ward_crimes, use_container_width=True, hide_index=True)

    # BBMP infra breakdown
    ward_infra = infra_df[infra_df["ward_name"] == selected_ward]
    if not ward_infra.empty:
        wi = ward_infra.iloc[0]
        st.markdown('<p class="section-label">BBMP infra coverage 🏙️</p>',
                    unsafe_allow_html=True)
        ia, ib, ic = st.columns(3)
        for col, lbl, val, clr in [
            (ia, "CCTV coverage",        wi.get("cctv_score",   0), "#C8F135"),
            (ib, "Street light coverage", wi.get("light_score",  0), "#FFB830"),
            (ic, "Police proximity",      wi.get("police_score", 0), "#3D5BFF"),
        ]:
            col.markdown(f"""
            <div style="background:rgba(255,255,255,0.04);border-radius:12px;
                        padding:14px;text-align:center;">
              <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.08em;
                          color:rgba(255,255,255,0.35);margin-bottom:6px;">{lbl}</div>
              <div style="font-family:'Syne',sans-serif;font-size:1.5rem;
                          font-weight:800;color:{clr};">{float(val):.2f}</div>
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
<div style="text-align:center;color:rgba(255,255,255,0.2);font-size:12px;
            padding:16px 0 32px;line-height:2;">
  SafeRoute.ai &nbsp;·&nbsp; Karnataka Govt FIRs &nbsp;·&nbsp;
  BBMP CCTV / Street Lights / Police Stations &nbsp;·&nbsp;
  XGBoost + IDW + DBSCAN ensemble<br>
  built with 💅 for the girls &nbsp;·&nbsp;
  <span style="color:#FF2D78;">data is power. share the route.</span>
</div>""", unsafe_allow_html=True)