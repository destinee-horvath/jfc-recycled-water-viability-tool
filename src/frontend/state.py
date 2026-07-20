"""
frontend/state.py
==================
Session-state management: initial state, per-phase input dicts, running the
assessment, and the Next/Save actions shown at the bottom of each phase page.
"""

from datetime import datetime

import streamlit as st

import config as C
import backend as B


def init_state():
    if "inputs" not in st.session_state:
        st.session_state.inputs = {p["id"]: {} for p in C.PHASES}
    if "meta" not in st.session_state:
        st.session_state.meta = {"assessment_name": "", "assessed_by": ""}
    if "page" not in st.session_state:
        st.session_state.page = "Setup"
    if "completed_phases" not in st.session_state:
        st.session_state.completed_phases = set()


def gi(phase_id):
    return st.session_state.inputs.setdefault(phase_id, {})


def reset_widget_state():
    """
    Clear every per-widget session-state key (all but the core ``inputs``/
    ``meta``/``page``/``completed_phases``). A keyed widget ignores a fresh
    ``value=`` once Streamlit has recorded state for that key, so this must
    run before reassigning ``inputs``/``meta`` on reset or after a load,
    followed by ``st.rerun()`` — otherwise widgets re-render stale values.
    """
    keep = {"inputs", "meta", "page", "completed_phases"}
    for key in list(st.session_state.keys()):
        if key not in keep:
            del st.session_state[key]


def current_results():
    return B.run_assessment(st.session_state.inputs)


def _next_phase_label(phase_id: str) -> str:
    try:
        idx = next(i for i, phase in enumerate(C.PHASES) if phase["id"] == phase_id)
    except StopIteration:
        return "Summary"
    return C.PHASES[idx + 1]["label"] if idx + 1 < len(C.PHASES) else "Summary"


def _save_current_progress():
    meta = dict(st.session_state.meta)
    meta.setdefault("assessment_name", "progress")
    meta["saved_at"] = datetime.now().isoformat(timespec="seconds")
    rec = B.build_record(st.session_state.inputs, meta)
    fname = B.suggest_filename(meta.get("assessment_name", "progress"))
    path = B.save_assessment(rec, fname)
    st.session_state["_save_toast"] = f"Saved to {path}"


def render_phase_actions(phase_id: str):
    completed = phase_id in st.session_state.completed_phases
    if completed:
        st.markdown('<div class="phase-complete">✓ Phase complete</div>', unsafe_allow_html=True)
    else:
        st.caption("Complete this phase and continue.")

    st.markdown('<div class="phase-actions">', unsafe_allow_html=True)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Next", width="stretch"):
            st.session_state.completed_phases.add(phase_id)
            st.session_state.page = _next_phase_label(phase_id)
            st.rerun()
    with c2:
        if st.button("Save current progress", width="stretch"):
            st.session_state.completed_phases.add(phase_id)
            _save_current_progress()
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
