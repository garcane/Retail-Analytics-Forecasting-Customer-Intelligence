"""Write a Snowflake-backed copy of the Power BI project. The committed project is never modified.

    .\\.venv\\Scripts\\python.exe powerbi/snowflake/apply_snowflake_source.py [--out powerbi_snowflake] [--force] [--ml-on-files]

What it does
  1. Copies RetailAnalytics.pbip, RetailAnalytics.Report and RetailAnalytics.SemanticModel into --out
     (default: powerbi_snowflake/ at the repo root, which should be git-ignored). Local Power BI state (.pbi/, cache.abf) is not copied.
  2. In the copy only, replaces definition/expressions.tmdl (DataFolder -> SnowflakeServer and SnowflakeWarehouse parameters)
     and, in each of the 12 import tables, the partition `source` block with the Power Query M template in templates/<table>.m.
  3. Leaves every other file byte-identical (report pages, relationships, measures, columns, formatting).
  With --ml-on-files only the nine PBI-schema tables are patched; late_delivery_scores, forecast_backtest and flag_share keep their
  file sources and the DataFolder parameter is kept (only needed where the ML tables have not been published by
  src/ml/publish_ml.py --write).

Safety
  * Refuses to write into a non-empty --out unless --force is given; --force replaces only the three project items by name,
    never anything else in --out. Refuses an --out that is, or is inside, the source project.
  * Refuses to run if a template's Table.TransformColumnTypes step differs from the one in the source table (the template would
    then change column types), or if a source table's partition no longer reads from DataFolder (already patched or edited in Desktop).
  * Line endings of each rewritten file follow the source file (the committed project is CRLF).

Nothing here connects to Snowflake or opens Power BI Desktop. Whether Desktop accepts the patched copy is UNVERIFIED.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_DIR = ROOT / "powerbi"
DEFAULT_OUT = ROOT / "powerbi_snowflake"
NAME = "RetailAnalytics"
PROJECT_ITEMS = (f"{NAME}.pbip", f"{NAME}.Report", f"{NAME}.SemanticModel")
EXPRESSIONS = Path(f"{NAME}.SemanticModel") / "definition" / "expressions.tmdl"
TABLES_DIR = Path(f"{NAME}.SemanticModel") / "definition" / "tables"
TEMPLATE_DIR = HERE / "templates"
EXPRESSIONS_TEMPLATE = HERE / "expressions.tmdl"

# One Power BI import table each; the three ML tables are fed by Python write-back (see docs/migration/POWERBI_SWITCH_GUIDE.md).
PBI_TABLES = ("dim_date", "dim_customer", "dim_product", "dim_seller", "dim_geography",
              "fact_orders", "fact_order_items", "fact_payments", "fact_reviews")
ML_TABLES = ("late_delivery_scores", "forecast_backtest", "flag_share")
TABLES = PBI_TABLES + ML_TABLES

TYPED_RE = re.compile(r"^[ \t]*Typed = Table\.TransformColumnTypes\(\w+, (.*)\)[ \t]*$", re.M)
SOURCE_INDENT = "\t\t\t\t"  # a partition's M expression sits four tabs deep in TMDL


class PatchError(RuntimeError):
    pass


def _read(path: Path) -> tuple[str, str]:
    """Return (text with LF endings, eol used by the file)."""
    raw = path.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    return raw.replace("\r\n", "\n"), eol


def _write(path: Path, text: str, eol: str) -> None:
    path.write_bytes(text.replace("\n", eol).encode("utf-8"))


def typed_step_arguments(m_text: str, label: str) -> str:
    """The arguments of the Table.TransformColumnTypes step after its first (previous-step) argument."""
    found = TYPED_RE.findall(m_text.replace("\r\n", "\n"))
    if len(found) != 1:
        raise PatchError(f"{label}: expected exactly one 'Typed = Table.TransformColumnTypes(...)' step, found {len(found)}")
    return found[0]


def split_partition(text: str, table: str, label: str) -> tuple[int, int]:
    """Line range [start, stop) of the partition's M expression (the lines under 'source =') in LF text."""
    lines = text.split("\n")
    heads = [i for i, line in enumerate(lines) if line == f"\tpartition {table} = m"]
    if len(heads) != 1:
        raise PatchError(f"{label}: expected one partition '{table}', found {len(heads)}")
    i = heads[0] + 1
    while i < len(lines) and lines[i] != "\t\tsource =":
        if not lines[i].startswith("\t\t"):
            raise PatchError(f"{label}: no 'source =' line inside partition '{table}'")
        i += 1
    if i >= len(lines):
        raise PatchError(f"{label}: no 'source =' line inside partition '{table}'")
    start = i + 1
    stop = start
    while stop < len(lines) and lines[stop].startswith("\t\t\t"):
        stop += 1
    if stop == start:
        raise PatchError(f"{label}: empty source block in partition '{table}'")
    return start, stop


