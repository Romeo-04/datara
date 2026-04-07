"""
Module 4 — Underserved Area Index (UAI) Engine
Computes a transparent, explainable composite score per division.
Score is based on five weighted factors.
All weights are documented and configurable.
"""

import pandas as pd
import numpy as np
from typing import Dict

# ---------------------------------------------------------------------------
# UAI Factor Definitions
# ---------------------------------------------------------------------------
# Each factor is normalized to [0, 1] where 1 = highest need / most underserved.
#
# Factor weights must sum to 1.0.
# Weights are chosen to reflect STAR's priorities:
#   - Specialization mismatch and training coverage are most actionable
#   - Geographic disadvantage signals access difficulty
#   - Staffing pressure (LTR) and novice rate are secondary signals
#   - NAT gap is an outcome indicator (used to corroborate, not lead)
# ---------------------------------------------------------------------------

UAI_WEIGHTS: Dict[str, float] = {
    "mismatch_rate":       0.30,  # % of teachers teaching outside specialization
    "training_gap_rate":   0.25,  # % of teachers with fewer than threshold trainings
    "geo_disadvantage":    0.20,  # geographic isolation score (0–1)
    "staffing_pressure":   0.15,  # learner-teacher ratio normalized
    "nat_gap_score":       0.10,  # outcome gap based on NAT MPS
}

assert abs(sum(UAI_WEIGHTS.values()) - 1.0) < 1e-9, "UAI weights must sum to 1.0"

FACTOR_LABELS = {
    "mismatch_rate":       "Specialization Mismatch",
    "training_gap_rate":   "Training Coverage Gap",
    "geo_disadvantage":    "Geographic Disadvantage",
    "staffing_pressure":   "Staffing Pressure",
    "nat_gap_score":       "Learning Outcome Gap (NAT)",
}


def compute_uai(division_df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds UAI score and factor breakdown to the division DataFrame.
    Returns the same DataFrame with added columns.
    """
    df = division_df.copy()

    # --- Normalize each factor to [0, 1] ---
    df["_norm_mismatch"] = _minmax(df["mismatch_rate"])
    df["_norm_training_gap"] = _minmax(df["training_gap_rate"])
    df["_norm_geo"] = _minmax(df["avg_geo_disadvantage"])
    df["_norm_staffing"] = _minmax(df["avg_ltr"])
    df["_norm_nat"] = _minmax(df["nat_gap_score"])

    # --- Weighted composite UAI score ---
    df["uai_score"] = (
        df["_norm_mismatch"]      * UAI_WEIGHTS["mismatch_rate"] +
        df["_norm_training_gap"]  * UAI_WEIGHTS["training_gap_rate"] +
        df["_norm_geo"]           * UAI_WEIGHTS["geo_disadvantage"] +
        df["_norm_staffing"]      * UAI_WEIGHTS["staffing_pressure"] +
        df["_norm_nat"]           * UAI_WEIGHTS["nat_gap_score"]
    ).round(4)

    # --- Priority rank (1 = most underserved) ---
    df["priority_rank"] = df["uai_score"].rank(ascending=False, method="min").astype(int)

    # --- Priority tier ---
    df["priority_tier"] = pd.qcut(
        df["uai_score"],
        q=3,
        labels=["Standard Priority", "High Priority", "Critical Priority"]
    )

    # --- Per-factor contribution (for explainability) ---
    df["factor_mismatch_contrib"] = (df["_norm_mismatch"] * UAI_WEIGHTS["mismatch_rate"]).round(4)
    df["factor_training_contrib"] = (df["_norm_training_gap"] * UAI_WEIGHTS["training_gap_rate"]).round(4)
    df["factor_geo_contrib"] = (df["_norm_geo"] * UAI_WEIGHTS["geo_disadvantage"]).round(4)
    df["factor_staffing_contrib"] = (df["_norm_staffing"] * UAI_WEIGHTS["staffing_pressure"]).round(4)
    df["factor_nat_contrib"] = (df["_norm_nat"] * UAI_WEIGHTS["nat_gap_score"]).round(4)

    # --- Drop internal normalization columns ---
    df = df.drop(columns=[c for c in df.columns if c.startswith("_norm_")])

    return df


def get_top_factors(row: pd.Series, top_n: int = 3) -> list:
    """
    Returns the top N contributing factors for a given division row.
    Used by the explainability layer.
    """
    factor_cols = {
        "factor_mismatch_contrib": "mismatch_rate",
        "factor_training_contrib": "training_gap_rate",
        "factor_geo_contrib": "geo_disadvantage",
        "factor_staffing_contrib": "staffing_pressure",
        "factor_nat_contrib": "nat_gap_score",
    }
    contribs = {label: row[col] for col, label in factor_cols.items()}
    sorted_factors = sorted(contribs.items(), key=lambda x: x[1], reverse=True)
    return [{"factor": FACTOR_LABELS[k], "key": k, "contribution": round(v, 4)}
            for k, v in sorted_factors[:top_n]]


def _minmax(series: pd.Series) -> pd.Series:
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)
