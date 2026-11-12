// Heatmap (SVG): rows x columns, one sequential hue (light -> dark = low -> high, or reversed when lower is better).
// Each cell is a hover/focus target; the value is printed in the cell when it fits, in white or near-black chosen by
// the cell colour's luminance, so it reads in both themes.
//
// heatmap(host, {
//   rows: [{key, label}], cols: [{key, label}],
//   value(rowKey, colKey) -> number|null,
//   format(v), higherIsBetter: true, domain?: [min, max],
//   cellHeight: 30, ariaLabel, valueName
// })

import { svg, el, onResize, cssVar } from "../core/dom.js";
import { createTooltip } from "./tooltip.js";

const STEPS = ["--seq-100", "--seq-200", "--seq-300", "--seq-400", "--seq-500", "--seq-600", "--seq-700"];
const TEXT_W = 6.6;

function luminance(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex.trim());
  if (!m) return 0.5;
  const n = parseInt(m[1], 16);
  const lin = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4; };
  return 0.2126 * lin((n >> 16) & 255) + 0.7152 * lin((n >> 8) & 255) + 0.0722 * lin(n & 255);
}

export function heatmap(host, options) {
  let opts = { higherIsBetter: true, cellHeight: 30, ...options };
  const frame = el("div", { class: "chart" });
  host.append(frame);
  const tooltip = createTooltip(frame);

  function draw(width) {
    for (const child of [...frame.childNodes]) if (child.tagName !== "DIV") child.remove();
    const { rows, cols } = opts;
    const vals = rows.flatMap((r) => cols.map((c) => opts.value(r.key, c.key))).filter(Number.isFinite);
    if (!vals.length) {
      frame.prepend(el("div", { class: "chart-empty", text: "No data for this selection" }));
      return;
    }
    frame.querySelector(".chart-empty")?.remove();
    const [lo, hi] = opts.domain || [Math.min(...vals), Math.max(...vals)];
    const colors = STEPS.map((s) => cssVar(s) || "#888888");
    const labelW = Math.min(width * 0.4, Math.max(...rows.map((r) => r.label.length)) * TEXT_W + 12);
    const m = { top: 22, right: 4, bottom: 4, left: labelW };
    const cw = (width - m.left - m.right) / cols.length;
    const ch = opts.cellHeight;
    const height = m.top + m.bottom + ch * rows.length;
    const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, role: "img", "aria-label": opts.ariaLabel || "Heatmap" });

    cols.forEach((c, j) => {
      const label = c.label.length * TEXT_W > cw ? c.label.slice(0, Math.max(1, Math.floor(cw / TEXT_W) - 1)) + "…" : c.label;
      root.append(svg("text", { class: "tick-label", x: m.left + cw * j + cw / 2, y: 14, "text-anchor": "middle", text: label }));
    });
    rows.forEach((r, i) => {
      root.append(svg("text", { class: "cat-label", x: m.left - 8, y: m.top + ch * i + ch / 2 + 4, "text-anchor": "end", text: r.label }));
      cols.forEach((c, j) => {
        const v = opts.value(r.key, c.key);
        const x0 = m.left + cw * j;
        const y0 = m.top + ch * i;
        if (!Number.isFinite(v)) {
          root.append(svg("rect", { class: "heat-cell", x: x0, y: y0, width: cw, height: ch, style: "fill:var(--surface-2)" }));
          return;
        }
        let t = hi === lo ? 0.5 : (v - lo) / (hi - lo);
        if (!opts.higherIsBetter) t = 1 - t;
        const step = Math.max(0, Math.min(STEPS.length - 1, Math.round(t * (STEPS.length - 1))));
        const fill = colors[step];
        const rect = svg("rect", { class: "heat-cell", x: x0, y: y0, width: cw, height: ch, rx: 3, style: `fill:${fill}`, tabindex: 0,
          "aria-label": `${r.label}, ${c.label}: ${opts.format(v)}` });
        root.append(rect);
        const text = opts.format(v);
        if (text.length * TEXT_W + 6 < cw) {
          root.append(svg("text", { class: "heat-label", x: x0 + cw / 2, y: y0 + ch / 2 + 4, "text-anchor": "middle",
            style: `fill:${luminance(fill) > 0.35 ? "#0b0b0b" : "#ffffff"}`, text }));
        }
        const show = (pos) => {
          rect.classList.add("is-hover");
          tooltip.show(pos.x, pos.y, { title: `${r.label} · ${c.label}`, rows: [{ value: text, label: opts.valueName || "" }] });
        };
        rect.addEventListener("pointermove", (ev) => {
          const box = frame.getBoundingClientRect();
          show({ x: ev.clientX - box.left, y: ev.clientY - box.top });
        });
        rect.addEventListener("focus", () => { const s = frame.clientWidth / width; show({ x: (x0 + cw / 2) * s, y: y0 * s }); });
        const hide = () => { rect.classList.remove("is-hover"); tooltip.hide(); };
        rect.addEventListener("pointerleave", hide);
        rect.addEventListener("blur", hide);
      });
    });
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
