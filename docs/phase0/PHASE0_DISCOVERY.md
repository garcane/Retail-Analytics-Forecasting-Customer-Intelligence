# Phase 0 — Discovery Report

**Project:** Google Cloud — Retail Analytics, Forecasting & Customer Intelligence Platform
**Date:** 2026-10-06
**Status:** Discovery complete for the data; architecture and ML target need approval (see §9). **No cloud resources have been provisioned.**

> Method note. Every dataset figure below comes from DuckDB queries run directly over the files in `data/` (scratch script, not yet the notebook — `notebooks/01_dataset_discovery.ipynb` is written but has **never been executed**, so it contains no outputs). Items marked **UNVERIFIED** were not confirmed against a primary source and must be re-checked before they drive a decision.

---

## 1. Dataset source and licence

| Item | Finding | Verification |
|---|---|---|
| Name | Brazilian E-Commerce Public Dataset by Olist | Kaggle API metadata |
| Owner | Olist | Kaggle API metadata |
| Source | `kaggle.com/datasets/olistbr/brazilian-ecommerce` | Kaggle API metadata |
| **Licence** | **CC BY-NC-SA 4.0** | Kaggle API metadata (`licenseName`) |
| Last updated | 2021-10-01 | Kaggle API metadata |
| Attribution | "Thanks to Olist for releasing this dataset." | Kaggle API metadata |
| Anonymisation | Data anonymised; partner names in review text replaced with Game of Thrones house names | Kaggle description |

**Implications of CC BY-NC-SA 4.0**
- **NonCommercial:** a portfolio / educational project is fine. It must not be presented as, or used for, commercial work.
- **ShareAlike:** adapted material (curated tables, derived features, possibly model artefacts trained on it) should be shared under the same licence if shared at all. Attribute Olist and link the licence in the README.
- **Redistribution:** `data/` is currently *tracked in Git* (see §8). Pushing it to a public GitHub repo redistributes the dataset. Permitted with attribution + same licence, but it also conflicts with Master Prompt §26 ("do not commit large raw datasets"). Recommendation: untrack it and document a download step instead.

Not verified from a primary source: whether the Kaggle licence text has any extra restrictions beyond standard CC BY-NC-SA. Read the full licence deed before publishing.

## 2. Dataset structure

| Table | Rows | Cols | Grain (verified) | Key |
|---|---:|---:|---|---|
| orders | 99,441 | 8 | one row per order | `order_id` |
| customers | 99,441 | 5 | one row per **order-customer link** (not per person) | `customer_id` |
| order_items | 112,650 | 7 | one row per item in an order | `(order_id, order_item_id)` |
| order_payments | 103,886 | 5 | one row per payment instalment/method per order | `(order_id, payment_sequential)` |
| order_reviews | 99,224 | 7 | **not** one per review_id (see §3) | `(review_id, order_id)` |
| products | 32,951 | 9 | one row per product | `product_id` |
| sellers | 3,095 | 4 | one row per seller | `seller_id` |
| category_translation | 71 | 2 | one row per Portuguese category | `product_category_name` |
| geolocation | 1,000,163 | 5 | many points per zip prefix (19,015 prefixes) | none |

Relationships: `orders → customers` (1:1 on `customer_id`), `orders → items / payments / reviews` (1:N on `order_id`), `items → products`, `items → sellers`, `products → translation`. `customers`/`sellers` link to `geolocation` only through zip-code prefix (many-to-many in raw form).

**Size:** ~80 MB on disk (nine CSV files). This is the single most important fact for architecture: the whole dataset fits in laptop memory and far inside every GCP free-tier limit.

**Types:** all timestamps parse as `TIMESTAMP`; zip prefixes must be read as `VARCHAR` (leading zeros). Two column names are misspelled in the source (`product_name_lenght`, `product_description_lenght`) — normalise in staging, do not edit raw.

## 3. Data quality findings

**Keys and duplicates**
- All primary keys unique except reviews. `review_id` is **not** unique: 814 surplus rows (the same `review_id` attached to different orders). 551 orders carry more than one review row.
- `customer_id` is regenerated per order. **99,441 `customer_id` → 96,096 real customers (`customer_unique_id`).** Customer analytics must group on `customer_unique_id`.

**Referential integrity** — zero orphans in every child→parent direction (items→orders/products/sellers, payments→orders, reviews→orders, orders→customers). Parent→child gaps:
- 775 orders have no items (status mix: unavailable/canceled/created etc.)
- 1 order has no payment
- 768 orders have no review
- 2 product categories missing from the translation table: `pc_gamer`, `portateis_cozinha_e_preparadores_de_alimentos`

