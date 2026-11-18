"""Path: src/gda/entity/locations/validation.py

Authoritative jurisdictional URN, structural hierarchy, and path validation routines.

Operational Role:
    Provides deterministic verification of jurisdictional tier sequences,
    URN structural conformity across Patterns 1-7, formatted location display
    strings, and deep relational graph integrity including cycle, tombstone,
    and index synchronization diagnostics.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from gda.core.enums.location import JurisdictionCategory
from gda.core.errors import ModelFormatError
from gda.core.logging import GDALogger
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.locations.errors import LocationHierarchyError
from gda.model.atom.id import LocationID
from gda.util.text import clean_string

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations

__version__ = "1.0.0+build.26"

__all__ = [
    "valid_collection_all",
    "valid_collection_cycles",
    "valid_collection_indexes",
    "valid_collection_patterns",
    "valid_collection_roots",
    "valid_collection_tombstones",
    "valid_display_text",
    "valid_hierarchy",
    "valid_urn",
    "validate_urn_tier_sequence",
]

_logger = GDALogger(__name__)

_LOCATION_URN_PATTERN: re.Pattern[str] = ENTITY_URN_REGEXES["LOC"]

_CATEGORY_ALLOWED_SEGMENT_COUNTS: dict[JurisdictionCategory, set[int]] = {
    JurisdictionCategory.COUNTRY: {1},
    JurisdictionCategory.STATOID: {2},
    JurisdictionCategory.COUNTY_EQUIVALENT: {3},
    JurisdictionCategory.CIVIL_TOWNSHIP: {4},
    JurisdictionCategory.MUNICIPALITY: {3, 4, 5},
    JurisdictionCategory.UNINCORPORATED_PLACE: {3, 4, 5},
}

_CATEGORY_ALLOWED_COMMA_COUNTS: dict[JurisdictionCategory, set[int]] = {
    JurisdictionCategory.COUNTRY: {0},
    JurisdictionCategory.STATOID: {1},
    JurisdictionCategory.COUNTY_EQUIVALENT: {2},
    JurisdictionCategory.CIVIL_TOWNSHIP: {3},
    JurisdictionCategory.MUNICIPALITY: {2, 3, 4},
    JurisdictionCategory.UNINCORPORATED_PLACE: {2, 3, 4},
}

_VALID_PARENT_CATEGORIES: dict[JurisdictionCategory, tuple[JurisdictionCategory, ...]] = {
    JurisdictionCategory.STATOID: (JurisdictionCategory.COUNTRY,),
    JurisdictionCategory.COUNTY_EQUIVALENT: (JurisdictionCategory.STATOID,),
    JurisdictionCategory.CIVIL_TOWNSHIP: (JurisdictionCategory.COUNTY_EQUIVALENT,),
    JurisdictionCategory.MUNICIPALITY: (
        JurisdictionCategory.CIVIL_TOWNSHIP,
        JurisdictionCategory.COUNTY_EQUIVALENT,
        JurisdictionCategory.STATOID,
    ),
    JurisdictionCategory.UNINCORPORATED_PLACE: (
        JurisdictionCategory.CIVIL_TOWNSHIP,
        JurisdictionCategory.COUNTY_EQUIVALENT,
        JurisdictionCategory.STATOID,
    ),
}


def valid_urn(
    urn: str,
    category: JurisdictionCategory | str | None = None,
) -> bool:
    """Validate that an individual URN conforms to the canonical location URN pattern."""
    clean_urn = urn.strip() if isinstance(urn, str) else ""
    if not clean_urn or not clean_urn.startswith("urn:gda:loc:"):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:loc:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    suffix = clean_urn.removeprefix("urn:gda:loc:")
    if not suffix:
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. Missing path segments after prefix.",
            details={"urn": clean_urn},
        )

    raw_tokens = suffix.split(":")
    if all(not tok for tok in raw_tokens):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. Missing path segments after prefix.",
            details={"urn": clean_urn},
        )

    if any(not tok for tok in raw_tokens):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters.",
            details={"urn": clean_urn},
        )

    if not _LOCATION_URN_PATTERN.match(clean_urn):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:loc:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens.",
            details={"urn": clean_urn},
        )

    if category is not None:
        if isinstance(category, JurisdictionCategory):
            res_cat = category
        else:
            try:
                res_cat = JurisdictionCategory(category)
            except ValueError as exc:
                raise ModelFormatError(f"Invalid jurisdiction category: '{category}'.") from exc

        if res_cat not in _CATEGORY_ALLOWED_SEGMENT_COUNTS:
            raise ModelFormatError(f"Unsupported jurisdiction category: '{res_cat.value}'.")

        allowed_counts = _CATEGORY_ALLOWED_SEGMENT_COUNTS[res_cat]
        actual_count = len(raw_tokens)
        if actual_count not in allowed_counts:
            raise ModelFormatError(
                f"URN '{clean_urn}' has {actual_count} hierarchical segment(s), "
                f"which is invalid for category '{res_cat.value}' "
                f"(allowed segment counts: {sorted(allowed_counts)}).",
                details={
                    "urn": clean_urn,
                    "category": res_cat.value,
                    "segment_count": actual_count,
                },
            )

    return True


def _split_and_validate_path_parts(display_text: str) -> list[str]:
    """Split and validate a comma-delimited location path string."""
    clean_text = clean_string(display_text)
    if not clean_text:
        raise ModelFormatError("Location path string cannot be empty or whitespace.")

    if clean_text.startswith(",") or clean_text.endswith(","):
        raise ModelFormatError(
            f"Invalid location path '{clean_text}': cannot have leading or trailing commas."
        )

    parts = [clean_string(part) for part in clean_text.split(",")]
    if any(not p for p in parts):
        raise ModelFormatError(
            f"Invalid location path '{clean_text}': Contains empty segments between commas."
        )

    if len(parts) - 1 > 4:
        raise ModelFormatError(
            f"Location path '{clean_text}' exceeds maximum allowed depth of 4 commas (5 tiers)."
        )

    return [p for p in parts if p]


def valid_display_text(
    display_text: str,
    category: JurisdictionCategory | str | None = None,
) -> bool:
    """Validate that a comma-separated location display string conforms to tier depth rules."""
    parts = _split_and_validate_path_parts(display_text)

    if category is not None:
        res_cat = (
            category
            if isinstance(category, JurisdictionCategory)
            else JurisdictionCategory(category)
        )
        allowed_commas = _CATEGORY_ALLOWED_COMMA_COUNTS[res_cat]
        comma_count = len(parts) - 1
        if comma_count not in allowed_commas:
            raise ModelFormatError(
                f"Display text '{display_text}' has {comma_count} comma delimiter(s), "
                f"which is invalid for category '{res_cat.value}' "
                f"(allowed comma counts: {sorted(allowed_commas)}).",
                details={
                    "display_text": display_text,
                    "category": res_cat.value,
                    "comma_count": comma_count,
                },
            )

    return True


def valid_hierarchy(
    nodes: list[tuple[str, str | None, JurisdictionCategory, bool]],
) -> bool:
    """Validate a raw list of (loc_id, parent_id, category, is_deprecated) location tuples."""
    if not nodes:
        return True

    node_map: dict[str, tuple[str | None, JurisdictionCategory, bool]] = {}
    for raw_id, parent_id, category, is_deprecated in nodes:
        loc_id = clean_string(raw_id)
        if not loc_id:
            raise ModelFormatError("Location ID in hierarchy cannot be blank.")
        if loc_id in node_map:
            raise ModelFormatError(f"Duplicate location ID encountered: '{loc_id}'.")
        if parent_id == loc_id:
            raise LocationHierarchyError(
                f"Cyclic reference detected: '{loc_id}' references itself as parent."
            )
        node_map[loc_id] = (parent_id, category, is_deprecated)

    for loc_id, (parent_id, category, is_deprecated) in node_map.items():
        if category == JurisdictionCategory.COUNTRY:
            if parent_id is not None:
                raise ModelFormatError(
                    f"COUNTRY location '{loc_id}' cannot have a parent jurisdiction."
                )
            continue

        if parent_id is None:
            raise ModelFormatError(
                f"Non-COUNTRY location '{loc_id}' ({category.value}) must have a valid parent jurisdiction."
            )

        if parent_id not in node_map:
            raise ModelFormatError(
                f"Location '{loc_id}' references non-existent parent '{parent_id}'."
            )

        parent_parent_id, parent_cat, parent_deprecated = node_map[parent_id]
        allowed_parents = _VALID_PARENT_CATEGORIES.get(category, ())
        if parent_cat not in allowed_parents:
            allowed_str = ", ".join(p.value for p in allowed_parents)
            raise ModelFormatError(
                f"Invalid parent category '{parent_cat.value}' for '{loc_id}' ({category.value}). "
                f"Expected parent of type: {allowed_str}."
            )

        if not is_deprecated:
            if parent_deprecated:
                raise LocationHierarchyError(
                    f"Active location '{loc_id}' cannot link to tombstoned parent '{parent_id}'."
                )
            curr_anc_id = parent_parent_id
            while curr_anc_id is not None and curr_anc_id in node_map:
                next_anc_id, _, anc_deprecated = node_map[curr_anc_id]
                if anc_deprecated:
                    raise LocationHierarchyError(
                        f"Active location '{loc_id}' has tombstoned ancestor '{curr_anc_id}'."
                    )
                curr_anc_id = next_anc_id

    return True


def validate_urn_tier_sequence(
    country: str | None,
    state: str | None = None,
    county: str | None = None,
    township: str | None = None,
    local: str | None = None,
) -> None:
    """Validate that a 5-tier jurisdictional input sequence satisfies dependency rules."""
    c = clean_string(country)
    s = clean_string(state)
    co = clean_string(county)
    twp = clean_string(township)
    loc = clean_string(local)

    if not c:
        raise ModelFormatError("Location hierarchy must contain a country.")
    if (co or twp or loc) and not s:
        raise ModelFormatError("Cannot attach sub-tiers to country without state.")
    if twp and not co:
        raise ModelFormatError("Cannot attach township without county.")


def valid_collection_cycles(collection: Locations) -> bool:
    """Detect circular parent references across all records in the collection."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}
    visited: set[LocationID] = set()
    rec_stack: set[LocationID] = set()

    def _traverse(curr_id: LocationID, path: list[str]) -> bool:
        visited.add(curr_id)
        rec_stack.add(curr_id)

        try:
            node = all_nodes.get(curr_id)
            if node and node.parent_id:
                p_id = node.parent_id
                if p_id in rec_stack:
                    cycle_str = " -> ".join(path + [str(p_id)])
                    errors.append(f"Cycle detected in location hierarchy: {cycle_str}")
                    return False
                if p_id not in visited and p_id in all_nodes:
                    if not _traverse(p_id, path + [str(p_id)]):
                        return False
            return True
        finally:
            rec_stack.remove(curr_id)

    for loc_id in all_nodes:
        if loc_id not in visited:
            _traverse(loc_id, [str(loc_id)])

    if errors:
        for err in errors:
            _logger.error(f"Hierarchy Cycle Error: {err}")
        return False
    return True


