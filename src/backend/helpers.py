"""
backend/helpers.py
===================
Small helpers shared across more than one phase assessor. Phase-specific
logic stays in backend/phases/; only put something here once a second phase
needs it.
"""

from __future__ import annotations

from .models import CheckResult


def numeric_trigger(meta: dict, val, indicative: bool) -> CheckResult:
    """A one-sided numeric trigger -> CONDITIONAL when exceeded."""
    unit = f" {meta['unit']}".rstrip()
    if val is None:
        return CheckResult(meta["label"], "CONDITIONAL", meta["ref"], "No result supplied — sampling required.")
    if val > meta["trigger"]:
        kind = "indicative — treat/settle before use" if indicative else "elevated — review case-by-case"
        return CheckResult(
            meta["label"], "CONDITIONAL", meta["ref"],
            f"{val:g}{unit} above trigger {meta['trigger']:g}{unit} ({kind}).",
        )
    return CheckResult(
        meta["label"], "PROCEED", meta["ref"],
        f"{val:g}{unit} within trigger {meta['trigger']:g}{unit}.",
    )
