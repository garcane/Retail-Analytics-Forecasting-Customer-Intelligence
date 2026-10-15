"""Build the DAX / Power BI specification page (docs/powerbi/DAX_SPECIFICATION.html) from model_spec.py.

One self-contained HTML file (no external scripts or fonts). It documents the data sources, the semantic model, every
relationship and measure (with the SQL it mirrors and the value it should return), every page and visual, and the
first-open validation checklist for Power BI Desktop.

    uv run python src/powerbi/build_spec_html.py
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import model_spec as ms

ROOT = ms.ROOT
OUT = ROOT / "docs" / "powerbi" / "DAX_SPECIFICATION.html"
TYPE_LABEL = {"slicer": "Slicer", "card": "Card", "clusteredColumnChart": "Column chart", "clusteredBarChart": "Bar chart",
              "lineChart": "Line chart", "tableEx": "Table"}
TYPE_COLOUR = {"slicer": "#6250d6", "card": "#2a78d6", "clusteredColumnChart": "#1baf7a", "clusteredBarChart": "#1baf7a",
               "lineChart": "#eb6834", "tableEx": "#52514e"}
E = html.escape


def field_text(f: ms.Field) -> str:
    kind, table, name = f
    return f"[{name}]" if kind == "measure" else f"{table}[{name}]"


def manifest() -> dict:
    path = ROOT / "powerbi" / "data" / "_manifest.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def edge_point(box: tuple[float, float, float, float], toward: tuple[float, float]) -> tuple[float, float]:
    """Where the line from a box's centre toward another point leaves the box."""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    dx, dy = toward[0] - cx, toward[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scale = min((w / 2) / abs(dx) if dx else float("inf"), (h / 2) / abs(dy) if dy else float("inf"))
    return cx + dx * scale, cy + dy * scale


def model_svg() -> str:
    pos = {  # table -> (x, y); boxes are 190 x 40
        "dim_date": (20, 20), "dim_customer": (20, 110), "dim_geography": (20, 200),
        "fact_reviews": (300, 20), "fact_orders": (300, 110), "fact_payments": (300, 200), "late_delivery_scores": (300, 290),
        "fact_order_items": (580, 110), "dim_product": (580, 20), "dim_seller": (580, 200),
        "forecast_backtest": (20, 290), "flag_share": (580, 290),
    }
    w, h = 190, 40
    boxes = {n: (x, y, w, h) for n, (x, y) in pos.items()}
    centre = {n: (x + w / 2, y + h / 2) for n, (x, y) in pos.items()}
    out = ['<svg viewBox="0 0 800 350" role="img" aria-label="Semantic model diagram" class="diagram">']
    for r in ms.RELATIONSHIPS:
        a = edge_point(boxes[r.many_table], centre[r.one_table])
        b = edge_point(boxes[r.one_table], centre[r.many_table])
        dash = "" if r.active else ' stroke-dasharray="5 4"'
        out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" class="rel"{dash}/>')
    for t in ms.TABLES:
        x, y = pos[t.name]
        cls = {"fact": "box-fact", "dimension": "box-dim", "other": "box-other"}[t.kind]
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="box-base"/>')
        out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" class="{cls}"/>')
        out.append(f'<text x="{x + w / 2}" y="{y + 25}" text-anchor="middle" class="box-text">{E(t.name)}</text>')
    out.append("</svg>")
    return "".join(out)


def wireframe(page: ms.Page) -> str:
    s = 0.5
    out = [f'<svg viewBox="0 0 {ms.PAGE_W * s:.0f} {ms.PAGE_H * s:.0f}" role="img" aria-label="Layout of {E(page.title)}" class="wire">',
           f'<rect width="{ms.PAGE_W * s:.0f}" height="{ms.PAGE_H * s:.0f}" class="wire-page"/>']
    for v in page.visuals:
        c = TYPE_COLOUR[v.type]
        out.append(f'<rect x="{v.x * s:.1f}" y="{v.y * s:.1f}" width="{v.w * s:.1f}" height="{v.h * s:.1f}" rx="3" fill="{c}" fill-opacity="0.16" stroke="{c}"/>')
        label = E(v.title if len(v.title) < 34 else v.title[:31] + "...")
        out.append(f'<text x="{(v.x + 6) * s:.1f}" y="{(v.y + 16) * s + 2:.1f}" class="wire-text">{label}</text>')
    out.append("</svg>")
    return "".join(out)


