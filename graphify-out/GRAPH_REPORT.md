# Graph Report - GCP  (2026-10-18)

## Corpus Check
- 116 files · ~112,783 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: .tmdl 16, .csv 8, (none) 5)

## Summary
- 973 nodes · 1782 edges · 84 communities (41 shown, 43 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 130 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ee0e35b2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- model_spec.py
- pytest
- Semantic model (12 tables, 13 relationships, 38 measures)
- Architecture Philosophy (Shared Across Cloud Projects)
- fact_order_items (grain: order item, 112,650 rows)
- test_bigquery_staging.py
- test_powerbi_project.py
- Architecture
- pandas
- run_analytics.py
- Late-delivery model (v1 logistic regression)
- test_feature_leakage.py
- Phase 0 — Discovery Report
- AUDIT.md
- duckdb
- forecast_baseline.py
- build_warehouse.py
- sql/bigquery — the same layers in GoogleSQL
- fact_order_items
- README.md
- powerbi/README.md
- BUSINESS_INSIGHTS.md
- `${PROJECT}.staging.stg_customers`
- Orders delivered late % (metric)
- Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)
- `${PROJECT}.staging.stg_geolocation`
- Final audit (Phase 10)
- EDA findings: Olist dataset discovery
- Business insights: Olist retail analytics
- What was done and what came out
- fact_order_items (PK: order_id, order_item_id; 112,650 rows)
- 5. Step by step
- Net revenue by product category (R$ millions, share of total)
- Net revenue per month (R$ millions)
- Chart: Average review score by how late the order arrived
- Agentic Loop (PLAN to DECIDE)
- Evidence Requirement and Evidence Integrity
- `${PROJECT}.staging.stg_order_items`
- Security
- AGENTS.md
- Lessons learned
- Recalibration and training window for the v1 late-delivery model
- DECISIONS.md
- Model card
- Cross-Cloud Learning (Azure/AWS/GCP equivalents)
- Customer Segmentation (K-Means, silhouette)
- `${PROJECT}.staging.stg_order_payments`
- Olist star schema diagram
- stg_category_translation.sql
- stg_customers.sql
- stg_geolocation.sql
- stg_order_items.sql
- stg_order_payments.sql
- stg_order_reviews.sql
- stg_orders.sql
- stg_products.sql
- stg_sellers.sql
- Graphify Knowledge Graph Usage Rules
- gcp
- `${PROJECT}.staging.stg_order_reviews`
- `${PROJECT}.staging.stg_orders`
- `${PROJECT}.staging.stg_products`
- `${PROJECT}.staging.stg_sellers`
- `${PROJECT}.staging.stg_category_translation`

## God Nodes (most connected - your core abstractions)
1. `Late-delivery model (v1 logistic regression)` - 25 edges
2. `Phase 0 — Discovery Report` - 17 edges
3. `DD-11: No recalibration or window tuning; use the model by rank` - 14 edges
4. `Semantic model (12 tables, 13 relationships, 38 measures)` - 14 edges
5. `Design decisions` - 13 edges
6. `DD-10: Keep v1 features as reference late-delivery model` - 13 edges
7. `main()` - 12 edges
8. `day()` - 12 edges
9. `5. Step by step` - 12 edges
10. `DD-01: Kimball star schema; facts never join to facts` - 12 edges

## Surprising Connections (you probably didn't know these)
- `3. What changes` --references--> `load()`  [INFERRED]
  docs/MIGRATING_TO_CLOUD.md → src/ml/late_delivery_baseline.py
- `3. Data quality findings` --references--> `orders()`  [INFERRED]
  docs/phase0/PHASE0_DISCOVERY.md → tests/test_recalibration.py
