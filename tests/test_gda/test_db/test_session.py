"""Path: tests/test_gda/test_db/test_session.py

Behavioral contract and verification test suite for DatabaseSessionManager.

Validates SQLite connection lifecycle, PRAGMA policies (WAL, foreign_keys, busy_timeout),
atomic transaction boundaries with BEGIN IMMEDIATE, nested savepoint isolation,
rollback semantics, and driver exception translation contracts.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from gda.core.config import DatabaseConfig
from gda.db.exceptions import (
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseOperationalError,
    TransactionError,
)
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: INITIALIZATION & INTROSPECTION CONTRACTS
# Note: Verify configuration binding, path resolution, in-memory checks, and .help()
# ==============================================================================


@pytest.mark.unit
def test_session_manager_initialization_defaults() -> None:
    """Verify session manager defaults bind to standard DatabaseConfig attributes."""
    manager = DatabaseSessionManager()
    assert manager.db_path == Path("data/archive.db")
    assert manager.is_in_memory is False
    assert manager.config.journal_mode == "WAL"
    assert manager.config.busy_timeout == 5000


@pytest.mark.unit
def test_session_manager_initialization_with_explicit_memory_path() -> None:
    """Verify session manager recognizes :memory: string identifiers."""
    manager = DatabaseSessionManager(db_path=":memory:")
    assert manager.db_path == ":memory:"
    assert manager.is_in_memory is True


@pytest.mark.unit
def test_session_manager_initialization_with_custom_config(tmp_path: Path) -> None:
    """Verify custom DatabaseConfig is honored when supplied to session manager."""
    custom_path = tmp_path / "custom.db"
    cfg = DatabaseConfig(db_path=custom_path, busy_timeout=2500, journal_mode="DELETE")
    manager = DatabaseSessionManager(config=cfg)
    assert manager.db_path == custom_path
    assert manager.config.busy_timeout == 2500
    assert manager.config.journal_mode == "DELETE"


@pytest.mark.unit
def test_session_manager_initialization_path_overrides_config(tmp_path: Path) -> None:
    """Verify explicit db_path argument takes precedence over config.db_path."""
    cfg = DatabaseConfig(db_path=Path("data/ignored.db"))
    override_path = tmp_path / "override.db"
    manager = DatabaseSessionManager(db_path=override_path, config=cfg)
    assert manager.db_path == override_path


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
# Note: Verify Row factory, WAL mode, foreign keys, and connection cleanup
# ==============================================================================


@pytest.mark.integration
def test_session_manager_applies_pragmas_on_disk(tmp_path: Path) -> None:
    """Verify mandatory PRAGMAs are executed against physical disk database files."""
    db_file = tmp_path / "pragma_test.db"
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
def test_session_manager_row_factory_configuration() -> None:
    """Verify row_factory is set to sqlite3.Row for column-name key access."""
    manager = DatabaseSessionManager(db_path=":memory:")
    with manager.get_connection() as conn:
        assert conn.row_factory == sqlite3.Row
        cursor = conn.cursor()
        try:
            row = cursor.execute("SELECT 1 AS col_a, 'value' AS col_b;").fetchone()
            assert row["col_a"] == 1
            assert row["col_b"] == "value"
        finally:
            cursor.close()


@pytest.mark.integration
def test_session_manager_creates_parent_directories_automatically(
    tmp_path: Path,
) -> None:
    """Verify parent directory structure is provisioned prior to database connection."""
    nested_db = tmp_path / "deep" / "nested" / "archive.db"
    assert not nested_db.parent.exists()

    manager = DatabaseSessionManager(db_path=nested_db)
    with manager.get_connection() as conn:
        assert nested_db.parent.exists()
        assert conn is not None


# ==============================================================================
# GROUP 3: ATOMIC TRANSACTIONS & SAVEPOINT NESTING
# Note: Verify BEGIN IMMEDIATE, commit, rollback, and nested savepoints
# ==============================================================================


@pytest.mark.integration
def test_session_manager_transaction_commit_success(tmp_path: Path) -> None:
    """Verify successful transaction execution commits mutations atomically."""
    db_file = tmp_path / "tx_commit.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.get_connection() as setup_conn:
        setup_conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);")

    with manager.transaction() as tx_conn:
        tx_conn.execute("INSERT INTO items (id, name) VALUES (1, 'alpha');")

    with manager.get_connection() as verify_conn:
        row = verify_conn.execute("SELECT name FROM items WHERE id = 1;").fetchone()
        assert row is not None
        assert row["name"] == "alpha"


@pytest.mark.integration
def test_session_manager_transaction_rollback_on_python_exception(
    tmp_path: Path,
) -> None:
    """Verify unhandled Python exceptions trigger transaction rollback."""
    db_file = tmp_path / "tx_rollback.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.get_connection() as setup_conn:
        setup_conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);")

    with pytest.raises(RuntimeError, match="Simulated application error"):
        with manager.transaction() as tx_conn:
            tx_conn.execute("INSERT INTO items (id, name) VALUES (1, 'alpha');")
            raise RuntimeError("Simulated application error")

    with manager.get_connection() as verify_conn:
        row = verify_conn.execute("SELECT COUNT(*) AS total FROM items;").fetchone()
        assert row["total"] == 0


@pytest.mark.integration
def test_session_manager_nested_savepoints_commit_success(tmp_path: Path) -> None:
    """Verify nested transaction creates a SAVEPOINT and releases it cleanly on success."""
    db_file = tmp_path / "nested_commit.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.get_connection() as setup_conn:
        setup_conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);")

    with manager.transaction() as outer_conn:
        outer_conn.execute("INSERT INTO items (id, name) VALUES (1, 'root');")

        with manager.transaction(conn=outer_conn) as inner_conn:
            inner_conn.execute("INSERT INTO items (id, name) VALUES (2, 'inner');")

        outer_conn.execute("INSERT INTO items (id, name) VALUES (3, 'resumed');")

    with manager.get_connection() as verify_conn:
        rows = verify_conn.execute("SELECT id, name FROM items ORDER BY id;").fetchall()
        assert len(rows) == 3
        assert rows[0]["id"] == 1 and rows[0]["name"] == "root"
        assert rows[1]["id"] == 2 and rows[1]["name"] == "inner"
        assert rows[2]["id"] == 3 and rows[2]["name"] == "resumed"


@pytest.mark.integration
def test_session_manager_nested_savepoints_partial_rollback(tmp_path: Path) -> None:
    """Verify nested transaction creates a SAVEPOINT and allows partial inner rollback."""
    db_file = tmp_path / "nested_savepoint.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.get_connection() as setup_conn:
        setup_conn.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);")

    with manager.transaction() as outer_conn:
        outer_conn.execute("INSERT INTO items (id, name) VALUES (1, 'root');")

        try:
            with manager.transaction(conn=outer_conn) as inner_conn:
                inner_conn.execute("INSERT INTO items (id, name) VALUES (2, 'inner');")
                raise ValueError("Inner failure")
        except ValueError:
            pass

        outer_conn.execute("INSERT INTO items (id, name) VALUES (3, 'resumed');")

    with manager.get_connection() as verify_conn:
        rows = verify_conn.execute("SELECT id, name FROM items ORDER BY id;").fetchall()
        assert len(rows) == 2
        assert rows[0]["id"] == 1 and rows[0]["name"] == "root"
        assert rows[1]["id"] == 3 and rows[1]["name"] == "resumed"


@pytest.mark.unit
def test_session_manager_nested_savepoint_driver_error_rollback() -> None:
    """Verify nested savepoint catches sqlite3.Error, rolls back savepoint, and translates error."""
    mock_conn = MagicMock(spec=sqlite3.Connection)
    manager = DatabaseSessionManager(db_path=":memory:")

    with manager.transaction(conn=mock_conn) as root_tx:
        with pytest.raises(DatabaseOperationalError):
            with manager.transaction(conn=root_tx) as inner_tx:
                inner_tx.execute("SYNTAX ERROR")
                raise sqlite3.OperationalError("Table not found")

    mock_conn.execute.assert_any_call("ROLLBACK TO SAVEPOINT sp_1;")


# ==============================================================================
# GROUP 4: DRIVER EXCEPTION TRANSLATION
# Note: Verify mapping of sqlite3 errors to ConstraintViolation, Timeout, and Operational
# ==============================================================================


@pytest.mark.unit
def test_session_manager_connection_failure_translation() -> None:
    """Verify driver connection failures raise DatabaseConnectionError."""
    with patch(
        "sqlite3.connect",
        side_effect=sqlite3.OperationalError("Unable to open database"),
    ):
        manager = DatabaseSessionManager(db_path="invalid_path.db")
        with pytest.raises(DatabaseOperationalError) as exc_info:
            manager.create_connection()
        assert "Database operational failure" in exc_info.value.message


@pytest.mark.integration
def test_session_manager_constraint_violation_translation(tmp_path: Path) -> None:
    """Verify sqlite3.IntegrityError translates to ConstraintViolationError."""
    db_file = tmp_path / "constraint_test.db"
    manager = DatabaseSessionManager(db_path=db_file)

    with manager.get_connection() as conn:
        conn.execute("CREATE TABLE unique_items (val TEXT UNIQUE);")

    with pytest.raises(ConstraintViolationError) as exc_info:
        with manager.transaction() as tx_conn:
            tx_conn.execute("INSERT INTO unique_items (val) VALUES ('duplicate');")
            tx_conn.execute("INSERT INTO unique_items (val) VALUES ('duplicate');")

    assert exc_info.value.error_code == "ERR_DB_CONSTRAINT"
    assert "constraint violation" in exc_info.value.message.lower()


@pytest.mark.unit
def test_session_manager_timeout_translation() -> None:
    """Verify sqlite3.OperationalError with 'locked' translates to ConnectionTimeoutError."""
    mock_conn = MagicMock(spec=sqlite3.Connection)

    def mock_execute(sql: str, *args: object, **kwargs: object) -> None:
        if sql == "COMMIT;":
            raise sqlite3.OperationalError("database is locked")

    mock_conn.execute.side_effect = mock_execute

    manager = DatabaseSessionManager(db_path=":memory:")
    with patch.object(manager, "create_connection", return_value=mock_conn):
        with pytest.raises(ConnectionTimeoutError) as exc_info:
            with manager.transaction():
                pass

        assert exc_info.value.error_code == "ERR_DB_TIMEOUT"
        assert "lock contention" in exc_info.value.message.lower()
    mock_conn.close.assert_called_once()


@pytest.mark.unit
def test_session_manager_operational_error_translation() -> None:
    """Verify general sqlite3.OperationalError translates to DatabaseOperationalError."""
    manager = DatabaseSessionManager(db_path=":memory:")
    with pytest.raises(DatabaseOperationalError) as exc_info:
        with manager.transaction() as tx_conn:
            tx_conn.execute("SELECT * FROM non_existent_table;")

    assert exc_info.value.error_code == "ERR_DB_OPERATIONAL"
    assert "Database operational failure" in exc_info.value.message


@pytest.mark.unit
def test_session_manager_generic_driver_error_translation() -> None:
    """Verify unclassified sqlite3.Error translates into fallback TransactionError."""
    mock_conn = MagicMock(spec=sqlite3.Connection)

    def mock_execute(sql: str, *args: object, **kwargs: object) -> None:
        if sql == "COMMIT;":
            raise sqlite3.Error("Unclassified SQLite driver fault")

    mock_conn.execute.side_effect = mock_execute

    manager = DatabaseSessionManager(db_path=":memory:")
    with patch.object(manager, "create_connection", return_value=mock_conn):
        with pytest.raises(TransactionError) as exc_info:
            with manager.transaction():
                pass

        assert exc_info.value.error_code == "ERR_DB_TRANSACTION"
        assert "Transaction aborted" in exc_info.value.message
    mock_conn.close.assert_called_once()


@pytest.mark.unit
def test_session_manager_rollback_failure_suppression() -> None:
    """Verify failure during rollback does not suppress the primary exception."""
    mock_conn = MagicMock(spec=sqlite3.Connection)

    def mock_execute(sql: str, *args: object, **kwargs: object) -> None:
        if sql == "CORRUPT SQL STATEMENT":
            raise sqlite3.OperationalError("Syntax error in query")
        if sql == "ROLLBACK;":
            raise sqlite3.Error("Rollback failed due to disconnected handle")

    mock_conn.execute.side_effect = mock_execute

    manager = DatabaseSessionManager(db_path=":memory:")
    with patch.object(manager, "create_connection", return_value=mock_conn):
        with pytest.raises(DatabaseOperationalError) as exc_info:
            with manager.transaction() as tx:
                tx.execute("CORRUPT SQL STATEMENT")

        assert exc_info.value.error_code == "ERR_DB_OPERATIONAL"
    mock_conn.close.assert_called_once()


@pytest.mark.unit
def test_session_manager_translate_and_raise_with_custom_details() -> None:
    """Verify _translate_and_raise attaches extra diagnostic details to the exception."""
    err = sqlite3.DatabaseError("Disk I/O error")
    with pytest.raises(TransactionError) as exc_info:
        DatabaseSessionManager._translate_and_raise(
            err=err,
            default_msg="Custom failure",
            fallback_cls=TransactionError,
            details={"sector": 512, "retry_count": 3},
        )
    assert exc_info.value.details["sector"] == 512
    assert exc_info.value.details["retry_count"] == 3
