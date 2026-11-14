# SNOWFLAKE CHILD PROJECT PROMPT
# Retail Analytics, Forecasting & Customer Intelligence Platform

This is the Snowflake rewrite of the Google Cloud project brief (`Google Cloud Project — Retail Analytics, Forecasting & Customer Intelligence Platform.md`, which it replaces; the original is in the git history up to commit `a00b0a5`). The business scenario, analytical questions, ML discipline, evidence rules and approval gates are carried over; the platform sections are rewritten for Snowflake.

> **Where this repository stands against this brief (2026-11-13).** Phase 0 discovery, the local prototype, the dimensional model, analytics, forecasting and the late-delivery model were done locally on DuckDB. The Snowflake data platform is built and has run live: stage and `COPY INTO`, dbt staging, intermediate and marts, 321 dbt tests, and a 0-difference reconciliation against DuckDB. **The ML lifecycle in Snowflake (sections 20 to 24) is the main gap.** Since 2026-11-13 the results (scores, forecast backtests) are published to `ML` tables and the model is in the Snowflake Model Registry, where it scores correctly inside Snowflake. Models still train on the client, and there is no scheduled in-warehouse scoring or ML monitoring yet. See `Snowflake Retail Project Local vs Cloud Architecture.md` and `snowflake/README.md`.

You are operating under the previously defined:

"CLOUD PORTFOLIO — MASTER AGENT PROMPT"

That master prompt is the governing constitution for this project.

You MUST inherit and obey all principles, standards, agentic loops, evidence requirements, security requirements, cost controls, documentation requirements, testing requirements and definition-of-done criteria from the Master Agent Prompt.

This document adds Snowflake-specific requirements and project context.

======================================================================
PROJECT IDENTITY
======================================================================

Project name:

Snowflake — Retail Analytics, Forecasting & Customer Intelligence Platform

Cloud data platform:

Snowflake (on the cloud and region of the account in use; record both in Phase 0)

Primary sector:

Retail / E-commerce

Dataset:

Olist Brazilian E-Commerce Public Dataset

Primary technologies:

- Snowflake stages (internal; external on S3, GCS or Azure Blob only if justified)
- `COPY INTO`, and Snowpipe only if continuous loading is genuinely needed
- Snowflake virtual warehouses
- dbt (dbt-core with dbt-snowflake)
- Snowpark for Python
- Snowflake ML (`snowflake-ml-python`): modelling, Feature Store and Model Registry, where justified
- Snowflake Tasks (and Streams where incremental processing is justified)
- Resource monitors, `ACCOUNT_USAGE` views and Snowflake Alerts
- Role-based access control, service users with key-pair authentication
- Python
- SQL
- pandas
- scikit-learn
- XGBoost where appropriate
- Jupyter
- Git / GitHub
- Power BI, or another suitable BI layer, where practical

The project MUST NOT become a generic "Snowflake tutorial".

It must demonstrate the ability to design, build, operate, evaluate and explain a realistic analytical and machine-learning platform on Snowflake.

======================================================================
1. PROJECT PURPOSE
======================================================================

Build an end-to-end retail analytics and machine-learning platform using the Olist Brazilian E-Commerce Public Dataset.

The platform should demonstrate the progression:

LOCAL DATA SCIENCE
        ↓
STAGED SOURCE FILES
        ↓
DATA ENGINEERING (ELT)
        ↓
ANALYTICAL WAREHOUSING
        ↓
BUSINESS INTELLIGENCE
        ↓
MACHINE LEARNING
        ↓
MODEL REGISTRY
        ↓
MODEL INFERENCE
        ↓
MONITORING
        ↓
DOCUMENTATION / GOVERNANCE

The project must demonstrate genuine use of Snowflake rather than simply pulling tables into a laptop notebook.

The core Snowflake differentiator should be:

"Governed analytical warehousing + SQL-first ELT with dbt + machine learning next to the data."

Snowflake should be treated as the analytical centre of the project, and, for the final ML workflow, as the place where training data, models, predictions and their monitoring live together.

======================================================================
2. DATASET
======================================================================

Use:

Olist Brazilian E-Commerce Public Dataset

The dataset contains approximately 100,000 orders from a Brazilian e-commerce marketplace and includes multiple related tables covering:

- customers
- orders
- order items
- payments
- reviews
- products
- sellers
- product categories
- geolocation

The dataset is relational rather than a single flat CSV.

This project MUST exploit that relational structure.

Do not flatten everything immediately into one massive dataframe.

First understand:

- table relationships
- primary keys
- foreign keys
- cardinality
- grain
- duplicate relationships
- temporal fields
- missing values
- referential integrity
- business meaning
- potential leakage
- unusual records
- date ranges
- currency / monetary fields
- delivery timestamps
- review timestamps
- customer, seller and product identifiers

