# EDA findings: Olist dataset discovery

Summary of `notebooks/01_dataset_discovery.ipynb`, which holds the queries, charts and the full evidence. Every issue below is documented, not silently dropped; the last column says how the data model handles it ([DATA_MODEL.md](DATA_MODEL.md)).

## The data

Nine files: orders 99,441 rows, customers 99,441, order items 112,650, payments 103,886, reviews 99,224, products 32,951, sellers 3,095, category translation 71, geolocation 1,000,163. Orders run from 2016-09-04 to 2018-10-17, with 97% `delivered`. Item revenue totals 13,591,643.70.

## Issue log

| # | Finding | Evidence | Handling in the model |
|---|---|---|---|
| 1 | `customer_id` is per order, not per person | 99,441 ids for 96,096 `customer_unique_id`; 2,997 customers ordered more than once; 250 appear in more than one zip prefix or state | `dim_customer` at `customer_unique_id` grain; location at order time carried on the facts via `dim_geography` |
| 2 | `review_id` is not unique | 99,224 rows, 98,410 ids; 789 ids on more than one order; 547 orders have 2-3 reviews | `fact_reviews` grain (`review_id`, `order_id`); `is_latest_review_for_order` flag |
| 3 | Joining child tables side by side overstates revenue | Orders + items + payments gives 118,434 rows and +4.54% item price; with reviews 119,143 rows and +5.02% | Facts never join to facts; order-level fact pre-aggregates items and payments |
| 4 | 775 orders have no items | 603 `unavailable`, 164 `canceled`, 5 `created`, 2 `invoiced`, 1 `shipped`. Also 1 order without payment, 768 without review | `fact_orders` keeps all orders; item count and totals are 0 |
| 5 | Payments do not always equal items + freight | 380 of 98,665 orders differ; 313 are instalment orders (0.62% of those, vs 0.14% of single-instalment orders); payments exceed items + freight by 2,870 in total | Revenue measured from items; `fact_payments` is its own fact and never forced to tie |
| 6 | Timestamp errors in the source | 166 orders with carrier date before purchase; 23 with customer delivery before carrier date | Kept; `has_timestamp_anomaly` flag |
| 7 | Missing milestone dates that conflict with status | 8 `delivered` orders have no delivery date, 14 no approval time, 2 no carrier date; 6 `canceled` orders have a delivery date | Date key -1 (not applicable); raw timestamps nullable |
| 8 | Date outliers | 4 items have a `shipping_limit_date` in 2020-02 to 2020-04; every other date column ends by 2018-11 | Kept as recorded; the calendar extends to 2020 |
| 9 | Months with no orders | 2016-11 has none; 2016 and the months after 2018-08 are thin | `dim_date` is a generated, gap-free calendar |
| 10 | Products with no category | 610 products (also no photo count or name/description length); 2 have no weight or dimensions | `dim_product` category `unknown` |
| 11 | Categories missing from the translation file | `pc_gamer` (3 products), `portateis_cozinha_e_preparadores_de_alimentos` (10) | English name falls back to the Portuguese name |
| 12 | Misspelled source columns | `product_name_lenght`, `product_description_lenght` | Renamed in staging |
| 13 | Geolocation has no key | 1,000,163 points for 19,015 prefixes; 31 points outside Brazil; 8 prefixes span more than one state | Collapsed to one row per prefix (median coordinates, most frequent city/state) |
| 14 | Some customer and seller zips are not in geolocation | 158 distinct customer prefixes (279 customer rows) and 7 seller prefixes unmatched | Unknown geography member (-1) |
| 15 | Zero or odd values | 383 items with zero freight; 6 voucher and 3 `not_defined` payments of value 0; 2 credit-card payments with 0 installments | Kept as recorded |
| 16 | Translation file starts with a UTF-8 BOM | First header would read `﻿product_category_name` | Header row skipped when reading, so the BOM never reaches a column name |

## Patterns worth knowing (associational, not causal)

- Late deliveries are **associated with** lower review scores: 2.57 average for late orders (7,701 reviews) vs 4.29 on time (88,658 reviews).
- Median delivery takes 10 days (mean 12.5, max 210); 7,827 of 96,476 orders with a delivery date arrived after the estimate.
- Orders ramp through 2017 (peak 7,544 in 2017-11) and hold around 6-7k a month in 2018.
- The top 10 categories are 62.4% of item revenue; São Paulo holds 42% of customer ids.

## Not yet covered

- The dataset licence has not been verified (your project prompt says to check it rather than assume).
- Leakage analysis, forecasting targets and customer segmentation come after the model, per the project plan.
