"""
config.py
=========
Single source of truth for the Recycled Water Viability Assessment Tool:
colour theme, regulation citations, RWMS elements, AGWR thresholds, and
UI dropdown option lists. Constant for the life of a run — cached via
``@st.cache_data`` in the frontend.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Anchored to this file's location (not cwd) so SAVE_DIR stays valid
# regardless of launch directory — same pattern as frontend/app.py's IMAGES_DIR.
BASE_DIR = Path(__file__).resolve().parent

# ----------------------------------------------------------------------------
# COLOUR THEME — change here to propagate everywhere
# ----------------------------------------------------------------------------
COLOUR_PRIMARY = "#1F3864"      # dark navy  — headers, primary actions
COLOUR_SECONDARY = "#2E75B6"    # mid blue   — secondary elements
COLOUR_SUCCESS = "#1D9E75"      # green      — VIABLE / PROCEED / Compliant
COLOUR_WARNING = "#EF9F27"      # amber      — CONDITIONAL / Pending
COLOUR_DANGER = "#E24B4A"       # red        — NOT VIABLE / REJECT / Not met
COLOUR_NEUTRAL = "#888780"      # gray       — neutral / N/A states
COLOUR_BG = "#FFFFFF"           # background

# Map a verdict state to its colour — use this everywhere for consistency.
STATE_COLOURS = {
    "PROCEED": COLOUR_SUCCESS,
    "CONDITIONAL": COLOUR_WARNING,
    "REJECT": COLOUR_DANGER,
    "NA": COLOUR_NEUTRAL,
}

# ----------------------------------------------------------------------------
# APP META
# ----------------------------------------------------------------------------
APP_TITLE = "Recycled Water Viability Assessment Tool"
APP_SUBTITLE = "Viability screening for recycled water across roadworks applications (IPWEA / NSW)"
SAVE_DIR = str(BASE_DIR / "saved_assessments")

DISCLAIMER = (
    "! DECISION SUPPORT ONLY. This tool provides a preliminary viability screen "
    "and does NOT replace formal EPA, council or water-authority approval. "
    "All outputs must be verified against the cited legislation by a "
    "qualified person before any works commence."
)

# Shown on the Setup page so engineers know what to gather before starting.
TOOL_PREREQUISITES = [
    "Water source & supplier details",
    "Supplier's approval (council, water authority, or stormwater)",
    "Your own EPL or development consent",
    "Approved RWMP for this use",
    "Water quality test results",
    "Site details: waterway distance, EPL status, containment",
    "Soil test results (USCS class, SAR/EC) — optional",
    "Estimated project costs — optional, defaults provided",
    "WHS arrangements: SWMS, PPE, signage",
]

# Single source of truth for phase display names (no "Phase N" prefix in UI).
# Used by PHASES below and the regulation-reference builders further down.
PHASE_DISPLAY_NAMES = {
    "supplier_approval": "Supplier & Dual Approval",
    "water_quality": "Water Quality",
    "rwmp": "Recycled Water Management Plan",
    "site_runoff": "Site Runoff & EPL Risk",
    "soil_conditions": "Soil & Site Conditions",
    "whs": "Worker Health & Safety",
    "financial": "Financial Feasibility",
}

# Phase list (id, label, description, whether a REJECT is a hard/mandatory
# failure). Checklist, not a gate: every phase stays assessed and editable
# regardless of others' outcomes; REJECT surfaces via backend.readiness_summary()
# as a blocking item but never blocks navigation.
PHASES = [
    {
        "id": "financial",
        "label": PHASE_DISPLAY_NAMES["financial"],
        "desc": "Whole-of-life cost incl. transport & restrictions.",
        "mandatory": False,
    },
    {
        "id": "supplier_approval",
        "label": PHASE_DISPLAY_NAMES["supplier_approval"],
        "desc": "Supplier's approval AND the user's own approval to use the water.",
        "mandatory": True,
    },
    {
        "id": "rwmp",
        "label": PHASE_DISPLAY_NAMES["rwmp"],
        "desc": "Approved Recycled Water Management Plan covering this use.",
        "mandatory": True,
    },
    {
        "id": "water_quality",
        "label": PHASE_DISPLAY_NAMES["water_quality"],
        "desc": "AGWR Phase 1 (2006), or concrete Table 3-1 limits by application.",
        "mandatory": False,
    },
    {
        "id": "site_runoff",
        "label": PHASE_DISPLAY_NAMES["site_runoff"],
        "desc": "POEO Act 1997 — pollution, licensing, capture, overflow, containment.",
        "mandatory": False,
    },
    {
        "id": "soil_conditions",
        "label": PHASE_DISPLAY_NAMES["soil_conditions"],
        "desc": "USCS soil classification and pavement layer data, plus SAR/EC structural-stability screening of the water source.",
        "mandatory": False,
    },
    {
        "id": "whs",
        "label": PHASE_DISPLAY_NAMES["whs"],
        "desc": "WHS Act/Reg 2017 — notification, health risks, PPE, contact & method.",
        "mandatory": True,
    },
]

# Lookup by id, not list position (backend/orchestration.py can't import
# frontend/refdata.py, which keeps its own copy for frontend use).
PHASE_BY_ID = {p["id"]: p for p in PHASES}

# ----------------------------------------------------------------------------
# UI GROUPING — order/section structure. Pages look themselves up via
# PHASE_BY_ID (never positional), so this order is free to change; drives
# Setup prerequisites, progress bar, Summary columns, and Next-button flow.
# ----------------------------------------------------------------------------
USE_GROUPED_SECTIONS = True

FLAT_PHASE_ORDER = [
    "financial", "supplier_approval", "rwmp", "water_quality", "site_runoff", "soil_conditions", "whs",
]
GROUPED_PHASE_ORDER = [
    "financial",
    "supplier_approval",
    "rwmp",
    "water_quality",
    "site_runoff",
    "soil_conditions",
    "whs",
]
PHASE_ORDER = GROUPED_PHASE_ORDER if USE_GROUPED_SECTIONS else FLAT_PHASE_ORDER

# Section grouping for the grouped UI. Phase IDs are baked into saved CSVs
# as column prefixes (e.g. water_quality.xxx) — renaming an id orphans
# existing saved files; re-save assessments after any rename.
PHASE_SECTIONS = [
    {"title": "Financial Feasibility", "phases": ["financial"]},
    {"title": "Compliance Requirements", "phases": ["supplier_approval", "rwmp", "water_quality"]},
    {"title": "Risk Assessment", "phases": ["site_runoff", "soil_conditions", "whs"]},
]

# ----------------------------------------------------------------------------
# PHASE 1 — water source, supplier authority, and DUAL APPROVAL
# ----------------------------------------------------------------------------
WATER_SOURCES = [
    "Treated effluent",
    "Stormwater",
    "Other",
]

# Who supplies the water -> the supplier-side statutory approval instrument.
SUPPLIER_AUTHORITIES = [
    "Council-run scheme",
    "Water supply authority",
]

SUPPLIER_APPROVAL_REFS = {
    "Council-run scheme":
        "Local Government Act 1993, s.60(b) & s.60(c)",
    "Water supply authority":
        "Water Management Act 2000, s.292(1)(a)",
}

# DUAL APPROVAL — the user's own approval to USE the water; supplier approval
# (s.60/s.292/s.68) doesn't grant this automatically. Defaults to
# "Unconfirmed" so the engineer isn't forced into a binary choice.
USER_APPROVAL_STATES = [
    "Permitted for this use",
    "Not permitted for this use",
    "Unconfirmed",
]
DUAL_APPROVAL_REF = (
    "User-side approval — the user's Environment Protection Licence (POEO Act "
    "1997) or development consent (EP&A Act 1979) must permit recycled-water use "
    "for the intended roadworks application. A licensed discharge point for "
    "treated effluent is NOT approval to USE the water."
)

# Tri-state, reused by every supplier-side approval check. "Unconfirmed" is
# CONDITIONAL not REJECT — remediable by obtaining/confirming approval,
# unlike a hard reject (e.g. dual approval's "not permitted").
APPROVAL_STATES = ["Yes", "No", "Unconfirmed"]

# Stormwater bypasses s.60/s.292/s.68. Unlike that framework ("No" = hard
# REJECT, needs pre-existing ministerial approval), stormwater's approvals
# are obtainable, so missing/unconfirmed is CONDITIONAL, never a hard reject.
STORMWATER_APPROVAL_REF = (
    "s.60/s.292/s.68 don't apply to stormwater. Confirm s.68 council "
    "approval, development consent, and WMA 2000 approvals instead — these "
    "are obtainable, so missing/unconfirmed approval is CONDITIONAL, not a "
    "hard reject."
)

# s.68 LGA doesn't apply to stormwater in Sydney/Hunter Water areas.
SYDNEY_HUNTER_REF = (
    "s.68 LGA does not apply in Sydney Water or Hunter Water operational "
    "areas — proceed via the Sydney Water Stormwater Harvesting Agreement "
    "and WMA 2000 approvals."
)

# ----------------------------------------------------------------------------
# PHASE 1 — plain-language content, shown alongside (not replacing) the
# citation. Informational only — doesn't feed p1_supplier_approval.py's gate logic.
# ----------------------------------------------------------------------------
SUPPLIER_APPROVAL_PLAIN = {
    "Council-run scheme": "Council needs approval to both run the plant and supply the water. Confirm both are current.",
    "Water supply authority": "Authorities like Sydney Water need ministerial approval to operate. Confirm it's current.",
}

# Tooltip text for the "?" help icon next to each supplier type's citation.
SUPPLIER_SECTION_TOOLTIPS = {
    "Council-run scheme": (
        "LG Act 1993 s.60: councils need ministerial approval to build/extend "
        "treatment works (b) and to supply treated sewage to anyone (c)."
    ),
    "Water supply authority": (
        "WM Act 2000 s.292(1)(a): authorities like Sydney Water need "
        "ministerial approval to build and run treatment/supply works."
    ),
}

# EPL section — informational only (see note above).
EPL_SECTION_TITLE = "Does the supplier hold an Environment Protection Licence (EPL)?"
EPL_SECTION_EXPLANATION = (
    "An EPL sets a facility's legal operating conditions"
)
EPL_STATES = ["Yes", "No", "Unconfirmed"]
EPL_NO_NOTE = (
    "If the supplier does not hold an EPL, confirm that their s.60 / s.292 "
    "approval (selected above) is sufficient for this specific use. An "
    "EPL is not always required, but one of the above approval pathways must apply."
)
EPL_UNCONFIRMED_NOTE = "Confirm EPL status with the supplier before proceeding."

DUAL_APPROVAL_PLAIN_NOTE = (
    "Supplier approval doesn't cover this — you need your own EPL or "
    "development consent for this specific use."
)

TOOLTIP_EPL = (
    "Issued by the NSW EPA under the POEO Act 1997 — sets a facility's legal "
    "operating conditions (what it can discharge, where, and how)."
)
TOOLTIP_DUAL_APPROVAL = (
    "Supplier approval lets the supplier treat and supply the water. Dual "
    "approval means you separately need your own EPL or development consent "
    "to use it for this activity."
)

# ----------------------------------------------------------------------------
# SOURCE-DOCUMENTATION LOOKUP NOTES — scannable pointers (st.caption) to
# where to check, for fields with a public register.
# ----------------------------------------------------------------------------

# No direct per-scheme register exists for s.60/s.292 ministerial approval —
# framed as "where to start", not a definitive lookup.
MINISTERIAL_APPROVAL_LOOKUP_NOTE = (
    "Don't have this confirmed yet? Start with the "
    "[NSW Water Register](https://waterregister.waternsw.com.au/search/SearchWizard.jsp) "
    "or DPIE's [water treatment/sewerage works approvals guidance]"
    "(https://water.dpie.nsw.gov.au/our-work/local-water-utilities/approval-and-inspection-of-water-treatment-and-sewerage-works/apply-for-water-treatment-and-sewerage-works-approvals), "
    "or confirm directly with the supplier."
)

# NSW EPA's own public POEO register — a genuine per-licence search.
EPL_REGISTER_NOTE = (
    "Don't have the EPL details yet? Search the "
    "[NSW EPA public register](https://apps.epa.nsw.gov.au/prpoeoapp/) by "
    "licensee name or location."
)

# No public RWMP register exists yet — deliberately no link; add one once
# a register is confirmed.
RWMP_LOOKUP_NOTE = (
    "No public RWMP register is available to check this against — confirm "
    "current RWMP status directly with the supplier."
)

# ----------------------------------------------------------------------------
# ROADWORKS APPLICATION TYPES — each routes to its own Phase 3 spec table.
# ----------------------------------------------------------------------------
APPLICATION_TYPES = [
    "Concrete Mixing",
    "Dust Suppression",
    "Earthworks (Compaction)",
]

# General Phase 3 field (not gated here) — cross-checked against WHS
# contact-risk level in Phase 6.
WATER_CLASSES = ["Class A", "Class B", "Class C", "Class D", "Unclassified"]

# ----------------------------------------------------------------------------
# CONCRETE MIXING — AS 1379
# ----------------------------------------------------------------------------
# Table 2.1 — compressive strength vs a control sample, at 7d/28d.
CONCRETE_STRENGTH_MIN_PCT = 90
CONCRETE_STRENGTH_REF = "AS 1379 Table 2.1"

# Table 2.2 — impurity limits in the mixing water (hard specification limits).
CONCRETE_TABLE_2_2 = {
    "conc_sugar": {"label": "Sugar",          "unit": "mg/L", "max": 100, "ref": "AS 1379 Table 2.2 — AS 1141.35"},
    "conc_oil":   {"label": "Oil and grease", "unit": "mg/L", "max": 50,  "ref": "AS 1379 Table 2.2 — APHA 5520"},
    "conc_ph":    {"label": "pH",             "unit": "",     "min": 5.0, "ref": "AS 1379 Table 2.2 — AS/NZS 1580.505.1 or APHA 4500-H"},
}

# Filtered-water turbidity — a hard limit, plus an indicative target.
CONCRETE_TURBIDITY_MAX_NTU = 5.0
CONCRETE_TURBIDITY_TARGET_NTU = 1.5
CONCRETE_TURBIDITY_REF = "AS 1379 — filtered water turbidity"

# Table 2.3 — reportable only; AS 1379 sets no pass/fail threshold, so
# these are recorded, not gated.
CONCRETE_TABLE_2_3 = {
    "conc_tds":      {"label": "Total dissolved solids", "ref": "AS 1379 Table 2.3 — AS 3550.4"},
    "conc_chloride": {"label": "Chloride as Cl",          "ref": "AS 1379 Table 2.3 — APHA 4500-Cl"},
    "conc_sulphate": {"label": "Sulphate as SO3",         "ref": "AS 1379 Table 2.3 — AS 1289.4.2.1"},
    "conc_sodium":   {"label": "Sodium equivalent",       "ref": "AS 1379 Table 2.3 — APHA 3500"},
}

# Applies to Concrete Mixing too, at Earthworks' less-restrictive tier —
# see EARTHWORKS_MICRO_TABLE.
CONCRETE_ECOLI = {"label": "E. coli", "unit": "cfu/100mL", "max": 100,
                   "ref": "AGWR Phase 1 (2006) Table 3.8"}

# ----------------------------------------------------------------------------
# EARTHWORKS (COMPACTION) — Table 3-1 impurity limits (Sydney Water Recycled),
# hard limits; exceeding renders water unsuitable.
# ----------------------------------------------------------------------------
EARTHWORKS_TABLE_3_1 = {
    "ew_sugar":    {"label": "Sugar",                  "unit": "ppm", "max": 100,   "ref": "Table 3-1 — AS 1141.35"},
    "ew_oil":      {"label": "Oil and grease",        "unit": "ppm", "max": 50,    "ref": "Table 3-1 — APHA 5520"},
    "ew_ph":       {"label": "pH",                     "unit": "",    "min": 5.0,   "ref": "Table 3-1 — AS/NZS 1580.505.1 or APHA 4500-H"},
    "ew_tds":      {"label": "Total dissolved solids", "unit": "ppm", "max": 1700,  "ref": "Table 3-1 — AS 3550.4 or APHA 2540 C"},
    "ew_chloride": {"label": "Chloride as Cl",         "unit": "ppm", "max": 300,   "ref": "Table 3-1 — APHA 4500-Cl"},
    "ew_sulphate": {"label": "Sulphate as SO3",        "unit": "ppm", "max": 350,   "ref": "Table 3-1 — AS 1289.4.2.1 or APHA 4110 B"},
    "ew_alkali":   {"label": "Alkali (sodium equiv.)", "unit": "ppm", "max": 1500,  "ref": "Table 3-1 — ASTM C114 or APHA 3120 B"},
    "ew_tss":      {"label": "Total suspended solids", "unit": "ppm", "max": 15000, "ref": "Table 3-1 — AS 3550.4 or APHA 2540 D"},
}

# Applies to all three application types. Earthworks isn't public-facing,
# so uses a less-strict tier than Dust Suppression (E. coli ≤100 vs ≤1) —
# this split isn't explicit in source guidance, worth double-checking.
EARTHWORKS_MICRO_TABLE = {
    "ew_bod_mgl": {"label": "BOD",                  "unit": "mg/L",      "max": 20,  "ref": "AGWR Phase 1 (2006) Table 3.8"},
    "ew_ss_mgl":  {"label": "Suspended Solids (SS)", "unit": "mg/L",      "max": 30,  "ref": "AGWR Phase 1 (2006) Table 3.8"},
    "ew_ecoli":   {"label": "E. coli",               "unit": "cfu/100mL", "max": 100, "ref": "AGWR Phase 1 (2006) Table 3.8"},
}

# ----------------------------------------------------------------------------
# DUST SUPPRESSION — Table 3.8. Public-facing, so uses the "unrestricted
# access" municipal-use tier.
# ----------------------------------------------------------------------------
DUST_PATHOGEN_MAX_PCT = 0.1   # max % virus/protozoa/bacteria present
DUST_PATHOGEN_REF = "Table 3.8 — unrestricted access"
DUST_TABLE_3_8 = {
    "dust_bod_mgl": {"label": "BOD",                   "unit": "mg/L",      "max": 20, "ref": "Table 3.8 — unrestricted access"},
    "dust_ss_mgl":  {"label": "Suspended Solids (SS)",  "unit": "mg/L",      "max": 30, "ref": "Table 3.8 — unrestricted access"},
    "dust_ecoli":   {"label": "E. coli",                "unit": "cfu/100mL", "max": 1,  "ref": "Table 3.8 — unrestricted access"},
}

# ----------------------------------------------------------------------------
# PHASE 3 — the 12 elements of the RWMS framework
# (NSW Guidelines for Recycled Water Management Systems,
#  NSW Office of Water, May 2015, pp. 11-52)
# ----------------------------------------------------------------------------
RWMS_ELEMENTS = [
    "Commitment to responsible use and management of recycled water quality",
    "Assessment of the recycled water supply system",
    "Preventive measures for recycled water management",
    "Operational procedures and process control",
    "Verification of recycled water quality and environmental performance",
    "Management of incidents and emergencies",
    "Operator, contractor and end user awareness and training",
    "Community involvement and awareness",
    "Research and development",
    "Documentation and reporting",
    "Evaluation and audit",
    "Review and continual improvement",
]
RWMS_SOURCE = ("NSW Guidelines for Recycled Water Management Systems, "
               "NSW Office of Water, May 2015, pp. 11-52")

# ----------------------------------------------------------------------------
# PHASE 4 — POEO Act 1997 references and scheduled-activity thresholds
# ----------------------------------------------------------------------------
POEO_REFS = {
    "s48":  "POEO Act 1997, s.48 (p.41) — licensing requirement for scheduled activities (premises-based)",
    "s120": "POEO Act 1997, s.120 (pp.94-95) — prohibition of pollution of waters (Ch 5, Pt 5.3)",
    "s123": "POEO Act 1997, s.123 (p.95) — maximum penalties for water pollution offences",
    "sch1_cl35": ("POEO Act 1997, Schedule 1, Clause 35 (p.302) — road construction as a "
                  "scheduled activity. EXCLUDES maintenance/operation of existing roads — "
                  "most basic maintenance will NOT trigger this."),
    "s153A": "POEO Act 1997, s.153A — Pollution Incident Response Management Plan (PIRMP), mandatory for EPL holders",
}

# Schedule 1 Clause 35 tonnage thresholds for road construction.
SCH1_CL35_THRESHOLD_REGULATED = 50000     # tonnes, regulated area
SCH1_CL35_THRESHOLD_ELSEWHERE = 150000    # tonnes, elsewhere

SENSITIVE_ENVIRONMENTS = [
    "None / not sensitive",
    "Drinking water catchment",
    "Marine park",
    "Wetland (RAMSAR or other)",
    "Other sensitive receiving environment",
]

# ----------------------------------------------------------------------------
# PHASE 5 — Soil & Site Conditions. USCS classification + pavement-layer
# data feed Financial Feasibility's defaults (always PROCEEDs); plus a
# SAR/EC structural-stability screen against the natural subgrade soil
# (see SAR/EC section below, backend/phases/p5_soil_conditions.py).
# ----------------------------------------------------------------------------
SOIL_TABLE_REF = "Carter & Bentley (1991), Table 5-17; FHWA NHI-06-088"
SOIL_TABLE_CITATION = (
    "Source: Carter & Bentley (1991), Table 5-17.  \n"
    "Reference: FHWA NHI-06-088, Table 5-17  \n"
    "https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi06088.pdf"
)

# USCS reference table: dry unit weight and OMC by soil class. Midpoints
# are the arithmetic mean of each range, used to pre-fill editable OMC/
# density inputs.
USCS_SOIL_TABLE = {
    "Gravel/Sand mixtures": {
        "GW": {
            "description": "Well-graded, clean",
            "dry_unit_weight_kN_m3_range": (19.6, 21.1),
            "dry_unit_weight_kN_m3_mid": 20.35,
            "omc_range": (8, 11),
            "omc_mid": 9.5,
        },
        "GP": {
            "description": "Poorly-graded, clean",
            "dry_unit_weight_kN_m3_range": (18.1, 19.6),
            "dry_unit_weight_kN_m3_mid": 18.85,
            "omc_range": (11, 14),
            "omc_mid": 12.5,
        },
        "GM": {
            "description": "Well-graded, small silt content",
            "dry_unit_weight_kN_m3_range": (18.6, 21.1),
            "dry_unit_weight_kN_m3_mid": 19.85,
            "omc_range": (8, 12),
            "omc_mid": 10.0,
        },
        "GC": {
            "description": "Well-graded, small clay content",
            "dry_unit_weight_kN_m3_range": (18.1, 19.6),
            "dry_unit_weight_kN_m3_mid": 18.85,
            "omc_range": (9, 14),
            "omc_mid": 11.5,
        },
    },
    "Sands and sandy soils": {
        "SW": {
            "description": "Well-graded, clean",
            "dry_unit_weight_kN_m3_range": (17.2, 20.6),
            "dry_unit_weight_kN_m3_mid": 18.9,
            "omc_range": (9, 16),
            "omc_mid": 12.5,
        },
        "SP": {
            "description": "Poorly-graded, small silt content",
            "dry_unit_weight_kN_m3_range": (15.7, 18.6),
            "dry_unit_weight_kN_m3_mid": 17.15,
            "omc_range": (12, 21),
            "omc_mid": 16.5,
        },
        "SM": {
            "description": "Well-graded, small silt content",
            "dry_unit_weight_kN_m3_range": (17.2, 19.6),
            "dry_unit_weight_kN_m3_mid": 18.4,
            "omc_range": (11, 16),
            "omc_mid": 13.5,
        },
        "SC": {
            "description": "Well-graded, small clay content",
            "dry_unit_weight_kN_m3_range": (16.7, 19.6),
            "dry_unit_weight_kN_m3_mid": 18.15,
            "omc_range": (11, 19),
            "omc_mid": 15.0,
        },
    },
    "Fine-grained soils of low plasticity": {
        "ML": {
            "description": "Silts",
            "dry_unit_weight_kN_m3_range": (14.7, 18.6),
            "dry_unit_weight_kN_m3_mid": 16.65,
            "omc_range": (12, 24),
            "omc_mid": 18.0,
        },
        "CL": {
            "description": "Clays",
            "dry_unit_weight_kN_m3_range": (14.7, 18.6),
            "dry_unit_weight_kN_m3_mid": 16.65,
            "omc_range": (12, 24),
            "omc_mid": 18.0,
        },
        "OL": {
            "description": "Organic silts",
            "dry_unit_weight_kN_m3_range": (12.7, 15.7),
            "dry_unit_weight_kN_m3_mid": 14.2,
            "omc_range": (21, 33),
            "omc_mid": 27.0,
        },
    },
    "Fine-grained soils of high plasticity": {
        "MH": {
            "description": "Silts",
            "dry_unit_weight_kN_m3_range": (10.8, 14.7),
            "dry_unit_weight_kN_m3_mid": 12.75,
            "omc_range": (24, 40),
            "omc_mid": 32.0,
        },
        "CH": {
            "description": "Clays",
            "dry_unit_weight_kN_m3_range": (12.7, 18.6),
            "dry_unit_weight_kN_m3_mid": 15.65,
            "omc_range": (19, 36),
            "omc_mid": 27.5,
        },
        "OH": {
            "description": "Organic clays",
            "dry_unit_weight_kN_m3_range": (10.3, 15.7),
            "dry_unit_weight_kN_m3_mid": 13.0,
            "omc_range": (21, 45),
            "omc_mid": 33.0,
        },
    },
}

# Dry unit weight conversion: 1 kN/m3 = 101.97 kg/m3 — used to convert
# kN/m3 midpoints to kg/m3 for financial-phase volume calcs.
KN_M3_TO_KG_M3 = 101.97

# Base layer has no USCS classification — single OMC default, no category/class selection.
BASE_LAYER_DEFAULTS = {
    "omc_range": (8, 14),
    "omc_mid": 11.0,
    # kN/m3 default — matches FINANCIAL_DEFAULTS' base density_kg_m3 (1900)
    # via KN_M3_TO_KG_M3, so it won't silently diverge from that fallback.
    "density_kN_m3_mid": 18.6,
    "note": "Base layer OMC default per standard practice. "
            "No USCS classification required for base.",
}

# ----------------------------------------------------------------------------
# PHASE 5 — SAR/EC soil structural stability: whether the water risks
# degrading the natural subgrade's structure (dispersion/slaking). Never a
# hard REJECT — remediable via soil testing + gypsum/lime amendment.
#
# Stable if SAR <= SOIL_STABILITY_SLOPE*EC + SOIL_STABILITY_INTERCEPT
# (team-derived fit, see SOIL_SAR_EC_REF). EC is dS/m — don't mix with the
# USSL uS/cm axis below.
# ----------------------------------------------------------------------------
SOIL_SAR_EC_REF = (
    "Team-derived linear approximation of the SAR-EC "
    "structural-stability boundary in ANZG (2018) Water Quality for "
    "Irrigation and General Water Uses: Guidelines, draft revised Ch 4.2 "
    "s.3.2, Fig 2, p.12 — SAR = 4.3 x EC - 0.4 (EC in dS/m). Not an "
    "independently published/verified formula."
)
SOIL_STABILITY_SLOPE = 4.3
SOIL_STABILITY_INTERCEPT = -0.4

# Plain-language "what is this?" note for SAR/EC, shown in an expander on
# the Soil & Site Conditions page.
SAR_EC_WHAT_IS_THIS = (
    "**Sodium Adsorption Ratio (SAR)** measures the proportion of sodium to "
    "calcium/magnesium in the water — high SAR water can cause clay soils "
    "to disperse or slake, weakening the subgrade's structure.\n\n"
    "**Electrical Conductivity (EC)** measures the water's salinity — it "
    "acts alongside SAR, since higher EC partly offsets high-SAR water's "
    "dispersion risk (this is why the check below screens the two "
    "together, not separately).\n\n"
    "Both are standard parameters on a water-testing laboratory's report — "
    "request SAR and EC (in dS/m) when you submit the water sample. They "
    "typically come back on the **same lab report as the other water-"
    "quality parameters already collected in Water Quality (Phase 3)** — "
    "this is not usually a separate test run or a separate sample."
)

# USSL (Richards, 1954) C-class salinity boundaries — fixed, EC-only,
# shown for context. S1-S4 sub-classification omitted (unverified for this
# tool); SAR/EC check above is the operative risk call.
SOIL_USSL_REF = "USSL Diagram (Richards, 1954), USDA Agriculture Handbook No. 60"
SOIL_USSL_C_CLASS_US_CM = [
    (250,           "C1 (Low salinity hazard)"),
    (750,           "C2 (Medium salinity hazard)"),
    (2250,          "C3 (High salinity hazard)"),
    (float("inf"),  "C4 (Very high salinity hazard)"),
]

# FINANCIAL_REGIONS keys with average rainfall well below Figure 2's
# ~1000mm/yr assumption — salt leaching is slower there, so PROCEED/marginal
# results may understate risk. Indicative BOM averages only; confirm on-site.
SOIL_LOW_RAINFALL_REGIONS = {"Dubbo", "Wagga Wagga"}

# ----------------------------------------------------------------------------
# PHASE 6 — Worker Health & Safety (WHS)
# ----------------------------------------------------------------------------
WHS_REF = ("Work Health and Safety Act 2011 (NSW) & WHS Regulation 2017 (NSW); "
           "SafeWork NSW guidance on recycled/non-potable water")

# Mandatory pre-works confirmations. Shortfalls are remediable, so they
# return CONDITIONAL, not a hard REJECT.
WHS_CHECKS = [
    ("whs_notified_class",  "Workers notified of the water classification / source"),
    ("whs_health_risks",    "Health risks (pathogen/chemical exposure) communicated to workers"),
    ("whs_ppe",             "PPE requirements specified and PPE available on site"),
    ("whs_swms",            "SWMS / safe work procedure covering recycled-water use in place"),
    ("whs_signage",         "Signage / no-drinking & wash-facility controls in place"),
]

# Application method drives contact risk (and therefore treatment standard/cost).
APPLICATION_METHODS = ["Direct application (low contact)", "Sprayed (higher contact)"]
CONTACT_RISK_LEVELS = ["None expected", "Workers only", "Workers and public"]

WHS_METHOD_NOTES = {
    "Direct application (low contact)":
        "Direct application — lower exposure; standard PPE generally sufficient.",
    "Sprayed (higher contact)":
        "Spraying — check spray-drift risk and weather (wind) before application "
        "and set worker exclusion zones. Higher contact risk.",
}
# Pre-application weather/wind check, required before spraying.
WHS_SPRAY_WEATHER_REF = "WHS Act 2011 (NSW) s.18 — primary duty of care"

WHS_IRRIGATION_NOTE = ("Risk is largely mitigated by ensuring people do not come "
                       "into contact with the water during application.")
WHS_TREATMENT_NOTE = ("Treatment standard is directly linked to contact risk — "
                      "higher contact requires a higher treatment standard, which "
                      "increases cost.")
NSW_HEALTH_NOTE = ("NSW Health may be involved in the approval process where human "
                   "contact with recycled water is possible.")

# Indicative buffer-zone distance range to sensitive receptors, by AGWR
# class (Phase 3's water_class). Always CONDITIONAL — no source maps a
# distance directly to class; see AGWR_BUFFER_ZONE_LIMITATION_NOTE.
AGWR_BUFFER_ZONE_RANGE_METRES = {
    "Class A": (25, 30),
    "Class B": (25, 30),
    "Class C": (30, 50),
    "Class D": (50, 100),
}
AGWR_BUFFER_ZONE_REF = ("AGWR Phase 1 (2006) — indicative buffer-zone guidance by water "
                        "quality class; NSW Health recycled water guidelines on aerosol risk")
AGWR_BUFFER_ZONE_LIMITATION_NOTE = (
    "Buffer zone distances are indicative only, interpolated from AGWR Phase "
    "1 (2006) qualitative guidance. No NSW Health or AGWR source maps buffer "
    "distance directly to AGWR class. Confirm actual distance with NSW "
    "Health on a per-project basis.")

# Minimum AGWR class per contact-risk level (None = any class acceptable).
# Cross-checked against the class selected in Phase 3.
CONTACT_RISK_MIN_CLASS = {
    "None expected":      None,
    "Workers only":       "Class B",
    "Workers and public": "Class A",
}
WATER_CLASS_REF = "AGWR Phase 1 (2006) — water quality class framework"

# ----------------------------------------------------------------------------
# PHASE 7 — Financial Feasibility (never a hard reject). Pavement + dust-
# suppression water demand, trucked in, compared under normal/drought
# pricing. See backend/phases/p7_financial.py.
# ----------------------------------------------------------------------------
FINANCIAL_REF = ("Whole-of-life cost comparison vs potable baseline, including "
                 "trucking. Unfavourable cost is CONDITIONAL only — the engineer "
                 "may proceed for sustainability / supply-security reasons.")

# Starting figures — review with finance/trucking contractor/water authority
# before relying on operationally. Single source of truth: both
# frontend/pages/p7_financial.py and backend/phases/p7_financial.py fall
# back to these when a key is missing.
FINANCIAL_DEFAULTS = {
    # --- Section 1: Water costs ---
    "water_cost_mode": "Standard",       # "Standard" | "Custom"
    "region": "Port Macquarie",
    "potable_cost_normal": 4.44,         # $/kL — Custom mode only
    "potable_cost_drought": 8.84,        # $/kL — Custom mode only
    "recycled_cost_normal": 2.22,        # $/kL — Custom mode only

    # --- Section 2: Pavement profile (per layer) ---
    # "included" (default True) excludes a layer from volume/cost totals
    # while still showing its figures.
    "pavement_layers": {
        "subgrade": {"omc_pct": 12.0, "mc_pct": 8.0, "thickness_m": 0.3, "density_kg_m3": 1700.0, "included": True},
        "subbase":  {"omc_pct": 9.0,  "mc_pct": 6.0, "thickness_m": 0.2, "density_kg_m3": 1800.0, "included": True},
        "base":     {"omc_pct": 9.0,  "mc_pct": 5.0, "thickness_m": 0.2, "density_kg_m3": 1900.0, "included": True},
    },

    # --- Section 3: Road geometry ---
    "num_lanes": 2,
    "lane_width_m": 3.5,
    "shoulder_width_m": 1.0,
    "num_shoulders": 2,
    "road_length_m": 5000.0,

    # --- Section 4: Transport & operational costs ---
    "num_trucks": 5,
    "hire_rate_per_hr": 200.0,      # truck + driver only, verified 2026-07-24 — fuel calculated separately
    "fuel_efficiency": 40.0,        # L/100km
    "diesel_price": 2.00,           # $/L
    "trips_per_truck": 4,
    "hours_onsite": 6.0,            # hours per truck on site
    "truck_capacity_kL": 15.0,
    "potable_distance_km": 10.0,    # site <-> potable source, one-way
    "recycled_distance_km": 15.0,   # site <-> recycled source, one-way
    "area_type": "Urban",           # "Urban (dense city)" | "Urban" | "Rural" — sets avg_speed_kmh's default
    "avg_speed_kmh": 50.0,

    # --- Dust suppression — no application-type gate; untick "included"
    # if unused, same pattern as a pavement layer. ---
    "dust_suppression_included": True,
    "surface_area_m2": 36000.0,          # bare fallback only — live page overwrites from Road Geometry on first render
    "site_conditions": "Medium",
    "temperature_conditions": "Sunny",
    "applications_per_day": 5,
    "water_per_m2_L": 4.0,
    "effective_area_pct": 30.0,
    # Independent input, also used as dust_suppression_days in the
    # delivery-day split (see backend/phases/p7_financial.py).
    "project_duration_days": 20,

    # --- Concrete Kerb + Elements — no gate; toggleable via "included". ---
    "concrete_included": True,
    "kerb_type": "SL (standard road)",
    "water_cement_ratio": 0.42,
    "additional_concrete_volume_m3": 0.0,   # drainage pits, aprons, etc. — not covered by the kerb lookup
}

# Kerb concrete volume per metre of road length (m^3/m). Real-world data.
CONCRETE_KERB_VOLUME_PER_M = {
    "SA (standard residential)": 0.154,
    "SL (standard road)": 0.102,
}

# Water-cement-ratio -> water volume fraction. Real data, not a
# placeholder — the 0.38 entry (0.133) is corrected from a source typo (13.3).
CONCRETE_WATER_CEMENT_RATIO_TABLE = {
    0.35: 0.1225,
    0.38: 0.133,
    0.42: 0.147,
    0.45: 0.1575,
}

# Real-world region/rate data, not a placeholder.
FINANCIAL_REGIONS = {
    "Sydney":          {"potable_cost_normal": 3.41, "potable_cost_drought": 3.84, "recycled_cost_normal": 3.07},
    "Ballina":         {"potable_cost_normal": 6.82, "potable_cost_drought": 6.82, "recycled_cost_normal": 0.30},
    "Port Macquarie":  {"potable_cost_normal": 4.44, "potable_cost_drought": 8.84, "recycled_cost_normal": 2.22},
    "Central Coast":   {"potable_cost_normal": 2.72, "potable_cost_drought": 4.20, "recycled_cost_normal": 2.10},
    "Dubbo":           {"potable_cost_normal": 2.25, "potable_cost_drought": 6.00, "recycled_cost_normal": 1.45},
}

# Default average travel speed by area type, real-world reference data.
AREA_TYPE_SPEEDS = {"Urban (dense city)": 40.0, "Urban": 50.0, "Rural": 60.0}

# Sets water_per_m2_L / applications_per_day defaults when the corresponding
# selectbox changes — same auto-fill/editable pattern as AREA_TYPE_SPEEDS.
DUST_SITE_CONDITIONS_WATER_L_M2 = {"Low": 1.0, "Medium": 2.0, "High": 4.0}
DUST_TEMPERATURE_APPLICATIONS_PER_DAY = {"Overcast": 3, "Sunny": 4, "Hot and Sunny": 6}

# Optional OpenRouteService integration — geocodes an address and looks up
# driving distance, alongside always-available manual entry. If
# ORS_API_KEY isn't set, ORS_ENABLED is False and the UI hides address lookup.
ORS_API_KEY = os.getenv("ORS_API_KEY")
ORS_ENABLED = bool(ORS_API_KEY)

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"
ORS_VEHICLE_PROFILE = "driving-hgv"
# HGV = heavy goods vehicle, appropriate for water trucks. Change to
# "driving-car" if HGV routing fails in rural areas — directions URL derives from this.
ORS_DIRECTIONS_URL = f"https://api.openrouteservice.org/v2/directions/{ORS_VEHICLE_PROFILE}"


# ----------------------------------------------------------------------------
# External references
# ----------------------------------------------------------------------------
NSW_RECYCLED_WATER_ROADMAP_URL = (
    "https://www.water.dcceew.nsw.gov.au/our-work/plans-and-strategies/recycled-water-roadmap"
)

# ----------------------------------------------------------------------------
# REGULATION REFERENCE LINKS — URLs for the "Regulation Reference" panel
# only. Kept separate from the plain-text ref constants above (used verbatim
# in cards/PDF/Excel exports, which don't render markdown links).
#
# NSW legislation links go to legislation.nsw.gov.au, which redirects to the
# current in-force version — no update needed as Acts are amended. Verified
# 2026-07-24.
# ----------------------------------------------------------------------------
LGA1993_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/act-1993-030"
WMA2000_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/act-2000-092"
POEO1997_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/act-1997-156"
WHS2011_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/act-2011-010"
WHSREG2017_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/sl-2017-0404"
AGWR2006_URL = "https://www.waterquality.gov.au/sites/default/files/documents/water-recycling-guidelines-full-21.pdf"
NSW_OFFICE_OF_WATER_2015_URL = (
    "https://www.water.dcceew.nsw.gov.au/sites/default/files/2025-08/"
    "Section-60-NSW-Guildeines-for-Recycled-Water-Management-Systems.pdf"
)
ANZG2018_URL = "https://www.waterquality.gov.au/anz-guidelines"
AS1379_URL = "https://store.standards.org.au/search?q=AS+1379"
SYDNEY_WATER_TECH_SPEC_URL = (
    "https://www.sydneywater.com.au/plumbing-building-developing/"
    "provider-information/standards-specifications.html"
)
FHWA_NHI_06_088_URL = "https://www.fhwa.dot.gov/engineering/geotech/pubs/nhi06088.pdf"
USDA_HANDBOOK_60_URL = "https://www.ars.usda.gov/ARSUserFiles/20360500/hb60_pdf/hb60intro.pdf"
EPA_ACT_1979_URL = "https://legislation.nsw.gov.au/view/html/inforce/current/act-1979-203"
NSW_HEALTH_URL = "https://www.health.nsw.gov.au/environment/water/Pages/wastewater.aspx"


def _cited(text: str, *links: tuple[str, str]) -> str:
    """Append '  \\nSource: [Label](url) · ...' for the Regulation Reference
    panel's markdown rendering. No-op if no links given."""
    if not links:
        return text
    joined = " · ".join(f"[{label}]({url})" for label, url in links)
    return f"{text}  \nSource: {joined}"


