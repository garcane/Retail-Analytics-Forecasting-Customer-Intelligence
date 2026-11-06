"""Guard tests for the Snowflake-backed Power BI copy (powerbi/snowflake/apply_snowflake_source.py).

Everything here is offline: the script is run into a temporary directory and compared with the committed project.
Nothing connects to Snowflake or opens Power BI Desktop, so these tests prove the patch touches only data sources;
they do not prove Desktop accepts the patched copy or that the Snowflake views return what the templates expect.
"""

import hashlib
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SNOW = ROOT / "powerbi" / "snowflake"
ORIGINAL = ROOT / "powerbi"
SM = "RetailAnalytics.SemanticModel"
DEFINITION = Path(SM) / "definition"
GUIDE = ROOT / "docs" / "migration" / "POWERBI_SWITCH_GUIDE.md"

PBI_TABLES = ["dim_date", "dim_customer", "dim_product", "dim_seller", "dim_geography",
              "fact_orders", "fact_order_items", "fact_payments", "fact_reviews"]
ML_TABLES = ["late_delivery_scores", "forecast_backtest", "flag_share"]
TABLES = PBI_TABLES + ML_TABLES
PROJECT_ITEMS = ["RetailAnalytics.pbip", "RetailAnalytics.Report", SM]
DERIVED = ["is_net_order", "is_labelled_delivery", "promised_days", "delay_bucket", "delay_bucket_order"]

TYPED_RE = re.compile(r"^[ \t]*Typed = Table\.TransformColumnTypes\(\w+, (.*)\)[ \t]*$", re.M)


def _load_script():
    spec = importlib.util.spec_from_file_location("apply_snowflake_source", SNOW / "apply_snowflake_source.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


script = _load_script()


def _tree_hash(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(folder.rglob("*")) if p.is_file() and ".pbi" not in p.relative_to(folder).parts}


def _project_files(base: Path) -> dict[str, bytes]:
    out = {}
    for item in PROJECT_ITEMS:
        p = base / item
        files = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file()]
        for f in files:
            if ".pbi" in f.relative_to(base).parts or f.name in ("cache.abf", "localSettings.json"):
                continue
            out[f.relative_to(base).as_posix()] = f.read_bytes()
    return out


def _split_outside_block(raw: bytes) -> tuple[list[str], list[str]]:
    """(lines outside the partition 'source =' M block, lines inside it) for one table file. Independent of the script's own logic."""
    lines = raw.decode("utf-8").split("\r\n") if b"\r\n" in raw else raw.decode("utf-8").split("\n")
    i = lines.index("\t\tsource =")
    j = i + 1
    while lines[j].startswith("\t\t\t"):
        j += 1
    return lines[: i + 1] + lines[j:], lines[i + 1: j]


@pytest.fixture(scope="module")
def patched(tmp_path_factory):
    before = _tree_hash(ORIGINAL)
    out = tmp_path_factory.mktemp("pbi_snowflake") / "copy"
    written = script.apply(ORIGINAL, out)
    return {"out": out, "written": written, "before": before}


# ------------------------------------------------------------------------------------------------ what must NOT change
def test_report_folder_is_byte_identical(patched):
    orig = {k: v for k, v in _project_files(ORIGINAL).items() if k.startswith("RetailAnalytics.Report/")}
    new = {k: v for k, v in _project_files(patched["out"]).items() if k.startswith("RetailAnalytics.Report/")}
    assert orig and orig.keys() == new.keys()
    assert [k for k in orig if orig[k] != new[k]] == []


@pytest.mark.parametrize("name", ["relationships.tmdl", "model.tmdl", "database.tmdl"])
def test_model_files_are_byte_identical(patched, name):
    assert (patched["out"] / DEFINITION / name).read_bytes() == (ORIGINAL / DEFINITION / name).read_bytes()


def test_only_expressions_and_the_twelve_tables_differ(patched):
    orig, new = _project_files(ORIGINAL), _project_files(patched["out"])
    assert orig.keys() == new.keys(), "the copy must contain exactly the project's files"
    changed = sorted(k for k in orig if orig[k] != new[k])
    expected = sorted([f"{DEFINITION.as_posix()}/expressions.tmdl"] + [f"{DEFINITION.as_posix()}/tables/{t}.tmdl" for t in TABLES])
    assert changed == expected


