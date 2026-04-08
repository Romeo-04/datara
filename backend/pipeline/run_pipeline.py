"""
Pipeline Runner — executes all modules end-to-end and writes processed outputs.

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


def run(data_dir: str = None, silent: bool = False) -> dict:
    """
    Run the full pipeline end-to-end.

    Args:
        data_dir: Path to raw CSV files. Defaults to data/synthetic/.
        silent:   Suppress print output (used when called from the API).

    Returns:
        dict with summary stats from the pipeline run.
    """
    DATA_OUT.mkdir(parents=True, exist_ok=True)
    raw_dir = Path(data_dir) if data_dir else DATA_RAW

    def log(msg):
        if not silent:
            print(msg)

    log("=== STAR Pipeline Starting ===\n")

    log("[1/6] Ingesting and standardizing data...")
    teachers, schools, logs, nat = load_all(str(raw_dir))
    log(f"      {len(teachers)} teachers | {len(schools)} schools | {len(logs)} training logs | {len(nat)} NAT records")

    log("[2/6] Profiling teacher records...")
    profiled = profile_teachers(teachers)
    mismatch_pct = profiled["is_mismatched"].mean() * 100
    gap_pct = profiled["has_training_gap"].mean() * 100
    log(f"      Overall mismatch rate: {mismatch_pct:.1f}% | Training gap rate: {gap_pct:.1f}%")

    log("[3/6] Aggregating to division level...")
    division_df = aggregate_by_division(profiled, schools, nat)
    log(f"      {len(division_df)} divisions")

    log("[4/6] Computing Underserved Area Index...")
    division_df = compute_uai(division_df)
    # Re-aggregate regions AFTER UAI so avg_uai_score is included
    region_df = aggregate_by_region(division_df)
    log(f"      {len(region_df)} regions")
    top5 = division_df.nsmallest(5, "priority_rank")[["division", "region", "uai_score", "priority_tier"]]
    log("      Top 5 most underserved divisions:")
    log(top5.to_string(index=False))

    log("[5/6] Generating intervention recommendations...")
    division_df = apply_recommendations(division_df)
    breakdown = division_df["intervention_label"].value_counts()
    log("      Intervention breakdown:")
    for label, count in breakdown.items():
        log(f"        {label}: {count} divisions")

    log("[6/6] Generating plain-language explanations...")
    division_df = apply_explanations(division_df)

    _save(division_df, DATA_OUT / "division_intelligence.csv", silent)
    _save(region_df, DATA_OUT / "region_summary.csv", silent)
    _save_api_json(division_df, region_df, DATA_OUT, silent)

    log(f"\n=== Pipeline Complete ===")
    log(f"    Outputs written to: {DATA_OUT}")

    return {
        "divisions": len(division_df),
        "regions": len(region_df),
        "teachers": int(profiled["teacher_id"].count()),
        "schools": int(schools["school_id"].count()),
        "mismatch_rate": round(mismatch_pct / 100, 4),
        "training_gap_rate": round(gap_pct / 100, 4),
        "critical_divisions": int((division_df["priority_tier"] == "Critical Priority").sum()),
        "high_divisions": int((division_df["priority_tier"] == "High Priority").sum()),
    }


def _save(df: pd.DataFrame, path: Path, silent: bool = False):
    df.to_csv(path, index=False)
    if not silent:
        print(f"      Saved: {path.name} ({len(df)} rows)")


def _save_api_json(division_df: pd.DataFrame, region_df: pd.DataFrame, out_dir: Path, silent: bool = False):
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
        "avg_uai_score", "max_uai_score", "critical_divisions", "high_divisions",
    ]
    available_reg = [c for c in reg_cols if c in region_df.columns]
    region_df[available_reg].to_json(out_dir / "region_summary.json", orient="records", indent=2)

    if not silent:
        print(f"      Saved: division_intelligence.json + region_summary.json")


if __name__ == "__main__":
    run()