def all_regulation_refs():
    """Flat list of (topic, citation) for the Regulation Reference panel."""
    dn = PHASE_DISPLAY_NAMES
    refs = []
    refs.append((f"{dn['supplier_approval']} — supplier: Council-run scheme",
                 _cited(SUPPLIER_APPROVAL_REFS["Council-run scheme"],
                        ("Local Government Act 1993", LGA1993_URL))))
    refs.append((f"{dn['supplier_approval']} — supplier: Water supply authority",
                 _cited(SUPPLIER_APPROVAL_REFS["Water supply authority"],
                        ("Water Management Act 2000", WMA2000_URL))))
    refs.append((f"{dn['supplier_approval']} — dual approval (user side)",
                 _cited(DUAL_APPROVAL_REF, ("POEO Act 1997", POEO1997_URL),
                        ("EP&A Act 1979", EPA_ACT_1979_URL))))
    refs.append((f"{dn['supplier_approval']} — stormwater approval pathway",
                 _cited(STORMWATER_APPROVAL_REF,
                        ("Local Government Act 1993", LGA1993_URL),
                        ("Water Management Act 2000", WMA2000_URL))))
    refs.append((f"{dn['water_quality']} — concrete mixing water",
                 _cited("AS 1379 Tables 2.1-2.3 — compressive strength, impurity limits, turbidity",
                        ("AS 1379", AS1379_URL))))
    refs.append((f"{dn['water_quality']} — earthworks (compaction)",
                 _cited("Table 3-1 impurity limits (Sydney Water Recycled)",
                        ("Sydney Water Technical Specification", SYDNEY_WATER_TECH_SPEC_URL))))
    refs.append((f"{dn['water_quality']} — dust suppression",
                 _cited("Table 3.8 — treatment processes & on-site controls (unrestricted access)",
                        ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['rwmp']} — RWMS framework",
                 _cited(RWMS_SOURCE, ("NSW Guidelines for Recycled Water Management Systems", NSW_OFFICE_OF_WATER_2015_URL))))
    for v in POEO_REFS.values():
        refs.append((f"{dn['site_runoff']} — POEO Act 1997", _cited(v, ("POEO Act 1997", POEO1997_URL))))
    refs.append((f"{dn['soil_conditions']} — soil & site",
                 _cited(SOIL_TABLE_REF, ("FHWA NHI-06-088", FHWA_NHI_06_088_URL))))
    refs.append((f"{dn['soil_conditions']} — SAR/EC structural stability",
                 _cited(SOIL_SAR_EC_REF, ("ANZG (2018)", ANZG2018_URL))))
    refs.append((f"{dn['soil_conditions']} — USSL salinity classification",
                 _cited(SOIL_USSL_REF, ("USDA Agriculture Handbook No. 60", USDA_HANDBOOK_60_URL))))
    refs.append((f"{dn['whs']} — WHS",
                 _cited(WHS_REF, ("WHS Act 2011", WHS2011_URL), ("WHS Regulation 2017", WHSREG2017_URL))))
    refs.append((f"{dn['whs']} — WHS: buffer zone",
                 _cited(AGWR_BUFFER_ZONE_REF, ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['whs']} — WHS: buffer zone limitation",
                 _cited(AGWR_BUFFER_ZONE_LIMITATION_NOTE, ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['whs']} — WHS: water class vs contact risk",
                 _cited(WATER_CLASS_REF, ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['whs']} — WHS: NSW Health",
                 _cited(NSW_HEALTH_NOTE, ("NSW Health — Wastewater management and water recycling", NSW_HEALTH_URL))))
    refs.append((f"{dn['financial']} — financial", FINANCIAL_REF))
    return refs


