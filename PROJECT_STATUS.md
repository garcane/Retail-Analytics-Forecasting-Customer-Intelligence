# PROJECT STATUS

_Last updated: 2026-10-13_

**Scope:** a **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery as the warehouse and query engine. There is no GCP project, and no cloud resources are used or planned (D-002).

**Current phase:** all in-scope phases complete. Phase 10 (final audit) is written in [docs/AUDIT.md](docs/AUDIT.md). Nothing is in progress and nothing is blocked.

## Phase status

| Phase (from the brief) | Status | Where |
|---|---|---|
| 0 Discovery | Done | `docs/phase0/PHASE0_DISCOVERY.md`, `docs/data/EDA_FINDINGS.md`, `notebooks/01_dataset_discovery.ipynb` |
| 1 Architecture | Done | `ARCHITECTURE.md`, `DECISIONS.md`, `docs/ml/LEAKAGE_ANALYSIS.md` |
| 2 Local prototype | Done | `docs/ml/PHASE2_BASELINES.md` |
| 3 Cloud foundation | Out of scope (D-002) | |
| 4 Data engineering | Done | `sql/`, `src/transformation/build_warehouse.py`, `docs/data/DATA_MODEL.md` (22 checks) |
| 5 Analytics | Done | `sql/analytics/`, `src/analytics/`, `docs/analytics/BUSINESS_INSIGHTS.md` |
| 6 Machine learning | Done | `notebooks/02_late_delivery_model.ipynb` and `03_weekly_forecast.ipynb` (with charts), interactive versions in `notebooks/marimo/`, `docs/ml/MODEL_CARD.md` and the experiment documents it links |
| Dashboard (Power BI, added later) | Built; opens and loads in Desktop (owner now edits layouts there) | `powerbi/README.md`, `docs/powerbi/DAX_SPECIFICATION.html`, `docs/powerbi/DASHBOARD_MOCKUP.html`, `powerbi/RetailAnalytics.pbip` (DD-15) |
| 7 Deployment, 8 Monitoring | Out of scope (D-002, D-005) | |
| 9 Documentation | Done | `README.md`, `SECURITY.md`, `COST.md`, `docs/LESSONS_LEARNED.md`, model card |
| 10 Final audit | Done | `docs/AUDIT.md` |

## Headline results

- **Data model:** 4 facts and 5 dimensions, built in about 25 seconds, 22/22 reconciliation checks pass.
- **Business findings:** net revenue R$ 13.49 million over 98,199 orders; 97% of customers bought once; late orders are the clearest driver of low reviews; the delivery promise was shortened sharply in 2018 (75% of August orders promised in under 20 days). See the insights document.
- **Late-delivery model:** logistic regression ranking orders at purchase time. Flagging the riskiest 10% beats chance by about 2.8 times on average (1.2 times in August 2018). Its probabilities are off in level; use it by rank (DD-11).
- **Experiments that did not help**, all documented: route, category and trailing-rate history; delivery-time slack; recalibration; training-window tuning (DD-10 to DD-12).
- **Weekly forecast:** the average of the naive and 8-week-average forecasts at one week, the 8-week average at four weeks; the more complex models do not clearly beat them on 85 weeks of data.

## Quality evidence

- `uv run pytest`: **96 tests pass** (about 45 seconds). Leakage tests were shown to fail when leaks were planted.
- A **clean clone** plus the raw data rebuilt the warehouse (22/22), passed all tests and regenerated the analytics tables and figures byte-for-byte. Late-delivery metrics reproduce to within about 0.001 to 0.002 (multithreaded numerics); v1 was identical.
- Security scan: no secrets, no tracked data or credentials ([SECURITY.md](SECURITY.md)). Cost: $0 ([COST.md](COST.md)).

## Decisions

D-001 to D-008 (user) and DD-01 to DD-17 (design) are in [DECISIONS.md](DECISIONS.md). **Open decisions:** none.

## Snowflake + dbt implementation (branch feature/snowflake-dbt-migration, 2026-11-08)

