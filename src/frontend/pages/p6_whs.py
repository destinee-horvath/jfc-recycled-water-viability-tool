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
    d["application_method"] = st.radio(
        "How is the water applied?", C.APPLICATION_METHODS,
        index=C.APPLICATION_METHODS.index(
            d.get("application_method", C.APPLICATION_METHODS[0])),
        key="whs_application_method")
    if d["application_method"] == "Sprayed (higher contact)":
        d["wind_weather_checked"] = st.checkbox(
            "Wind conditions and weather have been checked before application",
            value=bool(d.get("wind_weather_checked")),
            help=C.WHS_SPRAY_WEATHER_REF, key="whs_wind_weather_checked")
    else:
        st.caption("ℹ", help=C.WHS_METHOD_NOTES[d["application_method"]])

    d["contact_risk"] = st.radio(
        "Will workers or the public contact the treated area during/after application?",
        C.CONTACT_RISK_LEVELS,
        index=C.CONTACT_RISK_LEVELS.index(
            d.get("contact_risk", C.CONTACT_RISK_LEVELS[0])),
        key="whs_contact_risk")
    if d["contact_risk"] == "Workers only":
        st.caption("ℹ", help="Moderate risk — ensure PPE and SWMS cover all direct-contact scenarios.")
    elif d["contact_risk"] != "None expected":
        st.warning(f"{C.WHS_TREATMENT_NOTE}\n\n{C.NSW_HEALTH_NOTE}")
    else:
        st.caption("ℹ", help=C.WHS_IRRIGATION_NOTE)

    st.subheader("WHS checklist")
    st.info(
        "Field note: Workers commonly assess material moisture content by "
        "squeezing material in hand and observing texture and behaviour. "
        "Where recycled water is used, the material may feel or behave "
        "differently compared to potable water. Ensure workers are briefed "
        "on this and that any unusual observations are reported to the "
        "site supervisor.")
    for key, label in C.WHS_CHECKS:
        d[key] = st.checkbox(label, value=bool(d.get(key)), key=f"whs_{key}")

    render_phase_result(current_results()["whs"])
    render_phase_actions("whs")
