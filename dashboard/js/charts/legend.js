// Legend: always present for two or more series. With onToggle, each entry is a button that shows/hides its series.

import { el } from "../core/dom.js";

/** items: [{id, label, color, shape: "line"|"rect", active}] */
export function legend(items, { onToggle } = {}) {
  const root = el("div", { class: "legend", role: onToggle ? "group" : "list", "aria-label": "Legend" });
  for (const item of items) {
    const key = el("span", { class: `legend-key ${item.shape || "line"}`, style: { background: item.color }, "aria-hidden": "true" });
    if (onToggle) {
      const button = el("button", { type: "button", class: "legend-item", "aria-pressed": String(item.active !== false) }, key, item.label);
      button.addEventListener("click", () => {
        const active = button.getAttribute("aria-pressed") !== "true";
        button.setAttribute("aria-pressed", String(active));
        onToggle(item.id, active);
      });
      root.append(button);
    } else {
      root.append(el("span", { class: "legend-item", role: "listitem" }, key, item.label));
    }
  }
  return root;
}
