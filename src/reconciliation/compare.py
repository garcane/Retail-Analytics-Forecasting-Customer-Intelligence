"""Compare two result sets on a natural key and report exactly what differs.

Order of operations in ``compare_frames`` (a defect is counted once, where it belongs):
  1. schema: columns present on only one side;
  2. keys: duplicate keys on each side, keys missing from one side;
  3. values: only for keys present on both sides, column by column, with the column's mode and tolerance.
So a missing or extra row is never also counted as a value mismatch. Surrogate-key columns are compared in a separate
list and never decide pass/fail. Mismatches may be *classified* (``tie_break`` / ``downstream_of_tie_break``) by an
injected classifier: they are still counted and shown, only split out from the unexplained ones.

Comparison modes: ``exact`` (ints, Decimal money, booleans, strings, dates, timestamps; a float meeting a Decimal is
compared via its shortest repr), ``abs`` (|a-b| <= tol) and ``rel`` (|a-b| <= tol * max(|a|,|b|), equal values always
pass). Null matches null; null against a value is a mismatch. Without a rule, a column that holds a float on either side
is compared ``rel`` 1e-9 and every other column ``exact``.
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import numpy as np
import pandas as pd

from .checks import REL_DOUBLE, SENSITIVE_COLUMNS, Check, ColumnRule, TieBreak, render_duckdb, render_snowflake
from .fetch import Fetcher, redact_secrets

Classifier = Callable[[tuple, Any, Any], "str | None"]
TIE_BREAK = "tie_break"
DOWNSTREAM = "downstream_of_tie_break"


# ------------------------------------------------------------------ result objects


@dataclass
class ColumnResult:
    column: str
    mode: str
    tol: float
    surrogate: bool
    n_compared: int
    n_mismatch: int  # all mismatches, including classified ones
    n_null_mismatch: int  # one side null, the other not (subset of n_mismatch)
    tolerated: dict[str, int]  # classification label -> count
    max_abs_diff: float | None
    max_rel_diff: float | None
    examples: list[tuple[tuple, Any, Any]]  # (key, left, right); unexplained first

    @property
    def n_unexplained(self) -> int:
        return self.n_mismatch - sum(self.tolerated.values())


@dataclass
class Comparison:
    label: str
    left_name: str
    right_name: str
    left_rows: int
    right_rows: int
    matched_rows: int
    keys: tuple[str, ...]
    missing_in_right: int  # keys the left side has and the right lacks
    extra_in_right: int  # keys the right side has and the left lacks
    missing_examples: list[tuple]
    extra_examples: list[tuple]
    duplicate_keys_left: int
    duplicate_keys_right: int
    columns_only_left: list[str]
    columns_only_right: list[str]
    columns: list[ColumnResult]
    surrogate_columns: list[ColumnResult]
    rows_with_diff: int  # matched rows with >=1 unexplained mismatch in a non-surrogate column

    @property
    def n_unexplained(self) -> int:
        return sum(c.n_unexplained for c in self.columns)

    @property
    def n_tolerated(self) -> int:
        return sum(sum(c.tolerated.values()) for c in self.columns)

    @property
    def surrogate_mismatches(self) -> int:
        return sum(c.n_mismatch for c in self.surrogate_columns)

    @property
    def passed(self) -> bool:
        # A comparison of two empty frames (or with no matched row) proves nothing, so it never passes.
        if self.left_rows == 0 or self.right_rows == 0 or self.matched_rows == 0:
            return False
        return not (self.missing_in_right or self.extra_in_right or self.duplicate_keys_left
                    or self.duplicate_keys_right or self.columns_only_left or self.columns_only_right
                    or self.n_unexplained)

    @property
    def status(self) -> str:
        if not self.passed:
            return "FAIL"
        return "PASS_WITH_TIE_BREAKS" if self.n_tolerated else "PASS"


@dataclass
class ExpectedResult:
    metric: str
    expected: Decimal
    source: str
    left_value: Any
    right_value: Any
    left_ok: bool
    right_ok: bool


@dataclass
class TieBreakInfo:
    name: str
    n_ambiguous_orders: int
    direct_column: str | None
    cascade_columns: tuple[str, ...]
    n_direct: int
    n_downstream: int
    note: str = ""


@dataclass
class CheckResult:
    check_name: str
    group: str
    description: str
    comparisons: list[Comparison] = field(default_factory=list)
    expected: list[ExpectedResult] = field(default_factory=list)
    tie_breaks: list[TieBreakInfo] = field(default_factory=list)
    error: str | None = None
    elapsed_s: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def status(self) -> str:
        if self.error:
            return "ERROR"
        if not self.comparisons or any(c.status == "FAIL" for c in self.comparisons):
            return "FAIL"
        if any(not (e.left_ok and e.right_ok) for e in self.expected):
            return "FAIL"
        if any(c.status == "PASS_WITH_TIE_BREAKS" for c in self.comparisons):
            return "PASS_WITH_TIE_BREAKS"
        return "PASS"

    @property
    def primary(self) -> Comparison | None:
        return self.comparisons[0] if self.comparisons else None


# ------------------------------------------------------------------ value comparison


def _is_num(v: Any) -> bool:
    return isinstance(v, (int, float, Decimal)) and not isinstance(v, bool)


def _as_decimal(v: Any) -> Decimal:
    return Decimal(repr(v)) if isinstance(v, float) else Decimal(v)


def _stats(a: Any, b: Any) -> tuple[float | None, float | None]:
    if not (_is_num(a) and _is_num(b)):
        return None, None
    fa, fb = float(a), float(b)
    if np.isinf(fa) or np.isinf(fb):
        return None, None
    d = abs(fa - fb)
    denom = max(abs(fa), abs(fb))
    return d, (d / denom if denom > 0 else 0.0)


def compare_values(a: Any, b: Any, mode: str, tol: float) -> tuple[bool, float | None, float | None]:
    """(equal within rule, abs diff, rel diff) for two non-null values."""
    d, r = _stats(a, b)
    if mode in {"abs", "rel"} and _is_num(a) and _is_num(b):
        fa, fb = float(a), float(b)
        if fa == fb:
            return True, d, r
        if np.isinf(fa) or np.isinf(fb):
            return False, d, r
        diff = abs(fa - fb)
        if mode == "abs":
            return diff <= tol, d, r
        return diff <= tol * max(abs(fa), abs(fb)), d, r
    # exact (also the fallback for non-numeric values under abs/rel)
    try:
        if _is_num(a) and _is_num(b):
            if isinstance(a, float) and isinstance(b, float):
                return a == b, d, r
            if isinstance(a, float) or isinstance(b, float):
                if np.isnan(float(a)) or np.isnan(float(b)):
                    return False, d, r
                return _as_decimal(a) == _as_decimal(b), d, r
            return a == b, d, r
        return bool(a == b), d, r
    except (TypeError, InvalidOperation):
        return False, d, r


def _key_part(v: Any) -> Any:
    if isinstance(v, float) and v.is_integer():
        return int(v)
    if isinstance(v, Decimal) and v == v.to_integral_value():
        return int(v)
    return v


def _index_keys(df: pd.DataFrame, keys: Sequence[str]) -> tuple[dict[tuple, int], int]:
    """First row position per key and the number of surplus duplicate rows."""
    cols = [df[k].tolist() for k in keys]
    first: dict[tuple, int] = {}
    dups = 0
    for i, parts in enumerate(zip(*cols, strict=True)):
        k = tuple(_key_part(p) for p in parts)
        if k in first:
            dups += 1
        else:
            first[k] = i
    return first, dups


def _has_float(df: pd.DataFrame, col: str) -> bool:
    return any(isinstance(v, float) for v in df[col].tolist())


def compare_frames(left: pd.DataFrame, right: pd.DataFrame, keys: Sequence[str],
                   rules: Mapping[str, ColumnRule] | None = None, *, label: str = "left_vs_right",
                   left_name: str = "left", right_name: str = "right",
                   classifiers: Mapping[str, Classifier] | None = None, max_examples: int = 5) -> Comparison:
    rules = rules or {}
    classifiers = classifiers or {}
    keys = tuple(k.lower() for k in keys)
    left_cols, right_cols = list(left.columns), list(right.columns)
    only_left = [c for c in left_cols if c not in right_cols]
    only_right = [c for c in right_cols if c not in left_cols]
    for k in keys:
        if k not in left_cols or k not in right_cols:
            raise KeyError(f"key column {k!r} missing from one side ({label})")

    lidx, ldup = _index_keys(left, keys)
    ridx, rdup = _index_keys(right, keys)
    matched = [k for k in lidx if k in ridx]
    missing = [k for k in lidx if k not in ridx]
    extra = [k for k in ridx if k not in lidx]
    li = np.fromiter((lidx[k] for k in matched), dtype=np.int64, count=len(matched))
    ri = np.fromiter((ridx[k] for k in matched), dtype=np.int64, count=len(matched))

    common = [c for c in left_cols if c in right_cols and c not in keys]
    column_results: list[ColumnResult] = []
    surrogate_results: list[ColumnResult] = []
    row_has_diff = np.zeros(len(matched), dtype=bool)

    for col in common:
        rule = rules.get(col)
        if rule is None:
            rule = ColumnRule("rel", REL_DOUBLE) if (_has_float(left, col) or _has_float(right, col)) else ColumnRule()
        lv = left[col].to_numpy(dtype=object)[li]
        rv = right[col].to_numpy(dtype=object)[ri]
        classify = classifiers.get(col)
        n_mis = n_null = 0
        tolerated: dict[str, int] = {}
        max_abs: float | None = None
        max_rel: float | None = None
        unexplained_examples: list[tuple] = []
        tolerated_examples: list[tuple] = []
        for pos, (a, b) in enumerate(zip(lv, rv, strict=True)):
            if a is None and b is None:
                continue
            if a is None or b is None:
                ok, null_diff = False, True
            else:
                ok, d, r = compare_values(a, b, rule.mode, rule.tol)
                null_diff = False
                if d is not None:
                    max_abs = d if max_abs is None else max(max_abs, d)
                    max_rel = r if max_rel is None else max(max_rel, r)
            if ok:
                continue
            n_mis += 1
            n_null += int(null_diff)
            lab = classify(matched[pos], a, b) if classify else None
            if lab:
                tolerated[lab] = tolerated.get(lab, 0) + 1
                if len(tolerated_examples) < max_examples:
                    tolerated_examples.append((matched[pos], a, b))
            else:
                if not rule.surrogate:
                    row_has_diff[pos] = True
                if len(unexplained_examples) < max_examples:
                    unexplained_examples.append((matched[pos], a, b))
        result = ColumnResult(col, rule.mode, rule.tol, rule.surrogate, len(matched), n_mis, n_null, tolerated,
                              max_abs, max_rel, (unexplained_examples + tolerated_examples)[:max_examples])
        (surrogate_results if rule.surrogate else column_results).append(result)

    return Comparison(
        label=label, left_name=left_name, right_name=right_name, left_rows=len(left), right_rows=len(right),
        matched_rows=len(matched), keys=keys, missing_in_right=len(missing), extra_in_right=len(extra),
        missing_examples=missing[:max_examples], extra_examples=extra[:max_examples],
        duplicate_keys_left=ldup, duplicate_keys_right=rdup, columns_only_left=only_left,
        columns_only_right=only_right, columns=column_results, surrogate_columns=surrogate_results,
        rows_with_diff=int(row_has_diff.sum()),
    )


def display_value(column: str, value: Any, limit: int = 60) -> str:
    """Printable form of an example value; customer free text is replaced by its length."""
    if column in SENSITIVE_COLUMNS and isinstance(value, str):
        return f"<text, {len(value)} chars>"
    s = "NULL" if value is None else str(value)
    return s if len(s) <= limit else s[: limit - 3] + "..."


# ------------------------------------------------------------------ reference CSV


def _coerce(text: str, sample: Any) -> Any:
    if text == "":
        return None
    if isinstance(sample, bool):
        return text.strip().lower() == "true"
    if isinstance(sample, int):
        try:
            return int(text)
        except ValueError:
            return int(float(text))
    if isinstance(sample, float):
        return float(text)
    if isinstance(sample, Decimal):
        return Decimal(text)
    if isinstance(sample, datetime):
        return pd.Timestamp(text).to_pydatetime()
    if isinstance(sample, date):
        return date.fromisoformat(text)
    return text


def load_reference_csv(path: Path, template: pd.DataFrame) -> pd.DataFrame:
    """Read a tracked report CSV as text and coerce every column to the type the DuckDB query returned.

    Parsed with the ``csv`` module (not pandas) so keys such as ``4+`` and ``2016-09`` are never reinterpreted.
    """
    with Path(path).open(newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = [h.strip().lower() for h in next(reader)]
        rows = list(reader)
    samples: dict[str, Any] = {}
    for c in header:
        if c in template.columns:
            non_null = [v for v in template[c].tolist() if v is not None]
            samples[c] = non_null[0] if non_null else ""
    data = {c: pd.Series([_coerce(r[i], samples.get(c, "")) for r in rows], dtype=object) for i, c in enumerate(header)}
    return pd.DataFrame(data, columns=header)


# ------------------------------------------------------------------ running a check


@dataclass
class Side:
    """One backend: how to fetch, which SQL of a Check it runs, and how it renders shared templates."""

    name: str
    fetch: Fetcher
    sql_of: Callable[[Check], str]
    render: Callable[[str], str]


def duckdb_side(fetch: Fetcher, name: str = "duckdb") -> Side:
    return Side(name, fetch, lambda c: c.duckdb_sql, render_duckdb)


def snowflake_side(fetch: Fetcher, database: str = "RETAIL_OLIST", schema_prefix: str = "",
                   name: str = "snowflake") -> Side:
    return Side(name, fetch, lambda c: render_snowflake(c.snowflake_sql, database, schema_prefix),
                lambda sql: render_snowflake(sql, database, schema_prefix))


def _candidates(frame: pd.DataFrame) -> dict[Any, set]:
    out: dict[Any, set] = {}
    for oid, cand in zip(frame["order_id"].tolist(), frame["candidate"].tolist(), strict=True):
        out.setdefault(oid, set()).add(cand)
    return out


def _tie_classifiers(tie: TieBreak, left: Side, right: Side) -> tuple[dict[str, Classifier], TieBreakInfo]:
    lc = _candidates(left.fetch(left.render(tie.candidates_sql)))
    rc = _candidates(right.fetch(right.render(tie.candidates_sql)))
    cands: dict[Any, set] = {}
    for src in (lc, rc):
        for oid, s in src.items():
            cands.setdefault(oid, set()).update(s)
    ambiguous = {oid for oid, s in cands.items() if len(s) > 1}
    n_ambiguous = len(ambiguous)
    affected: set = set().union(*(cands[o] for o in ambiguous)) if ambiguous else set()
    info = TieBreakInfo(
        tie.name, len(ambiguous), tie.direct_column, tie.cascade_columns, 0, 0,
        note=(f"ambiguous orders: {left.name} {sum(1 for s in lc.values() if len(s) > 1)}, "
              f"{right.name} {sum(1 for s in rc.values() if len(s) > 1)}; tied values involved: {len(affected)}; "
              f"rows eligible for classification: {sum(1 for s in cands.values() if len(s) > 1 or s & affected)} "
              f"of {len(cands)}"))
    classifiers: dict[str, Classifier] = {}
    if tie.direct_column:
        def direct(key: tuple, a: Any, b: Any, _c=cands) -> str | None:
            s = _c.get(key[0])
            return TIE_BREAK if s and len(s) > 1 and a in s and b in s else None
        classifiers[tie.direct_column] = direct
    for col in tie.cascade_columns:
        if tie.cascade_row_level:
            def cascade(key: tuple, a: Any, b: Any, _c=cands, _aff=affected, _n=n_ambiguous) -> str | None:
                own = _c.get(key[0], set())
                if len(own) > 1:  # this order's own pick may have flipped: its category totals can be anything
                    return DOWNSTREAM
                # an unambiguous row has the same category on both sides; its running totals can only differ by the
                # ambiguous orders that moved between categories, so by at most their number
                if own & _aff and _is_num(a) and _is_num(b) and abs(float(a) - float(b)) <= _n:
                    return DOWNSTREAM
                return None
        else:
            def cascade(key: tuple, a: Any, b: Any, _n=n_ambiguous) -> str | None:
                return DOWNSTREAM if _n > 0 else None
        classifiers[col] = cascade
    return classifiers, info


def _compare_expected(check: Check, lf: pd.DataFrame, rf: pd.DataFrame) -> list[ExpectedResult]:
    def lookup(df: pd.DataFrame) -> dict[str, Any]:
        return dict(zip(df["metric"].tolist(), df["value"].tolist(), strict=True))

    lv, rv = lookup(lf), lookup(rf)
    out = []
    def ok(v: Any, want: Decimal) -> bool:
        return v is not None and compare_values(v, want, "exact", 0.0)[0]

    for metric, exp in check.expected.items():
        out.append(ExpectedResult(metric, exp.value, exp.source, lv.get(metric), rv.get(metric),
                                  ok(lv.get(metric), exp.value), ok(rv.get(metric), exp.value)))
    return out


def run_check(check: Check, left: Side, right: Side, *, reference_dir: Path | None = None) -> CheckResult:
    """Run one check: left vs right, then each side vs the tracked reference CSV, then documented constants."""
    res = CheckResult(check.name, check.group, check.description)
    t0 = time.perf_counter()
    try:
        lf = left.fetch(left.sql_of(check))
        rf = right.fetch(right.sql_of(check))

        classifiers: dict[str, Classifier] = {}
        for tie in check.tie_breaks:
            cls, info = _tie_classifiers(tie, left, right)
            classifiers.update(cls)
            res.tie_breaks.append(info)

        main = compare_frames(lf, rf, check.keys, check.rules, label=f"{left.name}_vs_{right.name}",
                              left_name=left.name, right_name=right.name, classifiers=classifiers)
        res.comparisons.append(main)
        for info in res.tie_breaks:
            if info.direct_column:
                info.n_direct = next((c.tolerated.get(TIE_BREAK, 0) for c in main.columns
                                      if c.column == info.direct_column), 0)
            info.n_downstream = sum(c.tolerated.get(DOWNSTREAM, 0) for c in main.columns
                                    if c.column in info.cascade_columns)

        if check.reference_csv and reference_dir is not None:
            ref = load_reference_csv(Path(reference_dir) / check.reference_csv, lf)
            for side, frame in ((left, lf), (right, rf)):
                res.comparisons.append(compare_frames(
                    frame, ref, check.keys, check.rules, label=f"{side.name}_vs_reference_csv",
                    left_name=side.name, right_name=check.reference_csv))
        if check.expected:
            res.expected = _compare_expected(check, lf, rf)
    except Exception as exc:  # noqa: BLE001 - a failing check must not stop the run; it is reported as ERROR
        first = (str(exc).strip().splitlines() or [""])[0]
        res.error = redact_secrets(f"{type(exc).__name__}: {first}")[:500]
    res.elapsed_s = time.perf_counter() - t0
    return res


def run_checks(checks: Sequence[Check], left: Side, right: Side, *, reference_dir: Path | None = None,
               progress: Callable[[CheckResult], None] | None = None) -> list[CheckResult]:
    results = []
    for chk in checks:
        r = run_check(chk, left, right, reference_dir=reference_dir)
        results.append(r)
        if progress:
            progress(r)
    return results
