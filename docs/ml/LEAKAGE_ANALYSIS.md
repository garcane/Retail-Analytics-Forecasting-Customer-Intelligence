# Leakage analysis

This document defines the two ML targets chosen in D-007 ([DECISIONS.md](../../DECISIONS.md)) and lists, column by column, what each model may and may not use. It is the design gate for Phase 2+: feature code must follow these rules, and any exception must be recorded here first.

Figures come from queries against `warehouse.duckdb` (2026-10-11), [EDA_FINDINGS.md](../data/EDA_FINDINGS.md) and [PHASE0_DISCOVERY.md](../phase0/PHASE0_DISCOVERY.md). Column names are those in [DATA_MODEL.md](../data/DATA_MODEL.md).

## Target A: late delivery

| | |
|---|---|
| **Question** | Will this order reach the customer after the delivery date promised at checkout? |
| **Label** | `fact_orders.is_late` (`delivered_customer_ts > estimated_delivery_ts`) |
| **Prediction unit** | One order (`order_id`) |
| **Prediction point** | The purchase timestamp (`purchase_ts`) |
| **Horizon** | Until delivery: median 10 days, max 210 |
| **Population** | Orders with a delivery date: 96,476 of 99,441 |
| **Positives** | 7,827 late (8.11%) |
| **Business use** | Flag at-risk orders at checkout so the promised date or the carrier can be adjusted, or the customer told early. Late orders average 2.57 review stars against 4.29 on time (association, not cause). |

**Why purchase time, not approval.** `estimated_delivery_ts` is shown to the customer at purchase and is never null. `approved_ts` is null for 160 orders. Predicting at purchase is also the most useful moment for the business. The price is that anything set at approval (see `shipping_limit_date` below) is not available.

### Population and label caveats

- **Selection on the outcome.** Only orders that were eventually delivered have a label. The 1,107 `shipped` orders and those canceled before delivery have none. The model therefore answers "if this order is delivered, will it be late?". That is a conditional question and must be stated wherever results are reported.
- **Six canceled orders have a delivery date** and so a label (EDA issue 7). Restrict training to `order_status = 'delivered'` (96,470 orders). This is a filter on the population, never a feature.
- **Right-censoring at the end.** Data stops on 2018-10-17. Late orders bought in the last weeks are more likely to still be in transit and so missing a label. 819 labelled orders were delivered after 2018-08-29. Test sets that end close to the cutoff will understate the late rate. Hold back the final weeks or report the share of unlabelled orders next to every test metric.
- **The base rate moves a lot.** The monthly late rate ranges from 1.4% (2018-06) to 21.4% (2018-03), with spikes in 2017-11 (14.3%) and 2018-02 (16.0%). A random split would mix these regimes and hide that drift. Only a time-ordered split shows how the model copes with it.
- **Timestamp anomalies.** 166 orders have the carrier date before purchase and 23 have customer delivery before the carrier date. Keep them; `has_timestamp_anomaly` may be used to exclude rows from training, but never as a feature.

## Target B: weekly order forecast

| | |
|---|---|
| **Question** | How many orders will be placed next week? Revenue (`sum(price)` from `fact_order_items`) is a secondary target. |
| **Series** | `count(distinct order_id)` per ISO week (Monday start) of `purchase_ts`, from `fact_orders` |
| **Window** | Weeks starting 2017-01-02 to 2018-08-20: 86 complete weeks |
| **Horizon** | 1 week ahead (main), up to 4 weeks |
| **Validation** | Rolling-origin backtest in time order; naïve and moving-average baselines first |

**Window edges** (from the warehouse):
- Before 2017: 4 orders in 2016-09, 324 in 2016-10, none in 2016-11 and 1 in 2016-12. This is a sparse tail, excluded and documented.
- Week of 2018-08-27: 130 orders over three days, then single figures. The data extraction ends mid-week, so this week is excluded.
- Week of 2018-08-20: 1,071 orders against about 1,900 in each of the two weeks before. This is probably also truncated by the extraction. Treat it as suspect: report backtest metrics with and without it.

