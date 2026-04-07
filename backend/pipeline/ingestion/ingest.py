"""
Module 1 — Data Ingestion & Standardization
Loads raw CSVs, validates schema, normalizes fields, flags missing data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple


REQUIRED_TEACHER_COLS = {
    "teacher_id", "school_id", "division", "region",
    "subject_taught", "specialization", "years_experience", "training_count"
}

REQUIRED_SCHOOL_COLS = {
    "school_id", "school_name", "division", "region",
    "learner_teacher_ratio", "geographic_disadvantage_score"
}

VALID_SUBJECTS = {
    "Biology", "Chemistry", "Physics", "Earth Science",
    "General Science", "Mathematics", "Statistics"
}


def load_teachers(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    _assert_columns(df, REQUIRED_TEACHER_COLS, "teachers")

    df["subject_taught"] = df["subject_taught"].str.strip().str.title()
    df["specialization"] = df["specialization"].str.strip().str.title()
    df["region"] = df["region"].str.strip()
    df["division"] = df["division"].str.strip()
    df["years_experience"] = pd.to_numeric(df["years_experience"], errors="coerce").fillna(0).astype(int)
    df["training_count"] = pd.to_numeric(df["training_count"], errors="coerce").fillna(0).astype(int)

    df["subject_valid"] = df["subject_taught"].isin(VALID_SUBJECTS)
    df["data_quality_flag"] = ~df["subject_valid"] | df["specialization"].isna()

    return df


def load_schools(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    _assert_columns(df, REQUIRED_SCHOOL_COLS, "schools")

    df["region"] = df["region"].str.strip()
    df["division"] = df["division"].str.strip()
    df["learner_teacher_ratio"] = pd.to_numeric(df["learner_teacher_ratio"], errors="coerce").fillna(30)
    df["geographic_disadvantage_score"] = pd.to_numeric(
        df["geographic_disadvantage_score"], errors="coerce"
    ).fillna(0.3).clip(0, 1)

    return df


def load_training_logs(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(2020).astype(int)
    return df


def load_nat_scores(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["nat_science_mps"] = pd.to_numeric(df["nat_science_mps"], errors="coerce").fillna(50)
    df["nat_math_mps"] = pd.to_numeric(df["nat_math_mps"], errors="coerce").fillna(50)
    df["nat_combined_mps"] = (df["nat_science_mps"] + df["nat_math_mps"]) / 2
    return df


def load_all(data_dir: str) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    base = Path(data_dir)
    teachers = load_teachers(str(base / "teachers.csv"))
    schools = load_schools(str(base / "schools.csv"))
    logs = load_training_logs(str(base / "training_logs.csv"))
    nat = load_nat_scores(str(base / "nat_scores.csv"))
    return teachers, schools, logs, nat


def _assert_columns(df: pd.DataFrame, required: set, name: str):
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"[Ingestion] '{name}' is missing columns: {missing}")
