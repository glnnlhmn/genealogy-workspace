"""Path: src/gda/db/schema/migrations/v010_sources_education_manuscripts_orgs_other.py

Migration v010: Archival source tables and indexes for Education, Manuscripts,
Orgs, and Other Miscellaneous domains.

Operational Role:
    Provisions dedicated relational tables with flattened analytical and foreign-key
    columns plus B-Tree indexes for AcademicCredentialRecord, FamilyBibleRecord,
    NarrativeManuscriptRecord, OrganizationMembershipRecord,
    OrganizationRosterRecord, and OtherMiscellaneousRecord.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 10
NAME: str = "v010_sources_education_manuscripts_orgs_other"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS education_credentials (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    institution_name_raw TEXT NOT NULL,
    subject_name_raw TEXT NOT NULL,
    issued_year INTEGER,
    issued_date_sort TEXT,
    education_level TEXT,
    institution_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    subject_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    degree_or_credential TEXT,
    graduation_year INTEGER,
    publication_title TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS manuscripts_family_bibles (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    family_surname TEXT NOT NULL,
    edition_imprint TEXT,
    publication_year INTEGER,
    original_owner_raw TEXT,
    original_owner_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS manuscripts_narratives (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    title_or_subject TEXT NOT NULL,
    author_or_sender_raw TEXT,
    author_or_sender_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    recipient_raw TEXT,
    recipient_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    collection_name TEXT,
    origin_place_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    destination_place_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    written_year INTEGER,
    written_date_sort TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orgs_memberships (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    individual_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    organization_name_raw TEXT NOT NULL,
    org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
    org_category TEXT NOT NULL,
    affiliation_type TEXT NOT NULL,
    membership_status TEXT NOT NULL,
    role_or_title_raw TEXT,
    degree_or_rank_raw TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orgs_rosters (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    enumeration_year INTEGER NOT NULL,
    jurisdiction_raw TEXT NOT NULL,
    jurisdiction_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    organization_name_raw TEXT NOT NULL,
    org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
    org_category TEXT NOT NULL,
    roster_title TEXT,
    entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS other_miscellaneous_records (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    item_year INTEGER,
    item_date_sort TEXT,
    organization_or_entity_name TEXT,
    organization_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_edu_cred_urn ON education_credentials(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_edu_cred_subj ON education_credentials(subject_id);
CREATE INDEX IF NOT EXISTS idx_edu_cred_loc ON education_credentials(institution_location_id);
CREATE INDEX IF NOT EXISTS idx_edu_cred_grad_yr ON education_credentials(graduation_year);

CREATE INDEX IF NOT EXISTS idx_ms_bible_urn ON manuscripts_family_bibles(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_ms_bible_surname ON manuscripts_family_bibles(family_surname);
CREATE INDEX IF NOT EXISTS idx_ms_bible_owner ON manuscripts_family_bibles(original_owner_id);

CREATE INDEX IF NOT EXISTS idx_ms_narr_urn ON manuscripts_narratives(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_ms_narr_author ON manuscripts_narratives(author_or_sender_id);
CREATE INDEX IF NOT EXISTS idx_ms_narr_recip ON manuscripts_narratives(recipient_id);
CREATE INDEX IF NOT EXISTS idx_ms_narr_origin ON manuscripts_narratives(origin_place_id);
CREATE INDEX IF NOT EXISTS idx_ms_narr_year ON manuscripts_narratives(written_year);

CREATE INDEX IF NOT EXISTS idx_orgs_mem_urn ON orgs_memberships(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_orgs_mem_ind ON orgs_memberships(individual_id);
CREATE INDEX IF NOT EXISTS idx_orgs_mem_org ON orgs_memberships(org_id);

CREATE INDEX IF NOT EXISTS idx_orgs_ros_urn ON orgs_rosters(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_orgs_ros_org ON orgs_rosters(org_id);
CREATE INDEX IF NOT EXISTS idx_orgs_ros_loc ON orgs_rosters(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_orgs_ros_year ON orgs_rosters(enumeration_year);

CREATE INDEX IF NOT EXISTS idx_other_misc_urn ON other_miscellaneous_records(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_other_misc_loc ON other_miscellaneous_records(organization_location_id);
CREATE INDEX IF NOT EXISTS idx_other_misc_year ON other_miscellaneous_records(item_year);
"""
