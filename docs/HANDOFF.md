# Handover: GCP Retail Analytics (local DuckDB build)

_Written 2026-10-10 to consolidate several separate Claude chats into one; updated 2026-10-11. Read this first in a new chat, then `PROJECT_STATUS.md`._

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

Full entries, with design decisions DD-01 to DD-10, are in `DECISIONS.md`. No decisions are open.

## Current state

- **Warehouse:** star schema with 4 facts and 5 dimensions in DuckDB. `build_warehouse.py` builds it and runs 22 reconciliation checks, all passing as of 2026-10-11.
- **Layout:** `sql/{staging,dimensions,facts,validation}/`, `src/transformation/`, `scripts/visualize_schema.py`, `docs/data/` (data model, EDA findings, `star_schema.png`), `docs/phase0/PHASE0_DISCOVERY.md`, `docs/ml/LEAKAGE_ANALYSIS.md`, and `ARCHITECTURE.md` and `DECISIONS.md` at the root.
- **Knowledge graph:** graphify is installed for Claude and Codex (`.claude/`, `.codex/`, `CLAUDE.md`, `AGENTS.md`). `graphify-out/` was built on 2026-10-06 from the docs and is now stale. Refresh with `graphify update .`.
- **Dataset download:** see `README.md`.

## Data findings (Phase 0 and EDA)

- Licence: CC BY-NC-SA 4.0 (verified through Kaggle API metadata).
- 99,441 `customer_id` values map to 96,096 real customers; 96.9% bought once. Use `customer_unique_id` for customer analysis.
- `review_id` is not unique (814 surplus rows).
- Joining items, payments and reviews side by side inflates revenue by 5.0%. Aggregate each child table to order grain before joining.
- Usable forecast window: 2017-01 to 2018-08, about 87 weeks.
- Late delivery goes with lower review scores (2.57 vs 4.29 average).

## Open work

1. **Discovery notebook: done.** Repaired and stored with a clean run in commit `d5e8d1e` (44 cells, no errors, findings, decisions table and date-outlier check). The separate notebook generator script is not wanted and does not need recovering.
2. **Geolocation step: done.** `build_warehouse.py` now converts the Kaggle CSV to Parquet on first run if only the CSV is present (tested for CSV-only, Parquet-present and missing-file cases).
3. **ML target and `data/`: done** (D-007, D-008).
4. **Phase 1 documents: done** (2026-10-11): `ARCHITECTURE.md`, `DECISIONS.md`, `docs/ml/LEAKAGE_ANALYSIS.md`.
5. **Phase 2 baselines: done** (2026-10-11). `sql/ml/late_delivery_features.sql`, `src/ml/late_delivery_baseline.py`, `src/ml/forecast_baseline.py`, metrics in `reports/`, write-up in `docs/ml/PHASE2_BASELINES.md`. Logistic regression is the best late-delivery model so far (PR-AUC 0.184 against a base rate of 0.085); seller history adds almost nothing; naive and the 8-week average win the forecast at 1 and 4 weeks.
6. **Tests: done.** `uv run pytest` runs 27 tests (leakage rules for the feature SQL on a mini warehouse, forecast no-lookahead, geolocation conversion, and recounts on the real warehouse).
7. **Feature experiment: done.** Route, category and trailing-28-day history did not help (DD-10); v1 stays the reference. Open next: test the drift explanation, recalibrate, better forecast models.
8. **Unverified:** BigQuery, Dataflow and Vertex AI pricing; Apache Beam on Python 3.13 on Windows. Both only matter if the cloud returns.

## Environment notes

- `uv` may need `--native-tls` on this machine. On Windows, set `PYTHONIOENCODING=utf-8` when printing DuckDB tables, or the console codec raises an error.
- `nbformat` and `nbconvert` are not project dependencies.
- `main.py` and `main.ipynb` were deleted by the user in commit `ac1ae8d`.
- Notebooks resolve `data/` relative to the working directory. A relative `data/...` path fails when the kernel starts in `notebooks/`; use a path built from the repo root.
