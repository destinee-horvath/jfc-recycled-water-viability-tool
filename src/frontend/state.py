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


def _current_progress_record():
    meta = dict(st.session_state.meta)
    meta.setdefault("assessment_name", "progress")
    meta["saved_at"] = datetime.now().isoformat(timespec="seconds")
    rec = B.build_record(st.session_state.inputs, meta)
    fname = B.suggest_filename(meta.get("assessment_name", "progress"))
    return rec, fname


def _save_current_progress():
    """Writes to the SERVER's own disk (config.SAVE_DIR) — useful when this
    app is run locally or self-hosted (the server IS the user's machine),
    but on a remote deployment (e.g. Streamlit Community Cloud) that disk
    belongs to the host, not the visitor, and is wiped on restart. Use the
    download button below to get a copy onto the visitor's own computer
    regardless of where the app is hosted."""
    rec, fname = _current_progress_record()
    path = B.save_assessment(rec, fname)
    st.session_state["_save_toast"] = f"Saved to {path}"


def autosave_progress():
    """Silently writes current progress to saved_assessments/ on every
    rerun — called once from app.main() after the active page has updated
    st.session_state.inputs, so it's always saving this run's latest
    values, not last run's. Skips a completely empty session (nothing
    entered anywhere yet) so a fresh visit doesn't immediately create a
    junk file. Deliberately silent (no toast) — the explicit "Save current
    progress" button above remains the one that confirms itself to the
    user; autosave is a safety net, not an action they took.

    Same server-disk caveat as _save_current_progress(): this protects
    against an accidental refresh or closed tab, not against the server's
    own disk being wiped (e.g. a Streamlit Community Cloud restart) — see
    the download button and warning in render_phase_actions() below.
    """
    if not any(st.session_state.inputs.values()):
        return
    rec, fname = _current_progress_record()
    B.save_assessment(rec, fname)


def render_phase_actions(phase_id: str):
    completed = phase_id in st.session_state.completed_phases
    if completed:
        st.markdown('<div class="phase-complete">✓ Phase complete</div>', unsafe_allow_html=True)
    else:
        st.caption("Complete this phase and continue.")

    st.markdown('<div class="phase-actions">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        if st.button("Next", width="stretch"):
            st.session_state.completed_phases.add(phase_id)
            st.session_state.page = _next_phase_label(phase_id)
            st.rerun()
    with c2:
        if st.button("Save current progress", width="stretch",
                      help="Saves to this app's own server — persists between "
                           "visits when self-hosted, but not on a remote "
                           "deployment (e.g. Streamlit Community Cloud), "
                           "where the server disk is wiped on restart. Use "
                           "Download to keep a copy on your own computer."):
            st.session_state.completed_phases.add(phase_id)
            _save_current_progress()
            st.rerun()
    with c3:
        rec, fname = _current_progress_record()
        if st.download_button(
                "⇩ Download progress (.csv)", data=B.record_to_csv_bytes(rec),
                file_name=fname, mime="text/csv", width="stretch",
                help="Downloads to your own computer (your browser's "
                     "downloads folder) — works the same regardless of "
                     "where this app is hosted."):
            st.session_state.completed_phases.add(phase_id)
    st.caption("⚠ Your progress is auto-saved to this app's own server as you go, but "
               "that storage isn't guaranteed to survive a server reset or redeploy — "
               "click **⇩ Download progress** regularly to keep a copy on your own computer.")
    st.markdown('</div>', unsafe_allow_html=True)
