# Reconciliation report: DuckDB vs Snowflake

**Status: NOT RUN.**

No reconciliation against Snowflake has been performed. This file is a placeholder and deliberately contains no
figures: any number that appears here must come from a real run of the tool below, never from an earlier estimate.

## How this file gets replaced

After the Snowflake objects exist, the raw data is loaded and `dbt build` has populated the marts, a person with Snowflake
access runs the reconciliation. It is read-only (single SELECT statements only) and refuses to connect without `--yes`:

```
python -m reconciliation.cli --yes --write-report
```

`--write-report` overwrites this file with a report rendered from the actual results (timestamp, git commit, redacted
account locator, tool versions, per-check status, per-column mismatch counts, max absolute and relative differences,
tie-break counts, surrogate-key comparison, and the headline figures compared three ways: DuckDB, Snowflake and the
documented constant). The renderer refuses to produce a report when there are no results, and an offline self-test
(`--offline-selftest`) refuses to overwrite this file.

## What the tool compares

- All dimension and fact tables, joined on natural keys; surrogate keys are compared and reported separately.
- The analytics marts, against both the DuckDB query output and the tracked CSV files in `reports/analytics`.
- The late-delivery feature table (row-level differences, per-column aggregates, and a classification of
  `arg_max` versus `max_by` tie-breaks), and the weekly orders and revenue series.
- The headline figures: net revenue, net orders, late orders, labelled and late labelled deliveries, and the share of
  one-time customers, as defined in `sql/validation/checks.sql` and `sql/analytics`.

Tolerances: counts, keys, money, booleans, strings, dates and timestamps must match exactly; floating-point values match
to a relative tolerance; great-circle distance and rates use absolute tolerances. See `src/reconciliation/checks.py`.

Until a live run exists, the Snowflake side of every check is UNVERIFIED.
