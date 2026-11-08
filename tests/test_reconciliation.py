"""Offline tests for src/reconciliation: comparison modes, exact defect detection, registry sanity, report and CLI guards.

Nothing here connects to Snowflake. The optional real-warehouse test is skipped when the DuckDB file is absent.
"""

import os
import re
import sys
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import duckdb
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:  # the pyproject pythonpath normally provides this
    sys.path.insert(0, str(ROOT / "src"))

from reconciliation import checks as C  # noqa: E402
from reconciliation import cli  # noqa: E402
from reconciliation import compare as K  # noqa: E402
from reconciliation import fetch as F  # noqa: E402
from reconciliation import report as R  # noqa: E402

STUB = ROOT / "docs" / "validation" / "RECONCILIATION_REPORT.md"


def frame(columns, rows):
    return F.frame_from_rows(columns, rows)


# ----------------------------------------------------------------------------- fixture for the generic comparator

COLS = ["id", "qty", "money", "flag", "name", "ts", "day", "ratio", "dist", "rate", "maybe"]


def base_rows(n=12):
    t0 = datetime(2018, 1, 1, 12, 0, 0)
    return [
        [i, i * 3, Decimal(f"{i}.50"), i % 2 == 0, f"name{i}", t0 + timedelta(hours=i), date(2018, 1, 1) + timedelta(days=i),
         1000.0 + i / 7, 500.0 + i / 3, 0.25 + i / 100, None if i % 3 == 0 else i * 2]
        for i in range(1, n + 1)
    ]


RULES = {"dist": C.absolute(C.ABS_DISTANCE_KM), "rate": C.absolute(C.ABS_RATE),
         "ratio": C.REL}  # ``ratio`` made explicit; ``dist``/``rate`` are the abs modes


def rows_with(mutate=None, drop=(), extra=()):
    rows = [list(r) for r in base_rows()]
    if mutate:
        for key, col, value in mutate:
            rows[key - 1][COLS.index(col)] = value
    rows = [r for r in rows if r[0] not in drop]
    rows += [list(r) for r in extra]
    return rows


def cmp_(left_rows, right_rows, **kw):
    return K.compare_frames(frame(COLS, left_rows), frame(COLS, right_rows), ["id"], RULES, max_examples=50, **kw)


def mismatches(c):
    return {(col.column, k[0]) for col in c.columns for k, _, _ in col.examples} if c.n_unexplained else set()


# ----------------------------------------------------------------------------- comparator: identical

def test_identical_frames_pass_every_mode():
    c = cmp_(base_rows(), base_rows())
    assert c.passed and c.status == "PASS"
    assert c.matched_rows == 12 and c.missing_in_right == c.extra_in_right == 0
    assert c.rows_with_diff == 0 and c.n_unexplained == 0
    modes = {col.column: col.mode for col in c.columns}
    assert modes["money"] == "exact" and modes["dist"] == "abs" and modes["ratio"] == "rel" and modes["qty"] == "exact"


def test_default_mode_is_relative_for_floats_and_exact_otherwise():
    left = frame(["id", "x", "n"], [[1, 1.0, 5], [2, 2.0, 6]])
    right = frame(["id", "x", "n"], [[1, 1.0 + 5e-10, 5], [2, 2.0, 6]])
    c = K.compare_frames(left, right, ["id"])
    assert c.passed
    assert {r.column: r.mode for r in c.columns} == {"x": "rel", "n": "exact"}
    right2 = frame(["id", "x", "n"], [[1, 1.0 + 5e-9, 5], [2, 2.0, 6]])
    assert not K.compare_frames(left, right2, ["id"]).passed


# ----------------------------------------------------------------------------- comparator: exactly the injected defects

