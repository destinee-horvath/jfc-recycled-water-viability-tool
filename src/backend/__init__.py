"""
backend/
========
All assessment logic + persistence for the Recycled Water Viability
Assessment Tool. The frontend holds no decision logic — it only collects
inputs and renders whatever this package returns.

Phase 7's config.FINANCIAL_DEFAULTS are starting figures, not confirmed
rates — review with finance/contractor/water authority before relying on them.

Package layout:
    models.py         CheckResult / PhaseResult data structures.
    helpers.py         Small helpers shared by more than one phase.
    phases/            One module per phase + the PHASE_FUNCS registry.
    orchestration.py   run_assessment() / readiness_summary().
    persistence.py     CSV save/load (swap for a DB/bucket client later).
    pdf.py             Readiness-summary PDF export.
    excel.py           Colour-coded Excel (.xlsx) export — display-only, not re-importable.
    ors_distance.py    Optional OpenRouteService geocoding/driving-distance lookup.

Contract: every phase function takes a plain ``dict`` of inputs and returns
a ``PhaseResult(phase_id, checks=[CheckResult, ...], state, mandatory)``.
"""

from .models import CheckResult, PhaseResult
from .phases import PHASE_FUNCS, financial_analysis, recycled_distance_breakeven_curve
from .orchestration import run_assessment, readiness_summary, section_rollup
from .persistence import (
    build_record,
    record_to_csv_bytes,
    save_assessment,
    list_saved,
    load_assessment_bytes,
    load_assessment_file,
    record_to_inputs,
    suggest_filename,
)
from .pdf import build_pdf
from .excel import build_xlsx
from .ors_distance import get_driving_distance_km, get_driving_route, geocode_address

__all__ = [
    "CheckResult", "PhaseResult",
    "PHASE_FUNCS", "financial_analysis", "recycled_distance_breakeven_curve",
    "run_assessment", "readiness_summary", "section_rollup",
    "build_record", "record_to_csv_bytes", "save_assessment", "list_saved",
    "load_assessment_bytes", "load_assessment_file", "record_to_inputs",
    "suggest_filename",
    "build_pdf", "build_xlsx",
    "get_driving_distance_km", "get_driving_route", "geocode_address",
]
