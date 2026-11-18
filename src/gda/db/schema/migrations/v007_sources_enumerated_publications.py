"""Path: src/gda/db/schema/migrations/v007_sources_enumerated_publications.py

Migration v007: Archival source tables and indexes for Enumerated and Publications domains.

Operational Role:
    Provisions dedicated relational tables with flattened analytical and foreign-key
    columns plus B-Tree indexes for enumerated records (population schedules,
    supplemental schedules, directories, tax/septennial rolls) and publications
    (catalog, newspaper clips, periodical articles).
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 7
NAME: str = "v007_sources_enumerated_publications"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS enumerated_population_schedules (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    schedule_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    enumeration_year INTEGER NOT NULL,
    jurisdiction_raw TEXT NOT NULL,
    jurisdiction_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    state TEXT NOT NULL,
    county TEXT NOT NULL,
    township_or_ward TEXT,
    supervisor_district TEXT,
    enumeration_district TEXT,
    sheet_number TEXT,
    sheet_side TEXT,
    entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enumerated_supplemental_schedules (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    schedule_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    enumeration_year INTEGER NOT NULL,
    jurisdiction_raw TEXT NOT NULL,
    jurisdiction_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    state TEXT NOT NULL,
    county TEXT NOT NULL,
    township_or_ward TEXT,
    enumeration_district TEXT,
    sheet_number TEXT,
    entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enumerated_directories (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    enumeration_year INTEGER NOT NULL,
    jurisdiction_raw TEXT NOT NULL,
    jurisdiction_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    publication_title_raw TEXT NOT NULL,
    page_number_raw TEXT,
    entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enumerated_tax_assessments (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    schedule_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    enumeration_year INTEGER NOT NULL,
    jurisdiction_raw TEXT NOT NULL,
    jurisdiction_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    roll_locator_raw TEXT NOT NULL,
    schedule_name TEXT,
    line_number INTEGER,
    taxpayer_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    taxpayer_name_raw TEXT NOT NULL,
    classification TEXT,
    stated_occupation TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publications_catalog (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    title_raw TEXT NOT NULL,
    pub_code TEXT NOT NULL UNIQUE,
    frequency TEXT,
    publisher_raw TEXT,
    place_of_publication_raw TEXT,
    location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    issn_or_lccn TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publications_newspaper_clips (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    newspaper_name_raw TEXT NOT NULL,
    issue_year INTEGER,
    issue_date_sort TEXT,
    news_category TEXT NOT NULL,
    parent_source_id TEXT,
    pub_code TEXT,
    publication_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    headline_raw TEXT,
    byline_raw TEXT,
    page_column TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS publications_periodical_articles (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    publication_title_raw TEXT NOT NULL,
    published_year INTEGER,
    published_date_sort TEXT,
    publication_kind TEXT NOT NULL,
    parent_source_id TEXT,
    pub_code TEXT,
    institution_org_id TEXT REFERENCES organizations(id) ON DELETE SET NULL,
    author_or_editor_raw TEXT,
    article_or_chapter_title TEXT,
    education_level TEXT,
    entry_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_enum_pop_urn ON enumerated_population_schedules(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_enum_pop_year ON enumerated_population_schedules(enumeration_year);
CREATE INDEX IF NOT EXISTS idx_enum_pop_jurisdiction ON enumerated_population_schedules(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_enum_pop_state_county ON enumerated_population_schedules(state, county);

CREATE INDEX IF NOT EXISTS idx_enum_supp_urn ON enumerated_supplemental_schedules(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_enum_supp_year ON enumerated_supplemental_schedules(enumeration_year);
CREATE INDEX IF NOT EXISTS idx_enum_supp_jurisdiction ON enumerated_supplemental_schedules(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_enum_supp_class ON enumerated_supplemental_schedules(schedule_class);

CREATE INDEX IF NOT EXISTS idx_enum_dir_urn ON enumerated_directories(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_enum_dir_year ON enumerated_directories(enumeration_year);
CREATE INDEX IF NOT EXISTS idx_enum_dir_jurisdiction ON enumerated_directories(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_enum_dir_title ON enumerated_directories(publication_title_raw);

CREATE INDEX IF NOT EXISTS idx_enum_tax_urn ON enumerated_tax_assessments(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_enum_tax_year ON enumerated_tax_assessments(enumeration_year);
CREATE INDEX IF NOT EXISTS idx_enum_tax_jurisdiction ON enumerated_tax_assessments(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_enum_tax_taxpayer ON enumerated_tax_assessments(taxpayer_id);

CREATE INDEX IF NOT EXISTS idx_pub_catalog_urn ON publications_catalog(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_pub_catalog_code ON publications_catalog(pub_code);
CREATE INDEX IF NOT EXISTS idx_pub_catalog_location ON publications_catalog(location_id);

CREATE INDEX IF NOT EXISTS idx_pub_clips_urn ON publications_newspaper_clips(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_pub_clips_year ON publications_newspaper_clips(issue_year);
CREATE INDEX IF NOT EXISTS idx_pub_clips_code ON publications_newspaper_clips(pub_code);
CREATE INDEX IF NOT EXISTS idx_pub_clips_parent ON publications_newspaper_clips(parent_source_id);
CREATE INDEX IF NOT EXISTS idx_pub_clips_location ON publications_newspaper_clips(publication_location_id);

CREATE INDEX IF NOT EXISTS idx_pub_articles_urn ON publications_periodical_articles(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_pub_articles_year ON publications_periodical_articles(published_year);
CREATE INDEX IF NOT EXISTS idx_pub_articles_code ON publications_periodical_articles(pub_code);
CREATE INDEX IF NOT EXISTS idx_pub_articles_parent ON publications_periodical_articles(parent_source_id);
CREATE INDEX IF NOT EXISTS idx_pub_articles_org ON publications_periodical_articles(institution_org_id);
"""