@pytest.mark.parametrize("table", TABLES)
def test_table_file_is_unchanged_outside_the_partition_source(patched, table):
    """Columns, measures, formatting, annotations and the partition header stay exactly as they were (including line endings)."""
    rel = DEFINITION / "tables" / f"{table}.tmdl"
    orig_outside, orig_block = _split_outside_block((ORIGINAL / rel).read_bytes())
    new_outside, new_block = _split_outside_block((patched["out"] / rel).read_bytes())
    assert new_outside == orig_outside
    assert any("DataFolder" in line for line in orig_block)
    assert new_block != orig_block
    orig_raw, new_raw = (ORIGINAL / rel).read_bytes(), (patched["out"] / rel).read_bytes()
    assert (b"\r\n" in orig_raw) == (b"\r\n" in new_raw), "line-ending style must be preserved"
    assert new_raw.count(b"\n") - new_raw.count(b"\r\n") == orig_raw.count(b"\n") - orig_raw.count(b"\r\n")


def test_original_project_is_not_modified(patched):
    assert _tree_hash(ORIGINAL) == patched["before"]
    # a second run into another place must not touch it either
    assert not (ORIGINAL / "powerbi_snowflake").exists()


# ------------------------------------------------------------------------------------------------ what MUST change
def test_no_datafolder_left_in_data_sources(patched):
    expr = (patched["out"] / DEFINITION / "expressions.tmdl").read_text(encoding="utf-8")
    assert "DataFolder" not in expr and "File.Contents" not in expr
    for t in TABLES:
        _, block = _split_outside_block((patched["out"] / DEFINITION / "tables" / f"{t}.tmdl").read_bytes())
        text = "\n".join(block)
        assert "DataFolder" not in text and "File.Contents" not in text and "Csv.Document" not in text and "Parquet.Document" not in text
    # The only remaining mention in the whole copy is the Power Query ordering annotation in model.tmdl, which must stay byte-identical
    # (see docs/migration/POWERBI_SWITCH_GUIDE.md, 'Known leftovers').
    hits = []
    for path, raw in _project_files(patched["out"]).items():
        if b"DataFolder" in raw:
            hits += [(path, line.strip()[:40]) for line in raw.decode("utf-8", "ignore").splitlines() if "DataFolder" in line]
    assert [h[0] for h in hits] == [f"{DEFINITION.as_posix()}/model.tmdl"]
    assert hits[0][1].startswith("annotation PBI_QueryOrder")


def test_expressions_define_the_two_snowflake_parameters(patched):
    expr = (patched["out"] / DEFINITION / "expressions.tmdl").read_text(encoding="utf-8")
    names = re.findall(r"^expression (\w+) = ", expr, re.M)
    assert names == ["SnowflakeServer", "SnowflakeWarehouse"]
    assert expr.count("IsParameterQuery=true") == 2 and expr.count("IsParameterQueryRequired=true") == 2
    assert 'expression SnowflakeServer = "<account>.snowflakecomputing.com"' in expr
    assert 'expression SnowflakeWarehouse = "RETAIL_WH"' in expr
    lineage = re.findall(r"lineageTag: (\S+)", expr)
    assert len(set(lineage)) == 2
    orig_expr = (ORIGINAL / DEFINITION / "expressions.tmdl").read_text(encoding="utf-8")
    assert not set(lineage) & set(re.findall(r"lineageTag: (\S+)", orig_expr))


# ------------------------------------------------------------------------------------------------ templates
def test_every_import_table_has_exactly_one_template():
    assert sorted(p.stem for p in (SNOW / "templates").glob("*.m")) == sorted(TABLES)
    tmdl_tables = sorted(p.stem for p in (ORIGINAL / DEFINITION / "tables").glob("*.tmdl")
                         if not p.stem.startswith(("LocalDateTable_", "DateTableTemplate_")))
    assert tmdl_tables == sorted(TABLES)


@pytest.mark.parametrize("table", TABLES)
def test_template_navigates_the_right_snowflake_object(table):
    text = (SNOW / "templates" / f"{table}.m").read_text(encoding="utf-8").replace("\r\n", "\n")
    schema, kind = ("PBI", "View") if table in PBI_TABLES else ("ML", "Table")
    assert "Snowflake.Databases(SnowflakeServer, SnowflakeWarehouse)" in text
    assert 'Name="RETAIL_OLIST", Kind="Database"' in text
    assert f'Name="{schema}", Kind="Schema"' in text
    assert f'Name="{table.upper()}", Kind="{kind}"' in text
    assert "Table.TransformColumnNames(Item, Text.Lower)" in text
    assert text.index("Table.TransformColumnNames") < text.index("Table.TransformColumnTypes")
    assert text.rstrip().endswith("in\n\tTyped")
    assert text.startswith("let\n")


