"""frontend/refdata.py — static reference data, cached so it isn't rebuilt
every rerun."""

import streamlit as st

import config as C

PHASE_BY_ID = {p["id"]: p for p in C.PHASES}


@st.cache_data
def get_reference_data():
    return {"regs": C.all_regulation_refs(), "rwms": C.RWMS_ELEMENTS}
