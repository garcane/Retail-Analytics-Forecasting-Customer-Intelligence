"""The generated Power BI project: schema validity, internal consistency and deterministic output.

Power BI Desktop is not available where this project is built, so these tests are the safeguard: every JSON file is
validated against Microsoft's published schemas (skipped when they cannot be downloaded), every name used by a visual,
relationship or measure is checked against the model, and the generators are checked for deterministic output.
"""

import json
import re
import tempfile
import urllib.request
from pathlib import Path

import pytest
from jsonschema import Draft7Validator
from referencing import Registry, Resource

import build_pbip as pbip
import build_spec_html
import model_spec as ms
from conftest import ROOT

pytestmark = pytest.mark.warehouse

SCHEMA_HOST = "https://developer.microsoft.com/json-schemas/"
SCHEMA_RAW = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"
CACHE = Path(tempfile.gettempdir()) / "pbi-json-schemas"


def _fetch(uri: str) -> str:
    assert uri.startswith(SCHEMA_HOST), uri
    local = CACHE / uri[len(SCHEMA_HOST):]
    if not local.exists():
        local.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(SCHEMA_RAW + uri[len(SCHEMA_HOST):], timeout=20) as r:  # noqa: S310 (fixed https host)
            local.write_text(r.read().decode("utf-8"), encoding="utf-8")
    return local.read_text(encoding="utf-8")


def _retrieve(uri: str) -> Resource:
    return Resource.from_contents(json.loads(_fetch(uri)))


@pytest.fixture(scope="module")
def generated() -> dict[str, str]:
    return pbip.files()


@pytest.fixture(scope="module")
def registry() -> Registry:
    try:
        _fetch(pbip.SCHEMAS["visual"])
    except OSError:
        pytest.skip("Microsoft's JSON schemas could not be downloaded (offline)")
    return Registry(retrieve=_retrieve)


def _json_files(generated: dict[str, str]) -> dict[str, dict]:
    return {p: json.loads(t) for p, t in generated.items() if p.endswith((".json", ".pbip", ".pbir", ".pbism"))}


# ------------------------------------------------------------------------------------------------ schema validation
def test_every_json_file_validates_against_its_published_schema(generated, registry):
    problems = []
    checked = 0
    for path, doc in _json_files(generated).items():
        if "$schema" not in doc:
            continue  # the theme file is not a schema-described item
        schema = json.loads(_fetch(doc["$schema"]))
        for err in Draft7Validator(schema, registry=registry).iter_errors(doc):
            problems.append(f"{path}: {'/'.join(map(str, err.absolute_path))}: {err.message[:160]}")
        checked += 1
    assert checked >= 50
    assert not problems, "\n".join(problems[:20])


# ------------------------------------------------------------------------------------------------ cross references
DAX_COLUMN = re.compile(r"(?:'([^']+)'|\b([A-Za-z_]\w*))\[([^\]]+)\]")
DAX_MEASURE = re.compile(r"(?<![\w'\]])\[([^\]]+)\]")


def _columns() -> dict[str, set[str]]:
    return {t: {c for c, _ in cols} for t, cols in ms.load_schema().items()}


def test_names_are_unique_and_every_table_has_a_schema():
    columns = _columns()
    assert len({t.name for t in ms.TABLES}) == len(ms.TABLES)
    assert set(columns) == {t.name for t in ms.TABLES}
    assert len({m.name for m in ms.MEASURES}) == len(ms.MEASURES)
    all_columns = {c for cols in columns.values() for c in cols}
    assert not {m.name for m in ms.MEASURES} & all_columns, "a measure shares its name with a column"
    ids = [v.id for p in ms.PAGES for v in p.visuals]
    assert len(ids) == len(set(ids)) and len({p.id for p in ms.PAGES}) == len(ms.PAGES)


