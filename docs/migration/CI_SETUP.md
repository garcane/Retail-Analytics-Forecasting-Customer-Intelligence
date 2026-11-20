# CI setup (GitHub Actions)

Three workflows live in `.github/workflows/`. Two are offline gates that need no secrets. One is a manual live build
that only runs when you have configured Snowflake secrets.

| Workflow | Trigger | Needs secrets | Purpose |
|---|---|---|---|
| `python-ci.yml` | every push, every pull request | Kaggle only (optional) | `ruff` on the new Snowflake-related code; download Olist from Kaggle, build the DuckDB warehouse and the Power BI export, then the full `pytest` suite |
| `dbt-ci.yml` | push / PR touching `snowflake/dbt/**` (or the workflow file) | no | `dbt deps`, `dbt parse --target ci` (required gate), `dbt compile --no-populate-cache` (informational) |
| `dbt-live.yml` | `workflow_dispatch` only | yes (environment-scoped) | `dbt build --target prod` against the real Snowflake account |

Missing Snowflake credentials cannot fail PR CI: the two PR-triggered workflows never read a Snowflake secret, and the
live workflow cannot be triggered by a push or a pull request at all. The only secret PR CI reads is the Kaggle token,
and without it the warehouse tests skip rather than fail.

## python-ci

Two jobs, so lint and tests report separately.

- `lint`: `uvx ruff@0.12.0 check --select E4,E7,E9,F` on `src/data_access`, `src/reconciliation`, `snowflake/ingestion`,
  `tests/test_data_access.py`, `tests/test_reconciliation.py`, `tests/test_snowflake_ingestion.py`,
  `tests/test_powerbi_snowflake.py` and `powerbi/snowflake`. Ruff is pinned and the rules are explicit because recent
  ruff releases (0.17.x) enable many more default rules and flag 56 style issues in this code that 0.12 does not.
  Legacy DuckDB code is deliberately not linted.
- `test`:
  1. `uv sync --locked --group dev`. `--locked` never rewrites `uv.lock`; it fails if the lock is out of date with
     `pyproject.toml`. That is intentional. If it fails, run `uv lock` locally and commit the result. `UV_PYTHON=3.13`
     is set because the root `.python-version` says 3.14 while the dbt side needs 3.13; `requires-python` is `>=3.13`.
  2. Restore `data/` from the Actions cache (key `olist-brazilian-ecommerce-v1`; bump the suffix to force a re-download).
  3. On a cache miss, download the nine Olist CSVs with `kaggle@2.2.5` (`datasets download -d olistbr/brazilian-ecommerce
     --unzip`). kaggle 2.2.5 imports `six` without declaring it, so the step adds `--with six==1.17.0`.
  4. If the CSVs are there: print their SHA-256, run `src/transformation/build_warehouse.py` (which fails the job if any
     of its validation checks fails, including the real-data figures such as 7,827 late deliveries), then
     `src/powerbi/export_data.py` to write `powerbi/data/`.
  5. `pytest -q` with `REQUIRE_WAREHOUSE=1` when step 4 built the warehouse.

### The `warehouse` marker

Tests that read `ROOT/warehouse.duckdb` carry `@pytest.mark.warehouse` (per module or per test). A collection hook in
`tests/conftest.py` skips them when the file is missing, except when `REQUIRE_WAREHOUSE=1`, where a missing file stops
the run with an error. So:

- With Kaggle credentials (or a cached copy), every test runs, and a broken build cannot hide as skips.
- Without them (for example a pull request from a fork, which receives no secrets), the warehouse tests are reported as
  skipped with a notice and the rest of the suite still gates the PR.

In `tests/test_powerbi_project.py`, only the two tests that read committed files are unmarked:
`test_committed_project_is_complete_and_holds_no_machine_path` (the committed `expressions.tmdl` must hold the
`DataFolder` placeholder, not a local path) and `test_generator_refuses_to_overwrite_a_project_saved_by_desktop`.

### Kaggle secret

Create a Kaggle API token (kaggle.com, *Settings > API*) and add it as a **repository** secret
(*Settings > Secrets and variables > Actions*):

| Secret | Value |
|---|---|
| `KAGGLE_API_TOKEN` | the new-style API token |

The legacy pair `KAGGLE_USERNAME` + `KAGGLE_KEY` (the two fields of `kaggle.json`) also works. Secrets are passed to the
step through `env`, never interpolated into the script. The dataset is CC BY-NC-SA 4.0: CI downloads it and keeps it only
in the Actions cache, which is private to this repository's workflows; it is never committed.

