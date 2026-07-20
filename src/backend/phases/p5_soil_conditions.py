"""
backend/phases/p5_soil_conditions.py
========================
PHASE 5 — SOIL & SITE CONDITIONS

Two independent checks:

1. USCS soil classification and pavement-layer data (subgrade, sub-base,
   base) that frontend/pages/p5_soil_conditions.py passes as default values
   into Financial Feasibility's pavement-profile inputs — see
   config.USCS_SOIL_TABLE. Information-entry only; always PROCEEDs.

2. SAR/EC structural-stability screen: whether the recycled water source
   risks degrading the structure of the NATURAL subgrade soil (dispersion/
   slaking, loss of permeability and strength) — see config.py's "PHASE 5 —
   SAR/EC soil structural stability" section for the boundary formula and
   its provenance. Never a hard REJECT (client decision, 2026-07-14) —
   remediable via soil dispersion testing and gypsum/lime amendment, so the
   worst outcome here is CONDITIONAL.
"""

from __future__ import annotations

import config as C
from ..models import CheckResult, PhaseResult


def _stability_threshold_sar(ec_dsm: float) -> float:
    """SAR threshold at a given EC, per the client-derived linear stability
    boundary (SAR = slope*EC + intercept) — see config.py's PHASE 5 SAR/EC
    section. A sample is stable if its actual SAR is on/below this line."""
    return C.SOIL_STABILITY_SLOPE * ec_dsm + C.SOIL_STABILITY_INTERCEPT


def _ussl_c_class(ec_dsm: float) -> str:
    """USSL salinity-hazard class from EC — fixed thresholds, no ambiguity.
    See config.SOIL_USSL_C_CLASS_US_CM for why the S (sodium-hazard) class
    isn't computed alongside this."""
    ec_us_cm = ec_dsm * 1000
    for limit, label in C.SOIL_USSL_C_CLASS_US_CM:
        if ec_us_cm <= limit:
            return label
    return C.SOIL_USSL_C_CLASS_US_CM[-1][1]


def _assess_sar_ec(inp: dict, ctx: dict) -> list[CheckResult]:
    checks: list[CheckResult] = []
    sar = inp.get("soil_water_sar")
    ec = inp.get("soil_water_ec_dsm")

    if sar is None or ec is None:
        checks.append(CheckResult(
            "SAR/EC soil structural stability", "CONDITIONAL", C.SOIL_SAR_EC_REF,
            "No SAR and/or EC result supplied for the recycled water source "
            "— sampling required before assessing structural stability risk "
            "to the natural subgrade soil."))
        return checks

    threshold_sar = _stability_threshold_sar(ec)
    basis = (
        f"threshold SAR <= {threshold_sar:.1f} at EC {ec:g} dS/m, per "
        f"SAR = {C.SOIL_STABILITY_SLOPE:g}*EC {C.SOIL_STABILITY_INTERCEPT:+g}"
    )
    if sar <= threshold_sar:
        checks.append(CheckResult(
            "SAR/EC soil structural stability", "PROCEED", C.SOIL_SAR_EC_REF,
            f"SAR {sar:g} sits on/below the stability boundary ({basis}). "
            "Soil structure not expected to be adversely affected."))
    else:
        checks.append(CheckResult(
            "SAR/EC soil structural stability", "CONDITIONAL", C.SOIL_SAR_EC_REF,
            f"SAR {sar:g} exceeds the stability boundary ({basis}) — "
            "degradation of soil structure (dispersion/slaking) is likely. "
            "Soil dispersion testing (e.g. Emerson class or Exchangeable "
            "Sodium Percentage) and a gypsum/lime amendment plan are "
            "required before this water is used on the subgrade; re-test "
            "after amendment."))

    checks.append(CheckResult(
        "USSL salinity classification (informational)", "PROCEED", C.SOIL_USSL_REF,
        f"{_ussl_c_class(ec)} at EC {ec:g} dS/m ({ec * 1000:g} µS/cm). "
        "Sodium (S-class) sub-classification is not reproduced here — see "
        "the SAR/EC structural stability result above for the operative "
        "sodium/dispersion risk determination."))

    region = ctx.get("financial", {}).get("region")
    if region in C.SOIL_LOW_RAINFALL_REGIONS:
        checks.append(CheckResult(
            "Rainfall context vs. stability-chart assumption", "CONDITIONAL",
            C.SOIL_SAR_EC_REF,
            f"Selected region ({region}) is drier, long-term, than Figure "
            "2's ~1000mm/yr rainfall assumption — salt leaching through the "
            "profile will be slower than the chart assumes, which can "
            "understate the true structural risk. Treat the result above "
            "with extra caution and consider site-specific dispersion "
            "testing regardless of the calculated outcome."))

    return checks


def assess_soil_conditions(inp: dict, ctx: dict = None) -> PhaseResult:
    g = PhaseResult(phase_id="soil_conditions", mandatory=False)
    g.checks.append(CheckResult(
        "Soil & site classification", "PROCEED", C.SOIL_TABLE_REF,
        "Soil classification data recorded. Values available as defaults "
        "in Financial Feasibility."))
    g.checks.extend(_assess_sar_ec(inp, ctx or {}))
    g.rollup()
    return g
