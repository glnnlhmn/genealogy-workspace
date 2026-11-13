"""Path: tests/test_gda/test_model/test_orgs/test_organization.py

Comprehensive unit tests for gda.model.orgs.organization.Organization.

Operational Role:
    Exercises construction, validation invariants, dirty-state tracking,
    immutability, mutation copy helpers, note forwarding, and dict/JSON
    serialization parity across all branches.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from gda.core.enums.archival import NoteType
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, NoteID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.orgs import Organization, OrganizationEntityModel

__version__ = "1.0.0+build.3"


@pytest.mark.unit
@pytest.mark.smoke
def test_organization_create_and_properties() -> None:
    """Verify Organization.create defaults, aliases, period accessors, and string representations."""
    assert OrganizationEntityModel is Organization

    period = TimePeriod(
        start_date=EventDate.create("1919"),
        end_date=EventDate.create("2020"),
    )
    org = Organization.create(
        org_id="ORG-000411",
        name="VFW Post 411",
        category="veterans",
        canonical_urn="  urn:gda:org:us:nh:concord:vfw_post_411  ",
        parent_org_id="ORG-000001",
        location_id="LOC-000010",
        meeting_site_id="SID-000020",
        period=period,
        is_active=True,
    )

    assert org.id == OrganizationID("ORG-000411")
    assert org.canonical_name == "VFW Post 411"
    assert org.category is OrganizationCategory.VETERANS
    assert org.canonical_urn == "urn:gda:org:us:nh:concord:vfw_post_411"
    assert org.parent_org_id == OrganizationID("ORG-000001")
    assert org.location_id == LocationID("LOC-000010")
    assert org.meeting_site_id == SiteID("SID-000020")
    assert org.date_founded == EventDate.create("1919")
    assert org.date_dissolved == EventDate.create("2020")
    assert org.is_active is True
    assert org.is_dirty is False
    assert org.aliases == []
    assert org.historical_names == []
    assert str(org) == "VFW Post 411 [VETERANS] (ORG-000411)"
    assert "Organization(id=OrganizationID" in repr(org)

    # Without period
    org_no_period = Organization.create(
        org_id=OrganizationID("ORG-000412"),
        name=NameThing.create(raw="Concord Men's Choir", canonical="Concord Men's Choir"),
        category=OrganizationCategory.CULTURAL_ARTS,
        canonical_urn="urn:gda:org:us:nh:concord:mens_choir",
    )
    assert org_no_period.date_founded is None
    assert org_no_period.date_dissolved is None


@pytest.mark.unit
@pytest.mark.integrity
def test_organization_validation_errors() -> None:
    """Verify __post_init__ and factory validation boundaries."""
    now = IsoTimestamp("2026-01-01T00:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    name = NameThing.create(raw="Test Org", canonical="Test Org")

    # Wrong id type
    with pytest.raises(TypeError, match="Organization 'id' must be an instance of OrganizationID"):
        Organization(
            id=SiteID("SID-000001"),  # type: ignore[arg-type]
            name=name,
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:org:test",
            audit=audit,
        )

    # Invalid ID pattern (7 digits passes AtomID but fails 6-digit Organization pattern)
    with pytest.raises(ModelFormatError, match="Invalid OrganizationID format"):
        Organization(
            id=OrganizationID("ORG-1234567"),
            name=name,
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:org:test",
            audit=audit,
        )

    # Invalid URN
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        Organization.create(
            org_id="ORG-000001",
            name="Test Org",
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:site:wrong",
        )

    # Whitespace URN trimmed in __post_init__ when constructed directly
    direct = Organization(
        id=OrganizationID("ORG-000001"),
        name=name,
        category=OrganizationCategory.CIVIC_SERVICE,
        canonical_urn="  urn:gda:org:test  ",
        audit=audit,
    )
    assert direct.canonical_urn == "urn:gda:org:test"

    # Self parent_org_id
    with pytest.raises(ModelFormatError, match="cannot be its own parent_org_id"):
        Organization.create(
            org_id="ORG-000001",
            name="Test Org",
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:org:test",
            parent_org_id="ORG-000001",
        )

    # Self superseded_by
    with pytest.raises(ModelFormatError, match="cannot be superseded by itself"):
        Organization.create(
            org_id="ORG-000001",
            name="Test Org",
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:org:test",
            tombstone=Tombstone[OrganizationID](
                is_deprecated=True,
                deprecated_at=now,
                superseded_by=OrganizationID("ORG-000001"),
            ),
        )

    # Empty name / invalid name type / invalid category / invalid category type
    with pytest.raises(ModelFormatError, match="cannot be empty"):
        Organization.create(
            org_id="ORG-000001",
            name="   ",
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:org:test",
        )

    with pytest.raises(TypeError, match="NameThing or str"):
        Organization.create(
            org_id="ORG-000001",
            name=123,  # type: ignore[arg-type]
            category=OrganizationCategory.CIVIC_SERVICE,
            canonical_urn="urn:gda:org:test",
        )

    with pytest.raises(ModelFormatError, match="Invalid OrganizationCategory value"):
        Organization.create(
            org_id="ORG-000001",
            name="Test Org",
            category="NOT_A_CATEGORY",
            canonical_urn="urn:gda:org:test",
        )

    with pytest.raises(TypeError, match="OrganizationCategory or str"):
        Organization.create(
            org_id="ORG-000001",
            name="Test Org",
            category=999,  # type: ignore[arg-type]
            canonical_urn="urn:gda:org:test",
        )


@pytest.mark.unit
def test_organization_immutable_mutations_and_dirty_tracking() -> None:
    """Verify all immutable update/alias/historic/note methods and dirty-state transitions."""
    note = Note.create(
        note_id=NoteID("NOT-000001"),
        text="Founded by local veterans.",
        note_type=NoteType.GENERAL,
    )
    org = Organization.create(
        org_id="ORG-000411",
        name="VFW Post 411",
        category=OrganizationCategory.VETERANS,
        canonical_urn="urn:gda:org:us:nh:concord:vfw_post_411",
        notes=[note],
    )
    assert org.is_dirty is False
    assert org.mark_clean() is org

    dirty = org.mark_dirty()
    assert dirty.is_dirty is True
    assert dirty.mark_dirty() is dirty
    assert dirty.mark_clean().is_dirty is False

    # Aliases
    with_alias = org.add_alias("Post 411")
    assert with_alias.aliases == ["Post 411"]
    assert with_alias.is_dirty is True
    assert with_alias.add_alias("Post 411") is with_alias

    without_alias = with_alias.remove_alias("Post 411")
    assert without_alias.aliases == []
    assert without_alias.remove_alias("Post 411") is without_alias

    # Historic variants
    with_hist = org.add_historic_variant(
        raw="Veterans of Foreign Wars Post No. 411",
        historic_name_type=HistoricNameType.HISTORICAL,
    )
    assert len(with_hist.historical_names) == 1
    assert with_hist.is_dirty is True

    without_hist = with_hist.remove_historic_variant("Veterans of Foreign Wars Post No. 411")
    assert without_hist.historical_names == []
    assert without_hist.remove_historic_variant("Nonexistent") is without_hist

    # update_name
    assert org.update_name("VFW Post 411") is org
    assert org.update_name(org.name) is org
    renamed = org.update_name("VFW Capital City Post 411")
    assert renamed.canonical_name == "VFW Capital City Post 411"
    assert renamed.is_dirty is True

    with pytest.raises(ModelFormatError, match="cannot be empty"):
        org.update_name("   ")
    with pytest.raises(TypeError, match="NameThing or str"):
        org.update_name(42)  # type: ignore[arg-type]

    # update_category
    assert org.update_category(OrganizationCategory.VETERANS) is org
    assert org.update_category("veterans") is org
    recat = org.update_category("civic_service")
    assert recat.category is OrganizationCategory.CIVIC_SERVICE
    assert recat.is_dirty is True

    with pytest.raises(ModelFormatError, match="Invalid OrganizationCategory value"):
        org.update_category("BOGUS")
    with pytest.raises(TypeError, match="OrganizationCategory or str"):
        org.update_category(123)  # type: ignore[arg-type]

    # update_parent_org, update_location, update_meeting_site
    assert org.update_parent_org(None) is org
    with_parent = org.update_parent_org("ORG-000001")
    assert with_parent.parent_org_id == OrganizationID("ORG-000001")
    assert with_parent.is_dirty is True

    assert org.update_location(None) is org
    with_loc = org.update_location("LOC-000005")
    assert with_loc.location_id == LocationID("LOC-000005")
    assert with_loc.is_dirty is True

    assert org.update_meeting_site(None) is org
    with_site = org.update_meeting_site("SID-000009")
    assert with_site.meeting_site_id == SiteID("SID-000009")
    assert with_site.is_dirty is True

    # update_period & update_active
    assert org.update_period(None) is org
    period = TimePeriod(start_date=EventDate.create("1920"))
    with_period = org.update_period(period)
    assert with_period.period == period
    assert with_period.is_dirty is True

    assert org.update_active(True) is org
    inactive = org.update_active(False)
    assert inactive.is_active is False
    assert inactive.is_dirty is True

    # update_urn
    assert org.update_urn("urn:gda:org:us:nh:concord:vfw_post_411") is org
    new_urn = org.update_urn("urn:gda:org:us:nh:concord:vfw_411")
    assert new_urn.canonical_urn == "urn:gda:org:us:nh:concord:vfw_411"
    assert new_urn.is_dirty is True
    with pytest.raises(ModelFormatError, match="Invalid canonical_urn format"):
        org.update_urn("bad-urn")

    # update_note (non-existent note returns self; existing note updates text and marks dirty)
    assert org.update_note("NOT-999999") is org
    updated_note_org = org.update_note("NOT-000001", text="Updated historical note.")
    assert updated_note_org.is_dirty is True
    assert updated_note_org.notes[0].text == "Updated historical note."


@pytest.mark.unit
def test_organization_serialization_roundtrip_and_errors() -> None:
    """Verify to_dict, from_dict, to_json, and from_json round-trip fidelity."""
    now = IsoTimestamp("2026-02-01T12:00:00Z")
    period = TimePeriod(start_date=EventDate.create("1885"))
    tomb = Tombstone[OrganizationID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=OrganizationID("ORG-000999"),
    )
    note = Note.create(
        note_id=NoteID("NOT-000002"),
        text="Merged into Post 999.",
        note_type=NoteType.RESEARCH,
    )
    org = Organization.create(
        org_id="ORG-000100",
        name="Eureka Lodge No. 70, F. & A.M.",
        category=OrganizationCategory.FRATERNAL,
        canonical_urn="urn:gda:org:us:nh:concord:eureka_lodge_70",
        parent_org_id="ORG-000010",
        location_id="LOC-000001",
        meeting_site_id="SID-000002",
        audit=AuditStamp(created_at=now, updated_at=now),
        tombstone=tomb,
        notes=[note],
        period=period,
        is_active=False,
    )

    payload = org.to_dict()
    assert payload["parent_org_id"] == "ORG-000010"
    assert payload["location_id"] == "LOC-000001"
    assert payload["meeting_site_id"] == "SID-000002"
    assert payload["tombstone"]["superseded_by"] == "ORG-000999"

    restored = Organization.from_dict(payload)
    assert restored == org

    json_str = org.to_json()
    restored_json = Organization.from_json(json_str)
    assert restored_json == org

    # Direct TimePeriod object passed in dict payload
    payload_with_period_obj = dict(payload)
    payload_with_period_obj["period"] = period
    assert Organization.from_dict(payload_with_period_obj) == org

    # Error branches in from_dict / from_json
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Organization.from_dict("not-a-dict")  # type: ignore[arg-type]

    for missing_key in ("id", "name", "category"):
        bad = dict(payload)
        bad.pop(missing_key)
        with pytest.raises(ModelFormatError, match=f"Missing required field '{missing_key}'"):
            Organization.from_dict(bad)

    with pytest.raises(ModelFormatError, match="Failed to parse Organization JSON"):
        Organization.from_json("{invalid json")

    # Minimal dict without optional fields
    minimal = Organization.from_dict(
        {
            "id": "ORG-000200",
            "name": "St. Paul's Men's Choir",
            "category": "CULTURAL_ARTS",
            "canonical_urn": "urn:gda:org:us:nh:concord:st_pauls_choir",
        }
    )
    assert minimal.parent_org_id is None
    assert minimal.location_id is None
    assert minimal.meeting_site_id is None
    assert minimal.period is None
    assert "parent_org_id" not in minimal.to_dict()
    assert replace(minimal, is_active=False).is_active is False
