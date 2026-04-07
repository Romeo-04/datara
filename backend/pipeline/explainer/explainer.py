"""
Module 6 — Explainability Layer
Generates plain-language explanations for each division's UAI score
and intervention recommendation. No LLM required — template-based.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import pandas as pd
from backend.pipeline.uai.uai_engine import get_top_factors, FACTOR_LABELS

FACTOR_PHRASES = {
    "mismatch_rate": lambda pct: (
        f"{pct:.0%} of science and math teachers are teaching outside their specialization"
    ),
    "training_gap_rate": lambda pct: (
        f"{pct:.0%} of teachers have received fewer than 2 STAR trainings"
    ),
    "geo_disadvantage": lambda score: (
        f"the division has a high geographic isolation score ({score:.2f})"
    ),
    "staffing_pressure": lambda ltr: (
        f"the average learner-to-teacher ratio is {ltr:.1f}"
    ),
    "nat_gap_score": lambda mps: (
        f"the combined NAT Mean Percentage Score is {mps:.1f}%"
    ),
}

TIER_PREAMBLES = {
    "Critical Priority": "This division is flagged as Critical Priority.",
    "High Priority": "This division is flagged as High Priority.",
    "Standard Priority": "This division has standard-level support needs.",
}


def generate_explanation(row: pd.Series) -> str:
    tier = str(row.get("priority_tier", "Standard Priority"))
    preamble = TIER_PREAMBLES.get(tier, "This division has been assessed.")
    top_factors = get_top_factors(row, top_n=3)

    reason_parts = []
    for f in top_factors:
        key = f["key"]
        phrase = _render_factor_phrase(key, row)
        if phrase:
            reason_parts.append(phrase)

    reasons = "; ".join(reason_parts) if reason_parts else "multiple capacity gaps were identified"

    intervention = row.get("intervention_label", "STAR support")
    delivery = row.get("intervention_delivery", "")

    explanation = (
        f"{preamble} "
        f"The UAI score is {row.get('uai_score', 0):.3f} (rank #{int(row.get('priority_rank', 0))} nationally). "
        f"This ranking is driven by: {reasons}. "
        f"Recommended action: {intervention} ({delivery})."
    )
    return explanation


def _render_factor_phrase(factor_key: str, row: pd.Series) -> str:
    value_map = {
        "mismatch_rate": row.get("mismatch_rate", 0),
        "training_gap_rate": row.get("training_gap_rate", 0),
        "geo_disadvantage": row.get("avg_geo_disadvantage", 0),
        "staffing_pressure": row.get("avg_ltr", 30),
        "nat_gap_score": row.get("nat_combined_mps", 50),
    }
    fn = FACTOR_PHRASES.get(factor_key)
    val = value_map.get(factor_key)
    if fn and val is not None:
        try:
            return fn(val)
        except Exception:
            return ""
    return ""


def apply_explanations(division_df: pd.DataFrame) -> pd.DataFrame:
    df = division_df.copy()
    df["explanation"] = df.apply(generate_explanation, axis=1)
    return df
