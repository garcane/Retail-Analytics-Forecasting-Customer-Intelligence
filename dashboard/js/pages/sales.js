// Sales & customers: categories, states, payments, repeat customers and seller concentration (sql/analytics 02-04, 06-07).

import { registerPage } from "../core/registry.js";
import * as f from "../core/format.js";
import { series, MUTED } from "../core/theme.js";
import { kpiRow } from "../components/kpi.js";
import { card, grid } from "../components/card.js";
import { controlsRow, segmented, select } from "../components/controls.js";
import { barChart } from "../charts/bar-chart.js";
import { legend } from "../charts/legend.js";

const pctFmt = (v) => f.pct(v, 1, { fraction: false });
const nice = (s) => String(s).replace(/_/g, " ");

const CATEGORY_METRICS = {
  net_revenue: { label: "Net revenue", format: (v) => f.brl(v, { compact: true }), tick: (v) => f.compact(v), sort: -1 },
  late_pct: { label: "Late deliveries %", format: pctFmt, tick: (v) => `${v}%`, sort: -1 },
  avg_review_score: { label: "Average review", format: (v) => f.num(v, 2), tick: (v) => f.num(v, 1), sort: 1, domain: [0, 5] },
  freight_pct_of_price: { label: "Freight % of price", format: pctFmt, tick: (v) => `${v}%`, sort: -1 },
  avg_item_price: { label: "Average item price", format: (v) => f.brl(v), tick: (v) => f.int(v), sort: -1 },
};

const STATE_METRICS = {
  net_revenue: { label: "Net revenue", format: (v) => f.brl(v, { compact: true }), tick: (v) => f.compact(v) },
  late_pct: { label: "Late deliveries %", format: pctFmt, tick: (v) => `${v}%` },
  median_delivery_days: { label: "Median delivery days", format: (v) => `${f.num(v, 1)} d`, tick: (v) => f.int(v) },
  avg_order_value: { label: "Average order value", format: (v) => f.brl(v), tick: (v) => f.int(v) },
  freight_pct_of_price: { label: "Freight % of price", format: pctFmt, tick: (v) => `${v}%` },
};

