"""
tests/test_rwmp.py
=====================
PHASE 2 — RWMP: CONDITIONAL / PROCEED coverage. Never a hard reject — RWMP
existence and end-use coverage are CONDITIONAL (obtainable before works
commence, mirroring the Phase 1 dual-approval reasoning), same as the
12-element written-confirmation and currency checks. This is a deliberate
design choice, not an oversight: see the SRS "Known Limitations" note.

Check 3 is a supplier written-confirmation flag (rwmp_12_elements_confirmed),
not an engineer element-by-element audit — DCCEEW already assesses RWMP
compliance with the 12 elements as part of s.60 approval.
"""

from backend.phases.p2_rwmp import assess_rwmp

VALID = {
    "has_approved_rwmp": True,
    "lists_roadworks_enduse": True,
    "rwmp_12_elements_confirmed": True,
    "rwmp_current": True,
}


def test_proceed_when_fully_compliant():
    r = assess_rwmp(VALID)
    assert r.state == "PROCEED"


def test_conditional_when_no_approved_rwmp():
    r = assess_rwmp(dict(VALID, has_approved_rwmp=False))
    assert r.state == "CONDITIONAL"
    check = next(c for c in r.checks if c.label == "Supplier holds an approved RWMP for this scheme")
    assert check.state == "CONDITIONAL"
    assert "WARNING" in check.detail
    assert "s.60" in check.detail


def test_conditional_when_enduse_not_listed():
    r = assess_rwmp(dict(VALID, lists_roadworks_enduse=False))
    assert r.state == "CONDITIONAL"
    check = next(c for c in r.checks
                 if c.label == "RWMP lists compaction / subgrade moisture preparation as an approved end use")
    assert check.state == "CONDITIONAL"
    assert "WARNING" in check.detail


def test_rwmp_never_returns_reject():
    """Deliberate design choice: no combination of inputs should ever
    produce REJECT."""
    scenarios = [
        {},
        dict(VALID, has_approved_rwmp=False),
        dict(VALID, lists_roadworks_enduse=False),
        dict(VALID, has_approved_rwmp=False, lists_roadworks_enduse=False,
             rwmp_12_elements_confirmed=False, rwmp_current=False),
    ]
    for inp in scenarios:
        assert assess_rwmp(inp).state != "REJECT", inp


def test_remaining_checks_still_evaluated_when_rwmp_missing():
    """Checks 1/2 no longer short-circuit — still evaluated even when the
    RWMP itself is missing."""
    r = assess_rwmp(dict(VALID, has_approved_rwmp=False))
    labels = {c.label for c in r.checks}
    assert ("Supplier has confirmed in writing that their approved RWMP "
            "complies with all 12 RWMS elements") in labels
    assert "RWMP current / reviewed within required period" in labels


def test_conditional_when_supplier_has_not_confirmed_12_elements():
    r = assess_rwmp(dict(VALID, rwmp_12_elements_confirmed=False))
    assert r.state == "CONDITIONAL"
    check = next(c for c in r.checks
                 if c.label == "Supplier has confirmed in writing that their "
                 "approved RWMP complies with all 12 RWMS elements")
    assert check.state == "CONDITIONAL"
    assert "DCCEEW" in check.detail


def test_proceed_when_supplier_has_confirmed_12_elements():
    r = assess_rwmp(dict(VALID, rwmp_12_elements_confirmed=True))
    check = next(c for c in r.checks
                 if c.label == "Supplier has confirmed in writing that their "
                 "approved RWMP complies with all 12 RWMS elements")
    assert check.state == "PROCEED"


def test_conditional_when_not_current():
    r = assess_rwmp(dict(VALID, rwmp_current=False))
    assert r.state == "CONDITIONAL"
