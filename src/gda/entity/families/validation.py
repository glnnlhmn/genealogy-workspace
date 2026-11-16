"""Path: src/gda/entity/families/validation.py

Authoritative family validation, URN verification, and relational diagnostics.

Operational Role:
    Provides deterministic verification of Family URN structure, spousal and
    filial invariants, optional foreign key alignment with governing Individual
    entities, and collection-level index and graveyard lifecycle synchronization.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.families.errors import FamilyValidationError
from gda.model.atom.id import IndividualID
from gda.model.base.family import ChildLink, FamilyUnion
from gda.model.entity.family import Family

if TYPE_CHECKING:
    from gda.entity.families.collection import Families
    from gda.entity.individuals.collection import Individuals

__version__ = "1.0.0+build.1"

__all__ = [
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_family",
    "valid_urn",
]

_logger = logging.getLogger(__name__)

_FAMILY_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["FAM"]


def valid_urn(urn: str) -> bool:
    """Validate that an individual URN conforms to the canonical family URN pattern."""
    clean_urn = urn.strip() if urn else ""
    if not clean_urn or not _FAMILY_URN_PATTERN.match(clean_urn):
        raise FamilyValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:fam:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    raw_tokens = clean_urn.removeprefix("urn:gda:fam:").split(":")
    if any(not tok for tok in raw_tokens):
        raise FamilyValidationError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters.",
            details={"urn": clean_urn},
        )

    return True


def valid_family(fam: Family) -> bool:
    """Validate all individual structural, partner, child, and union invariants of a Family."""
    valid_urn(fam.canonical_urn)

    if not isinstance(fam.union, FamilyUnion):
        raise FamilyValidationError(
            f"Family '{fam.id}' union must be a FamilyUnion instance, "
            f"got {type(fam.union).__name__}.",
            details={"family_id": str(fam.id)},
        )

    if len(fam.partner_ids) > 2:
        raise FamilyValidationError(
            f"Family '{fam.id}' cannot exceed 2 partners.",
            details={"family_id": str(fam.id)},
        )

    for pid in fam.partner_ids:
        if not isinstance(pid, IndividualID):
            raise FamilyValidationError(
                f"Family '{fam.id}' partner_ids must contain IndividualID instances.",
                details={"family_id": str(fam.id)},
            )

    for link in fam.children:
        if not isinstance(link, ChildLink):
            raise FamilyValidationError(
                f"Family '{fam.id}' children must contain ChildLink instances.",
                details={"family_id": str(fam.id)},
            )

    return True


def valid_collection_references(
    collection: Families,
    individuals_collection: Individuals | None = None,
) -> bool:
    """Verify partner_ids and child_ids references against active Individuals collection."""
    errors: list[str] = []

    for fam in collection:
        for pid in fam.partner_ids:
            if not str(pid).startswith("IND-"):
                errors.append(
                    f"Family '{fam.id}' has invalid partner IndividualID reference: '{pid}'."
                )
            elif individuals_collection is not None and pid not in individuals_collection:
                errors.append(
                    f"Family '{fam.id}' references missing or tombstoned partner Individual '{pid}'."
                )

        for cid in fam.child_ids:
            if not str(cid).startswith("IND-"):
                errors.append(
                    f"Family '{fam.id}' has invalid child IndividualID reference: '{cid}'."
                )
            elif individuals_collection is not None and cid not in individuals_collection:
                errors.append(
                    f"Family '{fam.id}' references missing or tombstoned child Individual '{cid}'."
                )

    if errors:
        for err in errors:
            _logger.error("Family Reference Error: %s", err)
        return False
    return True


def valid_collection_tombstones(collection: Families) -> bool:
    """Validate tombstone references and detect self, dangling, or deprecated supersession links."""
    errors: list[str] = []
    all_fams = {f.id: f for f in collection.iter_all()}

    for fam in collection.iter_all():
        if not fam.tombstone.is_deprecated:
            continue

        sup_id = fam.tombstone.superseded_by
        if sup_id is not None:
            if sup_id == fam.id:
                errors.append(f"Tombstoned family '{fam.id}' cannot supersede itself.")
            elif sup_id not in all_fams:
                errors.append(
                    f"Tombstoned family '{fam.id}' superseded by missing family '{sup_id}'."
                )
            else:
                target = all_fams[sup_id]
                if target.tombstone.is_deprecated:
                    errors.append(
                        f"Tombstoned family '{fam.id}' superseded by another tombstoned family '{sup_id}'."
                    )

    if errors:
        for err in errors:
            _logger.error("Family Tombstone Verification Error: %s", err)
        return False
    return True


def valid_collection_indexes(collection: Families) -> bool:
    """Validate synchronization between internal registry and secondary lookup indexes."""
    errors: list[str] = []

    for fam in collection:
        if fam.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{fam.canonical_urn}' missing from URN index.")
        elif collection._urn_index[fam.canonical_urn] != fam.id:
            errors.append(f"URN index mismatch for '{fam.canonical_urn}'.")

        if fam.union_type not in collection._union_type_index:
            errors.append(f"UnionType '{fam.union_type}' missing from union_type index.")
        elif fam.id not in collection._union_type_index[fam.union_type]:
            errors.append(
                f"Family '{fam.id}' missing from union_type index bucket for '{fam.union_type}'."
            )

        for pid in fam.partner_ids:
            if pid not in collection._partner_index:
                errors.append(f"Partner '{pid}' missing from partner index.")
            elif fam.id not in collection._partner_index[pid]:
                errors.append(f"Family '{fam.id}' missing from partner index bucket for '{pid}'.")

        for cid in fam.child_ids:
            if cid not in collection._child_index:
                errors.append(f"Child '{cid}' missing from child index.")
            elif fam.id not in collection._child_index[cid]:
                errors.append(f"Family '{fam.id}' missing from child index bucket for '{cid}'.")

    for fam_id in collection._urn_index.values():
        if fam_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{fam_id}'.")

    if errors:
        for err in errors:
            _logger.error("Family Index Verification Error: %s", err)
        return False
    return True


def valid_collection_all(
    collection: Families,
    individuals_collection: Individuals | None = None,
) -> bool:
    """Execute all collection-wide validation routines and aggregate diagnostic outcomes."""
    ref_ok = valid_collection_references(
        collection,
        individuals_collection=individuals_collection,
    )
    tomb_ok = valid_collection_tombstones(collection)
    idx_ok = valid_collection_indexes(collection)

    return bool(ref_ok and tomb_ok and idx_ok)