### Power BI DataFolder after saving in Desktop

The committed `powerbi/RetailAnalytics.SemanticModel/definition/expressions.tmdl` holds the placeholder
`C:\REPLACE\WITH\FULL\PATH\TO\powerbi\data`. When you open the project, set `DataFolder` to your local
`powerbi/data` path. Saving in Desktop writes that local path back into the file: restore the placeholder before
committing (`git checkout -- powerbi/RetailAnalytics.SemanticModel/definition/expressions.tmdl` if nothing else in it
changed), or the test above fails.

## dbt-ci

Runs in `snowflake/dbt` with the dbt environment from `snowflake/dbt/uv.lock` (`uv sync --locked`, Python 3.13,
dbt-core 1.11 / dbt-snowflake 1.11, isolated from the root project).

1. `dbt deps` fetches `dbt_utils` from hub.getdbt.com. This is the only network step.
2. `dbt parse --target ci` is the required gate. The `ci` target in `profiles.yml` has dummy defaults for every
   variable, and the workflow sets no `SNOWFLAKE_*` / `RETAIL_SF_*` variables, so parse cannot connect.
3. `dbt compile --no-populate-cache --target ci` is `continue-on-error`. It is informational: it renders all SQL to
   `target/compiled`. If it ever starts needing a connection it fails without failing the job.

Suggested branch protection: require `dbt-ci / dbt-parse` (and `python-ci / lint`). Do not require `dbt-live`.

## dbt-live (manual)

Use only after the Snowflake objects exist (`snowflake/setup/*.sql`) and RAW is loaded (`snowflake/ingestion/load_raw.py`,
see `docs/migration/INGESTION_RUNBOOK.md`). A prod build consumes warehouse credits.

Job 1, `detect`, checks that `SNOWFLAKE_ACCOUNT`, `SNOWFLAKE_USER` and `SNOWFLAKE_PRIVATE_KEY` are non-empty and emits
only a boolean. If any is missing it prints a notice and the run ends green with the `live` job skipped.

Job 2, `live` (only when the secrets exist):

1. installs dbt (`uv sync --locked`);
2. writes `SNOWFLAKE_PRIVATE_KEY` to `$RUNNER_TEMP/snowflake_rsa_key.p8` (`umask 077`, `chmod 600`), never echoed, and
   exports `SNOWFLAKE_PRIVATE_KEY_PATH` pointing at it, because `profiles.yml` reads a key file path;
3. exports `RETAIL_SF_ROLE` / `RETAIL_SF_WAREHOUSE` / `RETAIL_SF_DATABASE` only if they are non-empty, so an unset
   secret falls back to the `profiles.yml` defaults (`RETAIL_TRANSFORMER`, `RETAIL_WH`, `RETAIL_OLIST`) rather than
   passing an empty string;
4. `dbt deps`, then `dbt build --target prod` (nothing else touches Snowflake);
5. always deletes the key file.

Only one live run executes at a time (`concurrency: dbt-live`, not cancelled mid-run).

### Required secrets

Create a GitHub environment named `snowflake-prod` (Settings > Environments) and add these as **environment secrets**
(not repository secrets), so they are only released to jobs that reference that environment:

| Secret | Required | Notes |
|---|---|---|
| `SNOWFLAKE_ACCOUNT` | yes | account identifier (`orgname-accountname`), not a URL |
| `SNOWFLAKE_USER` | yes | the Snowflake user that holds the public key and the dbt role |
| `SNOWFLAKE_PRIVATE_KEY` | yes | the full PKCS#8 PEM text including the `BEGIN` / `END` lines and real newlines |
| `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` | only if the key is encrypted | leave unset for an unencrypted key |
| `RETAIL_SF_ROLE` | no | default `RETAIL_TRANSFORMER` |
| `RETAIL_SF_WAREHOUSE` | no | default `RETAIL_WH` |
| `RETAIL_SF_DATABASE` | no | default `RETAIL_OLIST` |

Hardening, all done in GitHub settings rather than in the workflow:

- Add required reviewers and/or a deployment-branch rule to the `snowflake-prod` environment. Both jobs reference the
  environment, so required reviewers are asked to approve twice per run (detect, then live). If that is annoying, use a
  deployment-branch rule instead of reviewers.
- Use a dedicated Snowflake user with only `RETAIL_TRANSFORMER`, and a key pair created just for CI so it can be revoked
  independently.
- Never paste key material into an issue, a workflow file or a log. The workflow does not print it, and GitHub masks
  secret values in logs, but masking is a safety net and not a control.

