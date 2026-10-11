"""Test the drift explanation for why route, category and trailing-rate features did not help (DD-10).

Claim under test: the late rate moves by regime (system-wide, month to month), so history features learn the regime of
the training period, and that does not carry into later months. Five checks, each of which could contradict it:

  E1  within-month skill of each feature, month by month, against its skill pooled over the whole training period
  E2  persistence of route / category / seller lateness between periods, absolute against relative to the system,
      with a noise ceiling from a random split-half inside one period
  E3  training-window length: does a shorter window help the history features?
  E4  relative history features (route and category rate minus the system rate at the time)
  E5  an oracle that is told the true late rate of the purchase month (NOT available at purchase), as a ceiling

Everything except E5 uses only information available at purchase. The month-level late rate used inside E2 is an
analysis tool, never a model input.

    uv run python src/ml/drift_analysis.py [--db warehouse.duckdb] [--out reports/drift_metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

import late_delivery_baseline as ldb

ROOT = Path(__file__).resolve().parents[2]

KEYS_SQL = """
with pop as (
    select order_id from fact_orders
    where order_status = 'delivered' and is_late is not null and not has_timestamp_anomaly
), it as (
    select oi.order_id, oi.seller_key, oi.price, p.product_category_name_english as category,
           s.seller_state, cg.state as customer_state
    from fact_order_items oi
    join pop using (order_id)
    join dim_product p    on p.product_key = oi.product_key
    join dim_seller s     on s.seller_key = oi.seller_key
    join dim_geography cg on cg.geography_key = oi.customer_geography_key
)
select order_id, min(seller_key) as seller_key,
       coalesce(min(seller_state), 'unknown') || '>' || coalesce(min(customer_state), 'unknown') as route,
       coalesce(arg_max(category, price), 'unknown') as category
