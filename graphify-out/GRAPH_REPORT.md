# Graph Report - GCP  (2026-10-13)

## Corpus Check
- 60 files · ~48,110 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .ipynb 1, .lock 1)

## Summary
- 389 nodes · 645 edges · 25 communities (19 shown, 6 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 25 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b9c12827`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Cloud vs Local Architecture Mapping
- Architecture Philosophy (Shared Across Cloud Projects)
- visualize_schema.py
- What was done and what came out
- Agentic Loop (PLAN to DECIDE)
- Evidence Requirement and Evidence Integrity
- Phase 0 — Discovery Report
- DECISIONS.md
- Design decisions
- Cross-Cloud Learning (Azure/AWS/GCP equivalents)
- Customer Segmentation (K-Means, silhouette)
- Column audit for target A
- Graphify Knowledge Graph Usage Rules
- gcp
- Architecture
- Data model: Olist star schema
- Handover: GCP Retail Analytics (local DuckDB build)
- AGENTS.md
- CLAUDE.md
- late_delivery_baseline.py
- forecast_baseline.py
- conftest.py
- test_feature_leakage.py
- recalibration.py
- test_drift_helpers.py

## God Nodes (most connected - your core abstractions)
1. `Phase 0 — Discovery Report` - 17 edges
2. `main()` - 12 edges
3. `Architecture` - 12 edges
4. `Design decisions` - 12 edges
5. `day()` - 11 edges
6. `run()` - 10 edges
7. `ensure_geolocation_parquet()` - 10 edges
8. `experiment_recalibration()` - 9 edges
9. `orders()` - 9 edges
10. `User decisions` - 9 edges

## Surprising Connections (you probably didn't know these)
- `DD-06: Convert geolocation CSV to Parquet in the build` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  DECISIONS.md → src/transformation/build_warehouse.py
- `3. Data quality findings` --references--> `orders()`  [INFERRED]
  docs/phase0/PHASE0_DISCOVERY.md → tests/test_recalibration.py
- `Components` --references--> `run_sql_file()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Components` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `test_csv_only_is_converted_and_keeps_leading_zeros()` --calls--> `ensure_geolocation_parquet()`  [INFERRED]
  tests/test_geolocation_conversion.py → src/transformation/build_warehouse.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]

## Communities (25 total, 6 thin omitted)

### Community 0 - "Cloud vs Local Architecture Mapping"
Cohesion: 0.08
Nodes (30): Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, dbt as First-Class Component, GCP Retail Project: Local vs Cloud Architecture, Apache Beam Direct Runner / Dataflow Runner Portability (+22 more)

### Community 1 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.13
Nodes (11): Cloud Portfolio Master Agent Prompt, Local to Cloud Progression Lifecycle, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail), Architecture Philosophy (Shared Across Cloud Projects), Multi-Cloud View (three production targets of one philosophy), Recommended Progression (Local, Cloud-simulated, Production), Google Cloud Child Project Prompt: Retail Analytics, Forecasting & Customer Intelligence Platform, Demand Forecasting (naive baseline, time-aware splits) (+3 more)

### Community 2 - "visualize_schema.py"
Cohesion: 0.15
Nodes (9): Components, draw(), load_graph(), main(), node_label(), ensure_geolocation_parquet(), main(), run_sql_file() (+1 more)

### Community 3 - "What was done and what came out"
Cohesion: 0.18
Nodes (11): August 2018 is a change in promise policy, not a label problem, Drift analysis: why the richer history features did not help, E1: single-feature skill, month by month, E2: does a route's, category's or seller's lateness persist?, E3 and E4: shorter training windows, and relative features, E5: what a perfect regime signal would buy, E6: is route history redundant with the state and distance columns?, Limits (+3 more)

### Community 4 - "Agentic Loop (PLAN to DECIDE)"
Cohesion: 0.33
Nodes (6): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done, Final Project Audit, Phase 0 Discovery (starting instruction)

### Community 5 - "Evidence Requirement and Evidence Integrity"
Cohesion: 0.33
Nodes (6): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git), Cloud IAM and Secret Manager, Evidence Checkpoints E01-E20

### Community 6 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 7 - "DECISIONS.md"
Cohesion: 0.11
Nodes (17): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data, Conclusions, Limits, R: recalibration on the latest resolved period (+9 more)

### Community 8 - "Design decisions"
Cohesion: 0.09
Nodes (22): D-001: Implementations use DuckDB, D-002: Local only, D-003: Idiomatic DuckDB SQL, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast, D-008: Untrack `data/` (+14 more)

### Community 11 - "Column audit for target A"
Cohesion: 0.14
Nodes (14): Checklist from the brief, Column audit for target A, Customer history, `fact_order_items` (aggregate to order grain first, per DD-01), `fact_orders`, `fact_payments`, `fact_reviews`, Forecast leakage (target B) (+6 more)

### Community 14 - "Architecture"
Cohesion: 0.18
Nodes (11): Architecture, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing, Related documents (+3 more)

### Community 15 - "Data model: Olist star schema"
Cohesion: 0.18
Nodes (11): Data model: Olist star schema, Design rules, Dimensions, Entity-relationship diagram, `fact_order_items` - the core sales fact, `fact_orders` - order lifecycle, `fact_payments` - payments, `fact_reviews` - reviews (+3 more)

### Community 16 - "Handover: GCP Retail Analytics (local DuckDB build)"
Cohesion: 0.25
Nodes (7): Current state, Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), Open work, What this project is now

### Community 19 - "late_delivery_baseline.py"
Cohesion: 0.08
Nodes (22): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts() (+14 more)

### Community 20 - "forecast_baseline.py"
Cohesion: 0.08
Nodes (17): backtest(), linear_trend(), f(), naive(), score(), weekly_series(), series(), test_changing_future_weeks_does_not_change_earlier_forecasts() (+9 more)

### Community 21 - "conftest.py"
Cohesion: 0.24
Nodes (3): mini(), MiniWarehouse, warehouse()

### Community 22 - "test_feature_leakage.py"
Cohesion: 0.14
Nodes (17): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+9 more)

### Community 23 - "recalibration.py"
Cohesion: 0.14
Nodes (21): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), make_calibrator() (+13 more)

### Community 24 - "test_drift_helpers.py"
Cohesion: 0.57
Nodes (5): frame(), test_relative_rates_are_positive_for_a_late_route(), test_relative_rates_are_zero_when_route_matches_the_system(), test_system_counts_do_not_depend_on_row_order(), test_system_counts_use_only_orders_delivered_strictly_before_purchase()

## Knowledge Gaps
- **119 isolated node(s):** `gcp`, `graphify`, `graphify`, `Data flow`, `Storage` (+114 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 175 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Phase 0 — Discovery Report` connect `Phase 0 — Discovery Report` to `DECISIONS.md`?**
  _High betweenness centrality (0.219) - this node is a cross-community bridge._
- **What connects `gcp`, `graphify`, `graphify` to the rest of the system?**
  _119 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Cloud vs Local Architecture Mapping` be split into smaller, more focused modules?**
  _Cohesion score 0.08064516129032258 - nodes in this community are weakly interconnected._
- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Architecture Philosophy (Shared Across Cloud Projects)` to `Cloud vs Local Architecture Mapping`, `DECISIONS.md`?**
  _High betweenness centrality (0.211) - this node is a cross-community bridge._
- **Should `Architecture Philosophy (Shared Across Cloud Projects)` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Why does `orders()` connect `recalibration.py` to `late_delivery_baseline.py`, `Phase 0 — Discovery Report`?**
  _High betweenness centrality (0.174) - this node is a cross-community bridge._
- **Should `visualize_schema.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14624505928853754 - nodes in this community are weakly interconnected._