# Final audit (Phase 10)

Audit of the local DuckDB build against the review areas in the project brief, run on 2026-10-13 at commit `578c46f` plus the clean-up listed below. Each verdict says what was actually checked. Where something could not be checked, it says so.

**Scope.** The brief's cloud phases (3 cloud foundation, 7 deployment, 8 monitoring) are out of scope by decision (D-002, D-005), so they are not audited here. Phase 4 (data engineering), 5 (analytics), 6 (ML), 9 (documentation) and the discovery, architecture and prototype phases are.

## Summary

| Area | Verdict |
|---|---|
| Correctness | **Good.** Warehouse reconciles to the raw data (22 checks); every analytics table reconciles to the facts (9 tests); leakage rules are tested |
| Reproducibility | **Good.** A clean clone plus the raw data rebuilt everything; outputs matched, with documented numeric noise in two ML files |
| Security | **Good for the scope.** No secrets, no tracked data, no network surface; dependencies not scanned |
| Cost | **$0**, measured run times recorded |
| Architecture | **Sound and documented**, with decisions logged (DD-01 to DD-13) |
| Testing | **61 tests pass**; leakage tests were shown to fail when leaks are planted |
| Documentation | **Complete** for every in-scope phase; one known inconsistency (original cloud brief left unchanged by design) |
| Evidence | **Saved** in `reports/` and the docs; figures and tables regenerate byte-for-byte |
| Interview readiness | See the last section |

The ML result is modest (ranking about 2.8 times better than chance at the top 10%), and documented as such. That is a finding about the data, not a defect in the process.

## 1. Correctness

- **Warehouse:** `build_warehouse.py` builds 9 tables and runs 22 reconciliation checks (row counts, money totals, fan-out, known data issues, calendar gaps). Result in the clean clone: **22/22 passed**.
- **Analytics:** 9 tests in [tests/test_analytics.py](../tests/test_analytics.py) tie each table to the fact tables (revenue, order, item, customer, payment totals; share and ordering invariants). All pass.
- **ML features:** [tests/test_feature_leakage.py](../tests/test_feature_leakage.py) checks, on a hand-built mini warehouse, that history uses delivery time not purchase time, an order never sees itself, the 28-day window boundaries, excluded rows, and delivery-time totals. Recounts against the real warehouse agree on random samples ([tests/test_warehouse.py](../tests/test_warehouse.py)).
- **Planted-leak checks:** three deliberate leaks (two in the feature SQL, one in the calibration split) were each caught by at least one test, then removed.
- **A mistake found and corrected during the audit:** the draft insights document said late orders account for "most of the lowest review scores". Recomputing from the table showed the opposite: about 70% of 1 and 2 star reviews come from on-time orders, because there are far more of them. The document now says so.

## 2. Reproducibility

Method: `git clone` into an empty folder, copy only the raw `data/` files in, then run the pipeline with the project's Python environment.

| Step | Result |
|---|---|
| Build the warehouse | 22/22 checks passed |
| `pytest` | 61 passed |
| Analytics queries and charts | All 8 CSVs and 5 PNGs **byte-identical** to the committed copies |
| Weekly forecast baselines | Metrics file identical |
| Late-delivery backtest | v1 numbers identical (PR-AUC 0.1837); other models differ slightly |

**Numeric noise.** The late-delivery metrics are not byte-identical between runs: across a fresh run the largest differences were about 0.001 in PR-AUC, 0.002 in ROC-AUC and 0.0024 in recall at the top 10%, in the gradient-boosting and extended-feature models (multithreaded numerical code). No conclusion in the documents depends on a difference this small. Seeds are fixed (`random_state=0`).

**Environment.** Python 3.13, `uv` with `uv.lock`. Dependencies were tidied in this audit: two unused packages (`fastparquet`, `jinja2`) removed, `scipy` declared (it was imported directly but installed only as a dependency of scikit-learn), and `ipykernel` declared as a dev dependency. *One mistake to record:* removing the unused packages made `uv` prune `ipykernel`, which had been installed by hand and never declared, so the notebook kernel briefly disappeared. It was restored immediately and is now declared so a re-sync cannot remove it again.

**Not reproduced:** the discovery notebook (`notebooks/01_dataset_discovery.ipynb`) was stored with a clean run at commit `d5e8d1e` but was not re-executed in this audit (no notebook runner is installed). The geolocation CSV-to-Parquet step was tested on a CSV regenerated from the Parquet file, not on Kaggle's original download.

## 3. Security

See [SECURITY.md](../SECURITY.md). Verified: no secret patterns in tracked text files; no data, database, credential or key files tracked; no hard-coded user paths. The raw data remains in earlier commits (history not rewritten, D-008). Not verified: dependency vulnerabilities (no scanner installed).

## 4. Cost

See [COST.md](../COST.md). Cloud cost is $0 by decision. Run times were measured: warehouse build about 25 s, analytics about 12 s, late-delivery backtest about 40 s, forecast models about 12 s, explainability about 43 s, full tests 20 to 40 s.

## 5. Architecture

See [ARCHITECTURE.md](../ARCHITECTURE.md) and [DECISIONS.md](../DECISIONS.md). A Kimball star schema (4 facts, 5 dimensions) with one stated grain per table; staging, dimension, fact, validation, analytics and ML layers as plain SQL files run in a fixed order by one script. Failure points and scaling limits are listed there. The design suits a roughly 100,000-order dataset on one machine; beyond that, the BigQuery notes in [DATA_MODEL.md](data/DATA_MODEL.md) apply.

