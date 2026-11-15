"""Path: tests/test_gda/test_model/test_source/test_manuscripts/test_manuscripts_contract.py

Authoritative public interface and contract verification suite for gda.model.source.manuscripts.

Operational Role:
    Freezes and validates the 2-submodule topology (bible, narrative), sorted
    __all__ facade, SourceRecord and IntrospectableMixin inheritance,
    centralized URN_REGEXES integration, and serialization contracts for
    BibleRegisterEntry, FamilyBibleRecord, and NarrativeManuscriptRecord.
"""

from __future__ import annotations

import dataclasses
import pkgutil

import pytest

import gda.model.source.manuscripts as manuscripts_pkg
import gda.model.source.manuscripts.bible as bible_mod
import gda.model.source.manuscripts.narrative as narrative_mod
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import URN_REGEXES
from gda.model.base.source import SourceRecord
from gda.model.source.manuscripts import (
    BibleRegisterEntry,
    FamilyBibleRecord,
    NarrativeManuscriptRecord,
)

__version__ = "1.0.0+build.1"

AUTHORITATIVE_MANUSCRIPTS_EXPORTS = [
    "BibleRegisterEntry",
    "FamilyBibleRecord",
    "NarrativeManuscriptRecord",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_manuscripts_package_topology_and_exports_contract() -> None:
    """Verify gda.model.source.manuscripts submodule topology and sorted __all__ exports."""
    discovered = {m.name for m in pkgutil.iter_modules(manuscripts_pkg.__path__)}
    assert discovered == {"bible", "narrative"}
    assert manuscripts_pkg.__all__ == AUTHORITATIVE_MANUSCRIPTS_EXPORTS
    assert manuscripts_pkg.__all__ == sorted(manuscripts_pkg.__all__)
    assert bible_mod.__all__ == ["BibleRegisterEntry", "FamilyBibleRecord"]
    assert narrative_mod.__all__ == ["NarrativeManuscriptRecord"]
    assert bible_mod._MS_URN_PATTERN is URN_REGEXES["MS"]
    assert bible_mod._BIBLE_URN_PATTERN is URN_REGEXES["BIBLE"]
    assert narrative_mod._MS_URN_PATTERN is URN_REGEXES["MS"]
    assert narrative_mod._NARRATIVE_URN_PATTERN is URN_REGEXES["NARRATIVE"]


@pytest.mark.unit
@pytest.mark.integrity
@pytest.mark.parametrize(
    "cls",
    (BibleRegisterEntry, FamilyBibleRecord, NarrativeManuscriptRecord),
    ids=lambda c: c.__name__,
)
def test_manuscripts_classes_enforce_frozen_strict_and_serialization(cls: type) -> None:
    """Verify all manuscript dataclasses enforce frozen/strict config and serialization methods."""
    assert dataclasses.is_dataclass(cls)
    assert issubclass(cls, IntrospectableMixin)
    assert cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    if cls is not BibleRegisterEntry:
        assert issubclass(cls, SourceRecord)
    for method in ("create", "to_dict", "from_dict", "to_json", "from_json"):
        assert callable(getattr(cls, method))
