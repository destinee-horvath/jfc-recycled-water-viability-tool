"""
tests/test_orchestration.py
=============================
End-to-end: run_assessment() + readiness_summary() across all 7 phases. This
is a checklist tool, not a sequential gate — every phase is always assessed
and always editable, regardless of any other phase's outcome; a REJECT
anywhere only adds to the blocking list, never blocks downstream phases.

No single pass/fail verdict or score by design — just the
blocking/pending/confirmed breakdown. The WHS buffer-zone check is always
CONDITIONAL (see backend/phases/p6_whs.py), so WHS itself — and therefore
every assessment as a whole — can never resolve to "everything PROCEEDs";
there's always at least one pending item.
"""

import backend as B

FULLY_VIABLE_INPUTS = {
    "supplier_approval": {
        "water_source": "Treated effluent",
        "supplier_authority": "Council-run scheme",
        "council_approval_held": "Yes",
        "user_approval_state": "Permitted for this use",
    },
    "water_quality": {
        "application_type": "Earthworks (Compaction)",
        "ew_sugar": 50, "ew_oil": 20, "ew_ph": 6, "ew_tds": 1000,
        "ew_chloride": 100, "ew_sulphate": 100, "ew_alkali": 500, "ew_tss": 5000,
        "ew_bod_mgl": 10, "ew_ss_mgl": 10, "ew_ecoli": 50,
        "water_class": "Class A",
    },
    "rwmp": {
        "has_approved_rwmp": True,
        "lists_roadworks_enduse": True,
        "rwmp_12_elements_confirmed": True,
        "rwmp_current": True,
    },
    "site_runoff": {
        "involves_extraction_or_processing": False,
        "distance_to_waterway_m": 200,
        "sensitive_environment": "None / not sensitive",
        "containment_documented": True,
    },
    "soil_conditions": {
        "soil_water_sar": 13, "soil_water_ec_dsm": 3.5,
    },
    "whs": {
        "application_method": "Direct application (low contact)",
        "contact_risk": "None expected",
        "whs_notified_class": True, "whs_health_risks": True,
        "whs_ppe": True, "whs_swms": True, "whs_signage": True,
    },
    # Deliberately cost-favourable (Custom mode, recycled cheaper on both
    # water rate and transport distance) so this phase PROCEEDs — the
    # config.FINANCIAL_DEFAULTS fallback is CONDITIONAL (see
    # tests/test_financial.py), which would make it impossible for "every
    # phase proceeds except buffer zone" to hold below.
    "financial": {
        "water_cost_mode": "Custom", "potable_cost_normal": 20.0,
        "potable_cost_drought": 30.0, "recycled_cost_normal": 1.0,
        "recycled_distance_km": 5,
    },
}


def _deep_copy_inputs():
    return {pid: dict(vals) for pid, vals in FULLY_VIABLE_INPUTS.items()}


def test_confirmed_and_no_blocking_when_every_phase_proceeds_except_buffer_zone():
    results = B.run_assessment(_deep_copy_inputs())
    readiness = B.readiness_summary(results)
    assert readiness["blocking"] == []
    assert readiness["pending"] == [c for c in results["whs"].checks
                                     if c.label == "Buffer zone — needs assessment"]
    assert len(readiness["confirmed"]) > 0


def test_pending_grows_when_one_phase_has_a_shortfall():
    inputs = _deep_copy_inputs()
    inputs["rwmp"]["has_approved_rwmp"] = False   # CONDITIONAL, no REJECT anywhere
    results = B.run_assessment(inputs)
    readiness = B.readiness_summary(results)
    assert readiness["blocking"] == []
    assert any(c.label == "Supplier holds an approved RWMP for this scheme"
               for c in readiness["pending"])


def test_blocking_populated_when_supplier_approval_rejects_but_downstream_phases_still_assessed():
    inputs = _deep_copy_inputs()
    inputs["supplier_approval"]["operated_without_approval"] = True
    results = B.run_assessment(inputs)
    readiness = B.readiness_summary(results)
    assert len(readiness["blocking"]) == 1
    assert results["supplier_approval"].state == "REJECT"
    # Downstream phases are not blocked — each is still assessed from its
    # own inputs, independently of Phase 1's outcome.
    assert results["water_quality"].state == "PROCEED"


def test_no_phase_ever_locks_downstream_phases():
    """The tool is a checklist, not a sequential gate — PhaseResult no
    longer has a locking concept at all, and every phase remains
    independently assessed regardless of any other phase's REJECT."""
    inputs = _deep_copy_inputs()
    inputs["supplier_approval"]["operated_without_approval"] = True
    results = B.run_assessment(inputs)
    assert not hasattr(results["financial"], "locked")

    inputs = _deep_copy_inputs()
    inputs["rwmp"]["has_approved_rwmp"] = False
    results = B.run_assessment(inputs)
    assert results["rwmp"].state == "CONDITIONAL"   # Phase 2 never returns REJECT
    assert results["financial"].state == "PROCEED"