Verify the dataset's current source, licence, attribution requirements and permitted portfolio use during Phase 0.

Do not assume licensing information from memory.

======================================================================
3. BUSINESS SCENARIO
======================================================================

Assume the project represents a hypothetical e-commerce analytics function.

The business wants to understand:

1. How sales performance changes over time.
2. Which products and categories drive revenue.
3. Which sellers perform well or poorly.
4. How delivery performance affects customer satisfaction.
5. Which customers represent valuable segments.
6. What future demand may look like.
7. Which orders, customers or products may present elevated operational or commercial risk.
8. How customer behaviour can be converted into actionable analytical features.
9. How the resulting analytical and ML workloads can operate reliably on Snowflake.

This is an educational portfolio project.

Do not present Olist-derived models as production-ready recommendations for a real company.

Do not make unsupported causal claims.

"Late delivery causes poor reviews" must NOT be stated simply because the data shows an association.

Instead use language such as:

"Late delivery is associated with lower review scores in this dataset."

======================================================================
4. CORE ANALYTICAL QUESTIONS
======================================================================

The project should answer meaningful business questions.

At minimum investigate:

### Sales

- What is total revenue over time?
- What are the strongest product categories?
- Which sellers generate the most revenue?
- What is average order value?
- How does order volume change over time?
- What are the major revenue trends?

### Customer

- How many unique customers are present?
- How frequently do customers purchase?
- What does customer value look like?
- Can customers be segmented using behavioural characteristics?
- What distinguishes higher-value customers from lower-value customers?

### Delivery

- How long do orders take to fulfil?
- Which sellers or categories have poor delivery performance?
- How frequently are orders delivered late?
- Is delivery performance associated with review scores?

### Reviews

- What drives higher or lower review scores?
- How are review scores distributed?
- Is there an observable relationship between delivery performance and customer satisfaction?

### Forecasting

- How does order and revenue demand evolve over time?
- Can future order volume or revenue be forecast?
- How accurately can a baseline model forecast demand?

### Machine learning

- Can customers be segmented?
- Can customer or order behaviour be used to predict a meaningful business outcome?
- Can future customer behaviour be estimated from historical information?

The exact final ML problem MUST be selected after exploratory analysis.

Do not force an arbitrary ML problem merely to include machine learning.

======================================================================
5. SNOWFLAKE ARCHITECTURE
======================================================================

Preferred conceptual architecture:

LOCAL DEVELOPMENT
        ↓
LOCAL EDA / BASELINE
        ↓
STAGE (internal or external)
        ↓
COPY INTO → RAW
        ↓
dbt: STAGING → INTERMEDIATE → MARTS
        ↓
ANALYTICAL / DIMENSIONAL MODEL
        ↓
BI / SQL ANALYTICS
        ↓
FEATURE ENGINEERING (dbt models; Feature Store if justified)
        ↓
SNOWPARK / SNOWFLAKE ML TRAINING
        ↓
MODEL REGISTRY
        ↓
BATCH INFERENCE (scheduled Task)
        ↓
MONITORING (resource monitors, ACCOUNT_USAGE, ML monitoring)
        ↓
DOCUMENTATION / EVIDENCE

The final architecture MUST be justified.

Do not automatically use every Snowflake feature.

======================================================================
6. SNOWFLAKE SERVICES
======================================================================

Investigate current Snowflake features, editions, regional availability, credit consumption and trial-credit implications before provisioning. Features of Snowflake ML (Feature Store, Model Registry, model monitoring, the ML functions such as forecasting) and their edition requirements change; verify each one in Phase 0 rather than assuming it from memory.

### Stages and loading

Use stages for:

- raw source files, kept unchanged
- the files' load history (`COPY INTO` refuses to reload a loaded file unless forced)
- model artefacts only if the registry is not used

Load with `COPY INTO` using an explicit file format (header, quoting, encoding, byte-order mark, line endings), `ON_ERROR = ABORT_STATEMENT`, and record every load in an ingestion log (file, checksum, expected and loaded rows, status).

Use Snowpipe only if files arrive continuously. For a static snapshot, justify why batch `COPY INTO` is enough.

### Warehouse objects

Use logical layers as schemas in one database, for example:

RETAIL_OLIST.RAW
RETAIL_OLIST.STAGING
RETAIL_OLIST.INTERMEDIATE
RETAIL_OLIST.MARTS
RETAIL_OLIST.PBI
RETAIL_OLIST.ML

Exact names must be decided during architecture.

### Snowflake as the analytical centre

Use it for:

