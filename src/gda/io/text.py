# Name: text.py
# Path: src/gda/io/text.py

"""Normalized UTF-8 text and markdown atomic persistence engine.

Operational Role:
    Provides canonical UTF-8 reading and writing for textual documents,
    narratives, markdown files, and transcripts within the digital archive.
    Integrates with GDABackupManager for pre-write Safe Backups and utilizes
    atomic_write to ensure failure-resilient filesystem commits.
"""

from __future__ import annotations

from pathlib import Path

from gda.core.introspectable import IntrospectableMixin
from gda.io.atomic import atomic_write
from gda.io.backup import GDABackupManager
from gda.io.errors import FileReadError

__version__ = "0.1.0+build.r1"


class GDATextIO(IntrospectableMixin):
    """Engine for normalized text and markdown atomic file operations."""

    DEFAULT_ENCODING: str = "utf-8"

    @classmethod
    def read(cls, file_path: Path | str, encoding: str = DEFAULT_ENCODING) -> str:
        """Read a text or markdown file from disk into a string.

        Args:
            file_path: Source text file path.
            encoding: Text character encoding (defaults to 'utf-8').

        Returns:
            Decoded text string.

        Raises:
            FileReadError: If file is missing, points to a directory, or decode fails.
        """
        target = Path(file_path).resolve()
        if not target.exists():
            raise FileReadError(f"Target text file '{target}' does not exist.")
        if target.is_dir():
            raise FileReadError(f"Target text path '{target}' is a directory.")

        try:
            return target.read_text(encoding=encoding)
        except (OSError, UnicodeDecodeError) as err:
            raise FileReadError(f"Failed to read text file '{target}': {err}") from err

    @classmethod
    def write(
        cls,
        file_path: Path | str,
        content: str,
        encoding: str = DEFAULT_ENCODING,
        create_backup: bool = False,
        backup_dir: Path | str | None = None,
    ) -> Path:
        """Write string content atomically to disk with optional Safe Backup.

        Args:
            file_path: Target destination path.
            content: Verbatim text string to persist.
            encoding: Text character encoding (defaults to 'utf-8').
            create_backup: When True, creates a Safe Backup of existing file first.
            backup_dir: Custom destination directory for snapshots.

        Returns:
            Resolved Path of the written text file.

        Raises:
            BackupError: If create_backup is True and snapshot generation fails.
            AtomicWriteError: If atomic staging or replacement fails.
        """
        target = Path(file_path).resolve()

        if create_backup and target.exists():
            GDABackupManager.create_backup(target_path=target, backup_dir=backup_dir)

        with atomic_write(target, mode="w", encoding=encoding) as stream:
            stream.write(content)

        return target
