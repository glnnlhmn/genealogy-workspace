"""Path: src/cli/commands/load_locations.py

Operational CLI command for bulk loading and validating location intake archives.

Reads partitioned JSON location envelopes from data/setup/dev/locations (or configured setup_dir),
verifies schema compliance against schemas/dev/intake/location_import.schema.json, and
initializes records into the target database environment via gda.db session managers.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gda.core.config import DatabaseConfig
from gda.core.introspectable import IntrospectableMixin
from gda.db.session import DatabaseSessionManager

__version__ = "1.0.0+build.6"

logger = logging.getLogger("gda.cli.load_locations")


class LocationLoader(IntrospectableMixin):
    """Orchestrates intake validation, dependency ordering, and database ingestion."""

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
                self.root_dir / "schemas" / "dev" / "intake" / "location_import.schema.json"
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
        """Resolve the configured setup/intake directory for the environment."""
        if not self._env_cfg:
            self.load_environment_config()
        configured_dir = self._env_cfg.get(
            "setup_dir", f"data/setup/{self.env_name.lower()}/locations"
        )
        return self.root_dir / Path(configured_dir)

    def validate_file_structure(self, file_path: Path) -> dict[str, Any]:
        """Validate an intake JSON file against minimal structural and schema requirements."""
        with open(file_path, encoding="utf-8") as fh:
            data = json.load(fh)

        required_envelope_keys = {
            "schema_version",
            "record_type",
            "created_at",
            "total_count",
            "locations",
        }
        missing_envelope = required_envelope_keys - set(data.keys())
        if missing_envelope:
            raise ValueError(
                f"File {file_path.name} missing envelope fields: {sorted(missing_envelope)}"
            )

        if data["record_type"] != "LOCATION_IMPORT":
            raise ValueError(
                f"File {file_path.name} has invalid record_type: '{data['record_type']}'"
            )

        locations = data.get("locations", [])
        if len(locations) != data["total_count"]:
            raise ValueError(
                f"File {file_path.name} total_count ({data['total_count']}) does not "
                f"match locations array length ({len(locations)})"
            )

        required_item_keys = {
            "id",
            "name",
            "category",
            "canonical_urn",
            "parent_id",
            "is_primary_local_authority",
            "is_unincorporated",
        }
        for idx, item in enumerate(locations):
            missing_item = required_item_keys - set(item.keys())
            if missing_item:
                raise ValueError(
                    f"File {file_path.name} location at index {idx} "
                    f"missing required fields: {sorted(missing_item)}"
                )

        return data

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
        """Execute partition discovery, validation, and ingestion into the target database."""
        self.load_environment_config()
        assert self._session_manager is not None

        if intake_dir is not None:
            target_dir = self.root_dir / Path(intake_dir)
        else:
            target_dir = self.get_default_setup_dir()

        files = self.discover_and_sort_files(target_dir)

        total_files = len(files)
        total_records = 0
        file_stats: dict[str, int] = {}

        now_utc = datetime.now(UTC).isoformat()

        logger.info(
            "Beginning intake load for [%s]: %d partition files discovered in %s.",
            self.env_name,
            total_files,
            target_dir,
        )

        with self._session_manager.get_connection() as conn:
            cursor = conn.cursor()
            for file_path in files:
                envelope = self.validate_file_structure(file_path)
                locations = envelope["locations"]
                envelope_created_at = envelope.get("created_at", now_utc)

                for loc in locations:
                    name_val = (
                        loc["name"]["canonical"]
                        if isinstance(loc["name"], dict)
                        else str(loc["name"])
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO locations (
                            id, name, category, canonical_urn, parent_id,
                            is_primary_local_authority, is_unincorporated,
                            created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            loc["id"],
                            name_val,
                            loc["category"],
                            loc["canonical_urn"],
                            loc["parent_id"],
                            1 if loc["is_primary_local_authority"] else 0,
                            1 if loc["is_unincorporated"] else 0,
                            envelope_created_at,
                            now_utc,
                        ),
                    )

                count = len(locations)
                file_stats[file_path.name] = count
                total_records += count
                logger.info("Processed %s (%d records)", file_path.name, count)

            conn.commit()

        logger.info(
            "Ingestion completed: %d total records persisted across %d files.",
            total_records,
            total_files,
        )
        file_stats["__TOTAL__"] = total_records
        return file_stats


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="load-locations",
        description="Load initial partitioned location intake files into database.",
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
        help="Relative path to directory containing JSON partition files (defaults to setup_dir in pyproject.toml)",
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