**Nulls**
- `orders`: `order_approved_at` 160, `order_delivered_carrier_date` 1,783, `order_delivered_customer_date` 2,965. Most are explained by status (shipped/processing/canceled…), but **8 delivered orders lack a delivery timestamp** and 14 delivered orders lack an approval timestamp.
- `reviews`: title 87,656 null, message 58,247 null (only 40,977 have free text).
- `products`: 610 with no category/name length/description length/photo count; 2 with no weight/dimensions.

**Logical violations** (documented, not removed)
- 1,359 orders handed to the carrier before `order_approved_at`
- 23 orders delivered to the customer before the carrier date
- 74 reviews created before the order's purchase timestamp
- Zero cases of approval before purchase or delivery before purchase.

**Values**
- No non-positive prices (min 0.85, max 6,735). 383 items have zero freight.
- Payments: 5 `payment_type` values including 3 `not_defined` (value 0) and 6 zero-value vouchers.
- Review scores: 1★ 11,424 · 2★ 3,151 · 3★ 8,179 · 4★ 19,142 · 5★ 57,328 (heavily skewed high).

**Geolocation:** 42 points fall outside a Brazil bounding box; 157 distinct customer zip prefixes have no geolocation row. Needs collapsing to one row per prefix before use as a dimension.

**Reconciliation:** of 98,665 orders present in both items and payments, 380 (0.4%) have `sum(price+freight)` ≠ `sum(payment_value)` (tolerance 0.01). Totals: items 15,843,410 vs payments 15,846,280. Payments are close to, but not exactly, a second view of the same money — revenue must have one declared definition.

## 4. Join fan-out (an explicit competency in the brief)

Joining children at different grains side by side inflates item-level measures:

| Join | Rows | `sum(price)` | Overcount |
|---|---:|---:|---:|
| orders ⟕ items | 113,425 | 13,591,643.70 | 0.0% (baseline) |
| + payments | 118,434 | 14,209,250.31 | **+4.5%** |
| + payments + reviews | 119,143 | 14,273,699.65 | **+5.0%** |

Rule for the model: collapse every child to order grain *before* joining, or keep facts at their own grain and join only via conformed dimensions.

## 5. Time coverage and what it means for forecasting

- Purchases: 2016-09-04 → 2018-10-17, but **volume is very uneven**: 4 orders in Sep 2016, 324 in Oct 2016, 1 in Dec 2016, then ~800/month in Jan 2017 rising to ~7,000/month by early 2018, and only **16 and 4 orders in Sep/Oct 2018**.
- Sensible modelling window: **2017-01-01 → 2018-08-28** (87 weekly points, 600 days with orders). Earlier/later data are sparse tails and would distort any time-series model; treat as a documented exclusion, not silent deletion.
- Only ~1.7 years of history ⇒ **one** observation of each annual season. Nov 2017 (7,544 orders, the peak) cannot be validated as "seasonal" from a single occurrence. A seasonal-naïve baseline with a 52-week period has almost no usable history, and a test set cannot confirm yearly seasonality. Be explicit about this limit rather than reporting a flattering metric.
- Growth flattens from Jan 2018 (~6,100–7,300/month). The series has trend + a level shift; a trend-only baseline will mis-extrapolate.

## 6. Business-question evidence (associations only, not causes)

- Delivered orders: median 10 days to deliver (mean 12.5); **8.1% delivered after the estimated date.**
- **Late delivery is associated with lower review scores in this dataset:** mean 2.57 (late, n=7,701) vs 4.29 (on time, n=88,658). This is association; confounders (product type, seller, region, expectations) are not controlled.
- **Customers:** 93,099 of 96,096 (96.9%) placed exactly one order; ~3.1% are repeat customers (max 17 orders). RFM "frequency" will be near-degenerate, and any repeat-purchase target is severely imbalanced and thinly observed.
- **Categories:** 74 category values after translation; top by item revenue: health_beauty (1.26M), watches_gifts (1.21M), bed_bath_table (1.04M), sports_leisure (0.99M), computers_accessories (0.91M).
- **Sellers:** 3,095 sellers; top 10 sellers = 13.2% of revenue, top 10% of sellers = 67.6%.
- Revenue measured as `sum(price)` over items: 13.59M BRL (freight excluded; payments differ, see §3).

## 7. Candidate analytical grains, targets, features, leakage

**Fact grains (proposed, to confirm in Phase 1):** `fact_order_items` (item), `fact_orders` (order, with payment/review pre-aggregated to order grain), `fact_payments` (payment), `fact_reviews` (review, deduplicated by an explicit rule). Dimensions: customer (on `customer_unique_id`), product, seller, date, geography (zip prefix).

