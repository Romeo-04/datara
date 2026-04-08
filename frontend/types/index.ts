export interface FactorBreakdown {
  mismatch: number;
  training_gap: number;
  geo_disadvantage: number;
  staffing_pressure: number;
  nat_gap: number;
}

export interface InterventionDetail {
  key: string;
  label: string;
  description: string;
  delivery: string;
  target: string;
}

export interface Division {
  division: string;
  region: string;
  priority_rank: number;
  priority_tier: "Critical Priority" | "High Priority" | "Standard Priority";
  uai_score: number;
  total_teachers: number;
  total_schools: number;
  mismatch_rate: number;
  training_gap_rate: number;
  avg_geo_disadvantage: number;
  avg_ltr: number;
  nat_combined_mps: number;
  avg_experience: number;
  novice_rate: number;
  factors: FactorBreakdown;
  intervention: InterventionDetail;
  explanation: string;
}

export interface Region {
  region: string;
  total_teachers: number;
  total_schools: number;
  n_divisions: number;
  avg_mismatch_rate: number;
  avg_training_gap_rate: number;
  avg_novice_rate: number;
  avg_ltr: number;
  avg_geo_disadvantage: number;
  avg_nat_combined_mps: number;
  avg_uai_score?: number;
  max_uai_score?: number;
  critical_divisions?: number;
  high_divisions?: number;
}

export interface StatsOverview {
  total_divisions: number;
  total_regions: number;
  total_teachers: number;
  total_schools: number;
  critical_divisions: number;
  high_priority_divisions: number;
  standard_divisions: number;
  national_avg_mismatch_rate: number;
  national_avg_training_gap_rate: number;
  national_avg_nat_mps: number;
}

export interface PaginatedDivisions {
  total: number;
  page: number;
  page_size: number;
  results: Division[];
}
