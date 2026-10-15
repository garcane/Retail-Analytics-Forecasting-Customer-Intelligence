# Security

This is a local, single-user, batch analytics project. It has no server, no network service, no accounts and no cloud resources (D-002, D-005 in [DECISIONS.md](DECISIONS.md)), so most of the usual attack surface does not exist. This page records what does matter and what was checked.

## What was checked (2026-10-13)

| Check | Result |
|---|---|
| Secret patterns (cloud keys, private keys, API keys, passwords) in every tracked text file | None found |
| Raw data, database files, credential-like files in Git (`data/`, `*.duckdb`, `.env*`, `*.pem`, `*.key`, service-account and credentials JSON) | None tracked; all covered by `.gitignore` |
| Hard-coded absolute or user-specific paths in code | None; paths are built from the repository root |
| Network calls from the project code | None. The only network use is installing dependencies with `uv` and, by the user, downloading the dataset from Kaggle |
| Dependencies | Ten direct runtime dependencies plus `pytest`, `ipykernel`, `marimo`, `nbformat`, `nbclient`, `jsonschema` and `referencing` for development, all from PyPI and pinned by `uv.lock`. On 2026-10-15 the 83 locked packages were checked against the OSV vulnerability database and no advisories were found (re-run before relying on this later; advisories are published continuously) |

## Data and privacy

- The dataset is anonymised by Olist: customer and seller identifiers are hashed, and review comments mention partners by invented names. The project uses no other personal data and does not try to re-identify anyone.
- Free-text review comments are stored in `fact_reviews` but are not used by any model or analysis. Review text is not reproduced in the documentation.
- The model's features include customer and seller **state**, which affects how orders are ranked. That is appropriate for logistics, but any use that affects customers directly would need a fairness review ([docs/ml/MODEL_CARD.md](docs/ml/MODEL_CARD.md)).

## Licence

The data is CC BY-NC-SA 4.0 (attribution, non-commercial, share-alike). Non-commercial use only; derived tables and artefacts must carry the same licence if shared. The raw files are not stored in Git (D-008). They remain in earlier commits, because history was not rewritten; this is permitted with attribution. **The GitHub repository (`garcane/GCP`) is public (checked 2026-10-15), so those nine files are downloadable from its early commits** (the first commits, before `d8f6954`). The data's licence allows sharing with attribution for non-commercial use; removing the files from history would need a history rewrite and a force-push, which has not been done and is the owner's decision.

## Practices to keep

- Never commit a Kaggle API token (`kaggle.json`); the README tells users to keep it out of Git, and `.gitignore` blocks common credential file names.
- SQL files use no string-built user input. The only substitution is the `${DATA_DIR}` token, which comes from a command-line argument chosen by the person running the build.
- The warehouse is opened read-only by every analysis and ML script.
- Power BI: the project contains no credentials or connection strings, only a `DataFolder` parameter (the committed value is a placeholder path) that points at local files. The exported data (`powerbi/data/`) is git-ignored because it derives from the CC BY-NC-SA dataset, and it leaves out review comment text. The schema test downloads JSON schemas from `raw.githubusercontent.com` (Microsoft's public repository) and nothing else.

## Not applicable by design

Authentication, authorisation, TLS, secrets management, IAM and network boundaries do not apply because nothing is deployed. If a cloud phase ever returns, these need a fresh design.
