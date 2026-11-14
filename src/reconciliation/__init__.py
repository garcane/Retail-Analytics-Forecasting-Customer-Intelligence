"""DuckDB (reference) vs Snowflake reconciliation. See docs/validation/RECONCILIATION_REPORT.md for the latest real run.

    python -m reconciliation.cli --list
    python -m reconciliation.cli --offline-selftest --duckdb <warehouse.duckdb>      # DuckDB vs DuckDB, no network
    python -m reconciliation.cli --yes --write-report                                  # live Snowflake run (read-only SELECTs)

(`src` must be on the path, as pytest's `pythonpath` does, or run with PYTHONPATH=src.)
"""
