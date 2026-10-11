# Graph Report - GCP  (2026-10-11)

## Corpus Check
- 40 files · ~29,458 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 4 file(s) not represented in the graph (top: (none) 2, .ipynb 1, .lock 1)

## Summary
- 204 nodes · 240 edges · 19 communities (13 shown, 6 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.81)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `321fdfd2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Cloud vs Local Architecture Mapping
- Architecture Philosophy (Shared Across Cloud Projects)
- visualize_schema.py
- Batch vs Real-Time Inference Decision
- Agentic Loop (PLAN to DECIDE)
- Evidence Requirement and Evidence Integrity
- Phase 0 — Discovery Report
- DECISIONS.md
- User decisions
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

## God Nodes (most connected - your core abstractions)
1. `Phase 0 — Discovery Report` - 17 edges
2. `Architecture` - 12 edges
3. `User decisions` - 9 edges
4. `draw()` - 8 edges
5. `Design decisions` - 8 edges
6. `ensure_geolocation_parquet()` - 7 edges
7. `Handover: GCP Retail Analytics (local DuckDB build)` - 7 edges
8. `Data model: Olist star schema` - 7 edges
9. `Leakage analysis` - 7 edges
10. `Column audit for target A` - 7 edges

## Surprising Connections (you probably didn't know these)
- `DD-06: Convert geolocation CSV to Parquet in the build` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  DECISIONS.md → src/transformation/build_warehouse.py
- `Components` --references--> `run_sql_file()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Components` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Recommended Progression (Local, Cloud-simulated, Production)` --semantically_similar_to--> `Local to Cloud Progression Lifecycle`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md
- `Cost Discipline (ephemeral expensive resources)` --semantically_similar_to--> `Cost Management as First-Class Requirement`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]

## Communities (19 total, 6 thin omitted)

### Community 0 - "Cloud vs Local Architecture Mapping"
Cohesion: 0.11
Nodes (25): Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), dbt as First-Class Component, GCP Retail Project: Local vs Cloud Architecture, Apache Beam Direct Runner / Dataflow Runner Portability, Cloud Deployment Pipeline (GCS to Dataflow to BigQuery to Vertex AI), Cloud vs Local Architecture Mapping, DuckDB (local BigQuery substitute) (+17 more)

### Community 1 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.13
Nodes (11): Cloud Portfolio Master Agent Prompt, Local to Cloud Progression Lifecycle, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail), Architecture Philosophy (Shared Across Cloud Projects), Multi-Cloud View (three production targets of one philosophy), Recommended Progression (Local, Cloud-simulated, Production), Google Cloud Child Project Prompt: Retail Analytics, Forecasting & Customer Intelligence Platform, Demand Forecasting (naive baseline, time-aware splits) (+3 more)

### Community 2 - "visualize_schema.py"
Cohesion: 0.16
Nodes (8): Components, draw(), load_graph(), main(), node_label(), ensure_geolocation_parquet(), main(), run_sql_file()

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
Cohesion: 0.15
Nodes (11): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data, PROJECT STATUS, 1. Get the data, 2. Set up and build the warehouse (+3 more)

### Community 8 - "User decisions"
Cohesion: 0.11
Nodes (18): D-001: Implementations use DuckDB, D-002: Local only, D-003: Idiomatic DuckDB SQL, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast, D-008: Untrack `data/` (+10 more)

### Community 11 - "Column audit for target A"
Cohesion: 0.14
Nodes (14): Checklist from the brief, Column audit for target A, Customer history, `fact_order_items` (aggregate to order grain first, per DD-01), `fact_orders`, `fact_payments`, `fact_reviews`, Forecast leakage (target B) (+6 more)

### Community 14 - "Architecture"
Cohesion: 0.18
Nodes (11): Architecture, Cost, Data flow, Deployment and monitoring, Failure points, ML (planned, D-007), Processing, Related documents (+3 more)

### Community 15 - "Data model: Olist star schema"
Cohesion: 0.18
Nodes (11): Data model: Olist star schema, Design rules, Dimensions, Entity-relationship diagram, `fact_order_items` - the core sales fact, `fact_orders` - order lifecycle, `fact_payments` - payments, `fact_reviews` - reviews (+3 more)

### Community 16 - "Handover: GCP Retail Analytics (local DuckDB build)"
Cohesion: 0.25
Nodes (7): Current state, Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), Open work, What this project is now

## Knowledge Gaps
- **98 isolated node(s):** `gcp`, `graphify`, `graphify`, `Data flow`, `Storage` (+93 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 109 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Architecture Philosophy (Shared Across Cloud Projects)` to `Cloud vs Local Architecture Mapping`, `DECISIONS.md`?**
  _High betweenness centrality (0.313) - this node is a cross-community bridge._
- **What connects `gcp`, `graphify`, `graphify` to the rest of the system?**
  _98 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Cloud vs Local Architecture Mapping` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._
- **Why does `Architecture` connect `Architecture` to `visualize_schema.py`, `DECISIONS.md`?**
  _High betweenness centrality (0.200) - this node is a cross-community bridge._
- **Should `Architecture Philosophy (Shared Across Cloud Projects)` be split into smaller, more focused modules?**
  _Cohesion score 0.12631578947368421 - nodes in this community are weakly interconnected._
- **Why does `Phase 0 — Discovery Report` connect `Phase 0 — Discovery Report` to `DECISIONS.md`?**
  _High betweenness centrality (0.171) - this node is a cross-community bridge._
- **Should `Phase 0 — Discovery Report` be split into smaller, more focused modules?**
  _Cohesion score 0.08695652173913043 - nodes in this community are weakly interconnected._