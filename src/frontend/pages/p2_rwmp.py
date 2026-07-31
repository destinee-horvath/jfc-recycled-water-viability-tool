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


_END_USE_BY_APPLICATION_TYPE = {
    "Concrete Mixing": "concrete mixing",
    "Dust Suppression": "dust suppression",
    "Earthworks (Compaction)": "compaction / subgrade moisture preparation",
}
_END_USE_FALLBACK = ("the intended roadworks application (e.g. compaction, "
                      "subgrade moisture preparation, concrete mixing, or other)")


def _rwmp_request_letter() -> str:
    """Supplier-confirmation letter (FR2.5), pre-filled from Setup/Phase 1/
    Phase 3. No public RWMP register exists, so this is the only way to
    confirm the four things this phase assesses (FR2.1-FR2.4)."""
    meta = st.session_state.meta
    supplier = st.session_state.inputs.get("supplier_approval", {})
    water_quality = st.session_state.inputs.get("water_quality", {})

    project_name = meta.get("assessment_name") or "[project name]"
    assessed_by = meta.get("assessed_by") or "[your name]"
    application = _END_USE_BY_APPLICATION_TYPE.get(
        water_quality.get("application_type"), _END_USE_FALLBACK)

    if supplier.get("water_source") == "Stormwater":
        scheme_line = "Scheme type: stormwater harvesting scheme"
    elif supplier.get("supplier_authority"):
        scheme_line = f"Scheme type: {supplier['supplier_authority']}"
    else:
        scheme_line = "Scheme type: [not yet recorded]"

    return (
        "To the Supplier,\n\n"
        f"{project_name} is assessing the viability of using recycled water "
        f"from your scheme for the following roadworks application: "
        f"{application}.\n\n"
        "As part of this assessment, we are required to confirm the "
        "following about your Recycled Water Management Plan (RWMP), in "
        "line with the NSW Guidelines for Recycled Water Management Systems "
        "(NSW Office of Water, May 2015):\n\n"
        "1. Does your scheme hold an approved RWMP?\n"
        f"2. Does that RWMP explicitly list {application} as an approved "
        "end use?\n"
        "3. Can you confirm in writing that your approved RWMP complies "
        "with all 12 elements of the NSW RWMS framework?\n"
        "4. Has your RWMP been reviewed within the required period, and is "
        "it current?\n\n"
        "We were unable to locate a public register to confirm this "
        "information ourselves, so we would appreciate your written "
        "confirmation on each point above at your earliest convenience.\n\n"
        f"{scheme_line}\n\n"
        "Regards,\n"
        f"{assessed_by}\n"
        f"{project_name}"
    )


def page_rwmp(results):
    REF = get_reference_data()
    g = C.PHASE_BY_ID["rwmp"]
    st.header(g["label"], help=g["desc"])
    d = gi("rwmp")

    st.caption(C.RWMP_LOOKUP_NOTE)

    with st.expander("✉ Request confirmation from your supplier", expanded=False):
        st.caption("No public RWMP register exists — use this template to "
                   "request confirmation directly from your supplier.")
        letter_key = "rwmp_request_letter_text"
        if letter_key not in st.session_state:
            st.session_state[letter_key] = _rwmp_request_letter()
        if st.button("🔄 Regenerate from current inputs", key="rwmp_regen_letter",
                     help="Overwrites any edits below with a fresh letter "
                          "built from what's currently entered in Setup, "
                          "Phase 1, and Phase 3."):
            st.session_state[letter_key] = _rwmp_request_letter()
        st.text_area("Supplier request letter — copy and paste into your "
                     "email client", key=letter_key, height=320)

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
    # Read from the checkboxes' own session_state, not d — d[key] isn't
    # written until the loop below runs, so reading d here would lag one
    # click behind whatever was just ticked.
    def _rwms_checked(key):
        widget_key = f"rwmp_{key}"
        if widget_key in st.session_state:
            return bool(st.session_state[widget_key])
        return bool(d.get(key))

    checked = sum(1 for i in range(1, len(REF["rwms"]) + 1)
                  if _rwms_checked(f"rwms_el_{i}_checked"))
    # key= binds open/closed state to session_state so ticking a checkbox
    # inside (which triggers a rerun) doesn't snap the expander shut again.
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
