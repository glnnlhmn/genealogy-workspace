"""Path: src/gda/db/schema/migrations/v009_sources_immigration_military.py

Migration v009: Archival source tables and indexes for Immigration and Military domains.

Operational Role:
    Provisions dedicated relational tables with flattened analytical and foreign-key
    columns plus B-Tree indexes for immigration records (passenger manifests and
    naturalizations) and military records (drafts, service, pensions, bounty land
    warrants, casualties, and awards).
"""

from __future__ import annotations

__version__ = "1.0.0+build.1"

__all__ = [
    "NAME",
    "UP_SQL",
    "VERSION",
]

VERSION: int = 9
NAME: str = "v009_sources_immigration_military"

UP_SQL: str = """
CREATE TABLE IF NOT EXISTS immigration_manifests (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    port_of_arrival_raw TEXT NOT NULL,
    arrival_year INTEGER,
    arrival_date_sort TEXT,
    manifest_locator TEXT NOT NULL,
    port_of_arrival_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    port_of_departure_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    ship_name TEXT,
    shipping_line TEXT,
    passenger_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS immigration_naturalizations (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    court_name TEXT NOT NULL,
    docket_locator TEXT NOT NULL,
    applicant_name_raw TEXT NOT NULL,
    event_year INTEGER,
    event_date_sort TEXT,
    court_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    applicant_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    current_residence_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    place_of_birth_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    stage TEXT,
    certificate_stub_number TEXT,
    witness_count INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS military_draft_records (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    draft_record_id TEXT NOT NULL,
    registrant_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    registrant_name_raw TEXT NOT NULL,
    draft_year INTEGER NOT NULL,
    board_jurisdiction_raw TEXT NOT NULL,
    card_tier TEXT NOT NULL,
    board_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS military_service_records (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    service_record_id TEXT NOT NULL,
    veteran_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    veteran_name_raw TEXT NOT NULL,
    branch TEXT NOT NULL,
    service_component TEXT NOT NULL,
    unit_designation_raw TEXT NOT NULL,
    rank_raw TEXT NOT NULL,
    service_number_raw TEXT,
    enlistment_year INTEGER,
    separation_year INTEGER,
    separation_character TEXT NOT NULL,
    enlistment_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS military_pension_records (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    veteran_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    veteran_name_raw TEXT NOT NULL,
    claimant_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    claimant_name_raw TEXT NOT NULL,
    claimant_role TEXT NOT NULL,
    payment_authority TEXT NOT NULL,
    application_year INTEGER NOT NULL,
    application_number_raw TEXT,
    certificate_number_raw TEXT,
    application_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS military_bounty_land_warrants (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    veteran_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    veteran_name_raw TEXT NOT NULL,
    warrantee_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    warrantee_name_raw TEXT NOT NULL,
    claimant_role TEXT NOT NULL,
    bounty_act TEXT NOT NULL,
    warrant_number_raw TEXT NOT NULL,
    acreage INTEGER NOT NULL,
    warrant_year INTEGER NOT NULL,
    patent_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    assignee_id TEXT REFERENCES individuals(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS military_casualty_records (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    record_class TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    servicemember_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    servicemember_name_raw TEXT NOT NULL,
    branch TEXT NOT NULL,
    casualty_category TEXT NOT NULL,
    casualty_year INTEGER NOT NULL,
    unit_designation_raw TEXT NOT NULL,
    rank_raw TEXT NOT NULL,
    casualty_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS military_award_records (
    id TEXT PRIMARY KEY,
    canonical_urn TEXT NOT NULL UNIQUE,
    record_category TEXT NOT NULL,
    record_type TEXT NOT NULL,
    repository_id TEXT NOT NULL,
    description TEXT NOT NULL,
    recipient_id TEXT NOT NULL REFERENCES individuals(id) ON DELETE CASCADE,
    recipient_name_raw TEXT NOT NULL,
    award_name_raw TEXT NOT NULL,
    branch TEXT NOT NULL,
    award_tier TEXT NOT NULL,
    award_scope TEXT NOT NULL,
    award_year INTEGER NOT NULL,
    action_year INTEGER,
    is_posthumous INTEGER NOT NULL DEFAULT 0,
    action_location_id TEXT REFERENCES locations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deprecated_at TEXT,
    payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_imm_man_urn ON immigration_manifests(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_imm_man_year ON immigration_manifests(arrival_year);
CREATE INDEX IF NOT EXISTS idx_imm_man_port ON immigration_manifests(port_of_arrival_id);
CREATE INDEX IF NOT EXISTS idx_imm_man_ship ON immigration_manifests(ship_name);

CREATE INDEX IF NOT EXISTS idx_imm_nat_urn ON immigration_naturalizations(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_imm_nat_applicant ON immigration_naturalizations(applicant_id);
CREATE INDEX IF NOT EXISTS idx_imm_nat_court_loc ON immigration_naturalizations(court_location_id);
CREATE INDEX IF NOT EXISTS idx_imm_nat_year ON immigration_naturalizations(event_year);

CREATE INDEX IF NOT EXISTS idx_mil_draft_urn ON military_draft_records(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_mil_draft_reg ON military_draft_records(registrant_id);
CREATE INDEX IF NOT EXISTS idx_mil_draft_year ON military_draft_records(draft_year);
CREATE INDEX IF NOT EXISTS idx_mil_draft_loc ON military_draft_records(board_location_id);

CREATE INDEX IF NOT EXISTS idx_mil_srv_urn ON military_service_records(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_mil_srv_vet ON military_service_records(veteran_id);
CREATE INDEX IF NOT EXISTS idx_mil_srv_branch ON military_service_records(branch);
CREATE INDEX IF NOT EXISTS idx_mil_srv_enl_year ON military_service_records(enlistment_year);

CREATE INDEX IF NOT EXISTS idx_mil_pen_urn ON military_pension_records(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_mil_pen_vet ON military_pension_records(veteran_id);
CREATE INDEX IF NOT EXISTS idx_mil_pen_claimant ON military_pension_records(claimant_id);
CREATE INDEX IF NOT EXISTS idx_mil_pen_year ON military_pension_records(application_year);

CREATE INDEX IF NOT EXISTS idx_mil_blw_urn ON military_bounty_land_warrants(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_mil_blw_vet ON military_bounty_land_warrants(veteran_id);
CREATE INDEX IF NOT EXISTS idx_mil_blw_warrantee ON military_bounty_land_warrants(warrantee_id);
CREATE INDEX IF NOT EXISTS idx_mil_blw_year ON military_bounty_land_warrants(warrant_year);

CREATE INDEX IF NOT EXISTS idx_mil_cas_urn ON military_casualty_records(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_mil_cas_member ON military_casualty_records(servicemember_id);
CREATE INDEX IF NOT EXISTS idx_mil_cas_year ON military_casualty_records(casualty_year);
CREATE INDEX IF NOT EXISTS idx_mil_cas_loc ON military_casualty_records(casualty_location_id);

CREATE INDEX IF NOT EXISTS idx_mil_awd_urn ON military_award_records(canonical_urn);
CREATE INDEX IF NOT EXISTS idx_mil_awd_recipient ON military_award_records(recipient_id);
CREATE INDEX IF NOT EXISTS idx_mil_awd_year ON military_award_records(award_year);
CREATE INDEX IF NOT EXISTS idx_mil_awd_tier ON military_award_records(award_tier);
"""
