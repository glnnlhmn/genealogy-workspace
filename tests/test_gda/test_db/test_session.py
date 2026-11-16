"""Path: tests/test_gda/test_db/test_session.py

Behavioral contract and verification test suite for DatabaseSessionManager.

Validates AppConfig/DatabaseConfig binding, environment resolution, SQLite
connection lifecycle, PRAGMA policies (WAL, foreign_keys, busy_timeout),
atomic transaction boundaries with BEGIN IMMEDIATE, nested savepoint isolation,
rollback semantics, and driver exception translation contracts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import gda.db.session as session_mod
from gda.core.config import AppConfig, DatabaseConfig
from gda.db.exceptions import (
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseConnectionError,
    DatabaseOperationalError,
    TransactionError,
)
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.9"


# ==============================================================================
# GROUP 1: INITIALIZATION, APPCONFIG BINDING & INTROSPECTION CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_session_manager_dunder_all_and_initialization_defaults() -> None:
    """Verify session manager __all__ and default binding to DatabaseConfig attributes."""
    assert session_mod.__all__ == ["DatabaseSessionManager"]

    manager = DatabaseSessionManager()
    assert manager.db_path == Path("data/archive.db")
    assert manager.is_in_memory is False
    assert manager.connection_string == "sqlite:///data/archive.db"
    assert manager.config.journal_mode == "WAL"
    assert manager.config.busy_timeout == 5000


@pytest.mark.unit
def test_session_manager_initialization_with_explicit_memory_path() -> None:
    """Verify session manager recognizes :memory: string identifiers and syncs config."""
    manager = DatabaseSessionManager(db_path=":memory:")
    assert manager.db_path == ":memory:"
    assert manager.is_in_memory is True
    assert manager.config.is_in_memory is True
    assert manager.connection_string == "sqlite:///:memory:"


@pytest.mark.unit
def test_session_manager_initialization_with_custom_config_and_app_config(
    tmp_path: Path,
) -> None:
    """Verify custom DatabaseConfig, AppConfig, and env_name are honored."""
    custom_path = tmp_path / "custom.db"
    cfg = DatabaseConfig(db_path=custom_path, busy_timeout=2500, journal_mode="DELETE")
    manager = DatabaseSessionManager(config=cfg)
    assert manager.db_path == custom_path
    assert manager.config.busy_timeout == 2500
    assert manager.config.journal_mode == "DELETE"

    app_cfg = AppConfig(root_path=tmp_path, database=cfg)
    app_mgr = DatabaseSessionManager(config=app_cfg)
    assert app_mgr.db_path == custom_path

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.gda.environments.PROD]
db_name = "gda_prod.db"
db_path = "data/db/gda_prod.db"
timeout_seconds = 30.0
""",
        encoding="utf-8",
    )
    env_mgr = DatabaseSessionManager(env_name="PROD", root_path=tmp_path)
    assert env_mgr.db_path == Path("data/db/gda_prod.db")
    assert env_mgr.config.db_name == "gda_prod.db"
    assert env_mgr.config.busy_timeout == 30000


@pytest.mark.unit
def test_session_manager_initialization_path_overrides_config(tmp_path: Path) -> None:
    """Verify explicit db_path argument takes precedence over config.db_path."""
    cfg = DatabaseConfig(db_path=Path("data/ignored.db"))
    override_path = tmp_path / "override.db"
    manager = DatabaseSessionManager(db_path=override_path, config=cfg)
    assert manager.db_path == override_path
    assert manager.config.db_path == override_path


@pytest.mark.unit
def test_session_manager_introspectable_help() -> None:
    """Verify IntrospectableMixin .help() produces directory output without errors."""
    manager = DatabaseSessionManager(db_path=":memory:")
    help_text = manager.help(as_str=True)
    assert help_text is not None
    assert "DatabaseSessionManager Public Directory" in help_text
    assert "get_connection" in help_text
    assert "transaction" in help_text


# ==============================================================================
# GROUP 2: PRAGMA ENFORCEMENT & CONNECTION LIFECYCLE
# ==============================================================================


@pytest.mark.integration
def test_session_manager_applies_pragmas_on_disk(tmp_path: Path) -> None:
    """Verify mandatory PRAGMAs are executed against physical disk database files."""
    db_file = tmp_path / "nested" / "dir" / "pragma_test.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.get_connection() as conn:
        cursor = conn.cursor()
        try:
            journal_mode = cursor.execute("PRAGMA journal_mode;").fetchone()[0]
            foreign_keys = cursor.execute("PRAGMA foreign_keys;").fetchone()[0]
            busy_timeout = cursor.execute("PRAGMA busy_timeout;").fetchone()[0]
            synchronous = cursor.execute("PRAGMA synchronous;").fetchone()[0]

            assert journal_mode.upper() == "WAL"
            assert foreign_keys == 1
            assert busy_timeout == 5000
            assert synchronous in (1, "NORMAL")
        finally:
            cursor.close()


