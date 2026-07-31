"""
backend/phases/p2_rwmp.py
========================
PHASE 2 — RWMP (Recycled Water Management Plan)

Checks 1-2 are deliberately CONDITIONAL, not REJECT, when missing — an RWMP
can be obtained/amended before works commence (see SRS "Known Limitations").
"""

from __future__ import annotations

import config as C
from ..models import CheckResult, PhaseResult


def assess_rwmp(inp: dict, ctx: dict = None) -> PhaseResult:
    g = PhaseResult(phase_id="rwmp", mandatory=True)
    ref = C.RWMS_SOURCE

    # --- Check 1: approved RWMP exists -> CONDITIONAL if missing (obtainable) ---
    if not inp.get("has_approved_rwmp"):
        g.checks.append(CheckResult(
            "Supplier holds an approved RWMP for this scheme", "CONDITIONAL", ref,
            "The supplier does not currently hold an approved RWMP. The supplier "
            "must develop, submit, and obtain approval for an RWMP under the NSW "
            "Guidelines for Recycled Water Management Systems (NSW Office of "
            "Water, May 2015) before works can commence. Works cannot proceed "
            "until this is confirmed. WARNING — this is a significant regulatory "
            "gap, not a minor shortfall: a supplier without an approved RWMP "
            "cannot lawfully hold s.60 approval and should not be supplying "
            "recycled water. Treat this with the same seriousness as a hard "
            "reject.",
        ))
    else:
        g.checks.append(CheckResult(
            "Supplier holds an approved RWMP for this scheme", "PROCEED", ref,
            "Approved RWMP confirmed.",
        ))

    # --- Check 2: RWMP covers this end use -> CONDITIONAL if missing (obtainable) ---
    if not inp.get("lists_roadworks_enduse"):
        g.checks.append(CheckResult(
            "RWMP lists compaction / subgrade moisture preparation as an approved end use",
            "CONDITIONAL", ref,
            "The RWMP exists but does not currently list compaction or subgrade "
            "moisture preparation as an approved end use. The supplier must "
            "amend the RWMP to include this use and obtain updated approval "
            "before works commence. Works cannot proceed until confirmed. "
            "WARNING — this is a significant regulatory gap, not a minor "
            "shortfall: treat this with the same seriousness as a hard reject.",
        ))
    else:
        g.checks.append(CheckResult(
            "RWMP lists compaction / subgrade moisture preparation as an approved end use",
            "PROCEED", ref, "Roadworks end use explicitly covered.",
        ))

    # --- Check 3: supplier written confirmation of 12-element RWMS compliance.
    # DCCEEW already audits this under s.60 — engineer just needs written confirmation. ---
    label = ("Supplier has confirmed in writing that their approved RWMP "
             "complies with all 12 RWMS elements")
    if inp.get("rwmp_12_elements_confirmed"):
        g.checks.append(CheckResult(
            label, "PROCEED", ref,
            "Supplier has confirmed in writing that their approved RWMP "
            "complies with all 12 RWMS elements.",
        ))
    else:
        g.checks.append(CheckResult(
            label, "CONDITIONAL", ref,
            "The supplier has not confirmed that their RWMP complies with "
            "all 12 elements of the RWMS framework as defined in the NSW "
            "Guidelines for Recycled Water Management Systems (NSW Office "
            "of Water, May 2015, pp.11-52). Obtain written confirmation "
            "from the supplier before works commence. Note: if the "
            "supplier holds s.60 approval, their RWMP will already have "
            "been reviewed by DCCEEW against these requirements — ask the "
            "supplier to confirm this in writing. The review and revision "
            "of the RWMP is entirely the supplier's responsibility — the "
            "engineer's role is to obtain written confirmation from the "
            "supplier that this has been done.",
        ))

    # --- Check 4: currency / review period ---
    if inp.get("rwmp_current"):
        g.checks.append(CheckResult(
            "RWMP current / reviewed within required period", "PROCEED", ref,
            "Within review period.",
        ))
    else:
        g.checks.append(CheckResult(
            "RWMP current / reviewed within required period", "CONDITIONAL", ref,
            "Confirm currency with the supplier before proceeding.",
        ))

    g.rollup()
    return g
