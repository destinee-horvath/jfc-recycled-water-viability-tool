"""
backend/phases/p7_financial.py
========================
PHASE — FINANCIAL FEASIBILITY (never a hard reject)

Ported term-for-term from the client's original cost model — treated as
ground truth. Where this disagreed with the tool's earlier implementation
or the URS/SRS, the documentation was updated to match the model, not the
other way around. Quirks in the source model that look like bugs are
implemented literally, not "corrected" — each is flagged with a comment at
the point it's implemented rather than silently fixed.

Combined project volume (§6) is pavement + dust suppression + concrete
kerb/elements, summed together with no branching by Water Quality's
selected application type anywhere. (An earlier version of this module
gated dust-suppression/concrete volume behind application_type — that was
based on an unverified assumption and has been removed; the source model
has no such gate.) Each of the three components can still be individually
excluded from a job via its own "included" flag (dust_suppression_included,
concrete_included, and per-layer for pavement) — a tool usability feature
with no equivalent in the source model, not a Water-Quality-driven gate.

Delivery days split into two additive parts (§10): pavement + concrete are
trucked and divided by the fleet's daily capacity (delivery_days_trucked);
dust suppression has its own independent day count (project_duration_days,
a direct input) added on top, not divided into the trucked-volume
calculation.

Water costs (§7) are rounded up to whole dollars, matching the source
model's own rounding. Everything else (volumes, per-day transport costs,
the break-even chart) stays full precision — the source model doesn't
round those, and the break-even chart specifically needs continuous values
to find a crossing point.
"""

from __future__ import annotations

import math

import config as C
from ..models import CheckResult, PhaseResult

_LAYER_NAMES = ("subgrade", "subbase", "base")


def _layer_volume_kL(layer: dict, total_width_m: float, road_length_m: float) -> float:
    """Water needed to bring one pavement layer from current to optimum
    moisture content, across the full road width and length. Matches the
    source model exactly (same terms, different multiplication order —
    mathematically identical)."""
    return (((layer["omc_pct"] - layer["mc_pct"]) / 100)
            * layer["thickness_m"] * total_width_m * road_length_m
            * layer["density_kg_m3"] / 1000)


def _transport_cost_per_day(distance_km: float, num_trucks: float, trips_per_truck: float,
                             avg_speed_kmh: float, hours_onsite: float, hire_rate_per_hr: float,
                             fuel_efficiency: float, diesel_price: float) -> float:
    """Whole-fleet daily hire + fuel cost for one source. Matches the
    source model exactly, including its quirks:
      * trips_per_truck multiplies into travel hours (and therefore fuel)
        but NOT hours_onsite.
      * Fuel cost uses a hardcoded 50 (assumed km/h) rather than the
        area-type-dependent avg_speed_kmh; not linked to the area-type
        speed selector. Confirm this assumption before changing it — this
        silently misprices fuel whenever the selected area type's speed
        isn't 50 (i.e. whenever it isn't "Urban").

    RESOLVED (2026-07-24): an earlier review question asked whether
    ``hire_rate_per_hr`` (config.FINANCIAL_DEFAULTS default $200/hr)
    already includes fuel, which would make the ``fuel_costs`` term below
    double-count it. Confirmed with the client: the hire rate is
    truck-and-driver only and excludes fuel, so the two additive terms
    (``total_hours * hire_rate_per_hr`` and ``fuel_costs``) are genuinely
    separate cost components, not an overlap. No calculation change
    required.
    """
    travel_hours_per_truck = ((distance_km / avg_speed_kmh) * 2 * trips_per_truck
                               if avg_speed_kmh > 0 else 0.0)
    total_travel_hours = travel_hours_per_truck * num_trucks
    total_hours_onsite = hours_onsite * num_trucks
    total_hours = total_travel_hours + total_hours_onsite
    fuel_costs = ((total_travel_hours * 50) / 100) * fuel_efficiency * diesel_price
    return (total_hours * hire_rate_per_hr) + fuel_costs


