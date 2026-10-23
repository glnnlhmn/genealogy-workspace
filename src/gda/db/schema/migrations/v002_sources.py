"""Path: src/gda/db/schema/migrations/v002_sources.py

Relational DDL migration defining evidentiary sources and media assets.

Operational Role:
    Defines SQLite tables for source records, document envelopes, and media cross-references.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

VERSION: int = 2
NAME: str = "canonical_source_records"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS source_records (
    source_id TEXT PRIMARY KEY,
    source_urn TEXT UNIQUE NOT NULL,
    record_category TEXT NOT NULL,
    description TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    associated_people_json TEXT,
    media_ids_json TEXT,
    payload_json TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    superseded_by TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS media_xrefs (
    xref_id TEXT PRIMARY KEY,
    entity_id TEXT NOT NULL,
    media_id TEXT NOT NULL,
    caption TEXT,
    date_json TEXT,
    compiled_at TEXT NOT NULL
);
"""
