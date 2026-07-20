"""
tests/test_supplier_approval.py
=====================
PHASE 1 — Supplier & Dual Approval: REJECT / CONDITIONAL / PROCEED coverage.

Hard gates (REJECT): historic operation without approval, council/authority
"No", and the discharge-point trap — none of these is obtainable after the
fact, so none is remediable by "confirm it later". Private scheme (s.68
greywater/blackwater) was removed per client review — not a credible pathway
for recycled water at roadworks scale; only council-run and water-authority
supplier types remain, plus stormwater's own pathway. Dual approval "Not
permitted" is CONDITIONAL, not REJECT: the user
can vary their EPL or obtain development consent before works commence, so
it's remediable, unlike the supplier-side pre-existing ministerial approvals.
Stormwater's own approval pathway (s.68/development consent/WMA 2000) is
likewise always CONDITIONAL when not held, never REJECT, for the same
obtainable-later reason.
"""

import config as C
from backend.phases.p1_supplier_approval import assess_supplier_approval

VALID = {
    "water_source": "Treated effluent",
    "supplier_authority": "Council-run scheme",
    "council_approval_held": "Yes",
    "user_approval_state": "Permitted for this use",
}


def test_proceed_when_all_approvals_held():
    r = assess_supplier_approval(VALID)
    assert r.state == "PROCEED"


def test_reject_when_operated_without_approval():
    inp = dict(VALID, operated_without_approval=True)
    r = assess_supplier_approval(inp)
    assert r.state == "REJECT"


def test_historic_reject_overrides_and_stops_all_other_checks():
    """Even with council approval also missing, the historic check
    short-circuits — only one check should ever be recorded."""
    inp = dict(VALID, operated_without_approval=True,
               council_approval_held="No", user_approval_state="Not permitted for this use")
    r = assess_supplier_approval(inp)
    assert r.state == "REJECT"
    assert len(r.checks) == 1


def test_reject_when_council_has_no_approval():
    inp = dict(VALID, council_approval_held="No")
    r = assess_supplier_approval(inp)
    assert r.state == "REJECT"


def test_conditional_when_council_approval_unconfirmed():
    inp = dict(VALID, council_approval_held="Unconfirmed")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_conditional_when_user_not_permitted():
    """Not permitted is CONDITIONAL, not REJECT — the user can vary their EPL
    or obtain development consent before works commence."""
    inp = dict(VALID, user_approval_state="Not permitted for this use")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_conditional_when_user_approval_unconfirmed():
    inp = dict(VALID, user_approval_state="Unconfirmed")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_conditional_by_default_when_user_approval_not_specified():
    """"Unconfirmed" is the default (last item in USER_APPROVAL_STATES) so the
    engineer isn't forced into a binary choice before checking their documents."""
    inp = {k: v for k, v in VALID.items() if k != "user_approval_state"}
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_reject_on_discharge_only_trap_for_treated_effluent():
    inp = dict(VALID, discharge_only=True)
    r = assess_supplier_approval(inp)
    assert r.state == "REJECT"


def test_reject_on_discharge_only_trap_for_other_source():
    """Unlike the old design, the discharge trap now also applies to 'Other'
    sources, not just Treated effluent."""
    inp = dict(VALID, water_source="Other", discharge_only=True)
    r = assess_supplier_approval(inp)
    assert r.state == "REJECT"


# ---------------------------------------------------------------------------
# Stormwater pathway
# ---------------------------------------------------------------------------
def test_conditional_for_stormwater_without_alternative_approval():
    """Stormwater's own approval pathway is CONDITIONAL, not REJECT, when
    not held — s.68/development consent/WMA 2000 approvals are obtainable."""
    inp = dict(VALID, water_source="Stormwater", stormwater_approvals_held="No")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_conditional_for_stormwater_when_unconfirmed():
    inp = dict(VALID, water_source="Stormwater", stormwater_approvals_held="Unconfirmed")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_proceed_for_stormwater_with_alternative_approval():
    inp = dict(VALID, water_source="Stormwater", stormwater_approvals_held="Yes")
    r = assess_supplier_approval(inp)
    assert r.state == "PROCEED"


