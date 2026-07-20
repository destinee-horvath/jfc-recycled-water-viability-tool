"""
frontend/pages/compare.py
==========================
Side-by-side phase-outcome comparison of two saved assessments. No headline
verdict/score by design — just the per-phase/per-check states.
"""

import streamlit as st

import config as C
import backend as B

from ..theme import badge


def page_compare():
    st.header("Compare two assessments")
    st.caption("Load two saved water sources side by side for the same project.")
    saved = B.list_saved()
    if len(saved) < 1:
        st.info("No saved assessments yet. Save one from the Summary page first.")
        return
    c1, c2 = st.columns(2)
    a = c1.selectbox("Assessment A", ["—"] + saved, key="cmpA")
    b = c2.selectbox("Assessment B", ["—"] + saved, key="cmpB")
    for col, pick in ((c1, a), (c2, b)):
        if pick == "—":
            continue
        rec = B.load_assessment_file(pick)
        inputs, meta = B.record_to_inputs(rec)
        res = B.run_assessment(inputs)
        readiness = B.readiness_summary(res)
        with col:
            st.markdown(f"**{meta.get('assessment_name') or pick}**")
            st.caption(f"By {meta.get('assessed_by','—')} · {meta.get('saved_at','')}")
            st.caption(f"{len(readiness['blocking'])} blocking · "
                      f"{len(readiness['pending'])} pending · "
                      f"{len(readiness['confirmed'])} confirmed")
            for phase in C.PHASES:
                r = res[phase["id"]]
                st.markdown(
                    f'{phase["label"]} · {badge(r.state)}',
                    unsafe_allow_html=True)
