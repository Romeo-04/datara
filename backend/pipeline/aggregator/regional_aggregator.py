"""
Module 3 — Regional Aggregator
Rolls up teacher-level profiled records to division and region level.
All outputs are aggregate — no individual teacher data is exposed.
"""

import pandas as pd
import numpy as np


def aggregate_by_division(
    profiled_teachers: pd.DataFrame,
    schools_df: pd.DataFrame,
    nat_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Produces one row per division with all aggregated capacity metrics.
    """
    t = profiled_teachers.copy()

    # --- Teacher-level aggregations per division ---
    teacher_agg = t.groupby("division").agg(
        total_teachers=("teacher_id", "count"),
        mismatch_count=("is_mismatched", "sum"),
        training_gap_count=("has_training_gap", "sum"),
        novice_count=("is_novice", "sum"),
        avg_training_count=("training_count", "mean"),
        avg_experience=("years_experience", "mean"),
        pct_permanent=("employment_status", lambda x: (x == "Permanent").mean()),
    ).reset_index()

    teacher_agg["mismatch_rate"] = teacher_agg["mismatch_count"] / teacher_agg["total_teachers"]
    teacher_agg["training_gap_rate"] = teacher_agg["training_gap_count"] / teacher_agg["total_teachers"]
    teacher_agg["novice_rate"] = teacher_agg["novice_count"] / teacher_agg["total_teachers"]

    # --- School-level aggregations per division ---
    school_agg = schools_df.groupby("division").agg(
        total_schools=("school_id", "count"),
        avg_ltr=("learner_teacher_ratio", "mean"),
        avg_geo_disadvantage=("geographic_disadvantage_score", "mean"),
        geographically_isolated_schools=("is_geographically_isolated", "sum"),
        region=("region", "first"),
    ).reset_index()

    school_agg["pct_gida_schools"] = (
        school_agg["geographically_isolated_schools"] / school_agg["total_schools"]
    )

    # --- Merge teacher + school ---
    div_df = teacher_agg.merge(school_agg, on="division", how="left")

    # --- Merge NAT scores ---
    nat_clean = nat_df[["division", "nat_science_mps", "nat_math_mps", "nat_combined_mps"]].copy()
    div_df = div_df.merge(nat_clean, on="division", how="left")
    div_df["nat_combined_mps"] = div_df["nat_combined_mps"].fillna(50)

    # --- Normalize NAT to 0–1 gap score (lower MPS = higher gap) ---
    max_mps = div_df["nat_combined_mps"].max()
    min_mps = div_df["nat_combined_mps"].min()
    if max_mps > min_mps:
        div_df["nat_gap_score"] = (max_mps - div_df["nat_combined_mps"]) / (max_mps - min_mps)
    else:
        div_df["nat_gap_score"] = 0.0

    return div_df


def aggregate_by_region(division_df: pd.DataFrame) -> pd.DataFrame:
    """
    Further rolls up division data to region level for top-level heatmap.
    """
    return division_df.groupby("region").agg(
        total_teachers=("total_teachers", "sum"),
        total_schools=("total_schools", "sum"),
        avg_mismatch_rate=("mismatch_rate", "mean"),
        avg_training_gap_rate=("training_gap_rate", "mean"),
        avg_novice_rate=("novice_rate", "mean"),
        avg_ltr=("avg_ltr", "mean"),
        avg_geo_disadvantage=("avg_geo_disadvantage", "mean"),
        avg_nat_gap_score=("nat_gap_score", "mean"),
        avg_nat_combined_mps=("nat_combined_mps", "mean"),
        n_divisions=("division", "count"),
    ).reset_index()
