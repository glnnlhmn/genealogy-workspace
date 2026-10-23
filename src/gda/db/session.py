"""Path: src/gda/db/session.py

Connection lifecycle, transaction orchestration, and PRAGMA management for GDA DB.

Operational Role:
    Provides DatabaseSessionManager to govern SQLite connection handles, enforce
    mandatory PRAGMA policies (WAL, foreign_keys=ON, busy_timeout=5000, NORMAL sync),
    manage atomic write transactions via BEGIN IMMEDIATE, support nested savepoints,
    and translate driver-level SQLite errors into the typed GDA database exception taxonomy.

Classes:
    DatabaseSessionManager: Primary database session coordinator and context provider.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from gda.core.config import DatabaseConfig
from gda.core.introspectable import IntrospectableMixin
from gda.db.exceptions import (
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationalError,
    TransactionError,
)

__version__ = "1.0.0+build.5"


class DatabaseSessionManager(IntrospectableMixin):
    """Orchestrate SQLite connections, transaction boundaries, and PRAGMA policies."""

    def __init__(
        self,
        db_path: Path | str | None = None,
        config: DatabaseConfig | None = None,
    ) -> None:
        """Initialize DatabaseSessionManager.

        Args:
            db_path: Optional explicit database path or ':memory:'. Overrides config if given.
            config: Optional DatabaseConfig instance. Defaults to default DatabaseConfig().
        """
        self._config = config or DatabaseConfig()
        if db_path is not None:
            self._db_path: Path | str = (
                db_path
                if str(db_path) in (":memory:", "file::memory:")
                else Path(db_path)
            )
        else:
            self._db_path = self._config.db_path

        self._savepoint_depth: int = 0

    @property
    def db_path(self) -> Path | str:
        """Return the active database target path or memory identifier."""
        return self._db_path

    @property
    def is_in_memory(self) -> bool:
        """Indicate whether the active target is an in-memory database."""
        return str(self._db_path) in (":memory:", "file::memory:")

    @property
    def config(self) -> DatabaseConfig:
        """Return the active DatabaseConfig instance."""
        return self._config

    def _apply_pragmas(self, conn: sqlite3.Connection) -> None:
        """Apply mandatory SQLite PRAGMAs to configure concurrency and integrity.

        Args:
            conn: Newly acquired sqlite3.Connection instance.
        """
        cursor = conn.cursor()
        try:
            if not self.is_in_memory:
                cursor.execute(f"PRAGMA journal_mode = {self._config.journal_mode};")

            fk_directive = "ON" if self._config.foreign_keys else "OFF"
            cursor.execute(f"PRAGMA foreign_keys = {fk_directive};")
            cursor.execute(f"PRAGMA busy_timeout = {self._config.busy_timeout};")
            cursor.execute(f"PRAGMA synchronous = {self._config.synchronous};")
        finally:
            cursor.close()

    def create_connection(self) -> sqlite3.Connection:
        """Establish and configure a fresh raw SQLite connection.

        Returns:
            Configured sqlite3.Connection with Row row-factory and applied PRAGMAs.

        Raises:
            DatabaseConnectionError: If connection instantiation or PRAGMA setup fails.
        """
        target = str(self._db_path)
        try:
            if not self.is_in_memory and isinstance(self._db_path, Path):
                self._db_path.parent.mkdir(parents=True, exist_ok=True)

            conn = sqlite3.connect(
                target,
                timeout=float(self._config.busy_timeout) / 1000.0,
                autocommit=True,
            )
            conn.row_factory = sqlite3.Row
            self._apply_pragmas(conn)
            return conn
        except sqlite3.Error as err:
            self._translate_and_raise(
                err,
                default_msg=f"Failed to establish database connection to: {target}",
                fallback_cls=DatabaseConnectionError,
            )

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection]:
        """Provide a managed connection context, closing the connection on exit.

        Yields:
            Configured sqlite3.Connection instance.
        """
        conn = self.create_connection()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(
        self, conn: sqlite3.Connection | None = None
    ) -> Generator[sqlite3.Connection]:
        """Execute an atomic transaction boundary with immediate locking or nested savepoints.

        Args:
            conn: Optional existing sqlite3.Connection. If None, acquires a fresh connection.

        Yields:
            Active sqlite3.Connection bound to the transaction.

        Raises:
            TransactionError: If transaction execution, savepoint, or commit fails.
            ConstraintViolationError: If relational or unique constraints fail.
            ConnectionTimeoutError: If lock contention triggers timeout.
            DatabaseOperationalError: On driver operational faults.
        """
        owns_connection = conn is None
        active_conn = self.create_connection() if owns_connection else conn
        assert active_conn is not None

        is_root = self._savepoint_depth == 0
        savepoint_name = f"sp_{self._savepoint_depth}"

        try:
            self._savepoint_depth += 1
            if is_root:
                active_conn.execute("BEGIN IMMEDIATE;")
            else:
                active_conn.execute(f"SAVEPOINT {savepoint_name};")

            yield active_conn

            if is_root:
                active_conn.execute("COMMIT;")
            else:
                active_conn.execute(f"RELEASE SAVEPOINT {savepoint_name};")

        except Exception as exc:
            try:
                if is_root:
                    active_conn.execute("ROLLBACK;")
                else:
                    active_conn.execute(f"ROLLBACK TO SAVEPOINT {savepoint_name};")
            except Exception:
                pass

            if isinstance(exc, sqlite3.Error):
                self._translate_and_raise(
                    exc,
                    default_msg="Transaction aborted due to driver error.",
                    fallback_cls=TransactionError,
                )
            raise
        finally:
            self._savepoint_depth -= 1
            if owns_connection:
                active_conn.close()

    @staticmethod
    def _translate_and_raise(
        err: sqlite3.Error,
        default_msg: str,
        fallback_cls: type[DatabaseError],
        details: dict[str, Any] | None = None,
    ) -> None:
        """Map raw sqlite3 driver errors into the typed GDA database exception taxonomy.

        Args:
            err: Caught sqlite3.Error instance.
            default_msg: Contextual descriptive fallback message.
            fallback_cls: Target fallback class if specific sub-matching does not apply.
            details: Optional diagnostic dictionary to merge with driver info.

        Raises:
            ConnectionTimeoutError: When lock contention triggers a busy error.
            ConstraintViolationError: When relational or unique constraints are breached.
            DatabaseOperationalError: When SQL syntax or runtime operations fail.
            DatabaseError: General persistence failure fallback.
        """
        err_msg = str(err)
        err_type = type(err).__name__
        diag: dict[str, Any] = {"driver_error": err_type, "driver_message": err_msg}
        if details:
            diag.update(details)

        if isinstance(err, sqlite3.OperationalError):
            if "locked" in err_msg.lower() or "busy" in err_msg.lower():
                raise ConnectionTimeoutError(
                    message=f"Database lock contention: {err_msg}",
                    details=diag,
                ) from err
            raise DatabaseOperationalError(
                message=f"Database operational failure: {err_msg}",
                details=diag,
            ) from err

        if isinstance(err, sqlite3.IntegrityError):
            raise ConstraintViolationError(
                message=f"Database constraint violation: {err_msg}",
                details=diag,
            ) from err

        raise fallback_cls(
            message=f"{default_msg} Details: {err_msg}",
            details=diag,
        ) from err
