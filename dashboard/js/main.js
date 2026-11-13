// Application shell: navigation, hash routing (#/<page-id>), per-page data loading, footer provenance.
// Pages and insight rules register themselves when their modules are imported (see pages/index.js).

import "./pages/index.js";
import "./insights/index.js";
import { el, clear, disposeCharts } from "./core/dom.js";
import { getPages, getPage } from "./core/registry.js";
import { load, manifest, refresh } from "./core/data-store.js";
import { initTheme } from "./core/theme.js";

const nav = document.getElementById("nav");
const main = document.getElementById("main");
const footer = document.getElementById("footer");

function currentId() {
  const id = location.hash.replace(/^#\/?/, "").split("?")[0];
  return getPage(id) ? id : getPages()[0].id;
}

function navigate(id) {
  location.hash = `#/${id}`;
}

function renderNav(active) {
  clear(nav);
  for (const p of getPages()) {
    nav.append(el("a", { href: `#/${p.id}`, "aria-current": p.id === active ? "page" : null, text: p.title }));
  }
}

let renderToken = 0;
async function route() {
  const id = currentId();
  const page = getPage(id);
  const token = ++renderToken;
  const isCurrent = () => token === renderToken;
  renderNav(id);
  document.title = `${page.title} · Retail Analytics Dashboard`;
  main.setAttribute("aria-busy", "true");
  try {
    if (await refresh()) renderFooter(); // a newer data build: drop stale caches before loading
    const data = await load(page.needs, page.optional);
    if (!isCurrent()) return; // a newer navigation won
    disposeCharts();
    // Each page renders into its own view. render() may be async (the overview loads more data); a page that
    // finishes after the user has moved on writes only into its own detached view, never into the next page.
    const view = el("div", { class: "page-view" });
    main.replaceChildren(view);
    view.append(el("div", { class: "page-head", "data-ghost": page.title },
      page.eyebrow ? el("span", { class: "eyebrow", text: page.eyebrow }) : null,
      el("h2", { text: page.title }),
      page.description ? el("p", { text: page.description }) : null));
    await page.render(view, data, { navigate, isCurrent });
    if (!isCurrent()) return;
    main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  } catch (err) {
    console.error(err);
    if (!isCurrent()) return;
    disposeCharts();
    clear(main);
    main.append(el("div", { class: "boot-error" },
      el("h1", { text: `Could not load "${page.title}"` }),
      el("p", { text: String(err.message || err) }),
      el("p", { text: "Rebuild the data with: uv run python src/dashboard/build_data.py --yes (Snowflake) or --backend duckdb (offline)" })));
  } finally {
    main.removeAttribute("aria-busy");
  }
}

async function renderFooter() {
  try {
    const m = await manifest();
    const when = m.generated_at ? m.generated_at.replace("T", " ").replace("+00:00", " UTC") : "unknown";
    const source = m.backend === "snowflake" ? "Snowflake (RETAIL_OLIST marts, built by dbt)" : "DuckDB (the local reference warehouse)";
    const col = (title, text) => el("div", {}, el("h4", { text: title }), el("p", { text }));
    footer.replaceChildren(el("div", { class: "footer-inner" },
      el("p", { class: "footer-headline", text: "Every figure here traces back to one dataset, two warehouses that agree." }),
      el("div", { class: "footer-cols" },
        col("Data source", source),
        col("Built", `${when}${m.git_sha ? ` · commit ${m.git_sha}` : ""}`),
        col("Dataset", "Olist Brazilian e-commerce, Kaggle. CC BY-NC-SA 4.0."),
        col("Privacy", "Aggregates only: no order-level rows, no review text.")),
      el("p", { class: "footer-small", text: "Retail Analytics, Forecasting & Customer Intelligence · DuckDB and Snowflake + dbt implementations · Power BI remains available for conventional reporting." })));
  } catch {
    footer.textContent = "";
  }
}

initTheme(document.getElementById("theme-toggle"));
window.addEventListener("hashchange", route);
renderFooter();
route().then(() => { window.__dashboardReady = true; });
