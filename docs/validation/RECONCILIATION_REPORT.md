# Reconciliation report: DuckDB vs Snowflake

## Run

| item | value |
|---|---|
| generated | 2026-11-13 21:02:21 UTC |
| git SHA | 0ebaf36d72be8f4adf889ca103945f31338c4a17 |
| mode | snowflake |
| left (reference) | duckdb file warehouse.duckdb (read-only) |
| right | snowflake account GW***69, database RETAIL_OLIST, role RETAIL_TRANSFORMER, warehouse RETAIL_WH |
| Snowflake account locator (redacted) | GW***69 |
| database / role / warehouse | RETAIL_OLIST / RETAIL_TRANSFORMER / RETAIL_WH |
| schema prefix (dbt dev target) | (none: prod schemas) |
| tool: python | 3.14.2 |
| tool: duckdb | 1.5.6 |
| tool: pandas | 3.0.5 |
| tool: numpy | 2.5.3 |
| tool: snowflake-connector-python | 5.2.0 |
| tool: dbt-core | not installed |
| tool: dbt-snowflake | not installed |

## Summary

PASS: 22 (of 22 checks)

| check | group | status | left rows | right rows | missing+extra keys | unexplained value diffs | classified tie-break diffs | error |
|---|---|---|---|---|---|---|---|---|
| dim_customer | dimension | PASS | 96097 | 96097 | 0 | 0 | 0 |  |
| dim_date | dimension | PASS | 1828 | 1828 | 0 | 0 | 0 |  |
| dim_geography | dimension | PASS | 19012 | 19012 | 0 | 0 | 0 |  |
| dim_product | dimension | PASS | 32952 | 32952 | 0 | 0 | 0 |  |
| dim_seller | dimension | PASS | 3096 | 3096 | 0 | 0 | 0 |  |
| fact_orders | fact | PASS | 99441 | 99441 | 0 | 0 | 0 |  |
| fact_order_items | fact | PASS | 112650 | 112650 | 0 | 0 | 0 |  |
| fact_payments | fact | PASS | 103886 | 103886 | 0 | 0 | 0 |  |
| fact_reviews | fact | PASS | 99224 | 99224 | 0 | 0 | 0 |  |
| row_counts | headline | PASS | 9 | 9 | 0 | 0 | 0 |  |
| headline_numbers | headline | PASS | 10 | 10 | 0 | 0 | 0 |  |
| mart_monthly_kpis | analytics | PASS | 24 | 24 | 0 | 0 | 0 |  |
| mart_category_performance | analytics | PASS | 74 | 74 | 0 | 0 | 0 |  |
| mart_state_performance | analytics | PASS | 28 | 28 | 0 | 0 | 0 |  |
| mart_seller_concentration | analytics | PASS | 6 | 6 | 0 | 0 | 0 |  |
| mart_delivery_vs_reviews | analytics | PASS | 5 | 5 | 0 | 0 | 0 |  |
| mart_payments | analytics | PASS | 5 | 5 | 0 | 0 | 0 |  |
| mart_repeat_customers | analytics | PASS | 4 | 4 | 0 | 0 | 0 |  |
| mart_delivery_trend | analytics | PASS | 23 | 23 | 0 | 0 | 0 |  |
| mart_late_delivery_features | ml | PASS | 96282 | 96282 | 0 | 0 | 0 |  |
| mart_late_delivery_features_aggregates | ml | PASS | 1 | 1 | 0 | 0 | 0 |  |
| mart_weekly_orders_revenue | ml | PASS | 101 | 101 | 0 | 0 | 0 |  |

## Documented constants (three-way)

Each metric: left value, right value, and the documented constant (source in the last column).

