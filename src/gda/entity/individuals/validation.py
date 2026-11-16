"""Path: src/gda/entity/individuals/validation.py

Authoritative individual validation, URN verification, and relational diagnostics.

Operational Role:
    Provides deterministic verification of Individual URN structure, naming
    and gender invariants, optional vital place foreign key alignment with
    governing Location and Site entities, and collection-level index and
    graveyard lifecycle synchronization.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.individuals.collection import (
    _extract_location_keys,
    _extract_site_keys,
    _extract_surname_keys,
)
from gda.entity.individuals.errors import IndividualValidationError
from gda.model.atom.gender import GenderAtom
from gda.model.atom.id import LocationID, SiteID
from gda.model.entity.individual import Individual

if TYPE_CHECKING:
    from gda.entity.individuals.collection import Individuals
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.2"

__all__ = [
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_individual",
    "valid_urn",
]

_logger = logging.getLogger(__name__)

_INDIVIDUAL_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["IND"]


def valid_urn(urn: str) -> bool:
    """Validate that an individual URN conforms to the canonical individual URN pattern."""
    clean_urn = urn.strip() if urn else ""
    if not clean_urn or not _INDIVIDUAL_URN_PATTERN.match(clean_urn):
        raise IndividualValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:ind:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    raw_tokens = clean_urn.removeprefix("urn:gda:ind:").split(":")
    if any(not tok for tok in raw_tokens):
        raise IndividualValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters.",
            details={"urn": clean_urn},
        )

    return True


def valid_individual(ind: Individual) -> bool:
    """Validate all individual structural, naming, and gender invariants of an Individual."""
    valid_urn(ind.canonical_urn)

    if not ind.name.canonical or not ind.name.canonical.strip():
        raise IndividualValidationError(
            f"Individual '{ind.id}' canonical name cannot be blank or whitespace.",
            details={"individual_id": str(ind.id)},
        )

    if not isinstance(ind.gender, GenderAtom):
        raise IndividualValidationError(
            f"Individual '{ind.id}' gender must be a GenderAtom instance, "
            f"got {type(ind.gender).__name__}.",
            details={"individual_id": str(ind.id)},
        )

    return True


def _validate_place_fk(
    ind_id: object,
    place_id: object,
    label: str,
    locations_collection: Locations | None,
    sites_collection: Sites | None,
    errors: list[str],
) -> None:
    """Validate a single vital place foreign key on an Individual."""
    if place_id is None:
        return
    if isinstance(place_id, LocationID):
        if locations_collection is not None and place_id not in locations_collection:
            errors.append(
                f"Individual '{ind_id}' {label} references missing or tombstoned Location '{place_id}'."
            )
    elif isinstance(place_id, SiteID):
        if sites_collection is not None and place_id not in sites_collection:
            errors.append(
                f"Individual '{ind_id}' {label} references missing or tombstoned Site '{place_id}'."
            )
    else:
        errors.append(f"Individual '{ind_id}' has invalid {label} reference: '{place_id}'.")


def valid_collection_references(
    collection: Individuals,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> bool:
    """Verify optional birth_place_id and death_place_id references against active collections."""
    errors: list[str] = []

    for ind in collection:
        _validate_place_fk(
            ind.id,
            ind.birth_place_id,
            "birth_place_id",
            locations_collection,
            sites_collection,
            errors,
        )
        _validate_place_fk(
            ind.id,
            ind.death_place_id,
            "death_place_id",
            locations_collection,
            sites_collection,
            errors,
        )

    if errors:
        for err in errors:
            _logger.error("Individual Reference Error: %s", err)
        return False
    return True


def valid_collection_tombstones(collection: Individuals) -> bool:
    """Validate tombstone references and detect self, dangling, or deprecated supersession links."""
    errors: list[str] = []
    all_inds = {i.id: i for i in collection.iter_all()}

    for ind in collection.iter_all():
        if not ind.tombstone.is_deprecated:
            continue

        sup_id = ind.tombstone.superseded_by
        if sup_id is not None:
            if sup_id == ind.id:
                errors.append(f"Tombstoned individual '{ind.id}' cannot supersede itself.")
            elif sup_id not in all_inds:
                errors.append(
                    f"Tombstoned individual '{ind.id}' superseded by missing individual '{sup_id}'."
                )
            else:
                target = all_inds[sup_id]
                if target.tombstone.is_deprecated:
                    errors.append(
                        f"Tombstoned individual '{ind.id}' superseded by another tombstoned individual '{sup_id}'."
                    )

    if errors:
        for err in errors:
            _logger.error("Individual Tombstone Verification Error: %s", err)
        return False
    return True


def valid_collection_indexes(collection: Individuals) -> bool:
    """Validate synchronization between internal registry and secondary lookup indexes."""
    errors: list[str] = []

    for ind in collection:
        if ind.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{ind.canonical_urn}' missing from URN index.")
        elif collection._urn_index[ind.canonical_urn] != ind.id:
            errors.append(f"URN index mismatch for '{ind.canonical_urn}'.")

        for alias in ind.aliases:
            c_alias = alias.strip().lower()
            if c_alias not in collection._alias_index:
                errors.append(
                    f"Alias '{alias}' for individual '{ind.id}' missing from alias index."
                )
            elif ind.id not in collection._alias_index[c_alias]:
                errors.append(
                    f"Individual '{ind.id}' missing from alias index bucket for '{alias}'."
                )

        for s_key in _extract_surname_keys(ind):
            if s_key not in collection._surname_index:
                errors.append(f"Surname '{s_key}' missing from surname index.")
            elif ind.id not in collection._surname_index[s_key]:
                errors.append(
                    f"Individual '{ind.id}' missing from surname index bucket for '{s_key}'."
                )

        for loc_id in _extract_location_keys(ind):
            if loc_id not in collection._location_index:
                errors.append(f"LocationID '{loc_id}' missing from location index.")
            elif ind.id not in collection._location_index[loc_id]:
                errors.append(
                    f"Individual '{ind.id}' missing from location index bucket for '{loc_id}'."
                )

        for site_id in _extract_site_keys(ind):
            if site_id not in collection._site_index:
                errors.append(f"SiteID '{site_id}' missing from site index.")
            elif ind.id not in collection._site_index[site_id]:
                errors.append(
                    f"Individual '{ind.id}' missing from site index bucket for '{site_id}'."
                )

    for ind_id in collection._urn_index.values():
        if ind_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{ind_id}'.")

    if errors:
        for err in errors:
            _logger.error("Individual Index Verification Error: %s", err)
        return False
    return True


def valid_collection_all(
    collection: Individuals,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> bool:
    """Execute all collection-wide validation routines and aggregate diagnostic outcomes."""
    ref_ok = valid_collection_references(
        collection,
        locations_collection=locations_collection,
        sites_collection=sites_collection,
    )
    tomb_ok = valid_collection_tombstones(collection)
    idx_ok = valid_collection_indexes(collection)

    return bool(ref_ok and tomb_ok and idx_ok)
