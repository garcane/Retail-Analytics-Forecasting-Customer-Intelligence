"""Register the late-delivery model (v1 logistic regression) in the Snowflake Model Registry.

Runs in this folder's own environment (snowflake-ml-python needs pandas<3 and connector<5; the root project does not):

    cd snowflake/ml; uv sync --native-tls                                    # once
    .venv/Scripts/python.exe register_model.py                               # prints the target and stops
    .venv/Scripts/python.exe register_model.py --yes                         # trains and evaluates; registers nothing
    .venv/Scripts/python.exe register_model.py --yes --register              # ... and logs a new model version

What is registered: the v1 pipeline from src/ml/late_delivery_baseline.py (median imputation and scaling of the v1
numeric features, one-hot of the three categoricals, LogisticRegression C=0.5), trained on every labelled order from
MARTS.MART_LATE_DELIVERY_FEATURES with purchase_ts >= TRAIN_START. Its quality figures are the out-of-time backtest
in reports/snowflake/late_delivery_metrics.json (six test months, each scored by a model trained only on earlier
orders); a model trained on all months has no honest held-out score of its own, so none is invented here.

After logging, the script scores a sample of orders inside Snowflake with the registered version (PREDICT_PROBA) and
compares the result with the local model; the comparison and the version details go to
reports/snowflake/model_registry.json. An existing version is never replaced: a version name that already exists is an
error. Needs, on RETAIL_OLIST.ML: CREATE MODEL (and CREATE STAGE for the library's fallback upload path); see
snowflake/setup/06_model_registry_grants.sql.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for sub in ("src", "src/ml"):
    if str(ROOT / sub) not in sys.path:
        sys.path.insert(0, str(ROOT / sub))

import late_delivery_baseline as ldb  # noqa: E402
from data_access import connect  # noqa: E402
from data_access.backend import ConfirmationRequired, MissingConfigError  # noqa: E402

MODEL_NAME = "LATE_DELIVERY_RISK"
DATABASE, SCHEMA = "RETAIL_OLIST", "ML"
FEATURES = ldb.NUMERIC_V1 + ldb.CATEGORICAL
BACKTEST_METRICS = ROOT / "reports" / "snowflake" / "late_delivery_metrics.json"
EVIDENCE = ROOT / "reports" / "snowflake" / "model_registry.json"
PARITY_SAMPLE = 2000
PARITY_TOLERANCE = 1e-9


def git_sha() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def training_frame(db) -> pd.DataFrame:
    df = ldb.load(db)
    return df[df["purchase_ts"] >= ldb.TRAIN_START].reset_index(drop=True)


def fit(train: pd.DataFrame):
    model = ldb.make_models(ldb.NUMERIC_V1, "v1")["logistic_regression_v1"]
    return model.fit(train[FEATURES], train["is_late"])


def backtest_metrics() -> dict:
    """The out-of-time v1 metrics from the Snowflake-backed backtest (macro average over the six test months)."""
    m = json.loads(BACKTEST_METRICS.read_text(encoding="utf-8"))["macro_average"]["logistic_regression_v1"]
    return {k: float(v) for k, v in m.items() if isinstance(v, (int, float))}


def version_name(sha: str, today: str) -> str:
    return f"V1_{today}_{sha}".upper()


def warehouse_parity(mv, model, sample: pd.DataFrame) -> dict:
    """Score `sample` inside Snowflake with the registered version and compare with the local model."""
    remote = mv.run(sample, function_name="predict_proba")
    prob_cols = [c for c in remote.columns if c not in sample.columns]
    remote_p1 = remote[prob_cols[-1]].astype(float).to_numpy()  # last output column = P(late)
    local_p1 = model.predict_proba(sample)[:, 1]
    diff = np.abs(remote_p1 - local_p1)
    return {"rows": int(len(sample)), "output_columns": prob_cols, "max_abs_diff": float(diff.max()),
            "within_tolerance": bool(diff.max() <= PARITY_TOLERANCE), "tolerance": PARITY_TOLERANCE}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--yes", action="store_true", help="confirm the printed Snowflake target and connect")
    parser.add_argument("--register", action="store_true", help="log a new model version (default: train only)")
    args = parser.parse_args(argv)

    try:
        db = connect("snowflake", confirm=args.yes)
    except (ConfirmationRequired, MissingConfigError) as exc:
        print(exc, file=sys.stderr)
        return 1

    import sklearn

    with db:
        train = training_frame(db)
        model = fit(train)
        metrics = backtest_metrics()
        sha = git_sha()
        today = datetime.now(UTC).strftime("%Y%m%d")
        version = version_name(sha, today)
        summary = {
            "model_name": f"{DATABASE}.{SCHEMA}.{MODEL_NAME}",
            "version_name": version,
            "model": "v1 logistic regression (src/ml/late_delivery_baseline.py make_models)",
            "features": FEATURES,
            "feature_table": f"{DATABASE}.MARTS.MART_LATE_DELIVERY_FEATURES",
            "training_rows": int(len(train)),
            "training_late_rate": round(float(train["is_late"].mean()), 6),
            "training_window": [str(train["purchase_ts"].min()), str(train["purchase_ts"].max())],
            "git_commit": sha,
            "scikit_learn": sklearn.__version__,
            "python": sys.version.split()[0],
            "evaluation": "rolling-origin backtest, 6 test months 2018-03..2018-08, each scored by a model trained only "
                          "on orders delivered before the month (reports/snowflake/late_delivery_metrics.json)",
            "backtest_macro_average": metrics,
        }
        print(json.dumps({k: v for k, v in summary.items() if k != "features"}, indent=1, default=str))
        if not args.register:
            print("dry run: nothing registered (add --register to log the version)")
            return 0

        from snowflake.ml.registry import Registry
        from snowflake.snowpark import Session

        session = Session.builder.configs({"connection": db.raw}).create()
        reg = Registry(session=session, database_name=DATABASE, schema_name=SCHEMA)
        existing = {m.name for m in reg.models()}
        if MODEL_NAME in existing and version in {v.version_name for v in reg.get_model(MODEL_NAME).versions()}:
            print(f"{MODEL_NAME} version {version} already exists; nothing replaced. Commit first for a new version.",
                  file=sys.stderr)
            return 2

        sample = train[FEATURES].sample(n=min(PARITY_SAMPLE, len(train)), random_state=0).reset_index(drop=True)
        mv = reg.log_model(
            model,
            model_name=MODEL_NAME,
            version_name=version,
            sample_input_data=sample.head(100),
            target_platforms=["WAREHOUSE"],
            conda_dependencies=[f"scikit-learn=={sklearn.__version__}"],
            comment=("Late-delivery risk at purchase time, v1 logistic regression. Use by rank (flag the riskiest X% "
                     "of a month), not as a calibrated probability: see docs/ml/MODEL_CARD.md."),
            metrics={**{f"backtest_{k}": v for k, v in metrics.items()},
                     "training_rows": summary["training_rows"], "git_commit": sha,
                     "feature_table": summary["feature_table"], "lifecycle_stage": "VALIDATED"},
        )
        model_ref = reg.get_model(MODEL_NAME)
        model_ref.default = version
        summary["registered_at"] = datetime.now(UTC).isoformat(timespec="seconds")
        summary["default_version"] = True
        print(f"registered {summary['model_name']} version {version} (now the default version)")

        try:
            summary["warehouse_parity"] = warehouse_parity(mv, model, sample)
            print(f"in-warehouse PREDICT_PROBA on {PARITY_SAMPLE:,} orders: max abs diff vs local "
                  f"{summary['warehouse_parity']['max_abs_diff']:.3e}")
        except Exception as exc:  # noqa: BLE001 - registration stands; record why scoring in Snowflake failed
            summary["warehouse_parity"] = {"error": f"{type(exc).__name__}: {exc}"[:2000]}
            print(f"registered, but scoring inside Snowflake failed: {summary['warehouse_parity']['error'][:500]}",
                  file=sys.stderr)

        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(summary, indent=1, default=str) + "\n", encoding="utf-8")
        print(f"wrote {EVIDENCE.relative_to(ROOT)}")
        ok = summary["warehouse_parity"].get("within_tolerance") is True
        return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
