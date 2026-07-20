"""
frontend/components.py
========================
Reusable UI pieces shared across phase pages: the progress bar, validated
numeric inputs, and the phase-result renderer.
"""

import streamlit as st

import config as C
import backend as B

from .theme import badge, COLOUR_NEUTRAL
from .state import gi


def progress_bar(results):
    cols = st.columns(len(C.PHASES))
    for col, phase in zip(cols, C.PHASES):
        r = results.get(phase["id"])
        colour = C.STATE_COLOURS.get(r.state, COLOUR_NEUTRAL) if r else COLOUR_NEUTRAL
        active = " ●" if st.session_state.page == phase["label"] else ""
        col.markdown(
            f'<div class="progress-step" style="border-color:{colour};color:{colour}">'
            f'{phase["label"]}{active}<br>'
            f'<span style="font-weight:800">{r.state if r else "—"}</span></div>',
            unsafe_allow_html=True,
        )


def opt_num(label, phase_id, key, help=None, default_measured=False):
    """Optional measurement: a Measured/Not measured toggle + non-negative value.

    ``default_measured`` only affects the FIRST render of a field that has
    never been touched — after that, Streamlit's own widget state (driven by
    the user's choice) takes over regardless of this default.
    """
    d = gi(phase_id)
    c1, c2 = st.columns([1, 2])
    default_index = 0 if (d.get(key) is not None or default_measured) else 1
    choice = c1.radio(
        "Measured?", ["Measured", "Not measured"], index=default_index,
        key=f"m_{phase_id}_{key}", label_visibility="collapsed", horizontal=True)
    if choice == "Measured":
        d[key] = c2.number_input(label, min_value=0.0,
                                 value=float(d.get(key) or 0.0),
                                 key=f"v_{phase_id}_{key}", help=help)
    else:
        c2.caption(f"{label} — not measured")
        d[key] = None


def measured_table(items, phase_id, show_header=True):
    """
    Renders a Parameter | Measured | Not measured | Value table —
    one row per (key, row_label, help_text) in ``items``. Unlike opt_num()'s
    single Measured/Not-measured radio, this uses a button PER COLUMN so the
    layout reads as a table (used by Phase 3). New fields default to visible
    (Measured); after the user picks a column once, that choice persists.
    The value itself starts empty (``value=None``), never a silent 0 — an
    untouched field must read as "no result supplied" (each check's own
    CONDITIONAL path), not as a measured zero that can trigger a false
    REJECT (e.g. compressive strength/pH) or false PROCEED (e.g. sugar/oil,
    which pass trivially at 0).
    ``show_header=False`` skips the header row — use when this call's rows
    follow directly on from a value_table()/measured_table() call that
    already drew the header, so the two read as one continuous table.
    """
    d = gi(phase_id)
    if show_header:
        h1, h2, h3, h4 = st.columns([2, 1, 1, 2])
        h1.markdown("**Parameter**")
        h2.markdown("**Measured**")
        h3.markdown("**Not measured**")
        h4.markdown("**Value**")

    for key, row_label, help_text in items:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        c1.markdown(row_label)

        state_key = f"measured_state_{phase_id}_{key}"
        st.session_state.setdefault(state_key, True)
        measured = st.session_state[state_key]

        # A just-clicked button can't restyle itself within the same script
        # run (Streamlit already sent its old `type` to the frontend before
        # the click is processed) — rerun immediately so the next pass draws
        # both buttons and the value input from the new, settled state.
        if c2.button("Measured", key=f"btn_m_{phase_id}_{key}",
                     type="primary" if measured else "secondary",
                     width="stretch") and not measured:
            st.session_state[state_key] = True
            st.rerun()
        if c3.button("Not measured", key=f"btn_nm_{phase_id}_{key}",
                     type="primary" if not measured else "secondary",
                     width="stretch") and measured:
            st.session_state[state_key] = False
            st.rerun()

        if measured:
            current = d.get(key)
            d[key] = c4.number_input(row_label, min_value=0.0,
                                     value=float(current) if current is not None else None,
                                     key=f"v_{phase_id}_{key}", help=help_text,
                                     label_visibility="collapsed")
        else:
            c4.caption("not measured")
            d[key] = None


