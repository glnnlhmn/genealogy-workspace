---
name: update-database-schema
description: Inspects, backs up, and applies schema migrations to SQLite databases across GDA environments (DEV, TEST, STAGING, PROD). Use when the operator asks to update, migrate, or upgrade a database schema.
---
# Update Database Schema

Safely migrate an existing SQLite database to the latest schema version across environments by creating an atomic pre-migration backup and delegating execution to `gda.db`.

## When to Use

* Applying newly registered schema migrations (`MIGRATION_REGISTRY`) to an existing database file.
* Upgrading an environment database (`DEV`, `TEST`, `STAGING`, `PROD`) after code updates.
* Inspecting current vs. pending schema versions across target databases.

## Operating Principles

* **Single Source of Truth:** Read database locations and backup directories dynamically from `[tool.gda.environments.<ENV>]` in `pyproject.toml`. Never hardcode file paths or timeouts.
* **Pre-Execution Safe Backup:** Before applying any schema migration or executing DDL against an existing database, create a timestamped backup copy (`[filename].[YYYYMMDD_HHMMSS].bk`) in the environment's configured backup directory (`archive/backups_workspace/db/<env>/`).
* **Zero Manual DDL:** Delegate version inspection and migration execution strictly to `gda.db.schema.manager.SchemaManager.migrate()`.
* **Atomic Transactions:** Each migration step runs inside an atomic transaction managed by `DatabaseSessionManager`.
* **Idempotent Application:** Only unapplied migrations are executed. If the database is already at the latest schema version, no DDL executes and no backup is created.

## Execution Workflow

1. **Resolve Environment Target:**
   * Load `pyproject.toml` using `tomllib`.
   * Extract configuration under `tool.gda.environments.<ENV>`.
   * Resolve absolute paths for `db_path` and `backup_tier_dir`.
   * Verify the target database file exists on disk.

2. **Inspect Migration Version:**
   * Initialize `DatabaseConfig` using `db_path` and `timeout_seconds`.
   * Create `DatabaseSessionManager` and `SchemaManager`.
   * Check `schema_mgr.get_current_version()` and compare against `MIGRATION_REGISTRY`.
   * If all migrations are already applied, report up-to-date status and exit cleanly.

3. **Enforce Safe Backup:**
   * Ensure `backup_tier_dir` exists.
   * Generate an atomic copy: `<backup_tier_dir>/<filename>.<YYYYMMDD_HHMMSS>.bk`.

4. **Execute Schema Migrations:**
   * Invoke `schema_mgr.migrate()`.
   * Confirm the newly applied versions and report the final schema version.

## Python Execution Pattern

```python
"""Database schema migration execution procedure."""

from __future__ import annotations

import shutil
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from gda.core.config import DatabaseConfig
from gda.db.schema.manager import SchemaManager
from gda.db.schema.migrations import MIGRATION_REGISTRY
from gda.db.session import DatabaseSessionManager


def update_environment_database(env_name: str, root_dir: str | Path = ".") -> list[int]:
    """Inspect, back up, and migrate an environment database to the latest schema."""
    root = Path(root_dir).resolve()
    pyproject_file = root / "pyproject.toml"

    with open(pyproject_file, "rb") as fh:
        pyproject = tomllib.load(fh)

    env_cfg = pyproject["tool"]["gda"]["environments"][env_name.upper()]
    db_path = root / Path(env_cfg["db_path"])

    if not db_path.exists():
        raise FileNotFoundError(
            f"Target database not found at {db_path}. Provision the database first."
        )

    busy_timeout_ms = int(env_cfg.get("timeout_seconds", 60.0) * 1000)
    db_config = DatabaseConfig(
        db_path=db_path,
        busy_timeout=busy_timeout_ms,
        journal_mode="WAL",
        foreign_keys=True,
        synchronous="NORMAL",
    )

    session_mgr = DatabaseSessionManager(config=db_config)
    schema_mgr = SchemaManager(session_manager=session_mgr)

    current_ver = schema_mgr.get_current_version()
    max_registered_ver = max((m.version for m in MIGRATION_REGISTRY), default=0)

    if current_ver >= max_registered_ver:
        print(f"[{env_name.upper()}] Database is already up to date at version {current_ver}.")
        return []

    # Safe Backup Protocol
    backup_tier_dir = root / Path(env_cfg.get("backup_tier_dir", "archive/backups_workspace/db"))
    backup_tier_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_file = backup_tier_dir / f"{db_path.name}.{timestamp}.bk"
    shutil.copy2(db_path, backup_file)
    print(f"[{env_name.upper()}] Pre-migration backup created: {backup_file}")

    # Run pending migrations
    applied_versions = schema_mgr.migrate()
    print(
        f"[{env_name.upper()}] Applied migrations: {applied_versions}. "
        f"New schema version: {schema_mgr.get_current_version()}"
    )
    return applied_versions
```

## Gotchas

* Always check whether migrations are actually pending before creating the backup copy to avoid cluttering `archive/backups_workspace/`.
* When rolling back a failed manual migration, restore both the main `.sqlite` file and remove any orphaned `-wal` or `-shm` index files.
* Environment keys in `pyproject.toml` are uppercase (`DEV`, `TEST`, `STAGING`, `PROD`).
