# Migrating from the local build to Google Cloud

This guide explains how to move the local DuckDB implementation onto the cloud design in the original brief (Cloud Storage, BigQuery, Vertex AI, Power BI on BigQuery). The local build was organised in the same layers as that design, so the move is mostly a change of **engine and location**, not of structure.

## Read this first: what is and is not verified

- **Nothing here has been run on Google Cloud.** The project is local by decision (D-002). The steps are a plan, not a record. Commands are illustrative: check them against the current Google Cloud documentation before running them.
- **Checked against the official GoogleSQL reference (2026-10-16):** BigQuery's join operators are `INNER`, `LEFT`, `RIGHT`, `FULL` and `CROSS`. There is **no `ASOF JOIN`**, which this project's ML features use (see step 6). `QUALIFY` is supported.
- **From general knowledge, not checked:** the other function equivalents in step 5 and the exact command flags. Treat them as starting points and verify each against the reference.
- **Prices, quotas and free-tier terms were never verified** (Phase 0, section 10) and are deliberately not quoted. Set a budget alert before you create anything, and tear everything down when you finish (step 11).
- The Dataflow part of the brief is **not** part of this plan, with a reason given in step 4.

## 1. How the local build mirrors the cloud design

| Layer (from the brief) | Local build (today) | Cloud design (to build) |
|---|---|---|
| RAW | `data/`: the nine Kaggle CSV files, never modified | Cloud Storage bucket, `raw/` prefix: the same nine files, immutable |
| STAGING | `sql/staging/`: typed views over the CSVs | BigQuery dataset `staging`: tables loaded with an explicit schema |
| CURATED (star schema) | `sql/dimensions/`, `sql/facts/` into `warehouse.duckdb` | BigQuery dataset `curated`: the same 5 dimensions and 4 facts |
| Validation | `sql/validation/checks.sql`, 22 checks, run on every build | The same checks as BigQuery queries, run after every load |
| ANALYTICAL | `sql/analytics/`, 8 queries, results in `reports/analytics/` | BigQuery dataset `analytics` |
| FEATURES | `sql/ml/late_delivery_features.sql` | BigQuery dataset `features` |
| Model training and registry | `src/ml/` scikit-learn scripts, metrics in `reports/*.json` | Vertex AI custom training job; model registered in Vertex AI Model Registry |
| PREDICTIONS | `src/ml/export_scores.py` writes `late_delivery_scores.parquet` | Vertex AI batch prediction writing a BigQuery table |
| BI | Power BI Desktop reading `powerbi/data/` (Parquet and CSV) | Power BI connected to the BigQuery tables |

