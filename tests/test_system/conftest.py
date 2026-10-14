# Name: conftest.py
# Path: tests/test_system/conftest.py
# Version: 1.0.1+build.r1

"""Pytest shared fixtures for system utility verification suites."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Resolve and return canonical directory path for system test fixtures."""
    root = Path(__file__).resolve().parents[2]
    target = root / "tests" / "fixtures" / "system" / "gsi"
    if not target.is_dir():
        # Fallback for alternative workspace layouts
        target = Path(__file__).resolve().parent.parent / "fixtures" / "system" / "gsi"
    return target


@pytest.fixture
def sandbox_sys_env(tmp_path: Path) -> Path:
    """Isolated environment for GSI and hook deployment tests."""
    target = tmp_path / "sys_sandbox"
    target.mkdir(parents=True, exist_ok=True)
    return target
