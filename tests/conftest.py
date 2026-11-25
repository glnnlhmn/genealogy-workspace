"""Path: tests/conftest.py

Repository-wide pytest configuration, Hypothesis profiles, and root fixtures.

Operational Role:
    Provides application-agnostic workspace path anchors, static fixture file
    routing into hermetic tmp_path sandboxes, and standardized Hypothesis
    property-testing profiles across all test suites (gda, gen_desk_tools,
    system, and cli). Never imports production packages to preserve strict
    tier isolation during collection.
"""

from __future__ import annotations

import os
import shutil
from collections.abc import Callable
from pathlib import Path

import pytest
from hypothesis import HealthCheck, settings

__version__ = "1.0.0+build.2"

__all__ = [
    "copy_fixture_file",
    "pytest_configure",
    "tests_fixtures_root",
    "workspace_root",
]


# ==============================================================================
# PYTEST HOOKS & HYPOTHESIS PROFILES
# Note: Configures deterministic, Windows-safe property-testing defaults once.
# ==============================================================================


def pytest_configure(config: pytest.Config) -> None:
    """Register workspace-wide Hypothesis profiles and activate the selected one."""
    del config  # Unused hook parameter retained for pytest signature compliance.

    # Fast, deadline-free profile for native Windows / Git Bash development runs.
    settings.register_profile(
        "dev",
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow],
    )

    # Deeper, derandomized profile for thorough pre-release and CI verification.
    settings.register_profile(
        "ci",
        max_examples=200,
        deadline=None,
        derandomize=True,
        suppress_health_check=[HealthCheck.too_slow],
    )

    active_profile = os.environ.get("HYPOTHESIS_PROFILE", "dev")
    settings.load_profile(active_profile)


# ==============================================================================
# ROOT WORKSPACE & STATIC FIXTURE ANCHORS
# Note: Pure pathlib anchors shared across all test tiers.
# ==============================================================================


@pytest.fixture(scope="session")
def workspace_root() -> Path:
    """Return the resolved repository root directory path."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def tests_fixtures_root(workspace_root: Path) -> Path:
    """Return the canonical tests/fixtures root directory path."""
    return workspace_root / "tests" / "fixtures"


@pytest.fixture
def copy_fixture_file(
    tests_fixtures_root: Path,
    tmp_path: Path,
) -> Callable[[str], Path]:
    """Return a factory that copies a static fixture file into an isolated tmp_path.

    Keeping golden/failure data under tests/fixtures/<subject>/ and copying on
    demand guarantees source fixtures remain immutable while tests receive a
    normal Path through conftest.py.
    """

    def _copy(relative_fixture_path: str) -> Path:
        source = tests_fixtures_root / relative_fixture_path
        if not source.is_file():
            raise FileNotFoundError(f"Static test fixture not found: {source}")

        destination = tmp_path / source.name
        shutil.copy2(source, destination)
        return destination

    return _copy