@pytest.mark.unit
def test_session_manager_foreign_keys_disabled_option() -> None:
    """Verify PRAGMA foreign_keys can be set to OFF when explicitly configured."""
    cfg = DatabaseConfig(db_path=":memory:", foreign_keys=False)
    manager = DatabaseSessionManager(config=cfg)

    with manager.get_connection() as conn:
        cursor = conn.cursor()
        try:
            fk = cursor.execute("PRAGMA foreign_keys;").fetchone()[0]
            assert fk == 0
        finally:
            cursor.close()


@pytest.mark.unit
def test_session_manager_row_factory_configured() -> None:
    """Verify connections return sqlite3.Row instances supporting dict-like access."""
    manager = DatabaseSessionManager(db_path=":memory:")
    with manager.get_connection() as conn:
        row = conn.execute("SELECT 42 AS answer, 'GDA' AS label;").fetchone()
        assert isinstance(row, sqlite3.Row)
        assert row["answer"] == 42
        assert row["label"] == "GDA"


# ==============================================================================
# GROUP 3: ATOMIC TRANSACTIONS & NESTED SAVEPOINTS
# ==============================================================================


@pytest.mark.integration
def test_session_manager_root_transaction_commit_and_rollback(tmp_path: Path) -> None:
    """Verify transaction() commits on clean exit and rolls back on exception."""
    db_file = tmp_path / "tx_test.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.transaction() as tx:
        tx.execute("CREATE TABLE items (id TEXT PRIMARY KEY, val TEXT);")
        tx.execute("INSERT INTO items VALUES ('1', 'committed');")

    with pytest.raises(RuntimeError, match="abort"):
        with manager.transaction() as tx:
            tx.execute("INSERT INTO items VALUES ('2', 'rolled_back');")
            raise RuntimeError("abort")

    with manager.get_connection() as conn:
        rows = conn.execute("SELECT id FROM items;").fetchall()
        assert [r["id"] for r in rows] == ["1"]

        # Also test passing an existing non-in_transaction connection to transaction()
        with manager.transaction(conn) as shared_tx:
            shared_tx.execute("INSERT INTO items VALUES ('3', 'shared_conn_commit');")

        rows_after = conn.execute("SELECT id FROM items ORDER BY id;").fetchall()
        assert [r["id"] for r in rows_after] == ["1", "3"]


@pytest.mark.integration
def test_session_manager_nested_savepoint_isolation(tmp_path: Path) -> None:
    """Verify nested transaction(conn) uses SAVEPOINT and isolates partial rollbacks."""
    db_file = tmp_path / "savepoint_test.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.transaction() as outer_tx:
        outer_tx.execute("CREATE TABLE logs (id INTEGER PRIMARY KEY, msg TEXT);")
        outer_tx.execute("INSERT INTO logs (msg) VALUES ('outer_start');")

        with manager.transaction(outer_tx) as inner_ok:
            inner_ok.execute("INSERT INTO logs (msg) VALUES ('inner_committed');")

        with pytest.raises(ValueError, match="inner failure"):
            with manager.transaction(outer_tx) as inner_fail:
                inner_fail.execute("INSERT INTO logs (msg) VALUES ('inner_rolled_back');")
                raise ValueError("inner failure")

        outer_tx.execute("INSERT INTO logs (msg) VALUES ('outer_end');")

    with manager.get_connection() as conn:
        msgs = [r["msg"] for r in conn.execute("SELECT msg FROM logs ORDER BY id;").fetchall()]
        assert msgs == ["outer_start", "inner_committed", "outer_end"]


# ==============================================================================
# GROUP 4: DRIVER ERROR TRANSLATION & DEFENSIVE BOUNDARIES
# ==============================================================================


@pytest.mark.regression
def test_session_manager_translates_integrity_and_operational_errors(
    tmp_path: Path,
) -> None:
    """Verify IntegrityError -> ConstraintViolationError, OperationalError, and DatabaseError passthrough."""
    db_file = tmp_path / "errors.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.transaction() as tx:
        tx.execute("CREATE TABLE uniq_test (code TEXT PRIMARY KEY);")
        tx.execute("INSERT INTO uniq_test VALUES ('A');")

    with pytest.raises(ConstraintViolationError) as exc_int:
        with manager.transaction() as tx:
            tx.execute("INSERT INTO uniq_test VALUES ('A');")
    assert exc_int.value.error_code == "ERR_DB_CONSTRAINT"

    with pytest.raises(DatabaseOperationalError) as exc_op:
        with manager.get_connection() as conn:
            conn.execute("SELECT * FROM non_existent_table;")
    assert exc_op.value.error_code == "ERR_DB_OPERATIONAL"

    with pytest.raises(DatabaseOperationalError, match="explicit domain error in get_connection"):
        with manager.get_connection():
            raise DatabaseOperationalError("explicit domain error in get_connection")

    with pytest.raises(DatabaseOperationalError, match="explicit domain error in transaction"):
        with manager.transaction():
            raise DatabaseOperationalError("explicit domain error in transaction")


