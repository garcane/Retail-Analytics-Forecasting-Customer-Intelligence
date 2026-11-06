"""Backend-neutral data access for the Python modelling code (DuckDB reference warehouse or Snowflake).

    from data_access import connect, datasets
    with connect() as db:                      # DATA_BACKEND=duckdb by default
        weekly = datasets.weekly_series(db)

Importing this package never imports the Snowflake connector and never opens a connection. See backend.py (selection,
auth, confirmation gate), normalise.py, datasets.py (tiers and schemas) and writeback.py (opt-in ML.* write-back).
"""

from . import datasets, writeback
from .backend import (
    ConfirmationRequired,
    DataAccess,
    DataAccessError,
    InvalidBackendError,
    MissingConfigError,
    connect,
    is_data_access,
    resolve_backend,
    wrap_duckdb,
)
from .datasets import SchemaError, validate_frame
from .normalise import conform_frame, normalise_frame

__all__ = [
    "ConfirmationRequired", "DataAccess", "DataAccessError", "InvalidBackendError", "MissingConfigError",
    "SchemaError", "conform_frame", "connect", "datasets", "is_data_access", "normalise_frame", "resolve_backend",
    "validate_frame", "wrap_duckdb", "writeback",
]
