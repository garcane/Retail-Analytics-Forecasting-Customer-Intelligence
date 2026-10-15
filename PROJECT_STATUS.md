# PROJECT STATUS

_Last updated: 2026-10-13_

**Scope:** a **local implementation of what would have been built on BigQuery**. DuckDB replaces Google Cloud and BigQuery as the warehouse and query engine. There is no GCP project, and no cloud resources are used or planned (D-002).

**Current phase:** all in-scope phases complete. Phase 10 (final audit) is written in [docs/AUDIT.md](docs/AUDIT.md). Nothing is in progress and nothing is blocked.

## Phase status

| Phase (from the brief) | Status | Where |
|---|---|---|
| 0 Discovery | Done | `docs/phase0/PHASE0_DISCOVERY.md`, `docs/data/EDA_FINDINGS.md`, `notebooks/01_dataset_discovery.ipynb` |
| 1 Architecture | Done | `ARCHITECTURE.md`, `DECISIONS.md`, `docs/ml/LEAKAGE_ANALYSIS.md` |
| 2 Local prototype | Done | `docs/ml/PHASE2_BASELINES.md` |
| 3 Cloud foundation | Out of scope (D-002) | |
| 4 Data engineering | Done | `sql/`, `src/transformation/build_warehouse.py`, `docs/data/DATA_MODEL.md` (22 checks) |
| 5 Analytics | Done | `sql/analytics/`, `src/analytics/`, `docs/analytics/BUSINESS_INSIGHTS.md` |
| 6 Machine learning | Done | `notebooks/02_late_delivery_model.ipynb` and `03_weekly_forecast.ipynb` (with charts), interactive versions in `notebooks/marimo/`, `docs/ml/MODEL_CARD.md` and the experiment documents it links |
| Dashboard (Power BI, added later) | Built; opens and loads in Desktop (owner now edits layouts there) | `powerbi/README.md`, `docs/powerbi/DAX_SPECIFICATION.html`, `docs/powerbi/DASHBOARD_MOCKUP.html`, `powerbi/RetailAnalytics.pbip` (DD-15) |
| 7 Deployment, 8 Monitoring | Out of scope (D-002, D-005) | |
| 9 Documentation | Done | `README.md`, `SECURITY.md`, `COST.md`, `docs/LESSONS_LEARNED.md`, model card |
| 10 Final audit | Done | `docs/AUDIT.md` |

## Headline results

- **Data model:** 4 facts and 5 dimensions, built in about 25 seconds, 22/22 reconciliation checks pass.
- **Business findings:** net revenue R$ 13.49 million over 98,199 orders; 97% of customers bought once; late orders are the clearest driver of low reviews; the delivery promise was shortened sharply in 2018 (75% of August orders promised in under 20 days). See the insights document.
- **Late-delivery model:** logistic regression ranking orders at purchase time. Flagging the riskiest 10% beats chance by about 2.8 times on average (1.2 times in August 2018). Its probabilities are off in level; use it by rank (DD-11).
- **Experiments that did not help**, all documented: route, category and trailing-rate history; delivery-time slack; recalibration; training-window tuning (DD-10 to DD-12).
- **Weekly forecast:** the average of the naive and 8-week-average forecasts at one week, the 8-week average at four weeks; the more complex models do not clearly beat them on 85 weeks of data.

## Quality evidence

- `uv run pytest`: **96 tests pass** (about 45 seconds). Leakage tests were shown to fail when leaks were planted.
- A **clean clone** plus the raw data rebuilt the warehouse (22/22), passed all tests and regenerated the analytics tables and figures byte-for-byte. Late-delivery metrics reproduce to within about 0.001 to 0.002 (multithreaded numerics); v1 was identical.
- Security scan: no secrets, no tracked data or credentials ([SECURITY.md](SECURITY.md)). Cost: $0 ([COST.md](COST.md)).

## Decisions

D-001 to D-008 (user) and DD-01 to DD-15 (design) are in [DECISIONS.md](DECISIONS.md). **Open decisions:** none.

## Open items (from the audit)

| Item | Why open |
|---|---|
| Dependency vulnerability scan | No scanner installed |
| Re-execute the discovery notebook | No notebook runner installed (it was stored with a clean run at `d5e8d1e`) |
| Geolocation CSV-to-Parquet on Kaggle's original file | Tested only on a CSV regenerated from the Parquet file |
| Add the newest documents to the knowledge graph | Needs `/graphify --update`; `graphify update .` (code only) is current |

## Known limitations

- The ML result is modest and documented as such; a better model would need information the dataset lacks (see the model card).
- Six test months and 85 forecast weeks are small samples.
- The original brief documents (`Cloud Portfolio — Master Agent Prompt.md`, `GCP.md`, the Retail Analytics document) still describe BigQuery, Dataflow, Vertex AI and monitoring services. They are kept unchanged by design.
- The raw data remains in earlier commits (history not rewritten, D-008).
