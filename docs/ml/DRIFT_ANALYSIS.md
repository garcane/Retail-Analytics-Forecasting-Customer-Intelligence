# Drift analysis: why the richer history features did not help

[PHASE2_BASELINES.md](PHASE2_BASELINES.md) left one explanation untested: the late rate shifts by regime, so route, category and trailing-rate features learn the training period and do not carry forward. This document tests it. The short answer is that it is **partly right and partly wrong**.

Code: [src/ml/drift_analysis.py](../../src/ml/drift_analysis.py). Results: [reports/drift_metrics.json](../../reports/drift_metrics.json). Run with `uv run python src/ml/drift_analysis.py` (a few minutes). All numbers are from the six-month backtest of the earlier document unless stated, so differences of about 0.005 PR-AUC are within noise.

## Verdict

| Claim | Verdict | Evidence |
|---|---|---|
| The trailing 28-day rate (v3) fails because it learns regime, and regimes do not persist | **Supported** | E1, lag check |
| Category history fails for the same reason | **Largely supported**, with the caveat that it is also just weak | E1, E2 |
| Route history (v2) fails for the same reason | **Not supported.** Route lateness is stable. It fails because it repeats what v1 already knows | E1, E2, E6 |
| Relative features (route minus system rate) rescue the history features | **Not supported**: small, consistent gain over v2, still no better than v1 | E4 |
| A system-wide level shift explains the loss of ranking quality | **Not supported.** A level shift hurts calibration, not ranking | E5 |
| The model suffers from drift | **Supported**, but in an ordinary v1 feature (promise length), most clearly in August 2018 | E1, E3, August check |

## What was done and what came out

### E1: single-feature skill, month by month

ROC-AUC of each feature on its own (0.5 means no skill), within each purchase month, against the same feature pooled across the whole training year. A feature that only tracks the regime looks good pooled and useless within a month.

| Feature | Pooled, train year | Mean within month, train | Pooled, test months | Mean within month, test | Lowest month |
|---|---:|---:|---:|---:|---:|
| Seller history rate | 0.556 | 0.540 | 0.503 | 0.527 | 0.467 |
| Route rate | 0.630 | 0.595 | 0.537 | 0.580 | 0.360 |
| Category rate | 0.565 | 0.519 | **0.380** | 0.482 | 0.456 |
| Trailing 28-day rate | 0.549 | **0.495** | 0.454 | **0.446** | 0.387 |
| Route rate minus system rate | 0.605 | 0.593 | 0.606 | 0.592 | 0.362 |
| Promised days (a v1 feature) | 0.503 | 0.487 | 0.411 | 0.403 | **0.186** |
| Distance (a v1 feature) | 0.573 | 0.554 | 0.551 | 0.554 | 0.273 |

- **Trailing rate:** it is worse than a coin flip within a month (0.495 in training, 0.446 in testing), and its pooled training skill (0.549) therefore comes entirely from differences between months. After a spike, the next month tends to be lower, so the feature points the wrong way. This is the regime-memorisation pattern.
- **Category rate:** no within-month skill (0.519, then 0.482), and pooled over the test months it is clearly inverted (0.380).
- **Route rate:** real within-month skill (0.52 to 0.69 in 16 of 18 months). Part of its pooled training skill (0.630 against 0.595) is between-month, but most is not.
- **August 2018 inverts almost everything**: route rate 0.360, promised days 0.186, distance 0.273. See the next section.

### August 2018 is a change in promise policy, not a label problem

I first suspected missing labels, since the data ends 2018-10-17. That is not it: only 1.2% of August's non-canceled orders have no label. What changed is the promised window:

| Purchase month | Share of orders promised in under 20 days | Late rate of those | Late rate of 30+ day promises |
|---|---:|---:|---:|
| 2018-04 | 28% | 4.1% | 5.4% |
| 2018-05 | 37% | 10.6% | 2.5% |
| 2018-06 | 18% | 1.9% | 1.0% |
| 2018-07 | 48% | 5.7% | 1.5% |
| 2018-08 | **72%** | **13.9%** | 0.0% |

In August nearly all lateness sits in the short promises (their average promise is 11 days), so a shorter promise means a later delivery. The direction varied in earlier months: April ran the other way, May and July resembled August more mildly, June was flat. This is concept drift in a plain v1 feature, and it is what makes August the weakest month for every model. Why the promise policy changed is not in the data.

### E2: does a route's, category's or seller's lateness persist?

Spearman correlation, across keys with enough orders, of lateness in one period against the next. "Relative" subtracts the month's overall late rate first. The ceiling is two random halves of the same period, which shows how much agreement noise alone allows.

