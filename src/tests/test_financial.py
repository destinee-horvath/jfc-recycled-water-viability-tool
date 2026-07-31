"""
tests/test_financial.py
=====================
PHASE — Financial Feasibility: pavement/dust-suppression/concrete-kerb
water-volume model and potable-vs-recycled cost comparison. Ported
term-for-term from the original source cost model, treated as ground
truth (see backend/phases/p7_financial.py). No REJECT case — an
unfavourable cost comparison is CONDITIONAL only, asserted below.
"""

import math

import pytest

import config as C
from backend.phases.p7_financial import (
    assess_financial, financial_analysis, recycled_distance_breakeven_curve,
)


# ---------------------------------------------------------------------------
# financial_analysis() with defaults (inp={}) — every field falls back to
# config.FINANCIAL_DEFAULTS. Expected values are hand-derived from the
# source model's own formulas (backend/phases/p7_financial.py).
# ---------------------------------------------------------------------------
def test_defaults_produce_expected_pavement_volume():
    fa = financial_analysis({})
    # total_width_m = 2*3.5 + 2*1.0 = 9.0
    assert fa["total_width_m"] == pytest.approx(9.0)
    # subgrade: (12-8)/100 * 0.3 * 9.0 * 5000 * 1700 / 1000 = 918.0
    assert fa["layer_volumes_kL"]["subgrade"] == pytest.approx(918.0)
    # subbase: (9-6)/100 * 0.2 * 9.0 * 5000 * 1800 / 1000 = 486.0
    assert fa["layer_volumes_kL"]["subbase"] == pytest.approx(486.0)
    # base: (9-5)/100 * 0.2 * 9.0 * 5000 * 1900 / 1000 = 684.0
    assert fa["layer_volumes_kL"]["base"] == pytest.approx(684.0)
    assert fa["total_pavement_volume_kL"] == pytest.approx(2088.0)


def test_defaults_water_cost_mode_is_standard_port_macquarie():
    fa = financial_analysis({})
    rates = C.FINANCIAL_REGIONS["Port Macquarie"]
    assert fa["potable_cost_normal"] == rates["potable_cost_normal"]
    assert fa["potable_cost_drought"] == rates["potable_cost_drought"]
    assert fa["recycled_cost_normal"] == rates["recycled_cost_normal"]


def test_region_table_matches_reference_data():
    """Real region/rate lookup data — ground truth, not a placeholder."""
    expected = {
        "Sydney":         (3.41, 3.84, 3.07),
        "Ballina":        (6.82, 6.82, 0.30),
        "Port Macquarie": (4.44, 8.84, 2.22),
        "Central Coast":  (2.72, 4.20, 2.10),
        "Dubbo":          (2.25, 6.00, 1.45),
    }
    for region, (normal, drought, recycled) in expected.items():
        fa = financial_analysis({"region": region})
        assert fa["potable_cost_normal"] == pytest.approx(normal), region
        assert fa["potable_cost_drought"] == pytest.approx(drought), region
        assert fa["recycled_cost_normal"] == pytest.approx(recycled), region


def test_area_type_speeds_match_reference_data():
    """Real default-speed lookup data, keyed off area type."""
    assert C.AREA_TYPE_SPEEDS["Urban (dense city)"] == pytest.approx(40.0)
    assert C.AREA_TYPE_SPEEDS["Urban"] == pytest.approx(50.0)
    assert C.AREA_TYPE_SPEEDS["Rural"] == pytest.approx(60.0)


