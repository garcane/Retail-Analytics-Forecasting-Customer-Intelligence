# DuckDB to Snowflake + dbt: SQL migration inventory

> **Live status (2026-11-13):** this page was written before the live run and its body is kept as the design record. The pipeline has since run on Snowflake: setup and RAW load (counts exact, no stray carriage returns), `dbt build` PASS=367 including the `ASOF JOIN`, reconciliation 22/22 with 0 differences, and the Tier 1 Python models. Not run: the ML write-back and the Power BI patched copy. Where this page says NOT YET RUN or UNVERIFIED about those steps, read [snowflake/README.md](../../snowflake/README.md) for the measured result.

Status as of 2026-11-06, branch `feature/snowflake-dbt-migration`. **Everything on this page was produced and checked offline. No SQL in this repository has been executed on Snowflake.** Where a statement depends on Snowflake behaviour it is marked UNVERIFIED and listed in [section 9](#9-unverified-until-a-live-snowflake-run).

The DuckDB implementation (`sql/**`, `src/**`) is unchanged and remains the reference. The Snowflake implementation lives next to it in `snowflake/`, `src/data_access/`, `src/reconciliation/` and `powerbi/snowflake/`. This page records, for every SQL file and every SQL snippet embedded in Python or a notebook, how hard the move to Snowflake is, what had to change, which dbt model replaces it (as built, from `snowflake/dbt/models`) and how the result is checked.

Contents: [1 Classes](#1-classification) | [2 File-count reconciliation](#2-reconciling-git-ls-files-sql) | [3 Summary](#3-summary-counts) | [4 Inventory: DuckDB SQL files](#4-inventory-a-the-28-duckdb-sql-files) | [5 sql/bigquery](#5-inventory-b-sqlbigquery-reference-only-18-files) | [6 Embedded SQL](#6-inventory-c-sql-embedded-in-python-and-notebooks) | [7 Constructs](#7-construct-by-construct-translation) | [8 Caveats and intentional differences](#8-numeric-null-order-surrogate-key-and-tie-break-caveats) | [9 UNVERIFIED](#9-unverified-until-a-live-snowflake-run) | [10 Snowflake-side SQL](#10-inventory-d-sql-added-for-snowflake-93-files)

## 1. Classification

The class describes the work needed to make the DuckDB logic produce the same result on Snowflake, judged by reading the file.

| Class | Meaning |
|---|---|
| 1 direct | The query body runs on Snowflake as written (only the dbt wrapper is added). |
| 2 minor | Same structure and logic; function names, casts, NULL ordering or a construct such as `FILTER (WHERE ...)` are substituted. |
| 3 substantive rewrite | The mechanism is re-expressed (different CTE shape, different construct, or a mechanism that has no one-to-one Snowflake form) but the intended result is the same. |
| 4 redesign | The concept is absent, replaced by a different mechanism, or intentionally changed (enforced constraints, file readers, catalog introspection, parquet export, a build-failing check query). |

Result of reading the 28 DuckDB SQL files: **no file is class 1.** Every file either sits behind a DuckDB-only wrapper (`read_csv`, enforced `PRIMARY KEY`/`REFERENCES`, `${DATA_DIR}`) or relies on a DuckDB default that Snowflake does not share (decimal-to-double division, `AVG` of a boolean cast, NULL placement under `DESC`). A class 1 label would hide those.

## 2. Reconciling `git ls-files "*.sql"`

Command run on 2026-11-08 from the repository root, after the generated dbt output was untracked: `git ls-files "*.sql" | wc -l` printed **139**. (On 2026-11-06, before the cleanup, it printed 443 because 304 generated files were tracked by mistake.)

| Group | Files | Where it is accounted for |
|---|---|---|
| Original DuckDB pipeline, `sql/staging`, `sql/dimensions`, `sql/facts`, `sql/analytics`, `sql/ml`, `sql/validation` | 28 | [Section 4](#4-inventory-a-the-28-duckdb-sql-files), one row each, classified |
| Original GoogleSQL translation, `sql/bigquery/raw` (9) and `sql/bigquery/staging` (9) | 18 | [Section 5](#5-inventory-b-sqlbigquery-reference-only-18-files), one row each, reference only, not classified |
| New Snowflake-side SQL written for this migration (macros, models, singular tests, setup, ingestion) | 93 | [Section 10](#10-inventory-d-sql-added-for-snowflake-93-files), counted per folder |
| **Total** | **28 + 18 + 93 = 139** | |

The 46 original files (28 + 18) are the "46 `.sql` files" counted in the migration plan. The 304 generated files (`snowflake/dbt/dbt_packages/dbt_utils` 112, `snowflake/dbt/target/compiled` 192) were untracked with `git rm -r --cached` and are ignored by `snowflake/dbt/.gitignore`. Re-run `git ls-files "*.sql" | wc -l` and compare against the table before relying on the arithmetic.

## 3. Summary counts

| Class | DuckDB SQL files (28) | Embedded snippets (section 6, 14 entries; a mixed entry is counted at its highest class) |
|---|---|---|
| 1 direct | 0 | 0 |
| 2 minor | 16 (`dim_customer`, `dim_geography`, `dim_product`, `dim_seller`, 4 facts, 8 analytics) | 7 (entries 1, 3, 4, 5, 6, 7, 9) |
| 3 substantive rewrite | 11 (9 staging views, `dim_date`, `late_delivery_features`) | 1 (entry 2, which inherits `late_delivery_features.sql`) |
| 4 redesign | 1 (`validation/checks.sql`) | 6 (entries 8, 10, 11, 12, 13, 14) |
| reference only (not classified) | 18 (`sql/bigquery/*`) | - |

Entries that are DuckDB-only by design (mock-up build, catalog introspection, notebook EDA, the Power BI check list) contain DuckDB-specific parts and are not ported; section 6 states the class of each part and the port status.

What is built on the Snowflake side: 9 staging, 9 intermediate (5 general + 4 late-delivery), 9 core marts, 8 analytics marts, 2 ML marts and 9 Power BI views = **46 dbt models**, plus 3 macros and 39 singular tests, and 282 generic tests declared in YAML (counts from `dbt parse`, see `docs/data_dictionary/DATA_DICTIONARY.md`).

## 4. Inventory A: the 28 DuckDB SQL files

Paths are relative to the repository root. dbt models are under `snowflake/dbt/models/`. "Recon" means the offline-built, not-yet-run `src/reconciliation` check of the same name (see `PYTHONPATH=src python -m reconciliation.cli --list`). "Sim" means the logic simulation described in section 9.

### 4.1 Staging (9 files, class 3)

All nine are `create or replace view stg_x as select * from read_csv('${DATA_DIR}/<file>.csv', header = true, columns = {...})`. `read_csv` has no Snowflake form: the file is first loaded to `RAW.<TABLE>` by `snowflake/ingestion/load_raw.py` (all columns `VARCHAR`) and typed in a dbt view. That is a different mechanism, not a rename, hence class 3. Empty strings: DuckDB's reader turns an empty field into NULL for every type; the dbt views do `nullif(col, '')` on every column to get the same result whichever way the loader stored the field.

| Original file | Purpose | Source | Output (grain) | Class | Required modifications | dbt model (as built) | Validation |
|---|---|---|---|---|---|---|---|
| `sql/staging/stg_orders.sql` | Typed view over orders | `olist_orders_dataset.csv` | one row per `order_id`; 5 `TIMESTAMP` columns | 3 | `read_csv` types to `cast(nullif(..))`; `TIMESTAMP` to `to_timestamp_ntz(nullif(c,''), 'YYYY-MM-DD HH24:MI:SS')` | `staging/stg_olist__orders` (view, `STAGING`) | dbt `unique`/`not_null`/`accepted_values(order_status)`; `assert_fact_orders_rows_eq_staging`; Recon `row_counts`; Sim |
| `sql/staging/stg_customers.sql` | Typed view over customers | `olist_customers_dataset.csv` | one row per `customer_id` (per ORDER) | 3 | zip prefix stays `VARCHAR` (leading zeros) | `staging/stg_olist__customers` | dbt `unique`/`not_null`; `assert_dim_customer_rows_eq_distinct_unique_ids`; Recon `dim_customer` |
| `sql/staging/stg_geolocation.sql` | Typed view over ~1M geolocation points | `olist_geolocation_dataset.csv` | not unique; `DOUBLE` lat/lng | 3 | `DOUBLE` to `float` casts | `staging/stg_olist__geolocation` | `assert_dim_geography_rows_eq_in_bounds_zip_prefixes`; Recon `dim_geography` |
| `sql/staging/stg_order_items.sql` | Typed view over items | `olist_order_items_dataset.csv` | one row per (`order_id`, `order_item_id`); money `DECIMAL(12,2)` | 3 | `DECIMAL(12,2)` to `number(12,2)`; timestamp parse | `staging/stg_olist__order_items` | dbt composite-unique; `assert_sum_price_fact_eq_staging`, `assert_sum_freight_fact_eq_staging` (exact money); Recon `fact_order_items` |
| `sql/staging/stg_order_payments.sql` | Typed view over payments | `olist_order_payments_dataset.csv` | one row per (`order_id`, `payment_sequential`) | 3 | as above | `staging/stg_olist__order_payments` | `assert_sum_payment_value_fact_eq_staging`; Recon `fact_payments` |
| `sql/staging/stg_order_reviews.sql` | Typed view over reviews | `olist_order_reviews_dataset.csv` | one row per (`review_id`, `order_id`); review ids repeat across orders | 3 | multi-line quoted comments need the loader's `FIELD_OPTIONALLY_ENCLOSED_BY`; no trim, whitespace kept as DuckDB does | `staging/stg_olist__order_reviews` | `assert_fact_reviews_rows_eq_staging`, `assert_one_latest_review_per_reviewed_order`; Recon `fact_reviews` |
| `sql/staging/stg_products.sql` | Typed view over products; fixes `lenght` | `olist_products_dataset.csv` | one row per `product_id` | 3 | rename `product_name_lenght`/`product_description_lenght`; the RAW table keeps the source spelling | `staging/stg_olist__products` | `assert_dim_product_rows_eq_staging`; Recon `dim_product` |
| `sql/staging/stg_sellers.sql` | Typed view over sellers | `olist_sellers_dataset.csv` | one row per `seller_id` | 3 | none beyond the pattern | `staging/stg_olist__sellers` | `assert_dim_seller_rows_eq_staging`; Recon `dim_seller` |
| `sql/staging/stg_category_translation.sql` | Portuguese to English category names | `product_category_name_translation.csv` (UTF-8 BOM) | one row per Portuguese name | 3 | the BOM is skipped by the loader file format (`SKIP_BYTE_ORDER_MARK`) and the loader strips it before its header check | `staging/stg_olist__category_translation` (source table `product_category_translation`) | dbt `unique`/`not_null`; used by `dim_product` |

### 4.2 Dimensions (5 files)

| Original file | Purpose | Source | Output | Class | Required modifications | dbt model (as built) | Validation |
|---|---|---|---|---|---|---|---|
| `sql/dimensions/dim_customer.sql` | One row per real person (`customer_unique_id`), type-1 location from the latest order, `-1` unknown member | `stg_customers`, `stg_orders` | `customer_key` BIGINT surrogate (1..n by `customer_unique_id`), zip, city, state | 2 | `create table` with `PRIMARY KEY`/`UNIQUE` to a model plus dbt tests; `insert ... values (-1, ...)` to a `union all` unknown row; `order by purchase desc` gets `nulls last`; surrogate key via `row_number() over (order by customer_unique_id)` kept | `marts/core/dim_customer` (table) built on `intermediate/int_customers_latest` | dbt `unique`/`not_null` on both keys; `assert_dim_customer_rows_eq_distinct_unique_ids`; `assert_unknown_members_present`; Recon `dim_customer`; Sim: identical to `warehouse.duckdb` |
| `sql/dimensions/dim_date.sql` | Calendar, one row per day for whole years around every used date, `-1` not applicable | all date columns of `stg_orders`, `stg_order_items`, `stg_order_reviews` | `date_key` yyyymmdd, year, quarter, month, month_name, year_month, iso_week, day_of_week, day_name, is_weekend | 3 | `generate_series` + `unnest` to `GENERATOR(rowcount => 10000)` + `row_number() over (order by seq4())`; `strftime` to `to_char`; `monthname`/`dayname` (abbreviated on Snowflake) to explicit `DECODE` of full English names; `weekofyear` to `weekiso`; `isodow` to `dayofweekiso`; interval arithmetic to `dateadd` | `marts/core/dim_date` | `assert_dim_date_has_no_gaps`, `assert_dim_date_contains_all_days_of_2016_11`, `assert_dim_date_covers_all_used_dates`; Recon `dim_date`; Sim: all 1,828 rows identical |
| `sql/dimensions/dim_geography.sql` | One row per zip prefix; median lat/lng, most frequent city/state | `stg_geolocation` | `geography_key`, `zip_prefix`, city, state, latitude, longitude, `n_source_points` | 2 | bounding-box filter and `median` kept; the ranked "mode" is expressed as pre-counted groups + `qualify row_number() ... = 1` (ties: count desc, then value ascending); NULL city/state counted as their own group as in DuckDB | `marts/core/dim_geography` on `intermediate/int_geography_points` and `int_geography_rollup` | `assert_dim_geography_rows_eq_in_bounds_zip_prefixes`; Recon `dim_geography`; UNVERIFIED: `MEDIAN` parity |
| `sql/dimensions/dim_product.sql` | One row per product; English category falls back to Portuguese then `'unknown'`; volume | `stg_products`, `stg_category_translation` | `product_key`, names, dimensions, `product_volume_cm3` BIGINT | 2 | constraints to tests; unknown member row; `length::bigint * height * width` kept | `marts/core/dim_product` | `assert_dim_product_rows_eq_staging`; Recon `dim_product` |
| `sql/dimensions/dim_seller.sql` | One row per seller, `-1` unknown | `stg_sellers` | `seller_key`, zip, city, state | 2 | as `dim_customer` | `marts/core/dim_seller` | `assert_dim_seller_rows_eq_staging`; Recon `dim_seller` |

### 4.3 Facts (4 files, class 2)

All four lose their `REFERENCES`/`PRIMARY KEY`/`NOT NULL` DDL (Snowflake would store but not enforce the keys); the dbt YAML declares `unique`, `not_null` and `relationships` tests (including the `-1` members) instead. Every `strftime(ts, '%Y%m%d')::integer` with `coalesce(..., -1)` becomes the `date_key()` macro.

| Original file | Purpose | Source | Output (grain) | Class | Required modifications | dbt model (as built) | Validation |
|---|---|---|---|---|---|---|---|
| `sql/facts/fact_order_items.sql` | Core sales fact | `stg_order_items`, `stg_orders`, 5 dims, `stg_customers`, `stg_sellers` | one row per (`order_id`, `order_item_id`), money `DECIMAL(12,2)` | 2 | `date_key()` macro; `price + freight_value` cast to `number(12,2)`; all surrogate keys resolved by `left join` with `coalesce(..., -1)` kept | `marts/core/fact_order_items` | composite-unique, 8 `relationships` and `not_null` tests; `assert_fact_order_items_rows_eq_staging`, `assert_item_revenue_unchanged_after_dimension_joins`, `assert_fact_order_items_unknown_keys_only_when_unmatched`; Recon `fact_order_items` (natural keys, FK keys compared separately) |
| `sql/facts/fact_orders.sql` | One row per order incl. 775 orders without items; lifecycle, delivery time, lateness | `stg_orders`, items and payments pre-aggregated, dims | `delivery_days` and `delivery_delay_days` DOUBLE, `is_late`, `has_timestamp_anomaly` | 2 | `date_diff('second', a, b) / 86400.0` to `datediff(second, a, b)::float / 86400.0`; the two pre-aggregation CTEs moved to their own models; sums cast back to `number(12,2)` (Snowflake widens `SUM` to `NUMBER(38,2)`) | `marts/core/fact_orders` on `intermediate/int_order_items_agg`, `int_order_payments_agg` | `assert_fact_orders_rows_eq_staging`, `assert_orders_without_items_kept`, `assert_late_deliveries_eq_staging`, `assert_timestamp_anomalies_eq_staging`, `assert_sum_items_price_orders_eq_order_items`, `assert_sum_payment_total_orders_eq_payments`; Recon `fact_orders`, `headline_numbers` |
| `sql/facts/fact_payments.sql` | One row per payment record | `stg_order_payments`, `stg_orders`, `dim_customer` | one row per (`order_id`, `payment_sequential`) | 2 | `date_key()` macro; constraints to tests | `marts/core/fact_payments` | `assert_fact_payments_rows_eq_staging`, `assert_sum_payment_value_fact_eq_staging`; Recon `fact_payments` |
| `sql/facts/fact_reviews.sql` | One row per (`review_id`, `order_id`) with `is_latest_review_for_order` | `stg_order_reviews`, `stg_orders`, `dim_customer` | comments kept as nullable columns | 2 | the `row_number() over (...) = 1` boolean column keeps its order but gets `desc nulls last`; evaluating the window comparison directly as a select column is a live check | `marts/core/fact_reviews` | `assert_fact_reviews_rows_eq_staging`, `assert_one_latest_review_per_reviewed_order`; Recon `fact_reviews` |

### 4.4 Analytics (8 files, class 2)

Each query becomes a `mart_*` table with the same output columns and order as the DuckDB query and the tracked `reports/analytics/NN_*.csv`. Two changes apply to all of them (see section 8): operands are cast to `::float` before division or `AVG`, and a stored table has no guaranteed read order, so the YAML descriptions tell the consumer to sort (some marts keep the final `order by` in their SQL, but that does not fix the order of later reads).

| Original file | Purpose | Source | Output | Class | Required modifications | dbt model (as built) | Validation |
|---|---|---|---|---|---|---|---|
| `sql/analytics/01_monthly_kpis.sql` | Net revenue, orders, AOV, month-on-month growth, thin-month flag | `fact_order_items`, `dim_date` | one row per `year_month` | 2 | `revenue::float / orders`; `lag()` window kept with `nulls last` | `marts/analytics/mart_monthly_kpis` | `assert_mart_monthly_kpis_reconcile_to_facts`, `assert_mart_monthly_kpis_growth_blank_next_to_thin_months`; Recon `mart_monthly_kpis` vs DuckDB and vs `reports/analytics/01_*.csv` |
| `sql/analytics/02_category_performance.sql` | Category revenue, share, cumulative share, lateness, review score | `fact_order_items`, `dim_product`, `fact_orders`, `fact_reviews` | one row per English category | 2 | `avg(price)` and money averages become `sum(x)::float / count(x)` (`security_and_services` average is 141.645, a rounding boundary); `avg(is_late::integer)` becomes a `CASE`; window totals cast `::float` | `marts/analytics/mart_category_performance` | `assert_mart_category_performance_reconciles_to_facts`; Recon `mart_category_performance` |
| `sql/analytics/03_state_performance.sql` | State revenue, share, lateness, median delivery days | `fact_orders`, `dim_geography` | one row per customer state | 2 | casts as above; `median` of a float; `count(o.is_late)` kept (counts non-NULL) | `marts/analytics/mart_state_performance` | `assert_mart_state_performance_reconciles_to_facts`; Recon `mart_state_performance` |
| `sql/analytics/04_seller_concentration.sql` | Revenue concentration across sellers | `fact_order_items` | 6 rows keyed by `metric` | 2 | `FILTER (WHERE rn <= k)` to `sum(case when rn <= k then revenue end)`; `ceil(0.1 * n_sellers)` keeps `0.1` as a decimal literal; every `union all` branch cast `::float` (DuckDB `double`); row order is the union order and is not guaranteed | `marts/analytics/mart_seller_concentration` | `assert_mart_seller_concentration_is_ordered`; Recon `mart_seller_concentration` (looked up by `metric`) |
| `sql/analytics/05_delivery_vs_reviews.sql` | Late delivery buckets vs latest review score | `fact_orders`, `fact_reviews` | 5 rows by `delay_group` | 2 | `100.0 * count(*) / sum(count(*)) over ()` and boolean averages cast `::float` / `CASE` | `marts/analytics/mart_delivery_vs_reviews` | `assert_mart_delivery_vs_reviews_reconciles_to_facts`; Recon `mart_delivery_vs_reviews` |
| `sql/analytics/06_payments.sql` | Payment mix | `fact_payments` | one row per payment type | 2 | money average as `sum / count`; share cast | `marts/analytics/mart_payments` | `assert_mart_payments_reconciles_to_facts`; Recon `mart_payments` |
| `sql/analytics/07_repeat_customers.sql` | Orders per real customer (1, 2, 3, 4+) | `fact_orders` | 4 rows by `orders_placed` | 2 | `n_orders::varchar` kept; shares cast `::float` | `marts/analytics/mart_repeat_customers` | `assert_mart_repeat_customers_reconciles_to_facts`; Recon `mart_repeat_customers` |
| `sql/analytics/08_delivery_trend.sql` | Delivery and promise by purchase month | `fact_orders` | one row per month | 2 | `strftime(.., '%Y-%m')` to `to_char(.., 'YYYY-MM')`; `date_diff('second',..)` to `datediff`; boolean averages via `CASE`; `median` | `marts/analytics/mart_delivery_trend` | `assert_mart_delivery_trend_reconciles_to_facts`; Recon `mart_delivery_trend` |

### 4.5 ML features and validation (2 files)

| Original file | Purpose | Source | Output | Class | Required modifications | dbt model (as built) | Validation |
|---|---|---|---|---|---|---|---|
| `sql/ml/late_delivery_features.sql` | One feature row per labelled delivered order, point-in-time seller, route, category and system history | `fact_orders`, `fact_order_items`, `fact_payments`, `dim_product`, `dim_seller`, `dim_geography` | 32 columns, 96,282 rows in `warehouse.duckdb` | 3 (highest risk of the migration) | `ASOF LEFT JOIN ... on key and ts > ts` to Snowflake `ASOF JOIN ... MATCH_CONDITION (purchase_ts > ts)` (strict `>`; the 28-day side uses a precomputed `purchase_ts_minus_28d` column because `MATCH_CONDITION` takes columns); a dbt var `late_delivery_history_method` (`asof` default, `range_join` fallback with `qualify row_number() = 1`) lets the fallback be selected without editing a file; named `window w as (...)` clauses inlined; `FILTER (WHERE n_prior >= 5)` to `CASE`; `arg_max(category, price)` and `arg_max(payment_type, payment_value)` replaced by a deterministic alphabetical pick (INTENTIONAL difference, section 8); `date_diff` to `datediff`; `pow` to `power`; `isodow` to `dayofweekiso`; haversine on FLOAT; split into four intermediate models and the mart | `intermediate/late_delivery/int_late_delivery_population`, `int_late_delivery_item_agg`, `int_late_delivery_seller_history`, `int_late_delivery_history`; mart `marts/ml/mart_late_delivery_features` | `assert_late_delivery_history_is_point_in_time`, `assert_late_delivery_seller_history_excludes_self`, `assert_late_delivery_one_row_per_population_order_with_items`; Recon `mart_late_delivery_features` and `..._aggregates` (status `PASS_WITH_TIE_BREAKS` allowed); Sim (ASOF rewritten by regex for DuckDB): 32 columns identical; values identical once the tie-break is aligned; UNVERIFIED: ASOF on Snowflake |
| `sql/validation/checks.sql` | 22 reconciliation checks of the star schema vs staging and EDA findings; the build fails if any `passed` is false | all staging and mart tables | one row per check | 4 | The single failing-build query is replaced by dbt tests: the 22 checks are 22 singular tests (mapping below) plus 3 guard tests; PK/FK checks "enforced by the table constraints" become generic tests; the hard-coded EDA constants (7,827 late, 166..189 anomalies) are not thresholds in dbt, they are compared by reconciliation | 25 singular tests at `snowflake/dbt/tests/assert_*.sql` + YAML generic tests | `dbt test` (not yet run on Snowflake); Sim: all 169 tests of the base project pass on the simulated models and 14 fail when 5 defects are injected |

Mapping of the 22 checks to singular tests (check numbers follow the order in `checks.sql`):

| # | Check | Singular test |
|---|---|---|
| 1-4 | fact rows = staging rows (orders, items, payments, reviews) | `assert_fact_orders_rows_eq_staging`, `assert_fact_order_items_rows_eq_staging`, `assert_fact_payments_rows_eq_staging`, `assert_fact_reviews_rows_eq_staging` |
| 5-8 | dim rows (customer, product, seller, geography) | `assert_dim_customer_rows_eq_distinct_unique_ids`, `assert_dim_product_rows_eq_staging`, `assert_dim_seller_rows_eq_staging`, `assert_dim_geography_rows_eq_in_bounds_zip_prefixes` |
| 9-14 | exact money (price, freight, item total, payment value, items price orders vs items, payment total) | `assert_sum_price_fact_eq_staging`, `assert_sum_freight_fact_eq_staging`, `assert_sum_item_total_eq_price_plus_freight`, `assert_sum_payment_value_fact_eq_staging`, `assert_sum_items_price_orders_eq_order_items`, `assert_sum_payment_total_orders_eq_payments` |
| 15 | fan-out: revenue unchanged after joining all dimensions | `assert_item_revenue_unchanged_after_dimension_joins` |
| 16 | orders without items kept | `assert_orders_without_items_kept` |
| 17 | late deliveries | `assert_late_deliveries_eq_staging` (derived from staging, not the constant 7,827) |
| 18 | timestamp anomalies | `assert_timestamp_anomalies_eq_staging` |
| 19 | one latest review per reviewed order | `assert_one_latest_review_per_reviewed_order` |
| 20 | customer zip not in `dim_geography` maps to `-1` | `assert_unmatched_customer_zip_maps_to_unknown_geography` (anti-join instead of `NOT IN`; `NOT IN` ignores NULL zips) |
| 21-22 | calendar has no gaps; 2016-11 has 30 days | `assert_dim_date_has_no_gaps`, `assert_dim_date_contains_all_days_of_2016_11` |
| guards | not in `checks.sql` | `assert_dim_date_covers_all_used_dates`, `assert_unknown_members_present`, `assert_fact_order_items_unknown_keys_only_when_unmatched` |

## 5. Inventory B: `sql/bigquery` (reference only, 18 files)

These are an earlier GoogleSQL translation record (`sql/bigquery/README.md`): nothing in them has ever run on Google Cloud. They are not part of the Snowflake migration and are **not classified**. They were read only as a typing template (STRING raw, casts in staging). Snowflake equivalents: `snowflake/ingestion/ddl_raw.sql` + `load_raw.py` for `raw/`, and `snowflake/dbt/models/staging/stg_olist__*` for `staging/`.

| File | Purpose | Snowflake counterpart |
|---|---|---|
| `sql/bigquery/raw/olist_customers_dataset.sql` | `create or replace external table` over the `olist_customers_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_geolocation_dataset.sql` | `create or replace external table` over the `olist_geolocation_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_order_items_dataset.sql` | `create or replace external table` over the `olist_order_items_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_order_payments_dataset.sql` | `create or replace external table` over the `olist_order_payments_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_order_reviews_dataset.sql` | `create or replace external table` over the `olist_order_reviews_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_orders_dataset.sql` | `create or replace external table` over the `olist_orders_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_products_dataset.sql` | `create or replace external table` over the `olist_products_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/olist_sellers_dataset.sql` | `create or replace external table` over the `olist_sellers_dataset` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/raw/product_category_name_translation.sql` | `create or replace external table` over the `product_category_name_translation` CSV in Cloud Storage; every column `STRING`, `allow_quoted_newlines` | `RAW.<TABLE>` in `snowflake/ingestion/ddl_raw.sql` (all `VARCHAR`, internal stage + `COPY INTO`, not an external table) |
| `sql/bigquery/staging/stg_category_translation.sql` | typed view `stg_category_translation` with `cast(.. as int64/datetime/numeric)` | `stg_olist__category_translation` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_customers.sql` | typed view `stg_customers` with `cast(.. as int64/datetime/numeric)` | `stg_olist__customers` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_geolocation.sql` | typed view `stg_geolocation` with `cast(.. as int64/datetime/numeric)` | `stg_olist__geolocation` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_order_items.sql` | typed view `stg_order_items` with `cast(.. as int64/datetime/numeric)` | `stg_olist__order_items` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_order_payments.sql` | typed view `stg_order_payments` with `cast(.. as int64/datetime/numeric)` | `stg_olist__order_payments` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_order_reviews.sql` | typed view `stg_order_reviews` with `cast(.. as int64/datetime/numeric)` | `stg_olist__order_reviews` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_orders.sql` | typed view `stg_orders` with `cast(.. as int64/datetime/numeric)` | `stg_olist__orders` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_products.sql` | typed view `stg_products` with `cast(.. as int64/datetime/numeric)` | `stg_olist__products` dbt view (same idea, Snowflake cast syntax) |
| `sql/bigquery/staging/stg_sellers.sql` | typed view `stg_sellers` with `cast(.. as int64/datetime/numeric)` | `stg_olist__sellers` dbt view (same idea, Snowflake cast syntax) |

## 6. Inventory C: SQL embedded in Python and notebooks

Embedded SQL is not in any `.sql` file, so it is not part of the section 2 count. Each entry states whether it was ported. "Tier 1" Python (`forecast_baseline`, `late_delivery_baseline`) can read from either backend through `src/data_access`; "Tier 2" modules stay DuckDB-only.

| # | Original query | Purpose | Source tables | Output | Class | Required modifications | Snowflake counterpart (as built) | Validation |
|---|---|---|---|---|---|---|---|---|
| 1 | `src/ml/forecast_baseline.py` `weekly_series` | Weekly orders and item revenue | `fact_orders`, `fact_order_items` | `week` date, `orders`, `revenue` double, ordered by week | 2 | `date_trunc('week', ts)::date` to the `iso_week_start` macro (explicit `dayofweekiso` arithmetic, independent of the `WEEK_START` session parameter); `sum(price)::float` | `marts/ml/mart_weekly_orders_revenue`, read by `data_access.datasets.weekly_series` with an explicit `ORDER BY week` | `assert_mart_weekly_orders_revenue_reconciles_to_facts`; Recon `mart_weekly_orders_revenue`; Sim equals the DuckDB SQL (101 weeks) |
| 2 | `src/ml/late_delivery_baseline.py` `load` | Runs `sql/ml/late_delivery_features.sql` | see section 4.5 | 32-column feature frame | 3 (inherits the file) | none in Python; the Snowflake path calls `datasets.late_delivery_features`, which selects the columns explicitly with `ORDER BY purchase_ts, order_id` because a table has no row order | `marts/ml/mart_late_delivery_features` | as section 4.5 |
| 3 | `late_delivery_baseline.py` `unlabelled_share` | Share of each month's orders without a usable label | `fact_orders` | dict month to share | 2 | `strftime` to `to_char`; `count(*) filter (where ..)` to `sum(case ..)` | no dedicated mart: `datasets.unlabelled_share` queries `MARTS.fact_orders` directly | tested with a fake cursor only (offline); UNVERIFIED on Snowflake |
| 4 | `src/ml/drift_analysis.py` `KEYS_SQL` (also imported by `export_scores.py`) | order to category (most expensive item), route, first seller | `fact_orders`, `fact_order_items`, `dim_product`, `dim_seller`, `dim_geography` | one row per labelled order | 2 | `arg_max(category, price)` would need the same deterministic tie-break as `int_late_delivery_item_agg` | not ported (Tier 2, DuckDB-only) | - |
| 5 | `src/powerbi/export_data.py` `FACT_SQL["fact_orders"]` | Power BI fact export with derived columns | `fact_orders` | 25 columns incl. `promised_days`, `is_net_order`, `is_labelled_delivery`, `delay_bucket`, `delay_bucket_order` | 2 | `date_diff` to `datediff(..)::float / 86400.0`; `case` logic unchanged | `pbi/pbi_fact_orders` (view `PBI.FACT_ORDERS`, explicit column list, no `select *`) | `assert_pbi_views_match_core_marts`; Sim: same names, order, types, values as the export |
| 6 | `export_data.py` `FACT_SQL["fact_order_items"]`, `["fact_payments"]`, `["fact_reviews"]` | Other three fact exports (`select *` plus `is_net_order`; reviews without comment text) | the facts | parquet files | 2 | explicit column lists instead of `select *` | `pbi/pbi_fact_order_items`, `pbi_fact_payments`, `pbi_fact_reviews` | as above |
| 7 | `export_data.py` `export()` dimension loop: `select * from dim_x [where full_date is not null] order by 1` | Five dimension CSV exports; `dim_date` without its `-1` row | the dimensions | CSV files | 2 | explicit columns; the `-1` date row removed in the view (1,827 rows); `order by` dropped | `pbi/pbi_dim_date`, `pbi_dim_customer`, `pbi_dim_product`, `pbi_dim_seller`, `pbi_dim_geography` | as above |
| 8 | `export_data.py` `copy (<select>) to '<file>.parquet' (format parquet)` and CSV `copy` | File export for Power BI | - | parquet / CSV | 4 | `COPY ... TO` a local file has no counterpart; Power BI reads the `PBI` views directly | `powerbi/snowflake/templates/*.m` (Snowflake connector navigation) | `tests/test_powerbi_snowflake.py` (offline) |
| 9 | `src/analytics/run_analytics.py` | Executes each `sql/analytics/*.sql`, writes CSV and figures | analytics SQL | CSV + PNG | 2 (SQL) | no SQL of its own; unchanged and DuckDB-only | the 8 `mart_*` tables replace the SQL; the script itself is not ported | Recon compares the marts to `reports/analytics/*.csv` |
| 10 | `src/powerbi/mockup_data.py` (14 queries) | Pre-aggregates data for the HTML dashboard mock-up | facts, dims, and local `read_parquet(late_delivery_scores.parquet)`, `read_csv(forecast_backtest.csv)` | JSON for a static HTML page | 4 for the file readers; 2 for the aggregates (`count(*) filter`, `date_diff`, `least(floor(x)::int, n)`) | n/a | not ported; DuckDB-only build artefact | - |
| 11 | `src/powerbi/model_spec.py` `CHECKS` (38 queries; 11 use `read_parquet` or `read_csv`, 7 use `filter (where ..)`) | Expected values for the Power BI verification checklist | facts plus exported files | numbers | 4 for the file readers; 2 otherwise | n/a | not ported; the checklist stays DuckDB-based | - |
| 12 | `scripts/visualize_schema.py`: `duckdb_tables()`, `duckdb_constraints()` | Draws the star schema with PK/FK from the catalog | DuckDB catalog | PNG | 4 | catalog functions and enforced constraints do not exist on Snowflake (`INFORMATION_SCHEMA` lists declared but unenforced keys) | not ported | - |
| 13 | `notebooks/01_dataset_discovery.ipynb` (several cells with SQL) (the marimo notebooks listed here originally had no SQL of their own and were removed, DD-24) | EDA over the raw CSVs: `read_csv_auto`, `describe`, `summarize`, `count(distinct (a, b))`, `mode()`, `not in (subquery)` | raw CSVs | tables and charts | 4 for `read_csv_auto`/`describe`/`summarize`; 3 for `count(distinct (a, b))` (must be rewritten as `count(distinct a, b)` or a concatenation; how Snowflake treats the parenthesised row value is UNVERIFIED); 2 for the rest | n/a | not ported; the notebook documents the source data and is the origin of the EDA constants | - |
| 14 | `src/transformation/build_warehouse.py` (`con.execute` of each file with `${DATA_DIR}` substituted) | Runs staging, dimensions, facts, then `checks.sql` | all SQL | `warehouse.duckdb` | 4 | replaced by the dbt DAG (`dbt build`) and the loader | `snowflake/dbt` as a whole | `dbt build` (not yet run) |

## 7. Construct-by-construct translation

Only constructs that occur in the files above are listed. "Where" names the first place it appears.

| DuckDB construct | Where | Snowflake translation as built | Note |
|---|---|---|---|
| `read_csv(path, header, columns={..})` | `sql/staging/*` | `source('olist_raw', ..)` over all-`VARCHAR` RAW tables + `cast(nullif(c, ''), type)` | loading done by `load_raw.py` (PUT + COPY INTO) |
| `${DATA_DIR}` token substitution | `build_warehouse.py` | none; `RETAIL_DATA_DIR` for the loader | |
| `create or replace view` / `create table` + `insert` | all layers | dbt `view` / `table` materialisation | |
| `PRIMARY KEY`, `UNIQUE`, `REFERENCES`, `NOT NULL` DDL | dims, facts | dbt `unique`, `not_null`, `relationships`, `unique_combination_of_columns` tests | Snowflake stores but does not enforce keys |
| `insert into dim values (-1, ..)` | dims | `union all` of a literal unknown-member row | `-1` members are asserted by `assert_unknown_members_present` |
| `join .. using (col)` | dims, facts, ML | kept or rewritten as `on` | |
| `TIMESTAMP` | staging | `TIMESTAMP_NTZ` via `to_timestamp_ntz(nullif(c,''), 'YYYY-MM-DD HH24:MI:SS')` | all CSV values match this pattern (checked offline) |
| `DECIMAL(12,2)` | staging, facts | `number(12,2)`; sums cast back to `number(12,2)` | `SUM` widens to `NUMBER(38,2)` |
| `INTEGER`, `BIGINT` | staging, dims | `integer`, `bigint` (both become `NUMBER(38,0)`) | width differs from DuckDB; Python normalises |
| `DOUBLE` | staging, facts | `float` | `DOUBLE` is an alias, the models write `float` |
| `strftime(ts, '%Y%m%d')::integer` + `coalesce(.., -1)` | facts | `date_key()` macro: `coalesce(to_char(ts, 'YYYYMMDD')::integer, -1)` | |
| `strftime(ts, '%Y-%m')` | `dim_date`, analytics 08 | `to_char(ts, 'YYYY-MM')` | |
| `date_diff('second', a, b) / 86400.0` | `fact_orders`, analytics 08, ML | `datediff(second, a, b)::float / 86400.0` | cast before the division |
| `date_trunc('year', x)`, `+ interval 1 year - interval 1 day` | `dim_date` | `date_trunc('year', x)`, `dateadd(day, -1, dateadd(year, 1, ..))` | |
| `generate_series(a, b, interval 1 day)` + `unnest` | `dim_date` | `table(generator(rowcount => 10000))` + `row_number() over (order by seq4()) - 1` + `dateadd` | `seq4()` can have gaps, hence the re-numbering; a test fails if the spine is too short |
| `monthname(d)`, `dayname(d)` | `dim_date` | `decode(month(d), 1, 'January', ..)`, `decode(dayofweekiso(d), 1, 'Monday', ..)` | Snowflake returns abbreviations; explicit names are locale independent |
| `weekofyear(d)` | `dim_date` | `weekiso(d)` | `2016-01-01` must be ISO week 53 (live check) |
| `isodow(d)` | `dim_date`, ML | `dayofweekiso(d)` | 1 = Monday |
| `date_trunc('week', ts)::date` | `weekly_series` | `iso_week_start` macro: `dateadd(day, -(dayofweekiso(d) - 1), d::date)` | never depends on `WEEK_START` |
| `year()`, `quarter()`, `month()`, `day()`, `hour()` | `dim_date`, ML | same names | |
| `median(x)` | `dim_geography`, analytics 03, 04, 08 | `median(x)` on float | interpolation parity is a live check |
| `arg_max(a, b)` | ML (`category`, `main_payment_type`), `KEYS_SQL` | deterministic pick: alphabetically first value among rows at the maximum | **not** `max_by`; see section 8 |
| `count(*) filter (where ..)`, `sum(..) filter (where ..)`, `avg(..) filter (where ..)` | analytics 04, ML, `unlabelled_share`, `mockup_data` | `sum(case when .. then .. end)` | |
| `avg(bool::integer)` | analytics 02, 03, 05, 08 | `avg((case when b then 1 when not b then 0 end)::float)` | keeps NULL as NULL; `iff(b, 1, 0)` would turn NULL into 0 |
| `sum(x) / count(x)` money averages | analytics 02, 06 | `sum(x)::float / count(x)` | see rounding note in section 8 |
| `x / y` of numbers | analytics, ML | `x::float / y` | |
| `any_value(n)::double` | analytics 04 | `any_value(n)::float` | |
| `ceil(0.1 * n_sellers)` | analytics 04 | unchanged (decimal literal kept) | |
| `... over w` with `window w as (..)` | ML | window written inline each time | |
| `ASOF LEFT JOIN t on k = k and ts > ts` | ML | `ASOF JOIN t MATCH_CONDITION (ts > t.ts) ON k = k`, or the range-join fallback | UNVERIFIED; the highest risk |
| `ts - interval 28 day` in the join condition | ML | precomputed `dateadd(day, -28, purchase_ts)` column | `MATCH_CONDITION` takes columns |
| `pow(x, 2)` | ML haversine | `power(x, 2)` | |
| `desc` (NULL placement) | `dim_customer`, `fact_reviews`, analytics | `desc nulls last` everywhere a `desc` feeds `row_number()` or `lag()` | see section 8 |
| `row_number() over (order by key)` surrogate keys | dims | unchanged, with a binary-collation assumption | see section 8 |
| `with checks(a, b, c) as (..)` + `::varchar` | `checks.sql` | not carried over; dbt singular tests | |
| `copy (select ..) to 'f.parquet'`, `read_parquet`, `read_csv` | `export_data`, `mockup_data`, `model_spec` | no counterpart; PBI views + Snowflake connector | |
| `describe`, `summarize`, `duckdb_tables()`, `duckdb_constraints()` | notebook 01, `visualize_schema.py` | no counterpart | |
| `count(distinct (a, b))`, `mode()` | notebook 01 only | not translated (the notebook is not ported) | |

Constructs the files use unchanged and expected to behave identically: `coalesce`, `nullif`, `round`, `substr`, `||`, `between`, `union all`, `select distinct`, `count(distinct x)`, `lag`, `sum() over ()`, `row_number`, `ceil`, `least`, `floor`, `radians`, `asin`, `sqrt`, `sin`, `cos`. That is an expectation, not a verified fact, until the live run.

## 8. Numeric, NULL-order, surrogate-key and tie-break caveats

**Division and averages.** DuckDB divides integers and decimals as floating point; Snowflake divides `NUMBER` by `NUMBER` with decimal scale rules, so `revenue / orders` or `100.0 * count(*) / sum(count(*)) over ()` can round differently. The models cast one operand `::float` first. `AVG` of an integer-cast boolean returns a scaled `NUMBER`; the models use a `CASE ... END::float` instead (so NULL labels stay NULL).

**Money averages and rounding.** DuckDB averages `DECIMAL` as double. The offline simulation found that `avg(price::float)` gave 141.64 where the DuckDB reference gives 141.65 for `security_and_services` (exact average 141.645, a `.xx5` boundary), so money averages are written `sum(x)::float / count(x)` with the sum taken on the exact decimal. How Snowflake's `ROUND(FLOAT)` behaves at `.xx5` boundaries is UNVERIFIED; `security_and_services.avg_item_price` is the row to inspect first in a live reconciliation.

**Sum widening and float sums.** `SUM(NUMBER(12,2))` is `NUMBER(38,2)`; the models cast back to `NUMBER(12,2)`. Float sums (`route_prior_days`, `recent_days_28d`) may accumulate in a different order than DuckDB, so agreement is expected to about 1e-9 relative, not bit equality. Reconciliation tolerances: counts, keys, money, booleans and timestamps exact; doubles relative 1e-9; haversine distance absolute 1e-6 km.

**NULL ordering.** In the DuckDB version used here, NULLs sort last under `DESC` (checked with a query by the dbt-base workstream). Snowflake places NULLs first under `DESC` by default. Every `desc` that feeds `row_number()` therefore carries `nulls last` (`int_customers_latest`, `fact_reviews.is_latest_review_for_order`, `mart_seller_concentration`), and the ordered windows in `mart_monthly_kpis` (`lag()`) state `nulls last` as well. Whether the result matches DuckDB on Snowflake is a live check.

**Surrogate keys.** `customer_key`, `product_key`, `seller_key` and `geography_key` are `row_number() over (order by <natural key>)`. They match DuckDB only if Snowflake orders those `VARCHAR`s by binary (code-point) comparison, which is the default; an account or database `COLLATION` default would shift the numbers. The facts resolve their keys by joining to the dimensions, so internal consistency does not depend on the numbering, but the numbers are not stable if the source data changes. Reconciliation therefore compares facts on natural keys and compares the `*_key` columns in a separate section that never decides the status.

**Deterministic tie-breaks kept identical to DuckDB:** latest customer order (purchase desc nulls last, then `customer_id`), latest review (creation desc, answer desc, `review_id`), top city/state (count desc, then value ascending, binary compare), category cumulative share (`revenue desc, category`), seller rank (`revenue desc, seller_key`).

**`arg_max` ties: resolved by aligning both engines (2026-11-12, DD-21).** `arg_max(category, price)` in `late_delivery_features.sql` had no tie-break. In `warehouse.duckdb` 57 of the 96,282 labelled orders have their most expensive items tied on price across different categories; there are no payment-type ties. Snowflake's `MAX_BY` is equally arbitrary, so it was not used: the Snowflake models take the alphabetically first value among the tied rows (`int_late_delivery_item_agg`, and the payment pick in `mart_late_delivery_features`), and the DuckDB query now uses the same rule (`first(category order by price desc, category)`, likewise for `payment_type`, also in `drift_analysis.KEYS_SQL`). `category` is not an output column but keys `category_prior_n` / `category_prior_late`, which is why a different pick in 57 orders moved those columns on about 26,000 rows. The live reconciliation on 2026-11-12 found **0 differences** in the feature table; the reconciliation's tie-break classifier is kept as a safety net and now counts 57 ambiguous orders with 0 diffs.

**The DuckDB reference was not reproducible; fixed (2026-11-12, DD-21).** Measured on the real warehouse: six runs of the original query at 8 threads differed on `category_prior_n` (up to 29,679 rows, by up to 7,350) and `category_prior_late` (up to 11,471 rows); runs at 1 thread were identical. Cause 1: `arg_max` picks among tied rows in whatever order the parallel scan delivers them (the 57 tied orders above). Cause 2, minor: `avg(prior_late_rate)` over a multi-seller order added doubles in thread order, so `seller_prior_late_rate` differed by about 3e-17 on 2 to 4 orders. Fix: the alphabetical tie-break, and `avg(prior_late_rate order by seller_key)` so the float sum has a fixed order. After the fix, ten 8-thread runs and runs at 1, 2 and 16 threads are bit-identical, a full re-run of the late-delivery backtest reproduces its metrics exactly, and `tests/test_feature_determinism.py` locks the rule in. Only the v2/v3 feature-set experiments use `category_prior_*`, so the reference model (logistic regression v1) and its metrics did not change.

**Intentionally different: constraints.** PK, FK, `UNIQUE` and `NOT NULL` are enforced by the DuckDB build; on Snowflake they are dbt tests that run only when `dbt test` or `dbt build` runs.

**Intentionally different: other points.**
- A new RAW landing layer (all `VARCHAR`, plus `_loaded_at`, `_source_file`, `_source_row_number`, `_batch_id`, and `RAW.INGESTION_LOG`) replaces DuckDB reading the CSVs in place.
- Tables have no row order. DuckDB analytics queries and the weekly series are ordered result sets; the Snowflake marts are stored unordered and every reader sorts (`src/data_access` does; the Power BI views are unordered by design).
- `fact_orders` aggregation of items and payments lives in two intermediate models instead of two CTEs; the late-delivery query is split into four intermediate models and a mart.
- Dbt singular tests derive expectations from staging; the EDA constants (7,827 late deliveries, 166..189 anomalies, 96,282 labelled, 7,823 labelled late, R$13,494,400.74 net revenue, 98,199 net orders, 96.96 percent one-time customers) are compared only by the reconciliation tool.
- Power BI views are dbt models named `pbi_<table>` with `alias` set so the Snowflake objects are `PBI.DIM_DATE` ... `PBI.FACT_REVIEWS`; `pbi_dim_date` drops the `-1` row; `pbi_fact_reviews` omits comment text. The Python-fed tables (`ML.LATE_DELIVERY_SCORES`, `ML.FORECAST_BACKTEST`, `ML.FLAG_SHARE`) carry an extra `run_id` column and are written only with the opt-in `FORECAST_WRITEBACK=1`.
- Training and scoring stay in Python on both backends; nothing is moved into Snowflake ML.
- Not ported (DuckDB-only): `drift_analysis`, `export_scores`, `export_data`, `run_analytics`, `mockup_data`, `visualize_schema`, the notebooks and the Power BI check list.

## 9. UNVERIFIED until a live Snowflake run

Everything below is unproven. No step of this migration has been executed on Snowflake; the preflight, setup, ingestion, `dbt build`, reconciliation and Python runs are all **NOT YET RUN**.

What was checked offline, and how (reported by the workstream that did it; the commands are in the files named):
- `dbt parse` and `dbt compile --no-populate-cache` pass for `--target ci` with no Snowflake variables and a dead proxy (`snowflake/dbt/README_LIVE_CHECKS.md`); `dbt parse --target prod` with dummy variables was re-run for this page's data dictionary (46 models, 282 generic and 39 singular tests, 9 sources).
- The compiled SQL parses with `sqlglot` in the Snowflake dialect (a syntax lint only).
- A logic simulation: compiled SQL transpiled to DuckDB and run on the real CSVs. The five dimensions, four facts and every analytics, weekly and Power BI model equal the reference `warehouse.duckdb` (floats within 1e-9). This tests join logic, tie-breaks, key numbering and rounding in DuckDB's arithmetic. It does **not** test Snowflake function behaviour.
- Python-side logic with fake connectors (`tests/test_data_access.py`, `tests/test_snowflake_ingestion.py`, `tests/test_reconciliation.py`, `tests/test_powerbi_snowflake.py`), and the DuckDB side of reconciliation against the real warehouse.

Needs a live run (the numbered items continue the list in `snowflake/dbt/README_LIVE_CHECKS.md`, which holds the detail):
1. Key-pair login, including an empty passphrase with an unencrypted key; role grants for `RETAIL_LOADER`, `RETAIL_TRANSFORMER`, `RETAIL_REPORTER`; the `CREATE SCHEMA` grant the dev target needs. The setup SQL has never been executed.
2. Ingestion: `PUT` with `file://C:/...` on Windows; `COPY INTO` accepting `METADATA$FILENAME`, `METADATA$FILE_ROW_NUMBER` and `CURRENT_TIMESTAMP()` in a transforming copy; CRLF line ends (the runbook has nine `ENDSWITH(.., CHR(13))` checks); literal backslashes (`ESCAPE_UNENCLOSED_FIELD = NONE`); the BOM; record counts equal to the Python `csv` record counts; reload and idempotent re-run.
3. Function semantics: `to_timestamp_ntz` with the explicit pattern; `weekiso` (2016-01-01 = 53); `dayofweekiso`; `MEDIAN(float)` parity at 1e-6; `ROUND(FLOAT)` at `.xx5`; `NULLS LAST` under `DESC`; `GENERATOR` giving exactly 1,827 days plus the `-1` row; `NUMBER(12,2)` casts of widened sums; `row_number() ... = 1` as a select expression; `qualify` in `int_geography_rollup`; binary collation for key ordering.
4. `ASOF JOIN ... MATCH_CONDITION` in `int_late_delivery_history` (four chained joins, optional `ON`, strict `>`, unmatched left rows kept, precomputed 28-day column). If it fails, run `dbt build -s +mart_late_delivery_features --vars '{late_delivery_history_method: range_join}'`; that fallback is quadratic and its runtime and credits are unknown.
5. Runtime and credit cost of `dbt build`, the seller range join and the two heavier singular tests on `XSMALL`. Measure, do not estimate.
6. Reconciliation: that the marts match the DuckDB reference apart from the explained tie-break differences, the headline numbers (R$13,494,400.74 net revenue; 98,199 net orders; 7,827 late; 96,282 labelled with 7,823 late; 96.96 percent one-time customers) and `docs/validation/RECONCILIATION_REPORT.md`, which is still the NOT RUN stub.
7. Python on Snowflake: connector type mapping (`NUMBER`, `TIMESTAMP_NTZ`, `BOOLEAN`) under pandas 3; `fetch_pandas_all`; `write_pandas` with upper-case columns; the `ML.*` write-back statements; connector support on Python 3.14. The `main()` entry points of `forecast_baseline.py` and `late_delivery_baseline.py` still open DuckDB directly (no `--backend` flag yet).
8. Power BI: that the patched copy opens; the Snowflake connector authentication option you choose; `Kind="View"` navigation for `PBI` and `Kind="Table"` for `ML`.

## 10. Inventory D: SQL added for Snowflake (93 files)

Listed from `git ls-files "*.sql"` on 2026-11-06, every file by name. These are the migration targets named in the "dbt model" columns above, plus infrastructure SQL. They are new, so no migration class applies. Per-model descriptions, grains, columns and tests are in `docs/data_dictionary/DATA_DICTIONARY.md`, and the purpose of each singular test is in its "Singular tests" table.

| Folder under `snowflake/` | Files | File names |
|---|---|---|
| `dbt/macros/` | 3 | `date_key.sql`, `generate_schema_name.sql`, `iso_week_start.sql` |
| `dbt/models/staging/` | 9 | `stg_olist__category_translation.sql`, `stg_olist__customers.sql`, `stg_olist__geolocation.sql`, `stg_olist__order_items.sql`, `stg_olist__order_payments.sql`, `stg_olist__order_reviews.sql`, `stg_olist__orders.sql`, `stg_olist__products.sql`, `stg_olist__sellers.sql` |
| `dbt/models/intermediate/` | 5 | `int_customers_latest.sql`, `int_geography_points.sql`, `int_geography_rollup.sql`, `int_order_items_agg.sql`, `int_order_payments_agg.sql` |
| `dbt/models/intermediate/late_delivery/` | 4 | `int_late_delivery_history.sql`, `int_late_delivery_item_agg.sql`, `int_late_delivery_population.sql`, `int_late_delivery_seller_history.sql` |
| `dbt/models/marts/core/` | 9 | `dim_customer.sql`, `dim_date.sql`, `dim_geography.sql`, `dim_product.sql`, `dim_seller.sql`, `fact_order_items.sql`, `fact_orders.sql`, `fact_payments.sql`, `fact_reviews.sql` |
| `dbt/models/marts/analytics/` | 8 | `mart_category_performance.sql`, `mart_delivery_trend.sql`, `mart_delivery_vs_reviews.sql`, `mart_monthly_kpis.sql`, `mart_payments.sql`, `mart_repeat_customers.sql`, `mart_seller_concentration.sql`, `mart_state_performance.sql` |
| `dbt/models/marts/ml/` | 2 | `mart_late_delivery_features.sql`, `mart_weekly_orders_revenue.sql` |
| `dbt/models/pbi/` | 9 | `pbi_dim_customer.sql`, `pbi_dim_date.sql`, `pbi_dim_geography.sql`, `pbi_dim_product.sql`, `pbi_dim_seller.sql`, `pbi_fact_order_items.sql`, `pbi_fact_orders.sql`, `pbi_fact_payments.sql`, `pbi_fact_reviews.sql` |
| `dbt/tests/` | 28 | `assert_dim_customer_rows_eq_distinct_unique_ids.sql`, `assert_dim_date_contains_all_days_of_2016_11.sql`, `assert_dim_date_covers_all_used_dates.sql`, `assert_dim_date_has_no_gaps.sql`, `assert_dim_geography_rows_eq_in_bounds_zip_prefixes.sql`, `assert_dim_product_rows_eq_staging.sql`, `assert_dim_seller_rows_eq_staging.sql`, `assert_fact_order_items_rows_eq_staging.sql`, `assert_fact_order_items_unknown_keys_only_when_unmatched.sql`, `assert_fact_orders_rows_eq_staging.sql`, `assert_fact_payments_rows_eq_staging.sql`, `assert_fact_reviews_rows_eq_staging.sql`, `assert_item_revenue_unchanged_after_dimension_joins.sql`, `assert_late_deliveries_eq_staging.sql`, `assert_late_delivery_history_is_point_in_time.sql`, `assert_late_delivery_one_row_per_population_order_with_items.sql`, `assert_late_delivery_seller_history_excludes_self.sql`, `assert_one_latest_review_per_reviewed_order.sql`, `assert_orders_without_items_kept.sql`, `assert_sum_freight_fact_eq_staging.sql`, `assert_sum_item_total_eq_price_plus_freight.sql`, `assert_sum_items_price_orders_eq_order_items.sql`, `assert_sum_payment_total_orders_eq_payments.sql`, `assert_sum_payment_value_fact_eq_staging.sql`, `assert_sum_price_fact_eq_staging.sql`, `assert_timestamp_anomalies_eq_staging.sql`, `assert_unknown_members_present.sql`, `assert_unmatched_customer_zip_maps_to_unknown_geography.sql` |
| `dbt/tests/analytics/` | 11 | `assert_mart_category_performance_reconciles_to_facts.sql`, `assert_mart_delivery_trend_reconciles_to_facts.sql`, `assert_mart_delivery_vs_reviews_reconciles_to_facts.sql`, `assert_mart_monthly_kpis_growth_blank_next_to_thin_months.sql`, `assert_mart_monthly_kpis_reconcile_to_facts.sql`, `assert_mart_payments_reconciles_to_facts.sql`, `assert_mart_repeat_customers_reconciles_to_facts.sql`, `assert_mart_seller_concentration_is_ordered.sql`, `assert_mart_state_performance_reconciles_to_facts.sql`, `assert_mart_weekly_orders_revenue_reconciles_to_facts.sql`, `assert_pbi_views_match_core_marts.sql` |
| `setup/` | 3 | `00_preflight.sql`, `01_objects.sql`, `02_grants.sql` |
| `ingestion/` | 2 | `ddl_raw.sql`, `file_formats.sql` |
| **Total** | **93** | |

How to reproduce the counts: `git ls-files "*.sql" | wc -l` (139), `git ls-files "sql/*" | grep -c "\.sql$"` (46), and `git ls-files "snowflake/*" | grep -c "\.sql$"` (93).
