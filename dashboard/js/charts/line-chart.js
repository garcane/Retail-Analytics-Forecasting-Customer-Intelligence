// Multi-series line chart (SVG). 2px lines, recessive hairline grid, one y-axis, crosshair that snaps to the nearest
// x and lists every series in one tooltip. Keyboard: focus the plot, arrow keys step through x positions.
//
// lineChart(host, {
//   series: [{id, label, color, points: [{x, y}], markers?: bool, width?: number}],
//   x: {type: "time"|"linear", format(v), tickFormat?(v), domain?: [a, b], label?},
//   y: {format(v), tickFormat?(v), zero?: bool, domain?: [a, b], label?},
//   height: 260,
//   refLines: [{x1, y1, x2, y2, label}],       // in data units, e.g. a diagonal or a target line
//   spans: [{x0, x1, label}],                  // shaded x ranges (e.g. a period excluded from scoring)
//   endLabels: true,                           // direct labels at line ends when <= 4 series and they do not collide
//   ariaLabel: "..."
// }) -> {update(partialOptions)}

import { svg, el, onResize } from "../core/dom.js";
import { linear, niceDomain, niceTicks, timeTicks } from "./scales.js";
import { createTooltip } from "./tooltip.js";

const TEXT_W = 6.6; // approx px per character of 11px tick text, for margins