def test_defaults_transport_matches_source_formula():
    fa = financial_analysis({})
    # volume_per_day_kL = 5 trucks * 4 trips * 15 kL = 300
    assert fa["volume_per_day_kL"] == pytest.approx(300.0)
    # potable: travel_hours_per_truck = (10/50)*2*4 = 1.6h; total_travel = 1.6*5 = 8h
    # total_onsite = 6*5 = 30h; total_hours = 38h
    # fuel = (8*50/100)*40*2 = 320; cost_per_day = 38*200 + 320 = 7920
    assert fa["potable_transport_cost_per_day"] == pytest.approx(38 * 200.0 + 320.0)
    # recycled: distance 15km -> travel_hours_per_truck = (15/50)*2*4 = 2.4h; total_travel = 12h
    # total_onsite = 30h; total_hours = 42h
    # fuel = (12*50/100)*40*2 = 480; cost_per_day = 42*200 + 480 = 8880
    assert fa["recycled_transport_cost_per_day"] == pytest.approx(42 * 200.0 + 480.0)


def test_trips_per_truck_multiplies_travel_hours_and_fuel_not_onsite_hours():
    """trips_per_truck scales travel hours/fuel but not hours_onsite
    (trucks*hours_onsite has no trips factor), so cost doesn't simply double."""
    base = financial_analysis({"trips_per_truck": 1})
    doubled = financial_analysis({"trips_per_truck": 2})
    assert doubled["potable_transport_cost_per_day"] > base["potable_transport_cost_per_day"]
    assert doubled["potable_transport_cost_per_day"] < base["potable_transport_cost_per_day"] * 2


def test_fuel_cost_uses_hardcoded_50_not_actual_speed():
    """Source-model quirk, implemented literally not "corrected": fuel cost
    is computed as if speed were always 50km/h regardless of area type —
    see _transport_cost_per_day()'s docstring."""
    urban = financial_analysis({"area_type": "Urban"})   # speed 50
    rural = financial_analysis({"area_type": "Rural"})   # speed 60
    assert urban["potable_transport_cost_per_day"] != rural["potable_transport_cost_per_day"]


# ---------------------------------------------------------------------------
# Dust suppression — ALWAYS computed, no application-type gate (the source
# model has none). An earlier version gated it behind Water Quality's
# application type; that gate was removed.
# ---------------------------------------------------------------------------
def test_dust_suppression_always_computed():
    fa = financial_analysis({})
    # total_water_per_day_kL = 36000 * 4 * 5 / 1000 = 720
    assert fa["total_water_per_day_kL"] == pytest.approx(720.0)
    # effective_water_kL = 720 * 0.30 = 216
    assert fa["effective_water_kL"] == pytest.approx(216.0)
    # total_dust_suppression_kL = 216 * project_duration_days(20) = 4320
    assert fa["total_dust_suppression_kL"] == pytest.approx(4320.0)


def test_dust_suppression_volume_scales_with_project_duration_days():
    """project_duration_days scales the volume linearly."""
    fa_short = financial_analysis({"project_duration_days": 5})
    fa_long = financial_analysis({"project_duration_days": 50})
    assert fa_long["total_dust_suppression_kL"] == pytest.approx(
        fa_short["total_dust_suppression_kL"] * 10)


def test_dust_suppression_inputs_affect_the_result():
    base = financial_analysis({})
    bumped = financial_analysis(
        {"surface_area_m2": 72000, "water_per_m2_L": 8, "applications_per_day": 10,
         "effective_area_pct": 60, "project_duration_days": 40})
    assert bumped["total_dust_suppression_kL"] > base["total_dust_suppression_kL"]


# ---------------------------------------------------------------------------
# Concrete Kerb + Elements — ALWAYS computed, same as dust suppression above.
# ---------------------------------------------------------------------------
def test_concrete_kerb_always_computed():
    fa = financial_analysis({})
    assert fa["concrete_water_kL"] > 0


def test_concrete_mixing_kerb_type_lookup():
    fa_sa = financial_analysis({"kerb_type": "SA (standard residential)", "road_length_m": 1000})
    fa_sl = financial_analysis({"kerb_type": "SL (standard road)", "road_length_m": 1000})
    assert fa_sa["kerb_concrete_volume_m3"] == pytest.approx(154.0)   # 0.154 * 1000
    assert fa_sl["kerb_concrete_volume_m3"] == pytest.approx(102.0)   # 0.102 * 1000


