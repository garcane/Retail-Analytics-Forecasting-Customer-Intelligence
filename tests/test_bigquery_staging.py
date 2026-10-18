"""Static checks that sql/bigquery/ mirrors sql/staging/ and data/.

BigQuery cannot run here (D-002: no GCP project exists), so instead of executing the
translated SQL these tests compare it file by file with the DuckDB originals, with the
read_csv column lists, and with the actual CSV headers' column order (BigQuery maps a
CSV external table's columns positionally after skip_leading_rows).
"""

import re
from pathlib import Path

from build_warehouse import RAW_FILES
from conftest import ROOT

BQ = ROOT / "sql" / "bigquery"
LOCAL_STAGING = ROOT / "sql" / "staging"

# sql/staging file stem -> raw CSV it reads (kept in step with RAW_FILES below)
STG_TO_CSV = {
    "stg_category_translation": "product_category_name_translation",
    "stg_customers": "olist_customers_dataset",
    "stg_geolocation": "olist_geolocation_dataset",
    "stg_order_items": "olist_order_items_dataset",
    "stg_order_payments": "olist_order_payments_dataset",
    "stg_order_reviews": "olist_order_reviews_dataset",
    "stg_orders": "olist_orders_dataset",
    "stg_products": "olist_products_dataset",
    "stg_sellers": "olist_sellers_dataset",
}

# docs/data/DATA_MODEL.md "Moving to BigQuery". VARCHAR -> STRING needs no cast
# because the raw external tables read every column as STRING.
BQ_TYPE = {
    "TIMESTAMP": "datetime",
    "INTEGER": "int64",
    "DECIMAL(12,2)": "numeric",
    "DOUBLE": "float64",
}


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_comments(sql: str) -> str:
    return re.sub(r"--[^\n]*", "", sql)


def local_columns(sql: str) -> list[tuple[str, str]]:
    """('price', 'DECIMAL(12,2)') pairs from the read_csv(columns = {...}) block."""
    return re.findall(r"'(\w+)':\s*'([A-Z]+(?:\(\d+,\d+\))?)'", sql)


def stems(folder: str) -> dict[str, Path]:
    path = BQ / folder
    return {p.stem: p for p in sorted(path.glob("*.sql"))} if path.exists() else {}


LOCAL = {p.stem: p for p in sorted(LOCAL_STAGING.glob("*.sql"))}
BQ_STAGING = stems("staging")
RAW = stems("raw")


def test_the_translation_map_covers_the_nine_raw_files():
    assert set(STG_TO_CSV) == set(LOCAL)
    assert set(STG_TO_CSV.values()) == {Path(name).stem for name in RAW_FILES}


def test_staging_has_the_same_file_names_as_the_local_staging_layer():
    assert set(BQ_STAGING) == set(LOCAL)
    assert set(RAW) == set(STG_TO_CSV.values())


def test_each_raw_file_is_an_external_table_over_its_csv():
    for csv_stem, path in RAW.items():
        sql = read(path)
        assert "create or replace external table" in sql, csv_stem
        assert f"`${{PROJECT}}.raw.{csv_stem}`" in sql, csv_stem
        assert f"gs://${{BUCKET}}/raw/olist/{csv_stem}.csv" in sql, csv_stem
        assert re.search(r"format\s*=\s*'CSV'", sql), csv_stem
        assert re.search(r"skip_leading_rows\s*=\s*1", sql), csv_stem
        assert re.search(r"allow_quoted_newlines\s*=\s*true", sql, re.I), csv_stem


def test_raw_columns_match_the_local_column_list_in_order_and_as_strings():
    for name, local_path in LOCAL.items():
        raw_sql = strip_comments(read(RAW[STG_TO_CSV[name]]))
        declared = re.findall(r"(?m)^\s*(\w+)\s+string\s*,?\s*$", raw_sql)
        expected = [col for col, _ in local_columns(read(local_path))]
        assert declared == expected, name


def test_each_staging_file_is_a_view_over_its_raw_table_with_the_typed_casts():
    for name, local_path in LOCAL.items():
        sql = read(BQ_STAGING[name])
        assert "create or replace view" in sql, name
        assert f"`${{PROJECT}}.staging.{name}`" in sql, name
        assert f"`${{PROJECT}}.raw.{STG_TO_CSV[name]}`" in sql, name
        for col, duckdb_type in local_columns(read(local_path)):
            if duckdb_type == "VARCHAR":
                continue
            pattern = rf"cast\s*\(\s*{col}\s+as\s+{BQ_TYPE[duckdb_type]}\s*\)"
            assert re.search(pattern, sql, re.I), f"{name}: {col} {duckdb_type}"


def test_every_local_column_reaches_the_view():
    """Explicit select lists must name each column; `select *` files rely on raw/."""
    for name, local_path in LOCAL.items():
        sql = read(BQ_STAGING[name])
        if re.search(r"select\s+\*", sql, re.I):
            continue  # raw/ carries the columns (checked above), the view exposes them all
        missing = [col for col, _ in local_columns(read(local_path))
                   if not re.search(rf"\b{col}\b", sql)]
        assert not missing, f"{name}: {missing}"


def test_the_products_renames_happen_in_the_view_not_in_raw():
    sql = read(BQ_STAGING["stg_products"])
    assert "product_name_length" in sql and "product_description_length" in sql
    assert not re.search(r"\bproduct_name_length\b", strip_comments(read(RAW["olist_products_dataset"])))


def test_the_tokens_replace_the_duckdb_one():
    for path in [*BQ_STAGING.values(), *RAW.values()]:
        sql = read(path)
        assert "${DATA_DIR}" not in sql, path
        assert "${PROJECT}" in sql, path
        if path.parent.name == "raw":
            assert "${BUCKET}" in sql, path
        else:
            assert "${BUCKET}" not in sql, path


def test_the_readme_documents_the_tokens_and_the_untested_status():
    readme = read(BQ / "README.md")
    for token in ("${PROJECT}", "${BUCKET}"):
        assert token in readme
    assert "has ever been run" in readme
