"""Path: tests/test_gda/test_util/conftest.py

Shared pytest fixtures for the gda.util identifier and text utility verification suite.

Operational Role:
    Provides canonical in-memory identifier collections and multilingual surname
    samples for testing gda.util.ids and gda.util.text without disk I/O.
"""

from __future__ import annotations

import pytest

__version__ = "1.0.0+build.1"


@pytest.fixture(scope="session")
def sample_smart_id_batch() -> tuple[str, ...]:
    """Provide a representative sequence of valid SmartID strings across prefixes."""
    return ("LOC-000001", "LOC-000104", "IND-000500", "LOC-000045")


@pytest.fixture(scope="session")
def sample_diacritic_text() -> str:
    """Provide a string containing common European genealogical diacritics."""
    return "Müller, François, Ångström, and Peña"
