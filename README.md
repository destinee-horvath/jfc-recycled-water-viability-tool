# Recycled Water Viability Assessment Tool

A web-based decision-support tool that screens whether a recycled water source
is viable for a given roadworks application under NSW legislation and IPWEA
guidelines. It guides practitioners through **seven assessment phases** -
always all editable, in any order - and rolls every check up into a
**blocking / pending / confirmed** readiness checklist, with a full audit
trail. There is no single pass/fail verdict or numeric score: each check
keeps its own outcome (PROCEED / CONDITIONAL / REJECT) so the practitioner
sees exactly what's confirmed and what still needs action.

> **Disclaimer:** This tool provides a preliminary viability screen and does
> **not** replace formal EPA, council, or water-authority approval. All outputs
> must be verified against the cited legislation by a qualified practitioner
> before any works commence.

---

## What the tool covers

### Phase 1 - Supplier & Dual Approval *(mandatory)*
Verifies that **both** the supplier's statutory approval and the user's own
approval to use the water are in place. Every gate is a strict pass/reject
except dual approval. Supported supplier types:
- Council-run schemes (LG Act 1993, s.60)
- Water supply authorities (Water Management Act 2000, s.292)
- Private schemes - greywater / blackwater (LG Act 1993, s.68)
- Stormwater - its own alternative-approval checker, since the s.60/s.292/s.68
  framework above doesn't apply to it.

A licensed effluent discharge point alone does **not** constitute approval to
use the water. Dual approval (does the user's own EPL/development consent
permit this specific use?) has three states - Permitted (PROCEED), Not
permitted (REJECT), and Unconfirmed (CONDITIONAL) - and defaults to
Unconfirmed so the engineer isn't forced into a decision before checking
their documents.

### Phase 2 - Water Quality
Each roadworks application is assessed against its own hard specification
table - no generic case-by-case screen:
- **Concrete Mixing** - AS 1379 Table 2.1 (compressive strength ≥ 90% of a
  control sample), Table 2.2 impurity limits (sugar, oil & grease, pH), and
  filtered-water turbidity (≤ 5 NTU, target ≤ 1.5 NTU). Table 2.3 (TDS,
  chloride, sulphate, sodium equivalent) is recorded for the file only - AS
  1379 sets no pass/fail threshold for these.
- **Dust Suppression** - Table 3.8 (unrestricted-access municipal-use tier):
  virus/protozoa/bacteria present (< 0.1%), BOD (< 20 mg/L), SS (< 30 mg/L),
  E. coli (< 1 cfu/100mL).
- **Earthworks (Compaction)** - Table 3-1 impurity limits (Sydney Water
  Recycled): sugar, oil & grease, pH, TDS, chloride, sulphate, alkali, TSS.

The intended AGWR water class (A–D) is still selected here as a general
field - Phase 6 cross-checks it against the WHS contact-risk level.

### Phase 3 - Recycled Water Management Plan *(mandatory)*
Confirms that an approved RWMP is in place and lists compaction/subgrade
moisture preparation as an approved end use - either gate missing is a hard
**REJECT**. Coverage of all **12 elements** of the NSW RWMS framework (NSW
Office of Water, May 2015) and RWMP currency are shortfalls only - flagged
**CONDITIONAL**, never a hard reject.

### Phase 4 - Site Runoff & EPL Risk
Screens the site against POEO Act 1997 obligations. **No hard reject at this
phase** - every shortfall returns CONDITIONAL:
- Scheduled-activity threshold (Schedule 1, Clause 35) for new road construction,
  and whether an Environment Protection Licence (EPL) is in place and covers
  recycled-water use.
- Runoff and receiving environment sensitivity (proximity to waters, drainage
  direction, drinking water catchments, marine parks, wetlands).
- PIRMP for EPL holders (s.153A).
- Ponding/overflow risk and containment/emergency response documentation.

### Phase 5 - Soil & Site Conditions
Flags conditions that trigger verification testing rather than auto-rejecting:
- Soil classification (clay, sandy, granular, mixed) with reactivity guidance.
- Slope gradient and elevation variability.
- Proximity to sensitive environments.
- pH/SAR/EC soil-suitability triggers - shown when Phase 2's application is
  Earthworks (Compaction), where moisture content most directly affects
  compaction outcomes - driving an **Optimum Moisture Content (OMC)** testing
  flag where salinity or SAR is elevated (testing must use the actual
  recycled water source).

### Phase 6 - Worker Health & Safety *(mandatory)*
Checks all WHS Act 2011 / WHS Regulation 2017 requirements before works
commence. It's a strict-liability regime (no hard reject - shortfalls return
**CONDITIONAL**, action required before works start):
- Application method (direct vs. sprayed) - spraying requires a pre-application
  wind/weather check.
- Human-contact risk level (none / workers only / workers and public).
- Proximity (within 50 m) to houses, schools, playing fields, roads, public
  open space, or water bodies - spray buffer zone.
- The Phase 2 water class must meet a minimum standard for the contact-risk
  level (None: any class; Workers only: Class B or better; Workers and
  public: Class A).
- Worker notification, health-risk communication, PPE, SWMS, and signage.

### Phase 7 - Financial Feasibility
Whole-of-project water cost comparison, ported cell-for-cell from the
client's own Excel costing model (treated as ground truth):
- Combined water volume across pavement moisture conditioning, dust
  suppression, and concrete kerb/elements - always summed together.
- Water cost and transport cost (truck fleet, trips, distance) compared
  between a potable and a recycled source, under both normal and drought
  potable pricing.
