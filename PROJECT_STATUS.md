# PROJECT STATUS

_Last updated: 2026-10-10_

**Scope:** this is a **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery as the warehouse and query engine. There is no GCP project, and no cloud resources are used or planned.

**Current phase:** Phase 0 complete / local DuckDB star schema built; Phase 1 architecture documents still to be written

**Decisions made**
- D-001 (user, 2026-10-06): implementations use DuckDB (local warehouse, DQ checks, tests).
- D-002 (user, 2026-10-10): local-only. DuckDB stands in for Google Cloud and BigQuery. No GCP project, no `gcloud`, no cloud phase. This supersedes D-001's "BigQuery-specific features demonstrated in the cloud phase". It also makes Dataflow/Beam and the BigQuery region question moot.
- D-003 (user, 2026-10-10): the query language is DuckDB SQL, written idiomatically. This supersedes D-001's "BigQuery-portable" clause.
- D-004 (user, 2026-10-10): no dbt. Transformations stay as plain SQL files under `sql/`, run by `src/transformation/build_warehouse.py`.
- D-005 (user, 2026-10-10): no Prometheus, Grafana or FastAPI.
- D-006 (user, 2026-10-10): `.gitignore` extended to cover `data/` and credential patterns. The nine files already tracked under `data/` are not yet untracked (see Next).

**Completed**
- Read governing docs (Master Agent Prompt, GCP child prompt, `GCP.md`).
- Dataset profiled with DuckDB (counts, keys, grain, integrity, nulls, date ranges, fan-out, reconciliation, delivery/review association).
- Licence verified (CC BY-NC-SA 4.0, via Kaggle API metadata).
- `docs/phase0/PHASE0_DISCOVERY.md` written.
- Local DuckDB star schema (`sql/staging|dimensions|facts|validation`, `src/transformation/build_warehouse.py`, `docs/data/DATA_MODEL.md`, `EDA_FINDINGS.md`) — **verified 2026-10-10**: build succeeds, all 9 tables populated, 22/22 reconciliation checks pass.
- `.gitignore` covers `*.duckdb`, caches, `data/` and credential patterns.
- `README.md` written (dataset download from Kaggle, build steps); `docs/HANDOFF.md` written.
- `notebooks/01_dataset_discovery.ipynb` repaired and stored with a clean run (commit `d5e8d1e`): 44 cells, no errors, findings, decisions table and date-outlier check included.
- `build_warehouse.py` converts the Kaggle geolocation CSV to Parquet on first run; tested for CSV-only, Parquet-present and missing-file cases.

**In progress**
- Nothing.

**Blocked / waiting on user**
- ML target: low review score, or late delivery plus the weekly forecast.
- Whether to untrack `data/` from Git, and whether to rewrite history.

**Next**
1. Decide the ML target.
2. Untrack `data/` with `git rm -r --cached data/` (files stay on disk) if the user agrees.
3. Phase 1 — Architecture (`ARCHITECTURE.md`, `DECISIONS.md`, `LEAKAGE_ANALYSIS.md`), written for a local DuckDB design.

**Tests:** warehouse build runs 22 in-script reconciliation checks (all pass). No `tests/` directory or pytest suite yet.

**Evidence:** local only. Phase 0 report and warehouse validation output.

**Cloud resources:** none, by decision (D-002).

**Estimated cost:** $0.

**Security status:** no secrets found or created. `.gitignore` now blocks common credential files. Raw `data/` is still tracked in Git until untracked.

**Open decisions:** ML target; untracking `data/` and any history rewrite.

**Known limitations:** the project docs (Master Agent Prompt, GCP child prompt, `GCP.md`) still describe BigQuery, Dataflow, Vertex AI and monitoring services. They are the original brief and have not been rewritten to match D-002 to D-005.
