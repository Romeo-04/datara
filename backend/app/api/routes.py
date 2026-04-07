"""API routes for the STAR Regional Intelligence System."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from backend.app.core.data_store import get_divisions, get_regions
from backend.app.models.schemas import (
    DivisionSummary, RegionSummary, PaginatedDivisions,
    StatsOverview, FactorBreakdown, InterventionDetail
)

router = APIRouter(prefix="/api/v1")


def _parse_division(raw: dict) -> DivisionSummary:
    return DivisionSummary(
        division=raw["division"],
        region=raw["region"],
        priority_rank=int(raw["priority_rank"]),
        priority_tier=str(raw.get("priority_tier", "Standard Priority")),
        uai_score=float(raw.get("uai_score", 0)),
        total_teachers=int(raw.get("total_teachers", 0)),
        total_schools=int(raw.get("total_schools", 0)),
        mismatch_rate=float(raw.get("mismatch_rate", 0)),
        training_gap_rate=float(raw.get("training_gap_rate", 0)),
        avg_geo_disadvantage=float(raw.get("avg_geo_disadvantage", 0)),
        avg_ltr=float(raw.get("avg_ltr", 0)),
        nat_combined_mps=float(raw.get("nat_combined_mps", 50)),
        avg_experience=float(raw.get("avg_experience", 0)),
        novice_rate=float(raw.get("novice_rate", 0)),
        factors=FactorBreakdown(
            mismatch=float(raw.get("factor_mismatch_contrib", 0)),
            training_gap=float(raw.get("factor_training_contrib", 0)),
            geo_disadvantage=float(raw.get("factor_geo_contrib", 0)),
            staffing_pressure=float(raw.get("factor_staffing_contrib", 0)),
            nat_gap=float(raw.get("factor_nat_contrib", 0)),
        ),
        intervention=InterventionDetail(
            key=str(raw.get("intervention_key", "")),
            label=str(raw.get("intervention_label", "")),
            description=str(raw.get("intervention_description", "")),
            delivery=str(raw.get("intervention_delivery", "")),
            target=str(raw.get("intervention_target", "")),
        ),
        explanation=str(raw.get("explanation", "")),
    )


def _parse_region(raw: dict) -> RegionSummary:
    return RegionSummary(
        region=raw["region"],
        total_teachers=int(raw.get("total_teachers", 0)),
        total_schools=int(raw.get("total_schools", 0)),
        n_divisions=int(raw.get("n_divisions", 0)),
        avg_mismatch_rate=float(raw.get("avg_mismatch_rate", 0)),
        avg_training_gap_rate=float(raw.get("avg_training_gap_rate", 0)),
        avg_novice_rate=float(raw.get("avg_novice_rate", 0)),
        avg_ltr=float(raw.get("avg_ltr", 0)),
        avg_geo_disadvantage=float(raw.get("avg_geo_disadvantage", 0)),
        avg_nat_combined_mps=float(raw.get("avg_nat_combined_mps", 50)),
    )


# --- Stats Overview ---

@router.get("/stats", response_model=StatsOverview)
def get_stats():
    """National-level summary statistics for the dashboard header."""
    divisions = get_divisions()
    regions = get_regions()
    tiers = [d.get("priority_tier", "") for d in divisions]
    return StatsOverview(
        total_divisions=len(divisions),
        total_regions=len(regions),
        total_teachers=sum(int(d.get("total_teachers", 0)) for d in divisions),
        total_schools=sum(int(d.get("total_schools", 0)) for d in divisions),
        critical_divisions=tiers.count("Critical Priority"),
        high_priority_divisions=tiers.count("High Priority"),
        standard_divisions=tiers.count("Standard Priority"),
        national_avg_mismatch_rate=_avg(divisions, "mismatch_rate"),
        national_avg_training_gap_rate=_avg(divisions, "training_gap_rate"),
        national_avg_nat_mps=_avg(divisions, "nat_combined_mps"),
    )


# --- Division endpoints ---

@router.get("/divisions", response_model=PaginatedDivisions)
def list_divisions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    region: Optional[str] = None,
    tier: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = Query("priority_rank", enum=["priority_rank", "uai_score", "mismatch_rate", "training_gap_rate"]),
):
    """Paginated, filterable list of divisions ordered by priority rank."""
    data = get_divisions()

    if region:
        data = [d for d in data if d["region"].lower() == region.lower()]
    if tier:
        data = [d for d in data if str(d.get("priority_tier", "")).lower() == tier.lower()]
    if search:
        s = search.lower()
        data = [d for d in data if s in d["division"].lower() or s in d["region"].lower()]

    reverse = sort_by in ("uai_score", "mismatch_rate", "training_gap_rate")
    data = sorted(data, key=lambda d: float(d.get(sort_by, 0)), reverse=reverse)

    total = len(data)
    start = (page - 1) * page_size
    end = start + page_size
    page_data = data[start:end]

    return PaginatedDivisions(
        total=total,
        page=page,
        page_size=page_size,
        results=[_parse_division(d) for d in page_data],
    )


@router.get("/divisions/top", response_model=List[DivisionSummary])
def get_top_divisions(n: int = Query(10, ge=1, le=50)):
    """Top N most underserved divisions by UAI score."""
    data = sorted(get_divisions(), key=lambda d: int(d.get("priority_rank", 999)))
    return [_parse_division(d) for d in data[:n]]


@router.get("/divisions/{division_name}", response_model=DivisionSummary)
def get_division(division_name: str):
    """Full detail for a single division."""
    for d in get_divisions():
        if d["division"].lower() == division_name.lower():
            return _parse_division(d)
    raise HTTPException(status_code=404, detail=f"Division '{division_name}' not found")


# --- Region endpoints ---

@router.get("/regions", response_model=List[RegionSummary])
def list_regions():
    """All regions with aggregated metrics."""
    return [_parse_region(r) for r in get_regions()]


@router.get("/regions/{region_name}/divisions", response_model=List[DivisionSummary])
def get_region_divisions(region_name: str):
    """All divisions within a specific region, ordered by priority rank."""
    data = [
        d for d in get_divisions()
        if d["region"].lower() == region_name.lower()
    ]
    if not data:
        raise HTTPException(status_code=404, detail=f"Region '{region_name}' not found")
    data = sorted(data, key=lambda d: int(d.get("priority_rank", 999)))
    return [_parse_division(d) for d in data]


# --- Intervention filter ---

@router.get("/interventions/{intervention_key}/divisions", response_model=List[DivisionSummary])
def get_divisions_by_intervention(intervention_key: str):
    """All divisions assigned a specific intervention type."""
    data = [
        d for d in get_divisions()
        if d.get("intervention_key", "") == intervention_key
    ]
    data = sorted(data, key=lambda d: int(d.get("priority_rank", 999)))
    return [_parse_division(d) for d in data]


def _avg(records: list, key: str) -> float:
    vals = [float(r.get(key, 0)) for r in records if r.get(key) is not None]
    return round(sum(vals) / len(vals), 4) if vals else 0.0
