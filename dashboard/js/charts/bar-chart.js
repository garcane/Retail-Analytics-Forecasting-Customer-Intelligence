// Bar chart (SVG), horizontal by default. Bars <= 24px thick, 4px rounded data end and square at the baseline,
// value at the tip, each bar its own hover/focus target (the whole row band, bigger than the mark).
//
// barChart(host, {
//   data: [{key, label, value, color?, note?}],
//   orientation: "horizontal" | "vertical",
//   format(v), tickFormat?(v),
//   color: "var(--series-1)",               // default bar colour
//   domain?: [min, max], zero: true,
//   refValue?: {value, label},             // e.g. the naive forecast (1.0) or the base rate
//   valueLabels: true,
//   rowHeight: 30 (horizontal), height: 260 (vertical),
//   ariaLabel
// }) -> {update(partialOptions)}

import { svg, el, onResize } from "../core/dom.js";
import { linear, niceDomain, band } from "./scales.js";
import { createTooltip } from "./tooltip.js";

const TEXT_W = 6.8;
const MAX_THICK = 24;
const R = 4;

/** Path for a bar from baseline b to value v along the value axis, rounded only at the data end. */
function barPath(horizontal, b, v, c0, thick) {
  const len = Math.abs(v - b);
  const r = Math.min(R, len, thick / 2);
  const dir = v >= b ? 1 : -1;
  if (horizontal) {
    const y0 = c0, y1 = c0 + thick;
    const xe = v;
    return `M${b},${y0}H${xe - dir * r}Q${xe},${y0} ${xe},${y0 + r}V${y1 - r}Q${xe},${y1} ${xe - dir * r},${y1}H${b}Z`;
  }
  const x0 = c0, x1 = c0 + thick;
  const ye = v;
  return `M${x0},${b}V${ye + dir * r}Q${x0},${ye} ${x0 + r},${ye}H${x1 - r}Q${x1},${ye} ${x1},${ye + dir * r}V${b}Z`;
}

