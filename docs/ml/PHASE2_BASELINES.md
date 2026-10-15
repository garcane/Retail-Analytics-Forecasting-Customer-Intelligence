# Phase 2: baseline results

Baselines for the two targets chosen in D-007. They follow the rules in [LEAKAGE_ANALYSIS.md](LEAKAGE_ANALYSIS.md). They set the bar that any later model has to beat; none of them is tuned.

| What | File |
|---|---|
| Late-delivery features (SQL) | [sql/ml/late_delivery_features.sql](../../sql/ml/late_delivery_features.sql) |
| Late-delivery backtest | [src/ml/late_delivery_baseline.py](../../src/ml/late_delivery_baseline.py), results in [reports/late_delivery_metrics.json](../../reports/late_delivery_metrics.json) |
| Weekly forecast backtest | [src/ml/forecast_baseline.py](../../src/ml/forecast_baseline.py), results in [reports/forecast_metrics.json](../../reports/forecast_metrics.json) |

Reproduce, after building the warehouse:

```
uv run python src/ml/late_delivery_baseline.py
uv run python src/ml/forecast_baseline.py
uv run pytest
```

The first takes about 40 seconds (feature query plus 6 monthly refits of 2 models) and the second about 3 seconds, measured on this laptop. Both open the warehouse read-only. The runs here used the project's `.venv` directly, which gives the same results as `uv run`.

## Target A: late delivery

**Setup.** 96,282 delivered orders, 8.13% late. The v1 features are the allowed and point-in-time columns of the audit, 16 numeric and 3 categorical: calendar, promised delivery days, basket, product weight and volume, distance and states between seller and customer, payment, and the seller's late rate over orders already delivered before this purchase. `purchase_month` is left out on purpose, because with under two years of history it can only memorise calendar months.

**Split.** Monthly rolling origin over 2018-03 to 2018-08. For each test month the models train on orders purchased from 2017-01-01 whose delivery date falls before the month starts, so no training label was resolved inside the test period. Metrics are averaged over the six months and not pooled, because a pooled ROC-AUC would rank scores from models trained at different dates.

**Macro-average over the six test months** (38,988 test orders):

| Model | PR-AUC | ROC-AUC | Brier | Precision, top 10% flagged | Recall, top 10% flagged |
|---|---:|---:|---:|---:|---:|
| Constant (training late rate) | 0.085 | 0.500 | 0.0792 | 0.106* | 0.106* |
| Seller's own history rate | 0.099 | 0.526 | 0.0817 | 0.102 | 0.123 |
| Logistic regression, v1 features | **0.184** | **0.707** | **0.0778** | **0.207** | **0.279** |
| Gradient boosting (depth 4), v1 features | 0.172 | 0.671 | 0.0796 | 0.196 | 0.259 |

The base rate averages 8.5% over these months. *A constant score has no ranking; its top-10% figures only show how ties fell and should read as the base rate.

**PR-AUC by month:**

| Month | Late rate | Unlabelled orders | Constant | Seller history | Logistic (v1) | Boosting (v1) |
|---|---:|---:|---:|---:|---:|---:|
| 2018-03 | 21.4% | 2.9% | 0.214 | 0.237 | 0.393 | 0.371 |
| 2018-04 | 5.3% | 2.1% | 0.053 | 0.066 | 0.180 | 0.175 |
| 2018-05 | 8.3% | 2.2% | 0.083 | 0.100 | 0.212 | 0.226 |
| 2018-06 | 1.4% | 1.9% | 0.014 | 0.012 | 0.061 | 0.055 |
| 2018-07 | 4.5% | 2.8% | 0.045 | 0.076 | 0.129 | 0.110 |
| 2018-08 | 10.5% | 3.2% | 0.105 | 0.105 | 0.127 | 0.096 |

**What the results say.**

