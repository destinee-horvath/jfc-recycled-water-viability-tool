"""
frontend/refdata.py
====================
Static reference data — cached so it isn't rebuilt every rerun.
"""

import streamlit as st

import config as C

PHASE_BY_ID = {p["id"]: p for p in C.PHASES}


@st.cache_data
def get_reference_data():
    """Static reference data — cached so it isn't rebuilt every rerun."""
    return {"regs": C.all_regulation_refs(), "rwms": C.RWMS_ELEMENTS}
