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


def _load_side(label: str, col, saved: list[str], key_prefix: str):
    """One side's picker: saved_assessments/ dropdown or uploaded CSV.
    Upload takes priority when present (mirrors setup.py's pattern)."""
    with col:
        pick = st.selectbox(f"{label} — from saved_assessments/", ["—"] + saved,
                             key=f"{key_prefix}_pick")
        up = st.file_uploader(f"{label} — …or upload a saved CSV", type=["csv"],
                               key=f"{key_prefix}_upload")
    if up is not None:
        return B.load_assessment_bytes(up.read()), up.name
    if pick != "—":
        return B.load_assessment_file(pick), pick
    return None, None


def page_compare():
    st.header("Compare two assessments")
    st.caption("Load two saved water sources side by side for the same project — "
               "pick from the server list, or upload a CSV directly.")
    saved = B.list_saved()
    if not saved:
        st.info("No saved assessments on the server yet — upload a CSV directly below instead.")
    c1, c2 = st.columns(2)
    a_rec, a_fallback_name = _load_side("Assessment A", c1, saved, "cmpA")
    b_rec, b_fallback_name = _load_side("Assessment B", c2, saved, "cmpB")

    for col, rec, fallback_name in ((c1, a_rec, a_fallback_name), (c2, b_rec, b_fallback_name)):
        if rec is None:
            continue
        inputs, meta = B.record_to_inputs(rec)
        res = B.run_assessment(inputs)
        readiness = B.readiness_summary(res)
        with col:
            st.markdown(f"**{meta.get('assessment_name') or fallback_name}**")
            st.caption(f"By {meta.get('assessed_by','—')} · {meta.get('saved_at','')}")
            st.caption(f"{len(readiness['blocking'])} blocking · "
                      f"{len(readiness['pending'])} pending · "
                      f"{len(readiness['confirmed'])} confirmed")
            for phase in C.PHASES:
                r = res[phase["id"]]
                st.markdown(
                    f'{phase["label"]} · {badge(r.state)}',
                    unsafe_allow_html=True)
