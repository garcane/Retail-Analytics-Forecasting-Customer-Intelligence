"""Late-delivery baselines (D-007), evaluated by monthly rolling origin.

For each test month M (2018-03 .. 2018-08) the models train on orders whose outcome was already known before M
started (delivered_customer_ts < start of M) and are scored on orders purchased in M. This is the split described in
docs/ml/LEAKAGE_ANALYSIS.md: time-ordered, no random split, no training label resolved inside the test period.

    uv run python src/ml/late_delivery_baseline.py [--db warehouse.duckdb] [--out reports/late_delivery_metrics.json]
"""

import argparse
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[2]
FEATURES_SQL = ROOT / "sql" / "ml" / "late_delivery_features.sql"

TRAIN_START = pd.Timestamp("2017-01-01")  # 2016 is a sparse tail (LEAKAGE_ANALYSIS, window edges)
TEST_MONTHS = pd.period_range("2018-03", "2018-08", freq="M")
FLAG_SHARE = 0.10  # operational metric: flag the 10% of orders with the highest predicted risk
MIN_SELLER_HISTORY = 5

NUMERIC = [
    "purchase_dow", "purchase_hour", "promised_days", "item_count", "items_price", "items_freight", "freight_ratio",
    "n_sellers", "total_weight_g", "max_volume_cm3", "max_item_freight", "distance_km", "same_state",
    "max_installments", "seller_prior_late_rate", "seller_prior_n",
]
CATEGORICAL = ["customer_state", "seller_state", "main_payment_type"]
# purchase_month is deliberately not a feature: with under two years of history it only memorises calendar months.


def load(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    df = con.execute(FEATURES_SQL.read_text(encoding="utf-8")).df()
    df["month"] = df["purchase_ts"].dt.to_period("M")
    df[NUMERIC] = df[NUMERIC].astype("float64")  # DuckDB returns nullable Int64; scikit-learn wants plain floats
    return df


def unlabelled_share(con: duckdb.DuckDBPyConnection) -> dict[str, float]:
    """Share of each month's orders with no usable label (not delivered, anomalous, or no delivery date)."""
    rows = con.execute(
        """select strftime(o.purchase_ts, '%Y-%m') ym, count(*) n,
                  count(*) filter (where o.order_status = 'delivered' and o.is_late is not null
                                   and not o.has_timestamp_anomaly) labelled
           from fact_orders o group by 1"""
    ).fetchall()
    return {ym: round(1 - labelled / n, 4) for ym, n, labelled in rows}


def top_share_metrics(y: np.ndarray, score: np.ndarray, share: float) -> dict[str, float]:
    """Precision and recall when the top `share` of orders by score are flagged (ties broken by order)."""
    k = max(1, int(round(share * len(y))))
    idx = np.argsort(-score, kind="stable")[:k]
    tp = y[idx].sum()
    return {"precision_at_top": float(tp / k), "recall_at_top": float(tp / max(y.sum(), 1))}


def evaluate(y: np.ndarray, score: np.ndarray) -> dict[str, float]:
    out = {
        "n": int(len(y)),
        "base_rate": float(y.mean()),
        "pr_auc": float(average_precision_score(y, score)),
        "roc_auc": float(roc_auc_score(y, score)),
        "brier": float(brier_score_loss(y, np.clip(score, 0, 1))),
    }
    out.update(top_share_metrics(y, score, FLAG_SHARE))
    return out


def make_models() -> dict[str, object]:
    linear_pre = ColumnTransformer(
        [
            ("num", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), NUMERIC),
            ("cat", OneHotEncoder(handle_unknown="ignore", min_frequency=50), CATEGORICAL),
        ]
    )
    tree_pre = ColumnTransformer(
        [
            ("num", "passthrough", NUMERIC),
            ("cat", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), CATEGORICAL),
        ]
    )
    cat_idx = list(range(len(NUMERIC), len(NUMERIC) + len(CATEGORICAL)))
    return {
        "logistic_regression": make_pipeline(linear_pre, LogisticRegression(max_iter=2000, C=0.5)),
        "gradient_boosting": make_pipeline(
            tree_pre,
            HistGradientBoostingClassifier(
                max_depth=4, learning_rate=0.05, max_iter=300, min_samples_leaf=100,
                categorical_features=cat_idx, random_state=0,
            ),
        ),
    }


def run(df: pd.DataFrame) -> tuple[dict[str, dict], dict[str, list[dict]]]:
    """Return (macro-average over test months, per-month rows) for each model.

    Metrics are averaged over months, not pooled: a pooled ROC-AUC would compare scores from models trained at
    different dates, so a constant baseline would be ranked by how its training rate drifted rather than by skill.
    """
    per_month: dict[str, list[dict]] = {}

    for month in TEST_MONTHS:
        start = month.start_time
        train = df[(df["purchase_ts"] >= TRAIN_START) & (df["delivered_customer_ts"] < start)]
        test = df[df["month"] == month]
        y_train, y_test = train["is_late"].to_numpy(), test["is_late"].to_numpy()
        train_rate = y_train.mean()

        scores: dict[str, np.ndarray] = {
            "constant_train_rate": np.full(len(test), train_rate),
            # seller's own history; the global training rate when the seller has fewer than 5 resolved orders
            "seller_history_rate": test["seller_prior_late_rate"].fillna(train_rate).to_numpy(),
        }
        for name, model in make_models().items():
            model.fit(train[NUMERIC + CATEGORICAL], y_train)
            scores[name] = model.predict_proba(test[NUMERIC + CATEGORICAL])[:, 1]

        for name, s in scores.items():
            row = {"month": str(month), "model": name, "n_train": int(len(train)), **evaluate(y_test, s)}
            per_month.setdefault(name, []).append(row)

    metrics = ["base_rate", "pr_auc", "roc_auc", "brier", "precision_at_top", "recall_at_top"]
    macro = {
        name: {"n_test": sum(r["n"] for r in rows), **{m: float(np.mean([r[m] for r in rows])) for m in metrics}}
        for name, rows in per_month.items()
    }
    return macro, per_month


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--out", type=Path, default=ROOT / "reports" / "late_delivery_metrics.json")
    args = parser.parse_args()

    con = duckdb.connect(str(args.db), read_only=True)
    df = load(con)
    unl = unlabelled_share(con)
    con.close()

    macro, per_month = run(df)

    print(f"features: {len(df):,} orders, late rate {df['is_late'].mean():.4f}")
    print(f"test months {TEST_MONTHS[0]}..{TEST_MONTHS[-1]}, flag top {FLAG_SHARE:.0%} of orders\n")
    cols = ["n_test", "base_rate", "pr_auc", "roc_auc", "brier", "precision_at_top", "recall_at_top"]
    print("macro-average over test months")
    print(pd.DataFrame(macro).T[cols].round(4).to_string())
    print("\nPR-AUC by month")
    pr = pd.DataFrame({m: [r["pr_auc"] for r in rows] for m, rows in per_month.items()},
                      index=[r["month"] for r in next(iter(per_month.values()))])
    pr.insert(0, "base_rate", [r["base_rate"] for r in next(iter(per_month.values()))])
    pr.insert(1, "unlabelled", [unl[str(m)] for m in TEST_MONTHS])
    print(pr.round(3).to_string())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"macro_average": macro, "per_month": per_month, "unlabelled_share": unl}, indent=2), encoding="utf-8"
    )
    print(f"\nwrote {args.out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
