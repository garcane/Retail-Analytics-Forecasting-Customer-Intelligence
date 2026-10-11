# Decisions

The decision log for the local DuckDB build. Each entry follows the template in the project brief. **User decisions** (D-001 to D-008) were made by the project owner. **Design decisions** (DD-01 onwards) were made while building the warehouse, and each one names the evidence behind it.

Later decisions can supersede earlier ones; when that happens the entry says so. The original cloud brief (`Cloud Portfolio — Master Agent Prompt.md`, `GCP.md`, the Retail Analytics project document) is kept unchanged on purpose, so where a decision below contradicts it, the decision wins.

| ID | Date | Decision | Status |
|---|---|---|---|
| D-001 | 2026-10-06 | Implementations use DuckDB | Active (the cloud-phase part is superseded by D-002, the portability part by D-003) |
| D-002 | 2026-10-10 | Local only, no GCP | Active |
| D-003 | 2026-10-10 | Idiomatic DuckDB SQL | Active |
| D-004 | 2026-10-10 | No dbt; plain SQL run by a Python script | Active |
| D-005 | 2026-10-10 | No Prometheus, Grafana or FastAPI | Active |
| D-006 | 2026-10-10 | `.gitignore` covers the database, `data/` and credentials | Active |
| D-007 | 2026-10-11 | ML target: late delivery, plus a weekly order forecast | Active |
| D-008 | 2026-10-11 | Untrack `data/` from Git; do not rewrite history | Done (commit `d8f6954`) |
| DD-01 | 2026-10-10 | Kimball star schema; facts never join to facts | Active |
| DD-02 | 2026-10-10 | Customer grain is `customer_unique_id` | Active |
| DD-03 | 2026-10-10 | Reviews keyed on (`review_id`, `order_id`) with a latest-review flag | Active |
| DD-04 | 2026-10-10 | Revenue is measured from order items only | Active |
| DD-05 | 2026-10-10 | Surrogate keys with an unknown member (-1) | Active |
| DD-06 | 2026-10-10 | Convert geolocation CSV to Parquet in the build | Active |
| DD-07 | 2026-10-11 | Customer segmentation is optional and may be dropped | Active |

---

## User decisions

### D-001: Implementations use DuckDB

- **Context:** The brief targets BigQuery, but the whole dataset is about 80 MB and fits in memory. Development needed a local engine for the warehouse, data-quality checks and tests.
- **Options:** DuckDB; SQLite; pandas or polars only; BigQuery from the start.
- **Chosen:** DuckDB.
- **Reason:** It is a columnar analytical engine with a SQL dialect close to BigQuery's, it reads CSV and Parquet directly, and it needs no server.
- **Trade-offs:** BigQuery-only features (partitioning, clustering, `INFORMATION_SCHEMA` jobs, slot pricing) cannot be shown.
- **Cost:** $0.
- **Security:** Data never leaves the machine.
- **Rejected:** SQLite (row store, weak analytics functions); pandas only (no SQL model to show); BigQuery first (cost and credentials before the model was known).
- **Superseded in part:** the original wording said BigQuery features would be shown in a cloud phase (removed by D-002) and that SQL should stay BigQuery-portable (removed by D-003).

### D-002: Local only

- **Context:** The cloud phase would need a GCP project, billing, IAM and `gcloud`. None of it is needed to show the data model and ML work.
- **Options:** Local then cloud (the brief); local with emulators; local only.
- **Chosen:** Local only. DuckDB stands in for Google Cloud and BigQuery. No GCP project, no `gcloud`, no cloud phase.
- **Reason:** Removes cost, credential risk and setup time.
- **Trade-offs:** No cloud deployment to show. Dataflow/Beam and the BigQuery region question become moot. Cloud pricing in Phase 0 stays unverified.
- **Cost:** $0.
- **Security:** No service accounts or keys exist, so none can leak.
- **Rejected:** Local then cloud (cost and scope); emulators (they add setup without adding evidence for this project).

