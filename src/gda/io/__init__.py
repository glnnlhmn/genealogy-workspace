"""Path: src/gda/io/__init__.py

Genealogy Digital Archive I/O and persistence infrastructure.

Operational Role:
    Defines the public application programming interface for physical disk
    mutations, atomic temporary staging, automated Safe Backup snapshots,
    and deterministic serialization across the archive.
"""

from __future__ import annotations

from gda.io.atomic import (
    AtomicWriter,
    atomic_write,
    atomic_write_bytes,
    atomic_write_stream,
    atomic_write_text,
)
from gda.io.backup import GDABackupManager
from gda.io.errors import (
    AtomicWriteError,
    BackupError,
    DirectoryCreationError,
    FileLockError,
    FileReadError,
    GDAIOError,
    SerializationError,
)
from gda.io.json import GDAJsonIO
from gda.io.text import GDATextIO

__version__ = "1.0.0+build.2"

__all__ = [
    "AtomicWriteError",  # errors.py
    "AtomicWriter",  # atomic.py
    "BackupError",  # errors.py
    "DirectoryCreationError",  # errors.py
    "FileLockError",  # errors.py
    "FileReadError",  # errors.py
    "GDABackupManager",  # backup.py
    "GDAIOError",  # errors.py
    "GDAJsonIO",  # json.py
    "GDATextIO",  # text.py
    "SerializationError",  # errors.py
    "atomic_write",  # atomic.py
    "atomic_write_bytes",  # atomic.py
    "atomic_write_stream",  # atomic.py
    "atomic_write_text",  # atomic.py
]
