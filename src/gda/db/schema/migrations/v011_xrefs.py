"""Path: src/gda/db/schema/migrations/v011_xrefs.py

Migration v011: Cross-reference bridge and derived index tables (gda.model.xref).

Operational Role:
    Provisions the 9 relational cross-reference tables with compound primary
    keys (xref_key) and B-Tree analytical indexes for FactParticipantXRef,
    IndividualFamilyXRef, IndividualOrganizationXRef, IndividualSourceXRef,
    IndividualSurnameXRef, LocationXRef, MediaXRef, SiteXRef, and SurnameXRef.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 11
NAME: str = "v011_xrefs"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS xref_fact_participants (
    id TEXT PRIMARY KEY,
    fact_id TEXT NOT NULL,
    individual_id TEXT NOT NULL,
    role TEXT NOT NULL,
    fact_type TEXT NOT NULL,
    is_primary_subject INTEGER NOT NULL DEFAULT 1,
    temporal_year INTEGER,
    location_id TEXT,
    site_id TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_individual_families (
    id TEXT PRIMARY KEY,
    family_id TEXT NOT NULL,
    individual_id TEXT NOT NULL,
    is_partner INTEGER NOT NULL,
    pedigree TEXT,
    child_order INTEGER,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_individual_organizations (
    id TEXT PRIMARY KEY,
    organization_id TEXT NOT NULL,
    individual_id TEXT NOT NULL,
    org_category TEXT NOT NULL,
    affiliation_type TEXT NOT NULL,
    membership_status TEXT NOT NULL,
    start_year INTEGER,
    end_year INTEGER,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_individual_sources (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    individual_id TEXT NOT NULL,
    role TEXT NOT NULL,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    is_primary_subject INTEGER NOT NULL DEFAULT 1,
    temporal_year INTEGER,
    location_id TEXT,
    site_id TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_individual_surnames (
    id TEXT PRIMARY KEY,
    surname TEXT NOT NULL,
    individual_id TEXT NOT NULL,
    is_birth_surname INTEGER NOT NULL DEFAULT 1,
    birth_year INTEGER,
    death_year INTEGER,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_locations (
    id TEXT PRIMARY KEY,
    location_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_media (
    id TEXT PRIMARY KEY,
    media_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_sites (
    id TEXT PRIMARY KEY,
    site_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS xref_surnames (
    id TEXT PRIMARY KEY,
    canonical_surname TEXT NOT NULL,
    variant_surname TEXT NOT NULL,
    variant_name_type TEXT NOT NULL,
    variant_phonetic_code TEXT,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_xref_fp_fact ON xref_fact_participants(fact_id);
CREATE INDEX IF NOT EXISTS idx_xref_fp_ind ON xref_fact_participants(individual_id);
CREATE INDEX IF NOT EXISTS idx_xref_fp_year ON xref_fact_participants(temporal_year);

CREATE INDEX IF NOT EXISTS idx_xref_if_fam ON xref_individual_families(family_id);
CREATE INDEX IF NOT EXISTS idx_xref_if_ind ON xref_individual_families(individual_id);

CREATE INDEX IF NOT EXISTS idx_xref_io_org ON xref_individual_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_xref_io_ind ON xref_individual_organizations(individual_id);

CREATE INDEX IF NOT EXISTS idx_xref_is_src ON xref_individual_sources(source_id);
CREATE INDEX IF NOT EXISTS idx_xref_is_ind ON xref_individual_sources(individual_id);
CREATE INDEX IF NOT EXISTS idx_xref_is_cat ON xref_individual_sources(record_category);
CREATE INDEX IF NOT EXISTS idx_xref_is_year ON xref_individual_sources(temporal_year);

CREATE INDEX IF NOT EXISTS idx_xref_isur_sur ON xref_individual_surnames(surname);
CREATE INDEX IF NOT EXISTS idx_xref_isur_ind ON xref_individual_surnames(individual_id);

CREATE INDEX IF NOT EXISTS idx_xref_loc_loc ON xref_locations(location_id);
CREATE INDEX IF NOT EXISTS idx_xref_loc_tgt ON xref_locations(target_id);

CREATE INDEX IF NOT EXISTS idx_xref_med_med ON xref_media(media_id);
CREATE INDEX IF NOT EXISTS idx_xref_med_tgt ON xref_media(target_id);

CREATE INDEX IF NOT EXISTS idx_xref_site_site ON xref_sites(site_id);
CREATE INDEX IF NOT EXISTS idx_xref_site_loc ON xref_sites(location_id);
CREATE INDEX IF NOT EXISTS idx_xref_site_tgt ON xref_sites(target_id);

CREATE INDEX IF NOT EXISTS idx_xref_sur_can ON xref_surnames(canonical_surname);
CREATE INDEX IF NOT EXISTS idx_xref_sur_var ON xref_surnames(variant_surname);
"""
