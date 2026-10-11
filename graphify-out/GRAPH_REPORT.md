# Graph Report - GCP  (2026-10-11)

## Corpus Check
- 52 files · ~38,598 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .ipynb 1, .lock 1)

## Summary
- 315 nodes · 450 edges · 23 communities (17 shown, 6 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 24 edges (avg confidence: 0.83)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `095e6455`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Cloud vs Local Architecture Mapping
- Architecture Philosophy (Shared Across Cloud Projects)
- duckdb
- Batch vs Real-Time Inference Decision
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
- pytest
- test_feature_leakage.py

## God Nodes (most connected - your core abstractions)
1. `Phase 0 — Discovery Report` - 17 edges
2. `Architecture` - 12 edges
3. `day()` - 11 edges
4. `Design decisions` - 11 edges
5. `run()` - 10 edges
6. `ensure_geolocation_parquet()` - 10 edges
7. `User decisions` - 9 edges
8. `draw()` - 8 edges
9. `main()` - 8 edges
10. `main()` - 8 edges

## Surprising Connections (you probably didn't know these)
- `DD-06: Convert geolocation CSV to Parquet in the build` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  DECISIONS.md → src/transformation/build_warehouse.py
- `Components` --references--> `run_sql_file()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Components` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Tests` --references--> `test_outcome_is_not_visible_at_the_instant_of_delivery()`  [INFERRED]
  docs/ml/PHASE2_BASELINES.md → tests/test_feature_leakage.py
- `Recommended Progression (Local, Cloud-simulated, Production)` --semantically_similar_to--> `Local to Cloud Progression Lifecycle`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]

## Communities (23 total, 6 thin omitted)

### Community 0 - "Cloud vs Local Architecture Mapping"
Cohesion: 0.11
Nodes (25): Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), dbt as First-Class Component, GCP Retail Project: Local vs Cloud Architecture, Apache Beam Direct Runner / Dataflow Runner Portability, Cloud Deployment Pipeline (GCS to Dataflow to BigQuery to Vertex AI), Cloud vs Local Architecture Mapping, DuckDB (local BigQuery substitute) (+17 more)

### Community 1 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.13
Nodes (11): Cloud Portfolio Master Agent Prompt, Local to Cloud Progression Lifecycle, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail), Architecture Philosophy (Shared Across Cloud Projects), Multi-Cloud View (three production targets of one philosophy), Recommended Progression (Local, Cloud-simulated, Production), Google Cloud Child Project Prompt: Retail Analytics, Forecasting & Customer Intelligence Platform, Demand Forecasting (naive baseline, time-aware splits) (+3 more)

### Community 2 - "duckdb"
Cohesion: 0.13
Nodes (13): Components, draw(), load_graph(), main(), node_label(), main(), ensure_geolocation_parquet(), main() (+5 more)

### Community 3 - "Batch vs Real-Time Inference Decision"
Cohesion: 0.29
Nodes (5): ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Model Comparison, Evaluation and Threshold Analysis, Supervised ML Problem Selection and Leakage Analysis

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
Cohesion: 0.14
Nodes (12): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data, PROJECT STATUS, 1. Get the data, 2. Set up and build the warehouse (+4 more)

### Community 8 - "Design decisions"
Cohesion: 0.10
Nodes (21): D-001: Implementations use DuckDB, D-002: Local only, D-003: Idiomatic DuckDB SQL, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast, D-008: Untrack `data/` (+13 more)

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
Cohesion: 0.10
Nodes (11): add_smoothed_rates(), calibration_table(), evaluate(), load(), make_models(), run(), top_share_metrics(), unlabelled_share() (+3 more)

### Community 20 - "forecast_baseline.py"
Cohesion: 0.15
Nodes (12): backtest(), linear_trend(), f(), main(), naive(), score(), weekly_series(), series() (+4 more)

### Community 21 - "pytest"
Cohesion: 0.12
Nodes (6): mini(), MiniWarehouse, warehouse(), features(), test_seller_history_matches_a_direct_recount_on_real_data(), test_weekly_series_covers_the_documented_window()

### Community 22 - "test_feature_leakage.py"
Cohesion: 0.14
Nodes (17): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+9 more)

## Knowledge Gaps
- **106 isolated node(s):** `gcp`, `graphify`, `graphify`, `Data flow`, `Storage` (+101 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 152 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture` connect `Architecture` to `duckdb`, `DECISIONS.md`?**
  _High betweenness centrality (0.273) - this node is a cross-community bridge._
- **What connects `gcp`, `graphify`, `graphify` to the rest of the system?**
  _106 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Cloud vs Local Architecture Mapping` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._
- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Architecture Philosophy (Shared Across Cloud Projects)` to `Cloud vs Local Architecture Mapping`, `DECISIONS.md`?**
  _High betweenness centrality (0.246) - this node is a cross-community bridge._
- **Should `Architecture Philosophy (Shared Across Cloud Projects)` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Why does `Components` connect `duckdb` to `Architecture`?**
  _High betweenness centrality (0.243) - this node is a cross-community bridge._
- **Should `duckdb` be split into smaller, more focused modules?**
  _Cohesion score 0.12643678160919541 - nodes in this community are weakly interconnected._