# Model card

Two models trained on the Olist Brazilian e-commerce dataset (about 100,000 orders, 2016 to 2018; CC BY-NC-SA 4.0, non-commercial use only). Both are baselines built to be honest about their limits, not production systems. All numbers come from time-ordered backtests; the supporting analyses are linked.

## 1. Late-delivery model

| | |
|---|---|
| **Task** | Given an order at the moment of purchase, rank it by how likely it is to arrive after the promised delivery date |
| **Unit and label** | One delivered order; label `fact_orders.is_late` (8.1% positive) |
| **Model** | Logistic regression on 16 numeric and 3 categorical features ("v1"), trained on all resolved orders from 2017-01 up to each test month |
| **Intended use** | Triage: flag the riskiest share of new orders (for example 10%) for proactive handling |
| **Not intended for** | Quoting a probability of lateness to a customer or seller; deciding anything about a person; use outside this dataset's period and market |
| **Code** | [late_delivery_features.sql](../../sql/ml/late_delivery_features.sql), [late_delivery_baseline.py](../../src/ml/late_delivery_baseline.py) |

**Features (all known at purchase).** The promised window (`promised_days`), basket size, weight and freight, customer state, seller state, a same-state flag and the distance between them, weekday and hour, instalments and payment type, and the seller's late rate over orders already delivered before this purchase. Excluded on purpose: every carrier, delivery and review field, `order_status`, and the shipping limit date, which is set after purchase ([LEAKAGE_ANALYSIS.md](LEAKAGE_ANALYSIS.md)).

**Evaluation.** Monthly rolling origin over 2018-03 to 2018-08 (38,988 test orders). Each model trains only on orders whose delivery was known before the test month starts.

| Model | PR-AUC | ROC-AUC | Brier | Precision, top 10% flagged | Share of late orders caught |
|---|---:|---:|---:|---:|---:|
| Always predict the training late rate | 0.085 | 0.500 | 0.0792 | n/a | n/a |
| Seller's own history rate | 0.099 | 0.526 | 0.0817 | 0.102 | 0.123 |
| **Logistic regression (v1)** | **0.184** | **0.707** | **0.0778** | **0.207** | **0.279** |
| Gradient boosting | 0.172 | 0.671 | 0.0796 | 0.196 | 0.259 |

Flagging the riskiest 10% of orders beat the base late rate by 2.4 to 3.9 times in five of six months, and by 1.2 times in August 2018 ([RECALIBRATION_AND_WINDOW.md](RECALIBRATION_AND_WINDOW.md)).

**What drives it** ([explainability_metrics.json](../../reports/explainability_metrics.json), grouped permutation importance: PR-AUC lost when a group is shuffled, mean over the six test months):

| Feature group | PR-AUC lost |
|---|---:|
| Route (states, same-state flag, distance) | 0.076 |
| Promise (`promised_days`) | 0.063 |
| Basket size and weight | 0.005 |
| Seller history | 0.005 |
| Payment | 0.001 |
| Purchase weekday and hour | 0.000 |

The model is essentially two things: where the parcel is going and how long the customer was promised. A longer promise lowers the risk (the largest numeric coefficient), and some destination states are riskier than others (for example Alagoas, the largest positive state coefficient, and Rio de Janeiro, against São Paulo and Paraná lower). In August 2018 shuffling the route group *raised* PR-AUC by 0.06: the geographic pattern learned from earlier months no longer held.

**What was tried and did not help** (details in the linked documents):

| Idea | Outcome |
|---|---|
| Route and category late-rate history (v2) | Slightly worse; route history repeats what states and distance already give |
| Trailing 28-day system late rate (v3) | Worse; the recent rate does not predict the next month's |
| Delivery-time slack: promised days minus how long the route and the system have recently taken (v5) | No gain (PR-AUC 0.176 against 0.184); top-quintile calibration somewhat closer |
| Recalibration on the latest resolved orders | Worse on Brier, log loss and calibration error |
| Shorter or walk-forward training windows | +0.010 PR-AUC, wins in only 3 of 6 months, mostly August |
| Gradient boosting | Worse than the linear model |

