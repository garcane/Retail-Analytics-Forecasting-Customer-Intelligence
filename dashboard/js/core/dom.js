// DOM helpers. All text goes in through textContent / createTextNode, never innerHTML: labels come from data files.

const SVG_NS = "http://www.w3.org/2000/svg";

function apply(node, attrs) {
  for (const [key, value] of Object.entries(attrs || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (key === "class") node.setAttribute("class", value);
    else if (key === "text") node.textContent = String(value);
    else if (key === "style" && typeof value === "object") Object.assign(node.style, value);
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2).toLowerCase(), value);
    else node.setAttribute(key, value === true ? "" : String(value));
  }
  return node;
}

function append(node, children) {
  for (const child of children.flat(Infinity)) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

/** el("div", {class: "card"}, "text", childNode, [more]) */
export function el(tag, attrs = {}, ...children) {
  return append(apply(document.createElement(tag), attrs), children);
}

/** SVG element; attribute names are used as given (viewBox, stroke-width, ...). */
export function svg(tag, attrs = {}, ...children) {
  return append(apply(document.createElementNS(SVG_NS, tag), attrs), children);
}

export function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
  return node;
}

// Every live chart registers its teardown here; the shell disposes them all before rendering the next page, so
// observers and theme listeners never outlive their (detached) DOM.
const live = new Set();

/** Tear down every chart created since the last call (called by main.js on navigation). */
export function disposeCharts() {
  for (const stop of [...live]) stop();
  live.clear();
}

/**
 * Re-run `draw(width)` whenever the host's width changes, and on theme change.
 * Returns {redraw, stop}. redraw() forces a draw now, or, if the host is hidden (width 0, e.g. a card showing its
 * table), as soon as it becomes visible again: the remembered width is reset either way, so a chart updated while
 * hidden is never left blank.
 */
export function onResize(host, draw) {
  let last = -1;
  const run = () => {
    const width = Math.floor(host.clientWidth);
    if (width > 0 && width !== last) {
      last = width;
      draw(width);
    }
  };
  const ro = new ResizeObserver(run);
  ro.observe(host);
  const redraw = () => { last = -1; run(); };
  window.addEventListener("themechange", redraw);
  // "layoutchange": something was shown or resized outside a ResizeObserver frame (e.g. a card switching back
  // from its table). Re-measure now; run() reads clientWidth synchronously, so this does not wait for a frame.
  window.addEventListener("layoutchange", run);
  requestAnimationFrame(run);
  const stop = () => {
    ro.disconnect();
    window.removeEventListener("themechange", redraw);
    window.removeEventListener("layoutchange", run);
    live.delete(stop);
  };
  live.add(stop);
  return { redraw, stop };
}

/** Resolved value of a CSS custom property, e.g. cssVar("--seq-400"). */
export function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

let uid = 0;
export const nextId = (prefix = "id") => `${prefix}-${++uid}`;
