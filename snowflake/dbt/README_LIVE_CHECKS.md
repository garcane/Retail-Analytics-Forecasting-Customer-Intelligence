# Live verification checklist (dbt base: staging, intermediate, core marts)

Nothing in this project has been run against Snowflake. Everything below is UNVERIFIED until someone runs it live.

## What was verified offline (2026-11-06)

| Check | Command / method | Result |
|---|---|---|
| `dbt deps` | `dbt deps --target ci` (hub.getdbt.com; no Snowflake) | dbt_utils 1.4.1 installed. Needed Windows root certificates exported to a PEM and passed through `REQUESTS_CA_BUNDLE` because this host's TLS inspection breaks the default certifi bundle. |
| `dbt parse` | `dbt parse --target ci` with no `SNOWFLAKE_*`/`RETAIL_*` set, `HTTP(S)_PROXY=http://127.0.0.1:9` (dead proxy) | Succeeds in ~10 s: 23 models, 169 data tests, 9 sources. The only warning is `models.retail_olist.pbi` matching no resources yet (disappears when models/pbi gets models). No deprecation warnings. |
| No connection opened by parse | dead proxy + `logs/dbt.log` | parse succeeds under a proxy that refuses every connection; `dbt.log` has no connection-open lines. |
| `dbt compile --no-populate-cache` | same dead proxy, `--target ci` | Succeeds, exit 0, no connection opened; writes 23 model + 169 test SQL files to `target/compiled`. |
| Targets | `dbt parse` with dummy env on `prod`, `dev`, `dev` + `DBT_DEV_SUFFIX=ALICE` | prod schemas `STAGING/INTERMEDIATE/MARTS`; dev `DBT_DEV_*`; suffix honoured (`ALICE_*`). Views for staging/intermediate, tables for marts. |
| dbt versions | `dbt parse` on 1.10.23 and 1.11.17 | both parse identically; 1.10 prints a "deprecated" notice on every command, hence the 1.11 pin. 1.12.x not tried. |
| SQL syntax lint | `sqlglot.parse(sql, read='snowflake')` on all 192 compiled files | 0 failures. This is a syntax lint only. |
| Logic simulation (NOT Snowflake) | compiled SQL transpiled to DuckDB with sqlglot, run on the real CSVs loaded as all-VARCHAR RAW tables | All 23 models build. The 5 dimensions and 4 facts are identical to the reference `warehouse.duckdb` tables (row counts, every column, `EXCEPT` both ways; floats within 1e-9). All 169 tests pass. Re-run with 5 injected defects (dropped item row, payment +1, flipped `is_late`, deleted calendar day, un-flagged latest review): 14 tests fail as expected. |

The simulation proves the *logic* (joins, tie-breaks, key assignment, rounding) matches DuckDB. It does not prove
Snowflake function semantics; those are the live checks below.

## Needs live verification

Setup / access
1. Key-pair login with an **empty** `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` and an unencrypted PKCS#8 key. profiles.yml passes `private_key_passphrase: ''`; dbt-snowflake may treat the empty string as "no passphrase" or try to decrypt. If it errors, drop the field for unencrypted keys.
2. `RETAIL_TRANSFORMER` can read `RAW`, create views/tables in `STAGING/INTERMEDIATE/MARTS/PBI` (and the dev-prefixed schemas), and use `RETAIL_WH`.
3. `generate_schema_name` result in a real dev run (`DBT_DEV_STAGING`, ...) and prod (`STAGING`, ...).
4. The compile result above used dummy credentials, so no Snowflake-side name resolution has happened.

