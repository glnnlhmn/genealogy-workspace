"""Path: src/gda/db/schema/migrations/v001_places.py

Relational DDL migration defining core place entities (locations and sites).

Operational Role:
    Defines the schema_migrations ledger alongside the locations and sites
    tables with flattened analytical columns for NameThing, Address, and
    Coordinates.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 1
NAME: str = "core_places_locations_and_sites"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    raw_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases_json TEXT DEFAULT '[]' NOT NULL,
    alt_spellings_json TEXT DEFAULT '[]' NOT NULL,
    historical_names_json TEXT DEFAULT '[]' NOT NULL,
    name_comment TEXT,
    category TEXT NOT NULL,
    parent_id TEXT,
    is_primary_local_authority INTEGER DEFAULT 0 NOT NULL,
    is_unincorporated INTEGER DEFAULT 0 NOT NULL,
    latitude REAL,
    longitude REAL,
    period_json TEXT,
    predecessor_ids_json TEXT DEFAULT '[]' NOT NULL,
    successor_ids_json TEXT DEFAULT '[]' NOT NULL,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    deprecated_at TEXT,
    superseded_by TEXT,
    notes_json TEXT DEFAULT '[]' NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES locations(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    raw_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases_json TEXT DEFAULT '[]' NOT NULL,
    alt_spellings_json TEXT DEFAULT '[]' NOT NULL,
    historical_names_json TEXT DEFAULT '[]' NOT NULL,
    name_comment TEXT,
    category TEXT NOT NULL,
    location_id TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 NOT NULL,
    address_line_1 TEXT,
    address_line_2 TEXT,
    address_city TEXT,
    address_state TEXT,
    address_postal_code TEXT,
    address_latitude REAL,
    address_longitude REAL,
    latitude REAL,
    longitude REAL,
    period_json TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    deprecated_at TEXT,
    superseded_by TEXT,
    notes_json TEXT DEFAULT '[]' NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE RESTRICT
);
"""
