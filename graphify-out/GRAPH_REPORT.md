# Graph Report - GCP  (2026-10-15)

## Corpus Check
- 149 files · ~115,223 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 41 file(s) not represented in the graph (top: .tmdl 22, .csv 8, (none) 4)

## Summary
- 1705 nodes · 2325 edges · 116 communities (90 shown, 26 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `147ebdf9`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- PHASE2_BASELINES.md
- late_delivery_baseline.py
- Architecture Philosophy (Shared Across Cloud Projects)
- recalibration.py
- Recalibration and training window for the v1 late-delivery model
- Column audit for target A
- run_analytics.py
- fact_order_items
- pytest
- Phase 0 — Discovery Report
- Orders delivered late % (metric)
- pandas
- Business insights: Olist retail analytics
- Final audit (Phase 10)
- Data model: Olist star schema
- What was done and what came out
- fact_order_items (PK: order_id, order_item_id; 112,650 rows)
- Net revenue by product category (R$ millions, share of total)
- Net revenue per month (R$ millions)
- Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)
- Chart: Average review score by how late the order arrived
- Handover: GCP Retail Analytics (local DuckDB build)
- Agentic Loop (PLAN to DECIDE)
- Evidence Requirement and Evidence Integrity
- Security
- AGENTS.md
- AUDIT.md
- Lessons learned
- duckdb
- Model card
- Cross-Cloud Learning (Azure/AWS/GCP equivalents)
- PROJECT STATUS
- Customer Segmentation (K-Means, silhouette)
- Olist star schema diagram
- Graphify Knowledge Graph Usage Rules
- gcp
- stg_category_translation.sql
- stg_customers.sql
- stg_geolocation.sql
- stg_order_items.sql
- stg_order_payments.sql
- stg_order_reviews.sql
- stg_orders.sql
- stg_products.sql
- stg_sellers.sql
- position
- position
- position
- position
- position
- Architecture
- test_powerbi_project.py
- position
- D-002: Local only, no GCP
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- position
- fact_order_items (grain: order item, 112,650 rows)
- ARCHITECTURE.md
- argparse
- numpy
- model_spec.py
- drift_analysis.py
- Design decisions
- combination
- report.json
- delivery/page.json
- forecast/page.json
- risk/page.json
- sales/page.json
- Power BI project
- pages.json
- version.json

## God Nodes (most connected - your core abstractions)
1. `Phase 0 — Discovery Report` - 17 edges
2. `Design decisions` - 13 edges
3. `main()` - 12 edges
4. `day()` - 12 edges
5. `Final audit (Phase 10)` - 12 edges
6. `Architecture` - 12 edges
7. `run()` - 11 edges
8. `Business insights: Olist retail analytics` - 11 edges
9. `main()` - 10 edges
10. `files()` - 10 edges

## Surprising Connections (you probably didn't know these)
- `3. Data quality findings` --references--> `orders()`  [INFERRED]
  docs/phase0/PHASE0_DISCOVERY.md → tests/test_recalibration.py
