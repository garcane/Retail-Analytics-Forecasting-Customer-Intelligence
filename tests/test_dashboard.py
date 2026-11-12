"""The HTML dashboard (dashboard/) and its data builder (src/dashboard/build_data.py).

Structure: HTML, CSS and JS stay in separate files; every module parses; every registered page exists.
Builder: JSON cleaning, the reconciliation-report parser, Snowflake mart reads put in the reference order,
the Snowflake-by-default gate, and that the committed data holds no account identifiers.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "dashboard"
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "src" / "dashboard"), str(ROOT / "src" / "ml")]

import build_data  # noqa: E402


# ------------------------------------------------------------------------------------------- separation of concerns
def test_index_html_has_no_inline_style_or_script():
    html = (DASH / "index.html").read_text(encoding="utf-8")
    assert "<style" not in html.lower()
    assert not re.search(r"\sstyle\s*=", html, re.I), "no style= attributes in the HTML"
    for tag in re.findall(r"<script\b[^>]*>(.*?)</script>", html, re.S | re.I):
        assert not tag.strip(), "scripts must be external files"
    assert not re.search(r"\son[a-z]+\s*=", html, re.I), "no inline event handlers"


def test_every_stylesheet_is_linked_and_exists():
    html = (DASH / "index.html").read_text(encoding="utf-8")
    linked = {h for h in re.findall(r'<link rel="stylesheet" href="([^"]+)"', html) if not h.startswith("http")}
    on_disk = {p.relative_to(DASH).as_posix() for p in (DASH / "css").rglob("*.css")}
    assert linked == on_disk


def test_every_page_and_insight_module_imported_exists():
    for index in ("js/pages/index.js", "js/insights/index.js"):
        text = (DASH / index).read_text(encoding="utf-8")
        for rel in re.findall(r'import "\./([^"]+)";', text):
            assert (DASH / index).parent.joinpath(rel).exists(), f"{index} imports missing {rel}"
    pages = re.findall(r'import "\./([^"]+)";', (DASH / "js/pages/index.js").read_text(encoding="utf-8"))
    on_disk = {p.name for p in (DASH / "js/pages").glob("*.js")} - {"index.js"}
    assert set(pages) == on_disk, "every page module is registered, and every registered page exists"


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
@pytest.mark.parametrize("path", sorted(p.relative_to(DASH).as_posix() for p in (DASH / "js").rglob("*.js")))
def test_every_js_file_parses(path):
    src = (DASH / path).read_text(encoding="utf-8")
    args = ["node", "--check", str(DASH / path)] if path.endswith("boot-check.js") else ["node", "--input-type=module", "--check"]
    r = subprocess.run(args, input=None if path.endswith("boot-check.js") else src, capture_output=True, text=True,
                       encoding="utf-8")
    assert r.returncode == 0, r.stderr


def test_no_innerhtml_in_dashboard_code():
    """Labels come from data files; all text goes in through textContent (core/dom.js)."""
    for p in (DASH / "js").rglob("*.js"):
        lines = p.read_text(encoding="utf-8").splitlines()
        code = "\n".join(line for line in lines if not line.lstrip().startswith("//"))
        assert not re.search(r"\.(innerHTML|outerHTML)\s*[+]?=|insertAdjacentHTML|document\.write", code), p


# --------------------------------------------------------------------------------------------------------- builder
def test_clean_makes_values_json_safe():
    raw = {"a": float("nan"), "b": np.int64(3), "c": [np.float64(1.23456789), pd.NA, pd.NaT],
           "d": pd.Timestamp("2018-01-02 03:04:05"), "e": float("inf")}
    out = build_data.clean(raw)
    assert out == {"a": None, "b": 3, "c": [1.234568, None, None], "d": "2018-01-02T03:04:05", "e": None}
    json.dumps(out)


def test_lineage_parser_reads_a_live_report_and_flags_the_stub(tmp_path, monkeypatch):
    report = tmp_path / "docs" / "validation"
    report.mkdir(parents=True)
    (report / "RECONCILIATION_REPORT.md").write_text(
        "# Reconciliation report: DuckDB vs Snowflake\n\n## Run\n\n| item | value |\n|---|---|\n"
        "| generated | 2026-11-12 15:39:23 UTC |\n| mode | snowflake |\n| secret | must-not-appear |\n\n"
        "## Summary\n\nPASS: 1 (of 1 checks)\n\n| check | group | status | left rows | right rows | missing+extra keys | unexplained value diffs | classified | error |\n"
        "|---|---|---|---|---|---|---|---|---|\n| dim_seller | dimension | PASS | 3096 | 3096 | 0 | 0 | 0 |  |\n",
        encoding="utf-8")
    monkeypatch.setattr(build_data, "ROOT", tmp_path)
    lin = build_data.lineage()
    assert lin["not_run"] is False
    assert lin["checks"] == [{"check": "dim_seller", "group": "dimension", "status": "PASS", "left_rows": "3096",
                              "right_rows": "3096", "missing_extra": "0", "unexplained": "0"}]
    assert lin["run"] == {"generated": "2026-11-12 15:39:23 UTC", "mode": "snowflake"}, "only whitelisted run fields"
    (report / "RECONCILIATION_REPORT.md").write_text("# Reconciliation report\n\nNOT RUN\n", encoding="utf-8")
    assert build_data.lineage()["not_run"] is True


class _FakeSnowflake:
    """Returns each mart shuffled, with upper-case columns and Decimal money, as the connector would."""
    backend = "snowflake"

    def read_sql(self, sql, params=None):
        name = re.search(r"mart_(\w+)", sql).group(1)
        ref = pd.read_csv(build_data.REPORTS / "analytics" / build_data.ANALYTICS[name])
        df = ref.sample(frac=1, random_state=7).reset_index(drop=True)
        for c in df.columns:
            if df[c].dtype == float:
                df[c] = df[c].map(lambda v: None if pd.isna(v) else Decimal(str(v))).astype(object)
        df.columns = [c.upper() for c in df.columns]
        return df


def test_snowflake_analytics_marts_are_put_in_the_reference_order():
    from_csv = build_data.analytics_tables(None)
    from_sf = build_data.analytics_tables(_FakeSnowflake(), "MARTS.")
    for key in build_data.ANALYTICS:
        assert from_sf[key]["columns"] == from_csv[key]["columns"], key
        first = from_csv[key]["columns"][0]
        assert [r[first] for r in from_sf[key]["rows"]] == [r[first] for r in from_csv[key]["rows"]], key
        assert from_sf[key]["source"] == f"Snowflake MARTS.mart_{key}"


def test_dashboard_builds_from_snowflake_by_default_and_needs_confirmation(monkeypatch, capsys, tmp_path):
    for name in ("DASHBOARD_BACKEND", "SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH", "RETAIL_SF_CONFIRM"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(sys, "argv", ["build_data", "--out", str(tmp_path / "out")])
    assert build_data.main() == 1
    err = capsys.readouterr().err
    assert "SNOWFLAKE_ACCOUNT" in err and "--backend duckdb" in err
    assert not (tmp_path / "out" / "manifest.json").exists()


# ------------------------------------------------------------------------------------------- committed data files
def test_committed_dashboard_data_is_complete_and_holds_no_identifiers():
    manifest = json.loads((DASH / "data" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["backend"] in ("snowflake", "duckdb")
    for name, entry in manifest["datasets"].items():
        path = DASH / "data" / entry["file"]
        assert path.exists(), name
        json.loads(path.read_text(encoding="utf-8"))
    for p in (DASH / "data").glob("*.json"):
        text = p.read_text(encoding="utf-8")
        assert "snowflakecomputing.com" not in text.lower(), p
        assert not re.search(r"\"(account|user|private_key\w*|passphrase)\"\s*:", text, re.I), p
        assert "review_comment" not in text, f"{p}: review text must not be exported"


# ------------------------------------------------------------------------------------- order category (risk page)
def test_order_category_matches_keys_sql_on_the_mini_warehouse(mini):
    from data_access import datasets, wrap_duckdb
    from drift_analysis import KEYS_SQL

    mini.con.execute("insert into dim_product values (2, 500, 1000, 2, 'watches_gifts'), (3, 500, 1000, 2, 'art')")
    a = mini.add_order(pd.Timestamp("2018-01-01"), pd.Timestamp("2018-01-05"), late=False)
    mini.con.execute("delete from fact_order_items where order_id = ?", [a])
    mini.con.execute("insert into fact_order_items values (?, 1, 2, 50, 5, 2, 1), (?, 1, 3, 50, 5, 2, 1)", [a, a])
    mini.add_order(pd.Timestamp("2018-01-02"), pd.Timestamp("2018-01-06"), late=True)
    mini.con.execute("create table dim_customer as select 1 as customer_key")  # KEYS_SQL does not need it; harmless
    got = datasets.order_category(wrap_duckdb(mini.con)).set_index("order_id")["category"]
    want = mini.con.execute(KEYS_SQL).df().set_index("order_id")["category"].sort_index()
    assert got.sort_index().equals(want)
    assert got[a] == "art", "price ties resolve to the alphabetically first category (DD-21)"


def test_order_category_reads_the_snowflake_intermediate_model():
    from data_access import datasets

    seen = {}

    class Fake:
        backend = "snowflake"

        def read_sql(self, sql, params=None):
            seen["sql"] = sql
            # the data_access wrapper lower-cases column names before a dataset sees them
            return pd.DataFrame({"order_id": ["b", "a"], "category": ["toys", "art"]})

    df = datasets.order_category(Fake())
    assert "INTERMEDIATE.int_late_delivery_item_agg" in seen["sql"]
    assert list(df.columns[:2]) == ["order_id", "category"]