See [PHASE2_BASELINES.md](PHASE2_BASELINES.md), [DRIFT_ANALYSIS.md](DRIFT_ANALYSIS.md) and DD-10 to DD-12 in [DECISIONS.md](../../DECISIONS.md).

**Limitations**
- **Probabilities are not trustworthy in level.** The mean prediction is off by about 0.06 per month on average (0.14 in March 2018), because the late rate swings between months (1.4% to 21.4%) and cannot be predicted from the recent past. Use rank, and set the operating point as a share of orders flagged, not a probability threshold.
- **Concept drift.** The relationship between promise length and lateness reversed in August 2018, when the promised windows shortened sharply. A shift like this degrades the ranking (lift fell to 1.2). A monitor on the distribution of promised days would catch it.
- **Only delivered orders have a label.** The model answers "if this order is delivered, will it be late?" About 2% to 3% of each test month has no label.
- **Small test set in time.** Six months, a single market, a dataset that ends in 2018.
- **Geography as a feature.** Customer and seller state drive the ranking. That is appropriate for logistics but means regions with historically slow service would be flagged more, and any use affecting customers directly would need a fairness review. There is no personal data in the features.

## 2. Weekly order forecast

| | |
|---|---|
| **Task** | Forecast next week's order count (and revenue) |
| **Series** | Orders per ISO week from `fact_orders`; 85 clean weeks, 2017-01-02 to 2018-08-13 |
| **Evaluation** | Rolling origin, first forecast after 26 weeks; 59 one-week and 56 four-week forecasts |
| **Code** | [forecast_baseline.py](../../src/ml/forecast_baseline.py), [forecast_models.py](../../src/ml/forecast_models.py) |

**Orders, mean absolute error (lower is better; "vs naive" below 1 beats repeating last week):**

| Model | 1 week: MAE | vs naive | 4 weeks: MAE | vs naive |
|---|---:|---:|---:|---:|
| Naive (last week) | 204 | 1.00 | 353 | 1.00 |
| Moving average, 8 weeks | 234 | 1.15 | **272** | **0.77** |
| Simple exponential smoothing | 214 | 1.05 | 349 | 0.99 |
| Damped trend | 228 | 1.12 | 394 | 1.12 |
| AR(1) with trend, 26 weeks | 231 | 1.13 | 526 | 1.49 |
| Average of naive and 8-week average | **183** | **0.90** | 300 | 0.85 |

**Recommendation.** For one week ahead, the average of the naive forecast and the 8-week average (about 10% lower error than naive); for four weeks ahead, the 8-week average (about 23% lower). Neither is a strong claim:

- The combination was assembled after seeing that these two baselines were the winners, so its edge is optimistic. It beat the naive forecast in only 51% of individual weeks.
- The ranking is not stable across series. On revenue, the AR(1) regression is among the best (0.87 and 0.76 of naive) while on orders it is among the worst (1.13 and 1.49). Two series that move together should not rank a model so differently, which says the 85-week backtest cannot separate these models.
- Every model under-forecasts on average because orders grew through 2017.
- One Black Friday and under two years of data: seasonality cannot be learned or tested.

## 3. Reproducing

```
uv run python src/transformation/build_warehouse.py
uv run python src/ml/late_delivery_baseline.py
uv run python src/ml/forecast_models.py
uv run python src/ml/explain_late_delivery.py
uv run pytest
```

Results can differ slightly between runs because of multithreaded numerical code: in a fresh-clone rerun the largest differences were about 0.001 in PR-AUC and 0.002 in ROC-AUC (the v1 logistic model came out identical), so compare to that tolerance. Metric files are in [reports/](../../reports/).