### D-003: Idiomatic DuckDB SQL

- **Context:** D-001 asked for BigQuery-portable SQL. That rules out convenient DuckDB functions and makes the SQL harder to read.
- **Options:** Portable SQL; idiomatic DuckDB SQL.
- **Chosen:** Idiomatic DuckDB SQL.
- **Reason:** With no cloud phase (D-002), portability has no user. The translation work is listed in [docs/data/DATA_MODEL.md](docs/data/DATA_MODEL.md#moving-to-bigquery) if it is ever needed.
- **Trade-offs:** A move to BigQuery would need dialect translation, not copy-paste.
- **Cost / Security:** None.
- **Rejected:** Portable SQL.

### D-004: No dbt

- **Context:** The shared architecture notes ([docs/architecture-philosophy.md](docs/architecture-philosophy.md)) favour dbt.
- **Options:** dbt with the DuckDB adapter; plain SQL files run by a script.
- **Chosen:** Plain SQL files under `sql/`, run in a fixed order by `src/transformation/build_warehouse.py`.
- **Reason:** Fewer moving parts. The build order is small and explicit.
- **Trade-offs:** No dbt lineage graph, docs site or built-in `unique`, `not_null` and `relationships` tests. Table constraints (primary and foreign keys) and `sql/validation/checks.sql` cover the same ground.
- **Cost / Security:** None.
- **Rejected:** dbt.

### D-005: No Prometheus, Grafana or FastAPI

- **Context:** The brief includes a monitoring stack and a serving API.
- **Chosen:** None of them.
- **Reason:** There is no long-running service to monitor or serve. The build is a batch job that either passes its checks or exits non-zero.
- **Trade-offs:** No live dashboards or prediction endpoint. Model outputs will be files and notebook results.
- **Cost / Security:** None; no network ports are opened.
- **Rejected:** A Docker monitoring stack; a FastAPI prediction service.

### D-006: `.gitignore` coverage

- **Context:** Phase 0 found no `.gitignore`, with `data/` tracked in Git.
- **Chosen:** Ignore `*.duckdb`, `*.duckdb.wal`, `data/`, `.env*`, `*.pem`, `*.key`, service-account and credential JSON files, and caches.
- **Reason:** The database is rebuilt from source; the raw data is re-downloadable; credentials must never be committed.
- **Security:** Blocks the common credential file patterns, although none are expected in this project.

### D-007: ML target is late delivery, plus a weekly forecast

- **Context:** Phase 0 §7 proposed three supervised candidates (low review score, late delivery, repeat purchase) and recommended low review score or late delivery, plus a weekly forecast.
- **Options:** Low review score (1-2 stars); late delivery; repeat purchase.
- **Chosen:** **Late-delivery classification** (one order, predicted at purchase) and a **weekly order-count forecast** (revenue secondary). Full definitions and the leakage audit are in [docs/ml/LEAKAGE_ANALYSIS.md](docs/ml/LEAKAGE_ANALYSIS.md).
- **Reason:** The late-delivery label comes straight from timestamps, with no dependence on reviews. The features available at purchase are concrete: seller, product size, freight, the seller-to-customer route and the promised delivery window. It also drives the review outcome, since late orders average 2.57 stars against 4.29 for on-time orders. The forecast uses the 87-week window found in Phase 0.
- **Trade-offs:** The positive class is 8.1%, so accuracy is meaningless and the model needs precision-recall metrics. Low review score is left as possible later work.
- **Cost / Security:** None.
- **Rejected:** Low review score (it depends on delivery outcomes, so its features overlap with post-outcome data and the leakage risk is highest); repeat purchase (about 3.1% positives in a short, censored window).

### D-008: Untrack `data/`

- **Context:** Nine raw files were tracked before D-006 added `data/` to `.gitignore`. Pushing them redistributes a CC BY-NC-SA dataset, and the brief says not to commit large raw datasets.
- **Options:** Leave tracked; untrack; untrack and rewrite history.
- **Chosen:** Untrack with `git rm -r --cached data/`. The files stay on disk. History is not rewritten.
- **Reason:** Stops future commits carrying the data without a destructive history rewrite.
- **Trade-offs:** Earlier commits still contain the files. If the repository is made public, those commits still expose the data, though with attribution under the same licence that is permitted.
- **Security:** No secrets were ever in `data/`.
- **Rejected:** History rewrite (needs a force-push and breaks existing clones).

---

## Design decisions

Evidence for these entries is in [docs/data/EDA_FINDINGS.md](docs/data/EDA_FINDINGS.md) and [docs/data/DATA_MODEL.md](docs/data/DATA_MODEL.md).

### DD-01: Kimball star schema; facts never join to facts

- **Context:** Items, payments and reviews hang off `order_id` at different grains. In the EDA, joining them side by side overstated item revenue by 4.54%, or 5.02% with reviews.
- **Options:** One wide order table; a star schema with one grain per fact.
- **Chosen:** Four facts (`fact_order_items`, `fact_orders`, `fact_payments`, `fact_reviews`) and five dimensions. Each table states its grain. Facts meet only through shared dimensions or after aggregation to a common grain; `fact_orders` pre-aggregates items and payments.
- **Trade-offs:** Some queries need two steps (aggregate, then join).
- **Rejected:** A wide table (silent fan-out).

### DD-02: Customer grain is `customer_unique_id`

- **Context:** `customer_id` is issued per order: 99,441 ids belong to 96,096 people.
- **Chosen:** `dim_customer` at the `customer_unique_id` grain. Location at the time of the order is carried on the facts, because 250 customers changed location.
- **Rejected:** `customer_id` (every customer would look like a one-time buyer).

### DD-03: Reviews keyed on (`review_id`, `order_id`)

- **Context:** `review_id` is not unique (789 ids span several orders), and 547 orders have 2-3 reviews.
- **Chosen:** `fact_reviews` grain is (`review_id`, `order_id`), with an `is_latest_review_for_order` flag to use before relating reviews to orders.
- **Rejected:** Deleting duplicates (that loses source rows).

### DD-04: Revenue from order items only

- **Context:** Payments differ from items plus freight on 380 of 98,665 orders, mostly instalment orders.
- **Chosen:** Revenue is `fact_order_items.price` (or `item_total_value` when freight is included). `fact_payments` is analysed on its own and never forced to tie.
- **Rejected:** Payment value as revenue; reconciling the two by adjustment.

### DD-05: Surrogate keys with an unknown member

- **Context:** 279 customer rows have a zip prefix that is missing from geolocation, and some milestone dates are null.
- **Chosen:** Deterministic surrogate keys (`row_number()` over the natural key) and a `-1` unknown member in every dimension, so a failed lookup never drops a fact row. `dim_date` uses `yyyymmdd` keys, with `-1` meaning "not applicable".
- **Rejected:** Inner joins that drop rows; null foreign keys.

### DD-06: Convert geolocation CSV to Parquet in the build

- **Context:** Kaggle ships geolocation as a CSV (about 1M rows), but staging reads Parquet.
- **Chosen:** `ensure_geolocation_parquet` in `build_warehouse.py` converts the CSV once if the Parquet file is missing. It keeps zip prefixes as text so leading zeros survive.
- **Trade-offs:** Not yet tested against Kaggle's original download (see [README.md](README.md)).

### DD-07: Customer segmentation is optional

- **Context:** 96.9% of customers ordered once, so frequency-based clusters carry little information (Phase 0 §7).
- **Chosen:** K-Means segmentation is tried honestly and dropped if it adds little. It is not a committed deliverable.
- **Rejected:** Committing to RFM segmentation up front.
