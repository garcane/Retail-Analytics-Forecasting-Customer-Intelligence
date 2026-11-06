# Snowflake RAW ingestion runbook

Scope: getting the nine Olist CSV files into `RETAIL_OLIST.RAW` with `snowflake/ingestion/load_raw.py`.

**Status of this document: written and unit-tested OFFLINE only.** The loader, the setup SQL and the
file format have not been run against any Snowflake account. Every statement about Snowflake's behaviour
below is marked **UNVERIFIED** until a live run confirms it, and this file must be updated with the
measured result (command, date, row counts) at that point. What *is* verified offline is listed at the end.

## 1. What each piece does, and what it never does

| Piece | Purpose | Changes Snowflake? |
|---|---|---|
| `snowflake/setup/00_preflight.sql` | `SHOW` / `SELECT` only: lists existing `RETAIL%` databases, warehouses, roles, and who you are | No (read-only) |
| `snowflake/setup/01_objects.sql` | `CREATE ... IF NOT EXISTS`: database, 6 schemas, warehouse `RETAIL_WH`, 3 roles | Yes, additive only |
| `snowflake/setup/02_grants.sql` | Least-privilege `GRANT`s incl. future grants | Yes, additive only |
| `snowflake/ingestion/file_formats.sql` | CSV file format `RAW.OLIST_CSV`, internal stage `RAW.OLIST_STAGE` | Yes, additive only |
| `snowflake/ingestion/ddl_raw.sql` | 9 RAW tables (all VARCHAR + 4 metadata columns) + `RAW.INGESTION_LOG` | Yes, additive only |
| `snowflake/ingestion/load_raw.py` | Uploads files, `COPY INTO`, verifies counts, writes the log | Writes data into RAW only |

None of the SQL files uses `OR REPLACE` or `DROP` (a test enforces this), none creates a resource monitor,
none touches account-level settings. **`load_raw.py` creates no database objects**: if the tables, stage or
file format are missing it fails with Snowflake's own error. The setup SQL is run separately, by you, after the gate below.

## 2. Approval gate: what the account owner must approve

1. **Run `00_preflight.sql` and read the output.** Check that no `RETAIL_OLIST` database, `RETAIL_WH`
   warehouse or `RETAIL_*` role already exists, and that none belongs to another project (the `.env` in this
   workspace holds variable names that appear to belong to a different project; nothing here reads its values).
   `IF NOT EXISTS` silently does nothing on a name collision, so a collision must be caught here.
2. **Approve creation** of: database `RETAIL_OLIST`; schemas `RAW, STAGING, INTERMEDIATE, MARTS, PBI, ML`;
   warehouse `RETAIL_WH` (XSMALL, auto-suspend 60 s, starts suspended); roles `RETAIL_LOADER`,
   `RETAIL_TRANSFORMER`, `RETAIL_REPORTER`.
3. **Approve the grants** in `02_grants.sql`, in particular `CREATE SCHEMA ON DATABASE` for `RETAIL_TRANSFORMER`
   (needed only by the dbt dev target, which creates `<DBT_DEV_SUFFIX>_STAGING` etc.).
4. **Approve the first `load_raw.py --yes` run.** It uploads about 120 MB of CSV to an internal stage and
   loads about 1.45 M rows; compute is XSMALL for a short time. Any credit figure is an estimate until measured.

If you cannot use `SECURITYADMIN` (no `CREATE ROLE`), use the single-role fallback described at the top of
`01_objects.sql`: skip role creation and `02_grants.sql`, run everything as the one role you have, and set
`RETAIL_SF_ROLE` to it. Least-privilege separation is then not in force.

## 3. Prerequisites

- Python with `snowflake-connector-python` for the loader (`pip install "snowflake-connector-python[pandas]"`;
  the project declares it as the optional `snowflake` extra). It is imported only when a live run connects, so
  `--dry-run` and the tests do not need it.
- Environment variables (set in your shell; never commit them, never put values in this repo):

