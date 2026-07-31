"""
backend/phases/p4_site_runoff.py
========================
PHASE 4 — SITE RUNOFF AND EPL RISK (POEO Act 1997)

No hard reject at this phase — every shortfall returns CONDITIONAL (see the
phase 4 flowchart). Gates run as a cascade; each is independent of the
others except where noted.
"""

from __future__ import annotations

import config as C
from ..models import CheckResult, PhaseResult


def assess_site_runoff(inp: dict, ctx: dict = None) -> PhaseResult:
    g = PhaseResult(phase_id="site_runoff", mandatory=False)

    # --- Scheduled-activity threshold (Sch 1, Cl 35) -> is an EPL required? ---
    label = "Does the project involve extraction, or on-site processing (crushing, grinding, or separating), of materials for road construction?"
    detail_note = (
        "Schedule 1 Clause 35 applies to extraction and on-site processing "
        "(crushing, grinding, or separating) of materials for road "
        "construction. It does NOT apply to onsite concrete batching, "
        "compacting road base, general earthworks, or maintenance "
        "activities."
    )
    involves_extraction_or_processing = inp.get("involves_extraction_or_processing", False)
    tonnes = inp.get("project_tonnes") or 0
    regulated = inp.get("in_regulated_area")
    threshold = (C.SCH1_CL35_THRESHOLD_REGULATED if regulated
                 else C.SCH1_CL35_THRESHOLD_ELSEWHERE)

    if not involves_extraction_or_processing:
        g.checks.append(CheckResult(
            label, "PROCEED", C.POEO_REFS["sch1_cl35"],
            f"Cl 35 not triggered. {detail_note}",
        ))
        epl_required = False
    elif tonnes >= threshold:
        g.checks.append(CheckResult(
            label, "CONDITIONAL", C.POEO_REFS["sch1_cl35"],
            f"{tonnes:,.0f} t ≥ {threshold:,.0f} t threshold — this is a "
            f"scheduled activity; an EPL is required under s.48 before "
            f"works commence. {detail_note}",
        ))
        epl_required = True
    else:
        g.checks.append(CheckResult(
            label, "PROCEED", C.POEO_REFS["sch1_cl35"],
            f"{tonnes:,.0f} t below {threshold:,.0f} t threshold — Cl 35 "
            f"not triggered. {detail_note}",
        ))
        epl_required = False

    # --- EPL in place / coverage (only relevant if actually required) ------
    if epl_required:
        if not inp.get("epl_in_place"):
            g.checks.append(CheckResult(
                "Environment Protection Licence (EPL) held", "CONDITIONAL",
                C.POEO_REFS["s48"],
                "Obtain an EPL before works begin.",
            ))
        elif not inp.get("epl_covers_recycled"):
            g.checks.append(CheckResult(
                "EPL covers recycled-water use", "CONDITIONAL",
                C.POEO_REFS["s48"],
                "EPL held but does not cover recycled-water use — vary the licence "
                "before works begin. The assessment continues through all "
                "remaining site checks regardless of this result. Resolve this "
                "item — apply to the NSW EPA to obtain or vary your EPL to cover "
                "recycled water use — before works commence.",
            ))
        else:
            g.checks.append(CheckResult(
                "EPL held and covers recycled-water use", "PROCEED",
                C.POEO_REFS["s48"], "EPL in place and covers the activity.",
            ))

    # --- Proximity to waters -------------------------------------------------
    # None must read as CONDITIONAL ("no result supplied"), never silently
    # pass — else an unentered distance would look the same as a confirmed-safe one.
    dist = inp.get("distance_to_waterway_m")
    if dist is not None and dist < 100:
        g.checks.append(CheckResult(
            "Within 100 m of waterway / drainage / stormwater outlet",
            "CONDITIONAL", C.POEO_REFS["s120"],
            f"{dist:g} m from waters — runoff controls must be confirmed and documented (s.120).",
        ))
    elif dist is not None:
        g.checks.append(CheckResult(
            "Within 100 m of waterway / drainage / stormwater outlet",
            "PROCEED", C.POEO_REFS["s120"],
            f"{dist:g} m from waters — outside the 100 m screening buffer.",
        ))
    else:
        g.checks.append(CheckResult(
            "Within 100 m of waterway / drainage / stormwater outlet",
            "CONDITIONAL", C.POEO_REFS["s120"],
            "Distance to nearest waterway/drainage/stormwater outlet not yet "
            "measured — enter it to confirm this site is outside the 100 m "
            "screening buffer.",
        ))

    # --- Runoff direction -----------------------------------------------------
    # Tri-state (Yes/No/Unconfirmed): a checkbox couldn't distinguish "confirmed
    # not toward waters" from "never checked", so this defaults to CONDITIONAL
    # until actively confirmed. Also accepts legacy True/False from old CSVs.
    slope = inp.get("slope_toward_waterway")
    if slope is True or slope == "Yes":
        g.checks.append(CheckResult(
            "Site slope / drainage directs runoff toward waters", "CONDITIONAL",
            C.POEO_REFS["s120"],
            "Site-specific runoff management plan required.",
        ))
    elif slope is False or slope == "No":
        g.checks.append(CheckResult(
            "Site slope / drainage directs runoff toward waters", "PROCEED",
            C.POEO_REFS["s120"],
            "Confirmed: site slope/drainage does not direct runoff toward waters.",
        ))
    else:
        g.checks.append(CheckResult(
            "Site slope / drainage directs runoff toward waters", "CONDITIONAL",
            C.POEO_REFS["s120"],
            "Not yet confirmed — determine whether site slope/drainage "
            "directs runoff toward waters.",
        ))

    # --- Sensitive receiving environment --------------------------------------
    # Selectbox default is visible to the user, so "None / not sensitive" is a
    # legitimate confirmation, not a silent pass.
    sens = inp.get("sensitive_environment", C.SENSITIVE_ENVIRONMENTS[0])
    if sens and sens != C.SENSITIVE_ENVIRONMENTS[0]:
        g.checks.append(CheckResult(
            "Sensitive receiving environment", "CONDITIONAL",
            f"{C.POEO_REFS['s120']}; {C.POEO_REFS['s123']}",
            f"{sens} — additional environmental assessment required before proceeding.",
        ))
    else:
        g.checks.append(CheckResult(
            "Sensitive receiving environment", "PROCEED",
            f"{C.POEO_REFS['s120']}; {C.POEO_REFS['s123']}",
            "None / not sensitive selected.",
        ))

    # --- PIRMP (mandatory for EPL holders) ------------------------------------
    if inp.get("epl_in_place"):
        if inp.get("pirmp_in_place"):
            g.checks.append(CheckResult(
                "PIRMP in place", "PROCEED", C.POEO_REFS["s153A"],
                "PIRMP documented.",
            ))
        else:
            g.checks.append(CheckResult(
                "PIRMP in place", "CONDITIONAL", C.POEO_REFS["s153A"],
                "Mandatory for EPL holders — must be in place before works commence.",
            ))

    # --- Ponding / overflow risk & containment / emergency response ----------
    # Two sequential questions (FR4.7): containment is only asked about if a
    # risk was actually identified.
    ponding_label = ("Is there a risk of ponding or site overflow, and if so, "
                      "are containment & emergency response procedures documented?")
    if not inp.get("ponding_overflow_risk"):
        g.checks.append(CheckResult(
            ponding_label, "PROCEED", C.POEO_REFS["s120"],
            "No identified risk of ponding or site overflow at this site.",
        ))
    elif inp.get("containment_documented"):
        g.checks.append(CheckResult(
            ponding_label, "PROCEED", C.POEO_REFS["s120"],
            "Ponding/overflow risk identified — containment & emergency "
            "response procedures documented.",
        ))
    else:
        g.checks.append(CheckResult(
            ponding_label, "CONDITIONAL", C.POEO_REFS["s120"],
            "Ponding/overflow risk identified — document the containment "
            "and emergency response procedures before works begin. "
            "Regulators will check this at approval.",
        ))

    g.rollup()
    return g
