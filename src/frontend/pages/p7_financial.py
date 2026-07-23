"""
frontend/pages/p7_financial.py
=========================
PHASE — Financial Feasibility

Collects inputs across six sections (Water Costs, Pavement Profile, Road
Geometry, Transport & Operational Costs, Dust Suppression, Concrete Kerb +
Elements) — all always shown, matching the client's original cost model,
which has no gate on any of these by Water Quality's selected application
type — and renders backend.financial_analysis()'s output as a cost
summary. All
calculation logic lives in backend/phases/p7_financial.py — this module
only collects inputs and displays results.
"""

import altair as alt
import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import config as C
import backend as B

from ..state import gi, render_phase_actions
from ..refdata import PHASE_BY_ID
from ..theme import COLOUR_PRIMARY, COLOUR_SUCCESS, COLOUR_WARNING, COLOUR_NEUTRAL, accounting_amount

def _persisted_expander(label: str, key: str):
    """st.expander bound to a session_state key so it stays open across a
    rerun triggered by a widget inside it — a bare `expanded=` literal is
    re-evaluated on every rerun and would otherwise snap shut as soon as
    the user touches anything inside (see frontend/pages/p2_rwmp.py for
    the same fix). Defaults to closed."""
    st.session_state.setdefault(key, False)
    return st.expander(label, expanded=st.session_state[key], key=key)


_LAYER_LABELS = {"subgrade": "Subgrade", "subbase": "Subbase", "base": "Base"}
_LAYER_FIELDS = [
    ("omc_pct", "OMC (%)"),
    ("mc_pct", "Current MC (%)"),
    ("thickness_m", "Thickness (m)"),
    ("density_kg_m3", "Density (kg/m³)"),
]

_SCALAR_KEYS = [
    "water_cost_mode", "region", "potable_cost_normal", "potable_cost_drought",
    "recycled_cost_normal", "drought_savings_custom",
    "num_lanes", "lane_width_m", "shoulder_width_m", "num_shoulders", "road_length_m",
    "num_trucks", "hire_rate_per_hr", "fuel_efficiency", "diesel_price",
    "trips_per_truck", "hours_onsite", "truck_capacity_kL",
    "potable_distance_km", "recycled_distance_km", "area_type", "avg_speed_kmh",
    "surface_area_m2", "site_conditions", "temperature_conditions",
    "applications_per_day", "water_per_m2_L", "effective_area_pct", "project_duration_days",
    "kerb_type", "water_cement_ratio", "additional_concrete_volume_m3",
]
_WIDGET_KEYS = (
    [f"financial_{k}" for k in _SCALAR_KEYS]
    + [f"financial_layer_{name}_{field}" for name in _LAYER_LABELS for field, _ in _LAYER_FIELDS]
    + [f"financial_layer_{name}_included" for name in _LAYER_LABELS]
    + ["financial_show_graph"]
    + [f"financial_{role}_addr_{part}" for role in ("potable", "recycled") for part in ("origin", "dest")]
    + ["_pending_potable_distance_km", "_pending_recycled_distance_km"]
    + [f"_ors_route_{role}" for role in ("potable", "recycled")]
    + [f"_ors_error_{role}" for role in ("potable", "recycled")]
    + ["_ors_last_run", "_ors_compare"]
)


def page_financial(results):
    g = PHASE_BY_ID["financial"]
    c1, c2 = st.columns([4, 1])
    with c1:
        st.header(g["label"], help=g["desc"])
    with c2:
        if st.button("⊘ Reset / clear inputs", key="financial_reset", width="stretch"):
            st.session_state.inputs["financial"] = {}
            for k in _WIDGET_KEYS:
                st.session_state.pop(k, None)
            st.rerun()

    d = gi("financial")
    D = C.FINANCIAL_DEFAULTS
    # One-way defaults only: read Phase 5's soil_to_financial (if the
    # engineer has filled it in) to seed these keys' FIRST value. Once a key
    # exists in `d` (including after this), setdefault below never
    # overwrites it again — so nothing here ever writes back to Phase 5, and
    # editing a value on this page never affects it either.
    soil_defaults = st.session_state.get("soil_to_financial")
    for k in _SCALAR_KEYS:
        d.setdefault(k, D[k])
    for name, layer_defaults in D["pavement_layers"].items():
        soil_layer = (soil_defaults or {}).get(name, {})
        for field, default in layer_defaults.items():
            if field == "included":
                value = soil_layer.get("active", default)
            else:
                value = soil_layer.get(field)
                if value is None:
                    value = default
            d.setdefault(f"layer_{name}_{field}", value)

    # Apply any distance calculated by _address_lookup() on the previous
    # run, BEFORE the distance number_input widgets below are instantiated
    # this run — writing to a widget's session_state key after it has
    # already been instantiated this run raises a StreamlitAPIException.
    for key in ("potable_distance_km", "recycled_distance_km"):
        pending_key = f"_pending_{key}"
        if pending_key in st.session_state:
            value = st.session_state.pop(pending_key)
            d[key] = value
            st.session_state[f"financial_{key}"] = value

    _water_costs_section(d)
    _pavement_profile_section(d)
    total_width_m = _road_geometry_section(d)
    _transport_section(d)
    # Dust suppression and concrete kerb+elements are always shown and always
    # included in the combined project volume — the source model has no
    # gate on either by Water Quality's selected application type.
    _dust_suppression_section(d)
    _concrete_mixing_section(d)

    fa = B.financial_analysis(d)
    _input_review(d, total_width_m)
    _cost_summary_section(fa, d)

    render_phase_actions("financial")


