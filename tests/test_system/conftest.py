"""Path: tests/test_system/conftest.py

Pytest shared fixtures for system utility verification suites.
"""

from __future__ import annotations

from pathlib import Path

import pytest

__version__ = "1.0.1+build.r2"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    """Resolve and return canonical directory path for system test fixtures."""
    root = Path(__file__).resolve().parents[2]
    target = root / "tests" / "fixtures" / "system" / "gsi"
    if not target.is_dir():
        target = Path(__file__).resolve().parent.parent / "fixtures" / "system" / "gsi"
    return target


@pytest.fixture
def sandbox_sys_env(tmp_path: Path) -> Path:
    """Isolated environment for GSI and hook deployment tests."""
    target = tmp_path / "sys_sandbox"
    target.mkdir(parents=True, exist_ok=True)
    return target