def value_table(items, phase_id, show_header=True):
    """
    Parameter | Value table for COMPULSORY numeric inputs — same column
    layout as measured_table() (parameter in the first column, value in the
    last) but without the Measured/Not measured toggle, since these fields
    are always required. Caller must st.session_state.setdefault(widget_key,
    ...) before calling, same as a plain st.number_input() would need.
    ``show_header=False`` skips the header row — use when this call's rows
    follow directly on from a value_table()/measured_table() call that
    already drew the header, so the two read as one continuous table.
    """
    d = gi(phase_id)
    if show_header:
        h1, h2, h3, h4 = st.columns([2, 1, 1, 2])
        h1.markdown("**Parameter**")
        h4.markdown("**Value**")

    for key, row_label, help_text, widget_key, min_value, max_value in items:
        c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
        c1.markdown(row_label)
        d[key] = c4.number_input(
            row_label, min_value=min_value, max_value=max_value,
            key=widget_key, help=help_text, label_visibility="collapsed")


def money(label, phase_id, key, help=None):
    """Non-negative money/number input persisted to session_state."""
    d = gi(phase_id)
    d[key] = st.number_input(label, min_value=0.0,
                             value=float(d.get(key) or 0.0),
                             step=1.0, key=f"f_{phase_id}_{key}", help=help)
    return d[key]


def colour_inputs_by_state(phase_result: B.PhaseResult, phase_id: str):
    """
    Border/tint the Measured/Not-measured and Value-table number inputs by
    their own check's REJECT (red) / PROCEED (green) state, for at-a-glance
    readability — CONDITIONAL/NA are left unstyled (default look), since
    they're neither a pass nor a fail. Relies on Streamlit's auto-generated
    ``st-key-<key>`` CSS class for the widget whose ``key=`` matches
    measured_table()/value_table()'s own ``v_{phase_id}_{key}`` convention,
    so this only colours checks that set CheckResult.key (see models.py).
    Call this once per page, anywhere after the relevant measured_table()/
    value_table() calls — a <style> tag applies regardless of DOM order.

    Targets ``div[data-testid="stNumberInputContainer"]`` rather than the
    bare ``input`` — that container div is what actually draws the visible
    border/background box in Streamlit's number_input; the nested <input>
    itself renders borderless, so styling it directly is invisible.
    """
    colour_by_state = {"REJECT": C.COLOUR_DANGER, "PROCEED": C.COLOUR_SUCCESS}
    css = "".join(
        f'.st-key-v_{phase_id}_{c.key} div[data-testid="stNumberInputContainer"] {{'
        f'border: 2px solid {colour_by_state[c.state]} !important;'
        f'background-color: {colour_by_state[c.state]}1a;}}'
        for c in phase_result.checks if c.key and c.state in colour_by_state
    )
    if css:
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def render_phase_result(r: B.PhaseResult):
    st.divider()
    colour = C.STATE_COLOURS.get(r.state, COLOUR_NEUTRAL)
    st.markdown(f"### Phase outcome: {badge(r.state)}", unsafe_allow_html=True)
    html = f'<div class="phasecard" style="--bar:{colour}">'
    for c in r.checks:
        html += (
            f'<div class="checkrow">{badge(c.state)}'
            f'<div><b>{c.label}</b><br>'
            f'<span style="color:#444">{c.detail}</span><br>'
            f'<span style="color:{COLOUR_NEUTRAL};font-size:0.78rem">{c.reference}</span>'
            f'</div></div>')
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

    getter = getattr(C, f"{r.phase_id}_regulation_refs", None)
    refs = getter() if getter else []
    if refs:
        with st.expander("☰ Regulation Reference", expanded=False):
            for topic, cite in refs:
                st.markdown(f"**{topic}**  \n{cite}")