def _water_costs_section(d):
    with _persisted_expander("💧 Water Costs", "financial_water_costs_expander"):
        st.info("DISCLAIMER: Refer to official council guidlines and water authority pricing for your region. Prices and conditions during droughts may vary.")

        d["water_cost_mode"] = st.radio(
            "Input mode", ["Standard", "Custom"],
            index=["Standard", "Custom"].index(d.get("water_cost_mode", "Standard")),
            horizontal=True, key="financial_water_cost_mode")

        if d["water_cost_mode"] == "Standard":
            d["region"] = st.selectbox(
                "Region", list(C.FINANCIAL_REGIONS.keys()),
                index=list(C.FINANCIAL_REGIONS.keys()).index(d.get("region", C.FINANCIAL_DEFAULTS["region"])),
                key="financial_region")
            rates = C.FINANCIAL_REGIONS[d["region"]]
            st.caption(
                f"Default rates for {d['region']} — potable (normal): "
                f"${rates['potable_cost_normal']:,.2f}/kL · potable (drought): "
                f"${rates['potable_cost_drought']:,.2f}/kL · recycled: "
                f"${rates['recycled_cost_normal']:,.2f}/kL."
                f"confirm with the local water authority/council.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                d["potable_cost_normal"] = st.number_input(
                    "Cost of potable water ($/kL)", min_value=0.0,
                    value=float(d["potable_cost_normal"]), key="financial_potable_cost_normal")
            with c2:
                d["potable_cost_drought"] = st.number_input(
                    "Cost of potable water in drought ($/kL)", min_value=0.0,
                    value=float(d["potable_cost_drought"]), key="financial_potable_cost_drought")
            with c3:
                d["recycled_cost_normal"] = st.number_input(
                    "Cost of recycled water ($/kL)", min_value=0.0,
                    value=float(d["recycled_cost_normal"]), key="financial_recycled_cost_normal")
            with c4:
                d["drought_savings_custom"] = st.number_input(
                    "Custom drought savings ($/kL)", min_value=0.0,
                    value=float(d["drought_savings_custom"]), key="financial_drought_savings_custom",
                    help="Recorded for the record only — not yet wired into the "
                         "cost comparison below; the source model does not "
                         "define how it combines with the drought cost above.")


def _pavement_profile_section(d):
    with _persisted_expander("🛣 Pavement Profile", "financial_pavement_profile_expander"):
        for name, label in _LAYER_LABELS.items():
            included_key = f"layer_{name}_included"
            d[included_key] = st.checkbox(
                f"{label} — relevant to this job", value=bool(d.get(included_key, True)),
                help="Water needed per layer = (OMC − current MC) × thickness "
                     "× road width × road length × density.",
                key=f"financial_{included_key}")
            cols = st.columns(4)
            for col, (field, field_label) in zip(cols, _LAYER_FIELDS):
                dk = f"layer_{name}_{field}"
                d[dk] = col.number_input(
                    field_label, min_value=0.0, value=float(d[dk]),
                    key=f"financial_{dk}", disabled=not d[included_key])
            if not d[included_key]:
                st.caption(f"{label} excluded — not counted in the water volume/cost calculation.")


