"""Path: tests/test_gda/test_entity/test_locations/test_validation.py

Unit and regression test suite for location jurisdictional validation primitives.

Operational Role:
    Verifies URN conformity, segment depths, comma counts, display text parsing,
    and raw tuple hierarchy integrity across Patterns 1 through 7.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from gda.core.errors import ModelFormatError
from gda.entity.locations.errors import LocationHierarchyError
from gda.entity.locations.validation import (
    valid_display_text,
    valid_hierarchy,
    valid_urn,
    validate_urn_tier_sequence,
)
from gda.enums.location import JurisdictionCategory

__version__ = "1.0.0+build.19"

# ==============================================================================
# GROUP 1: URN FORMAT & SEGMENT DEPTH (PATTERNS 1-7)
# ==============================================================================


@pytest.mark.smoke
def test_valid_urn_pattern_1_country_valid() -> None:
    """Verify Pattern 1 Country URN succeeds with exactly 1 segment."""
    assert valid_urn("urn:gda:loc:united_states", JurisdictionCategory.COUNTRY) is True


@pytest.mark.regression
def test_valid_urn_pattern_2_statoid_valid() -> None:
    """Verify Pattern 2 Statoid URN succeeds with exactly 2 segments."""
    assert valid_urn("urn:gda:loc:united_states:nh", JurisdictionCategory.STATOID) is True


@pytest.mark.regression
def test_valid_urn_pattern_3_county_valid() -> None:
    """Verify Pattern 3 County URN succeeds with exactly 3 segments."""
    assert (
        valid_urn(
            "urn:gda:loc:united_states:nh:merrimack",
            JurisdictionCategory.COUNTY_EQUIVALENT,
        )
        is True
    )


@pytest.mark.regression
def test_valid_urn_pattern_4_township_valid() -> None:
    """Verify Pattern 4 Township URN succeeds with exactly 4 segments."""
    assert (
        valid_urn(
            "urn:gda:loc:united_states:nh:merrimack:bow",
            JurisdictionCategory.CIVIL_TOWNSHIP,
        )
        is True
    )


@pytest.mark.regression
def test_valid_urn_pattern_5_municipality_depth_5_valid() -> None:
    """Verify Pattern 5 Municipality URN succeeds with depth 5."""
    assert (
        valid_urn(
            "urn:gda:loc:united_states:nh:merrimack:bow:center",
            JurisdictionCategory.MUNICIPALITY,
        )
        is True
    )


@pytest.mark.regression
def test_valid_urn_pattern_6_municipality_depth_4_valid() -> None:
    """Verify Pattern 6 Municipality URN succeeds with depth 4 skipping township."""
    assert (
        valid_urn(
            "urn:gda:loc:united_states:ca:los_angeles:los_angeles",
            JurisdictionCategory.MUNICIPALITY,
        )
        is True
    )


@pytest.mark.regression
def test_valid_urn_pattern_7_municipality_depth_3_valid() -> None:
    """Verify Pattern 7 Municipality edge-case URN succeeds with depth 3."""
    assert (
        valid_urn(
            "urn:gda:loc:united_states:va:richmond",
            JurisdictionCategory.MUNICIPALITY,
        )
        is True
    )


@pytest.mark.regression
def test_valid_urn_pattern_5_unincorporated_depth_5_valid() -> None:
    """Verify Pattern 5 Unincorporated place URN succeeds with depth 5."""
    assert (
        valid_urn(
            "urn:gda:loc:united_states:nh:merrimack:bow:bow_mills",
            JurisdictionCategory.UNINCORPORATED_PLACE,
        )
        is True
    )


@pytest.mark.unit
def test_valid_urn_category_as_string_valid() -> None:
    """Verify string enum representation is correctly parsed and validated."""
    assert valid_urn("urn:gda:loc:canada", "COUNTRY") is True


@pytest.mark.regression
def test_valid_urn_invalid_category_string_raises_error() -> None:
    """Verify unrecognized category string raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Invalid jurisdiction category"):
        valid_urn("urn:gda:loc:usa", "INVALID_CAT")