def valid_collection_roots(collection: Locations) -> bool:
    """Verify that every active location branch terminates at a COUNTRY root."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    for loc in collection:
        curr = loc
        seen: set[LocationID] = set()
        while curr.parent_id is not None:
            if curr.id in seen:
                errors.append(f"Cycle encountered while resolving root for '{loc.id}'")
                break
            seen.add(curr.id)

            parent = all_nodes.get(curr.parent_id)
            if not parent:
                errors.append(
                    f"Active location '{loc.id}' references non-existent parent '{curr.parent_id}'"
                )
                break
            curr = parent
        else:
            if curr.category != JurisdictionCategory.COUNTRY:
                errors.append(
                    f"Hierarchy branch for '{loc.id}' terminates at non-COUNTRY root "
                    f"'{curr.id}' ({curr.category.value})"
                )

    if errors:
        for err in errors:
            _logger.error(f"Root Anchoring Error: {err}")
        return False
    return True


def valid_collection_patterns(collection: Locations) -> bool:
    """Verify that all active locations comply with Pattern 1-7 jurisdictional tier rules."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    for loc in collection:
        if loc.category == JurisdictionCategory.COUNTRY:
            if loc.parent_id is not None:
                errors.append(f"COUNTRY node '{loc.id}' cannot have parent_id '{loc.parent_id}'")
            continue

        if loc.parent_id is None:
            errors.append(
                f"Non-COUNTRY node '{loc.id}' ({loc.category.value}) is missing parent_id"
            )
            continue

        parent = all_nodes.get(loc.parent_id)
        if not parent:
            continue

        allowed_parents = _VALID_PARENT_CATEGORIES.get(loc.category, ())
        if parent.category not in allowed_parents:
            errors.append(
                f"Pattern violation on '{loc.id}': '{loc.category.value}' under '{parent.category.value}'"
            )

    if errors:
        for err in errors:
            _logger.error(f"Pattern Compliance Error: {err}")
        return False
    return True