registerPage({
  id: "sales",
  title: "Sales & customers",
  order: 20,
  description: "Where the revenue comes from. Revenue is item price of net orders (not canceled or unavailable); freight is reported separately.",
  needs: ["analytics"],
  render(root, { analytics }) {
    const state = { catMetric: "net_revenue", top: "15", stateMetric: "net_revenue" };
    const cats = analytics.category_performance.rows;
    const states = analytics.state_performance.rows;

    controlsRow(root, [
      select({ label: "Category measure", value: state.catMetric, options: Object.entries(CATEGORY_METRICS).map(([value, m]) => ({ value, label: m.label })),
        onChange: (v) => { state.catMetric = v; drawCats(); } }),
      segmented({ label: "Categories shown", value: state.top, options: [{ value: "10", label: "Top 10" }, { value: "15", label: "Top 15" }, { value: "all", label: "All" }],
        onChange: (v) => { state.top = v; drawCats(); } }),
      select({ label: "State measure", value: state.stateMetric, options: Object.entries(STATE_METRICS).map(([value, m]) => ({ value, label: m.label })),
        onChange: (v) => { state.stateMetric = v; drawStates(); } }),
    ]);

    const g = grid(root);
    const catCard = card(g, {
      title: "Product categories", span: 7,
      foot: "Categories are ranked by net revenue; 'Top N' keeps the N largest. Late % and review are item-weighted (each item carries its order's outcome).",
      table: () => ({ columns: [
        { key: "category", label: "Category", format: nice },
        { key: "orders", label: "Orders", num: true, format: f.int },
        { key: "net_revenue", label: "Net revenue", num: true, format: (v) => f.brl(v) },
        { key: "revenue_share_pct", label: "Share", num: true, format: pctFmt },
        { key: "cumulative_share_pct", label: "Cumulative", num: true, format: pctFmt },
        { key: "late_pct", label: "Late %", num: true, format: pctFmt },
        { key: "avg_review_score", label: "Review", num: true, format: (v) => f.num(v, 2) },
      ], rows: cats, caption: "reports/analytics/02_category_performance.csv" }),
    });
    const catChart = barChart(catCard.body, { data: [], format: String, ariaLabel: "Product categories" });
    function drawCats() {
      const m = CATEGORY_METRICS[state.catMetric];
      const ranked = state.top === "all" ? cats : cats.slice(0, +state.top);
      // Rank the chosen categories by the chosen measure (largest first) so the bars read top-down.
      const data = ranked.map((r) => ({ key: r.category, label: nice(r.category), value: r[state.catMetric], note: `${f.int(r.orders)} orders` }))
        .sort((a, b) => b.value - a.value);
      catChart.update({ data, format: m.format, tickFormat: m.tick, domain: m.domain, valueName: m.label, ariaLabel: `Product categories by ${m.label}` });
    }
    drawCats();

    const stateCard = card(g, {
      title: "Customer states", span: 5,
      foot: "Late % and delivery days cover delivered orders with a delivery date. SP (São Paulo) dominates both volume and the fastest deliveries.",
      table: () => ({ columns: [
        { key: "customer_state", label: "State" },
        { key: "orders", label: "Orders", num: true, format: f.int },
        { key: "net_revenue", label: "Net revenue", num: true, format: (v) => f.brl(v) },
        { key: "revenue_share_pct", label: "Share", num: true, format: pctFmt },
        { key: "avg_order_value", label: "AOV", num: true, format: (v) => f.brl(v) },
        { key: "late_pct", label: "Late %", num: true, format: pctFmt },
        { key: "median_delivery_days", label: "Median days", num: true, format: (v) => f.num(v, 1) },
      ], rows: states, caption: "reports/analytics/03_state_performance.csv" }),
    });
    const stateChart = barChart(stateCard.body, { data: [], format: String, rowHeight: 22, ariaLabel: "Customer states" });
    function drawStates() {
      const m = STATE_METRICS[state.stateMetric];
      const data = states.map((r) => ({ key: r.customer_state, label: r.customer_state, value: r[state.stateMetric], note: `${f.int(r.orders)} orders` }))
        .sort((a, b) => b.value - a.value);
      stateChart.update({ data, format: m.format, tickFormat: m.tick, valueName: m.label, ariaLabel: `Customer states by ${m.label}` });
    }
    drawStates();

    // Payments
    const pay = analytics.payments.rows.filter((r) => r.payments > 10);
    const payCard = card(g, {
      title: "Payment mix", subtitle: "Share of payment value by type", span: 4,
      foot: "Payment value includes freight and is analysed on its own; revenue figures elsewhere come from items.",
      table: () => ({ columns: [
        { key: "payment_type", label: "Type", format: nice },
        { key: "payments", label: "Payments", num: true, format: f.int },
        { key: "payment_value", label: "Value", num: true, format: (v) => f.brl(v) },
        { key: "value_share_pct", label: "Share", num: true, format: pctFmt },
        { key: "avg_installments", label: "Avg installments", num: true, format: (v) => f.num(v, 2) },
      ], rows: analytics.payments.rows, caption: "reports/analytics/06_payments.csv" }),
    });
    barChart(payCard.body, {
      data: pay.map((r) => ({ key: r.payment_type, label: nice(r.payment_type), value: r.value_share_pct, note: `${f.num(r.avg_installments, 2)} installments on average` })),
      format: pctFmt, tickFormat: (v) => `${v}%`, valueName: "Share of payment value", ariaLabel: "Payment value share by type",
    });

    // Repeat customers: customer share vs revenue share, one measure per chart colour slot (two series, legend in title)
    const rep = analytics.repeat_customers.rows;
    const repCard = card(g, {
      title: "Orders per customer", subtitle: "Share of customers and of net revenue, by number of orders placed", span: 4,
      table: () => ({ columns: [
        { key: "orders_placed", label: "Orders placed" },
        { key: "customers", label: "Customers", num: true, format: f.int },
        { key: "customer_share_pct", label: "Customer share", num: true, format: (v) => f.pct(v, 2, { fraction: false }) },
        { key: "net_revenue", label: "Net revenue", num: true, format: (v) => f.brl(v) },
        { key: "revenue_share_pct", label: "Revenue share", num: true, format: (v) => f.pct(v, 2, { fraction: false }) },
      ], rows: rep, caption: "reports/analytics/07_repeat_customers.csv" }),
    });
    repCard.body.append(legend([
      { id: "c", label: "Customers", color: series(1), shape: "rect" },
      { id: "r", label: "Net revenue", color: series(2), shape: "rect" },
    ]));
    barChart(repCard.body, {
      data: rep.flatMap((r) => [
        { key: `c${r.orders_placed}`, label: `${r.orders_placed} order${r.orders_placed === "1" ? "" : "s"}: customers`, value: r.customer_share_pct, color: series(1) },
        { key: `r${r.orders_placed}`, label: `${r.orders_placed} order${r.orders_placed === "1" ? "" : "s"}: revenue`, value: r.revenue_share_pct, color: series(2) },
      ]),
      format: (v) => f.pct(v, 2, { fraction: false }), tickFormat: (v) => `${v}%`, rowHeight: 24, ariaLabel: "Customer and revenue share by orders placed",
    });

    // Seller concentration as stat tiles
    const sc = Object.fromEntries(analytics.seller_concentration.rows.map((r) => [r.metric, r.value]));
    const sellerCard = card(g, { title: "Seller concentration", subtitle: "Share of net revenue by seller rank", span: 4,
      table: () => ({ columns: [{ key: "metric", label: "Metric" }, { key: "value", label: "Value", num: true, format: (v) => f.num(v, 2) }],
        rows: analytics.seller_concentration.rows, caption: "reports/analytics/04_seller_concentration.csv" }) });
    kpiRow(sellerCard.body, [
      { label: "Sellers with revenue", value: f.int(sc["sellers with net revenue"]) },
      { label: "Top 10% of sellers", value: pctFmt(sc["top 10% of sellers share of revenue (%)"]) },
      { label: "Top 10 sellers", value: pctFmt(sc["top 10 sellers share of revenue (%)"]) },
      { label: "Median seller revenue", value: f.brl(sc["median seller revenue"], { digits: 0 }) },
    ]);
    barChart(sellerCard.body, {
      data: [["top 1 seller share of revenue (%)", "Top seller"], ["top 10 sellers share of revenue (%)", "Top 10 sellers"],
        ["top 10% of sellers share of revenue (%)", "Top 10%"], ["top 50% of sellers share of revenue (%)", "Top 50%"]]
        .filter(([k]) => sc[k] !== undefined).map(([k, label]) => ({ key: k, label, value: sc[k] })),
      format: pctFmt, tickFormat: (v) => `${v}%`, domain: [0, 100], color: MUTED, rowHeight: 24, ariaLabel: "Revenue share by seller rank",
    });
  },
});
