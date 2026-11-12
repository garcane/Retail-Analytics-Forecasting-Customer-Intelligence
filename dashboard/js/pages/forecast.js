// Weekly forecasts: the series, the rolling-origin backtest (forecast vs actual per week, per method) and the accuracy
// table. Methods are discovered from the data: a new method in forecast_backtest appears automatically.

import { registerPage } from "../core/registry.js";
import * as f from "../core/format.js";
import { series, MUTED } from "../core/theme.js";
import { methodLabel } from "../core/labels.js";
import { card, grid } from "../components/card.js";
import { controlsRow, segmented } from "../components/controls.js";
import { lineChart } from "../charts/line-chart.js";
import { barChart } from "../charts/bar-chart.js";
import { legend } from "../charts/legend.js";

registerPage({
  id: "forecast",
  eyebrow: "Forecasting",
  title: "Weekly forecast",
  order: 60,
  description: "Weekly orders and revenue, forecast one and four weeks ahead. Every forecast uses only the weeks before it (rolling origin), 2017-01 to 2018-08.",
  needs: ["forecast"],
  render(root, { forecast }) {
    const bt = forecast.backtest;
    const methods = [...new Set(bt.map((r) => r.method))].filter((m) => m !== "actual");
    const slot = Object.fromEntries(methods.map((m, i) => [m, series(i + 2)])); // slot 1 is reserved for "actual"
    const horizons = [...new Set(bt.map((r) => r.horizon))].sort((a, b) => a - b);
    const state = { target: "orders", horizon: horizons[0], selected: new Set(["naive_last_week", "moving_average_8", "combo_naive_ma8"].filter((m) => methods.includes(m))) };
    const yFmt = (v) => (state.target === "revenue" ? f.brl(v, { compact: true }) : f.int(v));
    const yTick = (v) => f.compact(v);

    controlsRow(root, [
      segmented({ label: "Target", value: state.target, options: [{ value: "orders", label: "Orders" }, { value: "revenue", label: "Revenue (R$)" }], onChange: (v) => { state.target = v; draw(); } }),
      segmented({ label: "Horizon", value: state.horizon, options: horizons.map((h) => ({ value: h, label: `${h} week${h > 1 ? "s" : ""} ahead` })), onChange: (v) => { state.horizon = v; draw(); } }),
    ]);
    const g = grid(root);

    const w = forecast.weekly;
    const mw = forecast.main_window;
    const series1 = card(g, { title: "Weekly series", subtitle: "Shaded weeks are outside the evaluation window", span: 12,
      foot: `Evaluation runs ${f.day(mw.first_week)} to ${f.day(mw.last_clean_week)}. The week of ${f.day(mw.suspect_week)} is incomplete in the source data and excluded. Revenue here is item price over all statuses.`,
      table: () => ({ columns: [{ key: "week", label: "Week", format: f.day }, { key: "orders", label: "Orders", num: true, format: f.int }, { key: "revenue", label: "Revenue", num: true, format: (v) => f.brl(v) }], rows: w }) });
    const seriesChart = lineChart(series1.body, { series: [], x: { type: "time", format: (v) => `week of ${f.day(v)}`, tickFormat: f.monthShort }, y: { format: yFmt, tickFormat: yTick, zero: true }, endLabels: false, height: 220, ariaLabel: "Weekly series" });

    const fc = card(g, { title: "Forecast vs actual", subtitle: "Select methods in the legend", span: 8,
      table: () => ({ columns: [{ key: "target_week", label: "Week", format: f.day }, { key: "method", label: "Method", format: methodLabel },
        { key: "forecast", label: "Forecast", num: true, format: (v) => f.num(v, 0) }, { key: "actual", label: "Actual", num: true, format: (v) => f.num(v, 0) },
        { key: "abs_error", label: "Abs. error", num: true, format: (v) => f.num(v, 0) }],
        rows: bt.filter((r) => r.target === state.target && r.horizon === state.horizon && r.method !== "actual") }) });
    const legendHost = document.createElement("div");
    fc.body.append(legendHost);
    const fcChart = lineChart(fc.body, { series: [], x: { type: "time", format: (v) => `week of ${f.day(v)}`, tickFormat: f.monthShort }, y: { format: yFmt, tickFormat: yTick, zero: true }, height: 300, endLabels: false, ariaLabel: "Forecast vs actual" });

    const acc = card(g, { title: "Accuracy vs the naive forecast", subtitle: "MAE / MAE of 'same as last week'; below 1 beats naive", span: 4,
      table: () => ({ columns: [{ key: "method", label: "Method", format: methodLabel }, { key: "mae", label: "MAE", num: true, format: (v) => f.num(v, 1) },
        { key: "mape", label: "MAPE", num: true, format: (v) => f.pct(v) }, { key: "mae_vs_naive", label: "vs naive", num: true, format: (v) => f.num(v, 3) },
        { key: "bias", label: "Bias", num: true, format: (v) => f.num(v, 1) }, { key: "share_of_weeks_beating_naive", label: "Weeks beating naive", num: true, format: (v) => f.pct(v, 0) }],
        rows: metricRows() }) });
    const accChart = barChart(acc.body, { data: [], format: (v) => f.num(v, 2), rowHeight: 26, zero: true, ariaLabel: "MAE relative to naive" });

    function metricRows() {
      const key = Object.keys(forecast.metrics.models).find((k) => k.startsWith(`${state.target} | main (`) && k.endsWith(`h=${state.horizon}`));
      const block = key ? forecast.metrics.models[key] : {};
      return Object.entries(block).filter(([k, v]) => !k.startsWith("_") && Number.isFinite(v?.mae)).map(([method, v]) => ({ method, ...v }));
    }

    function draw() {
      const tgt = state.target;
      const inWindow = (t) => t >= f.toTime(mw.first_week) && t <= f.toTime(mw.last_clean_week);
      const pts = w.map((r) => ({ x: f.toTime(r.week.slice(0, 10)), y: r[tgt] }));
      const xs = pts.map((p) => p.x);
      seriesChart.update({
        series: [{ id: "s", label: tgt === "orders" ? "Orders" : "Revenue", color: series(1), points: pts }],
        spans: [
          { x0: Math.min(...xs), x1: f.toTime(mw.first_week) - 86400000 * 3.5 },
          { x0: f.toTime(mw.last_clean_week) + 86400000 * 3.5, x1: Math.max(...xs) },
        ],
        y: { format: yFmt, tickFormat: yTick, zero: true },
      });

      const rows = bt.filter((r) => r.target === tgt && r.horizon === state.horizon);
      const actual = rows.filter((r) => r.method === "actual").map((r) => ({ x: f.toTime(r.target_week), y: r.actual }));
      legendHost.replaceChildren(legend([{ id: "actual", label: "Actual", color: series(1) },
        ...methods.map((m) => ({ id: m, label: methodLabel(m), color: slot[m], active: state.selected.has(m) }))], {
        onToggle: (id, on) => { if (id === "actual") return; if (on) state.selected.add(id); else state.selected.delete(id); drawForecast(); },
      }));
      function drawForecast() {
        fcChart.update({ series: [
          { id: "actual", label: "Actual", color: series(1), width: 2.5, points: actual },
          ...methods.filter((m) => state.selected.has(m)).map((m) => ({ id: m, label: methodLabel(m), color: slot[m],
            points: rows.filter((r) => r.method === m).map((r) => ({ x: f.toTime(r.target_week), y: r.forecast })) })),
        ], y: { format: yFmt, tickFormat: yTick, zero: true } });
        fc.refreshTable();
      }
      drawForecast();

      const mr = metricRows();
      accChart.update({ data: mr.map((r) => ({ key: r.method, label: methodLabel(r.method), value: r.mae_vs_naive, color: r.method === "naive_last_week" ? MUTED : (slot[r.method] || series(2)),
        note: `MAE ${f.num(r.mae, 1)}, MAPE ${f.pct(r.mape)}` })).sort((a, b) => a.value - b.value),
        refValue: { value: 1, label: "naive" }, valueName: "MAE vs naive" });
      acc.refreshTable();
      acc.setFoot(mr.length ? `Main window, ${state.horizon}-week horizon, ${tgt}. Source: reports/forecast_models_metrics.json.` : "No metrics for this selection.");
    }
    draw();
  },
});
