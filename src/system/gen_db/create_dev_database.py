"""Path: src/system/gen_db/create_dev_database.py

Provision and initialize GDA SQLite environment databases (DEV, TEST, STAGING, PROD).

Operational Role:
    Resolves environment database configurations from pyproject.toml via
    gda.core.config.AppConfig.for_environment(), optionally resets existing
    database files when --reset is requested, ensures parent directory
    hierarchies, enforces WAL concurrency PRAGMAs via DatabaseSessionManager,
    and executes modular analytical DDL migrations via SchemaManager.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

from gda.core.config import AppConfig
from gda.db.schema.manager import SchemaManager
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.3"

__all__ = [
    "create_environment_database",
    "main",
    "parse_args",
]


def _remove_existing_sqlite_files(db_path: Path) -> None:
    """Remove an existing SQLite database file and its WAL/SHM sidecars."""
    for candidate in (
        db_path,
        Path(f"{db_path}-wal"),
        Path(f"{db_path}-shm"),
    ):
        if candidate.exists():
            candidate.unlink()


def create_environment_database(
    env_name: str = "DEV",
    root_dir: str | Path = ".",
    *,
    reset: bool = False,
) -> Path:
    """Create and initialize an environment database from pyproject.toml settings.

    Args:
        env_name: Target environment key ('DEV', 'TEST', 'STAGING', 'PROD').
        root_dir: Workspace root directory containing pyproject.toml.
        reset: If True, removes any existing database file and WAL/SHM sidecars
            before provisioning the fresh schema.

    Returns:
        Path: Canonical resolved path to the initialized database file.

    Raises:
        FileNotFoundError: If pyproject.toml does not exist in root_dir.
        KeyError: If target environment is not configured under [tool.gda.environments].
    """
    root = Path(root_dir).resolve()
    pyproject_file = root / "pyproject.toml"

    if not pyproject_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {pyproject_file}")

    with open(pyproject_file, "rb") as fh:
        pyproject = tomllib.load(fh)

    env_table = pyproject.get("tool", {}).get("gda", {}).get("environments", {})
    target_key = env_name.strip().upper()

    if target_key not in env_table:
        raise KeyError(f"Environment '{target_key}' not defined under [tool.gda.environments]")

    app_cfg = AppConfig.for_environment(
        target_key,
        root_path=root,
        config_path=pyproject_file,
    )
    raw_db_path = Path(app_cfg.database.db_path)
    db_path = raw_db_path.resolve() if raw_db_path.is_absolute() else (root / raw_db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if reset:
        _remove_existing_sqlite_files(db_path)

    db_config = app_cfg.database.model_copy(update={"db_path": db_path})
    session_mgr = DatabaseSessionManager(config=db_config)
    schema_mgr = SchemaManager(session_manager=session_mgr)
    applied_versions = schema_mgr.init_db()
    current_version = schema_mgr.get_current_version()

    print(
        f"[{target_key}] Successfully initialized {db_path} "
        f"(applied migrations: {applied_versions}, schema version: v{current_version})"
    )
    return db_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="create_dev_database",
        description="Provision and initialize environment SQLite database from pyproject.toml.",
    )
    parser.add_argument(
        "--env",
        type=str,
        default="DEV",
        help="Target environment name to provision ('DEV', 'TEST', 'STAGING', 'PROD'; default: 'DEV').",
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Workspace repository root directory (default: '.').",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate the target SQLite database file from scratch.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI execution entrypoint."""
    args = parse_args(argv)
    try:
        create_environment_database(
            env_name=args.env,
            root_dir=args.root,
            reset=bool(args.reset),
        )
        return 0
    except Exception as exc:
        print(
            f"Error provisioning {args.env.upper()} database: {exc}",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
