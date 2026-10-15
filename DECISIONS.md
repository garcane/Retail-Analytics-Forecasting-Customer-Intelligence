# Decisions

The decision log for the local DuckDB build. Each entry follows the template in the project brief. **User decisions** (D-001 to D-008) were made by the project owner. **Design decisions** (DD-01 onwards) were made while building the warehouse, and each one names the evidence behind it.

Later decisions can supersede earlier ones; when that happens the entry says so. The original cloud brief (`Cloud Portfolio — Master Agent Prompt.md`, `GCP.md`, the Retail Analytics project document) is kept unchanged on purpose, so where a decision below contradicts it, the decision wins.

| ID | Date | Decision | Status |
|---|---|---|---|
| D-001 | 2026-10-06 | Implementations use DuckDB | Active (the cloud-phase part is superseded by D-002, the portability part by D-003) |
| D-002 | 2026-10-10 | Local only, no GCP | Active |
| D-003 | 2026-10-10 | Idiomatic DuckDB SQL | Active |
| D-004 | 2026-10-10 | No dbt; plain SQL run by a Python script | Active |
| D-005 | 2026-10-10 | No Prometheus, Grafana or FastAPI | Active |
| D-006 | 2026-10-10 | `.gitignore` covers the database, `data/` and credentials | Active |
| D-007 | 2026-10-11 | ML target: late delivery, plus a weekly order forecast | Active |
| D-008 | 2026-10-11 | Untrack `data/` from Git; do not rewrite history | Done (commit `d8f6954`) |
| DD-01 | 2026-10-10 | Kimball star schema; facts never join to facts | Active |
| DD-02 | 2026-10-10 | Customer grain is `customer_unique_id` | Active |
| DD-03 | 2026-10-10 | Reviews keyed on (`review_id`, `order_id`) with a latest-review flag | Active |
| DD-04 | 2026-10-10 | Revenue is measured from order items only | Active |
| DD-05 | 2026-10-10 | Surrogate keys with an unknown member (-1) | Active |
| DD-06 | 2026-10-10 | Convert geolocation CSV to Parquet in the build | Active |
| DD-07 | 2026-10-11 | Customer segmentation is optional and may be dropped | Active |
| DD-08 | 2026-10-11 | Add scikit-learn for the ML baselines | Active |
| DD-09 | 2026-10-11 | Report backtest metrics as a per-month macro-average | Active |
| DD-10 | 2026-10-11 | Keep v1 features as the reference late-delivery model | Active |
| DD-11 | 2026-10-13 | No recalibration or window tuning; use the model by rank | Active |
| DD-12 | 2026-10-13 | Close the late-delivery feature search; v1 is final. Forecast: recommend the simple averages | Active |
| DD-13 | 2026-10-13 | Present the ML in Jupyter notebooks that call the tested `src/ml` code | Active |
| DD-14 | 2026-10-13 | Add interactive marimo versions of the ML notebooks, keeping the Jupyter ones | Active |

---

## User decisions

### D-001: Implementations use DuckDB

- **Context:** The brief targets BigQuery, but the whole dataset is about 80 MB and fits in memory. Development needed a local engine for the warehouse, data-quality checks and tests.
- **Options:** DuckDB; SQLite; pandas or polars only; BigQuery from the start.
- **Chosen:** DuckDB.
- **Reason:** It is a columnar analytical engine with a SQL dialect close to BigQuery's, it reads CSV and Parquet directly, and it needs no server.
- **Trade-offs:** BigQuery-only features (partitioning, clustering, `INFORMATION_SCHEMA` jobs, slot pricing) cannot be shown.
- **Cost:** $0.
- **Security:** Data never leaves the machine.
- **Rejected:** SQLite (row store, weak analytics functions); pandas only (no SQL model to show); BigQuery first (cost and credentials before the model was known).
- **Superseded in part:** the original wording said BigQuery features would be shown in a cloud phase (removed by D-002) and that SQL should stay BigQuery-portable (removed by D-003).

### D-002: Local only

- **Context:** The cloud phase would need a GCP project, billing, IAM and `gcloud`. None of it is needed to show the data model and ML work.
- **Options:** Local then cloud (the brief); local with emulators; local only.
- **Chosen:** Local only. DuckDB stands in for Google Cloud and BigQuery. No GCP project, no `gcloud`, no cloud phase.
- **Reason:** Removes cost, credential risk and setup time.
- **Trade-offs:** No cloud deployment to show. Dataflow/Beam and the BigQuery region question become moot. Cloud pricing in Phase 0 stays unverified.
- **Cost:** $0.
- **Security:** No service accounts or keys exist, so none can leak.
- **Rejected:** Local then cloud (cost and scope); emulators (they add setup without adding evidence for this project).

