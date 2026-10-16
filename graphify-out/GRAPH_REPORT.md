# Graph Report - GCP  (2026-10-16)

## Corpus Check
- 46 files · ~95,939 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 890 nodes · 1680 edges · 70 communities (42 shown, 28 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 131 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Power BI Mock-up Build
- Test Suite and Fixtures
- Warehouse Dimensions and SQL
- Original Cloud Brief
- Data Model Documentation
- Recalibration Experiment
- Power BI Project Tests
- Architecture Overview
- Late-Delivery Baseline Models
- Schema Diagram Script
- ML Decisions DD-07 to DD-12
- Phase 2 Baselines Report
- Brief: Cloud Services and Risks
- Cost and Business Insights
- Explainability (Permutation)
- Forecast Baselines
- Core Decisions D-001 to D-006
- Score Export for Power BI
- Dimension SQL Files
- Architecture and Test Components
- Handoff and Data Untracking
- Drift Analysis Documents
- Drift Analysis Code
- Delivery Promise Charts
- EDA Findings and Setup
- Forecast Model Tests
- Audit Checklist
- Lessons and Validation Checks
- Business Insights Summary
- August 2018 Drift Findings
- Star Schema Tables
- Forecast Models (Damped, Combo)
- Category Revenue Charts
- Monthly KPI Charts
- Review Score vs Delay
- Brief: Agentic Loop and Phases
- Brief: Documentation and Security Standards
- Late-Delivery Helper Tests
- Security and Privacy
- Community 39
- Community 40
- Recalibration Conclusions
- Community 42
- Community 43
- Community 44
- Community 45
- Community 47
- Community 48
- Community 49
- Community 50
- Community 51
- Community 52
- Community 53
- Community 54
- Community 55
- Community 56
- Community 57
- Community 58
- Community 59

## God Nodes (most connected - your core abstractions)
1. `Late-delivery model (v1 logistic regression)` - 25 edges
2. `Phase 0 — Discovery Report` - 17 edges
3. `DD-11: No recalibration or window tuning; use the model by rank` - 14 edges
4. `Semantic model (12 tables, 13 relationships, 38 measures)` - 14 edges
5. `Design decisions` - 13 edges
6. `DD-10: Keep v1 features as reference late-delivery model` - 13 edges
7. `main()` - 12 edges
8. `DD-01: Kimball star schema; facts never join to facts` - 12 edges
9. `Final audit (Phase 10)` - 12 edges
10. `Architecture` - 12 edges

## Surprising Connections (you probably didn't know these)
- `3. Data quality findings` --references--> `orders()`  [INFERRED]
  docs/phase0/PHASE0_DISCOVERY.md → tests/test_recalibration.py
- `Use the model by rank, not probability` --semantically_similar_to--> `DD-11: No recalibration or window tuning; use the model by rank`  [INFERRED] [semantically similar]
  docs/ml/MODEL_CARD.md → DECISIONS.md
- `ML notebooks: Jupyter + marimo versions` --semantically_similar_to--> `Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions)`  [INFERRED] [semantically similar]
  docs/ml/MODEL_CARD.md → ARCHITECTURE.md
- `DD-06: Convert geolocation CSV to Parquet in the build` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  DECISIONS.md → src/transformation/build_warehouse.py
- `Components` --references--> `ensure_geolocation_parquet()`  [INFERRED]
  ARCHITECTURE.md → src/transformation/build_warehouse.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **GCP Cloud Data and ML Pipeline (GCS to Dataflow to BigQuery to Vertex AI to Monitoring)** — google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_google_cloud_storage, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_dataflow, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_bigquery, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_vertex_ai, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_cloud_monitoring [EXTRACTED 0.95]
- **Local Stack vs GCP Service Equivalents** — gcp_duckdb, gcp_apache_beam_direct_runner, gcp_mlflow, gcp_fastapi_serving, gcp_prometheus_grafana [EXTRACTED 0.95]
- **Olist warehouse star schema (4 fact tables around 5 dimensions)** — docs_data_star_schema_fact_payments, docs_data_star_schema_fact_orders, docs_data_star_schema_fact_order_items, docs_data_star_schema_fact_reviews, docs_data_star_schema_dim_date, docs_data_star_schema_dim_geography, docs_data_star_schema_dim_product, docs_data_star_schema_dim_seller, docs_data_star_schema_dim_customer [EXTRACTED 1.00]
- **Promise and lateness chart: two metrics over one Olist monthly dataset** — docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_promise_and_lateness_orders_promised_under_20_days_pct, docs_analytics_figures_promise_and_lateness_olist_delivered_orders_data [EXTRACTED 1.00]
- **Reviews vs delay chart: metric, buckets, source and insight** — docs_analytics_figures_reviews_vs_delay_average_review_score, docs_analytics_figures_reviews_vs_delay_delivery_delay_bucket, docs_analytics_figures_reviews_vs_delay_olist_data_source, docs_analytics_figures_reviews_vs_delay_score_drops_with_lateness [EXTRACTED 1.00]
- **Delivery performance by state: metrics, insights and data source** — docs_analytics_figures_states_median_days_to_deliver, docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_states_slowest_states_insight, docs_analytics_figures_states_olist_orders_data [INFERRED 0.75]
- **Categories chart: metric, insight and data source** — docs_analytics_figures_categories_net_revenue_by_category_metric, docs_analytics_figures_categories_top_categories_insight, docs_analytics_figures_categories_olist_data_source [INFERRED 0.85]
- **Leakage controls: purchase-time prediction, point-in-time stats, time-ordered split, planted-leak tests** — docs_ml_leakage_analysis_purchase_time_prediction, docs_ml_leakage_analysis_point_in_time_statistics, docs_ml_leakage_analysis_time_ordered_split, docs_audit_planted_leak_checks [INFERRED 0.85]
- **Local-first to Cloud Hybrid Strategy Across Docs** — cloud_portfolio_master_agent_prompt_local_first_cloud_aware, docs_architecture_philosophy_recommended_progression, gcp_local_pipeline, gcp_cloud_pipeline, google_cloud_project_retail_analytics_forecasting_customer_intelligence_platform_local_first_development [INFERRED 0.85]
- **Monthly KPIs chart: metrics, trend insight and data source** — docs_analytics_figures_monthly_kpis_net_revenue_per_month, docs_analytics_figures_monthly_kpis_average_order_value, docs_analytics_figures_monthly_kpis_olist_orders_data [INFERRED 0.85]
- **Kimball star schema: four facts conformed through five dimensions** — architecture_fact_orders, architecture_fact_order_items, architecture_fact_payments, architecture_fact_reviews, architecture_dim_date, architecture_dim_customer, architecture_dim_product, architecture_dim_seller, architecture_dim_geography [EXTRACTED 0.95]
- **Late-delivery improvement attempts that failed to beat v1** — docs_ml_model_card_features_v2, docs_ml_model_card_features_v3, docs_ml_model_card_features_v5_slack, docs_ml_model_card_recalibration, docs_ml_model_card_window_tuning, docs_ml_model_card_gradient_boosting [EXTRACTED 0.95]
- **Specification, mock-up and PBIP generated from one model_spec.py** — powerbi_readme_model_spec, docs_powerbi_dax_specification, powerbi_readme_dashboard_mockup, powerbi_readme_power_bi_dashboard [EXTRACTED 0.95]

## Communities (70 total, 28 thin omitted)

### Community 0 - "Power BI Mock-up Build"
Cohesion: 0.05
Nodes (37): main(), render(), dump(), field_json(), files(), lit(), m_load(), main() (+29 more)

### Community 1 - "Test Suite and Fixtures"
Cohesion: 0.05
Nodes (31): mini(), MiniWarehouse, warehouse(), net(), table(), test_category_revenue_matches_and_shares_are_consistent(), test_delay_buckets_cover_every_reviewed_delivered_order(), test_delivery_trend_covers_the_same_population_as_the_ml_features() (+23 more)

### Community 2 - "Warehouse Dimensions and SQL"
Cohesion: 0.06
Nodes (58): dim_customer, dim_date, dim_geography, dim_product, dim_seller, Dimension SQL (sql/dimensions), fact_order_items, fact_orders (+50 more)

### Community 3 - "Original Cloud Brief"
Cohesion: 0.05
Nodes (41): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail) (+33 more)

