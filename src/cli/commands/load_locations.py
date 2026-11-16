"""Path: src/cli/commands/load_locations.py

Operational CLI command for bulk loading and validating location intake archives.

Reads partitioned JSON location envelopes from data/setup/dev/locations (or configured setup_dir),
delegates validation and graph construction to the authoritative Locations collection and its
import/save utilities, and persists complete 19-column records via LocationRowMapper.
"""

from __future__ import annotations

import argparse
import logging
import sys
import tomllib
from pathlib import Path
from typing import Any

from gda.core.config import DatabaseConfig
from gda.core.introspectable import IntrospectableMixin
from gda.db.session import DatabaseSessionManager
from gda.entity.locations.collection import Locations
from gda.entity.locations.util import import_file, save_to_db

__version__ = "1.0.0+build.7"

logger = logging.getLogger("gda.cli.load_locations")


class LocationLoader(IntrospectableMixin):
    """Orchestrates location intake validation and ingestion via the Locations collection facade."""

    def __init__(
        self,
        env_name: str = "DEV",
        root_dir: str | Path = ".",
        schema_path: str | Path | None = None,
    ) -> None:
        """Initialize loader settings, resolving configuration paths relative to root."""
        self.root_dir = Path(root_dir).resolve()
        self.env_name = env_name.upper()
        self.pyproject_path = self.root_dir / "pyproject.toml"

        if schema_path:
            self.schema_path = self.root_dir / Path(schema_path)
        else:
            self.schema_path = (
                self.root_dir / "schemas" / "intake" / "dev" / "location_import.schema.json"
            )

        self._db_config: DatabaseConfig | None = None
        self._session_manager: DatabaseSessionManager | None = None
        self._env_cfg: dict[str, Any] = {}

    def load_environment_config(self) -> DatabaseConfig:
        """Parse pyproject.toml to derive target database configuration."""
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.pyproject_path}")

        with open(self.pyproject_path, "rb") as fh:
            pyproject = tomllib.load(fh)

        env_table = pyproject.get("tool", {}).get("gda", {}).get("environments", {})
        if self.env_name not in env_table:
            raise KeyError(
                f"Environment '{self.env_name}' not defined under [tool.gda.environments]"
            )

        self._env_cfg = env_table[self.env_name]
        db_path = self.root_dir / Path(self._env_cfg["db_path"])
        db_path.parent.mkdir(parents=True, exist_ok=True)

        busy_timeout_ms = int(self._env_cfg.get("timeout_seconds", 30.0) * 1000)
        self._db_config = DatabaseConfig(
            db_path=db_path,
            busy_timeout=busy_timeout_ms,
            journal_mode="WAL",
            foreign_keys=True,
            synchronous="NORMAL",
        )
        self._session_manager = DatabaseSessionManager(config=self._db_config)
        return self._db_config

    def get_default_setup_dir(self) -> Path:
        """Resolve the configured setup directory for locations in the target environment."""
        if not self._env_cfg:
            self.load_environment_config()
        configured_dir = self._env_cfg.get(
            "setup_dir", f"data/setup/{self.env_name.lower()}/locations"
        )
        return self.root_dir / Path(configured_dir)

    def discover_and_sort_files(self, intake_dir: Path) -> list[Path]:
        """Scan intake directory and sort files numerically to ensure hierarchical loading."""
        if not intake_dir.is_dir():
            raise FileNotFoundError(f"Intake directory does not exist: {intake_dir}")

        json_files = sorted(
            [p for p in intake_dir.glob("*.json") if p.is_file()],
            key=lambda p: p.name,
        )
        if not json_files:
            raise ValueError(f"No JSON intake partitions discovered in {intake_dir}")

        return json_files

    def load_partitions(self, intake_dir: str | Path | None = None) -> dict[str, int]:
        """Execute partition discovery, domain collection hydration, and database ingestion."""
        self.load_environment_config()

        if intake_dir is not None:
            target_dir = self.root_dir / Path(intake_dir)
        else:
            target_dir = self.get_default_setup_dir()

        files = self.discover_and_sort_files(target_dir)

        total_files = len(files)
        total_records = 0
        file_stats: dict[str, int] = {}

        logger.info(
            "Beginning domain intake load for [%s]: %d partition files discovered in %s.",
            self.env_name,
            total_files,
            target_dir,
        )

        collection = Locations()

        for file_path in files:
            count = import_file(collection, file_path)
            file_stats[file_path.name] = count
            total_records += count
            logger.info("Imported %s (%d records into domain collection)", file_path.name, count)

        written = save_to_db(collection)
        logger.info(
            "Ingestion completed: %d total entities committed via Locations collection.",
            written,
        )
        file_stats["__TOTAL__"] = written
        return file_stats


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="load-locations",
        description="Load partitioned location intake files into database via Locations domain collection.",
    )
    parser.add_argument(
        "-e",
        "--env",
        dest="env_name",
        default="DEV",
        help="Target database environment (default: DEV)",
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="intake_dir",
        default=None,
        help="Relative path to directory containing JSON partition files",
    )
    parser.add_argument(
        "--root",
        dest="root_dir",
        default=".",
        help="Root workspace path (default: .)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output logging",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable full debug traces and verbose diagnostic output",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI execution entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = logging.INFO
    if args.debug:
        log_level = logging.DEBUG
    elif not args.verbose:
        log_level = logging.WARNING

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stdout,
    )

    try:
        loader = LocationLoader(env_name=args.env_name, root_dir=args.root_dir)
        stats = loader.load_partitions(intake_dir=args.intake_dir)
        total = stats.get("__TOTAL__", 0)
        print(f"[{args.env_name.upper()}] Initial load successful: {total} locations persisted.")
        return 0
    except Exception as exc:
        logger.error("Intake failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
