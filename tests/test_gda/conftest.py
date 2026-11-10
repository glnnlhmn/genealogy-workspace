"""Path: tests/test_gda/conftest.py

Subsystem root pytest configuration and shared environment fixtures for GDA.

Operational Role:
    Provides hermetic environment variable routing, temporary filesystem
    sandboxing, and cross-subsystem test state baselines across all gda.*
    test packages.
"""

from __future__ import annotations

from pathlib import Path

import pytest

__version__ = "1.0.0+build.2"


@pytest.fixture
def mock_gda_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    """Hermetic environment routing for gda tests."""
    monkeypatch.setenv("GDA_ROOT", str(tmp_path))
    return tmp_path