def financial_analysis(inp: dict) -> dict:
    """Combined water-volume + whole-of-project cost model — see module
    docstring. No longer takes an application_type argument: the source
    model doesn't gate any Phase 7 calculation on Water Quality's selection."""
    D = C.FINANCIAL_DEFAULTS

    # --- Water costs (§1, keyed off region) -------------------
    mode = inp.get("water_cost_mode", D["water_cost_mode"])
    if mode == "Standard":
        region = inp.get("region", D["region"])
        rates = C.FINANCIAL_REGIONS.get(region, C.FINANCIAL_REGIONS[D["region"]])
        potable_cost_normal = rates["potable_cost_normal"]
        potable_cost_drought = rates["potable_cost_drought"]
        recycled_cost_normal = rates["recycled_cost_normal"]
    else:
        potable_cost_normal = float(inp.get("potable_cost_normal", D["potable_cost_normal"]) or 0)
        potable_cost_drought = float(inp.get("potable_cost_drought", D["potable_cost_drought"]) or 0)
        recycled_cost_normal = float(inp.get("recycled_cost_normal", D["recycled_cost_normal"]) or 0)

    # --- Pavement profile (§2/§3) ----------------------------------------------
    # Flat per-field keys (layer_<name>_<field>), not a nested dict — inputs
    # go through persistence.py's flat CSV round-trip, which only preserves
    # scalars/lists one level deep, not nested dicts.
    layers = {}
    layer_included = {}
    for name in _LAYER_NAMES:
        default_layer = D["pavement_layers"][name]
        layers[name] = {
            field: float(inp.get(f"layer_{name}_{field}", default) or 0)
            for field, default in default_layer.items() if field != "included"
        }
        layer_included[name] = bool(inp.get(f"layer_{name}_included", default_layer["included"]))

    num_lanes = float(inp.get("num_lanes", D["num_lanes"]) or 0)
    lane_width_m = float(inp.get("lane_width_m", D["lane_width_m"]) or 0)
    shoulder_width_m = float(inp.get("shoulder_width_m", D["shoulder_width_m"]) or 0)
    num_shoulders = float(inp.get("num_shoulders", D["num_shoulders"]) or 0)
    road_length_m = float(inp.get("road_length_m", D["road_length_m"]) or 0)
    total_width_m = (num_lanes * lane_width_m) + (num_shoulders * shoulder_width_m)

    # Volumes are always computed for every layer (informational, even when
    # excluded via the "included" checkbox — a tool feature the source
    # model has no equivalent of, since it has no mechanism to exclude a
    # layer at all; kept since it's a genuine usability improvement, not a
    # bug).
    layer_volumes_kL = {
        name: _layer_volume_kL(layer, total_width_m, road_length_m)
        for name, layer in layers.items()
    }
    total_pavement_volume_kL = sum(
        v for name, v in layer_volumes_kL.items() if layer_included[name]
    )

    # --- Transport & operational inputs (§8/§9) ---------------------------------
    num_trucks = float(inp.get("num_trucks", D["num_trucks"]) or 0)
    hire_rate_per_hr = float(inp.get("hire_rate_per_hr", D["hire_rate_per_hr"]) or 0)
    fuel_efficiency = float(inp.get("fuel_efficiency", D["fuel_efficiency"]) or 0)
    diesel_price = float(inp.get("diesel_price", D["diesel_price"]) or 0)
    trips_per_truck = float(inp.get("trips_per_truck", D["trips_per_truck"]) or 0)
    hours_onsite = float(inp.get("hours_onsite", D["hours_onsite"]) or 0)
    truck_capacity_kL = float(inp.get("truck_capacity_kL", D["truck_capacity_kL"]) or 0)
    potable_distance_km = float(inp.get("potable_distance_km", D["potable_distance_km"]) or 0)
    recycled_distance_km = float(inp.get("recycled_distance_km", D["recycled_distance_km"]) or 0)
    area_type = inp.get("area_type", D["area_type"])
    default_speed = C.AREA_TYPE_SPEEDS.get(area_type, C.AREA_TYPE_SPEEDS[D["area_type"]])
    avg_speed_kmh = float(inp.get("avg_speed_kmh", default_speed) or 0)

    # --- Dust suppression (§4) — no application-type gate, but toggleable via
    # "included" for jobs that don't use dust suppression at all (same
    # pattern as a pavement layer's "included") ---------------------------------
    dust_suppression_included = bool(inp.get("dust_suppression_included", D["dust_suppression_included"]))
    surface_area_m2 = float(inp.get("surface_area_m2", D["surface_area_m2"]) or 0)
    water_per_m2_L = float(inp.get("water_per_m2_L", D["water_per_m2_L"]) or 0)
    applications_per_day = float(inp.get("applications_per_day", D["applications_per_day"]) or 0)
    effective_area_pct = float(inp.get("effective_area_pct", D["effective_area_pct"]) or 0)
    project_duration_days = float(inp.get("project_duration_days", D["project_duration_days"]) or 0)

    total_water_per_day_kL = (surface_area_m2 * water_per_m2_L * applications_per_day) / 1000
    effective_water_kL = total_water_per_day_kL * (effective_area_pct / 100)
    # Always computed (informational, e.g. for the input-review/tooltip
    # figures), even when excluded from the totals below.
    dust_suppression_computed_kL = effective_water_kL * project_duration_days
    total_dust_suppression_kL = dust_suppression_computed_kL if dust_suppression_included else 0.0

    # --- Concrete Kerb + Elements (§5) — likewise toggleable via "included" ----
    concrete_included = bool(inp.get("concrete_included", D["concrete_included"]))
    kerb_type = inp.get("kerb_type", D["kerb_type"])
    kerb_volume_per_m = C.CONCRETE_KERB_VOLUME_PER_M.get(
        kerb_type, C.CONCRETE_KERB_VOLUME_PER_M[D["kerb_type"]])
    water_cement_ratio = float(inp.get("water_cement_ratio", D["water_cement_ratio"]) or 0)
    water_volume_fraction = C.CONCRETE_WATER_CEMENT_RATIO_TABLE.get(
        water_cement_ratio, C.CONCRETE_WATER_CEMENT_RATIO_TABLE[D["water_cement_ratio"]])
    additional_concrete_volume_m3 = float(
        inp.get("additional_concrete_volume_m3", D["additional_concrete_volume_m3"]) or 0)

    kerb_concrete_volume_m3 = kerb_volume_per_m * road_length_m
    # Always computed (informational), even when excluded from the totals below.
    concrete_water_computed_kL = (kerb_concrete_volume_m3 + additional_concrete_volume_m3) * water_volume_fraction
    concrete_water_kL = concrete_water_computed_kL if concrete_included else 0.0

    # --- Combined project volume (§6) --------------------------------------------
    combined_total_volume_kL = total_pavement_volume_kL + total_dust_suppression_kL + concrete_water_kL

    # --- Transport costs per day (§8/§9) -----------------------------------------
    potable_transport_cost_per_day = _transport_cost_per_day(
        potable_distance_km, num_trucks, trips_per_truck, avg_speed_kmh, hours_onsite,
        hire_rate_per_hr, fuel_efficiency, diesel_price)
    recycled_transport_cost_per_day = _transport_cost_per_day(
        recycled_distance_km, num_trucks, trips_per_truck, avg_speed_kmh, hours_onsite,
        hire_rate_per_hr, fuel_efficiency, diesel_price)

    # --- Delivery days (§10) ------------------------------------------------------
    # Pavement + concrete are trucked and divided by the fleet's daily
    # capacity; dust suppression's own day count is added on top rather
    # than divided in — matches the source model exactly.
    volume_per_day_kL = num_trucks * trips_per_truck * truck_capacity_kL
    trucked_volume_kL = total_pavement_volume_kL + concrete_water_kL
    delivery_days_trucked = (math.ceil(trucked_volume_kL / volume_per_day_kL)
                              if volume_per_day_kL > 0 else 0.0)
    dust_suppression_days = project_duration_days if dust_suppression_included else 0.0
    total_delivery_days = delivery_days_trucked + dust_suppression_days

    # --- Water costs (§7) — rounded up to whole dollars, matching the source ----
    # model's own rounding exactly.
    potable_water_cost_normal = math.ceil(combined_total_volume_kL * potable_cost_normal)
    potable_water_cost_drought = math.ceil(combined_total_volume_kL * potable_cost_drought)
    recycled_water_cost = math.ceil(combined_total_volume_kL * recycled_cost_normal)
    savings_normal = potable_water_cost_normal - recycled_water_cost
    savings_drought = potable_water_cost_drought - recycled_water_cost

    # --- Transport cost difference & Profit/Loss (§10) ---------------------------
    daily_cost_difference = recycled_transport_cost_per_day - potable_transport_cost_per_day
    total_cost_difference = total_delivery_days * daily_cost_difference
    profit_normal = max(savings_normal - total_cost_difference, 0)
    loss_normal = max(total_cost_difference - savings_normal, 0)
    profit_drought = max(savings_drought - total_cost_difference, 0)
    loss_drought = max(total_cost_difference - savings_drought, 0)

    # --- Continuous whole-of-project totals — NOT in the source model, kept -----
    # only for the break-even chart (FR7.9), which needs a distance-varying
    # continuous total to find a crossing point; the rounded, water-only
    # figures above can't do that on their own since they don't vary with
    # distance at all.
    potable_total_cost = (combined_total_volume_kL * potable_cost_normal
                           + potable_transport_cost_per_day * total_delivery_days)
    recycled_total_cost = (combined_total_volume_kL * recycled_cost_normal
                            + recycled_transport_cost_per_day * total_delivery_days)
    potable_drought_total = (combined_total_volume_kL * potable_cost_drought
                              + potable_transport_cost_per_day * total_delivery_days)

    if recycled_total_cost < potable_total_cost:
        verdict = "PROCEED"
    elif recycled_total_cost < potable_drought_total:
        verdict = "CONDITIONAL"
    else:
        verdict = "CONDITIONAL"

    return {
        "water_cost_mode": mode,
        "region": inp.get("region", D["region"]),
        "potable_cost_normal": potable_cost_normal,
        "potable_cost_drought": potable_cost_drought,
        "recycled_cost_normal": recycled_cost_normal,

        "total_width_m": total_width_m,
        "layer_volumes_kL": layer_volumes_kL,
        "layer_included": layer_included,
        "total_pavement_volume_kL": total_pavement_volume_kL,

        "total_water_per_day_kL": total_water_per_day_kL,
        "effective_water_kL": effective_water_kL,
        "project_duration_days": project_duration_days,
        "dust_suppression_included": dust_suppression_included,
        "dust_suppression_computed_kL": dust_suppression_computed_kL,
        "total_dust_suppression_kL": total_dust_suppression_kL,

        "kerb_type": kerb_type,
        "water_cement_ratio": water_cement_ratio,
        "additional_concrete_volume_m3": additional_concrete_volume_m3,
        "kerb_concrete_volume_m3": kerb_concrete_volume_m3,
        "concrete_included": concrete_included,
        "concrete_water_computed_kL": concrete_water_computed_kL,
        "concrete_water_kL": concrete_water_kL,

        "combined_total_volume_kL": combined_total_volume_kL,

        "potable_transport_cost_per_day": potable_transport_cost_per_day,
        "recycled_transport_cost_per_day": recycled_transport_cost_per_day,
        "volume_per_day_kL": volume_per_day_kL,
        "delivery_days_trucked": delivery_days_trucked,
        "dust_suppression_days": dust_suppression_days,
        "total_delivery_days": total_delivery_days,
        "delivery_days": total_delivery_days,   # kept for existing UI/report text

        "potable_water_cost_normal": potable_water_cost_normal,
        "potable_water_cost_drought": potable_water_cost_drought,
        "recycled_water_cost": recycled_water_cost,
        "savings_normal": savings_normal,
        "savings_drought": savings_drought,

        "daily_cost_difference": daily_cost_difference,
        "total_cost_difference": total_cost_difference,
        "profit_normal": profit_normal,
        "loss_normal": loss_normal,
        "profit_drought": profit_drought,
        "loss_drought": loss_drought,

        "potable_total_cost": potable_total_cost,
        "recycled_total_cost": recycled_total_cost,
        "potable_drought_total": potable_drought_total,

        "verdict": verdict,
    }