### Community 4 - "Data Model Documentation"
Cohesion: 0.06
Nodes (39): Data model: Olist star schema, Design rules, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), Dimensions (+31 more)

### Community 5 - "Recalibration Experiment"
Cohesion: 0.13
Nodes (21): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), make_calibrator() (+13 more)

### Community 6 - "Power BI Project Tests"
Cohesion: 0.10
Nodes (11): _columns(), _fetch(), generated(), _json_files(), registry(), _retrieve(), test_committed_project_is_complete_and_holds_no_machine_path(), test_every_json_file_validates_against_its_published_schema() (+3 more)

### Community 7 - "Architecture Overview"
Cohesion: 0.10
Nodes (20): Architecture, Components, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing (+12 more)

### Community 8 - "Late-Delivery Baseline Models"
Cohesion: 0.12
Nodes (11): add_smoothed_rates(), calibration_table(), evaluate(), load(), main(), make_models(), mean_days_to_deliver(), run() (+3 more)

### Community 9 - "Schema Diagram Script"
Cohesion: 0.20
Nodes (12): draw(), load_graph(), main(), node_label(), fig_categories(), fig_monthly(), fig_promise(), fig_reviews() (+4 more)

### Community 10 - "ML Decisions DD-07 to DD-12"
Cohesion: 0.16
Nodes (17): ML layer (src/ml, sql/ml), DD-12: Close the ML experiments; v1 and the simple forecasts are final, v4: relative route/category rate features, Always-predict-training-late-rate baseline, Grouped permutation importance, Features v2: route and category late-rate history, Features v3: trailing 28-day system late rate, Features v5: delivery-time slack (+9 more)

