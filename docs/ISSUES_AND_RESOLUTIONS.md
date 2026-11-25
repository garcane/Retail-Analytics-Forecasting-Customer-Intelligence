# Issues faced and how they were resolved

A working log of what went wrong on this project, why, and what fixed it. It is written from the git history (103 commits on `main`
between 2026-09-07 and 2026-11-25, three merged pull requests), the decision log ([DECISIONS.md](../DECISIONS.md)) and the build
sessions themselves. It is the source for any short write-up of the project. For what the project taught about data and modelling,
see [LESSONS_LEARNED.md](LESSONS_LEARNED.md); this file is about the problems met along the way.

Where a claim is not backed by a commit, a decision or a stored result, it says so.

## At a glance

| | |
|---|---|
| What was built | A DuckDB warehouse (star schema, 22 reconciliation checks), analytics, a late-delivery model and a weekly forecast; then a Snowflake + dbt twin of the same pipeline, the model inside Snowflake, and a five-page Power BI report that reads either |
| Reconciliation | DuckDB vs Snowflake: 22 of 22 checks, 0 differences |
| dbt | 46 models and 321 tests, `dbt build` PASS=367 |
| Tests | 385 pytest tests, all passing with the warehouse built |
| CI | GitHub Actions `python-ci` and `dbt-ci` pass on `main`; `python-ci` was first green on 2026-11-25 after more than 20 red runs |
| Model in Snowflake | Registered, and its scores equal the laptop model to 1e-16 (scored in Snowflake) and 1e-12 (trained in Snowflake) |
| Cost | 0.90 of a 5-credit monthly quota, behind a resource monitor |
| Tools | Claude Code (plan, code, test, review, browser automation of Snowsight and GitHub), GitHub (pull requests, Actions), GitHub Copilot in the editor, dbt, Snowflake, DuckDB, Power BI Desktop and its authoring CLI |
| Honest gaps | The scoring task is created and run once but kept suspended (the data is a static 2018 snapshot); `dbt-live` (manual) has never run; Entra and key-pair sign-in in Power BI were not tried; the model is modest by design of the data |

## How the work was run (and the guardrails that mattered)

- **The owner set the rules up front**, and they held for the whole project: no pushes or merges to `main` without an explicit yes; no credentials, key files or `.env` values in Git, logs or docs; stop and ask before anything destructive, account-wide or costly; never invent a passing result.
- **Every claim carries its evidence level**: run live, tested offline, or `UNVERIFIED`. Several docs were rewritten when a live run disagreed with an earlier statement (see "Documentation drift" below).
- **Independent review before trust.** Changes were reviewed by separate reviewer agents that were told to refute each finding; one review of the CI change this session confirmed only documentation drift and found no code defects. An earlier commit (2026-11-08) records fixes from an independent review. Findings that could not be demonstrated were dropped, which kept false alarms out of the fixes.
- **Browser automation for the parts with no API in reach**: Snowsight (running the setup SQL, the notebook workspace) and GitHub (pull requests, merges, settings), always with the owner's approval for anything that changes state.

## 1. Data and warehouse

**Keys do not mean what their names say.** `customer_id` is per order, so customer counts need `customer_unique_id`. *Fix:* grain stated for every table (DD-01, DD-02), facts never join to facts, reviews keyed on (`review_id`, `order_id`) (DD-03). *Evidence:* `docs/data/DATA_MODEL.md`.

**The EDA notebook had failing cells.** *Fix:* repaired, findings restored, a clean run stored (commit 2026-10-10).

**Geolocation: a Parquet conversion that bought nothing.** The build first converted the large geolocation CSV to Parquet. *Fix:* read the CSV directly and keep zip prefixes as text so leading zeros such as `01046` survive (DD-16). Also documented: pandas with the pyarrow engine parses the column as numbers first and the zeros are already lost.

**Money and counts had to reconcile exactly.** *Fix:* 22 build-time checks that fail the build (row counts, sums of price, freight and payments, the 7,827 late deliveries the EDA found, a complete calendar including a month with no orders). They caught nothing dramatic and are the reason later ports could be trusted.

**A non-deterministic feature query (DD-21).** The late-delivery features moved between runs. *Cause:* `arg_max` picked among 57 price-tied orders in thread order, which shifted `category_prior_*` on about 26,000 rows, and a float `avg` was summed in thread order. *Fix:* an alphabetical tie-break and an ordered aggregate, identical across 1, 2, 8 and 16 threads and the same rule as Snowflake; the v2 and v3 experiment metrics were regenerated and v1 was unchanged.

## 2. Machine learning

**Plausible ideas that did not help, kept as evidence.** Route, category and trailing-rate history features, delivery-time slack, recalibration, shorter training windows and gradient boosting did not beat the first simple logistic regression when judged on months it had not seen (DD-10 to DD-12). *Resolution:* v1 is final and the model is used by rank, not as a probability (DD-11).

**"The data drifts" was assumed, so it was tested.** *Result:* partly right, partly wrong; the real cause was the delivery promise being shortened in 2018, which moved the late label itself (`docs/ml/DRIFT_ANALYSIS.md`).

