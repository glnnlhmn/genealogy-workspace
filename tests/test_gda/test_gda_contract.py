"""Path: tests/test_gda/test_gda_contract.py

Authoritative top-level package contract test suite for src/gda/__init__.py.

Operational Role:
    1:1 verification suite for src/gda/__init__.py. Validates that the root
    gda package exposes all 6 completed architectural subpackages (core, db,
    entity, io, model, util) in sorted __all__ order with valid semantic
    versioning and sorted subpackage __all__ manifests.
"""

from __future__ import annotations

import pytest

import gda

__version__ = "1.0.0+build.1"

AUTHORITATIVE_GDA_SUBPACKAGES = [
    "core",
    "db",
    "entity",
    "io",
    "model",
    "util",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_gda_root_package_exports_and_subpackage_contracts() -> None:
    """Verify gda.__all__ is sorted and all 6 architectural subpackages resolve cleanly."""
    assert gda.__all__ == AUTHORITATIVE_GDA_SUBPACKAGES
    assert gda.__all__ == sorted(gda.__all__)
    assert hasattr(gda, "__version__")
    assert "+build." in gda.__version__

    for subpkg_name in AUTHORITATIVE_GDA_SUBPACKAGES:
        subpkg = getattr(gda, subpkg_name, None)
        assert subpkg is not None, f"Missing subpackage on gda: {subpkg_name}"
        assert hasattr(subpkg, "__all__"), f"gda.{subpkg_name} missing __all__"
        assert subpkg.__all__ == sorted(subpkg.__all__), (
            f"gda.{subpkg_name}.__all__ is not sorted alphabetically"
        )
        assert hasattr(subpkg, "__version__")
