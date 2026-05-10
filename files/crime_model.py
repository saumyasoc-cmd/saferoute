"""
SafeRoute.ai — Layer 1: XGBoost Historical Crime Risk Model
============================================================
Input : ward-level FIR aggregations + time features
Output: historical_risk score (0-1, percentile-ranked) per ward
        + feature importance dict for the dashboard
"""

import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings("ignore")


# ── Feature engineering ────────────────────────────────────────────────────

def build_crime_features(gdf: pd.DataFrame) -> pd.DataFrame:
    """
    Takes the spatially-joined FIR GeoDataFrame and returns
    a ward-level feature matrix ready for XGBoost.

    Expected columns in gdf (auto-detected, case-insensitive):
        ward_name, date, CrimeGroup_Name (or similar),
        Female (or victim_female), Girl (or victim_girl)
    """
    df = gdf.copy().reset_index(drop=True)

    # ── detect column names ────────────────────────────────────────────────
    female_col = next((c for c in df.columns if c.lower() in
                       ("female", "victim_female", "females")), None)
    girl_col   = next((c for c in df.columns if c.lower() in
                       ("girl", "victim_girl", "girls")), None)
    crime_col  = next((c for c in df.columns if c.lower() in
                       ("crimegroup_name", "crime_group_name",
                        "crimehead_name", "crime_name")), None)

    # ── per-ward base counts ───────────────────────────────────────────────
    counts = df.groupby("ward_name").size().rename("total_firs").reset_index()

    feats = counts.copy()

    # women crime ratio
    if female_col or girl_col:
        w_sum = pd.Series(0, index=range(len(counts)))
        if female_col:
            w_sum += df.groupby("ward_name")[female_col].sum() \
                       .reindex(counts["ward_name"]).values
        if girl_col:
            w_sum += df.groupby("ward_name")[girl_col].sum() \
                       .reindex(counts["ward_name"]).values
        feats["women_firs"]   = w_sum.values
        feats["women_ratio"]  = feats["women_firs"] / (feats["total_firs"] + 1)
    else:
        feats["women_firs"]  = 0
        feats["women_ratio"] = 0.0

    # ── time-series lag features ───────────────────────────────────────────
    if "date" in df.columns and df["date"].notna().any():
        ts = (df.groupby(["ward_name", "date"])
                .size()
                .reset_index(name="daily_count")
                .sort_values(["ward_name", "date"]))

        ts["lag_1"]  = ts.groupby("ward_name")["daily_count"].shift(1)
        ts["lag_7"]  = ts.groupby("ward_name")["daily_count"].shift(7)
        ts["lag_30"] = ts.groupby("ward_name")["daily_count"].shift(30)

        # rolling stats per ward
        ts["roll_7_mean"] = (ts.groupby("ward_name")["daily_count"]
                               .transform(lambda x: x.shift(1).rolling(7).mean()))
        ts["roll_7_std"]  = (ts.groupby("ward_name")["daily_count"]
                               .transform(lambda x: x.shift(1).rolling(7).std()))

        latest = ts.groupby("ward_name").tail(1)[
            ["ward_name", "lag_1", "lag_7", "lag_30",
             "roll_7_mean", "roll_7_std"]
        ].reset_index(drop=True)

        feats = feats.merge(latest, on="ward_name", how="left")
    else:
        for col in ["lag_1", "lag_7", "lag_30", "roll_7_mean", "roll_7_std"]:
            feats[col] = np.nan

    # ── time-of-day / day-of-week crime concentration ──────────────────────
    if "date" in df.columns and df["date"].notna().any():
        df["hour"]        = df["date"].dt.hour
        df["day_of_week"] = df["date"].dt.dayofweek
        df["is_night"]    = df["hour"].between(21, 23) | df["hour"].between(0, 5)
        df["is_weekend"]  = df["day_of_week"] >= 5

        night_ratio = (df.groupby("ward_name")["is_night"].mean()
                         .reindex(counts["ward_name"]).values)
        weekend_ratio = (df.groupby("ward_name")["is_weekend"].mean()
                           .reindex(counts["ward_name"]).values)
        feats["night_crime_ratio"]   = night_ratio
        feats["weekend_crime_ratio"] = weekend_ratio
    else:
        feats["night_crime_ratio"]   = 0.5
        feats["weekend_crime_ratio"] = 0.5

    # ── crime type diversity (entropy) ────────────────────────────────────
    if crime_col:
        def entropy(series):
            p = series.value_counts(normalize=True)
            return -(p * np.log(p + 1e-10)).sum()

        crime_entropy = (df.groupby("ward_name")[crime_col]
                           .apply(entropy)
                           .reindex(counts["ward_name"]).values)
        feats["crime_diversity"] = crime_entropy
    else:
        feats["crime_diversity"] = 0.0

    # ── log-scale total for skew reduction ────────────────────────────────
    feats["log_total_firs"] = np.log1p(feats["total_firs"])

    return feats.reset_index(drop=True)


# ── Model training ─────────────────────────────────────────────────────────

def train_xgboost(feats: pd.DataFrame) -> tuple:
    """
    Train an XGBoost regressor to score historical crime risk per ward.

    Returns
    -------
    ward_scores : pd.DataFrame  [ward_name, historical_risk, ...]
    model       : XGBRegressor  (fitted, for future prediction)
    importances : dict          {feature_name: importance_score}
    """
    FEATURE_COLS = [
        "log_total_firs", "women_ratio", "night_crime_ratio",
        "weekend_crime_ratio", "crime_diversity",
        "lag_1", "lag_7", "lag_30", "roll_7_mean", "roll_7_std"
    ]

    available = [c for c in FEATURE_COLS if c in feats.columns]
    X = feats[available].fillna(feats[available].median())

    # ── Target: composite risk score ─────────────────────────────────────
    # We construct a supervised-style target from what we know:
    # high women_ratio + high log_total_firs + high night_ratio = risky
    y = (
        0.5 * feats["log_total_firs"].fillna(0) +
        0.3 * feats.get("women_ratio", pd.Series(0, index=feats.index)).fillna(0) +
        0.2 * feats.get("night_crime_ratio", pd.Series(0.5, index=feats.index)).fillna(0)
    )
    y = (y - y.min()) / (y.max() - y.min() + 1e-10)  # normalise 0-1

    model = XGBRegressor(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbosity=0,
    )
    model.fit(X, y)

    # Cross-val score (just for info — not used for ranking)
    cv_scores = cross_val_score(model, X, y, cv=3, scoring="r2")

    preds = model.predict(X)
    # Percentile-rank so colours always spread across green/amber/red
    feats = feats.copy()
    feats["xgb_raw"]        = preds
    feats["historical_risk"] = pd.Series(preds).rank(pct=True).values

    importances = dict(zip(available, model.feature_importances_.tolist()))

    print(f"[XGBoost] R² CV mean={cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
    print(f"[XGBoost] Top features: "
          f"{sorted(importances.items(), key=lambda x: -x[1])[:3]}")

    return feats[["ward_name", "historical_risk", "xgb_raw",
                  "total_firs", "women_firs", "women_ratio",
                  "night_crime_ratio", "crime_diversity"]].copy(), model, importances
