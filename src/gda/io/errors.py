# Name: errors.py
# Path: src/gda/io/errors.py

"""Canonical I/O error hierarchy and specialized persistence exceptions.

Operational Role:
    Defines the exception domain for physical disk mutations, atomic staging,
    file locking contention, safe backups, reading, and serialization failures within gda.io.
    Integrates directly with the root GenealogyDeskError infrastructure from gda.core.errors.
"""

from __future__ import annotations

from gda.core.errors import GenealogyDeskError

__version__ = "0.1.0+build.r5"


class GDAIOError(GenealogyDeskError):
    """Base exception for all physical storage and filesystem persistence failures."""


class AtomicWriteError(GDAIOError):
    """Raised when an atomic staging, writing, syncing, or file replacement operation fails."""


class BackupError(GDAIOError):
    """Raised when an automated pre-write Safe Backup creation or restoration fails."""


class FileReadError(GDAIOError):
    """Raised when reading or decoding a target file from disk fails."""


class SerializationError(GDAIOError):
    """Raised when serializing data to or deserializing data from structured syntax fails."""


class FileLockError(GDAIOError):
    """Raised when temporary file locks or cross-process sharing violations cannot resolve."""


class DirectoryCreationError(GDAIOError):
    """Raised when an automated parent directory creation path fails."""
