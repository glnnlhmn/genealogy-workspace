"""Path: tests/test_gda/test_entity/test_facts/test_facts_contract.py

Authoritative public interface and contract verification suite for gda.entity.facts.

Operational Role:
    Verifies the end-to-end fact creation, timeline lookup, validation, and
    lifecycle gateway, enforces the 4-submodule topology and sorted 18-symbol
    __all__ contract of gda.entity.facts, verifies centralized
    ENTITY_URN_REGEXES['FID'] binding, and ensures zero legacy imports.
"""

from __future__ import annotations

import ast
import inspect
import pkgutil
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import gda.entity as entity_root_pkg
import gda.entity.facts as facts_pkg
import gda.entity.facts.collection as collection_mod
import gda.entity.facts.errors as errors_mod
import gda.entity.facts.util as util_mod
import gda.entity.facts.validation as validation_mod
from gda.core.enums.core import FactType
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.facts import (
    FactError,
    FactNotFoundError,
    Facts,
    FactValidationError,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_fact,
    undelete_fact,
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_fact,
    valid_urn,
)
from gda.model.atom.id import FactID

__version__ = "1.0.0+build.1"

_EXPECTED_SUBMODULES = {
    "collection",
    "errors",
    "util",
    "validation",
}

AUTHORITATIVE_FACTS_EXPORTS = [
    "FactError",
    "FactNotFoundError",
    "FactValidationError",
    "Facts",
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_fact",
    "undelete_fact",
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_fact",
    "valid_urn",
]


@pytest.mark.smoke
@pytest.mark.unit
def test_facts_subsystem_gateway_smoke_pipeline(
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify end-to-end fact creation, timeline lookup, validation, retirement, and restoration."""
    collection = Facts()

    fact = collection.create(
        fact_type=FactType.BIRTH,
        title="Birth of John Quincy Adams",
        primary_subject_id="IND-000001",
        date="1842-05-14",
        location_id="LOC-000004",
        site_id="SID-000001",
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )

    assert isinstance(fact.id, FactID)
    assert fact.fact_type == FactType.BIRTH
    assert fact.id in collection
    assert fact.canonical_urn in collection
    assert valid_fact(fact) is True
    assert (
        valid_collection_all(
            collection,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is True
    )

    retired = collection.soft_delete(fact.id, reason="Duplicate birth assertion")
    assert retired.tombstone.is_deprecated is True
    assert fact.id not in collection

    restored = collection.undelete(
        fact.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert fact.id in collection


@pytest.mark.unit
@pytest.mark.integrity
def test_facts_pkg_topology_and_dunder_all_contract() -> None:
    """Verify submodule topology, sorted 18-symbol __all__, and centralized URN regex binding."""
    discovered = {m.name for m in pkgutil.iter_modules(facts_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    assert facts_pkg.__all__ == AUTHORITATIVE_FACTS_EXPORTS
    assert facts_pkg.__all__ == sorted(facts_pkg.__all__)
    for attr in AUTHORITATIVE_FACTS_EXPORTS:
        assert hasattr(facts_pkg, attr), f"Export '{attr}' missing from gda.entity.facts"

    assert collection_mod.__all__ == ["Facts"]
    assert errors_mod.__all__ == [
        "FactError",
        "FactNotFoundError",
        "FactValidationError",
    ]
    assert util_mod.__all__ == sorted(util_mod.__all__)
    assert validation_mod.__all__ == sorted(validation_mod.__all__)
    assert validation_mod._FACT_URN_PATTERN is ENTITY_URN_REGEXES["FID"]

    assert entity_root_pkg.__all__ == sorted(entity_root_pkg.__all__)
    assert "Facts" in entity_root_pkg.__all__
    assert "facts" in entity_root_pkg.__all__


@pytest.mark.unit
@pytest.mark.integrity
def test_facts_pkg_class_and_exception_types() -> None:
    """Verify exported classes and exceptions conform to expected inheritance."""
    assert isinstance(Facts, type)
    assert issubclass(Facts, IntrospectableMixin)

    for exc_cls in (FactError, FactNotFoundError, FactValidationError):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.unit
@pytest.mark.integrity
def test_facts_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports in gda.entity.facts are callable."""
    callables = (
        can_tombstone,
        can_undelete,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        tombstone_fact,
        undelete_fact,
        valid_collection_all,
        valid_collection_indexes,
        valid_collection_references,
        valid_collection_tombstones,
        valid_fact,
        valid_urn,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.unit
@pytest.mark.integrity
def test_facts_pkg_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy gda.enums or gda.util.tombstone imports."""
    assert facts_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(facts_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(
                    ("gda.enums", "gda.util.tombstone", "gda.model.atom.geo")
                ), f"Forbidden legacy import in {py_path}: '{node.module}'"
