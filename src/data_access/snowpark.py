"""DataAccess look-alike over a Snowpark session, for code that runs inside Snowflake (Notebooks in Workspaces).

    from data_access.snowpark import from_active_session
    db = from_active_session()                 # the notebook's own session: no key, no password, no env vars
    df = ldb.load(db)                          # same code path as the laptop's Snowflake backend

Inside Snowflake there is no key pair to connect with (src/data_access/backend.py needs one); the notebook already has
an authenticated session. This wraps it with the same small interface the modelling code duck-types on: `.backend`,
`.read_sql(sql, params)` (results normalised exactly like the laptop path) and `.execute(sql, params)`. `.raw` is the
session's connector connection and `.target` describes database, role and warehouse, so writeback.py also works.
Importing this module never imports Snowflake; close() leaves the notebook's session open.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import pandas as pd

from .backend import DEFAULT_DATABASE, SnowflakeTarget
from .normalise import normalise_frame


class SnowparkAccess:
    backend = "snowflake"

    def __init__(self, session: Any, *, database: str | None = DEFAULT_DATABASE) -> None:
        self.session = session
        if database:
            session.use_database(database)
        self.target = SnowflakeTarget(
            account=_clean(session.get_current_account()),
            database=_clean(session.get_current_database()) or (database or ""),
            role=_clean(session.get_current_role()),
            warehouse=_clean(session.get_current_warehouse()),
        )

    @property
    def raw(self) -> Any:
        """The connector connection under the session (used by writeback.py for PUT/COPY)."""
        return self.session.connection

    def _query(self, sql: str, params: Sequence[Any] | None):
        return self.session.sql(sql, params=list(params)) if params else self.session.sql(sql)

    def read_sql(self, sql: str, params: Sequence[Any] | None = None) -> pd.DataFrame:
        return normalise_frame(self._query(sql, params).to_pandas())

    def execute(self, sql: str, params: Sequence[Any] | None = None) -> None:
        self._query(sql, params).collect()

    def close(self) -> None:
        """The notebook owns its session; do not close it."""

    def __enter__(self) -> SnowparkAccess:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


def _clean(value: Any) -> str:
    """Snowpark returns quoted identifiers such as '"RETAIL_OLIST"'; keep the bare name."""
    return str(value or "").strip('"')


def from_active_session(database: str | None = DEFAULT_DATABASE) -> SnowparkAccess:
    from snowflake.snowpark.context import get_active_session  # only available inside Snowflake

    return SnowparkAccess(get_active_session(), database=database)
