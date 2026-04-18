"""Budget estimation endpoint — computes PHP cost breakdown per division/region/intervention."""

from fastapi import APIRouter
from backend.app.core.data_store import get_divisions, get_regions

router = APIRouter(prefix="/api/v1")

# Cost model per intervention key
COST_MODEL = {
    "comprehensive_support": {
        "cost_per_teacher": 25000,
        "cost_per_school":  50000,
        "materials_pct":    0.15,
        "facilitator_pct":  0.30,
        "logistics_pct":    0.25,
        "lodging_pct":      0.20,
        "overhead_pct":     0.10,
    },
    "mobile_training_deployment": {
        "cost_per_teacher": 15000,
        "cost_per_school":  80000,
        "materials_pct":    0.12,
        "facilitator_pct":  0.25,
        "logistics_pct":    0.38,
        "lodging_pct":      0.15,
        "overhead_pct":     0.10,
    },
    "specialization_upskilling": {
        "cost_per_teacher": 18000,
        "cost_per_school":  30000,
        "materials_pct":    0.20,
        "facilitator_pct":  0.35,
        "logistics_pct":    0.20,
        "lodging_pct":      0.15,
        "overhead_pct":     0.10,
    },
    "blended_remote_program": {
        "cost_per_teacher": 8000,
        "cost_per_school":  15000,
        "materials_pct":    0.35,
        "facilitator_pct":  0.25,
        "logistics_pct":    0.10,
        "lodging_pct":      0.05,
        "overhead_pct":     0.25,
    },
    "coaching_mentoring": {
        "cost_per_teacher": 12000,
        "cost_per_school":  40000,
        "materials_pct":    0.10,
        "facilitator_pct":  0.45,
        "logistics_pct":    0.20,
        "lodging_pct":      0.15,
        "overhead_pct":     0.10,
    },
}

DEFAULT_MODEL = {
    "cost_per_teacher": 15000,
    "cost_per_school":  40000,
    "materials_pct":    0.20,
    "facilitator_pct":  0.30,
    "logistics_pct":    0.25,
    "lodging_pct":      0.15,
    "overhead_pct":     0.10,
}


def _estimate(division: dict) -> dict:
    model = COST_MODEL.get(division.get("intervention_key", ""), DEFAULT_MODEL)
    teachers = int(division.get("total_teachers", 0))
    schools  = int(division.get("total_schools",  0))
    geo      = float(division.get("avg_geo_disadvantage", 0.3))

    # Geographic multiplier: remote areas cost up to 1.5×
    geo_mult = 1.0 + geo * 0.5

    base  = model["cost_per_teacher"] * teachers + model["cost_per_school"] * schools
    total = round(base * geo_mult)

    return {
        "total":       total,
        "materials":   round(total * model["materials_pct"]),
        "facilitator": round(total * model["facilitator_pct"]),
        "logistics":   round(total * model["logistics_pct"]),
        "lodging":     round(total * model["lodging_pct"]),
        "overhead":    round(total * model["overhead_pct"]),
        "geo_multiplier": round(geo_mult, 3),
    }


@router.get("/budget")
def get_budget():
    divs = get_divisions()

    division_estimates = []
    for d in divs:
        est = _estimate(d)
        division_estimates.append({
            "division":           d["division"],
            "region":             d["region"],
            "priority_tier":      d.get("priority_tier", ""),
            "priority_rank":      d.get("priority_rank", 0),
            "intervention_label": d.get("intervention_label", ""),
            "intervention_key":   d.get("intervention_key", ""),
            "total_teachers":     int(d.get("total_teachers", 0)),
            "total_schools":      int(d.get("total_schools",  0)),
            "geo_disadvantage":   float(d.get("avg_geo_disadvantage", 0)),
            "estimated_cost":     est["total"],
            "breakdown": {
                "materials":   est["materials"],
                "facilitator": est["facilitator"],
                "logistics":   est["logistics"],
                "lodging":     est["lodging"],
                "overhead":    est["overhead"],
            },
            "geo_multiplier": est["geo_multiplier"],
        })

    # Aggregate by intervention
    intervention_map: dict = {}
    for d in division_estimates:
        key   = d["intervention_key"]
        label = d["intervention_label"]
        if key not in intervention_map:
            intervention_map[key] = {
                "key": key, "label": label,
                "divisions": 0, "teachers": 0, "schools": 0,
                "total": 0,
                "breakdown": {"materials": 0, "facilitator": 0, "logistics": 0, "lodging": 0, "overhead": 0},
            }
        g = intervention_map[key]
        g["divisions"] += 1
        g["teachers"]  += d["total_teachers"]
        g["schools"]   += d["total_schools"]
        g["total"]     += d["estimated_cost"]
        for k in g["breakdown"]:
            g["breakdown"][k] += d["breakdown"][k]

    # Aggregate by region
    region_map: dict = {}
    for d in division_estimates:
        r = d["region"]
        if r not in region_map:
            region_map[r] = {"region": r, "total": 0, "teachers": 0, "divisions": 0}
        region_map[r]["total"]     += d["estimated_cost"]
        region_map[r]["teachers"]  += d["total_teachers"]
        region_map[r]["divisions"] += 1

    # Aggregate by tier
    tier_map: dict = {
        "Critical Priority": {"divisions": 0, "teachers": 0, "total": 0},
        "High Priority":     {"divisions": 0, "teachers": 0, "total": 0},
        "Standard Priority": {"divisions": 0, "teachers": 0, "total": 0},
    }
    for d in division_estimates:
        tier = d["priority_tier"]
        if tier in tier_map:
            tier_map[tier]["divisions"] += 1
            tier_map[tier]["teachers"]  += d["total_teachers"]
            tier_map[tier]["total"]     += d["estimated_cost"]

    grand_total = sum(d["estimated_cost"] for d in division_estimates)

    return {
        "currency":          "PHP",
        "grand_total":       grand_total,
        "by_tier":           tier_map,
        "by_intervention":   sorted(intervention_map.values(), key=lambda x: -x["total"]),
        "by_region":         sorted(region_map.values(), key=lambda x: -x["total"]),
        "divisions":         sorted(division_estimates, key=lambda x: -x["estimated_cost"]),
    }
