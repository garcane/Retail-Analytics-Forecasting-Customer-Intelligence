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
```

The first takes about 40 seconds (feature query plus 6 monthly refits of 2 models) and the second about 3 seconds, measured on this laptop. Both open the warehouse read-only. The runs here used the project's `.venv` directly, which gives the same results as `uv run`.

## Target A: late delivery

**Setup.** 96,282 delivered orders, 8.13% late. Features are the allowed and point-in-time columns of the audit, 16 numeric and 3 categorical: calendar, promised delivery days, basket, product weight and volume, distance and states between seller and customer, payment, and the seller's late rate over orders already delivered before this purchase. `purchase_month` is left out on purpose, because with under two years of history it can only memorise calendar months.

**Split.** Monthly rolling origin over 2018-03 to 2018-08. For each test month the models train on orders purchased from 2017-01-01 whose delivery date falls before the month starts, so no training label was resolved inside the test period. Metrics are averaged over the six months and not pooled, because a pooled ROC-AUC would rank scores from models trained at different dates.

**Macro-average over the six test months** (38,988 test orders):

| Model | PR-AUC | ROC-AUC | Brier | Precision, top 10% flagged | Recall, top 10% flagged |
|---|---:|---:|---:|---:|---:|
| Constant (training late rate) | 0.085 | 0.500 | 0.0792 | 0.106* | 0.106* |
| Seller's own history rate | 0.099 | 0.526 | 0.0817 | 0.102 | 0.123 |
| Logistic regression | **0.184** | **0.707** | **0.0778** | **0.207** | **0.279** |
| Gradient boosting (depth 4) | 0.172 | 0.671 | 0.0796 | 0.196 | 0.259 |

The base rate averages 8.5% over these months. *A constant score has no ranking; its top-10% figures only show how ties fell and should read as the base rate.

**PR-AUC by month:**

| Month | Late rate | Unlabelled orders | Constant | Seller history | Logistic | Boosting |
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
- **Calibration barely improves.** Brier scores are almost equal across models because 8% positives dominate, and calibration itself has not been checked.
- **The last month is the weakest.** In 2018-08 logistic regression barely beats the base rate (0.127 against 0.105) and boosting falls below it. With six test months this is a hint of drift, not a finding.

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

## Limits

- Six test months and 59 test weeks are small samples; small gaps between models are inside the noise.
- The late-delivery model answers "if this order is delivered, will it be late?" (selection on delivery, as noted in the leakage analysis). 2-3% of each test month has no label.
- Hyperparameters are fixed, not tuned, and no calibration, feature importance or error analysis by state has been done.
- Results use one train and test pipeline run with fixed seeds (`random_state=0`); scikit-learn 1.9.1.

## Suggested next steps

1. Add features with a better chance of carrying signal: product category (grouped), seller and customer region pairs as point-in-time route late rates, and the length of the promised window relative to the route's typical delivery time.
2. Check calibration and decide on an operating threshold for the "flag the riskiest 10%" use.
3. For the forecast, try a damped-trend or exponential-smoothing model and a regression on calendar features, then compare against the 8-week average and the naive forecast with the same backtest.
4. Decide whether the segmentation experiment (DD-07) is worth running; the 96.9% single-order customers make it unlikely.
