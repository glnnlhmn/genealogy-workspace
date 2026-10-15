# Name: json.py
# Path: src/gda/io/json.py

"""Deterministic JSON serialization and atomic persistence engine.

Operational Role:
    Provides canonical JSON encoding, decoding, and filesystem persistence for
    the digital archive. Enforces deterministic serialization invariants (UTF-8,
    2-space indentation, sorted keys, unescaped Unicode, trailing newline) and
    manages optional Safe Backup generation before committing changes atomically.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gda.core.introspectable import IntrospectableMixin
from gda.io.atomic import atomic_write
from gda.io.backup import GDABackupManager
from gda.io.errors import FileReadError, SerializationError

__version__ = "0.1.0+build.r1"


class GDAJsonIO(IntrospectableMixin):
    """Engine for deterministic JSON reading and atomic writing."""

    DEFAULT_INDENT: int = 2

    @classmethod
    def read(cls, file_path: Path | str) -> Any:
        """Read and parse a UTF-8 JSON file from disk into native structures.

        Args:
            file_path: Source JSON file path.

        Returns:
            Parsed JSON data structure (dict, list, or primitive).

        Raises:
            FileReadError: If the file does not exist, is a directory, or fails to read.
            SerializationError: If the file contents are malformed JSON.
        """
        target = Path(file_path).resolve()
        if not target.exists():
            raise FileReadError(f"Target JSON file '{target}' does not exist.")
        if target.is_dir():
            raise FileReadError(f"Target JSON path '{target}' is a directory.")

        try:
            content = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as err:
            raise FileReadError(f"Failed to read JSON file '{target}': {err}") from err

        try:
            return json.loads(content)
        except json.JSONDecodeError as err:
            raise SerializationError(
                f"Failed to decode JSON from '{target}': {err}"
            ) from err

    @classmethod
    def write(
        cls,
        file_path: Path | str,
        data: Any,
        indent: int = DEFAULT_INDENT,
        sort_keys: bool = True,
        create_backup: bool = False,
        backup_dir: Path | str | None = None,
    ) -> Path:
        """Serialize data to UTF-8 JSON and commit to disk atomically.

        Enforces deterministic formatting: sorted keys, specified indent,
        unescaped Unicode characters, and a terminal newline. Optionally creates
        a Safe Backup snapshot prior to destructive overwriting.

        Args:
            file_path: Target destination path for JSON persistence.
            data: Native Python structure to serialize.
            indent: Number of spaces for structural indentation.
            sort_keys: Whether mapping keys are sorted alphabetically.
            create_backup: When True, creates a Safe Backup of existing file first.
            backup_dir: Custom destination directory for snapshots.

        Returns:
            Resolved Path of the written JSON file.

        Raises:
            SerializationError: If data cannot be serialized to JSON.
            BackupError: If create_backup is True and snapshot generation fails.
            AtomicWriteError: If atomic staging or replacement fails.
        """
        target = Path(file_path).resolve()

        try:
            serialized = (
                json.dumps(
                    data,
                    indent=indent,
                    sort_keys=sort_keys,
                    ensure_ascii=False,
                )
                + "\n"
            )
        except (TypeError, ValueError) as err:
            raise SerializationError(
                f"Failed to serialize data to JSON for '{target}': {err}"
            ) from err

        if create_backup and target.exists():
            GDABackupManager.create_backup(target_path=target, backup_dir=backup_dir)

        with atomic_write(target, mode="w", encoding="utf-8") as stream:
            stream.write(serialized)

        return target
