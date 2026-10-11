# Graph Report - GCP  (2026-10-06)

## Corpus Check
- Corpus is ~9,558 words - fits in a single context window. You may not need a graph.

## Summary
- 74 nodes · 82 edges · 14 communities (9 shown, 5 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 15 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Local vs Cloud Tool Mapping
- Local-First Philosophy
- Portfolio Master Prompt
- ML and Inference Methodology
- Agentic Workflow and Phases
- Docs, Evidence, Security
- Data Layers and Pipelines
- GCP Retail Architecture
- Warehouse and dbt Modelling
- Cross-Cloud Learning
- Customer Analytics
- Graphify Usage Rules
- gcp Package

## God Nodes (most connected - your core abstractions)
1. `BigQuery (analytical centre)` - 6 edges
2. `Cloud vs Local Architecture Mapping` - 6 edges
3. `Architecture Philosophy (Shared Across Cloud Projects)` - 6 edges
4. `Vertex AI` - 5 edges
5. `Dimensional Model (Fact and Dim tables, explicit grain)` - 5 edges
6. `Local-First, Cloud-Aware Development` - 4 edges
7. `Local to Cloud Progression Lifecycle` - 4 edges
8. `GCP Retail Project: Local vs Cloud Architecture` - 4 edges
9. `Local Development Pipeline (Olist CSV to Parquet to DuckDB)` - 4 edges
10. `Cloud Portfolio Master Agent Prompt` - 3 edges

## Surprising Connections (you probably didn't know these)
- `Core Principle: Build locally, cloud as production target, emulators where useful` --semantically_similar_to--> `Local-First, Cloud-Aware Development`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md
- `Recommended Progression (Local, Cloud-simulated, Production)` --semantically_similar_to--> `Local to Cloud Progression Lifecycle`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md
- `Cost Discipline (ephemeral expensive resources)` --semantically_similar_to--> `Cost Management as First-Class Requirement`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md
- `Narrative Goal (could own a data platform end to end)` --semantically_similar_to--> `Technical Interview Standard`  [INFERRED] [semantically similar]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md
- `dbt as First-Class Component` --conceptually_related_to--> `Data Warehousing and Analytical Modelling (grain, star schema)`  [INFERRED]
  docs/architecture-philosophy.md → Cloud Portfolio — Master Agent Prompt.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]

## Communities (14 total, 5 thin omitted)

### Community 0 - "Local vs Cloud Tool Mapping"
Cohesion: 0.21
Nodes (12): Cloud vs Local Architecture Mapping, DuckDB (local BigQuery substitute), FastAPI (local model serving), MLflow (local tracking and model registry), Prometheus + Grafana (local monitoring), BigQuery (analytical centre), BigQuery Partitioning, Clustering and Query Cost Optimisation, Cloud Monitoring (+4 more)

### Community 1 - "Local-First Philosophy"
Cohesion: 0.27
Nodes (5): Local to Cloud Progression Lifecycle, Architecture Philosophy (Shared Across Cloud Projects), Recommended Progression (Local, Cloud-simulated, Production), Local-First Development (notebooks vs src/sql/config), Repository Structure (src, sql, notebooks, infrastructure, docs)

### Community 2 - "Portfolio Master Prompt"
Cohesion: 0.29
Nodes (4): Cloud Portfolio Master Agent Prompt, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail), Multi-Cloud View (three production targets of one philosophy), Google Cloud Child Project Prompt: Retail Analytics, Forecasting & Customer Intelligence Platform

### Community 3 - "ML and Inference Methodology"
Cohesion: 0.29
Nodes (5): ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Model Comparison, Evaluation and Threshold Analysis, Supervised ML Problem Selection and Leakage Analysis

### Community 4 - "Agentic Workflow and Phases"
Cohesion: 0.33
Nodes (6): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done, Final Project Audit, Phase 0 Discovery (starting instruction)

### Community 5 - "Docs, Evidence, Security"
Cohesion: 0.33
Nodes (6): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git), Cloud IAM and Secret Manager, Evidence Checkpoints E01-E20

### Community 6 - "Data Layers and Pipelines"
Cohesion: 0.33
Nodes (6): Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Apache Beam Direct Runner / Dataflow Runner Portability, Data Lifecycle Layers (RAW, STAGING, CURATED, ANALYTICAL, FEATURES, PREDICTIONS), Automated Data Quality Checks, Dataflow (used only where justified), Google Cloud Storage (raw/staging/curated/features/models/predictions)

### Community 7 - "GCP Retail Architecture"
Cohesion: 0.50
Nodes (5): GCP Retail Project: Local vs Cloud Architecture, Cloud Deployment Pipeline (GCS to Dataflow to BigQuery to Vertex AI), Local Development Pipeline (Olist CSV to Parquet to DuckDB), Demand Forecasting (naive baseline, time-aware splits), Olist Brazilian E-Commerce Public Dataset

### Community 8 - "Warehouse and dbt Modelling"
Cohesion: 0.67
Nodes (4): Data Warehousing and Analytical Modelling (grain, star schema), dbt as First-Class Component, Dimensional Model (Fact and Dim tables, explicit grain), Join Multiplication Risk

## Knowledge Gaps
- **18 isolated node(s):** `gcp`, `Failure Documentation`, `Human Approval Gates`, `Notion and GitHub Relationship`, `Cloud IAM and Secret Manager` (+13 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 24 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BigQuery (analytical centre)` connect `Local vs Cloud Tool Mapping` to `Warehouse and dbt Modelling`, `Data Layers and Pipelines`?**
  _High betweenness centrality (0.162) - this node is a cross-community bridge._
- **What connects `gcp`, `Failure Documentation`, `Human Approval Gates` to the rest of the system?**
  _18 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Why does `Vertex AI` connect `Local vs Cloud Tool Mapping` to `ML and Inference Methodology`?**
  _High betweenness centrality (0.152) - this node is a cross-community bridge._
- **Why does `Dimensional Model (Fact and Dim tables, explicit grain)` connect `Warehouse and dbt Modelling` to `Local vs Cloud Tool Mapping`, `GCP Retail Architecture`?**
  _High betweenness centrality (0.144) - this node is a cross-community bridge._