## 6. Testing

61 tests, about 30 seconds: geolocation conversion (3 cases), leakage rules (12), forecast no-lookahead and values (12), recalibration split and calibrators (11), analytics reconciliation (9), real-warehouse recounts (5), helpers and drift utilities (9). Tests that need the built warehouse are skipped if it is missing. Gaps: no test runs the `build_warehouse.py` layers on synthetic data (the in-script checks play that role), and the charts are checked by eye, not by test.

## 7. Documentation

| Document | Purpose |
|---|---|
| [README.md](../README.md) | Overview, data download, build, run, repository map |
| [ARCHITECTURE.md](../ARCHITECTURE.md), [DECISIONS.md](../DECISIONS.md) | Design and the decision log (D-001 to D-008, DD-01 to DD-13) |
| [docs/data/](data/) | Data model and discovery findings |
| [docs/analytics/BUSINESS_INSIGHTS.md](analytics/BUSINESS_INSIGHTS.md) | Findings, with charts |
| [docs/ml/](ml/) | Leakage analysis, baselines, drift, recalibration, **model card** |
| [SECURITY.md](../SECURITY.md), [COST.md](../COST.md) | Security and cost |
| [docs/LESSONS_LEARNED.md](LESSONS_LEARNED.md) | What the project taught |
| [PROJECT_STATUS.md](../PROJECT_STATUS.md), [docs/HANDOFF.md](HANDOFF.md) | Current state for a new reader |

Known inconsistency: the original brief documents (`Cloud Portfolio — Master Agent Prompt.md`, `GCP.md`, the Retail Analytics document) still describe BigQuery, Dataflow and Vertex AI. They were kept unchanged on purpose.

## 8. Evidence

Raw outputs are committed in `reports/` (ML metrics as JSON, analytics tables as CSV) and `docs/analytics/figures/` (PNG). Every number quoted in the documents comes from those files or from a query shown next to it. The graphify knowledge graph (`graphify-out/`) covers the code; the newest documents are not in it until `/graphify --update` is run.

**Repository hygiene (fixed in this audit):** graphify's cache and dated backup folders had been committed on every refresh; they are now git-ignored and untracked (the graph and report stay tracked).

## 9. Interview readiness

**The 30-second version.** "I built a local analytics platform on the Olist e-commerce data: a validated star schema in DuckDB, an analytics layer that answers business questions, and two ML baselines (late-delivery ranking and a weekly forecast). The main lessons were about honesty: I tested for leakage at every step, found that most of my attempts to improve the model did not help, and could say why."

**Decisions to be able to defend**
1. *Why DuckDB and no cloud?* The dataset is 80 MB; the cloud added cost and credentials without adding evidence. The brief was kept intact in case it returns (D-001, D-002).
2. *Why a star schema, and why "facts never join to facts"?* Joining items, payments and reviews side by side overstated revenue by 5% (DD-01).
3. *Why predict at purchase time?* The promised date is known then, and the delivery fields would leak the answer (LEAKAGE_ANALYSIS).
4. *Why did you stop improving the model?* Four feature ideas, recalibration and window tuning were tested out-of-time against the same six months; none beat the first simple model, and continuing would fit noise (DD-10 to DD-12).
5. *Why is the model used by rank, not probability?* The late rate swings from 1.4% to 21.4% between months and cannot be predicted from the recent past, so probabilities are off in level (DD-11).

**Questions to expect, with honest answers**
- *"How good is the model?"* It flags the riskiest 10% of orders and catches about 28% of the late ones, 2.8 times better than chance on average, 1.2 times in the worst month. Moderate; useful for triage only.
- *"What would make it better?"* Information the dataset lacks: carrier backlog or promise-policy changes. The August 2018 promise change is the clearest example.
- *"What would you do with more time?"* Re-run the discovery notebook in the audit, scan dependencies, test the geolocation step on Kaggle's original file, and add the new documents to the knowledge graph.
- *"What went wrong?"* A pooled metric gave a nonsense baseline score; a draft insight was backwards; a dependency clean-up removed the notebook kernel. Each was found by checking, and is recorded.

## Addendum (2026-10-13, after the audit)

The two machine-learning notebooks were added: [notebooks/02_late_delivery_model.ipynb](../notebooks/02_late_delivery_model.ipynb) and [notebooks/03_weekly_forecast.ipynb](../notebooks/03_weekly_forecast.ipynb). Both were executed with the project's kernel (27 and 15 cells, 10 and 5 figures, no error outputs), and every figure was inspected by eye; four layout problems were found and fixed before storing. The test suite grew to **69 tests**: a new file checks that each committed notebook ran cleanly, stores its charts and imports only modules that exist. `nbformat` and `nbclient` were added as development dependencies. The notebooks were not part of the clean-clone reproduction above.

Later the same day, interactive marimo versions of both notebooks were added (`notebooks/marimo/`, DD-14). Each was checked with `marimo check` (now part of the test suite, which grew to 78 tests) and executed headlessly with no cell errors, and the new interactive charts were inspected by eye (two layout flaws, a legend over the data and a label crossing a reference line, were fixed).

## Open items

| Item | Why it is open |
|---|---|
| Dependency vulnerability scan | No scanner installed |
| Re-execute the discovery notebook | No notebook runner installed |
| Geolocation conversion on Kaggle's original CSV | Original file not available locally |
| Knowledge graph does not include the newest documents | Needs `/graphify --update` (model-based extraction) |
| The original brief documents describe the cloud design | Left unchanged by decision |
