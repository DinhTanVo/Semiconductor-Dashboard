# Historical V5 technical reference

Run and report instructions are superseded by README.md.

# V5 update notes

This release directly updates the supplied V4 project. The supplied V3 archive was opened and its original BGA component structure and CSS were restored; it is not a newly generated approximation.

## Navigation and filters
- Five separate live pages, sticky navigation and Previous/Next controls.
- Offline HTML: five quick-navigation anchors and Back to quick navigation links.
- EDA: product, stage, process/parameter, equipment, subdivision, period and inclusive measurement-date filters. Stage/process/equipment changes reset invalid dependent selections.
- Full dataset scope resets EDA filters to the default process study; the parameter-specific charts remain one process at a time. Stage coverage is explicitly labeled full-dataset context.
- Underlying data viewer: all 11 tables, selected/full scope, literal search, typed sorting, 10/25/50/100 rows per page and CSV export of the entire searched/sorted scope, not just the current page.
- Technical model: 11 entities, PK/FK, principal cardinalities, conditional package relationship, grouped header colors, zoom and fit. Additional validated ancestry FKs are listed in entity fields to avoid crossing connectors.
- Current V4 appendix structure and four selected SPC display states are retained; V2/V3 test logs are not substituted.

The data and statistical methods are unchanged. Default Python runtime remains the tested host; the optional Dash adapter is not claimed as execution-tested.

---

# Semiconductor Manufacturing & Quality Analytics | V5

**Vo Tan Dinh | Engineering, Data & Process Improvement**

## Open the deliverables first

- `output/portfolio_summary.pdf`: six-page, context-first CV portfolio.
- `output/full_dashboard_report.pdf`: every website tab at default scope, expanded methods/dictionaries and four selected SPC display states.
- `output/preview_report.html`: self-contained offline snapshot with embedded chart images. Open directly in a browser. This is a report, not the live filtering application.
- `output/qa_evidence/`: screenshots at 1440, 1024 and 390 px.

## Run the live website

Python 3.10+ recommended. From the project folder:

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:8050`. The default host uses Python's standard-library HTTP server and local Plotly. No Node build, cloud connection, CDN, external data access or API key is needed. The host is intended for a local portfolio demonstration, not public production deployment.

An **optional Dash hosting adapter** is provided:

```bash
python -m pip install -r requirements-dash.txt
python app.py --dash
```

The Dash adapter embeds the same website and exposes the same Python analysis endpoint. The default standard-library runtime was browser-tested. Dash could not be installed in the build environment, so the optional adapter is not claimed as executed or tested. This is a reconstructed V4, not a byte-identical patch of the original V2/V3 archives.

## What changed in V4

- Overview uses the approved Stage / title / lead / paragraph / Engineers monitor / Output hierarchy. No Purpose or Process description labels were added.
- All three stage descriptions and the BGA two-interface text follow the approved copy, with spelling and punctuation corrections only.
- Manufacturing flow illustrations and BGA are rebuilt as responsive HTML components because the original V2 assets were unavailable. SMT retains the known paste-printing → SPI → placement → reflow → AOI → X-ray flow; exact original asset fidelity is not claimed.
- Business traceability is prominent; technical table relationships and fields are collapsed below it.
- Exposure compares subdivisions only within one process. Daily coverage is a collapsed completeness check.
- I/MR defaults to 250 consecutive observations. First-signal, reference, post-action, custom and full-history views never refit the study limits.
- Findings include measured differences, counts/denominators, implications and a next verification step. Financial savings and causal attribution are not invented.
- Root Cause retains period/subdivision comparisons, intervention timeline, event exposure, competing hypotheses, supporting cohort comparison and lot-level associations.
- 5 Whys/CAPA notes survive tab navigation in the same browser session and can be downloaded as JSON. They are not stored in a shared database.

## Data provenance and statistical boundaries

All manufacturing data is synthetic. Seed **7241** generates 120 lots, 3,000 wafers, 24,000 tracked packages, 119,566 process runs, 59,898 measurements and 1,200 defect events. The reconstructed generator reproduces the previously displayed assembly cohort counts:

| Period | Passed | Total | Failed | Yield |
|---|---:|---:|---:|---:|
| Reference | 7,925 | 7,964 | 39 | 99.51% |
| Disturbance | 9,702 | 10,061 | 359 | 96.43% |
| Post-action | 5,939 | 5,975 | 36 | 99.40% |

These are educational outcomes, not company production records. The tracked package sample does not represent every die on each wafer.

- Fab yield uses distinct wafers. Assembly yield uses tracked packages passing all assembly screens. Final first-pass uses attempt 1. Retest recovery uses only retested packages.
- Event counts are not defective-unit counts. Process screen failures may repeat on a unit.
- Filters use run-end time and touched-unit cohorts. Final attempts are linked to selected final-test runs; a later retest timestamp does not silently change the cohort.
- First 40 observations estimate frozen I/MR limits; minimum 20. Only beyond-3-sigma rules are implemented. Baseline approval, independence and MSA adequacy still need engineering review.
- Capability minimum 30. Cp/Cpk are withheld for detected instability, zero variation or failed normality screening (alpha .01). Overall sample SD is not substituted for within sigma.
- Independent Cp/Cpk example uses fixed normal quantiles in deterministic shuffled order, not manufacturing resampling. It uses the same screening functions.
- Simulated latent values, bias and noise are audit-only. Observational conclusions do not use them to claim a physical cause.
- Before/after differences and correlations are descriptive, not causal proof. Interventions are timestamped simulated records, not verified corrective-action effectiveness.

## Data generation and validation

The website only loads and validates CSVs. It never silently regenerates them.

```bash
python -m src.generate_data
# Validates existing complete data without rewriting it.
python -m src.generate_data --overwrite
# Explicit deterministic regeneration.
pytest -q
```

Validation covers keys, conditional wafer/package context, ancestry, equipment/process context, measurement decomposition, source die eligibility, process chronology, pass flags, event context and retest eligibility.

## Re-export both PDFs

```bash
python -m pip install -r requirements-export.txt
python -m playwright install chromium
python -m src.export_reports
```

For an existing Chromium executable, use `--browser-executable /path/to/chrome` or the `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` environment variable.

To include downloaded 5 Whys/CAPA notes:

```bash
python -m src.export_reports --notes-json investigation_notes.json
```

The exporter includes note text from the supplied JSON. Default export notes are explicitly blank; no investigation answers are fabricated. The PDF includes default scopes and selected SPC states, not every filter combination.

## Structure

- `app.py`: local HTTP runtime and optional Dash host.
- `config/settings.py`: dataset, process, display and statistical settings.
- `src/generate_data.py`: deterministic synthetic generator.
- `src/data.py`: loading, validation and analytical joins.
- `src/analysis.py`: pure shared calculations.
- `src/figures.py`: Plotly figures.
- `tabs/views.py`: five page layouts and approved text.
- `assets/`: local CSS, browser behavior and bundled Plotly.js.
- `src/export_reports.py`: offline HTML and both PDF exports.
- `src/capture_ui.py`: actual browser checks and screenshots.
- `tests/`: reproducibility, grain, statistics, scope and export checks.

## Quality evidence

`output/test_results.txt` records the executed automated suite. `output/browser_checks.json` records actual browser checks and explicitly distinguishes the tested runtime from the optional Dash adapter. `output/export_manifest.json` records export scope and CSV SHA-256 values. No claims are made about production qualification or statistical assumptions beyond the implemented checks.
