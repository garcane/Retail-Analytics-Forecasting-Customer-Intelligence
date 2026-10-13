"""Build the dashboard mock-up (docs/powerbi/DASHBOARD_MOCKUP.html) from model_spec.py and the warehouse.

A single self-contained, interactive HTML page that looks like the Power BI report described by the specification:
the same four pages, the same visuals at the same positions, real numbers. The measures are re-implemented in
JavaScript over small pre-aggregated cubes (see mockup_data.py), so this is a mock-up of the dashboard, not a DAX engine.

    uv run python src/powerbi/build_mockup_html.py
"""

from __future__ import annotations

import json
import sys

import mockup_data
import model_spec as ms

OUT = ms.ROOT / "docs" / "powerbi" / "DASHBOARD_MOCKUP.html"

HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dashboard mock-up - Retail Analytics</title>
<style>
:root{--bg:#edece8;--ink:#0b0b0b;--ink2:#52514e;--line:#dcdad3;--card:#ffffff;--accent:#2a78d6}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:13px/1.4 "Segoe UI",system-ui,-apple-system,sans-serif}
header{background:#fff;border-bottom:1px solid var(--line);padding:8px 16px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
header h1{font-size:15px;margin:0;font-weight:600}.badge{background:#fff3d6;border:1px solid #eda100;color:#6b4b00;border-radius:10px;padding:1px 9px;font-size:12px}
nav{display:flex;gap:2px;flex-wrap:wrap;margin-left:auto}nav button{border:1px solid var(--line);background:#f7f6f3;color:var(--ink2);padding:6px 14px;cursor:pointer;font:inherit;border-radius:4px 4px 0 0}
nav button.on{background:#fff;color:var(--ink);border-bottom-color:#fff;font-weight:600;box-shadow:inset 0 3px 0 var(--accent)}
#wrap{padding:12px;overflow:hidden}#stage{position:relative;width:1280px;height:720px;transform-origin:0 0;background:var(--bg)}
.v{position:absolute;background:var(--card);border:1px solid var(--line);border-radius:4px;padding:6px 8px;overflow:hidden}
.v .t{font-size:11.5px;font-weight:600;color:var(--ink2);margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.v svg{display:block}.card .val{font-size:30px;font-weight:600;line-height:1.15;margin-top:6px}.card .sub{font-size:11px;color:var(--ink2)}
.slicer{padding:3px 8px!important}.slicer .t{margin-bottom:1px}.slicer select,.slicer input{font:inherit;padding:0 3px;border:1px solid #c9c7bf;border-radius:3px;background:#fff;max-width:100%}.slicer .row{display:flex;gap:6px;align-items:center}
.chip{display:inline-block;white-space:nowrap;border:1px solid #c9c7bf;border-radius:10px;padding:0 5px;margin:0 2px 0 0;cursor:pointer;font-size:10.5px;background:#fff;user-select:none}.chip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.scroll{overflow-y:auto;height:calc(100% - 20px)}table{border-collapse:collapse;width:100%;font-size:11.5px}th,td{padding:2px 6px;text-align:left;border-bottom:1px solid #eceae4}th{color:var(--ink2);font-weight:600;position:sticky;top:0;background:#fff}td.n{text-align:right;font-variant-numeric:tabular-nums}
.note{max-width:1280px;margin:0 auto;padding:0 12px 24px;color:var(--ink2);font-size:12px}.note b{color:var(--ink)}
text{font-family:"Segoe UI",system-ui,sans-serif}
</style></head><body>
<header><h1>Retail Analytics &middot; Olist</h1><span class="badge">MOCK-UP: generated from the specification, not Power BI</span><nav id="tabs"></nav></header>
<div id="wrap"><div id="stage"></div></div>
<div class="note" id="note"></div>
<script>
const D = __DATA__;
const SPEC = __SPEC__;
const PW = __PW__, PH = __PH__;
const C = {blue:'#2a78d6', orange:'#eb6834', grey:'#b9b8b1', ink:'#0b0b0b', ink2:'#52514e', grid:'#e4e3de', violet:'#6250d6', aqua:'#1baf7a', magenta:'#e87ba4', yellow:'#eda100'};
const METHOD_SHORT = {actual:'actual', naive_last_week:'naive', moving_average_8:'8-wk avg', simple_exp_smoothing:'smoothing', damped_trend:'damped', ar1_trend_26w:'AR(1)', combo_naive_ma8:'combo'};
const METHOD_NAME = {actual:'actual', naive_last_week:'naive', moving_average_8:'8-week average', simple_exp_smoothing:'exp. smoothing', damped_trend:'damped trend', ar1_trend_26w:'AR(1) + trend', combo_naive_ma8:'combination'};
const METHOD_COLOUR = {actual:C.ink, naive_last_week:C.grey, moving_average_8:C.blue, simple_exp_smoothing:C.violet, damped_trend:C.aqua, ar1_trend_26w:C.magenta, combo_naive_ma8:C.orange};
const BUCKETS = ['on time or early','1-3 days late','4-7 days late','8-14 days late','more than 14 days late'];
const S = {
  page: Math.min(Math.max(+((location.hash.match(/p=(\d)/) || [0, 0])[1]), 0), SPEC.length - 1),
  p1: {m0: 0, m1: D.months.length - 1, cat: 'All', st: 'All'},
  p2: {m0: 0, m1: D.months.length - 1, st: 'All'},
  p3: {month: 'All', share: 10, st: 'All'},
  p4: {target: 0, h: 1, methods: new Set(['actual', 'naive_last_week', 'combo_naive_ma8'])},
};

// ---------- formatting
const nf = (x, d = 0) => (x == null || isNaN(x)) ? '–' : x.toLocaleString('en-US', {minimumFractionDigits: d, maximumFractionDigits: d});
const pc = (x, d = 1) => (x == null || isNaN(x)) ? '–' : (100 * x).toFixed(d) + '%';
const sum = (a, f) => a.reduce((t, r) => t + f(r), 0);
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
function niceMax(v) { if (!(v > 0)) return 1; const p = Math.pow(10, Math.floor(Math.log10(v))), f = v / p; return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 2.5 ? 2.5 : f <= 5 ? 5 : 10) * p; }
function axisFmt(v) { const a = Math.abs(v); return a >= 1e6 ? (v / 1e6).toFixed(1).replace(/\.0$/, '') + 'M' : a >= 1e3 ? (v / 1e3).toFixed(1).replace(/\.0$/, '') + 'K' : (Number.isInteger(v) ? String(v) : v.toFixed(2).replace(/0+$/, '').replace(/\.$/, '')); }

// ---------- chart helpers (inline SVG)
function frame(w, h, ymax, yfmt, pad) {
  let s = '';
  for (let i = 0; i <= 4; i++) { const y = pad.t + (h - pad.t - pad.b) * (1 - i / 4); s += `<line x1="${pad.l}" x2="${w - pad.r}" y1="${y}" y2="${y}" stroke="${C.grid}"/><text x="${pad.l - 4}" y="${y + 3}" text-anchor="end" font-size="9" fill="${C.ink2}">${yfmt(ymax * i / 4)}</text>`; }
  return s;
}
function colChart(w, h, items, o = {}) {
  const pad = {l: 40, r: 6, t: 6, b: 26}, ymax = niceMax(Math.max(0, ...items.map(i => i.value || 0))), n = items.length, bw = (w - pad.l - pad.r) / Math.max(n, 1);
  let s = `<svg width="${w}" height="${h}">` + frame(w, h, ymax, o.yfmt || axisFmt, pad);
  items.forEach((it, i) => {
    const bh = ((it.value || 0) / ymax) * (h - pad.t - pad.b), x = pad.l + i * bw + bw * 0.14;
    s += `<rect x="${x}" y="${h - pad.b - bh}" width="${bw * 0.72}" height="${bh}" fill="${it.color || o.color || C.blue}"><title>${esc(it.label)}: ${esc(it.tip)}</title></rect>`;
    if (n <= 12 || i % Math.ceil(n / 10) === 0) s += `<text x="${x + bw * 0.36}" y="${h - pad.b + 12}" text-anchor="middle" font-size="9" fill="${C.ink2}">${esc(it.short || it.label)}</text>`;
  });
  return s + '</svg>';
}
function hbarChart(w, h, items, o = {}) {
  const pad = {l: o.lw || 118, r: 52, t: 2, b: 2}, rowH = 17, ymax = Math.max(1e-9, ...items.map(i => i.value || 0));
  let s = `<svg width="${w}" height="${Math.max(h, items.length * rowH + 4)}">`;
  items.forEach((it, i) => {
    const y = pad.t + i * rowH, bw = ((it.value || 0) / ymax) * (w - pad.l - pad.r);
    s += `<text x="${pad.l - 5}" y="${y + 11}" text-anchor="end" font-size="10" fill="${C.ink2}">${esc(it.label.length > 22 ? it.label.slice(0, 21) + '…' : it.label)}</text>`;
    s += `<rect x="${pad.l}" y="${y + 2}" width="${Math.max(bw, 0)}" height="12" fill="${it.color || o.color || C.blue}"><title>${esc(it.label)}: ${esc(it.tip)}</title></rect>`;
    if (it.value2 != null) { const b2 = (it.value2 / ymax) * (w - pad.l - pad.r); s += `<rect x="${pad.l}" y="${y + 14}" width="${Math.max(b2, 0)}" height="4" fill="${C.grey}"/>`; }
    s += `<text x="${pad.l + bw + 4}" y="${y + 11}" font-size="10" fill="${C.ink}">${esc(it.text)}</text>`;
  });
  return s + '</svg>';
}
function lineChart(w, h, labels, series, o = {}) {
  const pad = {l: 44, r: 8, t: 8, b: series.length > 1 ? 36 : 24}, vals = series.flatMap(s => s.values.filter(v => v != null)), ymax = o.ymax || niceMax(Math.max(0, ...vals)), n = labels.length;
  const X = i => pad.l + (n <= 1 ? 0 : i / (n - 1)) * (w - pad.l - pad.r), Y = v => pad.t + (1 - v / ymax) * (h - pad.t - pad.b);
  let s = `<svg width="${w}" height="${h}">` + frame(w, h, ymax, o.yfmt || axisFmt, pad);
  labels.forEach((l, i) => { if (n <= 8 || i % Math.ceil(n / 7) === 0) s += `<text x="${X(i)}" y="${h - pad.b + 12}" text-anchor="middle" font-size="9" fill="${C.ink2}">${esc(l)}</text>`; });
  series.forEach(se => {
    let d = '', open = false;
    se.values.forEach((v, i) => { if (v == null) { open = false; return; } d += (open ? 'L' : 'M') + X(i).toFixed(1) + ' ' + Y(v).toFixed(1); open = true; });
    s += `<path d="${d}" fill="none" stroke="${se.color}" stroke-width="${se.width || 2}"/>`;
    se.values.forEach((v, i) => { if (v != null && n <= 60) s += `<circle cx="${X(i)}" cy="${Y(v)}" r="2.4" fill="${se.color}"><title>${esc(se.name)} ${esc(labels[i])}: ${esc((o.tipfmt || nf)(v))}</title></circle>`; });
  });
  if (series.length > 1) series.forEach((se, i) => { s += `<rect x="${pad.l + 6 + i * 110}" y="${h - 9}" width="9" height="3" fill="${se.color}"/><text x="${pad.l + 18 + i * 110}" y="${h - 5}" font-size="9" fill="${C.ink2}">${esc(se.name)}</text>`; });
  return s + '</svg>';
}
const tableHtml = (cols, rows) => `<div class="scroll"><table><tr>${cols.map(c => `<th${c.n ? ' style="text-align:right"' : ''}>${esc(c.h)}</th>`).join('')}</tr>${rows.map(r => `<tr>${r.map((x, i) => `<td class="${cols[i].n ? 'n' : ''}">${esc(x)}</td>`).join('')}</tr>`).join('')}</table></div>`;
const median = h => { const n = h.reduce((a, b) => a + b, 0); if (!n) return null; let c = 0; for (let k = 0; k < h.length; k++) { if (c + h[k] >= n / 2) return k + (n / 2 - c) / h[k]; c += h[k]; } return null; };

// ---------- data access (filters per page)
const inM = (P, mi) => mi >= P.m0 && mi <= P.m1, inS = (P, si) => P.st === 'All' || D.states[si] === P.st;
function salesRows(P) {
  if (P.cat === 'All') return D.sales.filter(r => inM(P, r[0]) && inS(P, r[1])).map(r => ({mi: r[0], si: r[1], orders: r[2], revenue: r[3], freight: r[4], items: r[5], customers: r[6]}));
  const ci = D.cats.indexOf(P.cat);
  return D.cube.filter(r => inM(P, r[0]) && r[1] === ci && inS(P, r[2])).map(r => ({mi: r[0], ci: r[1], si: r[2], orders: r[3], items: r[4], revenue: r[5], freight: r[6], customers: r[9]}));
}
const group = (rows, key) => { const m = new Map(); rows.forEach(r => { const k = r[key]; (m.get(k) || m.set(k, []).get(k)).push(r); }); return m; };
const money = x => nf(x, 2);
function slicerMonths(P, el) {
  const opt = (i) => D.months.map((m, j) => `<option value="${j}"${j === i ? ' selected' : ''}>${m}</option>`).join('');
  el.innerHTML = `<div class="t">Month</div><div class="row">from <select data-k="m0">${opt(P.m0)}</select> to <select data-k="m1">${opt(P.m1)}</select></div>`;
  el.querySelectorAll('select').forEach(s => s.onchange = () => { P[s.dataset.k] = +s.value; if (P.m0 > P.m1) { if (s.dataset.k === 'm0') P.m1 = P.m0; else P.m0 = P.m1; } render(); });
}
function slicerSelect(title, options, value, onchange, el) {
  el.innerHTML = `<div class="t">${esc(title)}</div><select>${options.map(o => `<option${o === String(value) ? ' selected' : ''}>${esc(o)}</option>`).join('')}</select>`;
  el.querySelector('select').onchange = e => { onchange(e.target.value); render(); };
}

// ---------- visuals, by id (ids come from the specification)
const V = {
  s_month: (v, el) => slicerMonths(S.p1, el), s_cat: (v, el) => slicerSelect('Category', ['All', ...D.cats], S.p1.cat, x => S.p1.cat = x, el), s_state: (v, el) => slicerSelect('Customer state', ['All', ...D.states], S.p1.st, x => S.p1.st = x, el),
  c_rev: (v, el) => card(el, v, money(sum(salesRows(S.p1), r => r.revenue)), 'Net Revenue'),
  c_ord: (v, el) => card(el, v, nf(sum(salesRows(S.p1), r => r.orders)), 'Net Orders' + (S.p1.cat !== 'All' ? ' (orders containing the category)' : '')),
  c_aov: (v, el) => { const r = salesRows(S.p1); card(el, v, money(sum(r, x => x.revenue) / sum(r, x => x.orders)), 'Average Order Value'); },
  c_frt: (v, el) => { const r = salesRows(S.p1); card(el, v, pc(sum(r, x => x.freight) / sum(r, x => x.revenue)), 'Freight % of Revenue'); },
  c_cus: (v, el) => { const full = S.p1.m0 === 0 && S.p1.m1 === D.months.length - 1 && S.p1.st === 'All' && S.p1.cat === 'All'; card(el, v, nf(full ? D.customers_total : sum(salesRows(S.p1), r => r.customers)), full ? 'Buying Customers (exact)' : 'Buying Customers (approx.)'); },
  v_rev_month: (v, el) => { const g = group(salesRows(S.p1), 'mi'); const items = [...g.keys()].sort((a, b) => a - b).map(mi => { const t = sum(g.get(mi), r => r.revenue); return {label: D.months[mi], short: D.months[mi].slice(2), value: t, tip: 'R$ ' + money(t)}; }); body(el, v, colChart(v.w - 18, v.h - 30, items)); },
  v_aov_month: (v, el) => { const g = group(salesRows(S.p1), 'mi'); const ks = [...g.keys()].sort((a, b) => a - b); body(el, v, lineChart(v.w - 18, v.h - 30, ks.map(k => D.months[k].slice(2)), [{name: 'Average Order Value', color: C.blue, values: ks.map(k => sum(g.get(k), r => r.revenue) / sum(g.get(k), r => r.orders))}], {tipfmt: x => 'R$ ' + nf(x, 2)})); },
  v_rev_cat: (v, el) => { const ci = D.cats.indexOf(S.p1.cat); const rows = D.cube.filter(r => inM(S.p1, r[0]) && inS(S.p1, r[2]) && (S.p1.cat === 'All' || r[1] === ci)); const g = group(rows, 1); const items = [...g.entries()].map(([c, rs]) => ({label: D.cats[c], value: sum(rs, r => r[5])})).sort((a, b) => b.value - a.value).slice(0, 40).map(i => ({...i, text: nf(i.value / 1000, 0) + 'K', tip: 'R$ ' + money(i.value)})); el.innerHTML = `<div class="t">${esc(v.title)}</div><div class="scroll">${hbarChart(v.w - 28, v.h - 30, items)}</div>`; },
  v_rev_state: (v, el) => { const g = group(salesRows(S.p1), 'si'); const items = [...g.entries()].map(([s, rs]) => ({label: D.states[s], value: sum(rs, r => r.revenue)})).sort((a, b) => b.value - a.value).map(i => ({...i, lw: 40, text: nf(i.value / 1000, 0) + 'K', tip: 'R$ ' + money(i.value)})); el.innerHTML = `<div class="t">${esc(v.title)}</div><div class="scroll">${hbarChart(v.w - 28, v.h - 30, items, {lw: 36})}</div>`; },
  d_month: (v, el) => slicerMonths(S.p2, el), d_state: (v, el) => slicerSelect('Customer state', ['All', ...D.states], S.p2.st, x => S.p2.st = x, el),
  d_c_late: (v, el) => { const r = dl(); card(el, v, pc(sum(r, x => x[3]) / sum(r, x => x[2])), 'Late Rate %'); },
  d_c_med: (v, el) => { const r = dl(); const h = Array(61).fill(0); r.forEach(x => x[6].forEach((c, i) => h[i] += c)); const m = median(h); card(el, v, m == null ? '–' : nf(m, 1), 'Median Delivery Days (1-day resolution here)'); },
  d_c_rev: (v, el) => { const r = rv(); card(el, v, nf(sum(r, x => x[4]) / sum(r, x => x[3]), 2), 'Average Review Score'); },
  d_c_short: (v, el) => { const r = dl(); card(el, v, pc(sum(r, x => x[5]) / sum(r, x => x[2])), 'Share Promised Under 20 Days'); },
  d_late_month: (v, el) => { const g = group(dl(), 0); const ks = [...g.keys()].sort((a, b) => a - b); body(el, v, lineChart(v.w - 18, v.h - 30, ks.map(k => D.months[k].slice(2)), [{name: 'Late Rate %', color: C.orange, values: ks.map(k => sum(g.get(k), r => r[3]) / sum(g.get(k), r => r[2]))}], {yfmt: x => pc(x, 0), tipfmt: x => pc(x)})); },
  d_short_month: (v, el) => { const g = group(dl(), 0); const ks = [...g.keys()].sort((a, b) => a - b); body(el, v, lineChart(v.w - 18, v.h - 30, ks.map(k => D.months[k].slice(2)), [{name: 'Share Promised Under 20 Days', color: C.blue, values: ks.map(k => sum(g.get(k), r => r[5]) / sum(g.get(k), r => r[2]))}], {ymax: 1, yfmt: x => pc(x, 0), tipfmt: x => pc(x)})); },
  d_review_bucket: (v, el) => { const g = group(rv(), 2); const items = [1, 2, 3, 4, 5].map(b => { const rs = g.get(b) || []; const n = sum(rs, r => r[3]); const a = n ? sum(rs, r => r[4]) / n : null; return {label: BUCKETS[b - 1], short: ['on time', '1-3 d', '4-7 d', '8-14 d', '14+ d'][b - 1], value: a, color: b === 1 ? C.blue : C.orange, tip: nf(a, 2) + ' stars, ' + nf(n) + ' orders'}; }); body(el, v, colChart(v.w - 18, v.h - 30, items, {yfmt: x => x.toFixed(1)})); },
  d_state_table: (v, el) => { const g = group(dl(true), 1); const rows = [...g.entries()].map(([s, rs]) => { const h = Array(61).fill(0); rs.forEach(x => x[6].forEach((c, i) => h[i] += c)); const n = sum(rs, x => x[2]); return {s: D.states[s], n, late: sum(rs, x => x[3]) / n, med: median(h)}; }).sort((a, b) => b.n - a.n); el.innerHTML = `<div class="t">${esc(v.title)}</div>` + tableHtml([{h: 'dim_geography[state]'}, {h: 'Delivered Orders', n: 1}, {h: 'Late Rate %', n: 1}, {h: 'Median Delivery Days', n: 1}], rows.map(r => [r.s, nf(r.n), pc(r.late), nf(r.med, 1)])); },
  r_month: (v, el) => slicerSelect('Month', ['All', ...D.months.filter((m, i) => D.risk.some(r => r[0] === i))], S.p3.month, x => S.p3.month = x, el),
  r_flag: (v, el) => slicerSelect('Flag the riskiest X% of orders', D.shares.map(String), S.p3.share, x => S.p3.share = +x, el),
  r_state: (v, el) => slicerSelect('Customer state', ['All', ...D.states.filter((s, i) => D.risk.some(r => r[1] === i))], S.p3.st, x => S.p3.st = x, el),
  r_c_n: (v, el) => card(el, v, nf(sum(rk(), r => r[2])), 'Scored Orders'),
  r_c_base: (v, el) => { const r = rk(); card(el, v, pc(sum(r, x => x[3]) / sum(r, x => x[2])), 'Late Rate (scored)'); },
  r_c_flag: (v, el) => { const r = rk(), j = D.shares.indexOf(S.p3.share); card(el, v, pc(sum(r, x => x[4][2 * j + 1]) / sum(r, x => x[4][2 * j])), 'Late Rate Among Flagged'); },
  r_c_lift: (v, el) => { const r = rk(), j = D.shares.indexOf(S.p3.share); const l = (sum(r, x => x[4][2 * j + 1]) / sum(r, x => x[4][2 * j])) / (sum(r, x => x[3]) / sum(r, x => x[2])); card(el, v, isNaN(l) ? '–' : nf(l, 2) + 'x', 'Lift (pooled over the selection)'); },
  r_c_rec: (v, el) => { const r = rk(), j = D.shares.indexOf(S.p3.share); card(el, v, pc(sum(r, x => x[4][2 * j + 1]) / sum(r, x => x[3])), 'Recall'); },
  r_lift_month: (v, el) => { const j = D.shares.indexOf(S.p3.share); const g = group(rk(), 0); const items = [...g.keys()].sort((a, b) => a - b).map(mi => { const r = g.get(mi); const l = (sum(r, x => x[4][2 * j + 1]) / sum(r, x => x[4][2 * j])) / (sum(r, x => x[3]) / sum(r, x => x[2])); return {label: D.months[mi], short: D.months[mi].slice(2), value: l, tip: nf(l, 2) + 'x'}; }); body(el, v, colChart(v.w - 18, v.h - 30, items, {yfmt: x => x + 'x'})); },
  r_state_bar: (v, el) => { const j = D.shares.indexOf(S.p3.share); const g = group(rk(), 1); const items = [...g.entries()].filter(([s, rs]) => sum(rs, x => x[2]) >= 100).map(([s, rs]) => ({label: D.states[s], value: sum(rs, x => x[4][2 * j + 1]) / Math.max(1, sum(rs, x => x[4][2 * j])), value2: sum(rs, x => x[3]) / sum(rs, x => x[2])})).sort((a, b) => b.value - a.value).slice(0, 14).map(i => ({...i, lw: 40, text: pc(i.value), tip: 'flagged ' + pc(i.value) + ', all orders ' + pc(i.value2), color: C.orange})); el.innerHTML = `<div class="t">${esc(v.title)} (grey: all orders)</div><div class="scroll">${hbarChart(v.w - 28, v.h - 30, items, {lw: 62})}</div>`; },
  r_table: (v, el) => { const rows = []; D.risk.forEach(r => { if (!rkMatch(r)) return; (D.top[r[0] + '|' + r[1]] || []).forEach(t => rows.push([D.months[r[0]], D.states[r[1]], ...t])); }); rows.sort((a, b) => b[3] - a[3]); el.innerHTML = `<div class="t">${esc(v.title)}: top 12 of the selection in this mock-up</div>` + tableHtml([{h: 'month'}, {h: 'customer_state'}, {h: 'order_id'}, {h: 'risk_score', n: 1}, {h: 'category'}, {h: 'is_late', n: 1}], rows.slice(0, 12).map(r => [r[0], r[1], r[2], nf(r[3], 3), r[4], r[5]])); },
  f_target: (v, el) => slicerSelect('Target', ['orders', 'revenue'], ['orders', 'revenue'][S.p4.target], x => S.p4.target = x === 'orders' ? 0 : 1, el),
  f_horizon: (v, el) => slicerSelect('Weeks ahead', ['1', '4'], S.p4.h, x => S.p4.h = +x, el),
  f_method: (v, el) => { el.innerHTML = `<div class="t">${esc(v.title)}</div><div>` + D.methods.map(m => `<span class="chip${S.p4.methods.has(m) ? ' on' : ''}" data-m="${m}" title="${METHOD_NAME[m]}">${METHOD_SHORT[m]}</span>`).join('') + '</div>'; el.querySelectorAll('.chip').forEach(c => c.onclick = () => { const m = c.dataset.m; S.p4.methods.has(m) ? S.p4.methods.delete(m) : S.p4.methods.add(m); render(); }); },
  f_c_mae: (v, el) => { const f = fc(); const e = f.filter(r => r.m !== 0 && S.p4.methods.has(D.methods[r.m])).map(r => Math.abs(r.f - r.a)); card(el, v, e.length ? nf(sum(e, x => x) / e.length) : '–', 'MAE (selected methods)'); },
  f_c_rel: (v, el) => { const f = fc(); const e = f.filter(r => r.m !== 0 && S.p4.methods.has(D.methods[r.m])).map(r => Math.abs(r.f - r.a)), n = f.filter(r => r.m === 1).map(r => Math.abs(r.f - r.a)); const x = (sum(e, y => y) / e.length) / (sum(n, y => y) / n.length); card(el, v, isNaN(x) ? '–' : nf(x, 2) + 'x', 'MAE vs Naive (below 1 beats naive)'); },
  f_line: (v, el) => { const f = fc(); const wk = [...new Set(f.map(r => r.w))].sort((a, b) => a - b); const series = D.methods.filter(m => S.p4.methods.has(m)).map(m => ({name: METHOD_NAME[m], color: METHOD_COLOUR[m], width: m === 'actual' ? 3 : 1.8, values: wk.map(w => { const r = f.find(x => x.w === w && D.methods[x.m] === m); return r ? r.f : null; })})); body(el, v, lineChart(v.w - 18, v.h - 30, wk.map(w => D.weeks[w].slice(2)), series, {})); },
  f_mae_bar: (v, el) => { const f = fc(); const items = D.methods.slice(1).filter(m => S.p4.methods.has(m)).map(m => { const e = f.filter(r => D.methods[r.m] === m).map(r => Math.abs(r.f - r.a)); const mae = sum(e, x => x) / e.length; return {label: METHOD_NAME[m], value: mae, text: nf(mae), tip: nf(mae), color: METHOD_COLOUR[m], lw: 100}; }).sort((a, b) => a.value - b.value); el.innerHTML = `<div class="t">${esc(v.title)}</div><div class="scroll">${hbarChart(v.w - 28, v.h - 30, items, {lw: 100})}</div>`; },
  f_table: (v, el) => { const f = fc(); const nav = f.filter(r => r.m === 1).map(r => Math.abs(r.f - r.a)); const nae = sum(nav, x => x) / nav.length; const rows = D.methods.slice(1).filter(m => S.p4.methods.has(m)).map(m => { const e = f.filter(r => D.methods[r.m] === m).map(r => Math.abs(r.f - r.a)); const mae = sum(e, x => x) / e.length; return [METHOD_NAME[m], mae, mae / nae]; }).sort((a, b) => a[1] - b[1]); el.innerHTML = `<div class="t">${esc(v.title)}</div>` + tableHtml([{h: 'method'}, {h: 'MAE', n: 1}, {h: 'MAE vs Naive', n: 1}], rows.map(r => [r[0], nf(r[1]), nf(r[2], 2) + 'x'])); },
};
function card(el, v, value, sub) { el.classList.add('card'); el.innerHTML = `<div class="t">${esc(v.title)}</div><div class="val">${value}</div><div class="sub">${esc(sub)}</div>`; }
function body(el, v, svg) { el.innerHTML = `<div class="t">${esc(v.title)}</div>${svg}`; }
const dl = (allStates) => D.delivery.filter(r => inM(S.p2, r[0]) && (allStates || inS(S.p2, r[1])));
const rv = () => D.reviews.filter(r => inM(S.p2, r[0]) && inS(S.p2, r[1]));
const rkMatch = r => (S.p3.month === 'All' || D.months[r[0]] === S.p3.month) && (S.p3.st === 'All' || D.states[r[1]] === S.p3.st);
const rk = () => D.risk.filter(rkMatch);
const fc = () => D.forecast.filter(r => r[0] === S.p4.target && r[1] === S.p4.h).map(r => ({m: r[2], w: r[3], f: r[4], a: r[5]}));

function render() {
  const page = SPEC[S.page], stage = document.getElementById('stage');
  stage.innerHTML = '';
  page.visuals.forEach(v => {
    const el = document.createElement('div');
    el.className = 'v' + (v.type === 'slicer' ? ' slicer' : '');
    Object.assign(el.style, {left: v.x + 'px', top: v.y + 'px', width: v.w + 'px', height: v.h + 'px'});
    stage.appendChild(el);
    V[v.id](v, el);
  });
  document.querySelectorAll('#tabs button').forEach((b, i) => b.classList.toggle('on', i === S.page));
}
function fit() { const w = Math.min(window.innerWidth - 24, 1400), s = w / PW; const st = document.getElementById('stage'); st.style.transform = `scale(${s})`; document.getElementById('wrap').style.height = (PH * s + 24) + 'px'; }
document.getElementById('tabs').innerHTML = SPEC.map((p, i) => `<button data-i="${i}">${esc(p.title)}</button>`).join('');
document.querySelectorAll('#tabs button').forEach(b => b.onclick = () => { S.page = +b.dataset.i; render(); });
document.getElementById('note').innerHTML = '<b>About this mock-up.</b> Generated from <code>src/powerbi/model_spec.py</code> with real numbers from the warehouse; the measures are re-implemented in JavaScript, so it shows what the Power BI report is meant to look like, not a DAX engine. ' +
  'Slicers here are single-choice or ranges (Power BI offers multi-select). Three figures are approximate: buying customers whenever the selection is not the full range (a repeat customer counts once per month), the median delivery time (1-day resolution) and the riskiest-orders list (top 10 per month and state). ' +
  'With the default selections (everything selected) every card equals the specification\'s first-open checklist.';
window.addEventListener('resize', fit); fit(); render();
</script></body></html>
"""


def render() -> str:
    pages = [{"id": p.id, "title": p.title, "visuals": [{"id": v.id, "type": v.type, "title": v.title, "x": v.x, "y": v.y, "w": v.w, "h": v.h} for v in p.visuals]} for p in ms.PAGES]
    data = json.dumps(mockup_data.build(), separators=(",", ":"))
    return (HTML.replace("__DATA__", data).replace("__SPEC__", json.dumps(pages, separators=(",", ":")))
            .replace("__PW__", str(ms.PAGE_W)).replace("__PH__", str(ms.PAGE_H)))


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    text = render()
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ms.ROOT)} ({len(text) // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
