// Stat tiles. At most one `hero` per view (the single number the view leads with).
// kpiRow(parent, [{label, value, note, hero}])

import { el } from "../core/dom.js";

export function kpiRow(parent, items) {
  const row = el("div", { class: "kpi-row" });
  for (const item of items) {
    row.append(el("div", { class: `kpi${item.hero ? " hero" : ""}` },
      el("span", { class: "kpi-label", text: item.label }),
      el("span", { class: "kpi-value", text: item.value }),
      item.note ? el("span", { class: "kpi-note", text: item.note }) : null));
  }
  parent.append(row);
  return row;
}