- structured analytical data
- SQL transformations (through dbt)
- dimensional modelling
- aggregation
- feature preparation
- business metrics
- reusable views and tables
- ML training data, predictions and monitoring tables

Demonstrate:

- appropriate data types (`NUMBER` scale, `TIMESTAMP_NTZ` vs `TIMESTAMP_TZ`)
- natural clustering by load order, and an explicit clustering key only where pruning is measurably poor
- materialisation choices (view, table, incremental) per model
- query-profile awareness (partitions scanned vs total, spilling)
- the result cache and warehouse cache, and their effect on measured timings
- schema design and analytical grain
- data-quality checks

Do NOT treat Snowflake as merely "a place to put CSV files".

### dbt

Use dbt for every transformation after RAW.

Demonstrate:

- sources with freshness and row-count expectations where meaningful
- staging, intermediate and mart layers
- generic tests (unique, not null, relationships, accepted values and ranges)
- singular tests for business rules
- documentation (descriptions, grain, lineage)
- separate targets (dev, ci, prod)
- a CI gate that parses or compiles without credentials

### Data processing choice

For small datasets, compare:

- local transformation (DuckDB or pandas)
- SQL in Snowflake through dbt
- Snowpark Python inside Snowflake

and justify the selected approach. Do not use Snowpark for work that set-based SQL does better.

### Snowpark and Snowflake ML

Use them for the machine-learning lifecycle where they add value:

- training next to the data (stored procedure or Snowpark-optimised warehouse, if justified)
- model artefacts and versions in the Model Registry
- evaluation results stored as tables
- batch inference with the registered model
- a Feature Store only if more than one model or consumer reuses the features

Snowflake ML must represent a genuine ML lifecycle rather than a notebook that happens to read Snowflake.

### Model Registry

Register the champion model.

Record:

- model name
- version
- training data (table and query or snapshot)
- feature version
- training timestamp
- model type
- evaluation metrics
- hyperparameters
- dependencies (Python and package versions)
- Git commit
- limitations
- approval status

### Monitoring

Use Snowflake's own telemetry for operational visibility:

- load history and the ingestion log
- dbt run and test results
- Task history
- query history and warehouse metering (`ACCOUNT_USAGE`)
- resource monitors (credit quota, notify and suspend triggers)
- Alerts for failed loads, failed Tasks or failed quality checks

ML and data drift may be demonstrated with SQL over the feature and prediction tables, or with Snowflake's model monitoring if available on the account.

If simulated data is used to demonstrate drift, label it explicitly as simulated.

### Access control

Implement least privilege with role-based access control.

Consider:

- functional roles (loader, transformer, reporter) and the privileges each needs
- service users (`TYPE = SERVICE`) with key-pair authentication for pipelines
- human users with MFA
- future grants on schemas
- who may create objects, and in which schemas

Do not run pipelines as `ACCOUNTADMIN` or `SYSADMIN`.

Document why each role exists.

### Secrets

Never hard-code:

- private keys or passphrases
- passwords
- tokens
- account identifiers in published documents where avoidable

into source code or Git history.

Keep private keys outside the repository. Use environment variables or a secrets manager on the client side, and Snowflake secret objects only for integrations that need them.

======================================================================
7. LOCAL-FIRST DEVELOPMENT
======================================================================

Local development should remain an important component.

Do not move every experiment into Snowflake.

Use local resources for:

- initial EDA
- data understanding
- feature experimentation
- baseline models
- model comparison
- rapid iteration
- debugging
- visualisation

Keep a local reference implementation (DuckDB) that the Snowflake build is reconciled against.

Do not allow notebooks to become the production implementation.

Reusable logic belongs in `src/`, SQL in `sql/` (local) and the dbt project (Snowflake), configuration in `config/` or environment variables, and Snowflake setup scripts in a setup folder.

======================================================================
8. DATA ENGINEERING LAYERS
======================================================================

Implement a clear data lifecycle:

RAW
↓
STAGING
↓
INTERMEDIATE / CURATED
↓
MARTS (analytical)
↓
FEATURES
↓
PREDICTIONS (ML schema)

Each layer must have a documented purpose.

### RAW

Original source data.

- preserve source fidelity (text columns are acceptable; typing happens in staging)
- avoid destructive transformations
- document the source
- record load metadata (load timestamp, source file, batch id)

### STAGING

Standardisation layer:

- column naming
- data type conversion
- date parsing
- null handling
- duplicate detection
- schema validation

### INTERMEDIATE / CURATED

Clean relational data:

- validated relationships
- consistent schemas
- business-friendly naming
- quality checks
- pre-aggregation that prevents fan-out

### MARTS

Analytical layer: fact and dimension tables, for example:

FactOrders
FactOrderItems
FactPayments
FactReviews

