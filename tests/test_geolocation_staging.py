"""The geolocation staging view reads Kaggle's CSV directly and keeps zip prefixes as text."""

import duckdb
import pytest

from build_warehouse import RAW_FILES, check_raw_files, run_sql_file
from conftest import ROOT

STAGING = ROOT / "sql" / "staging" / "stg_geolocation.sql"


@pytest.fixture
def data_dir(tmp_path):
    (tmp_path / "olist_geolocation_dataset.csv").write_text(
        "geolocation_zip_code_prefix,geolocation_lat,geolocation_lng,geolocation_city,geolocation_state\n"
        "01046,-23.546,-46.635,sao paulo,SP\n"
        "01046,-23.548,-46.638,sao paulo,SP\n"
        "99010,-28.263,-52.405,passo fundo,RS\n",
        encoding="utf-8",
    )
    return tmp_path


def test_staging_keeps_leading_zeros_and_types(data_dir):
    con = duckdb.connect()
    run_sql_file(con, STAGING, data_dir)
    rows = con.execute("select * from stg_geolocation order by 1, 2").fetchall()
    assert [r[0] for r in rows] == ["01046", "01046", "99010"]
    assert con.execute("describe stg_geolocation").fetchall()[1][1] == "DOUBLE"


def test_no_parquet_is_read_or_written(data_dir):
    run_sql_file(duckdb.connect(), STAGING, data_dir)
    assert not list(data_dir.glob("*.parquet")) and "parquet" not in STAGING.read_text(encoding="utf-8").lower()


def test_missing_raw_file_gives_a_clear_error(data_dir):
    with pytest.raises(FileNotFoundError, match="README.md section 1"):
        check_raw_files(data_dir)
    for name in RAW_FILES:
        (data_dir / name).touch()
    check_raw_files(data_dir)
