"""
frontend/pages/p5_soil_conditions.py
=========================
PHASE 5 — Soil & Site Conditions

Collects USCS soil classification and pavement-layer data for three
independent, opt-in layers (subgrade, sub-base, base) and stores it in
st.session_state["soil_to_financial"] as one-way default values for the
Financial Feasibility phase's pavement-profile inputs (information entry
only — no pass/fail logic). Also collects the recycled water source's
SAR/EC for the SAR/EC structural-stability screen in
backend/phases/p5_soil_conditions.py.
"""

import streamlit as st

import config as C

from ..state import gi, render_phase_actions, current_results
from ..components import measured_table, value_table, render_phase_result
from ..refdata import PHASE_BY_ID

_CATEGORIES = list(C.USCS_SOIL_TABLE.keys())


def _uscs_layer_section(prefix: str, default_thickness: float):
    """Soil category -> USCS class -> reference table -> editable inputs,
    for a layer that requires USCS classification (subgrade / sub-base)."""
    d = gi("soil_conditions")
    cat_key = f"{prefix}_category"
    class_key = f"{prefix}_uscs_class"
    omc_key = f"{prefix}_omc_pct"
    mc_key = f"{prefix}_mc_pct"
    density_key = f"{prefix}_density_kN_m3"
    thickness_key = f"{prefix}_thickness_m"

    cat_widget_key = f"soil_conditions_{cat_key}"
    st.session_state.setdefault(cat_widget_key, _CATEGORIES[0])
    d[cat_key] = st.selectbox(
        "Soil category", _CATEGORIES,
        index=_CATEGORIES.index(st.session_state[cat_widget_key]),
        key=cat_widget_key)

    class_options = list(C.USCS_SOIL_TABLE[d[cat_key]].keys())
    labels = [f"{code} — {C.USCS_SOIL_TABLE[d[cat_key]][code]['description']}"
              for code in class_options]
    # Keying on the category means switching category always gets a fresh
    # widget (its own independent session-state slot) rather than trying to
    # carry over a selection that may not exist in the new option list.
    class_widget_key = f"soil_conditions_{class_key}__{d[cat_key]}"
    st.session_state.setdefault(class_widget_key, labels[0])
    chosen_label = st.selectbox(
        "USCS Soil Classification", labels,
        index=labels.index(st.session_state[class_widget_key]),
        help=C.SOIL_TABLE_CITATION, key=class_widget_key)
    d[class_key] = class_options[labels.index(chosen_label)]

    data = C.USCS_SOIL_TABLE[d[cat_key]][d[class_key]]
    lo, hi = data["dry_unit_weight_kN_m3_range"]
    omc_lo, omc_hi = data["omc_range"]
    # Centred table — st.markdown's own pipe-table syntax always renders
    # left-aligned with no centring hook, so build the HTML table directly
    # inside a centred flex container instead.
    st.markdown(
        '<div style="display:flex;justify-content:center">'
        '<table>'
        '<tr><th>Property</th><th>Range</th><th>Typical (mid)</th></tr>'
        f'<tr><td>Dry unit weight (kN/m³)</td><td>{lo:.1f} – {hi:.1f}</td>'
        f'<td>{data["dry_unit_weight_kN_m3_mid"]:.1f}</td></tr>'
        f'<tr><td>Optimum Moisture Content (%)</td><td>{omc_lo:g} – {omc_hi:g}</td>'
        f'<td>{data["omc_mid"]:g}</td></tr>'
        '</table>'
        '</div>',
        unsafe_allow_html=True)
    st.caption(f"Source: {C.SOIL_TABLE_REF}")

    # Composite keys (category + class) so a fresh class gets the table's
    # midpoint as its default, while re-selecting a previously-visited class
    # restores whatever the engineer last entered for it.
    omc_widget_key = f"soil_conditions_{omc_key}__{d[cat_key]}__{d[class_key]}"
    density_widget_key = f"soil_conditions_{density_key}__{d[cat_key]}__{d[class_key]}"
    thickness_widget_key = f"soil_conditions_{thickness_key}"
    st.session_state.setdefault(omc_widget_key, data["omc_mid"])
    st.session_state.setdefault(density_widget_key, data["dry_unit_weight_kN_m3_mid"])
    st.session_state.setdefault(thickness_widget_key, default_thickness)

    # One combined Parameter/Value table for this layer's compulsory
    # fields (always hold a value), and one Measured/Not measured table
    # for MC, which genuinely may not have been tested.
    value_table([
        (omc_key, "Optimum Moisture Content — OMC (%)",
         f"Pre-filled from typical value for {d[class_key]}. Adjust if "
         "site-specific data is available.",
         omc_widget_key, 1.0, 50.0),
        (density_key, "Dry unit weight (kN/m³)",
         f"Pre-filled from typical value for {d[class_key]}. Adjust if "
         "site-specific data is available.",
         density_widget_key, 5.0, 30.0),
        (thickness_key, "Layer thickness (m)", None, thickness_widget_key, 0.05, 2.0),
    ], "soil_conditions")
    density_kg = d[density_key] * C.KN_M3_TO_KG_M3
    st.caption(
        f"Note: kN/m³ is displayed to match the reference table. The "
        f"equivalent value in kg/m³ ({density_kg:,.1f} kg/m³) is used in "
        "the financial calculation.")

    measured_table([(
        mc_key, "Current Moisture Content — MC (%) (optional)",
        "Enter if known from site testing. Used in financial volume calculation.",
    )], "soil_conditions", show_header=False)


