"""Path: src/gda/io/backup.py

Safe Backup Protocol and snapshot lifecycle manager.

Operational Role:
    Provides pre-mutation snapshot generation, chronological history discovery,
    and atomic snapshot restoration for digital archive files. Enforces zero
    hardcoded folder assumptions by deriving default backup locations relative
    to the target file's parent directory, and guarantees collision-free naming
    via high-resolution timestamps and monotonic tiebreaker counters. Employs
    streamed chunked copy buffers to eliminate in-memory file size limits.
"""

from __future__ import annotations

import re
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path

from gda.core.introspectable import IntrospectableMixin
from gda.io.atomic import AtomicWriter, atomic_write_stream
from gda.io.errors import BackupError

__version__ = "1.0.0+build.2"

__all__ = [
    "GDABackupManager",
]


class GDABackupManager(IntrospectableMixin):
    """Manager for automated pre-write Safe Backups and atomic restorations."""

    BACKUP_EXT: str = ".bk"
    TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"
    CHUNK_SIZE: int = 64 * 1024

    @classmethod
    def _stream_file_chunks(cls, file_path: Path) -> Generator[bytes]:
        """Yield binary chunks of a file without exhausting system memory.

        Args:
            file_path: Source file path to read in chunks.

        Yields:
            Byte chunks of length CHUNK_SIZE.
        """
        with open(file_path, "rb") as stream:
            while chunk := stream.read(cls.CHUNK_SIZE):
                yield chunk

    @classmethod
    def resolve_backup_dir(
        cls, target_path: Path | str, backup_dir: Path | str | None = None
    ) -> Path:
        """Resolve and ensure the target backup directory.

        Args:
            target_path: File path targeted for backup operations.
            backup_dir: Optional explicit destination directory for snapshots.
                If omitted, defaults to a sibling 'backups/' directory relative
                to target_path.parent.

        Returns:
            Resolved Path of the ensured backup directory.
        """
        target = Path(target_path).resolve()
        destination = (
            Path(backup_dir).resolve() if backup_dir is not None else target.parent / "backups"
        )
        return AtomicWriter.ensure_directory(destination)

    @classmethod
    def create_backup(cls, target_path: Path | str, backup_dir: Path | str | None = None) -> Path:
        """Create an atomic timestamped snapshot of a target file.

        Generates snapshot filenames formatted as:
            [filename].[YYYYMMDD_HHMMSS].bk
        or with a collision counter if multiple snapshots occur in the same second:
            [filename].[YYYYMMDD_HHMMSS]_[counter].bk

        Args:
            target_path: File path to snapshot. Must exist on disk.
            backup_dir: Optional custom destination folder for the backup.

        Returns:
            Path of the generated backup snapshot.

        Raises:
            BackupError: If the target does not exist, is a directory, or copying fails.
        """
        target = Path(target_path).resolve()
        if not target.exists():
            raise BackupError(f"Cannot create backup: target file '{target}' does not exist.")
        if target.is_dir():
            raise BackupError(f"Cannot create backup: target path '{target}' is a directory.")

        destination_dir = cls.resolve_backup_dir(target, backup_dir)
        timestamp = datetime.now(UTC).strftime(cls.TIMESTAMP_FORMAT)
        base_name = f"{target.name}.{timestamp}"

        candidate_name = f"{base_name}{cls.BACKUP_EXT}"
        candidate_path = destination_dir / candidate_name

        counter = 1
        while candidate_path.exists():
            candidate_name = f"{base_name}_{counter}{cls.BACKUP_EXT}"
            candidate_path = destination_dir / candidate_name
            counter += 1

        try:
            atomic_write_stream(candidate_path, cls._stream_file_chunks(target))
        except Exception as err:
            raise BackupError(
                f"Failed to create backup of '{target}' at '{candidate_path}': {err}"
            ) from err

        return candidate_path

    @classmethod
    def list_backups(
        cls, target_path: Path | str, backup_dir: Path | str | None = None
    ) -> list[Path]:
        """Discover matching snapshots for a target file sorted chronologically.

        Sorts snapshots newest first using a natural sort key on the timestamp
        and the subsecond collision counter.

        Args:
            target_path: File path whose backups are to be discovered.
            backup_dir: Optional custom directory to search. Defaults to 'backups/'
                sibling directory.

        Returns:
            List of backup Path objects sorted newest first.
        """
        target = Path(target_path).resolve()
        destination = (
            Path(backup_dir).resolve() if backup_dir is not None else target.parent / "backups"
        )
        if not destination.exists() or not destination.is_dir():
            return []

        pattern = re.compile(
            rf"^{re.escape(target.name)}\.(\d{{8}}_\d{{6}})(?:_(\d+))?{re.escape(cls.BACKUP_EXT)}$"
        )

        matches: list[tuple[tuple[str, int], Path]] = []
        for child in destination.iterdir():
            if child.is_file():
                match = pattern.match(child.name)
                if match:
                    timestamp_str = match.group(1)
                    counter = int(match.group(2)) if match.group(2) else 0
                    matches.append(((timestamp_str, counter), child))

        matches.sort(key=lambda item: item[0], reverse=True)
        return [item[1] for item in matches]

    @classmethod
    def restore_backup(cls, backup_path: Path | str, target_path: Path | str) -> Path:
        """Atomically restore a snapshot file to the target destination.

        Args:
            backup_path: Source snapshot file path.
            target_path: Canonical destination path to overwrite atomically.

        Returns:
            Resolved Path of the restored destination file.

        Raises:
            BackupError: If backup_path does not exist or atomic restoration fails.
        """
        backup = Path(backup_path).resolve()
        target = Path(target_path).resolve()

        if not backup.exists():
            raise BackupError(f"Cannot restore backup: source '{backup}' does not exist.")
        if backup.is_dir():
            raise BackupError(f"Cannot restore backup: source '{backup}' is a directory.")

        try:
            atomic_write_stream(target, cls._stream_file_chunks(backup))
        except Exception as err:
            raise BackupError(
                f"Failed to restore backup from '{backup}' to '{target}': {err}"
            ) from err

        return target
