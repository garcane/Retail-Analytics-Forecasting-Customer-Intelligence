// Filter controls: standard form elements styled to the chart chrome. They live in ONE row above the content they
// scope (controlsRow), never inside a chart card.

import { el } from "../core/dom.js";

let n = 0;

/** Single choice as a segmented button group. options: [{value, label}] */
export function segmented({ label, options, value, onChange }) {
  const id = `seg-${++n}`;
  const group = el("div", { class: "segmented", role: "group", "aria-labelledby": id });
  const buttons = options.map((o) => {
    const b = el("button", { type: "button", "aria-pressed": String(o.value === value), text: o.label });
    b.addEventListener("click", () => {
      if (b.getAttribute("aria-pressed") === "true") return;
      buttons.forEach((x) => x.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      onChange(o.value);
    });
    group.append(b);
    return b;
  });
  return el("div", { class: "control" }, el("span", { class: "control-label", id, text: label }), group);
}

/** Single choice as a <select>, for longer option lists. */
export function select({ label, options, value, onChange }) {
  const id = `sel-${++n}`;
  const s = el("select", { class: "select", id });
  for (const o of options) s.append(el("option", { value: o.value, text: o.label, selected: o.value === value }));
  s.addEventListener("change", () => onChange(s.value));
  return el("div", { class: "control" }, el("label", { class: "control-label", for: id, text: label }), s);
}

export function controlsRow(parent, controls) {
  const row = el("div", { class: "controls-row", role: "toolbar", "aria-label": "Filters for this page" }, controls);
  parent.append(row);
  return row;
}