@pytest.mark.parametrize("table", TABLES)
def test_template_column_types_equal_the_originals(patched, table):
    orig_src = (ORIGINAL / DEFINITION / "tables" / f"{table}.tmdl").read_text(encoding="utf-8")
    template = (SNOW / "templates" / f"{table}.m").read_text(encoding="utf-8")
    orig_args, tmpl_args = TYPED_RE.findall(orig_src), TYPED_RE.findall(template)
    assert len(orig_args) == 1 and len(tmpl_args) == 1
    assert tmpl_args == orig_args
    # and the same step appears in the patched copy
    new_src = (patched["out"] / DEFINITION / "tables" / f"{table}.tmdl").read_text(encoding="utf-8")
    assert TYPED_RE.findall(new_src) == orig_args


@pytest.mark.parametrize("table", TABLES)
def test_typed_columns_match_the_model_source_columns(table):
    """Every sourceColumn the model reads is typed by the template (and nothing is typed that the model does not read), so a
    Snowflake view that exposes these lower-cased names is sufficient."""
    src = (ORIGINAL / DEFINITION / "tables" / f"{table}.tmdl").read_text(encoding="utf-8")
    model_cols = set(re.findall(r"^\t\tsourceColumn: (\S+)", src, re.M))
    typed_cols = set(re.findall(r'\{"(\w+)", ', TYPED_RE.findall((SNOW / "templates" / f"{table}.m").read_text(encoding="utf-8"))[0]))
    assert model_cols == typed_cols


def test_derived_columns_are_typed_in_the_templates():
    orders = (SNOW / "templates" / "fact_orders.m").read_text(encoding="utf-8")
    items = (SNOW / "templates" / "fact_order_items.m").read_text(encoding="utf-8")
    for col in DERIVED:
        assert f'"{col}"' in orders
    assert '"is_net_order"' in items


# ------------------------------------------------------------------------------------------------ script behaviour
def test_script_refuses_a_non_empty_target_without_force(tmp_path):
    (tmp_path / "keep.txt").write_text("mine")
    assert script.main(["--out", str(tmp_path)]) == 1
    assert (tmp_path / "keep.txt").read_text() == "mine" and not (tmp_path / PROJECT_ITEMS[0]).exists()


def test_force_replaces_only_the_project_items(tmp_path):
    out = tmp_path / "out"
    assert script.main(["--out", str(out)]) == 0
    (out / "keep.txt").write_text("mine")
    (out / SM / "stale.txt").write_text("stale")
    assert script.main(["--out", str(out), "--force"]) == 0
    assert (out / "keep.txt").read_text() == "mine"
    assert not (out / SM / "stale.txt").exists()


def test_script_refuses_to_write_into_the_original(tmp_path):
    before = _tree_hash(ORIGINAL)
    assert script.main(["--out", str(ORIGINAL), "--force"]) == 1
    assert script.main(["--out", str(ORIGINAL / "RetailAnalytics.Report"), "--force"]) == 1
    assert _tree_hash(ORIGINAL) == before


def test_script_refuses_an_already_patched_source(patched, tmp_path):
    assert script.main(["--source", str(patched["out"]), "--out", str(tmp_path / "again")]) == 1


def test_script_refuses_when_types_drift(tmp_path):
    """If a table's column types change in the source (e.g. edited in Desktop), the stale template must not silently win."""
    src = tmp_path / "src"
    for item in PROJECT_ITEMS:
        p = ORIGINAL / item
        (src / item).parent.mkdir(parents=True, exist_ok=True)
        if p.is_dir():
            import shutil
            shutil.copytree(p, src / item, ignore=shutil.ignore_patterns(".pbi"))
        else:
            (src / item).write_bytes(p.read_bytes())
    target = src / DEFINITION / "tables" / "dim_seller.tmdl"
    raw = target.read_bytes()
    assert b'{"seller_state", type text}' in raw
    target.write_bytes(raw.replace(b'{"seller_state", type text}', b'{"seller_state", type number}'))
    assert script.main(["--source", str(src), "--out", str(tmp_path / "o")]) == 1
    assert not (tmp_path / "o").exists()


