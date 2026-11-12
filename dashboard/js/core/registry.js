// Extension points. A page or an insight rule registers itself; the shell and the overview discover them here.
//
// Page contract:
//   registerPage({
//     id: "models",              // URL hash: #/models
//     title: "Late-delivery model",
//     order: 40,                 // navigation order
//     description: "...",        // one line under the page title
//     eyebrow: "Machine learning", // optional section category shown above the title (uppercase, accent dot)
//     needs: ["models"],         // datasets that must load (dashboard/data/<name>.json via manifest.json)
//     optional: ["risk"],        // datasets passed as null when absent
//     render(root, data, ctx),   // build the page into `root`; ctx.navigate(id) switches pages
//   })
//
// Insight contract (shown on the overview):
//   registerInsight({
//     id, kind: "Customers", needs: ["analytics"], page: "sales",
//     compute(data) -> {figure, text, source} | null    // null when the data needed is missing
//   })

const pages = [];
const insights = [];

export function registerPage(page) {
  for (const key of ["id", "title", "render"]) {
    if (!page[key]) throw new Error(`registerPage: missing "${key}"`);
  }
  if (pages.some((p) => p.id === page.id)) throw new Error(`registerPage: duplicate id "${page.id}"`);
  pages.push({ order: 100, needs: [], optional: [], description: "", ...page });
  pages.sort((a, b) => a.order - b.order);
}

export const getPages = () => pages.slice();
export const getPage = (id) => pages.find((p) => p.id === id);

export function registerInsight(rule) {
  if (!rule.id || typeof rule.compute !== "function") throw new Error("registerInsight: id and compute are required");
  insights.push({ needs: [], ...rule });
}

export const getInsights = () => insights.slice();
