# Handover: GCP Retail Analytics (local DuckDB build)

_Written 2026-10-10 to consolidate several separate Claude chats into one; updated 2026-10-13. Read this first in a new chat, then `PROJECT_STATUS.md`._

## What this project is now

A **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery. The original cloud brief (Master Agent Prompt, `GCP.md`, the Retail Analytics project document) is deliberately left unchanged, because parts of it may come back later.

## Decisions (made by the user)

| ID | Decision |
|---|---|
| D-001 | Implementations use DuckDB. |
| D-002 | Local-only. No GCP project, no `gcloud`, no cloud phase. Makes Dataflow/Beam and the BigQuery region moot. |
| D-003 | Query language is DuckDB SQL, written idiomatically (supersedes "BigQuery-portable"). |
| D-004 | No dbt. Plain SQL files in `sql/`, run by `src/transformation/build_warehouse.py`. |
| D-005 | No Prometheus, Grafana or FastAPI. |
| D-006 | `.gitignore` covers `*.duckdb`, `data/` and credential patterns. |
| D-007 | ML target: late delivery (one order, predicted at purchase) plus a weekly order forecast. |
| D-008 | `data/` untracked from Git (commit `d8f6954`); history not rewritten. |

Full entries, with design decisions DD-01 to DD-15, are in `DECISIONS.md`. No decisions are open.

## Current state (2026-10-13)

All in-scope phases are complete; see `PROJECT_STATUS.md` for the phase table and `docs/AUDIT.md` for the final audit. Nothing is in progress or blocked.

- **Warehouse:** star schema, 4 facts and 5 dimensions. `uv run python src/transformation/build_warehouse.py` builds it and runs 22 reconciliation checks.
- **Analytics:** `sql/analytics/` (8 queries), `src/analytics/run_analytics.py` (tables to `reports/analytics/`, charts to `docs/analytics/figures/`), findings in `docs/analytics/BUSINESS_INSIGHTS.md`.
- **ML:** late-delivery ranking model and weekly forecast. **The notebooks `notebooks/02_late_delivery_model.ipynb` and `03_weekly_forecast.ipynb` present the work with charts** (stored with outputs; they call the tested code in `src/ml/`). Interactive marimo versions are in `notebooks/marimo/` (run with `uv run marimo edit <file>`). Written summary: `docs/ml/MODEL_CARD.md`; experiment write-ups are `PHASE2_BASELINES.md`, `DRIFT_ANALYSIS.md` and `RECALIBRATION_AND_WINDOW.md` in the same folder. Code is in `src/ml/` and `sql/ml/`, saved metrics in `reports/`.
- **Power BI:** `powerbi/RetailAnalytics.pbip` with `docs/powerbi/DAX_SPECIFICATION.html` and `DASHBOARD_MOCKUP.html`, all generated from `src/powerbi/model_spec.py` (edit that, then re-run the three `build_*.py` scripts; do not hand-edit generated files). Data export: `uv run python src/powerbi/export_data.py`. **Desktop's first open failed on a measure/column name clash ignoring case (fixed, with a test); nothing further is confirmed**, so expect more first-open fixes one at a time. Next step for whoever has Desktop: follow `powerbi/README.md`, set `DataFolder`, run the first-open checklist, and fix anything Desktop reports (then change the generator, not the output).
- **Tests:** `uv run pytest`, 95 tests, about 45 seconds. The schema-validation test downloads Microsoft's JSON schemas on first run and is skipped when offline.
- **Other documents:** `ARCHITECTURE.md`, `DECISIONS.md` (D-001 to D-008, DD-01 to DD-15), `SECURITY.md`, `COST.md`, `docs/LESSONS_LEARNED.md`.
- **Knowledge graph:** graphify is installed for Claude and Codex (`.claude/`, `.codex/`, `CLAUDE.md`, `AGENTS.md`). The graph covers the code as of 2026-10-13; the newest documents are not in it until `/graphify --update` is run. The graph's cache and dated backups are git-ignored.
- **Dataset download:** see `README.md`.

## Data findings (Phase 0 and EDA)

- Licence: CC BY-NC-SA 4.0 (verified through Kaggle API metadata).
- 99,441 `customer_id` values map to 96,096 real customers; 96.9% bought once. Use `customer_unique_id` for customer analysis.
- `review_id` is not unique (814 surplus rows).
- Joining items, payments and reviews side by side inflates revenue by 5.0%. Aggregate each child table to order grain before joining.
- Usable forecast window: 2017-01 to 2018-08 (85 clean weeks).
- Late delivery goes with lower review scores (2.57 vs 4.29 average).
- The delivery promise was shortened sharply in 2018 (75% of August orders promised in under 20 days); this broke the late-delivery model's ranking that month.

## Open items

1. Dependency vulnerability scan (no scanner installed).
2. Re-execute the discovery notebook (no notebook runner installed).
3. Test the geolocation conversion on Kaggle's original CSV.
4. Run `/graphify --update` to add the newest documents to the graph.
5. **Unverified, only matters if the cloud returns:** BigQuery, Dataflow and Vertex AI pricing; Apache Beam on Python 3.13 on Windows.

## Environment notes

- `uv` may need `--native-tls` on this machine. On Windows, set `PYTHONIOENCODING=utf-8` when printing DuckDB tables, or the console codec raises an error.
- `nbformat` and `nbconvert` are not project dependencies. `ipykernel` and `pytest` are declared dev dependencies; do not install packages by hand into `.venv`, because `uv sync` and `uv remove` delete anything undeclared.
- `main.py` and `main.ipynb` were deleted by the user in commit `ac1ae8d`.
- Notebooks resolve `data/` relative to the working directory. A relative `data/...` path fails when the kernel starts in `notebooks/`; use a path built from the repo root.
