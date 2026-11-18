"""Path: src/gda/entity/organizations/validation.py

Authoritative organization validation, URN pattern verification, and relational diagnostics.

Operational Role:
    Provides deterministic verification of Organization URN structure, optional
    parent/child chapter hierarchies (supporting standalone root organizations
    without requiring state/national parents), optional foreign key alignment
    with governing Location and Site entities, and collection-level index and
    graveyard lifecycle synchronization.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from gda.core.enums.orgs import OrganizationCategory
from gda.core.logging import GDALogger
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.organizations.errors import OrganizationValidationError
from gda.model.atom.id import OrganizationID
from gda.model.entity.organization import Organization

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations
    from gda.entity.organizations.collection import Organizations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.5"

__all__ = [
    "valid_collection_all",
    "valid_collection_hierarchy",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_organization",
    "valid_urn",
]

_logger = GDALogger(__name__)

_ORG_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["ORG"]


def valid_urn(urn: str) -> bool:
    """Validate that an individual URN conforms to the canonical organization URN pattern."""
    clean_urn = urn.strip() if urn else ""
    if not clean_urn or not _ORG_URN_PATTERN.match(clean_urn):
        raise OrganizationValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:org:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    raw_tokens = clean_urn.removeprefix("urn:gda:org:").split(":")
    if any(not tok for tok in raw_tokens):
        raise OrganizationValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters.",
            details={"urn": clean_urn},
        )

    return True


def valid_organization(org: Organization) -> bool:
    """Validate all individual structural, naming, and classification invariants of an Organization."""
    valid_urn(org.canonical_urn)

    if not org.name.canonical or not org.name.canonical.strip():
        raise OrganizationValidationError(
            f"Organization '{org.id}' canonical name cannot be blank or whitespace.",
            details={"org_id": str(org.id)},
        )

    if not isinstance(org.category, OrganizationCategory):
        raise OrganizationValidationError(
            f"Organization '{org.id}' category must be an OrganizationCategory enum, "
            f"got {type(org.category).__name__}.",
            details={"org_id": str(org.id), "category": str(org.category)},
        )

    return True


def valid_collection_hierarchy(collection: Organizations) -> bool:
    """Validate optional parent_org_id links for cycles, missing parents, or tombstoned parents."""
    errors: list[str] = []
    all_nodes = {org.id: org for org in collection.iter_all()}
    visited: set[OrganizationID] = set()
    rec_stack: set[OrganizationID] = set()

    def _traverse(curr_id: OrganizationID, path: list[str]) -> bool:
        visited.add(curr_id)
        rec_stack.add(curr_id)

        try:
            node = all_nodes.get(curr_id)
            if node and node.parent_org_id:
                p_id = node.parent_org_id
                if p_id in rec_stack:
                    cycle_str = " -> ".join(path + [str(p_id)])
                    errors.append(f"Cycle detected in organization hierarchy: {cycle_str}")
                    return False
                if p_id not in visited and p_id in all_nodes:
                    if not _traverse(p_id, path + [str(p_id)]):
                        return False
            return True
        finally:
            rec_stack.remove(curr_id)

    for org_id in all_nodes:
        if org_id not in visited:
            _traverse(org_id, [str(org_id)])

    for org in collection:
        if org.parent_org_id is None:
            continue

        if org.parent_org_id not in all_nodes:
            errors.append(
                f"Active organization '{org.id}' references missing parent '{org.parent_org_id}'."
            )
            continue

        parent = all_nodes[org.parent_org_id]
        if parent.tombstone.is_deprecated:
            errors.append(
                f"Active organization '{org.id}' references tombstoned parent '{parent.id}'."
            )

    if errors:
        for err in errors:
            _logger.error(f"Organization Hierarchy Error: {err}")
        return False
    return True


def valid_collection_references(
    collection: Organizations,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> bool:
    """Verify optional LocationID and meeting SiteID references against active collections."""
    errors: list[str] = []

    for org in collection:
        if org.location_id is not None:
            if not str(org.location_id).startswith("LOC-"):
                errors.append(
                    f"Organization '{org.id}' has invalid LocationID reference: '{org.location_id}'."
                )
            elif locations_collection is not None and org.location_id not in locations_collection:
                errors.append(
                    f"Organization '{org.id}' references missing or tombstoned Location '{org.location_id}'."
                )

        if org.meeting_site_id is not None:
            if not str(org.meeting_site_id).startswith("SID-"):
                errors.append(
                    f"Organization '{org.id}' has invalid SiteID reference: '{org.meeting_site_id}'."
                )
            elif sites_collection is not None and org.meeting_site_id not in sites_collection:
                errors.append(
                    f"Organization '{org.id}' references missing or tombstoned Site '{org.meeting_site_id}'."
                )

    if errors:
        for err in errors:
            _logger.error(f"Organization Reference Error: {err}")
        return False
    return True


def valid_collection_tombstones(collection: Organizations) -> bool:
    """Validate tombstone references and detect self, dangling, or mismatched supersession links."""
    errors: list[str] = []
    all_orgs = {o.id: o for o in collection.iter_all()}

    for org in collection.iter_all():
        if not org.tombstone.is_deprecated:
            continue

        sup_id = org.tombstone.superseded_by
        if sup_id is not None:
            if sup_id == org.id:
                errors.append(f"Tombstoned organization '{org.id}' cannot supersede itself.")
            elif sup_id not in all_orgs:
                errors.append(
                    f"Tombstoned organization '{org.id}' superseded by missing organization '{sup_id}'."
                )
            else:
                target = all_orgs[sup_id]
                if target.tombstone.is_deprecated:
                    errors.append(
                        f"Tombstoned organization '{org.id}' superseded by another tombstoned organization '{sup_id}'."
                    )
                elif target.category != org.category:
                    errors.append(
                        f"Tombstoned organization '{org.id}' [{org.category.value}] superseded by "
                        f"mismatched category '{sup_id}' [{target.category.value}]."
                    )

    if errors:
        for err in errors:
            _logger.error(f"Organization Tombstone Verification Error: {err}")
        return False
    return True


def _check_org_bucket_membership(
    org_id: OrganizationID,
    key: Any,
    index_map: dict[Any, set[OrganizationID]],
    key_label: str,
    index_label: str,
    errors: list[str],
) -> None:
    """Verify that key exists in index_map and org_id is present in its bucket."""
    if key is None:
        return
    if key not in index_map:
        errors.append(f"{key_label} '{key}' missing from {index_label} index.")
    elif org_id not in index_map[key]:
        errors.append(
            f"Organization '{org_id}' missing from {index_label} index bucket for '{key}'."
        )


def valid_collection_indexes(collection: Organizations) -> bool:
    """Validate synchronization between internal registry and secondary lookup indexes."""
    errors: list[str] = []

    for org in collection:
        if org.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{org.canonical_urn}' missing from URN index.")
        elif collection._urn_index[org.canonical_urn] != org.id:
            errors.append(f"URN index mismatch for '{org.canonical_urn}'.")

        for alias in org.aliases:
            c_alias = alias.strip().lower()
            if c_alias not in collection._alias_index:
                errors.append(
                    f"Alias '{alias}' for organization '{org.id}' missing from alias index."
                )
            elif org.id not in collection._alias_index[c_alias]:
                errors.append(
                    f"Organization '{org.id}' missing from alias index bucket for '{alias}'."
                )

        _check_org_bucket_membership(
            org.id, org.category, collection._category_index, "Category", "category", errors
        )
        _check_org_bucket_membership(
            org.id, org.location_id, collection._location_index, "LocationID", "location", errors
        )
        _check_org_bucket_membership(
            org.id, org.meeting_site_id, collection._site_index, "SiteID", "site", errors
        )
        _check_org_bucket_membership(
            org.id,
            org.parent_org_id,
            collection._parent_index,
            "Parent OrganizationID",
            "parent",
            errors,
        )

    for org_id in collection._urn_index.values():
        if org_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{org_id}'.")

    if errors:
        for err in errors:
            _logger.error(f"Organization Index Verification Error: {err}")
        return False
    return True


def valid_collection_all(
    collection: Organizations,
    locations_collection: Locations | None = None,
    sites_collection: Sites | None = None,
) -> bool:
    """Execute all collection-wide validation routines and aggregate diagnostic outcomes."""
    hier_ok = valid_collection_hierarchy(collection)
    ref_ok = valid_collection_references(
        collection,
        locations_collection=locations_collection,
        sites_collection=sites_collection,
    )
    tomb_ok = valid_collection_tombstones(collection)
    idx_ok = valid_collection_indexes(collection)

    return bool(hier_ok and ref_ok and tomb_ok and idx_ok)
