import duckdb
import pytest

from build_warehouse import ensure_geolocation_parquet

CSV = (
    "geolocation_zip_code_prefix,geolocation_lat,geolocation_lng,geolocation_city,geolocation_state\n"
    "01046,-23.54,-46.63,sao paulo,SP\n"
    "01046,-23.55,-46.64,sao paulo,SP\n"
    "99999,-10.0,-50.0,somewhere,TO\n"
)


@pytest.fixture
def con():
    c = duckdb.connect(":memory:")
    yield c
    c.close()


def test_csv_only_is_converted_and_keeps_leading_zeros(con, tmp_path, capsys):
    (tmp_path / "olist_geolocation_dataset.csv").write_text(CSV, encoding="utf-8")
    ensure_geolocation_parquet(con, tmp_path)
    parquet = tmp_path / "olist_geolocation_dataset.parquet"
    assert parquet.exists() and "converted" in capsys.readouterr().out
    rows = con.execute(
        f"select geolocation_zip_code_prefix, count(*) from read_parquet('{parquet.as_posix()}') group by 1 order by 1"
    ).fetchall()
    assert rows == [("01046", 2), ("99999", 1)]


def test_existing_parquet_is_left_untouched(con, tmp_path):
    parquet = tmp_path / "olist_geolocation_dataset.parquet"
    parquet.write_bytes(b"not really parquet")
    (tmp_path / "olist_geolocation_dataset.csv").write_text(CSV, encoding="utf-8")
    ensure_geolocation_parquet(con, tmp_path)
    assert parquet.read_bytes() == b"not really parquet"


def test_missing_both_files_raises_with_pointer_to_readme(con, tmp_path):
    with pytest.raises(FileNotFoundError, match="README"):
        ensure_geolocation_parquet(con, tmp_path)
