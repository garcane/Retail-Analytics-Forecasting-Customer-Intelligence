"""Export the warehouse, the model scores and the forecast backtests as files Power BI can load.

Parquet for the large fact tables and the per-order scores (small, typed); CSV for the dimensions and the small tables.
Everything lands in powerbi/data/ (git-ignored, regenerable) with a manifest of row counts that the tests check.
Review comment text is deliberately not exported: no analysis uses it and it is free text written by customers.

    uv run python src/powerbi/export_data.py [--db warehouse.duckdb] [--out powerbi/data]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src" / "ml"))
import export_scores  # noqa: E402
import forecast_baseline as fb  # noqa: E402
import forecast_models as fm  # noqa: E402

# Derived columns keep the DAX short and tie it to the SQL definitions used everywhere else in the project:
#   is_net_order          not canceled or unavailable (and, on fact_orders, has items): sql/analytics/01, 03, 07
#   is_labelled_delivery  delivered, has a late/on-time label, no timestamp anomaly: the population of the ML features
#   promised_days         the promise shown at checkout, in days
#   delay_bucket          delivered orders only, same buckets as sql/analytics/05_delivery_vs_reviews.sql
FACT_SQL = {
    "fact_orders": """
        select order_id, order_status, customer_key, customer_geography_key,
               purchase_date_key, approved_date_key, carrier_date_key, delivered_customer_date_key, estimated_delivery_date_key,
               purchase_ts, estimated_delivery_ts, item_count, items_price, items_freight, payment_count, payment_total,
               delivery_days, delivery_delay_days, is_late, has_timestamp_anomaly,
               date_diff('second', purchase_ts, estimated_delivery_ts) / 86400.0 as promised_days,
               (order_status not in ('canceled', 'unavailable') and item_count > 0) as is_net_order,
               (order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly) as is_labelled_delivery,
               case when order_status <> 'delivered' or delivery_delay_days is null then null
                    when delivery_delay_days <= 0  then 'on time or early'
                    when delivery_delay_days <= 3  then '1-3 days late'
                    when delivery_delay_days <= 7  then '4-7 days late'
                    when delivery_delay_days <= 14 then '8-14 days late'
                    else 'more than 14 days late' end as delay_bucket,
               case when order_status <> 'delivered' or delivery_delay_days is null then null
                    when delivery_delay_days <= 0  then 1 when delivery_delay_days <= 3 then 2
                    when delivery_delay_days <= 7  then 3 when delivery_delay_days <= 14 then 4 else 5 end as delay_bucket_order
        from fact_orders order by order_id""",
    "fact_order_items": """
        select *, (order_status not in ('canceled', 'unavailable')) as is_net_order
        from fact_order_items order by order_id, order_item_id""",
    "fact_payments": "select * from fact_payments order by order_id, payment_sequential",
    "fact_reviews": """
        select review_id, order_id, customer_key, review_creation_date_key, review_answer_date_key, review_creation_ts,
               review_answer_ts, review_score, has_comment, is_latest_review_for_order
        from fact_reviews order by review_id, order_id""",
}
DIMENSIONS = ["dim_date", "dim_customer", "dim_product", "dim_seller", "dim_geography"]
FLAG_SHARES = [5, 10, 15, 20, 25, 30]


def forecast_backtest(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    """Long format: one row per (target, horizon, method, target week); 'actual' is included as a method for plotting."""
    weekly = fb.weekly_series(con)
    main = weekly.loc[fb.FIRST_WEEK:fb.LAST_CLEAN_WEEK]
    parts = []
    for target in ("orders", "revenue"):
        for horizon in fb.HORIZONS:
            bt = fb.backtest(main[target], horizon, fm.MODELS)
            for method in fm.MODELS:
                parts.append(pd.DataFrame({
                    "target": target, "horizon": horizon, "method": method, "target_week": bt.index,
                    "forecast": bt[method].to_numpy(), "actual": bt["actual"].to_numpy(),
                }))
            parts.append(pd.DataFrame({
                "target": target, "horizon": horizon, "method": "actual", "target_week": bt.index,
                "forecast": bt["actual"].to_numpy(), "actual": bt["actual"].to_numpy(),
            }))
    out = pd.concat(parts, ignore_index=True)
    out["abs_error"] = (out["forecast"] - out["actual"]).abs()
    out["target_week"] = pd.to_datetime(out["target_week"]).dt.date
    return out


def export(db: Path, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db), read_only=True)
    manifest: dict[str, dict] = {}

    for name, sql in FACT_SQL.items():
        path = out / f"{name}.parquet"
        con.execute(f"copy ({sql}) to '{path.as_posix()}' (format parquet)")
        manifest[name] = {"file": path.name, "format": "parquet", "rows": con.execute(f"select count(*) from read_parquet('{path.as_posix()}')").fetchone()[0]}

    for name in DIMENSIONS:
        path = out / f"{name}.csv"
        con.execute(f"copy (select * from {name} order by 1) to '{path.as_posix()}' (format csv, header true)")
        manifest[name] = {"file": path.name, "format": "csv", "rows": con.execute(f"select count(*) from {name}").fetchone()[0]}

    scores = export_scores.build(db)
    scores_path = out / "late_delivery_scores.parquet"
    scores.to_parquet(scores_path, index=False)
    manifest["late_delivery_scores"] = {"file": scores_path.name, "format": "parquet", "rows": len(scores)}

    backtest = forecast_backtest(con)
    con.close()
    backtest_path = out / "forecast_backtest.csv"
    backtest.to_csv(backtest_path, index=False)
    manifest["forecast_backtest"] = {"file": backtest_path.name, "format": "csv", "rows": len(backtest)}

    flag_path = out / "flag_share.csv"
    pd.DataFrame({"flag_pct": FLAG_SHARES}).to_csv(flag_path, index=False)
    manifest["flag_share"] = {"file": flag_path.name, "format": "csv", "rows": len(FLAG_SHARES)}

    (out / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "powerbi" / "data")
    args = parser.parse_args()
    manifest = export(args.db, args.out)
    for name, m in manifest.items():
        size = (args.out / m["file"]).stat().st_size / 1024
        print(f"  {name:<22} {m['format']:<8} {m['rows']:>9,} rows {size:>9,.0f} KB")
    print(f"wrote {len(manifest)} tables to {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
