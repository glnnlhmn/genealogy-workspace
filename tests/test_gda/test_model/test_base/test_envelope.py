"""Path: tests/test_gda/test_model/test_base/test_envelope.py

Comprehensive test suite verifying generic RegistryEnvelope contracts.

Operational Role:
    Verifies that RegistryEnvelope validates non-empty schema version strings,
    binds generation timestamps, enforces total_count matching record collection length,
    and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID
from gda.model.base.envelope import RegistryEnvelope

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: REGISTRYENVELOPE CREATION & PROPERTIES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_registry_envelope_valid_creation() -> None:
    """Verify RegistryEnvelope instantiates with matching counts and generic items."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    records = [IndividualID("IND-000001"), IndividualID("IND-000002")]

    envelope: RegistryEnvelope[IndividualID] = RegistryEnvelope(
        schema_version="1.0.0",
        last_modified=ts,
        total_count=2,
        records=records,
    )
    assert envelope.schema_version == "1.0.0"
    assert envelope.last_modified == ts
    assert envelope.total_count == 2
    assert envelope.records == records
    assert repr(envelope) == (
        "RegistryEnvelope(version='1.0.0', count=2, "
        "modified=IsoTimestamp(value='2026-10-16T12:00:00Z'))"
    )


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_registry_envelope_empty_schema_version_raises_error() -> None:
    """Verify RegistryEnvelope raises ModelFormatError on empty schema_version."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    with pytest.raises(ModelFormatError, match="schema_version cannot be empty"):
        RegistryEnvelope(
            schema_version="",
            last_modified=ts,
            total_count=0,
            records=[],
        )


@pytest.mark.unit
@pytest.mark.regression
def test_registry_envelope_count_mismatch_raises_error() -> None:
    """Verify RegistryEnvelope raises ModelFormatError when total_count != len(records)."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    records = [IndividualID("IND-000001")]

    with pytest.raises(ModelFormatError, match="total_count mismatch"):
        RegistryEnvelope(
            schema_version="1.0.0",
            last_modified=ts,
            total_count=5,
            records=records,
        )


@pytest.mark.unit
def test_registry_envelope_immutability() -> None:
    """Verify RegistryEnvelope is frozen and immutable."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    envelope: RegistryEnvelope[str] = RegistryEnvelope(
        schema_version="1.0.0",
        last_modified=ts,
        total_count=1,
        records=["item"],
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        envelope.total_count = 2  # type: ignore[misc]


@pytest.mark.unit
def test_registry_envelope_introspection() -> None:
    """Verify .help() renders member directory on RegistryEnvelope."""
    ts = IsoTimestamp("2026-10-16T12:00:00Z")
    envelope: RegistryEnvelope[str] = RegistryEnvelope(
        schema_version="1.0.0",
        last_modified=ts,
        total_count=0,
        records=[],
    )
    help_text = envelope.help(as_str=True)
    assert help_text is not None
    assert "=== RegistryEnvelope Public Directory ===" in help_text
