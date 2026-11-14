"""Backend selection and connection wrappers (DuckDB reference warehouse or Snowflake).

    DATA_BACKEND=duckdb|snowflake   (default duckdb)
    DUCKDB_PATH=warehouse.duckdb    (relative paths resolve against the repository root, like the existing scripts)

Snowflake uses key-pair authentication from the environment only (nothing is read from a file in this repository,
there is no .env loading here):

    SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PRIVATE_KEY_PATH, SNOWFLAKE_PRIVATE_KEY_PASSPHRASE (optional)
    RETAIL_SF_ROLE (default RETAIL_TRANSFORMER), RETAIL_SF_WAREHOUSE (default RETAIL_WH),
    RETAIL_SF_DATABASE (default RETAIL_OLIST)

A live Snowflake connection needs an explicit `confirm=True` (or RETAIL_SF_CONFIRM=1). Before anything else happens the
resolved account / database / role / warehouse are printed to stderr (never the user, key path or passphrase), and the
gate is checked before the connector is imported or the key file is opened.

The wrapper exposes the same small surface for both backends: `backend`, `read_sql(sql, params)`, `execute(sql,
params)`, `raw`, `close()`. Parameters use the `?` placeholder on both backends (the Snowflake connection is opened
with paramstyle="qmark").
"""

from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

import pandas as pd

from .normalise import normalise_frame

ROOT = Path(__file__).resolve().parents[2]

BACKENDS = ("duckdb", "snowflake")
DEFAULT_BACKEND = "duckdb"
DEFAULT_DUCKDB_PATH = "warehouse.duckdb"
DEFAULT_ROLE = "RETAIL_TRANSFORMER"
DEFAULT_WAREHOUSE = "RETAIL_WH"
DEFAULT_DATABASE = "RETAIL_OLIST"
REQUIRED_SNOWFLAKE_ENV = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH")


class DataAccessError(Exception):
    """Base class for the errors raised by this package."""


class InvalidBackendError(DataAccessError, ValueError):
    """DATA_BACKEND / backend= is not one of duckdb, snowflake."""


class MissingConfigError(DataAccessError):
    """Required environment variables are not set (names only are reported, never values)."""


class ConfirmationRequired(DataAccessError):
    """A live Snowflake connection was requested without confirm=True / RETAIL_SF_CONFIRM=1."""


def resolve_backend(backend: str | None = None) -> str:
    """Explicit argument, else DATA_BACKEND, else duckdb. Raises InvalidBackendError for anything else."""
    raw = backend if backend is not None else os.environ.get("DATA_BACKEND", "")
    value = (raw or "").strip().lower() or DEFAULT_BACKEND
    if value not in BACKENDS:
        raise InvalidBackendError(f"Unknown data backend {raw!r}; expected one of {', '.join(BACKENDS)}.")
    return value


def resolve_duckdb_path(path: str | os.PathLike | None = None) -> Path:
    raw = path if path is not None else os.environ.get("DUCKDB_PATH") or DEFAULT_DUCKDB_PATH
    p = Path(raw)
    return p if p.is_absolute() else ROOT / p


@dataclass(frozen=True)
class SnowflakeTarget:
    """What a live connection would hit. Deliberately holds no user name, key path or passphrase."""

    account: str
    database: str
    role: str
    warehouse: str

    def describe(self) -> str:
        return (f"Snowflake target: account={self.account} database={self.database} "
                f"role={self.role} warehouse={self.warehouse}")


def resolve_snowflake_target(env: dict[str, str] | None = None) -> SnowflakeTarget:
    env = os.environ if env is None else env
    account = env.get("SNOWFLAKE_ACCOUNT", "").strip()
    if not account:
        raise MissingConfigError("SNOWFLAKE_ACCOUNT is not set.")
    return SnowflakeTarget(
        account=account,
        database=env.get("RETAIL_SF_DATABASE", "").strip() or DEFAULT_DATABASE,
        role=env.get("RETAIL_SF_ROLE", "").strip() or DEFAULT_ROLE,
        warehouse=env.get("RETAIL_SF_WAREHOUSE", "").strip() or DEFAULT_WAREHOUSE,
    )


def _confirmed(confirm: bool) -> bool:
    return bool(confirm) or os.environ.get("RETAIL_SF_CONFIRM", "").strip() == "1"


