"""
frontend/pages/__init__.py
============================
Registry of phase pages. To add a new phase's UI:
  1. Create frontend/pages/<name>.py with a ``page_<name>(results)`` function
     (mirroring the backend/phases/<name>.py module of the same id).
  2. Import it and add it to PAGE_FUNCS below, keyed by the same id used in
     config.PHASES and backend.phases.PHASE_FUNCS.
frontend/app.py drives navigation from config.PHASES + this registry alone —
no other frontend code needs to change.
"""

from .setup import page_setup
from .p1_supplier_approval import page_supplier_approval
from .p2_rwmp import page_rwmp
from .p3_water_quality import page_water_quality
from .p4_site_runoff import page_site_runoff
from .p5_soil_conditions import page_soil_conditions
from .p6_whs import page_whs
from .p7_financial import page_financial
from .summary import page_summary
from .compare import page_compare
from .save_export import page_save_export

PAGE_FUNCS = {
    "supplier_approval": page_supplier_approval,
    "rwmp": page_rwmp,
    "water_quality": page_water_quality,
    "site_runoff": page_site_runoff,
    "soil_conditions": page_soil_conditions,
    "whs": page_whs,
    "financial": page_financial,
}
