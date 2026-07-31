"""frontend/components.py — reusable UI pieces shared across phase pages:
progress bar, validated numeric inputs, phase-result renderer."""

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


def right_status_panel_html(results) -> str:
    """Same data as progress_bar(), but as a fixed panel docked to the
    right edge (.status-panel-right, styles.py) with its own scroll, so it
    stays visible on long phase pages. Plain HTML, not Streamlit widgets —
    a position:fixed element can't host interactive ones. Phase pages only."""
    rows = []
    for phase in C.PHASES:
        r = results.get(phase["id"])
        colour = C.STATE_COLOURS.get(r.state, COLOUR_NEUTRAL) if r else COLOUR_NEUTRAL
        active = " ●" if st.session_state.page == phase["label"] else ""
        state_badge = badge(r.state) if r else badge("NA", "—")
        rows.append(
            f'<div class="progress-step-v" style="--accent:{colour}">'
            f'<span>{phase["label"]}{active}</span>{state_badge}</div>'
        )
    return (
        # Scoped here, not in inject_css(), so the extra padding only
        # applies when the panel actually renders.
        '<style>.block-container{padding-right:310px !important;}</style>'
        '<div class="status-panel-right">'
        '<h4>Phase status</h4>'
        + "".join(rows) +
        '</div>'
    )


def opt_num(label, phase_id, key, help=None, default_measured=False):
    """Optional measurement: a Measured/Not measured toggle + non-negative value.

    ``default_measured`` only affects the first render of an untouched
    field — after that, Streamlit's own widget state takes over.
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
    Parameter | Measured | Not measured | Value table, one row per (key,
    row_label, help_text) in ``items``. Unlike opt_num(), uses a button per
    column so it reads as a table (used by Phase 3); the user's column
    choice persists once made. Value starts empty (``None``), never a
    silent 0 — an untouched field must read as "no result supplied", not a
    measured zero that could trigger a false REJECT or PROCEED.
    ``show_header=False`` skips the header row when continuing a table
    started by a prior value_table()/measured_table() call.
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

        # A just-clicked button can't restyle itself in the same script run
        # (Streamlit already sent its old `type` before the click was
        # processed) — rerun so the next pass draws the settled state.
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
    Parameter | Value table for compulsory numeric inputs — same column
    layout as measured_table() but no Measured/Not-measured toggle. Caller
    must st.session_state.setdefault(widget_key, ...) beforehand, as a
    plain st.number_input() would need. ``show_header`` behaves as in
    measured_table().
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
    Border/tint each number input by its check's REJECT (red) / PROCEED
    (green) state; CONDITIONAL/NA stay unstyled. Relies on Streamlit's
    auto-generated ``st-key-<key>`` class matching measured_table()/
    value_table()'s ``v_{phase_id}_{key}`` convention, so only checks with
    a ``CheckResult.key`` get coloured (see models.py). Call once per page,
    after the relevant table calls — a <style> tag applies regardless of
    DOM order.

    Targets ``div[data-testid="stNumberInputContainer"]``, not the bare
    ``input`` — that container is what actually draws the border/
    background; the nested <input> itself renders borderless.
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
