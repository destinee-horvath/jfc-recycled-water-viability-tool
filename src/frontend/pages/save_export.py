"""
frontend/pages/save_export.py
==============================
Standalone Save & Export page — the same save/export actions as the bottom
of the Summary page (see summary.save_export_block), exposed directly from
the sidebar so they're reachable without paging through the full readiness
summary first.
"""

import streamlit as st

import backend as B

from .summary import save_export_block


def page_save_export(results):
    readiness = B.readiness_summary(results)
    save_export_block(results, readiness)
