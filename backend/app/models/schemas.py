"""Pydantic response schemas for the API."""

from pydantic import BaseModel
from typing import Optional, List


class FactorBreakdown(BaseModel):
    mismatch: float
    training_gap: float
    geo_disadvantage: float
    staffing_pressure: float
    nat_gap: float


class InterventionDetail(BaseModel):
    key: str
    label: str
    description: str
    delivery: str
    target: str


class DivisionSummary(BaseModel):
    division: str
    region: str
    priority_rank: int
    priority_tier: str
    uai_score: float
    total_teachers: int
    total_schools: int
    mismatch_rate: float
    training_gap_rate: float
    avg_geo_disadvantage: float
    avg_ltr: float
    nat_combined_mps: float
    avg_experience: float
    novice_rate: float
    factors: FactorBreakdown
    intervention: InterventionDetail
    explanation: str


class RegionSummary(BaseModel):
    region: str
    total_teachers: int
    total_schools: int
    n_divisions: int
    avg_mismatch_rate: float
    avg_training_gap_rate: float
    avg_novice_rate: float
    avg_ltr: float
    avg_geo_disadvantage: float
    avg_nat_combined_mps: float


class PaginatedDivisions(BaseModel):
    total: int
    page: int
    page_size: int
    results: List[DivisionSummary]


class StatsOverview(BaseModel):
    total_divisions: int
    total_regions: int
    total_teachers: int
    total_schools: int
    critical_divisions: int
    high_priority_divisions: int
    standard_divisions: int
    national_avg_mismatch_rate: float
    national_avg_training_gap_rate: float
    national_avg_nat_mps: float