| Variable | Needed for | Default |
|---|---|---|
| `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER`, `SNOWFLAKE_PRIVATE_KEY_PATH` | live run | none (required) |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | live run, only if the key is encrypted | unset |
| `RETAIL_SF_ROLE` | live run | `RETAIL_LOADER` (this script only; other tools default to `RETAIL_TRANSFORMER`) |
| `RETAIL_SF_WAREHOUSE` / `RETAIL_SF_DATABASE` | live run | `RETAIL_WH` / `RETAIL_OLIST` |
| `RETAIL_DATA_DIR` | everything | `./data`, else a clear error |

  Because `RETAIL_SF_ROLE` is shared with the other tools, check it before loading: if your shell sets it to
  `RETAIL_TRANSFORMER` the load fails (that role cannot write RAW). Pass `--role RETAIL_LOADER` to be explicit.
- Key-pair authentication only. The key file is read by the connector from `SNOWFLAKE_PRIVATE_KEY_PATH`.
  Registering the public key on the Snowflake user is done by the account owner (not covered by these scripts).
- The data folder. The CSVs are git-ignored and not in the repo; on the author's machine they are in
  `C:\Users\Student\GCP\data`. Set `RETAIL_DATA_DIR` (or pass `--data-dir`).

## 4. Procedure

All commands from the repo root. `--dry-run` is safe anywhere: it needs no credentials and never connects.

### 4.0 Dry run (always do this first)

```powershell
$env:RETAIL_DATA_DIR = "C:\Users\Student\GCP\data"
python snowflake\ingestion\load_raw.py --dry-run
```

Checks that all nine files exist, prints each file's record count and sha256, then prints every statement a
real run would issue (PUT with `file://C:/...` forward-slash URIs, TRUNCATE if `--reload`, the transforming
`COPY INTO`, the count check, the log insert). Offline result recorded 2026-11-06: record counts below.

| Table | Records (csv parsing) | Notes |
|---|---:|---|
| CUSTOMERS | 99,441 | |
| GEOLOCATION | 1,000,163 | |
| ORDER_ITEMS | 112,650 | |
| ORDER_PAYMENTS | 103,886 | |
| ORDER_REVIEWS | 99,224 | 104,720 newline characters in the file: embedded newlines in quoted comments |
| ORDERS | 99,441 | |
| PRODUCTS | 32,951 | |
| SELLERS | 3,095 | |
| PRODUCT_CATEGORY_TRANSLATION | 71 | file starts with a UTF-8 BOM (stripped before the header check) |

(The expected row count is always the csv-module record count, never a line count. The task brief quoted
104,719 physical lines for reviews; a raw count of `\n` bytes on the file in `C:\Users\Student\GCP\data` gives 104,720.
Either way it is not 99,224 and is not used.)

### 4.1 First load

1. Run `00_preflight.sql` (Snowsight worksheet or `snow sql -f`), review, get approval (section 2).
2. Run, in order: `01_objects.sql` (parts as `SECURITYADMIN`, then `SYSADMIN`; the file switches roles itself),
   `02_grants.sql`, then as `RETAIL_LOADER`: `ingestion/file_formats.sql`, `ingestion/ddl_raw.sql`.
3. Load:

```powershell
python snowflake\ingestion\load_raw.py --role RETAIL_LOADER          # prints target, stops: needs --yes
python snowflake\ingestion\load_raw.py --role RETAIL_LOADER --yes
```

Per table the loader: looks up a SUCCESS row for this file's sha256 in `RAW.INGESTION_LOG`; checks the RAW table
is empty; `PUT ... OVERWRITE = TRUE`; `COPY INTO` (transforming: `$1..$n`, `METADATA$FILENAME`,
`METADATA$FILE_ROW_NUMBER`, `CURRENT_TIMESTAMP()`, batch id; `ON_ERROR = ABORT_STATEMENT`); `SELECT COUNT(*)`
and compares with the expected record count; inserts a SUCCESS or FAILED row in `RAW.INGESTION_LOG`. It stops
at the first failing table (earlier tables stay loaded and logged).

Success criteria (UNVERIFIED until run): exit code 0, every table `LOADED`, `RAW.INGESTION_LOG` has 9 SUCCESS rows,
and each RAW count equals the table above. Plus a check the loader cannot do for you: all nine source files use
CRLF line endings, and a row count alone would not reveal a stray carriage return left on each record's last field.
Run, per table, and expect 0 (UNVERIFIED):

