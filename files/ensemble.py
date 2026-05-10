"""
SafeRoute.ai — Layer 4: Ensemble Combiner
==========================================
Merges outputs from all three models into a single safety score.

    safety_score = 1 - (
        0.35 * historical_risk   ← XGBoost (static, monthly update)
      + 0.30 * (1 - infra_score) ← Infra (more infra = safer, so invert)
      + 0.25 * live_threat_score ← DBSCAN (real-time)
      + 0.10 * time_penalty      ← Rule-based time multiplier
    )

Output: safety_score in [0, 1] where 1 = perfectly safe, 0 = avoid.
"""

import numpy as np
import pandas as pd
from datetime import datetime


# ── Time penalty ──────────────────────────────────────────────────────────

def time_penalty(hour: int | None = None,
                 is_festival: bool = False) -> float:
    """
    Returns a 0-1 penalty based on current time.
    Higher penalty = more dangerous time of day.

    Hour buckets (based on crime pattern analysis):
        22-04 → 0.90  (late night — highest risk)
        05-07 → 0.45  (early morning)
        08-20 → 0.10  (daytime — baseline)
        21    → 0.65  (early night — rising risk)

    Festival flag adds +0.15 (crowds, alcohol, reduced police presence).
    """
    if hour is None:
        hour = datetime.now().hour

    if   22 <= hour or hour <= 4:   base = 0.90
    elif  5 <= hour <= 7:           base = 0.45
    elif 21 <= hour <= 21:          base = 0.65
    else:                           base = 0.10

    penalty = base + (0.15 if is_festival else 0.0)
    return float(min(penalty, 1.0))


# ── Main combiner ─────────────────────────────────────────────────────────

def combine_scores(
    historical_df: pd.DataFrame,   # ward_name, historical_risk
    infra_df:      pd.DataFrame,   # ward_name, infra_score
    live_df:       pd.DataFrame,   # ward_name, live_threat_score
    hour:          int | None = None,
    is_festival:   bool = False,
    weights:       dict | None = None,
) -> pd.DataFrame:
    """
    Merge all model outputs into a final per-ward safety score.

    Parameters
    ----------
    historical_df : from crime_model.train_xgboost()
    infra_df      : from infra_model.compute_infra_scores()
    live_df       : from iot_model.compute_live_threat_scores()
    hour          : current hour (defaults to now)
    is_festival   : whether today is a known festival/event
    weights       : override default model weights

    Returns
    -------
    DataFrame: ward_name, safety_score, risk_level, risk_score,
               + all component scores for explainability
    """
    W = weights or {
        "historical": 0.35,
        "infra":      0.30,
        "live":       0.25,
        "time":       0.10,
    }
    assert abs(sum(W.values()) - 1.0) < 0.01, "Weights must sum to 1.0"

    t_penalty = time_penalty(hour, is_festival)

    # ── Merge all three DataFrames on ward_name ────────────────────────────
    df = historical_df[["ward_name", "historical_risk"]].copy()

    df = df.merge(
        infra_df[["ward_name", "infra_score",
                  "cctv_score", "light_score", "police_score"]],
        on="ward_name", how="left"
    )
    df = df.merge(
        live_df[["ward_name", "live_threat_score",
                 "nearby_clusters", "max_cluster_size"]],
        on="ward_name", how="left"
    )

    # Fill NaN for wards with no data
    df["historical_risk"]   = df["historical_risk"].fillna(0.5)
    df["infra_score"]       = df["infra_score"].fillna(0.5)
    df["live_threat_score"] = df["live_threat_score"].fillna(0.0)
    df["nearby_clusters"]   = df["nearby_clusters"].fillna(0).astype(int)
    df["max_cluster_size"]  = df["max_cluster_size"].fillna(0).astype(int)

    # ── Compute aggregate risk score ───────────────────────────────────────
    # Note: infra_score is SAFETY (higher = safer), so we invert it for risk
    df["risk_score"] = (
        W["historical"] * df["historical_risk"] +
        W["infra"]      * (1.0 - df["infra_score"]) +
        W["live"]       * df["live_threat_score"] +
        W["time"]       * t_penalty               # same for all wards
    )

    # Re-rank to ensure colour spread (percentile within current snapshot)
    df["risk_score"] = df["risk_score"].rank(pct=True)

    # Invert to safety score (1 = safe, 0 = dangerous)
    df["safety_score"] = 1.0 - df["risk_score"]

    # ── Risk level labels ──────────────────────────────────────────────────
    def risk_level(score):
        if score > 0.66:   return "high"
        elif score > 0.33: return "mid"
        else:              return "low"

    df["risk_level"]  = df["risk_score"].apply(risk_level)
    df["time_penalty"] = t_penalty
    df["hour_used"]    = hour if hour is not None else datetime.now().hour

    # ── Colour for map rendering ───────────────────────────────────────────
    COLOR_MAP = {"high": "#FF3B3B", "mid": "#FFB830", "low": "#00D4AA"}
    df["map_color"] = df["risk_level"].map(COLOR_MAP)

    # ── Explainability: which factor is dominant? ──────────────────────────
    def dominant_factor(row):
        contributions = {
            "crime history":  W["historical"] * row["historical_risk"],
            "infra gap":      W["infra"]      * (1 - row["infra_score"]),
            "live crowd":     W["live"]       * row["live_threat_score"],
            "time of day":    W["time"]       * row["time_penalty"],
        }
        return max(contributions, key=contributions.get)

    df["dominant_factor"] = df.apply(dominant_factor, axis=1)

    print(f"[Ensemble] Scores computed for {len(df)} wards at hour={df['hour_used'].iloc[0]}")
    print(f"[Ensemble] Distribution — "
          f"high: {(df['risk_level']=='high').sum()} | "
          f"mid: {(df['risk_level']=='mid').sum()} | "
          f"low: {(df['risk_level']=='low').sum()}")

    return df.reset_index(drop=True)