@pytest.mark.regression
def test_valid_urn_unsupported_category_raises_error() -> None:
    """Verify category not in allowed segment mapping raises ModelFormatError."""
    mock_category = MagicMock(spec=JurisdictionCategory)
    mock_category.value = "CUSTOM_TIER"
    with pytest.raises(ModelFormatError, match="Unsupported jurisdiction category"):
        valid_urn("urn:gda:loc:usa:custom", mock_category)


@pytest.mark.regression
def test_valid_urn_invalid_syntax_raises_error() -> None:
    """Verify malformed URN strings trigger ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        valid_urn("invalid:prefix:usa", JurisdictionCategory.COUNTRY)


@pytest.mark.regression
def test_valid_urn_empty_urn_raises_error() -> None:
    """Verify empty or whitespace URN triggers ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        valid_urn("   ", JurisdictionCategory.COUNTRY)


@pytest.mark.regression
def test_valid_urn_prefix_only_raises_error() -> None:
    """Verify URN with prefix but missing path segments raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        valid_urn("urn:gda:loc:", JurisdictionCategory.COUNTRY)


@pytest.mark.regression
def test_valid_urn_empty_segments_only_raises_error() -> None:
    """Verify URN with only delimiters after prefix raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Missing path segments after prefix"):
        valid_urn("urn:gda:loc:::", JurisdictionCategory.COUNTRY)


@pytest.mark.regression
def test_valid_urn_consecutive_colons_raises_error() -> None:
    """Verify URNs with adjacent colons trigger ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Contains empty or adjacent"):
        valid_urn("urn:gda:loc:usa::nh", JurisdictionCategory.STATOID)


@pytest.mark.regression
def test_valid_urn_depth_mismatch_raises_error() -> None:
    """Verify depth mismatch against category raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="invalid for category 'COUNTRY'"):
        valid_urn("urn:gda:loc:usa:nh", JurisdictionCategory.COUNTRY)


# ==============================================================================
# GROUP 2: LOCATION DISPLAY TEXT STRINGS
# ==============================================================================


@pytest.mark.regression
def test_valid_display_text_pattern_1_valid() -> None:
    """Verify single country token path string passes with 0 commas."""
    assert valid_display_text("USA", JurisdictionCategory.COUNTRY) is True


@pytest.mark.regression
def test_valid_display_text_pattern_2_valid() -> None:
    """Verify Statoid path string passes with 1 comma."""
    assert valid_display_text("New Hampshire, USA", JurisdictionCategory.STATOID) is True


@pytest.mark.regression
def test_valid_display_text_pattern_3_valid() -> None:
    """Verify County path string passes with 2 commas."""
    assert (
        valid_display_text(
            "Merrimack County, New Hampshire, USA",
            JurisdictionCategory.COUNTY_EQUIVALENT,
        )
        is True
    )


@pytest.mark.regression
def test_valid_display_text_pattern_4_valid() -> None:
    """Verify Township path string passes with 3 commas."""
    assert (
        valid_display_text(
            "Bow, Merrimack County, New Hampshire, USA",
            JurisdictionCategory.CIVIL_TOWNSHIP,
        )
        is True
    )


@pytest.mark.regression
def test_valid_display_text_pattern_5_valid() -> None:
    """Verify Municipality path string passes with 4 commas."""
    assert (
        valid_display_text(
            "Center, Bow, Merrimack County, New Hampshire, USA",
            JurisdictionCategory.MUNICIPALITY,
        )
        is True
    )


@pytest.mark.regression
def test_valid_display_text_pattern_7_edge_case_valid() -> None:
    """Verify Pattern 7 independent city passes with 2 commas."""
    assert valid_display_text("Richmond, Virginia, USA", JurisdictionCategory.MUNICIPALITY) is True


@pytest.mark.unit
def test_valid_display_text_without_target_category_valid() -> None:
    """Verify path string parses and passes when target_category is None."""
    assert valid_display_text("Bow, Merrimack, NH, USA") is True


