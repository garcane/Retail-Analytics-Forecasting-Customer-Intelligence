# GCP Retail Project: Local vs. Cloud Architecture

## Overview
This document outlines the architecture and engineering design for the **GCP Retail Project**, comparing the local equivalent stack with the managed Google Cloud Platform components.

---

## 1. Cloud vs. Local Architecture Mapping

| Component / Function | GCP Managed Service | Local Equivalent |
| :--- | :--- | :--- |
| **Object Storage** | Cloud Storage (GCS) | Local filesystem |
| **Data Processing / Pipeline** | Dataflow | Apache Beam Direct Runner |
| **Data Warehouse** | BigQuery | DuckDB |
| **Dimensional Data Model** | BigQuery Dimensional Model | DuckDB / PostgreSQL |
| **ML Platform & Tracking** | Vertex AI | MLflow + scikit-learn / XGBoost |
| **Model Registry** | Vertex AI Model Registry | MLflow Model Registry |
| **Model Endpoint / Serving** | Vertex AI Endpoint | FastAPI |
| **Monitoring** | Cloud Monitoring | Prometheus + Grafana |

---

## 2. End-to-End Pipeline Workflow

### Local Development Pipeline
```text
Olist CSV ──> Parquet ──> DuckDB (Dimensional Modeling) ──> Analytical SQL ──> ML Features
                             │
                             ├── DimCustomer, DimProduct, DimSeller, DimDate
                             └── FactOrders, FactOrderItems, FactPayments, FactReviews
```

### Cloud Deployment Pipeline
```text
Olist Data ──> Cloud Storage ──> Dataflow ──> BigQuery (Dimensional Model) ──> Vertex AI
```

---

## 3. Key GCP Technologies & Portability

### Apache Beam / Dataflow Portability
Google officially provides Apache Beam's **Direct Runner** specifically for local development and testing. The exact same Beam pipeline code can subsequently be deployed using the **Dataflow Runner** in Google Cloud without rewriting pipeline logic:

```python
# Local execution
pipeline = beam.Pipeline(runner='DirectRunner')

# GCP Cloud execution
pipeline = beam.Pipeline(runner='DataflowRunner')
```

### Analytics Engine (DuckDB vs BigQuery)
DuckDB serves as the ideal local substitute for BigQuery to demonstrate key analytical engineering skills:
- Analytical SQL and window functions
- Dimensional modeling (Star Schema)
- Columnar data storage and aggregations
- Feature engineering and query optimization
