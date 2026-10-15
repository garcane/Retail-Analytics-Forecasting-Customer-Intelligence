# Power BI project

A four-page dashboard over the local warehouse: sales overview, delivery and reviews, late-delivery risk, weekly forecast.
It is delivered as a Power BI Project (`RetailAnalytics.pbip`), built from the same definition as the two HTML documents
in [docs/powerbi/](../docs/powerbi/):

| File | What it is |
|---|---|
| [DAX_SPECIFICATION.html](../docs/powerbi/DAX_SPECIFICATION.html) | The specification: model, relationships, 38 measures with DAX, the SQL each mirrors and its expected value, page layouts, first-open checklist |
| [DASHBOARD_MOCKUP.html](../docs/powerbi/DASHBOARD_MOCKUP.html) | An interactive picture of the finished dashboard with real numbers (open it in any browser; not Power BI) |
| `RetailAnalytics.pbip` | The project: `RetailAnalytics.SemanticModel/` (tables, relationships, measures as TMDL) and `RetailAnalytics.Report/` (pages and visuals as PBIR) |

**Status: never opened in Power BI Desktop.** The project could not be built or opened on the machine it was generated on.
What was checked instead: every JSON file validates against Microsoft's published schemas, every table, column and measure
named anywhere exists, and the exported data reproduces the warehouse figures (`tests/test_powerbi_project.py`,
`tests/test_powerbi_export.py`). That does not prove Desktop will accept every file. If it shows an error on first open,
send the exact message and the file it names.

## Open it

1. Install **Power BI Desktop** (free, Windows), a recent version. If it does not offer to open `.pbip` files, enable *File > Options and settings > Options > Preview features > Power BI Project (.pbip) save option*, and the PBIR enhanced report format if listed, then restart.
2. Create the data files (they are not committed; they derive from the CC BY-NC-SA Olist data):
   ```
   uv run python src/transformation/build_warehouse.py     # if warehouse.duckdb does not exist yet
   uv run python src/powerbi/export_data.py                # writes powerbi/data/ (Parquet and CSV, about 40 MB)
   ```
3. Open `powerbi/RetailAnalytics.pbip`.
4. Set the data location once: *Home > Transform data > Manage parameters > DataFolder*, enter the **full path to
   `powerbi/data`** (for example `C:\Users\you\GCP\powerbi\data`, no trailing backslash), then *Close & Apply*. Until you do
   this the tables stay empty or show a "file not found" error.
5. Run the **first-open checklist** at the end of the specification: about a dozen headline numbers (net revenue R$ 13,494,400.74,
   98,199 net orders, 8.13% late, 21.5% late among the riskiest 10%, and so on) to compare with the cards. If they match, the
   measures and relationships are right.

## Optional

- The colour theme is in `theme/RetailAnalytics.theme.json` (*View > Themes > Browse for themes*). The report already uses the
  built-in base theme, so this is only for matching the project palette.
- Nothing in the project holds credentials. The only machine-specific setting is the `DataFolder` path, which Desktop keeps in
  the model and which is not committed (the committed value is a placeholder).

## Regenerate

The files under `RetailAnalytics.*` and `docs/powerbi/*.html` are generated; edit `src/powerbi/model_spec.py` and re-run, not the files.

```
uv run python src/powerbi/build_spec_html.py
uv run python src/powerbi/build_mockup_html.py
uv run python src/powerbi/build_pbip.py
```

Generation is deterministic (identifiers come from names), and a test fails if the committed project differs from the generator.
Changes you make in Desktop and save will be overwritten by the next generation; if you want to keep editing in Desktop,
stop regenerating.

## Known limits

- Row-level **review comments are not exported**; only the score and whether a comment exists.
- The risk page uses out-of-time scores for 2018-03 to 2018-08 only (the test months of the model); other months show no scores.
- Scores are for ranking, not probabilities (see `docs/ml/MODEL_CARD.md`).
- Measures were written to mirror the SQL, but DAX results have not been computed here; the checklist is how to confirm them.
