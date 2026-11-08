# Snowflake + dbt implementation: setup and runbook

A second, cloud implementation of the Olist star schema: **RAW -> dbt staging -> intermediate -> marts -> Python forecasting / Power BI** on Snowflake. The DuckDB implementation (`sql/`, `src/`, `warehouse.duckdb`) is unchanged and remains the reference; this folder sits next to it and does not replace it.

> **Status (2026-11-06): nothing in this guide has been run against a Snowflake account.** The code, SQL, dbt project and tests were built and checked offline. Every live step below is labelled **NOT YET RUN**; do not read any of them as a result. Where a step has an offline check that was actually run, it says so and gives the command. Details of what is and is not verified: [`dbt/README_LIVE_CHECKS.md`](dbt/README_LIVE_CHECKS.md), [`../docs/migration/SNOWFLAKE_MIGRATION.md`](../docs/migration/SNOWFLAKE_MIGRATION.md) (section 9).

Related pages: [architecture](../docs/architecture/SNOWFLAKE_ARCHITECTURE.md) | [SQL migration inventory](../docs/migration/SNOWFLAKE_MIGRATION.md) | [data dictionary](../docs/data_dictionary/DATA_DICTIONARY.md) | [ingestion runbook](../docs/migration/INGESTION_RUNBOOK.md) | [Power BI switch guide](../docs/migration/POWERBI_SWITCH_GUIDE.md) | [dbt project README](dbt/README.md) | [reconciliation report (NOT RUN stub)](../docs/validation/RECONCILIATION_REPORT.md)

## What is in this folder

| Path | Purpose | Changes Snowflake? |
|---|---|---|
| `setup/00_preflight.sql` | Read-only `SHOW`/`SELECT`: existing `RETAIL%` objects, your role | No |
| `setup/01_objects.sql` | Database `RETAIL_OLIST`, schemas `RAW, STAGING, INTERMEDIATE, MARTS, PBI, ML`, warehouse `RETAIL_WH`, roles | Yes, additive (`IF NOT EXISTS`) |
| `setup/02_grants.sql` | Least-privilege grants for `RETAIL_LOADER`, `RETAIL_TRANSFORMER`, `RETAIL_REPORTER` | Yes, additive |
| `ingestion/file_formats.sql`, `ingestion/ddl_raw.sql` | CSV file format and stage; nine RAW tables and `RAW.INGESTION_LOG` | Yes, additive |
| `ingestion/load_raw.py` | `PUT` + `COPY INTO` loader with checksum log and record-count checks | Writes data into `RAW` only |
| `dbt/` | The dbt project (46 models, 39 singular tests, generic tests in YAML) | Creates views and tables in `STAGING` to `PBI` |

Related code outside this folder: `src/data_access/` (Python backend switch), `src/reconciliation/` (DuckDB vs Snowflake comparison), `powerbi/snowflake/` (patched Power BI copy). None of the SQL uses `OR REPLACE` or `DROP`, and none creates a resource monitor or changes account-level settings.

## 1. Prerequisites

- **A Snowflake account and a user** with key-pair authentication (public key registered on the user by the account owner; the scripts do not do that). No passwords are used anywhere. For the full role setup you need `SECURITYADMIN` (or any role with `CREATE ROLE`) and `SYSADMIN`; without them see the single-role fallback at the top of `setup/01_objects.sql`.
- **Python environments.** There are two, kept apart on purpose:
  - The repo environment (`.venv`, Python 3.14.2 on this machine) runs the loader, `src/data_access`, `src/reconciliation` and the Power BI patch script. At the time of writing it can import `duckdb`, `pandas`, `snowflake.connector` (5.2.0) and `cryptography`; it has no `pytest`. That the connector works for a live connection on Python 3.14 is UNVERIFIED. **Do not run `uv sync`, `uv lock` or `uv run` at the repo root**: `.python-version` is 3.14 and `uv` would rebuild `.venv`.
  - The dbt environment `snowflake/dbt/.venv` (Python 3.13, `dbt-core` 1.11, `dbt-snowflake` 1.11) is created from `snowflake/dbt/pyproject.toml` and `uv.lock`; the commands are in [`dbt/README.md`](dbt/README.md). Behind a TLS-inspecting proxy `uv sync` needs `--native-tls`, and `dbt deps` may need your root certificates in `REQUESTS_CA_BUNDLE`.
