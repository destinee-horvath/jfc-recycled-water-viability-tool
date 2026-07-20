"""
tests/test_water_quality.py
=====================
PHASE 3 — Water Quality: REJECT / CONDITIONAL / PROCEED for each of the 3
application buckets (Concrete Mixing, Dust Suppression, Earthworks).
"""

from backend.phases.p3_water_quality import assess_water_quality


# ---- Concrete Mixing -------------------------------------------------------
CONCRETE_VALID = {
    "application_type": "Concrete Mixing",
    "compression_strength_pct": 95,
    "conc_sugar": 50,
    "conc_oil": 20,
    "conc_ph": 6,
    "conc_ecoli": 50,
    "filtered_turbidity_ntu": 2,
}


def test_concrete_proceed():
    r = assess_water_quality(CONCRETE_VALID)
    assert r.state == "PROCEED"


def test_concrete_reject_on_low_strength():
    inp = dict(CONCRETE_VALID, compression_strength_pct=80)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"


def test_concrete_reject_on_impurity_over_limit():
    inp = dict(CONCRETE_VALID, conc_sugar=500)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"


def test_concrete_conditional_when_untested():
    r = assess_water_quality({"application_type": "Concrete Mixing"})
    assert r.state == "CONDITIONAL"


def test_concrete_shows_all_checks_even_after_low_strength_reject():
    """A REJECT on Table 2.1 (strength) must not hide the Table 2.2
    impurities, turbidity, or Table 2.3 checks — the engineer needs the
    full picture in one pass, not just the first failure."""
    inp = dict(CONCRETE_VALID, compression_strength_pct=80,
               conc_tds=500, conc_chloride=50)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"
    labels = {c.label for c in r.checks}
    assert "Sugar" in labels
    assert "Oil and grease" in labels
    assert "pH" in labels
    assert "Filtered water turbidity" in labels
    assert "Total dissolved solids (reportable)" in labels


def test_concrete_shows_all_checks_even_after_impurity_reject():
    """A REJECT on Table 2.2 (e.g. sugar) must not hide turbidity or the
    Table 2.3 reportable checks."""
    inp = dict(CONCRETE_VALID, conc_sugar=500, conc_tds=500)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"
    labels = {c.label for c in r.checks}
    assert "Filtered water turbidity" in labels
    assert "Total dissolved solids (reportable)" in labels
    sugar_check = next(c for c in r.checks if c.label == "Sugar")
    assert sugar_check.state == "REJECT"


def test_concrete_reject_on_ecoli_over_limit():
    """E. coli added per client review feedback — same AGWR Table 3.8
    threshold (100 cfu/100mL) as Earthworks."""
    inp = dict(CONCRETE_VALID, conc_ecoli=500)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"
    ecoli_check = next(c for c in r.checks if c.label == "E. coli")
    assert ecoli_check.state == "REJECT"


def test_concrete_conditional_on_ecoli_when_untested():
    r = assess_water_quality(dict(CONCRETE_VALID, conc_ecoli=None))
    ecoli_check = next(c for c in r.checks if c.label == "E. coli")
    assert ecoli_check.state == "CONDITIONAL"


# ---- Dust Suppression -------------------------------------------------------
DUST_VALID = {
    "application_type": "Dust Suppression",
    "pathogen_pct": 0.01,
    "dust_bod_mgl": 10,
    "dust_ss_mgl": 10,
    "dust_ecoli": 0.5,
}


def test_dust_suppression_proceed():
    r = assess_water_quality(DUST_VALID)
    assert r.state == "PROCEED"


def test_dust_suppression_reject_on_pathogen_limit():
    inp = dict(DUST_VALID, pathogen_pct=0.5)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"


def test_dust_suppression_conditional_when_untested():
    r = assess_water_quality({"application_type": "Dust Suppression"})
    assert r.state == "CONDITIONAL"


def test_dust_suppression_shows_all_checks_even_after_pathogen_reject():
    """A REJECT on the pathogen screen must not hide the Table 3.8 checks."""
    inp = dict(DUST_VALID, pathogen_pct=0.5)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"
    labels = {c.label for c in r.checks}
    assert "BOD" in labels
    assert "Suspended Solids (SS)" in labels
    assert "E. coli" in labels


# ---- Earthworks (Compaction) ------------------------------------------------
EARTHWORKS_VALID = {
    "application_type": "Earthworks (Compaction)",
    "ew_sugar": 50, "ew_oil": 20, "ew_ph": 6, "ew_tds": 1000,
    "ew_chloride": 100, "ew_sulphate": 100, "ew_alkali": 500, "ew_tss": 5000,
    "ew_bod_mgl": 10, "ew_ss_mgl": 10, "ew_ecoli": 50,
}


def test_earthworks_proceed():
    r = assess_water_quality(EARTHWORKS_VALID)
    assert r.state == "PROCEED"


def test_earthworks_reject_on_tss_over_limit():
    inp = dict(EARTHWORKS_VALID, ew_tss=99999)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"


def test_earthworks_conditional_when_untested():
    r = assess_water_quality({"application_type": "Earthworks (Compaction)"})
    assert r.state == "CONDITIONAL"


def test_earthworks_reject_on_bod_over_limit():
    """Microbiological limits added per client review feedback (AGWR Phase 1
    2006 Table 3.8) — previously only applied to Dust Suppression."""
    inp = dict(EARTHWORKS_VALID, ew_bod_mgl=999)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"
    bod_check = next(c for c in r.checks if c.label == "BOD")
    assert bod_check.state == "REJECT"


def test_earthworks_reject_on_ss_over_limit():
    inp = dict(EARTHWORKS_VALID, ew_ss_mgl=999)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"


def test_earthworks_reject_on_ecoli_over_limit():
    inp = dict(EARTHWORKS_VALID, ew_ecoli=999)
    r = assess_water_quality(inp)
    assert r.state == "REJECT"


def test_earthworks_micro_checks_present_and_shown_alongside_table_3_1():
    r = assess_water_quality(EARTHWORKS_VALID)
    labels = {c.label for c in r.checks}
    assert {"BOD", "Suspended Solids (SS)", "E. coli"} <= labels
    assert "Sugar" in labels   # Table 3-1 checks still present too