DimCustomer
DimProduct
DimSeller
DimDate
DimGeography

The exact schema must be determined after inspecting the dataset.

Do not create dimensions merely to satisfy a textbook definition.

======================================================================
9. DATA MODELLING
======================================================================

Data grain MUST be documented explicitly.

For every major table state:

- table name
- grain
- primary key
- foreign keys
- measures
- dimensions
- source tables
- transformation logic

Snowflake does not enforce primary and foreign keys. Declare them where useful for tools, and enforce them with dbt tests.

Avoid accidental many-to-many joins.

Demonstrate that joining order-level, item-level, payment-level and review-level tables can multiply records if performed incorrectly.

======================================================================
10. SNOWFLAKE ENGINEERING
======================================================================

Snowflake should demonstrate real analytical engineering.

### Micro-partitions and clustering

Snowflake partitions automatically. Show partition pruning in the query profile for the main date filters (order purchase date, delivery date, review date).

Add a clustering key only if a measured query scans far more partitions than it needs, and record the before and after. At this data size a clustering key will probably not pay for its maintenance; say so if that is the finding.

### Warehouse sizing

Start with XSMALL and a short auto-suspend. Measure run time and credits before choosing a larger size. Explain the trade-off between size and elapsed time.

### Query optimisation

Demonstrate awareness of:

- `SELECT *` on wide tables
- unnecessary scans
- repeated transformations (views vs tables)
- partition pruning
- caching effects on benchmarks
- aggregation strategy
- materialised tables or dynamic tables where justified

Record credits used, not just elapsed time.

### Reusable SQL

Use dbt models, macros and tests rather than one giant query.

### Dialect migration

Where SQL is ported from the local engine, list every construct that changed (for example `arg_max` to `max_by`, `ASOF JOIN` syntax, date functions, `FILTER (WHERE)`), and verify results against the local reference.

======================================================================
11. DATA QUALITY
======================================================================

Build automated data-quality checks (dbt tests and a reconciliation against the local build).

At minimum test:

- row counts (source records vs loaded rows)
- null rates
- duplicate primary keys
- referential integrity
- date validity
- numerical ranges
- impossible values
- orphan records
- unexpected categories
- join multiplication
- schema consistency
- line-ending and encoding artefacts from the load

Document the results.

If quality issues are found in the original dataset, do not silently remove them.

Record the issue, frequency, treatment, rationale and impact.

======================================================================
12. CUSTOMER ANALYTICS
======================================================================

Develop meaningful customer-level features:

- order count
- total spend
- average order value
- recency
- purchase frequency
- category diversity
- average review score
- delivery experience
- geographic characteristics

Consider an RFM-style framework, but do not copy a textbook implementation blindly.

Explain feature definitions, observation period, cutoff date, leakage risks and customer grain.

Use neutral descriptive language rather than unsupported claims about customer behaviour.

======================================================================
13. CUSTOMER SEGMENTATION
======================================================================

Evaluate whether unsupervised learning provides value (K-Means, hierarchical clustering, Gaussian mixtures if justified).

Evaluate silhouette score, cluster size, stability and business interpretability.

Do not select a cluster count purely because an algorithm produces one.

If segmentation adds little value, document that finding and do not force it into the final architecture. (In this repository, segmentation was dropped because about 97% of customers buy once, DD-07.)

======================================================================
14. FORECASTING
======================================================================

Build at least one meaningful forecasting experiment (daily or weekly orders or revenue).

Start with simple baselines (naive, seasonal naive, moving average), then compare with an appropriate model (linear regression with time features, tree-based regression, exponential smoothing, ARIMA-style methods if justified). Snowflake's built-in forecasting function may be compared against them if available on the account; treat it as one more candidate, not as the default.

Do not use deep learning merely because it is available.

Evaluate with MAE, RMSE, and MAPE or sMAPE where appropriate, using time-aware splits.

Never shuffle temporal observations for forecasting evaluation.

Document horizon, training, validation and test periods, seasonality assumptions and limitations.

======================================================================
15. SUPERVISED MACHINE LEARNING
======================================================================

Select a supervised ML problem only after EDA.

The target must have a clear definition, prediction unit, prediction horizon, enough observations and a business interpretation.

Do not use future information to predict past outcomes.

Explicitly investigate target leakage, temporal leakage, post-outcome variables, duplicated information, identifiers, high-cardinality features and target-derived features.

Where history features need "the latest value before this event", use a point-in-time join (Snowflake `ASOF JOIN`) and test that it never looks ahead.

Create:

docs/ml/LEAKAGE_ANALYSIS.md

======================================================================
16. MODEL COMPARISON
======================================================================

Compare appropriate baselines, for example Logistic Regression, Random Forest and XGBoost for classification; Linear Regression, Random Forest and XGBoost regressors for regression.