# ------------------------------------------------------------------------------------------------ secrets / identifiers
SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key"),
    (re.compile(r"(?i)\b(?:password|passphrase|pwd|secret|token)\s*[=:]\s*[\"']?(?!<)[^\s\"'<]+"), "credential assignment"),
    (re.compile(r"(?i)\b(?!<account>\.)[\w.-]+\.snowflakecomputing\.com"), "real-looking Snowflake host"),
    (re.compile(r"(?i)\b[a-z]{2}\d{5}\.[a-z0-9-]+\.(?:aws|azure|gcp)\b"), "account locator"),
]


def _scan(name: str, text: str):
    return [f"{name}: {label}" for rx, label in SECRET_PATTERNS if rx.search(text)]


def test_no_real_looking_account_or_credential_strings(patched):
    problems = []
    for p in sorted(SNOW.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and p.suffix in {".m", ".tmdl", ".py", ".md"}:
            problems += _scan(p.relative_to(ROOT).as_posix(), p.read_text(encoding="utf-8"))
    for written in patched["written"]:
        problems += _scan(written.name, written.read_text(encoding="utf-8"))
    assert GUIDE.exists(), "docs/migration/POWERBI_SWITCH_GUIDE.md is missing"
    problems += _scan(GUIDE.name, GUIDE.read_text(encoding="utf-8"))
    assert problems == []


def test_secret_scanner_would_catch_real_looking_values():
    """The scanner itself: it must flag these and accept the committed placeholder."""
    assert _scan("x", 'expression SnowflakeServer = "ab12345.eu-west-1.aws"')
    assert _scan("x", 'Server = "myorg-prod01.snowflakecomputing.com"')
    assert _scan("x", "password = hunter2")
    assert _scan("x", "-----BEGIN PRIVATE KEY-----")
    assert not _scan("x", 'expression SnowflakeServer = "<account>.snowflakecomputing.com"')


# ------------------------------------------------------------------------------------------------ switch guide
def test_guide_covers_every_table_and_states_what_is_unverified():
    text = GUIDE.read_text(encoding="utf-8")
    for t in TABLES:
        assert t in text, t
    for t in PBI_TABLES:
        assert f"PBI.{t.upper()}" in text, t
    for t in ML_TABLES:
        assert f"ML.{t.upper()}" in text, t
    for col in DERIVED:
        assert col in text, col
    assert "UNVERIFIED" in text
    for phrase in ("Entra", "MFA", "key-pair", "DataFolder", "test_powerbi_project.py", "not been opened"):
        assert phrase.lower() in text.lower(), phrase


# ------------------------------------------------------------------------------------------------ --ml-on-files
@pytest.fixture(scope="module")
def patched_ml_files(tmp_path_factory):
    out = tmp_path_factory.mktemp("pbi_snowflake_mlfiles") / "copy"
    return out, script.apply(ORIGINAL, out, ml_on_files=True)


def test_ml_on_files_patches_only_the_nine_pbi_tables(patched_ml_files):
    out, _ = patched_ml_files
    orig, new = _project_files(ORIGINAL), _project_files(out)
    changed = sorted(k for k in orig if orig[k] != new[k])
    assert changed == sorted([f"{DEFINITION.as_posix()}/expressions.tmdl"] + [f"{DEFINITION.as_posix()}/tables/{t}.tmdl" for t in PBI_TABLES])
    for t in ML_TABLES:  # still file-based, byte-identical
        rel = f"{DEFINITION.as_posix()}/tables/{t}.tmdl"
        assert new[rel] == orig[rel] and b"DataFolder" in new[rel]


def test_ml_on_files_keeps_datafolder_beside_the_snowflake_parameters(patched_ml_files):
    out, _ = patched_ml_files
    raw = (out / DEFINITION / "expressions.tmdl").read_bytes()
    assert re.findall(rb"^expression (\w+) = ", raw, re.M) == [b"DataFolder", b"SnowflakeServer", b"SnowflakeWarehouse"]
    orig_raw = (ORIGINAL / DEFINITION / "expressions.tmdl").read_bytes()
    assert raw.startswith(orig_raw.rstrip(b"\r\n")), "the original DataFolder block is kept as is"
    if b"\r\n" in orig_raw:
        assert raw.count(b"\n") == raw.count(b"\r\n"), "line endings follow the source file (CRLF)"
    else:
        assert b"\r" not in raw
