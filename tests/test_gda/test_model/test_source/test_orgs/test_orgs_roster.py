"""Path: tests/test_gda/test_model/test_source/test_orgs/test_orgs_roster.py

Comprehensive unit tests for OrganizationRosterEntry and OrganizationRosterRecord.

Operational Role:
    Exercises entry creation, whitespace validation, dict/JSON serialization,
    roster duplicate-detection invariants (entry_urn, entry_id, line_number),
    entry lookup helpers (get_entry, require_entry), tabular flattening, and
    from_dict deserialization.
"""

from __future__ import annotations

import pytest

from gda.core.enums.orgs import AffiliationType, MembershipStatus, OrganizationCategory
from gda.core.enums.sources import SourceRecordCategory, SourceRecordType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, OrganizationID, RepositoryID, SourceID
from gda.model.atom.urn import SourceURN
from gda.model.atom.year import HistoricalYear
from gda.model.base.audit import AuditStamp
from gda.model.source.orgs import OrganizationRosterEntry, OrganizationRosterRecord

__version__ = "1.0.0+build.6"

_ROSTER_SID = "44444444-4444-4444-8444-444444444444"
_ENTRY_1_SID = "55555555-5555-4555-8555-555555555555"
_ENTRY_2_SID = "66666666-6666-4666-8666-666666666666"
_ROSTER_URN = "URN:SRC:1900:US_NH_CONCORD:LODGE70-ROSTER"
_ENTRY_1_URN = "URN:SRC:1900:US_NH_CONCORD:LODGE70-ROSTER-L1"
_ENTRY_2_URN = "URN:SRC:1900:US_NH_CONCORD:LODGE70-ROSTER-L2"


def _make_entries() -> tuple[OrganizationRosterEntry, OrganizationRosterEntry]:
    entry_1 = OrganizationRosterEntry(
        entry_urn=SourceURN(_ENTRY_1_URN),
        entry_id=SourceID(_ENTRY_1_SID),
        line_number=1,
        member_name_verbatim="  Abbott, John H.  ",
        individual_id=IndividualID("IND-000001"),
        affiliation_type=AffiliationType.OFFICER,
        membership_status=MembershipStatus.ACTIVE,
        role_or_title_raw="Worshipful Master",
        degree_or_rank_raw="Master Mason",
        admission_date_raw="1888",
        residence_raw="42 Main St.",
        remarks_raw="Past Master 1899",
    )
    entry_2 = OrganizationRosterEntry(
        entry_urn=SourceURN(_ENTRY_2_URN),
        line_number=2,
        member_name_verbatim="Bean, Samuel W.",
        membership_status=MembershipStatus.DEMITTED,
    )
    return entry_1, entry_2