- `Components` --references--> `run_sql_file()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py
- `Use the model by rank, not probability` --semantically_similar_to--> `DD-11: No recalibration or window tuning; use the model by rank`  [INFERRED] [semantically similar]
  docs/ml/MODEL_CARD.md → DECISIONS.md
- `ML notebooks: Jupyter + marimo versions` --semantically_similar_to--> `Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions)`  [INFERRED] [semantically similar]
  docs/ml/MODEL_CARD.md → ARCHITECTURE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Late-delivery improvement attempts that failed to beat v1** — docs_ml_model_card_features_v2, docs_ml_model_card_features_v3, docs_ml_model_card_features_v5_slack, docs_ml_model_card_recalibration, docs_ml_model_card_window_tuning, docs_ml_model_card_gradient_boosting [EXTRACTED 0.95]
- **Specification, mock-up and PBIP generated from one model_spec.py** — powerbi_readme_model_spec, docs_powerbi_dax_specification, powerbi_readme_dashboard_mockup, powerbi_readme_power_bi_dashboard [EXTRACTED 0.95]
- **Kimball star schema: four facts conformed through five dimensions** — architecture_fact_orders, architecture_fact_order_items, architecture_fact_payments, architecture_fact_reviews, architecture_dim_date, architecture_dim_customer, architecture_dim_product, architecture_dim_seller, architecture_dim_geography [EXTRACTED 0.95]
- **Olist warehouse star schema (4 fact tables around 5 dimensions)** — docs_data_star_schema_fact_payments, docs_data_star_schema_fact_orders, docs_data_star_schema_fact_order_items, docs_data_star_schema_fact_reviews, docs_data_star_schema_dim_date, docs_data_star_schema_dim_geography, docs_data_star_schema_dim_product, docs_data_star_schema_dim_seller, docs_data_star_schema_dim_customer [EXTRACTED 1.00]
- **Promise and lateness chart: two metrics over one Olist monthly dataset** — docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_promise_and_lateness_orders_promised_under_20_days_pct, docs_analytics_figures_promise_and_lateness_olist_delivered_orders_data [EXTRACTED 1.00]
- **Reviews vs delay chart: metric, buckets, source and insight** — docs_analytics_figures_reviews_vs_delay_average_review_score, docs_analytics_figures_reviews_vs_delay_delivery_delay_bucket, docs_analytics_figures_reviews_vs_delay_olist_data_source, docs_analytics_figures_reviews_vs_delay_score_drops_with_lateness [EXTRACTED 1.00]
- **Delivery performance by state: metrics, insights and data source** — docs_analytics_figures_states_median_days_to_deliver, docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_states_slowest_states_insight, docs_analytics_figures_states_olist_orders_data [INFERRED 0.75]
- **Categories chart: metric, insight and data source** — docs_analytics_figures_categories_net_revenue_by_category_metric, docs_analytics_figures_categories_top_categories_insight, docs_analytics_figures_categories_olist_data_source [INFERRED 0.85]
- **Leakage controls: purchase-time prediction, point-in-time stats, time-ordered split, planted-leak tests** — docs_ml_leakage_analysis_purchase_time_prediction, docs_ml_leakage_analysis_point_in_time_statistics, docs_ml_leakage_analysis_time_ordered_split, docs_audit_planted_leak_checks [INFERRED 0.85]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]
- **Monthly KPIs chart: metrics, trend insight and data source** — docs_analytics_figures_monthly_kpis_net_revenue_per_month, docs_analytics_figures_monthly_kpis_average_order_value, docs_analytics_figures_monthly_kpis_olist_orders_data [INFERRED 0.85]

## Communities (84 total, 43 thin omitted)

### Community 0 - "model_spec.py"
Cohesion: 0.06
Nodes (33): dump(), field_json(), files(), lit(), m_load(), main(), projection(), prop() (+25 more)

### Community 1 - "pytest"
Cohesion: 0.06
Nodes (26): mini(), MiniWarehouse, warehouse(), net(), table(), test_category_revenue_matches_and_shares_are_consistent(), test_delay_buckets_cover_every_reviewed_delivered_order(), test_delivery_trend_covers_the_same_population_as_the_ml_features() (+18 more)

### Community 2 - "Semantic model (12 tables, 13 relationships, 38 measures)"
Cohesion: 0.09
Nodes (41): dim_customer, dim_date, dim_geography, dim_product, dim_seller, Dimension SQL (sql/dimensions), fact_order_items, fact_orders (+33 more)

### Community 3 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.05
Nodes (41): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail) (+33 more)

### Community 4 - "fact_order_items (grain: order item, 112,650 rows)"
Cohesion: 0.06
Nodes (39): Data model: Olist star schema, Design rules, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), Dimensions (+31 more)

### Community 5 - "test_bigquery_staging.py"
Cohesion: 0.22
Nodes (11): local_columns(), read(), stems(), strip_comments(), test_each_raw_file_is_an_external_table_over_its_csv(), test_each_staging_file_is_a_view_over_its_raw_table_with_the_typed_casts(), test_every_local_column_reaches_the_view(), test_raw_columns_match_the_local_column_list_in_order_and_as_strings() (+3 more)

### Community 6 - "test_powerbi_project.py"
Cohesion: 0.10
Nodes (11): _columns(), _fetch(), generated(), _json_files(), registry(), _retrieve(), test_committed_project_is_complete_and_holds_no_machine_path(), test_every_json_file_validates_against_its_published_schema() (+3 more)

### Community 7 - "Architecture"
Cohesion: 0.09
Nodes (19): Architecture, Components, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing (+11 more)

### Community 8 - "pandas"
Cohesion: 0.06
Nodes (42): main(), permutation_drop(), add_smoothed_rates(), calibration_table(), evaluate(), load(), main(), make_models() (+34 more)

### Community 9 - "run_analytics.py"
Cohesion: 0.38
Nodes (8): fig_categories(), fig_monthly(), fig_promise(), fig_reviews(), fig_states(), main(), run_queries(), save()

### Community 10 - "Late-delivery model (v1 logistic regression)"
Cohesion: 0.12
Nodes (22): DD-11: No recalibration or window tuning; use the model by rank, DD-12: Close the ML experiments; v1 and the simple forecasts are final, Phase 0 / EDA data findings, E1: single-feature skill, month by month, E2: persistence of route/category/seller lateness, E5: oracle true month late rate ceiling, E6: route history redundant with state and distance, v4: relative route/category rate features (+14 more)

### Community 11 - "test_feature_leakage.py"
Cohesion: 0.13
Nodes (19): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+11 more)

### Community 12 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 13 - "AUDIT.md"
Cohesion: 0.14
Nodes (17): Current state (2026-10-13), Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), graphify knowledge graph, Open items, What this project is now (+9 more)

### Community 14 - "duckdb"
Cohesion: 0.06
Nodes (27): draw(), load_graph(), main(), node_label(), add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag() (+19 more)

### Community 15 - "forecast_baseline.py"
Cohesion: 0.06
Nodes (27): backtest(), linear_trend(), f(), main(), moving_average(), naive(), score(), weekly_series() (+19 more)

### Community 16 - "build_warehouse.py"
Cohesion: 0.10
Nodes (22): Raw data (data/), Staging SQL (sql/staging), Validation checks (sql/validation/checks.sql, 22 checks), Compute, Measured compute timings, Cost, If the project moved to the cloud, Total cloud cost $0 (+14 more)

### Community 17 - "sql/bigquery — the same layers in GoogleSQL"
Cohesion: 0.33
Nodes (6): Alternative not taken, Folders, How to run (untested, like the rest of the guide), sql/bigquery — the same layers in GoogleSQL, Tokens, Type mapping

### Community 18 - "fact_order_items"
Cohesion: 0.14
Nodes (9): dim_customer, dim_date, dim_geography, dim_product, dim_seller, fact_order_items, fact_orders, fact_payments (+1 more)

### Community 19 - "README.md"
Cohesion: 0.18
Nodes (11): ML layer (src/ml, sql/ml), Test suite (96 pytest tests), Planted-leak checks, Purchase-time (point-in-time) feature rule, Weekly order forecast, Forecast baselines: naive, moving averages, linear trend, Gradient boosting baseline (depth 4), Seller history rate baseline (+3 more)

### Community 20 - "powerbi/README.md"
Cohesion: 0.14
Nodes (19): Power BI generators and project (src/powerbi, powerbi/), warehouse.duckdb, DD-06: Convert geolocation CSV to Parquet in the build, Out-of-time late-delivery scores export (export_scores.py), DASHBOARD_MOCKUP.html, DataFolder parameter, export_data.py (Power BI data export), First-open checklist (+11 more)

### Community 21 - "BUSINESS_INSIGHTS.md"
Cohesion: 0.22
Nodes (9): Late delivery vs review score association (4.29 on time, 2.57 late), Net revenue R$ 13.49M over 98,199 orders, 2018 delivery promise shortened (75% of August orders under 20 days), 97% of customers buy once (repeat = 5.6% of revenue), Rio de Janeiro late-rate outlier (13.5% late, median 12 days), Seller concentration (top 10% of sellers = 67.5% of revenue), Insights correction: on-time orders produce ~70% of 1-2 star reviews, August 2018 delivery-promise policy shift (+1 more)

### Community 23 - "Orders delivered late % (metric)"
Cohesion: 0.27
Nodes (8): Promise and Lateness Chart (late-delivery rate and under-20-day promises by month), Olist delivered orders by purchase month (months with at least 500 orders, 2017-01 to 2018-08), Orders Promised in Under 20 Days (%) metric, Delivery performance by customer state (chart), Median days to deliver (metric), Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time, Olist Brazilian e-commerce orders data (source), Orders delivered late % (metric)

### Community 24 - "Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)"
Cohesion: 0.25
Nodes (8): 1. Get the data, 2. Set up and build the warehouse, 3. Run the baselines and tests, 4. Explore, Attribution, Repository map, Results at a glance, Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)

### Community 26 - "Final audit (Phase 10)"
Cohesion: 0.17
Nodes (12): 1. Correctness, 2. Reproducibility, 3. Security, 4. Cost, 5. Architecture, 6. Testing, 7. Documentation, 8. Evidence (+4 more)

### Community 27 - "EDA findings: Olist dataset discovery"
Cohesion: 0.40
Nodes (5): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data

### Community 28 - "Business insights: Olist retail analytics"
Cohesion: 0.18
Nodes (11): 1. Growth: fast in 2017, flat in 2018, 2. What sells: broad, and not concentrated in a few categories, 3. Geography: one region carries the marketplace, and the north-east pays for distance, 4. Seller base: a long tail with a strong head, 5. Delivery and reviews: lateness is the clearest cost to customer satisfaction, 6. The delivery promise changed, and it is the main story of 2018, 7. Customers: almost everyone buys once, 8. Payments (+3 more)

### Community 29 - "What was done and what came out"
Cohesion: 0.20
Nodes (10): August 2018 is a change in promise policy, not a label problem, Drift analysis: why the richer history features did not help, E2: does a route's, category's or seller's lateness persist?, E3 and E4: shorter training windows, and relative features, E5: what a perfect regime signal would buy, E6: is route history redundant with the state and distance columns?, Limits, Verdict (+2 more)

### Community 30 - "fact_order_items (PK: order_id, order_item_id; 112,650 rows)"
Cohesion: 0.42
Nodes (9): dim_customer (PK: customer_key; 96,097 rows), dim_date (PK: date_key; 1,828 rows), dim_geography (PK: geography_key; 19,012 rows), dim_product (PK: product_key; 32,952 rows), dim_seller (PK: seller_key; 3,096 rows), fact_order_items (PK: order_id, order_item_id; 112,650 rows), fact_orders (PK: order_id; 99,441 rows), fact_payments (PK: order_id, payment_sequential; 103,886 rows) (+1 more)

### Community 31 - "5. Step by step"
Cohesion: 0.11
Nodes (19): 1. How the local build mirrors the cloud design, 2. What carries over unchanged, 3. What changes, 4. Decisions to make before starting, 5. Step by step, 6. A suggested layout for the cloud twin, Migrating from the local build to Google Cloud, Read this first: what is and is not verified (+11 more)

### Community 32 - "Net revenue by product category (R$ millions, share of total)"
Cohesion: 0.36
Nodes (8): Top 12 categories by net revenue chart (categories.png), bed_bath_table category (1.04M, 7.7%), health_beauty category (1.26M, 9.3%, top revenue category), Net revenue by product category (R$ millions, share of total), Olist Brazilian e-commerce retail dataset (net revenue, 74 categories), Revenue concentration: long-tail distribution, top category 9.3% down to 3.0% at rank 12, Top 12 categories account for 69% of net revenue across 74 categories, watches_gifts category (1.20M, 8.9%)

### Community 33 - "Net revenue per month (R$ millions)"
Cohesion: 0.32
Nodes (5): Monthly KPIs chart (net revenue and average order value), Average order value (R$), Net revenue per month (R$ millions), 2017-11 revenue peak (R$1.00M), Olist retail orders data (data source)

### Community 34 - "Chart: Average review score by how late the order arrived"
Cohesion: 0.43
Nodes (4): Chart: Average review score by how late the order arrived, Metric: Average review score (1 to 5), Delivery delay buckets (on time or early, 1-3, 4-7, 8-14, more than 14 days late), Data source: Olist retail delivered orders with a review

### Community 35 - "Agentic Loop (PLAN to DECIDE)"
Cohesion: 0.33
Nodes (6): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done, Final Project Audit, Phase 0 Discovery (starting instruction)

### Community 36 - "Evidence Requirement and Evidence Integrity"
Cohesion: 0.33
Nodes (6): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git), Cloud IAM and Secret Manager, Evidence Checkpoints E01-E20

### Community 38 - "Security"
Cohesion: 0.33
Nodes (6): Data and privacy, Licence, Not applicable by design, Practices to keep, Security, What was checked (2026-10-13)

### Community 39 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): graphify, graphify knowledge graph (graphify-out/), graphify

### Community 40 - "Lessons learned"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 41 - "Recalibration and training window for the v1 late-delivery model"
Cohesion: 0.40
Nodes (5): Conclusions, Limits, R: recalibration on the latest resolved period, Recalibration and training window for the v1 late-delivery model, W: choosing the training window

### Community 42 - "DECISIONS.md"
Cohesion: 0.29
Nodes (4): Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions), DD-07: Customer segmentation is optional, ML notebooks: Jupyter + marimo versions, Monthly rolling-origin backtest (2018-03 to 2018-08)

### Community 43 - "Model card"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **41 isolated node(s):** `gcp`, `Always-predict-training-late-rate baseline`, `Seller own-history rate baseline`, `Grouped permutation importance`, `Seller concentration (top 10% of sellers = 67.5% of revenue)` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 390 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **43 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Architecture Philosophy (Shared Across Cloud Projects)` to `DECISIONS.md`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Late-delivery model (v1 logistic regression)` (e.g. with `ML layer (src/ml, sql/ml)` and `Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions)`) actually correct?**
  _`Late-delivery model (v1 logistic regression)` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `gcp`, `Always-predict-training-late-rate baseline`, `Seller own-history rate baseline` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `model_spec.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06140350877192982 - nodes in this community are weakly interconnected._
- **Why does `Phase 0 — Discovery Report` connect `Phase 0 — Discovery Report` to `README.md`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Should `pytest` be split into smaller, more focused modules?**
  _Cohesion score 0.05565638233514821 - nodes in this community are weakly interconnected._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._