- Optional address-based distance lookup (driving distance via
  OpenRouteService) as an alternative to entering distances manually.
- A recycled-source break-even distance chart showing the distance at which
  recycled water stops being cost favourable.

An unfavourable cost comparison returns **CONDITIONAL only, never a REJECT**
- the practitioner may proceed for sustainability or supply-security reasons.

---

## Supported application types

Concrete Mixing · Dust Suppression · Earthworks (Compaction)

Water sources: **Treated effluent**, **Stormwater**, **Other** - Stormwater
follows a separate approval pathway (the standard s.60/s.292/s.68 supplier
framework in Phase 1 does not apply to it).

---

## Key features

| Feature | Detail |
|---|---|
| Phase progress indicator | Colour-coded bar across all phases |
| Colour-coded outcomes | PROCEED (green) · CONDITIONAL (amber) · REJECT (red) at check and phase level |
| Save & load | Assessments saved as re-importable CSV with a timestamp and "Assessed by" field |
| PDF Readiness Summary | One-page export listing confirmed items, pending actions, and blockers |
| Excel export | Colour-coded .xlsx export of the full assessment (display-only, not re-importable) |
| Comparison view | Side-by-side phase-outcome comparison of two saved assessments |
| Regulation Reference | In-app panel citing the relevant Act, section, and guideline for every check |
| Audit trail | Every save records the assessor name, project name, and ISO timestamp |
| Input validation | Non-negative enforcement on all distance, cost, and flow inputs |
| Address-based distance lookup | Optional OpenRouteService geocoding to fill in Phase 7's driving distances |

---

## Running locally

### Prerequisites

- Python 3.9 or later
- `pip`

### Steps

```bash
# 1. Navigate to directory
cd jfc-recycled-water-viability-tool/src

# 2. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt


# 3. Launch the app
streamlit run streamlit_app.py
```

The app opens automatically in your default browser at `http://localhost:8501`.

Saved assessments are written to a `saved_assessments/` folder in the same
directory and persist between sessions.

---

## Deployment

### Streamlit Community Cloud (demo / review)

1. Push the `src/` folder contents to a GitHub repository.
2. Sign in at [share.streamlit.io](https://share.streamlit.io) and create a new
   app pointing to the repository; `streamlit_app.py` is detected automatically.
3. Streamlit installs `requirements.txt` on each deploy.

> **Note:** Community Cloud has an ephemeral filesystem - files saved to
> `saved_assessments/` do not persist across restarts. Users should download the
> CSV copy from the Summary page to retain their work.

### Internal / production hosting

The app can be containerised and hosted on any cloud or on-premises server:

```
streamlit run streamlit_app.py --server.port 8501
```

For persistent storage, replace the local CSV save/load functions in
`backend/persistence.py` with a cloud storage bucket or database. The rest of
the application is unaffected.

---

## Project structure

The app is split into an independent `frontend/` (UI) and `backend/`
(decision logic + persistence), each broken down one file per phase so a new
phase - or a new page - is additive: a new module plus one registry line,
with no changes to existing files.

```
src/
├── streamlit_app.py       # Thin entry point (Streamlit Cloud auto-detects this path)
├── config.py               # Colour theme and all static reference data (shared)
├── requirements.txt
├── requirements-dev.txt     # + pytest, for running tests/
├── saved_assessments/      # CSV audit files (created on first save)
├── tests/                   # REJECT/CONDITIONAL/PROCEED coverage per phase + orchestration
│
├── frontend/
│   ├── app.py               # main() + sidebar() - wires everything together
│   ├── theme.py              # Colour constants + badge()
│   ├── styles.py              # Page-wide CSS
│   ├── refdata.py             # Cached static reference data (regs, RWMS, phase lookup)
│   ├── state.py                # Session-state init + phase Next/Save actions
│   ├── components.py           # Shared widgets: progress bar, validated inputs, result card
│   └── pages/                   # One module per page + the PAGE_FUNCS registry
│       ├── setup.py, summary.py, compare.py
│       └── p1_supplier_approval.py … p7_financial.py
│
└── backend/
    ├── models.py               # CheckResult / PhaseResult data structures
    ├── helpers.py               # Small helpers shared by more than one phase
    ├── orchestration.py          # run_assessment() / readiness_summary()
    ├── persistence.py             # CSV save/load (swap for a DB/bucket client later)
    ├── pdf.py                      # Readiness-summary PDF export
    ├── excel.py                     # Colour-coded Excel (.xlsx) export
    ├── ors_distance.py                # Optional OpenRouteService geocoding/driving-distance lookup
    └── phases/                         # One module per phase + the PHASE_FUNCS registry
        └── p1_supplier_approval.py … p7_financial.py
```

`import backend as B` still works exactly as before - `backend/__init__.py`
re-exports the full public API, so nothing outside these two packages needs
to change when a phase or page is added.

### Adding a new phase

1. Add its `(id, label, desc, mandatory)` entry to `config.PHASES`, and add
   its id to `config.FLAT_PHASE_ORDER` / `GROUPED_PHASE_ORDER`.
2. Add `backend/phases/<name>.py` with `assess_<name>(inp, ctx) -> PhaseResult`,
   and register it in `backend/phases/__init__.py`.
3. Add `frontend/pages/<name>.py` with `page_<name>(results)`, and register it
   in `frontend/pages/__init__.py`.

---

## Acknowledgement

This project made use of Claude AI throughout its development - primarily in
building out the frontend, as well as in debugging and general code cleanup.
