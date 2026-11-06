"""Path: tests/test_gda/test_entity/test_sites/test_smoke.py

Subpackage smoke verification suite for gda.entity.sites public interface.

Operational Role:
    Executes gateway smoke checks validating public exports, collection
    instantiation, and foundational lifecycle operations exposed by the
    gda.entity.sites package root.
"""

from __future__ import annotations

import pytest

import gda.entity.sites as sites_pkg
from gda.entity.sites import (
    Sites,
    valid_collection_indexes,
    valid_site,
    valid_urn,
)
from gda.enums.site import SiteType
from gda.model.atom.id import LocationID, SiteID

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: PUBLIC EXPORTS & DISCOVERABILITY CONTRACTS
# Note: Verifies package __all__ completeness and top-level import availability
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_sites_package_exports_contract() -> None:
    """Verify gda.entity.sites exposes complete and uncorrupted public symbols."""
    expected_exports = {
        "SiteError",
        "SiteNotFoundError",
        "SiteValidationError",
        "Sites",
        "can_tombstone",
        "can_undelete",
        "export_file",
        "import_file",
        "load_from_db",
        "save_to_db",
        "tombstone_site",
        "undelete_site",
        "valid_collection_all",
        "valid_collection_indexes",
        "valid_collection_locations",
        "valid_collection_tombstones",
        "valid_site",
        "valid_site_address",
        "valid_urn",
    }
    actual_exports = set(getattr(sites_pkg, "__all__", []))
    assert expected_exports.issubset(actual_exports)

    for symbol in expected_exports:
        assert hasattr(sites_pkg, symbol)
        assert getattr(sites_pkg, symbol) is not None


# ==============================================================================
# GROUP 2: PUBLIC INTERFACE GATEWAY SMOKE WORKFLOWS
# Note: Verifies high-level end-to-end happy path across package facade
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_sites_collection_public_interface_smoke() -> None:
    """Verify end-to-end lifecycle using only public interfaces of gda.entity.sites."""
    # 1. Collection instantiation
    coll = Sites()
    assert len(coll) == 0
    assert coll.is_dirty is False

    # 2. Public factory creation and auto-indexing
    site = coll.create(
        name="Concord Historical Meetinghouse",
        category=SiteType.CHURCH,
        location_id=LocationID("LOC-000001"),
        alternate_names=["Old North Meetinghouse"],
    )
    assert site.id == SiteID("SID-000001")
    assert site.id in coll
    assert site.canonical_urn in coll
    assert "old north meetinghouse" in coll._alias_index
    assert len(coll) == 1
    assert coll.is_dirty is True

    # 3. Public query facades
    by_loc = coll.find_by_location("LOC-000001")
    assert len(by_loc) == 1
    assert by_loc[0].id == site.id

    by_cat = coll.find_by_category(SiteType.CHURCH)
    assert len(by_cat) == 1
    assert by_cat[0].id == site.id

    # 4. Public validation facade
    assert valid_site(site) is True
    assert valid_urn(site.canonical_urn) is True
    assert valid_collection_indexes(coll) is True

    # 5. Public retirement and restore facade
    retired = coll.soft_delete(site.id, reason="Demolished")
    assert retired.tombstone.is_deprecated is True
    assert len(coll) == 0

    restored = coll.undelete(site.id)
    assert restored.tombstone.is_deprecated is False
    assert len(coll) == 1
