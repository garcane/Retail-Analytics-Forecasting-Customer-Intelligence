// Application shell: navigation, hash routing (#/<page-id>), per-page data loading, footer provenance.
// Pages and insight rules register themselves when their modules are imported (see pages/index.js).

import "./pages/index.js";
import "./insights/index.js";
import { el, clear } from "./core/dom.js";
import { getPages, getPage } from "./core/registry.js";
import { load, manifest } from "./core/data-store.js";
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
  renderNav(id);
  document.title = `${page.title} · Retail Analytics Dashboard`;
  main.setAttribute("aria-busy", "true");
  try {
    const data = await load(page.needs, page.optional);
    if (token !== renderToken) return; // a newer navigation won
    clear(main);
    main.append(el("div", { class: "page-head" }, el("h2", { text: page.title }), page.description ? el("p", { text: page.description }) : null));
    page.render(main, data, { navigate });
    main.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  } catch (err) {
    console.error(err);
    if (token !== renderToken) return;
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
    footer.replaceChildren(
      `Data built ${when} from the ${m.backend === "snowflake" ? "Snowflake" : "DuckDB"} warehouse`,
      m.git_sha ? ` at commit ${m.git_sha}` : "",
      ". Olist dataset (Kaggle), CC BY-NC-SA 4.0. Only aggregates are shown; no order-level or review text.",
    );
  } catch {
    footer.textContent = "";
  }
}

initTheme(document.getElementById("theme-toggle"));
window.addEventListener("hashchange", route);
renderFooter();
route().then(() => { window.__dashboardReady = true; });