def _base_layer_section():
    """Base layer: no USCS classification, a single OMC default."""
    d = gi("soil_conditions")
    omc_key = "base_omc_pct"
    mc_key = "base_mc_pct"
    density_key = "base_density_kN_m3"
    thickness_key = "base_thickness_m"

    st.info(
        f"Base layer OMC is typically {C.BASE_LAYER_DEFAULTS['omc_range'][0]:g}"
        f"–{C.BASE_LAYER_DEFAULTS['omc_range'][1]:g}% per standard practice. "
        f"The midpoint value ({C.BASE_LAYER_DEFAULTS['omc_mid']:g}%) is used "
        "as the default. Adjust if site-specific data is available.")

    omc_widget_key = f"soil_conditions_{omc_key}"
    thickness_widget_key = f"soil_conditions_{thickness_key}"
    st.session_state.setdefault(omc_widget_key, C.BASE_LAYER_DEFAULTS["omc_mid"])
    st.session_state.setdefault(thickness_widget_key, 0.2)

    # One combined Parameter/Value table for the base layer's compulsory
    # fields, and one Measured/Not measured table for MC and density,
    # which genuinely may not have been tested (no USCS default to fall
    # back on for base).
    value_table([
        (omc_key, "Optimum Moisture Content — OMC (%)", None, omc_widget_key, 1.0, 50.0),
        (thickness_key, "Layer thickness (m)", None, thickness_widget_key, 0.05, 2.0),
    ], "soil_conditions")

    measured_table([
        (mc_key, "Current Moisture Content — MC (%) (optional)",
         "Enter if known from site testing. Used in financial volume calculation."),
        (density_key, "Dry unit weight (kN/m³)",
         "Enter if known. Used in financial calculation. Typical base course: 18–22 kN/m³"),
    ], "soil_conditions", show_header=False)
    if d.get(density_key) is not None:
        density_kg = d[density_key] * C.KN_M3_TO_KG_M3
        st.caption(
            f"Note: kN/m³ is displayed to match the reference table. The "
            f"equivalent value in kg/m³ ({density_kg:,.1f} kg/m³) is used in "
            "the financial calculation.")


def _build_soil_to_financial(d: dict):
    def layer_payload(prefix, has_uscs):
        active = bool(d.get(f"{prefix}_active", True))
        density_kN = d.get(f"{prefix}_density_kN_m3")
        payload = {
            "active": active,
            "omc_pct": d.get(f"{prefix}_omc_pct"),
            "mc_pct": d.get(f"{prefix}_mc_pct"),
            "density_kN_m3": density_kN,
            "density_kg_m3": density_kN * C.KN_M3_TO_KG_M3 if density_kN is not None else None,
            "thickness_m": d.get(f"{prefix}_thickness_m"),
        }
        if has_uscs:
            category = d.get(f"{prefix}_category")
            uscs_class = d.get(f"{prefix}_uscs_class")
            payload["uscs_class"] = uscs_class
            payload["description"] = (
                C.USCS_SOIL_TABLE[category][uscs_class]["description"]
                if category and uscs_class else None)
        else:
            payload["uscs_class"] = None
            payload["description"] = None
        return payload

    st.session_state["soil_to_financial"] = {
        "subgrade": layer_payload("subgrade", has_uscs=True),
        "subbase": layer_payload("subbase", has_uscs=True),
        "base": layer_payload("base", has_uscs=False),
    }


def page_soil_conditions(results):
    g = PHASE_BY_ID["soil_conditions"]
    st.header(g["label"], help=g["desc"])
    d = gi("soil_conditions")

    st.subheader(
        "Recycled water — SAR/EC structural stability",
        help="Screens the recycled water source against the NATURAL "
             "subgrade soil (not the manufactured pavement material below) "
             "for the risk of soil-structure degradation — "
             "dispersion/slaking from a high Sodium Adsorption Ratio (SAR) "
             "at low Electrical Conductivity (EC).")

    measured_table([
        ("soil_water_sar", "Sodium Adsorption Ratio (SAR) of recycled water source",
         "From a water quality lab report for the recycled water source."),
        ("soil_water_ec_dsm", "Electrical Conductivity (EC) of recycled water source (dS/m)",
         "Specific conductance in dS/m (1 dS/m = 1000 µS/cm) — check the lab "
         "report's units before entering."),
    ], "soil_conditions")

    st.divider()

    c1, c2, c3 = st.columns(3)
    with c1:
        d["subgrade_active"] = st.checkbox(
            "Subgrade (Soil)", value=bool(d.get("subgrade_active", True)),
            key="soil_conditions_subgrade_active")
    with c2:
        d["subbase_active"] = st.checkbox(
            "Sub-base", value=bool(d.get("subbase_active", True)),
            key="soil_conditions_subbase_active")
    with c3:
        d["base_active"] = st.checkbox(
            "Base", value=bool(d.get("base_active", True)),
            key="soil_conditions_base_active")

    if d["subgrade_active"]:
        st.subheader("Subgrade")
        _uscs_layer_section("subgrade", default_thickness=0.3)
        st.divider()

    if d["subbase_active"]:
        st.subheader("Sub-base")
        _uscs_layer_section("subbase", default_thickness=0.2)
        st.divider()

    if d["base_active"]:
        st.subheader("Base")
        _base_layer_section()

    _build_soil_to_financial(d)

    render_phase_result(current_results()["soil_conditions"])
    render_phase_actions("soil_conditions")
