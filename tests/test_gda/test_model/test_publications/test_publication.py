"""Path: tests/test_gda/test_model/test_publications/test_publication.py

Comprehensive unit tests for gda.model.publications.publication.Publication.

Operational Role:
    Exercises factory creation, SourceRecord inheritance, NameThing masthead
    forwarding, PUB_CODE_REGEX validation, PublicationFrequency parsing,
    TimePeriod accessors, dict/JSON round-trip serialization, and defensive
    deserialization boundaries.
"""

from __future__ import annotations

import pytest

from gda.core.enums.archival import PublicationFrequency
from gda.core.enums.core import AssociatedRole
from gda.core.enums.sources import SourceRecordCategory
from gda.core.enums.vital import HistoricNameType
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID, LocationID, MediaID, RepositoryID, SourceID
from gda.model.base.association import AssociatedIndividual
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.name import HistoricVariant, NameThing
from gda.model.base.tombstone import Tombstone
from gda.model.publications import Publication

__version__ = "1.0.0+build.2"

_SID = "11111111-1111-4111-8111-111111111111"
_SID_2 = "22222222-2222-4222-8222-222222222222"
_MID = "33333333-3333-4333-8333-333333333333"
_URN = "URN:SRC:1864:US_NH_CONCORD:CONCORD_MONITOR_RUN"
_URN_MIN = "URN:SRC:1890:US_NH_CONCORD:NH_PATRIOT_RUN"


@pytest.mark.unit
@pytest.mark.smoke
def test_publication_create_and_roundtrip() -> None:
    """Verify Publication.create with full masthead history, period, and serialization."""
    now = IsoTimestamp("2026-06-01T10:00:00Z")
    audit = AuditStamp(created_at=now, updated_at=now)
    start = EventDate.create("1864-05-23")
    end = EventDate.create("1923-03-31")
    period = TimePeriod(start_date=start, end_date=end)
    title = NameThing(
        raw="Concord Daily Monitor",
        canonical="Concord Daily Monitor",
        aliases=["Daily Monitor", "Concord Monitor"],
        historic=[
            HistoricVariant(
                raw="Concord Monitor and New Hampshire Patriot",
                name="Concord Monitor and New Hampshire Patriot",
                historic_name_type=HistoricNameType.HISTORICAL,
            )
        ],
    )
    tomb = Tombstone[SourceID](
        is_deprecated=True,
        deprecated_at=now,
        superseded_by=SourceID(_SID_2),
    )
    assoc = AssociatedIndividual(
        individual_id=IndividualID("IND-000001"),
        name_raw="William E. Chandler",
        role=AssociatedRole.EMPLOYER,
    )

    pub = Publication.create(
        source_id=_SID,
        source_urn=_URN,
        description="Microfilm run of the Concord Daily Monitor (1864-1923).",
        repository_id="REP-000001",
        title=title,
        pub_code="  concord_monitor  ",
        record_category="news",
        record_type="misc",
        frequency="Daily",
        publisher_raw="Monitor & Statesman Co.",
        place_of_publication_raw="Concord, NH",
        location_id="LOC-000001",
        publication_period=period,
        issn_or_lccn="sn83021319",
        is_active=False,
        audit=audit,
        media_ids=[_MID],
        associated_people=[assoc],
        tombstone=tomb,
    )

    assert pub.canonical_title == "Concord Daily Monitor"
    assert pub.aliases == ["Daily Monitor", "Concord Monitor"]
    assert len(pub.historical_titles) == 1
    assert pub.pub_code == "CONCORD_MONITOR"
    assert pub.frequency is PublicationFrequency.DAILY
    assert pub.location_id == LocationID("LOC-000001")
    assert pub.first_issue_date == start
    assert pub.last_issue_date == end
    assert pub.is_active is False
    assert str(pub) == "Publication [Concord Daily Monitor] (CONCORD_MONITOR)"

    payload = pub.to_dict()
    assert payload["pub_code"] == "CONCORD_MONITOR"
    assert payload["frequency"] == "Daily"
    assert payload["publisher_raw"] == "Monitor & Statesman Co."
    assert payload["place_of_publication_raw"] == "Concord, NH"
    assert payload["location_id"] == "LOC-000001"
    assert payload["issn_or_lccn"] == "sn83021319"

    restored = Publication.from_dict(payload)
    assert restored == pub

    restored_json = Publication.from_json(pub.to_json())
    assert restored_json == pub

    # Direct AuditStamp, TimePeriod, NameThing, and enum member name frequency in from_dict
    direct_payload = dict(payload)
    direct_payload["audit"] = audit
    direct_payload["publication_period"] = period
    direct_payload["title"] = title
    direct_payload["frequency"] = "SEMI_WEEKLY"
    restored_direct = Publication.from_dict(direct_payload)
    assert restored_direct.frequency is PublicationFrequency.SEMI_WEEKLY

    # Direct PublicationFrequency enum member passed to create()
    enum_freq_pub = Publication.create(
        source_id=_SID,
        source_urn=_URN_MIN,
        description="Enum frequency member check.",
        repository_id="REP-000001",
        title="New Hampshire Patriot",
        pub_code="NH_PATRIOT",
        frequency=PublicationFrequency.WEEKLY,
    )
    assert enum_freq_pub.frequency is PublicationFrequency.WEEKLY