def recycled_distance_breakeven_curve(inp: dict, n_points: int = 40) -> dict:
    """
    Cost-vs-distance curve for the "Cost summary & break-even analysis"
    chart. Unlike the old single-shared-distance model, potable and
    recycled now have their own independent distance inputs, so there's no
    one shared axis to sweep — this sweeps ``recycled_distance_km`` only
    (holding every other input, including ``potable_distance_km``, fixed),
    since that's the distance an engineer can actually negotiate/shop
    around on. Potable's totals are therefore flat reference lines here,
    not because they're distance-independent in general, but because this
    particular sweep doesn't touch potable_distance_km.

    Every point re-runs ``financial_analysis()`` rather than re-deriving
    the transport formula here, so the chart can never drift from what the
    checks/summary actually show. Recycled's transport cost is linear in
    distance, so the two break-even crossings are solved exactly from the
    first and last sampled points rather than by curve-fitting.
    """
    current_distance = float(inp.get("recycled_distance_km", C.FINANCIAL_DEFAULTS["recycled_distance_km"]) or 0)
    max_distance = max(current_distance * 2, 20.0)
    step = max_distance / n_points if n_points else max_distance

    curve = []
    for i in range(n_points + 1):
        dist = i * step
        fa = financial_analysis(dict(inp, recycled_distance_km=dist))
        curve.append({
            "distance_km": dist,
            "recycled": fa["recycled_total_cost"],
            "potable": fa["potable_total_cost"],
            "potable_drought": fa["potable_drought_total"],
        })

    def _breakeven(target_key: str):
        c0, c1 = curve[0]["recycled"], curve[-1]["recycled"]
        if max_distance <= 0 or c1 == c0:
            return None
        slope = (c1 - c0) / max_distance
        if slope <= 0:
            return None
        target = curve[0][target_key]
        d = (target - c0) / slope
        return d if d >= 0 else None

    return {
        "curve": curve,
        "max_distance_km": max_distance,
        "current_recycled_distance_km": current_distance,
        "breakeven_distance_km": _breakeven("potable"),
        "breakeven_distance_drought_km": _breakeven("potable_drought"),
    }