def test_perturbed_fixture_fails_on_exactly_the_injected_defects():
    right = rows_with(
        mutate=[
            (3, "money", Decimal("3.51")),          # value change: money is exact -> FAIL
            (4, "ratio", 1000.0 + 4 / 7 + 1e-12),   # float drift within rel 1e-9 -> pass
            (7, "ratio", (1000.0 + 7 / 7) * (1 + 1e-6)),  # drift outside -> FAIL
            (5, "dist", 500.0 + 5 / 3 + 5e-7),      # inside abs 1e-6 -> pass
            (6, "dist", 500.0 + 6 / 3 + 5e-5),      # outside -> FAIL
            (8, "name", None),                      # value vs null -> FAIL
            (9, "maybe", 99),                       # null vs value (row 9: maybe is None) -> FAIL
            (11, "flag", True),                     # boolean flip (row 11 was False) -> FAIL
        ],
        drop=(2,),                                  # missing key
        extra=[[99, 1, Decimal("1.00"), True, "x", datetime(2018, 1, 1), date(2018, 1, 1), 1.0, 1.0, 0.1, 1]],
    )
    left = base_rows()
    c = cmp_(left, right)

    assert not c.passed and c.status == "FAIL"
    assert c.missing_in_right == 1 and c.missing_examples == [(2,)]
    assert c.extra_in_right == 1 and c.extra_examples == [(99,)]
    assert c.matched_rows == 11
    assert mismatches(c) == {("money", 3), ("ratio", 7), ("dist", 6), ("name", 8), ("maybe", 9), ("flag", 11)}
    by_col = {col.column: col for col in c.columns}
    assert by_col["maybe"].n_null_mismatch == 1 and by_col["name"].n_null_mismatch == 1
    # float drift that stays inside tolerance is visible as a diff size, but is not a mismatch
    assert by_col["dist"].n_mismatch == 1 and by_col["dist"].max_abs_diff == pytest.approx(5e-5, rel=0.05)
    assert by_col["ratio"].n_mismatch == 1
    # missing / extra rows are not double-counted as value differences, and untouched columns are clean
    for clean in ("qty", "ts", "day", "rate"):
        assert by_col[clean].n_mismatch == 0
    assert c.rows_with_diff == 6


@pytest.mark.parametrize("mode,tol,inside,outside", [
    ("abs", 1e-6, 0.9e-6, 1.1e-6),
    ("abs", 1e-9, 0.9e-9, 1.1e-9),
    ("rel", 1e-9, 0.9e-9, 1.1e-9),
])
def test_tolerance_boundaries(mode, tol, inside, outside):
    rule = {"x": C.ColumnRule(mode, tol)}
    base = 1000.0 if mode == "rel" else 10.0
    delta = (lambda d: d * base) if mode == "rel" else (lambda d: d)
    left = frame(["id", "x"], [[1, base]])
    assert K.compare_frames(left, frame(["id", "x"], [[1, base + delta(inside)]]), ["id"], rule).passed
    assert not K.compare_frames(left, frame(["id", "x"], [[1, base + delta(outside)]]), ["id"], rule).passed


def test_exact_mode_semantics():
    ok = K.compare_values
    assert ok(Decimal("1.10"), Decimal("1.1"), "exact", 0)[0]            # scale is not a difference
    assert ok(5, Decimal("5.00"), "exact", 0)[0]                         # int vs Decimal (Snowflake NUMBER)
    assert ok(0.1, Decimal("0.1"), "exact", 0)[0]                        # float meets Decimal via shortest repr
    assert not ok(Decimal("10.00"), Decimal("10.01"), "exact", 0)[0]     # one cent is a failure
    assert not ok(0.1 + 0.2, 0.3, "exact", 0)[0]
    assert ok(True, True, "exact", 0)[0] and not ok(True, False, "exact", 0)[0]
    assert not ok(date(2018, 1, 1), datetime(2018, 1, 1), "exact", 0)[0]
    assert ok(datetime(2018, 1, 1, 1), datetime(2018, 1, 1, 1), "exact", 0)[0]
    assert not ok(datetime(2018, 1, 1, 1), datetime(2018, 1, 1, 1, 0, 1), "exact", 0)[0]
    assert ok(0.0, 0.0, "rel", 1e-9)[0]                                  # zero equals zero under rel