```sql
SELECT COUNT(*) FROM RAW.CUSTOMERS      WHERE ENDSWITH(customer_state, CHR(13));
SELECT COUNT(*) FROM RAW.GEOLOCATION    WHERE ENDSWITH(geolocation_state, CHR(13));
SELECT COUNT(*) FROM RAW.ORDER_ITEMS    WHERE ENDSWITH(freight_value, CHR(13));
SELECT COUNT(*) FROM RAW.ORDER_PAYMENTS WHERE ENDSWITH(payment_value, CHR(13));
SELECT COUNT(*) FROM RAW.ORDER_REVIEWS  WHERE ENDSWITH(review_answer_timestamp, CHR(13));
SELECT COUNT(*) FROM RAW.ORDERS         WHERE ENDSWITH(order_estimated_delivery_date, CHR(13));
SELECT COUNT(*) FROM RAW.PRODUCTS       WHERE ENDSWITH(product_width_cm, CHR(13));
SELECT COUNT(*) FROM RAW.SELLERS        WHERE ENDSWITH(seller_state, CHR(13));
SELECT COUNT(*) FROM RAW.PRODUCT_CATEGORY_TRANSLATION WHERE ENDSWITH(product_category_name_english, CHR(13));
```

A non-zero count means the record delimiter needs to be set explicitly to `'\r\n'` in `file_formats.sql` (then
`--reload all`). Embedded newlines inside quoted review comments are CRLF in the source and are kept as-is by both
DuckDB and Snowflake; that is not an error.

### 4.2 Re-run (no-op)

Running the same command again with unchanged files issues only `SELECT` statements: each table reports
`SKIPPED`. A table is skipped when (a) the log has a SUCCESS for the file's current sha256 **and** (b) the table
still holds exactly the logged number of records. If (a) holds but (b) does not (someone truncated or modified
the table), the loader stops with an error instead of silently skipping.

### 4.3 Reload

```powershell
python snowflake\ingestion\load_raw.py --role RETAIL_LOADER --yes --reload orders     # one table
python snowflake\ingestion\load_raw.py --role RETAIL_LOADER --yes --reload all
python snowflake\ingestion\load_raw.py --role RETAIL_LOADER --yes --reload orders,sellers --only orders,sellers
```

For each reloaded table: `PUT` first (so a failed upload leaves the old data untouched), then
`TRUNCATE TABLE RAW.<T>`, then `COPY INTO ... FORCE = TRUE`, then the same verification and log row.
**Never DROP.** `FORCE = TRUE` is used only in reload mode so Snowflake's 64-day load-history does not skip
the already-seen staged file (whether `TRUNCATE` clears that history is UNVERIFIED; `FORCE` makes it irrelevant).
Tables not named are processed normally (usually `SKIPPED`).

Use reload when: the source CSV changed (a changed file into a non-empty table is refused, never appended);
a table was altered by hand; or a load was logged FAILED.

### 4.4 Failure and recovery

| Symptom | Meaning | Action |
|---|---|---|
| `ERROR: Data directory not found` / `Missing N expected file(s)` | Nothing attempted, no connection made | Set `RETAIL_DATA_DIR`; make sure all nine files are present |
| `ERROR: Missing environment variable(s)` | Nothing attempted | Set the named variables (values are never printed) |
| Exit 2 after printing the target | `--yes` not given | Check account/role/warehouse/database shown, re-run with `--yes` |
| `COPY` error, e.g. column-count or parse error | `ON_ERROR = ABORT_STATEMENT`: the statement loaded nothing; a FAILED row is logged with `loaded_rows` NULL | Read Snowflake's message; fix the file or `file_formats.sql`; re-run (empty table => loads; non-empty => add `--reload <t>`) |
| `row count mismatch, RAW has X, CSV has Y` | COPY succeeded but the table does not match the local record count; logged FAILED with `loaded_rows = X` | Do not use the table. Investigate (see 4.5), then `--reload <t>` |
| `row count mismatch, RAW has 0 rows` on a first load after the table was emptied by hand | Snowflake's 64-day load history may skip a file it already copied (normal mode does not use `FORCE`) | `--reload <t>` (uses `FORCE = TRUE`) |
| `table already holds N rows but this file's sha256 has no SUCCESS` | File changed since the last load, or an earlier load finished but the log insert did not | `--reload <t>` (truncates and reloads; safe) |
| `the log has a SUCCESS ... but the table holds N rows` | Table was changed after a good load | `--reload <t>` |
| `Object does not exist` / `not authorized` | Setup SQL not run, wrong role | Run section 4.1 step 2 as the right roles; use `--role RETAIL_LOADER` |
| Upload or network error mid-run | Run stops; tables before it are loaded and logged SUCCESS | Re-run the same command: finished tables skip, the rest load |

