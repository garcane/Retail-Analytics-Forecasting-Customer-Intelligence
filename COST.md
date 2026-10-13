# Cost

**Total cloud cost: $0. No cloud resources exist or are planned (D-002).**

| Item | Cost |
|---|---|
| Warehouse and query engine (DuckDB, one local file) | $0 |
| ML (scikit-learn, numpy, scipy on a laptop) | $0 |
| Analytics and charts (SQL, matplotlib) | $0 |
| Dataset (Kaggle, free account) | $0 |
| Tooling (`uv`, `pytest`, open source) | $0 |

## Compute

Measured on the development laptop (2026-10-13):

| Step | Time |
|---|---|
| Build the warehouse (22 checks included) | about 25 seconds |
| Late-delivery backtest | about 40 seconds |
| Forecast backtests | 3 seconds (baselines), about 12 seconds (extra models) |
| Analytics queries and charts | about 12 seconds |
| Explainability (permutation importance) | about 43 seconds |
| Full test suite (61 tests) | 20 to 40 seconds |
| Drift analysis and recalibration | a few minutes each |

Disk: about 79 MB of raw data (Kaggle CSVs, one Parquet) and a 112 MB warehouse file, both git-ignored.

## If the project moved to the cloud

Pricing for BigQuery, Dataflow and Vertex AI was **never verified** (Phase 0 §10) and is not estimated here. At this data size (about 100,000 orders, 80 MB) the cost would be expected to be very small, within free tiers, but that is an expectation and not a checked figure. See the "Moving to BigQuery" section of [docs/data/DATA_MODEL.md](docs/data/DATA_MODEL.md) for the technical work involved.
