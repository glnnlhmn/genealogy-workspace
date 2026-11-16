"""Path: tests/test_gda/test_model/test_model_contract.py

Authoritative public interface and contract verification suite for gda.model.

Operational Role:
    Freezes and validates the 5-pillar subpackage topology of gda.model
    (atom, base, entity, source, xref), strict alphabetical __all__ ordering,
    and semantic version metadata.
"""

from __future__ import annotations

import pkgutil

import pytest

import gda.model as model_pkg

__version__ = "1.0.0+build.1"

AUTHORITATIVE_MODEL_PILLARS = [
    "atom",
    "base",
    "entity",
    "source",
    "xref",
]


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_model_package_five_pillar_topology_and_exports() -> None:
    """Verify gda.model exposes the exact 5 architectural subpackages in sorted order."""
    discovered = sorted(m.name for m in pkgutil.iter_modules(model_pkg.__path__) if m.ispkg)
    assert discovered == AUTHORITATIVE_MODEL_PILLARS
    assert model_pkg.__all__ == AUTHORITATIVE_MODEL_PILLARS
    assert model_pkg.__all__ == sorted(model_pkg.__all__)
    assert "+build." in model_pkg.__version__

    for pillar in AUTHORITATIVE_MODEL_PILLARS:
        subpkg = getattr(model_pkg, pillar, None)
        assert subpkg is not None
        assert hasattr(subpkg, "__all__")
        assert subpkg.__all__ == sorted(subpkg.__all__)
