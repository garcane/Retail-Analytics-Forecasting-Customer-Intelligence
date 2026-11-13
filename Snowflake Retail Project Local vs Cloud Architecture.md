# Snowflake Retail Project: Local vs. Cloud Architecture

## Overview

This document maps the **local stack** (DuckDB and Python on one laptop) onto the **Snowflake stack** for the Olist retail project. It replaces `GCP Retail Project Local vs Cloud Architecture.md`, the original Google Cloud mapping, which is in the git history up to commit `a00b0a5`.

Unlike the Google Cloud design, most of this mapping is built and has run: each row says whether the Snowflake side exists, and the status column is dated. Measured results are in [snowflake/README.md](snowflake/README.md).

---

## 1. Cloud vs. Local Architecture Mapping

| Component / Function | Snowflake | Local equivalent (built) | Snowflake status (2026-11-13) |
| :--- | :--- | :--- | :--- |
| **Object storage / landing** | Internal stage `RAW.OLIST_STAGE` (an external stage on S3, GCS or Azure Blob for a shared landing zone) | `data/` folder of nine CSVs | **Run**: `PUT` + `COPY INTO` |
| **Ingestion** | `COPY INTO` from the stage, with a checksum log (`RAW.INGESTION_LOG`); Snowpipe for continuous loads | DuckDB `read_csv` in staging SQL | **Run**: nine tables, counts exact, idempotent |
| **Transformation** | dbt on Snowflake: staging and intermediate views, mart tables | `sql/staging`, `sql/dimensions`, `sql/facts` run by `build_warehouse.py` | **Run**: `dbt build` PASS=367 |
| **Data warehouse** | Database `RETAIL_OLIST`, schemas `RAW, STAGING, INTERMEDIATE, MARTS, PBI, ML`, warehouse `RETAIL_WH` (XSMALL) | `warehouse.duckdb` | **Run** |
| **Dimensional model** | dbt marts `dim_*`, `fact_*` (same names as DuckDB) | 5 dimensions, 4 facts | **Run**, reconciled 0-diff |
| **Data quality** | dbt generic and singular tests (keys, relationships, the 22 checks) | `sql/validation/checks.sql` | **Run**: all pass |
| **Reconciliation** | `src/reconciliation`: Snowflake vs the DuckDB reference | (DuckDB is the reference) | **Run**: 22/22, 0 differences |
| **Feature engineering** | dbt `mart_late_delivery_features` (`ASOF JOIN`), `mart_weekly_orders_revenue` | `sql/ml/late_delivery_features.sql` | **Run**, reconciled 0-diff |
| **Model training** | Today: scikit-learn on the client, reading Snowflake; the trained model is then logged to the registry. Target: training inside Snowflake (stored procedure) | scikit-learn in `src/ml/` | **Partly**: client-side training on Snowflake data; the model lives in Snowflake |
| **Experiment results** | Metrics: `reports/snowflake/*.json` on the client. Scores and forecast backtests: tables in `ML` | `reports/*.json` | **Run** |
| **Model registry** | Snowflake Model Registry (`snowflake-ml-python`, `snowflake/ml/register_model.py`) | none (metrics files and the model card) | **Run** 2026-11-13: `ML.LATE_DELIVERY_RISK` `V1_20261113_CC90DC8` |
| **Batch inference** | Today: scores computed on the client and published to `ML.LATE_DELIVERY_SCORES` by `publish_ml.py`. Target: registry model run in a scheduled Task | `export_scores.py` to Parquet | **Run** (client-side scoring, results in Snowflake, 2026-11-13) |
| **Online inference** | Not planned (the model is used by rank, in batch) | none | n/a |
| **Orchestration** | Snowflake Tasks or an external scheduler calling `load_raw.py` and `dbt build` | run by hand | **Not built** |
| **Monitoring** | Resource monitor (`RETAIL_MONITOR`, 5 credits a month), `ACCOUNT_USAGE` views, dbt test results; ML drift as SQL over the `ML` tables | `drift_analysis.py` | **Partly**: monitor exists; ML monitoring not built |
| **Access control** | Roles `RETAIL_LOADER`, `RETAIL_TRANSFORMER`, `RETAIL_REPORTER`; service user `RETAIL_SVC` with key-pair authentication | none needed | **Run** |
| **BI** | Power BI on the `PBI` views; HTML dashboard built from `MARTS` | Power BI on exported files; HTML dashboard | Dashboard **run**; Power BI copy **not opened** |

---

## 2. End-to-End Pipeline Workflow

