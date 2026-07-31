"""
backend/models.py
==================
Shared result data structures used by every phase assessor.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Severity ordering for rollup; higher = worse/more blocking.
_SEVERITY = {"NA": 0, "PROCEED": 1, "CONDITIONAL": 2, "REJECT": 3}
_SEVERITY_INV = {v: k for k, v in _SEVERITY.items()}


@dataclass
class CheckResult:
    label: str
    state: str          # PROCEED | CONDITIONAL | REJECT | NA
    reference: str = ""
    detail: str = ""
    # Input key this check evaluates, so the frontend can colour that field.
    # Blank for compound/derived checks with no single field.
    key: str = ""


@dataclass
class PhaseResult:
    phase_id: str
    checks: list[CheckResult] = field(default_factory=list)
    state: str = "NA"
    mandatory: bool = False

    def rollup(self) -> str:
        """Worst state across this phase's checks."""
        if not self.checks:
            return "NA"
        worst = max(_SEVERITY[c.state] for c in self.checks)
        self.state = _SEVERITY_INV[worst]
        return self.state


def _worst(states: list[str]) -> str:
    if not states:
        return "NA"
    return _SEVERITY_INV[max(_SEVERITY[s] for s in states)]
