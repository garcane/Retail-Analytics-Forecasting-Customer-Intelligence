# Snowflake + dbt implementation: setup and runbook

A second, cloud implementation of the Olist star schema: **RAW -> dbt staging -> intermediate -> marts -> Python forecasting, the HTML dashboard and Power BI** on Snowflake. The DuckDB implementation (`sql/`, `src/`, `warehouse.duckdb`) is unchanged and remains the reference; this folder sits next to it and does not replace it.

> **Status (2026-11-13): the pipeline has run end to end on a live Snowflake account.** Setup, RAW load, `dbt build` (367 of 367 passed), the DuckDB-vs-Snowflake reconciliation (22 of 22 checks, 0 differences), both Tier 1 Python models and the dashboard data build have all run against `RETAIL_OLIST`. The ML outputs (scores, forecast backtest) are published to the `ML` schema. Not run yet: the Power BI patched copy. Each section below gives its own status, the date it ran and the measured result.

Related pages: [architecture](../docs/architecture/SNOWFLAKE_ARCHITECTURE.md) | [SQL migration inventory](../docs/migration/SNOWFLAKE_MIGRATION.md) | [data dictionary](../docs/data_dictionary/DATA_DICTIONARY.md) | [ingestion runbook](../docs/migration/INGESTION_RUNBOOK.md) | [Power BI switch guide](../docs/migration/POWERBI_SWITCH_GUIDE.md) | [dbt project README](dbt/README.md) | [reconciliation report](../docs/validation/RECONCILIATION_REPORT.md) | [dashboard](../dashboard/README.md)

## What is in this folder

| Path | Purpose | Changes Snowflake? |
|---|---|---|
| `setup/00_preflight.sql` | Read-only `SHOW`/`SELECT`: existing `RETAIL%` objects, your role | No |
| `setup/01_objects.sql` | Database `RETAIL_OLIST`, schemas `RAW, STAGING, INTERMEDIATE, MARTS, PBI, ML`, warehouse `RETAIL_WH` (XSMALL, auto-suspend 60 s), roles | Yes, additive (`IF NOT EXISTS`) |
| `setup/02_grants.sql` | Least-privilege grants for `RETAIL_LOADER`, `RETAIL_TRANSFORMER`, `RETAIL_REPORTER` | Yes, additive |
| `setup/03_resource_monitor.sql` | `RETAIL_MONITOR`: 5 credits a month on `RETAIL_WH`; notify at 75%, suspend at 100%, suspend immediately at 110% | Yes (needs `ACCOUNTADMIN`) |
| `setup/04_service_user.sql`, `setup/generate_key_pair.py` | Service user `RETAIL_SVC` (key-pair only, no password) with the loader and transformer roles; the script writes the key pair to `~/.snowflake/keys`, never inside the repo | Yes (needs `SECURITYADMIN`) |
| `setup/06_model_registry_grants.sql` | `CREATE MODEL` and `CREATE STAGE` on `RETAIL_OLIST.ML` for `RETAIL_TRANSFORMER` (the Model Registry) | Grant only (needs `SYSADMIN`) |
| `ml/` | Isolated Python 3.13 environment and `register_model.py` for the Snowflake Model Registry (section 9) | Creates model versions in `ML` |
| `setup/05_monitor_grant.sql`, `monitoring/credit_usage.py` | Read-only `MONITOR` on `RETAIL_MONITOR` for `RETAIL_TRANSFORMER`; a script that reports the month's credit use | Grant only (needs `ACCOUNTADMIN`) |
| `ingestion/file_formats.sql`, `ingestion/ddl_raw.sql` | CSV file format and stage; nine RAW tables and `RAW.INGESTION_LOG` | Yes, additive |
| `ingestion/load_raw.py` | `PUT` + `COPY INTO` loader with checksum log and record-count checks | Writes data into `RAW` only |
| `dbt/` | The dbt project (46 models, 321 tests) in its own Python 3.13 environment | Creates views and tables in `STAGING` to `PBI` |
| `dbt/make_ca_bundle.py` | Builds a CA bundle from the Windows root store, for dbt behind a TLS-inspecting proxy (section 7) | No |

Related code outside this folder: `src/data_access/` (Python backend switch), `src/reconciliation/` (DuckDB vs Snowflake comparison), `src/dashboard/build_data.py` (dashboard data, Snowflake by default), `powerbi/snowflake/` (patched Power BI copy). None of the SQL uses `OR REPLACE` or `DROP`. The only account-level object is the resource monitor, created with the owner's approval.

