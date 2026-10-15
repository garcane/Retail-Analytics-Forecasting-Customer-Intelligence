"""Recalibrate the v1 late-delivery model on the latest resolved period, and choose a training window walk-forward.

The drift analysis (docs/ml/DRIFT_ANALYSIS.md) found that the system-wide late rate moves between months, which hurts
calibration but not ranking, and that a short training window helped the v1 model. Two questions follow:

  R  Does fitting a calibrator on the most recent resolved orders fix the level?
       The base model trains only on orders whose delivery was known before the calibration window starts, and the
       calibrator is fitted on purchases from [start - gap - window, start - gap) that were delivered before the test
       month. The gap leaves time for most orders to resolve: right after the training cutoff, only fast deliveries
       are labelled yet, which would bias the calibration set low.
  W  Which training window should v1 use? Each test month picks its window from the three months before it, so no
     test month chooses its own window. Fixed windows are shown for comparison and are optimistic (chosen in hindsight).

    uv run python src/ml/recalibration.py [--db warehouse.duckdb] [--out reports/recalibration_metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, log_loss

import late_delivery_baseline as ldb

ROOT = Path(__file__).resolve().parents[2]

GAP_DAYS = 28
CAL_WINDOWS = (1, 2)  # months of purchases in the calibration set
CALIBRATORS = ("shift", "platt", "isotonic")
WINDOWS = (1, 2, 3, 4, 6, None)  # months of training data before a test month; None = everything from 2017-01
SELECTION_LOOKBACK = 3  # months used to choose the window for a test month
GRID_MONTHS = pd.period_range(ldb.TEST_MONTHS[0] - SELECTION_LOOKBACK, ldb.TEST_MONTHS[-1], freq="M")


def logit(p: np.ndarray) -> np.ndarray:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return np.log(p / (1 - p))


def sigmoid(z: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-z))


def calibration_split(df: pd.DataFrame, month: pd.Period, window_months: int, gap_days: int = GAP_DAYS):
    """(base training rows, calibration rows) for a test month, with the outcome-time rules above."""
    start = month.start_time
    cal_end = start - pd.Timedelta(days=gap_days)
    cal_start = cal_end - pd.DateOffset(months=window_months)
    calib = df[(df["purchase_ts"] >= cal_start) & (df["purchase_ts"] < cal_end) & (df["delivered_customer_ts"] < start)]
    base = df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < cal_start)]
    return base, calib


def make_calibrator(kind: str, p_cal: np.ndarray, y_cal: np.ndarray):
    """Return a function mapping model probabilities to recalibrated ones, fitted on the calibration rows."""
    if kind == "shift":  # one number added on the logit scale so that the mean prediction equals the observed rate
        z = logit(p_cal)
        b = brentq(lambda b: sigmoid(z + b).mean() - y_cal.mean(), -10, 10)
        return lambda p: sigmoid(logit(p) + b)
    if kind == "platt":  # intercept and slope on the logit scale
        lr = LogisticRegression(C=1e6).fit(logit(p_cal).reshape(-1, 1), y_cal)
        return lambda p: lr.predict_proba(logit(p).reshape(-1, 1))[:, 1]
    if kind == "isotonic":  # monotone step function
        iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1).fit(p_cal, y_cal)
        return lambda p: iso.predict(p)
    raise ValueError(kind)


def expected_calibration_error(y: np.ndarray, p: np.ndarray, bins: int = 5) -> float:
    bucket = pd.qcut(pd.Series(p).rank(method="first"), bins, labels=False)
    t = pd.DataFrame({"b": bucket, "p": p, "y": y}).groupby("b").agg(p=("p", "mean"), y=("y", "mean"), n=("y", "size"))
    return float((t["n"] * (t["p"] - t["y"]).abs()).sum() / t["n"].sum())


def score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        "brier": float(brier_score_loss(y, p)),
        "log_loss": float(log_loss(y, p)),
        "pr_auc": float(average_precision_score(y, p)),
        "mean_pred_minus_actual": float(p.mean() - y.mean()),
        "ece": expected_calibration_error(y, p),
    }


def fit_v1(train: pd.DataFrame):
    model = ldb.make_models(ldb.NUMERIC_V1, "x")["logistic_regression_x"]
    return model.fit(train[ldb.NUMERIC_V1 + ldb.CATEGORICAL], train["is_late"])


def predict(model, frame: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(frame[ldb.NUMERIC_V1 + ldb.CATEGORICAL])[:, 1]


def macro(rows: list[dict]) -> dict[str, float]:
    return {k: float(np.mean([r[k] for r in rows])) for k in rows[0] if isinstance(rows[0][k], float)}


# ------------------------------------------------------------------ R
def experiment_recalibration(df: pd.DataFrame) -> dict:
    per_month: dict[str, list[dict]] = {}
    for month in ldb.TEST_MONTHS:
        test = df[df["month"] == month]
        y = test["is_late"].to_numpy()
        reference = fit_v1(df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < month.start_time)])
        per_month.setdefault("reference: trained to the month start", []).append(
            {"month": str(month), "base_rate": float(y.mean()), **score(y, predict(reference, test))})
        for w in CAL_WINDOWS:
            base_rows, cal_rows = calibration_split(df, month, w)
            base = fit_v1(base_rows)
            p_test, p_cal = predict(base, test), predict(base, cal_rows)
            y_cal = cal_rows["is_late"].to_numpy()
            per_month.setdefault(f"base only (window {w}m, no calibration)", []).append(
                {"month": str(month), "base_rate": float(y.mean()), **score(y, p_test)})
            for kind in CALIBRATORS:
                p = make_calibrator(kind, p_cal, y_cal)(p_test)
                per_month.setdefault(f"base + {kind} (window {w}m)", []).append(
                    {"month": str(month), "base_rate": float(y.mean()), "cal_rows": float(len(cal_rows)),
                     "cal_rate": float(y_cal.mean()), **score(y, p)})
    return {"per_month": per_month, "macro": {k: macro(v) for k, v in per_month.items()}}


# ------------------------------------------------------------------ W
def experiment_window(df: pd.DataFrame) -> dict:
    grid: dict[tuple[str, str], dict] = {}
    for month in GRID_MONTHS:
        test = df[df["month"] == month]
        y = test["is_late"].to_numpy()
        for k in WINDOWS:
            lo = ldb.TRAIN_START if k is None else max(ldb.TRAIN_START, (month - k).start_time)
            train = df[(df["purchase_ts"] >= lo) & (df["delivered_customer_ts"] < month.start_time)]
            grid[(str(month), "all" if k is None else f"{k}m")] = score(y, predict(fit_v1(train), test))

    names = ["all" if k is None else f"{k}m" for k in WINDOWS]
    fixed = {n: macro([{"m": 0.0, **grid[(str(m), n)]} for m in ldb.TEST_MONTHS]) for n in names}

    chosen, walk = {}, []
    for month in ldb.TEST_MONTHS:
        prior = [str(month - i) for i in range(1, SELECTION_LOOKBACK + 1)]
        best = max(names, key=lambda n: np.mean([grid[(m, n)]["pr_auc"] for m in prior]))
        chosen[str(month)] = best
        walk.append(grid[(str(month), best)])
    return {"fixed": fixed, "walk_forward_choice": chosen,
            "walk_forward_macro": macro(walk),
            "by_month": {f"{m} | {n}": v for (m, n), v in grid.items()}}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "recalibration_metrics.json")
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    df = ldb.load(con)
    con.close()

    show = ["pr_auc", "brier", "log_loss", "ece", "mean_pred_minus_actual"]
    print("R  recalibration of the v1 logistic model (macro over the six test months; lower Brier/log loss/ECE is better)")
    r = experiment_recalibration(df)
    print(pd.DataFrame(r["macro"]).T[show].round(4).to_string(), "\n")
    print("Brier by month")
    print(pd.DataFrame({k: [x["brier"] for x in v] for k, v in r["per_month"].items()},
                       index=[x["month"] for x in next(iter(r["per_month"].values()))]).round(4).to_string(), "\n")

    print("W  training window for v1 (macro over the six test months)")
    w = experiment_window(df)
    print(pd.DataFrame(w["fixed"]).T[show].round(4).to_string())
    print("\nwalk-forward choice (window picked from the 3 months before each test month):")
    print(w["walk_forward_choice"])
    print(pd.Series(w["walk_forward_macro"])[show].round(4).to_string(), "\n")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"recalibration": r, "window": w}, indent=2, default=float), encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
