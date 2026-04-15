"""Rule-based AI chat — answers dashboard queries directly from live data, no API key needed."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.core.data_store import get_divisions, get_regions
from collections import Counter
import re

router = APIRouter(prefix="/api/v1")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _divisions():
    return sorted(get_divisions(), key=lambda d: int(d.get("priority_rank", 999)))


def _regions():
    return sorted(get_regions(), key=lambda r: float(r.get("avg_uai_score") or 0), reverse=True)


def _tier(d):
    return str(d.get("priority_tier", ""))


def _uai(d):
    return float(d.get("uai_score") or d.get("avg_uai_score") or 0)


def _color(tier):
    return {"Critical Priority": "🔴", "High Priority": "🟠", "Standard Priority": "🟢"}.get(tier, "⚪")


def _pct(val):
    return round(float(val or 0) * 100, 1)


def _top_n(q):
    m = re.search(r"top\s*(\d+)|(\d+)\s*(most|worst|highest|lowest|best)", q)
    return int(m.group(1) or m.group(2)) if m else 5


def answer(msg: str) -> str:
    q = msg.lower().strip()
    divs = _divisions()
    regs = _regions()

    critical_divs = [d for d in divs if _tier(d) == "Critical Priority"]
    high_divs     = [d for d in divs if _tier(d) == "High Priority"]
    standard_divs = [d for d in divs if _tier(d) == "Standard Priority"]

    total_teachers = sum(int(d.get("total_teachers", 0)) for d in divs)
    total_schools  = sum(int(d.get("total_schools",  0)) for d in divs)

    # ── Help ──────────────────────────────────────────────────────────────
    if re.search(r"^(help|what can you|what do you|commands|topics)", q):
        return (
            "**I can answer questions about:**\n\n"
            "**Divisions & Rankings**\n"
            "• *Top 10 most underserved divisions*\n"
            "• *Least underserved divisions*\n"
            "• *Tell me about [division name]*\n"
            "• *Divisions in Region VII*\n"
            "• *How many critical priority divisions are there?*\n\n"
            "**Regions**\n"
            "• *List all regions by UAI*\n"
            "• *Tell me about NCR*\n"
            "• *Which region has the most teachers?*\n"
            "• *Which region has the most critical divisions?*\n\n"
            "**Factors & Metrics**\n"
            "• *Which divisions have the highest mismatch rate?*\n"
            "• *Top 5 divisions with training gaps*\n"
            "• *Most geographically isolated divisions*\n"
            "• *Divisions with highest staffing pressure*\n"
            "• *Lowest NAT MPS divisions*\n"
            "• *What is the average UAI / mismatch rate?*\n\n"
            "**Interventions**\n"
            "• *What interventions are recommended?*\n"
            "• *Which divisions need retraining?*\n\n"
            "**Explanations**\n"
            "• *What is UAI?*\n"
            "• *What is mismatch rate / training gap / geo disadvantage / staffing pressure?*\n\n"
            "• *Give me a dashboard summary*"
        )

    # ── How many / count queries ──────────────────────────────────────────
    if re.search(r"how many.*(division|region|teacher|school)", q):
        if "critical" in q:
            return f"There are **{len(critical_divs)} Critical Priority divisions** across the country."
        if "high" in q:
            return f"There are **{len(high_divs)} High Priority divisions** across the country."
        if "standard" in q:
            return f"There are **{len(standard_divs)} Standard Priority divisions** across the country."
        if "region" in q:
            return f"There are **{len(regs)} regions** in the dataset."
        if "teacher" in q:
            return f"There are **{total_teachers:,} teachers** across all divisions."
        if "school" in q:
            return f"There are **{total_schools:,} schools** across all divisions."
        return (
            f"**National Summary:**\n"
            f"• {len(divs)} divisions across {len(regs)} regions\n"
            f"• {total_teachers:,} teachers | {total_schools:,} schools\n"
            f"• 🔴 {len(critical_divs)} Critical | 🟠 {len(high_divs)} High | 🟢 {len(standard_divs)} Standard"
        )

    # ── Average / national stats ──────────────────────────────────────────
    if re.search(r"average|national average|avg|mean|overall", q):
        if re.search(r"uai", q):
            avg = sum(_uai(d) for d in divs) / len(divs)
            return f"The **national average UAI score** is **{avg:.3f}**."
        if re.search(r"mismatch", q):
            avg = sum(float(d.get("mismatch_rate", 0)) for d in divs) / len(divs)
            return f"The **national average mismatch rate** is **{avg*100:.1f}%** of teachers teaching outside their specialization."
        if re.search(r"training|gap", q):
            avg = sum(float(d.get("training_gap_rate", 0)) for d in divs) / len(divs)
            return f"The **national average training gap rate** is **{avg*100:.1f}%** of teachers under-trained."
        if re.search(r"nat|mps|performance", q):
            avg = sum(float(d.get("nat_combined_mps", 50)) for d in divs) / len(divs)
            return f"The **national average NAT MPS** is **{avg:.1f}%**."
        # General averages
        avg_uai = sum(_uai(d) for d in divs) / len(divs)
        avg_mm  = sum(float(d.get("mismatch_rate", 0)) for d in divs) / len(divs)
        avg_tg  = sum(float(d.get("training_gap_rate", 0)) for d in divs) / len(divs)
        avg_nat = sum(float(d.get("nat_combined_mps", 50)) for d in divs) / len(divs)
        return (
            f"**National Averages:**\n"
            f"• Avg UAI Score: **{avg_uai:.3f}**\n"
            f"• Avg Mismatch Rate: **{avg_mm*100:.1f}%**\n"
            f"• Avg Training Gap: **{avg_tg*100:.1f}%**\n"
            f"• Avg NAT MPS: **{avg_nat:.1f}%**"
        )

    # ── Factor explanations ───────────────────────────────────────────────
    if re.search(r"what is (uai|underserved area index)|explain uai|uai (mean|formula|work|stand)", q):
        return (
            "**Underserved Area Index (UAI)**\n"
            "A composite score measuring how underserved a division is for STAR capacity-building. **Higher = more need.**\n\n"
            "**Formula (weighted sum of 5 factors):**\n"
            "• 0.30 × Specialization Mismatch Rate\n"
            "• 0.25 × Training Coverage Gap\n"
            "• 0.20 × Geographic Disadvantage\n"
            "• 0.15 × Staffing Pressure (LTR)\n"
            "• 0.10 × NAT Learning Outcome Gap\n\n"
            "Each factor is min-max normalized to [0, 1] before weighting.\n\n"
            "**Priority Tiers (by tercile):**\n"
            "🔴 Critical Priority — top third\n"
            "🟠 High Priority — middle third\n"
            "🟢 Standard Priority — bottom third"
        )

    if re.search(r"what is mismatch|explain mismatch|mismatch (mean|rate|refer)", q):
        avg = sum(float(d.get("mismatch_rate", 0)) for d in divs) / len(divs)
        worst = sorted(divs, key=lambda d: float(d.get("mismatch_rate", 0)), reverse=True)[0]
        return (
            "**Specialization Mismatch Rate**\n"
            "The percentage of teachers in a division who are teaching subjects *outside* their specialization. "
            "A high mismatch signals poor subject-teacher alignment and is the highest-weighted UAI factor (30%).\n\n"
            f"• National average: **{avg*100:.1f}%**\n"
            f"• Highest: **{worst['division']}** at **{_pct(worst.get('mismatch_rate'))}%**"
        )

    if re.search(r"what is training gap|explain training|training gap (mean|refer)", q):
        avg = sum(float(d.get("training_gap_rate", 0)) for d in divs) / len(divs)
        worst = sorted(divs, key=lambda d: float(d.get("training_gap_rate", 0)), reverse=True)[0]
        return (
            "**Training Coverage Gap**\n"
            "The percentage of teachers who have received fewer professional development trainings than the required threshold. "
            "It is the second-highest UAI factor (25%).\n\n"
            f"• National average: **{avg*100:.1f}%**\n"
            f"• Most affected: **{worst['division']}** at **{_pct(worst.get('training_gap_rate'))}%**"
        )

    if re.search(r"what is geo|explain geo|geographic disadvantage|isolation (mean|refer)", q):
        return (
            "**Geographic Disadvantage**\n"
            "A normalized score (0–1) representing how geographically isolated a division is from resources, "
            "training centers, and infrastructure. Remote or island divisions score higher. "
            "It contributes 20% to the UAI score."
        )

    if re.search(r"what is (staffing|ltr)|learner.teacher|explain staffing", q):
        return (
            "**Staffing Pressure (LTR)**\n"
            "The Learner-to-Teacher Ratio — how many students each teacher is responsible for on average. "
            "A higher ratio indicates greater workload pressure and fewer teachers relative to the student population. "
            "It contributes 15% to the UAI score."
        )

    if re.search(r"what is nat|explain nat|nat (mean|stand|refer)|mean percentage", q):
        avg = sum(float(d.get("nat_combined_mps", 50)) for d in divs) / len(divs)
        return (
            "**NAT — National Achievement Test**\n"
            "The NAT MPS (Mean Percentage Score) measures student achievement in Science and Math. "
            "A lower MPS signals a learning outcome gap and contributes 10% to the UAI as a corroborating indicator.\n\n"
            f"• National average NAT MPS: **{avg:.1f}%**\n"
            "• Passing threshold: typically **75%**"
        )

    # ── Top N / worst queries ─────────────────────────────────────────────
    n = _top_n(q)

    if re.search(r"top|worst|most underserved|highest (uai|priority)|most critical", q):
        tier_filter = None
        if "critical" in q:   tier_filter = "Critical Priority"
        elif "high" in q:     tier_filter = "High Priority"
        elif "standard" in q: tier_filter = "Standard Priority"

        pool = [d for d in divs if _tier(d) == tier_filter] if tier_filter else divs
        subset = pool[:n]
        if not subset:
            return "No divisions found for that filter."
        label = f"({tier_filter}) " if tier_filter else ""
        lines = [f"**Top {len(subset)} {label}Most Underserved Divisions:**"]
        for d in subset:
            lines.append(
                f"{_color(_tier(d))} **#{d.get('priority_rank')} {d['division']}** ({d['region']}) — UAI: {_uai(d):.3f}"
            )
        return "\n".join(lines)

    # ── Least underserved / best performing ──────────────────────────────
    if re.search(r"least underserved|best performing|lowest uai|safest|most served|least critical", q):
        subset = sorted(divs, key=_uai)[:n]
        lines = [f"**{n} Least Underserved Divisions (Lowest UAI):**"]
        for d in subset:
            lines.append(f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — UAI: {_uai(d):.3f}")
        return "\n".join(lines)

    # ── Divisions within a specific region ───────────────────────────────
    region_match = None
    for r in regs:
        rname = r["region"].lower()
        if rname in q or rname.replace("region ", "").strip() in q:
            region_match = r["region"]
            break
    # Also match shorthands like "region 7", "region vii"
    roman = {"i":"1","ii":"2","iii":"3","iv":"4","v":"5","vi":"6","vii":"7","viii":"8","ix":"9",
             "x":"10","xi":"11","xii":"12","xiii":"13"}
    if not region_match:
        for abbr, num in roman.items():
            if re.search(rf"\bregion\s+{abbr}\b", q):
                for r in regs:
                    if f"region {num}" in r["region"].lower() or f"region {abbr}" in r["region"].lower():
                        region_match = r["region"]
                        break

    if region_match and re.search(r"division|school|teacher|list|show|all|what", q):
        rdivs = [d for d in divs if d.get("region", "").lower() == region_match.lower()]
        if not rdivs:
            return f"No divisions found for **{region_match}**."
        lines = [f"**Divisions in {region_match}** ({len(rdivs)} total):"]
        for d in rdivs:
            lines.append(f"{_color(_tier(d))} **{d['division']}** — UAI: {_uai(d):.3f} | Rank #{d.get('priority_rank')}")
        return "\n".join(lines)

    # ── Specific division lookup ──────────────────────────────────────────
    for d in divs:
        name = d["division"].lower()
        if name in q or (len(name) > 5 and name[:6] in q):
            uai = _uai(d)
            tier = _tier(d)
            factors = []
            if d.get("factor_mismatch_contrib"):
                fc = [
                    ("Mismatch",        float(d.get("factor_mismatch_contrib", 0))),
                    ("Training Gap",    float(d.get("factor_training_contrib", 0))),
                    ("Geo Disadvantage",float(d.get("factor_geo_contrib", 0))),
                    ("Staffing Pressure",float(d.get("factor_staffing_contrib", 0))),
                    ("NAT Gap",         float(d.get("factor_nat_contrib", 0))),
                ]
                top2 = sorted(fc, key=lambda x: x[1], reverse=True)[:2]
                factors = f"\n• Top Drivers: {top2[0][0]} ({top2[0][1]:.3f}), {top2[1][0]} ({top2[1][1]:.3f})"
            return (
                f"{_color(tier)} **{d['division']}** ({d['region']})\n"
                f"• UAI Score: **{uai:.3f}** — {tier}\n"
                f"• Priority Rank: **#{d.get('priority_rank')}** out of {len(divs)}\n"
                f"• Teachers: {d.get('total_teachers')} | Schools: {d.get('total_schools')}\n"
                f"• Mismatch Rate: {_pct(d.get('mismatch_rate'))}%\n"
                f"• Training Gap: {_pct(d.get('training_gap_rate'))}%\n"
                f"• NAT MPS: {round(float(d.get('nat_combined_mps', 50)), 1)}%"
                f"{''.join(factors) if isinstance(factors, str) else ''}\n"
                f"• Recommended: **{d.get('intervention_label', 'N/A')}**\n"
                f"• {d.get('explanation', '')}"
            )

    # ── Specific region lookup ────────────────────────────────────────────
    if region_match:
        r = next((x for x in regs if x["region"] == region_match), None)
        if r:
            uai = float(r.get("avg_uai_score") or 0)
            tier = "Critical" if uai >= 0.65 else "High" if uai >= 0.40 else "Standard"
            icon = "🔴" if tier == "Critical" else "🟠" if tier == "High" else "🟢"
            rdivs = [d for d in divs if d.get("region", "").lower() == region_match.lower()]
            return (
                f"{icon} **{r['region']}**\n"
                f"• Avg UAI: **{uai:.3f}** — {tier} Priority\n"
                f"• Divisions: {r.get('n_divisions')} | Teachers: {r.get('total_teachers'):,} | Schools: {r.get('total_schools'):,}\n"
                f"• 🔴 {r.get('critical_divisions', 0)} Critical | 🟠 {r.get('high_divisions', 0)} High | 🟢 {len(rdivs) - int(r.get('critical_divisions',0)) - int(r.get('high_divisions',0))} Standard\n"
                f"• Avg Mismatch Rate: {_pct(r.get('avg_mismatch_rate'))}%\n"
                f"• Avg Training Gap: {_pct(r.get('avg_training_gap_rate') or r.get('avg_training_gap', 0))}%\n"
                f"• Avg NAT MPS: {round(float(r.get('avg_nat_combined_mps', 50)), 1)}%"
            )

    # ── Regions ranking ───────────────────────────────────────────────────
    if re.search(r"region|province", q) and re.search(r"rank|list|show|which|all|top", q):
        if re.search(r"teacher", q):
            ranked = sorted(regs, key=lambda r: int(r.get("total_teachers", 0)), reverse=True)
            lines = ["**Regions by Total Teachers:**"]
            for r in ranked:
                lines.append(f"• **{r['region']}** — {int(r.get('total_teachers', 0)):,} teachers")
            return "\n".join(lines)
        if re.search(r"school", q):
            ranked = sorted(regs, key=lambda r: int(r.get("total_schools", 0)), reverse=True)
            lines = ["**Regions by Total Schools:**"]
            for r in ranked:
                lines.append(f"• **{r['region']}** — {int(r.get('total_schools', 0)):,} schools")
            return "\n".join(lines)
        if re.search(r"critical", q):
            ranked = sorted(regs, key=lambda r: int(r.get("critical_divisions", 0)), reverse=True)
            lines = ["**Regions by Number of Critical Priority Divisions:**"]
            for r in ranked:
                lines.append(f"🔴 **{r['region']}** — {r.get('critical_divisions', 0)} critical divisions")
            return "\n".join(lines)
        if re.search(r"mismatch", q):
            ranked = sorted(regs, key=lambda r: float(r.get("avg_mismatch_rate", 0)), reverse=True)
            lines = ["**Regions by Avg Mismatch Rate:**"]
            for r in ranked:
                lines.append(f"• **{r['region']}** — {_pct(r.get('avg_mismatch_rate'))}%")
            return "\n".join(lines)
        # Default: by UAI
        lines = ["**Regions by Average UAI Score:**"]
        for r in regs:
            uai = float(r.get("avg_uai_score") or 0)
            tier = "Critical" if uai >= 0.65 else "High" if uai >= 0.40 else "Standard"
            icon = "🔴" if tier == "Critical" else "🟠" if tier == "High" else "🟢"
            lines.append(f"{icon} **{r['region']}** — UAI: {uai:.3f} ({tier})")
        return "\n".join(lines)

    # ── Which region has the most/highest X ──────────────────────────────
    if re.search(r"which region.*(most|highest|most|largest|biggest|best|worst)", q):
        if re.search(r"teacher", q):
            r = max(regs, key=lambda r: int(r.get("total_teachers", 0)))
            return f"**{r['region']}** has the most teachers with **{int(r.get('total_teachers', 0)):,}**."
        if re.search(r"school", q):
            r = max(regs, key=lambda r: int(r.get("total_schools", 0)))
            return f"**{r['region']}** has the most schools with **{int(r.get('total_schools', 0)):,}**."
        if re.search(r"critical", q):
            r = max(regs, key=lambda r: int(r.get("critical_divisions", 0)))
            return f"**{r['region']}** has the most critical divisions: **{r.get('critical_divisions')}**."
        if re.search(r"mismatch", q):
            r = max(regs, key=lambda r: float(r.get("avg_mismatch_rate", 0)))
            return f"**{r['region']}** has the highest avg mismatch rate at **{_pct(r.get('avg_mismatch_rate'))}%**."
        if re.search(r"uai|underserved|priority", q):
            r = regs[0]
            return f"**{r['region']}** has the highest average UAI score at **{float(r.get('avg_uai_score') or 0):.3f}**."
        r = regs[0]
        return f"**{r['region']}** is the most at-risk region with an average UAI of **{float(r.get('avg_uai_score') or 0):.3f}**."

    # ── Training gap rankings ─────────────────────────────────────────────
    if re.search(r"training gap|under.?trained|lacking training|training coverage", q):
        top = sorted(divs, key=lambda d: float(d.get("training_gap_rate", 0)), reverse=True)[:n]
        lines = [f"**Top {n} Divisions with Highest Training Gap:**"]
        for d in top:
            lines.append(
                f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — "
                f"{_pct(d.get('training_gap_rate'))}% under-trained"
            )
        return "\n".join(lines)

    # ── Geographic disadvantage rankings ─────────────────────────────────
    if re.search(r"geo(graphic)?|isolat|remote|access|far|distant", q):
        top = sorted(divs, key=lambda d: float(d.get("avg_geo_disadvantage") or d.get("geo_disadvantage", 0)), reverse=True)[:n]
        lines = [f"**Top {n} Most Geographically Isolated Divisions:**"]
        for d in top:
            score = float(d.get("avg_geo_disadvantage") or d.get("geo_disadvantage", 0))
            lines.append(f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — Geo Score: {score:.3f}")
        return "\n".join(lines)

    # ── Staffing pressure / LTR rankings ─────────────────────────────────
    if re.search(r"staffing|learner.teacher|ltr|overcrowded|overloaded", q):
        top = sorted(divs, key=lambda d: float(d.get("avg_ltr") or d.get("ltr", 0)), reverse=True)[:n]
        lines = [f"**Top {n} Divisions with Highest Staffing Pressure (LTR):**"]
        for d in top:
            ltr = float(d.get("avg_ltr") or d.get("ltr", 0))
            lines.append(f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — LTR: {ltr:.1f}")
        return "\n".join(lines)

    # ── Mismatch rankings ─────────────────────────────────────────────────
    if re.search(r"mismatch", q):
        top = sorted(divs, key=lambda d: float(d.get("mismatch_rate", 0)), reverse=True)[:n]
        lines = [f"**Top {n} Divisions by Mismatch Rate:**"]
        for d in top:
            lines.append(
                f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — {_pct(d.get('mismatch_rate'))}%"
            )
        return "\n".join(lines)

    # ── NAT / performance queries ─────────────────────────────────────────
    if re.search(r"nat|performance|mps|achievement", q):
        if re.search(r"best|highest|top performing", q):
            top = sorted(divs, key=lambda d: float(d.get("nat_combined_mps", 0)), reverse=True)[:n]
            lines = [f"**Top {n} Divisions by NAT MPS (Best Performing):**"]
            for d in top:
                lines.append(f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — NAT MPS: {round(float(d.get('nat_combined_mps', 50)), 1)}%")
        else:
            top = sorted(divs, key=lambda d: float(d.get("nat_combined_mps", 50)))[:n]
            lines = [f"**Top {n} Divisions with Lowest NAT MPS (Need Most Support):**"]
            for d in top:
                lines.append(f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — NAT MPS: {round(float(d.get('nat_combined_mps', 50)), 1)}%")
        return "\n".join(lines)

    # ── Intervention queries ──────────────────────────────────────────────
    if re.search(r"intervention|recommend|program|action|need|require", q):
        # Specific intervention type search
        intervention_keywords = {
            "retrain": "retraining",
            "retraining": "retraining",
            "deployment": "deployment",
            "deploy": "deployment",
            "mentoring": "mentoring",
            "mentor": "mentoring",
            "training": "training",
            "scholarship": "scholarship",
            "capacity": "capacity",
        }
        matched_kw = next((v for k, v in intervention_keywords.items() if k in q), None)
        if matched_kw:
            matched_divs = [d for d in divs if matched_kw.lower() in str(d.get("intervention_label", "")).lower()]
            if matched_divs:
                lines = [f"**Divisions needing '{matched_kw}' intervention ({len(matched_divs)} total):**"]
                for d in matched_divs[:10]:
                    lines.append(f"{_color(_tier(d))} **{d['division']}** ({d['region']}) — UAI: {_uai(d):.3f}")
                if len(matched_divs) > 10:
                    lines.append(f"_...and {len(matched_divs) - 10} more_")
                return "\n".join(lines)

        counts = Counter(d.get("intervention_label", "N/A") for d in divs)
        lines = ["**Recommended Interventions Across All Divisions:**"]
        for label, count in counts.most_common():
            sample = next((d for d in divs if d.get("intervention_label") == label), None)
            desc = sample.get("intervention_description", "") if sample else ""
            lines.append(f"• **{label}** — {count} divisions\n  _{desc}_")
        return "\n".join(lines)

    # ── Summary / overview ────────────────────────────────────────────────
    if re.search(r"summary|overview|dashboard|status|tell me|show me|general", q):
        top3 = divs[:3]
        avg_uai = sum(_uai(d) for d in divs) / len(divs)
        lines = [
            "**STARSight Dashboard Summary**",
            f"• {len(divs)} divisions across {len(regs)} regions",
            f"• {total_teachers:,} teachers | {total_schools:,} schools",
            f"• 🔴 {len(critical_divs)} Critical | 🟠 {len(high_divs)} High | 🟢 {len(standard_divs)} Standard",
            f"• National avg UAI: **{avg_uai:.3f}**",
            "",
            "**Top 3 Most Underserved:**",
        ]
        for d in top3:
            lines.append(f"  {_color(_tier(d))} #{d.get('priority_rank')} {d['division']} ({d['region']}) — UAI: {_uai(d):.3f}")
        lines.append(f"\n**Most At-Risk Region:** {regs[0]['region']} (UAI: {float(regs[0].get('avg_uai_score') or 0):.3f})")
        return "\n".join(lines)

    # ── Fallback ──────────────────────────────────────────────────────────
    return (
        "I'm not sure about that. Try asking:\n"
        "• *Top 5 most underserved divisions*\n"
        "• *Divisions in Region VII*\n"
        "• *Tell me about NCR*\n"
        "• *Which region has the most critical divisions?*\n"
        "• *Highest mismatch rate divisions*\n"
        "• *What is UAI?*\n"
        "• *help* — to see everything I can answer"
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return ChatResponse(reply=answer(req.message))