Do not compare models merely for quantity.

Explain the baseline, assumptions, strengths, weaknesses, compute requirements, interpretability, performance and operational suitability.

======================================================================
17. MODEL EVALUATION
======================================================================

Accuracy alone MUST NOT be treated as sufficient.

For classification: precision, recall, F1, ROC-AUC, PR-AUC, confusion matrix, calibration and threshold analysis.

For regression: MAE, RMSE, R² and residual behaviour.

For forecasting: appropriate temporal metrics.

The final model should not automatically be the one with the highest single metric. Weigh performance, interpretability, calibration, compute cost, operational complexity and business value.

Store evaluation results as tables in the `ML` schema as well as in the repository, so they can be queried and monitored.

======================================================================
18. THRESHOLD ANALYSIS
======================================================================

If classification is used, do not assume a 0.5 threshold.

Show how the threshold or the share of orders flagged changes precision, recall, intervention volume, false positives and false negatives.

If a business cost matrix is used, label it hypothetical, explain the assumptions, and do not present it as real Olist economics.

======================================================================
19. EXPLAINABILITY
======================================================================

Use feature importance, permutation importance or SHAP as appropriate.

"Predictive importance is not the same as causality."

Distinguish global importance, local explanations, model behaviour and business interpretation.

Do not overclaim.

======================================================================
20. SNOWFLAKE ML
======================================================================

The final model must have a reproducible implementation inside Snowflake.

The workflow should demonstrate:

1. Training data preparation (a dbt model or a Feature Store view).
2. Training configuration.
3. Model training (Snowpark stored procedure or Snowflake ML modelling API).
4. Evaluation, written to `ML` tables.
5. Model registration with metrics and lineage.
6. Candidate vs champion comparison.
7. Approval decision.
8. Batch inference.
9. Monitoring.

Do not simply read Snowflake tables into a local notebook and call this MLOps. Client-side training on Snowflake data is a valid intermediate step; it is not the end state.

Reusable code should exist outside notebooks, for example:

src/ml/
    features.py
    train.py
    evaluate.py
    predict.py
    register.py

======================================================================
21. CLOUD TRAINING VS LOCAL TRAINING
======================================================================

Distinguish LOCAL EXPERIMENTATION from IN-SNOWFLAKE REPRODUCTION.

Use local compute for rapid experimentation.

Once the champion approach is selected, reproduce the final training in Snowflake where technically and economically justified, and show that it gives the same metrics as the local run (or explain each difference, for example floating-point summation order).

Document the local environment, Snowflake environment (warehouse type and size, Python and package versions), dataset version, feature version, random seed, model configuration and evaluation metrics.

The goal is reproducibility.

======================================================================
22. MODEL REGISTRY
======================================================================

Register the champion model in the Snowflake Model Registry.

The entry should identify model name and version, training data, feature set, training code version and Git commit, model type, metrics, dependency environment, limitations and approval status.

Use a lifecycle such as:

EXPERIMENT
    ↓
CANDIDATE
    ↓
VALIDATED
    ↓
APPROVED
    ↓
DEPLOYED (used by the scheduled scoring Task)

Do not promote models automatically without evaluation.

======================================================================
23. BATCH VS ONLINE INFERENCE
======================================================================

### Batch inference

- scores written to a table by a scheduled Task using the registered model
- lower operational complexity and cost
- no always-on service
- consumers (BI, dashboard) read a table

### Online inference

- low latency for interactive applications
- on Snowflake this means a service (for example Snowpark Container Services) or an external endpoint
- always-on cost, operational complexity, monitoring and security work

For this portfolio project, batch inference should be preferred unless the business problem genuinely requires real-time predictions.

If an online service is created: keep it temporary, test it, capture evidence, document the cost, and drop it when no longer required (with approval).

======================================================================
24. MONITORING
======================================================================

Operational monitoring:

- load failures (ingestion log, `COPY_HISTORY`)
- dbt run and test failures
- Task failures (`TASK_HISTORY`)
- credit use (resource monitor, `WAREHOUSE_METERING_HISTORY`)
- long or spilling queries (`QUERY_HISTORY`)

ML monitoring, where practical:

- prediction distribution per scoring run
- feature distribution vs the training window
- data drift
- performance degradation once labels arrive
- input schema changes

If no genuine production stream exists, create a controlled demonstration, for example by replaying later months of the dataset as "new" data.

Any simulated data MUST be labelled as simulated.

======================================================================
25. SECURITY
======================================================================

Apply least privilege.

Document:

- the role hierarchy and each role's privileges
- service users and their authentication
- human users and MFA
- network policies where applicable
- secrets handling
- encryption (Snowflake encrypts at rest by default; say what you rely on)
- data sharing, if any