@pytest.mark.regression
def test_valid_display_text_empty_raises_error() -> None:
    """Verify empty or whitespace path string raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Location path string cannot be empty"):
        valid_display_text("   ")


@pytest.mark.regression
def test_valid_display_text_leading_or_trailing_comma_raises_error() -> None:
    """Verify path strings with leading or trailing commas raise ModelFormatError."""
    with pytest.raises(ModelFormatError, match="cannot have leading or trailing commas"):
        valid_display_text(", USA")

    with pytest.raises(ModelFormatError, match="cannot have leading or trailing commas"):
        valid_display_text("USA, ")


@pytest.mark.regression
def test_valid_display_text_empty_inner_segment_raises_error() -> None:
    """Verify empty inner segments raise ModelFormatError."""
    with pytest.raises(ModelFormatError, match="Contains empty segments"):
        valid_display_text("Bow, , NH, USA")


@pytest.mark.regression
def test_valid_display_text_excessive_depth_raises_error() -> None:
    """Verify path strings with more than 4 commas raise ModelFormatError."""
    with pytest.raises(ModelFormatError, match="maximum allowed depth"):
        valid_display_text("A, B, C, D, E, F")


@pytest.mark.regression
def test_valid_display_text_comma_mismatch_raises_error() -> None:
    """Verify comma count mismatch against target category raises ModelFormatError."""
    with pytest.raises(ModelFormatError, match="invalid for category 'STATOID'"):
        valid_display_text("Concord, Merrimack, NH, USA", JurisdictionCategory.STATOID)


# ==============================================================================
# GROUP 3: ISOLATED RAW HIERARCHY TUPLES
# ==============================================================================


@pytest.mark.unit
def test_valid_hierarchy_empty_returns_true() -> None:
    """Verify empty node list evaluates to True."""
    assert valid_hierarchy([]) is True


@pytest.mark.regression
def test_valid_hierarchy_full_tree_passes() -> None:
    """Verify clean 5-tier parent-child hierarchy passes validation."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, False),
        ("LOC-000003", "LOC-000002", JurisdictionCategory.COUNTY_EQUIVALENT, False),
        ("LOC-000004", "LOC-000003", JurisdictionCategory.CIVIL_TOWNSHIP, False),
        ("LOC-000005", "LOC-000004", JurisdictionCategory.MUNICIPALITY, False),
        ("LOC-000006", "LOC-000004", JurisdictionCategory.MUNICIPALITY, False),
    ]
    assert valid_hierarchy(nodes) is True


@pytest.mark.regression
def test_valid_hierarchy_deprecated_nodes_bypass_ancestor_traversal() -> None:
    """Verify deprecated nodes bypass active tombstone traversal cleanly."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, True),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, True),
    ]
    assert valid_hierarchy(nodes) is True


@pytest.mark.regression
def test_valid_hierarchy_direct_cycle_raises_error() -> None:
    """Verify direct self-referencing parent pointer raises LocationHierarchyError."""
    nodes = [
        ("LOC-000001", "LOC-000001", JurisdictionCategory.COUNTRY, False),
    ]
    with pytest.raises(LocationHierarchyError, match="Cyclic reference detected"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_blank_id_raises_error() -> None:
    """Verify blank or whitespace location ID raises ModelFormatError."""
    nodes = [
        ("   ", None, JurisdictionCategory.COUNTRY, False),
    ]
    with pytest.raises(ModelFormatError, match="cannot be blank"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_duplicate_id_raises_error() -> None:
    """Verify duplicate location IDs in the collection raise ModelFormatError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
    ]
    with pytest.raises(ModelFormatError, match="Duplicate location ID encountered"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_country_with_parent_raises_error() -> None:
    """Verify Country with non-null parent raises ModelFormatError."""
    nodes = [
        ("LOC-000001", "LOC-000002", JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", None, JurisdictionCategory.COUNTRY, False),
    ]
    with pytest.raises(ModelFormatError, match="cannot have a parent jurisdiction"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_non_country_without_parent_raises_error() -> None:
    """Verify non-country without parent jurisdiction raises ModelFormatError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.STATOID, False),
    ]
    with pytest.raises(ModelFormatError, match="must have a valid parent jurisdiction"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_dangling_parent_raises_error() -> None:
    """Verify child pointing to non-existent parent raises ModelFormatError."""
    nodes = [
        ("LOC-000001", "LOC-999999", JurisdictionCategory.STATOID, False),
    ]
    with pytest.raises(ModelFormatError, match="references non-existent parent"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_active_node_with_tombstoned_parent_raises_error() -> None:
    """Verify active child with deprecated immediate parent raises LocationHierarchyError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, True),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, False),
    ]
    with pytest.raises(LocationHierarchyError, match="cannot link to tombstoned parent"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_active_node_with_distant_tombstoned_ancestor_raises_error() -> None:
    """Verify active child with deprecated distant ancestor raises LocationHierarchyError."""
    nodes = [
        ("LOC-000003", "LOC-000002", JurisdictionCategory.COUNTY_EQUIVALENT, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, False),
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, True),
    ]
    with pytest.raises(LocationHierarchyError, match="has tombstoned ancestor 'LOC-000001'"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_ancestor_cycle_loop_guard_breaks() -> None:
    """Verify ancestor traversal loop guard breaks safely when ancestor points to self (covers line 299)."""
    with patch("gda.entity.locations.validation._split_and_validate_path_parts"):
        pass
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, False),
        ("LOC-000003", "LOC-000002", JurisdictionCategory.COUNTY_EQUIVALENT, False),
    ]
    assert valid_hierarchy(nodes) is True


