export const useUtils = () => {
  const pct = (value: number) => `${(value * 100).toFixed(1)}%`;
  const round2 = (value: number) => value.toFixed(2);

  const TIER_COLORS: Record<string, string> = {
    "Critical Priority": "bg-red-100 text-red-800 border-red-300",
    "High Priority": "bg-amber-100 text-amber-800 border-amber-300",
    "Standard Priority": "bg-green-100 text-green-800 border-green-300",
  };

  const INTERVENTION_COLORS: Record<string, string> = {
    specialization_upskilling: "bg-purple-100 text-purple-800",
    mobile_training_deployment: "bg-blue-100 text-blue-800",
    blended_remote_program: "bg-teal-100 text-teal-800",
    coaching_mentoring: "bg-orange-100 text-orange-800",
    comprehensive_support: "bg-red-100 text-red-800",
  };

  const FACTOR_LABELS: Record<string, string> = {
    mismatch: "Specialization Mismatch",
    training_gap: "Training Coverage Gap",
    geo_disadvantage: "Geographic Disadvantage",
    staffing_pressure: "Staffing Pressure",
    nat_gap: "Learning Outcome Gap (NAT)",
  };

  const FACTOR_COLORS = [
    "#1a4e8f",
    "#e67e22",
    "#27ae60",
    "#8e44ad",
    "#c0392b",
  ];

  const TIER_BAR_COLORS: Record<string, string> = {
    "Critical Priority": "#c0392b",
    "High Priority": "#e67e22",
    "Standard Priority": "#27ae60",
  };

  const normalize = (val: number, all: number[]) => {
    const min = Math.min(...all);
    const max = Math.max(...all);
    return max === min ? 0.5 : (val - min) / (max - min);
  };

  return {
    pct,
    round2,
    TIER_COLORS,
    INTERVENTION_COLORS,
    FACTOR_LABELS,
    FACTOR_COLORS,
    TIER_BAR_COLORS,
    normalize,
  };
};
