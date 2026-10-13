# Recalibration and training window for the v1 late-delivery model

[DRIFT_ANALYSIS.md](DRIFT_ANALYSIS.md) suggested two fixes: recalibrate the predicted level on the most recent resolved orders, and use a short training window. Both were tested out-of-time. **Neither is adopted.** The month-to-month level of the late rate cannot be predicted from the recent past, so there is nothing for a recalibration to learn, and the window gain disappears once the window is chosen without hindsight.

Code: [src/ml/recalibration.py](../../src/ml/recalibration.py). Results: [reports/recalibration_metrics.json](../../reports/recalibration_metrics.json). Tests: [tests/test_recalibration.py](../../tests/test_recalibration.py). Same six test months as before (2018-03 to 2018-08), logistic regression on the v1 features, metrics averaged over months. Six months is a small sample, so read differences of a few thousandths as noise.

## R: recalibration on the latest resolved period

**Design.** For each test month the base model trains only on orders whose delivery was known before the calibration window starts, so the calibrator never sees in-sample predictions. The calibration set is the purchases from the one or two months that end 28 days before the test month, restricted to orders delivered before it starts. The gap matters: right after a cutoff only fast deliveries are labelled, which would make the recent late rate look too low. Three calibrators were tried: a single level shift on the logit scale (so the mean prediction matches the observed rate), a logit-scale intercept and slope (Platt), and isotonic regression. Tests confirm the split uses no outcome from inside the test month, and that planting a leak in it fails two tests.

| Variant | PR-AUC | Brier | Log loss | Mean prediction minus actual | Calibration error (quintiles) |
|---|---:|---:|---:|---:|---:|
| **Reference: trained up to the month start, uncalibrated** | **0.1837** | **0.0778** | **0.2818** | +0.014 | 0.063 |
| Base only, window 1 month, no calibration | 0.1755 | 0.0789 | 0.2874 | +0.007 | 0.064 |
| Base + level shift, 1 month | 0.1755 | 0.0794 | 0.3014 | +0.002 | 0.077 |
| Base + Platt, 1 month | 0.1755 | 0.0801 | 0.3022 | +0.002 | 0.077 |
| Base + isotonic, 1 month | 0.1666 | 0.0801 | 0.3063 | +0.003 | 0.077 |
| Base only, window 2 months | 0.1657 | 0.0800 | 0.3004 | -0.002 | 0.061 |
| Base + level shift, 2 months | 0.1657 | 0.0789 | 0.2922 | +0.018 | 0.073 |
| Base + Platt, 2 months | 0.1657 | 0.0805 | 0.2941 | +0.018 | 0.076 |
| Base + isotonic, 2 months | 0.1560 | 0.0805 | 0.2952 | +0.018 | 0.075 |

**No variant beats the reference on Brier, log loss or calibration error.** Two effects work against recalibration:

1. **The recent late rate does not predict the next month's.** The calibration set's late rate against the test month's, for the 1-month window:

   | Test month | Late rate in calibration set | Late rate in test month |
   |---|---:|---:|
   | 2018-03 | 4.6% | 21.4% |
   | 2018-04 | 12.6% | 5.3% |
   | 2018-05 | 17.8% | 8.3% |
   | 2018-06 | 3.1% | 1.4% |
   | 2018-07 | 8.0% | 4.5% |
   | 2018-08 | 1.0% | 10.5% |

   The correlation across the six pairs is -0.18 (a tiny sample, but no sign of a relationship). This matches the drift analysis, where the month-to-month autocorrelation of the late rate was only 0.30 and the trailing rate's correlation with the next month was 0.08. A calibrator fitted to last period's level is effectively fitted to noise.
2. **The base model is staler.** Holding the most recent orders out for calibration means training on older data, and PR-AUC drops from 0.184 to 0.176 and 0.166. That alone costs more than the calibration gains.

Averaging the signed level error makes the shift look better than it is (+0.002): its monthly errors run from 0.01 to 0.14 in both directions, and the mean absolute monthly error is 0.077 for the shift against 0.061 for the reference. Platt and isotonic have more parameters to fit on about 6,000 to 13,000 calibration rows and are worse than the plain shift. Ranking is untouched by the monotone methods, as expected (the PR-AUC column only changes through the staler base model).