def supplier_approval_regulation_refs():
    """Flat list of (topic, citation) for Phase 1."""
    dn = PHASE_DISPLAY_NAMES
    refs = []
    refs.append((f"{dn['supplier_approval']} — supplier: Council-run scheme",
                 _cited(SUPPLIER_APPROVAL_REFS["Council-run scheme"],
                        ("Local Government Act 1993", LGA1993_URL))))
    refs.append((f"{dn['supplier_approval']} — supplier: Water supply authority",
                 _cited(SUPPLIER_APPROVAL_REFS["Water supply authority"],
                        ("Water Management Act 2000", WMA2000_URL))))
    refs.append((f"{dn['supplier_approval']} — dual approval (user side)",
                 _cited(DUAL_APPROVAL_REF, ("POEO Act 1997", POEO1997_URL),
                        ("EP&A Act 1979", EPA_ACT_1979_URL))))
    refs.append((f"{dn['supplier_approval']} — stormwater approval pathway",
                 _cited(STORMWATER_APPROVAL_REF,
                        ("Local Government Act 1993", LGA1993_URL),
                        ("Water Management Act 2000", WMA2000_URL))))
    return refs


def water_quality_regulation_refs():
    """Flat list of (topic, citation) for Phase 3."""
    dn = PHASE_DISPLAY_NAMES
    refs = []
    refs.append((f"{dn['water_quality']} — concrete mixing water",
                 _cited("AS 1379 Tables 2.1-2.3 — compressive strength, impurity limits, turbidity",
                        ("AS 1379", AS1379_URL))))
    refs.append((f"{dn['water_quality']} — earthworks (compaction)",
                 _cited("Table 3-1 impurity limits (Sydney Water Recycled)",
                        ("Sydney Water Technical Specification", SYDNEY_WATER_TECH_SPEC_URL))))
    refs.append((f"{dn['water_quality']} — dust suppression",
                 _cited("Table 3.8 — treatment processes & on-site controls (unrestricted access)",
                        ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    return refs


def rwmp_regulation_refs():
    """Flat list of (topic, citation) for Phase 2."""
    refs = []
    refs.append((f"{PHASE_DISPLAY_NAMES['rwmp']} — RWMS framework",
                 _cited(RWMS_SOURCE, ("NSW Guidelines for Recycled Water Management Systems", NSW_OFFICE_OF_WATER_2015_URL))))
    return refs


def site_runoff_regulation_refs():
    """Flat list of (topic, citation) for Phase 4."""
    refs = []
    for v in POEO_REFS.values():
        refs.append((f"{PHASE_DISPLAY_NAMES['site_runoff']} — POEO Act 1997", _cited(v, ("POEO Act 1997", POEO1997_URL))))
    return refs


def soil_conditions_regulation_refs():
    """Flat list of (topic, citation) for Phase 5."""
    dn = PHASE_DISPLAY_NAMES
    refs = []
    refs.append((f"{dn['soil_conditions']} — soil & site",
                 _cited(SOIL_TABLE_REF, ("FHWA NHI-06-088", FHWA_NHI_06_088_URL))))
    refs.append((f"{dn['soil_conditions']} — SAR/EC structural stability",
                 _cited(SOIL_SAR_EC_REF, ("ANZG (2018)", ANZG2018_URL))))
    refs.append((f"{dn['soil_conditions']} — USSL salinity classification",
                 _cited(SOIL_USSL_REF, ("USDA Agriculture Handbook No. 60", USDA_HANDBOOK_60_URL))))
    return refs


def whs_regulation_refs():
    """Flat list of (topic, citation) for Phase 6."""
    dn = PHASE_DISPLAY_NAMES
    refs = []
    refs.append((f"{dn['whs']} — WHS",
                 _cited(WHS_REF, ("WHS Act 2011", WHS2011_URL), ("WHS Regulation 2017", WHSREG2017_URL))))
    refs.append((f"{dn['whs']} — WHS: buffer zone",
                 _cited(AGWR_BUFFER_ZONE_REF, ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['whs']} — WHS: buffer zone limitation",
                 _cited(AGWR_BUFFER_ZONE_LIMITATION_NOTE, ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['whs']} — WHS: water class vs contact risk",
                 _cited(WATER_CLASS_REF, ("AGWR Phase 1 (2006)", AGWR2006_URL))))
    refs.append((f"{dn['whs']} — WHS: NSW Health",
                 _cited(NSW_HEALTH_NOTE, ("NSW Health — Wastewater management and water recycling", NSW_HEALTH_URL))))
    return refs


def financial_regulation_refs():
    """Flat list of (topic, citation) for Phase 7."""
    refs = []
    refs.append((f"{PHASE_DISPLAY_NAMES['financial']} — financial", FINANCIAL_REF))
    return refs