**Forecasting target (recommended):** weekly order count, 2017-01 → 2018-08, with time-ordered splits and naïve / moving-average baselines first. Revenue as a secondary target.

**Supervised ML candidates** (final choice is a Phase 0 → 1 approval gate, §9):

| Candidate | Target / rate | Prediction point | Assessment |
|---|---|---|---|
| **A. Low review (1–2★)** | 14.6% of reviews (≈14.6k/99.2k) | order approval / dispatch | Meaningful, moderately imbalanced, real operational use (proactive service). Needs one deduplicated review per order; leakage risk is highest here (actual delivery timing). |
| **B. Late delivery** | 8.1% of delivered | at purchase | Clean target from timestamps, no review dependency, directly feeds A. Features available at purchase: seller, product weight/dimensions, freight, seller–customer geography, estimated delivery window. |
| C. Repeat purchase | ~3.1% of customers | after first order | Weakest: tiny positive class, short observation window, high censoring. Probably not recommended. |

Recommendation: **A (or B) as the supervised problem, plus the weekly forecast; K-Means segmentation evaluated honestly and dropped if it adds little** (96.9% single-order customers makes frequency-based clusters uninformative).

**Leakage risks to document in `docs/ml/LEAKAGE_ANALYSIS.md`:**
- Delivery timestamps, late flag and review timestamps are *post-outcome* for target A at an approval-time prediction point.
- Seller/product aggregates (average review score, late rate) must be computed from orders strictly *before* each order's purchase date, or they leak the future.
- `order_status` at extraction time is a post-hoc state (e.g. canceled/delivered).
- Repeated reviews per order and identifiers (`customer_unique_id`, `seller_id` as high-cardinality categoricals).
- Customer-level features need a fixed cutoff date and an observation window.

**Customer features available:** order count, total spend, AOV, recency (vs. cutoff), category diversity, mean review, delivery experience, state/city/zip.

## 8. Repository and environment findings (problems to report)

1. **No `.gitignore`.** Needs one before anything else is added (credentials, `*.json` keys, model artefacts, `data/`, notebook checkpoints).
2. **`data/` is tracked in Git** (~80 MB working files; pack is ~40 MiB). The history also contains a commit that rewrote ~209k lines of `olist_order_reviews_dataset.csv` (line-ending change). Untracking is easy; *removing it from history* requires a destructive rewrite — not done, needs your decision.
3. **`main.ipynb`** is a legacy notebook of auto-generated `clean_data` functions (looks like a Data Wrangler export), with empty trailing cells. It cleans in place (title-casing, replacing `_`), which contradicts the "raw is immutable / don't silently transform" rule. `main.py` is deleted in the working tree.
4. **`notebooks/01_dataset_discovery.ipynb`** is untracked, well structured, and **unexecuted**. `nbconvert` is not installed in the venv.
5. **`pyproject.toml`** has duckdb/pandas/polars/pyarrow/matplotlib/seaborn only. Missing for later phases: scikit-learn, xgboost, mlflow, pytest, google-cloud-* libraries, apache-beam (if used), a SQL/dbt tool. `uv.lock` and `pyproject.toml` already have uncommitted modifications; I changed nothing.
6. **`gcloud` / `bq` / `gsutil` are not installed.** No evidence yet of a GCP project, billing account, or credentials.
7. **Python 3.13** is pinned. **UNVERIFIED:** whether the current Apache Beam release and Dataflow worker images support Python 3.13, and Beam on native Windows has historically been awkward. Check before committing to Dataflow (fallbacks: WSL, Docker, Cloud Shell, or a lower Python for the pipeline package only).
8. **`GCP Retail Project Local vs Cloud Architecture.md` local-equivalent stack is heavier than the brief needs.** Prometheus + Grafana + FastAPI locally conflicts with Master Prompt §31 ("do not overengineer") given that batch inference is the preferred path. Suggest MLflow only for local tracking; skip Prometheus/Grafana.

## 9. Architecture assessment

### Minimal viable architecture (recommended)

```
Local: EDA + baselines (DuckDB, notebooks)                         [already started]
   ↓
GCS (raw/ immutable copy of the CSV/Parquet files)
   ↓
BigQuery  ← load jobs, then SQL: staging → curated → analytical (star schema)
   ↓          partitioning/clustering, DQ checks, cost experiment
BI (Power BI Desktop / Looker Studio) + forecasting & feature tables
   ↓
Local experimentation → ONE reproducible Vertex AI custom training job
   ↓
Vertex AI Model Registry (champion, lifecycle labels, metrics, git commit)
   ↓
BATCH prediction → predictions table in BigQuery
   ↓
Cloud Monitoring (job health, logs-based metrics, budget alerts); drift demo labelled SIMULATED
```