export function barChart(host, options) {
  let opts = { orientation: "horizontal", zero: true, valueLabels: true, color: "var(--series-1)", ...options };
  const frame = el("div", { class: "chart" });
  host.append(frame);
  const tooltip = createTooltip(frame);

  function draw(width) {
    for (const child of [...frame.childNodes]) if (child.tagName !== "DIV") child.remove();
    frame.querySelector(".chart-empty")?.remove();
    const data = opts.data.filter((d) => Number.isFinite(d.value));
    if (!data.length) {
      frame.prepend(el("div", { class: "chart-empty", text: "No data for this selection" }));
      return;
    }
    const horizontal = opts.orientation !== "vertical";
    const values = data.map((d) => d.value).concat(opts.refValue ? [opts.refValue.value] : []);
    const nice = niceDomain(values, { zero: opts.zero, count: horizontal ? 4 : 5, min: opts.domain?.[0], max: opts.domain?.[1] });
    const tickFmt = opts.tickFormat || opts.format;
    const valueLabelW = opts.valueLabels ? Math.max(...data.map((d) => opts.format(d.value).length)) * TEXT_W + 10 : 8;

    let root;
    let height;
    if (horizontal) {
      const rowH = opts.rowHeight || 30;
      const labelW = Math.min(Math.max(width * 0.42, 80), Math.max(...data.map((d) => d.label.length)) * TEXT_W + 12);
      const m = { top: 4, right: valueLabelW, bottom: 22, left: labelW };
      height = m.top + m.bottom + rowH * data.length;
      const iw = Math.max(40, width - m.left - m.right);
      const x = linear(nice.domain, [m.left, m.left + iw]);
      const yb = band(data.map((d) => d.key), [m.top, m.top + rowH * data.length], { paddingInner: 0.25, paddingOuter: 0.1 });
      const thick = Math.min(MAX_THICK, yb.bandwidth);
      root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, role: "img", "aria-label": opts.ariaLabel || "Bar chart" });
      for (const t of nice.ticks) {
        const px = Math.round(x(t)) + 0.5;
        root.append(svg("line", { class: t === 0 ? "baseline" : "gridline", x1: px, x2: px, y1: m.top, y2: height - m.bottom }));
        root.append(svg("text", { class: "tick-label", x: px, y: height - 6, "text-anchor": "middle", text: tickFmt(t) }));
      }
      if (opts.refValue) {
        const px = x(opts.refValue.value);
        root.append(svg("line", { class: "ref-line", x1: px, x2: px, y1: m.top, y2: height - m.bottom, "stroke-width": 1.5 }));
      }
      const base = x(Math.max(nice.domain[0], Math.min(0, nice.domain[1])));
      for (const d of data) {
        const c0 = yb(d.key) + (yb.bandwidth - thick) / 2;
        const label = d.label.length * TEXT_W > labelW - 10 ? `${d.label.slice(0, Math.floor((labelW - 18) / TEXT_W))}…` : d.label;
        const g = svg("g", {});
        g.append(svg("text", { class: "cat-label", x: m.left - 8, y: c0 + thick / 2 + 4, "text-anchor": "end", text: label }));
        const bar = svg("path", { class: "bar", d: barPath(true, base, x(d.value), c0, thick), style: `fill:${d.color || opts.color}` });
        g.append(bar);
        if (opts.valueLabels) {
          const vx = x(d.value);
          g.append(svg("text", { class: "value-label", x: d.value >= 0 ? vx + 6 : vx - 6, y: c0 + thick / 2 + 4, "text-anchor": d.value >= 0 ? "start" : "end", text: opts.format(d.value) }));
        }
        const hit = svg("rect", { class: "hit", x: 0, y: yb(d.key) - (yb.step - yb.bandwidth) / 2, width, height: yb.step, tabindex: 0,
          "aria-label": `${d.label}: ${opts.format(d.value)}${d.note ? `, ${d.note}` : ""}` });
        g.append(hit);
        wire(hit, bar, d, () => ({ x: x(d.value), y: c0 }));
        root.append(g);
      }
      if (opts.refValue?.label) {
        root.append(svg("text", { class: "tick-label", x: x(opts.refValue.value) + 4, y: m.top + 10, text: opts.refValue.label }));
      }
    } else {
      height = opts.height || 260;
      const xLabelRows = data.some((d) => d.label.length * TEXT_W > width / data.length - 4) ? 2 : 1;
      const maxTick = Math.max(...nice.ticks.map((t) => tickFmt(t).length));
      const m = { top: opts.valueLabels ? 18 : 8, right: 8, bottom: 20 + (xLabelRows - 1) * 12, left: maxTick * TEXT_W + 14 };
      const iw = Math.max(40, width - m.left - m.right);
      const ih = height - m.top - m.bottom;
      const y = linear(nice.domain, [m.top + ih, m.top]);
      const xb = band(data.map((d) => d.key), [m.left, m.left + iw], { paddingInner: 0.3 });
      const thick = Math.min(MAX_THICK, xb.bandwidth);
      root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, role: "img", "aria-label": opts.ariaLabel || "Column chart" });
      for (const t of nice.ticks) {
        const py = Math.round(y(t)) + 0.5;
        root.append(svg("line", { class: t === 0 ? "baseline" : "gridline", x1: m.left, x2: m.left + iw, y1: py, y2: py }));
        root.append(svg("text", { class: "tick-label", x: m.left - 8, y: py + 4, "text-anchor": "end", text: tickFmt(t) }));
      }
      if (opts.refValue) {
        const py = y(opts.refValue.value);
        root.append(svg("line", { class: "ref-line", x1: m.left, x2: m.left + iw, y1: py, y2: py, "stroke-width": 1.5 }));
        if (opts.refValue.label) root.append(svg("text", { class: "tick-label", x: m.left + iw, y: py - 5, "text-anchor": "end", text: opts.refValue.label }));
      }
      const base = y(Math.max(nice.domain[0], Math.min(0, nice.domain[1])));
      data.forEach((d, i) => {
        const c0 = xb(d.key) + (xb.bandwidth - thick) / 2;
        const g = svg("g", {});
        const bar = svg("path", { class: "bar", d: barPath(false, base, y(d.value), c0, thick), style: `fill:${d.color || opts.color}` });
        g.append(bar);
        if (opts.valueLabels) g.append(svg("text", { class: "value-label", x: c0 + thick / 2, y: y(d.value) - 5, "text-anchor": "middle", text: opts.format(d.value) }));
        const stagger = xLabelRows > 1 && i % 2 === 1 ? 12 : 0;
        g.append(svg("text", { class: "tick-label", x: c0 + thick / 2, y: m.top + ih + 14 + stagger, "text-anchor": "middle", text: d.label }));
        const hit = svg("rect", { class: "hit", x: xb(d.key) - (xb.step - xb.bandwidth) / 2, y: m.top, width: xb.step, height: ih, tabindex: 0,
          "aria-label": `${d.label}: ${opts.format(d.value)}${d.note ? `, ${d.note}` : ""}` });
        g.append(hit);
        wire(hit, bar, d, () => ({ x: c0 + thick / 2, y: y(d.value) }));
        root.append(g);
      });
    }

    function wire(hit, bar, d, anchor) {
      const scale = () => frame.clientWidth / width;
      const rows = [{ value: opts.format(d.value), label: opts.valueName || "" , color: d.color || opts.color }];
      if (d.note) rows.push({ value: "", label: d.note });
      const show = (pos) => {
        bar.classList.add("is-hover");
        tooltip.show(pos.x, pos.y, { title: d.label, rows });
      };
      hit.addEventListener("pointermove", (ev) => {
        const box = frame.getBoundingClientRect();
        show({ x: ev.clientX - box.left, y: ev.clientY - box.top });
      });
      hit.addEventListener("focus", () => { const a = anchor(); show({ x: a.x * scale(), y: a.y * scale() }); });
      const hide = () => { bar.classList.remove("is-hover"); tooltip.hide(); };
      hit.addEventListener("pointerleave", hide);
      hit.addEventListener("blur", hide);
    }

    frame.prepend(root);
  }

  const stop = onResize(frame, draw);
  return {
    update(next) {
      opts = { ...opts, ...next };
      draw(Math.floor(frame.clientWidth));
    },
    destroy: stop,
  };
}
