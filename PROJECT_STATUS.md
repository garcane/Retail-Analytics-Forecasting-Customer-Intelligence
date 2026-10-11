# PROJECT STATUS

_Last updated: 2026-10-11_

**Scope:** this is a **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery as the warehouse and query engine. There is no GCP project, and no cloud resources are used or planned.

**Current phase:** Phase 2 (local prototype): baselines, a feature experiment and a pytest suite are done; next is testing the drift explanation and recalibration

**Decisions made:** D-001 to D-008 and design decisions DD-01 to DD-10, all recorded in [DECISIONS.md](DECISIONS.md). Latest: D-007 (2026-10-11) sets the ML target to late delivery plus a weekly order forecast; D-008 (2026-10-11) untracks `data/` from Git without rewriting history.

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

- Phase 2 baselines (2026-10-11): late-delivery features and rolling-origin backtest (logistic regression PR-AUC 0.184 against a base rate of 0.085), and weekly forecast baselines (naive best at one week, 8-week average best at four). Details in `docs/ml/PHASE2_BASELINES.md`. scikit-learn added (DD-08).
- Feature experiment and tests (2026-10-11): route, category and trailing-28-day history did not improve the late-delivery model (DD-10); calibration checked; pytest suite of 27 tests added, with leakage-rule tests that were verified to fail when leaks are planted. pytest 9.1.1 is a dev dependency.

**In progress**
- Nothing.

**Blocked / waiting on user**
- Nothing.

**Next**
1. Test the drift explanation (history over a fixed earlier window) and recalibrate the v1 model; see "Suggested next steps" in `docs/ml/PHASE2_BASELINES.md`.
2. Better forecast models (damped trend, exponential smoothing, calendar regression) against the same backtest.
3. Add the new docs to the graphify graph (`/graphify --update`).

**Tests:** warehouse build runs 22 in-script reconciliation checks (all pass). `uv run pytest`: 27 tests pass (about 30 seconds).

**Evidence:** local only. Phase 0 report and warehouse validation output.

**Cloud resources:** none, by decision (D-002).

**Estimated cost:** $0.

**Security status:** no secrets found or created. `.gitignore` blocks common credential files. `data/` is untracked; earlier commits still contain it (no history rewrite, D-008).

**Open decisions:** none.

**Known limitations:** the project docs (Master Agent Prompt, GCP child prompt, `GCP.md`) still describe BigQuery, Dataflow, Vertex AI and monitoring services. They are the original brief and have not been rewritten to match D-002 to D-005.
