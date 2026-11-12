"""Path: tests/test_gda/test_model/test_base/test_comp_envelopes/test_envelope.py

Comprehensive test suite verifying generic RegistryEnvelope contracts.

Operational Role:
    Verifies that RegistryEnvelope validates non-empty schema version strings,
    binds generation timestamps, enforces total_count matching record collection length,
    provides .create() factory construction, and guarantees immutability with 100%
    statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.dates import validate_iso_timestamp
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import IndividualID
from gda.model.base.envelope import RegistryEnvelope

__version__ = "1.1.0+build.1"


# ==============================================================================
# GROUP 1: REGISTRYENVELOPE CREATION & FACTORY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_registry_envelope_valid_creation(golden_timestamp: IsoTimestamp) -> None:
    """Verify RegistryEnvelope instantiates with matching counts and generic items."""
    records = [IndividualID("IND-000001"), IndividualID("IND-000002")]

    envelope: RegistryEnvelope[IndividualID] = RegistryEnvelope(
        schema_version="1.0.0",
        last_modified=golden_timestamp,
        total_count=2,
        records=records,
    )
    assert envelope.schema_version == "1.0.0"
    assert envelope.last_modified == golden_timestamp
    assert envelope.total_count == 2
    assert envelope.records == records
    assert str(envelope) == "RegistryEnvelope v1.0.0 (2 records)"
    assert repr(envelope) == (
        "RegistryEnvelope(version='1.0.0', count=2, "
        "modified=IsoTimestamp(value='2026-10-16T12:00:00Z'))"
    )


@pytest.mark.unit
@pytest.mark.smoke
def test_registry_envelope_create_factory(golden_timestamp: IsoTimestamp) -> None:
    """Verify RegistryEnvelope.create() computes total_count and parses timestamps."""
    env_now = RegistryEnvelope.create("  1.2.0  ", ["a", "b", "c"])
    assert env_now.schema_version == "1.2.0"
    assert env_now.total_count == 3
    assert validate_iso_timestamp(env_now.last_modified.value) is True

    env_str_ts = RegistryEnvelope.create("1.2.0", ["a"], last_modified="2026-10-16T12:00:00Z")
    assert env_str_ts.last_modified == golden_timestamp

    env_atom_ts = RegistryEnvelope.create("1.2.0", [], last_modified=golden_timestamp)
    assert env_atom_ts.last_modified == golden_timestamp


# ==============================================================================
# GROUP 2: DEFENSIVE BOUNDARIES & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_registry_envelope_validation_errors(golden_timestamp: IsoTimestamp) -> None:
    """Verify RegistryEnvelope raises errors on blank version, count mismatch, or bad types."""
    with pytest.raises(ModelFormatError, match="schema_version cannot be empty"):
        RegistryEnvelope(
            schema_version="   ",
            last_modified=golden_timestamp,
            total_count=0,
            records=[],
        )

    with pytest.raises(ModelFormatError, match="schema_version cannot be empty"):
        RegistryEnvelope.create("   ", [])

    with pytest.raises(ModelFormatError, match="Invalid last_modified type"):
        RegistryEnvelope.create("1.0.0", [], last_modified=123)  # type: ignore[arg-type]

    with pytest.raises(ModelFormatError, match="total_count mismatch"):
        RegistryEnvelope(
            schema_version="1.0.0",
            last_modified=golden_timestamp,
            total_count=5,
            records=[IndividualID("IND-000001")],
        )

    with pytest.raises(ValidationError):
        RegistryEnvelope(
            schema_version="1.0.0",
            last_modified="2026-10-16T12:00:00Z",  # type: ignore[arg-type]
            total_count=0,
            records=[],
        )


@pytest.mark.unit
def test_registry_envelope_immutability_and_introspection(
    golden_timestamp: IsoTimestamp,
) -> None:
    """Verify RegistryEnvelope is frozen and renders .help()."""
    envelope: RegistryEnvelope[str] = RegistryEnvelope(
        schema_version="1.0.0",
        last_modified=golden_timestamp,
        total_count=1,
        records=["item"],
    )
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        envelope.total_count = 2  # type: ignore[misc]

    help_text = envelope.help(as_str=True)
    assert help_text is not None
    assert "=== RegistryEnvelope Public Directory ===" in help_text
