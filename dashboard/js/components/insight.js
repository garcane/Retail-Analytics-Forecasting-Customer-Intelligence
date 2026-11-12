// Insight cards: eyebrow (kind), the evidence figure, the finding in words, its source, and a circular "satellite"
// link to the page that shows the evidence.
// insightGrid(parent, [{kind, figure, text, source, page, pageTitle}])

import { el } from "../core/dom.js";

export function insightGrid(parent, insights) {
  const grid = el("div", { class: "insights" });
  for (const i of insights) {
    grid.append(el("article", { class: "insight" },
      el("span", { class: "eyebrow", text: i.kind }),
      el("span", { class: "insight-figure", text: i.figure }),
      el("p", { class: "insight-text", text: i.text }),
      i.source ? el("span", { class: "card-foot", text: `Source: ${i.source}` }) : null,
      i.page ? el("a", { class: "satellite", href: `#/${i.page}`, "aria-label": `Open ${i.pageTitle || i.page}`, title: `Open ${i.pageTitle || i.page}` },
        el("span", { "aria-hidden": "true", text: "→" })) : null));
  }
  parent.append(grid);
  return grid;
}
