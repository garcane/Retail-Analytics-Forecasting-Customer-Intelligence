# Graph Report - GCP  (2026-10-13)

## Corpus Check
- 80 files · ~70,200 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 613 nodes · 1152 edges · 36 communities (31 shown, 5 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Project Documentation Hub
- ML Pipeline Code
- Cloud Architecture Brief
- Recalibration and Window Code
- Test Suite and Fixtures
- Star Schema and Leakage Audit
- Analytics and Schema Charts Code
- Warehouse Build Script
- Leakage Tests
- Phase 0 Discovery Report
- Delivery Charts and Findings
- Forecast Models
- Business Insights
- Final Audit
- Data Model Doc
- Drift Analysis
- Star Schema Diagram Tables
- Category Revenue Chart
- Monthly KPI Chart
- README and Repository Map
- Reviews vs Delay Chart
- Handover Document
- Master Prompt Phases
- Evidence and Security Standards
- Security Document
- Graphify Integration
- EDA Findings
- Lessons Learned
- Recalibration and Window Doc
- Model Card
- Cross-Cloud Learning
- Cost Document
- Customer Segmentation Brief
- Star Schema Image
- Graphify Usage Rules
- GCP Package Stub

## God Nodes (most connected - your core abstractions)
1. `Phase 0 — Discovery Report` - 17 edges
2. `Design decisions` - 13 edges
3. `Architecture` - 12 edges
4. `Final audit (Phase 10)` - 12 edges
5. `main()` - 12 edges
6. `day()` - 12 edges
7. `Business insights: Olist retail analytics` - 11 edges
8. `run()` - 11 edges
9. `main()` - 10 edges
10. `ensure_geolocation_parquet()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `3. Data quality findings` --references--> `orders()`  [INFERRED]
  docs/phase0/PHASE0_DISCOVERY.md → tests/test_recalibration.py
- `DD-06: Convert geolocation CSV to Parquet in the build` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  DECISIONS.md → src/transformation/build_warehouse.py
- `Components` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Components` --references--> `run_sql_file()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Tests` --references--> `test_outcome_is_not_visible_at_the_instant_of_delivery()`  [INFERRED]
  docs/ml/PHASE2_BASELINES.md → tests/test_feature_leakage.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]
- **Late-delivery improvement attempts that did not beat v1** — docs_ml_phase2_baselines_v2_history_features, docs_ml_phase2_baselines_v3_trailing_rate, docs_ml_model_card_v5_slack_features, docs_ml_recalibration_and_window_recalibration, docs_ml_recalibration_and_window_window_tuning, decisions_dd_12 [EXTRACTED 1.00]
- **Local-only scope decisions (DuckDB, no GCP, plain SQL, no monitoring stack)** — decisions_d_001_implementations_use_duckdb, decisions_d_002, decisions_d_003_idiomatic_duckdb_sql, decisions_d_004, decisions_d_005_no_prometheus_grafana_or_fastapi [EXTRACTED 1.00]
- **Leakage controls: purchase-time prediction, point-in-time stats, time-ordered split, planted-leak tests** — docs_ml_leakage_analysis_purchase_time_prediction, docs_ml_leakage_analysis_point_in_time_statistics, docs_ml_leakage_analysis_time_ordered_split, docs_audit_planted_leak_checks [INFERRED 0.85]
- **Monthly KPIs chart: metrics, trend insight and data source** — docs_analytics_figures_monthly_kpis_net_revenue_per_month, docs_analytics_figures_monthly_kpis_average_order_value, docs_analytics_figures_monthly_kpis_olist_orders_data [INFERRED 0.85]
- **Categories chart: metric, insight and data source** — docs_analytics_figures_categories_net_revenue_by_category_metric, docs_analytics_figures_categories_top_categories_insight, docs_analytics_figures_categories_olist_data_source [INFERRED 0.85]
- **Delivery performance by state: metrics, insights and data source** — docs_analytics_figures_states_median_days_to_deliver, docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_states_slowest_states_insight, docs_analytics_figures_states_olist_orders_data [INFERRED 0.75]
- **Reviews vs delay chart: metric, buckets, source and insight** — docs_analytics_figures_reviews_vs_delay_average_review_score, docs_analytics_figures_reviews_vs_delay_delivery_delay_bucket, docs_analytics_figures_reviews_vs_delay_olist_data_source, docs_analytics_figures_reviews_vs_delay_score_drops_with_lateness [EXTRACTED 1.00]
- **Promise and lateness chart: two metrics over one Olist monthly dataset** — docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_promise_and_lateness_orders_promised_under_20_days_pct, docs_analytics_figures_promise_and_lateness_olist_delivered_orders_data [EXTRACTED 1.00]
- **Olist warehouse star schema (4 fact tables around 5 dimensions)** — docs_data_star_schema_fact_payments, docs_data_star_schema_fact_orders, docs_data_star_schema_fact_order_items, docs_data_star_schema_fact_reviews, docs_data_star_schema_dim_date, docs_data_star_schema_dim_geography, docs_data_star_schema_dim_product, docs_data_star_schema_dim_seller, docs_data_star_schema_dim_customer [EXTRACTED 1.00]

