// Risk scores in use: what flagging the riskiest orders buys, by decile, flag share, month, state and category.
// Built from the out-of-time v1 scores (src/ml/export_scores.py), rolled up in src/dashboard/build_data.py.

import { registerPage } from "../core/registry.js";
import { manifest } from "../core/data-store.js";
import { el } from "../core/dom.js";
import * as f from "../core/format.js";
import { series, MUTED } from "../core/theme.js";
import { card, grid } from "../components/card.js";
import { kpiRow } from "../components/kpi.js";
import { controlsRow, select } from "../components/controls.js";
import { barChart } from "../charts/bar-chart.js";
import { lineChart } from "../charts/line-chart.js";
import { legend } from "../charts/legend.js";

const nice = (s) => String(s).replace(/_/g, " ");

registerPage({
  id: "risk",
  eyebrow: "Machine learning",
  title: "Risk scores",
  order: 50,
  description: "The v1 logistic regression used as intended: rank each month's orders by risk and flag the top share. Every order is scored by a model trained only on deliveries known before its month.",
  optional: ["risk"],
  async render(root, { risk }) {
    if (!risk) {
      // Say why, from the manifest the build wrote, instead of guessing.
      const m = await manifest();
      const notes = (m.notes || []).filter((n) => n.startsWith("risk.json"));
      root.append(el("div", { class: "card" },
        el("h3", { text: "Risk scores are not in this data build" }),
        el("p", { class: "secondary", text: `The data in dashboard/data was built ${m.generated_at || "at an unknown time"} from ${m.backend || "an unknown backend"} without the risk roll-ups.${notes.length ? ` Build note: ${notes.join(" ")}` : ""}` }),
        el("p", { class: "secondary", text: "Rebuild without --skip-scores (either backend works: src/dashboard/build_data.py --yes for Snowflake, or --backend duckdb offline), then reload." })));
      return;
    }
    const state = { month: "all" };
    controlsRow(root, [select({ label: "Test month", value: "all", options: [{ value: "all", label: "All six months" }, ...risk.months.map((m) => ({ value: m, label: f.month(m) }))],
      onChange: (v) => { state.month = v; draw(); } })]);

    const kpiHost = el("div");
    root.append(kpiHost);
    const g = grid(root);

    const dec = card(g, { title: "Late rate by risk decile", subtitle: "Decile 10 = the riskiest 10% of the month's orders", span: 6,
      table: () => ({ columns: [{ key: "decile", label: "Decile", num: true }, { key: "orders", label: "Orders", num: true, format: f.int }, { key: "late", label: "Late", num: true, format: f.int },
        { key: "late_rate", label: "Late rate", num: true, format: (v) => f.pct(v) }, { key: "lift", label: "Lift", num: true, format: (v) => f.ratio(v) }], rows: deciles() }) });
    const decChart = barChart(dec.body, { data: [], orientation: "vertical", format: (v) => f.pct(v), tickFormat: (v) => f.pct(v, 0), height: 240, ariaLabel: "Late rate by risk decile" });

    const op = card(g, { title: "Precision and recall by flag share", subtitle: "Flag the top X% of each month's orders; all months pooled by order counts", span: 6,
      foot: "Precision = flagged orders that were late. Recall = late orders that were flagged. Flagging more catches more late orders at lower precision.",
      table: () => ({ columns: [{ key: "flag_share", label: "Flag share", num: true, format: (v) => f.pct(v, 0) }, { key: "month", label: "Month" },
        { key: "flagged", label: "Flagged", num: true, format: f.int }, { key: "precision", label: "Precision", num: true, format: (v) => f.pct(v) },
        { key: "recall", label: "Recall", num: true, format: (v) => f.pct(v) }, { key: "base_rate", label: "Base rate", num: true, format: (v) => f.pct(v) }],
        rows: risk.operating_points.filter((r) => state.month === "all" || r.month === state.month) }) });
    op.body.append(legend([{ id: "p", label: "Precision", color: series(1) }, { id: "r", label: "Recall", color: series(2) }, { id: "b", label: "Base rate (no skill)", color: MUTED }]));
    const opChart = lineChart(op.body, { series: [], x: { type: "linear", format: (v) => `flag top ${f.pct(v, 0)}`, tickFormat: (v) => f.pct(v, 0), label: "Share of orders flagged" },
      y: { format: (v) => f.pct(v), tickFormat: (v) => f.pct(v, 0), zero: true }, height: 260, ariaLabel: "Precision and recall by flag share" });

    const st = card(g, { title: "Where the flags land: customer state", subtitle: "Share of the state's orders in the riskiest 10%, all test months", span: 6,
      table: () => ({ columns: [{ key: "customer_state", label: "State" }, { key: "orders", label: "Scored orders", num: true, format: f.int },
        { key: "late_rate", label: "Late rate", num: true, format: (v) => f.pct(v) }, { key: "flagged_share", label: "Flagged", num: true, format: (v) => f.pct(v) }], rows: risk.by_customer_state }) });
    barChart(st.body, { data: risk.by_customer_state.filter((r) => r.orders >= 200).map((r) => ({ key: r.customer_state, label: r.customer_state, value: r.flagged_share, note: `late rate ${f.pct(r.late_rate)}, ${f.int(r.orders)} orders` }))
      .sort((a, b) => b.value - a.value), format: (v) => f.pct(v), tickFormat: (v) => f.pct(v, 0), rowHeight: 22, ariaLabel: "Flagged share by customer state" });
    const ranked = risk.by_customer_state.filter((r) => r.orders >= 200).sort((a, b) => b.flagged_share - a.flagged_share);
    const topS = ranked.slice(0, 3).map((r) => `${r.customer_state} ${f.pct(r.flagged_share, 0)}`).join(", ");
    const lowS = ranked.slice(-2).map((r) => `${r.customer_state} ${f.pct(r.flagged_share, 0)}`).join(", ");
    st.setFoot(`States with at least 200 scored orders. Most flagged: ${topS}; least: ${lowS}. Customer state and route drive the score, which needs a fairness review before any customer-facing use (docs/ml/MODEL_CARD.md).`);

    const cat = card(g, { title: "Where the flags land: product category", subtitle: "25 largest categories by scored orders", span: 6,
      table: () => ({ columns: [{ key: "category", label: "Category", format: nice }, { key: "orders", label: "Scored orders", num: true, format: f.int },
        { key: "late_rate", label: "Late rate", num: true, format: (v) => f.pct(v) }, { key: "flagged_share", label: "Flagged", num: true, format: (v) => f.pct(v) }], rows: risk.by_category_top25 }) });
    barChart(cat.body, { data: risk.by_category_top25.map((r) => ({ key: r.category, label: nice(r.category), value: r.flagged_share, note: `late rate ${f.pct(r.late_rate)}` }))
      .sort((a, b) => b.value - a.value), format: (v) => f.pct(v), tickFormat: (v) => f.pct(v, 0), rowHeight: 22, ariaLabel: "Flagged share by product category" });

    function deciles() {
      if (state.month === "all") return risk.deciles_overall;
      return risk.deciles_by_month.filter((r) => r.month === state.month);
    }

    function draw() {
      const rows = deciles();
      const total = rows.reduce((s, r) => s + r.orders, 0);
      const late = rows.reduce((s, r) => s + r.late, 0);
      const top = rows.find((r) => r.decile === 10);
      const opRows = risk.operating_points.filter((r) => state.month === "all" || r.month === state.month);
      // Pool across months by counts (not a mean of monthly rates), so every figure on the page is computed over the
      // same orders as the decile chart: precision weighted by flagged orders, recall by late orders, base rate by orders.
      const perMonth = {};
      for (const r of risk.deciles_by_month) {
        const m = (perMonth[r.month] ||= { orders: 0, late: 0 });
        m.orders += r.orders;
        m.late += r.late;
      }
      const pooled = (share) => {
        const rs = opRows.filter((r) => Math.abs(r.flag_share - share) < 1e-9);
        let flagged = 0, hits = 0, caught = 0, lateAll = 0, orders = 0;
        for (const r of rs) {
          const m = perMonth[r.month] || { orders: 0, late: 0 };
          flagged += r.flagged;
          hits += (r.precision ?? 0) * r.flagged;
          caught += (r.recall ?? 0) * m.late;
          lateAll += m.late;
          orders += m.orders;
        }
        return { precision: flagged ? hits / flagged : null, recall: lateAll ? caught / lateAll : null, base_rate: orders ? lateAll / orders : null };
      };
      kpiHost.replaceChildren();
      kpiRow(kpiHost, [
        { label: "Scored orders", value: f.int(total), note: state.month === "all" ? `${risk.months.length} test months, pooled` : f.month(state.month) },
        { label: "Base late rate", value: f.pct(late / total) },
        { label: "Late rate in the riskiest 10%", value: top ? f.pct(top.late_rate) : f.DASH, note: top ? `${f.ratio(top.late / top.orders / (late / total), 1)} the base rate` : "" },
        { label: "Recall at 10% flagged", value: f.pct(pooled(0.1).recall), note: "share of all late orders caught" },
      ]);
      const base = late / total;
      decChart.update({ data: rows.map((r) => ({ key: String(r.decile), label: String(r.decile), value: r.late_rate, color: r.decile === 10 ? series(2) : series(1),
        note: `${f.int(r.late)} of ${f.int(r.orders)} late, lift ${f.ratio(r.late_rate / base)}` })), refValue: { value: base, label: "base rate" }, valueName: "Late rate" });
      dec.refreshTable();
      const shares = [...new Set(opRows.map((r) => r.flag_share))].sort((a, b) => a - b);
      const agg = (k) => shares.map((s) => ({ x: s, y: pooled(s)[k] }));
      opChart.update({ series: [
        { id: "p", label: "Precision", color: series(1), markers: true, points: agg("precision") },
        { id: "r", label: "Recall", color: series(2), markers: true, points: agg("recall") },
        { id: "b", label: "Base rate", color: MUTED, points: agg("base_rate") },
      ] });
      op.refreshTable();
    }
    draw();
  },
});
