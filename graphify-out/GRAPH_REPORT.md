# Graph Report - Retail-Analytics-Forecasting-Customer-Intelligence  (2026-11-20)

## Corpus Check
- 415 files · ~444,948 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 57 file(s) not represented in the graph (top: .tmdl 17, (none) 11, .css 9)

## Summary
- 3512 nodes · 5780 edges · 356 communities (202 shown, 154 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 372 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `0d176ed3`
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
- experiment_recalibration
- run_analytics.py
- DECISIONS.md
- test_feature_leakage.py
- Phase 0 — Discovery Report
- README.md
- Architecture
- numpy
- build_warehouse.py
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
- base.json
- DRIFT_ANALYSIS.md
- fact_order_items (PK: order_id, order_item_id; 112,650 rows)
- 5. Step by step
- Net revenue by product category (R$ millions, share of total)
- Net revenue per month (R$ millions)
- Chart: Average review score by how late the order arrived
- Agentic Loop (PLAN to DECIDE)
- Documentation Standard (README, ARCHITECTURE, DECISIONS, COST, SECURITY)
- `${PROJECT}.staging.stg_order_items`
- models.js
- AGENTS.md
- test_register_model.py
- stage_wrapper
- risk.js
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
- late_delivery_baseline.py
- pathlib
- validate_frame
- Check details
- drift_analysis.py
- export_scores.py
- orders
- load_raw.py
- compare.py
- test_powerbi_snowflake.py
- cli.py
- test_snowflake_ingestion.py
- report.py
- recalibration.py
- render_snowflake
- checks.py
- pytest
- pandas
- render_data_dictionary.py
- test_data_access.py
- load_table
- apply_snowflake_source.py
- test_publish_ml.py
- writeback.py
- Semantic model (12 tables, 13 relationships, 38 measures)
- weekly_series
- json
- Snowflake + dbt implementation: setup and runbook
- build_pbip.py
- 4. Procedure
- Power BI switch guide: from the local files to Snowflake
- .name
- format.js
- ddl_raw.sql
- Unslop
- Tokens
- Snowflake Retail Project: Local vs. Cloud Architecture
- model_spec.py
- Snowflake + dbt architecture
- DuckDB to Snowflake + dbt: SQL migration inventory
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
- barChart
- FakeCursor
- EDA findings: Olist dataset discovery
- argparse
- SKILL.md
- Effects
- Visuals
- fake_connector
- retail-olist-dbt
- Intermediate (INTERMEDIATE, views)
- MLOps Lifecycle
- AUDIT.md
- register_model.py
- powerbi-report-cli/SKILL.md
- Narrative / Data Story
- show
- needs_real_data
- Accessibility for Data Visualization
- test_yes_flag_is_passed_to_connect_as_confirmation
- make_snowflake_notebooks.py
- Operational Monitor Dashboard
- Measure
- Executive Summary Dashboard
- Color Strategy
- test_warehouse.py
- main.js
- Expression Tree Templates
- test_drift_helpers.py
- Version Control for PBIR Editing
- Retail analytics dashboard (HTML)
- Layout Composition
- retail-olist-ml-registry
- Table & Matrix Visual Authoring Guide
- test_scoring_task_sql.py
- Tone Catalog
- powerbi-report-cli planning mode -- Power BI Report Planning
- Lessons learned
- el
- Card Visual Authoring Guide - Part 3
- scoring_task.sql
- Cartesian Visuals (Bar, Column, Line, Scatter)
- Conditional Formatting Patterns - Part 7
- Theme Authoring — theme.json Reference
- Comparative Benchmark - Part 2
- Workflow
- Examples: CRUD Operations
- Contents
- Anti-Patterns — The Dashboard Slop Catalog
- Comparative / Benchmark Dashboard
- Page layout contract
- parametrize
- Authoring Workflows & Examples
- Button Sizing & Placement (Required)
- Card Sizing (Required)
- Formatting Patterns
- Layers
- Slicer Authoring Guide - Part 2
- Signatures
- Typography for Data
- Power BI Reports - CLI Skill
- labels.js
- Custom Visuals (AppSource, Organizational, Private `.pbiviz`)
- Add a Filter
- Analytical Canvas
- Chart Selection Decision Framework
- Interactivity & Storytelling
- text
- powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP) - Part 3
- Re-theming Workflow
- Theme Authoring — theme.json Reference - Part 2
- Contents
- powerbi-report-cli planning mode -- Power BI Report Planning - Part 2
- Image Visual Authoring Guide
- Dark Mode Authoring Checklist
- Button Visual Authoring Guide - Part 3
- Cartesian Visuals (Bar, Column, Line, Scatter) - Part 3
- powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP) - Part 2
- Shape Visual
- powerbi-report-cli management mode -- Power BI Report Items in Fabric
- test_notebooks_snowflake.py
- authoring.md
- Selectors (Targeting Specific Data)
- `definition.pbir` — Report → Semantic Model Binding
- Pre-Flight Checklist
- snapshot.mjs
- Color Strategy & Patterns
- Conditional Formatting Patterns - Part 3
- Formatting Patterns - Part 2
- `powerbi-report-author` CLI Reference
- Report Preview
- Report Preview - Part 2
- Checklist
- Recommended Defaults
- Agentic Workflow
- Contents
- Conditional Formatting Patterns - Part 6
- Power BI Desktop Preview Routing
- Brownfield Redesign — Entry Workflow
- Design Brief Contract
- Phase 2: baseline results
- FakeConn
- parametrize
- Filter Pane & Filter Card Formatting
- Textbox Visual Authoring Guide
- Archetype Composition & Variant Rotation
- Must/Prefer/Avoid
- Card Visual Authoring Guide
- Contents
- Field-Value Result Contracts and Support Guardrails
- Formatting & Theming Overview
- 6. Visual Styles (`visualStyles`)
- PBI Formatting Reference
- Chromatic signatures
- Typographic signatures
- Color & Typography
- Layout Variants
- Bookmark state
- warn
- powerbi-report-cli