CSS = """
:root{color-scheme:light dark;--bg:#fcfcfb;--surface:#ffffff;--ink:#0b0b0b;--ink2:#52514e;--line:#e4e3de;--accent:#2a78d6;--accent2:#eb6834;--code:#f3f2ee}
@media (prefers-color-scheme:dark){:root{--bg:#1a1a19;--surface:#222221;--ink:#f0efec;--ink2:#c3c2b7;--line:#3a3a38;--accent:#3987e5;--accent2:#d95926;--code:#2b2b29}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
header{padding:28px 24px 8px;max-width:1100px;margin:0 auto}h1{margin:0 0 6px;font-size:26px}h2{margin:36px 0 10px;font-size:20px;border-bottom:1px solid var(--line);padding-bottom:6px}
h3{margin:22px 0 6px;font-size:16px}main{max-width:1100px;margin:0 auto;padding:0 24px 60px}p,li{max-width:80ch}
nav{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);z-index:2}nav ul{display:flex;flex-wrap:wrap;gap:4px 16px;list-style:none;margin:0 auto;padding:10px 24px;max-width:1100px}
nav a{color:var(--ink2);text-decoration:none;font-size:14px}nav a:hover{color:var(--accent)}
.banner{background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--accent2);padding:10px 14px;border-radius:6px;margin:14px 0}
.stats{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0}.stat{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:10px 16px;min-width:120px}
.stat b{display:block;font-size:22px}.stat span{color:var(--ink2);font-size:13px}
table{border-collapse:collapse;width:100%;margin:10px 0;background:var(--surface);font-size:14px}th,td{border:1px solid var(--line);padding:6px 9px;text-align:left;vertical-align:top}
th{background:var(--code);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}
code,pre{font-family:ui-monospace,"Cascadia Code",Consolas,monospace;font-size:13px}pre{background:var(--code);border:1px solid var(--line);border-radius:6px;padding:10px 12px;overflow-x:auto;white-space:pre-wrap;word-break:break-word;margin:6px 0}
.measure{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:12px 14px;margin:12px 0}.measure h4{margin:0 0 2px;font-size:16px}
.meta{color:var(--ink2);font-size:13px;margin:0 0 6px}.tag{display:inline-block;background:var(--code);border:1px solid var(--line);border-radius:10px;padding:0 8px;font-size:12px;margin-right:6px}
.ok{color:var(--accent)}details{margin:6px 0}summary{cursor:pointer;font-weight:600}
.diagram,.wire{width:100%;max-width:800px;height:auto;background:var(--surface);border:1px solid var(--line);border-radius:8px}
.diagram .rel{stroke:var(--ink2);stroke-width:1.4}.box-base{fill:var(--surface)}.box-fact{fill:#2a78d6;fill-opacity:.18;stroke:#2a78d6}.box-dim{fill:#1baf7a;fill-opacity:.18;stroke:#1baf7a}.box-other{fill:#eb6834;fill-opacity:.18;stroke:#eb6834}
.box-text{fill:var(--ink);font:13px system-ui,sans-serif}.wire-page{fill:var(--bg);stroke:var(--line)}.wire-text{fill:var(--ink);font:7px system-ui,sans-serif}
.legend span{display:inline-block;margin-right:14px;font-size:13px;color:var(--ink2)}.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin-right:5px}
.check td:first-child{width:34px;text-align:center}@media print{nav{display:none}}
"""


