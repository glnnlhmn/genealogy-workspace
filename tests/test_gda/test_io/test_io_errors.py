# Name: test_io_errors.py
# Path: tests/test_gda/test_io/test_io_errors.py

"""Unit test suite for the gda.io exception hierarchy.

Operational Role:
    Verifies class inheritance contracts, exception instantiation, message
    propagation, and clean integration with gda.core.errors.GenealogyDeskError.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification per exception type.
    - Fully decorated: Decorated with @pytest.mark.unit.
    - Dependencies: Pure in-memory unit tests; zero physical disk I/O.
"""

from __future__ import annotations

import pytest

from gda.core.errors import GenealogyDeskError
from gda.io.errors import (
    AtomicWriteError,
    BackupError,
    DirectoryCreationError,
    FileLockError,
    FileReadError,
    GDAIOError,
    SerializationError,
)

__version__ = "0.1.0+build.r1"

# ==============================================================================
# GROUP 1: Exception Hierarchy & Inheritance Contracts
# Note: Verify inheritance boundaries from GenealogyDeskError and GDAIOError
# ==============================================================================


@pytest.mark.unit
def test_gda_io_error_inherits_from_genealogy_desk_error() -> None:
    """Verify GDAIOError inherits from the root framework GenealogyDeskError."""
    err = GDAIOError("I/O base error")
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "I/O base error"


@pytest.mark.unit
def test_atomic_write_error_inherits_from_gda_io_error() -> None:
    """Verify AtomicWriteError subclasses GDAIOError and preserves message."""
    err = AtomicWriteError("Failed staging atomic file")
    assert isinstance(err, GDAIOError)
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "Failed staging atomic file"


@pytest.mark.unit
def test_backup_error_inherits_from_gda_io_error() -> None:
    """Verify BackupError subclasses GDAIOError and preserves message."""
    err = BackupError("Failed backup snapshot")
    assert isinstance(err, GDAIOError)
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "Failed backup snapshot"


@pytest.mark.unit
def test_file_read_error_inherits_from_gda_io_error() -> None:
    """Verify FileReadError subclasses GDAIOError and preserves message."""
    err = FileReadError("Failed reading file")
    assert isinstance(err, GDAIOError)
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "Failed reading file"


@pytest.mark.unit
def test_serialization_error_inherits_from_gda_io_error() -> None:
    """Verify SerializationError subclasses GDAIOError and preserves message."""
    err = SerializationError("Syntax serialization failure")
    assert isinstance(err, GDAIOError)
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "Syntax serialization failure"


@pytest.mark.unit
def test_file_lock_error_inherits_from_gda_io_error() -> None:
    """Verify FileLockError subclasses GDAIOError and preserves message."""
    err = FileLockError("Lock acquisition timeout")
    assert isinstance(err, GDAIOError)
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "Lock acquisition timeout"


@pytest.mark.unit
def test_directory_creation_error_inherits_from_gda_io_error() -> None:
    """Verify DirectoryCreationError subclasses GDAIOError and preserves message."""
    err = DirectoryCreationError("Permission denied creating parent")
    assert isinstance(err, GDAIOError)
    assert isinstance(err, GenealogyDeskError)
    assert str(err) == "Permission denied creating parent"
