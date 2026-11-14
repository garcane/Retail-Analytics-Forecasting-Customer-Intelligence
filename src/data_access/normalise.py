"""Make Snowflake result frames look like the DuckDB ones the downstream code was written against.

`normalise_frame` is generic (no schema needed):
  - column names are lower-cased (Snowflake upper-cases unquoted identifiers);
  - Decimal columns (NUMBER with scale) become float64;
  - columns of Python ints with NULLs become nullable Int64;
  - columns of Python bools (with or without NULLs) become bool / nullable boolean;
  - TIMESTAMP_NTZ and DATE values become datetime64[ns] (timezone-aware columns are left alone).

`conform_frame` applies the safe, lossless casts a dataset schema asks for (see datasets.py): an integer column that
arrived as float because of NULLs becomes nullable Int64 (or int64 when there are none), numbers become float64,
text-like timestamps are parsed. It never invents data: anything it cannot convert losslessly is left as it is so
`validate_frame` reports it.

Schema "kinds": str, int, float, bool, datetime. A `float` column accepts any numeric dtype; an `int` column needs an
integer dtype.

Deviation from the DuckDB frames, on purpose: DuckDB hands pandas 3 `datetime64[us]`; the Snowflake path produces
`datetime64[ns]`. Both are accepted by validate_frame (kind "datetime" is any datetime64 unit).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Mapping
from decimal import Decimal

import pandas as pd
from pandas.api import types as pt

KINDS = ("str", "int", "float", "bool", "datetime")


def _non_null(s: pd.Series) -> list:
    return [v for v in s.tolist() if v is not None and v is not pd.NA and v is not pd.NaT
            and not (isinstance(v, float) and pd.isna(v))]


def _normalise_object_column(s: pd.Series) -> pd.Series:
    values = _non_null(s)
    if not values:
        return s
    if all(isinstance(v, Decimal) for v in values):
        return pd.to_numeric(s.map(lambda v: float(v) if isinstance(v, Decimal) else float("nan")), errors="coerce"
                             ).astype("float64")
    if all(isinstance(v, bool) for v in values):
        return s.astype("boolean") if len(values) != len(s) else s.astype("bool")
    if all(isinstance(v, int) and not isinstance(v, bool) for v in values):
        return s.astype("Int64")
    if all(isinstance(v, (dt.datetime, dt.date)) for v in values):
        if any(getattr(v, "tzinfo", None) is not None for v in values):
            return s
        return pd.to_datetime(s).astype("datetime64[ns]")
    return s


def normalise_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).lower() for c in out.columns]
    for col in out.columns:
        s = out[col]
        if pt.is_datetime64_dtype(s.dtype) and not isinstance(s.dtype, pd.DatetimeTZDtype):
            if s.dtype != "datetime64[ns]":
                out[col] = s.astype("datetime64[ns]")
        elif s.dtype == object:
            out[col] = _normalise_object_column(s)
    return out


def _to_int(s: pd.Series) -> pd.Series:
    if pt.is_integer_dtype(s.dtype):
        return s
    num = pd.to_numeric(s, errors="raise")
    notna = num.dropna()
    if not (notna == notna.round()).all():
        return s  # not integral: leave it for validate_frame to flag
    return num.astype("Int64") if num.isna().any() else num.astype("int64")


def _conform_column(s: pd.Series, kind: str) -> pd.Series:
    if kind == "int":
        return _to_int(s)
    if kind == "float":
        return s if pt.is_bool_dtype(s.dtype) else pd.to_numeric(s, errors="raise").astype("float64")
    if kind == "datetime":
        return s if pt.is_datetime64_any_dtype(s.dtype) else pd.to_datetime(s, errors="raise")
    if kind == "bool":
        if pt.is_bool_dtype(s.dtype):
            return s
        return s.astype("boolean") if s.isna().any() else s.astype("bool")
    return s


def conform_frame(df: pd.DataFrame, schema: Mapping[str, str]) -> pd.DataFrame:
    """Reorder to the schema's column order (extras last) and apply lossless casts; unconvertible columns are kept."""
    present = [c for c in schema if c in df.columns]
    out = df[present + [c for c in df.columns if c not in schema]].copy()
    for col in present:
        try:
            out[col] = _conform_column(out[col], schema[col])
        except (ValueError, TypeError, OverflowError):
            pass  # validate_frame will report the column
    return out
