# Lessons learned

What this project taught, in the order the lessons mattered. Each one points at the evidence.

## About the data

1. **Check grain before anything else.** The dataset's keys do not mean what their names suggest: `customer_id` is per order (99,441 ids for 96,096 people), and `review_id` is not unique. Joining the child tables side by side overstated revenue by 5%. The fix was a rule, not a patch: facts never join to facts, and every table states its grain ([DATA_MODEL.md](data/DATA_MODEL.md), DD-01 to DD-03).
2. **Reconciliation checks pay for themselves.** Twenty-two checks run on every build and fail it loudly. They caught nothing dramatic, which is the point: they are why the analytics tables could be tied back to the facts with no surprises ([tests/test_analytics.py](../tests/test_analytics.py)).
3. **Data ends in ragged ways.** The last weeks of the extract are truncated, and the earliest months are tiny. Both are documented exclusions, not silent deletions, and the weekly forecast depends on getting the edges right ([LEAKAGE_ANALYSIS.md](ml/LEAKAGE_ANALYSIS.md)).

## About modelling

4. **Define the prediction moment first, then the features.** Writing the leakage audit before any model (purchase time, column by column) removed a whole class of mistakes. The late-delivery label, for example, is built from the very timestamps that would have leaked.
5. **"Point-in-time" means by outcome time, not by purchase time.** A past order still in transit has no outcome yet. Getting this wrong makes history features look better than they are. It is easy to get wrong and was worth a mini-warehouse of hand-built orders to test ([tests/test_feature_leakage.py](../tests/test_feature_leakage.py)).
6. **A weak model honestly reported beats a strong one that leaks.** The best late-delivery model ranks orders about 2.8 times better than chance at the top 10%. Four feature ideas, two fixes and several models did not beat the first simple model, and the project says so ([MODEL_CARD.md](ml/MODEL_CARD.md), DD-10 to DD-12).
7. **Pooled metrics can mislead.** A first backtest pooled all test months and gave a constant "predict the average" model a ROC-AUC of 0.36, because pooling ranks different months' constants against each other. Per-month metrics fixed it (DD-09).
8. **Test the explanation, not just the result.** "Drift" was a plausible story for why features failed. Testing it showed part right (the recent late rate does not carry forward), part wrong (route history is stable but redundant), and revealed something I had not looked for: the delivery promise changed sharply in August 2018 ([DRIFT_ANALYSIS.md](ml/DRIFT_ANALYSIS.md)).
9. **Do not choose a setting by test score.** A two-month training window looked best (PR-AUC 0.205) until each month had to choose its own window from earlier months, when the gain shrank to noise ([RECALIBRATION_AND_WINDOW.md](ml/RECALIBRATION_AND_WINDOW.md)).
10. **Small samples cannot rank similar models.** On 59 weekly forecasts a regression was among the best models for revenue and among the worst for orders. The honest conclusion was to recommend the simple averages ([MODEL_CARD.md](ml/MODEL_CARD.md)).

## About process

11. **Decide the scope early and write it down.** Moving from a BigQuery build to a local DuckDB build, and dropping dbt, Prometheus and FastAPI, was cheap because the decisions were logged (D-001 to D-006) and the original brief was left intact.
12. **Tests should be able to fail.** For the leakage rules I planted deliberate leaks in the SQL and confirmed the tests caught them, then restored the file. A test that has never failed has not been shown to work.
13. **Check your own write-ups against the output.** Several figures in early drafts were transcribed or summarised wrongly (a percentage here, "most of the low scores" there). Checking every number against the saved tables before committing caught them. The insights document's claim that late orders account for most low review scores was wrong: on-time orders produce about 70% of them, simply because there are more.
14. **Tooling can quietly cost time.** A shell command that waits on stdin, a heredoc that does not parse, and a dependency manager behind a TLS-intercepting network each cost minutes. Writing scripts to files and timing long steps avoided most of it.

## What I would do differently

- Profile the **promise policy** (the delivery estimate) in discovery, not only the delivery outcome. It turned out to be the most important moving part of the dataset.
- Start the analytics layer in parallel with the warehouse, since the business questions would have shaped the data model earlier.
- Keep one results log from the first experiment, instead of reconstructing it from reports at the end.
