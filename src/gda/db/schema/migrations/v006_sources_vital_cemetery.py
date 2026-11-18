"""Path: src/gda/db/schema/migrations/v006_sources_vital_cemetery.py

Migration v006: Archival source tables and indexes for Vital and Cemetery domains.

Operational Role:
    Provisions dedicated relational tables with flattened analytical and foreign-key
    columns plus B-Tree indexes for vital records (baptisms, births, deaths,
    divorces, marriages) and cemetery records (markers, plot registries).
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 6
NAME: str = "v006_sources_vital_cemetery"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS vital_baptisms (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    baptized_name_raw TEXT NOT NULL,
    church_name_raw TEXT NOT NULL,
    baptism_year INTEGER,
    baptism_date_sort TEXT,
    birth_year INTEGER,
    individual_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    church_org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
    church_site_id TEXT REFERENCES sites(id) ON DELETE SET NULL,
    location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    sex TEXT,
    denomination TEXT,
    father_name_raw TEXT,
    mother_name_raw TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vital_births (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    child_name_raw TEXT NOT NULL,
    birth_year INTEGER,
    birth_date_sort TEXT,
    place_of_birth_raw TEXT NOT NULL,
    child_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    place_of_birth_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    sex TEXT NOT NULL,
    plurality TEXT NOT NULL,
    is_stillborn INTEGER NOT NULL DEFAULT 0,
    certificate_number TEXT,
    registration_district TEXT,
    father_name_raw TEXT,
    mother_maiden_name_raw TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vital_deaths (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    decedent_name_raw TEXT NOT NULL,
    death_year INTEGER,
    death_date_sort TEXT,
    birth_year INTEGER,
    place_of_death_raw TEXT NOT NULL,
    decedent_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    place_of_death_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    disposition_site_id TEXT REFERENCES sites(id) ON DELETE SET NULL,
    sex TEXT NOT NULL,
    is_stillborn INTEGER NOT NULL DEFAULT 0,
    marital_status TEXT,
    manner_of_death TEXT,
    cause_of_death_raw TEXT,
    certificate_number TEXT,
    father_name_raw TEXT,
    mother_maiden_name_raw TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vital_divorces (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    court_name TEXT NOT NULL,
    husband_name_raw TEXT NOT NULL,
    wife_name_raw TEXT NOT NULL,
    decree_year INTEGER,
    decree_date_sort TEXT,
    marriage_year INTEGER,
    husband_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    wife_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    jurisdiction_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    docket_number TEXT,
    state_file_number TEXT,
    decree_type TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS vital_marriages (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    groom_name_raw TEXT NOT NULL,
    bride_name_raw TEXT NOT NULL,
    union_type TEXT NOT NULL,
    marriage_year INTEGER,
    marriage_date_sort TEXT,
    groom_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    bride_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    place_of_marriage_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    license_number TEXT,
    place_of_marriage_raw TEXT,
    religious_denomination TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cemetery_markers (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    cemetery_name_raw TEXT NOT NULL,
    cemetery_site_id TEXT REFERENCES sites(id) ON DELETE SET NULL,
    location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    plot_location TEXT,
    findagrave_id TEXT,
    billiongraves_id TEXT,
    cemetery_grave_id TEXT,
    marker_type TEXT,
    material TEXT,
    physical_condition TEXT,
    survey_year INTEGER,
    interment_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cemetery_registries (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    cemetery_site_id TEXT NOT NULL REFERENCES sites(id) ON DELETE RESTRICT,
    cemetery_name_raw TEXT NOT NULL,
    location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    sexton_or_custodian TEXT,
    survey_year INTEGER,
    plot_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_vital_baptisms_urn ON vital_baptisms(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_vital_baptisms_individual ON vital_baptisms(individual_id);
CREATE INDEX IF NOT EXISTS idx_vital_baptisms_location ON vital_baptisms(location_id);
CREATE INDEX IF NOT EXISTS idx_vital_baptisms_year ON vital_baptisms(baptism_year);

CREATE INDEX IF NOT EXISTS idx_vital_births_urn ON vital_births(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_vital_births_child ON vital_births(child_id);
CREATE INDEX IF NOT EXISTS idx_vital_births_location ON vital_births(place_of_birth_id);
CREATE INDEX IF NOT EXISTS idx_vital_births_year ON vital_births(birth_year);
CREATE INDEX IF NOT EXISTS idx_vital_births_cert ON vital_births(certificate_number);

CREATE INDEX IF NOT EXISTS idx_vital_deaths_urn ON vital_deaths(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_vital_deaths_decedent ON vital_deaths(decedent_id);
CREATE INDEX IF NOT EXISTS idx_vital_deaths_location ON vital_deaths(place_of_death_id);
CREATE INDEX IF NOT EXISTS idx_vital_deaths_site ON vital_deaths(disposition_site_id);
CREATE INDEX IF NOT EXISTS idx_vital_deaths_year ON vital_deaths(death_year);
CREATE INDEX IF NOT EXISTS idx_vital_deaths_cert ON vital_deaths(certificate_number);

CREATE INDEX IF NOT EXISTS idx_vital_divorces_urn ON vital_divorces(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_vital_divorces_husband ON vital_divorces(husband_id);
CREATE INDEX IF NOT EXISTS idx_vital_divorces_wife ON vital_divorces(wife_id);
CREATE INDEX IF NOT EXISTS idx_vital_divorces_location ON vital_divorces(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_vital_divorces_year ON vital_divorces(decree_year);

CREATE INDEX IF NOT EXISTS idx_vital_marriages_urn ON vital_marriages(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_vital_marriages_groom ON vital_marriages(groom_id);
CREATE INDEX IF NOT EXISTS idx_vital_marriages_bride ON vital_marriages(bride_id);
CREATE INDEX IF NOT EXISTS idx_vital_marriages_location ON vital_marriages(place_of_marriage_id);
CREATE INDEX IF NOT EXISTS idx_vital_marriages_year ON vital_marriages(marriage_year);
CREATE INDEX IF NOT EXISTS idx_vital_marriages_license ON vital_marriages(license_number);

CREATE INDEX IF NOT EXISTS idx_cemetery_markers_urn ON cemetery_markers(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_cemetery_markers_site ON cemetery_markers(cemetery_site_id);
CREATE INDEX IF NOT EXISTS idx_cemetery_markers_location ON cemetery_markers(location_id);
CREATE INDEX IF NOT EXISTS idx_cemetery_markers_fag ON cemetery_markers(findagrave_id);

CREATE INDEX IF NOT EXISTS idx_cemetery_registries_urn ON cemetery_registries(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_cemetery_registries_site ON cemetery_registries(cemetery_site_id);
CREATE INDEX IF NOT EXISTS idx_cemetery_registries_location ON cemetery_registries(location_id);
"""