def assess_financial(inp: dict, ctx: dict = None) -> PhaseResult:
    """Whole-of-project cost: pavement + dust suppression + concrete kerb
    water volume (always summed — see module docstring), trucked from
    separate potable/recycled sources, compared under normal and drought
    potable pricing. Unfavourable cost -> CONDITIONAL only, never REJECT."""
    g = PhaseResult(phase_id="financial", mandatory=False)
    fa = financial_analysis(inp)

    if fa["combined_total_volume_kL"] <= 0:
        g.checks.append(CheckResult(
            "Whole-of-life cost comparison", "CONDITIONAL", C.FINANCIAL_REF,
            "Insufficient inputs (pavement geometry / moisture content) to "
            "compute a water volume, so no cost comparison could be made."))
        g.rollup()
        return g

    excluded = [name for name, inc in fa["layer_included"].items() if not inc]
    excluded_line = (f" ({', '.join(excluded)} excluded — not relevant to this job)"
                      if excluded else "")
    dust_note = "" if fa["dust_suppression_included"] else " (excluded — not relevant to this job)"
    concrete_note = "" if fa["concrete_included"] else " (excluded — not relevant to this job)"
    g.checks.append(CheckResult(
        "Total volume of water required", "PROCEED", C.FINANCIAL_REF,
        f"Pavement: {fa['total_pavement_volume_kL']:,.1f} kL{excluded_line}. "
        f"Dust suppression: {fa['total_dust_suppression_kL']:,.1f} kL{dust_note}. "
        f"Concrete kerb + elements: {fa['concrete_water_kL']:,.1f} kL{concrete_note}. "
        f"Combined total: {fa['combined_total_volume_kL']:,.1f} kL.",
    ))

    g.checks.append(CheckResult(
        "Water costs comparison", "PROCEED", C.FINANCIAL_REF,
        f"Potable (normal): ${fa['potable_water_cost_normal']:,.0f}. "
        f"Recycled: ${fa['recycled_water_cost']:,.0f}. "
        f"Potable (drought): ${fa['potable_water_cost_drought']:,.0f}. "
        f"Savings: ${fa['savings_normal']:,.0f} (normal), "
        f"${fa['savings_drought']:,.0f} (drought).",
    ))

    g.checks.append(CheckResult(
        "Transport costs comparison", "PROCEED", C.FINANCIAL_REF,
        f"Potable transport (per day): ${fa['potable_transport_cost_per_day']:,.0f}. "
        f"Recycled transport (per day): ${fa['recycled_transport_cost_per_day']:,.0f}. "
        f"Difference: ${fa['daily_cost_difference']:,.0f}/day over "
        f"{fa['total_delivery_days']:,.1f} days "
        f"({fa['delivery_days_trucked']:,.0f} trucked + "
        f"{fa['dust_suppression_days']:,.0f} dust suppression). "
        f"Total transport cost difference: ${fa['total_cost_difference']:,.0f}.",
    ))

    detail = (f"Water savings: ${fa['savings_normal']:,.0f} (normal), "
              f"${fa['savings_drought']:,.0f} (drought). "
              f"Transport cost difference: ${fa['total_cost_difference']:,.0f}. "
              f"Profit: ${fa['profit_normal']:,.0f} (normal), "
              f"${fa['profit_drought']:,.0f} (drought). "
              f"Loss: ${fa['loss_normal']:,.0f} (normal), "
              f"${fa['loss_drought']:,.0f} (drought).")

    if fa["profit_normal"] > 0:
        g.checks.append(CheckResult(
            "Total project cost comparison", "PROCEED", C.FINANCIAL_REF,
            detail + " Recycled water is cost favourable."))
    elif fa["profit_drought"] > 0:
        g.checks.append(CheckResult(
            "Total project cost comparison", "CONDITIONAL", C.FINANCIAL_REF,
            detail + " Recycled water is more expensive than potable under "
            "normal conditions, but cost favourable under drought pricing."))
    else:
        g.checks.append(CheckResult(
            "Total project cost comparison", "CONDITIONAL", C.FINANCIAL_REF,
            detail + " Recycled water is not cost favourable under any "
            "conditions modelled — the client may still proceed for "
            "sustainability / supply-security reasons."))

    g.rollup()
    return g
