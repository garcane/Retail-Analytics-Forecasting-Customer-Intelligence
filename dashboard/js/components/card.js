// Card: the container a panel renders into. With `table`, the card gets a "Table" toggle that swaps the chart for an
// accessible table of the same numbers (the table view every chart must have).
//
// const c = card(grid, {title, subtitle, span: 6, foot, table: () => ({columns, rows, caption})});
// c.body  -> element to draw the chart into
// c.setFoot(text), c.refreshTable()

import { el } from "../core/dom.js";
import { dataTable } from "./data-table.js";

export function card(parent, { title, subtitle, span = 12, foot, table, actions = [] } = {}) {
  const body = el("div", { class: "card-body" });
  const tableHost = el("div", { class: "card-body", hidden: true });
  const footEl = el("p", { class: "card-foot", text: foot || "" });
  if (!foot) footEl.hidden = true;
  const actionsEl = el("div", { class: "card-actions" });
  const titleId = `card-${Math.random().toString(36).slice(2, 9)}`;

  const root = el("section", { class: `card span-${span}`, "aria-labelledby": titleId },
    el("div", { class: "card-head" },
      el("div", { class: "titles" }, el("h3", { id: titleId, text: title }), subtitle ? el("p", { class: "subtitle", text: subtitle }) : null),
      actionsEl),
    body, tableHost, footEl);

  for (const a of actions) actionsEl.append(a);

  let showingTable = false;
  const renderTable = () => {
    tableHost.replaceChildren();
    const spec = table();
    dataTable(tableHost, spec);
  };
  if (table) {
    const toggle = el("button", { type: "button", class: "icon-button", "aria-pressed": "false", text: "Table" });
    toggle.addEventListener("click", () => {
      showingTable = !showingTable;
      toggle.setAttribute("aria-pressed", String(showingTable));
      toggle.textContent = showingTable ? "Chart" : "Table";
      if (showingTable) renderTable();
      body.hidden = showingTable;
      tableHost.hidden = !showingTable;
    });
    actionsEl.append(toggle);
  }

  parent.append(root);
  return {
    root,
    body,
    setFoot(text) {
      footEl.textContent = text || "";
      footEl.hidden = !text;
    },
    refreshTable() {
      if (showingTable) renderTable();
    },
  };
}

/** A 12-column grid for cards. */
export function grid(parent) {
  const g = el("div", { class: "grid" });
  parent.append(g);
  return g;
}
