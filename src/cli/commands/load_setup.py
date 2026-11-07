"""Path: src/cli/commands/load_setup.py

Operational CLI command for bulk loading baseline setup data into an environment database.

Reads partitioned JSON intake envelopes for locations, sites, or both from the
canonical setup root (data/setup/<env>/<entity>), verifies schema compliance,
and commits records into the target database via gda.db session managers.
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

__version__ = "1.0.0+build.1"

logger = logging.getLogger("gda.cli.load_setup")


class SetupLoader(IntrospectableMixin):
    """Orchestrates initial baseline setup loading across locations and sites."""

    def __init__(
        self,
        env_name: str = "DEV",
        root_dir: str | Path = ".",
    ) -> None:
        """Initialize loader settings, resolving configuration paths relative to root."""
        self.root_dir = Path(root_dir).resolve()
        self.env_name = env_name.upper()
        self.pyproject_path = self.root_dir / "pyproject.toml"

        self.locations_schema_path = (
            self.root_dir / "schemas" / "intake" / "dev" / "location_import.schema.json"
        )
        self.sites_schema_path = (
            self.root_dir / "schemas" / "intake" / "dev" / "sites_import.schema.json"
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

    def get_default_setup_dir(self, entity_type: str) -> Path:
        """Derive the canonical baseline setup directory for a given entity type."""
        env_slug = self.env_name.lower()
        if entity_type in ("locations", "sites"):
            return self.root_dir / "data" / "setup" / env_slug / entity_type
        raise ValueError(f"Unsupported entity type: {entity_type}")

    def validate_file_structure(self, file_path: Path, entity_type: str) -> dict[str, Any]:
        """Validate an intake JSON file against envelope and item invariants."""
        with open(file_path, encoding="utf-8") as fh:
            data = json.load(fh)

        required_envelope_keys = {
            "schema_version",
            "record_type",
            "created_at",
            "total_count",
            entity_type,
        }
        missing_envelope = required_envelope_keys - set(data.keys())
        if missing_envelope:
            raise ValueError(
                f"File {file_path.name} missing envelope fields: {sorted(missing_envelope)}"
            )

        expected_record_type = "LOCATION_IMPORT" if entity_type == "locations" else "SITE_IMPORT"
        if data["record_type"] != expected_record_type:
            raise ValueError(
                f"File {file_path.name} has invalid record_type: '{data['record_type']}' "
                f"(expected '{expected_record_type}')"
            )

        items = data.get(entity_type, [])
        if len(items) != data["total_count"]:
            raise ValueError(
                f"File {file_path.name} total_count ({data['total_count']}) does not "
                f"match {entity_type} array length ({len(items)})"
            )

        if entity_type == "locations":
            required_item_keys = {
                "id",
                "name",
                "category",
                "canonical_urn",
                "parent_id",
                "is_primary_local_authority",
                "is_unincorporated",
            }
        else:
            required_item_keys = {
                "id",
                "name",
                "category",
                "canonical_urn",
                "location_id",
                "is_active",
            }

        for idx, item in enumerate(items):
            missing_item = required_item_keys - set(item.keys())
            if missing_item:
                raise ValueError(
                    f"File {file_path.name} {entity_type} at index {idx} "
                    f"missing required fields: {sorted(missing_item)}"
                )

        return data

    def discover_and_sort_files(self, source_dir: Path) -> list[Path]:
        """Scan directory and sort partition files lexicographically."""
        if not source_dir.is_dir():
            raise FileNotFoundError(f"Setup directory does not exist: {source_dir}")

        json_files = sorted(
            [p for p in source_dir.glob("*.json") if p.is_file()],
            key=lambda p: p.name,
        )
        if not json_files:
            raise ValueError(f"No JSON setup partitions discovered in {source_dir}")

        return json_files

    def load_locations(self, source_dir: Path | None = None) -> int:
        """Load baseline location partitions into target database."""
        assert self._session_manager is not None
        target_dir = source_dir or self.get_default_setup_dir("locations")
        files = self.discover_and_sort_files(target_dir)

        now_utc = datetime.now(UTC).isoformat()
        total_records = 0

        logger.info(
            "Loading setup locations for [%s]: %d files discovered in %s",
            self.env_name,
            len(files),
            target_dir,
        )

        with self._session_manager.get_connection() as conn:
            cursor = conn.cursor()
            for file_path in files:
                envelope = self.validate_file_structure(file_path, "locations")
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
                total_records += count
                logger.info("Processed location partition %s (%d records)", file_path.name, count)

            conn.commit()

        return total_records

    def load_sites(self, source_dir: Path | None = None) -> int:
        """Load baseline site partitions into target database."""
        assert self._session_manager is not None
        target_dir = source_dir or self.get_default_setup_dir("sites")
        files = self.discover_and_sort_files(target_dir)

        now_utc = datetime.now(UTC).isoformat()
        total_records = 0

        logger.info(
            "Loading setup sites for [%s]: %d files discovered in %s",
            self.env_name,
            len(files),
            target_dir,
        )

        with self._session_manager.get_connection() as conn:
            cursor = conn.cursor()
            for file_path in files:
                envelope = self.validate_file_structure(file_path, "sites")
                sites = envelope["sites"]
                envelope_created_at = envelope.get("created_at", now_utc)

                for site in sites:
                    name_val = (
                        site["name"]["canonical"]
                        if isinstance(site["name"], dict)
                        else str(site["name"])
                    )
                    cursor.execute(
                        """
                        INSERT OR REPLACE INTO sites (
                            id, name, category, canonical_urn, location_id,
                            is_active, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            site["id"],
                            name_val,
                            site["category"],
                            site["canonical_urn"],
                            site["location_id"],
                            1 if site["is_active"] else 0,
                            envelope_created_at,
                            now_utc,
                        ),
                    )

                count = len(sites)
                total_records += count
                logger.info("Processed site partition %s (%d records)", file_path.name, count)

            conn.commit()

        return total_records

    def run_setup(
        self,
        entity: str = "both",
        source_dir: str | Path | None = None,
    ) -> dict[str, int]:
        """Execute baseline setup loading pipeline for requested entities."""
        self.load_environment_config()
        results: dict[str, int] = {}
        target_path = Path(source_dir) if source_dir else None

        if entity in ("locations", "both"):
            results["locations"] = self.load_locations(
                target_path if entity == "locations" else None
            )

        if entity in ("sites", "both"):
            results["sites"] = self.load_sites(target_path if entity == "sites" else None)

        return results


def build_parser() -> argparse.ArgumentParser:
    """Construct command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="load-setup",
        description="Load initial baseline locations and/or sites into the target database.",
    )
    parser.add_argument(
        "-e",
        "--env",
        dest="env_name",
        default="DEV",
        help="Target database environment (default: DEV)",
    )
    parser.add_argument(
        "--entity",
        dest="entity",
        choices=["locations", "sites", "both"],
        default="both",
        help="Entity types to load: locations, sites, or both (default: both)",
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="source_dir",
        default=None,
        help="Explicit directory override containing JSON setup partition files",
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
        loader = SetupLoader(env_name=args.env_name, root_dir=args.root_dir)
        stats = loader.run_setup(entity=args.entity, source_dir=args.source_dir)
        msg_parts = [f"{count} {ent}" for ent, count in stats.items()]
        print(f"[{args.env_name.upper()}] Setup successful: {', '.join(msg_parts)} persisted.")
        return 0
    except Exception as exc:
        logger.error("Setup load failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
