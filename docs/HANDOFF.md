# Handover: GCP Retail Analytics (local DuckDB build)

_Written 2026-10-10 to consolidate several separate Claude chats into one. Read this first in a new chat, then `PROJECT_STATUS.md`._

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

**Still open:** the ML target (low review score, or late delivery plus the weekly forecast), and whether to untrack the 9 files in `data/` that Git already tracks (`git rm -r --cached data/`; history rewrite not proposed).

## Current state

- **Warehouse:** star schema with 4 facts and 5 dimensions in DuckDB. `build_warehouse.py` builds it and runs 22 reconciliation checks, all passing as of 2026-10-10.
- **Layout:** `sql/{staging,dimensions,facts,validation}/`, `src/transformation/`, `scripts/visualize_schema.py`, `docs/data/` (data model, EDA findings, `star_schema.png`), `docs/phase0/PHASE0_DISCOVERY.md`.
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

1. **Discovery notebook.** `notebooks/01_dataset_discovery.ipynb` may still be an older generation. It can lack the Finding cells, the decisions table and the date-outlier check, and may contain DuckDB reserved-word aliases (`share`, `month`, `rows`) and a `.style` call that fail when run. The user does not want the separate notebook generator script recovered. Check the notebook, repair it in place if needed, then execute it so its outputs are reproducible.
2. **Geolocation step: done.** `build_warehouse.py` now converts the Kaggle CSV to Parquet on first run if only the CSV is present (tested for CSV-only, Parquet-present and missing-file cases).
3. **Decide the ML target** and untracking of `data/`.
4. **Tests.** No `tests/` directory or pytest suite yet.
5. **Phase 1 documents:** `ARCHITECTURE.md`, `DECISIONS.md`, `LEAKAGE_ANALYSIS.md`, written for the local DuckDB design.
6. **Unverified:** BigQuery, Dataflow and Vertex AI pricing; Apache Beam on Python 3.13 on Windows. Both only matter if the cloud returns.

## Environment notes

- `uv` may need `--native-tls` on this machine.
- `nbformat` and `nbconvert` are not project dependencies.
- `main.py` and `main.ipynb` were deleted by the user in commit `ac1ae8d`.
- Notebooks resolve `data/` relative to the working directory. A relative `data/...` path fails when the kernel starts in `notebooks/`; use a path built from the repo root.