### Community 11 - "Phase 2 Baselines Report"
Cohesion: 0.13
Nodes (19): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+11 more)

### Community 12 - "Brief: Cloud Services and Risks"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 13 - "Cost and Business Insights"
Cohesion: 0.15
Nodes (15): Compute, Measured compute timings, Cost, If the project moved to the cloud, 2018 delivery promise shortened (75% of August orders under 20 days), Rio de Janeiro late-rate outlier (13.5% late, median 12 days), Seller concentration (top 10% of sellers = 67.5% of revenue), Insights correction: on-time orders produce ~70% of 1-2 star reviews (+7 more)

### Community 14 - "Explainability (Permutation)"
Cohesion: 0.14
Nodes (10): main(), permutation_drop(), beats_naive_share(), main(), main(), manifest(), test_exported_scores_reproduce_the_stored_pr_auc(), test_manifest_row_counts_equal_the_files() (+2 more)

### Community 15 - "Forecast Baselines"
Cohesion: 0.15
Nodes (12): backtest(), linear_trend(), f(), main(), naive(), score(), weekly_series(), series() (+4 more)

### Community 16 - "Core Decisions D-001 to D-006"
Cohesion: 0.16
Nodes (16): Total cloud cost $0, D-001: Implementations use DuckDB, D-002: Local only, D-003: Idiomatic DuckDB SQL, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast (+8 more)

### Community 17 - "Score Export for Power BI"
Cohesion: 0.16
Nodes (6): build(), main(), score_test_months(), export(), forecast_backtest(), main()

### Community 18 - "Dimension SQL Files"
Cohesion: 0.14
Nodes (9): dim_customer, dim_date, dim_geography, dim_product, dim_seller, fact_order_items, fact_orders, fact_payments (+1 more)

