// Sortable data table. columns: [{key, label, format?(v, row), num?: bool}], rows: [{...}].
// Click (or Enter/Space on) a header to sort; aria-sort reflects the state and focus stays on the header.
// initialSort {key, dir} restores a previous sort; onSort({key, dir}) reports changes (card.js keeps it across
// filter changes so the reader's chosen order is not reset).

import { el } from "../core/dom.js";

export function dataTable(host, { columns, rows, caption, maxHeight = true, initialSort, onSort }) {
  const valid = initialSort && columns.some((c) => c.key === initialSort.key);
  let sortKey = valid ? initialSort.key : null;
  let dir = valid ? initialSort.dir : 1;
  const table = el("table", { class: "data" });
  const wrap = el("div", { class: `table-wrap${maxHeight ? " table-scroll" : ""}`, tabindex: 0, role: "region", "aria-label": caption || "Data table" }, table);
  host.append(wrap);

  const render = (focusKey) => {
    table.replaceChildren();
    if (caption) table.append(el("caption", { text: caption }));
    const head = el("tr");
    let toFocus = null;
    for (const c of columns) {
      const sorted = sortKey === c.key;
      const button = el("button", { type: "button", text: c.label + (sorted ? (dir > 0 ? " ▲" : " ▼") : "") });
      button.addEventListener("click", () => {
        dir = sortKey === c.key ? -dir : (c.num ? -1 : 1);
        sortKey = c.key;
        onSort?.({ key: sortKey, dir });
        render(c.key);
      });
      if (c.key === focusKey) toFocus = button;
      head.append(el("th", { scope: "col", class: c.num ? "num" : "", "aria-sort": sorted ? (dir > 0 ? "ascending" : "descending") : "none" }, button));
    }
    table.append(el("thead", {}, head));
    const body = el("tbody");
    const data = rows.slice();
    if (sortKey) {
      data.sort((a, b) => {
        const x = a[sortKey], y = b[sortKey];
        if (x === y) return 0;
        if (x === null || x === undefined) return 1;
        if (y === null || y === undefined) return -1;
        return (typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })) * dir;
      });
    }
    for (const r of data) {
      const tr = el("tr");
      for (const c of columns) {
        const v = r[c.key];
        tr.append(el("td", { class: c.num ? "num" : "", text: c.format ? c.format(v, r) : (v ?? "–") }));
      }
      body.append(tr);
    }
    table.append(body);
    toFocus?.focus(); // the header that was just activated is rebuilt; keep keyboard focus on it
  };
  render();
  return { rerender: () => render() };
}
