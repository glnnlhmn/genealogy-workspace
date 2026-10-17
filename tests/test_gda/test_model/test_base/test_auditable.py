# Name: test_auditable.py
# Path: tests/test_gda/test_model/test_base/test_auditable.py

"""Comprehensive test suite verifying AuditableModel base delegation and properties.

Operational Role:
    Verifies that AuditableModel correctly encapsulates an AuditStamp, exposes
    delegated created_at and updated_at properties, and guarantees immutability.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Standard 7-marker taxonomy.
    - Zero production disk I/O.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from gda.model.atom.date import IsoTimestamp
from gda.model.base.audit import AuditStamp
from gda.model.base.auditable import AuditableModel

__version__ = "1.0.0+build.r2"


# ==============================================================================
# GROUP 1: AUDITABLEMODEL CREATION & DELEGATION
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_auditable_model_properties_delegation() -> None:
    """Verify AuditableModel exposes created_at and updated_at properties."""
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    t2 = IsoTimestamp("2026-10-16T14:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t2)

    model = AuditableModel(audit=audit)
    assert model.audit == audit
    assert model.created_at == t1
    assert model.updated_at == t2


@pytest.mark.unit
def test_auditable_model_immutability() -> None:
    """Verify AuditableModel is frozen and immutable."""
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    model = AuditableModel(audit=audit)

    with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
        model.audit = audit.touch(IsoTimestamp("2026-10-16T13:00:00Z"))  # type: ignore[misc]


@pytest.mark.unit
def test_auditable_model_introspection() -> None:
    """Verify .help() renders on AuditableModel."""
    t1 = IsoTimestamp("2026-10-16T12:00:00Z")
    audit = AuditStamp(created_at=t1, updated_at=t1)
    model = AuditableModel(audit=audit)

    help_text = model.help(as_str=True)
    assert help_text is not None
    assert "=== AuditableModel Public Directory ===" in help_text
    assert "created_at" in help_text
    assert "updated_at" in help_text