| check | metric | documented | left | right | left ok | right ok | source |
|---|---|---|---|---|---|---|---|
| row_counts | fact_orders | 99441 | 99441.0000 | 99441.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:171-172 (parity targets) |
| row_counts | fact_order_items | 112650 | 112650.0000 | 112650.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:171-172 (parity targets) |
| row_counts | fact_payments | 103886 | 103886.0000 | 103886.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:171-172 (parity targets) |
| row_counts | fact_reviews | 99224 | 99224.0000 | 99224.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:171-172 (parity targets) |
| headline_numbers | net_revenue | 13494400.74 | 13494400.7400 | 13494400.7400 | yes | yes | docs/MIGRATING_TO_CLOUD.md:171; docs/analytics/BUSINESS_INSIGHTS.md |
| headline_numbers | net_orders | 98199 | 98199.0000 | 98199.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:171 |
| headline_numbers | late_orders | 7827 | 7827.0000 | 7827.0000 | yes | yes | sql/validation/checks.sql 'late deliveries (EDA: 7827)' |
| headline_numbers | orders_without_items | 775 | 775.0000 | 775.0000 | yes | yes | sql/validation/checks.sql 'orders without items (EDA: 775)' |
| headline_numbers | labelled_delivered_orders | 96282 | 96282.0000 | 96282.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:172 |
| headline_numbers | labelled_late_orders | 7823 | 7823.0000 | 7823.0000 | yes | yes | docs/MIGRATING_TO_CLOUD.md:172 |
| headline_numbers | one_time_customer_share_pct | 96.96 | 96.9600 | 96.9600 | yes | yes | reports/analytics/07_repeat_customers.csv (row 1) |

## arg_max / max_by tie-breaks

DuckDB `arg_max` and Snowflake `max_by` may pick different values when the maximum is tied. Orders with a tied maximum are counted below. A difference in the picked column is classified `tie_break` only when both values are among the order's tied candidates; differences in running category totals are classified `downstream_of_tie_break` whenever any ambiguous order exists (a weak bound, shown so it can be judged). Nothing is dropped: every classified difference is still counted.

| check | tie-break | ambiguous orders | picked column | tie_break diffs | downstream columns | downstream diffs | note |
|---|---|---|---|---|---|---|---|
| mart_late_delivery_features | main_payment_type | 0 | main_payment_type | 0 |  | 0 | ambiguous orders: duckdb 0, snowflake 0; tied values involved: 0; rows eligible for classification: 0 of 96281 |
| mart_late_delivery_features | category | 57 | (not in output) | 0 | category_prior_n, category_prior_late | 0 | ambiguous orders: duckdb 57, snowflake 57; tied values involved: 26; rows eligible for classification: 65132 of 96282 |
| mart_late_delivery_features_aggregates | category | 57 | (not in output) | 0 | sum_category_prior_n, sum_category_prior_late | 0 | ambiguous orders: duckdb 57, snowflake 57; tied values involved: 26; rows eligible for classification: 65132 of 96282 |

## Check details

### dim_customer (dimension): PASS

One row per customer_unique_id (+ the -1 member).

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 96097 | 96097 | 96097 | 0 | 0 | 0/0 | 0 |

All 3 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| customer_key | exact | 96097 | 0 | 0 |  | 0 | 0 |  |

### dim_date (dimension): PASS

One row per calendar day (+ the -1 member); date_key is the yyyymmdd smart key.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 1828 | 1828 | 1828 | 0 | 0 | 0/0 | 0 |

All 11 compared columns are identical.

### dim_geography (dimension): PASS

One row per zip prefix (+ the -1 member, keyed here as __UNKNOWN__). Medians compared relative 1e-9.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 19012 | 19012 | 19012 | 0 | 0 | 0/0 | 0 |

All 6 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| geography_key | exact | 19012 | 0 | 0 |  | 0 | 0 |  |

### dim_product (dimension): PASS

One row per product_id (+ the -1 member).

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 32952 | 32952 | 32952 | 0 | 0 | 0/0 | 0 |

All 10 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| product_key | exact | 32952 | 0 | 0 |  | 0 | 0 |  |

### dim_seller (dimension): PASS

One row per seller_id (+ the -1 member).

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 3096 | 3096 | 3096 | 0 | 0 | 0/0 | 0 |

All 3 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| seller_key | exact | 3096 | 0 | 0 |  | 0 | 0 |  |

### fact_orders (fact): PASS

One row per order. Customer and geography are compared by natural key.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 99441 | 99441 | 99441 | 0 | 0 | 0/0 | 0 |

All 23 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| customer_key | exact | 99441 | 0 | 0 |  | 0 | 0 |  |
| customer_geography_key | exact | 99441 | 0 | 0 |  | 0 | 0 |  |

### fact_order_items (fact): PASS

One row per (order_id, order_item_id). Dimensions compared by natural key.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 112650 | 112650 | 112650 | 0 | 0 | 0/0 | 0 |

All 11 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| customer_key | exact | 112650 | 0 | 0 |  | 0 | 0 |  |
| product_key | exact | 112650 | 0 | 0 |  | 0 | 0 |  |
| seller_key | exact | 112650 | 0 | 0 |  | 0 | 0 |  |
| customer_geography_key | exact | 112650 | 0 | 0 |  | 0 | 0 |  |
| seller_geography_key | exact | 112650 | 0 | 0 |  | 0 | 0 |  |

