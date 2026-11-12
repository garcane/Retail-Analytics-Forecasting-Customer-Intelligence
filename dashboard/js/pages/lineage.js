// Data & lineage: where every number on this dashboard comes from, the two warehouse implementations (DuckDB and
// Snowflake + dbt), and the live reconciliation between them.

import { registerPage } from "../core/registry.js";
import { el } from "../core/dom.js";
import * as f from "../core/format.js";
import { manifest } from "../core/data-store.js";
import { card, grid } from "../components/card.js";
import { kpiRow } from "../components/kpi.js";
import { dataTable } from "../components/data-table.js";

const FLOW = [
  ["Raw data", "9 Olist CSVs (Kaggle), ~124 MB", "the same files feed both implementations"],
  ["DuckDB (reference)", "sql/staging → dimensions → facts, 22 checks", "src/transformation/build_warehouse.py; local, free"],
  ["Snowflake RAW", "stage + COPY INTO, all text + load metadata", "snowflake/ingestion/load_raw.py; idempotent by file hash"],
  ["dbt (Snowflake)", "staging → intermediate → marts, 46 models, 321 tests", "snowflake/dbt; same table names as DuckDB"],
  ["Python models", "late-delivery classifier, weekly forecasts", "src/ml; reads either backend via src/data_access"],
  ["This dashboard", "dashboard/ (HTML + CSS + JS modules)", "data built by src/dashboard/build_data.py"],
  ["Power BI", "conventional reporting", "file sources, or Snowflake via powerbi/snowflake"],
];

registerPage({
  id: "lineage",
  eyebrow: "Data platform",
  title: "Data & lineage",
  order: 90,
  description: "Where the numbers come from, and the evidence that the DuckDB and Snowflake implementations agree.",
  needs: ["lineage"],
  async render(root, { lineage }) {
    const m = await manifest();
    const checks = lineage.checks || [];
    const pass = checks.filter((c) => c.status.startsWith("PASS")).length;
    const diffs = checks.reduce((s, c) => s + (+c.unexplained || 0) + (+c.missing_extra || 0), 0);
    kpiRow(root, [
      { label: "Reconciliation checks passing", value: lineage.not_run ? "not run" : `${pass} / ${checks.length}`, hero: true, note: lineage.run.generated ? `live run ${lineage.run.generated}` : "" },
      { label: "Unexplained differences", value: lineage.not_run ? f.DASH : f.int(diffs), note: "missing/extra keys + value diffs" },
      { label: "Dashboard data built from", value: m.backend === "snowflake" ? "Snowflake" : "DuckDB", note: m.git_sha ? `commit ${m.git_sha}` : "" },
    ]);

    const g = grid(root);
    const flow = card(g, { title: "Pipeline", subtitle: "One dataset, two warehouse implementations, three consumers", span: 6 });
    const ol = el("ol", { class: "facts-list" });
    for (const [name, what, where] of FLOW) ol.append(el("li", {}, el("strong", { text: name }), ` · ${what}. `, el("span", { class: "muted", text: where })));
    flow.body.append(ol);

    const run = card(g, { title: "Reconciliation run", subtitle: "DuckDB (reference) vs Snowflake marts, src/reconciliation", span: 6,
      foot: "Counts, keys, money and timestamps compared exactly; doubles within 1e-9 relative. Full report: docs/validation/RECONCILIATION_REPORT.md." });
    run.body.append(el("dl", { class: "facts" }, Object.entries(lineage.run).flatMap(([k, v]) => [el("dt", { text: k }), el("dd", { text: v })])));

    const tbl = card(g, { title: "Checks", subtitle: "Every table and analytics mart, compared row by row on natural keys", span: 12 });
    dataTable(tbl.body, { columns: [
      { key: "check", label: "Check" }, { key: "group", label: "Group" }, { key: "status", label: "Status" },
      { key: "left_rows", label: "DuckDB rows", num: true, format: (v) => f.int(+v) }, { key: "right_rows", label: "Snowflake rows", num: true, format: (v) => f.int(+v) },
      { key: "missing_extra", label: "Missing + extra keys", num: true }, { key: "unexplained", label: "Unexplained diffs", num: true },
    ], rows: checks, caption: lineage.source });

    const ds = card(g, { title: "Datasets behind this dashboard", subtitle: "dashboard/data/manifest.json", span: 12,
      foot: (m.notes || []).join(" ") });
    dataTable(ds.body, { columns: [
      { key: "name", label: "File" }, { key: "title", label: "Contents" }, { key: "source", label: "Source" },
      { key: "rows", label: "Rows", num: true, format: (v) => (v == null ? "" : f.int(v)) }, { key: "bytes", label: "Size", num: true, format: (v) => `${f.num(v / 1024, 1)} KB` },
    ], rows: Object.entries(m.datasets).map(([name, d]) => ({ name: d.file, ...d })), maxHeight: false });
  },
});