| Area | Built | Verified how | Not verified |
|---|---|---|---|
| Python data access (`src/data_access`) | yes | Offline tests with fake connectors; DuckDB path gives identical results to the original code on the real warehouse (read-only) | Any Snowflake query, `write_pandas`, key-pair login |
| Reconciliation (`src/reconciliation`) | yes | DuckDB-vs-DuckDB identity and perturbed fixtures | No DuckDB-vs-Snowflake run. `docs/validation/RECONCILIATION_REPORT.md` is a NOT RUN stub |
| Snowflake setup and RAW ingestion | yes | Offline tests (record counts incl. the reviews file, idempotency, no DROP / OR REPLACE) | Preflight, object creation, `PUT`, `COPY INTO`, CRLF handling in `COPY` |
| dbt project (staging, intermediate, marts, PBI views, tests) | yes | `dbt parse` and `dbt compile --no-populate-cache` offline; compiled SQL transpiled to DuckDB and run on the real CSVs matches the DuckDB reference tables (dims, facts, analytics marts at 1e-9) | `dbt build` / `dbt test` on Snowflake; Snowflake function semantics; the `ASOF JOIN ... MATCH_CONDITION` (a range-join fallback exists behind a var) |
| Power BI | patched-copy script + 12 M templates | 68 offline tests incl. byte-identical checks of report, measures and relationships | Nothing opened in Power BI Desktop; Snowflake authentication options in Desktop |
| CI | 3 workflows | YAML and `actionlint` locally; `dbt parse` on a clean copy | No workflow has run on GitHub |

Full suite (2026-11-08, Python 3.13 venv): 296 passed, 23 skipped, 10 failures/errors, all in `tests/test_powerbi_project.py` and all present before this work (baseline 74 passed, 21 skipped, same 10).

Live steps not yet run (they need your approval and a Snowflake connection): read-only preflight, object creation, RAW load, `dbt build`, DuckDB-vs-Snowflake reconciliation, Snowflake-backed Python runs. Until they run, nothing here is claimed to work on Snowflake.

## Open items (from the audit)

| Item | Why open |
|---|---|
| Compare the Power BI cards with the first-open checklist | The project loads in Desktop; the numbers have not been compared |
| Raw data in early commits of the public repository | History not rewritten (D-008); the owner decides whether to rewrite it |
| Power BI `DataFolder` holds a local path | The committed `powerbi/RetailAnalytics.SemanticModel/definition/expressions.tmdl` points at `C:\Users\Student\GCP\powerbi\data` instead of the `C:\REPLACE\WITH\FULL\PATH\TO\powerbi\data` placeholder, so `test_committed_project_is_complete_and_holds_no_machine_path` fails. The other 9 failures in `tests/test_powerbi_project.py` need `warehouse.duckdb`, which is git-ignored and absent from a fresh clone. The CI workflow `python-ci` is therefore red until the placeholder is restored and the warehouse-dependent tests skip. Not changed: it alters what Desktop opens, so it is the owner's call |
| DuckDB late-delivery feature query is not reproducible across multi-threaded runs | Seen on the real warehouse: `seller_prior_late_rate`, `category_prior_n` and `category_prior_late` differ between two runs of the unmodified `sql/ml/late_delivery_features.sql` (tie ordering in `arg_max` or the `ASOF` joins); identical with `SET threads = 1`. Pin the DuckDB reference to one thread for the reconciliation and find the cause. The Snowflake model adds a deterministic tie-break |
| Snowflake-backed runs of the two Tier 1 entry points | `forecast_baseline.py` and `late_delivery_baseline.py` accept `--backend snowflake --yes` (or `DATA_BACKEND`); a Snowflake run writes to `reports/snowflake/` so it cannot overwrite the tracked DuckDB metrics. The flag logic is tested offline; no run has happened against Snowflake. Tier 2 scripts (`drift_analysis`, `export_scores`, `export_data`, `run_analytics`) stay DuckDB-only |

## Known limitations

- The ML result is modest and documented as such; a better model would need information the dataset lacks (see the model card).
- Six test months and 85 forecast weeks are small samples.
- The original brief documents (`Cloud Portfolio — Master Agent Prompt.md`, `GCP Retail Project Local vs Cloud Architecture.md`, the Retail Analytics document) still describe BigQuery, Dataflow, Vertex AI and monitoring services. They are kept unchanged by design.
- The raw data remains in earlier commits (history not rewritten, D-008).