The diagram of the same flow is in the [README](../README.md#data-architecture).

**What the local build deliberately does not mirror** (decisions D-002, D-004, D-005): Dataflow and Apache Beam, MLflow, an online prediction endpoint, Cloud Monitoring (replaced by the validation checks and saved metrics), IAM and Secret Manager (nothing is deployed, so there is nothing to secure), and dbt (plain SQL files run in order).

## 2. What carries over unchanged

- **The model of the data:** grains, surrogate keys, the `-1` unknown member in every dimension, the rule that facts never join to facts ([docs/data/DATA_MODEL.md](data/DATA_MODEL.md)).
- **The order of the layers and the file-per-table structure** of the SQL.
- **The validation logic.** The 22 checks are plain SQL; only the dialect needs translating.
- **The ML code,** scikit-learn and pandas, and the leakage rules ([docs/ml/LEAKAGE_ANALYSIS.md](ml/LEAKAGE_ANALYSIS.md)). Only where the data is read from changes.
- **The Power BI model and measures** (12 tables, 13 relationships, 38 measures). Only the data source behind each table changes.

## 3. What changes

| Area | Change |
|---|---|
| SQL dialect | DuckDB to GoogleSQL: casts, date functions, medians, `FILTER`, the `ASOF` joins (step 5 and 6) |
| Where files live | Local folder to a Cloud Storage bucket |
| Running the layers | `build_warehouse.py` runs files in a local DuckDB connection; a cloud runner needs a BigQuery client and the same fixed order |
| Python data access | `duckdb.connect(...)` is opened in the `main()` of about ten scripts in `src/ml/`, `src/analytics/` and `src/powerbi/`, and functions such as `late_delivery_baseline.load` pull the data. Switch them to the BigQuery client library; a small shared data-access helper would make that a one-place change |
| Orchestration | None locally. In the cloud something must trigger the layers in order (Cloud Scheduler with Workflows, or Composer); choose when you get there |
| Credentials | None locally. In the cloud, service accounts with least privilege (step 1) |

## 4. Decisions to make before starting

1. **One location** for the bucket, the BigQuery datasets and the Vertex AI jobs. BigQuery datasets are tied to a location, and a job cannot read across locations freely. Service availability differs by region, so check Vertex AI in the region you choose. The data is public and anonymised, so residency is not a constraint.
2. **Dataflow: skip it.** The brief says to use Dataflow only where it adds value and to compare it with the alternatives for small data. About 100,000 orders (80 MB) load with one `bq load` per file and transform with SQL. The raw-to-staging step is the only place Dataflow could go, and it would add workers, cost and failure modes for no gain. The local build already made the same call (D-004).
3. **Partitioning and clustering are a demonstration, not a necessity, at this size.** A table of this size fits in one block of storage, so you will not see cost or speed gains. Do it to show the technique, and say so.
4. **Training on Vertex AI versus BigQuery ML.** The brief asks for a Vertex AI lifecycle. The scikit-learn code can run as a Vertex AI custom training job without rewriting the model.

## 5. Step by step

Placeholders: `PROJECT_ID`, `LOCATION`, `BUCKET`. Run from the repository root.

### Step 1. Project, budget and access

1. Create a project and attach billing. **Create a budget alert first** (Billing console) with a small threshold.
2. Enable the APIs: BigQuery, Cloud Storage, Vertex AI.
   ```
   gcloud config set project PROJECT_ID
   gcloud services enable bigquery.googleapis.com storage.googleapis.com aiplatform.googleapis.com
   ```
3. Create one service account per job type rather than using broad roles. Typical minimum roles (confirm the current role names): BigQuery Job User on the project, BigQuery Data Editor on the specific datasets, Storage Object Admin on the one bucket, Vertex AI User for training and prediction. Write down why each role exists.
4. For local development use `gcloud auth application-default login`. **Never put a service-account key file in the repository** (`.gitignore` already blocks common key file names, D-006).

### Step 2. Raw layer: Cloud Storage

```
gcloud storage buckets create gs://BUCKET --location=LOCATION --uniform-bucket-level-access
gcloud storage cp data/*.csv gs://BUCKET/raw/olist/
```

Upload the files exactly as downloaded. This is the immutable RAW layer; later layers are rebuilt from it. The brief also lists `staging/`, `curated/`, `features/`, `models/` and `predictions/` prefixes for any file artefacts.

### Step 3. Datasets

```
bq --location=LOCATION mk --dataset PROJECT_ID:staging
bq --location=LOCATION mk --dataset PROJECT_ID:curated
bq --location=LOCATION mk --dataset PROJECT_ID:analytics
bq --location=LOCATION mk --dataset PROJECT_ID:features
bq --location=LOCATION mk --dataset PROJECT_ID:predictions
```

### Step 4. Staging: load the CSVs with an explicit schema

The local staging files use `read_csv(... columns = {...})` with explicit types. Copy those column lists into BigQuery schema files and load each file:

```
bq load --source_format=CSV --skip_leading_rows=1 --allow_quoted_newlines \
  PROJECT_ID:staging.stg_order_reviews gs://BUCKET/raw/olist/olist_order_reviews_dataset.csv schemas/stg_order_reviews.json
```

- `--allow_quoted_newlines` matters: review comments contain line breaks inside quotes, which DuckDB's reader handles by default and BigQuery's does not unless told.
- The zip-code prefix columns must be `STRING`, so that values like `01046` keep their zero (the local staging does the same).
- Geolocation is the largest file (about 1,000,163 rows). It loads the same way.

### Step 5. Curated layer: translate the SQL

Create a parallel folder, `sql/bigquery/`, with the **same file names** as `sql/`, so each translated file can be compared with its DuckDB original. Keep the layer order: dimensions before facts, because facts reference them.

The constructs that need changing, with how many files use them (counted in `sql/`):

| DuckDB (this repo) | Where | GoogleSQL starting point (verify) |
|---|---|---|
| `x::TYPE` casts | 14 files | `CAST(x AS TYPE)` (`SAFE_CAST` where a bad value should become null). Types per the table in [DATA_MODEL.md](data/DATA_MODEL.md#moving-to-bigquery): `VARCHAR` to `STRING`, `DECIMAL(12,2)` to `NUMERIC`, `DOUBLE` to `FLOAT64`, `BOOLEAN` to `BOOL`, `TIMESTAMP` to `DATETIME` |
| `read_csv(... columns = {...})` | 9 staging files | Replaced by the `bq load` in step 4; staging becomes tables |
| `strftime(ts, '%Y%m%d')` | 6 files, 13 uses | `FORMAT_DATE('%Y%m%d', DATE(ts))` or `FORMAT_DATETIME(...)`; the date key is an integer, so wrap in `CAST(... AS INT64)` |
| `date_diff('second', start, end)` | 3 files, 6 uses | `DATETIME_DIFF(end, start, SECOND)`. **The argument order flips**: end first. A swap here silently negates every delivery duration |
| `median(x)` | 4 files | Exact: `PERCENTILE_CONT(x, 0.5) OVER (...)` (an analytic function, so grouped medians need a rewrite). Approximate: `APPROX_QUANTILES(x, 2)[OFFSET(1)]`. Expect small differences if you choose approximate |
| `agg(x) FILTER (WHERE c)` | 2 files | `COUNTIF(c)`, or `AVG(IF(c, x, NULL))` and similar |
| `unnest(generate_series(a, b, interval 1 day))` | `dim_date.sql` | `UNNEST(GENERATE_DATE_ARRAY(a, b))` |
| `date_trunc('year', d)`, `interval 1 year` | `dim_date.sql` | `DATE_TRUNC(d, YEAR)` (**argument order flips**), `DATE_ADD(d, INTERVAL 1 YEAR)`, `DATE_SUB(...)` |
| `monthname(d)`, `weekofyear(d)` | `dim_date.sql` | `FORMAT_DATE('%B', d)`, `EXTRACT(ISOWEEK FROM d)` |
| `isodow(d)` | 2 files | `EXTRACT(DAYOFWEEK FROM d)` counts Sunday as 1, so ISO weekday is `MOD(EXTRACT(DAYOFWEEK FROM d) + 5, 7) + 1` |
| `PRIMARY KEY`, inline `REFERENCES` | dimension and fact DDL | `PRIMARY KEY (...) NOT ENFORCED`, `FOREIGN KEY (...) REFERENCES ... NOT ENFORCED`. BigQuery does not enforce them, so the validation checks become the real guard |
| `${DATA_DIR}` token | the 9 staging files | Disappears with `read_csv` (step 4). Other layers refer to tables by name; add a `${PROJECT}.${DATASET}` token substituted the same way if you want one SQL set for several projects |
| `asof left join` | `sql/ml/late_delivery_features.sql`, 4 joins | **No equivalent. See step 6** |

### Step 6. Features: rewrite the `ASOF` joins

`late_delivery_features.sql` reads running totals "as of" each purchase with `asof left join`, which is what keeps the features free of leakage. GoogleSQL has no `ASOF JOIN`, so this file needs a rewrite rather than a translation.

One workable pattern (design, untested): give each running-total row a validity interval and join on it.

1. Build each cumulative table with **one row per key and timestamp** (group ties first, or the join can match two rows).
2. Add `next_ts` with `LEAD(ts) OVER (PARTITION BY key ORDER BY ts)`.
3. Join where `r.ts < purchase_ts AND (r.next_ts IS NULL OR purchase_ts <= r.next_ts)`. The local join uses a strict `>` on purchase time, which is why the lower bound is strict.

Do not trust the rewrite until it passes the same leakage tests as the original ([tests/test_feature_leakage.py](../tests/test_feature_leakage.py) run on a hand-built mini warehouse, with planted leaks shown to fail). Those tests are DuckDB-only today, so port them to a scratch dataset, **and** run a parity check: build the feature table in both engines from the same data and compare it row by row.

### Step 7. Validate

Run the layers in order (staging, dimensions, facts), then translate `sql/validation/checks.sql` and run it. Stop if any check fails, as the local build does. See the parity targets in step 10.

### Step 8. Partition and cluster (optional here)

From [DATA_MODEL.md](data/DATA_MODEL.md#moving-to-bigquery): partition `fact_orders` by purchase date and cluster on the most-filtered keys (`customer_key`, `seller_key`, `product_key`). BigQuery partitions on a `DATE` or timestamp column (or an integer range), and the facts store the purchase date as a `yyyymmdd` integer key, so either derive a `DATE` from `purchase_ts` or use an integer-range partition. `fact_order_items` has the integer `purchase_date_key` but no timestamp, so derive a `DATE` from the key (for example `PARSE_DATE('%Y%m%d', CAST(purchase_date_key AS STRING))`) or use an integer-range partition. Record why you chose each column (the brief asks for this). Check query cost with a dry run (`bq query --dry_run`) and cap spend with `--maximum_bytes_billed`.

### Step 9. Machine learning on Vertex AI

1. **Data access:** change the load functions in `src/ml/` to read the `features` dataset through the BigQuery client. Keep the rolling-origin evaluation and the leakage rules exactly as they are.
2. **Training:** package `src/ml/` and run it as a Vertex AI custom training job (a pre-built scikit-learn container or your own). Record training dataset, feature version, metrics and hyperparameters.
3. **Registry:** register the model in Vertex AI Model Registry with the fields the brief lists: name, version, training dataset, feature version, training timestamp, model type, evaluation metrics, hyperparameters, artefact location, dependencies, limitations, approval status. The limitations text already exists in [MODEL_CARD.md](ml/MODEL_CARD.md).
4. **Prediction:** use **batch prediction** into `predictions.late_delivery_scores`, replacing `export_scores.py`. Do not deploy an online endpoint: the model is used by rank over a month of orders, not one order at a time (the brief's batch-versus-online comparison favours batch here), and an endpoint adds running cost.

### Step 10. Power BI on BigQuery

1. In `RetailAnalytics.SemanticModel`, replace each table's Parquet/CSV source query with the Google BigQuery connector pointing at the matching table, and **keep every table and column name identical** so relationships and measures do not change.
2. The local export adds derived columns (`is_net_order`, `is_labelled_delivery`, `promised_days`, `delay_bucket` and others, defined in `src/powerbi/export_data.py`). Recreate them as BigQuery views, using the translated SQL.
3. Sign in with your Google account when Power BI asks. No credentials go into the project files.
4. Remove the `DataFolder` parameter once nothing uses it.
5. Check the cards against the first-open checklist in the [DAX specification](powerbi/DAX_SPECIFICATION.html).

### Step 11. Verify, then tear down

**Parity targets** (the local values; the cloud build must reproduce them):

| Check | Local value |
|---|---|
| Validation checks | 22 of 22 pass |
| Row counts | `fact_orders` 99,441; `fact_order_items` 112,650; `fact_payments` 103,886; `fact_reviews` 99,224 |
| Net orders / net revenue | 98,199 / R$ 13,494,400.74 |
| Delivered orders / late | 96,282 / 7,823 (8.13%) |
| Model, macro-average PR-AUC for v1 | 0.1837, within about 0.002 (numeric noise differs by environment) |
| Scored orders / flagged at 10% | 38,988 / 3,901 |
| Power BI headline cards | the 13 numbers in the specification's checklist |

**When you are done, delete what you created** (the datasets, the bucket, any Vertex AI resources) and confirm in the Billing console that nothing is still running. Cost control is the part of this plan that most needs care, because the prices were never checked.

## 6. A suggested layout for the cloud twin

Nothing below exists yet; it keeps the two builds easy to compare.

```
sql/                      local DuckDB SQL (unchanged)
sql/bigquery/             translated SQL, same file names and layer folders
src/transformation/
    build_warehouse.py    local runner (unchanged)
    build_bigquery.py     new: runs sql/bigquery in the same layer order, then the checks
schemas/                  BigQuery load schemas, copied from the staging column lists
```

If the cloud build is ever made, record the decision (it would supersede D-002 and D-003) in [DECISIONS.md](../DECISIONS.md) first.
