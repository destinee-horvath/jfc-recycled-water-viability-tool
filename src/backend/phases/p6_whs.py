"""
backend/phases/p6_whs.py
========================
PHASE 6 — WORKER HEALTH & SAFETY (WHS)

No hard reject — WHS shortfalls are remediable (CONDITIONAL,
action-before-works). It's a strict-liability regime, so every gate holds
CONDITIONAL until resolved rather than REJECT.
"""

from __future__ import annotations

import config as C
from ..models import CheckResult, PhaseResult

_CLASS_ORDER = {c: i for i, c in enumerate(C.WATER_CLASSES)}


def _class_meets_requirement(selected_class: str, required_class: str) -> bool:
    """True if selected_class is at least as strict as required_class."""
    sel_idx = _CLASS_ORDER.get(selected_class, len(C.WATER_CLASSES))
    req_idx = _CLASS_ORDER.get(required_class, len(C.WATER_CLASSES))
    return sel_idx <= req_idx


def assess_whs(inp: dict, ctx: dict = None) -> PhaseResult:
    g = PhaseResult(phase_id="whs", mandatory=True)

    # --- Proximity to sensitive receptors (buffer zone) ---------------------
    # Always CONDITIONAL — only an indicative range by water class exists, not
    # a real distance to test (see config.AGWR_BUFFER_ZONE_LIMITATION_NOTE).
    method = inp.get("application_method", C.APPLICATION_METHODS[0])
    selected_class = ((ctx or {}).get("water_quality", {}) or {}).get("water_class")
    buffer_range = C.AGWR_BUFFER_ZONE_RANGE_METRES.get(selected_class)
    if buffer_range is None:
        buffer_detail = (
            "Water quality class not yet confirmed — buffer zone range "
            "cannot be estimated. Classify the water source in Phase 3 "
            "before this check can be resolved.")
    else:
        low, high = buffer_range
        buffer_detail = (
            f"Buffer zone requires site-specific assessment. Based on AGWR "
            f"{selected_class} water, an indicative buffer distance of "
            f"{low}–{high}m applies to houses, schools, playing fields, "
            f"roads, public open space, and water bodies. Confirm exact "
            f"distance with NSW Health before works commence.")
    g.checks.append(CheckResult(
        "Buffer zone — needs assessment", "CONDITIONAL",
        C.AGWR_BUFFER_ZONE_REF, buffer_detail))

    # --- Application method -> contact/exposure risk ------------------------
    if method == "Sprayed (higher contact)":
        if inp.get("wind_weather_checked"):
            g.checks.append(CheckResult(
                "Wind/weather checked before spraying", "PROCEED",
                C.WHS_SPRAY_WEATHER_REF,
                "Spray drift, wind and weather confirmed before application."))
        else:
            g.checks.append(CheckResult(
                "Wind/weather checked before spraying", "CONDITIONAL",
                C.WHS_SPRAY_WEATHER_REF,
                "Higher contact risk — check spray drift, wind and weather before "
                "application and set worker exclusion zones."))
    else:
        g.checks.append(CheckResult(
            "Application method: direct", "PROCEED", C.WHS_REF,
            C.WHS_METHOD_NOTES[method]))

    # --- Human contact risk (workers / public) ------------------------------
    contact = inp.get("contact_risk", C.CONTACT_RISK_LEVELS[0])
    if contact == "None expected":
        g.checks.append(CheckResult(
            "Human contact with treated area", "PROCEED", C.WHS_REF,
            "No contact expected — " + C.WHS_IRRIGATION_NOTE))
    elif contact == "Workers only":
        g.checks.append(CheckResult(
            "Human contact with treated area", "CONDITIONAL", C.WHS_REF,
            "Moderate risk — ensure PPE and SWMS cover all direct-contact scenarios."))
    else:
        g.checks.append(CheckResult(
            "Human contact with treated area", "CONDITIONAL", C.WHS_REF,
            f"{contact} may contact the area during/after application. "
            f"{C.WHS_TREATMENT_NOTE} {C.NSW_HEALTH_NOTE}"))

    # --- Treatment standard vs contact-risk level ---------------------------
    required_class = C.CONTACT_RISK_MIN_CLASS.get(contact)
    selected_class = ((ctx or {}).get("water_quality", {}) or {}).get("water_class")
    if required_class is None:
        g.checks.append(CheckResult(
            "Treatment standard matches contact-risk level", "PROCEED",
            C.WATER_CLASS_REF, "No minimum water class required for this contact-risk level."))
    elif not selected_class:
        g.checks.append(CheckResult(
            "Treatment standard matches contact-risk level", "CONDITIONAL",
            C.WATER_CLASS_REF,
            f"No water class selected in Phase 3 — confirm it meets the "
            f"{required_class} minimum required for {contact.lower()} contact."))
    elif not _class_meets_requirement(selected_class, required_class):
        g.checks.append(CheckResult(
            "Treatment standard matches contact-risk level", "CONDITIONAL",
            C.WATER_CLASS_REF,
            f"{selected_class} is insufficient for {contact.lower()} contact "
            f"(requires {required_class} or better) — reassess the water "
            "quality class in Phase 3."))
    else:
        g.checks.append(CheckResult(
            "Treatment standard matches contact-risk level", "PROCEED",
            C.WATER_CLASS_REF,
            f"{selected_class} meets the {required_class} minimum required for "
            f"{contact.lower()} contact."))

    # --- WHS notification / PPE / SWMS / signage checklist ------------------
    # One combined check, not 5 separate ones.
    all_confirmed = all(inp.get(key) for key, _ in C.WHS_CHECKS)
    if all_confirmed:
        g.checks.append(CheckResult(
            "All WHS checks confirmed? All five items below must be "
            "confirmed YES before this check returns PROCEED. Any single "
            "NO triggers CONDITIONAL.",
            "PROCEED", C.WHS_REF, "All five WHS checklist items confirmed.",
        ))
    else:
        g.checks.append(CheckResult(
            "All WHS checks confirmed? All five items below must be "
            "confirmed YES before this check returns PROCEED. Any single "
            "NO triggers CONDITIONAL.",
            "CONDITIONAL", C.WHS_REF,
            "One or more WHS checks have not been confirmed. All five "
            "items must be in place before works commence: (1) workers "
            "notified of water classification and source, (2) health "
            "risks communicated, (3) PPE specified and available, "
            "(4) SWMS covering recycled water use in place, (5) signage "
            "and wash-facility controls confirmed.",
        ))

    g.rollup()
    return g
