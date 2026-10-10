"""Build the local Olist star-schema warehouse in DuckDB from the raw files in data/.

Runs sql/staging -> sql/dimensions -> sql/facts, then sql/validation/checks.sql.
The database file is rebuilt from scratch every run. Exits non-zero if any validation check fails.

    uv run python src/transformation/build_warehouse.py [--db warehouse.duckdb] [--data-dir data]
"""

import argparse
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"

# Dimensions before facts (facts reference them); order within each layer is explicit on purpose.
DIMENSIONS = ["dim_date", "dim_geography", "dim_customer", "dim_product", "dim_seller"]
FACTS = ["fact_orders", "fact_order_items", "fact_payments", "fact_reviews"]


def run_sql_file(con: duckdb.DuckDBPyConnection, path: Path, data_dir: Path) -> None:
    sql = path.read_text(encoding="utf-8").replace("${DATA_DIR}", data_dir.as_posix())
    con.execute(sql)


def ensure_geolocation_parquet(con: duckdb.DuckDBPyConnection, data_dir: Path) -> None:
    """Kaggle ships geolocation as CSV; staging reads Parquet. Convert once if only the CSV is present.

    The zip prefix is forced to VARCHAR so leading zeros (e.g. '01046') survive.
    """
    parquet = data_dir / "olist_geolocation_dataset.parquet"
    csv = data_dir / "olist_geolocation_dataset.csv"
    if parquet.exists():
        return
    if not csv.exists():
        raise FileNotFoundError(f"Neither {parquet.name} nor {csv.name} found in {data_dir}. See README.md section 1.")
    con.execute(
        f"""copy (
                select * from read_csv('{csv.as_posix()}', header=true, quote='"',
                                       types={{'geolocation_zip_code_prefix': 'VARCHAR'}})
            ) to '{parquet.as_posix()}' (format parquet)"""
    )
    print(f"converted {csv.name} -> {parquet.name}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()

    args.db.unlink(missing_ok=True)
    con = duckdb.connect(str(args.db))
    ensure_geolocation_parquet(con, args.data_dir)

    layers = [
        ("staging", sorted((SQL_DIR / "staging").glob("*.sql"))),
        ("dimensions", [SQL_DIR / "dimensions" / f"{name}.sql" for name in DIMENSIONS]),
        ("facts", [SQL_DIR / "facts" / f"{name}.sql" for name in FACTS]),
    ]
    for layer, files in layers:
        for path in files:
            run_sql_file(con, path, args.data_dir)
        print(f"built {layer}: {', '.join(p.stem for p in files)}")

    print("\nrow counts")
    for name in [*DIMENSIONS, *FACTS]:
        print(f"  {name:<18} {con.execute(f'select count(*) from {name}').fetchone()[0]:>9,}")

    results = con.execute((SQL_DIR / "validation" / "checks.sql").read_text(encoding="utf-8")).fetchall()
    failed = [r for r in results if not r[3]]
    print(f"\nvalidation: {len(results) - len(failed)}/{len(results)} checks passed")
    for name, expected, actual, passed in results:
        print(f"  [{'ok' if passed else 'FAIL'}] {name}" + ("" if passed else f"  expected={expected} actual={actual}"))

    con.close()
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
