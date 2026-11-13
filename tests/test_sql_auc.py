"""The rank-based ROC-AUC used by snowflake/dbt/models/monitoring/mon_feature_auc_by_month.sql equals scikit-learn's,
ties included. Run here in DuckDB with the same window-function formula (CASE in place of Snowflake's IFF)."""

import duckdb
import numpy as np
import pytest
from sklearn.metrics import roc_auc_score

FORMULA = """
with ranked as (
    select g, y, rank() over (partition by g order by x) + (count(*) over (partition by g, x) - 1) / 2.0 as avg_rank
    from t
)
select g,
       (sum(case when y = 1 then avg_rank else 0 end) - sum(y) * (sum(y) + 1) / 2.0)
           / nullif(sum(y) * (count(*) - sum(y)), 0) as auc
from ranked group by g order by g
"""


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_sql_auc_equals_sklearn_with_ties(seed):
    rng = np.random.default_rng(seed)
    n = 3000
    g = rng.integers(0, 4, n)
    x = rng.integers(0, 25, n).astype(float)          # heavy ties, like promised_days
    y = (rng.random(n) < 0.08 + 0.01 * x / 5).astype(int)
    con = duckdb.connect()
    con.register("t_df", __import__("pandas").DataFrame({"g": g, "x": x, "y": y}))
    con.execute("create table t as select * from t_df")
    got = dict(con.execute(FORMULA).fetchall())
    for grp in range(4):
        mask = g == grp
        assert got[grp] == pytest.approx(roc_auc_score(y[mask], x[mask]), abs=1e-12)


def test_formula_text_matches_the_dbt_model():
    from pathlib import Path

    model = (Path(__file__).resolve().parents[1] / "snowflake" / "dbt" / "models" / "monitoring"
             / "mon_feature_auc_by_month.sql").read_text(encoding="utf-8")
    assert "+ (count(*) over (partition by month, feature, x) - 1) / 2.0 as avg_rank" in model
    assert "(sum(iff(is_late = 1, avg_rank, 0)) - sum(is_late) * (sum(is_late) + 1) / 2.0)" in model
    assert "/ nullif(sum(is_late) * (count(*) - sum(is_late)), 0) as roc_auc" in model