export function lineChart(host, options) {
  let opts = options;
  const frame = el("div", { class: "chart" });
  host.append(frame);
  const tooltip = createTooltip(frame);

  function draw(width) {
    for (const child of [...frame.childNodes]) if (child.tagName !== "DIV") child.remove();
    const series = opts.series.filter((s) => s.points && s.points.length);
    const height = opts.height || 260;
    if (!series.length) {
      frame.prepend(el("div", { class: "chart-empty", text: "No data for this selection" }));
      return;
    }
    frame.querySelector(".chart-empty")?.remove();

    const xs = series.flatMap((s) => s.points.map((p) => p.x));
    const ys = series.flatMap((s) => s.points.map((p) => p.y)).concat((opts.refLines || []).flatMap((r) => [r.y1, r.y2]));
    const yNice = niceDomain(ys.filter(Number.isFinite), { zero: !!opts.y.zero, count: height < 220 ? 4 : 5,
      min: opts.y.domain?.[0], max: opts.y.domain?.[1] });
    const yTickFmt = opts.y.tickFormat || opts.y.format;
    const leftMargin = Math.max(36, Math.max(...yNice.ticks.map((t) => String(yTickFmt(t)).length)) * TEXT_W + 14);
    const endLabelsWanted = opts.endLabels !== false && series.length <= 4;
    const endLabelWidth = endLabelsWanted ? Math.min(140, Math.max(...series.map((s) => s.label.length)) * TEXT_W + 12) : 0;
    const m = { top: 12, right: Math.max(12, endLabelWidth), bottom: opts.x.label ? 42 : 28, left: leftMargin };
    const iw = Math.max(40, width - m.left - m.right);
    const ih = height - m.top - m.bottom;

    const xDomain = opts.x.domain || [Math.min(...xs), Math.max(...xs)];
    const x = linear(xDomain, [m.left, m.left + iw]);
    const y = linear(yNice.domain, [m.top + ih, m.top]);

    const root = svg("svg", { viewBox: `0 0 ${width} ${height}`, width, height, role: "img", "aria-label": opts.ariaLabel || "Line chart" });

    // shaded spans
    for (const s of opts.spans || []) {
      const x0 = Math.max(m.left, x(s.x0));
      const x1 = Math.min(m.left + iw, x(s.x1));
      if (x1 > x0) {
        root.append(svg("rect", { class: "band-shade", x: x0, y: m.top, width: x1 - x0, height: ih }));
        if (s.label) root.append(svg("text", { class: "tick-label", x: x0 + 4, y: m.top + 12, text: s.label }));
      }
    }

    // y grid + ticks
    for (const t of yNice.ticks) {
      const py = Math.round(y(t)) + 0.5;
      root.append(svg("line", { class: t === 0 ? "baseline" : "gridline", x1: m.left, x2: m.left + iw, y1: py, y2: py }));
      root.append(svg("text", { class: "tick-label", x: m.left - 8, y: py + 4, "text-anchor": "end", text: yTickFmt(t) }));
    }
    if (yNice.ticks[0] !== 0) root.append(svg("line", { class: "baseline", x1: m.left, x2: m.left + iw, y1: m.top + ih + 0.5, y2: m.top + ih + 0.5 }));

    // x ticks
    const maxTicks = Math.max(2, Math.floor(iw / 70));
    const xTicks = opts.x.type === "time" ? timeTicks(xDomain[0], xDomain[1], maxTicks) : niceTicks(xDomain[0], xDomain[1], Math.min(maxTicks, 6)).filter((t) => t >= xDomain[0] && t <= xDomain[1]);
    const xTickFmt = opts.x.tickFormat || opts.x.format;
    for (const t of xTicks) {
      const px = x(t);
      root.append(svg("line", { class: "baseline", x1: px, x2: px, y1: m.top + ih, y2: m.top + ih + 4 }));
      root.append(svg("text", { class: "tick-label", x: px, y: m.top + ih + 17, "text-anchor": "middle", text: xTickFmt(t) }));
    }
    if (opts.x.label) root.append(svg("text", { class: "axis-title", x: m.left + iw / 2, y: height - 6, "text-anchor": "middle", text: opts.x.label }));
    if (opts.y.label) root.append(svg("text", { class: "axis-title", x: m.left, y: m.top - 2, text: opts.y.label }));

    // reference lines
    for (const r of opts.refLines || []) {
      root.append(svg("line", { class: "ref-line", x1: x(r.x1), y1: y(r.y1), x2: x(r.x2), y2: y(r.y2) }));
      if (r.label) root.append(svg("text", { class: "tick-label", x: x(r.x2) - 4, y: y(r.y2) - 6, "text-anchor": "end", text: r.label }));
    }

    // lines
    for (const s of series) {
      const pts = s.points.filter((p) => Number.isFinite(p.y));
      let d = "";
      let pen = false;
      for (const p of s.points) {
        if (!Number.isFinite(p.y)) { pen = false; continue; }
        d += `${pen ? "L" : "M"}${x(p.x).toFixed(1)},${y(p.y).toFixed(1)}`;
        pen = true;
      }
      root.append(svg("path", { class: "series-line", d, style: `stroke:${s.color}`, "stroke-width": s.width || 2 }));
      if (s.markers || pts.length === 1) {
        for (const p of pts) root.append(svg("circle", { class: "marker", cx: x(p.x), cy: y(p.y), r: 4, style: `fill:${s.color}` }));
      }
    }

    // direct end labels, only when they do not collide
    if (endLabelsWanted) {
      const ends = series.map((s) => {
        const last = [...s.points].reverse().find((p) => Number.isFinite(p.y));
        return last ? { s, px: x(last.x), py: y(last.y) } : null;
      }).filter(Boolean).sort((a, b) => a.py - b.py);
      const collide = ends.some((e, i) => i > 0 && e.py - ends[i - 1].py < 13);
      if (!collide) {
        for (const e of ends) root.append(svg("text", { class: "end-label", x: e.px + 6, y: e.py + 4, text: e.s.label }));
      }
    }

    // interaction layer: crosshair snaps to the nearest x present in the data
    const allX = [...new Set(xs)].sort((a, b) => a - b);
    const lookup = series.map((s) => new Map(s.points.map((p) => [p.x, p.y])));
    const cross = svg("line", { class: "crosshair", y1: m.top, y2: m.top + ih, visibility: "hidden" });
    const dots = series.map((s) => svg("circle", { class: "marker", r: 4, style: `fill:${s.color}`, visibility: "hidden" }));
    const overlay = svg("rect", { class: "hit", x: m.left, y: m.top, width: iw, height: ih, tabindex: 0,
      "aria-label": `${opts.ariaLabel || "Chart"}. Use left and right arrow keys to read values.` });
    root.append(cross, ...dots, overlay);

    let index = -1;
    const showAt = (i, clientPos) => {
      index = Math.max(0, Math.min(allX.length - 1, i));
      const xv = allX[index];
      const px = x(xv);
      cross.setAttribute("x1", px);
      cross.setAttribute("x2", px);
      cross.setAttribute("visibility", "visible");
      const rows = [];
      series.forEach((s, k) => {
        const yv = lookup[k].get(xv);
        if (Number.isFinite(yv)) {
          dots[k].setAttribute("cx", px);
          dots[k].setAttribute("cy", y(yv));
          dots[k].setAttribute("visibility", "visible");
          rows.push({ value: opts.y.format(yv), label: s.label, color: s.color, sort: yv });
        } else dots[k].setAttribute("visibility", "hidden");
      });
      rows.sort((a, b) => b.sort - a.sort);
      const scale = frame.clientWidth / width;
      const pos = clientPos || { x: px * scale, y: m.top * scale + 20 };
      tooltip.show(pos.x, pos.y, { title: opts.x.format(xv), rows });
    };
    const hide = () => {
      cross.setAttribute("visibility", "hidden");
      dots.forEach((d) => d.setAttribute("visibility", "hidden"));
      tooltip.hide();
    };
    const nearest = (px) => {
      const xv = x.invert(px);
      let best = 0;
      for (let i = 1; i < allX.length; i++) if (Math.abs(allX[i] - xv) < Math.abs(allX[best] - xv)) best = i;
      return best;
    };
    overlay.addEventListener("pointermove", (ev) => {
      const box = frame.getBoundingClientRect();
      const scale = width / box.width;
      showAt(nearest((ev.clientX - box.left) * scale), { x: ev.clientX - box.left, y: ev.clientY - box.top });
    });
    overlay.addEventListener("pointerleave", hide);
    overlay.addEventListener("blur", hide);
    overlay.addEventListener("focus", () => showAt(index < 0 ? allX.length - 1 : index));
    overlay.addEventListener("keydown", (ev) => {
      const step = { ArrowRight: 1, ArrowLeft: -1, End: allX.length, Home: -allX.length }[ev.key];
      if (step !== undefined) {
        ev.preventDefault();
        showAt((index < 0 ? allX.length - 1 : index) + step);
      } else if (ev.key === "Escape") hide();
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