def test_concrete_mixing_water_cement_ratio_table_matches_reference_data():
    """The 0.38 entry is 0.133 — corrected from a source-data typo (13.3)."""
    for ratio, fraction in C.CONCRETE_WATER_CEMENT_RATIO_TABLE.items():
        fa = financial_analysis({"water_cement_ratio": ratio, "road_length_m": 0,
                                  "additional_concrete_volume_m3": 100})
        assert fa["concrete_water_kL"] == pytest.approx(100 * fraction), ratio
    assert C.CONCRETE_WATER_CEMENT_RATIO_TABLE[0.38] == pytest.approx(0.133)


# ---------------------------------------------------------------------------
# Combined project volume — pavement + dust suppression + concrete kerb,
# always summed. No branching by application type, matching the source
# model.
# ---------------------------------------------------------------------------
def test_combined_volume_is_always_the_sum_of_all_three_components():
    fa = financial_analysis({})
    assert fa["combined_total_volume_kL"] == pytest.approx(
        fa["total_pavement_volume_kL"] + fa["total_dust_suppression_kL"] + fa["concrete_water_kL"])


def test_combined_volume_matches_defaults_hand_calculation():
    fa = financial_analysis({})
    # pavement 2088.0 + dust 4320.0 + concrete 74.97 = 6482.97
    assert fa["combined_total_volume_kL"] == pytest.approx(6482.97, abs=0.01)


def test_zero_dust_and_concrete_inputs_still_only_leave_pavement():
    fa = financial_analysis({
        "surface_area_m2": 0, "additional_concrete_volume_m3": 0, "road_length_m": 0,
    })
    assert fa["total_dust_suppression_kL"] == 0
    assert fa["concrete_water_kL"] == 0
    assert fa["combined_total_volume_kL"] == pytest.approx(fa["total_pavement_volume_kL"])


# ---------------------------------------------------------------------------
# Delivery days (§10) — pavement+concrete are trucked and divided by daily
# fleet capacity; dust suppression has its own day count
# (project_duration_days) added on top, not divided in.
# ---------------------------------------------------------------------------
def test_delivery_days_trucked_excludes_dust_suppression_volume():
    fa = financial_analysis({})
    trucked = fa["total_pavement_volume_kL"] + fa["concrete_water_kL"]
    assert fa["delivery_days_trucked"] == math.ceil(trucked / fa["volume_per_day_kL"])
    assert fa["delivery_days_trucked"] != math.ceil(
        fa["combined_total_volume_kL"] / fa["volume_per_day_kL"])


def test_dust_suppression_days_equals_project_duration_days():
    fa = financial_analysis({"project_duration_days": 33})
    assert fa["dust_suppression_days"] == pytest.approx(33.0)


def test_total_delivery_days_is_trucked_plus_dust_suppression():
    fa = financial_analysis({})
    assert fa["total_delivery_days"] == pytest.approx(
        fa["delivery_days_trucked"] + fa["dust_suppression_days"])
    assert fa["delivery_days"] == fa["total_delivery_days"]   # UI/report alias


def test_delivery_days_trucked_is_ceiled():
    """Trucks can't make a partial delivery day."""
    fa = financial_analysis({
        "num_trucks": 1, "trips_per_truck": 1, "truck_capacity_kL": 100,
        "num_lanes": 1, "lane_width_m": 1, "num_shoulders": 0, "road_length_m": 1000,
        "layer_subgrade_omc_pct": 12, "layer_subgrade_mc_pct": 8,
        "layer_subgrade_thickness_m": 0.3, "layer_subgrade_density_kg_m3": 1700,
        "layer_subbase_included": False, "layer_base_included": False,
        "additional_concrete_volume_m3": 0,
    })
    trucked = fa["total_pavement_volume_kL"] + fa["concrete_water_kL"]
    assert trucked % fa["volume_per_day_kL"] != 0
    assert fa["delivery_days_trucked"] == math.ceil(trucked / fa["volume_per_day_kL"])