def _road_geometry_section(d):
    with _persisted_expander("📐 Road Geometry", "financial_road_geometry_expander"):
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            d["num_lanes"] = st.number_input(
                "Number of lanes", min_value=0, step=1, value=int(d["num_lanes"]),
                key="financial_num_lanes")
        with c2:
            d["lane_width_m"] = st.number_input(
                "Lane width (m)", min_value=0.0, value=float(d["lane_width_m"]),
                key="financial_lane_width_m")
        with c3:
            d["shoulder_width_m"] = st.number_input(
                "Shoulder width (m)", min_value=0.0, value=float(d["shoulder_width_m"]),
                key="financial_shoulder_width_m")
        with c4:
            d["num_shoulders"] = st.number_input(
                "Number of shoulders", min_value=0, step=1, value=int(d["num_shoulders"]),
                key="financial_num_shoulders")
        with c5:
            d["road_length_m"] = st.number_input(
                "Road length (m)", min_value=0.0, value=float(d["road_length_m"]),
                key="financial_road_length_m")

        total_width_m = (d["num_lanes"] * d["lane_width_m"]) + (d["num_shoulders"] * d["shoulder_width_m"])
        st.caption(f"↳ Total road width: **{total_width_m:,.1f} m** "
                   f"(= {d['num_lanes']:g} lanes × {d['lane_width_m']:g} m "
                   f"+ {d['num_shoulders']:g} shoulders × {d['shoulder_width_m']:g} m)")
        return total_width_m


