"""Path: src/gda/db/schema/manager.py

Schema migration engine and DDL execution coordinator for GDA DB.

Operational Role:
    Inspects applied migration versions against schema_migrations and applies
    pending DDL scripts sequentially inside atomic DatabaseSessionManager transactions.

Classes:
    SchemaManager: Governs DDL provisioning, version inspection, and migrations.
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from gda.core.introspectable import IntrospectableMixin
from gda.db.exceptions import DatabaseOperationalError
from gda.db.schema.migrations import MIGRATION_REGISTRY
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.4"


class SchemaManager(IntrospectableMixin):
    """Manage SQLite DDL schema provisioning, migration execution, and inspection."""

    def __init__(self, session_manager: DatabaseSessionManager) -> None:
        """Initialize SchemaManager.

        Args:
            session_manager: Configured DatabaseSessionManager instance.
        """
        self._session = session_manager

    @property
    def session_manager(self) -> DatabaseSessionManager:
        """Return the bound DatabaseSessionManager."""
        return self._session

    def ensure_migration_table(self, conn: sqlite3.Connection) -> None:
        """Ensure the schema_migrations tracking table exists.

        Args:
            conn: Active sqlite3.Connection.
        """
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TEXT NOT NULL
            );
            """
        )

    def get_applied_versions(self, conn: sqlite3.Connection) -> set[int]:
        """Query set of all migration versions previously applied.

        Args:
            conn: Active sqlite3.Connection.

        Returns:
            Set of applied integer migration versions.
        """
        self.ensure_migration_table(conn)
        cursor = conn.cursor()
        try:
            rows = cursor.execute("SELECT version FROM schema_migrations;").fetchall()
            return {int(row[0]) for row in rows}
        finally:
            cursor.close()

    def get_current_version(self) -> int:
        """Get the highest migration version currently applied to the database.

        Returns:
            Highest integer version applied, or 0 if uninitialized.
        """
        with self._session.get_connection() as conn:
            applied = self.get_applied_versions(conn)
            return max(applied) if applied else 0

    def migrate(self) -> list[int]:
        """Apply all outstanding schema migrations idempotently.

        Returns:
            List of newly applied migration versions.

        Raises:
            DatabaseOperationalError: On SQL migration execution failure.
        """
        applied_versions: list[int] = []

        with self._session.get_connection() as conn:
            self.ensure_migration_table(conn)
            already_applied = self.get_applied_versions(conn)

            for mig in sorted(MIGRATION_REGISTRY, key=lambda m: m.version):
                if mig.version in already_applied:
                    continue

                try:
                    with self._session.transaction(conn=conn) as tx_conn:
                        tx_conn.executescript(mig.up_sql)
                        now_iso = datetime.now(UTC).isoformat().replace("+00:00", "Z")
                        tx_conn.execute(
                            """
                            INSERT INTO schema_migrations (version, name, applied_at)
                            VALUES (?, ?, ?);
                            """,
                            (mig.version, mig.name, now_iso),
                        )
                    applied_versions.append(mig.version)
                except (sqlite3.Error, DatabaseOperationalError) as err:
                    err_msg = (
                        err.message
                        if isinstance(err, DatabaseOperationalError)
                        else str(err)
                    )
                    raise DatabaseOperationalError(
                        f"Migration {mig.version} ('{mig.name}') failed: {err_msg}",
                        details={"version": mig.version, "name": mig.name},
                    ) from err

        return applied_versions

    def init_db(self) -> list[int]:
        """Initialize and bootstrap database tables to latest schema version.

        Returns:
            List of applied migration versions.
        """
        return self.migrate()