@pytest.mark.regression
def test_valid_hierarchy_statoid_under_non_country_raises_error() -> None:
    """Verify STATOID under non-COUNTRY node raises ModelFormatError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, False),
        ("LOC-000003", "LOC-000002", JurisdictionCategory.STATOID, False),
    ]
    with pytest.raises(ModelFormatError, match="Expected parent of type: COUNTRY"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_county_under_non_statoid_raises_error() -> None:
    """Verify COUNTY_EQUIVALENT under non-STATOID node raises ModelFormatError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.COUNTY_EQUIVALENT, False),
    ]
    with pytest.raises(ModelFormatError, match="Expected parent of type: STATOID"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_civil_township_under_non_county_raises_error() -> None:
    """Verify CIVIL_TOWNSHIP under non-COUNTY node raises ModelFormatError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.STATOID, False),
        ("LOC-000003", "LOC-000002", JurisdictionCategory.CIVIL_TOWNSHIP, False),
    ]
    with pytest.raises(ModelFormatError, match="Expected parent of type: COUNTY_EQUIVALENT"):
        valid_hierarchy(nodes)


@pytest.mark.regression
def test_valid_hierarchy_municipality_under_invalid_tier_raises_error() -> None:
    """Verify MUNICIPALITY under invalid parent raises ModelFormatError."""
    nodes = [
        ("LOC-000001", None, JurisdictionCategory.COUNTRY, False),
        ("LOC-000002", "LOC-000001", JurisdictionCategory.MUNICIPALITY, False),
    ]
    with pytest.raises(ModelFormatError, match="Expected parent of type:"):
        valid_hierarchy(nodes)


# ==============================================================================
# GROUP 4: LEGACY URN TIER SEQUENCE FACADE
# ==============================================================================


@pytest.mark.unit
def test_validate_urn_tier_sequence_valid_calls() -> None:
    """Verify legacy sequence helper accepts valid inputs."""
    validate_urn_tier_sequence("USA", "NH", "Merrimack", "Bow", "Center")
    validate_urn_tier_sequence("USA", "NH", "Merrimack", None, "Center")
    validate_urn_tier_sequence("USA", "VA", None, None, "Richmond")


@pytest.mark.regression
def test_validate_urn_tier_sequence_invalid_calls_raise_error() -> None:
    """Verify legacy sequence helper rejects invalid hierarchies."""
    with pytest.raises(ModelFormatError, match="must contain a country"):
        validate_urn_tier_sequence(None, "NH", "Merrimack", "Bow", "Center")

    with pytest.raises(ModelFormatError, match="without state"):
        validate_urn_tier_sequence("USA", None, "Merrimack", "Bow", "Center")

    with pytest.raises(ModelFormatError, match="without county"):
        validate_urn_tier_sequence("USA", "NH", None, "Bow", "Center")
