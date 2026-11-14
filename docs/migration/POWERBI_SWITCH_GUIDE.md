# Power BI switch guide: from the local files to Snowflake

> **Live status (2026-11-13):** this page was written before the live run and its body is kept as the design record. The pipeline has since run on Snowflake: setup and RAW load (counts exact, no stray carriage returns), `dbt build` PASS=367 including the `ASOF JOIN`, reconciliation 22/22 with 0 differences, and the Tier 1 Python models. Not run: the ML write-back and the Power BI patched copy. Where this page says NOT YET RUN or UNVERIFIED about those steps, read [snowflake/README.md](../../snowflake/README.md) for the measured result.

How to point the dashboard at the Snowflake implementation (`RETAIL_OLIST`) instead of the exported Parquet/CSV files.

**Status of this guide: written offline, nothing here has been run against Snowflake or Power BI Desktop.**

| Claim | Status |
|---|---|
| `apply_snowflake_source.py` writes a patched copy and changes only `expressions.tmdl` plus each table's partition source; everything else is byte-identical; the original project is untouched | VERIFIED offline by `tests/test_powerbi_snowflake.py` (68 passed, 2026-11-08, run with pytest from a Python 3.13 venv; the repo `.venv` does not include the dev group) |
| Every template keeps the table's existing `Table.TransformColumnTypes` step and types exactly the columns the model reads | VERIFIED offline by the same tests |
| The patched copy has **not been opened** in Power BI Desktop, and no refresh has been run | UNVERIFIED. The M navigation (`Snowflake.Databases` > database > schema > view) is the standard shape but has not been executed |
| The `PBI` views and `ML` tables exist in Snowflake and return the expected columns and types | UNVERIFIED. Snowflake setup, ingestion and `dbt build` have not been run (see `snowflake/README.md`) |
| Which sign-in methods Power BI Desktop offers for Snowflake (see [Authentication](#authentication-unverified)) | UNVERIFIED. Check the current Microsoft and Snowflake documentation |

## What the patched copy changes

`powerbi/snowflake/apply_snowflake_source.py` copies `RetailAnalytics.pbip`, `RetailAnalytics.Report` and `RetailAnalytics.SemanticModel` to a git-ignored folder (default `powerbi_snowflake/` at the repo root) and rewrites, in the copy only:

- `definition/expressions.tmdl`: the `DataFolder` parameter is replaced by two text parameters, `SnowflakeServer` (placeholder `<account>.snowflakecomputing.com`, never a real account) and `SnowflakeWarehouse` (`RETAIL_WH`).
- The `source =` block of the partition in each of the 12 import tables, using the M templates in `powerbi/snowflake/templates/`.

Report pages and visuals, relationships, measures, column definitions, formatting, the date tables and `model.tmdl` are copied byte for byte. The committed project (and its file-based model) is never edited.

## Step by step

1. **Prerequisite (done 2026-11-13):** the Snowflake objects exist, `dbt build` has populated the `PBI` schema, and `src/ml/publish_ml.py --yes --write` has written the `ML` tables (see [the ML tables](#the-three-tables-that-depend-on-python-write-back)).
2. **Create the patched copy** from the repo root (use the repo venv; do not run `uv sync`):

   ```
   .\.venv\Scripts\python.exe powerbi/snowflake/apply_snowflake_source.py
   ```

   This switches all 12 tables to Snowflake. `--ml-on-files` patches only the nine `PBI` tables and leaves `late_delivery_scores`, `forecast_backtest` and `flag_share` on their Parquet/CSV sources (keeping the `DataFolder` parameter); it was needed only before the `ML` tables existed.
   The script refuses to write into a non-empty target without `--force`, and `--force` replaces only the three project items by name.
3. **Check that `powerbi_snowflake/` is git-ignored** (`git check-ignore powerbi_snowflake` should print the path; the repo `.gitignore` lists it). The patched copy will contain your account name once you enter it, so it must never be committed.
4. **Open** `powerbi_snowflake\RetailAnalytics.pbip` in Power BI Desktop (same preview-feature requirements as `powerbi/README.md`). It has **not been opened in Desktop by anyone yet**; if Desktop reports an error, note the exact message and the file it names.
5. **Set the parameters:** *Home > Transform data > Manage parameters*.
   - `SnowflakeServer`: your Snowflake account host, `<account>.snowflakecomputing.com` (the account identifier from Snowflake; do not commit it).
   - `SnowflakeWarehouse`: `RETAIL_WH`.
   - With `--ml-on-files`, also set `DataFolder` to the full path of `powerbi/data` as in `powerbi/README.md` (the exported Parquet/CSV files must exist for the three ML tables).
6. **Sign in** when Desktop prompts for the Snowflake data source (see below). Use a user whose **default role** is `RETAIL_REPORTER`, which should be the only role with `SELECT` on the `PBI` (and `ML`) schemas. The templates do not set a role option, so Desktop uses the user's default role. UNVERIFIED that no explicit role is needed.
7. **Close & Apply**, then run the **first-open checklist** from `powerbi/README.md` / the DAX specification. The DuckDB reference figures are: net revenue R$ 13,494,400.74, 98,199 net orders, 8.13% late, 21.5% late among the riskiest 10%. If the cards match, the views, types and relationships are right; if not, first compare the PBI view columns with the table below. (These are DuckDB-derived numbers; the reconciliation has since shown the Snowflake marts equal to DuckDB, 22/22 checks with 0 differences.)

## Authentication (UNVERIFIED)

**UNVERIFIED: I did not check which authentication methods Power BI Desktop currently offers for the Snowflake connector.** Check the current Microsoft Learn page for the Power Query Snowflake connector and Snowflake's own documentation for Power BI before choosing. The options to look for, none confirmed here:

- Microsoft Entra ID / single sign-on (needs Snowflake-side security-integration setup).
- Snowflake user name and password, which may be blocked or require MFA depending on the account's authentication policy.
- Key-pair authentication: the dbt and Python parts of this project use key pairs (`SNOWFLAKE_PRIVATE_KEY_PATH`), but whether Desktop can use a key pair for this connector is not confirmed. Do not assume it can.

Never write credentials into the `.pbip` files, the parameters or the repo. Desktop stores them in its own per-user data-source settings.

## Table to Snowflake object mapping

All objects are in database `RETAIL_OLIST`. Every template navigates `Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse)` > database > schema > object, lower-cases the column names with `Table.TransformColumnNames(_, Text.Lower)` (Snowflake returns upper-case names) and then applies the table's **existing** `Table.TransformColumnTypes` step verbatim.

| Power BI table | Snowflake object | Original source | Feeds from |
|---|---|---|---|
| `dim_date` | `PBI.DIM_DATE` | `dim_date.csv` | dbt `MARTS.dim_date` |
| `dim_customer` | `PBI.DIM_CUSTOMER` | `dim_customer.csv` | dbt `MARTS.dim_customer` |
| `dim_product` | `PBI.DIM_PRODUCT` | `dim_product.csv` | dbt `MARTS.dim_product` |
| `dim_seller` | `PBI.DIM_SELLER` | `dim_seller.csv` | dbt `MARTS.dim_seller` |
| `dim_geography` | `PBI.DIM_GEOGRAPHY` | `dim_geography.csv` | dbt `MARTS.dim_geography` |
| `fact_orders` | `PBI.FACT_ORDERS` | `fact_orders.parquet` | dbt `MARTS.fact_orders` plus derived columns |
| `fact_order_items` | `PBI.FACT_ORDER_ITEMS` | `fact_order_items.parquet` | dbt `MARTS.fact_order_items` plus `is_net_order` |
| `fact_payments` | `PBI.FACT_PAYMENTS` | `fact_payments.parquet` | dbt `MARTS.fact_payments` |
| `fact_reviews` | `PBI.FACT_REVIEWS` | `fact_reviews.parquet` | dbt `MARTS.fact_reviews` (column subset) |
| `late_delivery_scores` | `ML.LATE_DELIVERY_SCORES` | `late_delivery_scores.parquet` | Python write-back |
| `forecast_backtest` | `ML.FORECAST_BACKTEST` | `forecast_backtest.csv` | Python write-back |
| `flag_share` | `ML.FLAG_SHARE` | `flag_share.csv` | Python write-back |

The `PBI` objects are views (the templates use `Kind="View"`); the `ML` objects are tables (`Kind="Table"`). If a `PBI` object is built as a table instead, change the `Kind` in the template and re-run the script.

### What the `PBI` views must expose

Column names, order is irrelevant but names and types are not: they must match what `src/powerbi/export_data.py` writes, because the model's `sourceColumn` entries and the type step name them. A test checks that each template types exactly the columns the model reads. Snowflake `NUMBER` columns load fine into `Int64.Type`/`Currency.Type`; booleans must be `BOOLEAN`, dates `DATE`, timestamps `TIMESTAMP_NTZ`.

Derived columns that do not exist on the DuckDB marts and must be added in the `PBI` views (definitions from `FACT_SQL` in `export_data.py`):

| Column | On | Definition |
|---|---|---|
| `is_net_order` | `fact_orders` | `order_status not in ('canceled','unavailable') and item_count > 0` |
| `is_net_order` | `fact_order_items` | `order_status not in ('canceled','unavailable')` (no item-count condition) |
| `is_labelled_delivery` | `fact_orders` | `order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly` |
| `promised_days` | `fact_orders` | `datediff(second, purchase_ts, estimated_delivery_ts) / 86400.0`, as a float (cast before dividing) |
| `delay_bucket` | `fact_orders` | null unless `order_status = 'delivered'` and `delivery_delay_days` is not null; then `'on time or early'` (<= 0), `'1-3 days late'` (<= 3), `'4-7 days late'` (<= 7), `'8-14 days late'` (<= 14), else `'more than 14 days late'` |
| `delay_bucket_order` | `fact_orders` | same null rule; 1, 2, 3, 4, 5 for the five buckets above |

Other points the views must reproduce from the export:

- `dim_date` excludes the "Not applicable" row (`date_key` -1, null `full_date`): a date table's key cannot contain blanks. Facts pointing at -1 fall into Power BI's own (Blank) member.
- `fact_reviews` exposes only `review_id, order_id, customer_key, review_creation_date_key, review_answer_date_key, review_creation_ts, review_answer_ts, review_score, has_comment, is_latest_review_for_order`. Review comment text is deliberately not exposed.
- `fact_order_items` is `fact_order_items` plus `is_net_order`; `fact_payments` and the other dimensions are the mart columns as they are.
- `late_delivery_scores`, `forecast_backtest` and `flag_share` have the same columns as `late_delivery_scores.parquet`, `forecast_backtest.csv` and `flag_share.csv`, plus a leading `run_id` column added by the write-back. Write-back appends one block of rows per run and never deletes other runs, so the three ML templates keep only the latest `run_id` (text maximum; `run_id` is a UTC timestamp plus uuid) and drop the column before typing. The generated `run_id`s sort by time as text (for example `20261113T122357Z-a99b8a21`). The filter has not been run in Power BI Desktop.

## The three tables that depend on Python write-back

`late_delivery_scores`, `forecast_backtest` and `flag_share` are not produced by dbt. They come from the Python model scoring and forecast backtests, which would write to `ML.LATE_DELIVERY_SCORES`, `ML.FORECAST_BACKTEST` and `ML.FLAG_SHARE` through the opt-in write-back (`src/data_access`). That has run (2026-11-13, `src/ml/publish_ml.py --yes --write`): the three tables exist, are readable by `RETAIL_REPORTER`, and hold one run whose values match the DuckDB-built files. Re-run `publish_ml.py` to publish a new run; the templates pick the latest `run_id`. The report's Risk and Forecast pages depend on them.

## The `DataFolder` local-path issue

The committed `RetailAnalytics.SemanticModel/definition/expressions.tmdl` holds a local path (`DataFolder = "C:\Users\Student\GCP\powerbi\data"`), saved by Desktop on one machine, not the placeholder the project documents. As a result `tests/test_powerbi_project.py` (`test_committed_project_is_complete_and_holds_no_machine_path`, which expects the placeholder `DATA_FOLDER_PLACEHOLDER`) is expected to fail; that module is also marked `warehouse` and needs `warehouse.duckdb`. This was read from the test and the file, not confirmed by running it (the repo venv used for this work has no `jsonschema`). **This guide documents the issue and does not fix it**; the original project is left as is, and nothing in the Snowflake tests depends on that file passing.

The patched copy removes `DataFolder` entirely (or, with `--ml-on-files`, keeps the same committed value for the three ML tables, so set it to your own path in Desktop and never commit it).

## Known leftovers and limits

- `model.tmdl` is copied unchanged, so its `PBI_QueryOrder` annotation still lists `"DataFolder"` and does not list the two new parameters. It is only an ordering hint for the Power Query editor; whether Desktop ignores the stale name cleanly is UNVERIFIED. If it complains, edit the annotation in Desktop.
- The patched copy keeps the same `logicalId` in its `.platform` files as the original; do not publish both to one workspace.
- Import mode only: every refresh reads the Snowflake views and uses warehouse credits (`RETAIL_WH`, `AUTO_SUSPEND=60`). No cost has been measured.
- Nothing has been opened in Desktop, nothing refreshed, and no Snowflake connection has been made while writing this guide.
