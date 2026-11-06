#!/usr/bin/env python3
"""Render the Snowflake/dbt data dictionary (and a lineage diagram) from a dbt ``manifest.json``.

The manifest is produced offline by ``dbt parse`` (no Snowflake connection), so the dictionary can only contain what
is *declared* in the dbt project: model and column descriptions, declared data types, and the tests attached to each
column. It never contains warehouse facts (row counts, observed types); those need a live run.

Usage (from the repo root):

    # 1. produce a manifest WITHOUT touching the tracked snowflake/dbt/target and logs folders
    #    (dummy values only; dbt parse never connects):
    #      set SNOWFLAKE_ACCOUNT=dummy SNOWFLAKE_USER=dummy SNOWFLAKE_PRIVATE_KEY_PATH=dummy.p8
    #      snowflake/dbt/.venv/Scripts/dbt.exe parse --profiles-dir snowflake/dbt --project-dir snowflake/dbt \
    #          --target prod --target-path <scratch>/target --log-path <scratch>/logs
    # 2. render
    python scripts/render_data_dictionary.py --manifest <scratch>/target/manifest.json
    python scripts/render_data_dictionary.py --manifest <scratch>/target/manifest.json --lineage   # mermaid to stdout
    python scripts/render_data_dictionary.py --manifest <scratch>/target/manifest.json --check     # exit 1 if stale

The output is deterministic: nodes are sorted and no timestamps, invocation ids or absolute paths are written, so the
same project always renders the same bytes. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "snowflake" / "dbt" / "target" / "manifest.json"
DEFAULT_OUT = ROOT / "docs" / "data_dictionary" / "DATA_DICTIONARY.md"

# Display order of the layers (folder under models/, relative to the project root).
LAYER_ORDER = [
    ("staging", "Staging (STAGING, views)"),
    ("intermediate", "Intermediate (INTERMEDIATE, views)"),
    ("intermediate/late_delivery", "Intermediate, late-delivery features (INTERMEDIATE, views)"),
    ("marts/core", "Marts, core star schema (MARTS, tables)"),
    ("marts/analytics", "Marts, analytics (MARTS, tables)"),
    ("marts/ml", "Marts, ML inputs (MARTS, tables)"),
    ("pbi", "Power BI views (PBI, views)"),
]
LAYER_TITLE = dict(LAYER_ORDER)
# mermaid subgraph titles
LAYER_SHORT = {
    "source": "RAW sources",
    "staging": "STAGING",
    "intermediate": "INTERMEDIATE",
    "intermediate/late_delivery": "INTERMEDIATE (late delivery)",
    "marts/core": "MARTS core",
    "marts/analytics": "MARTS analytics",
    "marts/ml": "MARTS ml",
    "pbi": "PBI",
}


def load_manifest(path: Path) -> dict:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def norm_path(p: str) -> str:
    return p.replace("\\", "/")


def layer_of(node: dict) -> str:
    """Folder under models/ without the file name, e.g. 'marts/core'."""
    return "/".join(node["fqn"][1:-1])


def md_cell(text: str | None) -> str:
    """Make arbitrary text safe for a one-line markdown table cell."""
    if not text:
        return ""
    out = " ".join(str(text).split())
    return out.replace("|", "\\|")


def relation(node: dict) -> str:
    """Snowflake object name. dbt renders it unquoted, so Snowflake stores it upper-case; shown that way here."""
    rel = node.get("relation_name") or ""
    return rel.replace('"', "").upper()


def short_name(unique_id: str) -> str:
    return unique_id.split(".")[-1]


def describe_test(test: dict) -> str:
    meta = test["test_metadata"]
    name = meta["name"]
    kw = {k: v for k, v in meta["kwargs"].items() if k not in ("model", "column_name")}
    if name == "relationships":
        to = re.sub(r"^ref\('(.+)'\)$", r"\1", str(kw.get("to", "")))
        return f"relationships -> {to}.{kw.get('field')}"
    if name == "accepted_values":
        vals = ", ".join(str(v) for v in kw.get("values", []))
        return f"accepted_values [{vals}]"
    if name == "accepted_range":
        lo, hi = kw.get("min_value"), kw.get("max_value")
        bounds = []
        if lo is not None:
            bounds.append(f">= {lo}")
        if hi is not None:
            bounds.append(f"<= {hi}")
        text = "accepted_range " + " and ".join(bounds)
    elif name == "unique_combination_of_columns":
        text = "unique combination (" + ", ".join(kw.get("combination_of_columns", [])) + ")"
    elif kw:
        text = name + " " + json.dumps(kw, sort_keys=True)
    else:
        text = name
    where = test["config"].get("where")
    return f"{text} (where {where})" if where else text


def first_comment(raw_code: str) -> str:
    """First informative line of the leading '--' comment block of a singular test (boilerplate skipped)."""
    lines = []
    for line in (raw_code or "").splitlines():
        s = line.strip()
        if s.startswith("--"):
            lines.append(s.lstrip("-").strip())
        elif s:
            break
    boiler = "Singular test: returns the rows"
    useful = [t for t in lines if t and not t.startswith(boiler)]
    if useful:
        return useful[0]
    return next((t for t in lines if t), "")


def collect(manifest: dict) -> dict:
    nodes = manifest["nodes"]
    models = {k: v for k, v in nodes.items() if v["resource_type"] == "model"}
    tests = {k: v for k, v in nodes.items() if v["resource_type"] == "test"}
    sources = dict(manifest["sources"])

    col_tests: dict[tuple[str, str], list[str]] = defaultdict(list)
    model_tests: dict[str, list[str]] = defaultdict(list)
    singular: list[dict] = []
    for t in tests.values():
        if t.get("test_metadata"):
            target = t.get("attached_node")
            if not target:
                continue
            text = describe_test(t)
            col = t.get("column_name")
            if col:
                col_tests[(target, col)].append(text)
            else:
                model_tests[target].append(text)
        else:
            singular.append(t)
    for v in col_tests.values():
        v.sort()
    for v in model_tests.values():
        v.sort()
    singular.sort(key=lambda t: t["name"])
    return {"models": models, "tests": tests, "sources": sources, "col_tests": col_tests,
            "model_tests": model_tests, "singular": singular}


def render(manifest: dict) -> str:
    d = collect(manifest)
    models, sources, singular = d["models"], d["sources"], d["singular"]
    meta = manifest["metadata"]
    n_generic = sum(1 for t in d["tests"].values() if t.get("test_metadata"))
    schemas = sorted({m["schema"] for m in models.values()})
    prefixed = not all(s in {"STAGING", "INTERMEDIATE", "MARTS", "PBI"} for s in schemas)
    schema_note = ("prefixed dev/ci schema names (for example DBT_CI_MARTS)" if prefixed
                   else "plain prod schema names (STAGING, INTERMEDIATE, MARTS, PBI)")

    out: list[str] = []
    w = out.append
    w("# Data dictionary: Snowflake + dbt implementation")
    w("")
    w("> Generated by `scripts/render_data_dictionary.py` from the dbt `manifest.json` that `dbt parse` writes. "
      "Do not edit by hand: change the `description:` fields in `snowflake/dbt/models/**/*.yml` and re-render.")
    w("")
    w("## Scope and limits")
    w("")
    w(f"- Source of truth: dbt {meta.get('dbt_version', '?')} manifest (adapter `{meta.get('adapter_type', '?')}`), "
      f"project `{meta.get('project_name', '?')}`, rendered with {schema_note}.")
    w(f"- Contents: {len(sources)} RAW source tables, {len(models)} models, {n_generic} generic tests and "
      f"{len(singular)} singular tests.")
    w("- **Nothing here was observed on a Snowflake account.** `dbt parse` is offline. Descriptions, grains and tests are "
      "what the project declares. Row counts, physical column types and test results are UNVERIFIED until `dbt build` "
      "has run live (see `snowflake/dbt/README_LIVE_CHECKS.md`).")
    has_types = any(c.get("data_type") for m in models.values() for c in m["columns"].values())
    if not has_types:
        w("- Column data types are not declared in the dbt YAML (no `data_type:` entries), so no type column is shown. "
          "Types are defined by each model's SQL (the logical types match the DuckDB views; see "
          "`docs/migration/SNOWFLAKE_MIGRATION.md`) and `docs/data/DATA_MODEL.md` for the DuckDB original.")
    w("- Tests replace the primary-key and foreign-key constraints of the DuckDB warehouse: Snowflake does not enforce "
      "them, so uniqueness, not-null and referential integrity are checked by `dbt test` / `dbt build`.")
    w("- Column coverage: this file lists the columns documented in YAML. Whether those are *all* the columns a model "
      "emits cannot be checked offline.")
    w("")

    # coverage summary
    w("## Documentation coverage")
    w("")
    w("| Layer | Models | Models with a description | Models with column docs | Documented columns |")
    w("|---|---|---|---|---|")
    by_layer: dict[str, list[dict]] = defaultdict(list)
    for m in models.values():
        by_layer[layer_of(m)].append(m)
    for key, _title in LAYER_ORDER:
        ms = by_layer.get(key, [])
        if not ms:
            continue
        described = sum(1 for m in ms if (m.get("description") or "").strip())
        with_cols = sum(1 for m in ms if m["columns"])
        ncols = sum(len(m["columns"]) for m in ms)
        w(f"| `{key}` | {len(ms)} | {described} | {with_cols} | {ncols} |")
    unknown_layers = sorted(set(by_layer) - set(LAYER_TITLE))
    for key in unknown_layers:
        ms = by_layer[key]
        w(f"| `{key}` | {len(ms)} | {sum(1 for m in ms if (m.get('description') or '').strip())} | "
          f"{sum(1 for m in ms if m['columns'])} | {sum(len(m['columns']) for m in ms)} |")
    w("")
    gaps = sorted(m["name"] for m in models.values() if not m["columns"] or not (m.get("description") or "").strip())
    w("Models with no description or no column documentation: " + (", ".join(f"`{g}`" for g in gaps) if gaps else "none."))
    w("")

    # sources
    w("## RAW sources (`olist_raw`)")
    w("")
    w("Loaded by `snowflake/ingestion/load_raw.py` (NOT YET RUN). Every business column is `VARCHAR`; four metadata "
      "columns (`_loaded_at`, `_source_file`, `_source_row_number`, `_batch_id`) are added by the loader. The source "
      "spelling (for example `product_name_lenght`) is kept. Staging types and renames the columns.")
    w("")
    w("| Source table | Snowflake relation | Description | Columns documented in dbt |")
    w("|---|---|---|---|")
    for s in sorted(sources.values(), key=lambda s: s["name"]):
        cols = ", ".join(f"`{c}`" for c in sorted(s["columns"])) if s["columns"] else "none (see `snowflake/ingestion/ddl_raw.sql`)"
        rel = relation(s)
        w(f"| `{s['name']}` | `{rel}` | {md_cell(s.get('description'))} | {cols} |")
    w("")

    # models by layer
    for key, title in LAYER_ORDER + [(k, k) for k in unknown_layers]:
        ms = sorted(by_layer.get(key, []), key=lambda m: m["name"])
        if not ms:
            continue
        w(f"## {title}")
        w("")
        for m in ms:
            uid = m["unique_id"]
            mat = m["config"].get("materialized", "?")
            w(f"### `{m['name']}`")
            w("")
            w(f"- Snowflake object: `{relation(m)}` ({mat})")
            w(f"- File: `snowflake/dbt/{norm_path(m['original_file_path'])}`")
            deps = sorted(short_name(x) for x in m["depends_on"].get("nodes", []))
            w("- Depends on: " + (", ".join(f"`{x}`" for x in deps) if deps else "nothing (no ref or source)"))
            w("")
            desc = " ".join((m.get("description") or "").split())
            w(desc if desc else "_No description in YAML._")
            w("")
            mt = d["model_tests"].get(uid, [])
            if mt:
                w("Model-level tests: " + "; ".join(mt) + ".")
                w("")
            if m["columns"]:
                show_type = any(c.get("data_type") for c in m["columns"].values())
                head = "| Column | " + ("Declared type | " if show_type else "") + "Description | Tests |"
                sep = "|---|" + ("---|" if show_type else "") + "---|---|"
                w(head)
                w(sep)
                for cname, c in m["columns"].items():  # YAML order is the intended column order
                    tests_txt = "; ".join(d["col_tests"].get((uid, cname), [])) or ""
                    typ = f" `{c['data_type']}` |" if show_type and c.get("data_type") else (" |" if show_type else "")
                    w(f"| `{cname}` |{typ} {md_cell(c.get('description'))} | {md_cell(tests_txt)} |")
                w("")
            else:
                w("_No columns documented in YAML._")
                w("")

    # singular tests
    w("## Singular tests")
    w("")
    w("Each test is a query that returns the rows that violate a rule; a passing test returns zero rows. "
      "Not yet run on Snowflake.")
    w("")
    w("| Test | File | Models it reads | Purpose (first comment line) |")
    w("|---|---|---|---|")
    for t in singular:
        reads = sorted(short_name(x) for x in t["depends_on"].get("nodes", []))
        w(f"| `{t['name']}` | `snowflake/dbt/{norm_path(t['original_file_path'])}` | "
          f"{', '.join(f'`{x}`' for x in reads)} | {md_cell(first_comment(t.get('raw_code', '')))} |")
    w("")
    return "\n".join(out).rstrip("\n") + "\n"


def mermaid_id(unique_id: str) -> str:
    kind = unique_id.split(".")[0]
    name = unique_id.split(".")[-1] if kind != "source" else unique_id.split(".")[-1]
    return re.sub(r"[^0-9A-Za-z_]", "_", ("src_" if kind == "source" else "") + name)


def render_lineage(manifest: dict) -> str:
    """Mermaid flowchart of model-to-model and source-to-model dependencies, grouped by layer."""
    d = collect(manifest)
    models, sources = d["models"], d["sources"]
    lines = ["flowchart LR"]
    groups: dict[str, list[str]] = defaultdict(list)
    for s in sorted(sources.values(), key=lambda s: s["name"]):
        groups["source"].append(f'    {mermaid_id(s["unique_id"])}["{s["name"].upper()}"]')
    for m in sorted(models.values(), key=lambda m: m["name"]):
        groups[layer_of(m)].append(f'    {mermaid_id(m["unique_id"])}["{m["name"]}"]')
    for key in ["source"] + [k for k, _ in LAYER_ORDER]:
        if key not in groups:
            continue
        sg = "sg_" + re.sub(r"[^0-9A-Za-z]", "_", key)
        lines.append(f'  subgraph {sg}["{LAYER_SHORT[key]}"]')
        lines.extend(groups[key])
        lines.append("  end")
    edges = []
    for m in models.values():
        for dep in m["depends_on"].get("nodes", []):
            if dep in models or dep in sources:
                edges.append(f"  {mermaid_id(dep)} --> {mermaid_id(m['unique_id'])}")
    lines.extend(sorted(set(edges)))
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST,
                   help="manifest.json from `dbt parse` (default: snowflake/dbt/target/manifest.json)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="markdown file to write")
    p.add_argument("--lineage", action="store_true", help="print the mermaid lineage flowchart to stdout and exit")
    p.add_argument("--check", action="store_true", help="do not write; exit 1 if --out differs from a fresh render")
    args = p.parse_args(argv)

    if not args.manifest.is_file():
        print(f"manifest not found: {args.manifest}\nRun `dbt parse` first (see this script's docstring).", file=sys.stderr)
        return 2
    manifest = load_manifest(args.manifest)
    if args.lineage:
        sys.stdout.write(render_lineage(manifest))
        return 0
    text = render(manifest)
    if args.check:
        current = args.out.read_text(encoding="utf-8") if args.out.is_file() else None
        if current != text:
            print(f"{args.out} is stale or missing; re-run without --check.", file=sys.stderr)
            return 1
        print(f"{args.out} is up to date.")
        return 0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(f"wrote {args.out} ({len(text.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