### Community 19 - "Architecture and Test Components"
Cohesion: 0.20
Nodes (9): Raw data (data/), Staging SQL (sql/staging), Test suite (96 pytest tests), Late delivery vs review score association (4.29 on time, 2.57 late), Planted-leak checks, Purchase-time (point-in-time) feature rule, Phase 0 cloud architecture proposal (GCS, BigQuery, Dataflow, Vertex AI), Olist Brazilian E-Commerce dataset (Kaggle, CC BY-NC-SA 4.0) (+1 more)

### Community 20 - "Handoff and Data Untracking"
Cohesion: 0.16
Nodes (12): Current state (2026-10-13), Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), graphify knowledge graph, Open items, What this project is now (+4 more)

### Community 21 - "Drift Analysis Documents"
Cohesion: 0.23
Nodes (11): DD-11: No recalibration or window tuning; use the model by rank, August 2018 delivery-promise policy shift, E1: single-feature skill, month by month, E2: persistence of route/category/seller lateness, E5: oracle true month late rate ceiling, E6: route history redundant with state and distance, Recalibration on latest resolved orders, Shorter / walk-forward training windows (+3 more)

### Community 22 - "Drift Analysis Code"
Cohesion: 0.30
Nodes (8): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts()

### Community 23 - "Delivery Promise Charts"
Cohesion: 0.27
Nodes (8): Promise and Lateness Chart (late-delivery rate and under-20-day promises by month), Olist delivered orders by purchase month (months with at least 500 orders, 2017-01 to 2018-08), Orders Promised in Under 20 Days (%) metric, Delivery performance by customer state (chart), Median days to deliver (metric), Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time, Olist Brazilian e-commerce orders data (source), Orders delivered late % (metric)

### Community 24 - "EDA Findings and Setup"
Cohesion: 0.14
Nodes (13): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data, 1. Get the data, 2. Set up and build the warehouse, 3. Run the baselines and tests (+5 more)

### Community 25 - "Forecast Model Tests"
Cohesion: 0.31
Nodes (8): series(), test_ar1_trend_extends_an_exact_linear_series(), test_combination_is_the_mean_of_its_parts(), test_constant_series_is_forecast_as_constant_by_every_model(), test_damped_trend_continues_a_rising_series_but_less_than_a_straight_line(), test_exponential_smoothing_follows_the_latest_level_after_a_step(), test_forecasts_are_never_negative(), test_no_model_sees_weeks_after_its_origin()

### Community 26 - "Audit Checklist"
Cohesion: 0.17
Nodes (12): 1. Correctness, 2. Reproducibility, 3. Security, 4. Cost, 5. Architecture, 6. Testing, 7. Documentation, 8. Evidence (+4 more)

### Community 27 - "Lessons and Validation Checks"
Cohesion: 0.20
Nodes (4): Validation checks (sql/validation/checks.sql, 22 checks), Clean-clone reproduction, August 2018 delivery promise change (concept drift), Monthly rolling-origin backtest (2018-03 to 2018-08)

### Community 28 - "Business Insights Summary"
Cohesion: 0.18
Nodes (11): 1. Growth: fast in 2017, flat in 2018, 2. What sells: broad, and not concentrated in a few categories, 3. Geography: one region carries the marketplace, and the north-east pays for distance, 4. Seller base: a long tail with a strong head, 5. Delivery and reviews: lateness is the clearest cost to customer satisfaction, 6. The delivery promise changed, and it is the main story of 2018, 7. Customers: almost everyone buys once, 8. Payments (+3 more)

### Community 29 - "August 2018 Drift Findings"
Cohesion: 0.20
Nodes (10): August 2018 is a change in promise policy, not a label problem, Drift analysis: why the richer history features did not help, E2: does a route's, category's or seller's lateness persist?, E3 and E4: shorter training windows, and relative features, E5: what a perfect regime signal would buy, E6: is route history redundant with the state and distance columns?, Limits, Verdict (+2 more)