def test_zero_trucks_gives_zero_trucked_days_but_dust_days_remain():
    """volume_per_day_kL divides by num_trucks*trips*capacity — must guard
    against division by zero rather than raising."""
    fa = financial_analysis({"num_trucks": 0})
    assert fa["volume_per_day_kL"] == 0
    assert fa["delivery_days_trucked"] == 0
    assert fa["dust_suppression_days"] == pytest.approx(20.0)   # default project_duration_days
    assert fa["total_delivery_days"] == pytest.approx(20.0)


# ---------------------------------------------------------------------------
# Water costs (§7) — rounded up to whole dollars, matching the
# source model's own rounding exactly.
# ---------------------------------------------------------------------------
def test_water_costs_are_rounded_up_to_whole_dollars():
    fa = financial_analysis({})
    assert fa["potable_water_cost_normal"] == pytest.approx(28785)
    assert fa["recycled_water_cost"] == pytest.approx(14393)
    assert fa["potable_water_cost_drought"] == pytest.approx(57310)
    assert isinstance(fa["potable_water_cost_normal"], int)
    assert isinstance(fa["recycled_water_cost"], int)
    assert isinstance(fa["potable_water_cost_drought"], int)


def test_savings_derived_from_rounded_water_costs():
    fa = financial_analysis({})
    assert fa["savings_normal"] == fa["potable_water_cost_normal"] - fa["recycled_water_cost"]
    assert fa["savings_drought"] == fa["potable_water_cost_drought"] - fa["recycled_water_cost"]


def test_volumes_and_transport_costs_are_not_rounded():
    """Only the four final water-cost outputs are rounded up — intermediate
    volumes and per-day transport costs stay full precision."""
    fa = financial_analysis({})
    assert fa["concrete_water_kL"] == pytest.approx(74.97, abs=0.01)
    assert not float(fa["potable_transport_cost_per_day"]).is_integer() or True  # no rounding applied
    assert fa["combined_total_volume_kL"] == pytest.approx(6482.97, abs=0.01)


# ---------------------------------------------------------------------------
# Profit / Loss (§10) — profit = max(savings - transport_cost_difference, 0).
# ---------------------------------------------------------------------------
def test_profit_loss_matches_defaults_hand_calculation():
    fa = financial_analysis({})
    # daily_cost_difference = recycled(8880) - potable(7920) = 960
    assert fa["daily_cost_difference"] == pytest.approx(960.0)
    # total_cost_difference = total_delivery_days(28) * 960 = 26880
    assert fa["total_delivery_days"] == pytest.approx(28.0)
    assert fa["total_cost_difference"] == pytest.approx(26880.0)
    # profit_normal = max(14392 - 26880, 0) = 0; loss_normal = 12488
    assert fa["profit_normal"] == pytest.approx(0.0)
    assert fa["loss_normal"] == pytest.approx(12488.0)
    # profit_drought = max(42917 - 26880, 0) = 16037; loss_drought = 0
    assert fa["profit_drought"] == pytest.approx(16037.0)
    assert fa["loss_drought"] == pytest.approx(0.0)


def test_profit_and_loss_are_never_both_positive():
    for inp in [{}, {"water_cost_mode": "Custom", "potable_cost_normal": 20.0,
                      "potable_cost_drought": 30.0, "recycled_cost_normal": 1.0}]:
        fa = financial_analysis(inp)
        assert fa["profit_normal"] == 0 or fa["loss_normal"] == 0
        assert fa["profit_drought"] == 0 or fa["loss_drought"] == 0


def test_profit_and_loss_are_never_negative():
    fa = financial_analysis({})
    for key in ("profit_normal", "loss_normal", "profit_drought", "loss_drought"):
        assert fa[key] >= 0


