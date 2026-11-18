"""Path: src/gda/entity/facts/validation.py

Authoritative evidentiary fact validation, URN verification, and relational diagnostics.

Operational Role:
    Provides deterministic verification of Fact URN structure, subject and
    participant invariants, optional foreign key alignment with governing
    Location, Site, Individual, and Family entities, and collection-level index
    and graveyard lifecycle synchronization.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from gda.core.enums.core import FactType
from gda.core.logging import GDALogger
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.facts.errors import FactValidationError
from gda.model.atom.id import FactID, FamilyID, IndividualID
from gda.model.entity.fact import Fact

if TYPE_CHECKING:
    from gda.entity.facts.collection import Facts
    from gda.entity.families.collection import Families
    from gda.entity.individuals.collection import Individuals
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.4"

__all__ = [
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_fact",
    "valid_urn",
]

_logger = GDALogger(__name__)

_FACT_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["FID"]


def valid_urn(urn: str) -> bool:
    """Validate that an individual URN conforms to the canonical fact URN pattern."""
    clean_urn = urn.strip() if urn else ""
    if not clean_urn or not _FACT_URN_PATTERN.match(clean_urn):
        raise FactValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:fact:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    raw_tokens = clean_urn.removeprefix("urn:gda:fact:").split(":")
    if any(not tok for tok in raw_tokens):
        raise FactValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters.",
            details={"urn": clean_urn},
        )

    return True


def valid_fact(fact: Fact) -> bool:
    """Validate all individual structural, subject, and classification invariants of a Fact."""
    valid_urn(fact.canonical_urn)

    if not fact.title or not fact.title.strip():
        raise FactValidationError(
            f"Fact '{fact.id}' title cannot be blank or whitespace.",
            details={"fact_id": str(fact.id)},
        )

    if not isinstance(fact.fact_type, FactType):
        raise FactValidationError(
            f"Fact '{fact.id}' fact_type must be a FactType enum, "
            f"got {type(fact.fact_type).__name__}.",
            details={"fact_id": str(fact.id), "fact_type": str(fact.fact_type)},
        )

    if not isinstance(fact.primary_subject_id, (IndividualID, FamilyID)):
        raise FactValidationError(
            f"Fact '{fact.id}' primary_subject_id must be IndividualID or FamilyID.",
            details={"fact_id": str(fact.id)},
        )

    return True


def _check_fact_subject_and_participants(
    fact: Fact,
    individuals_collection: Individuals | None,
    families_collection: Families | None,
    errors: list[str],
) -> None:
    """Verify primary_subject_id and participant_ids against active persona collections."""
    subj = fact.primary_subject_id
    if isinstance(subj, IndividualID):
        if individuals_collection is not None and subj not in individuals_collection:
            errors.append(
                f"Fact '{fact.id}' references missing or tombstoned primary subject Individual '{subj}'."
            )
    elif isinstance(subj, FamilyID):
        if families_collection is not None and subj not in families_collection:
            errors.append(
                f"Fact '{fact.id}' references missing or tombstoned primary subject Family '{subj}'."
            )
    else:
        errors.append(f"Fact '{fact.id}' has invalid primary_subject_id reference: '{subj}'.")

    if individuals_collection is not None:
        for pid in fact.participant_ids:
            if pid not in individuals_collection:
                errors.append(
                    f"Fact '{fact.id}' references missing or tombstoned participant Individual '{pid}'."
                )


def _check_fact_place_references(
    fact: Fact,
    locations_collection: Locations | None,
    sites_collection: Sites | None,
    errors: list[str],
) -> None:
    """Verify optional LocationID and SiteID references on a Fact."""
    if fact.location_id is not None:
        if not str(fact.location_id).startswith("LOC-"):
            errors.append(
                f"Fact '{fact.id}' has invalid LocationID reference: '{fact.location_id}'."
            )
        elif locations_collection is not None and fact.location_id not in locations_collection:
            errors.append(
                f"Fact '{fact.id}' references missing or tombstoned Location '{fact.location_id}'."
            )

    if fact.site_id is not None:
        if not str(fact.site_id).startswith("SID-"):
            errors.append(f"Fact '{fact.id}' has invalid SiteID reference: '{fact.site_id}'.")
        elif sites_collection is not None and fact.site_id not in sites_collection:
            errors.append(
                f"Fact '{fact.id}' references missing or tombstoned Site '{fact.site_id}'."
            )


def valid_collection_references(
    collection: Facts,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
    individuals_collection: Individuals | None = None,
    families_collection: Families | None = None,
) -> bool:
    """Verify optional LocationID, SiteID, primary_subject_id, and participant references."""
    errors: list[str] = []

    for fact in collection:
        _check_fact_subject_and_participants(
            fact, individuals_collection, families_collection, errors
        )
        _check_fact_place_references(fact, locations_collection, sites_collection, errors)

    if errors:
        for err in errors:
            _logger.error(f"Fact Reference Error: {err}")
        return False
    return True


def valid_collection_tombstones(collection: Facts) -> bool:
    """Validate tombstone references and detect self, dangling, or deprecated supersession links."""
    errors: list[str] = []
    all_facts = {f.id: f for f in collection.iter_all()}

    for fact in collection.iter_all():
        if not fact.tombstone.is_deprecated:
            continue

        sup_id = fact.tombstone.superseded_by
        if sup_id is not None:
            if sup_id == fact.id:
                errors.append(f"Tombstoned fact '{fact.id}' cannot supersede itself.")
            elif sup_id not in all_facts:
                errors.append(f"Tombstoned fact '{fact.id}' superseded by missing fact '{sup_id}'.")
            else:
                target = all_facts[sup_id]
                if target.tombstone.is_deprecated:
                    errors.append(
                        f"Tombstoned fact '{fact.id}' superseded by another tombstoned fact '{sup_id}'."
                    )

    if errors:
        for err in errors:
            _logger.error(f"Fact Tombstone Verification Error: {err}")
        return False
    return True


def _check_fact_bucket_membership(
    fact_id: FactID,
    key: Any,
    index_map: dict[Any, set[FactID]],
    key_label: str,
    index_label: str,
    errors: list[str],
) -> None:
    """Verify that key exists in index_map and fact_id is present in its bucket."""
    if key is None:
        return
    if key not in index_map:
        errors.append(f"{key_label} '{key}' missing from {index_label} index.")
    elif fact_id not in index_map[key]:
        errors.append(f"Fact '{fact_id}' missing from {index_label} index bucket for '{key}'.")


def valid_collection_indexes(collection: Facts) -> bool:
    """Validate synchronization between internal registry and secondary lookup indexes."""
    errors: list[str] = []

    for fact in collection:
        if fact.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{fact.canonical_urn}' missing from URN index.")
        elif collection._urn_index[fact.canonical_urn] != fact.id:
            errors.append(f"URN index mismatch for '{fact.canonical_urn}'.")

        _check_fact_bucket_membership(
            fact.id,
            fact.primary_subject_id,
            collection._subject_index,
            "Primary subject",
            "subject",
            errors,
        )
        _check_fact_bucket_membership(
            fact.id, fact.fact_type, collection._type_index, "FactType", "type", errors
        )
        _check_fact_bucket_membership(
            fact.id, fact.location_id, collection._location_index, "LocationID", "location", errors
        )
        _check_fact_bucket_membership(
            fact.id, fact.site_id, collection._site_index, "SiteID", "site", errors
        )

        for pid in fact.participant_ids:
            _check_fact_bucket_membership(
                fact.id, pid, collection._participant_index, "Participant", "participant", errors
            )

    for fact_id in collection._urn_index.values():
        if fact_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{fact_id}'.")

    if errors:
        for err in errors:
            _logger.error(f"Fact Index Verification Error: {err}")
        return False
    return True


def valid_collection_all(
    collection: Facts,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
    individuals_collection: Individuals | None = None,
    families_collection: Families | None = None,
) -> bool:
    """Execute all collection-wide validation routines and aggregate diagnostic outcomes."""
    ref_ok = valid_collection_references(
        collection,
        locations_collection=locations_collection,
        sites_collection=sites_collection,
        individuals_collection=individuals_collection,
        families_collection=families_collection,
    )
    tomb_ok = valid_collection_tombstones(collection)
    idx_ok = valid_collection_indexes(collection)

    return bool(ref_ok and tomb_ok and idx_ok)
