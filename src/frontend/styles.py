"""
frontend/styles.py
===================
Page-wide CSS injection.
"""

import streamlit as st

from .theme import COLOUR_PRIMARY, COLOUR_NEUTRAL, COLOUR_SUCCESS


def inject_css():
    st.markdown(f"""
    <style>
      .block-container {{ padding-top: 1.1rem; max-width: 1200px; }}
      h1, h2, h3 {{ color: {COLOUR_PRIMARY}; }}
      .stButton>button[kind="primary"] {{
        background: {COLOUR_PRIMARY}; border-color: {COLOUR_PRIMARY};
      }}
      .badge {{
        display:inline-block; padding:2px 12px; border-radius:999px;
        color:#fff; font-weight:700; font-size:0.78rem; letter-spacing:.04em;
        white-space:nowrap;
      }}
      .disclaimer {{
        position:relative; top:0; z-index:1; background:{COLOUR_PRIMARY};
        color:#fff; padding:7px 14px; border-radius:8px; font-size:0.8rem;
        margin-top:3.2rem; margin-bottom:14px; line-height:1.35;
      }}
      .phasecard {{
        border:1px solid #e6e8ee; border-left:6px solid var(--bar,{COLOUR_NEUTRAL});
        border-radius:10px; padding:12px 14px; margin-bottom:10px; background:#fff;
      }}
      .checkrow {{
        display:flex; gap:10px; align-items:flex-start; padding:7px 0;
        border-top:1px solid #f0f1f4;
      }}
      .checkrow:first-child {{ border-top:none; }}
      .progress-step {{
        flex:1; text-align:center; padding:8px 4px; border-radius:8px;
        font-size:0.72rem; font-weight:600; border:1px solid #e6e8ee;
      }}
      .phase-actions {{ margin-top:2.2rem; padding-top:0.6rem; }}
      .phase-complete {{
        margin-top:1rem; padding:0.8rem 1rem; border:1px solid {COLOUR_SUCCESS};
        border-left:6px solid {COLOUR_SUCCESS}; background:#f4fff7; color:#176b3d;
        border-radius:8px; font-weight:700;
      }}
      .stSidebar .stButton>button {{ width:100%; justify-content:center; }}
      @media (max-width: 640px) {{ .block-container {{ padding:0.6rem; }} }}

      div[class*="st-key-financial_generate_graph"] button {{
        font-size: 1.25rem; font-weight: 800; padding: 0.9rem 2.2rem;
        background: {COLOUR_SUCCESS}; border-color: {COLOUR_SUCCESS}; color: #fff;
        border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.15);
      }}
      div[class*="st-key-financial_generate_graph"] button:hover {{
        filter: brightness(1.08); border-color: {COLOUR_SUCCESS};
      }}
    </style>
    """, unsafe_allow_html=True)
