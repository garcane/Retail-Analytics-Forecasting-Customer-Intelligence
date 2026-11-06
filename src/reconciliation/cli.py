"""Command line for the DuckDB-vs-Snowflake reconciliation.

    python -m reconciliation.cli --list
    python -m reconciliation.cli --offline-selftest [--duckdb PATH] [--checks a,b] [--groups fact,analytics]
    python -m reconciliation.cli --yes [--duckdb PATH] [--database DB] [--schema-suffix SUFFIX] [--write-report]

A live run opens a Snowflake connection, so it prints what it would connect to and refuses unless ``--yes`` is given.
It only ever sends single SELECT / WITH statements (enforced in ``fetch.assert_read_only``). Credentials come from the
environment (SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PRIVATE_KEY_PATH, optional SNOWFLAKE_PRIVATE_KEY_PASSPHRASE,
RETAIL_SF_ROLE / RETAIL_SF_WAREHOUSE / RETAIL_SF_DATABASE); the account locator is printed redacted, the user never.

Exit codes: 0 every check passed (tie-break-classified differences count as passed but are printed), 1 at least one
check failed or errored, 2 refused or bad usage.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import checks as checks_mod
from .compare import CheckResult, duckdb_side, run_checks, snowflake_side
from .fetch import DuckDBFetcher, SnowflakeFetcher, redact_secrets, resolve_snowflake_settings
from .report import DEFAULT_REPORT_PATH, ReconciliationRun, ReportError, collect_run_metadata, write_report


def _split(value: str | None) -> list[str] | None:
    return [v.strip() for v in value.split(",") if v.strip()] if value else None


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="reconciliation", description=__doc__.split("\n\n")[0])
    p.add_argument("--list", action="store_true", help="list the registered checks and exit")
    p.add_argument("--offline-selftest", action="store_true",
                   help="run DuckDB against DuckDB (no network, no Snowflake) to exercise the machinery and the SQL")
    p.add_argument("--yes", action="store_true", help="confirm that a live Snowflake connection may be opened")
    p.add_argument("--duckdb", type=Path, help="DuckDB file (default: $DUCKDB_PATH, then ./warehouse.duckdb); opened read-only")
    p.add_argument("--reference-dir", type=Path, default=checks_mod.REFERENCE_DIR,
                   help="directory with the tracked reports/analytics/NN_*.csv")
    p.add_argument("--checks", help="comma-separated check names (default: all)")
    p.add_argument("--groups", help="comma-separated groups: dimension, fact, headline, analytics, ml")
    p.add_argument("--database", help="Snowflake database (default: $RETAIL_SF_DATABASE or RETAIL_OLIST)")
    p.add_argument("--schema-suffix", help="dbt dev schema suffix (default: $DBT_DEV_SUFFIX); marts are read from <SUFFIX>_MARTS")
    p.add_argument("--write-report", action="store_true",
                   help="write the Markdown report (live runs: docs/validation/RECONCILIATION_REPORT.md)")
    p.add_argument("--report-path", type=Path, help="report destination (required with --write-report in a self-test)")
    return p


def _resolve_duckdb(arg: Path | None) -> Path:
    path = arg or Path(os.environ.get("DUCKDB_PATH") or checks_mod.ROOT / "warehouse.duckdb")
    if not path.exists():
        raise FileNotFoundError(f"DuckDB file not found: {path} (use --duckdb or DUCKDB_PATH)")
    return path


def _print_progress(r: CheckResult) -> None:
    p = r.primary
    detail = r.error or (f"{p.matched_rows} matched, {p.missing_in_right} missing, {p.extra_in_right} extra, "
                         f"{p.n_unexplained} unexplained diffs, {p.n_tolerated} classified" if p else "")
    print(f"  [{r.status:<20}] {r.check_name:<42} {r.elapsed_s:6.1f}s  {detail}", flush=True)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        selected = checks_mod.select_checks(_split(args.checks), _split(args.groups))
    except KeyError as exc:
        print(f"error: {exc.args[0]}", file=sys.stderr)
        return 2

    if args.list:
        for c in selected:
            print(f"{c.group:<10} {c.name:<42} keys={','.join(c.keys)}")
        return 0

    if args.offline_selftest and args.yes:
        print("choose either --offline-selftest (no network) or --yes (live Snowflake run), not both", file=sys.stderr)
        return 2
    if not args.offline_selftest and not args.yes:
        try:
            s = resolve_snowflake_settings(database=args.database, schema_suffix=args.schema_suffix)
            print(f"would connect to account {s.account_redacted}, database {s.database}, role {s.role}, "
                  f"warehouse {s.warehouse}", file=sys.stderr)
        except (RuntimeError, ValueError) as exc:
            print(f"(target not resolvable: {exc})", file=sys.stderr)
        print("refusing to connect to Snowflake without --yes (use --offline-selftest for a no-network run)",
              file=sys.stderr)
        return 2
    if args.write_report and args.offline_selftest and args.report_path is None:
        print("refusing: --write-report with --offline-selftest needs --report-path (the shipped report is reserved "
              "for a real Snowflake run)", file=sys.stderr)
        return 2
    if args.report_path is not None and args.offline_selftest and \
            args.report_path.resolve() == DEFAULT_REPORT_PATH.resolve():
        print("refusing: a self-test may not overwrite docs/validation/RECONCILIATION_REPORT.md", file=sys.stderr)
        return 2

    try:
        duck_path = _resolve_duckdb(args.duckdb)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.offline_selftest:
        print(f"OFFLINE SELF-TEST: DuckDB {duck_path.name} (read-only) against itself; Snowflake is not contacted.")
        left = DuckDBFetcher(duck_path)
        left_side, right_side = duckdb_side(left), duckdb_side(left, name="duckdb (self-test)")
        settings = None
        meta = collect_run_metadata("selftest", left_description=left.description,
                                    right_description=left.description + " (self-test)")
        closers = [left]
    else:
        try:
            settings = resolve_snowflake_settings(database=args.database, schema_suffix=args.schema_suffix)
        except (RuntimeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print("Live reconciliation target (read-only SELECTs):")
        print(f"  account   {settings.account_redacted}")
        print(f"  database  {settings.database}   marts schema {settings.schema_prefix}MARTS")
        print(f"  role      {settings.role}")
        print(f"  warehouse {settings.warehouse}")
        print(f"  duckdb    {duck_path.name} (read-only)")
        try:
            sf = SnowflakeFetcher(settings)
        except Exception as exc:  # noqa: BLE001
            first = (str(exc).splitlines() or [""])[0]
            print("error: could not connect: " + redact_secrets(f"{type(exc).__name__}: {first}"), file=sys.stderr)
            return 2
        left = DuckDBFetcher(duck_path)
        left_side = duckdb_side(left)
        right_side = snowflake_side(sf, settings.database, settings.schema_prefix)
        meta = collect_run_metadata("snowflake", settings=settings, left_description=left.description,
                                    right_description=sf.description)
        closers = [left, sf]

    try:
        print(f"Running {len(selected)} checks")
        results = run_checks(selected, left_side, right_side, reference_dir=args.reference_dir,
                             progress=_print_progress)
    finally:
        for c in closers:
            c.close()

    run = ReconciliationRun(meta, results)
    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    print("Summary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    for r in results:
        for t in r.tie_breaks:
            print(f"  tie-break {r.check_name}/{t.name}: {t.n_ambiguous_orders} ambiguous orders, "
                  f"{t.n_direct} picked-column diffs, {t.n_downstream} downstream diffs (counted, not hidden)")

    if args.write_report:
        try:
            path = write_report(run, args.report_path)
        except ReportError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        print(f"wrote {path}")
    return 0 if all(r.status in {"PASS", "PASS_WITH_TIE_BREAKS"} for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