- `DD-06: Convert geolocation CSV to Parquet in the build` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  DECISIONS.md → src/transformation/build_warehouse.py
- `Components` --references--> `run_sql_file()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Components` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Tests` --references--> `test_outcome_is_not_visible_at_the_instant_of_delivery()`  [INFERRED]
  docs/ml/PHASE2_BASELINES.md → tests/test_feature_leakage.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Late-delivery improvement attempts that did not beat v1** — docs_ml_phase2_baselines_v2_history_features, docs_ml_phase2_baselines_v3_trailing_rate, docs_ml_model_card_v5_slack_features, docs_ml_recalibration_and_window_recalibration, docs_ml_recalibration_and_window_window_tuning, decisions_dd_12 [EXTRACTED 1.00]
- **Local-only scope decisions (DuckDB, no GCP, plain SQL, no monitoring stack)** — decisions_d_001_implementations_use_duckdb, decisions_d_002, decisions_d_003_idiomatic_duckdb_sql, decisions_d_004, decisions_d_005_no_prometheus_grafana_or_fastapi [EXTRACTED 1.00]
- **Olist warehouse star schema (4 fact tables around 5 dimensions)** — docs_data_star_schema_fact_payments, docs_data_star_schema_fact_orders, docs_data_star_schema_fact_order_items, docs_data_star_schema_fact_reviews, docs_data_star_schema_dim_date, docs_data_star_schema_dim_geography, docs_data_star_schema_dim_product, docs_data_star_schema_dim_seller, docs_data_star_schema_dim_customer [EXTRACTED 1.00]
- **Promise and lateness chart: two metrics over one Olist monthly dataset** — docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_promise_and_lateness_orders_promised_under_20_days_pct, docs_analytics_figures_promise_and_lateness_olist_delivered_orders_data [EXTRACTED 1.00]
- **Reviews vs delay chart: metric, buckets, source and insight** — docs_analytics_figures_reviews_vs_delay_average_review_score, docs_analytics_figures_reviews_vs_delay_delivery_delay_bucket, docs_analytics_figures_reviews_vs_delay_olist_data_source, docs_analytics_figures_reviews_vs_delay_score_drops_with_lateness [EXTRACTED 1.00]
- **Delivery performance by state: metrics, insights and data source** — docs_analytics_figures_states_median_days_to_deliver, docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_states_slowest_states_insight, docs_analytics_figures_states_olist_orders_data [INFERRED 0.75]
- **Categories chart: metric, insight and data source** — docs_analytics_figures_categories_net_revenue_by_category_metric, docs_analytics_figures_categories_top_categories_insight, docs_analytics_figures_categories_olist_data_source [INFERRED 0.85]
- **Leakage controls: purchase-time prediction, point-in-time stats, time-ordered split, planted-leak tests** — docs_ml_leakage_analysis_purchase_time_prediction, docs_ml_leakage_analysis_point_in_time_statistics, docs_ml_leakage_analysis_time_ordered_split, docs_audit_planted_leak_checks [INFERRED 0.85]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]
- **Monthly KPIs chart: metrics, trend insight and data source** — docs_analytics_figures_monthly_kpis_net_revenue_per_month, docs_analytics_figures_monthly_kpis_average_order_value, docs_analytics_figures_monthly_kpis_olist_orders_data [INFERRED 0.85]

## Communities (116 total, 26 thin omitted)

### Community 0 - "PHASE2_BASELINES.md"
Cohesion: 0.13
Nodes (19): 2018 delivery promise shortened (75% of August orders under 20 days), 97% of customers buy once (repeat = 5.6% of revenue), Rio de Janeiro late-rate outlier (13.5% late, median 12 days), Seller concentration (top 10% of sellers = 67.5% of revenue), August 2018 delivery-promise policy shift, E1: single-feature skill, month by month, E2: persistence of route/category/seller lateness, E5: oracle true month late rate ceiling (+11 more)

### Community 1 - "late_delivery_baseline.py"
Cohesion: 0.10
Nodes (12): add_smoothed_rates(), calibration_table(), evaluate(), load(), main(), mean_days_to_deliver(), run(), top_share_metrics() (+4 more)

### Community 2 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.05
Nodes (41): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail) (+33 more)

### Community 3 - "recalibration.py"
Cohesion: 0.13
Nodes (22): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), main() (+14 more)

### Community 4 - "Recalibration and training window for the v1 late-delivery model"
Cohesion: 0.40
Nodes (5): Conclusions, Limits, R: recalibration on the latest resolved period, Recalibration and training window for the v1 late-delivery model, W: choosing the training window

### Community 5 - "Column audit for target A"
Cohesion: 0.12
Nodes (18): Planted-leak checks (tests shown to fail), Checklist from the brief, Column audit for target A, Customer history, `fact_order_items` (aggregate to order grain first, per DD-01), `fact_orders`, `fact_payments`, `fact_reviews` (+10 more)

### Community 6 - "run_analytics.py"
Cohesion: 0.08
Nodes (21): draw(), load_graph(), main(), node_label(), fig_categories(), fig_monthly(), fig_promise(), fig_reviews() (+13 more)

### Community 7 - "fact_order_items"
Cohesion: 0.14
Nodes (9): dim_customer, dim_date, dim_geography, dim_product, dim_seller, fact_order_items, fact_orders, fact_payments (+1 more)

### Community 8 - "pytest"
Cohesion: 0.06
Nodes (34): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, MiniWarehouse (+26 more)

### Community 9 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 10 - "Orders delivered late % (metric)"
Cohesion: 0.27
Nodes (8): Promise and Lateness Chart (late-delivery rate and under-20-day promises by month), Olist delivered orders by purchase month (months with at least 500 orders, 2017-01 to 2018-08), Orders Promised in Under 20 Days (%) metric, Delivery performance by customer state (chart), Median days to deliver (metric), Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time, Olist Brazilian e-commerce orders data (source), Orders delivered late % (metric)

### Community 11 - "pandas"
Cohesion: 0.17
Nodes (13): backtest(), linear_trend(), f(), main(), score(), weekly_series(), beats_naive_share(), main() (+5 more)

### Community 12 - "Business insights: Olist retail analytics"
Cohesion: 0.18
Nodes (11): 1. Growth: fast in 2017, flat in 2018, 2. What sells: broad, and not concentrated in a few categories, 3. Geography: one region carries the marketplace, and the north-east pays for distance, 4. Seller base: a long tail with a strong head, 5. Delivery and reviews: lateness is the clearest cost to customer satisfaction, 6. The delivery promise changed, and it is the main story of 2018, 7. Customers: almost everyone buys once, 8. Payments (+3 more)

### Community 13 - "Final audit (Phase 10)"
Cohesion: 0.18
Nodes (11): 1. Correctness, 2. Reproducibility, 3. Security, 4. Cost, 5. Architecture, 6. Testing, 7. Documentation, 8. Evidence (+3 more)

### Community 14 - "Data model: Olist star schema"
Cohesion: 0.20
Nodes (10): Data model: Olist star schema, Design rules, Dimensions, Entity-relationship diagram, `fact_order_items` - the core sales fact, `fact_orders` - order lifecycle, `fact_payments` - payments, `fact_reviews` - reviews (+2 more)

### Community 15 - "What was done and what came out"
Cohesion: 0.20
Nodes (10): August 2018 is a change in promise policy, not a label problem, Drift analysis: why the richer history features did not help, E2: does a route's, category's or seller's lateness persist?, E3 and E4: shorter training windows, and relative features, E5: what a perfect regime signal would buy, E6: is route history redundant with the state and distance columns?, Limits, Verdict (+2 more)

### Community 16 - "fact_order_items (PK: order_id, order_item_id; 112,650 rows)"
Cohesion: 0.42
Nodes (9): dim_customer (PK: customer_key; 96,097 rows), dim_date (PK: date_key; 1,828 rows), dim_geography (PK: geography_key; 19,012 rows), dim_product (PK: product_key; 32,952 rows), dim_seller (PK: seller_key; 3,096 rows), fact_order_items (PK: order_id, order_item_id; 112,650 rows), fact_orders (PK: order_id; 99,441 rows), fact_payments (PK: order_id, payment_sequential; 103,886 rows) (+1 more)

### Community 17 - "Net revenue by product category (R$ millions, share of total)"
Cohesion: 0.36
Nodes (8): Top 12 categories by net revenue chart (categories.png), bed_bath_table category (1.04M, 7.7%), health_beauty category (1.26M, 9.3%, top revenue category), Net revenue by product category (R$ millions, share of total), Olist Brazilian e-commerce retail dataset (net revenue, 74 categories), Revenue concentration: long-tail distribution, top category 9.3% down to 3.0% at rank 12, Top 12 categories account for 69% of net revenue across 74 categories, watches_gifts category (1.20M, 8.9%)

### Community 18 - "Net revenue per month (R$ millions)"
Cohesion: 0.32
Nodes (5): Monthly KPIs chart (net revenue and average order value), Average order value (R$), Net revenue per month (R$ millions), 2017-11 revenue peak (R$1.00M), Olist retail orders data (data source)

### Community 19 - "Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)"
Cohesion: 0.25
Nodes (8): 1. Get the data, 2. Set up and build the warehouse, 3. Run the baselines and tests, 4. Explore, Attribution, Repository map, Results at a glance, Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)

### Community 20 - "Chart: Average review score by how late the order arrived"
Cohesion: 0.43
Nodes (4): Chart: Average review score by how late the order arrived, Metric: Average review score (1 to 5), Delivery delay buckets (on time or early, 1-3, 4-7, 8-14, more than 14 days late), Data source: Olist retail delivered orders with a review

### Community 21 - "Handover: GCP Retail Analytics (local DuckDB build)"
Cohesion: 0.29
Nodes (7): Current state (2026-10-13), Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), Open items, What this project is now

### Community 22 - "Agentic Loop (PLAN to DECIDE)"
Cohesion: 0.33
Nodes (6): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done, Final Project Audit, Phase 0 Discovery (starting instruction)

### Community 23 - "Evidence Requirement and Evidence Integrity"
Cohesion: 0.33
Nodes (6): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git), Cloud IAM and Secret Manager, Evidence Checkpoints E01-E20

### Community 24 - "Security"
Cohesion: 0.33
Nodes (6): Data and privacy, Licence, Not applicable by design, Practices to keep, Security, What was checked (2026-10-13)

### Community 25 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): graphify, graphify knowledge graph (graphify-out/), graphify

### Community 26 - "AUDIT.md"
Cohesion: 0.17
Nodes (13): DD-11: No recalibration or window tuning; use the model by rank, Late delivery vs review score association (4.29 on time, 2.57 late), Open items, EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data (+5 more)

### Community 27 - "Lessons learned"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 28 - "duckdb"
Cohesion: 0.10
Nodes (13): main(), permutation_drop(), main(), render(), build(), mini(), warehouse(), manifest() (+5 more)

### Community 29 - "Model card"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

### Community 31 - "PROJECT STATUS"
Cohesion: 0.29
Nodes (7): Decisions, Headline results, Known limitations, Open items (from the audit), Phase status, PROJECT STATUS, Quality evidence

### Community 55 - "position"
Cohesion: 0.09
Nodes (22): projections, name, position, height, tabOrder, width, x, y (+14 more)

### Community 56 - "position"
Cohesion: 0.09
Nodes (22): projections, name, position, height, tabOrder, width, x, y (+14 more)

### Community 57 - "position"
Cohesion: 0.09
Nodes (22): projections, name, position, height, tabOrder, width, x, y (+14 more)

### Community 58 - "position"
Cohesion: 0.09
Nodes (22): projections, name, position, height, tabOrder, width, x, y (+14 more)

### Community 59 - "position"
Cohesion: 0.09
Nodes (22): projections, name, position, height, tabOrder, width, x, y (+14 more)

### Community 60 - "Architecture"
Cohesion: 0.10
Nodes (19): Architecture, Components, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing (+11 more)

### Community 61 - "test_powerbi_project.py"
Cohesion: 0.10
Nodes (11): _columns(), _fetch(), generated(), _json_files(), registry(), _retrieve(), test_committed_project_is_complete_and_holds_no_machine_path(), test_every_json_file_validates_against_its_published_schema() (+3 more)

### Community 62 - "position"
Cohesion: 0.09
Nodes (22): projections, name, position, height, tabOrder, width, x, y (+14 more)

### Community 63 - "D-002: Local only, no GCP"
Cohesion: 0.24
Nodes (8): Compute, Cost, If the project moved to the cloud, Total cloud cost $0, D-003: Idiomatic DuckDB SQL, Moving to BigQuery, Phase 0 cloud architecture proposal (GCS, BigQuery, Dataflow, Vertex AI), Unverified BigQuery, Dataflow and Vertex AI pricing

### Community 64 - "position"
Cohesion: 0.10
Nodes (20): name, position, height, tabOrder, width, x, y, z (+12 more)

### Community 65 - "position"
Cohesion: 0.10
Nodes (20): name, position, height, tabOrder, width, x, y, z (+12 more)

### Community 66 - "position"
Cohesion: 0.10
Nodes (20): name, position, height, tabOrder, width, x, y, z (+12 more)

### Community 67 - "position"
Cohesion: 0.10
Nodes (20): projections, name, position, height, tabOrder, width, x, y (+12 more)

### Community 68 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 69 - "position"
Cohesion: 0.10
Nodes (20): projections, name, position, height, tabOrder, width, x, y (+12 more)

### Community 70 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 71 - "position"
Cohesion: 0.10
Nodes (20): projections, name, position, height, tabOrder, width, x, y (+12 more)

### Community 72 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 73 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 74 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 75 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 76 - "position"
Cohesion: 0.10
Nodes (20): name, data, position, height, tabOrder, width, x, y (+12 more)

### Community 77 - "position"
Cohesion: 0.10
Nodes (20): projections, name, position, height, tabOrder, width, x, y (+12 more)

### Community 78 - "position"
Cohesion: 0.10
Nodes (20): projections, name, position, height, tabOrder, width, x, y (+12 more)

### Community 79 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 80 - "position"
Cohesion: 0.10
Nodes (20): filterConfig, filters, name, position, height, tabOrder, width, x (+12 more)

### Community 81 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 82 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 83 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 84 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 85 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 86 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 87 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 88 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 89 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 90 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 91 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 92 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 93 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 94 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 95 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 96 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 97 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 98 - "position"
Cohesion: 0.11
Nodes (18): name, position, height, tabOrder, width, x, y, z (+10 more)

### Community 99 - "fact_order_items (grain: order item, 112,650 rows)"
Cohesion: 0.18
Nodes (15): DD-02: Customer grain is `customer_unique_id`, Net revenue R$ 13.49M over 98,199 orders, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), fact_order_items (grain: order item, 112,650 rows) (+7 more)

### Community 100 - "ARCHITECTURE.md"
Cohesion: 0.19
Nodes (12): build_warehouse.py (build and validate script), warehouse.duckdb (single local database file), D-001: Implementations use DuckDB, D-005: No Prometheus, Grafana or FastAPI, DD-01: Kimball star schema; facts never join to facts, DD-06: Convert geolocation CSV to Parquet in the build, DD-07: Customer segmentation is optional, Clean-clone reproduction test (+4 more)

### Community 101 - "argparse"
Cohesion: 0.16
Nodes (7): build(), main(), score_test_months(), make_models(), export(), forecast_backtest(), main()

### Community 102 - "numpy"
Cohesion: 0.16
Nodes (14): ar1_with_trend(), series(), test_changing_future_weeks_does_not_change_earlier_forecasts(), test_horizon_shifts_the_target(), test_naive_and_moving_average_values(), test_score_is_below_one_for_a_better_model_than_naive(), series(), test_ar1_trend_extends_an_exact_linear_series() (+6 more)

### Community 103 - "model_spec.py"
Cohesion: 0.06
Nodes (33): dump(), field_json(), files(), lit(), m_load(), main(), projection(), prop() (+25 more)

### Community 106 - "drift_analysis.py"
Cohesion: 0.30
Nodes (8): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts()

### Community 107 - "Design decisions"
Cohesion: 0.13
Nodes (15): D-002: Local only, D-004: No dbt, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast, D-008: Untrack `data/`, DD-03: Reviews keyed on (`review_id`, `order_id`), DD-04: Revenue from order items only, DD-05: Surrogate keys with an unknown member (+7 more)

### Community 108 - "combination"
Cohesion: 0.17
Nodes (5): moving_average(), naive(), combination(), damped_trend(), simple_exponential_smoothing()

### Community 113 - "report.json"
Cohesion: 0.14
Nodes (16): name, reportVersionAtImport, type, name, reportVersionAtImport, type, page, report (+8 more)

### Community 118 - "delivery/page.json"
Cohesion: 0.29
Nodes (6): displayName, displayOption, height, name, $schema, width

### Community 119 - "forecast/page.json"
Cohesion: 0.29
Nodes (6): displayName, displayOption, height, name, $schema, width

### Community 120 - "risk/page.json"
Cohesion: 0.29
Nodes (6): displayName, displayOption, height, name, $schema, width

### Community 121 - "sales/page.json"
Cohesion: 0.29
Nodes (6): displayName, displayOption, height, name, $schema, width

### Community 122 - "Power BI project"
Cohesion: 0.33
Nodes (6): If the first refresh fails, Known limits, Open it, Optional, Power BI project, Regenerate (only to start over)

### Community 124 - "pages.json"
Cohesion: 0.50
Nodes (3): activePageName, pageOrder, $schema

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **33 isolated node(s):** `gcp`, `Seller history rate baseline`, `Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time`, `Olist Brazilian e-commerce orders data (source)`, `Seller concentration (top 10% of sellers = 67.5% of revenue)` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 890 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **26 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ensure_geolocation_parquet()` connect `Architecture` to `ARCHITECTURE.md`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **What connects `gcp`, `Seller history rate baseline`, `Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time` to the rest of the system?**
  _33 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `PHASE2_BASELINES.md` be split into smaller, more focused modules?**
  _Cohesion score 0.13043478260869565 - nodes in this community are weakly interconnected._
- **Why does `DD-06: Convert geolocation CSV to Parquet in the build` connect `ARCHITECTURE.md` to `Design decisions`, `fact_order_items (grain: order item, 112,650 rows)`, `Architecture`?**
  _High betweenness centrality (0.060) - this node is a cross-community bridge._
- **Should `late_delivery_baseline.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1032258064516129 - nodes in this community are weakly interconnected._
- **Why does `Phase 0 — Discovery Report` connect `Phase 0 — Discovery Report` to `ARCHITECTURE.md`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._