# PROJECT STATUS

_Last updated: 2026-11-25_

**Scope:** a **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery as the warehouse and query engine. There is no GCP project, and no cloud resources are used or planned (D-002).

**Current phase:** all in-scope phases complete. Phase 10 (final audit) is written in [docs/AUDIT.md](docs/AUDIT.md). Nothing is blocked.

**State on 2026-11-25:** the DuckDB, Snowflake + dbt and Power BI work is on `main` (pull requests #1 and #2, then the CI fixes). `python-ci` and `dbt-ci` run on GitHub and pass. The branch `feature/powerbi-cursor-theme` is the last piece of work: it adds the Power BI theme and Overview page (DD-28) and removes the HTML dashboard (DD-27).

## Phase status

| Phase (from the brief) | Status | Where |
|---|---|---|
| 0 Discovery | Done | `docs/phase0/PHASE0_DISCOVERY.md`, `docs/data/EDA_FINDINGS.md`, `notebooks/01_dataset_discovery.ipynb` |
| 1 Architecture | Done | `ARCHITECTURE.md`, `DECISIONS.md`, `docs/ml/LEAKAGE_ANALYSIS.md` |
| 2 Local prototype | Done | `docs/ml/PHASE2_BASELINES.md` |
| 3 Cloud foundation | Out of scope (D-002) | |
| 4 Data engineering | Done | `sql/`, `src/transformation/build_warehouse.py`, `docs/data/DATA_MODEL.md` (22 checks) |
| 5 Analytics | Done | `sql/analytics/`, `src/analytics/`, `docs/analytics/BUSINESS_INSIGHTS.md` |
| 6 Machine learning | Done | `notebooks/02_late_delivery_model.ipynb` and `03_weekly_forecast.ipynb` (with charts), `docs/ml/MODEL_CARD.md` and the experiment documents it links |
| Dashboard (Power BI, added later) | Built; five pages and a new theme (DD-15, DD-28); opens in Desktop from the exported files and, through the generated copy, from Snowflake | `powerbi/README.md`, `docs/powerbi/DAX_SPECIFICATION.html`, `docs/powerbi/DASHBOARD_MOCKUP.html`, `powerbi/RetailAnalytics.pbip` |
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

- `uv run pytest`: **385 tests pass** (2026-11-25, about 100 seconds with the warehouse built; 96 at the DuckDB audit). Tests that need the local `warehouse.duckdb` skip without it; CI builds it from Kaggle and requires it. Leakage tests were shown to fail when leaks were planted deliberately.
- A **clean clone** plus the raw data rebuilt the warehouse (22/22), passed all tests and regenerated the analytics tables and figures byte-for-byte. Late-delivery metrics reproduce to within about 0.001 to 0.002 (multithreaded numerics); v1 was identical.
- Security scan: no secrets, no tracked data or credentials ([SECURITY.md](SECURITY.md)). Cost: $0 ([COST.md](COST.md)).

## Decisions

D-001 to D-008 (user) and DD-01 to DD-28 (design) are in [DECISIONS.md](DECISIONS.md). **Open decisions:** which registry version is the model's default. `V1_20261113_CC90DC8` (registered from the laptop) is the default and is pinned by the scoring task; `V1WS_20261113_7370C92` (trained inside Snowflake) matches it to 1e-12. Nothing uses the default, so it is left as is until the owner chooses.

## Snowflake + dbt implementation and Power BI on Snowflake (merged to `main` in pull request #1; updated 2026-11-25)

| Area | Built | Verified how | Not verified |
|---|---|---|---|
| Snowflake setup, resource monitor, service user | yes | Run live in Snowsight 2026-11-12 (`RETAIL_OLIST`, `RETAIL_WH`, three roles, `RETAIL_MONITOR` at 5 credits a month, key-pair user `RETAIL_SVC`) | |
| RAW ingestion | yes | Run live 2026-11-12: nine tables, loaded rows equal to the CSV record counts, rerun skipped every file, no stray carriage returns | |
| dbt project (46 models, 321 tests) | yes | Run live 2026-11-12: `dbt build` PASS=367, including the `ASOF JOIN` | |
| Reconciliation (`src/reconciliation`) | yes | Run live: 22/22 checks, 0 differences, headline numbers exact ([report](docs/validation/RECONCILIATION_REPORT.md)) | |
| Python data access, Tier 1 models on Snowflake | yes | Run live 2026-11-13: forecast metrics identical; late-delivery metrics within 6e-6 (inputs differ only by float summation order, at most 1.4e-9) | Tier 2 scripts stay DuckDB-only by design |
| ML outputs in Snowflake (`publish_ml.py`) | yes | Run live 2026-11-13 (run `20261113T122357Z-a99b8a21`): 38,988 scores, 1,610 backtest rows, 6 flag shares; read back; matches DuckDB (backtest identical, scores within 8e-7); re-publish replaces a run atomically | Scored on the client (in-Snowflake scoring is in the rows below) |
| Snowflake Model Registry (`snowflake/ml/`) | yes | Run live 2026-11-13: `ML.LATE_DELIVERY_RISK` `V1_20261113_CC90DC8`, 96,019 training orders, backtest metrics and commit attached; scored 2,000 orders inside Snowflake, equal to local to 1.1e-16 | This first version's dependencies (scikit-learn, `snowflake-ml-python`) are ranges, not exact pins (scheduled scoring and monitoring are in the next row) |
| ML inside Snowflake (`notebooks/snowflake/`, `snowflake/ml/scoring_task.sql`, dbt `monitoring`) | yes | Run live 2026-11-13. The notebooks pass their checks in a Git-connected workspace. Notebook 04 registered `V1WS_20261113_7370C92` from inside Snowflake. Task `ML.SCORE_LATE_DELIVERY` executed once (SUCCEEDED, 6,306 orders) and is kept suspended. Monitoring views equal the Python results | No new data to score on a schedule (static 2018 snapshot); the account idle-timeout parameter is unchanged |
| HTML dashboard (removed 2026-11-25, DD-27) | removed | Was verified before removal: data built from Snowflake identical to a DuckDB build, seven pages with no console errors. `dashboard/`, `src/dashboard/` and `tests/test_dashboard.py` are gone; the last commit that has them is `39c32f3` on `main` | |
| Power BI on Snowflake | patched-copy script + 12 M templates | 68 offline tests incl. byte-identical checks of report, measures and relationships. **Opened in Desktop and signed in 2026-11-25**: all five pages load with Snowflake data (screenshots; headline figures match the first-open checklist: R$ 13.49M net revenue, 98K orders, 8.1% late) | The sign-in method that worked is not recorded. The generated copy holds the owner's account address, so it is git-ignored and never committed |
| CI | 3 workflows | `python-ci` (ruff, then the Kaggle download, warehouse build and full pytest) and `dbt-ci` have run on GitHub and pass; `python-ci` was first green on 2026-11-25 (run #29 on `main`). `actionlint` and a stubbed run of the download step locally | `dbt-live` (manual, needs Snowflake secrets) has never run |

Full suite (2026-11-25, warehouse built, `REQUIRE_WAREHOUSE=1`): 385 passed, 0 failed, 0 skipped. History: the 10 `tests/test_powerbi_project.py` failures and the Linux line-ending failures were fixed in pull request #2 and `fix/powerbi-ci-warehouse`; the 41 dashboard tests left with the dashboard (DD-27).

## Open items (from the audit)

| Item | Why open |
|---|---|
| ~~Compare the Power BI cards with the first-open checklist~~ (done by the owner, 2026-11-25) | Screenshots of the Snowflake-backed report agree with the headline figures (R$ 13.49M, 98K orders, 8.1% late) |
| Raw data in early commits of the public repository | History not rewritten (D-008); the owner decides whether to rewrite it |
| Power BI `DataFolder` holds a local path | **Fixed 2026-11-20.** The committed `expressions.tmdl` holds the `C:\REPLACE\WITH\FULL\PATH\TO\powerbi\data` placeholder again; set your own path in Desktop and restore the placeholder before committing (see `docs/migration/CI_SETUP.md`). The 9 warehouse-dependent tests skip without `warehouse.duckdb` and run in CI, which builds it from Kaggle |
| ~~DuckDB late-delivery feature query is not reproducible across multi-threaded runs~~ (fixed 2026-11-12, DD-21) | Cause: `arg_max` picked among 57 price-tied orders in thread order, which moved `category_prior_*` on about 26,000 rows; plus a float `avg` summed in thread order. Both are now deterministic (alphabetical tie-break, ordered aggregate), identical across 1/2/8/16 threads, and the same rule as Snowflake. The v2/v3 experiment metrics were regenerated; v1 is unchanged |
| ~~Snowflake-backed runs of the two Tier 1 entry points~~ (run 2026-11-13) | `--backend snowflake --yes` wrote `reports/snowflake/*.json`: forecast identical to DuckDB, late-delivery within 6e-6. Tier 2 scripts (`drift_analysis`, `export_data`, `run_analytics`) stay DuckDB-only |
| ~~Power BI patched copy~~ (opened and signed in 2026-11-25) | All 12 source tables exist in Snowflake and the five pages load. It is a generated, git-ignored copy: change the committed `powerbi/` project, then regenerate the copy (regenerating resets the `SnowflakeServer` parameter) |
| ~~Snowflake credit use~~ (measured 2026-11-13) | 0.90 of the 5-credit monthly quota: 0.9035 on `RETAIL_WH` since 2026-11-12, plus 0.0396 on the compute pool for the morning notebook session (an afternoon rerun of about 7 minutes was not yet visible). Recorded in `reports/snowflake/in_snowflake_checks.json`; re-measure with `snowflake/monitoring/credit_usage.py --yes` (`05_monitor_grant.sql` was run once as ACCOUNTADMIN) |
| Late-rate charts start with a 100% spike | The first month (2016-09) has only a few orders, and the Delivery and Overview pages do not filter months under 500 orders |

## Known limitations

- The ML result is modest and documented as such; a better model would need information the dataset lacks (see the model card).
- Six test months and 85 forecast weeks are small samples.
- `Cloud Portfolio — Master Agent Prompt.md` still describes the original multi-cloud brief and is kept unchanged by design. The Google Cloud project brief and its local-vs-cloud mapping were replaced on 2026-11-13 by Snowflake rewrites (`Snowflake Project — Retail Analytics, Forecasting & Customer Intelligence Platform.md`, `Snowflake Retail Project Local vs Cloud Architecture.md`); the originals are in the git history up to commit `a00b0a5`.
- The raw data remains in earlier commits (history not rewritten, D-008).
