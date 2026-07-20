"""
tests/test_whs.py
=====================
PHASE 6 — Worker Health & Safety: CONDITIONAL / PROCEED coverage.
No REJECT case — it's a strict-liability regime, but shortfalls are
remediable (CONDITIONAL), never a hard reject; asserted as an invariant below.

The buffer-zone check (see test_buffer_zone_* below) is always CONDITIONAL —
there's no real distance to test a yes/no question against, only an
indicative AGWR-class range — so the phase as a whole can never resolve to
PROCEED any more, even in the "everything else is perfect" case.
"""

import config as C
from backend.phases.p6_whs import assess_whs

WHS_ALL_CONFIRMED = {
    "whs_notified_class": True,
    "whs_health_risks": True,
    "whs_ppe": True,
    "whs_swms": True,
    "whs_signage": True,
}

VALID = dict(
    WHS_ALL_CONFIRMED,
    application_method="Direct application (low contact)",
    contact_risk="None expected",
)


def test_conditional_when_low_risk_and_checklist_complete():
    """Was PROCEED before the buffer-zone check became always-CONDITIONAL —
    every other check here still individually PROCEEDs; only the overall
    phase rollup changed."""
    r = assess_whs(VALID)
    assert r.state == "CONDITIONAL"
    non_buffer_checks = [c for c in r.checks if c.label != "Buffer zone — needs assessment"]
    assert all(c.state == "PROCEED" for c in non_buffer_checks)


def test_conditional_when_spraying_without_weather_check():
    inp = dict(VALID, application_method="Sprayed (higher contact)",
               wind_weather_checked=False)
    r = assess_whs(inp)
    assert r.state == "CONDITIONAL"


def test_wind_weather_check_proceeds_when_confirmed_before_spraying():
    # Overall phase state is still CONDITIONAL here (buffer zone is always
    # CONDITIONAL) — check the wind/weather gate specifically.
    inp = dict(VALID, application_method="Sprayed (higher contact)",
               wind_weather_checked=True)
    r = assess_whs(inp)
    check = next(c for c in r.checks if c.label == "Wind/weather checked before spraying")
    assert check.state == "PROCEED"


def _buffer_check(inp, ctx=None):
    r = assess_whs(inp, ctx)
    return next(c for c in r.checks if c.label == "Buffer zone — needs assessment")


def test_buffer_zone_conditional_and_ranged_for_class_a():
    check = _buffer_check(VALID, {"water_quality": {"water_class": "Class A"}})
    assert check.state == "CONDITIONAL"
    assert "AGWR Class A water" in check.detail
    assert "25–30m" in check.detail
    assert "NSW Health" in check.detail


def test_buffer_zone_conditional_and_ranged_for_class_b():
    check = _buffer_check(VALID, {"water_quality": {"water_class": "Class B"}})
    assert check.state == "CONDITIONAL"
    assert "AGWR Class B water" in check.detail
    assert "25–30m" in check.detail


def test_buffer_zone_conditional_and_ranged_for_class_c():
    check = _buffer_check(VALID, {"water_quality": {"water_class": "Class C"}})
    assert check.state == "CONDITIONAL"
    assert "AGWR Class C water" in check.detail
    assert "30–50m" in check.detail


def test_buffer_zone_conditional_and_ranged_for_class_d():
    check = _buffer_check(VALID, {"water_quality": {"water_class": "Class D"}})
    assert check.state == "CONDITIONAL"
    assert "AGWR Class D water" in check.detail
    assert "50–100m" in check.detail


def test_buffer_zone_conditional_when_unclassified():
    check = _buffer_check(VALID, {"water_quality": {"water_class": "Unclassified"}})
    assert check.state == "CONDITIONAL"
    assert "not yet confirmed" in check.detail
    assert "Classify the water source in Phase 3" in check.detail


def test_buffer_zone_conditional_when_no_water_class_selected_at_all():
    """No Phase 3 ctx at all (or water_class missing) — same 'classify
    first' message as an explicit Unclassified selection."""
    check = _buffer_check(VALID)
    assert check.state == "CONDITIONAL"
    assert "not yet confirmed" in check.detail


def test_buffer_zone_never_proceeds():
    for cls in list(C.AGWR_BUFFER_ZONE_RANGE_METRES) + ["Unclassified", None]:
        ctx = {"water_quality": {"water_class": cls}} if cls else None
        assert _buffer_check(VALID, ctx).state == "CONDITIONAL"


def test_conditional_when_water_class_insufficient_for_public_contact():
    inp = dict(VALID, contact_risk="Workers and public")
    ctx = {"water_quality": {"water_class": "Class C"}}
    r = assess_whs(inp, ctx)
    assert r.state == "CONDITIONAL"


def test_class_check_proceeds_when_water_class_meets_public_contact_requirement():
    # Overall phase state is still CONDITIONAL here — "Workers and public"
    # contact always raises its own CONDITIONAL note — so check the
    # class-vs-risk gate specifically rather than the overall rollup.
    inp = dict(VALID, contact_risk="Workers and public")
    ctx = {"water_quality": {"water_class": "Class A"}}
    r = assess_whs(inp, ctx)
    class_check = next(c for c in r.checks if c.label == "Treatment standard matches contact-risk level")
    assert class_check.state == "PROCEED"


def test_conditional_when_whs_checklist_incomplete():
    inp = dict(VALID, whs_ppe=False)
    r = assess_whs(inp)
    assert r.state == "CONDITIONAL"


def test_whs_checklist_is_a_single_combined_check():
    """Client review: relabelled to one combined 'All WHS checks confirmed?'
    check (was 5 independent per-item checks) — any single NO triggers
    CONDITIONAL, and the reason text enumerates all five items."""
    r = assess_whs(dict(VALID, whs_ppe=False))
    checklist_checks = [c for c in r.checks if c.label.startswith("All WHS checks confirmed?")]
    assert len(checklist_checks) == 1
    check = checklist_checks[0]
    assert check.state == "CONDITIONAL"
    for item in ("workers notified", "health risks", "PPE", "SWMS", "signage"):
        assert item in check.detail


def test_whs_checklist_proceeds_only_when_all_five_confirmed():
    r = assess_whs(VALID)
    check = next(c for c in r.checks if c.label.startswith("All WHS checks confirmed?"))
    assert check.state == "PROCEED"


def test_never_rejects_even_in_worst_case():
    inp = {
        "application_method": "Sprayed (higher contact)",
        "wind_weather_checked": False,
        "contact_risk": "Workers and public",
    }
    ctx = {"water_quality": {"water_class": "Class D"}}
    r = assess_whs(inp, ctx)
    assert r.state != "REJECT"
    assert r.state == "CONDITIONAL"
