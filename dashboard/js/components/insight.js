// Insight cards: the finding in words, the evidence figure, its source, and a link to the page that shows it.
// insightGrid(parent, [{kind, figure, text, source, page, pageTitle}])

import { el } from "../core/dom.js";

export function insightGrid(parent, insights) {
  const grid = el("div", { class: "insights" });
  for (const i of insights) {
    grid.append(el("article", { class: "insight" },
      el("span", { class: "insight-kind", text: i.kind }),
      el("span", { class: "insight-figure", text: i.figure }),
      el("p", { class: "insight-text", text: i.text }),
      i.source ? el("span", { class: "card-foot", text: `Source: ${i.source}` }) : null,
      i.page ? el("a", { class: "insight-link", href: `#/${i.page}`, text: `Open ${i.pageTitle || i.page} →` }) : null));
  }
  parent.append(grid);
  return grid;
}
