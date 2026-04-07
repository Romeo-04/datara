"""
In-memory data store — loads processed pipeline outputs at startup.
Avoids a database dependency for the MVP.
"""

import json
import pandas as pd
from pathlib import Path
from typing import Optional

_PROCESSED_DIR = Path(__file__).resolve().parents[3] / "data" / "processed"

_divisions: Optional[list] = None
_regions: Optional[list] = None


def load():
    global _divisions, _regions
    div_path = _PROCESSED_DIR / "division_intelligence.json"
    reg_path = _PROCESSED_DIR / "region_summary.json"

    if not div_path.exists():
        raise FileNotFoundError(
            f"Processed data not found at {div_path}. "
            "Run: python -m backend.pipeline.run_pipeline"
        )

    with open(div_path) as f:
        _divisions = json.load(f)

    with open(reg_path) as f:
        _regions = json.load(f)


def get_divisions() -> list:
    if _divisions is None:
        load()
    return _divisions


def get_regions() -> list:
    if _regions is None:
        load()
    return _regions