## Action versions

Actions are pinned to major tags: `actions/checkout@v7` and `astral-sh/setup-uv@v7`. setup-uv has newer releases
(10.x at the time of writing) but publishes no floating major tag beyond `v7`, so `v7` is the newest major tag usable
under this pinning policy. Re-check when updating. ruff is pinned to `0.12.0`.

## Verification record

Run on the Windows dev host on 2026-11-06, offline from Snowflake. Nothing was run on GitHub.

| Check | Result |
|---|---|
| YAML of all three workflows parses (PyYAML 6.0.3) | VERIFIED: parses; jobs `lint`, `test`, `dbt-parse`, `detect`, `live` |
| `actionlint` 1.7.12 (via `actionlint-py` in a scratch venv) on the three files | VERIFIED: exit 0, no findings. shellcheck was not installed, so `run:` script bodies were not shellchecked |
| `ruff@0.12.0 check --select E4,E7,E9,F` on the listed paths | VERIFIED: All checks passed. Also passes with ruff 0.17.4 and the same `--select` |
| `uv lock --check` on a copy of `pyproject.toml` + `uv.lock` | VERIFIED: exit 0, lock is consistent with `pyproject.toml` (94 packages) |
| python-ci `test` steps on a clean copy of the working tree (`uv sync --locked --group dev` into a scratch env, Python 3.13.5, then `pytest -q`) | VERIFIED on Windows (2026-11-06, before the Kaggle step): `5 failed, 279 passed, 25 skipped, 5 errors`, all in `tests/test_powerbi_project.py`. Fixed on 2026-11-20, see the next row |
| 2026-11-20: warehouse built from the Olist CSVs, `export_data.py`, then `REQUIRE_WAREHOUSE=1 pytest -q` (Windows, project `.venv`, Python 3.14) | VERIFIED: `424 passed`, 0 skipped. Without the warehouse: the 9 marked Power BI tests skip and the 2 file-only ones pass |
| dbt-ci steps on a clean copy of `snowflake/dbt`: `uv sync --locked`, `dbt deps`, `dbt parse --target ci` | VERIFIED: exit 0 each. dbt 1.11.17, adapter snowflake 1.11.6, dbt_utils 1.4.1. No `SNOWFLAKE_*` / `RETAIL_SF_*` variables set |
| `dbt parse --target ci` and `dbt compile --no-populate-cache --target ci` with `HTTP(S)_PROXY` pointed at a dead port | VERIFIED: both exit 0; "Found 46 models, 321 data tests, 9 sources, 657 macros"; `logs/dbt.log` has no connection-open lines |

Host-specific note: `dbt deps` only worked locally with `REQUESTS_CA_BUNDLE` set to an exported Windows root-certificate
bundle (TLS inspection on this host). GitHub-hosted runners do not need that, and the workflows do not set it.

### UNVERIFIED

- None of the three workflows has run on GitHub. Runner behaviour (Ubuntu, Python 3.13 download, the setup-uv cache,
  `uvx` resolution of `ruff@0.12.0`) is untested.
- The Kaggle step has not run: no Kaggle token was used here. `kaggle@2.2.5` (with `six`) was installed in a scratch
  environment and its `datasets download` flags checked, but a real download, the unzip layout on Ubuntu and the
  Actions cache save/restore are untested. The warehouse build and test run were done locally with the same Olist
  CSVs instead.
- The pytest result above is for Windows. A Linux run may differ (line endings, path handling); the CRLF files in the
  repo are the likeliest source.
- `dbt-live.yml`: the `detect` / skip logic, environment secret release, key-file writing, `dbt build --target prod`
  and key cleanup were never executed. The expression syntax was only linted by actionlint.
- Whether an empty `SNOWFLAKE_PRIVATE_KEY_PASSPHRASE` works with an unencrypted key under dbt-snowflake (also a
  `snowflake/dbt/README_LIVE_CHECKS.md` item). The workflow passes it through as an empty string when the secret is unset.
- The step that depends on a secret that is a multi-line PEM: GitHub stores and releases multi-line secrets correctly,
  but this was not exercised here.

### Repository hygiene note

`snowflake/dbt/target/`, `snowflake/dbt/dbt_packages/` and `snowflake/dbt/logs/` are currently tracked by git (from
earlier commits). CI regenerates all three, so they should be untracked (`git rm -r --cached`) and ignored at the root.
`dbt deps` in CI overwrites `dbt_packages/` in the checkout, which is harmless but would show as a dirty tree.
