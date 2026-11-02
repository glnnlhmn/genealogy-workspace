"""Path: src/gda/entity/locations/validation.py

Authoritative jurisdictional URN, structural hierarchy, and path validation routines.

Operational Role:
    Provides deterministic verification of jurisdictional tier sequences,
    URN structural conformity across Patterns 1-7, formatted location display
    strings, and deep relational graph integrity including cycle, tombstone,
    and index synchronization diagnostics.
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from gda.core.errors import ModelFormatError
from gda.entity.locations.errors import LocationHierarchyError
from gda.entity.locations.util import clean_string
from gda.enums.location import JurisdictionCategory
from gda.model.atom.id import LocationID

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations

__version__ = "1.0.0+build.17"

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

_logger = logging.getLogger(__name__)

# ==============================================================================
# AUTHORITATIVE JURISDICTION PATTERNS & TIER MAPPINGS
#
# Administrative Letter Codes:
#   A - Country (e.g., USA, Canada, UK, France, Germany)
#   B - Statoid (State, Province, Constituent Country, Region, Land)
#   C - County Equivalent (County, Parish, Borough, Census Division, Département)
#   D - Civil Township (Town, Civil Township, District, Canton, Amt)
#   E - Municipality (City, Incorporated Town, Village, Commune, Gemeinde)
#   F - Unincorporated Place / Locality (Neighborhood, Hamlet, Settlement, Ortsteil)
# ==============================================================================

_LOCATION_URN_PATTERN: re.Pattern[str] = re.compile(r"^urn:gda:loc:[a-z0-9_:\-]+$")

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

_VALID_PARENT_CATEGORIES: dict[
    JurisdictionCategory, tuple[JurisdictionCategory, ...]
] = {
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


def _extract_urn_segments(urn: str) -> list[str]:
    """Strip namespace prefix and return validated non-empty colon-delimited tokens."""
    clean_urn = urn.strip() if urn else ""
    if not clean_urn or not _LOCATION_URN_PATTERN.match(clean_urn):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. "
            "Must match 'urn:gda:loc:<namespace>' with lowercase alphanumeric, underscore, "
            "hyphen, and colon tokens."
        )

    prefix_stripped = clean_urn.removeprefix("urn:gda:loc:")
    tokens = [tok for tok in prefix_stripped.split(":") if tok]

    if not tokens:
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. Missing path segments after prefix."
        )

    raw_tokens = prefix_stripped.split(":")
    if any(not tok for tok in raw_tokens):
        raise ModelFormatError(
            f"Invalid canonical_urn format: '{clean_urn}'. Contains empty or adjacent delimiters."
        )

    return tokens


def _resolve_category(category: JurisdictionCategory | str) -> JurisdictionCategory:
    """Resolve an incoming category token or enum into a validated JurisdictionCategory."""
    if isinstance(category, JurisdictionCategory):
        return category
    try:
        return JurisdictionCategory(category)
    except (ValueError, KeyError) as err:
        raise ModelFormatError(
            f"Invalid jurisdiction category: '{category}'. Must be a valid JurisdictionCategory."
        ) from err


def _split_and_validate_path_parts(path_str: str) -> list[str]:
    """Tokenize comma-delimited path string and verify non-empty segment constraints."""
    cleaned = clean_string(path_str)
    if not cleaned:
        raise ModelFormatError("Location path string cannot be empty or whitespace.")

    if path_str.strip().startswith(",") or path_str.strip().endswith(","):
        raise ModelFormatError(
            "Location path string cannot have leading or trailing commas."
        )

    raw_parts = cleaned.split(",")
    parts: list[str] = []
    for part in raw_parts:
        trimmed = part.strip()
        if not trimmed:
            raise ModelFormatError(
                f"Invalid location path string format: '{path_str}'. Contains empty segments."
            )
        parts.append(trimmed)

    return parts


def validate_urn_tier_sequence(
    country: str | None,
    state: str | None,
    county: str | None,
    township: str | None,
    local: str | None,
) -> None:
    """Ensure jurisdictional tiers follow authoritative sequence rules (compatibility facade)."""
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
        raise ModelFormatError("Cannot attach civil township without county.")


def valid_urn(urn: str, category: JurisdictionCategory | str) -> bool:
    """Validate that an individual URN string conforms to the 7 authoritative pattern depths."""
    res_cat = _resolve_category(category)
    segments = _extract_urn_segments(urn)
    segment_count = len(segments)

    allowed_counts = _CATEGORY_ALLOWED_SEGMENT_COUNTS.get(res_cat)
    if allowed_counts is None:
        raise ModelFormatError(
            f"Unsupported jurisdiction category for URN validation: '{res_cat.value}'."
        )

    if segment_count not in allowed_counts:
        allowed_str = ", ".join(str(c) for c in sorted(allowed_counts))
        raise ModelFormatError(
            f"Canonical URN '{urn}' has {segment_count} segments, which is invalid for "
            f"category '{res_cat.value}' (expected segment count: {allowed_str})."
        )

    return True


def valid_display_text(
    path_str: str,
    target_category: JurisdictionCategory | str | None = None,
) -> bool:
    """Validate comma-delimited location display strings against authoritative tier depth."""
    parts = _split_and_validate_path_parts(path_str)
    comma_count = len(parts) - 1

    if comma_count > 4:
        raise ModelFormatError(
            f"Location path string has {comma_count} commas ({len(parts)} segments); "
            "maximum allowed depth across authoritative patterns is 4 commas (5 segments)."
        )

    if target_category is not None:
        res_cat = _resolve_category(target_category)
        allowed_commas = _CATEGORY_ALLOWED_COMMA_COUNTS.get(res_cat)
        if allowed_commas is not None and comma_count not in allowed_commas:
            allowed_str = ", ".join(str(c) for c in sorted(allowed_commas))
            raise ModelFormatError(
                f"Location path string '{path_str}' contains {comma_count} commas, which is "
                f"invalid for category '{res_cat.value}' (expected comma count: {allowed_str})."
            )

    return True


def valid_hierarchy(
    nodes: list[tuple[str, str | None, JurisdictionCategory | str, bool | None]],
) -> bool:
    """Evaluate an isolated list of node tuples for relational graph integrity."""
    if not nodes:
        return True

    node_map: dict[str, tuple[str | None, JurisdictionCategory, bool]] = {}
    for node in nodes:
        loc_id, parent_id, cat = node[0], node[1], node[2]
        is_deprecated = (
            bool(node[3]) if len(node) > 3 and node[3] is not None else False
        )

        clean_loc_id = clean_string(loc_id)
        if not clean_loc_id:
            raise ModelFormatError(
                "Location ID in relational hierarchy cannot be blank."
            )

        clean_parent_id = clean_string(parent_id) if parent_id is not None else None
        res_cat = _resolve_category(cat)

        if clean_loc_id in node_map:
            raise ModelFormatError(
                f"Duplicate location ID encountered in relational hierarchy: '{clean_loc_id}'."
            )
        node_map[clean_loc_id] = (clean_parent_id, res_cat, is_deprecated)

    visited: set[str] = set()
    rec_stack: set[str] = set()

    def _detect_cycle(curr_id: str, path: list[str]) -> None:
        visited.add(curr_id)
        rec_stack.add(curr_id)

        try:
            p_id = node_map[curr_id][0]
            if p_id is not None and p_id in node_map:
                if p_id in rec_stack:
                    cycle_repr = " -> ".join(path + [p_id])
                    raise LocationHierarchyError(
                        f"Cyclic reference detected in location hierarchy: {cycle_repr}."
                    )
                if p_id not in visited:
                    _detect_cycle(p_id, path + [p_id])
        finally:
            rec_stack.remove(curr_id)

    for loc_id in node_map:
        if loc_id not in visited:
            _detect_cycle(loc_id, [loc_id])

    for loc_id, (parent_id, cat, is_deprecated) in node_map.items():
        if cat == JurisdictionCategory.COUNTRY:
            if parent_id is not None:
                raise ModelFormatError(
                    f"Country location '{loc_id}' cannot have a parent jurisdiction ('{parent_id}')."
                )
            continue

        if parent_id is None:
            raise ModelFormatError(
                f"Non-country location '{loc_id}' [{cat.value}] must have a valid parent jurisdiction."
            )

        if parent_id not in node_map:
            raise ModelFormatError(
                f"Dangling parent reference: location '{loc_id}' references non-existent parent '{parent_id}'."
            )

        _, parent_cat, _ = node_map[parent_id]

        if not is_deprecated:
            curr_ancestor_id = parent_id
            seen_ancestors: set[str] = set()
            while curr_ancestor_id is not None:
                if curr_ancestor_id in seen_ancestors:
                    break
                seen_ancestors.add(curr_ancestor_id)
                anc_parent, _, anc_deprecated = node_map[curr_ancestor_id]
                if anc_deprecated:
                    if curr_ancestor_id == parent_id:
                        raise LocationHierarchyError(
                            f"Active location '{loc_id}' cannot link to tombstoned parent '{parent_id}'."
                        )
                    raise LocationHierarchyError(
                        f"Active location '{loc_id}' has tombstoned ancestor '{curr_ancestor_id}'."
                    )
                curr_ancestor_id = anc_parent

        valid_parents = _VALID_PARENT_CATEGORIES.get(cat, ())
        if parent_cat not in valid_parents:
            expected_str = ", ".join(p.value for p in valid_parents)
            raise ModelFormatError(
                f"Invalid hierarchy: '{loc_id}' [{cat.value}] cannot have parent '{parent_id}' "
                f"of type '{parent_cat.value}'. Expected parent of type: {expected_str}."
            )

    return True


def valid_collection_cycles(collection: Locations) -> bool:
    """Traverse the entire collection using DFS to detect direct or multi-hop relational cycles."""
    errors: list[str] = []
    visited: set[LocationID] = set()
    rec_stack: set[LocationID] = set()

    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    def _traverse(curr_id: LocationID, path: list[str]) -> bool:
        visited.add(curr_id)
        rec_stack.add(curr_id)

        try:
            node = all_nodes.get(curr_id)
            if node and node.parent_id:
                p_id = node.parent_id
                if p_id in rec_stack:
                    cycle_str = " -> ".join(path + [str(p_id)])
                    errors.append(f"Cycle detected: {cycle_str}")
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
            _logger.error("Relational Cycle Error: %s", err)
        return False
    return True


def valid_collection_roots(collection: Locations) -> bool:
    """Validate that every active entity traces upward to an authoritative COUNTRY root."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    for loc in collection:
        curr = loc
        seen_in_chain: set[LocationID] = {curr.id}

        while curr.parent_id is not None:
            if curr.parent_id not in all_nodes:
                errors.append(
                    f"Entity '{loc.id}' references missing parent '{curr.parent_id}'"
                )
                break
            curr = all_nodes[curr.parent_id]
            if curr.id in seen_in_chain:
                break
            seen_in_chain.add(curr.id)

        if curr.category != JurisdictionCategory.COUNTRY:
            errors.append(
                f"Entity '{loc.id}' traces to non-COUNTRY root '{curr.id}' [{curr.category.value}]"
            )

    if errors:
        for err in errors:
            _logger.error("Root Verification Error: %s", err)
        return False
    return True