### Community 30 - "Star Schema Tables"
Cohesion: 0.42
Nodes (9): dim_customer (PK: customer_key; 96,097 rows), dim_date (PK: date_key; 1,828 rows), dim_geography (PK: geography_key; 19,012 rows), dim_product (PK: product_key; 32,952 rows), dim_seller (PK: seller_key; 3,096 rows), fact_order_items (PK: order_id, order_item_id; 112,650 rows), fact_orders (PK: order_id; 99,441 rows), fact_payments (PK: order_id, payment_sequential; 103,886 rows) (+1 more)

### Community 31 - "Forecast Models (Damped, Combo)"
Cohesion: 0.22
Nodes (3): combination(), damped_trend(), simple_exponential_smoothing()

### Community 32 - "Category Revenue Charts"
Cohesion: 0.36
Nodes (8): Top 12 categories by net revenue chart (categories.png), bed_bath_table category (1.04M, 7.7%), health_beauty category (1.26M, 9.3%, top revenue category), Net revenue by product category (R$ millions, share of total), Olist Brazilian e-commerce retail dataset (net revenue, 74 categories), Revenue concentration: long-tail distribution, top category 9.3% down to 3.0% at rank 12, Top 12 categories account for 69% of net revenue across 74 categories, watches_gifts category (1.20M, 8.9%)

### Community 33 - "Monthly KPI Charts"
Cohesion: 0.32
Nodes (5): Monthly KPIs chart (net revenue and average order value), Average order value (R$), Net revenue per month (R$ millions), 2017-11 revenue peak (R$1.00M), Olist retail orders data (data source)

### Community 34 - "Review Score vs Delay"
Cohesion: 0.43
Nodes (4): Chart: Average review score by how late the order arrived, Metric: Average review score (1 to 5), Delivery delay buckets (on time or early, 1-3, 4-7, 8-14, more than 14 days late), Data source: Olist retail delivered orders with a review

### Community 35 - "Brief: Agentic Loop and Phases"
Cohesion: 0.33
Nodes (6): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done, Final Project Audit, Phase 0 Discovery (starting instruction)

### Community 36 - "Brief: Documentation and Security Standards"
Cohesion: 0.33
Nodes (6): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git), Cloud IAM and Secret Manager, Evidence Checkpoints E01-E20

### Community 38 - "Security and Privacy"
Cohesion: 0.33
Nodes (6): Data and privacy, Licence, Not applicable by design, Practices to keep, Security, What was checked (2026-10-13)

### Community 39 - "Community 39"
Cohesion: 0.50
Nodes (3): graphify, graphify knowledge graph (graphify-out/), graphify

### Community 40 - "Community 40"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 41 - "Recalibration Conclusions"
Cohesion: 0.40
Nodes (5): Conclusions, Limits, R: recalibration on the latest resolved period, Recalibration and training window for the v1 late-delivery model, W: choosing the training window

### Community 43 - "Community 43"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **41 isolated node(s):** `Seller concentration (top 10% of sellers = 67.5% of revenue)`, `Forecast baselines: naive, moving averages, linear trend`, `Gradient boosting baseline (depth 4)`, `Seller history rate baseline`, `Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time` (+36 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 337 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **28 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Original Cloud Brief` to `Core Decisions D-001 to D-006`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Late-delivery model (v1 logistic regression)` (e.g. with `ML layer (src/ml, sql/ml)` and `Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions)`) actually correct?**
  _`Late-delivery model (v1 logistic regression)` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Seller concentration (top 10% of sellers = 67.5% of revenue)`, `Forecast baselines: naive, moving averages, linear trend`, `Gradient boosting baseline (depth 4)` to the rest of the system?**
  _41 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Power BI Mock-up Build` be split into smaller, more focused modules?**
  _Cohesion score 0.0506558118498417 - nodes in this community are weakly interconnected._
- **Why does `Phase 0 — Discovery Report` connect `Brief: Cloud Services and Risks` to `Architecture and Test Components`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Should `Test Suite and Fixtures` be split into smaller, more focused modules?**
  _Cohesion score 0.052083333333333336 - nodes in this community are weakly interconnected._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._