Do not commit private keys, passphrases, passwords, tokens or `.env` files.

Add appropriate patterns to `.gitignore` and verify that no secrets exist in Git history.

======================================================================
26. COST OPTIMISATION
======================================================================

Cost is a first-class engineering constraint.

The Olist dataset is not large enough to justify large infrastructure.

Before provisioning, research the current credit price for the account's edition and region, and trial-credit terms.

Pay attention to:

- warehouse size and running time (credits)
- auto-suspend and auto-resume
- serverless features (Snowpipe, Tasks, clustering, search optimisation) and their own credit use
- storage, including Time Travel and Fail-safe
- cloud services usage
- data transfer if external stages or sharing are used

Avoid always-on warehouses, oversized warehouses, unnecessary duplicate tables and permanent services.

Create a resource monitor with notify and suspend triggers before the first heavy workload.

Demonstrate practical cost optimisation, for example:

"XSMALL vs SMALL warehouse for the dbt build: elapsed time vs credits"

or

"client-side training vs in-Snowflake training"

or

"view vs table materialisation for a frequently read mart"

Document what was tested, the resources used, the measured credits, the performance difference and the conclusion.

======================================================================
27. DATA PRIVACY & RESPONSIBLE ANALYTICS
======================================================================

Although this is a public dataset, treat data responsibly.

Document provenance, licence, limitations, privacy considerations, quasi-identifying fields, geographic information and customer identifiers.

Consider masking policies or secure views if identifiers are exposed to the reporting role.

Do not imply that the dataset represents all Brazilian e-commerce customers.

For segmentation and ML, consider proxy variables, geographic bias, historical bias, representativeness, transparency and human oversight.

======================================================================
28. POWER BI / BUSINESS INTELLIGENCE
======================================================================

Expose the Snowflake marts to Power BI (or another BI layer) through a reporting role that can read only the reporting schema.

The BI layer should focus on business consumption rather than reproducing SQL.

Potential report sections:

- Executive overview (revenue, orders, customers, AOV, growth, delivery performance)
- Product performance
- Seller performance
- Customer intelligence (segments, repeat behaviour, value)
- Forecasting (history, forecast, intervals where available)
- ML (model performance, prediction distribution, feature importance, risk distribution)

The BI model should read the analytical model and the `ML` prediction tables, not raw files.

======================================================================
29. TESTING
======================================================================

Implement testing throughout.

- **Data tests:** schema, nulls, uniqueness, referential integrity, ranges (dbt).
- **Transformation tests:** row counts, aggregation correctness, join correctness, grain (dbt and reconciliation).
- **ML tests:** feature schema, target schema, reproducibility, prediction shape, valid prediction ranges, no leakage.
- **Pipeline tests:** successful execution, failure handling, idempotent reloads, expected outputs.
- **Infrastructure tests:** objects exist, roles have the intended privileges and no more, setup scripts are idempotent and contain no destructive statements.

Tests must be automated where practical, and CI must pass without Snowflake credentials.

======================================================================
30. EVIDENCE REQUIREMENTS
======================================================================

Evidence must come from the real Snowflake account.

Do NOT fabricate screenshots or results.

Suggested evidence checkpoints:

E01 — Account, edition, region, resource monitor
E02 — Roles, service user, grants
E03 — Stage and file format
E04 — Raw files loaded (ingestion log, counts)
E05 — dbt project structure and lineage
E06 — dbt build and test results
E07 — Schemas and analytical tables
E08 — Query profile: pruning, warehouse sizing
E09 — Data-quality and reconciliation results
E10 — Analytical queries
E11 — Local model baseline
E12 — In-Snowflake training run
E13 — Model evaluation tables
E14 — Model Registry entry
E15 — Batch inference Task and prediction table
E16 — Online service if used
E17 — Monitoring and alerts
E18 — Cost analysis (measured credits)
E19 — Resource cleanup or suspension

Each evidence item should demonstrate a meaningful capability.

Store evidence references in `docs/evidence/` and track them in `PROJECT_STATUS.md`.

======================================================================
31. FAILURE DOCUMENTATION
======================================================================

Failures are evidence of engineering experience.

If something breaks, document what was attempted, the expected and actual behaviour, the error, the diagnosis, the fixes tried, the final solution and the lesson.

Potential examples:

- file format mismatch (quoting, line endings, byte-order mark)
- join multiplication
- dialect differences between the local engine and Snowflake
- non-deterministic tie-breaks giving different results across engines
- privilege errors from the role hierarchy
- TLS interception breaking client certificate checks
- Python dependency issues in Snowpark
- cost higher than expected

Do not hide meaningful failures.

