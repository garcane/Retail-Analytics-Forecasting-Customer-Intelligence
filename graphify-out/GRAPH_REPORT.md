# Graph Report - GCP  (2026-10-18)

## Corpus Check
- 116 files · ~112,835 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 35 file(s) not represented in the graph (top: .tmdl 16, .csv 8, (none) 5)

## Summary
- 974 nodes · 1773 edges · 91 communities (48 shown, 43 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 125 edges (avg confidence: 0.84)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b5c56e93`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- model_spec.py
- test_marimo.py
- Semantic model (12 tables, 13 relationships, 38 measures)
- Architecture Philosophy (Shared Across Cloud Projects)
- fact_order_items (grain: order item, 112,650 rows)
- test_bigquery_staging.py
- test_powerbi_project.py
- duckdb
- recalibration.py
- run_analytics.py
- Late-delivery model (v1 logistic regression)
- pytest
- Phase 0 — Discovery Report
- AUDIT.md
- argparse
- forecast_baseline.py
- D-002: Local only, no GCP
- sql/bigquery — the same layers in GoogleSQL
- fact_order_items
- DECISIONS.md
- powerbi/README.md
- DRIFT_ANALYSIS.md
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
- D-007: ML target is late delivery plus weekly order forecast
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
- late_delivery_baseline.py
- json
- numpy
- pandas
- drift_analysis.py
- GCP Retail Project: Local vs. Cloud Architecture
- Handover: GCP Retail Analytics (local DuckDB build)

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
- `3. Data quality findings` --references--> `orders()`  [INFERRED]
  docs/phase0/PHASE0_DISCOVERY.md → tests/test_recalibration.py
- `3. What changes` --references--> `load()`  [INFERRED]
  docs/MIGRATING_TO_CLOUD.md → src/ml/late_delivery_baseline.py
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
- **Late-delivery improvement attempts that failed to beat v1** — docs_ml_model_card_features_v2, docs_ml_model_card_features_v3, docs_ml_model_card_features_v5_slack, docs_ml_model_card_recalibration, docs_ml_model_card_window_tuning, docs_ml_model_card_gradient_boosting [EXTRACTED 0.95]
- **Specification, mock-up and PBIP generated from one model_spec.py** — powerbi_readme_model_spec, docs_powerbi_dax_specification, powerbi_readme_dashboard_mockup, powerbi_readme_power_bi_dashboard [EXTRACTED 0.95]
- **Kimball star schema: four facts conformed through five dimensions** — architecture_fact_orders, architecture_fact_order_items, architecture_fact_payments, architecture_fact_reviews, architecture_dim_date, architecture_dim_customer, architecture_dim_product, architecture_dim_seller, architecture_dim_geography [EXTRACTED 0.95]
- **Olist warehouse star schema (4 fact tables around 5 dimensions)** — docs_data_star_schema_fact_payments, docs_data_star_schema_fact_orders, docs_data_star_schema_fact_order_items, docs_data_star_schema_fact_reviews, docs_data_star_schema_dim_date, docs_data_star_schema_dim_geography, docs_data_star_schema_dim_product, docs_data_star_schema_dim_seller, docs_data_star_schema_dim_customer [EXTRACTED 1.00]
- **Promise and lateness chart: two metrics over one Olist monthly dataset** — docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_promise_and_lateness_orders_promised_under_20_days_pct, docs_analytics_figures_promise_and_lateness_olist_delivered_orders_data [EXTRACTED 1.00]
- **Reviews vs delay chart: metric, buckets, source and insight** — docs_analytics_figures_reviews_vs_delay_average_review_score, docs_analytics_figures_reviews_vs_delay_delivery_delay_bucket, docs_analytics_figures_reviews_vs_delay_olist_data_source, docs_analytics_figures_reviews_vs_delay_score_drops_with_lateness [EXTRACTED 1.00]
- **Delivery performance by state: metrics, insights and data source** — docs_analytics_figures_states_median_days_to_deliver, docs_analytics_figures_states_orders_delivered_late_pct, docs_analytics_figures_states_slowest_states_insight, docs_analytics_figures_states_olist_orders_data [INFERRED 0.75]
- **Categories chart: metric, insight and data source** — docs_analytics_figures_categories_net_revenue_by_category_metric, docs_analytics_figures_categories_top_categories_insight, docs_analytics_figures_categories_olist_data_source [INFERRED 0.85]
- **Leakage controls: purchase-time prediction, point-in-time stats, time-ordered split, planted-leak tests** — docs_ml_leakage_analysis_purchase_time_prediction, docs_ml_leakage_analysis_point_in_time_statistics, docs_ml_leakage_analysis_time_ordered_split, docs_audit_planted_leak_checks [INFERRED 0.85]
- **Monthly KPIs chart: metrics, trend insight and data source** — docs_analytics_figures_monthly_kpis_net_revenue_per_month, docs_analytics_figures_monthly_kpis_average_order_value, docs_analytics_figures_monthly_kpis_olist_orders_data [INFERRED 0.85]

## Communities (91 total, 43 thin omitted)

### Community 0 - "model_spec.py"
Cohesion: 0.06
Nodes (34): dump(), field_json(), files(), lit(), m_load(), main(), projection(), prop() (+26 more)

### Community 1 - "test_marimo.py"
Cohesion: 0.13
Nodes (9): test_file_is_a_marimo_app_that_only_uses_existing_project_modules(), test_interactive_controls_are_present(), test_marimo_check_passes(), test_no_machine_specific_paths(), code_cells(), notebook(), test_every_code_cell_was_executed_without_error(), test_notebook_code_parses_and_only_imports_modules_that_exist() (+1 more)

### Community 2 - "Semantic model (12 tables, 13 relationships, 38 measures)"
Cohesion: 0.09
Nodes (42): dim_customer, dim_date, dim_geography, dim_product, dim_seller, Dimension SQL (sql/dimensions), fact_order_items, fact_orders (+34 more)

### Community 3 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.05
Nodes (32): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail) (+24 more)

### Community 4 - "fact_order_items (grain: order item, 112,650 rows)"
Cohesion: 0.06
Nodes (39): Data model: Olist star schema, Design rules, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), Dimensions (+31 more)

### Community 5 - "test_bigquery_staging.py"
Cohesion: 0.22
Nodes (11): local_columns(), read(), stems(), strip_comments(), test_each_raw_file_is_an_external_table_over_its_csv(), test_each_staging_file_is_a_view_over_its_raw_table_with_the_typed_casts(), test_every_local_column_reaches_the_view(), test_raw_columns_match_the_local_column_list_in_order_and_as_strings() (+3 more)

### Community 6 - "test_powerbi_project.py"
Cohesion: 0.10
Nodes (11): _columns(), _fetch(), generated(), _json_files(), registry(), _retrieve(), test_committed_project_is_complete_and_holds_no_machine_path(), test_every_json_file_validates_against_its_published_schema() (+3 more)

### Community 7 - "duckdb"
Cohesion: 0.06
Nodes (25): Architecture, Components, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing (+17 more)

### Community 8 - "recalibration.py"
Cohesion: 0.13
Nodes (22): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), main() (+14 more)

### Community 9 - "run_analytics.py"
Cohesion: 0.20
Nodes (12): draw(), load_graph(), main(), node_label(), fig_categories(), fig_monthly(), fig_promise(), fig_reviews() (+4 more)

### Community 10 - "Late-delivery model (v1 logistic regression)"
Cohesion: 0.13
Nodes (16): Test suite (96 pytest tests), DD-11: No recalibration or window tuning; use the model by rank, DD-12: Close the ML experiments; v1 and the simple forecasts are final, Planted-leak checks, August 2018 delivery promise change (concept drift), Always-predict-training-late-rate baseline, Grouped permutation importance, Features v2: route and category late-rate history (+8 more)

### Community 11 - "pytest"
Cohesion: 0.09
Nodes (31): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, net() (+23 more)

### Community 12 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 13 - "AUDIT.md"
Cohesion: 0.16
Nodes (14): Compute, Measured compute timings, Cost, If the project moved to the cloud, Total cloud cost $0, Decisions, Headline results, Known limitations (+6 more)

### Community 14 - "argparse"
Cohesion: 0.17
Nodes (6): build(), main(), score_test_months(), export(), forecast_backtest(), main()

### Community 15 - "forecast_baseline.py"
Cohesion: 0.06
Nodes (21): backtest(), linear_trend(), f(), main(), moving_average(), naive(), score(), weekly_series() (+13 more)

### Community 16 - "D-002: Local only, no GCP"
Cohesion: 0.16
Nodes (13): Validation checks (sql/validation/checks.sql, 22 checks), D-001: Implementations use DuckDB, D-002: Local only, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast, D-008: Untrack `data/` (+5 more)

### Community 17 - "sql/bigquery — the same layers in GoogleSQL"
Cohesion: 0.33
Nodes (6): Alternative not taken, Folders, How to run (untested, like the rest of the guide), sql/bigquery — the same layers in GoogleSQL, Tokens, Type mapping

### Community 18 - "fact_order_items"
Cohesion: 0.14
Nodes (9): dim_customer, dim_date, dim_geography, dim_product, dim_seller, fact_order_items, fact_orders, fact_payments (+1 more)

### Community 19 - "DECISIONS.md"
Cohesion: 0.20
Nodes (12): Raw data (data/), Staging SQL (sql/staging), D-003: Idiomatic DuckDB SQL, Phase 0 / EDA data findings, graphify knowledge graph, Forecast baselines: naive, moving averages, linear trend, Gradient boosting baseline (depth 4), Seller history rate baseline (+4 more)

### Community 20 - "powerbi/README.md"
Cohesion: 0.14
Nodes (19): Power BI generators and project (src/powerbi, powerbi/), warehouse.duckdb, DD-06: Convert geolocation CSV to Parquet in the build, Out-of-time late-delivery scores export (export_scores.py), DASHBOARD_MOCKUP.html, DataFolder parameter, export_data.py (Power BI data export), First-open checklist (+11 more)

### Community 21 - "DRIFT_ANALYSIS.md"
Cohesion: 0.15
Nodes (15): Late delivery vs review score association (4.29 on time, 2.57 late), 2018 delivery promise shortened (75% of August orders under 20 days), Rio de Janeiro late-rate outlier (13.5% late, median 12 days), Seller concentration (top 10% of sellers = 67.5% of revenue), Insights correction: on-time orders produce ~70% of 1-2 star reviews, August 2018 delivery-promise policy shift, E1: single-feature skill, month by month, E2: persistence of route/category/seller lateness (+7 more)

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
Nodes (18): 1. How the local build mirrors the cloud design, 2. What carries over unchanged, 4. Decisions to make before starting, 5. Step by step, 6. A suggested layout for the cloud twin, Migrating from the local build to Google Cloud, Read this first: what is and is not verified, Step 10. Power BI on BigQuery (+10 more)

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

### Community 42 - "D-007: ML target is late delivery plus weekly order forecast"
Cohesion: 0.21
Nodes (7): ML layer (src/ml, sql/ml), Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions), DD-07: Customer segmentation is optional, 97% of customers buy once (repeat = 5.6% of revenue), Gradient boosting baseline, ML notebooks: Jupyter + marimo versions, Weekly order forecast

### Community 43 - "Model card"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

### Community 84 - "late_delivery_baseline.py"
Cohesion: 0.12
Nodes (10): 3. What changes, add_smoothed_rates(), calibration_table(), evaluate(), load(), main(), mean_days_to_deliver(), run() (+2 more)

### Community 85 - "json"
Cohesion: 0.15
Nodes (7): main(), permutation_drop(), make_models(), main(), render(), build(), test_exported_scores_reproduce_the_stored_pr_auc()

### Community 86 - "numpy"
Cohesion: 0.21
Nodes (9): ar1_with_trend(), series(), test_ar1_trend_extends_an_exact_linear_series(), test_combination_is_the_mean_of_its_parts(), test_constant_series_is_forecast_as_constant_by_every_model(), test_damped_trend_continues_a_rising_series_but_less_than_a_straight_line(), test_exponential_smoothing_follows_the_latest_level_after_a_step(), test_forecasts_are_never_negative() (+1 more)

### Community 87 - "pandas"
Cohesion: 0.26
Nodes (8): frame(), test_relative_rates_are_positive_for_a_late_route(), test_relative_rates_are_zero_when_route_matches_the_system(), test_system_counts_do_not_depend_on_row_order(), test_system_counts_use_only_orders_delivered_strictly_before_purchase(), test_smoothing_does_not_modify_the_input(), test_smoothing_returns_prior_without_history_and_raw_rate_with_lots(), test_top_share_metrics()

### Community 88 - "drift_analysis.py"
Cohesion: 0.30
Nodes (8): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts()

### Community 89 - "GCP Retail Project: Local vs. Cloud Architecture"
Cohesion: 0.20
Nodes (9): 1. Cloud vs. Local Architecture Mapping, 2. End-to-End Pipeline Workflow, 3. Key GCP Technologies & Portability, Analytics Engine (DuckDB vs BigQuery), Apache Beam / Dataflow Portability, Cloud Deployment Pipeline, GCP Retail Project: Local vs. Cloud Architecture, Local Development Pipeline (+1 more)

### Community 90 - "Handover: GCP Retail Analytics (local DuckDB build)"
Cohesion: 0.29
Nodes (7): Current state (2026-10-13), Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), Open items, What this project is now

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **42 isolated node(s):** `gcp`, `Always-predict-training-late-rate baseline`, `Seller own-history rate baseline`, `Grouped permutation importance`, `graphify knowledge graph` (+37 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 398 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **43 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Architecture Philosophy (Shared Across Cloud Projects)` to `DECISIONS.md`?**
  _High betweenness centrality (0.069) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `Late-delivery model (v1 logistic regression)` (e.g. with `ML layer (src/ml, sql/ml)` and `Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions)`) actually correct?**
  _`Late-delivery model (v1 logistic regression)` has 5 INFERRED edges - model-reasoned connections that need verification._
- **What connects `gcp`, `Always-predict-training-late-rate baseline`, `Seller own-history rate baseline` to the rest of the system?**
  _42 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `model_spec.py` be split into smaller, more focused modules?**
  _Cohesion score 0.058445353594389245 - nodes in this community are weakly interconnected._
- **Why does `Phase 0 — Discovery Report` connect `Phase 0 — Discovery Report` to `DECISIONS.md`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Should `test_marimo.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1341991341991342 - nodes in this community are weakly interconnected._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._