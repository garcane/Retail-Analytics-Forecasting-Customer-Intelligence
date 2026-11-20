# Graph Report - Retail-Analytics-Forecasting-Customer-Intelligence  (2026-11-20)

## Corpus Check
- 342 files · ~331,779 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 57 file(s) not represented in the graph (top: .tmdl 17, (none) 11, .css 9)

## Summary
- 2721 nodes · 4901 edges · 293 communities (136 shown, 157 thin omitted)
- Extraction: 94% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 269 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `41c7806d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- build_spec_html.py
- test_notebooks.py
- Design decisions
- Architecture Philosophy (Shared Across Cloud Projects)
- fact_order_items (grain: order item, 112,650 rows)
- re
- test_powerbi_project.py
- test_geolocation_staging.py
- recalibration.py
- run_analytics.py
- Late-delivery model (v1 logistic regression)
- test_feature_leakage.py
- Phase 0 — Discovery Report
- AUDIT.md
- Architecture
- weekly_series
- DECISIONS.md
- SnowparkAccess
- fact_order_items
- Model card
- Recalibration and training window for the v1 late-delivery model
- test_reconciliation.py
- `${PROJECT}.staging.stg_customers`
- Orders delivered late % (metric)
- Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)
- `${PROJECT}.staging.stg_geolocation`
- Final audit (Phase 10)
- powerbi/README.md
- Business insights: Olist retail analytics
- What was done and what came out
- fact_order_items (PK: order_id, order_item_id; 112,650 rows)
- 5. Step by step
- Net revenue by product category (R$ millions, share of total)
- Net revenue per month (R$ millions)
- Chart: Average review score by how late the order arrived
- Agentic Loop (PLAN to DECIDE)
- Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY)
- `${PROJECT}.staging.stg_order_items`
- datasets.py
- AGENTS.md
- test_register_model.py
- stage_wrapper
- el
- datasets
- Cross-Cloud Learning (Azure/AWS/GCP equivalents)
- story.mjs
- Retail Analytics, Forecasting & Customer Intelligence Platform
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
- pandas
- duckdb
- Section 3: Tier 1 DAX Optimization Patterns
- Check details
- drift_analysis.py
- pathlib
- Data dictionary: Snowflake + dbt implementation
- load_raw.py
- compare.py
- test_powerbi_snowflake.py
- fetch.py
- test_snowflake_ingestion.py
- report.py
- numpy
- cli.py
- checks.py
- pytest
- backend.py
- render_data_dictionary.py
- test_data_access.py
- load_table
- apply_snowflake_source.py
- test_publish_ml.py
- writeback.py
- Semantic model (12 tables, 13 relationships, 38 measures)
- validate_frame
- json
- Snowflake + dbt implementation: setup and runbook
- build_pbip.py
- 4. Procedure
- Power BI Semantic Model Authoring — CLI Skill
- model_spec.py
- format.js
- ddl_raw.sql
- Unslop
- Tokens
- Snowflake Retail Project: Local vs. Cloud Architecture
- table_tmdl
- Snowflake + dbt architecture
- FakeCursor
- test_dashboard.py
- Signs of slop
- test_feature_determinism.py
- data_dir
- _statements
- Comparison
- Staging (STAGING, views)
- Marts, core star schema (MARTS, tables)
- Power BI views (PBI, views)
- dbt project: Olist on Snowflake
- orders
- FakeCursor
- README.md
- serve.py
- SKILL.md
- Effects
- Visuals
- FakeConn
- retail-olist-dbt
- Intermediate (INTERMEDIATE, views)
- MLOps Lifecycle
- Security
- register_model.py
- DAX Query Syntax Rules
- ConfirmationRequired
- needs_real_data
- DAX Performance Decision Guide
- test_yes_flag_is_passed_to_connect_as_confirmation
- make_snowflake_notebooks.py
- Semantic Model Connection Binding Reference
- TMDL Guidelines
- DuckDB to Snowflake + dbt: SQL migration inventory
- Semantic Model Modeling Guidelines
- test_warehouse.py
- Field Parameters Reference
- ARCHITECTURE.md
- test_drift_helpers.py
- Column audit for target A
- Retail analytics dashboard (HTML)
- Semantic Model Metadata Discovery — DAX INFO Functions
- retail-olist-ml-registry
- build_mockup_html.py
- test_scoring_task_sql.py
- MiniWarehouse
- damped_trend
- Lessons learned
- forecast_baseline.py
- 0. Gathering Business Context
- scoring_task.sql
- Semantic Model REST API Reference
- Naming Conventions for Power BI Semantic Models
- test_notebooks_snowflake.py
- visualize_schema.py
- parametrize
- Properties Retrieval
- parametrize
- Power BI Project file (PBIP)
- Phase 1: Establish Baseline
- Direct Lake Modeling Guidelines
- EDA findings: Olist dataset discovery
- Phase 2: Optimization Iterations
- month
- load_dataset
- semantic-model-authoring

## God Nodes (most connected - your core abstractions)
1. `el()` - 41 edges
2. `Retail Analytics, Forecasting & Customer Intelligence Platform` - 35 edges
3. `DataAccess` - 26 edges
4. `Late-delivery model (v1 logistic regression)` - 25 edges
5. `Check details` - 23 edges
6. `Section 3: Tier 1 DAX Optimization Patterns` - 22 edges
7. `run_main()` - 21 edges
8. `lineChart()` - 20 edges
9. `barChart()` - 19 edges
10. `Power BI Semantic Model Authoring — CLI Skill` - 19 edges

## Surprising Connections (you probably didn't know these)
- `3. What changes` --references--> `load()`  [INFERRED]
  docs/MIGRATING_TO_CLOUD.md → src/ml/late_delivery_baseline.py
- `Type System` --references--> `Table`  [INFERRED]
  .claude/skills/semantic-model-authoring/references/dax-guidelines.md → src/powerbi/model_spec.py
- `Workflow: Rename or delete a field parameter` --references--> `table()`  [INFERRED]
  .claude/skills/semantic-model-authoring/references/field-parameters.md → tests/test_analytics.py
- `Key Rules` --references--> `read()`  [INFERRED]
  .claude/skills/semantic-model-authoring/references/tmdl-guidelines.md → tests/test_bigquery_staging.py
- ``mart_weekly_orders_revenue`` --references--> `orders()`  [INFERRED]
  docs/data_dictionary/DATA_DICTIONARY.md → tests/test_recalibration.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
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

## Communities (293 total, 157 thin omitted)

### Community 0 - "build_spec_html.py"
Cohesion: 0.17
Nodes (9): edge_point(), field_text(), main(), manifest(), model_svg(), render(), wireframe(), compute_checks() (+1 more)

### Community 1 - "test_notebooks.py"
Cohesion: 0.27
Nodes (5): code_cells(), notebook(), test_every_code_cell_was_executed_without_error(), test_notebook_code_parses_and_only_imports_modules_that_exist(), test_the_charts_are_stored_in_the_notebook()

### Community 2 - "Design decisions"
Cohesion: 0.12
Nodes (30): dim_customer, dim_date, dim_geography, dim_product, dim_seller, Dimension SQL (sql/dimensions), fact_order_items, fact_orders (+22 more)

### Community 3 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.14
Nodes (9): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail), Architecture Philosophy (Shared Across Cloud Projects), dbt as First-Class Component, Multi-Cloud View (three production targets of one philosophy) (+1 more)

### Community 4 - "fact_order_items (grain: order item, 112,650 rows)"
Cohesion: 0.12
Nodes (22): Data model: Olist star schema, Design rules, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), Dimensions (+14 more)

### Community 5 - "re"
Cohesion: 0.21
Nodes (12): local_columns(), read(), stems(), strip_comments(), test_each_raw_file_is_an_external_table_over_its_csv(), test_each_staging_file_is_a_view_over_its_raw_table_with_the_typed_casts(), test_every_local_column_reaches_the_view(), test_raw_columns_match_the_local_column_list_in_order_and_as_strings() (+4 more)

### Community 6 - "test_powerbi_project.py"
Cohesion: 0.05
Nodes (40): Action versions, CI setup (GitHub Actions), dbt-ci, dbt-live (manual), Kaggle secret, Power BI DataFolder after saving in Desktop, python-ci, Repository hygiene note (+32 more)

### Community 7 - "test_geolocation_staging.py"
Cohesion: 0.18
Nodes (8): Components, check_raw_files(), main(), run_sql_file(), data_dir(), test_missing_raw_file_gives_a_clear_error(), test_no_parquet_is_read_or_written(), test_staging_keeps_leading_zeros_and_types()

### Community 8 - "recalibration.py"
Cohesion: 0.23
Nodes (12): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), main() (+4 more)

### Community 9 - "run_analytics.py"
Cohesion: 0.38
Nodes (8): fig_categories(), fig_monthly(), fig_promise(), fig_reviews(), fig_states(), main(), run_queries(), save()

### Community 10 - "Late-delivery model (v1 logistic regression)"
Cohesion: 0.09
Nodes (30): DD-11: No recalibration or window tuning; use the model by rank, DD-12: Close the ML experiments; v1 and the simple forecasts are final, 2018 delivery promise shortened (75% of August orders under 20 days), Rio de Janeiro late-rate outlier (13.5% late, median 12 days), August 2018 delivery-promise policy shift, E1: single-feature skill, month by month, E2: persistence of route/category/seller lateness, E5: oracle true month late rate ceiling (+22 more)

### Community 11 - "test_feature_leakage.py"
Cohesion: 0.13
Nodes (19): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+11 more)

### Community 12 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 13 - "AUDIT.md"
Cohesion: 0.10
Nodes (23): Compute, Measured compute timings, Cost, If the project moved to the cloud, Total cloud cost $0, Seller concentration (top 10% of sellers = 67.5% of revenue), Insights correction: on-time orders produce ~70% of 1-2 star reviews, Current state (2026-10-13) (+15 more)

### Community 14 - "Architecture"
Cohesion: 0.18
Nodes (11): Architecture, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing, Related documents (+3 more)

### Community 15 - "weekly_series"
Cohesion: 0.16
Nodes (7): backtest(), linear_trend(), f(), score(), weekly_series(), beats_naive_share(), main()

### Community 16 - "DECISIONS.md"
Cohesion: 0.22
Nodes (12): D-001: Implementations use DuckDB, D-002: Local only, D-003: Idiomatic DuckDB SQL, D-004: No dbt, D-005: No Prometheus, Grafana or FastAPI, D-006: `.gitignore` coverage, D-007: ML target is late delivery, plus a weekly forecast, D-008: Untrack `data/` (+4 more)

### Community 17 - "SnowparkAccess"
Cohesion: 0.07
Nodes (16): Alternative not taken, Folders, How to run (untested, like the rest of the guide), sql/bigquery — the same layers in GoogleSQL, Tokens, Type mapping, _clean(), from_active_session() (+8 more)

### Community 18 - "fact_order_items"
Cohesion: 0.14
Nodes (9): dim_customer, dim_date, dim_geography, dim_product, dim_seller, fact_order_items, fact_orders, fact_payments (+1 more)

### Community 19 - "Model card"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

### Community 20 - "Recalibration and training window for the v1 late-delivery model"
Cohesion: 0.40
Nodes (5): Conclusions, Limits, R: recalibration on the latest resolved period, Recalibration and training window for the v1 late-delivery model, W: choosing the training window

### Community 21 - "test_reconciliation.py"
Cohesion: 0.05
Nodes (37): base_rows(), cmp_(), _fake_run(), frame(), mismatches(), _populate(), real_fetch(), _real_warehouse() (+29 more)

### Community 23 - "Orders delivered late % (metric)"
Cohesion: 0.27
Nodes (8): Promise and Lateness Chart (late-delivery rate and under-20-day promises by month), Olist delivered orders by purchase month (months with at least 500 orders, 2017-01 to 2018-08), Orders Promised in Under 20 Days (%) metric, Delivery performance by customer state (chart), Median days to deliver (metric), Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time, Olist Brazilian e-commerce orders data (source), Orders delivered late % (metric)

### Community 24 - "Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)"
Cohesion: 0.25
Nodes (8): 1. Get the data, 2. Set up and build the warehouse, 3. Run the baselines and tests, 4. Explore, Attribution, Repository map, Results at a glance, Retail Analytics, Forecasting & Customer Intelligence (local DuckDB build)

### Community 26 - "Final audit (Phase 10)"
Cohesion: 0.17
Nodes (12): 1. Correctness, 2. Reproducibility, 3. Security, 4. Cost, 5. Architecture, 6. Testing, 7. Documentation, 8. Evidence (+4 more)

### Community 27 - "powerbi/README.md"
Cohesion: 0.14
Nodes (18): Power BI generators and project (src/powerbi, powerbi/), DD-06: Convert geolocation CSV to Parquet in the build, Out-of-time late-delivery scores export (export_scores.py), DASHBOARD_MOCKUP.html, DataFolder parameter, export_data.py (Power BI data export), First-open checklist, If the first refresh fails (+10 more)

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
Cohesion: 0.50
Nodes (4): Agentic Loop (PLAN to DECIDE), Development Phases 0-10, Human Approval Gates, PROJECT_STATUS.md and Definition of Done

### Community 36 - "Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY)"
Cohesion: 0.50
Nodes (4): Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY), Evidence Requirement and Evidence Integrity, Failure Documentation, Security Principles (least privilege, no secrets in Git)

### Community 38 - "datasets.py"
Cohesion: 0.15
Nodes (10): is_data_access(), wrap_duckdb(), _conn(), _conform_column(), conform_frame(), _non_null(), normalise_frame(), _normalise_object_column() (+2 more)

### Community 39 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): graphify, graphify knowledge graph (graphify-out/), graphify

### Community 40 - "test_register_model.py"
Cohesion: 0.07
Nodes (7): env(), FakeDB, FakeModelRef, FakeRegistry, FakeVersion, feature_frame(), test_failed_scoring_is_recorded_and_returns_nonzero()

### Community 41 - "stage_wrapper"
Cohesion: 0.14
Nodes (17): backtest_frame(), scores_frame(), stage_wrapper(), test_create_table_sql_is_idempotent_ddl(), test_each_write_uses_a_fresh_stage_folder(), test_failed_copy_rolls_back_and_cleans_up(), test_failed_parquet_write_leaves_no_temp_files_and_no_staging(), test_local_temporary_file_is_deleted() (+9 more)

### Community 42 - "el"
Cohesion: 0.06
Nodes (98): barChart(), draw(), barPath(), heatmap(), draw(), luminance(), STEPS, legend() (+90 more)

### Community 43 - "datasets"
Cohesion: 0.05
Nodes (41): bytes, file, rows, source, title, backend, datasets, analytics (+33 more)

### Community 45 - "story.mjs"
Cohesion: 0.05
Nodes (26): args, chrome, positionals, args, chrome, file, frame, frames (+18 more)

### Community 46 - "Retail Analytics, Forecasting & Customer Intelligence Platform"
Cohesion: 0.05
Nodes (36): Access control, Batch inference, Customer, Data processing choice, dbt, Delivery, Dialect migration, Forecasting (+28 more)

### Community 84 - "pandas"
Cohesion: 0.07
Nodes (20): 4. Python integration, main(), permutation_drop(), build(), build_from(), score_test_months(), add_smoothed_rates(), calibration_table() (+12 more)

### Community 85 - "duckdb"
Cohesion: 0.13
Nodes (6): pytest_collection_modifyitems(), manifest(), test_manifest_row_counts_equal_the_files(), test_no_fact_key_is_missing_from_its_dimension(), test_review_comment_text_is_not_exported(), test_sql_auc_equals_sklearn_with_ties()

### Community 86 - "Section 3: Tier 1 DAX Optimization Patterns"
Cohesion: 0.05
Nodes (42): DAX001: Use Simple Column Filter Predicates as CALCULATE Arguments, DAX002: Use SUMMARIZECOLUMNS for Grouped Calculations, DAX003: Cache Repeated Expressions in Variables, DAX004: Remove Redundant Filters, DAX005: Move Complex SUMMARIZE Inputs to CALCULATETABLE, DAX006: Precompute Iterator Inputs with SUMMARIZECOLUMNS, DAX007: Convert Boolean Tests Without IF, DAX008: Context Transition in Iterator (+34 more)

### Community 87 - "Check details"
Cohesion: 0.07
Nodes (29): arg_max / max_by tie-breaks, Check details, dim_customer (dimension): PASS, dim_date (dimension): PASS, dim_geography (dimension): PASS, dim_product (dimension): PASS, dim_seller (dimension): PASS, Documented constants (three-way) (+21 more)

### Community 88 - "drift_analysis.py"
Cohesion: 0.30
Nodes (8): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts()

### Community 89 - "pathlib"
Cohesion: 0.11
Nodes (10): main(), main(), read_monitor(), main(), main(), compute(), main(), written_rows() (+2 more)

### Community 90 - "Data dictionary: Snowflake + dbt implementation"
Cohesion: 0.15
Nodes (13): Data dictionary: Snowflake + dbt implementation, Documentation coverage, `int_late_delivery_history`, `int_late_delivery_item_agg`, `int_late_delivery_population`, `int_late_delivery_seller_history`, Intermediate, late-delivery features (INTERMEDIATE, views), `mart_late_delivery_features` (+5 more)

### Community 91 - "load_raw.py"
Cohesion: 0.11
Nodes (21): build_parser(), check_files_exist(), _check_put_result(), count_records(), default_connect(), describe_files(), ident(), IngestError (+13 more)

### Community 92 - "compare.py"
Cohesion: 0.12
Nodes (18): _as_decimal(), _candidates(), _coerce(), _compare_expected(), ok(), compare_frames(), compare_values(), ExpectedResult (+10 more)

### Community 93 - "test_powerbi_snowflake.py"
Cohesion: 0.09
Nodes (17): patched(), patched_ml_files(), _project_files(), _scan(), _split_outside_block(), test_expressions_define_the_two_snowflake_parameters(), test_ml_on_files_keeps_datafolder_beside_the_snowflake_parameters(), test_ml_on_files_patches_only_the_nine_pbi_tables() (+9 more)

### Community 94 - "fetch.py"
Cohesion: 0.09
Nodes (10): assert_read_only(), canon_value(), DuckDBFetcher, frame_from_dataframe(), frame_from_rows(), ReadOnlyViolation, redact_account(), SnowflakeFetcher (+2 more)

### Community 95 - "test_snowflake_ingestion.py"
Cohesion: 0.13
Nodes (23): _ddl_tables(), expected_rows_for(), FakeConnection, run_main(), test_changed_file_into_nonempty_table_is_refused_not_appended(), test_copy_exception_is_logged_failed_and_stops(), test_ddl_matches_loader_spec_and_contract(), test_dry_run_emits_sql_and_never_connects_or_needs_credentials() (+15 more)

### Community 96 - "report.py"
Cohesion: 0.18
Nodes (14): ColumnResult, display_value(), _cell(), _col_rows(), collect_run_metadata(), _comparison_block(), _git(), _key_text() (+6 more)

### Community 97 - "numpy"
Cohesion: 0.21
Nodes (9): ar1_with_trend(), series(), test_ar1_trend_extends_an_exact_linear_series(), test_combination_is_the_mean_of_its_parts(), test_constant_series_is_forecast_as_constant_by_every_model(), test_damped_trend_continues_a_rising_series_but_less_than_a_straight_line(), test_exponential_smoothing_follows_the_latest_level_after_a_step(), test_forecasts_are_never_negative() (+1 more)

### Community 98 - "cli.py"
Cohesion: 0.12
Nodes (15): build_parser(), main(), _print_progress(), _resolve_duckdb(), _split(), CheckResult, duckdb_side(), run_checks() (+7 more)

### Community 99 - "checks.py"
Cohesion: 0.16
Nodes (19): absolute(), all_checks(), _analytics_checks(), Check, ColumnRule, _dimension_checks(), Expected, _fact_checks() (+11 more)

### Community 100 - "pytest"
Cohesion: 0.28
Nodes (11): net(), table(), test_category_revenue_matches_and_shares_are_consistent(), test_delay_buckets_cover_every_reviewed_delivered_order(), test_delivery_trend_covers_the_same_population_as_the_ml_features(), test_monthly_growth_is_blank_next_to_thin_months(), test_monthly_kpis_add_up_to_net_revenue(), test_payment_shares_add_up_and_total_matches_the_fact() (+3 more)

### Community 101 - "backend.py"
Cohesion: 0.14
Nodes (12): _confirmed(), connect(), _connect_snowflake(), InvalidBackendError, _load_private_key_der(), _load_snowflake_connector(), MissingConfigError, resolve_backend() (+4 more)

### Community 102 - "render_data_dictionary.py"
Cohesion: 0.15
Nodes (13): collect(), describe_test(), first_comment(), layer_of(), load_manifest(), main(), md_cell(), mermaid_id() (+5 more)

### Community 103 - "test_data_access.py"
Cohesion: 0.07
Nodes (12): check_wrapped_equals_raw(), sf_wrapper(), test_conform_integral_floats_to_ints_and_numbers_to_float(), test_duckdb_sql_text_matches_the_ml_modules(), test_normalise_dtypes(), test_real_warehouse_wrapped_equals_raw_and_validates(), test_snowflake_execute_and_close(), test_snowflake_late_features_match_duckdb_after_load() (+4 more)

### Community 104 - "load_table"
Cohesion: 0.18
Nodes (13): Executor, FileInfo, load_table(), _log_best_effort(), print_dry_run(), sql_copy(), sql_count(), sql_log_insert() (+5 more)

### Community 105 - "apply_snowflake_source.py"
Cohesion: 0.20
Nodes (9): apply(), _is_inside(), main(), patch_table(), PatchError, _read(), split_partition(), typed_step_arguments() (+1 more)

### Community 106 - "test_publish_ml.py"
Cohesion: 0.13
Nodes (5): FakeDB, frames(), patched(), test_compute_rejects_a_frame_with_a_missing_column(), test_hand_picked_run_ids_are_refused_before_connecting()

### Community 107 - "writeback.py"
Cohesion: 0.10
Nodes (15): DataAccess, DataAccessError, copy_sql(), create_table_sql(), delete_sql(), _load(), new_run_id(), _prepare() (+7 more)

### Community 108 - "Semantic model (12 tables, 13 relationships, 38 measures)"
Cohesion: 0.15
Nodes (17): August 2018 delivery promise change (concept drift), Use the model by rank, not probability, flag_share helper table, forecast_backtest table, late_delivery_scores table, DAX measure group: Delivery, DAX measure group: Forecast, DAX measure group: Reviews (+9 more)

### Community 109 - "validate_frame"
Cohesion: 0.11
Nodes (17): 3. Summary counts, 6. Inventory C: SQL embedded in Python and notebooks, _kind_ok(), late_delivery_features(), order_category(), _schema_ident(), SchemaError, unlabelled_share() (+9 more)

### Community 110 - "json"
Cohesion: 0.15
Nodes (15): analytics_tables(), clean(), commit(), discard(), forecast_metrics(), forecasts(), headline_kpis(), lineage() (+7 more)

### Community 111 - "Snowflake + dbt implementation: setup and runbook"
Cohesion: 0.11
Nodes (18): 10. Step 6: the HTML dashboard - RUN 2026-11-12, 11. Step 7: Power BI patched copy - NOT RUN, 12. Cost, 13. Where things stand, 1. Prerequisites, 2. Credentials and environment variables, 3. Offline checks (no Snowflake connection), 4. Step 1: preflight and setup - RUN 2026-11-12 (+10 more)

### Community 112 - "build_pbip.py"
Cohesion: 0.23
Nodes (10): dump(), field_json(), files(), lit(), main(), projection(), q(), relationships_tmdl() (+2 more)

### Community 113 - "4. Procedure"
Cohesion: 0.17
Nodes (12): 1. What each piece does, and what it never does, 2. Approval gate: what the account owner must approve, 3. Prerequisites, 4.0 Dry run (always do this first), 4.1 First load, 4.2 Re-run (no-op), 4.3 Reload, 4.4 Failure and recovery (+4 more)

### Community 114 - "Power BI Semantic Model Authoring — CLI Skill"
Cohesion: 0.06
Nodes (31): AVOID, Connecting to a Semantic Model, Connection Binding, Data Sources & Parameters, DENY, Example 1: Modify an Existing Semantic Model, Example 2: Create a New Semantic Model from a Fabric Lakehouse, Example 3: Bind a Semantic Model to a Fabric Connection (+23 more)

### Community 115 - "model_spec.py"
Cohesion: 0.18
Nodes (9): Operational Metadata (Owner, Storage Mode, Scale-Out), Check, col(), guid(), mea(), Measure, Page, Relationship (+1 more)

### Community 116 - "format.js"
Cohesion: 0.25
Nodes (16): brl(), cache, compact(), DASH, day(), int(), isNum(), MONTHS (+8 more)

### Community 117 - "ddl_raw.sql"
Cohesion: 0.18
Nodes (10): RAW.CUSTOMERS, RAW.GEOLOCATION, RAW.INGESTION_LOG, RAW.ORDER_ITEMS, RAW.ORDER_PAYMENTS, RAW.ORDER_REVIEWS, RAW.ORDERS, RAW.PRODUCT_CATEGORY_TRANSLATION (+2 more)

### Community 118 - "Unslop"
Cohesion: 0.12
Nodes (16): 1. Spacing, 2. Color, 3. Icons, 4. Copy, 5. Type, 6. Layout, 7. Details, 8. Visuals (+8 more)

### Community 119 - "Tokens"
Cohesion: 0.14
Nodes (14): Accent, App layout, Buttons, Dark, Depth, Icons, Light, Motion (+6 more)

### Community 120 - "Snowflake Retail Project: Local vs. Cloud Architecture"
Cohesion: 0.17
Nodes (12): 1. Cloud vs. Local Architecture Mapping, 2. End-to-End Pipeline Workflow, 3. Where the ML runs today, 4. Key Snowflake Technologies and Portability, Analytics engine: DuckDB vs Snowflake, Cost control, dbt instead of Dataflow, Local pipeline (reference) (+4 more)

### Community 121 - "table_tmdl"
Cohesion: 0.27
Nodes (6): m_load(), prop(), table_tmdl(), column_hidden(), m_type(), Table

### Community 122 - "Snowflake + dbt architecture"
Cohesion: 0.25
Nodes (8): 1. End-to-end flow: DuckDB path and Snowflake path, 2. Snowflake objects and roles, 3.1 Layer overview, 3.2 Model-level lineage (generated from the dbt manifest), 3. dbt layers and lineage, 5. Power BI integration, 6. Design decisions that shape the architecture, Snowflake + dbt architecture

### Community 123 - "FakeCursor"
Cohesion: 0.18
Nodes (4): 9. UNVERIFIED until a live Snowflake run, FakeCursor, FakeCursorPandas, StageCursor

### Community 124 - "test_dashboard.py"
Cohesion: 0.10
Nodes (6): _FakeSnowflake, test_every_js_file_parses(), test_failed_build_leaves_the_previous_build_intact(), test_no_innerhtml_in_dashboard_code(), test_order_category_reads_the_snowflake_intermediate_model(), test_snowflake_analytics_marts_are_put_in_the_reference_order()

### Community 125 - "Signs of slop"
Cohesion: 0.18
Nodes (11): Components, Copy, Icons, Landing pages and heroes, Motion, Signs of slop, Spacing, Surfaces and color (+3 more)

### Community 126 - "test_feature_determinism.py"
Cohesion: 0.40
Nodes (7): _add_categories(), day(), _single_item_order(), test_payment_value_tie_resolves_to_the_alphabetically_first_type(), test_price_tie_resolves_to_the_alphabetically_first_category(), test_repeated_multithreaded_runs_are_identical(), _tied_order()

### Community 127 - "data_dir"
Cohesion: 0.32
Nodes (5): data_dir(), env(), key_file(), test_header_mismatch_and_short_record_are_rejected(), _write_csv()

### Community 128 - "_statements"
Cohesion: 0.25
Nodes (6): _statements(), test_grants_include_future_grants_and_are_additive(), test_objects_sql_matches_the_contract(), test_preflight_is_read_only(), test_private_key_and_env_files_are_git_ignored(), test_setup_files_have_no_replace_or_drop_even_in_comments()

### Community 130 - "Staging (STAGING, views)"
Cohesion: 0.20
Nodes (10): Staging (STAGING, views), `stg_olist__category_translation`, `stg_olist__customers`, `stg_olist__geolocation`, `stg_olist__order_items`, `stg_olist__order_payments`, `stg_olist__order_reviews`, `stg_olist__orders` (+2 more)

### Community 131 - "Marts, core star schema (MARTS, tables)"
Cohesion: 0.22
Nodes (9): `dim_customer`, `dim_geography`, `dim_product`, `dim_seller`, `fact_order_items`, `fact_orders`, `fact_payments`, `fact_reviews` (+1 more)

### Community 132 - "Power BI views (PBI, views)"
Cohesion: 0.22
Nodes (9): `pbi_dim_customer`, `pbi_dim_geography`, `pbi_dim_product`, `pbi_dim_seller`, `pbi_fact_order_items`, `pbi_fact_orders`, `pbi_fact_payments`, `pbi_fact_reviews` (+1 more)

### Community 133 - "dbt project: Olist on Snowflake"
Cohesion: 0.33
Nodes (6): Commands, dbt project: Olist on Snowflake, Environment (isolated from the repo root), Layout and conventions, Translation notes (DuckDB -> Snowflake), Verification summary (offline)

### Community 134 - "orders"
Cohesion: 0.12
Nodes (19): `mart_category_performance`, `mart_delivery_trend`, `mart_delivery_vs_reviews`, `mart_monthly_kpis`, `mart_payments`, `mart_repeat_customers`, `mart_seller_concentration`, `mart_state_performance` (+11 more)

### Community 136 - "README.md"
Cohesion: 0.16
Nodes (6): Late delivery vs review score association (4.29 on time, 2.57 late), Planted-leak checks, Purchase-time (point-in-time) feature rule, Phase 0 cloud architecture proposal (GCS, BigQuery, Dataflow, Vertex AI), Olist Brazilian E-Commerce dataset (Kaggle, CC BY-NC-SA 4.0), Unverified BigQuery, Dataflow and Vertex AI pricing

### Community 139 - "Effects"
Cohesion: 0.29
Nodes (7): Dithering, Duotone, Effects, Glyphs, Halftone dots, Implementation, Performance

### Community 140 - "Visuals"
Cohesion: 0.29
Nodes (7): Decide what the visual is, Generate it, Objects for moments, Prompt recipe, Put it on the page, Styles that work, Visuals

### Community 141 - "FakeConn"
Cohesion: 0.13
Nodes (8): clean_env(), fake_connector(), connect(), FakeConn, _populate(), populated(), sf_env(), StageConn

### Community 235 - "Intermediate (INTERMEDIATE, views)"
Cohesion: 0.33
Nodes (6): `int_customers_latest`, `int_geography_points`, `int_geography_rollup`, `int_order_items_agg`, `int_order_payments_agg`, Intermediate (INTERMEDIATE, views)

### Community 236 - "MLOps Lifecycle"
Cohesion: 0.50
Nodes (3): ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability

### Community 237 - "Security"
Cohesion: 0.33
Nodes (6): Data and privacy, Licence, Not applicable by design, Practices to keep, Security, What was checked (2026-10-13)

### Community 238 - "register_model.py"
Cohesion: 0.14
Nodes (15): backtest_metrics(), check_in_warehouse(), fit(), git_sha(), log_kwargs(), main(), parity_sample(), predict_proba_sql() (+7 more)

### Community 239 - "DAX Query Syntax Rules"
Cohesion: 0.08
Nodes (25): Best Practices, CALCULATE and CALCULATETABLE Filter Rules, DAX Coding Best Practices, DAX Language Guidelines, DAX Query Examples, DAX Query Syntax Rules, DAX User-Defined Functions (UDFs), DEFINE Block (+17 more)

### Community 240 - "ConfirmationRequired"
Cohesion: 0.47
Nodes (5): ConfirmationRequired, test_refuses_without_confirmation(), connect(), test_refuses_without_confirmation(), connect()

### Community 245 - "needs_real_data"
Cohesion: 0.50
Nodes (3): test_loader_column_specs_match_real_csv_headers(), test_real_files_record_counts_and_headers(), test_real_reviews_has_99224_records_not_line_count()

### Community 246 - "DAX Performance Decision Guide"
Cohesion: 0.08
Nodes (25): Analyzing Trace Events, Compression, Segments, and Parallelism, Consult When Needed, DAX Performance Decision Guide, DAX vs. Data Layout: Reading the Signal, Decision Guide, Error Handling, Further Reading (+17 more)

### Community 248 - "make_snowflake_notebooks.py"
Cohesion: 0.27
Nodes (10): code(), main(), md(), must_replace(), nb02(), nb03(), nb04(), port() (+2 more)

### Community 249 - "Semantic Model Connection Binding Reference"
Cohesion: 0.09
Nodes (21): AVOID, Bind to a gateway or cloud connection, Bind using default / automatic settings (SSO), Common scenarios, `connectivityType` values, End-to-end Workflow, Endpoint, Limitations (+13 more)

### Community 250 - "TMDL Guidelines"
Cohesion: 0.11
Nodes (19): Calculation Groups, DAX User-Defined Functions (UDFs), Field parameter calculated tables, File: `cultures/fr-FR.tmdl`, File: `perspectives/Internet Sales.tmdl`, File: `roles/RegionalManager.tmdl`, Hierarchies, Key Rules (+11 more)

### Community 251 - "DuckDB to Snowflake + dbt: SQL migration inventory"
Cohesion: 0.18
Nodes (11): 10. Inventory D: SQL added for Snowflake (93 files), 1. Classification, 2. Reconciling `git ls-files "*.sql"`, 4.1 Staging (9 files, class 3), 4.2 Dimensions (5 files), 4.3 Facts (4 files, class 2), 4.4 Analytics (8 files, class 2), 4. Inventory A: the 28 DuckDB SQL files (+3 more)

### Community 252 - "Semantic Model Modeling Guidelines"
Cohesion: 0.11
Nodes (18): Calculated Columns, Calculation Groups, Core Principles, Date/Calendar Table, Descriptions & Documentation, Format String Reference, Hierarchies, Maintenance (+10 more)

### Community 253 - "test_warehouse.py"
Cohesion: 0.22
Nodes (3): features(), test_seller_history_matches_a_direct_recount_on_real_data(), test_weekly_series_covers_the_documented_window()

### Community 254 - "Field Parameters Reference"
Cohesion: 0.12
Nodes (16): AVOID, Common scenarios, Contents, Create a field parameter (Tier 1, MCP), Examples, Field Parameters Reference, MUST, Must / Prefer / Avoid (+8 more)

### Community 255 - "ARCHITECTURE.md"
Cohesion: 0.22
Nodes (10): ML layer (src/ml, sql/ml), Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions), Raw data (data/), Staging SQL (sql/staging), Test suite (96 pytest tests), Validation checks (sql/validation/checks.sql, 22 checks), warehouse.duckdb, Clean-clone reproduction (+2 more)

### Community 256 - "test_drift_helpers.py"
Cohesion: 0.57
Nodes (5): frame(), test_relative_rates_are_positive_for_a_late_route(), test_relative_rates_are_zero_when_route_matches_the_system(), test_system_counts_do_not_depend_on_row_order(), test_system_counts_use_only_orders_delivered_strictly_before_purchase()

### Community 257 - "Column audit for target A"
Cohesion: 0.13
Nodes (16): Checklist from the brief, Column audit for target A, Customer history, `fact_order_items` (aggregate to order grain first, per DD-01), `fact_orders`, `fact_payments`, `fact_reviews`, Forecast leakage (target B) (+8 more)

### Community 258 - "Retail analytics dashboard (HTML)"
Cohesion: 0.40
Nodes (5): Extending it, How it is organised, Refresh the data, Retail analytics dashboard (HTML), Run it

### Community 259 - "Semantic Model Metadata Discovery — DAX INFO Functions"
Cohesion: 0.14
Nodes (13): Complete INFO Function Catalog, Dependency Discovery, Dependency rowset for a DAX query, Dependency rowset scoped to a measure, Metadata Object → INFO Function Map, Narrowing Results (Projection + Filtering), Ordering Results, Recommended Discovery Order (+5 more)

### Community 262 - "build_mockup_html.py"
Cohesion: 0.24
Nodes (4): main(), render(), build(), test_mockup_cubes_add_up_to_the_specification_checks()

### Community 263 - "test_scoring_task_sql.py"
Cohesion: 0.31
Nodes (5): strip_comments(), test_predict_proba_arguments_match_the_shared_helper(), test_setup_files_are_additive_and_keep_placeholders(), test_task_is_idempotent_and_non_destructive(), test_task_never_writes_the_backtest_scores_table()

### Community 264 - "MiniWarehouse"
Cohesion: 0.14
Nodes (8): Known non-live caveats, Late-delivery feature models (A3c): `int_late_delivery_*`, `mart_late_delivery_features`, Live verification checklist (dbt base: staging, intermediate, core marts), Needs live verification, Rounding boundary checks (analytics marts), What was verified offline (2026-11-06), mini(), MiniWarehouse

### Community 266 - "Lessons learned"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 267 - "forecast_baseline.py"
Cohesion: 0.24
Nodes (8): moving_average(), naive(), combination(), series(), test_changing_future_weeks_does_not_change_earlier_forecasts(), test_horizon_shifts_the_target(), test_naive_and_moving_average_values(), test_score_is_below_one_for_a_better_model_than_naive()

### Community 268 - "0. Gathering Business Context"
Cohesion: 0.15
Nodes (13): 0. Gathering Business Context, 1. Model Architecture (Foundation), 2. Model Naming, 3. Descriptions, 4. AI Instructions, 5. AI Data Schema, 6. Verified Answers, Consumption Mode Decides the Investment (+5 more)

### Community 270 - "Semantic Model REST API Reference"
Cohesion: 0.15
Nodes (13): API Rules, Authentication & API Audiences, Create Semantic Model, Data Sources & Parameters (Power BI Datasets API), Execute DAX Queries (Power BI Datasets API), Get/Download Definition, Minimal TMDL Content, Permissions (Power BI Datasets API) (+5 more)

### Community 278 - "Naming Conventions for Power BI Semantic Models"
Cohesion: 0.17
Nodes (12): Anti-Patterns to Avoid, Column Names, Core Principle, Descriptions, Display Folder Organization, General Rules, Measure Names, Measure Variations (+4 more)

### Community 279 - "test_notebooks_snowflake.py"
Cohesion: 0.24
Nodes (7): git_sha(), code_cells(), test_cells_parse_and_use_the_notebook_session(), test_notebooks_store_no_outputs(), test_ported_notebooks_keep_every_original_analysis_cell(), test_the_three_notebooks_exist_and_are_up_to_date(), test_train_register_notebook_never_sets_the_default_version()

### Community 281 - "visualize_schema.py"
Cohesion: 0.38
Nodes (4): draw(), load_graph(), main(), node_label()

### Community 282 - "parametrize"
Cohesion: 0.25
Nodes (5): test_model_files_are_byte_identical(), test_table_file_is_unchanged_outside_the_partition_source(), test_template_column_types_equal_the_originals(), test_template_navigates_the_right_snowflake_object(), test_typed_columns_match_the_model_source_columns()

### Community 283 - "Properties Retrieval"
Cohesion: 0.29
Nodes (7): Data Source Response Properties, DirectQuery / LiveConnection Refresh Schedule Properties, Per-Table Storage Mode, Properties Retrieval, Refresh History Response Properties, Schema Properties (Tables, Columns, Measures, Relationships, Expressions), Upstream Dataflow Links

### Community 284 - "parametrize"
Cohesion: 0.29
Nodes (5): test_entry_points_reject_unknown_backend_from_env(), test_entry_points_snowflake_backend_needs_config_and_confirmation(), test_only_confirm_one_counts(), test_writeback_rejects_unsafe_run_ids_before_touching_snowflake(), test_writeback_statement_sequence_is_atomic_and_never_destructive()

### Community 285 - "Power BI Project file (PBIP)"
Cohesion: 0.33
Nodes (5): definition.pbir, definition.pbism file, .pbip file, Power BI Project file (PBIP), References

### Community 286 - "Phase 1: Establish Baseline"
Cohesion: 0.40
Nodes (5): Phase 1: Establish Baseline, Step 1: Resolve All Measure and Function Definitions, Step 2: Gather Model Context, Step 3: Execute Baseline (1 warm-up + 2+ measured runs), Step 4: Analyze Baseline

### Community 287 - "Direct Lake Modeling Guidelines"
Cohesion: 0.40
Nodes (5): Direct Lake Modeling Guidelines, Important, Partition Configuration, Process to create a direct lake model, TMDL example of a Direct Lake table configuration

### Community 288 - "EDA findings: Olist dataset discovery"
Cohesion: 0.40
Nodes (5): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data

### Community 289 - "Phase 2: Optimization Iterations"
Cohesion: 0.50
Nodes (4): Phase 2: Optimization Iterations, Step 1: Select and Apply Optimizations, Step 2: Execute and Compare, Step 3: Iterate and Escalate

### Community 290 - "month"
Cohesion: 0.50
Nodes (4): month(), `dim_date`, `pbi_dim_date`, 7. Construct-by-construct translation

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **37 isolated node(s):** `semantic-model-authoring`, `gcp`, `retail-olist-dbt`, `retail-olist-ml-registry`, `Always-predict-training-late-rate baseline` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1314 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **157 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `7. Construct-by-construct translation` connect `month` to `DuckDB to Snowflake + dbt: SQL migration inventory`, `pytest`, `validate_frame`?**
  _High betweenness centrality (0.114) - this node is a cross-community bridge._
- **What connects `semantic-model-authoring`, `gcp`, `retail-olist-dbt` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Design decisions` be split into smaller, more focused modules?**
  _Cohesion score 0.125 - nodes in this community are weakly interconnected._
- **Why does `table()` connect `pytest` to `month`, `Field Parameters Reference`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Should `Architecture Philosophy (Shared Across Cloud Projects)` be split into smaller, more focused modules?**
  _Cohesion score 0.13725490196078433 - nodes in this community are weakly interconnected._
- **Why does `month()` connect `month` to `format.js`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._