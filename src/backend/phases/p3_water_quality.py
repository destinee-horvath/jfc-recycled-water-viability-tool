"""
backend/phases/p3_water_quality.py
========================
PHASE 3 — WATER QUALITY (routed by roadworks application)

Each application type is assessed against its own hard specification table —
no generic case-by-case screen; see the phase 3 flowchart.
"""

from __future__ import annotations

import config as C
from ..models import CheckResult, PhaseResult


def assess_water_quality(inp: dict, ctx: dict = None) -> PhaseResult:
    application = inp.get("application_type", C.APPLICATION_TYPES[0])
    if application == "Concrete Mixing":
        return _assess_concrete(inp)
    if application == "Dust Suppression":
        return _assess_dust_suppression(inp)
    return _assess_earthworks(inp)


def _limit_check(key: str, label: str, meta: dict, val) -> CheckResult:
    """Shared REJECT/PROCEED/CONDITIONAL check against a max/min limit."""
    unit = f" {meta['unit']}".rstrip()
    if val is None:
        return CheckResult(label, "CONDITIONAL", meta["ref"],
                            "No result supplied — sampling required.", key=key)
    if "max" in meta and val > meta["max"]:
        return CheckResult(label, "REJECT", meta["ref"],
                            f"{val:g}{unit} exceeds the limit ≤ {meta['max']:g}{unit}.", key=key)
    if "min" in meta and val < meta["min"]:
        return CheckResult(label, "REJECT", meta["ref"],
                            f"{val:g}{unit} is below the minimum {meta['min']:g}{unit}.", key=key)
    limit = meta.get("max", meta.get("min"))
    return CheckResult(label, "PROCEED", meta["ref"],
                        f"{val:g}{unit} within limit ({limit:g}{unit}).", key=key)


def _assess_concrete(inp: dict) -> PhaseResult:
    """Concrete Mixing — AS 1379 Tables 2.1 (strength), 2.2 (impurities),
    filtered-water turbidity, and 2.3 (reportable only, no threshold)."""
    g = PhaseResult(phase_id="water_quality", mandatory=False)

    # --- Table 2.1: compressive strength vs control sample ------------------
    # No short-circuiting: every parameter is evaluated so the engineer sees
    # the full picture in one pass, not just the first failure.
    strength_pct = inp.get("compression_strength_pct")
    if strength_pct is None:
        g.checks.append(CheckResult(
            "Compressive strength vs control sample", "CONDITIONAL",
            C.CONCRETE_STRENGTH_REF, "No result supplied — testing required.",
            key="compression_strength_pct"))
    elif strength_pct < C.CONCRETE_STRENGTH_MIN_PCT:
        g.checks.append(CheckResult(
            "Compressive strength vs control sample", "REJECT",
            C.CONCRETE_STRENGTH_REF,
            f"{strength_pct:g}% is below the {C.CONCRETE_STRENGTH_MIN_PCT:g}% "
            "minimum of the control sample strength at the corresponding age.",
            key="compression_strength_pct"))
    else:
        g.checks.append(CheckResult(
            "Compressive strength vs control sample", "PROCEED",
            C.CONCRETE_STRENGTH_REF,
            f"{strength_pct:g}% meets the {C.CONCRETE_STRENGTH_MIN_PCT:g}% minimum.",
            key="compression_strength_pct"))

    # --- Table 2.2: impurities ----------------------------------------------
    for key, meta in C.CONCRETE_TABLE_2_2.items():
        g.checks.append(_limit_check(key, meta["label"], meta, inp.get(key)))

    # --- Microbiological (E. coli) -------------------------------------------
    g.checks.append(_limit_check("conc_ecoli", C.CONCRETE_ECOLI["label"], C.CONCRETE_ECOLI, inp.get("conc_ecoli")))

    # --- Filtered water turbidity --------------------------------------------
    turbidity = inp.get("filtered_turbidity_ntu")
    if turbidity is None:
        g.checks.append(CheckResult(
            "Filtered water turbidity", "CONDITIONAL", C.CONCRETE_TURBIDITY_REF,
            "No result supplied — sampling required.", key="filtered_turbidity_ntu"))
    elif turbidity > C.CONCRETE_TURBIDITY_MAX_NTU:
        g.checks.append(CheckResult(
            "Filtered water turbidity", "REJECT", C.CONCRETE_TURBIDITY_REF,
            f"{turbidity:g} NTU exceeds the {C.CONCRETE_TURBIDITY_MAX_NTU:g} NTU "
            f"maximum (target ≤ {C.CONCRETE_TURBIDITY_TARGET_NTU:g} NTU).",
            key="filtered_turbidity_ntu"))
    else:
        g.checks.append(CheckResult(
            "Filtered water turbidity", "PROCEED", C.CONCRETE_TURBIDITY_REF,
            f"{turbidity:g} NTU within the {C.CONCRETE_TURBIDITY_MAX_NTU:g} NTU maximum.",
            key="filtered_turbidity_ntu"))

    # --- Table 2.3: reportable only (no pass/fail threshold) ----------------
    for key, meta in C.CONCRETE_TABLE_2_3.items():
        val = inp.get(key)
        if val is not None:
            g.checks.append(CheckResult(
                f"{meta['label']} (reportable)", "PROCEED", meta["ref"],
                f"{val:g} — recorded for the file; AS 1379 sets no pass/fail limit.",
                key=key))

    g.rollup()
    return g


def _assess_dust_suppression(inp: dict) -> PhaseResult:
    """Dust Suppression — Table 3.8 (unrestricted-access municipal-use tier)."""
    g = PhaseResult(phase_id="water_quality", mandatory=False)

    # No short-circuiting: every parameter is evaluated, not just the first failure.
    pathogen_pct = inp.get("pathogen_pct")
    if pathogen_pct is None:
        g.checks.append(CheckResult(
            "Virus / Protozoa / Bacteria present", "CONDITIONAL",
            C.DUST_PATHOGEN_REF, "No result supplied — sampling required.",
            key="pathogen_pct"))
    elif pathogen_pct >= C.DUST_PATHOGEN_MAX_PCT:
        g.checks.append(CheckResult(
            "Virus / Protozoa / Bacteria present", "REJECT", C.DUST_PATHOGEN_REF,
            f"{pathogen_pct:g}% is at or above the {C.DUST_PATHOGEN_MAX_PCT:g}% limit.",
            key="pathogen_pct"))
    else:
        g.checks.append(CheckResult(
            "Virus / Protozoa / Bacteria present", "PROCEED", C.DUST_PATHOGEN_REF,
            f"{pathogen_pct:g}% is below the {C.DUST_PATHOGEN_MAX_PCT:g}% limit.",
            key="pathogen_pct"))

    for key, meta in C.DUST_TABLE_3_8.items():
        g.checks.append(_limit_check(key, meta["label"], meta, inp.get(key)))

    g.rollup()
    return g


def _assess_earthworks(inp: dict) -> PhaseResult:
    """Earthworks (Compaction) — Table 3-1 impurity limits (Sydney Water
    Recycled) plus AGWR Phase 1 (2006) Table 3.8 microbiological limits."""
    g = PhaseResult(phase_id="water_quality", mandatory=False)
    for key, meta in C.EARTHWORKS_TABLE_3_1.items():
        g.checks.append(_limit_check(key, meta["label"], meta, inp.get(key)))
    for key, meta in C.EARTHWORKS_MICRO_TABLE.items():
        g.checks.append(_limit_check(key, meta["label"], meta, inp.get(key)))
    g.rollup()
    return g