### Local pipeline (reference)

```text
Olist CSV ──> DuckDB staging views ──> star schema (warehouse.duckdb) ──> 22 checks ──> analytics SQL ──> ML features
                                         │                                                                   │
                                         ├── dim_customer, dim_product, dim_seller, dim_date, dim_geography   └──> scikit-learn ──> reports/*.json
                                         └── fact_orders, fact_order_items, fact_payments, fact_reviews
```

### Snowflake pipeline (as built)

```text
Olist CSV ──PUT──> internal stage ──COPY INTO──> RAW (all VARCHAR + load metadata)
          ──dbt──> STAGING (typed views) ──> INTERMEDIATE ──> MARTS (dim_*, fact_*, mart_*) ──> PBI views
                                                                │
                                                                ├──> reconciliation against DuckDB (22 checks)
                                                                ├──> HTML dashboard data (build_data.py)
                                                                └──> Python on the client (connector) ──> scikit-learn ──> reports/snowflake/*.json
```

### Snowflake pipeline (target for the ML layer, not built)

```text
MARTS.mart_late_delivery_features ──> Snowpark training (stored procedure) ──> Model Registry (versioned v1)
                                  ──> scheduled Task: registry model scores new orders ──> ML.LATE_DELIVERY_SCORES ──> PBI / dashboard
                                  ──> drift and calibration SQL over ML tables ──> alert
```

---

## 3. Where the ML runs today

The data side of the ML is fully in Snowflake: the feature table and the weekly series are dbt models, tested, and identical to DuckDB. The **compute** of the ML is not. `forecast_baseline.py` and `late_delivery_baseline.py` connect with the Snowflake connector, pull the features into pandas, and train scikit-learn models on the laptop. On 2026-11-13 this gave forecast metrics identical to DuckDB, and late-delivery metrics equal to within 6e-6; the inputs differ only by floating-point summation order.

What that means:

- **Ported:** feature engineering, including the leakage-safe `ASOF JOIN` history, the training data, and the weekly series.
- **Client-side, by design for now:** training and evaluation (rolling-origin backtests over six test months).
- **Ported on 2026-11-13:** the results. `src/ml/publish_ml.py` writes the scores, forecast backtest and flag shares to `ML.*` under one run id; they match the DuckDB outputs.
- **Ported on 2026-11-13:** the model. `snowflake/ml/register_model.py` logs the v1 model to the Snowflake Model Registry (`ML.LATE_DELIVERY_RISK`, version `V1_20261113_CC90DC8`), and scoring inside Snowflake with it matches the local model to 1.1e-16.
- **Not yet ported:** scheduled scoring inside Snowflake, training inside Snowflake and ML monitoring.

The next steps, in order of value per effort:

1. ~~Publish the results to the `ML` schema~~ (done 2026-11-13, `publish_ml.py`).
2. ~~Log the v1 scikit-learn pipeline to the Snowflake Model Registry, with its metrics and the git commit~~ (done 2026-11-13, `snowflake/ml/register_model.py`).
3. Score inside Snowflake from the registered model, scheduled by a Task.
4. Move the drift and calibration checks to SQL over the `ML` tables.

## 4. Key Snowflake Technologies and Portability

### dbt instead of Dataflow

The Google Cloud design used Apache Beam so that one pipeline could run locally (Direct Runner) and in the cloud (Dataflow Runner). On Snowflake the equivalent portability comes from SQL and dbt. The same models compile for a `dev` target (prefixed schemas), a `ci` target (parse only, no connection) and `prod`, and they are tested by the same dbt tests in each. For 100,000 orders, set-based SQL in the warehouse is simpler and cheaper than a distributed pipeline.

### Analytics engine: DuckDB vs Snowflake

DuckDB stays the local reference. The Snowflake port changed the dialect but not the model:

- `arg_max` → `max_by`, with explicit tie-breaks so both engines agree row for row (DD-21)
- `ASOF JOIN` → `ASOF JOIN ... MATCH_CONDITION`
- `strftime` → `to_char`, `date_diff` → `datediff`, `FILTER (WHERE)` → `CASE`
- enforced primary and foreign keys → dbt tests

Every translation is listed in [docs/migration/SNOWFLAKE_MIGRATION.md](docs/migration/SNOWFLAKE_MIGRATION.md).

### Cost control

One XSMALL warehouse with a 60-second auto-suspend, capped by a 5-credit monthly resource monitor. There is no always-on compute and no endpoint. Measured on 2026-11-13: the whole build so far used 0.34 credits.
