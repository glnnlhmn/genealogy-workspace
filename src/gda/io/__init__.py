# Name: __init__.py
# Path: src/gda/io/__init__.py

"""Genealogy Digital Archive I/O and persistence infrastructure.

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

__version__ = "0.1.0+build.r1"

__all__ = [
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
]
