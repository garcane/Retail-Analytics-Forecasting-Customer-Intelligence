# PROJECT STATUS

_Last updated: 2026-10-11_

**Scope:** this is a **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery as the warehouse and query engine. There is no GCP project, and no cloud resources are used or planned.

**Current phase:** Phase 1 (architecture documents) complete; next is the pytest suite, then Phase 2 baselines

**Decisions made:** D-001 to D-008 and design decisions DD-01 to DD-07, all recorded in [DECISIONS.md](DECISIONS.md). Latest: D-007 (2026-10-11) sets the ML target to late delivery plus a weekly order forecast; D-008 (2026-10-11) untracks `data/` from Git without rewriting history.

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
- `data/` untracked from Git (commit `d8f6954`, files kept on disk); build re-verified 22/22 afterwards.
- Phase 1 documents written: `ARCHITECTURE.md`, `DECISIONS.md`, `docs/ml/LEAKAGE_ANALYSIS.md` (target figures checked against `warehouse.duckdb`).

**In progress**
- Nothing.

**Blocked / waiting on user**
- Nothing.

**Next**
1. pytest suite (`tests/`): build, validation checks, geolocation conversion.
2. Phase 2: late-delivery baseline and naïve / moving-average weekly forecast, following `docs/ml/LEAKAGE_ANALYSIS.md`.
3. Refresh the graphify graph (`graphify update .`).

**Tests:** warehouse build runs 22 in-script reconciliation checks (all pass). No `tests/` directory or pytest suite yet.

**Evidence:** local only. Phase 0 report and warehouse validation output.

**Cloud resources:** none, by decision (D-002).

**Estimated cost:** $0.

**Security status:** no secrets found or created. `.gitignore` blocks common credential files. `data/` is untracked; earlier commits still contain it (no history rewrite, D-008).

**Open decisions:** none.

**Known limitations:** the project docs (Master Agent Prompt, GCP child prompt, `GCP.md`) still describe BigQuery, Dataflow, Vertex AI and monitoring services. They are the original brief and have not been rewritten to match D-002 to D-005.
