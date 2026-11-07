<!--Path: .skills/create-database/SKILL.md-->
---
name: create-database
description: Provisions and initializes a new SQLite database for a target GDA environment (DEV, TEST, STAGING, PROD). Use when the operator asks to create, bootstrap, or provision a database for an environment.
---

# Create Database

Initialize a SQLite database for a specified target environment by reading configuration settings directly from `pyproject.toml` and applying schema migrations via `gda.db`.

## When to Use

* Provisioning a new database file for an environment (`DEV`, `TEST`, `STAGING`, `PROD`).
* Bootstrapping initial schemas and tables for a newly configured environment.
* Setting up local test or development database instances.

## Operating Principles

* **Single Source of Truth:** Never hardcode database target paths, timeouts, or environment definitions. Read directly from `[tool.gda.environments.<ENV>]` in `pyproject.toml`.
* **Zero Custom DDL:** Do not execute custom `CREATE TABLE` statements. Delegate all table creation and migration logic directly to `gda.db.schema.manager.SchemaManager.init_db()`.
* **Safe Directory Creation:** Ensure the target parent directory exists before instantiating the database connection.
* **Standard Concurrency PRAGMAs:** Enforce `WAL` journal mode, `foreign_keys = ON`, `synchronous = NORMAL`, and timeout settings via `DatabaseConfig` and `DatabaseSessionManager`.

## Execution Workflow

1. **Load Environment Settings:**
   * Parse `pyproject.toml` using `tomllib`.
   * Extract the environment table under `tool.gda.environments.<ENV>`.
   * Resolve `db_path` and `timeout_seconds`.

2. **Ensure Storage Hierarchy:**
   * Resolve the absolute path to `db_path`.
   * Create missing parent directories via `db_path.parent.mkdir(parents=True, exist_ok=True)`.

3. **Configure Database Session:**
   * Instantiate `DatabaseConfig` with `db_path`, `busy_timeout` (derived in milliseconds from `timeout_seconds`), `journal_mode="WAL"`, `foreign_keys=True`, and `synchronous="NORMAL"`.
   * Instantiate `DatabaseSessionManager(config=db_config)`.

4. **Initialize Schema:**
   * Instantiate `SchemaManager(session_manager=session_mgr)`.
   * Execute `schema_mgr.init_db()`.
   * Confirm applied migration versions returned by `init_db()`.

## Python Execution Pattern

```python
"""Database creation execution procedure."""

from __future__ import annotations

import tomllib
from pathlib import Path

from gda.core.config import DatabaseConfig
from gda.db.schema.manager import SchemaManager
from gda.db.session import DatabaseSessionManager


def create_environment_database(env_name: str, root_dir: str | Path = ".") -> Path:
    """Create and initialize an environment database from pyproject.toml settings."""
    root = Path(root_dir).resolve()
    pyproject_file = root / "pyproject.toml"

    with open(pyproject_file, "rb") as fh:
        pyproject = tomllib.load(fh)

    env_cfg = pyproject["tool"]["gda"]["environments"][env_name.upper()]
    db_path = root / Path(env_cfg["db_path"])
    db_path.parent.mkdir(parents=True, exist_ok=True)

    busy_timeout_ms = int(env_cfg.get("timeout_seconds", 30.0) * 1000)
    db_config = DatabaseConfig(
        db_path=db_path,
        busy_timeout=busy_timeout_ms,
        journal_mode="WAL",
        foreign_keys=True,
        synchronous="NORMAL",
    )

    session_mgr = DatabaseSessionManager(config=db_config)
    schema_mgr = SchemaManager(session_manager=session_mgr)
    applied_versions = schema_mgr.init_db()

    print(f"[{env_name.upper()}] Initialized {db_path} (migrations: {applied_versions})")
    return db_path
```

## Gotchas

* Environment keys in `pyproject.toml` are uppercase (`DEV`, `TEST`, `STAGING`, `PROD`). Normalize inputs using `.upper()`.
* Do not bypass `SchemaManager` to create tables manually.
* Ensure timeout values are converted from seconds (`float`) to milliseconds (`int`) for `DatabaseConfig.busy_timeout`.