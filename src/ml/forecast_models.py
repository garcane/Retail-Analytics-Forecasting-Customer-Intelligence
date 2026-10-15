"""Weekly order forecast: exponential smoothing, damped trend and a short regression, against the baselines.

Same series, window, rolling-origin backtest and edge rules as forecast_baseline.py (see its docstring and
docs/ml/LEAKAGE_ANALYSIS.md). Every model is refitted at each origin on the weeks up to that origin only, so nothing
after the origin can influence a forecast. Written with numpy and scipy only.

    uv run python src/ml/forecast_models.py [--db warehouse.duckdb] [--out reports/forecast_models_metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import minimize, minimize_scalar

import forecast_baseline as fb

ROOT = Path(__file__).resolve().parents[2]


def simple_exponential_smoothing(history: np.ndarray, h: int = 1) -> float:
    """Level only. The smoothing weight minimises the one-step squared error over the history."""
    def sse(alpha: float) -> float:
        level, total = history[0], 0.0
        for y in history[1:]:
            total += (y - level) ** 2
            level = alpha * y + (1 - alpha) * level
        return total

    alpha = minimize_scalar(sse, bounds=(0.01, 0.99), method="bounded").x
    level = history[0]
    for y in history[1:]:
        level = alpha * y + (1 - alpha) * level
    return float(level)


def damped_trend(history: np.ndarray, h: int = 1) -> float:
    """Holt's method with a damped trend: the slope fades by `phi` each week instead of continuing forever."""
    def run(params: np.ndarray):
        alpha, beta, phi = params
        level, trend, total = history[0], history[1] - history[0], 0.0
        for y in history[1:]:
            forecast = level + phi * trend
            total += (y - forecast) ** 2
            new_level = alpha * y + (1 - alpha) * forecast
            trend = beta * (new_level - level) + (1 - beta) * phi * trend
            level = new_level
        return total, level, trend

    fit = minimize(lambda p: run(p)[0], x0=[0.5, 0.1, 0.9], bounds=[(0.01, 0.99), (0.001, 0.5), (0.8, 0.98)],
                   method="L-BFGS-B")
    _, level, trend = run(fit.x)
    phi = fit.x[2]
    return float(max(level + trend * sum(phi ** i for i in range(1, h + 1)), 0.0))


def ar1_with_trend(window: int = 26):
    """OLS of this week on last week and a time trend over the last `window` weeks, iterated h steps ahead."""
    def f(history: np.ndarray, h: int = 1) -> float:
        y = history[-window:]
        t = np.arange(len(y))
        design = np.column_stack([np.ones(len(y) - 1), t[1:], y[:-1]])
        coef, *_ = np.linalg.lstsq(design, y[1:], rcond=None)
        last, step = y[-1], len(y) - 1
        for _ in range(h):
            step += 1
            last = coef[0] + coef[1] * step + coef[2] * last
        return float(max(last, 0.0))
    return f


def combination(history: np.ndarray, h: int = 1) -> float:
    """Average of the naive forecast and the 8-week moving average, the two baseline winners."""
    return float((fb.naive(history, h) + fb.moving_average(8)(history, h)) / 2)


MODELS = {
    "naive_last_week": fb.naive,
    "moving_average_8": fb.moving_average(8),
    "simple_exp_smoothing": simple_exponential_smoothing,
    "damped_trend": damped_trend,
    "ar1_trend_26w": ar1_with_trend(26),
    "combo_naive_ma8": combination,
}


def beats_naive_share(bt: pd.DataFrame) -> dict[str, float]:
    naive_err = (bt["actual"] - bt["naive_last_week"]).abs()
    return {c: float(((bt["actual"] - bt[c]).abs() < naive_err).mean()) for c in bt.columns if c not in ("actual",)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "forecast_models_metrics.json")
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    full = fb.weekly_series(con)
    con.close()
    variants = {
        "main (to 2018-08-13)": full.loc[fb.FIRST_WEEK:fb.LAST_CLEAN_WEEK],
        "with suspect week 2018-08-20": full.loc[fb.FIRST_WEEK:fb.SUSPECT_WEEK],
    }

    results: dict[str, dict] = {}
    for target in ("orders", "revenue"):
        for variant, frame in variants.items():
            for h in fb.HORIZONS:
                bt = fb.backtest(frame[target], h, MODELS)
                res = fb.score(bt)
                shares = beats_naive_share(bt)
                for name in MODELS:
                    res[name]["share_of_weeks_beating_naive"] = shares[name]
                results[f"{target} | {variant} | h={h}"] = res
                if variant.startswith("main"):
                    no_bf = bt.drop(index=[w for w in fb.BLACK_FRIDAY_WEEKS if w in bt.index])
                    results[f"{target} | main, excluding Black Friday week | h={h}"] = fb.score(no_bf)

    for key, res in results.items():
        if not key.startswith("orders"):
            continue
        n = int(res["_n_forecasts"]["n"])
        cols = ["mae", "mape", "mae_vs_naive", "bias"] + (["share_of_weeks_beating_naive"] if "share_of_weeks_beating_naive" in res["naive_last_week"] else [])
        print(f"{key}  (n={n})")
        print(pd.DataFrame({k: v for k, v in res.items() if k != "_n_forecasts"}).T[cols].round(3).to_string(), "\n")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT)} (orders and revenue)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
