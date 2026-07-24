"""
frontend/app.py
================
Streamlit UI entry point. Wires together session state, styling, the
sidebar, and page routing. NO decision logic lives here — see backend/ for
the phase rules.
"""

from pathlib import Path

import streamlit as st

import config as C
import backend as B

from .styles import inject_css
from .state import init_state, current_results, reset_widget_state, autosave_progress
from .components import progress_bar
from .refdata import get_reference_data, PHASE_BY_ID
from .theme import badge
from .pages import PAGE_FUNCS, page_setup, page_summary, page_compare, page_save_export

# Anchored to this file's own location, not the process's working directory
# — Streamlit Cloud does not guarantee the working directory is src/, so a
# plain "frontend/images/..." string resolves incorrectly there even though
# it happens to work locally when the app is launched from inside src/.
IMAGES_DIR = Path(__file__).parent / "images"

st.set_page_config(
    page_title=C.APP_TITLE,
    page_icon="◧",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _nav_button(label):
    is_active = (st.session_state.page == label)
    if st.button(label, key=f"nav_{label}", type="primary" if is_active else "secondary",
                 width="stretch"):
        st.session_state.page = label
        st.rerun()


def _section_for_phase(phase_id):
    for section in C.PHASE_SECTIONS:
        if phase_id in section["phases"]:
            return section
    return None


def _section_banner_html(section, results):
    member_results = [results[pid] for pid in section["phases"]]
    state = B.section_rollup(member_results)
    return (
        f'<div style="background:{C.COLOUR_PRIMARY};color:#fff;padding:14px 18px;'
        f'border-radius:10px;margin-bottom:14px;display:flex;justify-content:space-between;'
        f'align-items:center;font-size:1.15rem;font-weight:800">'
        f'<span>{section["title"]}</span>{badge(state)}</div>'
    )


def sidebar():
    REF = get_reference_data()
    with st.sidebar:
        logo1, logo2 = st.columns(2)
        logo1.image(str(IMAGES_DIR / "IPWEA-logo.png"), width="stretch")
        logo2.image(str(IMAGES_DIR / "JFC-logo.jpg"), width="stretch")
        st.divider()

        st.markdown(f"### ◧ {C.APP_TITLE}")
        st.caption(C.APP_SUBTITLE)

        st.sidebar.markdown("**Navigate**")
        _nav_button("Setup")
        if C.USE_GROUPED_SECTIONS:
            for section in C.PHASE_SECTIONS:
                st.caption(section["title"])
                for pid in section["phases"]:
                    _nav_button(PHASE_BY_ID[pid]["label"])
        else:
            for pid in C.FLAT_PHASE_ORDER:
                _nav_button(PHASE_BY_ID[pid]["label"])

        st.caption("Results")
        _nav_button("Summary")
        _nav_button("Compare")
        _nav_button("Save & Export")

        st.divider()
        with st.expander("☰ Regulation Reference", expanded=False):
            for topic, cite in REF["regs"]:
                st.markdown(f"**{topic}**  \n{cite}")

        st.caption(C.NSW_HEALTH_NOTE)

        st.divider()
        if st.button("⊘ Reset / clear assessment", width="stretch"):
            reset_widget_state()
            st.session_state.inputs = {p["id"]: {} for p in C.PHASES}
            st.session_state.meta = {"assessment_name": "", "assessed_by": ""}
            st.session_state.page = "Setup"
            st.rerun()


def main():
    init_state()
    inject_css()
    sidebar()

    if "_save_toast" in st.session_state:
        st.toast(st.session_state.pop("_save_toast"))

    st.markdown(f'<div class="disclaimer">! {C.DISCLAIMER}</div>',
                unsafe_allow_html=True)

    page = st.session_state.page
    current_phase_id = next((p["id"] for p in C.PHASES if p["label"] == page), None)
    section = (_section_for_phase(current_phase_id)
               if C.USE_GROUPED_SECTIONS and current_phase_id else None)

    # Reserve the section banner's and progress bar's spots now, but fill
    # them in with fresh results AFTER the page below has run — the page is
    # what writes this run's just-changed widget values into
    # st.session_state.inputs, so computing results before it runs would
    # show last run's (stale) state.
    section_slot = st.empty() if section else None
    progress_slot = st.empty()
    st.write("")

    if page == "Setup":
        page_setup()
    elif page == "Summary":
        page_summary(current_results())
    elif page == "Compare":
        page_compare()
    elif page == "Save & Export":
        page_save_export(current_results())
    elif current_phase_id:
        PAGE_FUNCS[current_phase_id](current_results())

    # After the page above has written this run's widget values into
    # st.session_state.inputs — same ordering reason as the section
    # banner/progress bar below.
    autosave_progress()

    if section_slot is not None:
        with section_slot.container():
            st.markdown(_section_banner_html(section, current_results()), unsafe_allow_html=True)

    with progress_slot.container():
        progress_bar(current_results())


if __name__ == "__main__":
    main()
