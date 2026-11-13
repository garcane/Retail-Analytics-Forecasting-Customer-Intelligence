# Retail analytics dashboard (HTML)

An interactive dashboard that puts the business analytics and the machine-learning outputs side by side: sales, delivery and reviews, the late-delivery model, risk operating points, the weekly forecast, and the data lineage behind every figure. It is a static site with no build step. The Power BI report in `powerbi/` is separate and unchanged. Decisions: DD-22 (why HTML, and how it is structured), DD-23 (data from Snowflake by default).

## Run it

From the repository root:

```powershell
.\.venv\Scripts\python.exe src\dashboard\serve.py              # http://127.0.0.1:8000  (--port to change)
```

`serve.py` binds to 127.0.0.1 only and sends `Cache-Control: no-cache`, so after an edit or a rebuild the browser always loads the current files. Plain `python -m http.server` also works, but it sends no cache header and the browser can then mix an old JavaScript module with a new one. Opening `index.html` straight from disk does not work, because browsers block ES modules and `fetch()` on `file://`; the page says so and shows the command.

## Refresh the data

The committed `dashboard/data/*.json` files are the last build. To rebuild:

```powershell
.\.venv\Scripts\python.exe src\dashboard\build_data.py                    # Snowflake (default): prints the target, then stops
.\.venv\Scripts\python.exe src\dashboard\build_data.py --yes              # Snowflake: connects and builds
.\.venv\Scripts\python.exe src\dashboard\build_data.py --backend duckdb   # offline, from warehouse.duckdb (or DUCKDB_PATH / --db)
```

- Snowflake needs the credentials described in [`../snowflake/README.md`](../snowflake/README.md) (section 2). `DASHBOARD_BACKEND=duckdb` makes DuckDB the default for your session.
- `--skip-scores` skips the risk roll-ups, which retrain the v1 late-delivery model (about two minutes). The risk page then says the scores were not built and how to build them.
- Model metrics (the model and forecast comparison) come from the tracked `reports/*.json`, which the scripts in `src/ml/` produce. Re-run those first if the models changed.
- Each file is written under a temporary name and swapped in only when the whole build succeeds, so a failed build leaves the previous one intact. `manifest.json` is written last and records the build time, git commit, backend and the source of each dataset; the page footer shows it.
- Only aggregates are written. The files hold no customer, order or seller identifiers, and a test checks this.

| File | Built from |
|---|---|
| `kpis.json` | `fact_orders`, `fact_order_items`, `fact_reviews` |
| `analytics.json` | the eight analytics marts (`MARTS.mart_*` on Snowflake, `reports/analytics/*.csv` on DuckDB) |
| `forecast.json` | the weekly series and rolling-origin backtests; `reports/forecast*_metrics.json` |
| `models.json` | `reports/late_delivery_metrics.json` and the experiment reports |
| `risk.json` | v1 scores on the late-delivery features (each test month scored by a model trained only on earlier orders), rolled up by month and risk decile, by flag share, and by state and category |
| `lineage.json` | the layers and the latest `docs/validation/RECONCILIATION_REPORT.md` |

## How it is organised

```
index.html                 shell: navigation, theme toggle, <main>, footer; no inline style or script
css/tokens.css             design tokens: colours (light and dark), type, spacing, radii, chart palette
css/base.css, layout.css   element defaults; page frame, navigation, grid, footer
css/components/*.css       one file per component: card, kpi, controls, insight, tooltip, table, chart
js/boot-check.js           plain script: explains file:// and failed starts
js/main.js                 router (#/<page>), page lifecycle, footer provenance
js/core/                   registry (pages, insights), data-store (manifest + cached fetch), dom helpers,
                           format, labels, theme (Auto/Light/Dark, colour-slot allocation)
js/components/             card (with a Table toggle), kpi, controls, data-table, insight
js/charts/                 line-chart, bar-chart, heatmap, legend, scales, tooltip (SVG, no library)
js/pages/                  overview, sales, delivery, models, risk, forecast, lineage
js/insights/rules.js       the automatic findings shown on the overview
data/                      built JSON (see above)
```

Every chart has a table view of the same numbers (the card's **Table** button), keyboard focus with tooltips, and a legend when it has more than one series. Colours come from `tokens.css`. Series colours are allocated in order, and anything beyond the palette is drawn in a neutral grey rather than reusing a colour. The dark theme redefines the same tokens.

## Extending it

**A new page.** Create `js/pages/<name>.js`, register it, and import it in `js/pages/index.js`:

```js
import { registerPage } from "../core/registry.js";
import { card, grid } from "../components/card.js";
import { lineChart } from "../charts/line-chart.js";

registerPage({
  id: "returns",                 // URL: #/returns
  title: "Returns",
  order: 55,                     // position in the navigation
  eyebrow: "Operations",
  description: "One line under the title.",
  needs: ["analytics"],          // datasets that must load; optional: [...] are passed as null when absent
  render(root, data, ctx) {      // may be async; check ctx.isCurrent() after an await
    const g = grid(root);
    const c = card(g, { title: "...", span: 12, table: () => ({ columns, rows }) });
    lineChart(c.body, { /* series, x, y, formatters */ });
  },
});
```

Charts register their own clean-up; the shell disposes of them when you leave the page.

**A new dataset.** Add a function to `src/dashboard/build_data.py` that returns a JSON-safe dict (pass values through `clean`), `write` it in `main()` with a title and source, and list it in the page's `needs`. Keep it aggregated.

**A new insight on the overview.** Append to `js/insights/rules.js`:

```js
registerInsight({
  id: "late-share", kind: "Delivery", needs: ["kpis"], page: "delivery",
  compute: (data) => data.kpis ? { figure: "8.1%", text: "...", source: "fact_orders" } : null,
});
```

Return `null` when the data is missing and the card simply does not show.

**Rules the tests enforce** (`tests/test_dashboard.py`): no inline `<style>` or `<script>` in `index.html`; every stylesheet linked and present; every page and insight module imported exists; every JavaScript file parses (when `node` is installed); no `innerHTML` (all text goes through `textContent`, because labels come from data); committed data complete and free of identifiers; a failed build leaves the previous data in place.
