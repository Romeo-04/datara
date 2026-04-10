"""
Upload endpoint — accepts CSV files from STAR managers,
saves them to data/uploads/, re-runs the pipeline, and reloads the data store.
"""

import io
import os
import shutil
import sys
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

router = APIRouter(prefix="/api/v1")

UPLOAD_DIR = ROOT / "data" / "uploads"
SYNTHETIC_DIR = ROOT / "data" / "synthetic"

REQUIRED_COLUMNS = {
    "teachers": {
        "teacher_id", "school_id", "division", "region",
        "subject_taught", "specialization", "years_experience", "training_count",
    },
    "schools": {
        "school_id", "school_name", "division", "region",
        "learner_teacher_ratio", "geographic_disadvantage_score",
    },
    "training_logs": {"teacher_id", "training_name", "year"},
    "nat_scores": {"division", "region", "nat_science_mps", "nat_math_mps"},
}

COLUMN_DESCRIPTIONS = {
    "teachers": [
        "teacher_id", "school_id", "division", "region",
        "subject_taught", "specialization", "years_experience",
        "training_count", "employment_status",
    ],
    "schools": [
        "school_id", "school_name", "school_type", "division", "region",
        "learner_teacher_ratio", "is_geographically_isolated",
        "geographic_disadvantage_score",
    ],
    "training_logs": [
        "log_id", "teacher_id", "division", "region",
        "training_name", "year", "modality",
    ],
    "nat_scores": [
        "division", "region", "nat_science_mps", "nat_math_mps", "year",
    ],
}


@router.get("/upload/schema")
def get_upload_schema():
    """Returns required and optional columns for each uploadable file type."""
    return {
        "files": [
            {
                "key": key,
                "label": key.replace("_", " ").title(),
                "required_columns": list(REQUIRED_COLUMNS[key]),
                "all_columns": COLUMN_DESCRIPTIONS[key],
                "optional": key in ("training_logs", "nat_scores"),
            }
            for key in REQUIRED_COLUMNS
        ]
    }


@router.post("/upload")
async def upload_datasets(
    teachers: UploadFile = File(default=None),
    schools: UploadFile = File(default=None),
    training_logs: UploadFile = File(default=None),
    nat_scores: UploadFile = File(default=None),
):
    """
    Accept up to 4 CSV files, validate, run pipeline, reload API data store.
    Any file not uploaded falls back to existing synthetic/upload data.
    """
    if os.getenv("VERCEL") == "1":
        raise HTTPException(
            status_code=501,
            detail=(
                "Dataset upload is disabled on the Vercel demo deployment. "
                "Persistent uploads require Vercel Blob, Postgres, or another "
                "shared storage backend."
            ),
        )

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_results = {}
    file_map = {
        "teachers": teachers,
        "schools": schools,
        "training_logs": training_logs,
        "nat_scores": nat_scores,
    }

    for name, upload in file_map.items():
        if upload and upload.filename:
            if not upload.filename.lower().endswith(".csv"):
                raise HTTPException(400, detail=f"'{name}' must be a .csv file")

            raw = await upload.read()
            try:
                df = pd.read_csv(io.BytesIO(raw))
            except Exception as e:
                raise HTTPException(400, detail=f"Could not parse '{name}': {e}")

            missing = REQUIRED_COLUMNS[name] - set(df.columns)
            if missing:
                raise HTTPException(
                    400,
                    detail=f"'{name}' is missing required columns: {sorted(missing)}",
                )

            dest = UPLOAD_DIR / f"{name}.csv"
            dest.write_bytes(raw)
            upload_results[name] = {"rows": len(df), "columns": list(df.columns)}

    if not upload_results:
        raise HTTPException(400, detail="No files were uploaded.")

    # Fill missing files from synthetic fallback
    for name in REQUIRED_COLUMNS:
        dest = UPLOAD_DIR / f"{name}.csv"
        if not dest.exists():
            fallback = SYNTHETIC_DIR / f"{name}.csv"
            if fallback.exists():
                shutil.copy(fallback, dest)

    # Re-run pipeline on uploaded data
    try:
        from backend.pipeline.run_pipeline import run as run_pipeline
        summary = run_pipeline(data_dir=str(UPLOAD_DIR), silent=True)
    except Exception as e:
        raise HTTPException(500, detail=f"Pipeline failed: {e}")

    # Reload in-memory data store
    try:
        from backend.app.core.data_store import load
        load()
    except Exception as e:
        raise HTTPException(500, detail=f"Data reload failed: {e}")

    return {
        "status": "success",
        "uploaded_files": upload_results,
        "pipeline_summary": summary,
    }
