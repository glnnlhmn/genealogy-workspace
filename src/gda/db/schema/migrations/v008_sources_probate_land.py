"""Path: src/gda/db/schema/migrations/v008_sources_probate_land.py

Migration v008: Archival source tables and indexes for Probate and Land domains.

Operational Role:
    Provisions dedicated relational tables with flattened analytical and foreign-key
    columns plus B-Tree indexes for probate records (wills/letters and estate
    inventories/accounts) and land records (deeds and sovereign/federal grants).
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 8
NAME: str = "v008_sources_probate_land"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS probate_wills (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    court_name TEXT NOT NULL,
    filing_locator TEXT NOT NULL,
    decedent_name_raw TEXT NOT NULL,
    court_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    estate_file_number TEXT,
    book_and_page TEXT,
    decedent_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    decedent_residence_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    written_year INTEGER,
    written_date_sort TEXT,
    probated_year INTEGER,
    probated_date_sort TEXT,
    letters_year INTEGER,
    bequest_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS probate_inventories (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    court_name TEXT NOT NULL,
    filing_locator TEXT NOT NULL,
    decedent_name_raw TEXT NOT NULL,
    court_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    estate_file_number TEXT,
    book_and_page TEXT,
    decedent_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    parent_probate_source_id TEXT,
    appraised_year INTEGER,
    appraised_date_sort TEXT,
    total_appraised_value_numeric REAL,
    currency_code TEXT NOT NULL DEFAULT 'USD',
    item_count INTEGER NOT NULL DEFAULT 0,
    ledger_entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS land_deeds (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    office_title TEXT NOT NULL,
    recording_locator TEXT NOT NULL,
    written_year INTEGER,
    written_date_sort TEXT,
    recorded_year INTEGER,
    recorded_date_sort TEXT,
    office_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    parcel_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    primary_grantor_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    primary_grantee_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    deed_book TEXT,
    page_number TEXT,
    instrument_number TEXT,
    acreage_numeric REAL,
    dower_relinquished INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS land_grants (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    issuing_authority TEXT NOT NULL,
    instrument_locator TEXT NOT NULL,
    patentee_name_raw TEXT NOT NULL,
    office_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    parcel_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    patent_or_warrant_number TEXT,
    certificate_or_entry_number TEXT,
    grant_basis TEXT,
    patentee_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    assignee_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    warrant_year INTEGER,
    surveyed_year INTEGER,
    patented_year INTEGER,
    patented_date_sort TEXT,
    acreage_numeric REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_probate_wills_urn ON probate_wills(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_probate_wills_decedent ON probate_wills(decedent_id);
CREATE INDEX IF NOT EXISTS idx_probate_wills_court_loc ON probate_wills(court_location_id);
CREATE INDEX IF NOT EXISTS idx_probate_wills_file_num ON probate_wills(estate_file_number);
CREATE INDEX IF NOT EXISTS idx_probate_wills_prob_year ON probate_wills(probated_year);

CREATE INDEX IF NOT EXISTS idx_probate_inv_urn ON probate_inventories(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_probate_inv_decedent ON probate_inventories(decedent_id);
CREATE INDEX IF NOT EXISTS idx_probate_inv_parent ON probate_inventories(parent_probate_source_id);
CREATE INDEX IF NOT EXISTS idx_probate_inv_court_loc ON probate_inventories(court_location_id);
CREATE INDEX IF NOT EXISTS idx_probate_inv_year ON probate_inventories(appraised_year);

CREATE INDEX IF NOT EXISTS idx_land_deeds_urn ON land_deeds(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_land_deeds_grantor ON land_deeds(primary_grantor_id);
CREATE INDEX IF NOT EXISTS idx_land_deeds_grantee ON land_deeds(primary_grantee_id);
CREATE INDEX IF NOT EXISTS idx_land_deeds_parcel_loc ON land_deeds(parcel_location_id);
CREATE INDEX IF NOT EXISTS idx_land_deeds_year ON land_deeds(written_year);

CREATE INDEX IF NOT EXISTS idx_land_grants_urn ON land_grants(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_land_grants_patentee ON land_grants(patentee_id);
CREATE INDEX IF NOT EXISTS idx_land_grants_assignee ON land_grants(assignee_id);
CREATE INDEX IF NOT EXISTS idx_land_grants_parcel_loc ON land_grants(parcel_location_id);
CREATE INDEX IF NOT EXISTS idx_land_grants_pat_year ON land_grants(patented_year);
"""