======================================================================
32. REPOSITORY STRUCTURE
======================================================================

Use a professional repository structure similar to:

README.md
ARCHITECTURE.md
DECISIONS.md
PROJECT_STATUS.md
COST.md
SECURITY.md
RESPONSIBLE_AI.md
MODEL_CARD.md
LICENSE
.gitignore
.env.example

notebooks/
src/
    ingestion/
    data_access/
    analytics/
    ml/
    monitoring/
sql/                (local reference)
snowflake/
    setup/          (idempotent objects, grants, monitor, users)
    ingestion/
    dbt/            (models, tests, macros)
tests/
docs/
    architecture/
    data/
    ml/
    migration/
    evidence/
    failures/
scripts/

The exact structure may evolve.

Do not create empty directories simply to make the repository look impressive.

======================================================================
33. DOCUMENTATION
======================================================================

README.md should tell the complete story:

1. Business problem
2. Dataset
3. Architecture
4. Why Snowflake
5. Data engineering (ELT with dbt)
6. Analytical model
7. Analytics
8. Forecasting
9. Machine learning
10. Snowflake ML
11. Model registry
12. Inference
13. Monitoring
14. Security
15. Cost optimisation
16. Results
17. Limitations
18. Evidence
19. Reproduction instructions

ARCHITECTURE.md should explain components, data flow, responsibilities, security boundaries, failure points, scalability and cost.

DECISIONS.md should document important decisions with: decision, context, options, chosen option, reason, trade-offs, cost implications, security implications and alternatives rejected.

======================================================================
34. PROJECT STATUS
======================================================================

Maintain PROJECT_STATUS.md.

It MUST track: current phase, completed, in progress, blocked, next, tests, evidence, Snowflake objects, measured and estimated credits, security status, open decisions and known limitations.

Update it after meaningful milestones.

======================================================================
35. AGENTIC EXECUTION LOOP
======================================================================

For every significant task use:

PLAN → INSPECT → IMPLEMENT → TEST → VERIFY → EVIDENCE → DOCUMENT → REVIEW → STATUS → DECIDE

Never skip VERIFY.

Never claim success merely because a command returned successfully.

Do not say:

"COPY INTO completed."

Instead verify:

- every file loaded once
- loaded rows equal source records
- no truncated or carriage-return-polluted values
- dbt tests pass on the result
- the reconciliation against the local reference passes

======================================================================
36. HUMAN APPROVAL GATES
======================================================================

Pause and request approval before:

- major architecture changes
- creating warehouses larger than XSMALL, or multi-cluster warehouses
- account-level changes (resource monitors, network policies, account parameters)
- creating users or changing role grants
- always-on services or online endpoints
- dropping, replacing or truncating existing databases, schemas or tables
- changing the core ML objective
- changing the dataset
- introducing unnecessary services
- accepting significant technical debt

Do not pause for trivial implementation details.

======================================================================
37. SNOWFLAKE-SPECIFIC LEARNING OBJECTIVES
======================================================================

By completion, the repository should demonstrate understanding of:

### Snowflake fundamentals

- accounts, editions, regions
- databases, schemas, stages
- virtual warehouses and credits
- the role hierarchy and system roles

### Loading

- stages and file formats
- `COPY INTO`, load history and idempotency
- Snowpipe and when it is not needed

### Transformation

- dbt on Snowflake: models, materialisations, tests, targets
- views vs tables vs dynamic tables

### Warehousing

- micro-partitions and pruning
- clustering keys and their cost
- caching
- query profile
- dimensional modelling

### Snowflake ML

- Snowpark Python
- training next to the data
- Model Registry
- batch inference
- ML monitoring

### Operations

- Tasks and scheduling
- resource monitors and Alerts
- `ACCOUNT_USAGE` telemetry

### MLOps

- reproducibility
- versioning
- model lifecycle
- monitoring

======================================================================
38. CROSS-CLOUD DIFFERENTIATION
======================================================================

This project MUST NOT simply replicate the Azure or AWS project.

Azure:

Healthcare + Data Factory / Databricks + Azure ML + healthcare predictive analytics

AWS:

Financial services + S3 / Glue / Athena + SageMaker + credit-risk classification

Snowflake:

Retail / E-commerce + stages / dbt / Snowflake + Snowflake ML + customer intelligence, forecasting and analytical warehousing

The Snowflake project should therefore put particularly strong emphasis on:

SQL-FIRST ELT (dbt)
+
DIMENSIONAL MODELLING
+
DATA QUALITY AND RECONCILIATION
+
GOVERNANCE (roles, cost controls)
+
FORECASTING
+
ML NEXT TO THE DATA

Do not weaken this differentiation by making all three architectures identical.

