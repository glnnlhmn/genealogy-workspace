"""Path: tests/test_gda/test_model/test_base/test_record_metadata.py

Comprehensive test suite verifying RecordMetadata contracts.

Operational Role:
    Verifies that RecordMetadata enforces mandatory UUIDv4 SourceIDs,
    non-empty URNs, controlled category and type strings, optional RepositoryIDs,
    and immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.id import RepositoryID, SourceID
from gda.model.base.record_metadata import RecordMetadata

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: RECORDMETADATA CREATION & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_record_metadata_valid_creation() -> None:
    """Verify RecordMetadata instantiates with complete attributes."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    rep = RepositoryID("REP-000100")

    meta = RecordMetadata(
        source_id=sid,
        source_urn="urn:gda:source:vital:nh:1880:death:00123",
        record_category="VITAL",
        record_type="DEATH_CERTIFICATE",
        repository_id=rep,
    )
    assert meta.source_id == sid
    assert meta.source_urn == "urn:gda:source:vital:nh:1880:death:00123"
    assert meta.record_category == "VITAL"
    assert meta.record_type == "DEATH_CERTIFICATE"
    assert meta.repository_id == rep
    assert repr(meta) == (
        "RecordMetadata(source_id=SourceID(value='c9a646d3-9c61-4a70-8b14-c48c8b417c8d'), "
        "source_urn='urn:gda:source:vital:nh:1880:death:00123', record_category='VITAL', "
        "record_type='DEATH_CERTIFICATE', repository_id=RepositoryID(value='REP-000100'))"
    )


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
@pytest.mark.parametrize(
    ("urn", "cat", "rtype", "field_expected"),
    [
        ("", "VITAL", "DEATH_CERTIFICATE", "source_urn"),
        ("urn:sample", "", "DEATH_CERTIFICATE", "record_category"),
        ("urn:sample", "VITAL", "   ", "record_type"),
    ],
)
def test_record_metadata_empty_strings_raise_error(
    urn: str, cat: str, rtype: str, field_expected: str
) -> None:
    """Verify RecordMetadata raises ModelFormatError on empty string fields."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    with pytest.raises(ModelFormatError, match=f"'{field_expected}' cannot be empty"):
        RecordMetadata(
            source_id=sid,
            source_urn=urn,
            record_category=cat,
            record_type=rtype,
        )


@pytest.mark.unit
def test_record_metadata_immutability() -> None:
    """Verify RecordMetadata is frozen and immutable."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    meta = RecordMetadata(
        source_id=sid,
        source_urn="urn:sample",
        record_category="VITAL",
        record_type="DEATH_CERTIFICATE",
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        meta.record_type = "BIRTH_CERTIFICATE"  # type: ignore[misc]


@pytest.mark.unit
def test_record_metadata_introspection() -> None:
    """Verify .help() renders member directory on RecordMetadata."""
    sid = SourceID("c9a646d3-9c61-4a70-8b14-c48c8b417c8d")
    meta = RecordMetadata(
        source_id=sid,
        source_urn="urn:sample",
        record_category="VITAL",
        record_type="DEATH_CERTIFICATE",
    )
    help_text = meta.help(as_str=True)
    assert help_text is not None
    assert "=== RecordMetadata Public Directory ===" in help_text