def test_null_semantics_and_nan():
    left = frame(["id", "x"], [[1, None], [2, float("nan")], [3, 1]])
    right = frame(["id", "x"], [[1, None], [2, None], [3, None]])
    c = K.compare_frames(left, right, ["id"])
    assert c.columns[0].n_mismatch == 1 and c.columns[0].n_null_mismatch == 1  # only row 3; NaN is treated as null


def test_schema_and_key_problems_are_reported_before_values():
    left = frame(["id", "a", "b"], [[1, 1, 1], [1, 2, 2], [2, 3, 3]])
    right = frame(["id", "a", "c"], [[1, 1, 1], [2, 3, 3], [2, 3, 3]])
    c = K.compare_frames(left, right, ["id"])
    assert c.columns_only_left == ["b"] and c.columns_only_right == ["c"]
    assert c.duplicate_keys_left == 1 and c.duplicate_keys_right == 1
    assert not c.passed


def test_composite_and_null_keys():
    left = frame(["a", "b", "v"], [[1, None, 1], [1, "x", 2]])
    right = frame(["a", "b", "v"], [[1, None, 1], [1, "x", 3]])
    c = K.compare_frames(left, right, ["a", "b"])
    assert c.matched_rows == 2 and c.columns[0].n_mismatch == 1 and c.missing_in_right == 0
    # Decimal / int / integral float keys meet
    c2 = K.compare_frames(frame(["k", "v"], [[Decimal("1"), 1]]), frame(["k", "v"], [[1.0, 1]]), ["k"])
    assert c2.passed and c2.matched_rows == 1


def test_surrogate_keys_are_reported_separately_and_do_not_decide_status():
    rules = {"sk": C.SURROGATE}
    left = frame(["nat", "sk", "v"], [["a", 1, 10], ["b", 2, 20]])
    right = frame(["nat", "sk", "v"], [["a", 2, 10], ["b", 1, 20]])
    c = K.compare_frames(left, right, ["nat"], rules)
    assert c.passed and c.status == "PASS"
    assert [s.column for s in c.surrogate_columns] == ["sk"] and c.surrogate_mismatches == 2
    assert [s.column for s in c.columns] == ["v"] and c.rows_with_diff == 0


def test_classifier_splits_tie_breaks_but_still_counts_them():
    left = frame(["order_id", "pay"], [["o1", "boleto"], ["o2", "card"], ["o3", "card"]])
    right = frame(["order_id", "pay"], [["o1", "card"], ["o2", "voucher"], ["o3", "card"]])
    cands = {"o1": {"boleto", "card"}, "o2": {"card", "boleto"}}
    def cls(key, a, b):
        return K.TIE_BREAK if key[0] in cands and a in cands[key[0]] and b in cands[key[0]] else None

    c = K.compare_frames(left, right, ["order_id"], classifiers={"pay": cls})
    col = c.columns[0]
    assert col.n_mismatch == 2 and col.tolerated == {K.TIE_BREAK: 1} and col.n_unexplained == 1
    assert not c.passed  # o2 voucher is not a tied candidate -> still a failure


# ----------------------------------------------------------------------------- fetch layer

def test_fetch_keeps_decimals_exact_and_lowercases_names():
    con = duckdb.connect(":memory:")
    con.execute("create table t as select 1::decimal(12,2) as \"Money\", 12345678901.23::decimal(18,2) as big, "
                "true as flag, null::double as nothing")
    df = F.DuckDBFetcher(con)("select * from t")
    assert list(df.columns) == ["money", "big", "flag", "nothing"]
    assert isinstance(df["big"][0], Decimal) and df["big"][0] == Decimal("12345678901.23")
    assert df["nothing"][0] is None and df["flag"][0] is True


