"""Explain the v1 late-delivery model: grouped permutation importance per test month, and logistic coefficients.

Permutation importance: in a test month, shuffle one group of columns together (rows keep their labels, the group's
values are reassigned at random) and measure the drop in PR-AUC. A large drop means the model leans on that group.
Groups are shuffled jointly because related columns (for example both states and the distance) carry the same
information and would hide each other if shuffled one at a time. Repeated 10 times per month with a fixed seed.

    uv run python src/ml/explain_late_delivery.py [--db warehouse.duckdb] [--out reports/explainability_metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

import late_delivery_baseline as ldb

ROOT = Path(__file__).resolve().parents[2]
REPEATS = 10

GROUPS = {
    "promise (promised_days)": ["promised_days"],
    "route (states, same_state, distance)": ["customer_state", "seller_state", "same_state", "distance_km"],
    "basket size and weight": ["item_count", "items_price", "items_freight", "freight_ratio", "n_sellers",
                               "total_weight_g", "max_volume_cm3", "max_item_freight"],
    "seller history": ["seller_prior_late_rate", "seller_prior_n"],
    "purchase calendar (weekday, hour)": ["purchase_dow", "purchase_hour"],
    "payment": ["max_installments", "main_payment_type"],
}


def permutation_drop(model, test: pd.DataFrame, columns: list[str], base: float, rng: np.random.Generator) -> float:
    drops = []
    features = ldb.NUMERIC_V1 + ldb.CATEGORICAL
    for _ in range(REPEATS):
        shuffled = test[features].copy()
        order = rng.permutation(len(shuffled))
        shuffled[columns] = shuffled[columns].to_numpy()[order]
        score = average_precision_score(test["is_late"], model.predict_proba(shuffled)[:, 1])
        drops.append(base - score)
    return float(np.mean(drops))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "explainability_metrics.json")
    args = parser.parse_args()

    assert sorted(c for g in GROUPS.values() for c in g) == sorted(ldb.NUMERIC_V1 + ldb.CATEGORICAL), \
        "every v1 feature must be in exactly one group"

    con = duckdb.connect(str(args.db), read_only=True)
    df = ldb.load(con)
    con.close()

    rng = np.random.default_rng(0)
    features = ldb.NUMERIC_V1 + ldb.CATEGORICAL
    rows = []
    for month in ldb.TEST_MONTHS:
        train = df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < month.start_time)]
        test = df[df["month"] == month]
        model = ldb.make_models(ldb.NUMERIC_V1, "x")["logistic_regression_x"].fit(train[features], train["is_late"])
        base = average_precision_score(test["is_late"], model.predict_proba(test[features])[:, 1])
        for name, cols in GROUPS.items():
            rows.append({"month": str(month), "group": name, "base_pr_auc": base,
                         "pr_auc_drop": permutation_drop(model, test, cols, base, rng)})
    imp = pd.DataFrame(rows)
    table = imp.pivot(index="group", columns="month", values="pr_auc_drop")
    table["mean"] = table.mean(axis=1)
    table = table.sort_values("mean", ascending=False)
    print("PR-AUC lost when a feature group is shuffled (higher = the model relies on it more)")
    print(table.round(4).to_string(), "\n")

    # coefficients of the final model: everything resolved before the last test month
    last = ldb.TEST_MONTHS[-1].start_time
    train = df[(df["purchase_ts"] >= ldb.TRAIN_START) & (df["delivered_customer_ts"] < last)]
    final = ldb.make_models(ldb.NUMERIC_V1, "x")["logistic_regression_x"].fit(train[features], train["is_late"])
    names = final[:-1].get_feature_names_out()
    coefs = pd.Series(final[-1].coef_[0], index=[n.split("__", 1)[1] for n in names])
    top = coefs.reindex(coefs.abs().sort_values(ascending=False).index).head(15)
    print("largest logistic coefficients (numeric features are standardised, so they compare directly;")
    print("positive = later; one-hot columns are relative to the other categories)")
    print(top.round(3).to_string())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({
        "permutation_pr_auc_drop": table.round(5).to_dict("index"),
        "top_coefficients": top.round(4).to_dict(),
        "repeats": REPEATS,
    }, indent=2), encoding="utf-8")
    print(f"\nwrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