def test_proceed_for_stormwater_in_sydney_hunter_area_regardless_of_approvals():
    """In Sydney/Hunter Water operational areas, s.68 LGA doesn't apply at
    all — the Sydney/Hunter check short-circuits the stormwater approvals
    check entirely."""
    inp = dict(VALID, water_source="Stormwater", sydney_hunter_area=True,
               stormwater_approvals_held="No")
    r = assess_supplier_approval(inp)
    assert r.state == "PROCEED"


def test_discharge_trap_is_na_for_stormwater():
    inp = dict(VALID, water_source="Stormwater", stormwater_approvals_held="Yes")
    r = assess_supplier_approval(inp)
    discharge_check = next(c for c in r.checks if "discharge" in c.label.lower())
    assert discharge_check.state == "NA"


def test_stormwater_never_evaluates_supplier_checks():
    """Check 3c must skip checks 4/5a/5b entirely for stormwater."""
    inp = dict(VALID, water_source="Stormwater", stormwater_approvals_held="Yes",
               supplier_authority="Council-run scheme",
               council_approval_held="No")
    r = assess_supplier_approval(inp)
    assert r.state == "PROCEED"   # the council-run REJECT must never fire


# ---------------------------------------------------------------------------
# Water supply authority
# ---------------------------------------------------------------------------
def test_proceed_for_water_supply_authority():
    inp = dict(VALID, supplier_authority="Water supply authority", authority_approval_held="Yes")
    r = assess_supplier_approval(inp)
    assert r.state == "PROCEED"


def test_reject_when_water_supply_authority_has_no_approval():
    inp = dict(VALID, supplier_authority="Water supply authority", authority_approval_held="No")
    r = assess_supplier_approval(inp)
    assert r.state == "REJECT"


def test_conditional_when_water_supply_authority_approval_unconfirmed():
    inp = dict(VALID, supplier_authority="Water supply authority",
               authority_approval_held="Unconfirmed")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"


def test_private_scheme_removed_from_supplier_authorities():
    """Client review: s.68 private-scheme approvals are for small-scale
    septic systems, not a credible pathway for recycled water at roadworks
    scale. Only council-run and water-authority schemes remain."""
    assert C.SUPPLIER_AUTHORITIES == ["Council-run scheme", "Water supply authority"]
    assert "Private scheme (greywater/blackwater)" not in C.SUPPLIER_APPROVAL_REFS


# ---------------------------------------------------------------------------
# Discharge trap / "Other" source / EPL section independence
# ---------------------------------------------------------------------------
def test_proceed_when_treated_effluent_discharge_trap_not_triggered():
    inp = dict(VALID, water_source="Treated effluent", discharge_only=False)
    r = assess_supplier_approval(inp)
    assert r.state == "PROCEED"


def test_other_water_source_uses_the_standard_supplier_path():
    """'Other' is not a special CONDITIONAL case — it runs the same
    supplier-approval path as Treated effluent."""
    inp = dict(VALID, water_source="Other")
    r = assess_supplier_approval(inp)
    assert r.state == "PROCEED"


def test_epl_section_fields_do_not_affect_gate_state():
    """The informational EPL section (epl_status / epl_number /
    epl_conditions_permit_supply) is saved to session state and the CSV
    export, but assess_supplier_approval() never reads it, by design."""
    base_result = assess_supplier_approval(VALID).state
    scenarios = [
        dict(VALID, epl_status="Yes", epl_conditions_permit_supply=True),
        dict(VALID, epl_status="Yes", epl_conditions_permit_supply=False),
        dict(VALID, epl_status="No"),
        dict(VALID, epl_status="Unconfirmed"),
        dict(VALID, epl_status="Yes", epl_number="EPL-12345", epl_conditions_permit_supply=True),
    ]
    for inp in scenarios:
        assert assess_supplier_approval(inp).state == base_result, inp


# ---------------------------------------------------------------------------
# Rollup / severity ordering
# ---------------------------------------------------------------------------
def test_rollup_worst_state_wins_na_lowest():
    """NA < PROCEED < CONDITIONAL < REJECT — a NA discharge-trap check for
    stormwater must never outrank a CONDITIONAL/REJECT from other checks."""
    inp = dict(VALID, water_source="Stormwater", stormwater_approvals_held="No")
    r = assess_supplier_approval(inp)
    assert r.state == "CONDITIONAL"   # not NA, even though a NA check exists