class DataAccess:
    """Thin wrapper over a DuckDB or Snowflake connection with a common read_sql()."""

    def __init__(self, backend: str, raw: Any, *, target: SnowflakeTarget | None = None) -> None:
        self.backend = backend
        self.raw = raw
        self.target = target

    def _duck(self, sql: str, params: Sequence[Any] | None):
        return self.raw.execute(sql, list(params)) if params else self.raw.execute(sql)

    @staticmethod
    def _run(cur: Any, sql: str, params: Sequence[Any] | None) -> None:
        if params:
            cur.execute(sql, tuple(params))
        else:
            cur.execute(sql)

    # -- reading ---------------------------------------------------------------------------------------------
    def read_sql(self, sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
        """Run a query and return a DataFrame. DuckDB frames are returned untouched; Snowflake frames are normalised."""
        if self.backend == "duckdb":
            return self._duck(sql, params).df()
        cur = self.raw.cursor()
        try:
            self._run(cur, sql, params)
            if hasattr(cur, "fetch_pandas_all"):
                df = cur.fetch_pandas_all()
            else:
                df = pd.DataFrame(cur.fetchall(), columns=[d[0] for d in cur.description])
        finally:
            cur.close()
        return normalise_frame(df)

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        """Run a statement that returns no frame (DDL / DML)."""
        if self.backend == "duckdb":
            self._duck(sql, params)
            return
        cur = self.raw.cursor()
        try:
            self._run(cur, sql, params)
        finally:
            cur.close()

    # -- lifecycle -------------------------------------------------------------------------------------------
    def close(self) -> None:
        self.raw.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def wrap_duckdb(con: Any) -> DataAccess:
    """Wrap an already-open DuckDB connection (e.g. the test warehouse) without changing it."""
    return DataAccess("duckdb", con)


def is_data_access(obj: Any) -> bool:
    """True for a DataAccess wrapper (and look-alikes); False for a raw DuckDB connection."""
    return getattr(obj, "backend", None) in BACKENDS and callable(getattr(obj, "read_sql", None))


def _load_snowflake_connector():  # isolated so tests can substitute a fake
    from snowflake import connector

    return connector


def _load_private_key_der(path: str, passphrase: str | None) -> bytes:  # isolated so tests need no cryptography
    from cryptography.hazmat.primitives import serialization

    data = Path(path).read_bytes()
    key = serialization.load_pem_private_key(data, password=passphrase.encode() if passphrase else None)
    return key.private_bytes(
        encoding=serialization.Encoding.DER,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )


def _connect_snowflake(*, confirm: bool) -> DataAccess:
    target = resolve_snowflake_target()
    missing = [n for n in REQUIRED_SNOWFLAKE_ENV if not os.environ.get(n, "").strip()]
    if missing:
        raise MissingConfigError("Missing environment variables for Snowflake: " + ", ".join(missing))
    print(target.describe(), file=sys.stderr)
    if not _confirmed(confirm):
        raise ConfirmationRequired(
            f"Refusing to open a live connection to {target.describe()}. "
            "Pass confirm=True (or set RETAIL_SF_CONFIRM=1) once you have checked the target above."
        )
    passphrase = os.environ.get("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE") or None
    der = _load_private_key_der(os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"], passphrase)
    connector = _load_snowflake_connector()
    raw = connector.connect(
        account=target.account,
        user=os.environ["SNOWFLAKE_USER"],
        private_key=der,
        role=target.role,
        warehouse=target.warehouse,
        database=target.database,
        paramstyle="qmark",
        session_parameters={"QUERY_TAG": "retail_data_access"},
    )
    return DataAccess("snowflake", raw, target=target)


def connect(backend: str | None = None, *, confirm: bool = False, duckdb_path: str | os.PathLike | None = None,
            read_only: bool = True) -> DataAccess:
    """Open the configured backend. Default is the DuckDB warehouse, opened read-only."""
    chosen = resolve_backend(backend)
    if chosen == "snowflake":
        return _connect_snowflake(confirm=confirm)
    import duckdb

    path = resolve_duckdb_path(duckdb_path)
    if not path.exists():
        raise FileNotFoundError(f"DuckDB warehouse not found at {path}; build it or set DUCKDB_PATH.")
    return DataAccess("duckdb", duckdb.connect(str(path), read_only=read_only))
