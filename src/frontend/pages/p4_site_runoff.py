"""
frontend/pages/p4_site_runoff.py
=========================
PHASE 4 — Site Runoff & EPL Risk
"""

import streamlit as st

import config as C

from ..state import gi, render_phase_actions, current_results
from ..components import measured_table, render_phase_result


def page_site_runoff(results):
    g = C.PHASE_BY_ID["site_runoff"]
    st.header(g["label"], help=g["desc"])
    d = gi("site_runoff")

    st.subheader("Scheduled-activity threshold (Sch 1, Cl 35)")
    d["involves_extraction_or_processing"] = st.checkbox(
        "Does the project involve extraction, or on-site processing "
        "(crushing, grinding, or separating), of materials for road "
        "construction?",
        value=bool(d.get("involves_extraction_or_processing", False)),
        help="Schedule 1 Clause 35 applies to extraction and on-site "
             "processing (crushing, grinding, or separating) of materials "
             "for road construction. It does NOT apply to onsite concrete "
             "batching, compacting road base, general earthworks, or "
             "maintenance activities.",
        key="site_runoff_involves_extraction_or_processing")
    if d["involves_extraction_or_processing"]:
        d["in_regulated_area"] = st.checkbox(
            "Site is in a regulated area",
            value=bool(d.get("in_regulated_area")), key="site_runoff_in_regulated_area")
        thr = (C.SCH1_CL35_THRESHOLD_REGULATED if d["in_regulated_area"]
               else C.SCH1_CL35_THRESHOLD_ELSEWHERE)
        d["project_tonnes"] = st.number_input(
            f"Material moved (t) — threshold {thr:,}", min_value=0.0,
            value=float(d.get("project_tonnes") or 0.0),
            key="site_runoff_project_tonnes")

    st.subheader("EPL")
    d["epl_in_place"] = st.checkbox("EPL in place", value=bool(d.get("epl_in_place")),
                                    key="site_runoff_epl_in_place")
    d["epl_covers_recycled"] = st.checkbox(
        "EPL covers recycled-water use",
        value=bool(d.get("epl_covers_recycled")), key="site_runoff_epl_covers_recycled")
    if d["epl_in_place"]:
        d["pirmp_in_place"] = st.checkbox(
            "PIRMP in place (mandatory for EPL holders, s.153A)",
            value=bool(d.get("pirmp_in_place")), key="site_runoff_pirmp_in_place")

    st.subheader("Runoff & receiving environment")
    measured_table([(
        "distance_to_waterway_m",
        "Distance to nearest waterway / drain / outlet (m)",
        "Negative distances are not allowed.",
    )], "site_runoff")

    d["slope_toward_waterway"] = st.checkbox(
        "Site slope / drainage directs runoff toward waters",
        value=bool(d.get("slope_toward_waterway")), key="site_runoff_slope_toward_waterway")

    d["sensitive_environment"] = st.selectbox(
        "Sensitive receiving environment", C.SENSITIVE_ENVIRONMENTS,
        index=C.SENSITIVE_ENVIRONMENTS.index(
            d.get("sensitive_environment", C.SENSITIVE_ENVIRONMENTS[0])),
        key="site_runoff_sensitive_environment")

    d["containment_documented"] = st.checkbox(
        "Is there a risk of ponding or site overflow, and are containment & "
        "emergency response procedures documented?",
        value=bool(d.get("containment_documented")),
        help="Regulators check this at approval. Fines apply for non-compliant discharge (s.123).",
        key="site_runoff_containment_documented")

    render_phase_result(current_results()["site_runoff"])
    render_phase_actions("site_runoff")
