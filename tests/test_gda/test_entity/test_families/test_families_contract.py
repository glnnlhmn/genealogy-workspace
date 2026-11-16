"""Path: tests/test_gda/test_entity/test_families/test_families_contract.py

Authoritative public interface and contract verification suite for gda.entity.families.

Operational Role:
    Verifies the end-to-end family creation, partner/child lookup, validation,
    and lifecycle gateway, enforces the 4-submodule topology and sorted
    18-symbol __all__ contract of gda.entity.families, verifies centralized
    ENTITY_URN_REGEXES['FAM'] binding, and ensures zero legacy imports.
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
import gda.entity.families as fams_pkg
import gda.entity.families.collection as collection_mod
import gda.entity.families.errors as errors_mod
import gda.entity.families.util as util_mod
import gda.entity.families.validation as validation_mod
from gda.core.enums.vital import PedigreeType
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.core.types import ENTITY_URN_REGEXES
from gda.entity.families import (
    Families,
    FamilyError,
    FamilyNotFoundError,
    FamilyValidationError,
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_family,
    undelete_family,
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_family,
    valid_urn,
)
from gda.model.atom.id import FamilyID

__version__ = "1.0.0+build.1"

_EXPECTED_SUBMODULES = {
    "collection",
    "errors",
    "util",
    "validation",
}

AUTHORITATIVE_FAMILIES_EXPORTS = [
    "Families",
    "FamilyError",
    "FamilyNotFoundError",
    "FamilyValidationError",
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_family",
    "undelete_family",
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_references",
    "valid_collection_tombstones",
    "valid_family",
    "valid_urn",
]


@pytest.mark.smoke
@pytest.mark.unit
def test_families_subsystem_gateway_smoke_pipeline(
    mock_individuals_collection: MagicMock,
) -> None:
    """Verify end-to-end family creation, partner/child lookup, validation, retirement, and restoration."""
    collection = Families()

    fam = collection.create(
        partner_ids=["IND-000001", "IND-000002"],
        children=[("IND-000003", PedigreeType.BIRTH)],
        individuals_collection=mock_individuals_collection,
    )

    assert isinstance(fam.id, FamilyID)
    assert fam.id in collection
    assert fam.canonical_urn in collection
    assert collection.find_by_partner("IND-000001") == [fam]
    assert collection.find_by_child("IND-000003") == [fam]
    assert valid_family(fam) is True
    assert (
        valid_collection_all(
            collection,
            individuals_collection=mock_individuals_collection,
        )
        is True
    )

    retired = collection.soft_delete(fam.id, reason="Duplicate family unit")
    assert retired.tombstone.is_deprecated is True
    assert fam.id not in collection

    restored = collection.undelete(
        fam.id,
        individuals_collection=mock_individuals_collection,
    )
    assert restored.tombstone.is_deprecated is False
    assert fam.id in collection


@pytest.mark.unit
@pytest.mark.integrity
def test_families_pkg_topology_and_dunder_all_contract() -> None:
    """Verify submodule topology, sorted 18-symbol __all__, and centralized URN regex binding."""
    discovered = {m.name for m in pkgutil.iter_modules(fams_pkg.__path__)}
    assert discovered == _EXPECTED_SUBMODULES

    assert fams_pkg.__all__ == AUTHORITATIVE_FAMILIES_EXPORTS
    assert fams_pkg.__all__ == sorted(fams_pkg.__all__)
    for attr in AUTHORITATIVE_FAMILIES_EXPORTS:
        assert hasattr(fams_pkg, attr), f"Export '{attr}' missing from gda.entity.families"

    assert collection_mod.__all__ == ["Families"]
    assert errors_mod.__all__ == [
        "FamilyError",
        "FamilyNotFoundError",
        "FamilyValidationError",
    ]
    assert util_mod.__all__ == sorted(util_mod.__all__)
    assert validation_mod.__all__ == sorted(validation_mod.__all__)
    assert validation_mod._FAMILY_URN_PATTERN is ENTITY_URN_REGEXES["FAM"]

    assert entity_root_pkg.__all__ == sorted(entity_root_pkg.__all__)
    assert "Families" in entity_root_pkg.__all__
    assert "families" in entity_root_pkg.__all__


@pytest.mark.unit
@pytest.mark.integrity
def test_families_pkg_class_and_exception_types() -> None:
    """Verify exported classes and exceptions conform to expected inheritance."""
    assert isinstance(Families, type)
    assert issubclass(Families, IntrospectableMixin)

    for exc_cls in (FamilyError, FamilyNotFoundError, FamilyValidationError):
        assert issubclass(exc_cls, GenealogyDeskError)
        assert issubclass(exc_cls, Exception)


@pytest.mark.unit
@pytest.mark.integrity
def test_families_pkg_callable_function_contracts() -> None:
    """Verify all functional facade exports in gda.entity.families are callable."""
    callables = (
        can_tombstone,
        can_undelete,
        export_file,
        import_file,
        load_from_db,
        save_to_db,
        tombstone_family,
        undelete_family,
        valid_collection_all,
        valid_collection_indexes,
        valid_collection_references,
        valid_collection_tombstones,
        valid_family,
        valid_urn,
    )
    for func in callables:
        assert callable(func)
        assert isinstance(func, types.FunctionType)


@pytest.mark.unit
@pytest.mark.integrity
def test_families_pkg_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy gda.enums or gda.util.tombstone imports."""
    assert fams_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(fams_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(
                    ("gda.enums", "gda.util.tombstone", "gda.model.atom.geo")
                ), f"Forbidden legacy import in {py_path}: '{node.module}'"