| Key | P1 to P2 (absolute / relative) | P2 to P3 (absolute / relative) | Ceiling (absolute / relative) |
|---|---|---|---|
| Route (27, 39, 40 keys) | 0.18 / 0.23 | **0.70 / 0.71** | 0.85 / 0.83 |
| Category (28, 32, 31 keys) | 0.05 / 0.04 | 0.26 / 0.17 | 0.61 / 0.62 |
| Seller (69, 86, 140 keys) | 0.07 / 0.08 | 0.45 / 0.39 | 0.45 / 0.48 |

P1 is March to August 2017, P2 is September 2017 to February 2018, and P3 is March to August 2018.

- **Routes are stable from P2 to P3**, close to the noise ceiling. Absolute and relative agree, which does not fit the idea that route lateness is just the system's regime.
- **Categories are not**, and sellers persist from P2 to P3 but not from P1 to P2.
- **P1 predicts nothing for anything.** P1 is the early, small-volume 2017 period, with few keys passing the order threshold (27 routes). Treat the P1 column as weak evidence either way.

### E3 and E4: shorter training windows, and relative features

Logistic regression, macro PR-AUC over the six test months (the last column leaves out August). Window is how many months of training data precede each test month.

| Window | v1 | v2 | v3 | v4 (relative) | v1 without August |
|---|---:|---:|---:|---:|---:|
| 2 months | **0.205** | 0.198 | 0.172 | 0.203 | 0.207 |
| 3 months | 0.187 | 0.169 | 0.174 | 0.179 | 0.192 |
| 6 months | 0.183 | 0.181 | 0.180 | 0.183 | 0.195 |
| All history | 0.184 | 0.174 | 0.177 | 0.176 | 0.195 |

- **Shorter windows help v1 itself** (0.205 with two months against 0.184 with everything). Even the ordinary features' relationship to lateness changes over time, which is the clearest evidence of drift. The cost is a small, noisy training set.
- **No window makes history features beat v1.** At best they tie it (v4 at six months).
- **Relative route and category rates (v4) beat v2 in all four windows** by 0.002 to 0.011. That favours expressing history relative to the system, but it is small and still not an improvement on v1.
- **Leaving out August** roughly halves v3's gap to v1 (0.0066 with August, 0.0036 without: 0.191 against 0.195) and leaves v2's unchanged (0.186 against 0.195). August is part of the story for v3 and none of it for v2.

### E5: what a perfect regime signal would buy

I gave the model the true late rate of the purchase month. This is **not** available at purchase and is a ceiling, not a feature.

| Model | PR-AUC | Brier |
|---|---:|---:|
| v1 | 0.1837 | 0.0778 |
| v1 + true month rate | 0.1839 | **0.0711** |
| v3 + true month rate | 0.1784 | 0.0726 |

Ranking does not move at all, while Brier drops by 9%. This is expected: PR-AUC is computed within each month, and a month-level number cannot reorder orders inside a month. System-level drift is therefore a **calibration** problem (the predicted level is wrong), not a ranking problem. It also means the top-quintile over-confidence seen earlier is at least partly a level shift. The trailing rate cannot supply that signal: the correlation between it at the start of a month and the month's actual rate is 0.08, and the month-to-month autocorrelation of the late rate is only 0.30.

### E6: is route history redundant with the state and distance columns?

| Model | PR-AUC | PR-AUC without August |
|---|---:|---:|
| v1 (states and distance) | **0.184** | **0.195** |
| v1 without states and distance | 0.117 | 0.112 |
| ... plus route history | 0.151 | 0.161 |
| v1 plus route history | 0.175 | 0.186 |

Take away the geography and route history is valuable: it recovers half of the lost 0.067. But on top of the full v1 it **lowers** PR-AUC by about 0.009. So route history is informative and stable (E1, E2), yet already present in v1's seller state, customer state and distance, and its extra copy adds noise. That is the better explanation for v2.

## What this changes

- **DD-10 stands**: v1 remains the reference. The reasons recorded there are refined: v3 and category history fail because of regime (and, for category, weak signal), route history because of redundancy.
- **Do not add more history features.** Neither drift nor redundancy suggests they will help; the one route-history gain needs the geography removed.
- **Fix the level, not the ranking.** The oracle shows that a correct month-level rate recovers calibration. A recalibration step fitted on the most recent resolved period is the cheapest next test (it cannot use the true month rate, so how much it recovers is open).
- **Treat promise length as unstable.** Its relationship to lateness flipped by month. A short training window (E3) helps v1 and is worth tuning, but with six test months the size of the gain is uncertain.

## Limits

- Six test months. A difference of 0.005 PR-AUC between two models is inside the noise, and the August month alone moves the averages.
- E2 uses few keys (27 to 140 per cell), and the P1 period is small and early.
- Tests were run on logistic regression only. Gradient boosting was not repeated.
- "Regime" here means month-level variation. Weekly or carrier-specific shifts would not show up in these checks.
- The cause of the August change in promise policy is not known.
- The route and category keys in the analysis are rebuilt by a separate query that mirrors the feature SQL; they are used only for diagnostics.
