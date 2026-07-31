"""
backend/orchestration.py
=========================
Run all phases, roll up per-check readiness.

By design there's no single pass/fail verdict or score — only a
blocking/pending/confirmed breakdown. Per-phase state still rolls up
per-section via section_rollup().
"""

from __future__ import annotations

import config as C
from .models import PhaseResult, _worst
from .phases import PHASE_FUNCS


def run_assessment(inputs: dict[str, dict]) -> dict[str, PhaseResult]:
    """
    Run all phases in config.PHASE_ORDER. Every phase gets the full `inputs`
    dict as ctx, so order doesn't affect results. No phase blocks another —
    a REJECT is surfaced via readiness_summary() but doesn't stop the user
    working through the rest; this is a checklist, not a sequential gate.
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