## Communities (36 total, 5 thin omitted)

### Community 0 - "Project Documentation Hub"
Cohesion: 0.05
Nodes (64): build_warehouse.py (build and validate script), warehouse.duckdb (single local database file), Total cloud cost $0, D-001: Implementations use DuckDB, D-002: Local only, D-003: Idiomatic DuckDB SQL, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI (+56 more)

### Community 1 - "ML Pipeline Code"
Cohesion: 0.05
Nodes (39): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts() (+31 more)

### Community 2 - "Cloud Architecture Brief"
Cohesion: 0.05
Nodes (41): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail) (+33 more)

### Community 3 - "Recalibration and Window Code"
Cohesion: 0.10
Nodes (29): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), make_calibrator() (+21 more)

### Community 4 - "Test Suite and Fixtures"
Cohesion: 0.08
Nodes (22): mini(), MiniWarehouse, warehouse(), net(), table(), test_category_revenue_matches_and_shares_are_consistent(), test_delay_buckets_cover_every_reviewed_delivered_order(), test_delivery_trend_covers_the_same_population_as_the_ml_features() (+14 more)

### Community 5 - "Star Schema and Leakage Audit"
Cohesion: 0.08
Nodes (29): Net revenue R$ 13.49M over 98,199 orders, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), fact_order_items (grain: order item, 112,650 rows), fact_orders (grain: order) (+21 more)

### Community 6 - "Analytics and Schema Charts Code"
Cohesion: 0.20
Nodes (12): draw(), load_graph(), main(), node_label(), fig_categories(), fig_monthly(), fig_promise(), fig_reviews() (+4 more)

### Community 7 - "Warehouse Build Script"
Cohesion: 0.10
Nodes (18): Architecture, Components, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing (+10 more)

### Community 8 - "Leakage Tests"
Cohesion: 0.13
Nodes (19): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+11 more)

### Community 9 - "Phase 0 Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 10 - "Delivery Charts and Findings"
Cohesion: 0.27
Nodes (8): Promise and Lateness Chart (late-delivery rate and under-20-day promises by month), Olist delivered orders by purchase month (months with at least 500 orders, 2017-01 to 2018-08), Orders Promised in Under 20 Days (%) metric, Delivery performance by customer state (chart), Median days to deliver (metric), Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time, Olist Brazilian e-commerce orders data (source), Orders delivered late % (metric)

### Community 11 - "Forecast Models"
Cohesion: 0.17
Nodes (5): moving_average(), naive(), combination(), damped_trend(), simple_exponential_smoothing()

### Community 12 - "Business Insights"
Cohesion: 0.18
Nodes (11): 1. Growth: fast in 2017, flat in 2018, 2. What sells: broad, and not concentrated in a few categories, 3. Geography: one region carries the marketplace, and the north-east pays for distance, 4. Seller base: a long tail with a strong head, 5. Delivery and reviews: lateness is the clearest cost to customer satisfaction, 6. The delivery promise changed, and it is the main story of 2018, 7. Customers: almost everyone buys once, 8. Payments (+3 more)

### Community 13 - "Final Audit"
Cohesion: 0.18
Nodes (11): 1. Correctness, 2. Reproducibility, 3. Security, 4. Cost, 5. Architecture, 6. Testing, 7. Documentation, 8. Evidence (+3 more)

### Community 14 - "Data Model Doc"
Cohesion: 0.20
Nodes (10): Data model: Olist star schema, Design rules, Dimensions, Entity-relationship diagram, `fact_order_items` - the core sales fact, `fact_orders` - order lifecycle, `fact_payments` - payments, `fact_reviews` - reviews (+2 more)

### Community 15 - "Drift Analysis"
Cohesion: 0.20
Nodes (10): August 2018 is a change in promise policy, not a label problem, Drift analysis: why the richer history features did not help, E2: does a route's, category's or seller's lateness persist?, E3 and E4: shorter training windows, and relative features, E5: what a perfect regime signal would buy, E6: is route history redundant with the state and distance columns?, Limits, Verdict (+2 more)

