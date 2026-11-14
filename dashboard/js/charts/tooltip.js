// One tooltip per chart. Values lead (strong), names follow; rows are keyed with a short line in the series colour.

import { el, clear } from "../core/dom.js";

export function createTooltip(host) {
  const tip = el("div", { class: "tooltip", role: "status", "aria-live": "polite" });
  host.append(tip);
  return {
    /** x, y: pointer position relative to host. rows: [{value, label, color}] */
    show(x, y, { title, rows = [] }) {
      clear(tip);
      if (title) tip.append(el("div", { class: "tooltip-title", text: title }));
      for (const row of rows) {
        tip.append(
          el("div", { class: "tooltip-row" },
            row.color ? el("span", { class: "tooltip-key", style: { background: row.color } }) : null,
            el("strong", { text: row.value }),
            el("span", { text: row.label })),
        );
      }
      tip.classList.add("is-visible");
      const hostWidth = host.clientWidth;
      const w = tip.offsetWidth;
      const h = tip.offsetHeight;
      let left = x + 14;
      if (left + w > hostWidth) left = Math.max(0, x - w - 14);
      const top = Math.max(0, y - h - 10);
      tip.style.left = `${left}px`;
      tip.style.top = `${top}px`;
    },
    hide() {
      tip.classList.remove("is-visible");
    },
  };
}
