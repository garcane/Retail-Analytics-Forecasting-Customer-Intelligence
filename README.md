# Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)

A local implementation of what would have been built on Google Cloud and BigQuery. DuckDB replaces BigQuery as the warehouse and query engine, and all SQL is written in DuckDB's dialect. Nothing here needs a cloud account.

The original cloud brief (BigQuery, Dataflow, Vertex AI, monitoring) is kept unchanged in `Cloud Portfolio — Master Agent Prompt.md`, `GCP.md` and the Retail Analytics project document, in case parts of it come back later. Current scope and decisions are in `PROJECT_STATUS.md` and `docs/HANDOFF.md`.

## 1. Get the data

The dataset is the **Brazilian E-Commerce Public Dataset by Olist**, published on Kaggle:

<https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce>

It is licensed **CC BY-NC-SA 4.0** (attribution, non-commercial, share-alike). The raw files are not stored in Git (`data/` is in `.gitignore`), so download them yourself.

**Option A: in the browser.** Log in to Kaggle (a free account is required), click *Download*, and unzip the CSV files into `data/` at the repo root.

**Option B: Kaggle CLI.** Create an API token in your Kaggle account settings and install the CLI (`uv tool install kaggle`). Keep the token out of Git. Then:

```
kaggle datasets download -d olistbr/brazilian-ecommerce -p data --unzip
```

You should end up with these nine files in `data/`:

```
olist_customers_dataset.csv
olist_geolocation_dataset.csv
olist_order_items_dataset.csv
olist_order_payments_dataset.csv
olist_order_reviews_dataset.csv
olist_orders_dataset.csv
olist_products_dataset.csv
olist_sellers_dataset.csv
product_category_name_translation.csv
```

**Geolocation: download the CSV, the build converts it for you.** Kaggle ships geolocation as a CSV with about a million rows, by far the largest file in the dataset. The project stores it as Parquet (16.6 MB here, compressed and typed), and the staging SQL reads `data/olist_geolocation_dataset.parquet`. You do not convert it yourself:

1. Put the original `olist_geolocation_dataset.csv` in `data/` with the other files.
2. Run the build (section 2). On the first run it prints `converted olist_geolocation_dataset.csv -> olist_geolocation_dataset.parquet`, keeping zip prefixes as text so leading zeros such as `01046` survive.
3. Later runs find the Parquet file and skip the step. You can delete the CSV afterwards if you want the space back.

If neither file is present, the build stops with an error that points back to this section. The conversion reproduced the existing Parquet file exactly (1,000,163 rows) when tested on a CSV generated from it. It has not been run against Kaggle's original download, so if the build fails on geolocation, check this step first.

## 2. Set up and build the warehouse

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```
uv sync
uv run python src/transformation/build_warehouse.py
```

This rebuilds `warehouse.duckdb` from scratch (it is git-ignored), running `sql/staging`, `sql/dimensions` and `sql/facts` in order. It then runs the checks in `sql/validation/checks.sql` and exits non-zero if any fail. Optional flags: `--db` and `--data-dir`.

On a network that intercepts TLS, `uv` may need the `--native-tls` flag.

## 3. Run the baselines and tests

```
uv run python src/ml/late_delivery_baseline.py
uv run python src/ml/forecast_baseline.py
uv run python src/ml/drift_analysis.py   # a few minutes
uv run python src/ml/recalibration.py  # a few minutes
uv run pytest
```

Metrics are written to `reports/`, and `docs/ml/PHASE2_BASELINES.md` explains them. The tests that read the real warehouse are skipped if `warehouse.duckdb` has not been built.

## 4. Explore

- `notebooks/01_dataset_discovery.ipynb`: dataset discovery and EDA.
- `docs/ml/LEAKAGE_ANALYSIS.md`, `docs/ml/PHASE2_BASELINES.md` and `docs/ml/DRIFT_ANALYSIS.md` and `docs/ml/RECALIBRATION_AND_WINDOW.md`: ML targets, leakage rules, baseline results, drift tests and recalibration.
- `ARCHITECTURE.md` and `DECISIONS.md`: design and decision log.
- `docs/data/DATA_MODEL.md`: star schema, grains and design decisions.
- `docs/data/EDA_FINDINGS.md`: EDA findings.
- `docs/phase0/PHASE0_DISCOVERY.md`: Phase 0 discovery report.

Notebooks locate `data/` relative to the working directory, so run them with the repo root or `notebooks/` as the working directory.

## Attribution

Data: Olist, via Kaggle, CC BY-NC-SA 4.0. Derived work must keep the same licence and be non-commercial.
