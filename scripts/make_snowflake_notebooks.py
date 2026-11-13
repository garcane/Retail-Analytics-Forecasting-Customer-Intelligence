"""Generate the Snowflake versions of the ML notebooks (Notebooks in Workspaces) from the originals.

    python scripts/make_snowflake_notebooks.py           # writes notebooks/snowflake/*.ipynb
    python scripts/make_snowflake_notebooks.py --check   # exit 1 if the committed copies are out of date

02 and 03 are the original notebooks with only the data access changed: instead of opening warehouse.duckdb they use
the notebook's own Snowflake session (src/data_access/snowpark.py), so ldb.load / fb.weekly_series read the dbt marts.
Every other cell is copied unchanged, and a last cell checks the numbers against the committed metrics. 04 trains the
v1 model inside Snowflake and registers it (snowflake/ml/register_model.py helpers). Edit the originals or this script,
never the generated files. Outputs are not stored: the notebooks are run inside Snowflake.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "notebooks" / "snowflake"
PINNED = ["scikit-learn==1.9.1", "snowflake-ml-python==2.8.0", "duckdb"]

INSTALL = (
    "# Snowflake only. The container runtime ships its own package versions. The results depend on scikit-learn 1.9.1\n"
    "# (the laptop's version and the registered model's), and the project modules import duckdb at module level.\n"
    "# Same list as notebooks/snowflake/requirements.txt. If this installs anything, restart the kernel once.\n"
    f"%pip install -q {' '.join(PINNED)}"
)

BANNER = (
    "> **Snowflake version**, generated from `notebooks/{original}` by `scripts/make_snowflake_notebooks.py` "
    "(do not edit by hand). It reads the dbt marts in `RETAIL_OLIST` through the notebook's own session instead of "
    "`warehouse.duckdb`; every analysis cell is the original. Run it as role `RETAIL_TRANSFORMER` on a CPU compute pool "
    "with query warehouse `RETAIL_WH`, and **suspend the notebook service when you are done** (the compute pool bills "
    "while it runs). The last cell checks the results against the committed metrics.\n\n"
)

CONNECT = (
    "from data_access.snowpark import from_active_session  # noqa: E402\n"
    "\n"
    "db = from_active_session()   # this notebook's own Snowflake session: no keys, no passwords\n"
    'print(f"database {db.target.database}, role {db.target.role}, warehouse {db.target.warehouse}")\n'
    "import scipy, sklearn  # noqa: E402,E401\n"
    'print(f"numpy {np.__version__}, scipy {scipy.__version__}, pandas {pd.__version__}, scikit-learn {sklearn.__version__}")\n'
    'assert sklearn.__version__ == "1.9.1", f"scikit-learn {sklearn.__version__}: run the install cell, then restart"\n'
)

VERIFY_02 = '''# Snowflake check. The metrics above were computed from Snowflake data. Against the Snowflake-backed backtest committed
# in reports/snowflake/ (same data, same code) the only differences come from the numeric libraries: the logistic
# regression is fitted by scipy's L-BFGS, and this runtime's numpy/scipy are not the laptop's (measured 2026-11-13:
# 0.0 on the laptop, 1.3e-09 in a Snowflake workspace). Against the DuckDB reference add the float-summation noise of
# the features (about 6e-6).
def per_month(path):
    rows = json.loads((ROOT / path).read_text(encoding="utf-8"))["per_month"]["logistic_regression_v1"]
    return pd.DataFrame(rows).set_index("month")


cols = ["n", "base_rate", "pr_auc", "roc_auc", "brier", "precision_at_top", "recall_at_top"]
for path, tol in [("reports/snowflake/late_delivery_metrics.json", 1e-6), ("reports/late_delivery_metrics.json", 1e-5)]:
    ref = per_month(path).loc[summary.index, cols]
    gap = float((summary[cols].astype(float) - ref.astype(float)).abs().max().max())
    print(f"{path}: largest difference {gap:.2e} (allowed {tol:g})")
    assert gap <= tol, path
print("checks passed")'''

VERIFY_03 = '''# Snowflake check. The weekly series from Snowflake equals the DuckDB one (reconciled 0-diff), so the methods with a
# closed form must reproduce the committed DuckDB reference (reports/forecast_models_metrics.json) exactly. The methods
# fitted with scipy.optimize can move slightly with the numpy/scipy version (measured 2026-11-13 in a Snowflake
# workspace: damped trend 3.5e-07, AR(1) 1.3e-11, exponential smoothing 2.3e-13; 0.0 on the laptop).
import json

ref = json.loads((ROOT / "reports" / "forecast_models_metrics.json").read_text(encoding="utf-8"))
OPTIMISED = {"simple_exp_smoothing", "damped_trend", "ar1_trend_26w"}
worst = {}
for (target, h), sc in scores.items():
    r = ref[f"{target} | main (to 2018-08-13) | h={h}"]
    for method, values in sc.items():
        if method.startswith("_"):
            continue
        for key in ("mae", "mape", "mae_vs_naive", "bias"):
            gap = abs(values[key] - r[method][key]) / max(1.0, abs(r[method][key]))
            worst[method] = max(worst.get(method, 0.0), gap)
for method, gap in sorted(worst.items()):
    tol = 1e-6 if method in OPTIMISED else 1e-9
    print(f"{method:22s} largest relative difference {gap:.2e} (allowed {tol:g})")
    assert gap <= tol, method
print("checks passed")'''


def code(src: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": src}


def md(src: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": src}


def text(cell: dict) -> str:
    return "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]


def must_replace(src: str, old: str, new: str) -> str:
    if src.count(old) != 1:
        raise SystemExit(f"generator out of date: expected exactly one {old[:60]!r} in the original notebook")
    return src.replace(old, new)


def port(original: str, setup_edits: list[tuple[str, str]], verify: str, path_edits: list[tuple[str, str]]) -> dict:
    nb = json.loads((ROOT / "notebooks" / original).read_text(encoding="utf-8"))
    cells = []
    for i, cell in enumerate(nb["cells"]):
        cell = copy.deepcopy(cell)
        src = text(cell)
        if i == 0:
            cell = md(BANNER.format(original=original) + src.replace("](../", "](../../"))
        elif cell["cell_type"] == "markdown":
            cell = md(src.replace("](../", "](../../"))
        elif i == 1:
            for old, new in setup_edits:
                src = must_replace(src, old, new)
            cells.append(code(INSTALL))
            cell = code(src)
        else:
            for old, new in path_edits:
                if old in src:
                    src = src.replace(old, new)
            cell = code(src)
        cells.append(cell)
    cells.append(code(verify))
    nb["cells"] = cells
    nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                      "language_info": {"name": "python"}}
    return nb


COMMON_SETUP = [
    ("import duckdb\n", ""),
    ('sys.path.insert(0, str(ROOT / "src" / "ml"))', 'sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "ml")]'),
]


def nb02() -> dict:
    return port(
        "02_late_delivery_model.ipynb",
        COMMON_SETUP + [
            ('WAREHOUSE = ROOT / "warehouse.duckdb"\nif not WAREHOUSE.exists():\n    raise FileNotFoundError('
             '"warehouse.duckdb not found. Run: uv run python src/transformation/build_warehouse.py")\n', CONNECT),
            ("con = duckdb.connect(str(WAREHOUSE), read_only=True)\n"
             "df = ldb.load(con)          # one row per delivered order: features known at purchase, plus the label\n"
             "con.close()\n",
             "df = ldb.load(db)           # MARTS.MART_LATE_DELIVERY_FEATURES: one row per delivered order\n"),
        ],
        VERIFY_02,
        # the experiment comparison reads the Snowflake-backed backtest; drift_metrics.json stays the DuckDB reference
        [('ROOT / "reports" / "late_delivery_metrics.json"', 'ROOT / "reports" / "snowflake" / "late_delivery_metrics.json"'),
         ('drift = json.loads((ROOT / "reports" / "drift_metrics.json")',
          '# DuckDB reference: drift_analysis.py is not ported; the SQL monitoring views cover the raw-feature part\n'
          'drift = json.loads((ROOT / "reports" / "drift_metrics.json")')],
    )


def nb03() -> dict:
    return port(
        "03_weekly_forecast.ipynb",
        COMMON_SETUP + [
            ('WAREHOUSE = ROOT / "warehouse.duckdb"\nif not WAREHOUSE.exists():\n    raise FileNotFoundError('
             '"warehouse.duckdb not found. Run: uv run python src/transformation/build_warehouse.py")\n', CONNECT),
            ("con = duckdb.connect(str(WAREHOUSE), read_only=True)\n"
             "weekly = fb.weekly_series(con)   # orders and net item revenue per ISO week\n"
             "con.close()\n",
             "weekly = fb.weekly_series(db)    # MARTS.MART_WEEKLY_ORDERS_REVENUE: orders and net item revenue per ISO week\n"),
        ],
        VERIFY_03,
        [],
    )


NB04_CELLS = [
    md("# 04 - Train and register the late-delivery model inside Snowflake\n\n"
       "> Generated by `scripts/make_snowflake_notebooks.py`. Run as role `RETAIL_TRANSFORMER` on a CPU compute pool "
       "with query warehouse `RETAIL_WH`; **suspend the notebook service when done**.\n\n"
       "This trains the v1 logistic regression on `MARTS.MART_LATE_DELIVERY_FEATURES` **here, in Snowflake**, and logs it "
       "to the Model Registry as a new version of `RETAIL_OLIST.ML.LATE_DELIVERY_RISK` named `V1WS_<date>_<tag>` "
       "(`WS` = trained in a Snowflake workspace). It never replaces a version and never changes the default version. "
       "Its quality figures are the out-of-time backtest (`reports/snowflake/late_delivery_metrics.json`): a model trained "
       "on every month has no honest held-out score of its own, and its scores for 2018 orders are in-sample.\n\n"
       "The last cells score every training order with the new version three ways (in this notebook, `mv.run`, and SQL "
       "`MODEL(...)!PREDICT_PROBA`) and compare them, and with the laptop-registered version."),
    code(INSTALL),
    code("import hashlib\n"
         "import sys\n"
         "from datetime import UTC, datetime\n"
         "from pathlib import Path\n\n"
         'ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "pyproject.toml").exists())\n'
         'sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "ml"), str(ROOT / "snowflake" / "ml")]\n'
         "import numpy as np  # noqa: E402\n"
         "import sklearn  # noqa: E402\n"
         "import register_model as rm  # noqa: E402\n"
         "from data_access.snowpark import from_active_session  # noqa: E402\n\n"
         "db = from_active_session()\n"
         'print(f"database {db.target.database}, role {db.target.role}, warehouse {db.target.warehouse}")\n'
         'assert db.target.role == "RETAIL_TRANSFORMER", "run as RETAIL_TRANSFORMER so it owns what it creates"\n'
         'assert sklearn.__version__ == "1.9.1", f"scikit-learn {sklearn.__version__}: run the install cell, then restart"\n'
         "session = db.session\n"
         'session.use_schema(f"{rm.DATABASE}.{rm.SCHEMA}")  # mv.run uploads its input here'),
    code("train = rm.training_frame(db)          # labelled orders from 2017 on, read from the dbt mart\n"
         "model = rm.fit(train)                   # the v1 pipeline from src/ml/late_delivery_baseline.py\n"
         "sample = rm.parity_sample(train)\n"
         "metrics = rm.backtest_metrics()\n"
         'print(f"trained on {len(train):,} orders, late rate {train[\'is_late\'].mean():.3f}")'),
    code("# Provenance: the git commit if this workspace has one, otherwise a hash of the model code plus a fingerprint of\n"
         "# the training data. Either way the version name says exactly what was trained on what.\n"
         "commit = rm.git_sha()\n"
         'code_files = sorted((ROOT / "src" / "ml").glob("late_delivery_baseline.py")) + sorted((ROOT / "src" / "data_access").glob("*.py")) \\\n'
         '    + [ROOT / "snowflake" / "ml" / "register_model.py"]\n'
         "code_hash = hashlib.sha256(b\"\".join(p.read_bytes() for p in code_files)).hexdigest()\n"
         "data_fp = db.read_sql(\"select count(*) as n, max(purchase_ts) as last_ts, hash_agg(*) as h \"\n"
         '                      "from MARTS.MART_LATE_DELIVERY_FEATURES where purchase_ts >= \'2017-01-01\'").iloc[0]\n'
         'tag = commit if commit != "unknown" else hashlib.sha256(f"{code_hash}|{data_fp.to_dict()}".encode()).hexdigest()[:7]\n'
         'version = f"V1WS_{datetime.now(UTC):%Y%m%d}_{tag}".upper()\n'
         'print("commit", commit, "| code", code_hash[:12], "| data", data_fp.to_dict(), "| version", version)'),
    code("from snowflake.ml.registry import Registry\n\n"
         "reg = Registry(session=session, database_name=rm.DATABASE, schema_name=rm.SCHEMA)\n"
         'assert version not in rm.versions(reg), f"{version} already exists; nothing replaced"\n'
         "mv = reg.log_model(model, **rm.log_kwargs(version, sample, metrics, sklearn.__version__, {\n"
         '    "training_rows": len(train), "source": "snowflake-workspace-notebook", "git_commit": commit,\n'
         '    "code_sha256": code_hash, "training_data_rows": int(data_fp["n"]), "training_data_hash": str(data_fp["h"])}))\n'
         'print("registered", version, "(not set as default)")'),
    code("# Three ways to score the same orders with the new version, plus the laptop-registered version.\n"
         'local = train[["order_id"]].assign(local=model.predict_proba(train[rm.FEATURES])[:, 1])\n'
         "run = rm.warehouse_parity(mv, model, sample)                       # mv.run on 2,000 orders\n"
         "where = \" where purchase_ts >= '2017-01-01'\"\n"
         'sql_new = db.read_sql(rm.predict_proba_sql(version) + where).rename(columns={"risk_score": "sql_new"})\n'
         'sql_v1 = db.read_sql(rm.predict_proba_sql("V1_20261113_CC90DC8") + where).rename(columns={"risk_score": "sql_laptop"})\n'
         'm = local.merge(sql_new, on="order_id").merge(sql_v1, on="order_id")\n'
         "result = {\n"
         '    "rows": len(m),\n'
         '    "mv_run_vs_notebook": run["max_abs_diff"],\n'
         '    "sql_vs_notebook": float(np.abs(m["sql_new"] - m["local"]).max()),\n'
         '    "new_vs_laptop_version": float(np.abs(m["sql_new"] - m["sql_laptop"]).max()),\n'
         "}\n"
         "print(result)\n"
         "for k in (\"mv_run_vs_notebook\", \"sql_vs_notebook\", \"new_vs_laptop_version\"):\n"
         '    mv.set_metric(f"parity_{k}", result[k])\n'
         'assert len(m) == len(train) and result["mv_run_vs_notebook"] <= 1e-12 and result["sql_vs_notebook"] <= 1e-12'),
]


def nb04() -> dict:
    return {"cells": copy.deepcopy(NB04_CELLS), "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}


NOTEBOOKS = {
    "02_late_delivery_model_sf.ipynb": nb02,
    "03_weekly_forecast_sf.ipynb": nb03,
    "04_train_register_sf.ipynb": nb04,
}


def render(nb: dict) -> str:
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    stale = []
    files = {name: render(build()) for name, build in NOTEBOOKS.items()}
    files["requirements.txt"] = "\n".join(PINNED) + "\n"
    for name, content in files.items():
        path = OUT / name
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(name)
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8", newline="\n")
            print(f"wrote {path.relative_to(ROOT)}")
    if stale:
        print("out of date (run scripts/make_snowflake_notebooks.py): " + ", ".join(stale), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