**Limits to state with results:** less than two years of history means one observation of each season. The 2017-11 peak (7,544 orders, the month of Black Friday) cannot be confirmed as seasonal, and a 52-week seasonal-naïve baseline has almost no usable history.

## Column audit for target A

Each column is classified as one of the following:
- **Allowed:** known at purchase.
- **Point-in-time:** usable only as a statistic computed from earlier, already-resolved orders.
- **Post-outcome:** only known after purchase.
- **Target-derived:** a function of the label.
- **Identifier:** a key, not a feature.
- **High-cardinality:** usable only after encoding.

### `fact_orders`

| Column | Class | Rule |
|---|---|---|
| `order_id`, `customer_id` | Identifier | Never a feature. `customer_id` is per order, so it carries no history either. |
| `customer_key` | Identifier | Never a raw feature. See customer history below. |
| `customer_geography_key` | Allowed | Join to `dim_geography` for state, coordinates and the route to the seller. |
| `purchase_ts`, `purchase_date_key` | Allowed | Calendar features: weekday, hour, month, days to month end. |
| `estimated_delivery_ts`, `estimated_delivery_date_key` | Allowed | The promised date. Use the promised window (`estimated_delivery_ts - purchase_ts`) as a feature. Stored at midnight on every row. |
| `approved_ts`, `approved_date_key` | Post-outcome | Known only at approval. Allowed only if the prediction point moves to approval. |
| `carrier_ts`, `carrier_date_key` | Post-outcome | Exclude. |
| `delivered_customer_ts`, `delivered_customer_date_key` | Post-outcome | Exclude. They define the label. |
| `delivery_days`, `delivery_delay_days` | Target-derived | Exclude. `delivery_delay_days > 0` is the label. |
| `is_late` | Target | The label. |
| `order_status` | Post-outcome | Exclude. It is the state at extraction time (delivered, canceled and so on). Usable only to define the population. |
| `has_timestamp_anomaly` | Post-outcome | Exclude as a feature (it is built from carrier and delivery dates). May be used to filter rows. |
| `item_count`, `items_price`, `items_freight` | Allowed | The basket is fixed at checkout. |
| `payment_count`, `payment_total` | Allowed, with care | Payment is made at checkout, but 1 order has no payment. Prefer item-side money. |

### `fact_order_items` (aggregate to order grain first, per DD-01)

| Column | Class | Rule |
|---|---|---|
| `product_key` → `dim_product` | Allowed | Weight, dimensions, volume, category, photo count. 610 products have no category (use `unknown`). |
| `seller_key` → `dim_seller` | High-cardinality | 3,095 sellers. Do not one-hot encode. Use seller state and route, plus point-in-time seller statistics. |
| `seller_geography_key` | Allowed | Seller location; distance and same-state flag to the customer. |
| `price`, `freight_value` | Allowed | Freight is quoted at checkout and reflects distance and size. |
| `shipping_limit_date` | Post-outcome at purchase | 79% of values are approval time plus whole days, against 3% for purchase time, so it is set at approval. Exclude for a purchase-time model. |
| `order_status` | Post-outcome | As in `fact_orders`. |

### `fact_payments`

| Column | Class | Rule |
|---|---|---|
| `payment_type`, `payment_installments` | Allowed | Chosen at checkout. Aggregate to order grain (main type, maximum instalments). |
| `payment_sequential`, `payment_value` | Allowed | Prefer `payment_count` and `payment_total` from `fact_orders`. |

### `fact_reviews`

All columns are **post-outcome** for target A: the review is written after delivery and reflects it. That covers `review_score`, comment title and message, `has_comment`, creation and answer timestamps and keys, and `is_latest_review_for_order`. Exclude all of them, including as the order's own features.

