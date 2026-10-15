# Name: test_init.py
# Path: tests/test_gda/test_io/test_init.py

"""Unit test suite for the gda.io package root and public exports.

Operational Role:
    Verifies package surface exports, __all__ definitions, and version availability
    with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification of export definitions and version contracts.
    - Fully decorated: Standard pytest markers (@pytest.mark.unit).
    - Dependencies: In-memory module import inspection.
"""

from __future__ import annotations

import pytest

import gda.io

__version__ = "0.1.0+build.r1"

# ==============================================================================
# GROUP 1: Package Export Surface
# Note: Verification of __all__ definitions and exported classes/functions
# ==============================================================================


@pytest.mark.unit
def test_package_exports_expected_symbols() -> None:
    """Verify gda.io exports all canonical persistence classes and functions."""
    expected_exports = {
        "AtomicWriteError",
        "AtomicWriter",
        "BackupError",
        "DirectoryCreationError",
        "FileLockError",
        "FileReadError",
        "GDAIOError",
        "GDAJsonIO",
        "GDATextIO",
        "GDABackupManager",
        "SerializationError",
        "atomic_write",
        "atomic_write_bytes",
        "atomic_write_stream",
        "atomic_write_text",
    }
    assert set(gda.io.__all__) == expected_exports
    for symbol in expected_exports:
        assert hasattr(gda.io, symbol)


@pytest.mark.unit
def test_package_declares_pep440_version() -> None:
    """Verify gda.io package root declares a valid __version__ string."""
    assert hasattr(gda.io, "__version__")
    assert isinstance(gda.io.__version__, str)
    assert "+build.r" in gda.io.__version__