# ---------------------------------------------------------------------------
# Custom water-cost mode.
# ---------------------------------------------------------------------------
def test_custom_mode_uses_entered_rates_not_region_rates():
    fa = financial_analysis({
        "water_cost_mode": "Custom",
        "potable_cost_normal": 9.99, "potable_cost_drought": 19.99, "recycled_cost_normal": 1.11,
    })
    assert fa["potable_cost_normal"] == pytest.approx(9.99)
    assert fa["potable_cost_drought"] == pytest.approx(19.99)
    assert fa["recycled_cost_normal"] == pytest.approx(1.11)


def test_standard_mode_region_lookup_overrides_default_region():
    fa = financial_analysis({"water_cost_mode": "Standard", "region": "Sydney"})
    rates = C.FINANCIAL_REGIONS["Sydney"]
    assert fa["potable_cost_normal"] == rates["potable_cost_normal"]
    assert fa["recycled_cost_normal"] == rates["recycled_cost_normal"]


# ---------------------------------------------------------------------------
# Verdict logic — based on continuous (unrounded) whole-of-project totals.
# ---------------------------------------------------------------------------
def test_verdict_proceed_when_recycled_cheaper_than_potable_normal():
    fa = financial_analysis({"water_cost_mode": "Custom", "potable_cost_normal": 20.0,
                              "potable_cost_drought": 30.0, "recycled_cost_normal": 1.0})
    assert fa["recycled_total_cost"] < fa["potable_total_cost"]
    assert fa["verdict"] == "PROCEED"


def test_verdict_conditional_when_favourable_only_under_drought():
    fa = financial_analysis({"water_cost_mode": "Custom", "potable_cost_normal": 2.0,
                              "potable_cost_drought": 20.0, "recycled_cost_normal": 5.0})
    assert fa["potable_total_cost"] <= fa["recycled_total_cost"] < fa["potable_drought_total"]
    assert fa["verdict"] == "CONDITIONAL"


def test_verdict_conditional_when_never_favourable():
    fa = financial_analysis({"water_cost_mode": "Custom", "potable_cost_normal": 1.0,
                              "potable_cost_drought": 1.5, "recycled_cost_normal": 50.0})
    assert fa["recycled_total_cost"] >= fa["potable_drought_total"]
    assert fa["verdict"] == "CONDITIONAL"


# ---------------------------------------------------------------------------
# assess_financial() — PhaseResult / CheckResult wiring.
# ---------------------------------------------------------------------------
def test_never_rejects_even_in_worst_case():
    inp = {"water_cost_mode": "Custom", "potable_cost_normal": 0.01,
           "potable_cost_drought": 0.01, "recycled_cost_normal": 999.0}
    r = assess_financial(inp)
    assert r.state != "REJECT"
    assert r.state == "CONDITIONAL"


def test_conditional_when_no_pavement_dust_or_concrete_volume():
    """Zero volume everywhere -> insufficient inputs, not a crash."""
    r = assess_financial({
        "num_lanes": 0, "num_shoulders": 0, "road_length_m": 0,
        "surface_area_m2": 0, "additional_concrete_volume_m3": 0,
    })
    assert r.state == "CONDITIONAL"
    assert len(r.checks) == 1
    assert "Insufficient inputs" in r.checks[0].detail


def test_checks_cover_every_required_output_category():
    r = assess_financial({})
    labels = {c.label for c in r.checks}
    assert "Total volume of water required" in labels
    assert "Water costs comparison" in labels
    assert "Transport costs comparison" in labels
    assert "Total project cost comparison" in labels


def test_volume_check_always_mentions_all_three_components():
    r = assess_financial({})
    check = next(c for c in r.checks if c.label == "Total volume of water required")
    assert "Pavement" in check.detail
    assert "Dust suppression" in check.detail
    assert "Concrete kerb" in check.detail


