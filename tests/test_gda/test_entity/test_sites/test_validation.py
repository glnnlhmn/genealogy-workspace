"""Path: tests/test_gda/test_entity/test_sites/test_validation.py

Comprehensive test suite verifying Site validation, URN checks, and collection diagnostics.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from gda.entity.sites.errors import SiteValidationError
from gda.entity.sites.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_locations,
    valid_collection_tombstones,
    valid_site,
    valid_site_address,
    valid_urn,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import SiteID
from gda.model.base.address import Address
from gda.model.base.tombstone import Tombstone

__version__ = "1.0.0+build.5"


# ==============================================================================
# GROUP 1: URN VALIDATION CONTRACTS
# Note: Verifies deterministic URN tokenization, delimiters, and syntax enforcement
# ==============================================================================


@pytest.mark.regression
def test_valid_urn_conforming_urn_passes() -> None:
    """Verify valid site URN with canonical tokens passes verification."""
    assert valid_urn("urn:gda:site:us:nh:bow:center_cemetery_s000001") is True


@pytest.mark.regression
def test_valid_urn_missing_prefix_raises_validation_error() -> None:
    """Verify URN without canonical prefix raises SiteValidationError."""
    with pytest.raises(SiteValidationError, match="Invalid canonical_urn format"):
        valid_urn("site:us:nh:bow:center_cemetery")


@pytest.mark.regression
def test_valid_urn_empty_segments_raises_validation_error() -> None:
    """Verify URN with empty or adjacent colon delimiters raises SiteValidationError."""
    with pytest.raises(SiteValidationError, match="Contains empty or adjacent delimiters"):
        valid_urn("urn:gda:site:us::bow")


@pytest.mark.regression
def test_valid_urn_empty_string_raises_validation_error() -> None:
    """Verify empty URN string raises SiteValidationError."""
    with pytest.raises(SiteValidationError, match="Invalid canonical_urn format"):
        valid_urn("")


# ==============================================================================
# GROUP 2: PHYSICAL ADDRESS BOUNDARIES
# Note: Verifies street address non-empty primary line constraints
# ==============================================================================


@pytest.mark.regression
def test_valid_site_address_populated_passes(make_site) -> None:
    """Verify populated Address passes address validation."""
    addr = Address.create(address_line_1="10 Branch Londonderry Turnpike")
    site = make_site(address=addr)
    assert valid_site_address(site) is True


@pytest.mark.regression
def test_valid_site_address_absent_passes(make_site) -> None:
    """Verify absent Address passes address validation."""
    site = make_site(address=None)
    assert valid_site_address(site) is True


@pytest.mark.regression
def test_valid_site_address_empty_street_raises_validation_error() -> None:
    """Verify address with whitespace line raises SiteValidationError."""
    mock_site = MagicMock()
    mock_site.id = SiteID("SID-000001")
    mock_addr = MagicMock()
    mock_addr.address_line_1 = "   "
    mock_site.address = mock_addr

    with pytest.raises(SiteValidationError, match="address must contain non-empty address_line_1"):
        valid_site_address(mock_site)


# ==============================================================================
# GROUP 3: COMPOSITE SITE ENTITY VALIDATION
# Note: Verifies name, category enum typing, and full invariant validation
# ==============================================================================


@pytest.mark.regression
def test_valid_site_conforming_entity_passes(make_site) -> None:
    """Verify properly formed Site domain entity passes all validation checks."""
    site = make_site()
    assert valid_site(site) is True


@pytest.mark.regression
def test_valid_site_blank_canonical_name_raises_validation_error() -> None:
    """Verify Site with blank canonical name raises SiteValidationError."""
    mock_site = MagicMock()
    mock_site.id = SiteID("SID-000001")
    mock_site.canonical_urn = "urn:gda:site:us:nh:bow:church_s000001"
    mock_site.address = None
    mock_site.name.canonical = "   "

    with pytest.raises(SiteValidationError, match="canonical name cannot be blank or whitespace"):
        valid_site(mock_site)


@pytest.mark.regression
def test_valid_site_non_enum_category_raises_validation_error() -> None:
    """Verify Site with non-SiteType category raises SiteValidationError."""
    mock_site = MagicMock()
    mock_site.id = SiteID("SID-000001")
    mock_site.canonical_urn = "urn:gda:site:us:nh:bow:church_s000001"
    mock_site.address = None
    mock_site.name.canonical = "Old First Church"
    mock_site.category = "NOT_A_SITETYPE_ENUM"

    with pytest.raises(SiteValidationError, match="category must be a SiteType enum"):
        valid_site(mock_site)


# ==============================================================================
# GROUP 4: COLLECTION-LEVEL RELATIONAL & GRAVEYARD DIAGNOSTICS
# Note: Verifies foreign key alignment, tombstone supersession, and index integrity
# ==============================================================================


@pytest.mark.regression
def test_valid_collection_locations_valid_references_passes(
    make_site, mock_locations_collection
) -> None:
    """Verify collection with valid LocationID references passes."""
    site = make_site(location_id="LOC-000001")
    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]

    assert valid_collection_locations(mock_coll, mock_locations_collection) is True
    assert valid_collection_locations(mock_coll, locations_collection=None) is True


@pytest.mark.regression
def test_valid_collection_locations_invalid_location_id_format_fails() -> None:
    """Verify collection with invalid LocationID string fails verification."""
    site = MagicMock()
    site.id = SiteID("SID-000001")
    site.location_id = "INVALID-ID"

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]

    assert valid_collection_locations(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_locations_missing_from_locations_collection_fails(make_site) -> None:
    """Verify collection referencing missing LocationID fails verification."""
    site = make_site(location_id="LOC-000099")
    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]

    mock_loc_coll = MagicMock()
    mock_loc_coll.__contains__.return_value = False

    assert valid_collection_locations(mock_coll, mock_loc_coll) is False


@pytest.mark.regression
def test_valid_collection_tombstones_self_superseded_fails(make_site) -> None:
    """Verify tombstoned site superseding itself fails verification."""
    now = IsoTimestamp.now_utc()
    site = make_site(site_id="SID-000001")
    tombstone = Tombstone[SiteID]().retire(timestamp=now, superseded_by=SiteID("SID-000001"))
    object.__setattr__(site, "tombstone", tombstone)

    mock_coll = MagicMock()
    mock_coll.iter_all.return_value = [site]

    assert valid_collection_tombstones(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_tombstones_missing_replacement_fails(make_site) -> None:
    """Verify tombstoned site superseding non-existent site fails verification."""
    now = IsoTimestamp.now_utc()
    tombstone = Tombstone[SiteID]().retire(timestamp=now, superseded_by=SiteID("SID-000099"))
    site = make_site(site_id="SID-000001", tombstone=tombstone)

    mock_coll = MagicMock()
    mock_coll.iter_all.return_value = [site]

    assert valid_collection_tombstones(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_tombstones_superseded_by_tombstoned_site_fails(make_site) -> None:
    """Verify tombstoned site superseded by another deprecated site fails verification."""
    now = IsoTimestamp.now_utc()
    tombstone_1 = Tombstone[SiteID]().retire(timestamp=now, superseded_by=SiteID("SID-000002"))
    tombstone_2 = Tombstone[SiteID]().retire(timestamp=now)

    site_1 = make_site(site_id="SID-000001", tombstone=tombstone_1)
    site_2 = make_site(site_id="SID-000002", tombstone=tombstone_2)

    mock_coll = MagicMock()
    mock_coll.iter_all.return_value = [site_1, site_2]

    assert valid_collection_tombstones(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_tombstones_valid_active_supersession_passes(make_site) -> None:
    """Verify tombstoned site superseded by active site passes verification."""
    now = IsoTimestamp.now_utc()
    tombstone_1 = Tombstone[SiteID]().retire(timestamp=now, superseded_by=SiteID("SID-000002"))
    tombstone_none = Tombstone[SiteID]().retire(timestamp=now, superseded_by=None)

    site_1 = make_site(site_id="SID-000001", tombstone=tombstone_1)
    site_2 = make_site(site_id="SID-000002")
    site_3 = make_site(site_id="SID-000003", tombstone=tombstone_none)

    mock_coll = MagicMock()
    mock_coll.iter_all.return_value = [site_1, site_2, site_3]

    assert valid_collection_tombstones(mock_coll) is True


@pytest.mark.regression
def test_valid_collection_indexes_synchronized_passes(make_site) -> None:
    """Verify perfectly synchronized lookup indexes pass verification."""
    site = make_site(site_id="SID-000001")
    site = site.add_alias("First Parish Church")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {"first parish church": site.id}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_indexes(mock_coll) is True


@pytest.mark.regression
def test_valid_collection_indexes_missing_urn_fails(make_site) -> None:
    """Verify index check fails when canonical URN is missing from index."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_urn_mismatch_fails(make_site) -> None:
    """Verify index check fails when URN index points to incorrect SiteID."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: SiteID("SID-000099")}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_missing_alias_fails(make_site) -> None:
    """Verify index check fails when site alias is absent from alias index."""
    site = make_site(site_id="SID-000001")
    site = site.add_alias("Old Church")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_missing_location_index_fails(make_site) -> None:
    """Verify index check fails when LocationID is missing from location index."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {}
    mock_coll._location_index = {}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_missing_site_in_location_bucket_fails(make_site) -> None:
    """Verify index check fails when site is omitted from location bucket."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: set()}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_missing_category_index_fails(make_site) -> None:
    """Verify index check fails when category is missing from category index."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_missing_site_in_category_bucket_fails(make_site) -> None:
    """Verify index check fails when site is omitted from category bucket."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {site.category: set()}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_indexes_dangling_urn_pointer_fails() -> None:
    """Verify index check fails when URN index points to unregistered SiteID."""
    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = []
    mock_coll._registry = {}
    mock_coll._urn_index = {"urn:gda:site:us:nh:bow:dangling": SiteID("SID-000099")}

    assert valid_collection_indexes(mock_coll) is False


@pytest.mark.regression
def test_valid_collection_all_comprehensive_passes(make_site, mock_locations_collection) -> None:
    """Verify composite collection-wide validation passes on clean state."""
    site = make_site(site_id="SID-000001")

    mock_coll = MagicMock()
    mock_coll.__iter__.return_value = [site]
    mock_coll.iter_all.return_value = [site]
    mock_coll._registry = {site.id: site}
    mock_coll._urn_index = {site.canonical_urn: site.id}
    mock_coll._alias_index = {}
    mock_coll._location_index = {site.location_id: {site.id}}
    mock_coll._category_index = {site.category: {site.id}}

    assert valid_collection_all(mock_coll, mock_locations_collection) is True