- **There is real but modest signal.** Logistic regression doubles the base rate in PR-AUC (0.184 against 0.085), and flagging the riskiest 10% of orders catches 28% of the late ones at about 21% precision, against 8.5% by chance. That is useful for triage but not for firm promises.
- **Boosting does not beat the linear model** with these features and settings. The extra capacity buys nothing, so improvement is more likely to come from better features than from a bigger model.
- **Seller history is almost useless here.** ROC-AUC is 0.526, close to a coin flip. Late deliveries cluster in time (for example March 2018) more than they stick to individual sellers, so a seller's past rate says little about the next order.
- **Calibration is decent but over-confident at the top.** Brier scores are almost equal across models because 8% positives dominate. By score quintile, the v1 logistic model's mean prediction tracks the observed late rate closely except in the highest-risk quintile, where it predicts 21.5% against an observed 17.0% (table below).
- **The last month is the weakest.** In 2018-08 logistic regression barely beats the base rate (0.127 against 0.105) and boosting falls below it. With six test months this is a hint of drift, not a finding.

### Do richer history features help? No.

Three feature sets were compared with the same backtest. v2 adds the late rate of the order's route (seller state to customer state) and of its product category. v3 adds the system-wide late rate over the trailing 28 days. All three are point-in-time: they count only orders whose delivery was already known before this purchase, and are shrunk toward the training late rate when a route or category has little history (20 pseudo-orders each, 100 for the trailing rate).

| Model | PR-AUC | ROC-AUC | Brier | Recall, top 10% flagged |
|---|---:|---:|---:|---:|
| Logistic regression, v1 | **0.184** | **0.707** | **0.0778** | **0.279** |
| Logistic regression, v2 (+ route, category) | 0.174 | 0.687 | 0.0815 | 0.273 |
| Logistic regression, v3 (+ trailing 28 days) | 0.178 | 0.681 | 0.0859 | 0.268 |
| Gradient boosting, v1 | 0.172 | 0.671 | 0.0796 | 0.259 |
| Gradient boosting, v2 | 0.156 | 0.638 | 0.0803 | 0.249 |
| Gradient boosting, v3 | 0.146 | 0.633 | 0.0861 | 0.199 |

Each group of added features leaves the logistic model no better and the boosted model worse, and Brier gets worse as well. The calibration table shows the mechanism: the extra history makes the model more confident without making it more right.

| Score quintile (4 = highest risk) | v1 predicted | v1 actual | v2 predicted | v2 actual | v3 predicted | v3 actual |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 0.032 | 0.027 | 0.034 | 0.032 | 0.037 | 0.035 |
| 1 | 0.059 | 0.056 | 0.064 | 0.062 | 0.068 | 0.067 |
| 2 | 0.081 | 0.074 | 0.092 | 0.078 | 0.098 | 0.077 |
| 3 | 0.112 | 0.100 | 0.133 | 0.093 | 0.147 | 0.083 |
| 4 | 0.215 | 0.170 | 0.260 | 0.163 | 0.283 | 0.166 |

(Mean over the six test months, logistic regression.) Predicted risk in the top quintile rises from 0.215 to 0.283 while the observed rate stays near 0.165.

I suspected drift, and tested it in [DRIFT_ANALYSIS.md](DRIFT_ANALYSIS.md). The answer is mixed. The trailing 28-day rate (v3) and category rate do fail because they track the regime, which does not persist. Route history does not: it is stable, but it repeats what v1 already holds in seller state, customer state and distance, so adding it only adds noise. The system-wide level shift hurts calibration, not ranking. And the ordinary promise-length feature itself flipped in August 2018, which is why that month is the weakest.

The v2 and v3 features stay in the SQL and the script so the comparison can be rerun; v1 remains the reference model (DD-10 in [DECISIONS.md](../../DECISIONS.md)).

## Target B: weekly forecast

**Setup.** Orders per ISO week from `fact_orders`, revenue (item price) as secondary. The main series is the 85 clean weeks from 2017-01-02 to 2018-08-13. The week of 2018-08-20 (1,071 orders against about 1,900 before it) is reported separately as a sensitivity run. The week of 2018-08-27 is always excluded. Forecasts are rolling-origin and start after 26 weeks of history, so there are 59 one-week and 56 four-week forecasts. The models have no fitted parameters beyond a straight line over the last 12 weeks.

**Orders, main series:**

| Model | 1 week: MAE | MAPE | vs naive | 4 weeks: MAE | MAPE | vs naive |
|---|---:|---:|---:|---:|---:|---:|
| Naive (last week) | **204** | **14.0%** | 1.00 | 353 | 25.0% | 1.00 |
| Moving average, 4 weeks | 245 | 17.5% | 1.20 | 302 | 20.6% | 0.85 |
| Moving average, 8 weeks | 234 | 16.4% | 1.15 | **272** | **18.3%** | **0.77** |
| Linear trend, last 12 weeks | 253 | 18.2% | 1.24 | 369 | 25.2% | 1.05 |