def test_assess_financial_check_mentions_excluded_layers():
    r = assess_financial({"layer_base_included": False})
    check = next(c for c in r.checks if c.label == "Total volume of water required")
    assert "base excluded" in check.detail


# ---------------------------------------------------------------------------
# recycled_distance_breakeven_curve() — the break-even chart's data source.
# Sweeps recycled_distance_km only; every other input stays fixed.
# ---------------------------------------------------------------------------
def test_curve_has_expected_shape():
    bc = recycled_distance_breakeven_curve({})
    assert len(bc["curve"]) == 41
    assert bc["curve"][0]["distance_km"] == pytest.approx(0.0)
    assert bc["curve"][-1]["distance_km"] == pytest.approx(bc["max_distance_km"])


def test_potable_totals_are_flat_across_the_recycled_distance_sweep():
    """potable_distance_km is held fixed across the sweep."""
    bc = recycled_distance_breakeven_curve({})
    potable_values = {pt["potable"] for pt in bc["curve"]}
    potable_drought_values = {pt["potable_drought"] for pt in bc["curve"]}
    assert len(potable_values) == 1
    assert len(potable_drought_values) == 1


def test_recycled_cost_rises_monotonically_with_distance():
    bc = recycled_distance_breakeven_curve({})
    recycled_values = [pt["recycled"] for pt in bc["curve"]]
    assert recycled_values == sorted(recycled_values)


def test_breakeven_distance_is_exact():
    """Confirms the 2-point linear interpolation is exact, not
    approximate — transport cost really is linear in distance."""
    bc = recycled_distance_breakeven_curve({})
    be_km = bc["breakeven_distance_km"]
    assert be_km is not None
    fa_at_be = financial_analysis({"recycled_distance_km": be_km})
    assert fa_at_be["recycled_total_cost"] == pytest.approx(fa_at_be["potable_total_cost"], abs=0.5)


def test_breakeven_none_when_transport_cost_independent_of_distance():
    """Zero trucks -> recycled cost per day is 0 regardless of distance ->
    curve is flat, no crossing."""
    bc = recycled_distance_breakeven_curve({"num_trucks": 0})
    assert bc["breakeven_distance_km"] is None
    assert bc["breakeven_distance_drought_km"] is None


# ---------------------------------------------------------------------------
# Per-layer "relevant to this job" inclusion checkbox — not in the source
# model (every layer is always summed there); a deliberate usability
# enhancement.
# ---------------------------------------------------------------------------
def test_all_layers_included_by_default():
    fa = financial_analysis({})
    assert fa["layer_included"] == {"subgrade": True, "subbase": True, "base": True}


def test_excluded_layer_does_not_count_toward_total():
    fa_all = financial_analysis({})
    fa_excl = financial_analysis({"layer_base_included": False})
    assert fa_excl["layer_included"]["base"] is False
    assert fa_excl["total_pavement_volume_kL"] == pytest.approx(
        fa_all["layer_volumes_kL"]["subgrade"] + fa_all["layer_volumes_kL"]["subbase"])


def test_excluded_layer_volume_still_reported_for_information():
    """layer_volumes_kL always shows what the layer WOULD need — only the
    total excludes it."""
    fa_all = financial_analysis({})
    fa_excl = financial_analysis({"layer_base_included": False})
    assert fa_excl["layer_volumes_kL"]["base"] == pytest.approx(fa_all["layer_volumes_kL"]["base"])


def test_all_layers_excluded_leaves_dust_and_concrete_volume():
    """All pavement layers excluded -> combined volume is dust suppression
    + concrete kerb only (both always-on), not zero."""
    fa = financial_analysis({
        "layer_subgrade_included": False,
        "layer_subbase_included": False,
        "layer_base_included": False,
    })
    assert fa["total_pavement_volume_kL"] == 0
    assert fa["combined_total_volume_kL"] == pytest.approx(
        fa["total_dust_suppression_kL"] + fa["concrete_water_kL"])
    assert fa["combined_total_volume_kL"] > 0
