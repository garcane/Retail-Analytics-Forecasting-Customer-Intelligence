"""Build the JSON data files behind the HTML dashboard (dashboard/).

The dashboard is static: HTML + CSS + ES-module JavaScript that reads dashboard/data/*.json. This script is the only
place that touches the warehouse. It combines

* the tracked analytical outputs     reports/analytics/*.csv (the eight business queries)
* the tracked model outputs          reports/*.json (late-delivery backtest, explainability, recalibration, drift,
                                     forecast metrics)
* live aggregates from the warehouse headline KPIs, the weekly series, per-week forecast backtests and, on DuckDB,
                                     the out-of-time risk scores rolled up by decile, state and flag share

and writes one JSON file per dataset plus manifest.json, which lists every dataset with its source and row count.
Only aggregates are written: no order-level rows, no review text.

    uv run python src/dashboard/build_data.py --yes                 # default: Snowflake marts (RETAIL_OLIST.MARTS)
    uv run python src/dashboard/build_data.py --backend duckdb      # offline fallback: the DuckDB reference warehouse
    python -m http.server 8000 --directory dashboard                # then open http://localhost:8000

The default source is Snowflake (DD-22): the dbt marts, read through src/data_access with the key-pair credentials in
the environment (see snowflake/README.md; --yes confirms the printed target). The DuckDB path needs no credentials and
produces the same figures (the live reconciliation shows 0 differences); set DASHBOARD_BACKEND=duckdb to make it the
default locally. The risk roll-ups retrain the v1 model per test month on whichever backend is used.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for sub in ("src", "src/ml", "src/powerbi"):
    if str(ROOT / sub) not in sys.path:
        sys.path.insert(0, str(ROOT / sub))

REPORTS = ROOT / "reports"
ANALYTICS = {  # dataset id -> tracked CSV (sql/analytics/NN_*.sql output)
    "monthly_kpis": "01_monthly_kpis.csv",
    "category_performance": "02_category_performance.csv",
    "state_performance": "03_state_performance.csv",
    "seller_concentration": "04_seller_concentration.csv",
    "delivery_vs_reviews": "05_delivery_vs_reviews.csv",
    "payments": "06_payments.csv",
    "repeat_customers": "07_repeat_customers.csv",
    "delivery_trend": "08_delivery_trend.csv",
}
FLAG_SHARES = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30)


# ---------------------------------------------------------------------------------------------------------- helpers
def clean(value):
    """JSON-safe: NaN/inf -> None, numpy scalars -> Python, timestamps -> ISO strings."""
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if value is pd.NA or value is pd.NaT:
        return None
    if hasattr(value, "item") and not isinstance(value, (str, bytes)):
        try:
            value = value.item()
        except (ValueError, AttributeError):
            pass
    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else round(value, 6)
    if isinstance(value, (pd.Timestamp, dt.datetime, dt.date)):
        return value.isoformat()[:10] if isinstance(value, dt.date) and not isinstance(value, dt.datetime) else value.isoformat()
    return value


def records(df: pd.DataFrame) -> list[dict]:
    return clean(df.to_dict(orient="records"))


def git_sha() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def read_json(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


# --------------------------------------------------------------------------------------------- tracked outputs
def analytics_tables(con=None, schema: str = "") -> dict:
    """The eight business tables. From the Snowflake marts (MARTS.mart_<key>) when `con` is a Snowflake connection,
    otherwise from the tracked CSVs written by the DuckDB pipeline. Snowflake tables have no row order, so rows are put
    in the CSV's key order (its first column); the columns and their order are the CSV's (the marts reconcile 0-diff)."""
    from data_access.normalise import normalise_frame

    out = {}
    for key, file in ANALYTICS.items():
        ref = pd.read_csv(REPORTS / "analytics" / file)
        if con is None or getattr(con, "backend", "duckdb") != "snowflake":
            out[key] = {"source": f"reports/analytics/{file}", "columns": list(ref.columns), "rows": records(ref)}
            continue
        df = normalise_frame(con.read_sql(f"select * from {schema}mart_{key}"))
        missing = [c for c in ref.columns if c not in df.columns]
        if missing:
            raise ValueError(f"{schema}mart_{key} lacks columns {missing} that reports/analytics/{file} has")
        df = df[list(ref.columns)]
        k = ref.columns[0]
        order = {str(v): i for i, v in enumerate(ref[k])}
        df = df.assign(_o=df[k].astype(str).map(order).fillna(len(order))).sort_values(["_o", k]).drop(columns="_o")
        out[key] = {"source": f"Snowflake {schema}mart_{key}", "columns": list(ref.columns), "rows": records(df)}
    return out


def model_outputs() -> dict:
    ld = read_json("late_delivery_metrics.json")
    ex = read_json("explainability_metrics.json")
    rc = read_json("recalibration_metrics.json")
    dr = read_json("drift_metrics.json")
    calib = {k.removeprefix("calibration_"): v for k, v in ld.items() if k.startswith("calibration_")}
    return {
        "late_delivery": {
            "source": "reports/late_delivery_metrics.json (src/ml/late_delivery_baseline.py)",
            "macro_average": ld["macro_average"],
            "per_month": ld["per_month"],
            "calibration": calib,
            "other": {k: v for k, v in ld.items() if k not in ("macro_average", "per_month") and not k.startswith("calibration_")},
        },
        "explainability": {"source": "reports/explainability_metrics.json (src/ml/explain_late_delivery.py)", **ex},
        "recalibration": {"source": "reports/recalibration_metrics.json (src/ml/recalibration.py)",
                          "macro": rc["recalibration"]["macro"], "window": rc.get("window", {})},
        "drift": {"source": "reports/drift_metrics.json (src/ml/drift_analysis.py)",
                  "windows": dr.get("E3_E4", {}), "by_month": dr.get("E1", {}).get("by_month", [])},
    }


def forecast_metrics() -> dict:
    return {"baselines": read_json("forecast_metrics.json"), "models": read_json("forecast_models_metrics.json"),
            "source": "reports/forecast_metrics.json, reports/forecast_models_metrics.json"}


def lineage() -> dict:
    """Implementation status for the Data & lineage page, from the committed reconciliation report (a live run)."""
    path = ROOT / "docs" / "validation" / "RECONCILIATION_REPORT.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    run, checks, section = {}, [], None
    for line in text.splitlines():
        if line.startswith("## "):
            section = line[3:].strip().lower()
            continue
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= set("-: "):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if section == "run" and len(cells) == 2 and cells[0] != "item":
            run[cells[0]] = cells[1]
        elif section == "summary" and len(cells) >= 7 and cells[0] != "check":
            checks.append({"check": cells[0], "group": cells[1], "status": cells[2], "left_rows": cells[3],
                           "right_rows": cells[4], "missing_extra": cells[5], "unexplained": cells[6]})
    keep = ("generated", "git SHA", "mode", "database / role / warehouse", "tool: duckdb",
            "tool: snowflake-connector-python")
    return {"source": "docs/validation/RECONCILIATION_REPORT.md (src/reconciliation, live run)",
            "not_run": "NOT RUN" in text or not checks,
            "run": {k: v for k, v in run.items() if k in keep}, "checks": checks}


# -------------------------------------------------------------------------------------------- warehouse queries
def headline_kpis(con, schema: str) -> dict:
    s = schema
    sales = con.read_sql(f"""
        select sum(price) as net_revenue, count(distinct order_id) as net_orders, count(*) as items
        from {s}fact_order_items where order_status not in ('canceled', 'unavailable')""")
    deliv = con.read_sql(f"""
        select count(*) as labelled_orders, sum(case when is_late then 1 else 0 end) as late_orders
        from {s}fact_orders
        where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly""")
    rev = con.read_sql(f"""
        select avg(review_score) as avg_review_score from {s}fact_reviews where is_latest_review_for_order""")
    span = con.read_sql(f"select min(purchase_ts) as first_purchase, max(purchase_ts) as last_purchase from {s}fact_orders")
    sales.columns = [c.lower() for c in sales.columns]
    deliv.columns = [c.lower() for c in deliv.columns]
    rev.columns = [c.lower() for c in rev.columns]
    span.columns = [c.lower() for c in span.columns]
    r = {**sales.iloc[0].to_dict(), **deliv.iloc[0].to_dict(), **rev.iloc[0].to_dict(), **span.iloc[0].to_dict()}
    r = {k: (float(v) if hasattr(v, "as_tuple") else v) for k, v in r.items()}  # Decimal -> float
    for k in ("net_orders", "items", "labelled_orders", "late_orders"):  # counts stay integers on both backends
        r[k] = int(r[k]) if r[k] is not None else None
    r["avg_order_value"] = r["net_revenue"] / r["net_orders"]
    r["late_rate"] = r["late_orders"] / r["labelled_orders"]
    rep = pd.read_csv(REPORTS / "analytics" / ANALYTICS["repeat_customers"])
    one = rep.loc[rep["orders_placed"].astype(str) == "1"]
    r["one_time_customer_share"] = float(one["customer_share_pct"].iloc[0]) / 100 if len(one) else None
    return clean(r)


def forecasts(con) -> dict:
    import export_data  # src/powerbi: reuses the Power BI backtest, so both consumers show the same numbers
    import forecast_baseline as fb

    weekly = fb.weekly_series(con)
    bt = export_data.forecast_backtest(con)
    weekly = weekly.reset_index().rename(columns={weekly.index.name or "index": "week"})
    return {
        "weekly": records(weekly),
        "backtest": records(bt),
        "main_window": {"first_week": str(fb.FIRST_WEEK)[:10], "last_clean_week": str(fb.LAST_CLEAN_WEEK)[:10],
                        "suspect_week": str(fb.SUSPECT_WEEK)[:10]},
        "source": "fb.weekly_series + export_data.forecast_backtest (rolling origin, horizons 1 and 4 weeks)",
    }


def risk_rollups(con) -> dict:
    """Out-of-time v1 scores (export_scores.build_from, on either backend) rolled up: no order-level rows leave here."""
    import export_scores

    s = export_scores.build_from(con)
    s["decile"] = (s["risk_percentile"] * 10).apply(math.ceil).clip(1, 10).astype(int)
    base = s.groupby("month")["is_late"].mean().rename("base_rate")
    dec = (s.groupby(["month", "decile"]).agg(orders=("is_late", "size"), late=("is_late", "sum")).reset_index()
           .merge(base, on="month"))
    dec["late_rate"] = dec["late"] / dec["orders"]
    dec["lift"] = dec["late_rate"] / dec["base_rate"]
    overall = (s.groupby("decile").agg(orders=("is_late", "size"), late=("is_late", "sum")).reset_index())
    overall["late_rate"] = overall["late"] / overall["orders"]
    overall["lift"] = overall["late_rate"] / s["is_late"].mean()

    rows = []
    for share in FLAG_SHARES:
        for month, g in s.groupby("month"):
            flagged = g["risk_percentile"] > 1 - share
            n_late = g["is_late"].sum()
            rows.append({"flag_share": share, "month": month, "flagged": int(flagged.sum()),
                         "precision": float(g.loc[flagged, "is_late"].mean()) if flagged.any() else None,
                         "recall": float(g.loc[flagged, "is_late"].sum() / n_late) if n_late else None,
                         "base_rate": float(g["is_late"].mean())})
    op = pd.DataFrame(rows)

    by_state = (s.assign(flag=s["flagged_top10"]).groupby("customer_state")
                .agg(orders=("is_late", "size"), late_rate=("is_late", "mean"), flagged_share=("flag", "mean"))
                .reset_index().sort_values("orders", ascending=False))
    by_cat = (s.assign(flag=s["flagged_top10"]).groupby("category")
              .agg(orders=("is_late", "size"), late_rate=("is_late", "mean"), flagged_share=("flag", "mean"))
              .reset_index().sort_values("orders", ascending=False).head(25))
    return {
        "source": "src/ml/export_scores.py (v1 logistic regression, trained only on orders delivered before each test month)",
        "n_scored": len(s), "months": sorted(s["month"].unique().tolist()),
        "deciles_by_month": records(dec), "deciles_overall": records(overall),
        "operating_points": records(op), "by_customer_state": records(by_state), "by_category_top25": records(by_cat),
    }


# -------------------------------------------------------------------------------------------------------- main
def write(out: Path, name: str, payload: dict, manifest: dict, title: str, source: str, rows: int | None = None) -> None:
    """Stage <name>.json.tmp. commit() swaps every staged file in only after the whole build succeeded, so a failed
    build never leaves a mix of two builds or a manifest whose sizes and sources do not match the files."""
    final = out / f"{name}.json"
    tmp = out / f"{name}.json.tmp"
    tmp.write_text(json.dumps(clean(payload), separators=(",", ":"), ensure_ascii=False) + "\n", encoding="utf-8")
    manifest["datasets"][name] = {"file": final.name, "title": title, "source": source, "rows": rows,
                                  "bytes": tmp.stat().st_size}


def commit(out: Path, manifest: dict) -> None:
    for meta in manifest["datasets"].values():
        tmp = out / f"{meta['file']}.tmp"
        if tmp.exists():
            os.replace(tmp, out / meta["file"])
    tmp = out / "manifest.json.tmp"
    tmp.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    os.replace(tmp, out / "manifest.json")  # last: readers only ever see a complete, matching build


def discard(out: Path) -> None:
    for tmp in out.glob("*.json.tmp"):
        tmp.unlink()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    # The dashboard is built from the Snowflake marts by default (DD-22); DuckDB is the offline fallback.
    # $DASHBOARD_BACKEND overrides the default for this script only.
    parser.add_argument("--backend", choices=("duckdb", "snowflake"),
                        default=os.environ.get("DASHBOARD_BACKEND", "snowflake").strip().lower() or "snowflake")
    parser.add_argument("--db", type=Path, default=None, help="DuckDB warehouse (default: $DUCKDB_PATH or warehouse.duckdb)")
    parser.add_argument("--out", type=Path, default=ROOT / "dashboard" / "data")
    parser.add_argument("--yes", action="store_true", help="confirm the printed Snowflake target")
    parser.add_argument("--skip-scores", action="store_true", help="skip the risk-score roll-ups (they retrain v1)")
    args = parser.parse_args()

    from data_access import connect
    from data_access.backend import resolve_duckdb_path

    db = Path(args.db) if args.db else resolve_duckdb_path(None)
    if args.backend == "duckdb" and not db.exists():
        print(f"DuckDB warehouse not found: {db}. Build it (src/transformation/build_warehouse.py) or pass --db.",
              file=sys.stderr)
        return 1
    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {"generated_at": dt.datetime.now(dt.UTC).isoformat(timespec="seconds"), "git_sha": git_sha(),
                "backend": args.backend, "datasets": {}, "notes": []}

    if args.backend == "snowflake":
        from data_access.backend import ConfirmationRequired, MissingConfigError
        try:
            con = connect("snowflake", confirm=args.yes)
        except (ConfirmationRequired, MissingConfigError) as exc:
            print(f"{exc}\nRe-run with --yes after checking the target, or build offline with --backend duckdb.",
                  file=sys.stderr)
            return 1
    else:
        con = connect("duckdb", duckdb_path=db)
    schema = "MARTS." if args.backend == "snowflake" else ""
    where = "Snowflake RETAIL_OLIST.MARTS" if args.backend == "snowflake" else "DuckDB warehouse"
    risk = None
    discard(args.out)  # leftovers from an interrupted build
    try:
        write(args.out, "kpis", headline_kpis(con, schema), manifest, "Headline KPIs",
              f"{where}: fact_order_items, fact_orders, fact_reviews; reports/analytics/07")
        fc = forecasts(con)
        write(args.out, "forecast", {**fc, "metrics": forecast_metrics()}, manifest, "Weekly forecasts",
              f"{where}: {fc['source']}; {forecast_metrics()['source']}", rows=len(fc["backtest"]))
        tables = analytics_tables(con, schema)
        write(args.out, "analytics", tables, manifest, "Business analytics (8 queries)",
              f"{where}: mart_* (dbt)" if args.backend == "snowflake" else "reports/analytics/*.csv (sql/analytics)",
              rows=sum(len(t["rows"]) for t in tables.values()))
        if not args.skip_scores:
            risk = risk_rollups(con)
            risk["source"] = f"{where}: {risk['source']}"
    except BaseException:
        discard(args.out)  # nothing was swapped in: the previous build stays intact
        raise
    finally:
        con.close()
    write(args.out, "models", model_outputs(), manifest, "Late-delivery model results",
          "reports/late_delivery_metrics.json, explainability, recalibration, drift")
    lin = lineage()
    write(args.out, "lineage", lin, manifest, "DuckDB vs Snowflake reconciliation", lin["source"], rows=len(lin["checks"]))

    if risk is not None:
        write(args.out, "risk", risk, manifest, "Risk-score roll-ups", risk["source"], rows=risk["n_scored"])
    else:
        manifest["notes"].append("risk.json not rebuilt (--skip-scores); the previous build is served if present.")
        previous = args.out / "risk.json"
        if previous.exists():  # keep serving the previous build of the roll-ups, and say so
            risk = json.loads(previous.read_text(encoding="utf-8"))
            manifest["datasets"]["risk"] = {"file": previous.name, "title": "Risk-score roll-ups (previous build)",
                                            "source": risk.get("source", ""), "rows": risk.get("n_scored"),
                                            "bytes": previous.stat().st_size}

    commit(args.out, manifest)
    for name, meta in manifest["datasets"].items():
        print(f"  {name:10s} {meta['bytes']:>9,} bytes  {meta['title']}")
    print(f"wrote {args.out} ({args.backend}, git {manifest['git_sha']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
