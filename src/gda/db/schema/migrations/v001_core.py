"""Path: src/gda/db/schema/migrations/v001_core.py

Relational DDL migration defining core knowledge graph entities.

Operational Role:
    Defines SQLite tables for primary domain entities (individuals, families,
    facts, locations, sites, and relationship xrefs) and the migration ledger.
"""

from __future__ import annotations

__version__ = "1.0.0+build.3"

VERSION: int = 1
NAME: str = "canonical_core_entities"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    parent_id TEXT,
    is_primary_local_authority INTEGER DEFAULT 0 NOT NULL,
    is_unincorporated INTEGER DEFAULT 0 NOT NULL,
    coordinates_json TEXT,
    period_json TEXT,
    historical_names_json TEXT,
    alternate_names_json TEXT,
    associated_jurisdiction_ids_json TEXT,
    predecessor_ids_json TEXT,
    successor_ids_json TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    superseded_by TEXT,
    notes_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES locations(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS sites (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    location_id TEXT NOT NULL,
    is_active INTEGER DEFAULT 1 NOT NULL,
    address_json TEXT,
    coordinates_json TEXT,
    period_json TEXT,
    historical_names_json TEXT,
    alternate_names_json TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    superseded_by TEXT,
    notes_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS individuals (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    raw_name TEXT NOT NULL,
    given_name TEXT,
    middle_name TEXT,
    surname TEXT,
    suffix TEXT,
    maiden_name TEXT,
    sex TEXT DEFAULT 'U' NOT NULL,
    is_deceased INTEGER DEFAULT 1 NOT NULL,
    birth_year INTEGER,
    birth_date_sort TEXT,
    birth_date_json TEXT,
    death_year INTEGER,
    death_date_sort TEXT,
    death_date_json TEXT,
    birth_place_id TEXT,
    death_place_id TEXT,
    historical_names_json TEXT,
    alternate_names_json TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    superseded_by TEXT,
    notes_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS families (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT UNIQUE NOT NULL,
    union_json TEXT NOT NULL,
    partner_ids_json TEXT NOT NULL,
    children_json TEXT NOT NULL,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    superseded_by TEXT,
    notes_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

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
    participants_json TEXT,
    citations_json TEXT,
    is_deprecated INTEGER DEFAULT 0 NOT NULL,
    superseded_by TEXT,
    notes_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE SET NULL,
    FOREIGN KEY (site_id) REFERENCES sites(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS individual_family_xrefs (
    xref_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    role TEXT,
    display_label TEXT,
    compiled_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_participant_xrefs (
    xref_id TEXT PRIMARY KEY,
    associated_ind_id TEXT NOT NULL,
    fact_id TEXT NOT NULL,
    primary_subject_id TEXT NOT NULL,
    role TEXT NOT NULL,
    title TEXT,
    event_date_json TEXT,
    compiled_at TEXT NOT NULL
);
"""