def valid_collection_patterns(collection: Locations) -> bool:
    """Validate every active record's complete ancestry chain against Patterns 1-7."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    for loc in collection:
        if loc.category == JurisdictionCategory.COUNTRY:
            if loc.parent_id is not None:
                errors.append(
                    f"COUNTRY '{loc.id}' cannot have parent '{loc.parent_id}'"
                )
            continue

        if not loc.parent_id or loc.parent_id not in all_nodes:
            errors.append(f"Location '{loc.id}' missing valid parent pointer")
            continue

        parent = all_nodes[loc.parent_id]
        valid_parents = _VALID_PARENT_CATEGORIES.get(loc.category, ())

        if parent.category not in valid_parents:
            errors.append(
                f"Location '{loc.id}' [{loc.category.value}] has invalid parent '{parent.id}' "
                f"[{parent.category.value}]"
            )

    if errors:
        for err in errors:
            _logger.error("Pattern Verification Error: %s", err)
        return False
    return True


def valid_collection_tombstones(collection: Locations) -> bool:
    """Validate tombstone boundaries, deprecated ancestry isolation, and supersession links."""
    errors: list[str] = []
    all_nodes = {loc.id: loc for loc in collection.iter_all()}

    for loc in collection:
        curr_parent_id = loc.parent_id
        seen_ancestors: set[LocationID] = set()

        while curr_parent_id is not None:
            if curr_parent_id in seen_ancestors:
                break
            seen_ancestors.add(curr_parent_id)

            parent = all_nodes.get(curr_parent_id)
            if not parent:
                break
            if parent.tombstone.is_deprecated:
                errors.append(
                    f"Active entity '{loc.id}' has tombstoned ancestor '{parent.id}'"
                )
                break
            curr_parent_id = parent.parent_id

    for loc in collection.iter_all():
        if not loc.tombstone.is_deprecated:
            continue
        if not loc.tombstone.superseded_by:
            continue

        sup_id = loc.tombstone.superseded_by
        if sup_id not in all_nodes:
            errors.append(
                f"Tombstoned '{loc.id}' superseded by missing entity '{sup_id}'"
            )
        else:
            replacement = all_nodes[sup_id]
            if replacement.category != loc.category:
                errors.append(
                    f"Tombstoned '{loc.id}' [{loc.category.value}] superseded by "
                    f"mismatched category '{sup_id}' [{replacement.category.value}]"
                )

    if errors:
        for err in errors:
            _logger.error("Tombstone Verification Error: %s", err)
        return False
    return True


def valid_collection_indexes(collection: Locations) -> bool:
    """Validate bidirectional synchronization between registry and lookup indexes."""
    errors: list[str] = []

    for loc in collection:
        if loc.canonical_urn not in collection._urn_index:
            errors.append(f"Canonical URN '{loc.canonical_urn}' missing from URN index")
        elif collection._urn_index[loc.canonical_urn] != loc.id:
            errors.append(f"URN index mismatch for '{loc.canonical_urn}'")

        for alias in loc.alternate_names:
            c_alias = clean_string(alias)
            if c_alias and c_alias.lower() not in collection._alias_index:
                errors.append(
                    f"Alias '{alias}' for '{loc.id}' missing from alias index"
                )

    for _urn, loc_id in collection._urn_index.items():
        if loc_id not in collection._registry:
            errors.append(f"URN index contains dangling reference to '{loc_id}'")

    if errors:
        for err in errors:
            _logger.error("Index Verification Error: %s", err)
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
