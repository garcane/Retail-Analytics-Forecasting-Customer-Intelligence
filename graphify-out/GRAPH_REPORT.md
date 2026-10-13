# Graph Report - GCP  (2026-10-13)

## Corpus Check
- 81 files · ~70,200 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 12 file(s) not represented in the graph (top: .csv 8, (none) 2, .ipynb 1)

## Summary
- 665 nodes · 1190 edges · 55 communities (31 shown, 24 thin omitted)
- Extraction: 94% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 65 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `2323c54d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- AUDIT.md
- pandas
- Architecture Philosophy (Shared Across Cloud Projects)
- recalibration.py
- pytest
- fact_order_items (grain: order item, 112,650 rows)
- duckdb
- fact_order_items
- test_feature_leakage.py
- Phase 0 — Discovery Report
- Orders delivered late % (metric)
- numpy
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
- EDA findings: Olist dataset discovery
- Lessons learned
- Recalibration and training window for the v1 late-delivery model
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
10. `ensure_geolocation_parquet()` - 10 edges

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

## Communities (55 total, 24 thin omitted)

### Community 0 - "AUDIT.md"
Cohesion: 0.05
Nodes (67): build_warehouse.py (build and validate script), warehouse.duckdb (single local database file), Compute, Cost, If the project moved to the cloud, Total cloud cost $0, D-001: Implementations use DuckDB, D-002: Local only (+59 more)

### Community 1 - "pandas"
Cohesion: 0.07
Nodes (28): add_relative_rates(), e1_feature_skill(), e2_persistence(), e_lag(), fit_score(), macro(), main(), with_system_counts() (+20 more)

### Community 2 - "Architecture Philosophy (Shared Across Cloud Projects)"
Cohesion: 0.05
Nodes (41): Cloud Portfolio Master Agent Prompt, Data Warehousing and Analytical Modelling (grain, star schema), Layered Data Architecture (RAW/STAGING/CURATED/ANALYTICAL), Local to Cloud Progression Lifecycle, ML Methodology (target, leakage, baseline first), MLOps Lifecycle, Model Evaluation and Explainability, Three-Project Cloud Portfolio (Azure Healthcare, AWS Finance, GCP Retail) (+33 more)

### Community 3 - "recalibration.py"
Cohesion: 0.13
Nodes (22): calibration_split(), expected_calibration_error(), experiment_recalibration(), experiment_window(), fit_v1(), logit(), macro(), main() (+14 more)

### Community 4 - "pytest"
Cohesion: 0.14
Nodes (14): net(), table(), test_category_revenue_matches_and_shares_are_consistent(), test_delay_buckets_cover_every_reviewed_delivered_order(), test_delivery_trend_covers_the_same_population_as_the_ml_features(), test_monthly_growth_is_blank_next_to_thin_months(), test_monthly_kpis_add_up_to_net_revenue(), test_payment_shares_add_up_and_total_matches_the_fact() (+6 more)

### Community 5 - "fact_order_items (grain: order item, 112,650 rows)"
Cohesion: 0.08
Nodes (28): Net revenue R$ 13.49M over 98,199 orders, dim_customer (grain: customer_unique_id, 96,097 rows), dim_date (generated calendar 2016-2020, 1,828 rows), dim_geography (one row per zip prefix, 19,012 rows), dim_product (32,952 rows), dim_seller (3,096 rows), fact_order_items (grain: order item, 112,650 rows), fact_orders (grain: order) (+20 more)

### Community 6 - "duckdb"
Cohesion: 0.06
Nodes (34): Architecture, Components, Cost, Data flow, Deployment and monitoring, Failure points, ML (baselines built, D-007), Processing (+26 more)

### Community 7 - "fact_order_items"
Cohesion: 0.14
Nodes (9): dim_customer, dim_date, dim_geography, dim_product, dim_seller, fact_order_items, fact_orders, fact_payments (+1 more)

### Community 8 - "test_feature_leakage.py"
Cohesion: 0.13
Nodes (19): Do richer history features help? No., Limits, Phase 2: baseline results, Suggested next steps, Target A: late delivery, Target B: weekly forecast, Tests, day() (+11 more)

### Community 9 - "Phase 0 — Discovery Report"
Cohesion: 0.09
Nodes (23): 10. Current GCP services, pricing and free-tier implications, 11. IAM and security requirements (to implement in Phase 3, not yet), 12. Cost risks and mitigations, 13. Evidence plan, 14. Items covered (child prompt §43 checklist), 15. Decisions, 16. Known limitations of this discovery, 1. Dataset source and licence (+15 more)

### Community 10 - "Orders delivered late % (metric)"
Cohesion: 0.27
Nodes (8): Promise and Lateness Chart (late-delivery rate and under-20-day promises by month), Olist delivered orders by purchase month (months with at least 500 orders, 2017-01 to 2018-08), Orders Promised in Under 20 Days (%) metric, Delivery performance by customer state (chart), Median days to deliver (metric), Filter: customer states with at least 1,000 delivered orders, ordered by median delivery time, Olist Brazilian e-commerce orders data (source), Orders delivered late % (metric)

### Community 11 - "numpy"
Cohesion: 0.07
Nodes (27): backtest(), linear_trend(), f(), main(), moving_average(), naive(), score(), weekly_series() (+19 more)

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

### Community 26 - "EDA findings: Olist dataset discovery"
Cohesion: 0.40
Nodes (5): EDA findings: Olist dataset discovery, Issue log, Not yet covered, Patterns worth knowing (associational, not causal), The data

### Community 27 - "Lessons learned"
Cohesion: 0.40
Nodes (5): About modelling, About process, About the data, Lessons learned, What I would do differently

### Community 28 - "Recalibration and training window for the v1 late-delivery model"
Cohesion: 0.40
Nodes (5): Conclusions, Limits, R: recalibration on the latest resolved period, Recalibration and training window for the v1 late-delivery model, W: choosing the training window

### Community 29 - "Model card"
Cohesion: 0.50
Nodes (4): 1. Late-delivery model, 2. Weekly order forecast, 3. Reproducing, Model card

### Community 31 - "PROJECT STATUS"
Cohesion: 0.29
Nodes (7): Decisions, Headline results, Known limitations, Open items (from the audit), Phase status, PROJECT STATUS, Quality evidence

## Ambiguous Edges - Review These
- `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` → `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`  [AMBIGUOUS]
  docs/analytics/figures/promise_and_lateness.png · relation: conceptually_related_to

## Knowledge Gaps
- **33 isolated node(s):** `gcp`, `BigQuery Partitioning, Clustering and Query Cost Optimisation`, `Automated Data Quality Checks`, `Demand Forecasting (naive baseline, time-aware splits)`, `Join Multiplication Risk` (+28 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 274 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ensure_geolocation_parquet()` connect `duckdb` to `AUDIT.md`?**
  _High betweenness centrality (0.248) - this node is a cross-community bridge._
- **What connects `gcp`, `BigQuery Partitioning, Clustering and Query Cost Optimisation`, `Automated Data Quality Checks` to the rest of the system?**
  _33 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `AUDIT.md` be split into smaller, more focused modules?**
  _Cohesion score 0.05307709906199954 - nodes in this community are weakly interconnected._
- **Why does `DD-06: Convert geolocation CSV to Parquet in the build` connect `AUDIT.md` to `fact_order_items (grain: order item, 112,650 rows)`, `duckdb`?**
  _High betweenness centrality (0.240) - this node is a cross-community bridge._
- **Should `pandas` be split into smaller, more focused modules?**
  _Cohesion score 0.06810035842293907 - nodes in this community are weakly interconnected._
- **Why does `Architecture Philosophy (Shared Across Cloud Projects)` connect `Architecture Philosophy (Shared Across Cloud Projects)` to `AUDIT.md`?**
  _High betweenness centrality (0.117) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `Late-delivery spikes: ~14% in 2017-11 and ~21% in 2018-03, versus ~3-5% baseline` and `Rising share of short delivery promises: near 0% in early 2017 to 75% by 2018-08`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._