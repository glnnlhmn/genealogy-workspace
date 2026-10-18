"""Path: tests/test_gda/test_model/test_entity/test_site.py

Comprehensive test suite verifying Site and site categorization primitives.

Operational Role:
    Verifies SiteCategory, Site, and backward-compatible SiteEntityModel
    behavioral contracts, including BaseEntity inheritance, foreign key LocationID
    validation, URN formatting, optional address/coordinate composition, historical
    name integration, and immutability invariants.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.errors import ModelFormatError
from gda.model.atom.date import DateModifier, DateString, EventDate, IsoTimestamp
from gda.model.atom.geo import Coordinates, Latitude, Longitude
from gda.model.atom.id import FactID, LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.name import HistoricalName, NameStatus
from gda.model.base.time_period import TimePeriod
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.site import Site, SiteCategory, SiteEntityModel

__version__ = "1.0.0+build.6"


# ==============================================================================
# FIXTURES: GOLDEN PAYLOADS & BASE INSTANCES
# ==============================================================================


@pytest.fixture
def golden_timestamp() -> IsoTimestamp:
    """Fixture providing a standard test timestamp."""
    return IsoTimestamp("2026-10-16T12:00:00Z")


@pytest.fixture
def golden_audit(golden_timestamp: IsoTimestamp) -> AuditStamp:
    """Fixture providing a standard audit stamp."""
    return AuditStamp(created_at=golden_timestamp, updated_at=golden_timestamp)


@pytest.fixture
def golden_period() -> TimePeriod:
    """Fixture providing a standard bounded temporal period."""
    return TimePeriod(
        start_date=EventDate(date=DateString("1730"), modifier=DateModifier.EXACT),
        end_date=EventDate(date=DateString("1920"), modifier=DateModifier.ABOUT),
    )


@pytest.fixture
def golden_address() -> Address:
    """Fixture providing a street-level Address instance without civil jurisdictions."""
    return Address(
        address_line_1="Woodhill Hook Road",
        postal_code="03304",
    )


@pytest.fixture
def golden_site(
    golden_audit: AuditStamp, golden_period: TimePeriod, golden_address: Address
) -> Site:
    """Fixture providing a complete standard Site instance."""
    site_id = SiteID("SID-000001")
    loc_id = LocationID("LOC-000004")
    coords = Coordinates(latitude=Latitude(43.1319), longitude=Longitude(-71.5497))
    hn = HistoricalName(raw_name="Center Burying Ground", status=NameStatus.COLLOQUIAL)

    return Site(
        id=site_id,
        audit=golden_audit,
        name="Old Bow Center Cemetery",
        category=SiteCategory.CEMETERY,
        canonical_urn="urn:gda:site:us:nh:merrimack:bow:old-bow-center-cemetery",
        location_id=loc_id,
        address=golden_address,
        coordinates=coords,
        historical_names=[hn],
        alternate_names=["Town Hall Graveyard"],
        period=golden_period,
        is_active=False,
    )


# ==============================================================================
# GROUP 1: SITECATEGORY ENUMERATION INVARIANTS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_site_category_enumeration_members() -> None:
    """Verify SiteCategory enumerates all standardized physical venue categories."""
    expected = {
        "CEMETERY",
        "CHURCH",
        "RESIDENCE",
        "HOSPITAL",
        "GOVERNMENT",
        "MILITARY",
        "REPOSITORY",
        "COMMERCIAL",
        "LANDMARK",
        "OTHER",
    }
    assert {c.value for c in SiteCategory} == expected


# ==============================================================================
# GROUP 2: SITE CREATION & ATTRIBUTES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_site_valid_creation_and_alias_equivalence(
    golden_site: Site,
    golden_audit: AuditStamp,
    golden_period: TimePeriod,
    golden_address: Address,
) -> None:
    """Verify Site instantiates with complete attributes and supports backward compatibility alias."""
    site = golden_site
    assert isinstance(site, SiteEntityModel)
    assert site.id == SiteID("SID-000001")
    assert site.audit == golden_audit
    assert site.created_at == golden_audit.created_at
    assert site.updated_at == golden_audit.updated_at
    assert site.name == "Old Bow Center Cemetery"
    assert site.category == SiteCategory.CEMETERY
    assert (
        site.canonical_urn == "urn:gda:site:us:nh:merrimack:bow:old-bow-center-cemetery"
    )
    assert site.location_id == LocationID("LOC-000004")
    assert site.address == golden_address
    assert site.coordinates is not None
    assert len(site.historical_names) == 1
    assert site.alternate_names == ["Town Hall Graveyard"]
    assert site.period == golden_period
    assert site.date_established == golden_period.start_date
    assert site.date_closed == golden_period.end_date
    assert site.is_active is False
    assert site.is_deprecated is False
    assert str(site) == "Old Bow Center Cemetery [CEMETERY] (SID-000001)"


@pytest.mark.unit
@pytest.mark.smoke
def test_site_defaults(golden_audit: AuditStamp) -> None:
    """Verify Site defaults optional address, coordinates, and collections."""
    site = Site(
        id=SiteID("SID-000002"),
        audit=golden_audit,
        name="Rural Meetinghouse Marker",
        category=SiteCategory.LANDMARK,
        canonical_urn="urn:gda:site:us:nh:bow:meetinghouse-marker",
        location_id=LocationID("LOC-000004"),
    )

    assert site.address is None
    assert site.coordinates is None
    assert site.historical_names == []
    assert site.alternate_names == []
    assert site.period is None
    assert site.date_established is None
    assert site.date_closed is None
    assert site.is_active is True


# ==============================================================================
# GROUP 3: DEFENSIVE BOUNDARIES & VALIDATIONS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "bad_id_str",
    [
        "SID-12345",
        "SID-1234567",
        "SID-ABCDEF",
        "000001",
        "",
    ],
)
def test_site_invalid_site_id_raises_format_error(
    bad_id_str: str, golden_audit: AuditStamp
) -> None:
    """Verify malformed SiteID values raise ModelFormatError when constructed."""
    try:
        bad_id = SiteID(bad_id_str)
        with pytest.raises(ModelFormatError, match="Invalid SiteID format"):
            Site(
                id=bad_id,
                audit=golden_audit,
                name="Invalid ID Site",
                category=SiteCategory.LANDMARK,
                canonical_urn="urn:gda:site:us:nh:bow:invalid",
                location_id=LocationID("LOC-000004"),
            )
    except ModelFormatError:
        pass


@pytest.mark.unit
@pytest.mark.regression
def test_site_conflicting_atom_id_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Site rejects foreign AtomID subclasses assigned to id."""
    wrong_id = FactID("FID-000001")
    with pytest.raises((TypeError, ValidationError)):
        Site(
            id=wrong_id,  # type: ignore[arg-type]
            audit=golden_audit,
            name="Wrong ID Site",
            category=SiteCategory.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:wrong",
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_site_foreign_location_id_type_raises_error(golden_audit: AuditStamp) -> None:
    """Verify Site rejects foreign AtomID subclasses assigned to location_id."""
    wrong_loc = FactID("FID-000001")
    with pytest.raises(ValidationError):
        Site(
            id=SiteID("SID-000001"),
            audit=golden_audit,
            name="Wrong Loc Site",
            category=SiteCategory.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:site",
            location_id=wrong_loc,  # type: ignore[arg-type]
        )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize("blank_name", ["", "   ", "\t\n"])
def test_site_blank_name_raises_format_error(
    blank_name: str, golden_audit: AuditStamp
) -> None:
    """Verify Site raises ModelFormatError if name is blank."""
    with pytest.raises(ModelFormatError, match="'name' cannot be empty or whitespace"):
        Site(
            id=SiteID("SID-000001"),
            audit=golden_audit,
            name=blank_name,
            category=SiteCategory.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:site",
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_urn",
    [
        "",
        "   ",
        "urn:gda:loc:us:nh:bow",
        "urn:site:us:nh:bow",
        "URN:GDA:SITE:US:NH",
        "urn:gda:site:invalid space",
    ],
)
def test_site_invalid_urn_raises_format_error(
    invalid_urn: str, golden_audit: AuditStamp
) -> None:
    """Verify Site raises ModelFormatError when canonical_urn is malformed."""
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Site(
            id=SiteID("SID-000001"),
            audit=golden_audit,
            name="Valid Site",
            category=SiteCategory.LANDMARK,
            canonical_urn=invalid_urn,
            location_id=LocationID("LOC-000004"),
        )


@pytest.mark.unit
@pytest.mark.regression
def test_site_tombstone_self_superseded_raises_error(
    golden_audit: AuditStamp, golden_timestamp: IsoTimestamp
) -> None:
    """Verify Site rejects a tombstone where superseded_by points to itself."""
    site_id = SiteID("SID-000001")
    tombstone = TombstoneRecord(
        is_deprecated=True,
        deprecated_at=golden_timestamp,
        superseded_by=site_id,
    )
    with pytest.raises(ModelFormatError, match="cannot be superseded by itself"):
        Site(
            id=site_id,
            audit=golden_audit,
            name="Demolished Site",
            category=SiteCategory.LANDMARK,
            canonical_urn="urn:gda:site:us:nh:bow:demolished",
            location_id=LocationID("LOC-000004"),
            tombstone=tombstone,
        )


# ==============================================================================
# GROUP 4: IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
def test_site_immutability(golden_site: Site) -> None:
    """Verify Site instances are frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        golden_site.name = "Renamed Landmark"  # type: ignore[misc]


@pytest.mark.unit
def test_site_introspection(golden_site: Site) -> None:
    """Verify .help() introspection renders member directory on Site."""
    help_text = golden_site.help(as_str=True)
    assert help_text is not None
    assert "=== Site Public Directory ===" in help_text
    assert "created_at" in help_text
    assert "is_deprecated" in help_text
    assert "date_established" in help_text
    assert "date_closed" in help_text
