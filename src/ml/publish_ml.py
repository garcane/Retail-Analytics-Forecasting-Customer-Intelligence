"""Compute the ML outputs from Snowflake and publish them to the ML schema, for Power BI and other consumers.

    python src/ml/publish_ml.py                    # prints the Snowflake target and stops
    python src/ml/publish_ml.py --yes              # computes and validates the three outputs; writes nothing
    python src/ml/publish_ml.py --yes --write      # ... and writes them to ML.* under one new run_id

Outputs, all from the Snowflake marts (the same code paths as the DuckDB files under powerbi/data/):
    ML.LATE_DELIVERY_SCORES  out-of-time v1 risk scores for the six test months (export_scores.build_from)
    ML.FORECAST_BACKTEST     rolling-origin forecasts, horizons 1 and 4 weeks (export_data.forecast_backtest)
    ML.FLAG_SHARE            the flag shares the Power BI risk page offers

Every table gets the same run_id (UTC time + random suffix). Earlier runs are kept; consumers read the latest run_id
(the Power BI templates do). Writing a run is atomic per table (src/data_access/writeback.py). Re-publish an
existing run_id with --run-id to replace its rows; only the generated form is accepted, because consumers take the
text-greatest run_id as the latest. --write is required (FORECAST_WRITEBACK=1 is not enough here), so
a dry run is the default.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for sub in ("src", "src/ml", "src/powerbi"):
    if str(ROOT / sub) not in sys.path:
        sys.path.insert(0, str(ROOT / sub))

import export_data  # noqa: E402  (src/powerbi)
import pandas as pd  # noqa: E402
import export_scores  # noqa: E402
from data_access import connect, writeback  # noqa: E402
from data_access.backend import ConfirmationRequired, DataAccessError, MissingConfigError  # noqa: E402


def compute(db) -> dict:
    """The three frames, validated against the write-back schemas (nothing is written)."""
    scores = export_scores.build_from(db)
    backtest = export_data.forecast_backtest(db)
    flags = pd.DataFrame({"flag_pct": list(writeback.FLAG_SHARES)})
    frames = {"LATE_DELIVERY_SCORES": scores, "FORECAST_BACKTEST": backtest, "FLAG_SHARE": flags}
    for table, df in frames.items():
        writeback._prepare(table, df, "validate")  # raises SchemaError on a missing column or wrong dtype
    return frames


def written_rows(db, run_id: str) -> dict[str, int]:
    """Row counts per table for one run_id, read back from Snowflake."""
    out = {}
    for table in writeback.TABLE_COLUMNS:
        sql = f"select count(*) as n from {writeback._qualified(db, table, writeback.ML_SCHEMA)} where run_id = ?"
        out[table] = int(db.read_sql(sql, [run_id])["n"].iloc[0])
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--yes", action="store_true", help="confirm the printed Snowflake target and connect")
    parser.add_argument("--write", action="store_true", help="write to ML.* (default: compute and validate only)")
    parser.add_argument("--run-id", default=None,
                        help="an existing run_id, as printed by an earlier publish, to replace its rows (default: a new one)")
    args = parser.parse_args(argv)
    if args.run_id is not None and not writeback.GENERATED_RUN_ID.match(args.run_id):
        parser.error(f"--run-id must be a run_id printed by an earlier publish (YYYYMMDDTHHMMSSZ-xxxxxxxx), got "
                     f"{args.run_id!r}: consumers take the text-greatest run_id as the latest, so any other form "
                     "could hide every later run")
    try:
        db = connect("snowflake", confirm=args.yes)
    except (ConfirmationRequired, MissingConfigError) as exc:
        print(exc, file=sys.stderr)
        return 1
    with db:
        frames = compute(db)
        scores = frames["LATE_DELIVERY_SCORES"]
        flagged = scores[scores["flagged_top10"]]
        print(f"LATE_DELIVERY_SCORES {len(scores):>7,} rows ({scores['month'].nunique()} months; late rate "
              f"{scores['is_late'].mean():.3f}, flagged {len(flagged):,} with late rate {flagged['is_late'].mean():.3f})")
        print(f"FORECAST_BACKTEST    {len(frames['FORECAST_BACKTEST']):>7,} rows")
        print(f"FLAG_SHARE           {len(frames['FLAG_SHARE']):>7,} rows")
        if not args.write:
            print("dry run: nothing written (add --write to publish)")
            return 0
        run_id = args.run_id or writeback.new_run_id()
        for table, df in frames.items():
            n = writeback.write_table(db, table, df, run_id, enabled=True)
            print(f"wrote {n:,} rows to {writeback.ML_SCHEMA}.{table}")
        check = written_rows(db, run_id)
        expected = {t: len(df) for t, df in frames.items()}
        if check != expected:
            raise DataAccessError(f"read-back mismatch for run_id {run_id}: {check} vs expected {expected}")
        print(f"run_id {run_id}: read back {check}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
