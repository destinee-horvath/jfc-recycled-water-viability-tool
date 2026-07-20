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
    "containment_documented": True,
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
    inp = dict(VALID, containment_documented=False)
    r = assess_site_runoff(inp)
    assert r.state == "CONDITIONAL"


def test_never_rejects_even_in_worst_case():
    inp = dict(
        involves_extraction_or_processing=True, project_tonnes=999999,
        in_regulated_area=True, epl_in_place=True, epl_covers_recycled=False,
        pirmp_in_place=False, distance_to_waterway_m=1,
        slope_toward_waterway=True, sensitive_environment="Marine park",
        containment_documented=False,
    )
    r = assess_site_runoff(inp)
    assert r.state != "REJECT"
    assert r.state == "CONDITIONAL"


def test_proceed_when_not_extraction_or_processing_regardless_of_tonnes():
    """Cl 35 applies to extraction/on-site processing of materials only —
    NOT onsite concrete batching, general earthworks, compacting road base,
    or maintenance, regardless of tonnage moved."""
    inp = dict(VALID, involves_extraction_or_processing=False, project_tonnes=999999)
    r = assess_site_runoff(inp)
    check = next(c for c in r.checks
                 if c.label == "Does the project involve extraction, or "
                 "on-site processing (crushing, grinding, or separating), "
                 "of materials for road construction?")
    assert check.state == "PROCEED"


def test_schedule_1_check_runs_before_epl_check():
    """Confirms Schedule 1 runs before EPL — this pins that ordering."""
    inp = dict(VALID, involves_extraction_or_processing=True,
               project_tonnes=999999, in_regulated_area=True)
    r = assess_site_runoff(inp)
    labels = [c.label for c in r.checks]
    sch1_idx = labels.index("Does the project involve extraction, or "
                            "on-site processing (crushing, grinding, or "
                            "separating), of materials for road construction?")
    epl_idx = next(i for i, l in enumerate(labels) if "EPL" in l)
    assert sch1_idx < epl_idx
