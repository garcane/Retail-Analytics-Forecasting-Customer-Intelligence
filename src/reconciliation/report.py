"""Render the reconciliation report as Markdown, only ever from real result objects.

``render_report`` refuses (``ReportError``) to produce anything without a ``ReconciliationRun`` that holds at least one
``CheckResult``; there is no template with placeholder numbers. The stub shipped in docs/validation/RECONCILIATION_REPORT.md
is a separate static file that says NOT RUN and contains no figures.

``write_report`` additionally refuses to overwrite the shipped report path with a self-test run, so DuckDB-vs-DuckDB
numbers can never be mistaken for a Snowflake reconciliation.
"""

from __future__ import annotations

import importlib.metadata as importlib_metadata
import platform
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .checks import ROOT
from .compare import CheckResult, ColumnResult, Comparison, display_value
from .fetch import SnowflakeSettings

DEFAULT_REPORT_PATH = ROOT / "docs" / "validation" / "RECONCILIATION_REPORT.md"
MODES = ("snowflake", "selftest")


class ReportError(ValueError):
    """The report cannot be produced from what was given."""


@dataclass
class RunMetadata:
    mode: str  # snowflake | selftest
    generated_at: str
    git_sha: str
    git_dirty: bool
    account_locator: str  # already redacted; "n/a" for a self-test
    database: str
    role: str
    warehouse: str
    schema_prefix: str
    left_description: str
    right_description: str
    tool_versions: dict[str, str] = field(default_factory=dict)


@dataclass
class ReconciliationRun:
    metadata: RunMetadata
    results: list[CheckResult]


def _git(*args: str) -> str | None:
    try:
        out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, timeout=20, check=True)
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def tool_versions() -> dict[str, str]:
    versions = {"python": platform.python_version()}
    for dist in ("duckdb", "pandas", "numpy", "snowflake-connector-python", "dbt-core", "dbt-snowflake"):
        try:
            versions[dist] = importlib_metadata.version(dist)
        except importlib_metadata.PackageNotFoundError:
            versions[dist] = "not installed"
    return versions


def collect_run_metadata(mode: str, *, settings: SnowflakeSettings | None = None, left_description: str = "",
                         right_description: str = "") -> RunMetadata:
    if mode not in MODES:
        raise ReportError(f"mode must be one of {MODES}")
    if mode == "snowflake" and settings is None:
        raise ReportError("a snowflake run needs its (redacted) connection settings")
    sha = _git("rev-parse", "HEAD")
    status = _git("status", "--porcelain")
    return RunMetadata(
        mode=mode,
        generated_at=datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
        git_sha=sha or "unknown",
        git_dirty=bool(status),
        account_locator=settings.account_redacted if settings else "n/a",
        database=settings.database if settings else "n/a",
        role=settings.role if settings else "n/a",
        warehouse=settings.warehouse if settings else "n/a",
        schema_prefix=settings.schema_prefix if settings else "",
        left_description=left_description,
        right_description=right_description,
        tool_versions=tool_versions(),
    )


# ------------------------------------------------------------------ rendering helpers


def _cell(value: Any, limit: int = 60) -> str:
    s = "NULL" if value is None else str(value)
    s = s.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    return s if len(s) <= limit else s[: limit - 3] + "..."


def _num(x: float | None) -> str:
    return "" if x is None else f"{x:.3g}"


