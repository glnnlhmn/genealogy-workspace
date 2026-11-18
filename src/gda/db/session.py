"""Path: src/gda/db/session.py

SQLite connection lifecycle and atomic transaction management for GDA.

Provides the DatabaseSessionManager class, enforcing WAL journal mode, foreign key
integrity, busy timeouts, and atomic transaction / savepoint boundaries. Consumes
DatabaseConfig and AppConfig from gda.core.config as the single source of truth
for connection strings, environment database targets, and PRAGMA settings, and
translates low-level sqlite3 exceptions into the canonical gda.db.exceptions hierarchy.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import NoReturn

from gda.core.config import AppConfig, DatabaseConfig
from gda.core.introspectable import IntrospectableMixin
from gda.db.exceptions import (
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationalError,
    TransactionError,
)
from gda.io.atomic import AtomicWriter

__version__ = "1.0.0+build.9"

__all__ = [
    "DatabaseSessionManager",
]


class DatabaseSessionManager(IntrospectableMixin):
    """Manages SQLite connections, PRAGMA enforcement, and nested transactions.

    Supports both physical disk databases (with automatic parent directory creation
    and WAL mode) and ephemeral in-memory databases (`:memory:`). All configuration
    and connection URI metadata is sourced from gda.core.config.DatabaseConfig.
    """

    def __init__(
        self,
        db_path: Path | str | None = None,
        config: DatabaseConfig | AppConfig | None = None,
        *,
        env_name: str | None = None,
        root_path: Path | str | None = None,
    ) -> None:
        """Initialize the session manager with path, config, or environment settings.

        Args:
            db_path: Explicit path to SQLite database file or ':memory:'.
                Overrides config.db_path if provided.
            config: DatabaseConfig or AppConfig instance. If omitted and env_name is
                provided, loads environment configuration via AppConfig.for_environment().
            env_name: Optional environment key ('DEV', 'TEST', 'STAGING', 'PROD')
                resolved from pyproject.toml via AppConfig.for_environment().
            root_path: Optional workspace root path when resolving env_name.
        """
        if isinstance(config, AppConfig):
            base_cfg = config.database
        elif isinstance(config, DatabaseConfig):
            base_cfg = config
        elif env_name is not None:
            app_cfg = AppConfig.for_environment(env_name, root_path=root_path)
            base_cfg = app_cfg.database
        else:
            base_cfg = DatabaseConfig()

        if db_path is not None:
            normalized = DatabaseConfig.normalize_db_path(db_path)
            base_cfg = base_cfg.model_copy(update={"db_path": normalized})

        self._config: DatabaseConfig = base_cfg
        self._db_path: Path | str = self._config.db_path
        self._savepoint_counter: int = 0

    @property
    def db_path(self) -> Path | str:
        """Return the resolved database path or ':memory:' identifier."""
        return self._db_path

    @property
    def config(self) -> DatabaseConfig:
        """Return the active DatabaseConfig governing this session manager."""
        return self._config

    @property
    def is_in_memory(self) -> bool:
        """Indicate whether the target database is an in-memory instance."""
        return self._config.is_in_memory

    @property
    def connection_string(self) -> str:
        """Return the canonical connection URI string from DatabaseConfig."""
        return self._config.connection_string

    def _ensure_parent_directory(self) -> None:
        """Ensure parent directory exists on disk for file-backed databases."""
        if not self.is_in_memory:
            target = Path(self._db_path)
            AtomicWriter.ensure_directory(target.parent)

    def _apply_pragmas(self, conn: sqlite3.Connection) -> None:
        """Apply mandatory GDA concurrency and integrity PRAGMAs to a connection."""
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA busy_timeout = {self._config.busy_timeout};")
            fk_state = "ON" if self._config.foreign_keys else "OFF"
            cursor.execute(f"PRAGMA foreign_keys = {fk_state};")
            cursor.execute(f"PRAGMA synchronous = {self._config.synchronous};")
            if not self.is_in_memory:
                cursor.execute(f"PRAGMA journal_mode = {self._config.journal_mode};")
        finally:
            cursor.close()

    def _translate_and_raise(self, exc: sqlite3.Error, context: str) -> NoReturn:
        """Translate a raw sqlite3.Error into the canonical gda.db.exceptions hierarchy."""
        msg = str(exc)
        lower_msg = msg.lower()
        details = {"db_path": str(self._db_path), "context": context, "driver_error": msg}

        if isinstance(exc, sqlite3.IntegrityError):
            raise ConstraintViolationError(
                message=f"Integrity constraint violated during {context}: {msg}",
                details=details,
            ) from exc

        if isinstance(exc, sqlite3.OperationalError):
            if "locked" in lower_msg or "busy" in lower_msg:
                raise ConnectionTimeoutError(
                    message=f"Database locked or busy during {context}: {msg}",
                    details=details,
                ) from exc
            raise DatabaseOperationalError(
                message=f"Operational error during {context}: {msg}",
                details=details,
            ) from exc

        if context == "connection":
            raise DatabaseConnectionError(
                message=f"Failed to connect to database '{self._db_path}': {msg}",
                details=details,
            ) from exc

        raise TransactionError(
            message=f"Database error during {context}: {msg}",
            details=details,
        ) from exc

    def connect(self) -> sqlite3.Connection:
        """Open and configure a new SQLite connection with Row factory and PRAGMAs.

        Returns:
            Configured sqlite3.Connection in manual transaction control mode (autocommit=True).

        Raises:
            DatabaseConnectionError: If connection or directory creation fails.
            ConnectionTimeoutError: If pragma application times out under lock contention.
            DatabaseOperationalError: If pragma execution fails.
        """
        try:
            self._ensure_parent_directory()
            timeout_sec = self._config.busy_timeout / 1000.0
            conn = sqlite3.connect(
                str(self._db_path),
                timeout=timeout_sec,
                autocommit=True,
            )
            conn.row_factory = sqlite3.Row
            self._apply_pragmas(conn)
            return conn
        except sqlite3.Error as exc:
            self._translate_and_raise(exc, context="connection")
        except Exception as exc:
            raise DatabaseConnectionError(
                message=f"Filesystem error preparing database at '{self._db_path}': {exc}",
                details={"db_path": str(self._db_path), "os_error": str(exc)},
            ) from exc

    @contextmanager
    def get_connection(self) -> Iterator[sqlite3.Connection]:
        """Context manager yielding a configured SQLite connection and closing it on exit."""
        conn = self.connect()
        try:
            yield conn
        except DatabaseError:
            raise
        except sqlite3.Error as exc:
            self._translate_and_raise(exc, context="session")
        finally:
            conn.close()

    @contextmanager
    def transaction(
        self, connection: sqlite3.Connection | None = None
    ) -> Iterator[sqlite3.Connection]:
        """Execute an atomic transaction or nested savepoint.

        If `connection` is None, opens a new connection and begins an immediate
        transaction (`BEGIN IMMEDIATE`), committing on clean exit or rolling back
        on exception.

        If `connection` is provided and already inside a transaction (`in_transaction`),
        creates a nested `SAVEPOINT`, releasing it on success or rolling back to the
        savepoint on exception.

        Args:
            connection: Optional existing sqlite3.Connection for nested or shared transactions.

        Yields:
            Active sqlite3.Connection within the transaction or savepoint scope.
        """
        if connection is None:
            with self.get_connection() as conn:
                with self._root_transaction(conn) as tx_conn:
                    yield tx_conn
        elif connection.in_transaction:
            with self._nested_savepoint(connection) as sp_conn:
                yield sp_conn
        else:
            with self._root_transaction(connection) as tx_conn:
                yield tx_conn

    @contextmanager
    def _root_transaction(self, conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
        """Manage a top-level BEGIN IMMEDIATE / COMMIT / ROLLBACK transaction."""
        try:
            conn.execute("BEGIN IMMEDIATE;")
        except sqlite3.Error as exc:
            self._translate_and_raise(exc, context="begin_transaction")

        try:
            yield conn
        except Exception as exc:
            try:
                if conn.in_transaction:
                    conn.execute("ROLLBACK;")
            except sqlite3.Error as rb_exc:
                raise TransactionError(
                    message=f"Failed to roll back transaction: {rb_exc}",
                    details={"db_path": str(self._db_path), "original_error": str(exc)},
                ) from rb_exc

            if isinstance(exc, DatabaseError):
                raise
            if isinstance(exc, sqlite3.Error):
                self._translate_and_raise(exc, context="transaction")
            raise
        else:
            try:
                if conn.in_transaction:
                    conn.execute("COMMIT;")
            except sqlite3.Error as cm_exc:
                self._translate_and_raise(cm_exc, context="commit_transaction")

    @contextmanager
    def _nested_savepoint(self, conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
        """Manage a nested SAVEPOINT / RELEASE / ROLLBACK TO SAVEPOINT block."""
        self._savepoint_counter += 1
        sp_name = f"sp_gda_{self._savepoint_counter}"

        try:
            conn.execute(f"SAVEPOINT {sp_name};")
        except sqlite3.Error as exc:
            self._translate_and_raise(exc, context=f"savepoint_begin:{sp_name}")

        try:
            yield conn
        except Exception as exc:
            try:
                conn.execute(f"ROLLBACK TO SAVEPOINT {sp_name};")
                conn.execute(f"RELEASE SAVEPOINT {sp_name};")
            except sqlite3.Error as rb_exc:
                raise TransactionError(
                    message=f"Failed to roll back savepoint '{sp_name}': {rb_exc}",
                    details={"savepoint": sp_name, "original_error": str(exc)},
                ) from rb_exc

            if isinstance(exc, DatabaseError):
                raise
            if isinstance(exc, sqlite3.Error):
                self._translate_and_raise(exc, context=f"savepoint:{sp_name}")
            raise
        else:
            try:
                conn.execute(f"RELEASE SAVEPOINT {sp_name};")
            except sqlite3.Error as rel_exc:
                self._translate_and_raise(rel_exc, context=f"savepoint_release:{sp_name}")