### D-003: Idiomatic DuckDB SQL

- **Context:** D-001 asked for BigQuery-portable SQL. That rules out convenient DuckDB functions and makes the SQL harder to read.
- **Options:** Portable SQL; idiomatic DuckDB SQL.
- **Chosen:** Idiomatic DuckDB SQL.
- **Reason:** With no cloud phase (D-002), portability has no user. The translation work is listed in [docs/data/DATA_MODEL.md](docs/data/DATA_MODEL.md#moving-to-bigquery) if it is ever needed.
- **Trade-offs:** A move to BigQuery would need dialect translation, not copy-paste.
- **Cost / Security:** None.
- **Rejected:** Portable SQL.

### D-004: No dbt

- **Context:** The shared architecture notes ([docs/architecture-philosophy.md](docs/architecture-philosophy.md)) favour dbt.
- **Options:** dbt with the DuckDB adapter; plain SQL files run by a script.
- **Chosen:** Plain SQL files under `sql/`, run in a fixed order by `src/transformation/build_warehouse.py`.
- **Reason:** Fewer moving parts. The build order is small and explicit.
- **Trade-offs:** No dbt lineage graph, docs site or built-in `unique`, `not_null` and `relationships` tests. Table constraints (primary and foreign keys) and `sql/validation/checks.sql` cover the same ground.
- **Cost / Security:** None.
- **Rejected:** dbt.

### D-005: No Prometheus, Grafana or FastAPI

- **Context:** The brief includes a monitoring stack and a serving API.
- **Chosen:** None of them.
- **Reason:** There is no long-running service to monitor or serve. The build is a batch job that either passes its checks or exits non-zero.
- **Trade-offs:** No live dashboards or prediction endpoint. Model outputs will be files and notebook results.
- **Cost / Security:** None; no network ports are opened.
- **Rejected:** A Docker monitoring stack; a FastAPI prediction service.

### D-006: `.gitignore` coverage

- **Context:** Phase 0 found no `.gitignore`, with `data/` tracked in Git.
- **Chosen:** Ignore `*.duckdb`, `*.duckdb.wal`, `data/`, `.env*`, `*.pem`, `*.key`, service-account and credential JSON files, and caches.
- **Reason:** The database is rebuilt from source; the raw data is re-downloadable; credentials must never be committed.
- **Security:** Blocks the common credential file patterns, although none are expected in this project.

### D-007: ML target is late delivery, plus a weekly forecast

- **Context:** Phase 0 §7 proposed three supervised candidates (low review score, late delivery, repeat purchase) and recommended low review score or late delivery, plus a weekly forecast.
- **Options:** Low review score (1-2 stars); late delivery; repeat purchase.
- **Chosen:** **Late-delivery classification** (one order, predicted at purchase) and a **weekly order-count forecast** (revenue secondary). Full definitions and the leakage audit are in [docs/ml/LEAKAGE_ANALYSIS.md](docs/ml/LEAKAGE_ANALYSIS.md).
- **Reason:** The late-delivery label comes straight from timestamps, with no dependence on reviews. The features available at purchase are concrete: seller, product size, freight, the seller-to-customer route and the promised delivery window. It also drives the review outcome, since late orders average 2.57 stars against 4.29 for on-time orders. The forecast uses the 87-week window found in Phase 0.
- **Trade-offs:** The positive class is 8.1%, so accuracy is meaningless and the model needs precision-recall metrics. Low review score is left as possible later work.
- **Cost / Security:** None.
- **Rejected:** Low review score (it depends on delivery outcomes, so its features overlap with post-outcome data and the leakage risk is highest); repeat purchase (about 3.1% positives in a short, censored window).

### D-008: Untrack `data/`

- **Context:** Nine raw files were tracked before D-006 added `data/` to `.gitignore`. Pushing them redistributes a CC BY-NC-SA dataset, and the brief says not to commit large raw datasets.
- **Options:** Leave tracked; untrack; untrack and rewrite history.
- **Chosen:** Untrack with `git rm -r --cached data/`. The files stay on disk. History is not rewritten.
- **Reason:** Stops future commits carrying the data without a destructive history rewrite.
- **Trade-offs:** Earlier commits still contain the files. If the repository is made public, those commits still expose the data, though with attribution under the same licence that is permitted.
- **Security:** No secrets were ever in `data/`.
- **Rejected:** History rewrite (needs a force-push and breaks existing clones).

---

## Design decisions

Evidence for these entries is in [docs/data/EDA_FINDINGS.md](docs/data/EDA_FINDINGS.md) and [docs/data/DATA_MODEL.md](docs/data/DATA_MODEL.md).

### DD-01: Kimball star schema; facts never join to facts

- **Context:** Items, payments and reviews hang off `order_id` at different grains. In the EDA, joining them side by side overstated item revenue by 4.54%, or 5.02% with reviews.
- **Options:** One wide order table; a star schema with one grain per fact.
- **Chosen:** Four facts (`fact_order_items`, `fact_orders`, `fact_payments`, `fact_reviews`) and five dimensions. Each table states its grain. Facts meet only through shared dimensions or after aggregation to a common grain; `fact_orders` pre-aggregates items and payments.
- **Trade-offs:** Some queries need two steps (aggregate, then join).
- **Rejected:** A wide table (silent fan-out).

### DD-02: Customer grain is `customer_unique_id`

- **Context:** `customer_id` is issued per order: 99,441 ids belong to 96,096 people.
- **Chosen:** `dim_customer` at the `customer_unique_id` grain. Location at the time of the order is carried on the facts, because 250 customers changed location.
- **Rejected:** `customer_id` (every customer would look like a one-time buyer).

### DD-03: Reviews keyed on (`review_id`, `order_id`)

- **Context:** `review_id` is not unique (789 ids span several orders), and 547 orders have 2-3 reviews.
- **Chosen:** `fact_reviews` grain is (`review_id`, `order_id`), with an `is_latest_review_for_order` flag to use before relating reviews to orders.
- **Rejected:** Deleting duplicates (that loses source rows).

### DD-04: Revenue from order items only

- **Context:** Payments differ from items plus freight on 380 of 98,665 orders, mostly instalment orders.
- **Chosen:** Revenue is `fact_order_items.price` (or `item_total_value` when freight is included). `fact_payments` is analysed on its own and never forced to tie.
- **Rejected:** Payment value as revenue; reconciling the two by adjustment.

### DD-05: Surrogate keys with an unknown member

- **Context:** 279 customer rows have a zip prefix that is missing from geolocation, and some milestone dates are null.
- **Chosen:** Deterministic surrogate keys (`row_number()` over the natural key) and a `-1` unknown member in every dimension, so a failed lookup never drops a fact row. `dim_date` uses `yyyymmdd` keys, with `-1` meaning "not applicable".
- **Rejected:** Inner joins that drop rows; null foreign keys.

### DD-06: Convert geolocation CSV to Parquet in the build

- **Context:** Kaggle ships geolocation as a CSV (about 1M rows), but staging reads Parquet.
- **Chosen:** `ensure_geolocation_parquet` in `build_warehouse.py` converts the CSV once if the Parquet file is missing. It keeps zip prefixes as text so leading zeros survive.
- **Trade-offs:** Not yet tested against Kaggle's original download (see [README.md](README.md)).

### DD-07: Customer segmentation is optional

- **Context:** 96.9% of customers ordered once, so frequency-based clusters carry little information (Phase 0 §7).
- **Chosen:** K-Means segmentation is tried honestly and dropped if it adds little. It is not a committed deliverable.
- **Rejected:** Committing to RFM segmentation up front.

### DD-08: Add scikit-learn

- **Context:** Phase 2 needs a logistic regression and a gradient-boosting baseline. Neither was installed.
- **Options:** scikit-learn; hand-written numpy models; only rate-based baselines.
- **Chosen:** scikit-learn 1.9.1 (adds scipy, joblib, threadpoolctl; recorded in `pyproject.toml` and `uv.lock`).
- **Reason:** Standard, well-tested implementations. A baseline that has to be debugged is a poor baseline.
- **Trade-offs:** Larger environment. statsmodels, lightgbm and xgboost were not added; the forecast baselines use numpy only.
- **Cost / Security:** None beyond a PyPI install.
- **Rejected:** Hand-written models; rate baselines only (they cannot show what a feature-based model adds).

### DD-09: Macro-average of per-month metrics

- **Context:** The late-delivery backtest refits the models for each test month. A first version pooled all test orders, which gave the constant baseline a ROC-AUC of 0.36, because pooling ranks the different months' constants against each other.
- **Chosen:** Compute each metric per test month and report the mean, with the per-month table beside it.
- **Reason:** Each month is scored by a model trained at one date, and the late rate moves a lot from month to month (1.4% to 21.4%).
- **Trade-offs:** Months with fewer orders count as much as larger ones.
- **Rejected:** Pooled metrics (misleading, as above).

### DD-10: v1 features stay the reference model

- **Context:** Route and category history (v2) and a trailing 28-day system late rate (v3) were added to the late-delivery model as the most promising improvement. Neither helped: logistic-regression PR-AUC fell from 0.184 to 0.174 and 0.178, and calibration at the top of the score range got worse (see [docs/ml/PHASE2_BASELINES.md](docs/ml/PHASE2_BASELINES.md)).
- **Chosen:** v1 (calendar, promise, basket, route geometry, payment, seller history) stays the reference. The v2 and v3 features stay in the SQL and the script, so the comparison can be rerun.
- **Reason:** A model should not get more complex without a measured gain.
- **Trade-offs:** The drift explanation was tested afterwards ([docs/ml/DRIFT_ANALYSIS.md](docs/ml/DRIFT_ANALYSIS.md)) and holds only in part: v3 and category history fail because they track regime, route history fails because it repeats the state and distance columns already in v1.
- **Rejected:** Adopting v3 because it uses more information; deleting v2 and v3 and losing the record of what was tried.

### DD-11: No recalibration or window tuning; use the model by rank

- **Context:** The drift analysis suggested recalibrating v1 on the latest resolved orders and shortening its training window. Both were tested out-of-time ([docs/ml/RECALIBRATION_AND_WINDOW.md](docs/ml/RECALIBRATION_AND_WINDOW.md)).
- **Findings:** Recalibration made Brier, log loss and calibration error worse in every variant: the late rate of the recent past did not predict the next month's (correlation -0.18 over six pairs), and holding orders out for calibration made the base model staler. Choosing the window walk-forward gained +0.010 PR-AUC, but in only three of six months, mostly from August 2018.
- **Chosen:** v1 trained on all resolved history, uncalibrated. The model is described and used as a **ranker**: the operating point is a share of orders flagged (for example the riskiest 10%), not a probability threshold. Its probabilities are not to be quoted as absolute risks.
- **Reason:** A change is only adopted when it beats the reference out-of-time. Neither did.
- **Trade-offs:** The level of the predicted probabilities stays off by about 0.06 on average per month (0.14 in March 2018). Short-window adaptation after a policy change such as August 2018 is left for monitoring, not built.
- **Rejected:** Platt, isotonic and level-shift recalibration; a fixed 2-month window (looked best only in hindsight); a probability cut-off for flagging.

### DD-12: Close the ML experiments; v1 and the simple forecasts are final

- **Context:** After the history features (DD-10) and recalibration and windows (DD-11), one more idea remained: the slack between the promised delivery time and how long deliveries have actually been taking (per route, and system-wide over 28 days). For the weekly forecast, exponential smoothing, a damped trend and an AR(1)-with-trend regression were the untried options.
- **Findings:** The slack features did not beat v1 (logistic PR-AUC 0.176 against 0.184, Brier equal; top-quintile calibration somewhat closer: 0.191 predicted against 0.165 actual, from 0.215). None of the forecast models clearly beat the simple averages; the ranking of the more complex ones flips between orders and revenue, so the 85-week backtest cannot separate them. See [docs/ml/MODEL_CARD.md](docs/ml/MODEL_CARD.md).
- **Chosen:** v1 is the final late-delivery model, used by rank. For the forecast: the average of the naive and 8-week-average forecasts at one week, and the 8-week average at four weeks, with the caveat that the combination was assembled after seeing the baseline results.
- **Reason:** Four feature ideas and two post-hoc fixes have been tried against the same six test months. Continuing would mostly fit noise in that sample. The remaining brief phases (analytics, documentation, audit) matter more than another 0.005 of PR-AUC.
- **Trade-offs:** The ranking is moderate (lift about 2.8 times at the top 10%) and probabilities remain unreliable in level. A better model would need information this dataset does not contain.
- **Rejected:** Further feature search on the same test months; selecting a forecast model from a single 59-week backtest.

### DD-13: ML presented in notebooks that call the tested code

- **Context:** The ML work existed as scripts and JSON metrics. The project owner wanted to see the output as charts, in a notebook.
- **Options:** Jupyter notebooks; marimo notebooks; a static report generated from the scripts.
- **Chosen:** Two Jupyter notebooks (`02_late_delivery_model`, `03_weekly_forecast`) that import the existing modules from `src/ml/` and draw the results, stored with their outputs.
- **Reason:** Jupyter fits the existing discovery notebook and the declared `ipykernel`, and the logic stays in code that has tests. Marimo would add a dependency and a second file format for little gain here.
- **Trade-offs:** Stored outputs make the notebooks large (about 0.4 to 0.6 MB each) and can go stale if the code changes; a test checks that they were run without errors, but not that their numbers still match. The notebooks were built and executed with a throwaway script that is not part of the repository.
- **Cost / Security:** None. `nbformat` and `nbclient` are development dependencies.
- **Rejected:** Re-implementing the models inside the notebooks (duplicates tested logic); marimo (revisit if reactive notebooks are wanted).

### DD-14: marimo notebooks alongside the Jupyter ones

- **Context:** The project owner wanted the ML notebooks in marimo as well. DD-13 had chosen Jupyter, and the reasons for it (stored charts, familiar format) still hold.
- **Options:** Replace the Jupyter notebooks; keep both; convert cell for cell without changes.
- **Chosen:** Keep both. The marimo versions are `notebooks/marimo/02_late_delivery_model.py` and `03_weekly_forecast.py`, rewritten by hand rather than auto-converted, with interactive controls added.
- **Reason:** marimo forbids defining a variable in two cells, and the Jupyter cells reuse names such as `fig`, `ax` and `x`, so a mechanical conversion would not run. The rewrite wraps each chart in its own cell with private variables, and adds what marimo is good for: a test-month picker, a "flag the riskiest X%" slider, a measure picker, a feature picker, a button for the one-minute permutation importance, and target, horizon and method pickers for the forecast.
- **Trade-offs:** Two copies of each notebook to keep in step (both call the same `src/ml` code, so only the presentation can diverge). marimo files store no outputs, so the Jupyter versions stay the quick way to see the charts without running anything.
- **Cost / Security:** None. `marimo` is a development dependency (it opens a local server only when run).
- **Verification:** `marimo check` is part of the test suite; both notebooks were also executed headlessly (`marimo export html`) with no cell errors, and the interactive charts were inspected by eye.
- **Rejected:** Replacing the Jupyter notebooks (loses the stored charts); a mechanical `marimo convert` (does not run as is).

### DD-15: Power BI delivered specification-first from one definition

- **Context:** The project owner wanted a Power BI dashboard, delivered in order: an HTML DAX specification, then an HTML mock-up, then a Power BI Project built from both. Power BI Desktop is not available where the project is built, and no .NET tooling exists to parse the model files.
- **Options:** Write the three deliverables by hand; generate all three from one Python definition; ship only a specification and mock-up.
- **Chosen:** `src/powerbi/model_spec.py` holds the tables, relationships, measures (DAX, format, the SQL each mirrors, expected value), checks, pages and visuals. Three generators produce `docs/powerbi/DAX_SPECIFICATION.html`, `docs/powerbi/DASHBOARD_MOCKUP.html` and `powerbi/RetailAnalytics.pbip` (TMDL semantic model plus PBIR report). Data is exported as Parquet (large facts and the model scores) and CSV (dimensions and small tables) and loaded through a `DataFolder` parameter, because Power Query needs absolute paths.
- **Reason:** One source means the specification, mock-up and project cannot disagree, and a changed measure is a one-place edit. Expected values computed by SQL give the owner a checklist to confirm the DAX once opened in Desktop.
- **Trade-offs:** The first open in Desktop failed on a case-insensitive name clash (measure `Forecast` vs column `forecast`), fixed by renaming and by a new test; further first-open fixes are possible; edits made in Desktop are overwritten if the generator is run again. The mock-up re-implements the measures in JavaScript and is a picture, not a DAX engine (some measures are approximate under a partial selection and say so on the page).
- **Verification instead of Desktop:** every JSON file validates against Microsoft's published schemas; cross-reference tests check every name; the exported data reproduces warehouse and model figures; the mock-up's data sums to the specification's expected values; output is deterministic. Field references use `Entity`, which the schema defines for stored references (`Source` is only for aliases inside a query).
- **Cost / Security:** None; Desktop is free and the project holds no credentials. Review comment text is not exported.
- **Rejected:** Hand-written project files (drift between the three); a `.pbix` (binary, cannot be generated or reviewed as text); custom visuals (extra dependencies, no benefit).
