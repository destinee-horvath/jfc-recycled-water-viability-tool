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
      .progress-step-v {{
        display:flex; flex-direction:column; align-items:flex-start;
        gap:6px; padding:10px 12px; margin-bottom:8px; border-radius:10px;
        font-size:0.72rem; font-weight:600; background:#fff;
        border:1px solid #eef0f4; border-left:4px solid var(--accent,#e6e8ee);
        box-shadow:0 1px 2px rgba(0,0,0,0.04);
      }}
      .status-panel-right {{
        position:fixed; top:4.5rem; right:14px; width:250px;
        max-height:calc(100vh - 5.5rem); overflow-y:auto;
        background:#f6f7fa; border:1px solid #e6e8ee; border-radius:16px;
        padding:16px; z-index:999; box-shadow:0 6px 20px rgba(0,0,0,0.08);
      }}
      .status-panel-right h4 {{
        margin:0 0 12px 0; font-size:0.8rem; color:{COLOUR_PRIMARY};
        text-transform:uppercase; letter-spacing:.05em;
      }}
      .phase-actions {{ margin-top:2.2rem; padding-top:0.6rem; }}
      .phase-complete {{
        margin-top:1rem; padding:0.8rem 1rem; border:1px solid {COLOUR_SUCCESS};
        border-left:6px solid {COLOUR_SUCCESS}; background:#f4fff7; color:#176b3d;
        border-radius:8px; font-weight:700;
      }}
      .stSidebar .stButton>button {{ width:100%; justify-content:center; }}
      div[data-testid="stExpander"] {{
        border-radius:12px !important; border:1px solid #e6e8ee !important;
        margin-bottom:10px; box-shadow:0 1px 3px rgba(0,0,0,0.03);
      }}
      div[data-testid="stExpander"] summary {{
        padding:12px 14px; background:#fafbfc; border-radius:12px;
      }}
      div[data-testid="stExpander"] summary:hover {{ background:#eef1f7; }}
      div[data-testid="stExpander"] summary span[data-testid="stIconMaterial"] {{
        font-size:1.5rem !important; color:{COLOUR_PRIMARY};
      }}
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
