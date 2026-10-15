"""The files exported for Power BI agree with the warehouse, the stored model metrics and the dashboard mock-up."""

import json

import duckdb
import pandas as pd
import pytest
from sklearn.metrics import average_precision_score

import build_mockup_html
import model_spec as ms
from conftest import ROOT

pytestmark = pytest.mark.warehouse

DATA = ROOT / "powerbi" / "data"


@pytest.fixture(scope="module")
def manifest():
    if not (DATA / "_manifest.json").exists():
        pytest.skip("powerbi/data not exported; run src/powerbi/export_data.py")
    return json.loads((DATA / "_manifest.json").read_text(encoding="utf-8"))


def test_every_table_in_the_model_has_an_exported_file(manifest):
    assert set(manifest) == {t.name for t in ms.TABLES}
    for t in ms.TABLES:
        assert manifest[t.name]["file"] == t.file and (DATA / t.file).exists()


def test_row_counts_equal_the_warehouse(manifest, warehouse):
    for name in ("fact_orders", "fact_order_items", "fact_payments", "fact_reviews", "dim_date", "dim_customer", "dim_product", "dim_seller", "dim_geography"):
        assert manifest[name]["rows"] == warehouse.execute(f"select count(*) from {name}").fetchone()[0], name


def test_manifest_row_counts_equal_the_files(manifest):
    con = duckdb.connect(":memory:")
    for name, m in manifest.items():
        reader = f"read_parquet('{(DATA / m['file']).as_posix()}')" if m["format"] == "parquet" else f"read_csv('{(DATA / m['file']).as_posix()}', header=true)"
        assert con.execute(f"select count(*) from {reader}").fetchone()[0] == m["rows"], name


def test_no_fact_key_is_missing_from_its_dimension(manifest):
    con = duckdb.connect(":memory:")
    p = lambda n: f"read_parquet('{(DATA / (n + '.parquet')).as_posix()}')"  # noqa: E731
    c = lambda n: f"read_csv('{(DATA / (n + '.csv')).as_posix()}', header=true)"  # noqa: E731
    for r in ms.RELATIONSHIPS:
        many = p(r.many_table) if ms.TABLE_BY_NAME[r.many_table].fmt == "parquet" else c(r.many_table)
        one = p(r.one_table) if ms.TABLE_BY_NAME[r.one_table].fmt == "parquet" else c(r.one_table)
        orphans = con.execute(f"select count(*) from {many} m where m.{r.many_col} is not null and m.{r.many_col} not in (select {r.one_col} from {one})").fetchone()[0]
        assert orphans == 0, f"{r.many_table}.{r.many_col} has {orphans} values missing from {r.one_table}"
        if r.one_table != "dim_date":  # the one side of a relationship must be unique
            assert con.execute(f"select count({r.one_col}) = count(distinct {r.one_col}) from {one}").fetchone()[0], f"{r.one_table}.{r.one_col} not unique"


def test_review_comment_text_is_not_exported(manifest):
    cols = duckdb.connect(":memory:").execute(f"describe select * from read_parquet('{(DATA / 'fact_reviews.parquet').as_posix()}')").fetchall()
    assert not [c[0] for c in cols if "comment" in c[0] and c[0] != "has_comment"]


def test_exported_scores_reproduce_the_stored_pr_auc(manifest):
    scores = pd.read_parquet(DATA / "late_delivery_scores.parquet")
    stored = json.loads((ROOT / "reports" / "late_delivery_metrics.json").read_text(encoding="utf-8"))["macro_average"]["logistic_regression_v1"]["pr_auc"]
    macro = sum(average_precision_score(g["is_late"], g["risk_score"]) for _, g in scores.groupby("month")) / scores["month"].nunique()
    assert macro == pytest.approx(stored, abs=0.002)
    assert scores["order_id"].is_unique and scores["risk_percentile"].between(0, 1).all()


def test_mockup_cubes_add_up_to_the_specification_checks(manifest):
    """The mock-up embeds pre-aggregated cubes; summed over everything they must give the specification's expected values."""
    import mockup_data

    d = mockup_data.build()
    checks = {(c["measure"], c["context"]): c["value"] for c in ms.compute_checks()}
    assert sum(r[2] for r in d["sales"]) == checks[("Net Orders", "no filters")]
    assert sum(r[3] for r in d["sales"]) == pytest.approx(checks[("Net Revenue", "no filters")], abs=0.01)
    assert sum(r[2] for r in d["delivery"]) == checks[("Delivered Orders", "no filters")]
    assert sum(r[3] for r in d["delivery"]) / sum(r[2] for r in d["delivery"]) == pytest.approx(checks[("Late Rate %", "no filters")], abs=1e-9)
    assert sum(r[4][2] for r in d["risk"]) == checks[("Flagged Orders", "flag_share[flag_pct] = 10 (default)")]  # flags alternate count, late per share: 5%, 10%, ...
    assert d["customers_total"] > 0
    html = build_mockup_html.render()
    assert "Power BI" in html and "http://" not in html.replace("http://www.w3.org", "") and "https://" not in html
