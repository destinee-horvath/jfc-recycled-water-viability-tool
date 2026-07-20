"""
backend/orchestration.py
=========================
ORCHESTRATION — run all phases, roll up per-check readiness.

No single pass/fail verdict or numeric score is computed here (removed —
clients only want the blocking/pending/confirmed breakdown, not a headline
VIABLE/CONDITIONAL/NOT VIABLE judgment or a 0-100 score). Each phase's own
state (PROCEED/CONDITIONAL/REJECT/NA) still exists and still rolls up
per-section (section_rollup) — only the single overall app-wide verdict is
gone.
"""

from __future__ import annotations

import config as C
from .models import PhaseResult, _worst
from .phases import PHASE_FUNCS


def run_assessment(inputs: dict[str, dict]) -> dict[str, PhaseResult]:
    """
    Run all phases in the order given by config.PHASE_ORDER (flat 1-7, or
    grouped, per config.USE_GROUPED_SECTIONS). Every phase always receives
    the full `inputs` dict as its ctx regardless of order, so execution
    order has no effect on any phase's own result — this only changes the
    order results are computed in, not what they compute. Every phase is
    always assessed and always editable — a REJECT anywhere is surfaced as a
    checklist item via readiness_summary(), but it does not block the user
    from working through the remaining phases. This is a decision-support
    checklist, not a sequential gate.
    """
    results: dict[str, PhaseResult] = {}
    for pid in C.PHASE_ORDER:
        phase = C.PHASE_BY_ID[pid]
        res = PHASE_FUNCS[pid](inputs.get(pid, {}), inputs)
        res.mandatory = phase["mandatory"]
        results[pid] = res
    return results


def section_rollup(phase_results: list[PhaseResult]) -> str:
    """Worst state across a section's member phases (NA < PROCEED <
    CONDITIONAL < REJECT), for the grouped UI's section badges."""
    return _worst([r.state for r in phase_results])


def readiness_summary(results: dict[str, PhaseResult]) -> dict:
    """
    Flat blocking/pending/confirmed check lists across every phase — no
    verdict string, no score. REJECT checks are action items required before
    works (blocking); CONDITIONAL checks are pending action items; PROCEED
    checks are confirmed.
    """
    blocking = [c for r in results.values() for c in r.checks if c.state == "REJECT"]
    pending = [c for r in results.values() for c in r.checks if c.state == "CONDITIONAL"]
    confirmed = [c for r in results.values() for c in r.checks if c.state == "PROCEED"]

    return {
        "blocking": blocking,
        "pending": pending,
        "confirmed": confirmed,
    }
