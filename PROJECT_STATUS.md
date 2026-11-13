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

## Snowflake + dbt implementation and HTML dashboard (branch feature/snowflake-dbt-migration, updated 2026-11-13)

| Area | Built | Verified how | Not verified |
|---|---|---|---|
| Snowflake setup, resource monitor, service user | yes | Run live in Snowsight 2026-11-12 (`RETAIL_OLIST`, `RETAIL_WH`, three roles, `RETAIL_MONITOR` at 5 credits a month, key-pair user `RETAIL_SVC`) | Credit use (the service user cannot read the monitor; read it as ACCOUNTADMIN) |
| RAW ingestion | yes | Run live 2026-11-12: nine tables, loaded rows equal to the CSV record counts, rerun skipped every file, no stray carriage returns | |
| dbt project (46 models, 321 tests) | yes | Run live 2026-11-12: `dbt build` PASS=367, including the `ASOF JOIN` | |
| Reconciliation (`src/reconciliation`) | yes | Run live: 22/22 checks, 0 differences, headline numbers exact ([report](docs/validation/RECONCILIATION_REPORT.md)) | |
| Python data access, Tier 1 models on Snowflake | yes | Run live 2026-11-13: forecast metrics identical; late-delivery metrics within 6e-6 (inputs differ only by float summation order, at most 1.4e-9) | Tier 2 scripts stay DuckDB-only by design |
| ML write-back to `ML.*` | yes | Offline tests with a fake connector | Not run on Snowflake |
| HTML dashboard (`dashboard/`, DD-22, DD-23) | yes | Data built from Snowflake, identical to a DuckDB build; all seven pages load with no console errors; `tests/test_dashboard.py` | Dark theme not checked visually |
| Power BI on Snowflake | patched-copy script + 12 M templates | 68 offline tests incl. byte-identical checks of report, measures and relationships | Not opened in Power BI Desktop; sign-in method |
| CI | 3 workflows | YAML and `actionlint` locally; `dbt parse` on a clean copy | No workflow has run on GitHub |

Full suite (2026-11-13): see the commit that records this update; the only failures are the 10 in `tests/test_powerbi_project.py` that predate this work.

## Open items (from the audit)

| Item | Why open |
|---|---|
| Compare the Power BI cards with the first-open checklist | The project loads in Desktop; the numbers have not been compared |
| Raw data in early commits of the public repository | History not rewritten (D-008); the owner decides whether to rewrite it |
| Power BI `DataFolder` holds a local path | The committed `powerbi/RetailAnalytics.SemanticModel/definition/expressions.tmdl` points at `C:\Users\Student\GCP\powerbi\data` instead of the `C:\REPLACE\WITH\FULL\PATH\TO\powerbi\data` placeholder, so `test_committed_project_is_complete_and_holds_no_machine_path` fails. The other 9 failures in `tests/test_powerbi_project.py` need `warehouse.duckdb`, which is git-ignored and absent from a fresh clone. The CI workflow `python-ci` is therefore red until the placeholder is restored and the warehouse-dependent tests skip. Not changed: it alters what Desktop opens, so it is the owner's call |
| ~~DuckDB late-delivery feature query is not reproducible across multi-threaded runs~~ (fixed 2026-11-12, DD-21) | Cause: `arg_max` picked among 57 price-tied orders in thread order, which moved `category_prior_*` on about 26,000 rows; plus a float `avg` summed in thread order. Both are now deterministic (alphabetical tie-break, ordered aggregate), identical across 1/2/8/16 threads, and the same rule as Snowflake. The v2/v3 experiment metrics were regenerated; v1 is unchanged |
| ~~Snowflake-backed runs of the two Tier 1 entry points~~ (run 2026-11-13) | `--backend snowflake --yes` wrote `reports/snowflake/*.json`: forecast identical to DuckDB, late-delivery within 6e-6. Tier 2 scripts (`drift_analysis`, `export_data`, `run_analytics`) stay DuckDB-only |
| ML write-back and the Power BI patched copy | Built and tested offline; not run. The write-back is opt-in (`FORECAST_WRITEBACK=1`); the Power BI copy needs Desktop and a sign-in decision |
| Snowflake credit use | Not measured: run `SHOW RESOURCE MONITORS LIKE 'RETAIL_MONITOR'` as ACCOUNTADMIN |

## Known limitations

- The ML result is modest and documented as such; a better model would need information the dataset lacks (see the model card).
- Six test months and 85 forecast weeks are small samples.
- The original brief documents (`Cloud Portfolio — Master Agent Prompt.md`, `GCP Retail Project Local vs Cloud Architecture.md`, the Retail Analytics document) still describe BigQuery, Dataflow, Vertex AI and monitoring services. They are kept unchanged by design.
- The raw data remains in earlier commits (history not rewritten, D-008).
