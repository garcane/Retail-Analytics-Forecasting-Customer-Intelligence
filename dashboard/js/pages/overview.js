// Overview: the headline numbers, the monthly trajectory and the findings the data supports (insight rules).

import { registerPage, getInsights, getPages } from "../core/registry.js";
import { load } from "../core/data-store.js";
import { el } from "../core/dom.js";
import * as f from "../core/format.js";
import { series } from "../core/theme.js";
import { kpiRow } from "../components/kpi.js";
import { card, grid } from "../components/card.js";
import { insightGrid } from "../components/insight.js";
import { lineChart } from "../charts/line-chart.js";

registerPage({
  id: "overview",
  eyebrow: "Retail analytics",
  title: "Overview",
  order: 10,
  description: "Olist marketplace orders from September 2016 to October 2018: what was sold, how it was delivered, and what the models learned.",
  needs: ["kpis", "analytics"],
  async render(root, { kpis, analytics }) {
    kpiRow(root, [
      { label: "Net revenue (item price, excl. freight)", value: f.brl(kpis.net_revenue, { compact: true }), note: f.brl(kpis.net_revenue), hero: true },
      { label: "Net orders", value: f.int(kpis.net_orders), note: "not canceled or unavailable" },
      { label: "Average order value", value: f.brl(kpis.avg_order_value), note: "net revenue / net orders" },
      { label: "Late deliveries", value: f.pct(kpis.late_rate), note: `${f.int(kpis.late_orders)} of ${f.int(kpis.labelled_orders)} delivered orders` },
      { label: "Average review score", value: f.num(kpis.avg_review_score, 2), note: "latest review per order, 1-5" },
      { label: "One-time customers", value: f.pct(kpis.one_time_customer_share, 2), note: "placed exactly one order" },
    ]);

    const months = analytics.monthly_kpis.rows;
    const full = months.filter((r) => !r.thin_month);
    const thin = months.filter((r) => r.thin_month).map((r) => f.month(r.year_month));
    const thinNote = thin.length ? `Months with fewer than 500 orders are left out of the lines: ${thin.join(", ")}.` : "";
    const g = grid(root);

    const rev = card(g, {
      title: "Net revenue by month", subtitle: "Item price of net orders, R$", span: 6, foot: thinNote,
      table: () => ({ columns: [
        { key: "year_month", label: "Month", format: f.month },
        { key: "net_revenue", label: "Net revenue", num: true, format: (v) => f.brl(v) },
        { key: "revenue_mom_pct", label: "vs previous month", num: true, format: (v) => f.signed(v, 1, "%") },
        { key: "thin_month", label: "Thin month", format: (v) => (v ? "yes" : "") },
      ], rows: months, caption: "Monthly net revenue (reports/analytics/01_monthly_kpis.csv)" }),
    });
    lineChart(rev.body, {
      series: [{ id: "rev", label: "Net revenue", color: series(1), points: full.map((r) => ({ x: f.toTime(r.year_month), y: r.net_revenue })) }],
      x: { type: "time", format: f.month, tickFormat: f.monthShort },
      y: { format: (v) => f.brl(v, { compact: true }), zero: true },
      endLabels: false, ariaLabel: "Net revenue by month",
    });

    const ord = card(g, {
      title: "Orders and average order value", subtitle: "Two measures, two charts: net orders per month, and AOV in R$", span: 6, foot: thinNote,
      table: () => ({ columns: [
        { key: "year_month", label: "Month", format: f.month },
        { key: "orders", label: "Net orders", num: true, format: f.int },
        { key: "customers", label: "Customers", num: true, format: f.int },
        { key: "avg_order_value", label: "AOV", num: true, format: (v) => f.brl(v) },
        { key: "items_per_order", label: "Items per order", num: true, format: (v) => f.num(v, 3) },
      ], rows: months, caption: "Monthly orders and AOV" }),
    });
    lineChart(ord.body, {
      series: [{ id: "orders", label: "Net orders", color: series(1), points: full.map((r) => ({ x: f.toTime(r.year_month), y: r.orders })) }],
      x: { type: "time", format: f.month, tickFormat: f.monthShort },
      y: { format: f.int, tickFormat: f.compact, zero: true }, height: 170, endLabels: false, ariaLabel: "Net orders by month",
    });
    lineChart(ord.body, {
      series: [{ id: "aov", label: "Average order value", color: series(3), points: full.map((r) => ({ x: f.toTime(r.year_month), y: r.avg_order_value })) }],
      x: { type: "time", format: f.month, tickFormat: f.monthShort },
      y: { format: (v) => f.brl(v), tickFormat: (v) => `R$ ${f.int(v)}` }, height: 150, endLabels: false, ariaLabel: "Average order value by month",
    });

    // Findings: every registered insight rule whose datasets are available.
    root.append(el("h3", { class: "section-title", text: "What the data says" }));
    const titles = Object.fromEntries(getPages().map((p) => [p.id, p.title]));
    const rules = getInsights();
    const names = [...new Set(rules.flatMap((r) => r.needs))];
    const data = await load([], names);
    const results = [];
    for (const rule of rules) {
      if (rule.needs.some((n) => !data[n])) continue;
      try {
        const r = rule.compute(data);
        if (r) results.push({ kind: rule.kind, page: rule.page, pageTitle: titles[rule.page], ...r });
      } catch (err) {
        console.warn(`insight ${rule.id} failed`, err);
      }
    }
    insightGrid(root, results);
  },
});