======================================================================
39. COST-CONSCIOUS ARCHITECTURE
======================================================================

Optimise for:

MAXIMUM DEMONSTRATED COMPETENCY
per
UNIT OF PLATFORM COMPLEXITY
per
CREDIT

Before creating an object or feature, ask:

1. What competency does this demonstrate?
2. Is this the simplest feature that demonstrates it?
3. How many credits does it use, and is it serverless or warehouse-billed?
4. Can it be suspended or dropped afterwards?
5. Can the workload run locally?
6. Can a scheduled batch replace an always-on service?
7. Is the complexity justified?
8. Does it materially improve the portfolio?

If the answers are weak, do not create it.

======================================================================
40. FINAL PROJECT AUDIT
======================================================================

Before declaring the project complete, verify:

DATA
- provenance and licence documented
- schemas understood, relationships validated
- data quality tested
- leakage investigated

SNOWFLAKE
- roles and grants reviewed
- stages and loads reviewed
- dbt project reviewed
- warehouse sizing and monitors reviewed
- Snowflake ML objects reviewed
- unnecessary objects removed or suspended

DATA ENGINEERING
- RAW, staging, intermediate and mart layers implemented
- transformations reproducible
- analytical model documented
- optimisation demonstrated with measurements

ANALYTICS
- business questions answered
- metrics validated against the local reference
- BI output usable

ML
- target justified
- leakage investigated
- baseline established
- models compared
- metrics appropriate
- explainability included
- limitations documented

MLOPS
- in-Snowflake training reproducible
- model registered
- batch inference demonstrated
- monitoring implemented

SECURITY
- least privilege
- no secrets committed
- credentials protected

COST
- major credit drivers identified
- measured credits recorded
- optimisation demonstrated

DOCUMENTATION
- README, architecture, decisions, model card, responsible AI, evidence, failures and PROJECT_STATUS.md complete and current

REPRODUCIBILITY
- setup instructions tested
- dependencies documented
- commands work
- repository is clean

======================================================================
41. DEFINITION OF DONE
======================================================================

The project is NOT complete when "the model works".

It is complete only when:

IMPLEMENTATION + TESTING + VERIFICATION + SNOWFLAKE DEPLOYMENT + DATA ENGINEERING + ANALYTICS + MACHINE LEARNING + MLOPS + SECURITY + COST OPTIMISATION + EVIDENCE + DOCUMENTATION + REPRODUCIBILITY

are all sufficiently demonstrated.

The final repository should allow a technical interviewer to answer:

"Can this person actually build something on Snowflake?"

with:

"Yes."

======================================================================
42. INTERVIEW STANDARD
======================================================================

Every major decision should be explainable in an interview. The user should be able to answer:

- Why Snowflake?
- Why stages and `COPY INTO` rather than Snowpipe?
- Why dbt?
- Why this schema and these layers?
- Why views here and tables there?
- Why (or why not) a clustering key?
- Why this warehouse size?
- Why not process everything locally?
- Why train in Snowflake rather than on a laptop?
- Why this model, and not another?
- How did you prevent leakage?
- Why this evaluation metric?
- Why batch instead of real time?
- How does the local build reconcile with Snowflake?
- How would this scale?
- What would break first?
- How is it secured?
- How many credits does it use?
- What would you change for production?
- What are the limitations of the dataset?

If an answer cannot be explained clearly, the implementation should be reconsidered or documented better.

======================================================================
43. STARTING INSTRUCTION
======================================================================

DO NOT immediately create every Snowflake object.

Begin with PHASE 0 — DISCOVERY. Establish:

1. Dataset source.
2. Dataset licence.
3. Dataset structure.
4. Table relationships.
5. Data types.
6. Date ranges.
7. Missing values.
8. Duplicate records.
9. Referential integrity.
10. Potential analytical grains.
11. Candidate business questions.
12. Candidate forecasting target.
13. Candidate ML target.
14. Leakage risks.
15. Customer-level feature opportunities.
16. The Snowflake account's edition, cloud and region.
17. Current credit pricing for that edition and region.
18. Trial-credit implications.
19. Which Snowflake ML features are available on the account.
20. Required roles, users and grants.
21. Minimal viable architecture.
22. Architectural alternatives.
23. Cost risks.
24. Evidence requirements.

Produce a Phase 0 discovery report before creating substantial objects.

Do not blindly follow the proposed architecture if discovery shows that a simpler or better one is appropriate.

The objective is not:

"Use as many Snowflake features as possible."

The objective is:

"Demonstrate that the user can design and operate a credible, cost-conscious analytical and machine-learning platform on Snowflake."

======================================================================
END OF SNOWFLAKE CHILD PROJECT PROMPT
======================================================================
