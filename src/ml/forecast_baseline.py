"""Weekly order forecast baselines (D-007): naive, moving averages and a short linear trend.

Series: orders per ISO week (Monday start) by purchase date, from fact_orders; revenue (sum of item price from
fact_order_items, DD-04) as the secondary target. Window and edge rules are in docs/ml/LEAKAGE_ANALYSIS.md:
  - weeks start 2017-01-02 .. 2018-08-13 are the main series (85 weeks);
  - the week of 2018-08-20 looks truncated by the extraction (1,071 orders against about 1,900 in the previous two
    weeks) and is reported as a sensitivity run, not in the main result;
  - the week of 2018-08-27 (130 orders, extraction ends mid-week) is always excluded.
Evaluation is a rolling origin in time order: forecasts for week t+h use only weeks up to t. There is no fitting step
beyond that, so no information flows from later weeks.

    uv run python src/ml/forecast_baseline.py [--db warehouse.duckdb] [--out reports/forecast_metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

FIRST_WEEK = pd.Timestamp("2017-01-02")
LAST_CLEAN_WEEK = pd.Timestamp("2018-08-13")
SUSPECT_WEEK = pd.Timestamp("2018-08-20")
BLACK_FRIDAY_WEEKS = [pd.Timestamp("2017-11-20")]  # Black Friday 2017-11-24 is the one observed instance
MIN_HISTORY = 26  # first origin has half a year of weeks behind it
HORIZONS = (1, 4)


def weekly_series(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(
        """
        with orders as (
            select date_trunc('week', purchase_ts)::date as week, count(*) as orders
            from fact_orders group by 1
        ), revenue as (
            select date_trunc('week', o.purchase_ts)::date as week, sum(oi.price)::double as revenue
            from fact_order_items oi join fact_orders o using (order_id) group by 1
        )
        select week, orders, coalesce(revenue, 0) as revenue
        from orders left join revenue using (week)
        order by week
        """
    ).df().assign(week=lambda d: pd.to_datetime(d["week"])).set_index("week")


# Each forecaster sees only `history` (a 1-d array ending at the origin week) and returns a constant forecast.
def naive(history: np.ndarray) -> float:
    return history[-1]


def moving_average(k: int):
    return lambda history: history[-k:].mean()


def linear_trend(k: int):
    """Straight line fitted to the last k weeks, extended `h` weeks ahead (h passed via closure at call time)."""
    def f(history: np.ndarray, h: int = 1) -> float:
        y = history[-k:]
        slope, intercept = np.polyfit(np.arange(len(y)), y, 1)
        return max(intercept + slope * (len(y) - 1 + h), 0.0)
    return f


MODELS = {
    "naive_last_week": naive,
    "moving_average_4": moving_average(4),
    "moving_average_8": moving_average(8),
    "linear_trend_12": linear_trend(12),
}


def backtest(series: pd.Series, h: int) -> pd.DataFrame:
    """Rolling-origin forecasts of week t+h made at origin t, for every origin with enough history."""
    values = series.to_numpy(dtype=float)
    rows = []
    for t in range(MIN_HISTORY - 1, len(values) - h):
        history = values[: t + 1]
        row = {"target_week": series.index[t + h], "actual": values[t + h]}
        for name, f in MODELS.items():
            row[name] = f(history, h) if f is MODELS["linear_trend_12"] else f(history)
        rows.append(row)
    return pd.DataFrame(rows).set_index("target_week")


def score(bt: pd.DataFrame) -> dict[str, dict[str, float]]:
    naive_mae = (bt["actual"] - bt["naive_last_week"]).abs().mean()
    out = {}
    for name in MODELS:
        err = bt["actual"] - bt[name]
        out[name] = {
            "mae": float(err.abs().mean()),
            "mape": float((err.abs() / bt["actual"]).mean()),
            "mae_vs_naive": float(err.abs().mean() / naive_mae),  # below 1 beats the naive forecast
            "bias": float(err.mean()),  # actual minus forecast; positive = the model under-forecasts
        }
    out["_n_forecasts"] = {"n": float(len(bt))}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "forecast_metrics.json")
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    full = weekly_series(con)
    con.close()

    variants = {
        "main (to 2018-08-13)": full.loc[FIRST_WEEK:LAST_CLEAN_WEEK],
        "with suspect week 2018-08-20": full.loc[FIRST_WEEK:SUSPECT_WEEK],
    }
    results: dict[str, dict] = {}
    for target in ("orders", "revenue"):
        for variant, frame in variants.items():
            for h in HORIZONS:
                bt = backtest(frame[target], h)
                results[f"{target} | {variant} | h={h}"] = score(bt)
                if variant.startswith("main"):
                    no_bf = bt.drop(index=[w for w in BLACK_FRIDAY_WEEKS if w in bt.index])
                    results[f"{target} | main, excluding Black Friday week | h={h}"] = score(no_bf)

    print(f"weeks in main series: {len(variants['main (to 2018-08-13)'])}; first origin after {MIN_HISTORY} weeks\n")
    for key, res in results.items():
        if not key.startswith("orders"):
            continue
        n = int(res.pop("_n_forecasts")["n"])
        print(f"{key}  (n={n})")
        print(pd.DataFrame(res).T[["mae", "mape", "mae_vs_naive", "bias"]].round(3).to_string(), "\n")
        res["_n_forecasts"] = {"n": float(n)}

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT)} (orders and revenue)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
