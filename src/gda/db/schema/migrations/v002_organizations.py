"""Path: src/gda/db/schema/migrations/v002_organizations.py

Relational DDL migration defining voluntary and institutional organizations.

Operational Role:
    Defines the organizations table with flattened NameThing columns and
    foreign key references to parent organizations, locations, and meeting sites.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 2
NAME: str = "core_organizations"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS organizations (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    raw_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases_json TEXT DEFAULT '[]' NOT NULL,
    alt_spellings_json TEXT DEFAULT '[]' NOT NULL,
    historical_names_json TEXT DEFAULT '[]' NOT NULL,
    name_comment TEXT,
    category TEXT NOT NULL,
    parent_org_id TEXT,
    location_id TEXT,
    meeting_site_id TEXT,
    is_active INTEGER DEFAULT 1 NOT NULL,
    period_json TEXT,
    predecessor_ids_json TEXT DEFAULT '[]' NOT NULL,
    successor_ids_json TEXT DEFAULT '[]' NOT NULL,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    deprecated_at TEXT,
    superseded_by TEXT,
    notes_json TEXT DEFAULT '[]' NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_org_id) REFERENCES organizations(id) ON DELETE SET NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    FOREIGN KEY (meeting_site_id) REFERENCES sites(id) ON DELETE SET NULL
);
"""
