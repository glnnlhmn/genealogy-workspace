"""Path: tests/test_gda/test_model/test_source/test_education/test_education_contract.py

Authoritative public interface and contract verification suite for gda.model.source.education.

Operational Role:
    Freezes and validates the submodule topology, sorted __all__ facade,
    SourceRecord and IntrospectableMixin inheritance, frozen/strict Pydantic
    dataclass configuration, centralized URN_REGEXES['DIPLOMA'] usage, and
    required serialization methods for AcademicCredentialRecord.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest

import gda.model.source.education as education_pkg
import gda.model.source.education.credential as credential_mod
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_REGEXES
from gda.model.base.source import SourceRecord
from gda.model.source.education import AcademicCredentialRecord

__version__ = "1.0.0+build.1"

AUTHORITATIVE_EDUCATION_EXPORTS = [
    "AcademicCredentialRecord",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_education_package_topology_and_exports_contract() -> None:
    """Verify gda.model.source.education submodule topology and sorted __all__ exports."""
    discovered = {m.name for m in pkgutil.iter_modules(education_pkg.__path__)}
    assert discovered == {"credential"}
    assert education_pkg.__all__ == AUTHORITATIVE_EDUCATION_EXPORTS
    assert education_pkg.__all__ == sorted(education_pkg.__all__)
    assert credential_mod.__all__ == ["AcademicCredentialRecord"]
    assert credential_mod._DIPLOMA_URN_PATTERN is URN_REGEXES["DIPLOMA"]


@pytest.mark.unit
@pytest.mark.integrity
def test_academic_credential_record_inheritance_and_methods_contract() -> None:
    """Verify AcademicCredentialRecord extends SourceRecord and enforces frozen/strict invariants."""
    assert dataclasses.is_dataclass(AcademicCredentialRecord)
    assert issubclass(AcademicCredentialRecord, SourceRecord)
    assert issubclass(AcademicCredentialRecord, IntrospectableMixin)
    assert AcademicCredentialRecord.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    for method in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(AcademicCredentialRecord, method))
