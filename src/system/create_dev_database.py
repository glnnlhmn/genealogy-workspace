"""Path: src/system/create_dev_database.py

Provision and initialize the DEV SQLite database environment.

Reads environment configuration from pyproject.toml, ensures parent directory
hierarchy, applies WAL pragmas, and delegates initial table migrations to SchemaManager.
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

from gda.core.config import DatabaseConfig
from gda.db.schema.manager import SchemaManager
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.1"


def create_environment_database(env_name: str = "DEV", root_dir: str | Path = ".") -> Path:
    """Create and initialize an environment database from pyproject.toml settings."""
    root = Path(root_dir).resolve()
    pyproject_file = root / "pyproject.toml"

    if not pyproject_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {pyproject_file}")

    with open(pyproject_file, "rb") as fh:
        pyproject = tomllib.load(fh)

    env_table = pyproject.get("tool", {}).get("gda", {}).get("environments", {})
    target_key = env_name.upper()

    if target_key not in env_table:
        raise KeyError(f"Environment '{target_key}' not defined under [tool.gda.environments]")

    env_cfg = env_table[target_key]
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

    print(f"[{target_key}] Successfully initialized {db_path} (migrations: {applied_versions})")
    return db_path


def main() -> None:
    """CLI execution entrypoint."""
    try:
        create_environment_database(env_name="DEV")
    except Exception as exc:
        print(f"Error provisioning DEV database: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