from it group by order_id
"""

TRAIN_MONTHS = pd.period_range("2017-03", "2018-02", freq="M")  # the span before the first test month
ALL_MONTHS = pd.period_range("2017-03", "2018-08", freq="M")
PERIODS = {
    "P1 2017-03..08": ("2017-03-01", "2017-09-01"),
    "P2 2017-09..2018-02": ("2017-09-01", "2018-03-01"),
    "P3 2018-03..08": ("2018-03-01", "2018-09-01"),
}
MIN_ORDERS = {"route": 100, "category": 100, "seller": 50}
WINDOWS = (2, 3, 6, None)  # months of training data before the test month; None = everything from 2017-01
SYSTEM_SMOOTHING = 100


def with_system_counts(df: pd.DataFrame) -> pd.DataFrame:
    """Point-in-time system-wide counts: orders delivered strictly before each purchase, and how many were late."""
    order = np.argsort(df["delivered_customer_ts"].to_numpy(), kind="stable")
    delivered = df["delivered_customer_ts"].to_numpy()[order]
    cum_late = np.concatenate([[0], np.cumsum(df["is_late"].to_numpy()[order])])
    idx = np.searchsorted(delivered, df["purchase_ts"].to_numpy(), side="left")
    out = df.copy()
    out["sys_n"], out["sys_late"] = idx.astype(float), cum_late[idx].astype(float)
    return out


def add_relative_rates(df: pd.DataFrame, prior: float) -> pd.DataFrame:
    out = ldb.add_smoothed_rates(df, prior)
    sys_rate = (out["sys_late"] + SYSTEM_SMOOTHING * prior) / (out["sys_n"] + SYSTEM_SMOOTHING)
    out["route_rel"] = out["route_rate"] - sys_rate
    out["category_rel"] = out["category_rate"] - sys_rate
    return out


NUMERIC_V4 = ldb.NUMERIC_V1 + ["route_rel", "route_prior_n", "category_rel", "category_prior_n"]


# ---------------------------------------------------------------- E1
def e1_feature_skill(df: pd.DataFrame, prior: float) -> dict:
    d = add_relative_rates(df, prior)
    d["seller_prior_late_rate"] = d["seller_prior_late_rate"].fillna(prior)
    d["distance_km"] = d["distance_km"].fillna(d["distance_km"].median())
    features = ["seller_prior_late_rate", "route_rate", "category_rate", "recent_rate_28d", "route_rel",
                "promised_days", "distance_km"]
    rows = []
    for m in ALL_MONTHS:
        sub = d[d["month"] == m]
        rows.append({"month": str(m), "late_rate": float(sub["is_late"].mean()),
                     **{f: float(roc_auc_score(sub["is_late"], sub[f])) for f in features}})
    by_month = pd.DataFrame(rows).set_index("month")

    def pooled(months):
        sub = d[d["month"].isin(months)]
        return {f: float(roc_auc_score(sub["is_late"], sub[f])) for f in features}

    summary = pd.DataFrame({
        "pooled_train_period": pooled(TRAIN_MONTHS),
        "mean_within_month_train": by_month.loc[[str(m) for m in TRAIN_MONTHS], features].mean(),
        "pooled_test_period": pooled(ldb.TEST_MONTHS),
        "mean_within_month_test": by_month.loc[[str(m) for m in ldb.TEST_MONTHS], features].mean(),
        "sd_within_month": by_month[features].std(),
        "min_within_month": by_month[features].min(),
    })
    return {"by_month": by_month.reset_index().to_dict("records"), "summary": summary.round(4).to_dict("index")}


# ---------------------------------------------------------------- E2
def e2_persistence(df: pd.DataFrame) -> dict:
    d = df.copy()
    d["residual"] = d["is_late"] - d.groupby("month")["is_late"].transform("mean")  # lateness relative to the month
    rng = np.random.default_rng(0)
    out = {}
    for level, col in (("route", "route"), ("category", "category"), ("seller", "seller_key")):
        stats = {}
        for name, (a, b) in PERIODS.items():
            sub = d[(d["purchase_ts"] >= a) & (d["purchase_ts"] < b)]
            stats[name] = sub.groupby(col).agg(n=("is_late", "size"), absolute=("is_late", "mean"),
                                               relative=("residual", "mean"))
        p2 = d[(d["purchase_ts"] >= PERIODS["P2 2017-09..2018-02"][0]) & (d["purchase_ts"] < PERIODS["P2 2017-09..2018-02"][1])]
        half = rng.random(len(p2)) < 0.5
        h1 = p2[half].groupby(col).agg(n=("is_late", "size"), absolute=("is_late", "mean"), relative=("residual", "mean"))
        h2 = p2[~half].groupby(col).agg(n=("is_late", "size"), absolute=("is_late", "mean"), relative=("residual", "mean"))
        # the ceiling uses keys with enough orders in each half, matched to the size of the period-to-period test
        pairs = {"P1->P2": (stats["P1 2017-03..08"], stats["P2 2017-09..2018-02"]),
                 "P2->P3": (stats["P2 2017-09..2018-02"], stats["P3 2018-03..08"]),
                 "ceiling: random halves of P2": (h1, h2)}
        res = {}
        for label, (x, y) in pairs.items():
            floor = MIN_ORDERS[level] if "ceiling" not in label else MIN_ORDERS[level] // 2
            j = x.join(y, lsuffix="_a", rsuffix="_b", how="inner")
            j = j[(j["n_a"] >= floor) & (j["n_b"] >= floor)]
            res[label] = {"keys": int(len(j)),
                          "spearman_absolute": float(j["absolute_a"].corr(j["absolute_b"], method="spearman")),
                          "spearman_relative": float(j["relative_a"].corr(j["relative_b"], method="spearman"))}
        out[level] = res
    return out


# ---------------------------------------------------------------- E3 / E4 / E5
def fit_score(df: pd.DataFrame, numeric: list[str], window: int | None, oracle: bool = False,
              categorical: list[str] | None = None) -> pd.DataFrame:
    categorical = ldb.CATEGORICAL if categorical is None else categorical
    rows = []
    for month in ldb.TEST_MONTHS:
        start = month.start_time
        lo = ldb.TRAIN_START if window is None else max(ldb.TRAIN_START, (month - window).start_time)
        train = df[(df["purchase_ts"] >= lo) & (df["delivered_customer_ts"] < start)]
        test = df[df["month"] == month]
        prior = train["is_late"].mean()
        train, test = add_relative_rates(train, prior), add_relative_rates(test, prior)
        cols = numeric + ["month_rate_oracle"] if oracle else numeric
        model = ldb.make_models(cols, "x", categorical)["logistic_regression_x"]
        model.fit(train[cols + categorical], train["is_late"])
        p = model.predict_proba(test[cols + categorical])[:, 1]
        y = test["is_late"].to_numpy()
        rows.append({"month": str(month), "pr_auc": average_precision_score(y, p), "roc_auc": roc_auc_score(y, p),
                     "brier": brier_score_loss(y, p), "base_rate": y.mean(), "n_train": len(train)})
    return pd.DataFrame(rows)


def macro(frame: pd.DataFrame) -> dict[str, float]:
    out = {k: float(frame[k].mean()) for k in ("pr_auc", "roc_auc", "brier")}
    out["pr_auc_ex_aug"] = float(frame.loc[frame["month"] != "2018-08", "pr_auc"].mean())  # August 2018 is an outlier month
    return out


def e_lag(df: pd.DataFrame) -> dict:
    """Does the trailing 28-day rate at the start of a month predict that month's rate?"""
    monthly = df.groupby("month")["is_late"].mean().loc[ALL_MONTHS]
    first = df[df["month"].isin(ALL_MONTHS)].sort_values("purchase_ts").groupby("month").head(50)
    start_trailing = first.groupby("month")["recent_late_28d"].mean() / first.groupby("month")["recent_n_28d"].mean()
    lag1 = float(monthly.autocorr(lag=1))
    return {
        "monthly_late_rate": {str(m): round(float(v), 4) for m, v in monthly.items()},
        "lag1_autocorrelation": lag1,
        "corr_trailing_rate_at_month_start_vs_month_rate": float(start_trailing.loc[ALL_MONTHS].corr(monthly)),
        "mean_abs_gap_trailing_vs_actual": float((start_trailing.loc[ALL_MONTHS] - monthly).abs().mean()),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "drift_metrics.json")
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    df = ldb.load(con).merge(con.execute(KEYS_SQL).df(), on="order_id", how="left")
    con.close()
    assert df["route"].notna().all()
    df = with_system_counts(df)
    df["month_rate_oracle"] = df.groupby("month")["is_late"].transform("mean")  # E5 only: uses the future
    prior = float(df.loc[df["month"] <= pd.Period("2018-02"), "is_late"].mean())

    results: dict[str, object] = {}

    print("E1  single-feature ROC-AUC (0.5 = no skill)")
    e1 = e1_feature_skill(df, prior)
    results["E1"] = e1
    print(pd.DataFrame(e1["summary"]).T.round(3).to_string(), "\n")
    print(pd.DataFrame(e1["by_month"]).set_index("month").round(3).to_string(), "\n")

    print("E2  persistence of lateness across periods (Spearman across keys)")
    e2 = e2_persistence(df)
    results["E2"] = e2
    for level, res in e2.items():
        print(level)
        print(pd.DataFrame(res).T.round(3).to_string())
    print()

    print("E3/E4  logistic regression by training window and feature set (macro over test months)")
    sets = {"v1": ldb.NUMERIC_V1, "v2": ldb.NUMERIC_V2, "v3": ldb.NUMERIC_V3, "v4 (relative)": NUMERIC_V4}
    grid = {}
    for window in WINDOWS:
        for name, numeric in sets.items():
            grid[f"{name} | window={'all' if window is None else str(window) + 'm'}"] = macro(fit_score(df, numeric, window))
    results["E3_E4"] = grid
    print(pd.DataFrame(grid).T.round(4).to_string(), "\n")

    print("E6  is route history redundant with the state and distance columns already in v1?")
    no_geo = [c for c in ldb.NUMERIC_V1 if c not in ("distance_km", "same_state")]
    only_pay = ["main_payment_type"]
    route_cols = ["route_rate", "route_prior_n"]
    e6 = {
        "v1 (states + distance)": macro(fit_score(df, ldb.NUMERIC_V1, None)),
        "v1 without states and distance": macro(fit_score(df, no_geo, None, categorical=only_pay)),
        "... + route history": macro(fit_score(df, no_geo + route_cols, None, categorical=only_pay)),
        "v1 + route history (= v2 without category)": macro(fit_score(df, ldb.NUMERIC_V1 + route_cols, None)),
    }
    results["E6_redundancy"] = e6
    print(pd.DataFrame(e6).T.round(4).to_string(), "\n")

    print("E5  oracle ceiling (told the true late rate of the purchase month)")
    oracle = {name: macro(fit_score(df, numeric, None, oracle=True)) for name, numeric in (("v1", ldb.NUMERIC_V1), ("v3", ldb.NUMERIC_V3))}
    results["E5_oracle"] = oracle
    print(pd.DataFrame(oracle).T.round(4).to_string(), "\n")

    print("Does the trailing rate track the monthly rate?")
    lag = e_lag(df)
    results["lag"] = lag
    print(json.dumps({k: v for k, v in lag.items() if k != "monthly_late_rate"}, indent=2))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=2, default=float), encoding="utf-8")
    print(f"\nwrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
