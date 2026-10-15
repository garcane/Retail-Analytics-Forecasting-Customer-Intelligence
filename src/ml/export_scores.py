"""Per-order late-delivery risk scores for the test months, for use outside Python (the Power BI risk page).

The scores are *out-of-time*: each order in a test month is scored by the v1 logistic regression trained only on orders
whose delivery was already known before that month started (the same rolling origin as the backtest and the notebooks).
The risk percentile is computed within each month, so "the riskiest 10%" means the riskiest 10% of that month's orders,
which is how the model is meant to be used (by rank, not by probability; see docs/ml/MODEL_CARD.md).

    uv run python src/ml/export_scores.py [--db warehouse.duckdb] [--out powerbi/data/late_delivery_scores.parquet]
"""

import argparse
import sys
from pathlib import Path

import duckdb
import pandas as pd

import late_delivery_baseline as ldb
from drift_analysis import KEYS_SQL  # order -> product category (most expensive item), route, first seller

ROOT = Path(__file__).resolve().parents[2]
FLAG_SHARE = 0.10  # the headline operating point used in the documents


def score_test_months(df: pd.DataFrame) -> pd.DataFrame:
    """One row per order in a test month, with its out-of-time risk score and within-month percentile."""
    features = ldb.NUMERIC_V1 + ldb.CATEGORICAL
    parts = []
    for month in ldb.TEST_MONTHS:
        train = df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < month.start_time)]
        test = df[df["month"] == month].copy()
        model = ldb.make_models(ldb.NUMERIC_V1, "v1")["logistic_regression_v1"].fit(train[features], train["is_late"])
        test["risk_score"] = model.predict_proba(test[features])[:, 1]
        # 1.0 = the riskiest order of the month; method="first" breaks ties deterministically
        test["risk_percentile"] = test["risk_score"].rank(method="first", pct=True)
        parts.append(test)
    out = pd.concat(parts, ignore_index=True)
    out["flagged_top10"] = out["risk_percentile"] > 1 - FLAG_SHARE
    out["purchase_date_key"] = out["purchase_ts"].dt.strftime("%Y%m%d").astype("int64")
    out["month"] = out["month"].astype(str)
    return out


def build(db: Path) -> pd.DataFrame:
    con = duckdb.connect(str(db), read_only=True)
    df = ldb.load(con).merge(con.execute(KEYS_SQL).df()[["order_id", "category"]], on="order_id", how="left")
    con.close()
    df["category"] = df["category"].fillna("unknown")
    scored = score_test_months(df)
    columns = ["order_id", "month", "purchase_date_key", "risk_score", "risk_percentile", "flagged_top10", "is_late",
               "customer_state", "seller_state", "category", "promised_days"]
    return scored[columns].sort_values(["month", "risk_percentile"], ascending=[True, False]).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "powerbi" / "data" / "late_delivery_scores.parquet")
    args = parser.parse_args()
    scores = build(args.db)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(args.out, index=False)
    flagged = scores[scores["flagged_top10"]]
    print(f"{len(scores):,} scored orders ({scores['month'].nunique()} months); late rate {scores['is_late'].mean():.3f}; "
          f"flagged {len(flagged):,} with late rate {flagged['is_late'].mean():.3f}")
    print(f"wrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
