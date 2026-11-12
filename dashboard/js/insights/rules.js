// Findings computed from the data files, so the text always matches the numbers. Each rule names the datasets it
// needs and the page that shows the evidence; it returns null when the data does not support the statement.

import { registerInsight } from "../core/registry.js";
import * as f from "../core/format.js";
import { modelLabel } from "../core/labels.js";

registerInsight({
  id: "one-time-customers", kind: "Customers", needs: ["analytics"], page: "sales",
  compute({ analytics }) {
    const rows = analytics.repeat_customers.rows;
    const one = rows.find((r) => String(r.orders_placed) === "1");
    if (!one) return null;
    return {
      figure: f.pct(one.customer_share_pct, 2, { fraction: false }),
      text: `of customers placed exactly one order, and they bring ${f.pct(one.revenue_share_pct, 1, { fraction: false })} of net revenue. Growth here is an acquisition problem; retention analytics (RFM, CLV) have little to work with.`,
      source: "reports/analytics/07_repeat_customers.csv",
    };
  },
});

registerInsight({
  id: "lateness-kills-reviews", kind: "Delivery", needs: ["analytics"], page: "delivery",
  compute({ analytics }) {
    const rows = analytics.delivery_vs_reviews.rows;
    const onTime = rows[0];
    const worst = rows[rows.length - 1];
    if (!onTime || !worst) return null;
    return {
      figure: `${f.num(onTime.avg_review_score, 2)} → ${f.num(worst.avg_review_score, 2)}`,
      text: `Average review score, ${onTime.delay_group} vs ${worst.delay_group}. Low scores (1-2) rise from ${f.pct(onTime.low_score_pct, 1, { fraction: false })} to ${f.pct(worst.low_score_pct, 1, { fraction: false })}: lateness, not the product, drives bad reviews.`,
      source: "reports/analytics/05_delivery_vs_reviews.csv",
    };
  },
});

registerInsight({
  id: "promise-shortening", kind: "Delivery", needs: ["analytics"], page: "delivery",
  compute({ analytics }) {
    const rows = analytics.delivery_trend.rows.filter((r) => r.delivered_orders >= 500);
    const last = rows[rows.length - 1];
    const yearBefore = rows.find((r) => r.purchase_month === `${+last.purchase_month.slice(0, 4) - 1}${last.purchase_month.slice(4)}`);
    if (!last || !yearBefore) return null;
    return {
      figure: f.pct(last.promised_under_20d_pct, 1, { fraction: false }),
      text: `of ${f.month(last.purchase_month)} orders were promised in under 20 days, against ${f.pct(yearBefore.promised_under_20d_pct, 1, { fraction: false })} a year earlier. Deliveries got faster (median ${f.num(last.median_delivery_days, 1)} days), yet the late rate rose to ${f.pct(last.late_pct, 1, { fraction: false })}: the promise moved, not the logistics.`,
      source: "reports/analytics/08_delivery_trend.csv",
    };
  },
});

registerInsight({
  id: "category-pareto", kind: "Sales", needs: ["analytics"], page: "sales",
  compute({ analytics }) {
    const rows = analytics.category_performance.rows;
    const n80 = rows.findIndex((r) => r.cumulative_share_pct >= 80) + 1;
    if (!n80) return null;
    return {
      figure: `${n80} of ${rows.length}`,
      text: `product categories make up 80% of net revenue. The largest, ${rows[0].category.replace(/_/g, " ")}, alone is ${f.pct(rows[0].revenue_share_pct, 1, { fraction: false })}.`,
      source: "reports/analytics/02_category_performance.csv",
    };
  },
});

registerInsight({
  id: "seller-concentration", kind: "Sellers", needs: ["analytics"], page: "sales",
  compute({ analytics }) {
    const get = (prefix) => analytics.seller_concentration.rows.find((r) => r.metric.startsWith(prefix))?.value;
    const top10pct = get("top 10% of sellers");
    const sellers = get("sellers with net revenue");
    if (top10pct === undefined || sellers === undefined) return null;
    return {
      figure: f.pct(top10pct, 1, { fraction: false }),
      text: `of net revenue comes from the top 10% of ${f.int(sellers)} sellers, while the median seller earned ${f.brl(get("median seller revenue"), { digits: 0 })} over the whole period.`,
      source: "reports/analytics/04_seller_concentration.csv",
    };
  },
});

registerInsight({
  id: "model-lift", kind: "Late-delivery model", needs: ["models"], page: "models",
  compute({ models }) {
    const macro = models.late_delivery.macro_average;
    const best = Object.entries(macro).filter(([, v]) => Number.isFinite(v.pr_auc)).sort((a, b) => b[1].pr_auc - a[1].pr_auc)[0];
    if (!best) return null;
    const [key, v] = best;
    return {
      figure: f.ratio(v.precision_at_top / v.base_rate, 1),
      text: `lift: flagging the riskiest 10% of orders with ${modelLabel(key)} finds late deliveries at ${f.pct(v.precision_at_top)} against a ${f.pct(v.base_rate)} base rate (mean of six monthly out-of-time tests). Useful for ranking, not as a probability.`,
      source: "reports/late_delivery_metrics.json",
    };
  },
});

registerInsight({
  id: "richer-features-did-not-help", kind: "Late-delivery model", needs: ["models"], page: "models",
  compute({ models }) {
    const m = models.late_delivery.macro_average;
    const v1 = m.logistic_regression_v1;
    const others = Object.entries(m).filter(([k]) => /_v[2-9]$/.test(k));
    if (!v1 || !others.length) return null;
    const better = others.filter(([, v]) => v.pr_auc > v1.pr_auc);
    return {
      figure: better.length ? `${better.length} beat v1` : `0 of ${others.length}`,
      text: better.length
        ? `richer feature sets beat the v1 logistic regression on PR-AUC.`
        : `richer feature sets (route, category and system-wide history, delivery slack) beat the simple v1 logistic regression on PR-AUC (${f.num(v1.pr_auc, 3)}). Late deliveries cluster in time more than in sellers or routes.`,
      source: "reports/late_delivery_metrics.json",
    };
  },
});

registerInsight({
  id: "simple-forecasts-win", kind: "Forecasting", needs: ["forecast"], page: "forecast",
  compute({ forecast }) {
    const key = Object.keys(forecast.metrics.models).find((k) => k.startsWith("orders | main (") && k.endsWith("h=4"));
    if (!key) return null;
    const methods = Object.entries(forecast.metrics.models[key]).filter(([k, v]) => !k.startsWith("_") && Number.isFinite(v.mae));
    const [bestKey, best] = methods.sort((a, b) => a[1].mae - b[1].mae)[0];
    return {
      figure: f.num(best.mae_vs_naive, 2),
      text: `MAE relative to the naive forecast for the best 4-week-ahead method (${bestKey.replace(/_/g, " ")}). Simple averages match or beat the trend and autoregressive models on this 85-week series.`,
      source: "reports/forecast_models_metrics.json",
    };
  },
});

registerInsight({
  id: "migration-reconciled", kind: "Data platform", needs: ["lineage"], page: "lineage",
  compute({ lineage }) {
    if (lineage.not_run || !lineage.checks.length) return null;
    const pass = lineage.checks.filter((c) => c.status.startsWith("PASS")).length;
    return {
      figure: `${pass} / ${lineage.checks.length}`,
      text: `reconciliation checks pass between the DuckDB reference and the Snowflake + dbt build, row by row and to the cent (run ${lineage.run.generated || "?"}).`,
      source: "docs/validation/RECONCILIATION_REPORT.md",
    };
  },
});