- **The data.** The nine Olist CSVs are git-ignored and not in this repository. Point `RETAIL_DATA_DIR` at the folder that holds them (on the author's machine: `C:\Users\Student\GCP\data`). Without it the loader falls back to `./data` and then stops with an error naming the folder.
- **The reference warehouse** (only for reconciliation): `warehouse.duckdb`, opened read-only. Set `DUCKDB_PATH` or pass `--duckdb`.

## 2. Environment variables (`.env.example`)

1. Copy [`../.env.example`](../.env.example) to a git-ignored file. Both `.env` and `.env.*` are in `.gitignore`. If you already have a `.env` for another project, do not overwrite it: use `.env.retail` instead.
2. Fill in the placeholders in the copy. Never put real values in `.env.example` and never commit the copy.
3. **Nothing in this repository loads a `.env` file.** Export the variables into your PowerShell session first, for example:

```powershell
# loads KEY=VALUE lines of the file you named into this session only; prints nothing
Get-Content .env.retail | Where-Object { $_ -match '^\s*[A-Za-z_][A-Za-z0-9_]*\s*=' } | ForEach-Object {
  $k, $v = $_ -split '=', 2
  Set-Item -Path ("Env:" + $k.Trim()) -Value $v.Trim().Trim('"')
}
```

Variables (the template lists them all, with defaults):

| Variable | Used by | Default |
|---|---|---|
| `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_PATH` | every live command | required |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | every live command, only for an encrypted key | unset |
| `RETAIL_SF_ROLE` | dbt, `src/data_access`, reconciliation | `RETAIL_TRANSFORMER` (the loader defaults to `RETAIL_LOADER`) |
| `RETAIL_SF_WAREHOUSE`, `RETAIL_SF_DATABASE` | all | `RETAIL_WH`, `RETAIL_OLIST` |
| `RETAIL_SF_CONFIRM` | `src/data_access` live-connect gate (only the value `1` counts) | unset |
| `RETAIL_DATA_DIR` | loader | `./data` |
| `DBT_DEV_SUFFIX` | dbt dev/ci schema prefix; reconciliation `--schema-suffix` | `DBT_DEV` (dev), `DBT_CI` (ci) |
| `DATA_BACKEND` | `src/data_access` | `duckdb` |
| `DUCKDB_PATH` | `src/data_access`, reconciliation | `warehouse.duckdb` |
| `FORECAST_WRITEBACK` | opt-in `ML` table write-back | unset (off) |
| `RECON_WAREHOUSE` | optional real-warehouse tests only | unset |

Set `RETAIL_SF_ROLE` with care: if your shell has `RETAIL_SF_ROLE=RETAIL_TRANSFORMER`, the RAW load fails (that role cannot write `RAW`). Pass `--role RETAIL_LOADER` to the loader explicitly.

## 3. Offline checks you can run now (no Snowflake connection)

These need no credentials. Results below are from the authoring session on 2026-11-06 and only prove what each line says.

| Check | Command (repo root) | Result when run |
|---|---|---|
| dbt parses with no connection | in PowerShell, `$env:SNOWFLAKE_ACCOUNT="dummy"; $env:SNOWFLAKE_USER="dummy"; $env:SNOWFLAKE_PRIVATE_KEY_PATH="dummy.p8"; snowflake\dbt\.venv\Scripts\dbt.exe parse --profiles-dir snowflake\dbt --project-dir snowflake\dbt --target prod --target-path <scratch>\target --log-path <scratch>\logs` | succeeded: 46 models, 9 sources. (Use a scratch `--target-path` and `--log-path`: the tracked `snowflake/dbt/target` and `logs` would otherwise be modified.) |
| Data dictionary is current | `python scripts\render_data_dictionary.py --manifest <scratch>\target\manifest.json --check` | rendered `docs/data_dictionary/DATA_DICTIONARY.md` and `--check` reported it up to date |
| List the reconciliation checks | `$env:PYTHONPATH="src"; .\.venv\Scripts\python.exe -m reconciliation.cli --list` | listed 22 checks |
| Loader dry run (prints SQL and local record counts) | `.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --dry-run` | ran with `RETAIL_DATA_DIR` set to the folder holding the nine CSVs, on the repo `.venv` (Python 3.14.2): printed record counts CUSTOMERS 99,441, GEOLOCATION 1,000,163, ORDER_ITEMS 112,650, ORDER_PAYMENTS 103,886, ORDER_REVIEWS 99,224, ORDERS 99,441, PRODUCTS 32,951, SELLERS 3,095, PRODUCT_CATEGORY_TRANSLATION 71, and the SQL a real run would issue; no connection was made |

The test files (`tests/test_data_access.py`, `tests/test_reconciliation.py`, `tests/test_snowflake_ingestion.py`, `tests/test_powerbi_snowflake.py`) need `pytest`, which the repo `.venv` does not have. Their workstreams ran them from other virtual environments; install `pytest` deliberately if you want to run them (the root `dev` dependency group lists it, but see the warning about `uv` above).

## 4. Step 1: preflight (a gate, read-only) - NOT YET RUN

Run `setup/00_preflight.sql` in a Snowsight worksheet (or `snow sql -f`). It only lists existing `RETAIL%` databases, warehouses and roles and your current role. Read the output and confirm:
- no `RETAIL_OLIST` database, `RETAIL_WH` warehouse or `RETAIL_*` role exists, or each one that does belongs to this project;
- you have the roles the next step needs.

`CREATE ... IF NOT EXISTS` silently does nothing on a name collision, so a collision has to be caught here. **Do not continue until the owner of the account has approved the creation.**

## 5. Step 2: create objects and grants - NOT YET RUN

After approval, run in Snowsight or `snow sql -f`, in this order (the files switch roles themselves):

1. `setup/01_objects.sql` (roles as `SECURITYADMIN`, the rest as `SYSADMIN`)
2. `setup/02_grants.sql` (as `SECURITYADMIN`; includes `CREATE SCHEMA ON DATABASE` for `RETAIL_TRANSFORMER`, needed only by the dbt dev target; approve it explicitly)
3. as `RETAIL_LOADER`: `ingestion/file_formats.sql`, then `ingestion/ddl_raw.sql`

Nothing here has been executed; syntax, privilege requirements and the `GRANT ... TO USER IDENTIFIER($VAR)` form are untested. Re-running is designed to be safe.

## 6. Step 3: ingestion - NOT YET RUN

Full detail, failure table and the CRLF/backslash checks: [`../docs/migration/INGESTION_RUNBOOK.md`](../docs/migration/INGESTION_RUNBOOK.md).

```powershell
$env:RETAIL_DATA_DIR = "<folder with the nine csv files>"
.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --dry-run                      # offline: no credentials, no connection
.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --role RETAIL_LOADER           # prints the target and stops (needs --yes)
.\.venv\Scripts\python.exe snowflake\ingestion\load_raw.py --role RETAIL_LOADER --yes     # live: uploads and loads
```

Expected record counts come from the Python `csv` module (reviews: 99,224 records, not the physical line count). A second run with unchanged files should be a no-op; `--reload <table>` truncates and reloads and never drops. After the first live run, run the nine `ENDSWITH(.., CHR(13))` queries in the runbook (section 4.1): the CRLF handling of the file format is UNVERIFIED.

## 7. Step 4: dbt - NOT YET RUN

```powershell
cd snowflake\dbt
.\.venv\Scripts\dbt.exe deps   --profiles-dir . --project-dir .                     # needs network to hub.getdbt.com, no Snowflake
.\.venv\Scripts\dbt.exe parse  --profiles-dir . --project-dir . --target ci         # offline, never connects
# live:
.\.venv\Scripts\dbt.exe build  --profiles-dir . --project-dir . --target dev        # writes to <DBT_DEV_SUFFIX>_STAGING ... _PBI
.\.venv\Scripts\dbt.exe build  --profiles-dir . --project-dir . --target prod       # writes to STAGING, INTERMEDIATE, MARTS, PBI
```

- `dev` and `ci` write to prefixed schemas, `prod` to the plain ones. Power BI templates and `src/data_access` read the plain `MARTS`/`PBI`/`ML` by default (`data_access` datasets accept a `marts_schema` argument for a dev prefix; reconciliation has `--schema-suffix`).
- Staging and intermediate models are views, marts are tables, Power BI models are views in `PBI`.
- **Highest-risk model:** `int_late_delivery_history` uses Snowflake `ASOF JOIN ... MATCH_CONDITION`, which has never run on Snowflake. If it fails: `dbt build -s +mart_late_delivery_features --vars '{late_delivery_history_method: range_join}'` (semantically identical, much slower; measure before relying on it).
- `dbt test` runs 282 generic and 39 singular tests that replace the primary and foreign keys DuckDB enforces. None has run on Snowflake. The checklist of things to verify live, with detail: [`dbt/README_LIVE_CHECKS.md`](dbt/README_LIVE_CHECKS.md).
- Record the measured runtime and credit use of the first `dbt build`; the documentation does not quote an estimate as a result.

## 8. Step 5: reconciliation against DuckDB - NOT YET RUN

Compares the five dimensions, four facts, eight analytics marts, the late-delivery feature table and the weekly series, plus the headline numbers, with exact comparison for money, counts, keys, booleans and timestamps. It only sends single `SELECT`/`WITH` statements.

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m reconciliation.cli --list
.\.venv\Scripts\python.exe -m reconciliation.cli --offline-selftest --duckdb <path to warehouse.duckdb>   # DuckDB against itself, no Snowflake
.\.venv\Scripts\python.exe -m reconciliation.cli --duckdb <path to warehouse.duckdb>                      # prints the target, refuses without --yes
.\.venv\Scripts\python.exe -m reconciliation.cli --duckdb <path to warehouse.duckdb> --yes --write-report  # live; overwrites docs/validation/RECONCILIATION_REPORT.md
```

`docs/validation/RECONCILIATION_REPORT.md` is a stub that says NOT RUN until a live run writes it. Expect `PASS_WITH_TIE_BREAKS` on the late-delivery feature table: `category_prior_n` and `category_prior_late` are expected to differ because the Snowflake models break `arg_max` ties alphabetically while DuckDB's pick is arbitrary (see section 8 of the migration inventory, including the unresolved question of whether the DuckDB reference is itself reproducible). Any other differing column is a defect to investigate, not to explain away.

## 9. Step 6: Python on Snowflake instead of DuckDB - NOT YET RUN

The backend is chosen by `DATA_BACKEND` (default `duckdb`) or by the `backend` argument. A live Snowflake connection requires the credentials in the environment and an explicit confirmation; before connecting it prints the resolved account, database, role and warehouse. **The `main()` functions of `forecast_baseline.py` and `late_delivery_baseline.py` still open DuckDB directly and have no `--backend` flag**, so use the functions:

```powershell
$env:PYTHONPATH = "src;src\ml"
.\.venv\Scripts\python.exe -c "
from data_access import connect
import forecast_baseline as fb
import late_delivery_baseline as ldb
with connect('snowflake', confirm=True) as db:       # NOT YET RUN: check the printed target first
    weekly = fb.weekly_series(db)
    df = ldb.load(db)
    unlabelled = ldb.unlabelled_share(db)
"
```

Reads come from `MARTS.mart_weekly_orders_revenue`, `MARTS.mart_late_delivery_features` and `MARTS.fact_orders`, with an explicit `ORDER BY` on the weekly series and the feature table (`unlabelled_share` is grouped by month and returned as a dict, so it has none). Results are normalised to the DuckDB dtypes and validated against per-dataset schemas.

Write-back of the forecast backtest, late-delivery scores and flag shares to `ML.FORECAST_BACKTEST`, `ML.LATE_DELIVERY_SCORES` and `ML.FLAG_SHARE` is **off by default**. It runs only with `FORECAST_WRITEBACK=1` (or `enabled=True`), only on the Snowflake backend, and only issues `CREATE TABLE IF NOT EXISTS`, `DELETE ... WHERE run_id = ?` and an append, never a drop or truncate. The tables carry an extra `run_id` column. The module `src/data_access/writeback.py` documents the details and the non-transactional delete-then-insert.

`drift_analysis`, `export_scores`, `export_data` and `run_analytics` stay DuckDB-only.

## 10. Step 7: Power BI patched copy - NOT YET RUN

```powershell
.\.venv\Scripts\python.exe powerbi\snowflake\apply_snowflake_source.py --ml-on-files
```

This writes a copy of the project to `powerbi_snowflake/` and rewrites only `expressions.tmdl` and the data-source block of each import table. The committed project is not changed. `--ml-on-files` keeps the three Python-fed tables on their Parquet/CSV files until the `ML` write-back has run; run without it (plus `--force`) to switch all 12 tables.

- **`powerbi_snowflake/` was not in `.gitignore` when this was written.** Check with `git check-ignore powerbi_snowflake` and add it before you create the copy: it will contain your account name.
- The patched copy has not been opened in Power BI Desktop, the Snowflake sign-in method is undecided, and the `PBI` views it reads do not exist until Step 4 has run. Follow the guide: [`../docs/migration/POWERBI_SWITCH_GUIDE.md`](../docs/migration/POWERBI_SWITCH_GUIDE.md).

## 11. Where things stand

| Capability | Built and checked offline | Run live |
|---|---|---|
| Setup SQL (preflight, objects, grants) | static checks only: preflight is read-only, no `OR REPLACE`/`DROP` | NOT YET RUN |
| RAW ingestion | loader logic with a fake connector; local record counts from the real CSVs | NOT YET RUN |
| dbt project (46 models, tests) | `dbt parse`/`compile`; compiled SQL parses in the Snowflake dialect; logic simulated in DuckDB and equal to `warehouse.duckdb` | NOT YET RUN |
| Reconciliation | DuckDB side against the real warehouse; fake and injected-defect fixtures | NOT YET RUN |
| Python backend switch and write-back | fake connector tests; DuckDB path identical to before | NOT YET RUN |
| Power BI patched copy | byte-identity tests on the generated copy | NOT YET RUN (not opened in Desktop) |

## Known issues to be aware of

- The DuckDB reference's late-delivery features were reported to vary between runs on `arg_max` ties; the accounts of the workstreams that saw it disagree about the effect of `threads = 1`. Unresolved.
- CI workflow files under `.github/workflows/` come from another workstream and are not covered here.
