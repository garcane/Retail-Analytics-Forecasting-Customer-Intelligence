"""Generate the Power BI project (powerbi/RetailAnalytics.pbip) from model_spec.py.

    powerbi/RetailAnalytics.pbip
    powerbi/RetailAnalytics.SemanticModel/   definition.pbism + definition/*.tmdl   (TMDL: tables, relationships, measures)
    powerbi/RetailAnalytics.Report/          definition.pbir + definition/...       (PBIR: pages and visuals)
    powerbi/theme/RetailAnalytics.theme.json (optional colour theme)

Files follow Microsoft's published formats (Power BI Desktop projects, TMDL, PBIR). Power BI Desktop is not available in
the build environment, so the project has been validated against the published JSON schemas (tests/test_powerbi_project.py)
and the first open in Desktop found one error (a measure sharing a name with a column ignoring case), now fixed and tested. Output is deterministic: identifiers are derived from names, so re-running changes nothing.

    uv run python src/powerbi/build_pbip.py [--force]   # --force overwrites an existing project, including edits made in Desktop
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import model_spec as ms

OUT = ms.ROOT / "powerbi"
NAME = "RetailAnalytics"
SCHEMA_BASE = "https://developer.microsoft.com/json-schemas/fabric"
SCHEMAS = {
    "pbip": f"{SCHEMA_BASE}/pbip/pbipProperties/1.0.0/schema.json",
    "pbism": f"{SCHEMA_BASE}/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "pbir": f"{SCHEMA_BASE}/item/report/definitionProperties/2.0.0/schema.json",
    "version": f"{SCHEMA_BASE}/item/report/definition/versionMetadata/1.0.0/schema.json",
    "report": f"{SCHEMA_BASE}/item/report/definition/report/3.3.0/schema.json",
    "pages": f"{SCHEMA_BASE}/item/report/definition/pagesMetadata/1.1.0/schema.json",
    "page": f"{SCHEMA_BASE}/item/report/definition/page/2.1.0/schema.json",
    "visual": f"{SCHEMA_BASE}/item/report/definition/visualContainer/2.12.0/schema.json",
}
DATA_FOLDER_PLACEHOLDER = r"C:\REPLACE\WITH\FULL\PATH\TO\powerbi\data"
T = "\t"


# ------------------------------------------------------------------------------------------------ TMDL helpers
def q(name: str) -> str:
    """Quote an object name when TMDL requires it (dot, equals, colon, single quote or whitespace)."""
    if any(c in name for c in ".=:' ") or not name:
        return "'" + name.replace("'", "''") + "'"
    return name


def prop(value: str) -> str:
    """A property value; wrap in double quotes (doubling inner ones) when it contains a quote, so the parser keeps it."""
    return '"' + value.replace('"', '""') + '"' if '"' in value else value


def m_load(table: ms.Table, schema: list[tuple[str, str]]) -> list[str]:
    """Power Query for one table: read the file from DataFolder and set explicit types."""
    path = f'DataFolder & "\\{table.file}"'
    types = ", ".join(f'{{"{c}", {ms.m_type(d).replace("type number", "type number")}}}' for c, d in schema)
    if table.fmt == "parquet":
        return [f"Source = Parquet.Document(File.Contents({path})),", f'Typed = Table.TransformColumnTypes(Source, {{{types}}})']
    return [f'Source = Csv.Document(File.Contents({path}), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            "Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
            f'Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, "en-US")']


def table_tmdl(table: ms.Table, schema: list[tuple[str, str]]) -> str:
    lines = [f"/// {table.description}", f"table {q(table.name)}"]
    if table.date_table:
        lines.append(f"{T}dataCategory: Time")
    lines.append(f"{T}lineageTag: {ms.guid('table', table.name)}")
    lines.append("")
    for m in (m for m in ms.MEASURES if m.table == table.name):
        lines.append(f"{T}/// {m.description}")
        lines.append(f"{T}measure {q(m.name)} = {m.dax}")
        lines.append(f"{T}{T}formatString: {prop(m.fmt)}")
        lines.append(f"{T}{T}displayFolder: {m.folder}")
        lines.append(f"{T}{T}lineageTag: {ms.guid('measure', table.name, m.name)}")
        lines.append("")
    for name, dtype in schema:
        lines.append(f"{T}column {q(name)}")
        lines.append(f"{T}{T}dataType: {ms.tmdl_type(dtype)}")
        if ms.column_hidden(table, name):
            lines.append(f"{T}{T}isHidden")
        if table.date_table and name == "full_date":
            lines.append(f"{T}{T}isKey")
        if name in table.formats:
            lines.append(f"{T}{T}formatString: {prop(table.formats[name])}")
        lines.append(f"{T}{T}lineageTag: {ms.guid('column', table.name, name)}")
        if name in table.sort_by:
            lines.append(f"{T}{T}sortByColumn: {q(table.sort_by[name])}")
        lines.append(f"{T}{T}summarizeBy: none")
        lines.append(f"{T}{T}sourceColumn: {name}")
        lines.append("")
    lines.append(f"{T}partition {q(table.name)} = m")
    lines.append(f"{T}{T}mode: import")
    lines.append(f"{T}{T}source =")
    lines.append(f"{T}{T}{T}let")
    steps = m_load(table, schema)
    for i, step in enumerate(steps):
        lines.append(f"{T}{T}{T}{T}{step}")
    lines.append(f"{T}{T}{T}in")
    lines.append(f"{T}{T}{T}{T}Typed")
    lines.append("")
    return "\n".join(lines)


def relationships_tmdl() -> str:
    out = []
    for r in ms.RELATIONSHIPS:
        out.append(f"relationship {r.name}")
        if not r.active:
            out.append(f"{T}isActive: false")
        out.append(f"{T}fromColumn: {q(r.many_table)}.{q(r.many_col)}")
        out.append(f"{T}toColumn: {q(r.one_table)}.{q(r.one_col)}")
        out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------ PBIR helpers
def lit(text: str) -> dict:
    return {"expr": {"Literal": {"Value": "'" + text.replace("'", "''") + "'"}}}


def field_json(f: ms.Field) -> dict:
    kind, table, name = f
    return {("Column" if kind == "column" else "Measure"): {"Expression": {"SourceRef": {"Entity": table}}, "Property": name}}


def projection(f: ms.Field) -> dict:
    _, table, name = f
    return {"field": field_json(f), "queryRef": f"{table}.{name}", "nativeQueryRef": name, "active": True}


def visual_json(v: ms.Visual, z: int) -> dict:
    visual: dict = {
        "visualType": v.type,
        "query": {"queryState": {role: {"projections": [projection(f) for f in fields]} for role, fields in v.roles.items()}},
        "drillFilterOtherVisuals": True,
    }
    if v.sort:
        visual["query"]["sortDefinition"] = {"sort": [{"field": field_json(v.sort[0]), "direction": v.sort[1]}], "isDefaultSort": False}
    if v.type == "slicer" and v.id.endswith(("month", "cat", "state")):
        visual["objects"] = {"data": [{"properties": {"mode": lit("Dropdown")}}]}
    visual["visualContainerObjects"] = {"title": [{"properties": {"text": lit(v.title), "show": {"expr": {"Literal": {"Value": "true"}}}}}]}
    return {"$schema": SCHEMAS["visual"], "name": v.id,
            "position": {"x": v.x, "y": v.y, "z": z * 1000, "height": v.h, "width": v.w, "tabOrder": z * 1000},
            "visual": visual}


def dump(obj: dict) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False) + "\n"


THEME = {"name": "Retail Analytics", "dataColors": list(ms.PALETTE.values()), "background": "#FFFFFF", "foreground": "#0B0B0B",
         "tableAccent": ms.PALETTE["blue"], "good": ms.PALETTE["aqua"], "neutral": ms.PALETTE["yellow"], "bad": ms.PALETTE["red"]}


def files() -> dict[str, str]:
    """Every file of the project, as {relative path: text}."""
    schema = ms.load_schema()
    sm, rp = f"{NAME}.SemanticModel", f"{NAME}.Report"
    out: dict[str, str] = {
        f"{NAME}.pbip": dump({"$schema": SCHEMAS["pbip"], "version": "1.0", "artifacts": [{"report": {"path": rp}}], "settings": {"enableAutoRecovery": True}}),
        f"{sm}/definition.pbism": dump({"$schema": SCHEMAS["pbism"], "version": "4.0"}),
        f"{sm}/definition/database.tmdl": "database\n" + f"{T}compatibilityLevel: 1567\n",
        f"{sm}/definition/model.tmdl": "model Model\n" + f"{T}culture: en-US\n{T}defaultPowerBIDataSourceVersion: powerBI_V3\n{T}discourageImplicitMeasures\n{T}sourceQueryCulture: en-US\n\n"
                                      + "\n".join(f"ref table {q(t.name)}" for t in ms.TABLES) + "\n",
        f"{sm}/definition/expressions.tmdl": f'expression DataFolder = "{DATA_FOLDER_PLACEHOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
                                              f"{T}lineageTag: {ms.guid('expression', 'DataFolder')}\n",
        f"{sm}/definition/relationships.tmdl": relationships_tmdl(),
        f"{rp}/definition.pbir": dump({"$schema": SCHEMAS["pbir"], "version": "4.0", "datasetReference": {"byPath": {"path": f"../{sm}"}}}),
        f"{rp}/definition/version.json": dump({"$schema": SCHEMAS["version"], "version": "2.0.0"}),
        f"{rp}/definition/report.json": dump({
            "$schema": SCHEMAS["report"],
            "themeCollection": {"baseTheme": {"name": "CY24SU10", "reportVersionAtImport": {"page": "2.1.0", "report": "3.3.0", "visual": "2.12.0"}, "type": "SharedResources"}},
        }),
        f"{rp}/definition/pages/pages.json": dump({"$schema": SCHEMAS["pages"], "pageOrder": [p.id for p in ms.PAGES], "activePageName": ms.PAGES[0].id}),
        "theme/RetailAnalytics.theme.json": dump(THEME),
    }
    for t in ms.TABLES:
        out[f"{sm}/definition/tables/{t.name}.tmdl"] = table_tmdl(t, schema[t.name])
    for p in ms.PAGES:
        out[f"{rp}/definition/pages/{p.id}/page.json"] = dump({"$schema": SCHEMAS["page"], "name": p.id, "displayName": p.title, "displayOption": "FitToPage",
                                                               "width": ms.PAGE_W, "height": ms.PAGE_H})
        for z, v in enumerate(p.visuals, start=1):
            out[f"{rp}/definition/pages/{p.id}/visuals/{v.id}/visual.json"] = dump(visual_json(v, z))
    return out


def main() -> int:
    if (OUT / f"{NAME}.pbip").exists() and "--force" not in sys.argv:
        print(f"{OUT.relative_to(ms.ROOT)}/{NAME}.pbip already exists and has been saved by Power BI Desktop, which now owns the report and model. "
              "Regenerating would overwrite every change made in Desktop. Re-run with --force only to start over from the specification.")
        return 1
    generated = files()
    for sub in (f"{NAME}.SemanticModel", f"{NAME}.Report", "theme"):  # rebuild generated folders; keep README.md and data/
        shutil.rmtree(OUT / sub, ignore_errors=True)
    (OUT / f"{NAME}.pbip").unlink(missing_ok=True)
    for rel, text in generated.items():
        path = OUT / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote {len(generated)} files under {OUT.relative_to(ms.ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