Function semantics (each is a place where Snowflake could differ from DuckDB)
5. `to_timestamp_ntz(nullif(col,''), 'YYYY-MM-DD HH24:MI:SS')`: all timestamp values in the 9 CSVs match this exact pattern (checked offline on the CSVs: 0 non-matching, empties only in the nullable order columns), but the Snowflake call itself is unrun.
6. `RAW` empty-field handling: staging applies `nullif(col,'')` so it is correct whether the loader stored NULL or `''`. Confirm no column relies on a quoted empty string.
7. `MEDIAN(float)` parity for `dim_geography.latitude/longitude`: compare to the DuckDB values at 1e-6 (DuckDB's median interpolates; Snowflake's MEDIAN of FLOAT should as well).
8. Binary collation for the `city`/`state` tie-breaks and for `row_number() over (order by customer_unique_id | product_id | seller_id | zip_prefix)`. The Snowflake default is binary (code-point) order, as in DuckDB. If an account/database default `COLLATION` is set, surrogate keys would shift.
9. `weekiso(d)`: 2016-01-01 must be ISO week 53 (DuckDB value). `dayofweekiso`: 1 = Monday. Check `WEEK_OF_YEAR_POLICY` does not affect `weekiso` (it should not).
10. `dim_date`: `GENERATOR(rowcount => 10000)` + `row_number() over (order by seq4())` yields 1,827 dated rows + the -1 row = 1,828, 2016-01-01..2020-12-31.
11. `datediff(second, a, b)::float / 86400.0` equals the DuckDB `delivery_days` / `delivery_delay_days` (the simulation matched to 0.0 abs difference, DOUBLE vs FLOAT should be identical).
12. `NUMBER(12,2)` sums: `sum()` widens to `NUMBER(38,2)`; models cast back to `NUMBER(12,2)`. Confirm the exact-money singular tests pass (they compare sums without tolerance).
13. `NULLS LAST` under `DESC` in `int_customers_latest` and `fact_reviews.is_latest_review_for_order` produces the same latest row as DuckDB (the simulation only exercised DuckDB's own NULL ordering, so this is not a Snowflake test).
14. `row_number() ... = 1` evaluated directly as a boolean select expression in `fact_reviews`.
15. `qualify row_number() over (partition by zip_prefix order by n desc, state) = 1` in `int_geography_rollup`; the NULL-state group sorts last with `ORDER BY ... state` (ascending default NULLS LAST) as in DuckDB.
16. Column types in Snowflake: INTEGER columns land as `NUMBER(38,0)`, BIGINT the same; FLOAT is double precision. Downstream (Power BI / Python) normalisation must not assume width.

dbt behaviour
17. `dbt build` end to end: runtime, warehouse credits (measure, do not estimate), test results. All 169 tests, including the three extra guards: `assert_dim_date_covers_all_used_dates`, `assert_unknown_members_present`, `assert_fact_order_items_unknown_keys_only_when_unmatched`.
18. Singular test 20 (`customer zip not in dim_geography -> -1`) uses an anti-join, not the original `NOT IN`; verify the count equals the DuckDB value (`NOT IN` ignores NULL zips; if there are none the two agree).
19. `relationships` tests rely on the -1 members existing in every dimension; confirm `assert_unknown_members_present` passes.

## Known non-live caveats

- The data tests (`unique`, `relationships`, ...) replace the PK/FK constraints DuckDB enforces; they only run on `dbt test`/`dbt build`.
- EDA constants (7,827 late; 166/189 anomalies; 96,282 labelled) are deliberately not thresholds in dbt; the reconciliation workstream compares them against the DuckDB values.
- `dbt parse` currently warns once about `models.retail_olist.pbi`: no model exists under `models/pbi/` yet.


## Late-delivery feature models (A3c): `int_late_delivery_*`, `mart_late_delivery_features`

Offline status (2026-11-06). NOTHING here has run on Snowflake.

| Check | Method | Result |
|---|---|---|
| `dbt parse` / `compile --no-populate-cache`, `--target ci`, dead proxy, no `SNOWFLAKE_*`/`RETAIL_*` env | `--target-path target_a3c` (private target dir) | passes; also with `--vars '{late_delivery_history_method: range_join}'`; an invalid value raises a compiler error |
| sqlglot 30.30.0 `read='snowflake'` lint | all compiled files of the 4 intermediate models, the mart, their generic tests and the 3 new singular tests, both ASOF and fallback variants | 0 failures. sqlglot DOES parse `ASOF JOIN ... MATCH_CONDITION (...)` (it builds a Join with method=ASOF), but it cannot transpile it to DuckDB; the simulation rewrites it by regex. Lint only, not proof of Snowflake semantics |
| Logic simulation (NOT Snowflake) | compiled SQL -> DuckDB (sqlglot) on the real CSVs; ASOF rewritten to DuckDB `ASOF LEFT JOIN`; ancestors of the mart built | all 25 models build; mart has 96,282 rows. All 194 tests in that lineage pass, incl. the 3 new singular tests |
| Column list / order vs `sql/ml/late_delivery_features.sql` | `describe` on read-only `warehouse.duckdb` vs simulated mart | identical: 32 columns, same names, same order. Types differ only where DuckDB returns HUGEINT (6 count columns, `total_weight_g`); the models cast to BIGINT / NUMBER(38,0) |
| Values vs the DuckDB query | reference = the DuckDB query with the same tie-break rule as the models; `EXCEPT` both ways on the 26 non-float columns, floats within 1e-9 relative | 0 differing rows, 0 differing columns, 96,282 rows both sides |
| Values vs the UNMODIFIED DuckDB query | same comparison | differs only in `category_prior_n` (26,470 orders) and `category_prior_late` (11,516 orders), caused by `arg_max(category, price)` ties (see below). Max abs diff 7,350 (a tied order whose own category pick moves it between a large and a small category); mean 2.97 |
| Leakage scenarios | the 10 SQL scenarios of `tests/test_feature_leakage.py` run against the compiled models on the repo's `MiniWarehouse` (pytest stubbed: the repo venv has no pytest) | 10/10 pass (strict `>`, same-instant, 28-day boundaries, 5-order seller rule, anomalies excluded). With `>` mutated to `>=` the same-instant scenario fails |
| Fallback == ASOF | both variants run on a 19-day purchase window (2,124 orders; 836 of them with no earlier route history, so the "left join keeps unmatched rows" case is exercised) | `EXCEPT` both ways = 0 rows, floats bit-identical |
| Mutation check on the singular tests | `>` -> `>=` in the history; `<` -> `<=` in the seller history; seller history without the self guard and with future orders | the matching singular test fails each time (286 / 4 / 96,278 offending rows) |

Needs live verification (Snowflake itself)

20. **`ASOF JOIN ... MATCH_CONDITION` in `int_late_delivery_history`** (the highest risk in this workstream). Check: (a) the syntax is accepted, four chained ASOF joins in one query included; (b) `ON` may be omitted for the system-wide lookups (`cum_all`); (c) the strict `>` operator is accepted and picks the LATEST right-hand row strictly before the left timestamp; (d) unmatched left rows are KEPT (an order with no earlier delivery must still appear, with NULL totals that the model coalesces to 0) - singular test `assert_late_delivery_one_row_per_population_order_with_items` fails if ASOF behaves as an inner join; (e) a MATCH_CONDITION between two TIMESTAMP_NTZ columns, the 28-day side using the precomputed `purchase_ts_minus_28d` column. If any of these fails, run the fallback: `dbt build -s +mart_late_delivery_features --vars '{late_delivery_history_method: range_join}'`. The fallback is semantically identical (verified offline on a window) but quadratic on the system-wide lookups (about 96k x 48k candidate rows before `qualify`), so measure its runtime and credits before relying on it.
21. `row_number()` / `sum() over (... rows between unbounded preceding and current row)` windows and `qualify` with `nulls last` in the fallback behave as in DuckDB.
22. **`arg_max` tie-break (intentional difference).** `int_late_delivery_item_agg.category` and the payment pick in the mart break ties alphabetically instead of DuckDB's arbitrary pick. In `warehouse.duckdb` 57 of 96,282 orders have a price tie across different categories (0 payment ties across types). DuckDB's own pick on these ties is stable across thread counts but matches none of: alphabetical first/last, lowest/highest `order_item_id`. Live reconciliation should therefore show differences in `category_prior_n` / `category_prior_late` only (about 26k / 11.5k orders against the current `warehouse.duckdb`, mostly +-1, up to a few thousand for the tied orders themselves) and nothing else; any other column differing is a real defect.
23. Runtime of the seller-keyed range join in `int_late_delivery_seller_history` (equality on seller + `delivered_customer_ts < purchase_ts`) on XSMALL; DuckDB does it in about 1 s. Measure, do not estimate.
24. `MAX`/`SUM` over FLOAT: `route_prior_days` and `recent_days_28d` are running float sums; Snowflake and DuckDB may accumulate in different orders, so expect agreement to about 1e-9 relative, not bit equality. `freight_ratio` and `promised_days` are computed in FLOAT in both.
25. `haversine` (`asin`, `power`, `radians`) on FLOAT agrees with DuckDB `distance_km` at the plan's 1e-6 km tolerance.
26. Singular test cost: `assert_late_delivery_history_is_point_in_time` cross-joins about 400 sampled orders with the 96k population (a few tens of millions of row pairs); `assert_late_delivery_seller_history_excludes_self` re-runs the seller range join. Both are cheap in DuckDB (1-6 s); confirm on XSMALL.
27. Row order: the mart keeps `order by purchase_ts, order_id` but Snowflake does not guarantee read order; readers (`src/data_access`) must `ORDER BY purchase_ts, order_id` themselves.