@pytest.mark.regression
def test_session_manager_translates_locked_busy_and_connection_errors() -> None:
    """Verify locked/busy OperationalError -> ConnectionTimeoutError and connect faults."""
    manager = DatabaseSessionManager(db_path=":memory:")

    with pytest.raises(ConnectionTimeoutError) as exc_lock:
        manager._translate_and_raise(
            sqlite3.OperationalError("database is locked"), context="write"
        )
    assert exc_lock.value.error_code == "ERR_DB_TIMEOUT"

    with pytest.raises(DatabaseConnectionError):
        manager._translate_and_raise(sqlite3.Error("driver failure"), context="connection")

    with pytest.raises(TransactionError):
        manager._translate_and_raise(sqlite3.Error("generic tx error"), context="commit")

    with patch("sqlite3.connect", side_effect=sqlite3.Error("cannot open")):
        with pytest.raises(DatabaseConnectionError, match="Failed to connect"):
            manager.connect()

    with patch.object(
        DatabaseSessionManager,
        "_ensure_parent_directory",
        side_effect=OSError("read-only filesystem"),
    ):
        with pytest.raises(DatabaseConnectionError, match="Filesystem error"):
            manager.connect()


@pytest.mark.regression
def test_session_manager_transaction_and_savepoint_driver_fault_branches() -> None:
    """Verify defensive error branches in _root_transaction and _nested_savepoint."""
    manager = DatabaseSessionManager(db_path=":memory:")

    # 1. BEGIN IMMEDIATE fails
    mock_conn = MagicMock(spec=sqlite3.Connection)
    mock_conn.in_transaction = False
    mock_conn.execute.side_effect = sqlite3.OperationalError("cannot start transaction")
    with pytest.raises(DatabaseOperationalError):
        with manager._root_transaction(mock_conn):
            pass

    # 2. ROLLBACK fails during exception handling in _root_transaction
    mock_conn_rb = MagicMock(spec=sqlite3.Connection)
    mock_conn_rb.in_transaction = True

    def _rb_side_effect(sql: str) -> None:
        if sql == "ROLLBACK;":
            raise sqlite3.Error("rollback failed")

    mock_conn_rb.execute.side_effect = _rb_side_effect
    with pytest.raises(TransactionError, match="Failed to roll back transaction"):
        with manager._root_transaction(mock_conn_rb):
            raise RuntimeError("trigger rollback")

    # 3. COMMIT fails in _root_transaction
    mock_conn_cm = MagicMock(spec=sqlite3.Connection)
    mock_conn_cm.in_transaction = True

    def _cm_side_effect(sql: str) -> None:
        if sql == "COMMIT;":
            raise sqlite3.Error("commit failed")

    mock_conn_cm.execute.side_effect = _cm_side_effect
    with pytest.raises(TransactionError, match="Database error during commit_transaction"):
        with manager._root_transaction(mock_conn_cm):
            pass

    # 4. Manual commit inside _root_transaction (so conn.in_transaction is False on exit/rollback)
    mock_conn_manual = MagicMock(spec=sqlite3.Connection)
    mock_conn_manual.in_transaction = False
    with manager._root_transaction(mock_conn_manual):
        pass
    with pytest.raises(RuntimeError):
        with manager._root_transaction(mock_conn_manual):
            raise RuntimeError("already rolled back")

    # 5. SAVEPOINT begin fails in _nested_savepoint
    mock_sp_begin = MagicMock(spec=sqlite3.Connection)
    mock_sp_begin.execute.side_effect = sqlite3.Error("savepoint begin error")
    with pytest.raises(TransactionError):
        with manager._nested_savepoint(mock_sp_begin):
            pass

    # 6. SAVEPOINT rollback fails in _nested_savepoint
    mock_sp_rb = MagicMock(spec=sqlite3.Connection)

    def _sp_rb_side_effect(sql: str) -> None:
        if sql.startswith("ROLLBACK TO SAVEPOINT"):
            raise sqlite3.Error("sp rollback failed")

    mock_sp_rb.execute.side_effect = _sp_rb_side_effect
    with pytest.raises(TransactionError, match="Failed to roll back savepoint"):
        with manager._nested_savepoint(mock_sp_rb):
            raise RuntimeError("trigger sp rollback")

    # 7. SAVEPOINT body raises sqlite3.Error or DatabaseError
    mock_sp_err = MagicMock(spec=sqlite3.Connection)
    with pytest.raises(ConstraintViolationError):
        with manager._nested_savepoint(mock_sp_err):
            raise sqlite3.IntegrityError("duplicate in sp")

    with pytest.raises(DatabaseOperationalError):
        with manager._nested_savepoint(mock_sp_err):
            raise DatabaseOperationalError("domain db error in sp")

    # 8. RELEASE SAVEPOINT fails on clean exit
    mock_sp_rel = MagicMock(spec=sqlite3.Connection)

    def _sp_rel_side_effect(sql: str) -> None:
        if sql.startswith("RELEASE SAVEPOINT"):
            raise sqlite3.Error("sp release failed")

    mock_sp_rel.execute.side_effect = _sp_rel_side_effect
    with pytest.raises(TransactionError, match="savepoint_release"):
        with manager._nested_savepoint(mock_sp_rel):
            pass
