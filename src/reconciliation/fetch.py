"""Fetchers: run one SELECT on one backend and return a DataFrame of plain Python values.

The comparison code only needs a ``Fetcher`` (a callable ``sql -> DataFrame``), so tests and the offline self-test
inject in-memory DuckDB fetchers and never touch Snowflake. Results are fetched with ``fetchall()`` and a cursor
``description`` rather than ``DataFrame()`` helpers, because those turn DECIMAL(12,2) money into float64 and would make an
"exact money" comparison a float comparison. Every column becomes dtype ``object`` holding Python ``Decimal`` /
``int`` / ``float`` / ``bool`` / ``str`` / ``date`` / ``datetime`` / ``None`` (column names lower-cased, NaN -> None).

Snowflake access is lazy (the connector is imported inside ``SnowflakeFetcher``) and read-only by construction:
``assert_read_only`` rejects anything that is not a single SELECT / WITH statement. UNVERIFIED: the Snowflake path has
never been run against a live account in this repository state.
"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

Fetcher = Callable[[str], pd.DataFrame]

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|merge|create|drop|alter|truncate|copy|grant|revoke|call|execute|undrop)\b",
    re.IGNORECASE,
)


class ReadOnlyViolation(ValueError):
    """Raised when a statement given to a fetcher is not a single read-only SELECT."""


def _strip_sql_noise(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return re.sub(r"'(?:[^']|'')*'", "''", sql)  # string literals -> empty literal


def assert_read_only(sql: str) -> None:
    """Allow exactly one SELECT / WITH statement. Raises ReadOnlyViolation otherwise."""
    body = _strip_sql_noise(sql).strip().rstrip(";").strip()
    if not body:
        raise ReadOnlyViolation("empty statement")
    if ";" in body:
        raise ReadOnlyViolation("more than one statement")
    first = body.split(None, 1)[0].lower().lstrip("(")
    if first not in {"select", "with"}:
        raise ReadOnlyViolation(f"statement starts with {first!r}, only SELECT / WITH is allowed")
    bad = _FORBIDDEN.search(body)
    if bad:
        raise ReadOnlyViolation(f"forbidden keyword {bad.group(1)!r} in statement")


def canon_value(v: Any) -> Any:
    """Plain-Python canonical form of one fetched value (NaN/NaT -> None, numpy scalars -> Python)."""
    if v is None:
        return None
    try:
        import numpy as np  # local: numpy is a pandas dependency
        if isinstance(v, np.bool_):
            return bool(v)
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            v = float(v)
    except ImportError:  # pragma: no cover
        pass
    if isinstance(v, float):
        return None if math.isnan(v) else v
    if v is pd.NaT:
        return None
    if isinstance(v, pd.Timestamp):
        return v.to_pydatetime()
    return v


def frame_from_rows(columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> pd.DataFrame:
    """DataFrame of dtype=object columns with lower-cased names."""
    names = [str(c).lower() for c in columns]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate column names after lower-casing: {names}")
    data = {n: pd.Series([canon_value(r[i]) for r in rows], dtype=object) for i, n in enumerate(names)}
    return pd.DataFrame(data, columns=names)


def frame_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise an existing DataFrame the same way (used for CSV/test input)."""
    return frame_from_rows(list(df.columns), df.itertuples(index=False, name=None))


# ---------------------------------------------------------------- DuckDB


class DuckDBFetcher:
    """Read-only DuckDB. ``source`` is a database path (opened read_only=True) or an open connection (not closed)."""

    def __init__(self, source: Any, name: str = "duckdb") -> None:
        import duckdb

        self.name = name
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"DuckDB file not found: {path}")
            self._con = duckdb.connect(str(path), read_only=True)
            self._owns = True
            self.description = f"duckdb file {path.name} (read-only)"
        else:
            self._con = source
            self._owns = False
            self.description = "duckdb connection"

    def __call__(self, sql: str) -> pd.DataFrame:
        assert_read_only(sql)
        cur = self._con.execute(sql)
        cols = [d[0] for d in cur.description]
        return frame_from_rows(cols, cur.fetchall())

    def close(self) -> None:
        if self._owns:
            self._con.close()


