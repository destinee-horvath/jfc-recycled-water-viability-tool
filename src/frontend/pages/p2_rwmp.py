"""
frontend/pages/p2_rwmp.py
=========================
PHASE 2 — RWMP
"""

import streamlit as st

import config as C

from ..state import gi, render_phase_actions, current_results
from ..components import render_phase_result
from ..refdata import get_reference_data


def page_rwmp(results):
    REF = get_reference_data()
    g = C.PHASE_BY_ID["rwmp"]
    st.header(g["label"], help=g["desc"])
    d = gi("rwmp")

    st.caption(C.RWMP_LOOKUP_NOTE)
    d["has_approved_rwmp"] = st.checkbox(
        "Supplier holds an approved RWMP for this scheme",
        value=bool(d.get("has_approved_rwmp")), key="rwmp_has_approved_rwmp")
    d["lists_roadworks_enduse"] = st.checkbox(
        "RWMP lists compaction / subgrade moisture preparation as an approved end use",
        value=bool(d.get("lists_roadworks_enduse")), key="rwmp_lists_roadworks_enduse")
    d["rwmp_current"] = st.checkbox(
        "RWMP current / reviewed within required period",
        value=bool(d.get("rwmp_current")), key="rwmp_rwmp_current")

    d["rwmp_12_elements_confirmed"] = st.checkbox(
        "Supplier has confirmed in writing that their approved RWMP complies "
        "with all 12 RWMS elements",
        value=bool(d.get("rwmp_12_elements_confirmed")),
        help="RWMP compliance with the 12 elements is assessed by DCCEEW as "
             "part of the s.60 approval process — the engineer is not "
             "required to independently audit the RWMP. The review and "
             "revision of the RWMP is entirely the supplier's "
             "responsibility; obtain written confirmation from the "
             "supplier that this has been done.",
        key="rwmp_rwmp_12_elements_confirmed")
    # Read from the checkbox widgets' own session_state entries, not d — a
    # click updates st.session_state[key] before this script reruns from
    # the top, but d[key] isn't written until the loop below executes the
    # checkbox() calls, which happens after this line. Reading d here would
    # make the count lag one click behind whatever was just ticked.
    def _rwms_checked(key):
        widget_key = f"rwmp_{key}"
        if widget_key in st.session_state:
            return bool(st.session_state[widget_key])
        return bool(d.get(key))

    checked = sum(1 for i in range(1, len(REF["rwms"]) + 1)
                  if _rwms_checked(f"rwms_el_{i}_checked"))
    # key= binds open/closed state to session_state so ticking a checkbox
    # inside (which triggers a rerun) doesn't snap the expander shut again —
    # a bare `expanded=False` literal is re-evaluated on every rerun and
    # would otherwise force it closed after every click.
    expander_key = "rwmp_rwms_expander"
    st.session_state.setdefault(expander_key, False)
    with st.expander(f"Reference: the 12 RWMS elements — personal checklist "
                      f"({checked}/{len(REF['rwms'])})",
                      expanded=st.session_state[expander_key], key=expander_key):
        st.caption(C.RWMS_SOURCE)
        st.caption("Optional — for your own tracking only. Ticking these boxes "
                   "does not feed into the assessment; the single confirmation "
                   "checkbox above is what's actually assessed.")
        for i, el in enumerate(REF["rwms"], 1):
            key = f"rwms_el_{i}_checked"
            d[key] = st.checkbox(el, value=bool(d.get(key)), key=f"rwmp_{key}")

    render_phase_result(current_results()["rwmp"])
    render_phase_actions("rwmp")
