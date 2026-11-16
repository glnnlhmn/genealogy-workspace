"""Path: src/gda/db/schema/migrations/v004_facts.py

Relational DDL migration defining evidentiary fact assertions.

Operational Role:
    Defines the facts table with chronological sort keys, spatial foreign keys
    (locations and sites), participant lists, and source citations.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 4
NAME: str = "core_facts"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS facts (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    fact_type TEXT NOT NULL,
    title TEXT NOT NULL,
    primary_subject_id TEXT NOT NULL,
    fact_year INTEGER,
    fact_date_sort TEXT,
    date_json TEXT,
    location_id TEXT,
    site_id TEXT,
    value TEXT,
    description TEXT,
    narrative TEXT,
    participants_json TEXT DEFAULT '[]' NOT NULL,
    citations_json TEXT DEFAULT '[]' NOT NULL,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    deprecated_at TEXT,
    superseded_by TEXT,
    notes_json TEXT DEFAULT '[]' NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE SET NULL
);
"""
