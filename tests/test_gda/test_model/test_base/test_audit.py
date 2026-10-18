"""Path: tests/test_gda/test_model/test_base/test_audit.py

Comprehensive test suite verifying AuditStamp invariants and transitions.

Operational Role:
    Verifies that AuditStamp enforces valid ISO timestamps, chronological ordering,
    touch mutation helpers, immutability, and runtime introspection.

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
from gda.model.base.audit import AuditStamp

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: AUDITSTAMP CREATION & VALIDATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_audit_stamp_valid_creation() -> None:
    """Verify AuditStamp instantiates with equal or advancing timestamps."""
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    t2 = IsoTimestamp("2026-10-16T13:00:00Z")

    audit_same = AuditStamp(created_at=t1, updated_at=t1)
    assert audit_same.created_at == t1
    assert audit_same.updated_at == t1
    assert repr(audit_same) == (
        "AuditStamp(created_at=IsoTimestamp(value='2026-10-16T12:00:00Z'), "
        "updated_at=IsoTimestamp(value='2026-10-16T12:00:00Z'))"
    )

    audit_advanced = AuditStamp(created_at=t1, updated_at=t2)
    assert audit_advanced.updated_at == t2


@pytest.mark.unit
@pytest.mark.regression
def test_audit_stamp_chronological_inversion_raises_error() -> None:
    """Verify AuditStamp raises ModelFormatError if updated_at precedes created_at."""
    t1 = IsoTimestamp("2026-10-16T14:00:00Z")
    t2 = IsoTimestamp("2026-10-16T12:00:00Z")

    with pytest.raises(ModelFormatError, match="cannot precede created_at"):
        AuditStamp(created_at=t1, updated_at=t2)


# ==============================================================================
# GROUP 2: TOUCH TRANSITION & IMMUTABILITY
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_audit_stamp_touch_returns_new_instance() -> None:
    """Verify .touch() returns a new AuditStamp with advanced updated_at."""
    t1 = IsoTimestamp("2026-10-16T10:00:00Z")
    t2 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)

    touched = audit.touch(t2)
    assert touched is not audit
    assert touched.created_at == t1
    assert touched.updated_at == t2
    assert audit.updated_at == t1


@pytest.mark.unit
def test_audit_stamp_immutability() -> None:
    """Verify AuditStamp is frozen and immutable."""
    t1 = IsoTimestamp("2026-10-16T10:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        audit.updated_at = IsoTimestamp("2026-10-16T11:00:00Z")  # type: ignore[misc]


@pytest.mark.unit
def test_audit_stamp_introspection() -> None:
    """Verify .help() renders member directory on AuditStamp."""
    t1 = IsoTimestamp("2026-10-16T10:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    help_text = audit.help(as_str=True)
    assert help_text is not None
    assert "=== AuditStamp Public Directory ===" in help_text
    assert "touch" in help_text