@pytest.mark.unit
@pytest.mark.integrity
def test_publication_validation_and_minimal_roundtrip() -> None:
    """Verify Publication minimal round-trip and validation error branches."""
    minimal = Publication.create(
        source_id=SourceID(_SID),
        source_urn=_URN_MIN,
        description="New Hampshire Patriot serial container.",
        repository_id=RepositoryID("REP-000001"),
        title="New Hampshire Patriot",
        pub_code="NH_PATRIOT",
        media_ids=[MediaID(_MID)],
    )
    assert minimal.first_issue_date is None
    assert minimal.last_issue_date is None

    min_dict = minimal.to_dict()
    for opt_key in (
        "frequency",
        "publisher_raw",
        "place_of_publication_raw",
        "location_id",
        "publication_period",
        "issn_or_lccn",
    ):
        assert opt_key not in min_dict
    assert Publication.from_dict(min_dict) == minimal

    # Direct constructor normalizes lowercase pub_code
    direct = Publication(
        source_id=SourceID(_SID),
        source_urn=minimal.source_urn,
        description="Direct init test",
        repository_id=RepositoryID("REP-000001"),
        audit=minimal.audit,
        title=NameThing.create(raw="Direct Title", canonical="Direct Title"),
        pub_code="  nh_patriot  ",
    )
    assert direct.pub_code == "NH_PATRIOT"

    # Validation failures
    with pytest.raises(ModelFormatError, match="requires record_category in"):
        Publication.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Wrong category",
            repository_id="REP-000001",
            title="New Hampshire Patriot",
            pub_code="NH_PATRIOT",
            record_category=SourceRecordCategory.VITAL,
        )

    with pytest.raises(ModelFormatError, match="Invalid pub_code format"):
        Publication.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad pub_code",
            repository_id="REP-000001",
            title="New Hampshire Patriot",
            pub_code="X",
        )

    with pytest.raises(ModelFormatError, match="cannot be empty or whitespace"):
        Publication.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Empty title",
            repository_id="REP-000001",
            title="   ",
            pub_code="NH_PATRIOT",
        )

    with pytest.raises(TypeError, match="must be NameThing or str"):
        Publication.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad title type",
            repository_id="REP-000001",
            title=12345,  # type: ignore[arg-type]
            pub_code="NH_PATRIOT",
        )

    with pytest.raises(ModelFormatError, match="Invalid PublicationFrequency value"):
        Publication.create(
            source_id=_SID,
            source_urn=_URN_MIN,
            description="Bad frequency",
            repository_id="REP-000001",
            title="New Hampshire Patriot",
            pub_code="NH_PATRIOT",
            frequency="DECENNIAL",
        )

    # from_dict error branches
    with pytest.raises(ModelFormatError, match="must be a dictionary"):
        Publication.from_dict("bad")  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="requires source_id"):
        Publication.from_dict({"source_id": _SID})

    bad_audit = dict(min_dict)
    bad_audit["audit"] = "bad"
    with pytest.raises(ModelFormatError, match="audit must be an AuditStamp or dictionary"):
        Publication.from_dict(bad_audit)