@pytest.mark.parametrize("sql", [
    "select 1", "with a as (select 1) select * from a;", "-- comment\nselect 'drop table x'", "/* x */ select 1",
    "select review_creation_ts from t",
])
def test_read_only_guard_accepts_selects(sql):
    F.assert_read_only(sql)


@pytest.mark.parametrize("sql", [
    "drop table x", "delete from x", "insert into x select 1", "select 1; drop table x", "create table x as select 1",
    "update x set a = 1", "copy x to 'f'", "", "  ;", "put file:///x @s", "merge into a using b on true",
])
def test_read_only_guard_rejects_everything_else(sql):
    with pytest.raises(F.ReadOnlyViolation):
        F.assert_read_only(sql)


def test_account_redaction_and_settings(monkeypatch):
    assert F.redact_account("ab12345.eu-west-1") == "ab***-1"
    assert "12345" not in F.redact_account("ab12345.eu-west-1")
    env = {"SNOWFLAKE_ACCOUNT": "acct-secret-1", "SNOWFLAKE_USER": "someone", "SNOWFLAKE_PRIVATE_KEY_PATH": "k.p8"}
    s = F.resolve_snowflake_settings(env)
    assert (s.role, s.warehouse, s.database, s.schema_prefix) == ("RETAIL_TRANSFORMER", "RETAIL_WH", "RETAIL_OLIST", "")
    assert F.resolve_snowflake_settings({**env, "DBT_DEV_SUFFIX": "gappeah"}).schema_prefix == "GAPPEAH_"
    with pytest.raises(RuntimeError) as err:
        F.resolve_snowflake_settings({})
    assert "SNOWFLAKE_ACCOUNT" in str(err.value) and "acct-secret" not in str(err.value)
    assert "acct-secret-1" not in F.redact_secrets("failed for acct-secret-1 as someone", env)
    assert "someone" not in F.redact_secrets("failed for acct-secret-1 as someone", env)
    with pytest.raises(ValueError):
        F.resolve_snowflake_settings(env, database="x; drop")


# ----------------------------------------------------------------------------- registry

def test_registry_covers_the_contract():
    names = {c.name for c in C.all_checks()}
    assert len(names) == len(C.all_checks())
    for dim in ("dim_customer", "dim_date", "dim_geography", "dim_product", "dim_seller"):
        assert dim in names
    for fact in ("fact_orders", "fact_order_items", "fact_payments", "fact_reviews"):
        assert fact in names
    for mart in ("mart_monthly_kpis", "mart_category_performance", "mart_state_performance", "mart_seller_concentration",
                 "mart_delivery_vs_reviews", "mart_payments", "mart_repeat_customers", "mart_delivery_trend",
                 "mart_late_delivery_features", "mart_weekly_orders_revenue", "headline_numbers", "row_counts"):
        assert mart in names


def test_headline_constants_are_the_documented_ones():
    exp = {c.name: c.expected for c in C.all_checks() if c.expected}
    h = {k: v.value for k, v in exp["headline_numbers"].items()}
    assert h["net_revenue"] == Decimal("13494400.74") and h["net_orders"] == 98199
    assert h["late_orders"] == 7827 and h["labelled_delivered_orders"] == 96282 and h["labelled_late_orders"] == 7823
    assert h["one_time_customer_share_pct"] == Decimal("96.96")
    assert all(v.source for v in exp["headline_numbers"].values())


def test_analytics_checks_use_the_tracked_sql_and_csv():
    for chk in C.all_checks():
        if chk.group != "analytics":
            continue
        stem = chk.reference_csv[:-4]
        assert chk.duckdb_sql == (ROOT / "sql" / "analytics" / f"{stem}.sql").read_text(encoding="utf-8")
        assert (ROOT / "reports" / "analytics" / chk.reference_csv).exists()


