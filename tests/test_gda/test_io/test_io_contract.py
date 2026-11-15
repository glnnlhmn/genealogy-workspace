"""Path: tests/test_gda/test_io/test_io_contract.py

Authoritative public interface and contract verification suite for gda.io.

Operational Role:
    Freezes and validates the public API surface of the gda.io package.
    Verifies symbol parity, strict alphabetical __all__ ordering, module-level
    __all__ declarations across submodules, exception hierarchy inheritance,
    IntrospectableMixin composition, and callable method signatures.
"""

from __future__ import annotations

import inspect

import pytest

import gda.io
import gda.io.atomic as io_atomic
import gda.io.backup as io_backup
import gda.io.errors as io_errors
import gda.io.json as io_json
import gda.io.text as io_text
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.io import (
    AtomicWriteError,
    AtomicWriter,
    BackupError,
    DirectoryCreationError,
    FileLockError,
    FileReadError,
    GDABackupManager,
    GDAIOError,
    GDAJsonIO,
    GDATextIO,
    SerializationError,
)

__version__ = "1.0.0+build.2"

AUTHORITATIVE_IO_EXPORTS: frozenset[str] = frozenset(
    {
        # atomic.py (5)
        "AtomicWriter",
        "atomic_write",
        "atomic_write_bytes",
        "atomic_write_stream",
        "atomic_write_text",
        # backup.py (1)
        "GDABackupManager",
        # errors.py (7)
        "AtomicWriteError",
        "BackupError",
        "DirectoryCreationError",
        "FileLockError",
        "FileReadError",
        "GDAIOError",
        "SerializationError",
        # json.py (1)
        "GDAJsonIO",
        # text.py (1)
        "GDATextIO",
    }
)


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_io_exports_exact_authoritative_symbols() -> None:
    """Verify gda.io exports the exact 15 authoritative symbols with zero drift."""
    assert frozenset(gda.io.__all__) == AUTHORITATIVE_IO_EXPORTS
    assert len(gda.io.__all__) == 15
    for symbol in AUTHORITATIVE_IO_EXPORTS:
        assert hasattr(gda.io, symbol), f"Missing symbol {symbol} in gda.io"
        assert getattr(gda.io, symbol) is not None


@pytest.mark.integrity
@pytest.mark.unit
def test_io_all_and_submodule_alls_are_sorted_alphabetically() -> None:
    """Verify gda.io and all gda.io submodules declare alphabetically sorted __all__ lists."""
    assert gda.io.__all__ == sorted(gda.io.__all__)
    for mod in (io_atomic, io_backup, io_errors, io_json, io_text):
        assert hasattr(mod, "__all__"), f"{mod.__name__} missing __all__"
        assert mod.__all__ == sorted(mod.__all__)
        assert hasattr(mod, "__version__")
        assert "+build." in mod.__version__


@pytest.mark.integrity
@pytest.mark.unit
def test_io_exception_hierarchy_contract() -> None:
    """Verify strict inheritance hierarchy of all gda.io exception classes."""
    assert issubclass(GDAIOError, GenealogyDeskError)
    assert issubclass(AtomicWriteError, GDAIOError)
    assert issubclass(FileLockError, AtomicWriteError)
    assert issubclass(BackupError, GDAIOError)
    assert issubclass(FileReadError, GDAIOError)
    assert issubclass(SerializationError, GDAIOError)
    assert issubclass(DirectoryCreationError, GDAIOError)


@pytest.mark.integrity
@pytest.mark.unit
def test_io_service_classes_inherit_introspectable_and_preserve_signatures() -> None:
    """Verify I/O manager classes inherit IntrospectableMixin and preserve method signatures."""
    for cls in (AtomicWriter, GDABackupManager, GDAJsonIO, GDATextIO):
        assert issubclass(cls, IntrospectableMixin)

    assert {"directory"} <= set(inspect.signature(AtomicWriter.ensure_directory).parameters)
    assert {"source", "destination", "max_retries", "backoff_factor"} <= set(
        inspect.signature(AtomicWriter.replace_with_retry).parameters
    )
    assert {"target_path", "backup_dir"} <= set(
        inspect.signature(GDABackupManager.create_backup).parameters
    )
    assert {"backup_path", "target_path"} <= set(
        inspect.signature(GDABackupManager.restore_backup).parameters
    )
    assert {"file_path", "data", "indent", "sort_keys", "create_backup", "backup_dir"} <= set(
        inspect.signature(GDAJsonIO.write).parameters
    )
    assert {"file_path", "content", "encoding", "create_backup", "backup_dir"} <= set(
        inspect.signature(GDATextIO.write).parameters
    )
