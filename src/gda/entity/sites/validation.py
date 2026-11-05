"""Path: src/gda/entity/sites/validation.py

Authoritative site validation, URN pattern verification, and relational diagnostics.

Operational Role:
    Provides deterministic verification of Site URN structure, physical address,
    foreign key alignment with governing Location entities, and collection-level
    index and graveyard lifecycle synchronization.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from gda.entity.sites.errors import SiteValidationError
from gda.enums.site import SiteType
from gda.model.entity.site import Site

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.6"

__all__ = [
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_locations",
    "valid_collection_tombstones",
    "valid_site",
    "valid_site_address",
    "valid_urn",
]

_logger = logging.getLogger(__name__)

_SITE_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:site:[a-z0-9_:\-]+$")


def valid_urn(urn: str) -> bool:
    """Validate that an individual URN conforms to the canonical site URN pattern.

    Args:
        urn: Canonical URN string to validate.

    Returns:
        True if valid.

    Raises:
        SiteValidationError: If the URN does not conform to the required pattern.
    """
    clean_urn = urn.strip() if urn else ""
    if not clean_urn or not _SITE_URN_PATTERN.match(clean_urn):
        raise SiteValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:site:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    raw_tokens = clean_urn.removeprefix("urn:gda:site:").split(":")
    if any(not tok for tok in raw_tokens):
        raise SiteValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters.",
            details={"urn": clean_urn},
        )

    return True


def valid_site_address(site: Site) -> bool:
    """Validate that an optional physical street address complies with domain invariants.

    Args:
        site: Site entity to inspect.

    Returns:
        True if valid or address is absent.

    Raises:
        SiteValidationError: If address_line_1 is empty or whitespace.
    """
    if site.address is not None:
        if not site.address.address_line_1 or not site.address.address_line_1.strip():
            raise SiteValidationError(
                f"Site '{site.id}' address must contain non-empty address_line_1.",
                details={"site_id": str(site.id)},
            )
    return True


def valid_site(site: Site) -> bool:
    """Validate all individual structural, naming, and classification invariants of a Site.

    Args:
        site: Site domain entity.

    Returns:
        True if all invariants pass.

    Raises:
        SiteValidationError: If any individual invariant is violated.
    """
    valid_urn(site.canonical_urn)
    valid_site_address(site)

    if not site.name.canonical or not site.name.canonical.strip():
        raise SiteValidationError(
            f"Site '{site.id}' canonical name cannot be blank or whitespace.",
            details={"site_id": str(site.id)},
        )

    if not isinstance(site.category, SiteType):
        raise SiteValidationError(
            f"Site '{site.id}' category must be a SiteType enum, got {type(site.category).__name__}.",
            details={"site_id": str(site.id), "category": str(site.category)},
        )

    return True


def valid_collection_locations(
    collection: Sites,
    locations_collection: Locations | None = None,
) -> bool:
    """Verify that every active Site references an active, non-tombstoned LocationID.

    Args:
        collection: In-memory Sites collection.
        locations_collection: Optional Locations collection providing authoritative jurisdiction checks.

    Returns:
        True if all foreign keys resolve cleanly.
    """
    errors: list[str] = []

    for site in collection:
        loc_id = site.location_id
        if not loc_id or not str(loc_id).startswith("LOC-"):
            errors.append(f"Site '{site.id}' has invalid LocationID reference: '{loc_id}'.")
            continue

        if locations_collection is not None:
            if loc_id not in locations_collection:
                errors.append(
                    f"Site '{site.id}' references missing or tombstoned Location '{loc_id}'."
                )

    if errors:
        for err in errors:
            _logger.error("Location Reference Error: %s", err)
        return False
    return True


def valid_collection_tombstones(collection: Sites) -> bool:
    """Validate tombstone references and detect circular or dangling supersession links.

    Args:
        collection: In-memory Sites collection.

    Returns:
        True if tombstone graph integrity is preserved.
    """
    errors: list[str] = []
    all_sites = {s.id: s for s in collection.iter_all()}

    for site in collection.iter_all():
        if not site.tombstone.is_deprecated:
            continue

        sup_id = site.tombstone.superseded_by
        if sup_id is not None:
            if sup_id == site.id:
                errors.append(f"Tombstoned site '{site.id}' cannot supersede itself.")
            elif sup_id not in all_sites:
                errors.append(f"Tombstoned site '{site.id}' superseded by missing site '{sup_id}'.")
            else:
                target = all_sites[sup_id]
                if target.tombstone.is_deprecated:
                    errors.append(
                        f"Tombstoned site '{site.id}' superseded by another tombstoned site '{sup_id}'."
                    )

    if errors:
        for err in errors:
            _logger.error("Site Tombstone Verification Error: %s", err)
        return False
    return True


def valid_collection_indexes(collection: Sites) -> bool:
    """Validate synchronization between internal registry and secondary lookup indexes.

    Args:
        collection: In-memory Sites collection.

    Returns:
        True if all index entries are bidirectional and consistent.
    """
    errors: list[str] = []

    for site in collection:
        if site.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{site.canonical_urn}' missing from URN index.")
        elif collection._urn_index[site.canonical_urn] != site.id:
            errors.append(f"URN index mismatch for '{site.canonical_urn}'.")

        for alias in site.aliases:
            c_alias = alias.strip().lower()
            if c_alias and c_alias not in collection._alias_index:
                errors.append(f"Alias '{alias}' for site '{site.id}' missing from alias index.")

        if site.location_id not in collection._location_index:
            errors.append(f"LocationID '{site.location_id}' missing from location index.")
        elif site.id not in collection._location_index[site.location_id]:
            errors.append(
                f"Site '{site.id}' missing from location index bucket for '{site.location_id}'."
            )

        if site.category not in collection._category_index:
            errors.append(f"Category '{site.category}' missing from category index.")
        elif site.id not in collection._category_index[site.category]:
            errors.append(
                f"Site '{site.id}' missing from category index bucket for '{site.category}'."
            )

    for site_id in collection._urn_index.values():
        if site_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{site_id}'.")

    if errors:
        for err in errors:
            _logger.error("Site Index Verification Error: %s", err)
        return False
    return True


def valid_collection_all(
    collection: Sites,
    locations_collection: Locations | None = None,
) -> bool:
    """Execute all collection-wide validation routines and aggregate diagnostic outcomes.

    Args:
        collection: In-memory Sites collection.
        locations_collection: Optional Locations collection for foreign key verification.

    Returns:
        True if all validation checks succeed.
    """
    loc_ok = valid_collection_locations(collection, locations_collection)
    tomb_ok = valid_collection_tombstones(collection)
    idx_ok = valid_collection_indexes(collection)

    return bool(loc_ok and tomb_ok and idx_ok)