# ── Reroute trigger ────────────────────────────────────────────────────────

def should_reroute(ward_name: str,
                   scores_df: pd.DataFrame,
                   threshold: float = 0.60) -> dict:
    """
    Check whether a specific ward exceeds the risk threshold
    and return a structured reroute decision.

    Parameters
    ----------
    ward_name  : the ward a woman is about to enter
    scores_df  : output of combine_scores()
    threshold  : risk_score above which rerouting is recommended

    Returns
    -------
    dict with keys: reroute (bool), risk_score, risk_level,
                    dominant_factor, message
    """
    row = scores_df[scores_df["ward_name"] == ward_name]
    if row.empty:
        return {
            "reroute": False,
            "risk_score": None,
            "risk_level": "unknown",
            "dominant_factor": None,
            "message": "no data for this ward bestie, proceed carefully 🤷‍♀️"
        }

    row = row.iloc[0]
    reroute = bool(row["risk_score"] > threshold)

    MESSAGES = {
        True: {
            "crime history":  "this ward has a rough FIR history — not today bestie 🚨",
            "infra gap":      "no CCTV, no lights, no police nearby — we are NOT doing this 🚫",
            "live crowd":     "there's a big male cluster forming here rn — taking the long way 🔄",
            "time of day":    "it's late and this area gets sketchy — rerouting for your safety 🌙",
        },
        False: {
            "crime history":  "history's not perfect but you're okay for now 👀",
            "infra gap":      "limited infra but manageable — stay on main roads 💅",
            "live crowd":     "a few clusters nearby but nothing alarming — keep moving 🚶‍♀️",
            "time of day":    "it's a bit late but this area is holding up — normal precautions 🕐",
        }
    }

    factor = row.get("dominant_factor", "crime history")
    message = MESSAGES[reroute].get(factor, "stay safe bestie 💜")

    return {
        "reroute":          reroute,
        "risk_score":       float(row["risk_score"]),
        "safety_score":     float(row["safety_score"]),
        "risk_level":       row["risk_level"],
        "dominant_factor":  factor,
        "nearby_clusters":  int(row.get("nearby_clusters", 0)),
        "message":          message,
    }