# ---------------------------------------------------------------- Snowflake


@dataclass(frozen=True)
class SnowflakeSettings:
    account: str
    user: str
    private_key_path: str
    passphrase_set: bool
    role: str
    warehouse: str
    database: str
    schema_prefix: str  # "" for prod; "<DBT_DEV_SUFFIX>_" for dev

    @property
    def account_redacted(self) -> str:
        return redact_account(self.account)


def redact_account(account: str) -> str:
    """Keep only the first and last two characters of an account locator."""
    a = account.strip()
    if len(a) <= 4:
        return "***"
    return f"{a[:2]}***{a[-2:]}"


def resolve_snowflake_settings(env: Mapping[str, str] | None = None, *, database: str | None = None,
                               schema_suffix: str | None = None) -> SnowflakeSettings:
    """Resolve settings from environment variables; raises with the *names* of missing variables only."""
    env = os.environ if env is None else env
    missing = [n for n in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH") if not env.get(n)]
    if missing:
        raise RuntimeError("missing environment variables: " + ", ".join(missing))
    db = database or env.get("RETAIL_SF_DATABASE") or "RETAIL_OLIST"
    suffix = schema_suffix if schema_suffix is not None else env.get("DBT_DEV_SUFFIX", "")
    for label, value in (("database", db), ("schema suffix", suffix)):
        if value and not _IDENT.match(value):
            raise ValueError(f"{label} {value!r} is not a plain identifier")
    return SnowflakeSettings(
        account=env["SNOWFLAKE_ACCOUNT"],
        user=env["SNOWFLAKE_USER"],
        private_key_path=env["SNOWFLAKE_PRIVATE_KEY_PATH"],
        passphrase_set=bool(env.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")),
        role=env.get("RETAIL_SF_ROLE") or "RETAIL_TRANSFORMER",
        warehouse=env.get("RETAIL_SF_WAREHOUSE") or "RETAIL_WH",
        database=db,
        schema_prefix=f"{suffix.upper()}_" if suffix else "",
    )


def redact_secrets(text: str, env: Mapping[str, str] | None = None) -> str:
    """Remove the account locator and user name from an error message before it reaches a report or the console."""
    env = os.environ if env is None else env
    for name in ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER"):
        value = env.get(name)
        if value:
            text = text.replace(value, "<redacted>")
    return text


class SnowflakeFetcher:
    """Key-pair authenticated, SELECT-only Snowflake fetcher. UNVERIFIED against a live account."""

    def __init__(self, settings: SnowflakeSettings, env: Mapping[str, str] | None = None) -> None:
        self.settings = settings
        self.name = "snowflake"
        env = os.environ if env is None else env
        try:
            import snowflake.connector
            from cryptography.hazmat.primitives import serialization
        except ImportError as exc:  # pragma: no cover - not installed in the offline venv
            raise RuntimeError("snowflake-connector-python and cryptography are required for a live run "
                               f"({exc.name} is not installed)") from exc
        passphrase = env.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        key = serialization.load_pem_private_key(
            Path(settings.private_key_path).read_bytes(),
            password=passphrase.encode() if passphrase else None,
        )
        der = key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        self._con = snowflake.connector.connect(
            account=settings.account, user=settings.user, private_key=der, role=settings.role,
            warehouse=settings.warehouse, database=settings.database,
            session_parameters={"QUERY_TAG": "retail-reconciliation (read-only)"},
        )
        self.description = (f"snowflake account {settings.account_redacted}, database {settings.database}, "
                            f"role {settings.role}, warehouse {settings.warehouse}")

    def __call__(self, sql: str) -> pd.DataFrame:
        assert_read_only(sql)
        cur = self._con.cursor()
        try:
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            return frame_from_rows(cols, cur.fetchall())
        finally:
            cur.close()

    def close(self) -> None:
        self._con.close()
