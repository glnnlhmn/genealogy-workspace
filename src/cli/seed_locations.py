"""Path: src/cli/seed_locations.py

CLI utility to initialize database schema and ingest pre-seeded jurisdictional reference data.

Operational Role:
    Reads authoritative pre-seeded locations (USA, PA, NH, Lancaster divisions)
    from data/reference/us_pa_nh_locations_preload.json, ensures target SQLite
    schema migrations are applied, and commits entities using LocationRowMapper.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from gda.entity.locations.loader import load_preseeded_locations

from gda.db.mapper import LocationRowMapper
from gda.db.schema import SchemaManager
from gda.db.session import DatabaseSessionManager
from gda.entity.locations.collection import Locations

__version__ = "1.0.0+build.1"

_DEFAULT_PRELOAD_PATH = Path("data/reference/us_pa_nh_locations_preload.json")
_DEV_DB_PATH = Path("data/archive_dev.db")
_PROD_DB_PATH = Path("data/archive_prod.db")


def seed_database(db_path: Path, preload_path: Path = _DEFAULT_PRELOAD_PATH) -> int:
    """Initialize schema and insert pre-seeded locations into the specified SQLite database.

    Args:
        db_path: Path to the target SQLite database file.
        preload_path: Path to the pre-seeded location JSON reference file.

    Returns:
        Number of locations written to the database.
    """
    if not preload_path.exists():
        print(
            f"Error: Preload reference file '{preload_path}' not found.",
            file=sys.stderr,
        )
        return 0

    db_path.parent.mkdir(parents=True, exist_ok=True)
    session_mgr = DatabaseSessionManager(db_path=db_path)

    # 1. Apply schema migrations
    schema_mgr = SchemaManager(session_manager=session_mgr)
    applied_migrations = schema_mgr.init_db()
    if applied_migrations:
        print(f"[{db_path.name}] Applied migrations: {applied_migrations}")

    # 2. Populate in-memory collection from clean reference JSON
    collection = Locations()
    count = load_preseeded_locations(collection, preload_path=preload_path)
    print(f"[{db_path.name}] Loaded {count} locations into memory.")

    # 3. Persist entities to SQLite via LocationRowMapper
    mapper = LocationRowMapper()
    inserted_count = 0

    with session_mgr.get_connection() as conn:
        for loc in collection:
            # Check if record already exists to remain idempotent
            existing = conn.execute(
                "SELECT 1 FROM locations WHERE id = ?", (str(loc.id),)
            ).fetchone()
            if not existing:
                row_dict = mapper.to_row(loc)
                columns = ", ".join(row_dict.keys())
                placeholders = ", ".join("?" for _ in row_dict)
                conn.execute(
                    f"INSERT INTO locations ({columns}) VALUES ({placeholders})",
                    list(row_dict.values()),
                )
                inserted_count += 1
        conn.commit()

    print(
        f"[{db_path.name}] Successfully committed {inserted_count} new records to database."
    )
    return inserted_count


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser for seed utility."""
    parser = argparse.ArgumentParser(
        description="Seed locations reference data into target archive databases."
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help=f"Seed into development database ({_DEV_DB_PATH})",
    )
    parser.add_argument(
        "--prod",
        action="store_true",
        help=f"Seed into production database ({_PROD_DB_PATH})",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Seed into both dev and prod databases",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Explicit SQLite database path",
    )
    parser.add_argument(
        "--preload-path",
        type=Path,
        default=_DEFAULT_PRELOAD_PATH,
        help=f"Custom JSON preload file path (default: {_DEFAULT_PRELOAD_PATH})",
    )
    return parser


def main() -> None:
    """CLI orchestrator entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    targets: list[Path] = []
    if args.db_path:
        targets.append(args.db_path)
    if args.dev or args.all:
        targets.append(_DEV_DB_PATH)
    if args.prod or args.all:
        targets.append(_PROD_DB_PATH)

    if not targets:
        # Default to dev if no flags provided
        targets.append(_DEV_DB_PATH)

    for target in targets:
        seed_database(target, preload_path=args.preload_path)


if __name__ == "__main__":
    main()