### Dataflow: honest assessment
For ~80 MB, **BigQuery load jobs + SQL (or even local DuckDB) do everything Dataflow would, faster and cheaper.** Dataflow is justifiable only as a bounded, deliberate demonstration (e.g. one Beam batch job: validate and normalise raw files → typed Parquet in `staging/`, with a documented three-way comparison: local vs BigQuery SQL vs Dataflow). The Direct-Runner-to-Dataflow-Runner portability argued for in `GCP Retail Project Local vs Cloud Architecture.md` is a real talking point. Cost is small (cents to low dollars) but complexity and the Python 3.13 / Windows issue above are real. This is an **approval gate** (child prompt §36: "introducing unnecessary services").

### Options table

| Decision | Option 1 | Option 2 | Recommendation |
|---|---|---|---|
| Ingestion/transform | BigQuery SQL only | + one Dataflow/Beam job | Option 2 only if you accept the complexity and want the Beam story; otherwise Option 1 with the comparison written up |
| SQL transformation tool | Plain `sql/` scripts run by Python | dbt (`dbt-bigquery` + `dbt-duckdb` locally) | dbt fits the architecture-philosophy doc (tests, lineage, portability DuckDB↔BigQuery) but adds a tool; decide before Phase 4 |
| Region | `us-central1` / `US` (inside free tier) | `southamerica-east1` (closer to the data's origin, not free-tier) | US: data is public/anonymised so residency is not a concern, and Always-Free GCS is US-only |
| Inference | Batch | Online endpoint | Batch; one short-lived endpoint demo only if wanted, then undeploy |
| BI | Power BI Desktop (you know it; Windows) | Looker Studio (free, native BigQuery) | Power BI per brief; Looker Studio as fallback |

## 10. Current GCP services, pricing and free-tier implications

**Verified from the official Google Cloud free-programme page:**
- Free Trial: **$300 credit, 90 days**, no billing during the trial.
- Always Free: BigQuery **1 TiB queries + 10 GiB storage per month**; Cloud Storage **5 GB-months, US regions only**; Logging first 50 GiB/project/month; Secret Manager 6 active secret versions + 10k access ops/month.
- **Dataflow and Vertex AI are not in the Always-Free table** — their usage burns trial credit/billing.

**UNVERIFIED (third-party search snippets; the official pricing pages could not be fetched — re-check on cloud.google.com/products/calculator before provisioning):**
- BigQuery on-demand ≈ $6.25 / TiB scanned; active storage ≈ $0.02 / GiB-month, long-term ≈ $0.01.
- Dataflow batch (us-central1) ≈ $0.056 / vCPU-hr and $0.003557 / GiB-hr (default 1 vCPU + 3.75 GB worker ≈ $0.08/hr).
- Vertex AI custom training `n1-standard-4` ≈ $0.219/hr; batch prediction and online endpoints are billed per node-hour; online endpoints bill while idle.

### Expected cost (estimates, to be replaced by actuals in `COST.md`)

| Component | Expectation | Risk |
|---|---|---|
| GCS | ~80 MB; inside free tier if in a US region | none |
| BigQuery | well under 1 GiB stored, queries far under 1 TiB/month → $0 | accidental `SELECT *` loops; mitigate with `maximum_bytes_billed` |
| Dataflow (if used) | minutes × 1–2 small workers → cents–low dollars | autoscaling to many workers, leftover jobs |
| Vertex AI training | one 15–30 min job → cents | notebook instances left running |
| Vertex AI batch prediction | few cents–<$1 (node spin-up overhead) | — |
| Vertex AI online endpoint | **always-on node ≈ dollars/day** | forgetting to undeploy — the main cost risk |
| Monitoring/Logging | inside free allotments | log volume from Dataflow |

Everything fits comfortably inside the $300 trial. Note that a billing **budget only alerts, it does not cap spend** — set budget alerts at low thresholds *and* per-query byte limits, and verify teardown (E20).

## 11. IAM and security requirements (to implement in Phase 3, not yet)

- Separate identities: a human developer user (project-scoped, not Owner for daily work), and dedicated service accounts per function — e.g. `sa-ingest` (GCS object admin on the project bucket, BigQuery data editor on the raw/staging datasets), `sa-transform` (BigQuery data editor + job user), `sa-vertex-train` (Vertex AI user, GCS/BigQuery read, Artifact write), `sa-batch-predict` (read models/features, write predictions).
- No service-account JSON keys in the repo; prefer `gcloud auth application-default login` locally and attached service accounts in cloud. Secret Manager only if a real secret exists (none currently).
- Add key/credential patterns to `.gitignore` and run a secrets scan on history before publishing.
- Document why each role exists (`SECURITY.md`).

## 12. Cost risks and mitigations
1. Online endpoint left deployed → default to batch; if used, time-box and delete; record in E17/E20.
2. Dataflow autoscaling / orphaned jobs → cap `max_num_workers`, small machine type, check job list after runs.
3. BigQuery scans → `maximum_bytes_billed`, dry-run first, partition/cluster experiment documents savings.
4. Vertex notebooks/workbench instances → don't use; train via custom jobs from scripts.
5. Trial expiry (90 days) → plan evidence capture and teardown to fit; schedule cloud work in a focused window rather than spreading it out.

## 13. Evidence plan
E01–E20 as listed in the child prompt §30. Phase 0 produces **no cloud evidence** (nothing provisioned). Local evidence available now: this report, the executed discovery notebook (once run). Cloud evidence starts at E01 in Phase 3. Anything simulated (drift demo) must carry a "SIMULATED" label.

## 14. Items covered (child prompt §43 checklist)

| # | Item | Status |
|---|---|---|
| 1–2 | Source, licence | Done (§1) |
| 3–4 | Structure, relationships | Done (§2) |
| 5 | Data types | Done (§2) |
| 6 | Date ranges | Done (§5) |
| 7–9 | Missing, duplicates, referential integrity | Done (§3) |
| 10 | Analytical grains | Proposed (§7), confirm in Phase 1 |
| 11–13 | Business questions, forecast target, ML target | Candidates (§6–7), **ML target needs approval** |
| 14–15 | Leakage, customer features | Done at planning level (§7); full analysis in Phase 6 |
| 16–19 | GCP services, pricing, free tier, IAM | Free tier verified; **pricing partly unverified** (§10); IAM planned (§11) |
| 20–21 | Minimal architecture, alternatives | Done (§9) |
| 22–23 | Cost risks, evidence | Done (§12–13) |

## 15. Decisions

### Decided
- **D-001 (2026-10-06, user): DuckDB is the engine for the implementations.** The local warehouse (staging → curated → dimensional model → features → forecast/ML inputs) is built in DuckDB, reading the existing Parquet/CSV files; DuckDB also executes the data-quality checks and the pytest suite.
  - SQL lives in `sql/` and is written to stay portable to BigQuery where practical (standard joins, CTEs, window functions). Known dialect differences (`date_trunc` return types, `QUALIFY`, `::` casts, `STRUCT`/`ARRAY` handling, identifier quoting) must be tracked in a short translation note rather than discovered at load time.
  - Consequence for the cloud phase: DuckDB cannot demonstrate BigQuery partitioning, clustering, slot/bytes-billed economics or IAM. Those still require a BigQuery run, so the cloud step becomes "load the same curated Parquet and re-run the same SQL in BigQuery", which is also the cleanest local → cloud story.
  - This narrows gate 4 below: plain SQL on DuckDB vs `dbt-duckdb` (which still targets DuckDB locally and can target BigQuery later).

### Open (approval gates)

1. **Dataflow:** include one bounded Beam job, or go BigQuery-SQL-only and document the comparison? (DuckDB makes the "local transform" side of that comparison trivial.)
2. **Region:** US (free tier) vs `southamerica-east1`?
3. **ML target:** A (low review), B (late delivery), or both? Is the weekly forecast the agreed forecasting target?
4. **Transform tool (DuckDB either way):** plain `sql/` scripts driven by Python, or `dbt-duckdb`?
5. **Repo hygiene:** add `.gitignore` and untrack `data/` (safe)? Rewrite Git history to purge the data (destructive, only if you want the repo public without the dataset in history)?
6. **Local stack:** drop Prometheus/Grafana/FastAPI from the local equivalents?
7. **GCP account:** do you already have a project/billing account or an unused $300 trial? I can't see this from the repo.

## 16. Known limitations of this discovery
- Figures come from a scratch script; the discovery notebook has not been executed, so its outputs are not yet reproducible evidence.
- BigQuery/Dataflow/Vertex pricing is not confirmed from official pages.
- Beam Python-3.13/Windows compatibility not tested.
- Dataset is one marketplace, 2016–2018, ~100k orders; findings must not be generalised to Brazilian e-commerce or to Olist today.