## W: choosing the training window

**Design.** The window is how many months of the most recent resolved orders v1 trains on. Hindsight (picking the best window by test score) is selection on the test set, so each test month instead chooses its window from the three months before it (walk-forward, by PR-AUC). The fixed windows are shown for comparison and are optimistic.

| Window | PR-AUC | Brier | Log loss |
|---|---:|---:|---:|
| 1 month | 0.1506 | 0.0823 | 0.4523 |
| 2 months (best in hindsight) | **0.2051** | 0.0796 | 0.3045 |
| 3 months | 0.1866 | 0.0785 | 0.2852 |
| 4 months | 0.1859 | 0.0790 | 0.2820 |
| 6 months | 0.1825 | 0.0818 | 0.2913 |
| All history (current) | 0.1837 | **0.0778** | **0.2818** |
| **Walk-forward choice** | 0.1941 | 0.0792 | 0.3027 |

The walk-forward gain over all history is +0.010 PR-AUC, and it is **not reliable**:

| Test month | Window chosen | PR-AUC, chosen | PR-AUC, all history | Difference |
|---|---|---:|---:|---:|
| 2018-03 | 3 months | 0.385 | 0.393 | -0.008 |
| 2018-04 | 4 months | 0.152 | 0.180 | -0.029 |
| 2018-05 | 6 months | 0.203 | 0.212 | -0.009 |
| 2018-06 | 6 months | 0.073 | 0.061 | +0.012 |
| 2018-07 | 2 months | 0.155 | 0.129 | +0.026 |
| 2018-08 | 2 months | 0.197 | 0.127 | **+0.070** |

- It wins in three months out of six and loses in the other three. The average gain (0.010) is smaller than the month-to-month spread (standard deviation 0.035), so it cannot be told apart from zero.
- Most of the gain is one month. August 2018 is when the promise-length relationship flipped (see the drift analysis), and a short window adapts to that. In stable months it loses.
- The chosen window jumps from month to month (3, 4, 6, 6, 2, 2 months), so the selection itself is noisy. Calibration also gets worse (Brier 0.0792 against 0.0778, calibration error 0.075 against 0.063).
- A 1-month window is clearly too little data (log loss 0.45).
- The 2-month window looks best (0.205) only in hindsight. With six test months, that is a selection effect, not evidence.

## Conclusions

- **Keep v1, trained on all resolved history.** No recalibration, no window tuning.
- **Use the model for ranking, and say so.** The level of its probabilities is not trustworthy in any single month (the mean prediction is off by about 0.06 on average, and by 0.14 in March 2018). What it supports is triage: flagging the riskiest 10% of orders gave 2.4 to 3.9 times the base late rate in five of the six months, and only 1.2 times in August 2018:

  | Month | Late rate | Precision, top 10% flagged | Share of late orders caught | Lift |
  |---|---:|---:|---:|---:|
  | 2018-03 | 21.4% | 50.6% | 23.7% | 2.4 |
  | 2018-04 | 5.3% | 20.8% | 39.1% | 3.9 |
  | 2018-05 | 8.3% | 23.2% | 28.1% | 2.8 |
  | 2018-06 | 1.4% | 5.0% | 36.6% | 3.7 |
  | 2018-07 | 4.5% | 12.4% | 27.7% | 2.8 |
  | 2018-08 | 10.5% | 12.5% | 12.0% | 1.2 |

- **Set the operating point by share flagged, not by a probability cut-off.** A fixed probability threshold would flag far too many orders in a high-rate month and almost none in a low-rate one.
- **What would fix the level is information the data does not have**: something observed at purchase that signals the current regime, such as carrier backlog or a changed promise policy. The late-delivery data cannot supply it.
- **Watch for promise-policy changes.** August 2018 shows that a change in how delivery dates are promised breaks the model's ranking; a monitor on the distribution of promised days would catch it.

## Limits

- Six test months, and a single dataset ending in 2018. The calibration findings rest on level errors in only six months.
- Logistic regression only; gradient boosting was not repeated.
- The window search covered 1, 2, 3, 4 and 6 months and everything; finer choices were not tried.
- The calibration gap (28 days) and windows (1 and 2 months) were fixed up front and not tuned.