### fact_payments (fact): PASS

One row per (order_id, payment_sequential).

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 103886 | 103886 | 103886 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| customer_key | exact | 103886 | 0 | 0 |  | 0 | 0 |  |

### fact_reviews (fact): PASS

One row per (review_id, order_id). Comment text is compared but never echoed.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 99224 | 99224 | 99224 | 0 | 0 | 0/0 | 0 |

All 10 compared columns are identical.

Surrogate keys (reported separately; they do not decide the status above):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| customer_key | exact | 99224 | 0 | 0 |  | 0 | 0 |  |

### row_counts (headline): PASS

Row count of every dimension and fact (documented parity targets for the facts).

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 9 | 9 | 9 | 0 | 0 | 0/0 | 0 |

All 1 compared columns are identical.

### headline_numbers (headline): PASS

Headline figures, three-way: DuckDB vs Snowflake vs the documented constant. Definitions: net = not canceled/unavailable (sql/analytics/01, 03, 07); late = fact_orders.is_late (sql/validation/checks.sql); labelled = delivered, is_late not null, no timestamp anomaly (Power BI is_labelled_delivery, ML population); one-time = customers with exactly one net order (sql/analytics/07).

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 10 | 10 | 10 | 0 | 0 | 0/0 | 0 |

All 1 compared columns are identical.

### mart_monthly_kpis (analytics): PASS

Monthly KPIs: Snowflake mart_monthly_kpis vs sql/analytics/01_monthly_kpis.sql and reports/analytics/01_monthly_kpis.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 24 | 24 | 24 | 0 | 0 | 0/0 | 0 |

All 9 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 01_monthly_kpis.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 24 | 24 | 24 | 0 | 0 | 0/0 | 0 |

All 9 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 01_monthly_kpis.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 24 | 24 | 24 | 0 | 0 | 0/0 | 0 |

All 9 compared columns are identical.

### mart_category_performance (analytics): PASS

Category performance: Snowflake mart_category_performance vs sql/analytics/02_category_performance.sql and reports/analytics/02_category_performance.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 74 | 74 | 74 | 0 | 0 | 0/0 | 0 |

All 9 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 02_category_performance.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 74 | 74 | 74 | 0 | 0 | 0/0 | 0 |

All 9 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 02_category_performance.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 74 | 74 | 74 | 0 | 0 | 0/0 | 0 |

All 9 compared columns are identical.

### mart_state_performance (analytics): PASS

Customer-state performance: Snowflake mart_state_performance vs sql/analytics/03_state_performance.sql and reports/analytics/03_state_performance.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 28 | 28 | 28 | 0 | 0 | 0/0 | 0 |

All 8 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 03_state_performance.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 28 | 28 | 28 | 0 | 0 | 0/0 | 0 |

All 8 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 03_state_performance.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 28 | 28 | 28 | 0 | 0 | 0/0 | 0 |

All 8 compared columns are identical.

### mart_seller_concentration (analytics): PASS

Seller revenue concentration: Snowflake mart_seller_concentration vs sql/analytics/04_seller_concentration.sql and reports/analytics/04_seller_concentration.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 6 | 6 | 6 | 0 | 0 | 0/0 | 0 |

All 1 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 04_seller_concentration.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 6 | 6 | 6 | 0 | 0 | 0/0 | 0 |

All 1 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 04_seller_concentration.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 6 | 6 | 6 | 0 | 0 | 0/0 | 0 |

All 1 compared columns are identical.

### mart_delivery_vs_reviews (analytics): PASS

Late delivery vs review score: Snowflake mart_delivery_vs_reviews vs sql/analytics/05_delivery_vs_reviews.sql and reports/analytics/05_delivery_vs_reviews.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 5 | 5 | 5 | 0 | 0 | 0/0 | 0 |

All 4 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 05_delivery_vs_reviews.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 5 | 5 | 5 | 0 | 0 | 0/0 | 0 |

All 4 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 05_delivery_vs_reviews.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 5 | 5 | 5 | 0 | 0 | 0/0 | 0 |

All 4 compared columns are identical.

### mart_payments (analytics): PASS

Payment mix: Snowflake mart_payments vs sql/analytics/06_payments.sql and reports/analytics/06_payments.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 5 | 5 | 5 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 06_payments.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 5 | 5 | 5 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 06_payments.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 5 | 5 | 5 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