def valid_collection_tombstones(collection: Locations) -> bool:
    """Verify graveyard isolation and superseded_by integrity across the collection."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    for loc in collection:
        curr = loc
        seen: set[LocationID] = set()
        while curr.parent_id is not None:
            if curr.id in seen:
                break
            seen.add(curr.id)
            parent = all_nodes.get(curr.parent_id)
            if not parent:
                break
            if parent.tombstone.is_deprecated:
                errors.append(f"Active location '{loc.id}' has tombstoned ancestor '{parent.id}'")
                break
            curr = parent

    for loc in collection.iter_all():
        if not loc.tombstone.is_deprecated:
            continue

        sup_id = loc.tombstone.superseded_by
        if sup_id is not None:
            target = all_nodes.get(sup_id)
            if not target:
                errors.append(f"Tombstoned location '{loc.id}' superseded by missing '{sup_id}'")
            elif target.category != loc.category:
                errors.append(
                    f"Tombstoned location '{loc.id}' ({loc.category.value}) superseded by "
                    f"mismatched category '{target.id}' ({target.category.value})"
                )

    if errors:
        for err in errors:
            _logger.error(f"Tombstone Boundary Error: {err}")
        return False
    return True


def valid_collection_indexes(collection: Locations) -> bool:
    """Verify that URN, alias, category, and parent indexes are synchronized with registry."""
    errors: list[str] = []

    for loc in collection:
        if loc.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{loc.canonical_urn}' missing from URN index")
        elif collection._urn_index[loc.canonical_urn] != loc.id:
            errors.append(f"URN index mismatch for '{loc.canonical_urn}'")

        for alias in loc.aliases:
            key = alias.strip().lower()
            if key not in collection._alias_index:
                errors.append(f"Alias '{alias}' for '{loc.id}' missing from alias index")
            elif loc.id not in collection._alias_index[key]:
                errors.append(f"Alias '{alias}' for '{loc.id}' missing from alias index")

        if loc.category not in collection._category_index:
            errors.append(f"Category '{loc.category}' missing from category index")
        elif loc.id not in collection._category_index[loc.category]:
            errors.append(f"Location '{loc.id}' missing from category index bucket")

        if loc.parent_id is not None:
            if loc.parent_id not in collection._parent_index:
                errors.append(f"Parent '{loc.parent_id}' missing from parent index")
            elif loc.id not in collection._parent_index[loc.parent_id]:
                errors.append(f"Location '{loc.id}' missing from parent index bucket")

    for _urn, loc_id in collection._urn_index.items():
        if loc_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{loc_id}'")

    if errors:
        for err in errors:
            _logger.error(f"Index Verification Error: {err}")
        return False
    return True


def valid_collection_all(collection: Locations) -> bool:
    """Execute all collection-wide validation routines and aggregate diagnostic logging."""
    c_ok = valid_collection_cycles(collection)
    if not c_ok:
        _logger.error("Collection validation aborted early due to cyclic parent links.")
        return False

    r_ok = valid_collection_roots(collection)
    p_ok = valid_collection_patterns(collection)
    t_ok = valid_collection_tombstones(collection)
    i_ok = valid_collection_indexes(collection)

    return bool(r_ok and p_ok and t_ok and i_ok)
