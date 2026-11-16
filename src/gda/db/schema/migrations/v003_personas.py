"""Path: src/gda/db/schema/migrations/v003_personas.py

Relational DDL migration defining individuals and domestic family units.

Operational Role:
    Defines the individuals and families tables with flattened analytical
    columns for NamePerson, vital dates/places, and FamilyUnion attributes.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 3
NAME: str = "core_individuals_and_families"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS individuals (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    raw_name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    prefix TEXT,
    given_name TEXT,
    middle_name TEXT,
    surname TEXT,
    suffix TEXT,
    married_names_json TEXT DEFAULT '[]' NOT NULL,
    aliases_json TEXT DEFAULT '[]' NOT NULL,
    alt_spellings_json TEXT DEFAULT '[]' NOT NULL,
    name_comment TEXT,
    gender TEXT DEFAULT 'U' NOT NULL,
    is_deceased INTEGER DEFAULT 1 NOT NULL,
    birth_year INTEGER,
    birth_date_sort TEXT,
    birth_date_json TEXT,
    death_year INTEGER,
    death_date_sort TEXT,
    death_date_json TEXT,
    birth_place_id TEXT,
    death_place_id TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    deprecated_at TEXT,
    superseded_by TEXT,
    notes_json TEXT DEFAULT '[]' NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS families (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    union_type TEXT NOT NULL,
    dissolution_type TEXT,
    start_date_json TEXT,
    end_date_json TEXT,
    partner_ids_json TEXT DEFAULT '[]' NOT NULL,
    children_json TEXT DEFAULT '[]' NOT NULL,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    deprecated_at TEXT,
    superseded_by TEXT,
    notes_json TEXT DEFAULT '[]' NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""