### Community 16 - "Star Schema Diagram Tables"
Cohesion: 0.42
Nodes (9): dim_customer (PK: customer_key; 96,097 rows), dim_date (PK: date_key; 1,828 rows), dim_geography (PK: geography_key; 19,012 rows), dim_product (PK: product_key; 32,952 rows), dim_seller (PK: seller_key; 3,096 rows), fact_order_items (PK: order_id, order_item_id; 112,650 rows), fact_orders (PK: order_id; 99,441 rows), fact_payments (PK: order_id, payment_sequential; 103,886 rows) (+1 more)

### Community 17 - "Category Revenue Chart"
Cohesion: 0.36
Nodes (8): Top 12 categories by net revenue chart (categories.png), bed_bath_table category (1.04M, 7.7%), health_beauty category (1.26M, 9.3%, top revenue category), Net revenue by product category (R$ millions, share of total), Olist Brazilian e-commerce retail dataset (net revenue, 74 categories), Revenue concentration: long-tail distribution, top category 9.3% down to 3.0% at rank 12, Top 12 categories account for 69% of net revenue across 74 categories, watches_gifts category (1.20M, 8.9%)

### Community 18 - "Monthly KPI Chart"
Cohesion: 0.32
Nodes (5): Monthly KPIs chart (net revenue and average order value), Average order value (R$), Net revenue per month (R$ millions), 2017-11 revenue peak (R$1.00M), Olist retail orders data (data source)

### Community 19 - "README and Repository Map"
Cohesion: 0.25
Nodes (8): 1. Get the data, 2. Set up and build the warehouse, 3. Run the baselines and tests, 4. Explore, Attribution, Repository map, Results at a glance, Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)

### Community 20 - "Reviews vs Delay Chart"
Cohesion: 0.43
Nodes (4): Chart: Average review score by how late the order arrived, Metric: Average review score (1 to 5), Delivery delay buckets (on time or early, 1-3, 4-7, 8-14, more than 14 days late), Data source: Olist retail delivered orders with a review

### Community 21 - "Handover Document"
Cohesion: 0.29
Nodes (7): Current state (2026-10-13), Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), Open items, What this project is now

### Community 22 - "Master Prompt Phases"
Cohesion: 0.33
Nodes (6): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done, Final Project Audit, Phase 0 Discovery (starting instruction)

### Community 23 - "Evidence and Security Standards"
Cohesion: 0.33
Nodes (6): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git), Cloud IAM and Secret Manager, Evidence Checkpoints E01-E20

### Community 24 - "Security Document"
Cohesion: 0.33
Nodes (6): Data and privacy, Licence, Not applicable by design, Practices to keep, Security, What was checked (2026-10-13)

### Community 25 - "Graphify Integration"
Cohesion: 0.50
Nodes (3): graphify, graphify knowledge graph (graphify-out/), graphify

### Community 26 - "EDA Findings"
Cohesion: 0.40
Nodes (5): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data

### Community 27 - "Lessons Learned"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 28 - "Recalibration and Window Doc"
Cohesion: 0.40
Nodes (5): Conclusions, Limits, R: recalibration on the latest resolved period, Recalibration and training window for the v1 late-delivery model, W: choosing the training window

### Community 29 - "Model Card"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

### Community 31 - "Cost Document"
Cohesion: 0.67
Nodes (3): Compute, Cost, If the project moved to the cloud

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **160 isolated node(s):** `Checklist from the brief`, `Customer history`, ``fact_order_items` (aggregate to order grain first, per DD-01)`, ``fact_orders``, ``fact_payments`` (+155 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 232 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `ensure_geolocation_parquet()` connect `Warehouse Build Script` to `Project Documentation Hub`, `ML Pipeline Code`?**
  _High betweenness centrality (0.286) - this node is a cross-community bridge._
- **What connects `Checklist from the brief`, `Customer history`, ``fact_order_items` (aggregate to order grain first, per DD-01)` to the rest of the system?**
  _160 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Project Documentation Hub` be split into smaller, more focused modules?**
  _Cohesion score 0.0547008547008547 - nodes in this community are weakly interconnected._
- **Why does `DD-06: Convert geolocation CSV to Parquet in the build` connect `Project Documentation Hub` to `Star Schema and Leakage Audit`, `Warehouse Build Script`?**
  _High betweenness centrality (0.276) - this node is a cross-community bridge._
- **Should `ML Pipeline Code` be split into smaller, more focused modules?**
  _Cohesion score 0.05268414481897628 - nodes in this community are weakly interconnected._
- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Cloud Architecture Brief` to `Project Documentation Hub`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._