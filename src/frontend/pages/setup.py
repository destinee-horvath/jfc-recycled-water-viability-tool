"""
frontend/pages/setup.py
========================
Assessment setup page — project metadata + loading a previous assessment.
"""

import streamlit as st

import config as C
import backend as B

from ..state import reset_widget_state


def page_setup():
    st.header("Assessment setup")

    st.info("Before you start, it helps to have the following ready.")
    st.info("Not everything below is required to get started — every phase can be filled "
               "in, left blank, or revisited in any order at any time.")
    with st.expander("What you'll need", expanded=True):
        for item in C.TOOL_PREREQUISITES:
            st.markdown(f"- {item}")

    m = st.session_state.meta
    c1, c2 = st.columns(2)
    m["assessment_name"] = c1.text_input(
        "Project / assessment name", value=m.get("assessment_name", ""),
        placeholder="e.g. Pacific Hwy Subgrade", key="setup_assessment_name")
    m["assessed_by"] = c2.text_input(
        "Assessed by", value=m.get("assessed_by", ""),
        placeholder="Your name (audit trail)", key="setup_assessed_by")

    st.subheader("Load a previous assessment")
    c1, c2 = st.columns(2)
    saved = B.list_saved()
    with c1:
        pick = st.selectbox("From saved_assessments/", ["—"] + saved, key="setup_load_pick")
        if pick != "—" and st.button("Load selected", width="stretch"):
            _apply_record(B.load_assessment_file(pick))
            st.success(f"Loaded {pick}")
            st.rerun()
    with c2:
        up = st.file_uploader("…or upload a saved CSV", type=["csv"])
        if up is not None and st.button("Load uploaded", width="stretch"):
            _apply_record(B.load_assessment_bytes(up.read()))
            st.success("Loaded uploaded assessment")
            st.rerun()


def _apply_record(rec):
    inputs, meta = B.record_to_inputs(rec)
    base = {p["id"]: {} for p in C.PHASES}
    base.update(inputs)
    reset_widget_state()
    st.session_state.inputs = base
    st.session_state.meta = {"assessment_name": meta.get("assessment_name", ""),
                             "assessed_by": meta.get("assessed_by", "")}
