"""Rule-based AI chat — answers dashboard queries directly from live data, no API key needed."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.core.data_store import get_divisions, get_regions
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


def answer(msg: str) -> str:
    q = msg.lower().strip()
    divs = _divisions()
    regs = _regions()

    tiers = [_tier(d) for d in divs]
    critical_divs = [d for d in divs if _tier(d) == "Critical Priority"]
    high_divs = [d for d in divs if _tier(d) == "High Priority"]
    standard_divs = [d for d in divs if _tier(d) == "Standard Priority"]

    # ── How many / count queries ──────────────────────────────────────────
    if re.search(r"how many.*(division|region|teacher|school)", q):
        if "critical" in q:
            return f"There are **{len(critical_divs)} Critical Priority divisions** (UAI ≥ 0.65)."
        if "high" in q:
            return f"There are **{len(high_divs)} High Priority divisions** (UAI 0.40–0.65)."
        if "standard" in q:
            return f"There are **{len(standard_divs)} Standard Priority divisions** (UAI < 0.40)."
        if "region" in q:
            return f"There are **{len(regs)} regions** in the dataset."
        if "teacher" in q:
            total = sum(int(d.get("total_teachers", 0)) for d in divs)
            return f"There are **{total:,} teachers** across all divisions."
        if "school" in q:
            total = sum(int(d.get("total_schools", 0)) for d in divs)
            return f"There are **{total:,} schools** across all divisions."
        total_divs = len(divs)
        total_teachers = sum(int(d.get("total_teachers", 0)) for d in divs)
        total_schools = sum(int(d.get("total_schools", 0)) for d in divs)
        return (
            f"**National Summary:**\n"
            f"• {total_divs} divisions across {len(regs)} regions\n"
            f"• {total_teachers:,} teachers, {total_schools:,} schools\n"
            f"• 🔴 {len(critical_divs)} Critical | 🟠 {len(high_divs)} High | 🟢 {len(standard_divs)} Standard"
        )

    # ── Top N divisions ───────────────────────────────────────────────────
    top_match = re.search(r"top\s*(\d+)", q)
    n = int(top_match.group(1)) if top_match else 5

    if re.search(r"top|worst|most underserved|highest (uai|priority)", q):
        tier_filter = None
        if "critical" in q:
            tier_filter = "Critical Priority"
        elif "high" in q:
            tier_filter = "High Priority"
        elif "standard" in q:
            tier_filter = "Standard Priority"

        pool = [d for d in divs if _tier(d) == tier_filter] if tier_filter else divs
        subset = pool[:n]
        if not subset:
            return f"No divisions found for that filter."
        lines = [f"**Top {len(subset)} {'(' + tier_filter + ') ' if tier_filter else ''}Most Underserved Divisions:**"]
        for d in subset:
            lines.append(
                f"{_color(_tier(d))} **#{d.get('priority_rank')} {d['division']}** ({d['region']}) — "
                f"UAI: {_uai(d):.3f}"
            )
        return "\n".join(lines)

    # ── Specific division lookup ──────────────────────────────────────────
    for d in divs:
        name = d["division"].lower()
        if name in q or (len(name) > 5 and name[:6] in q):
            uai = _uai(d)
            tier = _tier(d)
            return (
                f"{_color(tier)} **{d['division']}** ({d['region']})\n"
                f"• UAI Score: **{uai:.3f}** — {tier}\n"
                f"• Priority Rank: **#{d.get('priority_rank')}**\n"
                f"• Teachers: {d.get('total_teachers')} | Schools: {d.get('total_schools')}\n"
                f"• Mismatch Rate: {round(float(d.get('mismatch_rate', 0)) * 100, 1)}%\n"
                f"• Training Gap: {round(float(d.get('training_gap_rate', 0)) * 100, 1)}%\n"
                f"• NAT MPS: {round(float(d.get('nat_combined_mps', 50)), 1)}%\n"
                f"• Recommended Intervention: **{d.get('intervention_label', 'N/A')}**\n"
                f"• {d.get('explanation', '')}"
            )

    # ── Specific region lookup ────────────────────────────────────────────
    for r in regs:
        rname = r["region"].lower()
        if rname in q or rname.replace("region ", "").strip() in q:
            uai = float(r.get("avg_uai_score") or 0)
            tier = "Critical" if uai >= 0.65 else "High" if uai >= 0.40 else "Standard"
            return (
                f"**{r['region']}**\n"
                f"• Avg UAI: **{uai:.3f}** — {tier} Priority\n"
                f"• Divisions: {r.get('n_divisions')} | Teachers: {r.get('total_teachers')} | Schools: {r.get('total_schools')}\n"
                f"• Critical Divisions: 🔴 {r.get('critical_divisions', 0)} | High: 🟠 {r.get('high_divisions', 0)}\n"
                f"• Avg Mismatch: {round(float(r.get('avg_mismatch_rate', 0)) * 100, 1)}%\n"
                f"• Avg NAT MPS: {round(float(r.get('avg_nat_combined_mps', 50)), 1)}%"
            )

    # ── Regions ranking ───────────────────────────────────────────────────
    if re.search(r"region|province", q) and re.search(r"rank|list|show|which|all|top", q):
        lines = [f"**Regions by Average UAI Score:**"]
        for r in regs:
            uai = float(r.get("avg_uai_score") or 0)
            tier = "Critical" if uai >= 0.65 else "High" if uai >= 0.40 else "Standard"
            icon = "🔴" if tier == "Critical" else "🟠" if tier == "High" else "🟢"
            lines.append(f"{icon} **{r['region']}** — UAI: {uai:.3f} ({tier})")
        return "\n".join(lines)

    # ── Intervention queries ──────────────────────────────────────────────
    if re.search(r"intervention|recommend|program|action", q):
        from collections import Counter
        counts = Counter(d.get("intervention_label", "N/A") for d in divs)
        lines = ["**Recommended Interventions Across Divisions:**"]
        for label, count in counts.most_common():
            sample = next((d for d in divs if d.get("intervention_label") == label), None)
            desc = sample.get("intervention_description", "") if sample else ""
            lines.append(f"• **{label}** — {count} divisions\n  _{desc}_")
        return "\n".join(lines)

    # ── Mismatch queries ──────────────────────────────────────────────────
    if re.search(r"mismatch", q):
        top = sorted(divs, key=lambda d: float(d.get("mismatch_rate", 0)), reverse=True)[:5]
        lines = ["**Top 5 Divisions by Mismatch Rate:**"]
        for d in top:
            lines.append(f"• **{d['division']}** ({d['region']}) — {round(float(d.get('mismatch_rate', 0)) * 100, 1)}%")
        return "\n".join(lines)

    # ── NAT / performance queries ─────────────────────────────────────────
    if re.search(r"nat|performance|score|mps", q):
        low = sorted(divs, key=lambda d: float(d.get("nat_combined_mps", 50)))[:5]
        lines = ["**Top 5 Divisions with Lowest NAT MPS (need most support):**"]
        for d in low:
            lines.append(f"• **{d['division']}** ({d['region']}) — NAT MPS: {round(float(d.get('nat_combined_mps', 50)), 1)}%")
        return "\n".join(lines)

    # ── UAI explanation ───────────────────────────────────────────────────
    if re.search(r"what is uai|explain uai|uai mean|uai formula|uai work", q):
        return (
            "**Underserved Area Index (UAI)**\n"
            "UAI measures how underserved a division is for STAR capacity-building. Higher = more need.\n\n"
            "**Formula:**\n"
            "UAI = 0.30 × Mismatch + 0.25 × Training Gap + 0.20 × Geo Disadvantage + 0.15 × LTR + 0.10 × NAT Gap\n\n"
            "**Priority Tiers:**\n"
            "🔴 Critical Priority — UAI ≥ 0.65\n"
            "🟠 High Priority — UAI 0.40–0.65\n"
            "🟢 Standard Priority — UAI < 0.40"
        )

    # ── Summary / overview ────────────────────────────────────────────────
    if re.search(r"summary|overview|dashboard|status|tell me|show me", q):
        total_teachers = sum(int(d.get("total_teachers", 0)) for d in divs)
        total_schools = sum(int(d.get("total_schools", 0)) for d in divs)
        top3 = divs[:3]
        lines = [
            "**STARSight Dashboard Summary**",
            f"• {len(divs)} divisions across {len(regs)} regions",
            f"• {total_teachers:,} teachers | {total_schools:,} schools",
            f"• 🔴 {len(critical_divs)} Critical | 🟠 {len(high_divs)} High | 🟢 {len(standard_divs)} Standard",
            "",
            "**Top 3 Most Underserved:**",
        ]
        for d in top3:
            lines.append(f"  {_color(_tier(d))} #{d.get('priority_rank')} {d['division']} ({d['region']}) — UAI: {_uai(d):.3f}")
        lines.append(f"\n**Most At-Risk Region:** {regs[0]['region']} (UAI: {float(regs[0].get('avg_uai_score') or 0):.3f})")
        return "\n".join(lines)

    # ── Fallback ──────────────────────────────────────────────────────────
    return (
        "I can answer questions about the STARSight dashboard data. Try asking:\n"
        "• *What are the top 5 critical priority divisions?*\n"
        "• *Tell me about BARMM*\n"
        "• *Which region has the highest UAI?*\n"
        "• *What interventions are recommended?*\n"
        "• *What is UAI?*\n"
        "• *Give me a dashboard summary*"
    )


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    return ChatResponse(reply=answer(req.message))