def test_relationships_join_existing_columns_of_the_same_type():
    schema = {t: dict(cols) for t, cols in ms.load_schema().items()}
    for r in ms.RELATIONSHIPS:
        many, one = ms.tmdl_type(schema[r.many_table][r.many_col]), ms.tmdl_type(schema[r.one_table][r.one_col])  # BIGINT and INTEGER both load as int64
        assert many == one, f"{r.many_table}.{r.many_col} {many} vs {r.one_table}.{r.one_col} {one}"
    assert sum(r.active for r in ms.RELATIONSHIPS if r.many_table == "fact_orders" and r.one_table == "dim_date") == 1
    pairs = [(r.many_table, r.one_table) for r in ms.RELATIONSHIPS if r.active]
    assert len(pairs) == len(set(pairs)), "two active relationships between the same pair of tables (ambiguous)"


def test_measure_dax_only_references_existing_columns_and_measures():
    columns, measures = _columns(), {m.name for m in ms.MEASURES}
    for m in ms.MEASURES:
        assert m.table in columns, m.name
        for quoted, bare, name in DAX_COLUMN.findall(m.dax):
            table = quoted or bare
            assert table in columns and name in columns[table], f"{m.name}: {table}[{name}]"
        stripped = DAX_COLUMN.sub("", m.dax)
        for name in DAX_MEASURE.findall(stripped):
            assert name in measures, f"{m.name}: [{name}]"


def test_every_visual_field_exists():
    columns, measures = _columns(), {m.name: m.table for m in ms.MEASURES}
    for page in ms.PAGES:
        for v in page.visuals:
            fields = [f for fs in v.roles.values() for f in fs] + ([v.sort[0]] if v.sort else [])
            for kind, table, name in fields:
                if kind == "measure":
                    assert measures.get(name) == table, f"{v.id}: measure {name}"
                else:
                    assert name in columns.get(table, ()), f"{v.id}: {table}[{name}]"
            assert 0 <= v.x and v.x + v.w <= ms.PAGE_W and 0 <= v.y and v.y + v.h <= ms.PAGE_H, f"{v.id} sits outside the page"


def test_generated_visuals_and_tmdl_use_the_same_names(generated):
    measure_lines = {m.name for m in ms.MEASURES}
    tmdl = "\n".join(t for p, t in generated.items() if p.endswith(".tmdl"))
    for name in measure_lines:
        assert f"measure {pbip.q(name)} =" in tmdl, name
    assert all(t.name in generated.get(f"{pbip.NAME}.SemanticModel/definition/model.tmdl", "") for t in ms.TABLES)
    visuals = [json.loads(t) for p, t in generated.items() if p.endswith("visual.json")]
    assert len(visuals) == sum(len(p.visuals) for p in ms.PAGES)
    for v in visuals:
        for role in v["visual"]["query"]["queryState"].values():
            for proj in role["projections"]:
                ((kind, body),) = proj["field"].items()
                assert kind in ("Column", "Measure") and body["Expression"]["SourceRef"]["Entity"] in {t.name for t in ms.TABLES}


def test_tmdl_is_tab_indented_and_has_no_trailing_whitespace(generated):
    for path, text in generated.items():
        if not path.endswith(".tmdl"):
            continue
        for n, line in enumerate(text.splitlines(), start=1):
            assert line == line.rstrip(), f"{path}:{n} trailing whitespace"
            assert not line.startswith(" "), f"{path}:{n} space indentation"


def test_data_folder_placeholder_is_not_a_real_machine_path(generated):
    text = "\n".join(generated.values())
    assert pbip.DATA_FOLDER_PLACEHOLDER in text
    assert "Users\\Student" not in text and "Users/Student" not in text


# ------------------------------------------------------------------------------------------------ determinism
def test_generation_is_deterministic(generated):
    assert pbip.files() == generated
    assert build_spec_html.render() == build_spec_html.render()


def test_committed_project_matches_the_generator(generated):
    for rel, text in generated.items():
        path = ROOT / "powerbi" / rel
        assert path.exists(), f"{rel} missing: run src/powerbi/build_pbip.py"
        assert path.read_text(encoding="utf-8") == text, f"{rel} is stale: run src/powerbi/build_pbip.py"
