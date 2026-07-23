"""
frontend/pages/p1_supplier_approval.py
=========================
PHASE 1 — Supplier & Dual Approval
"""

import streamlit as st

import config as C

from ..state import gi, render_phase_actions, current_results
from ..components import render_phase_result


def page_supplier_approval(results):
    g = C.PHASE_BY_ID["supplier_approval"]
    st.header(g["label"], help=g["desc"])
    d = gi("supplier_approval")

    d["operated_without_approval"] = st.radio(
        "⚠ Has this scheme operated historically WITHOUT approval?",
        ["No", "Yes"],
        index=1 if d.get("operated_without_approval") else 0,
        horizontal=True,
        help="Auto-reject — no retrospective approval is possible.",
        key="supplier_approval_operated_without_approval") == "Yes"

    if d["operated_without_approval"]:
        st.error("No retrospective approval possible — assessment cannot proceed.")
        render_phase_result(current_results()["supplier_approval"])
        render_phase_actions("supplier_approval")
        return

    d["water_source"] = st.selectbox(
        "Water source", C.WATER_SOURCES,
        index=C.WATER_SOURCES.index(d.get("water_source", C.WATER_SOURCES[0])),
        key="supplier_approval_water_source")

    st.subheader("Supplier-side approval")

    def _approval_radio(label, field, help=None):
        try:
            idx = C.APPROVAL_STATES.index(d.get(field, C.APPROVAL_STATES[-1]))
        except ValueError:
            idx = len(C.APPROVAL_STATES) - 1
        d[field] = st.radio(label, C.APPROVAL_STATES, index=idx, horizontal=True,
                            help=help, key=f"supplier_approval_{field}")

    if d["water_source"] == "Stormwater":
        st.info("Stormwater doesn't need the standard s.60/s.292/s.68 approval — confirm below instead.")
        d["sydney_hunter_area"] = st.checkbox(
            "Site is in a Sydney Water or Hunter Water operational area",
            value=bool(d.get("sydney_hunter_area")),
            help=C.SYDNEY_HUNTER_REF, key="supplier_approval_sydney_hunter_area")
        if not d["sydney_hunter_area"]:
            _approval_radio(
                "Has the stormwater harvesting scheme received approval from the local council, "
                "development consent from the planning authority, and water management approval "
                "from the relevant authority?",
                "stormwater_approvals_held", help=C.STORMWATER_APPROVAL_REF)
    else:
        d["supplier_authority"] = st.selectbox(
            "Supplier / scheme type", C.SUPPLIER_AUTHORITIES,
            index=C.SUPPLIER_AUTHORITIES.index(
                d.get("supplier_authority", C.SUPPLIER_AUTHORITIES[0])),
            key="supplier_approval_supplier_authority")
        st.markdown(f"↳ **Approval route:** {C.SUPPLIER_APPROVAL_REFS[d['supplier_authority']]}",
                    help=f"{C.SUPPLIER_SECTION_TOOLTIPS[d['supplier_authority']]}\n\n"
                         f"{C.SUPPLIER_APPROVAL_PLAIN[d['supplier_authority']]}")

        if d["supplier_authority"] == "Council-run scheme":
            _approval_radio("Does the council hold ministerial approval to operate its water treatment "
                                "works and supply recycled water to third parties? "
                                "(Local Government Act 1993, s.60(b) & s.60(c))",
                                "council_approval_held")
        else:
            _approval_radio(
                "Does the water supply authority hold the required ministerial approval? "
                "Authorities such as Sydney Water or Hunter Water must hold approval to "
                "construct, maintain, and operate their water treatment and supply works "
                "under the Water Management Act 2000, s.292(1)(a)",
                "authority_approval_held")
        st.caption(C.MINISTERIAL_APPROVAL_LOOKUP_NOTE)

        if d["water_source"] in ("Treated effluent", "Other"):
            d["discharge_only"] = st.checkbox(
                "Has a discharge licence, but NOT approved for this use",
                value=bool(d.get("discharge_only")),
                help="A discharge licence is not permission to use the water.",
                key="supplier_approval_discharge_only")

    # --- EPL section (informational — does not affect the pass/reject gates) -
    st.caption("Environment Protection Licence (EPL)",
               help=f"{C.EPL_SECTION_EXPLANATION} {C.TOOLTIP_EPL}")
    st.caption(C.EPL_REGISTER_NOTE)

    try:
        epl_index = C.EPL_STATES.index(d.get("epl_status", C.EPL_STATES[-1]))
    except ValueError:
        epl_index = len(C.EPL_STATES) - 1
    d["epl_status"] = st.radio(
        "Does the supplier hold a current EPL?",
        C.EPL_STATES, index=epl_index, key="supplier_approval_epl_status")

    if d["epl_status"] == "Yes":
        d["epl_number"] = st.text_input(
            "EPL number (optional, for record-keeping)",
            value=d.get("epl_number", ""), key="supplier_approval_epl_number")
        d["epl_conditions_permit_supply"] = st.checkbox(
            "EPL conditions permit supply for this roadworks use",
            value=bool(d.get("epl_conditions_permit_supply")),
            key="supplier_approval_epl_conditions_permit_supply")
    elif d["epl_status"] == "No":
        st.caption("ℹ", help=C.EPL_NO_NOTE)
    else:
        st.warning(C.EPL_UNCONFIRMED_NOTE)

    st.subheader("Dual approval — your permission to use this water",
                 help=f"{C.TOOLTIP_DUAL_APPROVAL} {C.DUAL_APPROVAL_PLAIN_NOTE}")
    try:
        # Falls back to the safe default if a legacy saved value
        # (e.g. the retired "Unconfirmed" option) is no longer a valid choice.
        user_state_index = C.USER_APPROVAL_STATES.index(
            d.get("user_approval_state", C.USER_APPROVAL_STATES[-1]))
    except ValueError:
        user_state_index = len(C.USER_APPROVAL_STATES) - 1
    d["user_approval_state"] = st.radio(
        "Does your EPL / development consent permit this use?", C.USER_APPROVAL_STATES,
        index=user_state_index,
        key="supplier_approval_user_approval_state")

    render_phase_result(current_results()["supplier_approval"])
    render_phase_actions("supplier_approval")
