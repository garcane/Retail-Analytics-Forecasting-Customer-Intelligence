# dbt project: Olist on Snowflake

> **Live status (2026-11-13):** this page was written before the live run and its body is kept as the design record. The pipeline has since run on Snowflake: setup and RAW load (counts exact, no stray carriage returns), `dbt build` PASS=367 including the `ASOF JOIN`, reconciliation 22/22 with 0 differences, and the Tier 1 Python models. Not run: the ML write-back and the Power BI patched copy. Where this page says NOT YET RUN or UNVERIFIED about those steps, read [snowflake/README.md](../README.md) for the measured result.

Snowflake + dbt implementation of the Olist star schema, built alongside the (unchanged) DuckDB one.
Status of every claim is stated in [README_LIVE_CHECKS.md](README_LIVE_CHECKS.md): nothing here has been run
against a live Snowflake account.

```
RAW (VARCHAR landing tables, loaded by snowflake/ingestion)
  -> STAGING       9 views   stg_olist__*   typed, same columns as sql/staging/stg_*.sql
  -> INTERMEDIATE  views     int_*          customers_latest, geography_points/rollup, order_items_agg, order_payments_agg
  -> MARTS         tables    dim_* / fact_*  same names, grain, columns as sql/dimensions + sql/facts
```

## Layout and conventions

| Folder | Materialisation | Schema (prod) | Contents |
|---|---|---|---|
| `models/staging/` | view | `STAGING` | `_sources.yml` (source `olist_raw`) + 9 staging models |
| `models/intermediate/` | view | `INTERMEDIATE` | non-late-delivery intermediates; `late_delivery/` is a sub-folder for the ML features |
| `models/marts/core/` | table | `MARTS` | 5 dimensions + 4 facts (with `-1` unknown members) |
| `models/marts/analytics/` | table | `MARTS` | `mart_*` for `sql/analytics/01..08` (separate workstream) |
| `models/marts/ml/` | table | `MARTS` | `mart_late_delivery_features`, `mart_weekly_orders_revenue` (separate workstream) |
| `models/pbi/` | view | `PBI` | Power BI-facing views (separate workstream) |
| `macros/` | | | `generate_schema_name`, `iso_week_start`, `date_key` only |
| `tests/` | | | singular tests: ports of `sql/validation/checks.sql` plus three guards |

**dbt model names are global.** The Power BI views in `PBI` must expose the object names `DIM_DATE`, `FACT_ORDERS`,
etc., but a model called `dim_date` already exists in `marts/core`. Name those models `pbi_dim_date`,
`pbi_fact_orders`, ... and set `alias: dim_date` (`{{ config(alias='dim_date') }}`) so the Snowflake object is
`PBI.DIM_DATE`.

Schema routing (`macros/generate_schema_name.sql`):

| Target | Schema of a `+schema: marts` model |
|---|---|
| `prod` | `MARTS` |
| `dev` | `<DBT_DEV_SUFFIX>_MARTS` (default prefix `DBT_DEV`) |
| `ci` | `<DBT_DEV_SUFFIX>_MARTS` (default prefix `DBT_CI`) |

## Environment (isolated from the repo root)

The root project is on Python 3.14 / DuckDB. dbt lives in its own environment:

```powershell
# from the repo root; the explicit environment path keeps uv away from the root .venv
$env:UV_PROJECT_ENVIRONMENT = "$PWD\snowflake\dbt\.venv"
uv sync --project snowflake/dbt --python 3.13          # add --native-tls behind a TLS-intercepting proxy
```

Resolved (see `uv.lock`): `dbt-core 1.11.17`, `dbt-snowflake 1.11.6`, `dbt-adapters 1.24.5`,
`snowflake-connector-python 4.8.0`, Python 3.13.5; `dbt_utils 1.4.1` (via `dbt deps`, pinned in `package-lock.yml`).

## Commands

```powershell
cd snowflake/dbt
dbt deps    --profiles-dir . --project-dir .                    # needs network to hub.getdbt.com, not Snowflake
dbt parse   --profiles-dir . --project-dir . --target ci       # offline; no env vars needed; never connects
dbt compile --profiles-dir . --project-dir . --target ci --no-populate-cache   # offline as well (see live checks)
# live (needs the SNOWFLAKE_* / RETAIL_SF_* environment variables, see profiles.yml): NOT RUN
dbt build   --profiles-dir . --project-dir . --target dev
```

Generated, git-ignored paths: `target/`, `logs/`, `dbt_packages/`, `.venv/`, `.user.yml` (see `.gitignore` here).
`package-lock.yml` and `uv.lock` are committed.

## Translation notes (DuckDB -> Snowflake)

| DuckDB | Snowflake here | Why |
|---|---|---|
| `read_csv(columns={...})` types | `cast(nullif(col,''), ...)`, `to_timestamp_ntz(..., 'YYYY-MM-DD HH24:MI:SS')` | RAW is all VARCHAR; `nullif` mirrors DuckDB reading empty fields as NULL |
| `strftime(ts,'%Y%m%d')::int` | `date_key()` macro = `coalesce(to_char(ts,'YYYYMMDD')::integer, -1)` | |
| `date_diff('second',a,b)/86400.0` | `datediff(second,a,b)::float / 86400.0` | avoid NUMBER-scale division |
| `order by x desc` (NULLs last by default) | `desc nulls last` | Snowflake sorts NULLs first under DESC |
| `monthname/dayname`, `weekofyear`, `isodow` | `decode(month(d),...)`, `weekiso`, `dayofweekiso` | full English names; ISO week |
| `generate_series` | `GENERATOR(rowcount=>10000)` + `row_number() over (order by seq4())` | `seq4()` can have gaps |
| PK / FK constraints | dbt `unique`, `not_null`, `relationships` tests | Snowflake does not enforce them |

## Verification summary (offline)

See README_LIVE_CHECKS.md, section "What was verified offline".
