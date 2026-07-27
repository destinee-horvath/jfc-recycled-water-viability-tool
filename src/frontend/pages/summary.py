"""
frontend/pages/summary.py
==========================
Readiness summary (blocking/pending/confirmed), phase-outcome recap, and
save/export actions. No single pass/fail verdict or score by design —
just the per-check breakdown.
"""

from datetime import datetime

import streamlit as st

import config as C
import backend as B

from ..theme import badge


def page_summary(results):
    st.header("Summary & readiness")

    st.subheader("Phase outcomes")
    all_phase_ids = [p["id"] for p in C.PHASES]
    selected_ids = all_phase_ids
    selected_phases = [p for p in C.PHASES if p["id"] in selected_ids]

    if not selected_phases:
        st.caption("Select at least one phase to show.")
    else:
        cols = st.columns(len(selected_phases))
        for col, phase in zip(cols, selected_phases):
            r = results[phase["id"]]
            col.markdown(
                f'**{phase["label"]}**<br>{badge(r.state)}',
                unsafe_allow_html=True)

        st.divider()

        if len(selected_phases) > 1:
            for phase in selected_phases:
                st.markdown(f"### {phase['label']}")
                c1, c2, c3 = st.columns(3)
                _readiness_columns(results[phase["id"]].checks, c1, c2, c3)
                st.divider()
        else:
            c1, c2, c3 = st.columns(3)
            _readiness_columns(results[selected_phases[0]["id"]].checks, c1, c2, c3)
            st.divider()

    readiness = B.readiness_summary(results)
    save_export_block(results, readiness)


def _readiness_columns(checks, c1, c2, c3):
    blocking = [c for c in checks if c.state == "REJECT"]
    pending = [c for c in checks if c.state == "CONDITIONAL"]
    confirmed = [c for c in checks if c.state == "PROCEED"]
    with c1:
        st.markdown(f"#### {badge('REJECT','Required')}", unsafe_allow_html=True)
        for c in blocking:
            st.markdown(f"- {c.label}")
        if not blocking:
            st.caption("Nothing blocking.")
    with c2:
        st.markdown(f"#### {badge('CONDITIONAL','Pending')}", unsafe_allow_html=True)
        for c in pending:
            st.markdown(f"- {c.label}")
        if not pending:
            st.caption("Nothing pending.")
    with c3:
        st.markdown(f"#### {badge('PROCEED','Confirmed')}", unsafe_allow_html=True)
        for c in confirmed:
            st.markdown(f"- {c.label}")


def save_export_block(results, readiness):
    st.subheader("Save & export")
    m = st.session_state.meta
    c1, c2 = st.columns(2)
    m["assessment_name"] = c1.text_input("Assessment name (filename)",
                                         value=m.get("assessment_name", ""),
                                         key="summary_assessment_name")
    m["assessed_by"] = c2.text_input("Assessed by", value=m.get("assessed_by", ""),
                                     key="summary_assessed_by")

    if not m["assessment_name"]:
        st.caption("Enter an assessment name to enable saving.")
        return

    meta = dict(m, saved_at=datetime.now().isoformat(timespec="seconds"))
    rec = B.build_record(st.session_state.inputs, meta)
    fname = B.suggest_filename(m["assessment_name"])

    c1, c2, c3, c4 = st.columns(4)
    if c1.button("⤓ Save to saved_assessments/", width="stretch"):
        path = B.save_assessment(rec, fname)
        st.success(f"Saved {path}")
    c2.download_button("⇩ Download CSV (re-importable)",
                       data=B.record_to_csv_bytes(rec),
                       file_name=fname, mime="text/csv",
                       width="stretch")
    c3.download_button("▤ Download PDF Readiness Summary",
                       data=B.build_pdf(meta, results, readiness),
                       file_name=fname.replace(".csv", ".pdf"),
                       mime="application/pdf", width="stretch")
    c4.download_button("▦ Download Excel Report (colour-coded)",
                       data=B.build_xlsx(meta, results, readiness, st.session_state.inputs),
                       file_name=fname.replace(".csv", ".xlsx"),
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       width="stretch")
