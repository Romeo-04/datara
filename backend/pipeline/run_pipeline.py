"""
Pipeline Runner — executes all modules end-to-end and writes processed outputs.
Run this script to regenerate the processed data used by the API.

Usage (from project root):
    python -m backend.pipeline.run_pipeline
"""

import sys
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.pipeline.ingestion.ingest import load_all
from backend.pipeline.profiler.teacher_profiler import profile_teachers
from backend.pipeline.aggregator.regional_aggregator import aggregate_by_division, aggregate_by_region
from backend.pipeline.uai.uai_engine import compute_uai
from backend.pipeline.recommender.intervention_recommender import apply_recommendations
from backend.pipeline.explainer.explainer import apply_explanations

DATA_RAW = ROOT / "data" / "synthetic"
DATA_OUT = ROOT / "data" / "processed"


def run():
    DATA_OUT.mkdir(parents=True, exist_ok=True)

    print("=== STAR Pipeline Starting ===\n")

    print("[1/6] Ingesting and standardizing data...")
    teachers, schools, logs, nat = load_all(str(DATA_RAW))
    print(f"      {len(teachers)} teachers | {len(schools)} schools | {len(logs)} training logs | {len(nat)} NAT records")

    print("[2/6] Profiling teacher records...")
    profiled = profile_teachers(teachers)
    mismatch_pct = profiled["is_mismatched"].mean() * 100
    gap_pct = profiled["has_training_gap"].mean() * 100
    print(f"      Overall mismatch rate: {mismatch_pct:.1f}% | Training gap rate: {gap_pct:.1f}%")

    print("[3/6] Aggregating to division level...")
    division_df = aggregate_by_division(profiled, schools, nat)
    region_df = aggregate_by_region(division_df)
    print(f"      {len(division_df)} divisions | {len(region_df)} regions")

    print("[4/6] Computing Underserved Area Index...")
    division_df = compute_uai(division_df)
    top5 = division_df.nsmallest(5, "priority_rank")[["division", "region", "uai_score", "priority_tier"]]
    print("      Top 5 most underserved divisions:")
    print(top5.to_string(index=False))

    print("[5/6] Generating intervention recommendations...")
    division_df = apply_recommendations(division_df)
    breakdown = division_df["intervention_label"].value_counts()
    print("      Intervention breakdown:")
    for label, count in breakdown.items():
        print(f"        {label}: {count} divisions")

    print("[6/6] Generating plain-language explanations...")
    division_df = apply_explanations(division_df)

    _save(division_df, DATA_OUT / "division_intelligence.csv")
    _save(region_df, DATA_OUT / "region_summary.csv")
    _save_api_json(division_df, region_df, DATA_OUT)

    print(f"\n=== Pipeline Complete ===")
    print(f"    Outputs written to: {DATA_OUT}")


def _save(df: pd.DataFrame, path: Path):
    df.to_csv(path, index=False)
    print(f"      Saved: {path.name} ({len(df)} rows)")


def _save_api_json(division_df: pd.DataFrame, region_df: pd.DataFrame, out_dir: Path):
    div_cols = [
        "division", "region", "priority_rank", "priority_tier", "uai_score",
        "total_teachers", "total_schools",
        "mismatch_rate", "training_gap_rate", "avg_geo_disadvantage",
        "avg_ltr", "nat_combined_mps", "nat_gap_score",
        "avg_experience", "novice_rate",
        "factor_mismatch_contrib", "factor_training_contrib",
        "factor_geo_contrib", "factor_staffing_contrib", "factor_nat_contrib",
        "intervention_key", "intervention_label",
        "intervention_description", "intervention_delivery", "intervention_target",
        "explanation",
    ]
    available = [c for c in div_cols if c in division_df.columns]
    div_json = division_df[available].sort_values("priority_rank").copy()

    # Convert any list columns to strings to keep JSON clean
    for col in div_json.columns:
        if div_json[col].dtype == object:
            div_json[col] = div_json[col].apply(
                lambda x: json.dumps(x) if isinstance(x, list) else x
            )

    div_json.to_json(out_dir / "division_intelligence.json", orient="records", indent=2)

    reg_cols = [
        "region", "total_teachers", "total_schools", "n_divisions",
        "avg_mismatch_rate", "avg_training_gap_rate", "avg_novice_rate",
        "avg_ltr", "avg_geo_disadvantage", "avg_nat_gap_score", "avg_nat_combined_mps",
    ]
    available_reg = [c for c in reg_cols if c in region_df.columns]
    region_df[available_reg].to_json(out_dir / "region_summary.json", orient="records", indent=2)

    print(f"      Saved: division_intelligence.json + region_summary.json")


if __name__ == "__main__":
    run()