def render() -> str:
    schema = ms.load_schema()
    checks = ms.compute_checks()
    mf = manifest()
    by_measure: dict[str, list[dict]] = {}
    for c in checks:
        by_measure.setdefault(c["measure"], []).append(c)
    n_visuals = sum(len(p.visuals) for p in ms.PAGES)
    parts: list[str] = []
    add = parts.append

    add(f"<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>DAX Specification - Retail Analytics dashboard</title><style>{CSS}</style></head><body>")
    add("<nav><ul><li><a href='#overview'>Overview</a></li><li><a href='#sources'>Data sources</a></li><li><a href='#model'>Model</a></li>"
        "<li><a href='#relationships'>Relationships</a></li><li><a href='#measures'>Measures</a></li><li><a href='#pages'>Pages</a></li>"
        "<li><a href='#checklist'>First-open checklist</a></li><li><a href='#limits'>Limitations</a></li></ul></nav>")
    add("<header><h1>DAX and Power BI specification</h1><p class='meta'>Retail Analytics, Forecasting &amp; Customer Intelligence (Olist data). "
        "Step 1 of 3: this specification &rarr; <a href='DASHBOARD_MOCKUP.html'>mock-up</a> &rarr; <code>powerbi/RetailAnalytics.pbip</code>.</p></header><main>")

    add("<section id='overview'><h2>Overview</h2>")
    add("<p>This page specifies a four-page Power BI report over the project's star schema: the semantic model (tables, relationships, DAX measures) and the report "
        "(pages and visuals). It is <b>generated</b> from <code>src/powerbi/model_spec.py</code>, which also generates the mock-up and the Power BI project, so the three cannot disagree. "
        "Every measure lists the SQL it mirrors and the value it should return, so the numbers in Power BI can be checked against the warehouse.</p>")
    add("<div class='banner'><b>Status.</b> The DAX has not been executed here: Power BI Desktop is not available in the build environment. "
        "The values below are computed from the warehouse by SQL, and the first-open checklist is how to confirm that each DAX measure returns the same number.</div>")
    add(f"<div class='stats'><div class='stat'><b>{len(ms.TABLES)}</b><span>tables</span></div><div class='stat'><b>{len(ms.RELATIONSHIPS)}</b><span>relationships</span></div>"
        f"<div class='stat'><b>{len(ms.MEASURES)}</b><span>measures</span></div><div class='stat'><b>{len(ms.PAGES)}</b><span>pages</span></div>"
        f"<div class='stat'><b>{n_visuals}</b><span>visuals</span></div><div class='stat'><b>{len(checks)}</b><span>checks</span></div></div></section>")

    add("<section id='sources'><h2>Data sources</h2><p>Run <code>uv run python src/powerbi/export_data.py</code> after building the warehouse. It writes the files below to "
        "<code>powerbi/data/</code> (git-ignored, regenerable). Parquet is used for the large facts and the scores (typed, small); CSV for dimensions and the small tables. "
        "Review comment text is deliberately not exported.</p>")
    add("<table><tr><th>Table</th><th>Role</th><th>File</th><th>Rows</th><th>What it holds</th></tr>")
    for t in ms.TABLES:
        add(f"<tr><td><code>{t.name}</code></td><td>{t.kind}</td><td><code>{t.file}</code></td><td class='num'>{mf.get(t.name, {}).get('rows', ''):,}</td><td>{E(t.description)}</td></tr>"
            if mf.get(t.name) else f"<tr><td><code>{t.name}</code></td><td>{t.kind}</td><td><code>{t.file}</code></td><td></td><td>{E(t.description)}</td></tr>")
    add("</table><h3>Set-up in Power BI Desktop</h3><ol>"
        "<li>Install Power BI Desktop (Windows, free). Open <code>powerbi/RetailAnalytics.pbip</code>.</li>"
        "<li>When prompted (or via <i>Transform data &rarr; Manage parameters</i>), set the text parameter <b>DataFolder</b> to the full path of <code>powerbi/data</code>, with no trailing backslash.</li>"
        "<li>Refresh. Every table should load; row counts match the table above.</li>"
        "<li>Work through the <a href='#checklist'>first-open checklist</a>.</li></ol></section>")

    add(f"<section id='model'><h2>Semantic model</h2><p>A star schema with a conformed set of dimensions. Blue boxes are facts, green are dimensions, orange are standalone tables. "
        f"Dashed lines are inactive relationships.</p>{model_svg()}")
    add("<h3>Tables and columns</h3><p class='meta'>Column names and types are read from the warehouse and the export queries. Surrogate and foreign keys are hidden in the field list. "
        "All numeric aggregation is done by the explicit measures below (implicit measures are discouraged).</p>")
    for t in ms.TABLES:
        cols = schema[t.name]
        add(f"<details><summary><code>{t.name}</code> &middot; {len(cols)} columns</summary><p class='meta'>{E(t.description)}</p><table><tr><th>Column</th><th>Type</th><th>Notes</th></tr>")
        for name, dtype in cols:
            notes = []
            if ms.column_hidden(t, name):
                notes.append("hidden")
            if name in t.sort_by:
                notes.append(f"sorts by <code>{t.sort_by[name]}</code>")
            if name in t.formats:
                notes.append(f"format <code>{E(t.formats[name])}</code>")
            if t.date_table and name == "full_date":
                notes.append("date table key")
            add(f"<tr><td><code>{name}</code></td><td>{ms.tmdl_type(dtype)}</td><td>{'; '.join(notes)}</td></tr>")
        add("</table></details>")
    add("</section>")

    add("<section id='relationships'><h2>Relationships</h2><p>All are many-to-one with a single filter direction (from the one side to the many side). "
        "Items, payments and reviews reach dates, customers and states <b>through their order</b>, so there is exactly one filter path to each table and no ambiguity. "
        "The order table keeps one active relationship to the date table (purchase date) and four inactive ones for the other milestones; a measure opts in with <code>USERELATIONSHIP</code>.</p>")
    add("<table><tr><th>Many side</th><th>One side</th><th>Active</th><th>Purpose</th></tr>")
    for r in ms.RELATIONSHIPS:
        add(f"<tr><td><code>{r.many_table}[{r.many_col}]</code></td><td><code>{r.one_table}[{r.one_col}]</code></td><td>{'yes' if r.active else 'no'}</td><td>{E(r.note)}</td></tr>")
    add("</table></section>")

    add("<section id='measures'><h2>Measures</h2><p>Each measure is defined once, on the table shown, with the display folder as its group. "
        "&ldquo;Check&rdquo; gives the filter context and the value the warehouse produces; see the <a href='#checklist'>checklist</a> for the full list.</p>")
    folders: dict[str, list[ms.Measure]] = {}
    for m in ms.MEASURES:
        folders.setdefault(m.folder, []).append(m)
    for folder, items in folders.items():
        add(f"<h3>{E(folder)}</h3>")
        for m in items:
            add(f"<div class='measure'><h4>{E(m.name)}</h4><p class='meta'><span class='tag'>{m.table}</span><span class='tag'>format {E(m.fmt)}</span></p><p>{E(m.description)}</p>"
                f"<pre><code>{E(m.name)} =\n{E(m.dax)}</code></pre>")
            for c in by_measure.get(m.name, []):
                add(f"<p class='meta'><b>Check</b> &middot; {E(c['context'])} &rarr; <b>{E(c['text'])}</b></p>")
            add("</div>")
    add("</section>")

    add("<section id='pages'><h2>Report pages</h2><p>1280 &times; 720 pixels, fixed layout. Visual types are standard Power BI visuals (no custom visuals). "
        "The mock-up and the Power BI project use exactly these positions.</p>")
    add("<p class='legend'>" + "".join(f"<span><i style='background:{TYPE_COLOUR[k]}'></i>{v}</span>" for k, v in TYPE_LABEL.items()) + "</p>")
    for p in ms.PAGES:
        add(f"<h3>{E(p.title)}</h3><p>{E(p.description)}</p>{wireframe(p)}<table><tr><th>Visual</th><th>Type</th><th>Fields</th><th>Sort</th></tr>")
        for v in p.visuals:
            fields = "<br>".join(f"{E(role)}: " + ", ".join(f"<code>{E(field_text(f))}</code>" for f in fs) for role, fs in v.roles.items())
            sort = f"<code>{E(field_text(v.sort[0]))}</code> {v.sort[1].lower()}" if v.sort else ""
            add(f"<tr><td>{E(v.title)}</td><td>{TYPE_LABEL[v.type]}</td><td>{fields}</td><td>{sort}</td></tr>")
        add("</table>")
    add("</section>")

    add("<section id='checklist'><h2>First-open validation checklist</h2><p>After the first refresh, set the filter context shown (using the slicers or a temporary card), "
        "and compare the measure with the expected value. All expected values are computed from the warehouse and the exported files by the SQL in the appendix.</p>")
    add("<h3>Headline checks</h3><table class='check'><tr><th></th><th>Measure</th><th>Filter context</th><th>Expected</th></tr>")
    for i in ms.HEADLINE_CHECKS:
        c = checks[i]
        add(f"<tr><td>&#9744;</td><td>{E(c['measure'])}</td><td>{E(c['context'])}</td><td class='num'><b>{E(c['text'])}</b></td></tr>")
    add("</table><details><summary>All checks, with the SQL behind each value</summary><table><tr><th>Measure</th><th>Filter context</th><th>Expected</th><th>SQL</th></tr>")
    for c in checks:
        sql = c["sql"].replace("{D}", "powerbi/data")
        add(f"<tr><td>{E(c['measure'])}</td><td>{E(c['context'])}</td><td class='num'>{E(c['text'])}</td><td><pre>{E(sql)}</pre></td></tr>")
    add("</table></details></section>")

    add("<section id='limits'><h2>Notes and limitations</h2><ul>"
        "<li><b>Not executed here.</b> Power BI Desktop was not available when this was generated, so no DAX measure has been run and the <code>.pbip</code> has not been opened. "
        "Report files were validated against Microsoft's published JSON schemas; the model files follow the TMDL documentation. Expect that a first open may need small fixes.</li>"
        "<li><b>Pooled versus averaged lift.</b> The <i>Lift</i> measure pools the selected orders, so with all six months selected it shows 2.44x; the 2.8x quoted in the model card is the average of the six monthly lifts (March 2018's high late rate weighs on a pooled figure).</li>"
        "<li><b>Payments do not tie to revenue.</b> <i>Payment Value</i> (all payments) is analysed on its own and differs from net item revenue, by design (DD-04).</li>"
        "<li><b>Category table.</b> The category bar chart lists all 74 categories sorted by revenue (no Top-N filter); per-category average review score is not included because reviews belong to orders, not items.</li>"
        "<li><b>Out-of-time scores.</b> The risk page shows scores for 2018-03 to 2018-08 only; probabilities are not reliable in level, so the page is built around rank (flag the riskiest X%).</li>"
        "<li><b>Forecast methods</b> are the project's baselines; on 85 weeks the ranking of the complex methods is not reliable (see the model card).</li>"
        "<li><b>No credentials.</b> The project reads local files only; <code>DataFolder</code> is a local path set by the user.</li></ul></section>")
    add("</main></body></html>")
    return "".join(parts)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = render()
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({len(text) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