"vs naive" is the model's MAE divided by the naive model's MAE; below 1 is better.

**Revenue, main series** gives the same ranking: naive is best at one week (MAE 30,442, MAPE 15.6%), and the 8-week average is best at four weeks (MAE 38,339, 0.79 of naive).

**What the results say.**

- **One week ahead, nothing beats the naive forecast.** Smoothing only adds lag in a series that was still growing through 2017. At four weeks the extra noise in last week's value hurts, and the 8-week average is best.
- **Every model under-forecasts on average** (positive bias, up to about 110 orders for the 4-week horizon), because the series trended upward over most of the test period.
- **The straight-line trend never helps.** It is no better than naive at either horizon (1.24 and 1.05 times its MAE). I have not tested why; the Black Friday spike and the level shift after it are the likely cause.
- **Black Friday week matters.** Dropping that one target week improves the one-week naive MAE from 204 to 178. The results above include it.
- **The suspect week changes little.** Including the week of 2018-08-20 raises the one-week naive MAE from 204 to 214 and leaves the ranking unchanged.
- **A single Black Friday and no second year** mean seasonality cannot be learned or tested. A seasonal-naive baseline is not possible with 85 weeks (LEAKAGE_ANALYSIS, limits).

## Tests

`uv run pytest` runs 31 tests in about 15 to 30 seconds. They cover:

- **Leakage rules on a tiny hand-built warehouse** ([tests/test_feature_leakage.py](../../tests/test_feature_leakage.py)): history counts orders by delivery time, not purchase time; an order never sees its own outcome, or one delivered at the instant of its purchase; the seller rate needs five resolved orders; the 28-day window includes its first instant and excludes the last; unlabelled, canceled and anomalous orders are neither rows nor history; no post-outcome columns are returned.
- **Forecast** ([tests/test_forecast_baseline.py](../../tests/test_forecast_baseline.py)): changing weeks after the forecast origin cannot change an earlier forecast, and each baseline gives the value computed by hand.
- **Helpers** ([tests/test_late_delivery_helpers.py](../../tests/test_late_delivery_helpers.py)) and **geolocation conversion** ([tests/test_geolocation_conversion.py](../../tests/test_geolocation_conversion.py)): CSV only (leading zeros kept), Parquet already present, neither present.
- **The real warehouse** ([tests/test_warehouse.py](../../tests/test_warehouse.py), skipped if `warehouse.duckdb` is missing): the 22 validation checks pass, and the feature columns match direct recounts from the fact tables on random samples.

To check the tests themselves, I planted two leaks in the feature SQL. Loosening the strict `>` on the route history to `>=` made `test_outcome_is_not_visible_at_the_instant_of_delivery` fail, and keying the seller history on purchase time instead of delivery time failed two more tests. The SQL was then restored.

## Limits

- Six test months and 59 test weeks are small samples; small gaps between models are inside the noise.
- The late-delivery model answers "if this order is delivered, will it be late?" (selection on delivery, as noted in the leakage analysis). 2-3% of each test month has no label.
- Hyperparameters are fixed, not tuned, and no feature importance or error analysis by state has been done. Calibration was checked by score quintile, for the logistic models only.
- Results use one train and test pipeline run with fixed seeds (`random_state=0`); scikit-learn 1.9.1.

## Suggested next steps

1. Done, with negative results: recalibration and a tuned training window did not beat v1 out-of-time ([RECALIBRATION_AND_WINDOW.md](RECALIBRATION_AND_WINDOW.md), DD-11). The model is to be used by rank, flagging a share of orders.
2. Do not add more history features; see [DRIFT_ANALYSIS.md](DRIFT_ANALYSIS.md). The one untried idea from the first list is the promised window relative to the route's typical delivery time, but the promise relationship itself is unstable.
3. For the forecast, try a damped-trend or exponential-smoothing model and a regression on calendar features, then compare against the 8-week average and the naive forecast with the same backtest.
4. Decide whether the segmentation experiment (DD-07) is worth running; the 96.9% single-order customers make it unlikely.