def test_snowflake_sql_renders_and_is_read_only():
    for chk in C.all_checks():
        sf = C.render_snowflake(chk.snowflake_sql, "RETAIL_OLIST", "")
        assert "{M}" not in sf and "{" not in sf.replace("{{", "")
        F.assert_read_only(sf)
        F.assert_read_only(C.render_duckdb(chk.duckdb_sql))
        assert "RETAIL_OLIST.MARTS." in sf
        for t in chk.tie_breaks:
            F.assert_read_only(C.render_snowflake(t.candidates_sql))
    dev = C.render_snowflake("select * from {M}dim_date", "RETAIL_OLIST", "DEV_")
    assert dev == "select * from RETAIL_OLIST.DEV_MARTS.dim_date"
    with pytest.raises(ValueError):
        C.render_snowflake("select 1 from {M}t", "bad db")


def test_no_credentials_in_the_package():
    secret_like = re.compile(r"(BEGIN [A-Z ]*PRIVATE KEY|password\s*=\s*['\"][^'\"]+['\"]|[A-Za-z0-9+/]{40,}={0,2}\s*$)",
                             re.MULTILINE)
    for path in (ROOT / "src" / "reconciliation").glob("*.py"):
        assert not secret_like.search(path.read_text(encoding="utf-8")), path


# ----------------------------------------------------------------------------- running registered SQL on the mini warehouse

def _sides(mini):
    f = F.DuckDBFetcher(mini.con)
    return K.duckdb_side(f), K.duckdb_side(f, name="duckdb (self-test)")


def _populate(mini):
    t0 = datetime(2018, 1, 1, 10)
    for i in range(12):
        mini.add_order(t0 + timedelta(days=i * 3), t0 + timedelta(days=i * 3 + (20 if i % 4 == 0 else 8)))
    mini.add_order(t0 + timedelta(days=40), None, status="canceled")


def test_registered_ml_checks_self_compare_clean_on_the_mini_warehouse(mini):
    _populate(mini)
    left, right = _sides(mini)
    for name in ("mart_late_delivery_features", "mart_late_delivery_features_aggregates", "mart_weekly_orders_revenue"):
        res = K.run_check(C.select_checks([name])[0], left, right)
        assert res.error is None, res.error
        assert res.status == "PASS", (name, res.primary)
        assert res.primary.matched_rows > 0


def test_weekly_check_sql_matches_forecast_baseline(mini):
    import forecast_baseline as fb
    _populate(mini)
    chk = C.select_checks(["mart_weekly_orders_revenue"])[0]
    got = F.DuckDBFetcher(mini.con)(chk.duckdb_sql)
    want = fb.weekly_series(mini.con).reset_index()
    assert [pd.Timestamp(w) for w in got["week"]] == list(want["week"])
    assert [int(o) for o in got["orders"]] == list(want["orders"])
    assert [float(r) for r in got["revenue"]] == pytest.approx(list(want["revenue"]))


def test_feature_tie_break_classification_with_a_real_price_tie(mini):
    """An order whose two items tie on price but sit in different categories is ambiguous for arg_max."""
    _populate(mini)
    mini.con.execute("insert into dim_product values (2, 400, 800, 1, 'books')")
    oid = mini.add_order(datetime(2018, 3, 1), datetime(2018, 3, 5))
    mini.con.execute("insert into fact_order_items values (?, 1, 2, 100, 10, 2, 1)", [oid])  # tie on price 100
    tie = next(t for t in C.select_checks(["mart_late_delivery_features"])[0].tie_breaks if t.name == "category")
    f = F.DuckDBFetcher(mini.con)
    cands = K._candidates(f(C.render_duckdb(tie.candidates_sql)))
    assert cands[oid] == {"toys", "books"}
    assert sum(1 for s in cands.values() if len(s) > 1) == 1


# ----------------------------------------------------------------------------- reference CSV

