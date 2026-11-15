"""Path: tests/test_gda/test_model/test_base/test_base_audit.py

Comprehensive test suite verifying AuditStamp invariants and transitions.

Operational Role:
    Verifies that AuditStamp enforces valid ISO timestamps, chronological ordering,
    .now() and .touch() lifecycle helpers, strict mode rejection, immutability,
    and runtime introspection with 100% statement and branch coverage.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest
from pydantic import ValidationError

from gda.core.dates import validate_iso_timestamp
from gda.core.errors import ModelFormatError
from gda.model.atom.date import IsoTimestamp
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: AUDITSTAMP CREATION & VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_audit_stamp_valid_creation(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify AuditStamp instantiates with equal or advancing timestamps."""
    audit_same = AuditStamp(created_at=ts_created, updated_at=ts_created)
    assert audit_same.created_at == ts_created
    assert audit_same.updated_at == ts_created
    assert str(audit_same) == "created=2026-10-16T10:00:00Z, updated=2026-10-16T10:00:00Z"
    assert repr(audit_same) == (
        "AuditStamp(created_at=IsoTimestamp(value='2026-10-16T10:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T10:00:00Z'))"
    )

    audit_advanced = AuditStamp(created_at=ts_created, updated_at=ts_updated)
    assert audit_advanced.updated_at == ts_updated


@pytest.mark.unit
@pytest.mark.smoke
def test_audit_stamp_now_factory() -> None:
    """Verify AuditStamp.now() mints synchronized UTC timestamps."""
    stamp = AuditStamp.now()
    assert stamp.created_at == stamp.updated_at
    assert validate_iso_timestamp(stamp.created_at.value) is True


@pytest.mark.unit
@pytest.mark.regression
def test_audit_stamp_chronological_inversion_raises_error(
    ts_created: IsoTimestamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify AuditStamp raises ModelFormatError if updated_at precedes created_at."""
    with pytest.raises(ModelFormatError, match="cannot precede created_at"):
        AuditStamp(created_at=ts_updated, updated_at=ts_created)


@pytest.mark.unit
@pytest.mark.regression
def test_audit_stamp_strict_mode_rejects_raw_strings() -> None:
    """Verify strict=True rejects raw strings in place of IsoTimestamp instances."""
    with pytest.raises(ValidationError):
        AuditStamp(
            created_at="2026-10-16T10:00:00Z",  # type: ignore[arg-type]
            updated_at="2026-10-16T10:00:00Z",  # type: ignore[arg-type]
        )


# ==============================================================================
# GROUP 2: TOUCH TRANSITION, IMMUTABILITY & INTROSPECTION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_audit_stamp_touch_returns_new_instance(
    sample_audit: AuditStamp,
    ts_updated: IsoTimestamp,
) -> None:
    """Verify .touch() returns a new AuditStamp with explicit or default UTC updated_at."""
    touched = sample_audit.touch(ts_updated)
    assert touched is not sample_audit
    assert touched.created_at == sample_audit.created_at
    assert touched.updated_at == ts_updated
    assert sample_audit.updated_at == sample_audit.created_at

    touched_now = sample_audit.touch()
    assert touched_now.created_at == sample_audit.created_at
    assert touched_now.updated_at.value >= sample_audit.created_at.value


@pytest.mark.unit
def test_audit_stamp_immutability(sample_audit: AuditStamp) -> None:
    """Verify AuditStamp is frozen and immutable."""
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        sample_audit.updated_at = IsoTimestamp("2026-10-16T11:00:00Z")  # type: ignore[misc]


@pytest.mark.unit
def test_audit_stamp_introspection(sample_audit: AuditStamp) -> None:
    """Verify .help() renders member directory on AuditStamp."""
    help_text = sample_audit.help(as_str=True)
    assert help_text is not None
    assert "=== AuditStamp Public Directory ===" in help_text
    assert "touch" in help_text