def patch_table(text: str, table: str, template: str) -> str:
    """Replace the partition source block of one table (LF text in, LF text out)."""
    label = f"{table}.tmdl"
    start, stop = split_partition(text, table, label)
    lines = text.split("\n")
    block = "\n".join(lines[start:stop])
    if "DataFolder" not in block:
        raise PatchError(f"{label}: partition source does not read from DataFolder (already patched, or edited in Desktop); refusing to guess")
    if typed_step_arguments(block, f"{label} (source)") != typed_step_arguments(template, f"templates/{table}.m"):
        raise PatchError(
            f"{label}: the template's Table.TransformColumnTypes differs from the project's; patching would change column types. "
            f"Update powerbi/snowflake/templates/{table}.m to match."
        )
    new_block = [SOURCE_INDENT + line if line else line for line in template.replace("\r\n", "\n").rstrip("\n").split("\n")]
    return "\n".join(lines[:start] + new_block + lines[stop:])


def _is_inside(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def apply(source: Path = SOURCE_DIR, out: Path = DEFAULT_OUT, force: bool = False, ml_on_files: bool = False) -> list[Path]:
    """Create the patched copy in `out`. Returns the files that were rewritten (all inside `out`).

    ml_on_files=True patches only the nine PBI-schema tables: the three Python-fed tables keep their file (parquet/CSV) sources
    and the DataFolder parameter is kept next to the new Snowflake parameters, so the copy works before ML write-back exists."""
    source, out = source.resolve(), out.resolve()
    for item in PROJECT_ITEMS:
        if not (source / item).exists():
            raise PatchError(f"{source / item} not found")
    if _is_inside(out, source):
        raise PatchError(f"--out {out} is the source project or inside it; the original must never be written to")
    templates = {t: (TEMPLATE_DIR / f"{t}.m").read_text(encoding="utf-8") for t in TABLES}

    # Build everything in memory first from the (read-only) source, so a failure leaves no half-written copy.
    rewritten: dict[Path, tuple[str, str]] = {}
    expr_text = EXPRESSIONS_TEMPLATE.read_text(encoding="utf-8").replace("\r\n", "\n")
    src_expr, expr_eol = _read(source / EXPRESSIONS)
    if "DataFolder" not in src_expr:
        raise PatchError("expressions.tmdl does not define DataFolder (already patched?)")
    rewritten[EXPRESSIONS] = ((src_expr.rstrip("\n") + "\n\n" + expr_text) if ml_on_files else expr_text, expr_eol)
    for t in (PBI_TABLES if ml_on_files else TABLES):
        text, eol = _read(source / TABLES_DIR / f"{t}.tmdl")
        rewritten[TABLES_DIR / f"{t}.tmdl"] = (patch_table(text, t, templates[t]), eol)

    if out.exists() and any(out.iterdir()):
        if not force:
            raise PatchError(f"{out} is not empty; choose another --out or pass --force (replaces only {', '.join(PROJECT_ITEMS)})")
        for item in PROJECT_ITEMS:
            target = out / item
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
    out.mkdir(parents=True, exist_ok=True)

    ignore = shutil.ignore_patterns(".pbi", "cache.abf", "localSettings.json")
    for item in PROJECT_ITEMS:
        src = source / item
        if src.is_dir():
            shutil.copytree(src, out / item, ignore=ignore)
        else:
            shutil.copy2(src, out / item)

    written = []
    for rel, (text, eol) in rewritten.items():
        target = out / rel
        _write(target, text, eol)
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--source", type=Path, default=SOURCE_DIR, help="folder holding RetailAnalytics.pbip (default: powerbi/)")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the patched copy (default: powerbi_snowflake/)")
    parser.add_argument("--force", action="store_true", help="replace the project items in a non-empty --out")
    parser.add_argument("--ml-on-files", action="store_true",
                        help="keep late_delivery_scores, forecast_backtest and flag_share on their file sources (and keep the DataFolder "
                             "parameter); only needed where src/ml/publish_ml.py has not published the ML tables")
    args = parser.parse_args(argv)
    try:
        written = apply(args.source, args.out, args.force, args.ml_on_files)
    except PatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"wrote patched copy to {args.out.resolve()}")
    print(f"rewrote {len(written)} files (expressions.tmdl + {len(written) - 1} partition sources); everything else is a byte copy")
    print("next: docs/migration/POWERBI_SWITCH_GUIDE.md (set SnowflakeServer / SnowflakeWarehouse, sign in). Not opened in Desktop: UNVERIFIED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