def test_reference_csv_is_coerced_to_the_query_types(tmp_path):
    template = frame(["orders_placed", "customers", "pct", "money", "flag"],
                     [["1", 5, 96.96, Decimal("12.50"), True]])
    p = tmp_path / "r.csv"
    p.write_text("orders_placed,customers,pct,money,flag\n4+,3,0.05,31393.3,False\n1,5,96.96,12.5,True\n", encoding="utf-8")
    ref = K.load_reference_csv(p, template)
    assert ref["orders_placed"].tolist() == ["4+", "1"]               # a key that pandas would mangle stays text
    assert ref["customers"].tolist() == [3, 5] and ref["flag"].tolist() == [False, True]
    assert ref["money"].tolist() == [Decimal("31393.3"), Decimal("12.5")]
    c = K.compare_frames(template, ref.iloc[[1]].reset_index(drop=True), ["orders_placed"])
    assert c.passed


def test_tracked_analytics_csvs_load_against_their_checks():
    """Every tracked CSV has the columns the DuckDB query returns (no warehouse needed)."""
    for chk in C.all_checks():
        if chk.group != "analytics":
            continue
        header = (ROOT / "reports" / "analytics" / chk.reference_csv).read_text(encoding="utf-8").splitlines()[0]
        cols = set(header.lower().split(","))
        assert set(chk.keys) <= cols, chk.name


# ----------------------------------------------------------------------------- report

def _fake_run(mode="snowflake", **kw):
    left = frame(["id", "v"], [[1, Decimal("1.00")], [2, Decimal("2.00")]])
    right = frame(["id", "v"], [[1, Decimal("1.00")], [2, Decimal("2.01")], [3, Decimal("3.00")]])
    cmp = K.compare_frames(left, right, ["id"], label="duckdb_vs_snowflake", left_name="duckdb", right_name="snowflake")
    res = K.CheckResult("demo", "fact", "demo check", comparisons=[cmp])
    meta = R.RunMetadata(mode=mode, generated_at="2026-01-01 00:00:00 UTC", git_sha="abc123", git_dirty=False,
                         account_locator="ab***ef", database="RETAIL_OLIST", role="RETAIL_TRANSFORMER",
                         warehouse="RETAIL_WH", schema_prefix="", left_description="duckdb", right_description="snowflake",
                         tool_versions={"python": "3.13"})
    return R.ReconciliationRun(meta, [res]), res


def test_report_refuses_without_results():
    meta = _fake_run()[0].metadata
    with pytest.raises(R.ReportError):
        R.render_report(R.ReconciliationRun(meta, []))
    with pytest.raises(R.ReportError):
        R.render_report(None)
    with pytest.raises(R.ReportError):
        R.render_report(R.ReconciliationRun(meta, ["not a result"]))


def test_report_renders_only_what_the_results_say(tmp_path):
    run, _ = _fake_run()
    text = R.render_report(run)
    assert "abc123" in text and "ab***ef" in text and "FAIL" in text
    assert "| demo |" in text and "2.01" in text            # the injected value difference is shown
    assert "extra in right" in text
    assert "NOT RUN" not in text


def test_report_never_prints_review_text():
    left = frame(["id", "review_comment_message"], [[1, "secret customer text"]])
    right = frame(["id", "review_comment_message"], [[1, "other customer text"]])
    cmp = K.compare_frames(left, right, ["id"])
    run, res = _fake_run()
    res.comparisons = [cmp]
    text = R.render_report(run)
    assert "customer text" not in text and "<text, 20 chars>" in text


def test_selftest_report_is_labelled_and_cannot_overwrite_the_shipped_report(tmp_path):
    run, _ = _fake_run("selftest")
    assert "not a Snowflake reconciliation" in R.render_report(run)
    with pytest.raises(R.ReportError):
        R.write_report(run, R.DEFAULT_REPORT_PATH)
    out = R.write_report(run, tmp_path / "x.md")
    assert out.read_text(encoding="utf-8").startswith("# Reconciliation report: OFFLINE SELF-TEST")


