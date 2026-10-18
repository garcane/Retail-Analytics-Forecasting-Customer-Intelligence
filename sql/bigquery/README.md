# sql/bigquery — the same layers in GoogleSQL

Translated SQL for BigQuery, one file per table with the **same file names** as [`sql/`](../../), so every file can be compared side by side with its DuckDB original — the layout that [docs/MIGRATING_TO_CLOUD.md](../../docs/MIGRATING_TO_CLOUD.md) section 6 reserves for this folder. Started with the **staging layer** (DD-18); dimensions, facts, validation, analytics and the ML features are **not translated yet**.

Nothing in this folder has ever been run on Google Cloud: no GCP project exists (D-002), and the SQL is a translation record, not a deployment. The files are checked by `tests/test_bigquery_staging.py`, which compares them with the DuckDB originals and with the column lists in `data/`, and every construct was checked against the GoogleSQL reference (2026-10-18).

## Folders

| Folder | Creates | Translates |
|---|---|---|
| `raw/` | 9 CSV **external tables** over the immutable files in `gs://<bucket>/raw/olist/`, every column `STRING` | the `read_csv(columns = {...})` blocks of `sql/staging/` — the part that reads a file |
| `staging/` | 9 typed **views**, same names as `sql/staging/` | the `create or replace view` part of `sql/staging/` |

RAW stays bytes as written (the BOM header is skipped, zip prefixes keep their leading zeros); typing happens in the staging views, exactly where the local files do it. `read_csv` has no BigQuery equivalent, so each local staging file splits in two: file name + column order → `raw/`, types + renames → `staging/`.

`allow_quoted_newlines = true` is set on every external table (3,852 review comments contain line breaks inside quotes; DuckDB's reader accepts them by default).

### Alternative not taken

Step 4 of the migration guide loads **native** staging tables with `bq load` and `schemas/*.json`. That produces the same object names and schema as `staging/`; pick one route, not both. The views here re-scan the CSVs on Cloud Storage at query time — fine for an 80 MB dataset, too slow for production.

## Tokens

Two tokens are substituted at run time, the same way `build_warehouse.py` substitutes `${DATA_DIR}`:

| Token | Becomes |
|---|---|
| `${PROJECT}` | the GCP project id, e.g. `` `my-project.staging.stg_orders` `` |
| `${BUCKET}` | the bucket name, e.g. `gs://my-bucket/raw/olist/...` |

## Type mapping

From [docs/data/DATA_MODEL.md](../../docs/data/DATA_MODEL.md#moving-to-bigquery):

| DuckDB (`sql/staging`) | GoogleSQL (`sql/bigquery/staging`) |
|---|---|
| `VARCHAR` | `STRING` — already STRING in `raw/`, so no cast |
| `INTEGER` | `INT64` |
| `DECIMAL(12,2)` | `NUMERIC` |
| `DOUBLE` | `FLOAT64` |
| `TIMESTAMP` (no time zone) | `DATETIME` |

## How to run (untested, like the rest of the guide)

1. Create the datasets, `raw` in addition to the guide's step 3: `bq --location=LOC mk --dataset PROJECT:raw` and `bq --location=LOC mk --dataset PROJECT:staging`.
2. Upload the CSVs exactly as in the guide's step 2.
3. Substitute `${PROJECT}` and `${BUCKET}`, run every file in `raw/`, then every file in `staging/`: `bq query --use_legacy_sql=false "$SQL"`.
4. Check the view row counts against the local staging layer (e.g. `stg_orders` 99,441 rows), then continue with the curated layer of `sql/` when it is translated.

Assumptions verified against the local data before writing these files: every timestamp value has the full `YYYY-MM-DD HH:MM:SS` form (so `cast(... as datetime)` is safe), integer and money columns contain only clean values, empty CSV fields are NULL in DuckDB's typed read as well as in BigQuery's reader, and all nine CSV header orders match the column lists above (BigQuery maps a CSV external table's columns positionally after `skip_leading_rows`).