Reviews of *earlier* orders may enter only through point-in-time statistics (below), and only once the review was created before the prediction point.

### Point-in-time statistics

Seller, product, category and route statistics are the strongest likely features (a seller's past late rate, for example), and also the easiest way to leak. Rules:

1. Compute each statistic for an order at time *t* only from orders whose **outcome was known before *t***. For a past late rate, that means `delivered_customer_ts < t`, not `purchase_ts < t`: an order bought earlier but still in transit has no outcome yet.
2. Never include the order itself.
3. Use a minimum count (for example, at least 5 resolved orders) and fall back to the global rate; record which rows used the fallback.
4. Compute these statistics in SQL with a time-bounded window or a self-join on `delivered_customer_ts < purchase_ts`, never with a group-by over the whole table.

Implemented in [sql/ml/late_delivery_features.sql](../../sql/ml/late_delivery_features.sql): the seller rate uses the self-join, and the route, category and trailing-28-day statistics use running totals read with a strict `ASOF` join. Both follow rules 1-3, and [tests/test_feature_leakage.py](../../tests/test_feature_leakage.py) checks each rule. Results are in [PHASE2_BASELINES.md](PHASE2_BASELINES.md).

### Customer history

93,356 distinct customers account for the 96,476 labelled orders, and 96.9% of all customers ordered once. Customer-history features (previous orders, previous late deliveries) are empty for almost every row. If they are used, compute them point-in-time by `customer_key` (`customer_unique_id`, DD-02), never by `customer_id`.

## Forecast leakage (target B)

- **Features for week *w*** may use only orders from weeks before *w*: lags, rolling means and trend. Calendar features for *w* itself (ISO week, month, number of days in the month, known events such as Black Friday) are known in advance and allowed.
- `dim_date` has no holiday column. Brazilian holidays and retail events must be added as a separate, hand-maintained calendar, with its source cited.
- **Scaling and smoothing** (normalisation, outlier caps) are fitted on the training part of each backtest fold only.
- **Truncated edge weeks** (above) are excluded before any model sees them. Leaving them in looks like a demand collapse.
- **Revenue as a target:** use `fact_order_items` only (DD-04). Never join payments onto items (fan-out, DD-01).

## Splits and evaluation

| | Target A | Target B |
|---|---|---|
| **Split** | By `purchase_ts`: train on the oldest data, validate on the next block, test on the latest labelled block. No random or stratified-random split. | Rolling origin: fit up to week *w*, forecast *w+1…w+h*, step forward. |
| **Gap** | Leave a gap at least as long as typical delivery (about 2-3 weeks) between train and test, so training labels are not resolved inside the test period. | None needed beyond using past data only. |
| **Baseline** | Previous-period late rate, and the late rate by seller state. | Last week (naïve), and a 4-week moving average. |
| **Metrics** | PR-AUC, recall at a fixed precision, Brier score. No accuracy, since the positive rate is 8%. Report results per test month. | MAE, MAPE, plus skill against the naïve baseline. |

## Checklist from the brief

| Item | Where it is handled |
|---|---|
| Target leakage | `delivery_days`, `delivery_delay_days` and the delivery date are excluded. |
| Temporal leakage | Point-in-time statistics keyed on outcome time; time-ordered splits with a gap. |
| Post-outcome variables | Carrier and delivery timestamps, `order_status`, `shipping_limit_date`, all review fields. |
| Duplicated information | `review_id` duplicates do not matter here because reviews are excluded. Payment totals and item totals overlap, so prefer the item-side measures. |
| Identifiers | `order_id`, `customer_id`, `review_id` and raw surrogate keys are never features. |
| High-cardinality features | Sellers (3,095), products (32,951), zip prefixes (19,012): no one-hot encoding. Use attributes or point-in-time statistics. |
| Target-derived features | Anything built from `delivered_customer_ts`, including `has_timestamp_anomaly`. |
