// Late-delivery model: every model and feature set from the rolling-origin backtest (six monthly out-of-time tests,
// 2018-03 to 2018-08), compared on a chosen metric, plus calibration, explainability, recalibration and training-window
// experiments. Models are discovered from the data: a new model key in late_delivery_metrics.json appears here.

import { registerPage } from "../core/registry.js";
import { el } from "../core/dom.js";
import * as f from "../core/format.js";
import { series, MUTED } from "../core/theme.js";
import { modelInfo, METRICS, FEATURE_SETS, humanize } from "../core/labels.js";
import { card, grid } from "../components/card.js";
import { controlsRow, select, segmented } from "../components/controls.js";
import { barChart } from "../charts/bar-chart.js";
import { lineChart } from "../charts/line-chart.js";
import { heatmap } from "../charts/heatmap.js";
import { legend } from "../charts/legend.js";

const FAMILY_COLOR = { "Logistic regression": series(1), "Gradient boosting": series(2), Baseline: MUTED };
const fmt3 = (v) => f.num(v, 3);

registerPage({
  id: "models",
  title: "Late-delivery model",
  order: 40,
  description: "Which orders will arrive late? Each model is trained only on orders delivered before the test month starts, then scored on that month (2018-03 to 2018-08). Metrics are means of the six months.",
  needs: ["models"],
  render(root, { models }) {
    const ld = models.late_delivery;
    const keys = Object.keys(ld.macro_average);
    const info = Object.fromEntries(keys.map((k) => [k, modelInfo(k)]));
    // A fixed colour slot per non-baseline model, by its position in the data: colour follows the model, not its rank.
    const slot = {};
    keys.filter((k) => !info[k].baseline).forEach((k, i) => { slot[k] = series(i + 1); });
    const colorOf = (k) => slot[k] || MUTED;
    const months = [...new Set(Object.values(ld.per_month).flat().map((r) => r.month))].sort();
    const baseRate = ld.macro_average.constant_train_rate?.base_rate ?? Object.values(ld.macro_average)[0]?.base_rate;

    const state = { metric: "pr_auc", family: "all", selected: new Set(keys.filter((k) => /_v1$/.test(k) || k === "constant_train_rate" || k === "logistic_regression_v2")) };
    const availableMetrics = Object.keys(METRICS).filter((m) => keys.some((k) => Number.isFinite(ld.macro_average[k][m])));
    const families = [...new Set(keys.map((k) => info[k].family))];

    controlsRow(root, [
      select({ label: "Metric", value: state.metric, options: availableMetrics.map((m) => ({ value: m, label: METRICS[m].label })), onChange: (v) => { state.metric = v; draw(); } }),
      segmented({ label: "Model family", value: state.family, options: [{ value: "all", label: "All" }, ...families.map((x) => ({ value: x, label: x }))], onChange: (v) => { state.family = v; draw(); } }),
    ]);
    const metricNote = el("p", { class: "secondary" });
    root.append(metricNote);

    const g = grid(root);
    const visibleKeys = () => keys.filter((k) => state.family === "all" || info[k].family === state.family || info[k].baseline);
    const refFor = (metric) => ({
      pr_auc: { value: baseRate, label: "no skill (base rate)" }, precision_at_top: { value: baseRate, label: "no skill (base rate)" },
      roc_auc: { value: 0.5, label: "chance" }, recall_at_top: { value: 0.1, label: "random 10%" },
      brier: { value: ld.macro_average.constant_train_rate?.brier, label: "constant baseline" },
    }[metric]);

    // 1. Comparison of all models (macro average)
    const cmp = card(g, { title: "Model comparison", span: 6,
      table: () => ({ columns: [
        { key: "label", label: "Model" }, { key: "featureSet", label: "Features" },
        ...availableMetrics.map((m) => ({ key: m, label: METRICS[m].label, num: true, format: fmt3 })),
      ], rows: keys.map((k) => ({ label: info[k].label, featureSet: info[k].featureSet || "-", ...ld.macro_average[k] })), caption: "Macro average over the six test months" }) });
    cmp.body.append(legend(families.map((x) => ({ id: x, label: x, color: FAMILY_COLOR[x] || MUTED, shape: "rect" }))));
    const cmpChart = barChart(cmp.body, { data: [], format: fmt3, rowHeight: 26, ariaLabel: "Model comparison" });

    // 2. Per-month heatmap
    const hm = card(g, { title: "Stability across test months", span: 6,
      table: () => ({ columns: [{ key: "label", label: "Model" }, ...months.map((m) => ({ key: m, label: m, num: true, format: fmt3 }))],
        rows: visibleKeys().map((k) => ({ label: info[k].label, ...Object.fromEntries((ld.per_month[k] || []).map((r) => [r.month, r[state.metric]])) })), caption: "Metric per test month" }) });
    const lookup = Object.fromEntries(keys.map((k) => [k, Object.fromEntries((ld.per_month[k] || []).map((r) => [r.month, r]))]));
    const hmChart = heatmap(hm.body, { rows: [], cols: months.map((m) => ({ key: m, label: f.monthShort(m) })), value: () => null, format: fmt3 });

    // 3. Per-month lines for chosen models (legend toggles)
    const pm = card(g, { title: "Month by month", subtitle: "Select models in the legend", span: 12 });
    const legendHost = el("div");
    pm.body.append(legendHost);
    const pmChart = lineChart(pm.body, { series: [], x: { type: "time", format: f.month, tickFormat: f.monthShort }, y: { format: fmt3 }, height: 280, ariaLabel: "Metric by test month" });

    function draw() {
      const m = state.metric;
      const meta = METRICS[m];
      metricNote.textContent = `${meta.label}: ${meta.description}.`;
      const vk = visibleKeys();
      const data = vk.map((k) => ({ key: k, label: info[k].label, value: ld.macro_average[k][m], color: FAMILY_COLOR[info[k].family] || MUTED,
        note: info[k].featureSet ? FEATURE_SETS[info[k].featureSet] || info[k].featureSet : "baseline" }))
        .sort((a, b) => (meta.higherIsBetter ? b.value - a.value : a.value - b.value));
      const ref = refFor(m);
      cmpChart.update({ data, refValue: ref && Number.isFinite(ref.value) ? ref : undefined, valueName: meta.label, ariaLabel: `Models ranked by ${meta.label}` });
      cmp.setFoot(`Ranked by ${meta.label}${meta.higherIsBetter ? " (higher is better)" : " (lower is better)"}. The vertical line is the ${ref?.label || "reference"}.`);
      hmChart.update({ rows: vk.map((k) => ({ key: k, label: info[k].label })), value: (k, mo) => lookup[k][mo]?.[m], higherIsBetter: meta.higherIsBetter, valueName: meta.label, ariaLabel: `${meta.label} by model and month` });
      // Name the hardest month from the data (the month most models score worst in on this metric).
      const worst = {};
      for (const k of vk.filter((x) => !info[x].baseline)) {
        const rows = (ld.per_month[k] || []).filter((r) => Number.isFinite(r[m]));
        if (!rows.length) continue;
        const w = rows.reduce((a, b) => ((meta.higherIsBetter ? b[m] < a[m] : b[m] > a[m]) ? b : a));
        worst[w.month] = (worst[w.month] || 0) + 1;
      }
      const [hardest, count] = Object.entries(worst).sort((a, b) => b[1] - a[1])[0] || [];
      const nModels = Object.values(worst).reduce((s, x) => s + x, 0);
      hm.setFoot(`Darker = better ${meta.label}.${hardest ? ` ${f.month(hardest)} is the worst month for ${count} of ${nModels} models on this metric.` : ""}`);
      hm.refreshTable();
      cmp.refreshTable();

      legendHost.replaceChildren(legend(vk.map((k) => ({ id: k, label: info[k].label, color: colorOf(k), active: state.selected.has(k) })), {
        onToggle: (id, on) => { if (on) state.selected.add(id); else state.selected.delete(id); drawLines(); },
      }));
      drawLines();
    }
    function drawLines() {
      const m = state.metric;
      const vk = visibleKeys().filter((k) => state.selected.has(k));
      pmChart.update({ series: vk.map((k) => ({ id: k, label: info[k].label, color: colorOf(k), markers: true,
        points: (ld.per_month[k] || []).map((r) => ({ x: f.toTime(r.month), y: r[m] })) })), y: { format: fmt3 } });
    }

    // 4. Calibration (feature sets of the logistic model)
    const cal = ld.calibration?.logistic_regression || [];
    if (cal.length) {
      const sets = [...new Set(cal.map((r) => r.features))];
      const cc = card(g, { title: "Calibration: predicted vs observed late rate", subtitle: "Logistic regression, by score quintile, mean of test months", span: 6,
        foot: "Points on the diagonal are well calibrated. Richer feature sets push the top quintile's prediction up without the observed rate following: more confident, not more right.",
        table: () => ({ columns: [{ key: "features", label: "Feature set" }, { key: "bucket", label: "Quintile (4 = riskiest)", num: true },
          { key: "predicted", label: "Predicted", num: true, format: fmt3 }, { key: "actual", label: "Observed", num: true, format: fmt3 }], rows: cal }) });
      const calColor = (s) => colorOf(`logistic_regression_${s}`);
      cc.body.append(legend(sets.map((s) => ({ id: s, label: `Features ${s}`, color: calColor(s) }))));
      const maxV = Math.max(...cal.flatMap((r) => [r.predicted, r.actual]));
      const top = Math.ceil(maxV * 20) / 20;
      lineChart(cc.body, {
        series: sets.map((s) => ({ id: s, label: `Features ${s}`, color: calColor(s), markers: true,
          points: cal.filter((r) => r.features === s).sort((a, b) => a.bucket - b.bucket).map((r) => ({ x: r.predicted, y: r.actual })) })),
        x: { type: "linear", format: (v) => `predicted ${f.pct(v)}`, tickFormat: (v) => f.pct(v, 0), domain: [0, top], label: "Mean predicted late rate" },
        y: { format: (v) => `observed ${f.pct(v)}`, tickFormat: (v) => f.pct(v, 0), domain: [0, top] },
        refLines: [{ x1: 0, y1: 0, x2: top, y2: top, label: "perfect calibration" }], endLabels: false, height: 300,
        ariaLabel: "Calibration of the logistic regression by feature set",
      });
    }

    // 5. Explainability
    const ex = models.explainability;
    if (ex?.permutation_pr_auc_drop) {
      const groups = Object.keys(ex.permutation_pr_auc_drop);
      const exMonths = Object.keys(ex.permutation_pr_auc_drop[groups[0]]).filter((k) => k !== "mean");
      const ec = card(g, { title: "What drives the v1 model", subtitle: "Drop in PR-AUC when a feature group is shuffled (permutation importance)", span: 6,
        foot: `Mean over test months and ${ex.repeats ?? "several"} shuffles. A negative value means the model did better without that group in that month.`,
        table: () => ({ columns: [{ key: "group", label: "Feature group" }, ...exMonths.map((mo) => ({ key: mo, label: mo, num: true, format: (v) => f.num(v, 4) })), { key: "mean", label: "Mean", num: true, format: (v) => f.num(v, 4) }],
          rows: groups.map((gk) => ({ group: gk, ...ex.permutation_pr_auc_drop[gk] })) }) });
      barChart(ec.body, {
        data: groups.map((gk) => ({ key: gk, label: gk, value: ex.permutation_pr_auc_drop[gk].mean })).sort((a, b) => b.value - a.value),
        format: (v) => f.num(v, 3), color: series(1), valueName: "Mean PR-AUC drop", ariaLabel: "Permutation importance by feature group",
      });
      heatmap(ec.body, { rows: groups.map((gk) => ({ key: gk, label: gk })), cols: exMonths.map((mo) => ({ key: mo, label: f.monthShort(mo) })),
        value: (gk, mo) => ex.permutation_pr_auc_drop[gk][mo], format: (v) => f.num(v, 2), valueName: "PR-AUC drop", cellHeight: 26, ariaLabel: "Permutation importance by month" });
    }

    // 6. Recalibration variants
    const rc = models.recalibration?.macro;
    if (rc) {
      const rows = Object.entries(rc).map(([variant, v]) => ({ variant, ...v }));
      const bestRc = rows.reduce((a, b) => (b.brier < a.brier ? b : a));
      const rcCard = card(g, { title: "Recalibration and training window", subtitle: "Brier score by variant (lower is better), macro over test months", span: 6,
        foot: `Lowest Brier: ${bestRc.variant} (${f.num(bestRc.brier, 4)}). The model is used by rank, not as a probability (DD-11).`,
        table: () => ({ columns: [{ key: "variant", label: "Variant" }, ...["brier", "log_loss", "pr_auc", "ece", "mean_pred_minus_actual"].map((k) => ({ key: k, label: humanize(k), num: true, format: (v) => f.num(v, 4) }))], rows }) });
      barChart(rcCard.body, {
        data: rows.map((r) => ({ key: r.variant, label: r.variant, value: r.brier, note: `ECE ${f.num(r.ece, 3)}, PR-AUC ${f.num(r.pr_auc, 3)}`, color: r.variant.startsWith("reference") ? series(1) : MUTED }))
          .sort((a, b) => a.value - b.value),
        format: (v) => f.num(v, 4), tickFormat: (v) => f.num(v, 3), zero: false, rowHeight: 24, valueName: "Brier score", ariaLabel: "Brier score by recalibration variant",
      });
    }

    // 7. Training window x feature set (drift experiments)
    const win = models.drift?.windows;
    if (win && Object.keys(win).length) {
      const parsed = Object.entries(win).map(([k, v]) => { const [fs, w] = k.split(" | window="); return { fs: fs.trim(), w: w.trim(), ...v }; });
      const fsList = [...new Set(parsed.map((p) => p.fs))];
      const wList = [...new Set(parsed.map((p) => p.w))];
      const bestAt = wList.map((w) => {
        const cands = parsed.filter((p) => p.w === w && Number.isFinite(p.pr_auc));
        const b = cands.reduce((a, c) => (c.pr_auc > a.pr_auc ? c : a));
        return `${w === "all" ? "all history" : w}: ${b.fs}`;
      });
      const wc = card(g, { title: "Training window vs feature set", subtitle: "PR-AUC, macro over test months", span: 6,
        foot: `Best feature set per window: ${bestAt.join("; ")}. Details: docs/ml/DRIFT_ANALYSIS.md.`,
        table: () => ({ columns: [{ key: "fs", label: "Feature set" }, { key: "w", label: "Window" }, ...["pr_auc", "roc_auc", "brier"].map((k) => ({ key: k, label: METRICS[k].label, num: true, format: fmt3 }))], rows: parsed }) });
      heatmap(wc.body, { rows: fsList.map((x) => ({ key: x, label: x })), cols: wList.map((w) => ({ key: w, label: w === "all" ? "all history" : w })),
        value: (fs, w) => parsed.find((p) => p.fs === fs && p.w === w)?.pr_auc, format: fmt3, valueName: "PR-AUC", ariaLabel: "PR-AUC by feature set and training window" });
    }

    // Feature-set glossary
    const used = [...new Set(keys.map((k) => info[k].featureSet).filter(Boolean))];
    const gl = card(g, { title: "Feature sets", span: 12 });
    gl.body.append(el("dl", { class: "facts" }, used.flatMap((s) => [el("dt", { text: s }), el("dd", { text: FEATURE_SETS[s] || "(no description)" })])));

    draw();
  },
});
