"""
backend/phases/p1_supplier_approval.py
========================
PHASE 1 — SUPPLIER APPROVAL + DUAL APPROVAL (user-side)

Check order: (1) historical operation, (2) water source routing, (3) stormwater
alternative approval or (4-5) supplier-type approval, (7) discharge-point
trap, (8) dual approval. See each section below for the specific rules.
"""

from __future__ import annotations

import config as C
from ..models import CheckResult, PhaseResult


def assess_supplier_approval(inp: dict, ctx: dict = None) -> PhaseResult:
    g = PhaseResult(phase_id="supplier_approval", mandatory=True)

    # --- Check 1: historical operation without approval -> AUTO REJECT, stop ---
    if inp.get("operated_without_approval"):
        g.checks.append(CheckResult(
            "Scheme operated historically without approval",
            "REJECT",
            "Local Government Act 1993 / Water Management Act 2000",
            "No retrospective approval is possible. This check overrides all "
            "other checks — assessment cannot proceed.",
        ))
        g.rollup()
        return g

    # --- Check 2: water source routing ---
    source = inp.get("water_source", C.WATER_SOURCES[0])

    if source == "Stormwater":
        # --- Check 3a: Sydney/Hunter Water operational area ---
        if inp.get("sydney_hunter_area"):
            g.checks.append(CheckResult(
                "Sydney/Hunter Water operational area", "PROCEED", C.SYDNEY_HUNTER_REF,
                "s.68 LGA does not apply in Sydney Water or Hunter Water "
                "operational areas. Proceed via the Sydney Water Stormwater "
                "Harvesting Agreement and WMA 2000 approvals.",
            ))
        else:
            # --- Check 3b: stormwater approvals (never a hard reject) ---
            label = "Stormwater: s.68 council approval, development consent, WMA 2000"
            state = inp.get("stormwater_approvals_held", C.APPROVAL_STATES[-1])
            if state == "Yes":
                g.checks.append(CheckResult(label, "PROCEED", C.STORMWATER_APPROVAL_REF,
                    "Alternative stormwater approvals confirmed."))
            elif state == "No":
                g.checks.append(CheckResult(label, "CONDITIONAL", C.STORMWATER_APPROVAL_REF,
                    "s.68 LGA council approval, development consent, and WMA 2000 "
                    "approvals must be obtained before works commence. This is "
                    "not a hard reject — approvals are obtainable."))
            else:
                g.checks.append(CheckResult(label, "CONDITIONAL", C.STORMWATER_APPROVAL_REF,
                    "Confirm s.68, development consent, and WMA 2000 approval "
                    "status with the relevant authorities before proceeding."))

        # --- Check 3c / 7: discharge trap does not apply to stormwater ---
        g.checks.append(CheckResult(
            "Effluent: licensed discharge point vs approved use", "NA", "",
            "Discharge trap not applicable for stormwater source.",
        ))

    else:
        # --- Check 4/5: supplier type routing -> council or water authority approval ---
        # Private scheme (s.68 greywater/blackwater) is not covered: s.68
        # private-scheme approvals are for small-scale septic systems, not a
        # credible pathway for recycled water at roadworks scale. Only
        # council-run and water-authority schemes remain here.
        authority = inp.get("supplier_authority", C.SUPPLIER_AUTHORITIES[0])
        ref = C.SUPPLIER_APPROVAL_REFS.get(authority, "")
        label = "Supplier: statutory supply approval held?"

        field = "council_approval_held" if authority == "Council-run scheme" else "authority_approval_held"
        state = inp.get(field, C.APPROVAL_STATES[-1])
        if state == "Yes":
            g.checks.append(CheckResult(label, "PROCEED", ref,
                f"{authority} approval confirmed."))
        elif state == "No":
            g.checks.append(CheckResult(label, "REJECT", ref,
                f"{authority} does not hold the required ministerial approval "
                "under the cited provision. This is a hard gate."))
            g.rollup()
            return g
        else:
            g.checks.append(CheckResult(label, "CONDITIONAL", ref,
                f"Confirm that the {authority.lower()} holds a current "
                "ministerial approval under the cited provision before proceeding."))

        # --- Check 7: discharge-point trap (treated effluent / other) ---
        if inp.get("discharge_only"):
            g.checks.append(CheckResult(
                "Effluent: licensed discharge point vs approved use", "REJECT",
                C.DUAL_APPROVAL_REF,
                "The supplier holds only a licensed discharge point, not an "
                "approved use for this roadworks application. A licensed "
                "discharge point is NOT approval to use the water. This is a "
                "hard gate.",
            ))
            g.rollup()
            return g
        g.checks.append(CheckResult(
            "Effluent: licensed discharge point vs approved use", "PROCEED",
            C.DUAL_APPROVAL_REF,
            "Supplier holds an approved use, not just a discharge point.",
        ))

    # --- Check 8: dual approval — user-side permission to USE the water (all sources) ---
    user_state = inp.get("user_approval_state", C.USER_APPROVAL_STATES[-1])
    if user_state == "Permitted for this use":
        g.checks.append(CheckResult(
            "User approval permits recycled-water use for this application",
            "PROCEED", C.DUAL_APPROVAL_REF,
            "User's EPL / development consent explicitly permits the intended use.",
        ))
    elif user_state == "Not permitted for this use":
        g.checks.append(CheckResult(
            "User approval permits recycled-water use for this application",
            "CONDITIONAL", C.DUAL_APPROVAL_REF,
            "User's own EPL / consent does not currently permit this use — "
            "supplier approval alone is insufficient. This is obtainable: vary "
            "the EPL or obtain development consent before works commence.",
        ))
    else:
        g.checks.append(CheckResult(
            "User approval permits recycled-water use for this application",
            "CONDITIONAL", C.DUAL_APPROVAL_REF,
            "Unconfirmed — verify the user's EPL / development consent covers "
            "this use before proceeding. Supplier approval does not cover "
            "user-side permission.",
        ))

    g.rollup()
    return g