def test_snowflake_metadata_requires_settings():
    with pytest.raises(R.ReportError):
        R.collect_run_metadata("snowflake")
    meta = R.collect_run_metadata("selftest")
    assert meta.account_locator == "n/a" and len(meta.git_sha) >= 7 and "python" in meta.tool_versions


def test_shipped_report_is_a_not_run_stub_without_numbers():
    text = STUB.read_text(encoding="utf-8")
    assert "NOT RUN" in text
    assert not re.search(r"\d", text), "the stub must not contain any figure"


# ----------------------------------------------------------------------------- CLI guards and an end-to-end offline run

def test_cli_refuses_snowflake_without_yes(monkeypatch, capsys):
    def boom(*a, **k):
        raise AssertionError("must not connect")
    monkeypatch.setattr(cli, "SnowflakeFetcher", boom)
    monkeypatch.setenv("SNOWFLAKE_ACCOUNT", "acct-xyz-123")
    monkeypatch.setenv("SNOWFLAKE_USER", "someone")
    monkeypatch.setenv("SNOWFLAKE_PRIVATE_KEY_PATH", "nokey.p8")
    assert cli.main([]) == 2
    err = capsys.readouterr().err
    assert "without --yes" in err and "acct-xyz-123" not in err and "someone" not in err


def test_cli_yes_without_credentials_stops_before_connecting(monkeypatch, capsys, tmp_path):
    for n in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH"):
        monkeypatch.delenv(n, raising=False)
    db = tmp_path / "w.duckdb"
    duckdb.connect(str(db)).close()
    monkeypatch.setattr(cli, "SnowflakeFetcher", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no connect")))
    assert cli.main(["--yes", "--duckdb", str(db)]) == 2
    assert "missing environment variables" in capsys.readouterr().err


def test_cli_selftest_write_report_needs_an_explicit_path(tmp_path, capsys):
    db = tmp_path / "w.duckdb"
    duckdb.connect(str(db)).close()
    assert cli.main(["--offline-selftest", "--write-report", "--duckdb", str(db)]) == 2
    assert cli.main(["--offline-selftest", "--report-path", str(R.DEFAULT_REPORT_PATH), "--duckdb", str(db)]) == 2
    assert cli.main(["--offline-selftest", "--yes", "--duckdb", str(db)]) == 2
    assert cli.main(["--checks", "nope", "--offline-selftest"]) == 2


def test_cli_offline_selftest_end_to_end(mini, tmp_path, capsys):
    _populate(mini)
    db = tmp_path / "mini.duckdb"
    mini.con.execute(f"attach '{db.as_posix()}' as f")
    for t in ("fact_orders", "fact_order_items", "fact_payments", "dim_product", "dim_seller", "dim_geography"):
        mini.con.execute(f"create table f.{t} as select * from {t}")
    mini.con.execute("detach f")
    report = tmp_path / "selftest.md"
    code = cli.main(["--offline-selftest", "--duckdb", str(db), "--write-report", "--report-path", str(report),
                     "--checks", "mart_late_delivery_features,mart_late_delivery_features_aggregates,mart_weekly_orders_revenue"])
    out = capsys.readouterr().out
    assert code == 0, out
    assert "Snowflake is not contacted" in out
    text = report.read_text(encoding="utf-8")
    assert "OFFLINE SELF-TEST" in text and "mart_weekly_orders_revenue" in text


def test_a_failing_registered_sql_is_reported_as_error_not_raised(mini):
    left, right = _sides(mini)  # mini has no dim_customer: the dimension check cannot run
    res = K.run_check(C.select_checks(["dim_customer"])[0], left, right)
    assert res.status == "ERROR" and "dim_customer" in res.error


# ----------------------------------------------------------------------------- optional: the real warehouse

def _real_warehouse():
    for cand in (os.environ.get("RECON_WAREHOUSE"), os.environ.get("DUCKDB_PATH"), ROOT / "warehouse.duckdb",
                 ROOT.parent / "GCP" / "warehouse.duckdb"):
        if cand and Path(cand).exists():
            return Path(cand)
    return None


@pytest.fixture(scope="module")
def real_fetch():
    path = _real_warehouse()
    if path is None:
        pytest.skip("no warehouse.duckdb found (set RECON_WAREHOUSE)")
    f = F.DuckDBFetcher(path)
    yield f
    f.close()


def test_real_warehouse_every_registered_duckdb_sql_executes_and_headlines_hold(real_fetch):
    for chk in C.all_checks():
        df = real_fetch(chk.duckdb_sql)
        assert len(df) > 0, chk.name
        assert set(chk.keys) <= set(df.columns), chk.name
        for t in chk.tie_breaks:
            assert len(real_fetch(C.render_duckdb(t.candidates_sql))) > 0
    head = real_fetch(C.select_checks(["headline_numbers"])[0].duckdb_sql)
    got = dict(zip(head["metric"], head["value"], strict=True))
    for metric, exp in C.select_checks(["headline_numbers"])[0].expected.items():
        assert got[metric] == exp.value, metric


def test_real_warehouse_weekly_sql_equals_forecast_baseline(real_fetch):
    import forecast_baseline as fb
    chk = C.select_checks(["mart_weekly_orders_revenue"])[0]
    got = real_fetch(chk.duckdb_sql)
    want = fb.weekly_series(real_fetch._con).reset_index()
    assert [pd.Timestamp(w) for w in got["week"]] == list(want["week"])
    assert [int(o) for o in got["orders"]] == list(want["orders"])
    assert [float(r) for r in got["revenue"]] == pytest.approx(list(want["revenue"]), rel=1e-12)


def test_real_warehouse_analytics_match_the_tracked_csvs(real_fetch):
    left = K.duckdb_side(real_fetch)
    for chk in C.select_checks(groups=["analytics"]):
        res = K.run_check(chk, left, K.duckdb_side(real_fetch, name="duckdb (self-test)"), reference_dir=C.REFERENCE_DIR)
        assert res.error is None, res.error
        assert res.status == "PASS", (chk.name, [(c.label, c.n_unexplained, c.missing_in_right) for c in res.comparisons])
        assert len(res.comparisons) == 3


# ----------------------------------------------------------------------------- tight bound on the category cascade

def test_cascade_classifier_bound():
    con = duckdb.connect(":memory:")
    con.execute("create table cand (order_id varchar, candidate varchar)")
    # o1 is ambiguous between toys and books; o2 is a toys order, o3 a books order, o4 a food order (unaffected)
    con.execute("insert into cand values ('o1','toys'),('o1','books'),('o2','toys'),('o3','books'),('o4','food')")
    side = K.duckdb_side(F.DuckDBFetcher(con))
    tie = C.TieBreak("category", "select order_id, candidate from cand", cascade_columns=("n",))
    cls, info = K._tie_classifiers(tie, side, side)
    assert info.n_ambiguous_orders == 1
    f = cls["n"]
    assert f(("o1",), 10, 400) == K.DOWNSTREAM      # the ambiguous order itself: anything goes
    assert f(("o2",), 10, 11) == K.DOWNSTREAM       # affected category, off by <= number of ambiguous orders
    assert f(("o2",), 10, 12) is None               # off by more than the ambiguous orders can explain
    assert f(("o4",), 10, 11) is None               # category untouched by any tie
    assert f(("o9",), 10, 11) is None               # unknown order
    assert "eligible" in info.note

def test_empty_comparison_never_passes():
    """Two empty frames (or no matched row) prove nothing: a comparison must not pass vacuously."""
    assert not K.compare_frames(frame(["id", "x"], []), frame(["id", "x"], []), ["id"]).passed
    assert not K.compare_frames(frame(["id", "x"], [[1, 1]]), frame(["id", "x"], []), ["id"]).passed
    assert K.compare_frames(frame(["id", "x"], [[1, 1]]), frame(["id", "x"], [[1, 1]]), ["id"]).passed
