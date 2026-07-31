"""
tests/test_soil_conditions.py
=====================
PHASE 5 — Soil & Site Conditions.

Two independent checks: USCS soil classification (information-entry only,
always PROCEEDs) and the SAR/EC structural-stability screen (CONDITIONAL/
PROCEED only, never REJECT — see backend/phases/p5_soil_conditions.py and
config.py's "PHASE 5 — SAR/EC soil structural stability" section). The
stability boundary is the line SAR = SOIL_STABILITY_SLOPE*EC +
SOIL_STABILITY_INTERCEPT — a sample is stable if its SAR is on/below this
line at its EC.
"""

from backend.phases.p5_soil_conditions import assess_soil_conditions


def test_soil_classification_check_always_present_and_proceeds():
    r = assess_soil_conditions({})
    classification = next(c for c in r.checks if c.label == "Soil & site classification")
    assert classification.state == "PROCEED"


def test_conditional_when_sar_ec_untested():
    r = assess_soil_conditions({})
    assert r.state == "CONDITIONAL"
    stability = next(c for c in r.checks if c.label == "SAR/EC soil structural stability")
    assert stability.state == "CONDITIONAL"


def test_no_ussl_or_rainfall_check_when_sar_ec_untested():
    """EC-dependent informational checks shouldn't appear with no result
    to classify."""
    r = assess_soil_conditions({})
    labels = {c.label for c in r.checks}
    assert "USSL salinity classification (informational)" not in labels


def test_proceed_when_sar_on_or_below_the_boundary_line():
    # threshold SAR at EC=3.5 is 4.3*3.5 - 0.4 = 14.65
    inp = {"soil_water_sar": 13, "soil_water_ec_dsm": 3.5}
    r = assess_soil_conditions(inp)
    stability = next(c for c in r.checks if c.label == "SAR/EC soil structural stability")
    assert stability.state == "PROCEED"


def test_proceed_at_exact_boundary():
    # threshold SAR at EC=1.0 is 4.3*1.0 - 0.4 = 3.9 exactly
    inp = {"soil_water_sar": 3.9, "soil_water_ec_dsm": 1.0}
    r = assess_soil_conditions(inp)
    stability = next(c for c in r.checks if c.label == "SAR/EC soil structural stability")
    assert stability.state == "PROCEED"


def test_conditional_when_sar_exceeds_the_boundary_line():
    # threshold SAR at EC=1.0 is 3.9 — SAR=13 is well above it
    inp = {"soil_water_sar": 13, "soil_water_ec_dsm": 1.0}
    r = assess_soil_conditions(inp)
    stability = next(c for c in r.checks if c.label == "SAR/EC soil structural stability")
    assert stability.state == "CONDITIONAL"
    assert "likely" in stability.detail


def test_never_rejects_even_in_the_worst_case():
    inp = {"soil_water_sar": 30, "soil_water_ec_dsm": 0.1}
    r = assess_soil_conditions(inp)
    assert r.state != "REJECT"
    assert all(c.state != "REJECT" for c in r.checks)


def test_ussl_classification_shown_alongside_stability_result():
    inp = {"soil_water_sar": 13, "soil_water_ec_dsm": 3.5}
    r = assess_soil_conditions(inp)
    ussl = next(c for c in r.checks if c.label == "USSL salinity classification (informational)")
    assert ussl.state == "PROCEED"
    assert "C4" in ussl.detail


def test_low_rainfall_region_adds_caution_check():
    inp = {"soil_water_sar": 13, "soil_water_ec_dsm": 3.5}
    ctx = {"financial": {"region": "Dubbo"}}
    r = assess_soil_conditions(inp, ctx)
    labels = {c.label for c in r.checks}
    assert "Rainfall context vs. stability-chart assumption" in labels


def test_no_rainfall_caution_for_higher_rainfall_region():
    inp = {"soil_water_sar": 13, "soil_water_ec_dsm": 3.5}
    ctx = {"financial": {"region": "Port Macquarie"}}
    r = assess_soil_conditions(inp, ctx)
    labels = {c.label for c in r.checks}
    assert "Rainfall context vs. stability-chart assumption" not in labels