def _render_route_map(role: str, route: dict):
    """One folium map for a single lookup: water-source marker, site marker,
    driving route polyline, auto-fit to its own bounds. Degrades to
    markers-only (no crash) if the route has no usable geometry — missing
    or malformed geometry from ORS never blocks the distance result itself."""
    origin, destination = route["origin"], route["destination"]
    geometry = route.get("geometry") or []

    m = folium.Map()
    bounds = [(origin["lat"], origin["lng"]), (destination["lat"], destination["lng"])] + geometry
    m.fit_bounds(bounds)

    folium.Marker(
        [origin["lat"], origin["lng"]],
        tooltip=f"Water source: {route.get('origin_label', '')}",
        icon=folium.Icon(color="blue", icon="tint"),
    ).add_to(m)
    folium.Marker(
        [destination["lat"], destination["lng"]],
        tooltip=f"Site: {route.get('destination_label', '')}",
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(m)

    if geometry:
        folium.PolyLine(geometry, color=COLOUR_PRIMARY, weight=4, opacity=0.8).add_to(m)
    else:
        st.caption("⚠ Route geometry unavailable — showing markers only.")

    st.caption(f"**{route['distance_km']:,.1f} km** — "
               f"{route.get('origin_label', '')} → {route.get('destination_label', '')}")
    st_folium(m, key=f"ors_map_{role}", height=350, returned_objects=[])


def _address_lookup(role: str, d: dict, distance_key: str):
    """Optional 'Calculate from addresses' expander for one distance field
    (role is 'potable' or 'recycled'). Entirely hidden when ORS isn't
    configured — the manual number_input above is always the fallback.
    Stores its result in session_state (`_ors_route_<role>`) so the map can
    be re-rendered — and compared against the other lookup — without a
    fresh ORS call; see the Compare button in _transport_section()."""
    if not C.ORS_ENABLED:
        return

    with _persisted_expander("📍 Calculate from addresses (optional)", f"financial_{role}_addr_expander"):
        origin_addr = st.text_input(
            "Water source address", key=f"financial_{role}_addr_origin",
            placeholder="e.g. 123 Smith St, Port Macquarie NSW")
        dest_addr = st.text_input(
            "Site address", key=f"financial_{role}_addr_dest",
            placeholder="e.g. Pacific Highway, Kempsey NSW")

        if st.button("Calculate driving distance", key=f"financial_{role}_calc_btn"):
            if not origin_addr or not dest_addr:
                st.session_state[f"_ors_error_{role}"] = (
                    "Enter both the water source address and the site address.")
            else:
                with st.spinner("Looking up addresses and calculating driving distance…"):
                    origin = B.geocode_address(origin_addr, C.ORS_API_KEY)
                    destination = B.geocode_address(dest_addr, C.ORS_API_KEY)
                    if origin is None or destination is None:
                        st.session_state[f"_ors_error_{role}"] = (
                            "Could not locate one or both addresses. Please "
                            "check the addresses and try again, or enter the "
                            "distance manually.")
                    else:
                        route = B.get_driving_route(origin, destination, C.ORS_API_KEY)
                        if route is None:
                            st.session_state[f"_ors_error_{role}"] = (
                                "Could not calculate driving distance. Please "
                                "enter the distance manually.")
                        else:
                            st.session_state.pop(f"_ors_error_{role}", None)
                            st.session_state[f"_ors_route_{role}"] = {
                                **route,
                                "origin": origin, "destination": destination,
                                "origin_label": origin_addr, "destination_label": dest_addr,
                            }
                            st.session_state["_ors_last_run"] = role
                            # The number_input above has already been instantiated this
                            # run, so neither `d[...]` nor its session_state key can be
                            # set directly here — stash it as pending and rerun; the top
                            # of page_financial() applies it before the widget renders.
                            st.session_state[f"_pending_{distance_key}"] = route["distance_km"]
                            st.session_state["_save_toast"] = (
                                f"Driving distance calculated: {route['distance_km']:.1f} km "
                                "(via OpenRouteService). You can adjust this manually if needed.")
                            st.rerun()

        error = st.session_state.get(f"_ors_error_{role}")
        if error:
            st.error(error)

        # Default: only the map for the lookup just run is shown. The
        # Compare button (once, after both lookups — see _transport_section)
        # can additionally reveal the other one, reusing the stored result
        # rather than calling ORS again.
        stored_route = st.session_state.get(f"_ors_route_{role}")
        if stored_route and (st.session_state.get("_ors_last_run") == role
                              or st.session_state.get("_ors_compare")):
            _render_route_map(role, stored_route)


def _transport_section(d):
    with _persisted_expander("🚚 Transport & Operational Costs", "financial_transport_expander"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            d["num_trucks"] = st.number_input(
                "Number of water trucks", min_value=0, step=1, value=int(d["num_trucks"]),
                key="financial_num_trucks")
        with c2:
            d["hire_rate_per_hr"] = st.number_input(
                "Hire rate incl. driver ($/hr)", min_value=0.0, value=float(d["hire_rate_per_hr"]),
                key="financial_hire_rate_per_hr")
        with c3:
            d["fuel_efficiency"] = st.number_input(
                "Avg fuel efficiency (L/100km)", min_value=0.0, value=float(d["fuel_efficiency"]),
                key="financial_fuel_efficiency")
        with c4:
            d["diesel_price"] = st.number_input(
                "Price of diesel ($/L)", min_value=0.0, value=float(d["diesel_price"]),
                key="financial_diesel_price")

        c1, c2, c3 = st.columns(3)
        with c1:
            d["trips_per_truck"] = st.number_input(
                "Trips per truck", min_value=0, step=1, value=int(d["trips_per_truck"]),
                key="financial_trips_per_truck")
        with c2:
            d["hours_onsite"] = st.number_input(
                "Hours required per truck on site", min_value=0.0, value=float(d["hours_onsite"]),
                key="financial_hours_onsite")
        with c3:
            d["truck_capacity_kL"] = st.number_input(
                "Truck capacity (kL)", min_value=0.0, value=float(d["truck_capacity_kL"]),
                key="financial_truck_capacity_kL")

        st.markdown("**Source distances**",
                    help=None if C.ORS_ENABLED else
                    "To enable automatic distance calculation, add your "
                    "OpenRouteService API key to the .env file. Get a free "
                    "key at openrouteservice.org")
        c1, c2 = st.columns(2)
        with c1:
            # setdefault (not value=) — a pending ORS-calculated distance
            # may already have set this session_state key above; passing
            # value= as well would trigger Streamlit's "widget created with
            # a default value but also had its value set via the Session
            # State API" warning.
            st.session_state.setdefault("financial_potable_distance_km", float(d["potable_distance_km"]))
            d["potable_distance_km"] = st.number_input(
                "Distance site to potable source (km)", min_value=0.0,
                key="financial_potable_distance_km")
            _address_lookup("potable", d, "potable_distance_km")
        with c2:
            st.session_state.setdefault("financial_recycled_distance_km", float(d["recycled_distance_km"]))
            d["recycled_distance_km"] = st.number_input(
                "Distance site to recycled source (km)", min_value=0.0,
                key="financial_recycled_distance_km")
            _address_lookup("recycled", d, "recycled_distance_km")

        if C.ORS_ENABLED:
            both_ready = bool(st.session_state.get("_ors_route_potable")) and \
                bool(st.session_state.get("_ors_route_recycled"))
            comparing = st.session_state.get("_ors_compare", False)
            if st.button("🔀 Hide comparison" if comparing else "🔀 Compare both routes",
                         key="financial_ors_compare_btn", disabled=not both_ready,
                         help=None if both_ready else
                         "Run both address lookups above first.",
                         width="stretch"):
                st.session_state["_ors_compare"] = not comparing
                st.rerun()

        st.markdown("**Average travel speed**")
        c1, c2 = st.columns([1, 2])
        with c1:
            area_types = list(C.AREA_TYPE_SPEEDS.keys())
            new_area_type = st.radio(
                "Area type", area_types,
                index=area_types.index(d.get("area_type", "Urban"))
                if d.get("area_type") in area_types else area_types.index("Urban"),
                horizontal=True, key="financial_area_type")
        if new_area_type != d.get("area_type"):
            # Area type just changed — reset the speed to that type's default.
            # Once the user edits the speed field directly, it's left alone.
            # Both `d` AND the number_input's own session_state key must be
            # updated here, before that widget is instantiated below —
            # passing a new `value=` alone has no effect once a widget's key
            # already holds a value in session_state (Streamlit ignores
            # `value` on every run after the first for a given key), which
            # is why the area-type buttons previously appeared to do nothing.
            d["avg_speed_kmh"] = C.AREA_TYPE_SPEEDS[new_area_type]
            st.session_state["financial_avg_speed_kmh"] = d["avg_speed_kmh"]
        d["area_type"] = new_area_type
        with c2:
            d["avg_speed_kmh"] = st.number_input(
                "Average speed (km/h)", min_value=0.0, value=float(d["avg_speed_kmh"]),
                step=1.0, key="financial_avg_speed_kmh")


def _dust_suppression_section(d):
    with _persisted_expander("💨 Dust Suppression", "financial_dust_suppression_expander"):
        c1, c2 = st.columns(2)
        with c1:
            d["surface_area_m2"] = st.number_input(
                "Surface area (m²)", min_value=0.0, value=float(d["surface_area_m2"]),
                key="financial_surface_area_m2")
        with c2:
            d["applications_per_day"] = st.number_input(
                "Applications per day", min_value=0, step=1, value=int(d["applications_per_day"]),
                key="financial_applications_per_day")

        c1, c2, c3 = st.columns(3)
        with c1:
            d["site_conditions"] = st.selectbox(
                "Site conditions (traffic, wind, temperature activity)",
                C.DUST_SITE_CONDITIONS,
                index=C.DUST_SITE_CONDITIONS.index(d.get("site_conditions", "Medium")),
                key="financial_site_conditions")
        with c2:
            d["temperature_conditions"] = st.selectbox(
                "Temperature conditions", C.DUST_TEMPERATURE_CONDITIONS,
                index=C.DUST_TEMPERATURE_CONDITIONS.index(d.get("temperature_conditions", "Sunny")),
                key="financial_temperature_conditions")
        with c3:
            d["water_per_m2_L"] = st.number_input(
                "Water volume per m² (L)", min_value=0.0, value=float(d["water_per_m2_L"]),
                key="financial_water_per_m2_L")

        c1, c2 = st.columns(2)
        with c1:
            d["effective_area_pct"] = st.number_input(
                "Effective area for dust suppression (%)", min_value=0.0, max_value=100.0,
                value=float(d["effective_area_pct"]), key="financial_effective_area_pct")
        with c2:
            d["project_duration_days"] = st.number_input(
                "Project duration (days)", min_value=0.0,
                value=float(d["project_duration_days"]), key="financial_project_duration_days",
                help="Not in the original cost model — added because its own "
                     "day-count formula for dust suppression cancelled out "
                     "algebraically to always equal the pavement volume, "
                     "making it independent of every other dust-suppression "
                     "input above. This field replaces it with an explicit, "
                     "editable duration.")


def _concrete_mixing_section(d):
    with _persisted_expander("🧱 Concrete Kerb + Elements", "financial_concrete_kerb_expander"):
        st.caption("Water demand = (kerb concrete volume + additional concrete "
                   "volume) × water volume fraction for the selected water-"
                   "cement ratio. Always included in the combined project "
                   "volume, regardless of Water Quality's selected application type.")
        kerb_types = list(C.CONCRETE_KERB_VOLUME_PER_M.keys())
        ratios = list(C.CONCRETE_WATER_CEMENT_RATIO_TABLE.keys())
        c1, c2, c3 = st.columns(3)
        with c1:
            d["kerb_type"] = st.selectbox(
                "Kerb type", kerb_types,
                index=kerb_types.index(d.get("kerb_type", kerb_types[0])),
                help="Kerb concrete volume per metre of road length.",
                key="financial_kerb_type")
        with c2:
            d["water_cement_ratio"] = st.selectbox(
                "Water-cement ratio", ratios,
                index=ratios.index(d.get("water_cement_ratio", ratios[0])),
                help="Water volume fraction of total concrete volume.",
                key="financial_water_cement_ratio")
        with c3:
            d["additional_concrete_volume_m3"] = st.number_input(
                "Additional concrete volume (m³)", min_value=0.0,
                value=float(d["additional_concrete_volume_m3"]),
                help="Road elements not covered by the kerb lookup — e.g. "
                     "drainage pits, aprons.",
                key="financial_additional_concrete_volume_m3")


def _input_review(d, total_width_m):
    """Lets the user check every value entered above in one place before
    trusting the cost comparison below."""
    with _persisted_expander("🔍 Review your inputs", "financial_review_inputs_expander"):
        rows = [
            ("Water cost mode", d.get("water_cost_mode", "")),
        ]
        if d.get("water_cost_mode") == "Standard":
            rows.append(("Region", d.get("region", "")))
        else:
            rows += [
                ("Potable cost (normal)", f"${d.get('potable_cost_normal', 0):,.2f}/kL"),
                ("Potable cost (drought)", f"${d.get('potable_cost_drought', 0):,.2f}/kL"),
                ("Recycled cost (normal)", f"${d.get('recycled_cost_normal', 0):,.2f}/kL"),
                ("Custom drought savings", f"${d.get('drought_savings_custom', 0):,.2f}/kL"),
            ]
        for name, label in _LAYER_LABELS.items():
            status = "" if d.get(f"layer_{name}_included", True) else " (excluded)"
            rows.append((f"{label}{status} — OMC/MC/thickness/density",
                         f"{d.get(f'layer_{name}_omc_pct', 0):g}% / "
                         f"{d.get(f'layer_{name}_mc_pct', 0):g}% / "
                         f"{d.get(f'layer_{name}_thickness_m', 0):g} m / "
                         f"{d.get(f'layer_{name}_density_kg_m3', 0):g} kg/m³"))
        rows += [
            ("Number of lanes", f"{d.get('num_lanes', 0):g}"),
            ("Lane width", f"{d.get('lane_width_m', 0):g} m"),
            ("Shoulder width", f"{d.get('shoulder_width_m', 0):g} m"),
            ("Number of shoulders", f"{d.get('num_shoulders', 0):g}"),
            ("Road length", f"{d.get('road_length_m', 0):g} m"),
            ("Number of trucks", f"{d.get('num_trucks', 0):g}"),
            ("Hire rate", f"${d.get('hire_rate_per_hr', 0):,.2f}/hr"),
            ("Fuel efficiency", f"{d.get('fuel_efficiency', 0):g} L/100km"),
            ("Diesel price", f"${d.get('diesel_price', 0):,.2f}/L"),
            ("Trips per truck", f"{d.get('trips_per_truck', 0):g}"),
            ("Hours onsite per truck", f"{d.get('hours_onsite', 0):g}"),
            ("Truck capacity", f"{d.get('truck_capacity_kL', 0):g} kL"),
            ("Potable source distance", f"{d.get('potable_distance_km', 0):g} km"),
            ("Recycled source distance", f"{d.get('recycled_distance_km', 0):g} km"),
            ("Area type / avg speed", f"{d.get('area_type', '')} / {d.get('avg_speed_kmh', 0):g} km/h"),
        ]
        body = "".join(
            f"<tr><td style='padding:4px 10px'>{name}</td>"
            f"<td style='padding:4px 10px;text-align:right'>{value}</td></tr>"
            for name, value in rows)
        st.markdown(
            f"<table style='width:100%;border-collapse:collapse;font-size:0.9rem'>"
            f"<tr style='color:{COLOUR_PRIMARY};font-weight:700;border-bottom:1px solid #ddd'>"
            f"<td style='padding:4px 10px'>Input</td>"
            f"<td style='padding:4px 10px;text-align:right'>Value</td></tr>"
            f"{body}</table>", unsafe_allow_html=True)


def _net_position_line(net: float, scenario_label: str) -> str:
    """One-line plain-language readout of a signed net-position figure —
    lets the reader skip mentally subtracting savings from the transport
    cost difference themselves."""
    if net > 0:
        return f"Recycled water **saves ${net:,.0f}** compared to potable under {scenario_label} pricing."
    if net < 0:
        return f"Recycled water **costs ${abs(net):,.0f} more** than potable under {scenario_label} pricing."
    return f"Recycled water costs the same as potable under {scenario_label} pricing."


def _cost_summary_section(fa: dict, d: dict):
    st.divider()
    st.subheader("Cost summary & break-even analysis")

    if fa["combined_total_volume_kL"] <= 0:
        st.caption("Enter pavement geometry and moisture content to compute the comparison.")
        return

    net_normal = fa["savings_normal"] - fa["total_cost_difference"]
    net_drought = fa["savings_drought"] - fa["total_cost_difference"]
    st.markdown(_net_position_line(net_normal, "normal"))

    st.markdown("**Total volume of water required** (always summed — pavement, "
                "dust suppression, and concrete kerb+elements all combine)")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pavement", f"{fa['total_pavement_volume_kL']:,.1f} kL")
    c2.metric("Dust suppression", f"{fa['total_dust_suppression_kL']:,.1f} kL")
    c3.metric("Concrete kerb + elements", f"{fa['concrete_water_kL']:,.1f} kL")
    c4.metric("Combined total", f"{fa['combined_total_volume_kL']:,.1f} kL")

    st.markdown("**Water costs comparison** (rounded up to whole dollars)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Potable (normal)", f"${fa['potable_water_cost_normal']:,.0f}")
    c2.metric("Recycled", f"${fa['recycled_water_cost']:,.0f}")
    c3.metric("Potable (drought)", f"${fa['potable_water_cost_drought']:,.0f}")

    st.markdown("**Water cost savings** (potable minus recycled — parentheses/red "
                "= recycled water costs more)")
    c1, c2 = st.columns(2)
    c1.markdown(f"Savings (normal): {accounting_amount(fa['savings_normal'], favourable=fa['savings_normal'] >= 0)}",
                unsafe_allow_html=True)
    c2.markdown(f"Savings (drought): {accounting_amount(fa['savings_drought'], favourable=fa['savings_drought'] >= 0)}",
                unsafe_allow_html=True)

    st.markdown("**Transport costs comparison** (per day; "
                f"{fa['delivery_days_trucked']:,.0f} trucked days "
                f"[pavement+concrete] + {fa['dust_suppression_days']:,.0f} "
                "dust-suppression days)")
    c1, c2, c3 = st.columns(3)
    c1.metric("Potable transport / day", f"${fa['potable_transport_cost_per_day']:,.0f}")
    c2.metric("Recycled transport / day", f"${fa['recycled_transport_cost_per_day']:,.0f}")
    with c3:
        st.caption("Total cost difference (parentheses/red = recycled costs more)")
        st.markdown(accounting_amount(fa['total_cost_difference'],
                                       favourable=fa['total_cost_difference'] <= 0),
                    unsafe_allow_html=True)

    st.markdown("**Net position** (water savings minus transport cost difference)")
    c1, c2 = st.columns(2)
    with c1:
        st.caption(_net_position_line(net_normal, "normal"))
        st.markdown(f"Normal: {accounting_amount(net_normal, favourable=net_normal >= 0)}",
                    unsafe_allow_html=True)
    with c2:
        st.caption(_net_position_line(net_drought, "drought"))
        st.markdown(f"Drought: {accounting_amount(net_drought, favourable=net_drought >= 0)}",
                    unsafe_allow_html=True)

    if fa["verdict"] == "PROCEED":
        verdict_colour, verdict_text = COLOUR_SUCCESS, "PROCEED — recycled water is cost favourable."
    elif fa["recycled_total_cost"] < fa["potable_drought_total"]:
        verdict_colour, verdict_text = COLOUR_WARNING, (
            "CONDITIONAL — more expensive under normal conditions, but "
            "favourable under drought pricing.")
    else:
        verdict_colour, verdict_text = COLOUR_WARNING, (
            "CONDITIONAL — not cost favourable under any conditions modelled; "
            "may still proceed for sustainability reasons.")
    st.markdown(
        f'<div style="background:{verdict_colour};color:#fff;padding:10px 14px;'
        f'border-radius:10px;font-weight:800">{verdict_text}</div>', unsafe_allow_html=True)

    st.markdown("")
    if st.button("📈 Generate graph", key="financial_generate_graph"):
        st.session_state["financial_show_graph"] = True
    if st.session_state.get("financial_show_graph"):
        bc = B.recycled_distance_breakeven_curve(d)
        _render_breakeven_chart(bc)
        if bc["breakeven_distance_km"] is not None:
            st.caption(
                f"Break-even vs normal potable price: "
                f"**{bc['breakeven_distance_km']:,.1f} km** (recycled source "
                f"distance). Break-even vs drought price: "
                + (f"**{bc['breakeven_distance_drought_km']:,.1f} km**."
                   if bc["breakeven_distance_drought_km"] is not None else "n/a."))
        else:
            st.caption(
                "Recycled water's total cost never exceeds potable's within "
                "the distance range plotted, at the current transport "
                "assumptions.")
    else:
        st.caption("Click **Generate graph** to plot cost vs recycled-source "
                   "trucking distance.")


def _render_breakeven_chart(bc: dict):
    """Line chart of total project cost vs recycled-source trucking
    distance (potable_distance_km and every other input stay fixed while
    this sweeps recycled_distance_km — see
    backend.recycled_distance_breakeven_curve's docstring for why)."""
    curve = pd.DataFrame(bc["curve"]).melt(
        id_vars="distance_km",
        value_vars=["recycled", "potable", "potable_drought"],
        var_name="series", value_name="cost",
    )
    series_names = {
        "recycled": "Recycled (incl. trucking)",
        "potable": "Potable",
        "potable_drought": "Potable (drought)",
    }
    curve["series"] = curve["series"].map(series_names)

    BREAKEVEN_LABEL = "Break-even distance"
    # One shared colour/dash scale, covering both the three cost curves and
    # the break-even marker below, so layering them produces a single
    # combined legend instead of an unlabelled grey line the user has to
    # guess at.
    domain = [series_names["recycled"], series_names["potable"], series_names["potable_drought"],
              BREAKEVEN_LABEL]
    range_ = [COLOUR_SUCCESS, COLOUR_PRIMARY, COLOUR_WARNING, COLOUR_NEUTRAL]
    dash = [[1, 0], [1, 0], [6, 3], [4, 4]]

    lines = alt.Chart(curve).mark_line(strokeWidth=2.5).encode(
        x=alt.X("distance_km:Q", title="Recycled water trucking distance (km)"),
        y=alt.Y("cost:Q", title="Total project cost (AUD)", axis=alt.Axis(format="$,.0f")),
        color=alt.Color("series:N", title="Series", sort=domain,
                        scale=alt.Scale(domain=domain, range=range_)),
        strokeDash=alt.StrokeDash("series:N", sort=domain,
                                  scale=alt.Scale(domain=domain, range=dash), legend=None),
    )

    hover = alt.selection_point(fields=["distance_km"], nearest=True, on="mouseover", empty=False)
    hover_points = lines.mark_point(size=60, opacity=0).encode(
        opacity=alt.condition(hover, alt.value(1), alt.value(0)),
        tooltip=[
            alt.Tooltip("distance_km:Q", title="Distance (km)", format=",.1f"),
            alt.Tooltip("series:N", title="Series"),
            alt.Tooltip("cost:Q", title="Total cost", format="$,.0f"),
        ],
    ).add_params(hover)
    hover_rule = lines.mark_rule(color=COLOUR_NEUTRAL, strokeWidth=1).encode(
        opacity=alt.condition(hover, alt.value(0.6), alt.value(0)),
    ).transform_filter(hover)

    layers = [lines, hover_points, hover_rule]

    breakeven_rows = []
    if bc["breakeven_distance_km"] is not None and bc["breakeven_distance_km"] <= bc["max_distance_km"]:
        breakeven_rows.append({
            "distance_km": bc["breakeven_distance_km"],
            "label": f"vs potable: {bc['breakeven_distance_km']:,.1f} km",
        })
    if (bc["breakeven_distance_drought_km"] is not None
            and bc["breakeven_distance_drought_km"] <= bc["max_distance_km"]):
        breakeven_rows.append({
            "distance_km": bc["breakeven_distance_drought_km"],
            "label": f"vs drought price: {bc['breakeven_distance_drought_km']:,.1f} km",
        })
    if breakeven_rows:
        be_df = pd.DataFrame(breakeven_rows)
        be_df["series"] = BREAKEVEN_LABEL
        be_rules = alt.Chart(be_df).mark_rule(strokeWidth=1.5).encode(
            x="distance_km:Q",
            color=alt.Color("series:N", sort=domain, scale=alt.Scale(domain=domain, range=range_),
                            legend=None),
            strokeDash=alt.StrokeDash("series:N", sort=domain,
                                      scale=alt.Scale(domain=domain, range=dash), legend=None),
        )
        # Distance labels directly on the chart (exact km), on top of the
        # shared legend explaining what the grey dashed line itself means.
        be_labels = alt.Chart(be_df).mark_text(
            align="left", dx=6, dy=-6, color=COLOUR_NEUTRAL, fontWeight="bold", fontSize=11,
        ).encode(x="distance_km:Q", y=alt.value(12), text="label:N")
        layers += [be_rules, be_labels]

    # resolve_legend(color="shared") is required, not cosmetic: the
    # break-even rule layer only encodes x (a full-height vertical line),
    # and layering that with the x+y line chart makes Vega-Lite silently
    # drop the legend entirely under its default resolution — even though
    # every layer requests the same "Series" legend. Forcing it back to
    # "shared" is the documented workaround.
    chart = (alt.layer(*layers).properties(height=340)
             .configure_view(strokeWidth=0)
             .resolve_legend(color="shared"))
    st.altair_chart(chart, width="stretch")
