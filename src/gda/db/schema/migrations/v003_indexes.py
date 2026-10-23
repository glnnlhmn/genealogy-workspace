"""Path: src/gda/db/schema/migrations/v003_indexes.py

Tertiary relational DDL migration establishing performance indexes.

Operational Role:
    Defines performant B-Tree indexes for entity lookups, chronological ranges,
    source categories, and relational cross-references.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

VERSION: int = 3
NAME: str = "canonical_performance_indexes"

UP_SQL: str = """
CREATE INDEX IF NOT EXISTS idx_individuals_surname ON individuals(surname);
CREATE INDEX IF NOT EXISTS idx_individuals_given_name ON individuals(given_name);
CREATE INDEX IF NOT EXISTS idx_individuals_urn ON individuals(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_individuals_birth_year ON individuals(birth_year);
CREATE INDEX IF NOT EXISTS idx_individuals_death_year ON individuals(death_year);
CREATE INDEX IF NOT EXISTS idx_individuals_birth_sort ON individuals(birth_date_sort);

CREATE INDEX IF NOT EXISTS idx_families_urn ON families(canonical_urn);

CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(primary_subject_id);
CREATE INDEX IF NOT EXISTS idx_facts_type ON facts(fact_type);
CREATE INDEX IF NOT EXISTS idx_facts_year ON facts(fact_year);
CREATE INDEX IF NOT EXISTS idx_facts_date_sort ON facts(fact_date_sort);
CREATE INDEX IF NOT EXISTS idx_facts_location ON facts(location_id);
CREATE INDEX IF NOT EXISTS idx_facts_site ON facts(site_id);

CREATE INDEX IF NOT EXISTS idx_locations_parent ON locations(parent_id);
CREATE INDEX IF NOT EXISTS idx_locations_category ON locations(category);

CREATE INDEX IF NOT EXISTS idx_sites_location ON sites(location_id);
CREATE INDEX IF NOT EXISTS idx_sites_category ON sites(category);

CREATE INDEX IF NOT EXISTS idx_ind_fam_xref_subject ON individual_family_xrefs(subject_id);
CREATE INDEX IF NOT EXISTS idx_ind_fam_xref_target ON individual_family_xrefs(target_id);

CREATE INDEX IF NOT EXISTS idx_fact_part_xref_ind ON fact_participant_xrefs(associated_ind_id);
CREATE INDEX IF NOT EXISTS idx_fact_part_xref_fact ON fact_participant_xrefs(fact_id);

CREATE INDEX IF NOT EXISTS idx_source_records_urn ON source_records(source_urn);
CREATE INDEX IF NOT EXISTS idx_source_records_category ON source_records(record_category);
CREATE INDEX IF NOT EXISTS idx_source_records_repo ON source_records(repository_id);

CREATE INDEX IF NOT EXISTS idx_media_xref_entity ON media_xrefs(entity_id);
CREATE INDEX IF NOT EXISTS idx_media_xref_media ON media_xrefs(media_id);
"""
