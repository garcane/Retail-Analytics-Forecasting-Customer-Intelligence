# Cost

**The DuckDB implementation costs $0 and uses no cloud resources (D-002).** The Snowflake implementation (DD-19) uses a small Snowflake warehouse capped by a resource monitor; see the section below.

| Item | Cost |
|---|---|
| Warehouse and query engine (DuckDB, one local file) | $0 |
| ML (scikit-learn, numpy, scipy on a laptop) | $0 |
| Analytics and charts (SQL, matplotlib) | $0 |
| Dataset (Kaggle, free account) | $0 |
| Tooling (`uv`, `pytest`, open source) | $0 |

## Compute

Measured on the development laptop (2026-10-13):

| Step | Time |
|---|---|
| Build the warehouse (22 checks included) | about 25 seconds |
| Late-delivery backtest | about 40 seconds |
| Forecast backtests | 3 seconds (baselines), about 12 seconds (extra models) |
| Analytics queries and charts | about 12 seconds |
| Explainability (permutation importance) | about 43 seconds |
| Full test suite (96 tests) | 30 to 60 seconds |
| Export the Power BI data files (includes re-scoring the model) | under a minute |
| Generate the specification, mock-up and Power BI project | a few seconds each |
| Run the late-delivery notebook (all cells) | about 1 to 1.5 minutes |
| Run the forecast notebook (all cells) | about 15 seconds |
| Drift analysis and recalibration | a few minutes each |

Disk: about 79 MB of raw data (the nine Kaggle CSV files), a 112 MB warehouse file and about 40 MB of Power BI data files, all git-ignored. Power BI Desktop is free; no Power BI service, gateway or licence is used, so the cost stays $0.

## Snowflake implementation (branch feature/snowflake-dbt-migration)

**Compute pools are billed separately.** The Snowflake notebooks (`notebooks/snowflake/`, DD-26) run on a compute pool (`SYSTEM_COMPUTE_POOL_CPU`, CPU_X64_S) that bills while a notebook service is running. A service's idle timeout defaults to 24 hours, and `RETAIL_MONITOR` covers only the warehouse. Suspend the notebook service after each session. One session ran on 2026-11-13: the pool resumed at 07:26 and the service was suspended at about 07:45 (account time), with a 15-minute idle timeout per service; the pool auto-suspends 5 minutes after. Its credits are **not measured**: compute-pool metering is not visible to `RETAIL_SVC` and `RETAIL_MONITOR` does not cover pools. Read it as ACCOUNTADMIN in *Admin → Cost management*. The scheduled scoring and the monitoring views run on `RETAIL_WH`, inside the monitor.

The pipeline has run on Snowflake (2026-11-12 and 2026-11-13). **0.34 credits measured** (2026-11-13, `RETAIL_MONITOR`: 0.34 of the 5-credit monthly quota, 6.8%, 4.66 remaining). The monitor was created during setup, before the first load, so this covers everything that has run on `RETAIL_WH`: the RAW load and its idempotent rerun, every `dbt build`, the reconciliation runs, the dashboard data builds, the Snowflake ML runs and the ad hoc checks. The money cost depends on the account's credit price (edition, region, contract), which has not been checked, so no currency figure is given. To re-measure at any time: `python snowflake/monitoring/credit_usage.py --yes` (see `snowflake/README.md`, section 12).

- Compute: one warehouse, `RETAIL_WH`, size XSMALL, `AUTO_SUSPEND = 60`, `AUTO_RESUME = TRUE`, created suspended. An XSMALL warehouse consumes 1 credit per hour of running time (Snowflake's published rate; the price of a credit depends on edition, region and contract and has not been checked here).
- Cap: `RETAIL_MONITOR` (`snowflake/setup/03_resource_monitor.sql`) gives `RETAIL_WH` a quota of 5 credits a month: notify at 75%, suspend at 100%, suspend immediately at 110%.
- Measured run times on XSMALL (wall clock, including connection and upload): RAW load of all nine files about one minute; `dbt build` (46 models, 321 tests) about one minute; reconciliation and the dashboard data build under a minute each; the late-delivery backtest on Snowflake data about 2.5 minutes, almost all of it local model training. With the 60-second auto-suspend the whole sequence is minutes of warehouse time, which agrees with the metered 0.34 credits.
- Storage: the nine CSVs are about 124 MB; RAW, STAGING, INTERMEDIATE and MARTS together are a small multiple of that. Not measured.
- The DuckDB implementation still costs $0, and so does the HTML dashboard (static files served locally).

## If the project moved to the cloud

Pricing for BigQuery, Dataflow and Vertex AI was **never verified** (Phase 0 §10) and is not estimated here. At this data size (about 100,000 orders, 80 MB) the cost would be expected to be very small, within free tiers, but that is an expectation and not a checked figure. See the "Moving to BigQuery" section of [docs/data/DATA_MODEL.md](docs/data/DATA_MODEL.md) for the technical work involved.