The log is append-only history: a FAILED row followed later by a SUCCESS row for the same table is normal.

### 4.5 Informational: row numbers and how to investigate a mismatch

`_source_row_number` is `METADATA$FILE_ROW_NUMBER`. For `order_reviews`, whether it counts **records** or
**physical lines** when a quoted field contains line breaks is **UNVERIFIED**; the column is informational
only and nothing in dbt or the reconciliation may depend on it. Use `review_id`/`order_id` for identity.

If a count mismatches, likely suspects (all UNVERIFIED) are quoting/escape settings in `file_formats.sql`
(the real data has literal backslashes in unquoted fields, e.g. `sellers` and `order_reviews`, which is why
`ESCAPE_UNENCLOSED_FIELD = NONE` is set), a record the Python `csv` module and Snowflake parse differently,
or a partial earlier load. Compare with e.g. `SELECT COUNT(*), COUNT(DISTINCT review_id) FROM RAW.ORDER_REVIEWS`.

Note on NULLs: empty fields load as NULL (`EMPTY_FIELD_AS_NULL`, `NULL_IF = ('')`). The text `NULL` is kept as text.
Whether that matches DuckDB's `read_csv` handling column by column is a reconciliation question, not asserted here.

## 5. What is verified, and what is not

**Verified offline (2026-11-06, `pytest tests/test_snowflake_ingestion.py`, fake connector, no Snowflake):**

- Record counting with the `csv` module on a synthetic file with embedded newlines and doubled quotes, and on the
  real reviews file (99,224 records) and all nine real files; BOM stripping; header and field-count validation.
- A missing file, data directory or environment variable fails before any connection is attempted.
- Without `--yes` nothing connects; with `--dry-run` nothing connects and no credentials are needed.
- Statement order PUT -> (TRUNCATE) -> COPY -> COUNT -> log; idempotent skip on matching sha256 (no PUT/COPY/TRUNCATE/INSERT
  on the second run); refusal to append a changed file to a non-empty table; `--reload` emits TRUNCATE (never DROP) and FORCE.
- FAILED is logged for a COPY exception and for a row-count mismatch; re-run after a failure completes without duplicates.
- No passphrase or key content appears in any printed output or executed SQL.
- `00_preflight.sql` contains only `SHOW`/`SELECT`; `01_objects.sql`/`02_grants.sql` contain no `OR REPLACE`/`DROP`;
  `ddl_raw.sql` columns equal the loader's column lists and the real CSV headers.

**UNVERIFIED (needs a live Snowflake run):**

- That any SQL file executes (syntax, privilege requirements, `GRANT ... TO USER IDENTIFIER($VAR)`, role switching).
- The `PUT` result format the loader inspects, and `file://C:/...` URIs with `AUTO_COMPRESS` on this Windows host.
- That `CURRENT_TIMESTAMP()::TIMESTAMP_NTZ` and `METADATA$FILE_ROW_NUMBER` are accepted in a transforming `COPY`, and that
  `ERROR_ON_COLUMN_COUNT_MISMATCH` is enforced there (the loader additionally validates the field count of every record locally).
- That Snowflake parses all nine files into exactly the record counts above (embedded newlines, doubled quotes,
  backslashes, CRLF line endings).
- Load-history/`FORCE` interaction with `TRUNCATE`; `METADATA$FILE_ROW_NUMBER` semantics for multiline records.
- Runtime and credit cost. Any figure quoted elsewhere is an estimate until measured here.

Record the live results (date, command, roles, exit code, the nine counts, elapsed time) in this section when they exist.
