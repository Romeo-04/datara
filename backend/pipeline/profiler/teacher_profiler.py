"""
Module 2 — Teacher Record Profiler (backend only, never exposed in frontend)
- Checks subject vs. specialization alignment
- Flags training gaps and experience bands
- Produces per-record flags that feed into aggregation
Output stays inside the pipeline; individual scores never reach the API.
"""

import pandas as pd
import numpy as np

# Subject → acceptable specialization mapping
SUBJECT_VALID_SPECIALIZATIONS = {
    "Biology": ["Biology", "General Science"],
    "Chemistry": ["Chemistry", "General Science"],
    "Physics": ["Physics", "General Science"],
    "Earth Science": ["Earth Science", "General Science"],
    "General Science": ["Biology", "Chemistry", "Physics", "Earth Science", "General Science"],
    "Mathematics": ["Mathematics", "Statistics"],
    "Statistics": ["Mathematics", "Statistics"],
}

# Experience bands
EXPERIENCE_BANDS = {
    "novice": (0, 3),
    "developing": (3, 8),
    "proficient": (8, 15),
    "expert": (15, 999),
}

# Training gap threshold: fewer than this many trainings = gap
TRAINING_GAP_THRESHOLD = 2


def profile_teachers(teachers_df: pd.DataFrame) -> pd.DataFrame:
    df = teachers_df.copy()

    # 1. Subject-specialization alignment
    df["is_mismatched"] = df.apply(_check_mismatch, axis=1)

    # 2. Training gap flag
    df["has_training_gap"] = df["training_count"] < TRAINING_GAP_THRESHOLD

    # 3. Experience band
    df["experience_band"] = df["years_experience"].apply(_experience_band)

    # 4. Is novice teacher (high support need)
    df["is_novice"] = df["experience_band"] == "novice"

    # 5. Composite record-level support need score (0–3, used internally only)
    df["_support_need_score"] = (
        df["is_mismatched"].astype(int) +
        df["has_training_gap"].astype(int) +
        df["is_novice"].astype(int)
    )

    return df


def _check_mismatch(row: pd.Series) -> bool:
    subject = str(row.get("subject_taught", "")).strip()
    spec = str(row.get("specialization", "")).strip()
    valid = SUBJECT_VALID_SPECIALIZATIONS.get(subject, [])
    if not valid:
        return False  # unknown subject — do not flag
    return spec not in valid


def _experience_band(years: int) -> str:
    for band, (lo, hi) in EXPERIENCE_BANDS.items():
        if lo <= years < hi:
            return band
    return "expert"