## God Nodes (most connected - your core abstractions)
1. `el()` - 41 edges
2. `Retail Analytics, Forecasting & Customer Intelligence Platform` - 35 edges
3. `barChart()` - 34 edges
4. `lineChart()` - 29 edges
5. `DataAccess` - 26 edges
6. `Late-delivery model (v1 logistic regression)` - 25 edges
7. `Check details` - 23 edges
8. `card()` - 22 edges
9. `Measure` - 21 edges
10. `run_main()` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Anti-Patterns` --references--> `show()`  [INFERRED]
  .claude/skills/powerbi-report-cli/references/authoring/button-part-03.md → dashboard/js/boot-check.js
- `Dual-Entry Pattern` --references--> `show()`  [INFERRED]
  .claude/skills/powerbi-report-cli/references/authoring/formatting.md → dashboard/js/boot-check.js
- `layout — Gap & Series Order` --references--> `barChart()`  [INFERRED]
  .claude/skills/powerbi-report-cli/references/authoring/cartesian-part-02.md → dashboard/js/charts/bar-chart.js
- `totals — Stacked Charts` --references--> `barChart()`  [INFERRED]
  .claude/skills/powerbi-report-cli/references/authoring/cartesian-part-02.md → dashboard/js/charts/bar-chart.js
- `3D column (`barChart`)` --references--> `barChart()`  [INFERRED]
  .claude/skills/powerbi-report-cli/references/authoring/map.md → dashboard/js/charts/bar-chart.js

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

## Communities (356 total, 154 thin omitted)

### Community 0 - "build_spec_html.py"
Cohesion: 0.15
Nodes (11): edge_point(), field_text(), main(), manifest(), model_svg(), render(), wireframe(), compute_checks() (+3 more)

### Community 1 - "test_notebooks.py"
Cohesion: 0.27
Nodes (5): code_cells(), notebook(), test_every_code_cell_was_executed_without_error(), test_notebook_code_parses_and_only_imports_modules_that_exist(), test_the_charts_are_stored_in_the_notebook()

### Community 2 - "Design decisions"
Cohesion: 0.17
Nodes (24): dim_customer, dim_date, dim_geography, dim_product, dim_seller, Dimension SQL (sql/dimensions), fact_order_items, fact_orders (+16 more)

### Community 3 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.14
Nodes (9): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail), Architecture Philosophy (Shared Across Cloud Projects), dbt as First-Class Component, Multi-Cloud View (three production targets of one philosophy) (+1 more)

### Community 4 - "fact_order_items (grain: order item, 112,650 rows)"
Cohesion: 0.06
Nodes (40): Net revenue R$ 13.49M over 98,199 orders, Data model: Olist star schema, Design rules, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows) (+32 more)

### Community 5 - "re"
Cohesion: 0.18
Nodes (14): local_columns(), read(), stems(), strip_comments(), test_each_raw_file_is_an_external_table_over_its_csv(), test_each_staging_file_is_a_view_over_its_raw_table_with_the_typed_casts(), test_every_local_column_reaches_the_view(), test_raw_columns_match_the_local_column_list_in_order_and_as_strings() (+6 more)

### Community 6 - "test_powerbi_project.py"
Cohesion: 0.12
Nodes (10): _columns(), _fetch(), generated(), _json_files(), registry(), _retrieve(), test_every_json_file_validates_against_its_published_schema(), test_every_visual_field_exists() (+2 more)

### Community 7 - "test_geolocation_staging.py"
Cohesion: 0.18
Nodes (7): Components, check_raw_files(), run_sql_file(), data_dir(), test_missing_raw_file_gives_a_clear_error(), test_no_parquet_is_read_or_written(), test_staging_keeps_leading_zeros_and_types()

### Community 8 - "experiment_recalibration"
Cohesion: 0.23
Nodes (11): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), make_calibrator() (+3 more)

### Community 9 - "run_analytics.py"
Cohesion: 0.20
Nodes (12): draw(), load_graph(), main(), node_label(), fig_categories(), fig_monthly(), fig_promise(), fig_reviews() (+4 more)

### Community 10 - "DECISIONS.md"
Cohesion: 0.16
Nodes (15): Notebooks (01 discovery, 02 late-delivery, 03 forecast, marimo versions), DD-07: Customer segmentation is optional, DD-11: No recalibration or window tuning; use the model by rank, DD-12: Close the ML experiments; v1 and the simple forecasts are final, Always-predict-training-late-rate baseline, Grouped permutation importance, Features v2: route and category late-rate history, Features v5: delivery-time slack (+7 more)

### Community 11 - "test_feature_leakage.py"
Cohesion: 0.22
Nodes (12): day(), test_an_order_never_sees_its_own_outcome(), test_delivery_time_history_sums_only_resolved_orders(), test_history_counts_orders_delivered_before_purchase_not_purchased_before(), test_label_is_passed_through_as_integer(), test_one_row_per_order_with_multiple_items_and_sellers(), test_outcome_is_not_visible_at_the_instant_of_delivery(), test_output_has_no_post_outcome_columns() (+4 more)

### Community 12 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 13 - "README.md"
Cohesion: 0.13
Nodes (12): ML layer (src/ml, sql/ml), Test suite (96 pytest tests), warehouse.duckdb, Planted-leak checks, Purchase-time (point-in-time) feature rule, Weekly order forecast, Forecast baselines: naive, moving averages, linear trend, Gradient boosting baseline (depth 4) (+4 more)

### Community 14 - "Architecture"
Cohesion: 0.18
Nodes (11): Architecture, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing, Related documents (+3 more)

### Community 15 - "numpy"
Cohesion: 0.07
Nodes (27): backtest(), linear_trend(), f(), main(), moving_average(), naive(), score(), weekly_series() (+19 more)

### Community 16 - "build_warehouse.py"
Cohesion: 0.10
Nodes (22): Raw data (data/), Staging SQL (sql/staging), Validation checks (sql/validation/checks.sql, 22 checks), Compute, Measured compute timings, Cost, If the project moved to the cloud, Total cloud cost $0 (+14 more)

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
Cohesion: 0.08
Nodes (23): 1. Growth: fast in 2017, flat in 2018, 2. What sells: broad, and not concentrated in a few categories, 3. Geography: one region carries the marketplace, and the north-east pays for distance, 4. Seller base: a long tail with a strong head, 5. Delivery and reviews: lateness is the clearest cost to customer satisfaction, 6. The delivery promise changed, and it is the main story of 2018, 7. Customers: almost everyone buys once, 8. Payments (+15 more)

### Community 27 - "powerbi/README.md"
Cohesion: 0.14
Nodes (18): Power BI generators and project (src/powerbi, powerbi/), DD-06: Convert geolocation CSV to Parquet in the build, Out-of-time late-delivery scores export (export_scores.py), DASHBOARD_MOCKUP.html, DataFolder parameter, export_data.py (Power BI data export), First-open checklist, If the first refresh fails (+10 more)

### Community 28 - "base.json"
Cohesion: 0.05
Nodes (38): bad, color, fontFace, fontSize, center, dataColors, good, color (+30 more)

### Community 29 - "DRIFT_ANALYSIS.md"
Cohesion: 0.08
Nodes (26): Late delivery vs review score association (4.29 on time, 2.57 late), 2018 delivery promise shortened (75% of August orders under 20 days), 97% of customers buy once (repeat = 5.6% of revenue), Rio de Janeiro late-rate outlier (13.5% late, median 12 days), Seller concentration (top 10% of sellers = 67.5% of revenue), Insights correction: on-time orders produce ~70% of 1-2 star reviews, August 2018 is a change in promise policy, not a label problem, August 2018 delivery-promise policy shift (+18 more)

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

### Community 38 - "models.js"
Cohesion: 0.17
Nodes (26): Object Names for visualStyles, legend(), controlsRow(), segmented(), allocateSlots(), apply(), initTheme(), isDark() (+18 more)

### Community 39 - "AGENTS.md"
Cohesion: 0.50
Nodes (3): graphify, graphify knowledge graph (graphify-out/), graphify

### Community 40 - "test_register_model.py"
Cohesion: 0.07
Nodes (7): env(), FakeDB, FakeModelRef, FakeRegistry, FakeVersion, feature_frame(), test_failed_scoring_is_recorded_and_returns_nonzero()

### Community 41 - "stage_wrapper"
Cohesion: 0.14
Nodes (17): backtest_frame(), scores_frame(), stage_wrapper(), test_create_table_sql_is_idempotent_ddl(), test_each_write_uses_a_fresh_stage_folder(), test_failed_copy_rolls_back_and_cleans_up(), test_failed_parquet_write_leaves_no_temp_files_and_no_staging(), test_local_temporary_file_is_deleted() (+9 more)

### Community 42 - "risk.js"
Cohesion: 0.16
Nodes (22): card(), grid(), select(), dataTable(), insightGrid(), kpiRow(), getInsights(), insights (+14 more)

### Community 43 - "datasets"
Cohesion: 0.05
Nodes (41): bytes, file, rows, source, title, backend, datasets, analytics (+33 more)

### Community 45 - "story.mjs"
Cohesion: 0.07
Nodes (22): args, chrome, file, frame, frames, [frameX, frameY, frameWidth], html, [input, out] (+14 more)

### Community 46 - "Retail Analytics, Forecasting & Customer Intelligence Platform"
Cohesion: 0.05
Nodes (36): Access control, Batch inference, Customer, Data processing choice, dbt, Delivery, Dialect migration, Forecasting (+28 more)

### Community 84 - "late_delivery_baseline.py"
Cohesion: 0.09
Nodes (15): 4. Python integration, add_smoothed_rates(), calibration_table(), evaluate(), _is_data_access(), load(), main(), mean_days_to_deliver() (+7 more)

### Community 85 - "pathlib"
Cohesion: 0.07
Nodes (14): main(), main(), permutation_drop(), make_models(), main(), render(), build(), manifest() (+6 more)

### Community 86 - "validate_frame"
Cohesion: 0.24
Nodes (7): _kind_ok(), SchemaError, validate_frame(), test_validate_frame_accepts_matching_frame_and_other_units(), test_validate_frame_extra_columns_policy(), test_validate_frame_fails_on_missing_column(), test_validate_frame_fails_on_wrong_dtype()

### Community 87 - "Check details"
Cohesion: 0.07
Nodes (29): arg_max / max_by tie-breaks, Check details, dim_customer (dimension): PASS, dim_date (dimension): PASS, dim_geography (dimension): PASS, dim_product (dimension): PASS, dim_seller (dimension): PASS, Documented constants (three-way) (+21 more)

### Community 88 - "drift_analysis.py"
Cohesion: 0.30
Nodes (8): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts()

### Community 89 - "export_scores.py"
Cohesion: 0.13
Nodes (9): Table to Snowflake object mapping, What the `PBI` views must expose, build(), build_from(), main(), score_test_months(), export(), forecast_backtest() (+1 more)

### Community 90 - "orders"
Cohesion: 0.10
Nodes (23): Data dictionary: Snowflake + dbt implementation, Documentation coverage, `int_late_delivery_history`, `int_late_delivery_item_agg`, `int_late_delivery_population`, `int_late_delivery_seller_history`, Intermediate, late-delivery features (INTERMEDIATE, views), `mart_category_performance` (+15 more)

### Community 91 - "load_raw.py"
Cohesion: 0.11
Nodes (21): build_parser(), check_files_exist(), _check_put_result(), count_records(), default_connect(), describe_files(), ident(), IngestError (+13 more)

### Community 92 - "compare.py"
Cohesion: 0.12
Nodes (18): _as_decimal(), _candidates(), _coerce(), _compare_expected(), ok(), compare_frames(), compare_values(), ExpectedResult (+10 more)

### Community 93 - "test_powerbi_snowflake.py"
Cohesion: 0.10
Nodes (15): patched(), patched_ml_files(), _project_files(), _scan(), test_expressions_define_the_two_snowflake_parameters(), test_ml_on_files_keeps_datafolder_beside_the_snowflake_parameters(), test_ml_on_files_patches_only_the_nine_pbi_tables(), test_no_real_looking_account_or_credential_strings() (+7 more)

### Community 94 - "cli.py"
Cohesion: 0.07
Nodes (20): build_parser(), main(), _resolve_duckdb(), _split(), duckdb_side(), run_checks(), Side, snowflake_side() (+12 more)

### Community 95 - "test_snowflake_ingestion.py"
Cohesion: 0.14
Nodes (21): expected_rows_for(), FakeConnection, run_main(), test_changed_file_into_nonempty_table_is_refused_not_appended(), test_copy_exception_is_logged_failed_and_stops(), test_dry_run_emits_sql_and_never_connects_or_needs_credentials(), test_dry_run_reload_shows_truncate_and_force(), test_first_load_runs_put_copy_verify_log_for_every_table() (+13 more)

### Community 96 - "report.py"
Cohesion: 0.12
Nodes (19): _print_progress(), CheckResult, ColumnResult, display_value(), redact_account(), SnowflakeSettings, _cell(), _col_rows() (+11 more)

### Community 97 - "recalibration.py"
Cohesion: 0.22
Nodes (9): test_base_and_calibration_rows_do_not_overlap(), test_base_model_outcomes_are_known_before_the_calibration_window_starts(), test_calibrators_return_probabilities(), test_ece_is_zero_for_a_perfectly_calibrated_split(), test_platt_reduces_overconfidence(), test_shift_calibrator_matches_the_observed_rate(), test_split_uses_only_outcomes_known_before_the_test_month(), test_unknown_calibrator_is_rejected() (+1 more)

### Community 99 - "checks.py"
Cohesion: 0.18
Nodes (18): absolute(), all_checks(), _analytics_checks(), Check, ColumnRule, _dimension_checks(), Expected, _fact_checks() (+10 more)

### Community 100 - "pytest"
Cohesion: 0.28
Nodes (11): net(), table(), test_category_revenue_matches_and_shares_are_consistent(), test_delay_buckets_cover_every_reviewed_delivered_order(), test_delivery_trend_covers_the_same_population_as_the_ml_features(), test_monthly_growth_is_blank_next_to_thin_months(), test_monthly_kpis_add_up_to_net_revenue(), test_payment_shares_add_up_and_total_matches_the_fact() (+3 more)

### Community 101 - "pandas"
Cohesion: 0.07
Nodes (27): main(), read_monitor(), ConfirmationRequired, _confirmed(), connect(), _connect_snowflake(), DataAccessError, InvalidBackendError (+19 more)

### Community 102 - "render_data_dictionary.py"
Cohesion: 0.15
Nodes (13): collect(), describe_test(), first_comment(), layer_of(), load_manifest(), main(), md_cell(), mermaid_id() (+5 more)

### Community 103 - "test_data_access.py"
Cohesion: 0.07
Nodes (11): check_wrapped_equals_raw(), sf_wrapper(), test_duckdb_sql_text_matches_the_ml_modules(), test_normalise_dtypes(), test_real_warehouse_wrapped_equals_raw_and_validates(), test_snowflake_execute_and_close(), test_snowflake_late_features_match_duckdb_after_load(), test_snowflake_read_sql_normalises_and_binds_params() (+3 more)

### Community 104 - "load_table"
Cohesion: 0.20
Nodes (13): Executor, FileInfo, load_table(), _log_best_effort(), print_dry_run(), sql_copy(), sql_count(), sql_log_insert() (+5 more)

### Community 105 - "apply_snowflake_source.py"
Cohesion: 0.19
Nodes (9): apply(), _is_inside(), main(), patch_table(), PatchError, _read(), split_partition(), typed_step_arguments() (+1 more)

### Community 106 - "test_publish_ml.py"
Cohesion: 0.13
Nodes (5): FakeDB, frames(), patched(), test_compute_rejects_a_frame_with_a_missing_column(), test_hand_picked_run_ids_are_refused_before_connecting()

### Community 107 - "writeback.py"
Cohesion: 0.10
Nodes (17): DataAccess, is_data_access(), wrap_duckdb(), _conn(), copy_sql(), create_table_sql(), delete_sql(), _load() (+9 more)

### Community 108 - "Semantic model (12 tables, 13 relationships, 38 measures)"
Cohesion: 0.12
Nodes (20): August 2018 delivery promise change (concept drift), Features v3: trailing 28-day system late rate, Use the model by rank, not probability, flag_share helper table, forecast_backtest table, late_delivery_scores table, DAX measure group: Customers, DAX measure group: Delivery (+12 more)

### Community 109 - "weekly_series"
Cohesion: 0.13
Nodes (13): 6. Inventory C: SQL embedded in Python and notebooks, late_delivery_features(), load_dataset(), order_category(), _schema_ident(), unlabelled_share(), weekly_series(), conform_frame() (+5 more)

### Community 110 - "json"
Cohesion: 0.15
Nodes (16): Extending it, analytics_tables(), clean(), commit(), discard(), forecast_metrics(), forecasts(), git_sha() (+8 more)

### Community 111 - "Snowflake + dbt implementation: setup and runbook"
Cohesion: 0.11
Nodes (18): 10. Step 6: the HTML dashboard - RUN 2026-11-12, 11. Step 7: Power BI patched copy - NOT RUN, 12. Cost, 13. Where things stand, 1. Prerequisites, 2. Credentials and environment variables, 3. Offline checks (no Snowflake connection), 4. Step 1: preflight and setup - RUN 2026-11-12 (+10 more)

### Community 112 - "build_pbip.py"
Cohesion: 0.24
Nodes (10): dump(), field_json(), files(), lit(), main(), projection(), q(), relationships_tmdl() (+2 more)

### Community 113 - "4. Procedure"
Cohesion: 0.17
Nodes (12): 1. What each piece does, and what it never does, 2. Approval gate: what the account owner must approve, 3. Prerequisites, 4.0 Dry run (always do this first), 4.1 First load, 4.2 Re-run (no-op), 4.3 Reload, 4.4 Failure and recovery (+4 more)

### Community 114 - "Power BI switch guide: from the local files to Snowflake"
Cohesion: 0.06
Nodes (27): Action versions, CI setup (GitHub Actions), dbt-ci, dbt-live (manual), Known baseline failures (CI will be red until fixed), python-ci, Repository hygiene note, Required secrets (+19 more)

### Community 115 - ".name"
Cohesion: 0.15
Nodes (16): Anti-patterns, Bookmark Authoring, Bookmark buttons, Bookmark group, Bookmark index and groups, Bookmark navigator, Contents, Current page (+8 more)

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

### Community 121 - "model_spec.py"
Cohesion: 0.16
Nodes (10): m_load(), prop(), table_tmdl(), Check, col(), column_hidden(), m_type(), mea() (+2 more)

### Community 122 - "Snowflake + dbt architecture"
Cohesion: 0.25
Nodes (8): 1. End-to-end flow: DuckDB path and Snowflake path, 2. Snowflake objects and roles, 3.1 Layer overview, 3.2 Model-level lineage (generated from the dbt manifest), 3. dbt layers and lineage, 5. Power BI integration, 6. Design decisions that shape the architecture, Snowflake + dbt architecture

### Community 123 - "DuckDB to Snowflake + dbt: SQL migration inventory"
Cohesion: 0.11
Nodes (11): 10. Inventory D: SQL added for Snowflake (93 files), 1. Classification, 2. Reconciling `git ls-files "*.sql"`, 3. Summary counts, 5. Inventory B: `sql/bigquery` (reference only, 18 files), 8. Numeric, NULL-order, surrogate-key and tie-break caveats, 9. UNVERIFIED until a live Snowflake run, DuckDB to Snowflake + dbt: SQL migration inventory (+3 more)

### Community 124 - "test_dashboard.py"
Cohesion: 0.09
Nodes (7): _FakeSnowflake, test_every_js_file_parses(), test_failed_build_leaves_the_previous_build_intact(), test_no_innerhtml_in_dashboard_code(), test_order_category_matches_keys_sql_on_the_mini_warehouse(), test_order_category_reads_the_snowflake_intermediate_model(), test_snowflake_analytics_marts_are_put_in_the_reference_order()

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

### Community 129 - "Comparison"
Cohesion: 0.14
Nodes (12): Conditional Formatting Patterns - Part 5, Contents, Number vs percent thresholds (and percentile), Rule bounds: one-sided vs two-sided ranges, Type 2: Rules-Based Formatting, 4.1 Staging (9 files, class 3), 4.2 Dimensions (5 files), 4.3 Facts (4 files, class 2) (+4 more)

### Community 130 - "Staging (STAGING, views)"
Cohesion: 0.20
Nodes (10): Staging (STAGING, views), `stg_olist__category_translation`, `stg_olist__customers`, `stg_olist__geolocation`, `stg_olist__order_items`, `stg_olist__order_payments`, `stg_olist__order_reviews`, `stg_olist__orders` (+2 more)

### Community 131 - "Marts, core star schema (MARTS, tables)"
Cohesion: 0.15
Nodes (13): month(), `dim_customer`, `dim_date`, `dim_geography`, `dim_product`, `dim_seller`, `fact_order_items`, `fact_orders` (+5 more)

### Community 132 - "Power BI views (PBI, views)"
Cohesion: 0.22
Nodes (9): `pbi_dim_customer`, `pbi_dim_geography`, `pbi_dim_product`, `pbi_dim_seller`, `pbi_fact_order_items`, `pbi_fact_orders`, `pbi_fact_payments`, `pbi_fact_reviews` (+1 more)

### Community 133 - "dbt project: Olist on Snowflake"
Cohesion: 0.33
Nodes (6): Commands, dbt project: Olist on Snowflake, Environment (isolated from the repo root), Layout and conventions, Translation notes (DuckDB -> Snowflake), Verification summary (offline)

### Community 134 - "barChart"
Cohesion: 0.14
Nodes (26): Column/Bar Family, Line Family, Visual Type Families, Use, Choosing the Anchor Chart, Use, Power BI Visual Type Crosswalk, Placements (+18 more)

### Community 136 - "EDA findings: Olist dataset discovery"
Cohesion: 0.40
Nodes (5): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data

### Community 137 - "argparse"
Cohesion: 0.20
Nodes (4): main(), main(), NoCacheHandler, main()

### Community 139 - "Effects"
Cohesion: 0.29
Nodes (7): Dithering, Duotone, Effects, Glyphs, Halftone dots, Implementation, Performance

### Community 140 - "Visuals"
Cohesion: 0.29
Nodes (7): Decide what the visual is, Generate it, Objects for moments, Prompt recipe, Put it on the page, Styles that work, Visuals

### Community 141 - "fake_connector"
Cohesion: 0.22
Nodes (6): clean_env(), fake_connector(), connect(), _populate(), populated(), sf_env()

### Community 235 - "Intermediate (INTERMEDIATE, views)"
Cohesion: 0.33
Nodes (6): `int_customers_latest`, `int_geography_points`, `int_geography_rollup`, `int_order_items_agg`, `int_order_payments_agg`, Intermediate (INTERMEDIATE, views)

### Community 236 - "MLOps Lifecycle"
Cohesion: 0.50
Nodes (3): ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability

### Community 237 - "AUDIT.md"
Cohesion: 0.10
Nodes (23): Current state (2026-10-13), Data findings (Phase 0 and EDA), Decisions (made by the user), Environment notes, Handover: GCP Retail Analytics (local DuckDB build), graphify knowledge graph, Open items, What this project is now (+15 more)

### Community 238 - "register_model.py"
Cohesion: 0.13
Nodes (15): backtest_metrics(), check_in_warehouse(), fit(), git_sha(), log_kwargs(), main(), parity_sample(), predict_proba_sql() (+7 more)

### Community 239 - "powerbi-report-cli/SKILL.md"
Cohesion: 0.08
Nodes (18): Contents, Ensure a slicer and a visual exist on the page, Field Parameters (report-side pattern), Recognizing an existing field parameter, Target-visual projection encoding, Workflow, Contents, Fallback: the `powerbi-desktop` bridge CLI (+10 more)

### Community 240 - "Narrative / Data Story"
Cohesion: 0.08
Nodes (25): Annotation Techniques, Annotation Z-Order, Chart Selection, Color & Typography, Contents, Core Principles, Decision Checklist, Decision Table: Which Pattern? (+17 more)

### Community 241 - "show"
Cohesion: 0.12
Nodes (13): Dual-Entry Pattern (Required), ribbonBands — Stacked Charts, Background Images, Canvas Background (`background`), Contents, Dynamic Color Limitation, Page-Level Formatting (`page.json` objects), See Also (+5 more)

### Community 245 - "needs_real_data"
Cohesion: 0.50
Nodes (3): test_loader_column_specs_match_real_csv_headers(), test_real_files_record_counts_and_headers(), test_real_reviews_has_99224_records_not_line_count()

### Community 246 - "Accessibility for Data Visualization"
Cohesion: 0.09
Nodes (22): 1. Headline + Trend, 2. Chart Structure + Notable Finding, 3. Comparison Framing, 4. Data-as-Table Fallback, Accessibility for Data Visualization, Accessibility Testing Checklist, Alt Text Patterns, Archetype Accessibility Priorities (+14 more)

### Community 248 - "make_snowflake_notebooks.py"
Cohesion: 0.29
Nodes (9): code(), main(), md(), must_replace(), nb02(), nb03(), nb04(), port() (+1 more)

### Community 249 - "Operational Monitor Dashboard"
Cohesion: 0.09
Nodes (22): Chart Selection, Color & Typography, Contents, Core Principles, Decision Checklist, Do NOT Use, Exception Table, Freshness & Refresh (+14 more)

### Community 250 - "Measure"
Cohesion: 0.11
Nodes (19): Authoring Workflow, Charts, Conditional Formatting Patterns, Contents, Data-Bound Expression Rules, Formatting Options by Visual Type, Choose gradient colors by measure meaning, Conditional Formatting Patterns - Part 4 (+11 more)

### Community 251 - "Executive Summary Dashboard"
Cohesion: 0.10
Nodes (19): Card / CardVisual, Chart Selection, Color & Typography, Contents, Core Principles, Decision Checklist, Do NOT Use, Do NOT Use (+11 more)

### Community 252 - "Color Strategy"
Cohesion: 0.10
Nodes (19): Archetype Calibration, Categorical Palettes, Color Assignment Rules, Color Assignment Strategy, Color Strategy, Color Vision Deficiency (CVD) and WCAG Contrast, Conditional Formatting Techniques, Contents (+11 more)

### Community 253 - "test_warehouse.py"
Cohesion: 0.22
Nodes (3): features(), test_seller_history_matches_a_direct_recount_on_real_data(), test_weekly_series_covers_the_documented_window()

### Community 254 - "main.js"
Cohesion: 0.23
Nodes (18): cache, dataset(), fetchJson(), load(), manifest(), refresh(), clear(), disposeCharts() (+10 more)

### Community 255 - "Expression Tree Templates"
Cohesion: 0.11
Nodes (17): Aggregation Expression, Column Expression, Comparison Expression, Contains/StartsWith Expression, Contents, Entity Source Expression, Expansion state, Expression Tree Templates (+9 more)

### Community 256 - "test_drift_helpers.py"
Cohesion: 0.57
Nodes (5): frame(), test_relative_rates_are_positive_for_a_late_route(), test_relative_rates_are_zero_when_route_matches_the_system(), test_system_counts_do_not_depend_on_row_order(), test_system_counts_use_only_orders_delivered_strictly_before_purchase()

### Community 257 - "Version Control for PBIR Editing"
Cohesion: 0.11
Nodes (17): 1. Create a working branch, 2. Make changes, 3. Validate & verify, 4. Ask user before committing, 5. Continue or finish, Branching Workflow, Contents, Decision Tree (+9 more)

### Community 258 - "Retail analytics dashboard (HTML)"
Cohesion: 0.50
Nodes (4): How it is organised, Refresh the data, Retail analytics dashboard (HTML), Run it

### Community 259 - "Layout Composition"
Cohesion: 0.11
Nodes (17): 12-Column Grid, 1–3 slicers — inline with title, 4+ slicers — vertical filter rail, 8-Point Base Grid, Bounds and overlap, Composition Templates, Concrete Arithmetic (FHD 1920 x 1080 canvas), Contents (+9 more)

### Community 262 - "Table & Matrix Visual Authoring Guide"
Cohesion: 0.12
Nodes (16): `backColor` vs `backColorPrimary` — Different Purposes, Column width (static), Conditional Formatting, Contents, Default Rule — Grow to Fit, `fontColor` vs `fontColorPrimary` — Different Purposes (pivotTable), Full Table Example with Custom Styling, Matrix (`pivotTable`) (+8 more)

### Community 263 - "test_scoring_task_sql.py"
Cohesion: 0.31
Nodes (5): strip_comments(), test_predict_proba_arguments_match_the_shared_helper(), test_setup_files_are_additive_and_keep_placeholders(), test_task_is_idempotent_and_non_destructive(), test_task_never_writes_the_backtest_scores_table()

### Community 264 - "Tone Catalog"
Cohesion: 0.12
Nodes (16): 10. Corporate Cool, 11. Scholarly Calm, 12. Brand-Forward (template), 1. Editorial Newsroom, 2. Industrial Cockpit, 3. Clinical Calm, 4. FT Pink Financial, 5. Bauhaus Catalog (+8 more)

### Community 265 - "powerbi-report-cli planning mode -- Power BI Report Planning"
Cohesion: 0.12
Nodes (16): AVOID, Contents, Dependency Checklist, Entry modes — how the user is starting, Examples of When to Use, MUST, Must/Prefer/Avoid, powerbi-report-cli planning mode -- Power BI Report Planning (+8 more)

### Community 266 - "Lessons learned"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 267 - "el"
Cohesion: 0.31
Nodes (12): heatmap(), draw(), luminance(), STEPS, createTooltip(), append(), apply(), cssVar() (+4 more)

### Community 268 - "Card Visual Authoring Guide - Part 3"
Cohesion: 0.12
Nodes (15): Accent bar, Card Visual Authoring Guide - Part 3, cardCalloutArea, Contents, Discovering Properties, divider, Instance selectors required, Key Formatting Rules (+7 more)

### Community 270 - "Cartesian Visuals (Bar, Column, Line, Scatter)"
Cohesion: 0.12
Nodes (15): Cartesian Visuals (Bar, Column, Line, Scatter), Category Drill Hierarchy, Contents, dataPoint — Color Assignment, Date Hierarchy Binding, Formatting Patterns, Multiple Y Measures, One bubble per group — the single-point pitfall (+7 more)

### Community 278 - "Conditional Formatting Patterns - Part 7"
Cohesion: 0.12
Nodes (15): Aggregation Function values, Applies to tables and matrices, Category consistency across visuals, Chart color inheritance, Chart field-value color, Column width — not conditionally formattable, Conditional Formatting Patterns - Part 7, Contents (+7 more)

### Community 279 - "Theme Authoring — theme.json Reference"
Cohesion: 0.12
Nodes (15): 1. Data Colors (`dataColors`), 2. Sentiment Colors, 3. Gradient Defaults, 4. Structural Colors, 5. Text Classes (`textClasses`), 7. Style Presets, Limitations, Registering a Custom Theme (+7 more)

### Community 280 - "Comparative Benchmark - Part 2"
Cohesion: 0.12
Nodes (15): Color & Typography, Comparative Benchmark - Part 2, Comparison Charts, Contents, Decision Checklist, Diverging Palette, IBCS Purist Palette, Interaction Design (Moderate) (+7 more)

### Community 281 - "Workflow"
Cohesion: 0.12
Nodes (16): AVOID, Gotchas, MUST, Must/Prefer/Avoid, powerbi-report-cli design mode -- Power BI Report Visual Design, PREFER, Step 0 — Data-First Investigation, Step 1 — Design Identity (+8 more)

### Community 282 - "Examples: CRUD Operations"
Cohesion: 0.12
Nodes (15): Conceptual fallback safety requirements (not an executable workflow), Contents, Create Report (with Definition), Decode Definition Parts to Local Files, definition.pbir — Semantic Model Reference, Delete Report, Examples: CRUD Operations, Get Report Definition (+7 more)

### Community 283 - "Contents"
Cohesion: 0.13
Nodes (14): Cartesian Visuals (Bar, Column, Line, Scatter) - Part 2, categoryAxis / valueAxis, Conditional Colors, Contents, Invert Axis (`invertAxis`), labels — Data Labels, layout — Gap & Series Order, legend (+6 more)

### Community 284 - "Anti-Patterns — The Dashboard Slop Catalog"
Cohesion: 0.13
Nodes (14): Anti-Patterns — The Dashboard Slop Catalog, Cluster 1 — Visual Noise (Chartjunk), Cluster 2 — Misleading Encoding, Cluster 3 — Cognitive Overload, Cluster 4 — Color Misuse, Cluster 5 — Interactivity Theater, Cluster 6 — Archetype Mismatch, Contents (+6 more)

### Community 285 - "Comparative / Benchmark Dashboard"
Cohesion: 0.13
Nodes (14): Callout Evidence Rule, Chart Selection, Comparative / Benchmark Dashboard, Contents, Core Principles, Do NOT Use, IBCS Primer, Job To Be Done (+6 more)

### Community 286 - "Page layout contract"
Cohesion: 0.13
Nodes (14): Analytical Canvas with filter rail, Canvas, Common region patterns, Contents, Date slicer example variants, Design Brief Contract - Part 2, Executive Summary with inline slicers, Grid regions (+6 more)

### Community 287 - "parametrize"
Cohesion: 0.15
Nodes (9): _assert_same_line_endings(), _split_outside_block(), test_model_files_are_byte_identical(), test_no_datafolder_left_in_data_sources(), test_patch_keeps_either_line_ending_style(), test_table_file_is_unchanged_outside_the_partition_source(), test_template_column_types_equal_the_originals(), test_template_navigates_the_right_snowflake_object() (+1 more)

### Community 288 - "Authoring Workflows & Examples"
Cohesion: 0.14
Nodes (13): Add a New Page, Add a Visual to a Page, Authoring Workflows & Examples, Change Theme, Common Layout Templates, Contents, Drillthrough Page, Format Versions (+5 more)

### Community 289 - "Button Sizing & Placement (Required)"
Cohesion: 0.14
Nodes (13): Button Sizing & Placement (Required), Button Visual Authoring Guide, CLI Discovery, Contents, Placement, Step 0: Gather inputs, Step 1: Compute width (prevents horizontal truncation), Step 2: Set height (fixed range — do NOT derive by shrinking) (+5 more)

### Community 290 - "Card Sizing (Required)"
Cohesion: 0.14
Nodes (13): Card Sizing Anti-Patterns, Card Sizing (Required), Card Visual Authoring Guide - Part 2, Contents, Default values (cascade resolution), Quick-reference safe dimensions, Step 0: Read the canvas height, Step 1: Compute dimensions (+5 more)

### Community 291 - "Formatting Patterns"
Cohesion: 0.14
Nodes (13): Auto-Generated Subtitles, Color Strategy & Patterns, Conditional Formatting, Contents, Formatting JSON Structure, Formatting Patterns, Literal Values, Page Objects vs Visual Container Objects (+5 more)

### Community 292 - "Layers"
Cohesion: 0.14
Nodes (13): 3D column (`barChart`), Add Data-Driven Formatting, Azure Map Visual Authoring Guide, Contents, Heat map (`heatMapLayer`), Layers, Markers — icon, size, and clustering (`bubbleLayer`), Overview (+5 more)

### Community 293 - "Slicer Authoring Guide - Part 2"
Cohesion: 0.14
Nodes (13): Add/Modify a Slicer, Calendar Date Picker Templates, Contents, Date Between Slicer Template, Discovering Properties, Manual, Relative, Resolve the date field and preselection (+5 more)

### Community 294 - "Signatures"
Cohesion: 0.14
Nodes (13): Authoring fresh signatures, Composing tone + signature, Contents, Iconographic signatures, S10. Hairline rules instead of borders, S11. Pill-shaped section labels, S12. Modular grid with consistent gutter, S13. Duotone iconography on KPI cards (+5 more)

### Community 295 - "Typography for Data"
Cohesion: 0.14
Nodes (13): Alignment Rules, Archetype Calibration, Contents, Core Principles, Custom font fallback caveat, Density & Readability, Font Family Guidance, Number Format Decision Table (+5 more)

### Community 296 - "Power BI Reports - CLI Skill"
Cohesion: 0.14
Nodes (14): Authoring, AVOID, Complete Reference Index, Design, Examples, Mode Boundary Rules, Mode Guides, Mode Selection (+6 more)

### Community 297 - "labels.js"
Cohesion: 0.22
Nodes (11): BASELINES, FAMILIES, FEATURE_SETS, humanize(), methodLabel(), METHODS, METRICS, modelInfo() (+3 more)

### Community 298 - "Custom Visuals (AppSource, Organizational, Private `.pbiviz`)"
Cohesion: 0.15
Nodes (12): 1. AppSource (public) visual, 2. Organizational (org store) visual, 3. Private (`.pbiviz`) visual, AppSource licensing and freemium data caps, Binding data to a custom visual, Contents, Custom Visuals (AppSource, Organizational, Private `.pbiviz`), Desktop verification (+4 more)

### Community 299 - "Add a Filter"
Cohesion: 0.15
Nodes (12): Add a Filter, Advanced Filter, Categorical Filter (In-list), Contents, Exclude/Include Filter, Filter Types, Filters authoring Workflows & Examples, Inverted Selection (Exclude) (+4 more)

### Community 300 - "Analytical Canvas"
Cohesion: 0.15
Nodes (12): Analytical Canvas, Chart Selection, Contents, Control Selection Table, Core Principles, Decision Checklist, Do NOT Use, Filter Rail Design (+4 more)

### Community 301 - "Chart Selection Decision Framework"
Cohesion: 0.15
Nodes (12): Archetype Applicability, Cardinality Limits by Visual Type, Chart Selection Decision Framework, Contents, Core Principle, Decision Checklist, Edge Cases & Exceptions, Encoding Accuracy Hierarchy (+4 more)

### Community 302 - "Interactivity & Storytelling"
Cohesion: 0.15
Nodes (12): 5 Clusters, Bookmark Design Rules, Contents, Core Principles, Cross-Filter Etiquette, Descriptive Titles & Information Scent, Interaction Complexity Budget, Interaction Taxonomy (+4 more)

### Community 303 - "text"
Cohesion: 0.18
Nodes (11): Action Types, Button Visual Authoring Guide - Part 2, Conditional Formatting (Data-Driven Color), Contents, Data Function (translytical task flow), Formatting Objects, Icon Options, Shape Options (+3 more)

### Community 304 - "powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP) - Part 3"
Cohesion: 0.17
Nodes (11): Authoring Metadata & Validation CLI, Contents, Custom visuals (AppSource / organizational / private `.pbiviz`), Edit → Validate → Preview → Review, Instance Selectors, Mandatory Screenshot Review, powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP) - Part 3, Prefer modern visual types (+3 more)

### Community 305 - "Re-theming Workflow"
Cohesion: 0.17
Nodes (11): Contents, Preventive Authoring: Theme-Adaptive Visuals, Re-theming an Existing Report, Re-theming & Dark Mode — Workflow Reference - Part 2, Re-theming Workflow, Step 0: Build a color mapping table, Step 1: Update theme JSON AND bulk-replace all old colors (single atomic step), Step 2: Audit per-visual formatting for gaps (+3 more)

### Community 306 - "Theme Authoring — theme.json Reference - Part 2"
Cohesion: 0.17
Nodes (11): 10. Custom Icons, 8. ThemeDataColor Resolution, 9. Theme Defaults for Page Objects, Common Percent Values, Common Pitfalls, Contents, Re-theming & Dark Mode, Resolution Algorithm (+3 more)

### Community 307 - "Contents"
Cohesion: 0.17
Nodes (11): Conditional Formatting — MANDATORY, Contents, Date Between Slicer (`slicer`, mode: Between), Dropdown Slicer (`slicer`, mode: Dropdown), Scatter (`scatterChart`), Slicers, Temporal slicer decision matrix, Textbox (page titles, annotations) (+3 more)

### Community 308 - "powerbi-report-cli planning mode -- Power BI Report Planning - Part 2"
Cohesion: 0.17
Nodes (11): Anti-Patterns and Pitfalls, Approval Gate, Contents, Design Contract Gate, Fabric Publish Rules, Implementation After Approval, Locked Report Spec Output, powerbi-report-cli planning mode -- Power BI Report Planning - Part 2 (+3 more)

### Community 309 - "Image Visual Authoring Guide"
Cohesion: 0.18
Nodes (10): 1. Local file path to the image, 2. A url (from the web), 3. Select from data, Example — Local registered resource as plot area background, Image Formatting (`objects.image`), Image object vs Visual Container Objects (VCO) — overlapping properties, Image Visual Authoring Guide, Plot Area Background Image (`plotArea.image`) (+2 more)

### Community 310 - "Dark Mode Authoring Checklist"
Cohesion: 0.18
Nodes (10): Dark Mode Authoring Checklist, Re-theming & Dark Mode — Workflow Reference - Part 3, Step 1: Theme structural colors, Step 2: Page canvas backgrounds, Step 3: Filter pane + filter cards, Step 4: Slicer entries in `visualStyles`, Step 5: Azure Map basemap style, Step 6: Table/matrix `stylePreset` = `'None'` (+2 more)

### Community 311 - "Button Visual Authoring Guide - Part 3"
Cohesion: 0.20
Nodes (9): Anti-Patterns, Back button, Button Visual Authoring Guide - Part 3, Common Patterns, Contents, Drillthrough button, Hover State Example, Navigation bar (multiple page buttons) (+1 more)

### Community 312 - "Cartesian Visuals (Bar, Column, Line, Scatter) - Part 3"
Cohesion: 0.20
Nodes (9): Bar Chart (Minimal), Cartesian Visuals (Bar, Column, Line, Scatter) - Part 3, Clustered Bar Chart with Per-Measure Colors, Clustered Bar Chart (with Per-Series Color), Complete Examples, Contents, Minimal Examples, smallMultiplesLayout — Rows Role (+1 more)

### Community 313 - "powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP) - Part 2"
Cohesion: 0.20
Nodes (9): CLI Setup, Contents, Greenfield: creating a brand-new report, Greenfield / Design Handoff, Key Files, Large Build Execution, PBIR File Layout, powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP) - Part 2 (+1 more)

### Community 314 - "Shape Visual"
Cohesion: 0.20
Nodes (9): Available Shapes and Formatting, Basic Example (Rectangle Divider), Complete Example (Arrow with All Formatting), Conditional Formatting (Data-Driven Color), Container Shapes, Contents, Rotation, Shape Text Caveat (+1 more)

### Community 315 - "powerbi-report-cli management mode -- Power BI Report Items in Fabric"
Cohesion: 0.20
Nodes (9): Authentication, Companion Skills, Contents, Deterministic PBIR Transport Helper, Finding Workspaces and Reports, Modern-PBIR preflight before pack, powerbi-report-cli management mode -- Power BI Report Items in Fabric, Resolve Report ID by Name (+1 more)

### Community 316 - "test_notebooks_snowflake.py"
Cohesion: 0.29
Nodes (6): code_cells(), test_cells_parse_and_use_the_notebook_session(), test_notebooks_store_no_outputs(), test_ported_notebooks_keep_every_original_analysis_cell(), test_the_three_notebooks_exist_and_are_up_to_date(), test_train_register_notebook_never_sets_the_default_version()

### Community 317 - "authoring.md"
Cohesion: 0.22
Nodes (8): AVOID, Contents, Critical notes, MUST, Must/Prefer/Avoid, powerbi-report-cli authoring mode -- Power BI Report Authoring (PBIR/PBIP), PREFER, Quick Start Workflow

### Community 318 - "Selectors (Targeting Specific Data)"
Cohesion: 0.22
Nodes (9): DataViewWildcard Selector, Dual-Entry Pattern, ID Selector (Instance Selector), Metadata Selector, No Selector (Static / Base), Scope Identity Selector, Selector Types and Precedence, Selectors (Targeting Specific Data) (+1 more)

### Community 319 - "`definition.pbir` — Report → Semantic Model Binding"
Cohesion: 0.22
Nodes (8): Contents, `definition.pbir` — Report → Semantic Model Binding, Error → fix quick reference (Desktop connection dialogs), Form 1 — `byPath` (local co-located model), Form 2 — `byConnection` live to a remote Fabric model (report host), Form 3 — `byConnection` for Fabric REST API publish, Pick the right form first, See also

### Community 320 - "Pre-Flight Checklist"
Cohesion: 0.22
Nodes (8): Accessibility (Step 7), Contents, Final visual audit (after build), Identity (Step 1), Page-level layout (Step 6), Pre-Flight Checklist, Routing (Steps 2–3), Theme & propagation (Step 1 → Step 5)

### Community 321 - "snapshot.mjs"
Cohesion: 0.22
Nodes (3): args, chrome, positionals

### Community 322 - "Color Strategy & Patterns"
Cohesion: 0.25
Nodes (7): Color Strategy & Patterns, Color Strategy Quick Reference, Contents, Pattern: Cross-Visual Measure-Color Consistency, Pattern: Different Formatting for Totals vs Data, Pattern: Per-Series Colors, Pattern: Single-Series Default Color

### Community 323 - "Conditional Formatting Patterns - Part 3"
Cohesion: 0.25
Nodes (7): Aggregation: columns vs. measures, Buttons and shapes, Color value results (hex), Conditional Formatting Patterns - Part 3, Contents, Driving field vs. target field, Selector summary by visual type

### Community 324 - "Formatting Patterns - Part 2"
Cohesion: 0.25
Nodes (7): Background Images — Routing, Formatting Patterns - Part 2, Line & Marker Formatting (lineStyles / markers), Page-Level Formatting (`page.json` objects), References, Row Banding (Table & Matrix), Shape Visual Formatting

### Community 325 - "`powerbi-report-author` CLI Reference"
Cohesion: 0.25
Nodes (7): Command catalog, Contents, `powerbi-report-author` CLI Reference, Preview result handling, Rendering preview vs PBIR inspection commands, Screenshot options, Validation result handling

### Community 326 - "Report Preview"
Cohesion: 0.25
Nodes (7): Argument selection, Contents, Core workflow, Desktop operation routing, Direct topic routes, Host selection, Report Preview

### Community 327 - "Report Preview - Part 2"
Cohesion: 0.25
Nodes (7): Contents, Errors and fix/retry, Exact command examples, Preview lifecycle, Report Preview - Part 2, Status and ambiguity, Unsaved host changes

### Community 328 - "Checklist"
Cohesion: 0.25
Nodes (7): Checklist, Common screenshot problems, Data rendering, Formatting and theming, Layout and visibility, Review workflow, Screenshot Review

### Community 329 - "Recommended Defaults"
Cohesion: 0.25
Nodes (7): Contents, Fill variant, Recommended Defaults, Sizing, Slicer Authoring Guide, Slicer Template, `Values` projection count

### Community 330 - "Agentic Workflow"
Cohesion: 0.25
Nodes (7): Agentic Workflow, Contents, Creating a new report in Fabric, Modifying an existing report in Fabric, powerbi-report-cli management mode -- Power BI Report Items in Fabric - Part 4, Publishing a local `.pbip`, Troubleshooting

### Community 331 - "Contents"
Cohesion: 0.29
Nodes (6): Azure Maps layers, Card, Chart target capability matrix, Conditional Formatting Patterns - Part 2, Contents, KPI

### Community 332 - "Conditional Formatting Patterns - Part 6"
Cohesion: 0.29
Nodes (6): Conditional Formatting Patterns - Part 6, Contents, Icon name catalog, Type 3: Icon Sets, Type 4: Data Bars, Type 5: Web URL

### Community 333 - "Power BI Desktop Preview Routing"
Cohesion: 0.29
Nodes (6): Canonical entry point, Contents, Desktop operations, Failures and diagnostics, Model-aware reload, Power BI Desktop Preview Routing

### Community 334 - "Brownfield Redesign — Entry Workflow"
Cohesion: 0.29
Nodes (6): Brownfield Redesign — Entry Workflow, Brownfield-specific Pre-Flight items, Entry workflow (6 steps), How each Step changes in brownfield mode, Theme-swap shortcut (light↔dark), When this file applies

### Community 335 - "Design Brief Contract"
Cohesion: 0.29
Nodes (6): Contents, Design Brief Contract, Full template, Minimal-brief escape hatch, Required marker, Why the structure

### Community 336 - "Phase 2: baseline results"
Cohesion: 0.29
Nodes (7): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests

### Community 338 - "parametrize"
Cohesion: 0.29
Nodes (5): test_entry_points_reject_unknown_backend_from_env(), test_entry_points_snowflake_backend_needs_config_and_confirmation(), test_only_confirm_one_counts(), test_writeback_rejects_unsafe_run_ids_before_touching_snowflake(), test_writeback_statement_sequence_is_atomic_and_never_destructive()

### Community 339 - "Filter Pane & Filter Card Formatting"
Cohesion: 0.33
Nodes (5): Contents, Filter Cards (`filterCard`), Filter Pane & Filter Card Formatting, Filter Pane (`outspacePane`), Theme-Level Styling

### Community 340 - "Textbox Visual Authoring Guide"
Cohesion: 0.33
Nodes (5): Contents, Dynamic textbox value, Rules, Static textbox title, Textbox Visual Authoring Guide

### Community 341 - "Archetype Composition & Variant Rotation"
Cohesion: 0.33
Nodes (5): Archetype Composition & Variant Rotation, Avoid mono-archetype reports, Common multi-archetype compositions, Composition vs. tone, Cross-page variant rotation

### Community 342 - "Must/Prefer/Avoid"
Cohesion: 0.33
Nodes (5): AVOID, MUST, Must/Prefer/Avoid, powerbi-report-cli management mode -- Power BI Report Items in Fabric - Part 3, PREFER

### Community 343 - "Card Visual Authoring Guide"
Cohesion: 0.40
Nodes (4): Card Visual Authoring Guide, Contents, Multi-Value Template, Single-Value Template

### Community 344 - "Contents"
Cohesion: 0.40
Nodes (4): Cartesian Visuals (Bar, Column, Line, Scatter) - Part 4, Contents, Line Chart with Y2 Secondary Axis and Per-Series Styling, Stacked Column Chart with Ribbons and Totals

### Community 345 - "Field-Value Result Contracts and Support Guardrails"
Cohesion: 0.40
Nodes (5): Field-Value Result Contracts and Support Guardrails, Result contracts, Shared authoring checks, Support decision and fallbacks, Validation and diagnostics

### Community 346 - "Formatting & Theming Overview"
Cohesion: 0.40
Nodes (4): Formatting Cascade, Formatting & Theming Overview, Selector Types (Quick Reference), Static Property Value Encoding — Three Formats

### Community 347 - "6. Visual Styles (`visualStyles`)"
Cohesion: 0.40
Nodes (5): 6. Visual Styles (`visualStyles`), Encoding in visualStyles, Example — Universal + Type-Specific, The `$id` Property — Instance Discrimination, Three-Level Hierarchy

### Community 348 - "PBI Formatting Reference"
Cohesion: 0.40
Nodes (5): Analytical Visuals, Page-Level Settings, PBI Formatting Reference, Slicers, size()

### Community 349 - "Chromatic signatures"
Cohesion: 0.40
Nodes (5): Chromatic signatures, S5. Single-accent discipline, S6. Highlight-and-grey, S7. FT pink (or any tinted) surface, S8. Status-coded KPI cards

### Community 350 - "Typographic signatures"
Cohesion: 0.40
Nodes (5): S1. Tabular numerals throughout, S2. Display serif headlines, S3. All-caps tracked headlines, S4. Caption-style annotations under every visual, Typographic signatures

### Community 351 - "Color & Typography"
Cohesion: 0.50
Nodes (4): Color & Typography, Focus + Context, Palette Strategy, Typography

### Community 352 - "Layout Variants"
Cohesion: 0.50
Nodes (4): Layout Variants, Variant A — Filter-Rail (default for dense exploration), Variant B — Inline-Slicers (1–3 slicers, content gets full width), Variant C — Small-Multiples-Grid

### Community 353 - "Bookmark state"
Cohesion: 0.67
Nodes (3): Bookmark state, Options mapping, Target visuals

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **37 isolated node(s):** `powerbi-report-cli`, `gcp`, `retail-olist-dbt`, `retail-olist-ml-registry`, `Always-predict-training-late-rate baseline` (+32 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1791 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **154 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Measure` connect `Measure` to `Comparison`, `Conditional Formatting Patterns - Part 3`, `Table & Matrix Visual Authoring Guide`, `Custom Visuals (AppSource, Organizational, Private `.pbiviz`)`, `Contents`, `Add a Filter`, `Cartesian Visuals (Bar, Column, Line, Scatter)`, `show`, `Conditional Formatting Patterns - Part 7`, `model_spec.py`?**
  _High betweenness centrality (0.172) - this node is a cross-community bridge._
- **What connects `powerbi-report-cli`, `gcp`, `retail-olist-dbt` to the rest of the system?**
  _37 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `build_spec_html.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14619883040935672 - nodes in this community are weakly interconnected._
- **Why does `text()` connect `text` to `Typographic signatures`, `Formatting Patterns`, `Conditional Formatting Patterns - Part 3`, `barChart`, `show`, `Re-theming Workflow`, `make_snowflake_notebooks.py`, `Shape Visual`, `Page layout contract`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Should `Architecture Philosophy (Shared Across Cloud Projects)` be split into smaller, more focused modules?**
  _Cohesion score 0.13725490196078433 - nodes in this community are weakly interconnected._
- **Should `fact_order_items (grain: order item, 112,650 rows)` be split into smaller, more focused modules?**
  _Cohesion score 0.06025641025641026 - nodes in this community are weakly interconnected._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._