**A two-month training window looked like a win and was noise.** *Fix:* each month had to choose its window using only earlier months; the gain disappeared. No setting was chosen by its test score.

## 3. Snowflake and dbt

**A silent difference between engines.** RAW tables load every column as text so nothing is lost on ingest; typing happens in dbt staging. *Verified:* all nine tables loaded with row counts exactly equal to the CSV record counts, a rerun skipped every file by checksum, and no stray carriage returns reached the data.

**Proving the port, not assuming it.** *Fix:* a reconciliation tool that compares DuckDB and Snowflake table by table, with tests that perturb data to prove it can fail. *Result:* 22 of 22 checks, 0 differences. Python models gave identical forecast metrics and late-delivery metrics within 6e-6; the remaining gap is floating-point summation order, not a bug.

**Uploading model outputs needed a stage the role could not create.** `write_pandas` tried to create a stage and was denied. *Fix:* stage through the user's own stage (`@~`), run `DELETE` for the run id, `COPY INTO`, then `COMMIT` in one transaction, so a re-publish replaces a run atomically; the run id format is validated before any connection is made.

**Registry calls failed on a missing schema.** *Fix:* set the registry session's schema explicitly. *Result:* the model registered and scoring in Snowflake matched the laptop model to 1e-16.

**The registry needs its own Python environment.** *Fix:* an isolated Python 3.13 environment with its own lock file (DD-25); registration refuses to run from a dirty working tree, so a version always names the commit it came from.

**A Snowflake Scripting task body rejected `SELECT INTO` with a subquery.** *Fix:* split it into two statements and built the insert as a dynamic statement inside an explicit transaction.

**A resource monitor is invisible to most roles.** *Fix:* a one-time, read-only `MONITOR` grant (`05_monitor_grant.sql`, run once as the owner) so credit use could be measured without a broad role. *Correction:* the docs said 0.34 credits; the evidence file recorded 0.90 of 5 and the docs were corrected (2026-11-25).

**Notebooks: the new way to run them has a different bill.** Warehouse notebooks are being retired, and notebooks in Workspaces run on a compute pool billed separately from the 5-credit warehouse monitor. *Fix:* a Git-connected workspace, a 15-minute idle timeout per notebook service, and the service suspended after each session; scheduled scoring was done as a SQL task on the warehouse instead of a scheduled notebook.

**Notebook checks were stricter than the workspace runtime.** The workspace had different numpy and scipy than the laptop (numpy 2.3.5, scipy 1.15.3). *Fix:* tolerances chosen from measured evidence (closed-form methods 1e-9, optimised methods 1e-6, backtest against Snowflake 1e-6 and against DuckDB 1e-5), not loosened until green.

**A notebook sat on "Connecting…".** *Fix:* reconnect the kernel from the notebook's connect menu.

**Account-level privileges needed approval.** Running a task needs `EXECUTE TASK` on the account. *Fix:* asked first, granted by the owner, written down in the grants audit (`SECURITY.md`); the task was executed once (6,306 orders scored in 16 seconds) and left suspended.

## 4. GitHub Actions and CI

**`python-ci` was red for a long time.** Every run in the Actions list from #4 to #26 failed. Three separate causes:

1. **Warehouse-dependent tests.** Nine tests in `tests/test_powerbi_project.py` built their schema from a git-ignored `warehouse.duckdb`. *Fix:* a `warehouse` marker with a collection hook that skips them when the file is missing, plus `REQUIRE_WAREHOUSE=1` so CI can never skip them silently. CI now downloads the Olist CSVs from Kaggle (cached), builds the warehouse, runs the export, and runs every test.
2. **A committed local path.** The committed Power BI `DataFolder` held `C:\Users\...` instead of the placeholder, so a test failed. *Fix:* the placeholder was restored, and the docs say to restore it before committing.
3. **Windows files on a Linux runner.** Twelve tests failed only on Linux because they compared line counts of CRLF files. *Fix:* the test now asserts that each file keeps its own line-ending style, with explicit LF and CRLF cases.

**The Kaggle CLI broke in CI.** Version 2.2.5 imports `six` without declaring it. *Fix:* pin the CLI and add `six` explicitly. The download step was tested for each credential case (none, token, legacy pair, partial) with a stubbed command before it ever ran on GitHub.