def _table(header: Sequence[str], rows: Sequence[Sequence[Any]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(_cell(c, 120) for c in r) + " |" for r in rows]
    return lines


def _key_text(key: tuple) -> str:
    return ", ".join(str(p) for p in key)


def _col_rows(check: str, cols: Sequence[ColumnResult], only_noteworthy: bool) -> list[list[Any]]:
    rows = []
    for c in cols:
        noteworthy = c.n_mismatch or (c.max_abs_diff or 0) > 0
        if only_noteworthy and not noteworthy:
            continue
        tol = f"{c.mode} {c.tol:g}" if c.mode != "exact" else "exact"
        tolerated = ", ".join(f"{k}={v}" for k, v in sorted(c.tolerated.items())) or ""
        ex = "; ".join(f"[{_key_text(k)}] {display_value(c.column, a)} vs {display_value(c.column, b)}"
                       for k, a, b in c.examples[:3])
        rows.append([c.column, tol, c.n_compared, c.n_mismatch, c.n_unexplained, tolerated,
                     _num(c.max_abs_diff), _num(c.max_rel_diff), ex])
    return rows


COL_HEADER = ["column", "rule", "compared", "mismatches", "unexplained", "classified", "max abs diff",
              "max rel diff", "examples (key: left vs right)"]


def _comparison_block(res: CheckResult, cmp: Comparison) -> list[str]:
    out = [f"**{cmp.label}** ({cmp.left_name} vs {cmp.right_name}): **{cmp.status}**", ""]
    out += _table(
        ["left rows", "right rows", "matched keys", "missing in right", "extra in right", "duplicate keys L/R",
         "rows with a differing value"],
        [[cmp.left_rows, cmp.right_rows, cmp.matched_rows, cmp.missing_in_right, cmp.extra_in_right,
          f"{cmp.duplicate_keys_left}/{cmp.duplicate_keys_right}", cmp.rows_with_diff]])
    out.append("")
    if cmp.columns_only_left or cmp.columns_only_right:
        out += [(f"Columns only on {cmp.left_name}: {', '.join(cmp.columns_only_left) or 'none'}; "
                f"only on {cmp.right_name}: {', '.join(cmp.columns_only_right) or 'none'}."), ""]
    if cmp.missing_examples:
        out += [f"Missing in {cmp.right_name} (first {len(cmp.missing_examples)}): "
                + "; ".join(f"[{_key_text(k)}]" for k in cmp.missing_examples), ""]
    if cmp.extra_examples:
        out += [f"Extra in {cmp.right_name} (first {len(cmp.extra_examples)}): "
                + "; ".join(f"[{_key_text(k)}]" for k in cmp.extra_examples), ""]
    rows = _col_rows(res.check_name, cmp.columns, only_noteworthy=True)
    if rows:
        out += ["Columns with a difference (including float drift inside tolerance):", ""]
        out += _table(COL_HEADER, rows) + [""]
    else:
        out += [f"All {len(cmp.columns)} compared columns are identical.", ""]
    if cmp.surrogate_columns:
        srows = _col_rows(res.check_name, cmp.surrogate_columns, only_noteworthy=False)
        out += ["Surrogate keys (reported separately; they do not decide the status above):", ""]
        out += _table(COL_HEADER, srows) + [""]
    return out


def _validate_run(run: Any) -> None:
    if not isinstance(run, ReconciliationRun):
        raise ReportError("render_report needs a ReconciliationRun built from real check results")
    if not run.results:
        raise ReportError("no check results: refusing to render a report with nothing in it")
    if not all(isinstance(r, CheckResult) for r in run.results):
        raise ReportError("results must be CheckResult objects")
    if run.metadata.mode not in MODES:
        raise ReportError("unknown run mode")


def render_report(run: ReconciliationRun) -> str:
    _validate_run(run)
    m, results = run.metadata, run.results
    selftest = m.mode == "selftest"
    lines: list[str] = []
    if selftest:
        lines += ["# Reconciliation report: OFFLINE SELF-TEST (DuckDB vs DuckDB)", "",
                  ("> **This is not a Snowflake reconciliation.** Both sides are DuckDB; it only shows the comparison "
                  "machinery and the registered DuckDB SQL work."), ""]
    else:
        lines += ["# Reconciliation report: DuckDB vs Snowflake", ""]

    lines += ["## Run", ""]
    lines += _table(["item", "value"], [
        ["generated", m.generated_at],
        ["git SHA", m.git_sha + (" (working tree had uncommitted changes)" if m.git_dirty else "")],
        ["mode", m.mode],
        ["left (reference)", m.left_description or "duckdb"],
        ["right", m.right_description or ("duckdb (self-test)" if selftest else "snowflake")],
        ["Snowflake account locator (redacted)", m.account_locator],
        ["database / role / warehouse", f"{m.database} / {m.role} / {m.warehouse}"],
        ["schema prefix (dbt dev target)", m.schema_prefix or "(none: prod schemas)"],
    ] + [[f"tool: {k}", v] for k, v in m.tool_versions.items()])
    lines.append("")

    counts: dict[str, int] = {}
    for r in results:
        counts[r.status] = counts.get(r.status, 0) + 1
    lines += ["## Summary", "",
              ", ".join(f"{k}: {v}" for k, v in sorted(counts.items())) + f" (of {len(results)} checks)", ""]
    rows = []
    for r in results:
        p = r.primary
        if p is None:
            rows.append([r.check_name, r.group, r.status, "", "", "", "", "", r.error or ""])
            continue
        rows.append([r.check_name, r.group, r.status, p.left_rows, p.right_rows, p.missing_in_right + p.extra_in_right,
                     p.n_unexplained, p.n_tolerated, ""])
    lines += _table(["check", "group", "status", "left rows", "right rows", "missing+extra keys",
                     "unexplained value diffs", "classified tie-break diffs", "error"], rows) + [""]

    # three-way headline and documented constants
    exp_results = [(r, e) for r in results for e in r.expected]
    if exp_results:
        lines += ["## Documented constants (three-way)", "",
                  "Each metric: left value, right value, and the documented constant (source in the last column).", ""]
        lines += _table(["check", "metric", "documented", "left", "right", "left ok", "right ok", "source"],
                        [[r.check_name, e.metric, e.expected, e.left_value, e.right_value,
                          "yes" if e.left_ok else "NO", "yes" if e.right_ok else "NO", e.source]
                         for r, e in exp_results]) + [""]

    ties = [(r, t) for r in results for t in r.tie_breaks]
    if ties:
        lines += ["## arg_max / max_by tie-breaks", "",
                  ("DuckDB `arg_max` and Snowflake `max_by` may pick different values when the maximum is tied. Orders with "
                  "a tied maximum are counted below. A difference in the picked column is classified `tie_break` only "
                  "when both values are among the order's tied candidates; differences in running category totals are "
                  "classified `downstream_of_tie_break` whenever any ambiguous order exists (a weak bound, shown so it "
                  "can be judged). Nothing is dropped: every classified difference is still counted."), ""]
        lines += _table(["check", "tie-break", "ambiguous orders", "picked column", "tie_break diffs",
                         "downstream columns", "downstream diffs", "note"],
                        [[r.check_name, t.name, t.n_ambiguous_orders, t.direct_column or "(not in output)", t.n_direct,
                          ", ".join(t.cascade_columns) or "", t.n_downstream, t.note] for r, t in ties]) + [""]

    lines += ["## Check details", ""]
    for r in results:
        lines += [f"### {r.check_name} ({r.group}): {r.status}", "", r.description, ""]
        if r.error:
            lines += [f"Error: `{_cell(r.error, 400)}`", ""]
            continue
        for cmp in r.comparisons:
            lines += _comparison_block(r, cmp)

    lines += ["## Notes", "",
              ("- Snowflake SQL is generated from `src/reconciliation/checks.py` against the dbt marts; it was written to "
              "the model contract and is only as verified as this run."),
              "- Customer review text is compared but never printed; examples show its length only.",
              ("- Counts, keys, money (Decimal), booleans, strings, dates and timestamps compare exact; doubles relative "
              "1e-9; `distance_km` absolute 1e-6; rates absolute 1e-9."), ""]
    return "\n".join(lines)


def write_report(run: ReconciliationRun, path: Path | None = None) -> Path:
    """Render and write. A self-test run may not overwrite the shipped report path."""
    target = Path(path) if path is not None else DEFAULT_REPORT_PATH
    if run.metadata.mode == "selftest" and target.resolve() == DEFAULT_REPORT_PATH.resolve():
        raise ReportError("refusing to write a self-test over docs/validation/RECONCILIATION_REPORT.md; "
                          "pass a different --report-path")
    text = render_report(run)  # validates before touching the disk
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    return target
