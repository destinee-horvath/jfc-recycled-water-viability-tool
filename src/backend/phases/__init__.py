"""
backend/phases/__init__.py
===========================
Registry of phase assessors. To add a new phase:
  1. Add its (id, label, desc, mandatory) entry to config.PHASES.
  2. Create backend/phases/<name>.py with an ``assess_<name>(inp, ctx) -> PhaseResult``.
  3. Import it and add it to PHASE_FUNCS below, keyed by the same id used in config.PHASES.
No other backend or frontend code needs to change.
"""

from .p1_supplier_approval import assess_supplier_approval
from .p2_rwmp import assess_rwmp
from .p3_water_quality import assess_water_quality
from .p4_site_runoff import assess_site_runoff
from .p5_soil_conditions import assess_soil_conditions
from .p6_whs import assess_whs
from .p7_financial import assess_financial, financial_analysis, recycled_distance_breakeven_curve

PHASE_FUNCS = {
    "supplier_approval": assess_supplier_approval,
    "rwmp": assess_rwmp,
    "water_quality": assess_water_quality,
    "site_runoff": assess_site_runoff,
    "soil_conditions": assess_soil_conditions,
    "whs": assess_whs,
    "financial": assess_financial,
}