@pytest.mark.unit
@pytest.mark.smoke
def test_roster_entry_and_record_lifecycle() -> None:
    """Verify OrganizationRosterEntry and OrganizationRosterRecord creation, lookup, and flattening."""
    now = IsoTimestamp("2026-04-01T08:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    entry_1, entry_2 = _make_entries()

    assert entry_1.member_name_verbatim == "Abbott, John H."
    assert str(entry_1) == f"Line 1: Abbott, John H. ({entry_1.entry_urn})"
    assert "OrganizationRosterEntry(line_number=1" in repr(entry_1)

    # Entry dict/json roundtrip (including explicit None fields in from_dict)
    e1_restored = OrganizationRosterEntry.from_json(entry_1.to_json())
    assert e1_restored == entry_1
    e2_from_dict = OrganizationRosterEntry.from_dict(
        {
            "entry_urn": _ENTRY_2_URN,
            "entry_id": None,
            "line_number": 2,
            "member_name_verbatim": "Bean, Samuel W.",
            "individual_id": None,
            "membership_status": "DEMITTED",
        }
    )
    assert e2_from_dict == entry_2

    roster = OrganizationRosterRecord(
        source_id=SourceID(_ROSTER_SID),
        source_urn=SourceURN(_ROSTER_URN),
        record_category=SourceRecordCategory.FRATERNAL,
        record_type=SourceRecordType.MEMBERSHIP_ROSTER,
        description="Annual Return of Eureka Lodge No. 70, Concord, NH, 1900.",
        repository_id=RepositoryID("REP-000001"),
        audit=audit,
        enumeration_year=HistoricalYear(1900),
        jurisdiction_raw="Concord, Merrimack County, NH",
        jurisdiction_id=LocationID("LOC-000001"),
        enumerator_or_assessor_raw="William H. Carter, Secretary",
        organization_name_raw="  Eureka Lodge No. 70, F. & A.M.  ",
        org_id=OrganizationID("ORG-000070"),
        org_category=OrganizationCategory.FRATERNAL,
        roster_title="Officers and Members",
        page_number="14",
        entries=(entry_1, entry_2),
    )

    assert roster.organization_name_raw == "Eureka Lodge No. 70, F. & A.M."
    assert roster.entry_count == 2

    # Entry lookups
    assert roster.get_entry("") is None
    assert roster.get_entry(entry_1.entry_urn) == entry_1
    assert roster.get_entry(SourceID(_ENTRY_1_SID)) == entry_1
    assert roster.get_entry("URN:SRC:1900:US_NH_CONCORD:NONEXISTENT") is None
    assert roster.require_entry(entry_2.entry_urn) == entry_2
    with pytest.raises(ModelFormatError, match="No roster entry matching identifier"):
        roster.require_entry("URN:SRC:1900:US_NH_CONCORD:MISSING")

    # Flattening
    rows = roster.flatten_entries()
    assert len(rows) == 2
    assert rows[0]["organization_name_raw"] == "Eureka Lodge No. 70, F. & A.M."
    assert rows[0]["org_id"] == "ORG-000070"
    assert rows[0]["member_name_verbatim"] == "Abbott, John H."
    assert rows[1]["member_name_verbatim"] == "Bean, Samuel W."

    # Dict / JSON roundtrip
    payload = roster.to_dict()
    restored = OrganizationRosterRecord.from_dict(payload)
    assert restored == roster

    restored_json = OrganizationRosterRecord.from_json(roster.to_json())
    assert restored_json == roster

    # Pre-instantiated OrganizationRosterEntry passed inside entries list in from_dict
    payload_pre_built = dict(payload)
    payload_pre_built["entries"] = [entry_1, entry_2]
    assert OrganizationRosterRecord.from_dict(payload_pre_built) == roster


@pytest.mark.unit
@pytest.mark.integrity
def test_roster_validation_and_error_branches() -> None:
    """Verify entry and roster validation boundaries and duplicate detection."""
    now = IsoTimestamp("2026-04-01T08:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    entry_1, entry_2 = _make_entries()

    # Entry whitespace name & invalid deserialization
    with pytest.raises(ModelFormatError, match="member_name_verbatim"):
        OrganizationRosterEntry(
            entry_urn=SourceURN("URN:SRC:1900:US_NH_CONCORD:LODGE70-ROSTER-BAD"),
            line_number=1,
            member_name_verbatim="   ",
        )

    with pytest.raises(ModelFormatError, match="payload must be a dictionary"):
        OrganizationRosterEntry.from_dict("not-a-dict")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="Failed to parse OrganizationRosterEntry JSON"):
        OrganizationRosterEntry.from_json("{bad json")

    base_kwargs = {
        "source_id": SourceID(_ROSTER_SID),
        "source_urn": SourceURN(_ROSTER_URN),
        "description": "Roster test",
        "repository_id": RepositoryID("REP-000001"),
        "audit": audit,
        "enumeration_year": HistoricalYear(1900),
        "jurisdiction_raw": "Concord, NH",
        "organization_name_raw": "Eureka Lodge No. 70",
    }

    # Disallowed category
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        OrganizationRosterRecord(
            **base_kwargs,  # type: ignore[arg-type]
            record_category=SourceRecordCategory.TAX,
            entries=(entry_1,),
        )

    # Disallowed record_type
    with pytest.raises(ModelFormatError, match="requires record_type in"):
        OrganizationRosterRecord(
            **base_kwargs,  # type: ignore[arg-type]
            record_type=SourceRecordType.CITY_DIRECTORY,
            entries=(entry_1,),
        )

    # Empty organization_name_raw
    with pytest.raises(ModelFormatError, match="organization_name_raw"):
        OrganizationRosterRecord(
            **{**base_kwargs, "organization_name_raw": "   "},  # type: ignore[arg-type]
            entries=(entry_1,),
        )

    # Duplicate entry_urn
    dup_urn = OrganizationRosterEntry(
        entry_urn=entry_1.entry_urn,
        line_number=2,
        member_name_verbatim="Duplicate URN Member",
    )
    with pytest.raises(ModelFormatError, match="Duplicate OrganizationRosterEntry entry_urn"):
        OrganizationRosterRecord(
            **base_kwargs,  # type: ignore[arg-type]
            entries=(entry_1, dup_urn),
        )

    # Duplicate entry_id
    dup_id = OrganizationRosterEntry(
        entry_urn=entry_2.entry_urn,
        entry_id=entry_1.entry_id,
        line_number=2,
        member_name_verbatim="Duplicate ID Member",
    )
    with pytest.raises(ModelFormatError, match="Duplicate OrganizationRosterEntry entry_id"):
        OrganizationRosterRecord(
            **base_kwargs,  # type: ignore[arg-type]
            entries=(entry_1, dup_id),
        )

    # Duplicate line_number
    dup_line = OrganizationRosterEntry(
        entry_urn=entry_2.entry_urn,
        line_number=1,
        member_name_verbatim="Duplicate Line Member",
    )
    with pytest.raises(ModelFormatError, match="Duplicate OrganizationRosterEntry line_number"):
        OrganizationRosterRecord(
            **base_kwargs,  # type: ignore[arg-type]
            entries=(entry_1, dup_line),
        )

    # Non-list/tuple entries in from_dict
    valid_roster = OrganizationRosterRecord(
        **base_kwargs,  # type: ignore[arg-type]
        entries=(entry_1,),
    )
    bad_entries_payload = valid_roster.to_dict()
    bad_entries_payload["entries"] = "not-a-list"
    with pytest.raises(ModelFormatError, match="'entries' must be a list or tuple"):
        OrganizationRosterRecord.from_dict(bad_entries_payload)
