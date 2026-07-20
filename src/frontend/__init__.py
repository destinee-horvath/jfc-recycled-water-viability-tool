"""
frontend/
=========
Streamlit UI only. Collects inputs into st.session_state, hands them to
backend.run_assessment(), and renders colour-coded results.

Package layout:
    theme.py      Colour constants + badge().
    styles.py     Page-wide CSS injection.
    refdata.py    Cached static reference data (regs, RWMS elements, phase lookup).
    state.py      Session-state init/helpers + the Next/Save phase actions.
    components.py Shared widgets: progress bar, validated inputs, result card.
    pages/        One module per page + the PAGE_FUNCS registry.
    app.py        main() — wires it all together; this is what streamlit_app.py runs.
"""
