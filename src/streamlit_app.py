"""
streamlit_app.py — Recycled Water Viability Assessment Tool (ENTRY POINT)
==========================================================================
Kept at this path/name so Streamlit Community Cloud auto-detects it. All
actual UI code lives in frontend/ (see frontend/app.py); all decision logic
lives in backend/ (see backend/phases/). Run locally:

    streamlit run streamlit_app.py
"""

from frontend.app import main

main()