**Result:** `python-ci` first passed on 2026-11-25 (run #29 on `main`), and every later run passed. `dbt-ci` (offline `dbt parse`) has passed since the first pull request; `dbt-live` is manual-only and has never run.

**Secrets handling.** `.env` files, key files (`*.p8`) and the patched Power BI copy are git-ignored; secrets reach workflows only through `env`, never inlined into a script. The one secret PR CI reads is `KAGGLE_API_TOKEN`, and without it the warehouse tests skip instead of failing.

## 5. Power BI

**Desktop rejected the generated project.** A measure named `Forecast` clashed with a column `forecast`, because Power BI compares names ignoring case. *Fix:* the measures became `Forecast Value` and `Actual Value`, with a test that checks names ignoring case (2026-10-15).

**The first refresh failed on the date table.** An empty "Not applicable" row cannot be a date table's key. *Fix:* the export leaves it out.

**Generated vs hand-edited.** After the first fixes the committed project is the one Desktop saved, and the generator refuses to overwrite it (`--force` overrides); the specification and mock-up are generated, the report is edited in Desktop.

**Pointing the report at Snowflake without rewriting it.** *Fix:* a script that writes a git-ignored Snowflake-backed copy by changing only the connection parameters and each table's source block, with 68 tests that prove the report, measures and relationships stay byte-identical. *Result:* opened in Desktop and signed in on 2026-11-25, all five pages loaded.

**Sign-in failed with `Failed to parse PEM block containing the private key`** even though user name and password had been chosen, because Desktop was attempting key-pair authentication. *Fix:* retyping the user name and password in both the current-file and the global Data source settings. *Likely cause:* a credential saved by an earlier attempt; not confirmed.

**A new theme did not reach every visual.** Cards and slicers carried their own `background`, `border` and `dropShadow` settings, which sit above the theme. *Fix:* sweep those overrides from 22 visuals so the theme applies. Other findings on the way: two theme keys the schema does not accept were removed; cloned visuals shared filter IDs with their originals and got new ones; a per-series colour needed a data-point setting rather than a line-style one; a card label was truncated and got an explicit label.

**Colours checked, not eyeballed.** Every chart colour is at least 3:1 against white and text at least 7:1 (the contrast table was computed before any file was written). The brief's pastel colours were too light for chart marks and were kept out of charts.

**Screenshots lied twice.** A capture taken right after a reload showed blank cards and an empty table (the model had not finished drawing). *Fix:* capture one page at a time with settle time and recheck. For the README images, the order ids in the risk table were replaced with placeholder bars, in line with the rule that no order identifiers are committed.

**Known and unresolved:** the late-rate charts start with a 100% spike (the first month has only a few orders and months under 500 orders are not filtered out).

## 6. Environment and tooling

- **A Python 3.14 crash that looked like a test hang.** `pytest` exited with no output. *Cause:* an `SSLKEYLOGFILE` environment variable crashes Python 3.14 on Windows whenever it opens an HTTPS connection (`OPENSSL_Uplink: no OPENSSL_Applink`). *Fix:* unset it for the process.
- **TLS inspection on the network** broke package installs and Node tools. *Fix:* a certificate bundle with the Windows roots, passed through `REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` and `uv --native-tls`, never disabling verification.
- **A scratch file named `inspect.py` shadowed the standard library.** Renamed.
- **Relative paths failed inside subprocesses.** Absolute paths.
- **Shell quoting ate backslashes** in generated scripts, and string-patch scripts missed their targets. *Fix:* write scripts to files and use exact-match edits that assert they hit once; a documentation refresh of 61 replacements either applied completely or stopped.
- **The agent's own classifier blocked a setup step** and the owner approved it explicitly: a guardrail working as intended.
- **Browser automation:** a background tab did not respond to input, so the foreground tab was used; the browser tool group was reset between steps, so tab ids were re-read each time.

## 7. Git, branches and documentation

**Generated files conflicted.** Two branches both regenerated the knowledge graph (`graphify-out/`), so a pull request could not merge. *Fix:* keep `main`'s copy of the generated files, merge, then regenerate afterwards.

**A tracked folder of generated artefacts** (`dbt/target`, `dbt_packages`, `logs`) was untracked and ignored (2026-11-08).

**Documentation drift.** Docs said "never opened in Desktop", "has not run on GitHub", "0.34 credits" and "10 known failures" after those had changed. *Fix:* each claim was traced to a stored result and rewritten, and one test now fails if the switch guide drops required caveats. A test also caught a rewrite that removed a file name it required, which is how the check earned its place.

**The HTML dashboard was removed on purpose (DD-27).** The folder had been deleted by the owner while code, tests and docs still referred to it, leaving four failing tests. *Fix:* removed `src/dashboard/` and its 41 tests, the ignore rule and every reference, and recorded that the last commit containing it is `39c32f3`.

**Branch hygiene.** All feature and fix branches were already merged into `main`, so they were deleted (locally and on GitHub) after the last merge; merged pull-request pages keep a restore button.

## What this shows (for a short write-up)

- A local-first build that was **ported, not rewritten**: same shape, same names, same checks, with a tool that proves the two agree.
- **Evidence over assertion**: tolerances from measurements, `UNVERIFIED` labels, corrected numbers when a live run disagreed.
- **Cost and security as design inputs**: a resource monitor, separate pool billing understood and capped, key-pair auth, no secrets in Git, approval gates on every account-level change.
- **CI that tells the truth**: a Windows-first project made to pass on Linux runners, with tests that cannot skip silently when they should run.
- **AI as a pair, with rules**: Claude Code did the planning, implementation, reviews and browser work under written guardrails; every merge to `main` was the owner's decision.
