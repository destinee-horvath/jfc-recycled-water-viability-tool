"""
tests/test_site_runoff.py
=====================
PHASE 4 — Site Runoff & EPL Risk: CONDITIONAL / PROCEED coverage.
No REJECT case — this phase never hard-rejects (every shortfall is
CONDITIONAL), which is itself asserted below as a design invariant.
"""

from backend.phases.p4_site_runoff import assess_site_runoff

VALID = {
    "involves_extraction_or_processing": False,
    "distance_to_waterway_m": 200,
    "slope_toward_waterway": False,
    "sensitive_environment": "None / not sensitive",
    "ponding_overflow_risk": False,
    "containment_documented": False,
}


def test_proceed_when_maintenance_and_no_risks():
    r = assess_site_runoff(VALID)
    assert r.state == "PROCEED"


def test_conditional_when_epl_required_but_missing():
    inp = dict(VALID, involves_extraction_or_processing=True,
               project_tonnes=60000, in_regulated_area=True)
    r = assess_site_runoff(inp)
    assert r.state == "CONDITIONAL"


def test_conditional_when_near_waterway():
    inp = dict(VALID, distance_to_waterway_m=10)
    r = assess_site_runoff(inp)
    assert r.state == "CONDITIONAL"


def test_conditional_when_containment_undocumented():
    inp = dict(VALID, ponding_overflow_risk=True, containment_documented=False)
    r = assess_site_runoff(inp)
    assert r.state == "CONDITIONAL"


def test_proceed_when_ponding_risk_and_containment_documented():
    inp = dict(VALID, ponding_overflow_risk=True, containment_documented=True)
    r = assess_site_runoff(inp)
    assert r.state == "PROCEED"


def test_proceed_when_no_ponding_risk_regardless_of_containment():
    """Containment is never even asked about — FR4.7's skip-the-second-
    question behaviour."""
    inp = dict(VALID, ponding_overflow_risk=False, containment_documented=False)
    r = assess_site_runoff(inp)
    assert r.state == "PROCEED"


def test_never_rejects_even_in_worst_case():
    inp = dict(
        involves_extraction_or_processing=True, project_tonnes=999999,
        in_regulated_area=True, epl_in_place=True, epl_covers_recycled=False,
        pirmp_in_place=False, distance_to_waterway_m=1,
        slope_toward_waterway=True, sensitive_environment="Marine park",
        ponding_overflow_risk=True, containment_documented=False,
    )
    r = assess_site_runoff(inp)
    assert r.state != "REJECT"
    assert r.state == "CONDITIONAL"


def test_proceed_when_not_extraction_or_processing_regardless_of_tonnes():
    """Cl 35 applies to extraction/on-site processing only — not concrete
    batching, general earthworks, or road-base compaction, regardless of
    tonnage."""
    inp = dict(VALID, involves_extraction_or_processing=False, project_tonnes=999999)
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Does the project involve extraction, or "
                 "on-site processing (crushing, grinding, or separating), "
                 "of materials for road construction?")
    assert check.state == "PROCEED"


def test_conditional_when_completely_untouched():
    """No silent PROCEED for an untouched phase — waterway-distance and
    slope/drainage fields default to their own CONDITIONAL."""
    r = assess_site_runoff({})
    assert r.state == "CONDITIONAL"


def test_conditional_when_waterway_distance_not_measured():
    inp = dict(VALID)
    del inp["distance_to_waterway_m"]
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Within 100 m of waterway / drainage / stormwater outlet")
    assert check.state == "CONDITIONAL"


def test_proceed_when_waterway_distance_confirmed_outside_buffer():
    r = assess_site_runoff(VALID)
    check = next(c for c in r.checks
                 if c.label == "Within 100 m of waterway / drainage / stormwater outlet")
    assert check.state == "PROCEED"


def test_conditional_when_slope_unconfirmed():
    inp = dict(VALID)
    del inp["slope_toward_waterway"]
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Site slope / drainage directs runoff toward waters")
    assert check.state == "CONDITIONAL"
    assert "not yet confirmed" in check.detail.lower()


def test_conditional_when_slope_explicitly_unconfirmed_string():
    inp = dict(VALID, slope_toward_waterway="Unconfirmed")
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Site slope / drainage directs runoff toward waters")
    assert check.state == "CONDITIONAL"


def test_conditional_when_slope_confirmed_yes():
    inp = dict(VALID, slope_toward_waterway="Yes")
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Site slope / drainage directs runoff toward waters")
    assert check.state == "CONDITIONAL"


def test_proceed_when_slope_confirmed_no():
    inp = dict(VALID, slope_toward_waterway="No")
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Site slope / drainage directs runoff toward waters")
    assert check.state == "PROCEED"


def test_slope_accepts_legacy_boolean_values():
    """CSVs saved before this field became a tri-state stored plain
    True/False — must still be interpreted correctly."""
    inp = dict(VALID, slope_toward_waterway=True)
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Site slope / drainage directs runoff toward waters")
    assert check.state == "CONDITIONAL"

    inp = dict(VALID, slope_toward_waterway=False)
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Site slope / drainage directs runoff toward waters")
    assert check.state == "PROCEED"


def test_proceed_when_sensitive_environment_left_at_default():
    r = assess_site_runoff(VALID)
    check = next(c for c in r.checks if c.label == "Sensitive receiving environment")
    assert check.state == "PROCEED"


def test_schedule_1_check_runs_before_epl_check():
    inp = dict(VALID, involves_extraction_or_processing=True,
               project_tonnes=999999, in_regulated_area=True)
    r = assess_site_runoff(inp)
    labels = [c.label for c in r.checks]
    sch1_idx = labels.index("Does the project involve extraction, or "
                            "on-site processing (crushing, grinding, or "
                            "separating), of materials for road construction?")
    epl_idx = next(i for i, l in enumerate(labels) if "EPL" in l)
    assert sch1_idx < epl_idx
