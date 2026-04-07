"""
Module 5 — Intervention Recommender
Maps each division's UAI factor profile to the most appropriate
STAR capacity-building intervention type.
Rules are transparent, documented, and based on dominant gap factors.
"""

import pandas as pd
from typing import Dict, List

# ---------------------------------------------------------------------------
# STAR Intervention Catalog
# ---------------------------------------------------------------------------

INTERVENTIONS: Dict[str, Dict] = {
    "specialization_upskilling": {
        "label": "Specialization Upskilling Program",
        "description": (
            "Deploy subject-specific upskilling workshops targeting teachers "
            "who are teaching outside their area of specialization. "
            "Focus on Biology, Chemistry, Physics, and Mathematics alignment."
        ),
        "delivery": "Face-to-face intensive (3–5 days)",
        "target": "Teachers with mismatched specialization",
    },
    "mobile_training_deployment": {
        "label": "Mobile Training Deployment",
        "description": (
            "Deploy STAR mobile training teams directly to the division. "
            "Prioritize areas with low training coverage where teachers "
            "have received fewer than 2 STAR trainings."
        ),
        "delivery": "On-site, itinerant training teams",
        "target": "Divisions with high training gap rate",
    },
    "blended_remote_program": {
        "label": "Blended / Asynchronous Learning Program",
        "description": (
            "Provide STAR digital learning modules and scheduled virtual sessions "
            "for geographically isolated divisions where face-to-face deployment "
            "is logistically difficult."
        ),
        "delivery": "Online + modular self-paced",
        "target": "Geographically isolated or remote divisions",
    },
    "coaching_mentoring": {
        "label": "In-School Coaching and Mentoring",
        "description": (
            "Assign STAR-certified science and math coaches to work alongside "
            "teachers within schools. Designed for divisions with high novice "
            "teacher rates and high learner-teacher ratios."
        ),
        "delivery": "School-embedded (1–2 semester engagement)",
        "target": "Divisions with high novice rate and staffing pressure",
    },
    "comprehensive_support": {
        "label": "Comprehensive STAR Support Package",
        "description": (
            "Apply a combined intervention: upskilling + mobile training + "
            "coaching for divisions flagged as critical priority across "
            "multiple UAI factors simultaneously."
        ),
        "delivery": "Multi-modal, phased over 1 school year",
        "target": "Critical priority divisions with 3+ dominant gap factors",
    },
}

# ---------------------------------------------------------------------------
# Rule-based recommender
# ---------------------------------------------------------------------------

# Factor thresholds (normalized 0–1) for triggering a rule
THRESHOLDS = {
    "mismatch_rate": 0.4,
    "training_gap_rate": 0.35,
    "geo_disadvantage": 0.6,
    "staffing_pressure": 0.5,
}

CRITICAL_UAI_THRESHOLD = 0.65


def recommend_intervention(row: pd.Series) -> Dict:
    """
    Given a division row with UAI scores and factor contributions,
    returns the most appropriate STAR intervention.
    """
    flags = _get_dominant_flags(row)
    n_flags = len(flags)

    # If critical tier and multiple flags → comprehensive
    if row.get("uai_score", 0) >= CRITICAL_UAI_THRESHOLD and n_flags >= 3:
        return _build_result("comprehensive_support", flags)

    # Priority rules (ordered by impact)
    if "geo_disadvantage" in flags:
        return _build_result("blended_remote_program", flags)

    if "mismatch_rate" in flags and "training_gap_rate" in flags:
        return _build_result("comprehensive_support", flags)

    if "mismatch_rate" in flags:
        return _build_result("specialization_upskilling", flags)

    if "training_gap_rate" in flags:
        return _build_result("mobile_training_deployment", flags)

    if "staffing_pressure" in flags:
        return _build_result("coaching_mentoring", flags)

    # Default fallback
    return _build_result("mobile_training_deployment", flags)


def _get_dominant_flags(row: pd.Series) -> List[str]:
    """Returns factor keys that exceed their trigger threshold (normalized)."""
    flags = []
    factor_map = {
        "mismatch_rate": "_norm_mismatch",
        "training_gap_rate": "_norm_training_gap",
        "geo_disadvantage": "_norm_geo",
        "staffing_pressure": "_norm_staffing",
    }
    # Use contribution columns as proxy for normalized values
    contrib_map = {
        "mismatch_rate": ("factor_mismatch_contrib", 0.30),
        "training_gap_rate": ("factor_training_contrib", 0.25),
        "geo_disadvantage": ("factor_geo_contrib", 0.20),
        "staffing_pressure": ("factor_staffing_contrib", 0.15),
    }
    for factor, (col, weight) in contrib_map.items():
        contrib = row.get(col, 0)
        normalized_proxy = contrib / weight if weight > 0 else 0
        if normalized_proxy >= THRESHOLDS[factor]:
            flags.append(factor)
    return flags


def _build_result(intervention_key: str, flags: List[str]) -> Dict:
    intervention = INTERVENTIONS[intervention_key].copy()
    intervention["intervention_key"] = intervention_key
    intervention["triggered_by"] = flags
    return intervention


def apply_recommendations(division_df: pd.DataFrame) -> pd.DataFrame:
    """Applies the recommender to all divisions and adds result columns."""
    df = division_df.copy()
    recommendations = df.apply(recommend_intervention, axis=1)
    df["intervention_key"] = recommendations.apply(lambda r: r["intervention_key"])
    df["intervention_label"] = recommendations.apply(lambda r: r["label"])
    df["intervention_description"] = recommendations.apply(lambda r: r["description"])
    df["intervention_delivery"] = recommendations.apply(lambda r: r["delivery"])
    df["intervention_target"] = recommendations.apply(lambda r: r["target"])
    df["intervention_triggered_by"] = recommendations.apply(lambda r: r["triggered_by"])
    return df
