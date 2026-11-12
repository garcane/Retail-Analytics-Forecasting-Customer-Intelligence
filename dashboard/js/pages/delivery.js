// Delivery: the late-delivery trend, the promise vs the actual delivery time, and what lateness does to reviews
// (sql/analytics 05 and 08).

import { registerPage } from "../core/registry.js";
import * as f from "../core/format.js";
import { series } from "../core/theme.js";
import { card, grid } from "../components/card.js";
import { controlsRow, segmented } from "../components/controls.js";
import { lineChart } from "../charts/line-chart.js";
import { barChart } from "../charts/bar-chart.js";
import { legend } from "../charts/legend.js";

const pctFmt = (v) => f.pct(v, 1, { fraction: false });

registerPage({
  id: "delivery",
  eyebrow: "Operations",
  title: "Delivery",
  order: 30,
  description: "Delivered orders with a late/on-time label and no timestamp anomaly, by purchase month. Late = delivered after the date promised at checkout.",
  needs: ["analytics"],
  render(root, { analytics }) {
    const all = analytics.delivery_trend.rows;
    const state = { minOrders: "500" };
    controlsRow(root, [
      segmented({ label: "Months shown", value: state.minOrders, options: [
        { value: "500", label: "500+ delivered orders" }, { value: "0", label: "All months" }],
        onChange: (v) => { state.minOrders = v; draw(); } }),
    ]);
    const g = grid(root);
    const tableSpec = () => ({ columns: [
      { key: "purchase_month", label: "Month", format: f.month },
      { key: "delivered_orders", label: "Delivered orders", num: true, format: f.int },
      { key: "late_pct", label: "Late %", num: true, format: pctFmt },
      { key: "median_delivery_days", label: "Median delivery days", num: true, format: (v) => f.num(v, 1) },
      { key: "avg_promised_days", label: "Average promised days", num: true, format: (v) => f.num(v, 1) },
      { key: "promised_under_20d_pct", label: "Promised < 20 days", num: true, format: pctFmt },
    ], rows: all, caption: "reports/analytics/08_delivery_trend.csv" });

    const lateCard = card(g, { title: "Late deliveries by purchase month", subtitle: "Share of delivered orders that arrived after the promised date", span: 6, table: tableSpec });
    const lateChart = lineChart(lateCard.body, { series: [], x: { type: "time", format: f.month, tickFormat: f.monthShort }, y: { format: pctFmt, tickFormat: (v) => `${v}%`, zero: true }, endLabels: false, ariaLabel: "Late delivery rate by month" });

    const daysCard = card(g, { title: "Promise vs actual delivery time", subtitle: "Days from purchase, both on one axis (same unit)", span: 6, table: tableSpec,
      foot: "In 2018 the promise was cut sharply while deliveries kept getting faster: the gap closed from the promise side." });
    daysCard.body.append(legend([
      { id: "p", label: "Average promised days", color: series(2) },
      { id: "m", label: "Median delivery days", color: series(1) },
    ]));
    const daysChart = lineChart(daysCard.body, { series: [], x: { type: "time", format: f.month, tickFormat: f.monthShort }, y: { format: (v) => `${f.num(v, 1)} days`, tickFormat: f.int, zero: true }, ariaLabel: "Promised and actual delivery days by month" });

    const shortCard = card(g, { title: "Orders promised in under 20 days", subtitle: "Share of the month's delivered orders", span: 6, table: tableSpec });
    const shortChart = lineChart(shortCard.body, { series: [], x: { type: "time", format: f.month, tickFormat: f.monthShort }, y: { format: pctFmt, tickFormat: (v) => `${v}%`, zero: true, domain: [0, 100] }, endLabels: false, height: 220, ariaLabel: "Share promised under 20 days by month" });

    const rev = analytics.delivery_vs_reviews.rows;
    const revCard = card(g, { title: "Review score by delivery delay", subtitle: "Latest review per order, 1-5", span: 6,
      foot: "Low score = 1 or 2 stars. Delay is days between the promised and the actual delivery date.",
      table: () => ({ columns: [
        { key: "delay_group", label: "Delay" },
        { key: "orders", label: "Orders", num: true, format: f.int },
        { key: "share_of_orders_pct", label: "Share", num: true, format: pctFmt },
        { key: "avg_review_score", label: "Avg review", num: true, format: (v) => f.num(v, 2) },
        { key: "low_score_pct", label: "Low score %", num: true, format: pctFmt },
      ], rows: rev, caption: "reports/analytics/05_delivery_vs_reviews.csv" }) });
    barChart(revCard.body, {
      data: rev.map((r) => ({ key: r.delay_group, label: r.delay_group, value: r.avg_review_score, note: `${f.int(r.orders)} orders, ${pctFmt(r.low_score_pct)} low scores` })),
      format: (v) => f.num(v, 2), tickFormat: (v) => f.num(v, 0), domain: [0, 5], valueName: "Average review score", ariaLabel: "Average review score by delivery delay",
    });

    function draw() {
      const rows = all.filter((r) => r.delivered_orders >= +state.minOrders);
      const pts = (key) => rows.map((r) => ({ x: f.toTime(r.purchase_month), y: r[key] }));
      lateChart.update({ series: [{ id: "late", label: "Late %", color: series(1), points: pts("late_pct") }] });
      daysChart.update({ series: [
        { id: "p", label: "Average promised days", color: series(2), points: pts("avg_promised_days") },
        { id: "m", label: "Median delivery days", color: series(1), points: pts("median_delivery_days") },
      ] });
      shortChart.update({ series: [{ id: "u20", label: "Promised < 20 days", color: series(1), points: pts("promised_under_20d_pct") }] });
    }
    draw();
  },
});
