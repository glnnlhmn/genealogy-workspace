"""Path: tests/test_gda/test_entity/test_individuals/test_individuals_contract.py

Authoritative public interface and contract verification suite for gda.entity.individuals.

Operational Role:
    Verifies the end-to-end individual persona creation, surname lookup,
    validation, and lifecycle gateway, enforces the 4-submodule topology and
    sorted 18-symbol __all__ contract of gda.entity.individuals, verifies
    centralized ENTITY_URN_REGEXES['IND'] binding, and ensures zero legacy
    imports.
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
import gda.entity.individuals as inds_pkg
import gda.entity.individuals.collection as collection_mod
import gda.entity.individuals.errors as errors_mod
import gda.entity.individuals.util as util_mod
import gda.entity.individuals.validation as validation_mod
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.individuals import (
    IndividualError,
    IndividualNotFoundError,
    Individuals,
    IndividualValidationError,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_individual,
    undelete_individual,
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_individual,
    valid_urn,
)
from gda.model.atom.id import IndividualID

__version__ = "1.0.0+build.1"

_EXPECTED_SUBMODULES = {
    "collection",
    "errors",
    "util",
    "validation",
}

AUTHORITATIVE_INDIVIDUALS_EXPORTS = [
    "IndividualError",
    "IndividualNotFoundError",
    "IndividualValidationError",
    "Individuals",
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_individual",
    "undelete_individual",
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_individual",
    "valid_urn",
]


@pytest.mark.smoke
@pytest.mark.unit
def test_individuals_subsystem_gateway_smoke_pipeline(
    mock_locations_collection: MagicMock,
    mock_sites_collection: MagicMock,
) -> None:
    """Verify end-to-end individual creation, surname lookup, validation, retirement, and restoration."""
    collection = Individuals()

    ind = collection.create(
        name="Abigail Smith",
        gender="F",
        birth_date="1744-11-22",
        death_date="1818-10-28",
        birth_place_id="LOC-000004",
        death_place_id="SID-000001",
        alternate_names=["Abby Adams"],
        married_names=["Adams"],
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )

    assert isinstance(ind.id, IndividualID)
    assert ind.id in collection
    assert ind.canonical_urn in collection
    assert collection.find_by_surname("Smith") == [ind]
    assert collection.find_by_surname("Adams") == [ind]
    assert valid_individual(ind) is True
    assert (
        valid_collection_all(
            collection,
            locations_collection=mock_locations_collection,
            sites_collection=mock_sites_collection,
        )
        is True
    )

    retired = collection.soft_delete(ind.id, reason="Duplicate persona")
    assert retired.tombstone.is_deprecated is True
    assert ind.id not in collection

    restored = collection.undelete(
        ind.id,
        locations_collection=mock_locations_collection,
        sites_collection=mock_sites_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert ind.id in collection


@pytest.mark.unit
@pytest.mark.integrity
def test_individuals_pkg_topology_and_dunder_all_contract() -> None:
    """Verify submodule topology, sorted 18-symbol __all__, and centralized URN regex binding."""
    discovered = {m.name for m in pkgutil.iter_modules(inds_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    assert inds_pkg.__all__ == AUTHORITATIVE_INDIVIDUALS_EXPORTS
    assert inds_pkg.__all__ == sorted(inds_pkg.__all__)
    for attr in AUTHORITATIVE_INDIVIDUALS_EXPORTS:
        assert hasattr(inds_pkg, attr), f"Export '{attr}' missing from gda.entity.individuals"

    assert collection_mod.__all__ == ["Individuals"]
    assert errors_mod.__all__ == [
        "IndividualError",
        "IndividualNotFoundError",
        "IndividualValidationError",
    ]
    assert util_mod.__all__ == sorted(util_mod.__all__)
    assert validation_mod.__all__ == sorted(validation_mod.__all__)
    assert validation_mod._INDIVIDUAL_URN_PATTERN is ENTITY_URN_REGEXES["IND"]

    assert entity_root_pkg.__all__ == sorted(entity_root_pkg.__all__)
    assert "Individuals" in entity_root_pkg.__all__
    assert "individuals" in entity_root_pkg.__all__


@pytest.mark.unit
@pytest.mark.integrity
def test_individuals_pkg_class_and_exception_types() -> None:
    """Verify exported classes and exceptions conform to expected inheritance."""
    assert isinstance(Individuals, type)
    assert issubclass(Individuals, IntrospectableMixin)

    for exc_cls in (IndividualError, IndividualNotFoundError, IndividualValidationError):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.unit
@pytest.mark.integrity
def test_individuals_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports in gda.entity.individuals are callable."""
    callables = (
        can_tombstone,
        can_undelete,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        tombstone_individual,
        undelete_individual,
        valid_collection_all,
        valid_collection_indexes,
        valid_collection_references,
        valid_collection_tombstones,
        valid_individual,
        valid_urn,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.unit
@pytest.mark.integrity
def test_individuals_pkg_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy gda.enums or gda.util.tombstone imports."""
    assert inds_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(inds_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(
                    ("gda.enums", "gda.util.tombstone", "gda.model.atom.geo")
                ), f"Forbidden legacy import in {py_path}: '{node.module}'"
