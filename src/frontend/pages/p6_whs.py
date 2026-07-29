"""
frontend/pages/p6_whs.py
=========================
PHASE 6 — Worker Health & Safety
"""

import streamlit as st

import config as C

from ..state import gi, render_phase_actions, current_results
from ..components import render_phase_result
from ..refdata import PHASE_BY_ID


def page_whs(results):
    g = PHASE_BY_ID["whs"]
    st.header(g["label"], help=g["desc"])
    d = gi("whs")

    st.info("This phase constitutes a risk assessment for worker and public "
            "exposure to recycled water on site. All checks below form "
            "part of that risk assessment process. (WHS Act 2011 NSW "
            "s.19; WHS Regulation 2017 NSW)")
    st.info("No hard reject at this phase — WHS shortfalls are remediable "
            "(CONDITIONAL, action-before-works). Strict liability offence — "
            "no intention needed to prove guilt.")

    st.subheader("Application method & contact risk", help=C.WHS_REF)

    _current_method = st.session_state.get(
        "whs_application_method", d.get("application_method", C.APPLICATION_METHODS[0]))
    d["application_method"] = st.radio(
        "How is the water applied?", C.APPLICATION_METHODS,
        index=C.APPLICATION_METHODS.index(
            d.get("application_method", C.APPLICATION_METHODS[0])),
        help=C.WHS_METHOD_NOTES.get(_current_method),
        key="whs_application_method")
    if d["application_method"] == "Sprayed (higher contact)":
        d["wind_weather_checked"] = st.checkbox(
            "Wind conditions and weather have been checked before application",
            value=bool(d.get("wind_weather_checked")),
            help=C.WHS_SPRAY_WEATHER_REF, key="whs_wind_weather_checked")

    _CONTACT_RISK_HELP = {
        "Workers only": "Moderate risk — ensure PPE and SWMS cover all direct-contact scenarios.",
        "None expected": C.WHS_IRRIGATION_NOTE,
    }
    _current_contact_risk = st.session_state.get(
        "whs_contact_risk", d.get("contact_risk", C.CONTACT_RISK_LEVELS[0]))
    d["contact_risk"] = st.radio(
        "Will workers or the public contact the treated area during/after application?",
        C.CONTACT_RISK_LEVELS,
        index=C.CONTACT_RISK_LEVELS.index(
            d.get("contact_risk", C.CONTACT_RISK_LEVELS[0])),
        help=_CONTACT_RISK_HELP.get(_current_contact_risk),
        key="whs_contact_risk")
    # "Workers and public" gets a standing warning box, not just a hover
    # tooltip — kept visible rather than folded into help= above.
    if d["contact_risk"] not in ("Workers only", "None expected"):
        st.warning(f"{C.WHS_TREATMENT_NOTE}\n\n{C.NSW_HEALTH_NOTE}")

    st.subheader("WHS checklist")
    st.warning(
        "Field note: Workers commonly assess material moisture content by " 
        "squeezing material in hand and observing texture and behaviour. "
        "Where the water source is unknown or recycled, do "
        "not handle material without the correct PPE — doing so risks a "
        "WHS breach. Report any uncertainty about water source to the site "
        "supervisor.")
    for key, label in C.WHS_CHECKS:
        d[key] = st.checkbox(label, value=bool(d.get(key)), key=f"whs_{key}")

    render_phase_result(current_results()["whs"])
    render_phase_actions("whs")
