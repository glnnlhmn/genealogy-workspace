"""Path: src/gda/db/schema/migrations/v005_indexes.py

Relational DDL migration establishing analytical B-Tree indexes for core entities.

Operational Role:
    Defines performant B-Tree indexes across locations, sites, organizations,
    individuals, families, and facts for onomastic, spatial, chronological,
    and hierarchical queries.
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 5
NAME: str = "core_entity_analytical_indexes"

UP_SQL: str = """
CREATE INDEX IF NOT EXISTS idx_locations_urn ON locations(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_locations_canonical_name ON locations(canonical_name);
CREATE INDEX IF NOT EXISTS idx_locations_parent ON locations(parent_id);
CREATE INDEX IF NOT EXISTS idx_locations_category ON locations(category);

CREATE INDEX IF NOT EXISTS idx_sites_urn ON sites(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_sites_canonical_name ON sites(canonical_name);
CREATE INDEX IF NOT EXISTS idx_sites_location ON sites(location_id);
CREATE INDEX IF NOT EXISTS idx_sites_category ON sites(category);

CREATE INDEX IF NOT EXISTS idx_organizations_urn ON organizations(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_organizations_canonical_name ON organizations(canonical_name);
CREATE INDEX IF NOT EXISTS idx_organizations_category ON organizations(category);
CREATE INDEX IF NOT EXISTS idx_organizations_parent ON organizations(parent_org_id);
CREATE INDEX IF NOT EXISTS idx_organizations_location ON organizations(location_id);
CREATE INDEX IF NOT EXISTS idx_organizations_site ON organizations(meeting_site_id);

CREATE INDEX IF NOT EXISTS idx_individuals_urn ON individuals(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_individuals_canonical_name ON individuals(canonical_name);
CREATE INDEX IF NOT EXISTS idx_individuals_surname ON individuals(surname);
CREATE INDEX IF NOT EXISTS idx_individuals_given_name ON individuals(given_name);
CREATE INDEX IF NOT EXISTS idx_individuals_birth_year ON individuals(birth_year);
CREATE INDEX IF NOT EXISTS idx_individuals_death_year ON individuals(death_year);
CREATE INDEX IF NOT EXISTS idx_individuals_birth_sort ON individuals(birth_date_sort);
CREATE INDEX IF NOT EXISTS idx_individuals_birth_place ON individuals(birth_place_id);
CREATE INDEX IF NOT EXISTS idx_individuals_death_place ON individuals(death_place_id);

CREATE INDEX IF NOT EXISTS idx_families_urn ON families(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_families_union_type ON families(union_type);

CREATE INDEX IF NOT EXISTS idx_facts_urn ON facts(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_facts_subject ON facts(primary_subject_id);
CREATE INDEX IF NOT EXISTS idx_facts_type ON facts(fact_type);
CREATE INDEX IF NOT EXISTS idx_facts_year ON facts(fact_year);
CREATE INDEX IF NOT EXISTS idx_facts_date_sort ON facts(fact_date_sort);
CREATE INDEX IF NOT EXISTS idx_facts_location ON facts(location_id);
CREATE INDEX IF NOT EXISTS idx_facts_site ON facts(site_id);
"""
