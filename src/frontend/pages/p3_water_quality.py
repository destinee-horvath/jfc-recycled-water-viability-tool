"""
frontend/pages/p3_water_quality.py
=========================
PHASE 3 — Water Quality (by application)
"""

import streamlit as st

import config as C

from ..state import gi, render_phase_actions, current_results
from ..components import measured_table, colour_inputs_by_state, render_phase_result


def page_water_quality(results):
    g = C.PHASE_BY_ID["water_quality"]
    st.header(g["label"], help=g["desc"])
    d = gi("water_quality")

    d["application_type"] = st.selectbox(
        "Roadworks application", C.APPLICATION_TYPES,
        index=C.APPLICATION_TYPES.index(
            d.get("application_type", C.APPLICATION_TYPES[0])),
        key="water_quality_application_type")
    app = d["application_type"]

    # Kept as a general field — Phase 6 cross-checks it against the WHS
    # contact-risk level, regardless of which table below applies.
    d["water_class"] = st.selectbox(
        "Intended AGWR water class", C.WATER_CLASSES,
        index=C.WATER_CLASSES.index(d.get("water_class", "Unclassified")),
        key="water_quality_water_class")

    if app == "Concrete Mixing":
        _concrete_fields()
    elif app == "Dust Suppression":
        _dust_suppression_fields()
    else:
        _earthworks_fields()

    phase_result = current_results()["water_quality"]
    colour_inputs_by_state(phase_result, "water_quality")
    render_phase_result(phase_result)
    render_phase_actions("water_quality")


def _limit_text(meta: dict) -> str:
    lim = meta.get("max")
    return (f"≤ {lim:g} {meta['unit']}".strip() if lim is not None
            else f"> {meta['min']:g} {meta['unit']}".strip())


def _concrete_fields():
    st.info("**Concrete Mixing** — assessed against **AS 1379** compressive "
            "strength, impurity limits and filtered-water turbidity.")

    st.subheader("Table 2.1 — compressive strength")
    measured_table([(
        "compression_strength_pct",
        f"Compressive strength (≥ {C.CONCRETE_STRENGTH_MIN_PCT:g}% of control sample)",
        C.CONCRETE_STRENGTH_REF,
    )], "water_quality")

    st.subheader("Table 2.2 — impurity limits")
    measured_table([
        (key, f"{meta['label']} ({_limit_text(meta)})", meta["ref"])
        for key, meta in C.CONCRETE_TABLE_2_2.items()
    ], "water_quality")

    st.subheader("Microbiological (AGWR Phase 1 2006)")
    measured_table([(
        "conc_ecoli",
        f"{C.CONCRETE_ECOLI['label']} ({_limit_text(C.CONCRETE_ECOLI)})",
        C.CONCRETE_ECOLI["ref"],
    )], "water_quality")

    st.subheader("Filtered water turbidity")
    measured_table([(
        "filtered_turbidity_ntu",
        f"Filtered water turbidity (≤ {C.CONCRETE_TURBIDITY_MAX_NTU:g} NTU max, "
        f"target ≤ {C.CONCRETE_TURBIDITY_TARGET_NTU:g} NTU)",
        C.CONCRETE_TURBIDITY_REF,
    )], "water_quality")

    st.subheader("Table 2.3 — reportable only (no pass/fail threshold)")
    measured_table([
        (key, meta["label"], meta["ref"])
        for key, meta in C.CONCRETE_TABLE_2_3.items()
    ], "water_quality")


def _dust_suppression_fields():
    st.info("**Dust Suppression** — assessed against **Table 3.8** "
            "(unrestricted-access municipal-use tier, since this is public-facing).")

    measured_table([(
        "pathogen_pct",
        f"Virus / Protozoa / Bacteria present (< {C.DUST_PATHOGEN_MAX_PCT:g}% required)",
        C.DUST_PATHOGEN_REF,
    )], "water_quality")

    st.subheader("Table 3.8 — impurity limits")
    measured_table([
        (key, f"{meta['label']} (< {meta['max']:g} {meta['unit']})", meta["ref"])
        for key, meta in C.DUST_TABLE_3_8.items()
    ], "water_quality")


def _earthworks_fields():
    st.info("**Earthworks (Compaction)** — assessed against **Table 3-1** "
            "impurity limits (Sydney Water Recycled) and AGWR Phase 1 (2006) "
            "Table 3.8 microbiological limits.")

    st.subheader("Table 3-1 — impurity limits")
    measured_table([
        (key, f"{meta['label']} ({_limit_text(meta)})", meta["ref"])
        for key, meta in C.EARTHWORKS_TABLE_3_1.items()
    ], "water_quality")

    st.subheader("Microbiological (AGWR Phase 1 2006, Table 3.8)")
    measured_table([
        (key, f"{meta['label']} ({_limit_text(meta)})", meta["ref"])
        for key, meta in C.EARTHWORKS_MICRO_TABLE.items()
    ], "water_quality")