## 1. Prerequisites

- **A Snowflake account.** Setup needs `ACCOUNTADMIN` once (resource monitor), `SECURITYADMIN` (roles, the service user) and `SYSADMIN` (database, warehouse). Day-to-day work then runs as `RETAIL_SVC` with key-pair authentication; no password is stored anywhere.
- **Python environments.** There are two, kept apart on purpose:
  - The repo environment (`.venv`, Python 3.14.2 on the author's machine) runs the loader, `src/data_access`, `src/reconciliation`, the ML scripts, the dashboard build and the Power BI patch script. `snowflake-connector-python` 5.2.0 connected live from it on 2026-11-12. **Do not run `uv sync`, `uv lock` or `uv run` at the repo root**: `.python-version` is 3.14 and `uv` would rebuild `.venv`.
  - The dbt environment `snowflake/dbt/.venv` (Python 3.13, `dbt-core` 1.11.17, `dbt-snowflake` 1.11.6) is created from `snowflake/dbt/pyproject.toml` and `uv.lock`; the commands are in [`dbt/README.md`](dbt/README.md).
- **The data.** The nine Olist CSVs are git-ignored and not in this repository. Point `RETAIL_DATA_DIR` at the folder that holds them. Without it the loader falls back to `./data` and then stops with an error naming the folder.
- **The reference warehouse** (for reconciliation and the DuckDB side of any comparison): `warehouse.duckdb`, opened read-only. Set `DUCKDB_PATH` or pass `--duckdb`.

## 2. Credentials and environment variables

1. Generate the key pair: `.\.venv\Scripts\python.exe snowflake\setup\generate_key_pair.py`. It writes `retail_svc_rsa_key.p8` (encrypted), `.pub` and `.pass` under `~/.snowflake/keys`, refuses paths inside the repository and prints only the public key.
2. Copy [`../.env.example`](../.env.example) to the git-ignored `.env.retail` (keep any existing `.env`, which may belong to another project). Fill in the account, `SNOWFLAKE_USER=RETAIL_SVC`, the key path and the passphrase. Never commit the copy; `.env` and `.env.*` are ignored, and so are `*.p8`, `*.p12`, `*.pfx` and `rsa_key*`.
3. **Nothing in this repository loads a `.env` file by itself.** Load it into your PowerShell session first:

```powershell
# loads KEY=VALUE lines of the file you named into this session only; prints nothing
Get-Content .env.retail | Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' } | ForEach-Object {
  $k, $v = $_ -split '=', 2
  Set-Item -Path ("Env:" + $k.Trim()) -Value $v.Trim().Trim('"')
}
```

| Variable | Used by | Default |
|---|---|---|
| `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_PATH` | every live command | required |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | every live command, only for an encrypted key | unset |
| `RETAIL_SF_ROLE` | dbt, `src/data_access`, reconciliation | `RETAIL_TRANSFORMER` (the loader defaults to `RETAIL_LOADER`) |
| `RETAIL_SF_WAREHOUSE`, `RETAIL_SF_DATABASE` | all | `RETAIL_WH`, `RETAIL_OLIST` |
| `RETAIL_SF_CONFIRM` | `src/data_access` live-connect gate (only the value `1` counts) | unset |
| `RETAIL_DATA_DIR` | loader | `./data` |
| `DBT_DEV_SUFFIX` | dbt dev/ci schema prefix; reconciliation `--schema-suffix`. **Leave it unset in `.env.retail`** when you work against the prod schemas, or the reconciliation looks for `<suffix>_MARTS` | `DBT_DEV` (dev), `DBT_CI` (ci) |
| `DATA_BACKEND` | `src/data_access`, the ML scripts | `duckdb` |
| `DASHBOARD_BACKEND` | `src/dashboard/build_data.py` | `snowflake` |
| `DUCKDB_PATH` | `src/data_access`, reconciliation, dashboard build | `warehouse.duckdb` |
| `FORECAST_WRITEBACK` | opt-in `ML` write-back for callers of `src/data_access/writeback.py` (`publish_ml.py` uses its own `--write` flag instead) | unset (off) |
| `REQUESTS_CA_BUNDLE` | dbt only, behind a TLS-inspecting proxy (section 7) | unset |

If your shell has `RETAIL_SF_ROLE=RETAIL_TRANSFORMER`, the RAW load fails (that role cannot write `RAW`). Pass `--role RETAIL_LOADER` to the loader explicitly.

## 3. Offline checks (no Snowflake connection)

| Check | Command (repo root) |
|---|---|
| dbt parses with no connection | in PowerShell, `$env:SNOWFLAKE_ACCOUNT="dummy"; $env:SNOWFLAKE_USER="dummy"; $env:SNOWFLAKE_PRIVATE_KEY_PATH="dummy.p8"; snowflake\dbt\.venv\Scripts\dbt.exe parse --profiles-dir snowflake\dbt --project-dir snowflake\dbt --target ci --target-path <scratch>\target --log-path <scratch>\logs` |
| Data dictionary is current | `python scripts\render_data_dictionary.py --manifest <scratch>\target\manifest.json --check` |
| List the reconciliation checks | `$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m reconciliation.cli --list` (22 checks) |
| Loader dry run (SQL and local record counts) | `.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --dry-run` |
| Test suite | `pytest` (from an environment that has it; the repo `.venv` does not) |

## 4. Step 1: preflight and setup - RUN 2026-11-12

Run in a Snowsight worksheet, in this order. The author ran them in the `Retail_Olist` workspace as `ACCOUNTADMIN`.

1. `setup/00_preflight.sql` (read-only). Confirm that no `RETAIL_OLIST`, `RETAIL_WH` or `RETAIL_*` role already exists for another purpose: `CREATE ... IF NOT EXISTS` silently does nothing on a name collision.
2. `setup/01_objects.sql`, then `setup/02_grants.sql`.
3. `setup/03_resource_monitor.sql` (`ACCOUNTADMIN`).
4. `setup/04_service_user.sql` after pasting the public key printed by `generate_key_pair.py` in place of `<RSA_PUBLIC_KEY>` in your worksheet copy. Keep the placeholder in the committed file.
5. As `RETAIL_LOADER`: `ingestion/file_formats.sql`, then `ingestion/ddl_raw.sql`. The loader expects `RAW.INGESTION_LOG` to exist, so run these before the first load.
6. Optional, `ACCOUNTADMIN`: `setup/05_monitor_grant.sql`, so the service user can report credit use (section 12). Run 2026-11-13.
7. For the Model Registry, `SYSADMIN`: `setup/06_model_registry_grants.sql` (section 9). Run 2026-11-13.
8. For the notebooks in a Git-connected workspace, `ACCOUNTADMIN`: `setup/07_git_workspace.sql`. Run 2026-11-13 (prefix `https://github.com/<owner>/`). Then *Workspaces → + → Git workspace*, public repository, switch to the branch; connect a notebook service on `SYSTEM_COMPUTE_POOL_CPU` with a **15-minute idle timeout**, as `RETAIL_TRANSFORMER` on `RETAIL_WH`; suspend the service afterwards (*Monitoring → Services & jobs*).
9. For the scheduled scoring task, `ACCOUNTADMIN` and `SYSADMIN`: `setup/08_scoring_task_grants.sql`, then `ml/scoring_task.sql` as `RETAIL_TRANSFORMER`. **Grants not run**; the tables and config of `ml/scoring_task.sql` exist.

Result: the database, six schemas, warehouse, three roles, monitor and service user exist; re-running each file is a no-op. Objects of other projects on the account were not touched.

## 5. Step 2: ingestion - RUN 2026-11-12

Full detail and failure table: [`../docs/migration/INGESTION_RUNBOOK.md`](../docs/migration/INGESTION_RUNBOOK.md).

```powershell
$env:RETAIL_DATA_DIR = "<folder with the nine csv files>"
.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --role RETAIL_LOADER           # prints the target and stops
.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --role RETAIL_LOADER --yes     # uploads and loads
```

Measured (batch `20261112T153220Z`, about one minute in all): all nine tables `SUCCESS` in `RAW.INGESTION_LOG`, each with loaded rows equal to the record count from the Python `csv` module: CUSTOMERS 99,441, GEOLOCATION 1,000,163, ORDER_ITEMS 112,650, ORDER_PAYMENTS 103,886, ORDER_REVIEWS 99,224, ORDERS 99,441, PRODUCTS 32,951, SELLERS 3,095, PRODUCT_CATEGORY_TRANSLATION 71. A second run skipped every file (checksums already loaded). The `ENDSWITH(<last column>, CHR(13))` check returns 0 for all nine tables (re-checked 2026-11-13), so the CRLF handling of the file format is correct; 3,852 review messages keep their embedded line breaks inside quotes, as intended.

## 6. Step 3: dbt - RUN 2026-11-12

```powershell
cd snowflake\dbt
.\.venv\Scripts\dbt.exe deps   --profiles-dir . --project-dir .                     # needs network to hub.getdbt.com
.\.venv\Scripts\dbt.exe parse  --profiles-dir . --project-dir . --target ci         # offline, never connects
.\.venv\Scripts\dbt.exe build  --profiles-dir . --project-dir . --target prod       # STAGING, INTERMEDIATE, MARTS, PBI
```

Measured: `dbt build --target prod` finished with `PASS=367 WARN=0 ERROR=0 SKIP=0` (46 models, 321 tests) in about a minute on the XSMALL warehouse. The `ASOF JOIN ... MATCH_CONDITION` in `int_late_delivery_history` ran as written; the range-join fallback (`--vars '{late_delivery_history_method: range_join}'`) was not needed.

- `dev` and `ci` write to prefixed schemas, `prod` to the plain ones. Python, the dashboard build, the reconciliation and the Power BI templates read the plain schemas by default.
- Staging and intermediate models are views, marts are tables, Power BI models are views in `PBI`.
- Run dbt with the absolute path to `dbt.exe` when you start it from a script; a relative path was not found by `subprocess` on Windows.

## 7. TLS-inspecting proxies (Avast and similar)

On the author's machine Avast's web shield re-signs HTTPS traffic. Windows trusts Avast's root certificate, but the `certifi` bundle inside the dbt venv does not, so `dbt build` failed with `SSL: CERTIFICATE_VERIFY_FAILED`. The fix applies to one PowerShell session and changes nothing globally:

```powershell
.\.venv\Scripts\python.exe snowflake\dbt\make_ca_bundle.py      # writes ~/.snowflake/ca-bundle-with-windows-roots.pem
$env:REQUESTS_CA_BUNDLE = "$HOME\.snowflake\ca-bundle-with-windows-roots.pem"
```

The repo `.venv` (connector 5.2) connected without it. `uv sync` for the dbt venv may also need `--native-tls`. Do not turn off certificate verification instead.

## 8. Step 4: reconciliation against DuckDB - RUN

Compares the five dimensions, four facts, eight analytics marts, the late-delivery feature table and the weekly series, plus the headline numbers, with exact comparison for money, counts, keys, booleans and timestamps. It sends only single `SELECT`/`WITH` statements.

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m reconciliation.cli --duckdb <path to warehouse.duckdb> --yes --write-report   # overwrites docs/validation/RECONCILIATION_REPORT.md
```

Measured: **22 of 22 checks PASS with 0 differences** ([report](../docs/validation/RECONCILIATION_REPORT.md)), including the late-delivery feature table. The tie-break differences once expected there are gone: both engines now break `arg_max`/`max_by` ties the same way (DD-21). The headline numbers match exactly: R$13,494,400.74 net revenue, 98,199 net orders, 7,827 late, 96,282 labelled with 7,823 late.

## 9. Step 5: Python on Snowflake - RUN 2026-11-13

```powershell
.\.venv\Scripts\python.exe src\ml\forecast_baseline.py      --backend snowflake --yes   # writes reports\snowflake\forecast_metrics.json
.\.venv\Scripts\python.exe src\ml\late_delivery_baseline.py --backend snowflake --yes   # writes reports\snowflake\late_delivery_metrics.json
```

A Snowflake run writes to `reports/snowflake/`, so it never overwrites the tracked DuckDB metrics. Measured against the DuckDB metrics in `reports/`:

- **Weekly forecast:** identical, every value (0 differences).
- **Late-delivery model:** the gradient-boosting results are identical. Seven logistic-regression values (v1 and v5) differ by at most 6e-6 (largest: one month's PR-AUC, 0.180318 vs 0.180324). The cause is floating-point rounding in the inputs, not different data: both backends return the same 96,282 rows, in the same order, with the same columns, but three averaged features are summed in a different order (`recent_days_28d` differs by at most 1.4e-9, `route_prior_days` by 2.3e-10, `distance_km` by 1.4e-12), and the logistic solver carries that into the sixth decimal.

`drift_analysis`, `export_scores`, `export_data` and `run_analytics` stay DuckDB-only. `export_scores` reads the order category through `datasets.order_category`, which works on both backends, so the dashboard's risk page can be built from Snowflake.

### Publishing the ML outputs to Snowflake - RUN 2026-11-13

```powershell
.\.venv\Scripts\python.exe src\ml\publish_ml.py --yes            # computes and validates the three outputs; writes nothing
.\.venv\Scripts\python.exe src\ml\publish_ml.py --yes --write    # writes them under one new run_id
```

`publish_ml.py` computes the late-delivery scores (`export_scores.build_from`), the forecast backtest (`export_data.forecast_backtest`) and the flag shares from the Snowflake marts and writes them to `ML.LATE_DELIVERY_SCORES`, `ML.FORECAST_BACKTEST` and `ML.FLAG_SHARE`, all under one `run_id`. A dry run is the default; `--write` is required to write. Earlier runs are kept; consumers read the latest `run_id`. `--run-id` replaces the rows of an existing run and accepts only the generated form (`YYYYMMDDTHHMMSSZ-xxxxxxxx`): the Power BI templates take the text-greatest `run_id` as the latest, which holds only for that form.

Each table is written by `src/data_access/writeback.py`: `CREATE TABLE IF NOT EXISTS`; `PUT` of one Parquet file into the user stage `@~`; then `BEGIN; DELETE ... WHERE run_id = ?; COPY INTO ...; COMMIT`, so a run's rows are replaced atomically; then the staged file is removed. It uses the user stage, which needs no grant, so the write-back does not depend on `CREATE STAGE` on `ML` (granted since `setup/06_model_registry_grants.sql`, for the Model Registry only); `write_pandas` would also not have been transactional. Nothing is dropped, replaced or truncated.

Measured (run `20261113T122357Z-a99b8a21`, about 35 seconds): 38,988 scores (six test months; late rate 0.088; the 3,901 flagged orders have a late rate of 0.215), 1,610 backtest rows and 6 flag shares, read back with matching counts. Column types are as declared (`DATE`, `BOOLEAN`, `NUMBER(38,0)`, `FLOAT`, `TEXT`), the user stage is empty afterwards, and `RETAIL_REPORTER` has `SELECT` on the new tables through the future grants. Re-publishing the same `run_id` left exactly one copy of its rows. Against the same outputs built from DuckDB: the backtest is identical; the scores cover the same orders with identical flags, labels, months, states and categories, and the risk scores differ by at most 8e-7 (floating-point summation order, as in section 9), which reorders 8 near-tied orders within their month by one position.

### The model in the Snowflake Model Registry - RUN 2026-11-13

```powershell
cd snowflake\ml; uv sync --native-tls; cd ..\..                                   # once: its own Python 3.13 environment
snowflake\ml\.venv\Scripts\python.exe snowflake\ml\register_model.py --yes             # trains and reports; registers nothing
snowflake\ml\.venv\Scripts\python.exe snowflake\ml\register_model.py --yes --register  # logs a new version (named V1_<date>_<commit>)
snowflake\ml\.venv\Scripts\python.exe snowflake\ml\register_model.py --yes --verify V1_20261113_CC90DC8  # re-checks a version in Snowflake
```

`snowflake-ml-python` needs pandas below 3 and a connector below 5, so the registry code runs in `snowflake/ml/.venv` (Python 3.13, `snowflake-ml-python` 2.8.0, the newest in Snowflake's own package channel, and scikit-learn 1.9.1, the repo's version and in the channel). Behind a TLS-inspecting proxy set `REQUESTS_CA_BUNDLE` as in section 7. It needs `setup/06_model_registry_grants.sql` (once, `SYSADMIN`).

The registered model is the v1 logistic regression from `src/ml/late_delivery_baseline.py`, trained on every labelled order in `MARTS.MART_LATE_DELIVERY_FEATURES` from 2017 on. It carries the out-of-time backtest metrics from `reports/snowflake/late_delivery_metrics.json` (a model trained on all months has no honest held-out score of its own), the git commit and the feature table. An existing version is never replaced; a new commit gives a new version name.

Measured: `RETAIL_OLIST.ML.LATE_DELIVERY_RISK` version `V1_20261113_CC90DC8` (the default version) was trained on 96,019 orders and exposes `PREDICT_PROBA`, `PREDICT`, `DECISION_FUNCTION` and `PREDICT_LOG_PROBA`, runnable in warehouses, with Python 3.13 and `snowflake-ml-python` 2.8.0 from Snowflake's Anaconda channel. Scoring 2,000 orders inside Snowflake with it matched the local model to 1.1e-16. Its backtest metrics: ROC AUC 0.707, PR AUC 0.184, precision in the riskiest 10% 0.207 against a base rate of 0.085. Details: `reports/snowflake/model_registry.json`. One caveat: this first version was logged before the script pinned dependencies exactly (`relax_version` defaulted to true), so its exact pins, scikit-learn and `snowflake-ml-python` among them, were relaxed to compatible ranges, and Snowflake may resolve newer versions of them for it in future. Versions logged from now on keep every pin exact, and `--verify` re-checks a version against a local retrain.

Not built yet: scoring new orders inside Snowflake on a schedule (a Task calling the model) and ML monitoring in SQL. Publishing (above) still scores on the client.

### ML inside Snowflake: notebooks, scheduled scoring, monitoring (DD-26)

| Piece | Where it runs | Status (2026-11-13) |
|---|---|---|
| `notebooks/snowflake/02_late_delivery_model_sf.ipynb`, `03_weekly_forecast_sf.ipynb` | Notebooks in Workspaces (Container Runtime, CPU compute pool), run by hand | **Run in a Git-connected workspace 2026-11-13** (runtime numpy 2.3.5, scipy 1.15.3, pandas 2.3.3; scikit-learn 1.9.1 pinned). All cells ran on Snowflake data. Closed-form forecast methods match the DuckDB reference exactly; the scipy-optimised ones within 3.5e-7, and late delivery within 1.3e-9 of the Snowflake backtest. Those gaps come from the library versions (0.0 on the laptop). |
| `notebooks/snowflake/04_train_register_sf.ipynb` | Same, run by hand | **Run 2026-11-13:** trained v1 inside Snowflake on 96,019 orders and registered `V1WS_20261113_7370C92` (not default). Over all 96,019 orders, `mv.run` and SQL scores equal the in-notebook model to 3.3e-16, and the laptop-registered version to 1.1e-12. |
| `snowflake/ml/scoring_task.sql`: task `ML.SCORE_LATE_DELIVERY` into `ML.LATE_DELIVERY_SCORES_REGISTRY` | SQL on `RETAIL_WH`, no compute pool | Tables and config created; the scoring block was run twice live (6,306 orders of 2018-08, the rerun replaced them, scores equal to the local model to 2.8e-16). **The task itself is not created:** it needs `setup/08_scoring_task_grants.sql`. |
| `snowflake/dbt/models/monitoring/` (schema `ML_MONITORING`) | dbt views on `RETAIL_WH` | **Built live** (PASS=18). Calibration equals the Python calculation exactly; single-feature AUCs match `drift_analysis.py` E1 to 5e-13; the drift view shows 74.8% of August 2018 orders promised under 20 days. |

Notes:
- **How the notebooks are made.** They are generated from the originals by `scripts/make_snowflake_notebooks.py`, so edit the originals or the script. They read the marts through the notebook's own session (`src/data_access/snowpark.py`): no keys inside Snowflake.
- **Running them.** Run them as `RETAIL_TRANSFORMER` (PUBLIC already has USAGE on `SYSTEM_COMPUTE_POOL_CPU`). Use the Git-connected workspace from `setup/07_git_workspace.sql`, and **suspend the notebook service after each session**: the compute pool bills while it runs and is not covered by `RETAIL_MONITOR`. The default idle timeout is 24 hours unless an admin sets `NOTEBOOK_VNEXT_IDLE_TIMEOUT_OPTIONS_MINUTES`.
- **Why scheduled scoring writes its own table.** The registered model was trained on every month, so its 2018 scores are in-sample. They go to their own table, never to `ML.LATE_DELIVERY_SCORES`, which holds the out-of-time backtest that Power BI and the monitoring views read. The dataset ends in 2018, so a scheduled run replays the same month; `ML.SCORING_CONFIG` pins the model version and the month.
- **Waiting for the owner's approval:**
  - `setup/08_scoring_task_grants.sql`: `EXECUTE TASK` on the account.
  - The notebook idle-timeout account parameter.

## 10. Step 6: the HTML dashboard - RUN 2026-11-12

`src/dashboard/build_data.py` builds `dashboard/data/*.json` from Snowflake by default (DD-22): KPIs and weekly series from `MARTS`, the analytics tables from `MARTS.mart_*`, risk roll-ups from a v1 retrain on the Snowflake features. A build from Snowflake and one from DuckDB (`--backend duckdb`) gave identical files for the KPIs, analytics, forecast and risk. See [`../dashboard/README.md`](../dashboard/README.md).

## 11. Step 7: Power BI patched copy - NOT RUN

```powershell
.\.venv\Scripts\python.exe powerbi\snowflake\apply_snowflake_source.py --ml-on-files
```

This writes a git-ignored copy to `powerbi_snowflake/` and rewrites only `expressions.tmdl` and the data-source block of each import table. The `PBI` views it reads now exist. The copy has not been opened in Power BI Desktop and the sign-in method is undecided: follow [`../docs/migration/POWERBI_SWITCH_GUIDE.md`](../docs/migration/POWERBI_SWITCH_GUIDE.md). The `ML` tables now exist too (section 9), so the copy can be made without `--ml-on-files` and read all 12 tables from Snowflake.

## 12. Cost

`RETAIL_WH` is XSMALL with a 60-second auto-suspend, and `RETAIL_MONITOR` suspends it at 5 credits a month. Everything above ran in a few minutes of warehouse time in total.

**0.34 credits measured** (2026-11-13, `RETAIL_MONITOR`: 0.34 of the 5-credit monthly quota, 6.8%, 4.66 remaining). The monitor was created during setup, before the first load, so this covers everything that has run on `RETAIL_WH`: the RAW load and its idempotent rerun, every `dbt build`, the reconciliation runs, the dashboard data builds, the Snowflake ML runs and the ad hoc checks.

A resource monitor is visible only to roles that hold a privilege on it. To measure credits as the service user:

1. Once, as `ACCOUNTADMIN` in Snowsight, run `setup/05_monitor_grant.sql` (done 2026-11-13). It grants `MONITOR` (read-only) on `RETAIL_MONITOR` to `RETAIL_TRANSFORMER`, and nothing account-wide.
2. Then, at any time:

```powershell
.\.venv\Scripts\python.exe snowflake\monitoring\credit_usage.py --yes   # quota, used and remaining credits for the current month
```

Without step 1 the script stops with a message rather than reporting zero. Without either, `SHOW RESOURCE MONITORS LIKE 'RETAIL_MONITOR';` as `ACCOUNTADMIN` in Snowsight gives the same figures.

## 13. Where things stand

| Capability | Offline | Live |
|---|---|---|
| Setup SQL, resource monitor, service user | static checks: preflight read-only, no `OR REPLACE`/`DROP` | RUN 2026-11-12 in Snowsight |
| RAW ingestion | fake-connector tests; local record counts | RUN 2026-11-12: 9/9 tables, counts exact, rerun is a no-op, no stray CRs |
| dbt project (46 models, 321 tests) | `dbt parse`/`compile` | RUN 2026-11-12: PASS=367 |
| Reconciliation | fixture and perturbation tests | RUN: 22/22, 0 differences |
| Python on Snowflake (Tier 1) | fake-connector tests | RUN 2026-11-13: forecast identical; late-delivery equal to 6e-6 |
| Dashboard data build | unit tests | RUN 2026-11-12: identical to the DuckDB build |
| ML outputs in Snowflake (`publish_ml.py`) | stage-fake tests: statement order, rollback, clean-up | RUN 2026-11-13: run `20261113T122357Z-a99b8a21`, counts read back, matches DuckDB |
| Power BI patched copy | byte-identity tests | NOT RUN (not opened in Desktop) |
| Model Registry (`ml/register_model.py`) | fake-registry tests: gate, no replacement, exact pin, verify | RUN 2026-11-13: `LATE_DELIVERY_RISK` `V1_20261113_CC90DC8`, scored inside Snowflake, equal to local to 1.1e-16 |
| Notebooks in Snowflake (`notebooks/snowflake/`) | generator check, parse and hygiene tests; executed against Snowflake data | RUN in a workspace 2026-11-13; 04 registered `V1WS_20261113_7370C92` |
| Scheduled scoring (`ml/scoring_task.sql`) | statement-shape tests | Block RUN twice live 2026-11-13 (6,306 orders, 2.8e-16); task NOT CREATED (needs `setup/08`) |
| Drift and calibration in SQL (`dbt/models/monitoring/`) | AUC formula test | RUN 2026-11-13: PASS=18, equal to the Python results |
| Credit use | | MEASURED 2026-11-13: 0.34 credits of the 5-credit monthly quota (section 12) |