### mart_repeat_customers (analytics): PASS

Repeat purchasing: Snowflake mart_repeat_customers vs sql/analytics/07_repeat_customers.sql and reports/analytics/07_repeat_customers.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 4 | 4 | 4 | 0 | 0 | 0/0 | 0 |

All 4 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 07_repeat_customers.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 4 | 4 | 4 | 0 | 0 | 0/0 | 0 |

All 4 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 07_repeat_customers.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 4 | 4 | 4 | 0 | 0 | 0/0 | 0 |

All 4 compared columns are identical.

### mart_delivery_trend (analytics): PASS

Delivery trend by purchase month: Snowflake mart_delivery_trend vs sql/analytics/08_delivery_trend.sql and reports/analytics/08_delivery_trend.csv.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 23 | 23 | 23 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

**duckdb_vs_reference_csv** (duckdb vs 08_delivery_trend.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 23 | 23 | 23 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

**snowflake_vs_reference_csv** (snowflake vs 08_delivery_trend.csv): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 23 | 23 | 23 | 0 | 0 | 0/0 | 0 |

All 5 compared columns are identical.

### mart_late_delivery_features (ml): PASS

Row-level diff of the late-delivery feature table vs sql/ml/late_delivery_features.sql. arg_max / max_by tie-breaks (category, main_payment_type) are classified and counted, never hidden.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 96282 | 96282 | 96282 | 0 | 0 | 0/0 | 0 |

Columns with a difference (including float drift inside tolerance):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| distance_km | abs 1e-06 | 96282 | 0 | 0 |  | 1.36e-12 | 5.61e-16 |  |
| seller_prior_late_rate | abs 1e-09 | 96282 | 0 | 0 |  | 2.78e-17 | 3.31e-16 |  |
| route_prior_days | rel 1e-09 | 96282 | 0 | 0 |  | 2.33e-10 | 1.25e-15 |  |
| recent_days_28d | rel 1e-09 | 96282 | 0 | 0 |  | 1.4e-09 | 3.01e-14 |  |

### mart_late_delivery_features_aggregates (ml): PASS

Per-column aggregates (row count, sums, non-null counts, extremes, distinct counts) of the late-delivery feature table.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 1 | 1 | 1 | 0 | 0 | 0/0 | 0 |

Columns with a difference (including float drift inside tolerance):

| column | rule | compared | mismatches | unexplained | classified | max abs diff | max rel diff | examples (key: left vs right) |
|---|---|---|---|---|---|---|---|---|
| avg_seller_prior_late_rate | abs 1e-09 | 1 | 0 | 0 |  | 1.78e-15 | 3.25e-14 |  |
| sum_promised_days | rel 1e-09 | 1 | 0 | 0 |  | 2.05e-08 | 8.96e-15 |  |
| sum_freight_ratio | rel 1e-09 | 1 | 0 | 0 |  | 1.28e-09 | 4.33e-14 |  |
| sum_distance_km | rel 1e-09 | 1 | 0 | 0 |  | 2.98e-07 | 5.17e-15 |  |
| sum_seller_prior_late_rate | rel 1e-09 | 1 | 0 | 0 |  | 1.46e-10 | 3.24e-14 |  |
| sum_route_prior_days | rel 1e-09 | 1 | 0 | 0 |  | 5.72e-05 | 1.13e-14 |  |
| sum_recent_days_28d | rel 1e-09 | 1 | 0 | 0 |  | 0.000146 | 2.37e-14 |  |

### mart_weekly_orders_revenue (ml): PASS

Weekly orders and revenue (ISO Monday weeks) vs src/ml/forecast_baseline.py weekly_series.

**duckdb_vs_snowflake** (duckdb vs snowflake): **PASS**

| left rows | right rows | matched keys | missing in right | extra in right | duplicate keys L/R | rows with a differing value |
|---|---|---|---|---|---|---|
| 101 | 101 | 101 | 0 | 0 | 0/0 | 0 |

All 2 compared columns are identical.

## Notes

- Snowflake SQL is generated from `src/reconciliation/checks.py` against the dbt marts; it was written to the model contract and is only as verified as this run.
- Customer review text is compared but never printed; examples show its length only.
- Counts, keys, money (Decimal), booleans, strings, dates and timestamps compare exact; doubles relative 1e-9; `distance_km` absolute 1e-6; rates absolute 1e-9.
