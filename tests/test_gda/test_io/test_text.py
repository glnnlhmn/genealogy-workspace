# Name: test_text.py
# Path: tests/test_gda/test_io/test_text.py

"""Unit and integration test suite for gda.io.text.

Operational Role:
    Verifies UTF-8 text/markdown reading, atomic persistence, Safe Backup integration,
    and typed error mappings with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification per condition.
    - Fully decorated: Standard pytest markers (@pytest.mark.unit, @pytest.mark.integration).
    - Dependencies: tmp_path hermetic sandboxing and monkeypatched error injections.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gda.io.backup import GDABackupManager
from gda.io.errors import FileReadError
from gda.io.text import GDATextIO

__version__ = "0.1.0+build.r1"

# ==============================================================================
# GROUP 1: Text Reading & Decoding
# Note: Verification of valid reading, missing file, directory, and I/O error
# ==============================================================================


@pytest.mark.integration
def test_read_loads_utf8_text_content(tmp_path: Path) -> None:
    """Verify read loads UTF-8 text file content cleanly."""
    target = tmp_path / "notes.md"
    target.write_text("# Genealogy Note\nMüller lineage record.", encoding="utf-8")

    result = GDATextIO.read(target)
    assert result == "# Genealogy Note\nMüller lineage record."


@pytest.mark.unit
def test_read_raises_file_read_error_when_missing(tmp_path: Path) -> None:
    """Verify read raises FileReadError when target file does not exist."""
    missing = tmp_path / "missing_story.txt"
    with pytest.raises(FileReadError, match="Target text file .* does not exist"):
        GDATextIO.read(missing)


@pytest.mark.unit
def test_read_raises_file_read_error_when_target_is_directory(
    tmp_path: Path,
) -> None:
    """Verify read raises FileReadError when target path points to a directory."""
    directory = tmp_path / "text_dir"
    directory.mkdir()
    with pytest.raises(FileReadError, match="Target text path .* is a directory"):
        GDATextIO.read(directory)


@pytest.mark.unit
def test_read_raises_file_read_error_on_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify read raises FileReadError when read_text encounters OSError."""
    target = tmp_path / "locked.txt"
    target.write_text("sample", encoding="utf-8")

    def mock_read_text(self: Path, *args: object, **kwargs: object) -> str:
        raise OSError("Permission denied")

    monkeypatch.setattr(Path, "read_text", mock_read_text)
    with pytest.raises(FileReadError, match="Failed to read text file"):
        GDATextIO.read(target)


# ==============================================================================
# GROUP 2: Text Writing & Safe Backup Integration
# Note: Verification of atomic writing, directory auto-creation, and backup logic
# ==============================================================================


@pytest.mark.integration
def test_write_persists_utf8_text_atomically(tmp_path: Path) -> None:
    """Verify write persists text content cleanly and auto-provisions directories."""
    target = tmp_path / "nested" / "narrative.md"
    content = "# Chapter 1\nHistorical biographical summary."

    result = GDATextIO.write(target, content)

    assert result == target.resolve()
    assert target.exists()
    assert target.read_text(encoding="utf-8") == content


@pytest.mark.integration
def test_write_creates_safe_backup_when_flag_enabled_and_file_exists(
    tmp_path: Path,
) -> None:
    """Verify write creates Safe Backup snapshot prior to overwriting existing text file."""
    target = tmp_path / "draft.txt"
    target.write_text("initial draft", encoding="utf-8")

    custom_backup_dir = tmp_path / "text_backups"
    GDATextIO.write(
        target,
        "second revision",
        create_backup=True,
        backup_dir=custom_backup_dir,
    )

    assert target.read_text(encoding="utf-8") == "second revision"
    backups = GDABackupManager.list_backups(target, backup_dir=custom_backup_dir)
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "initial draft"


@pytest.mark.integration
def test_write_skips_safe_backup_when_target_does_not_exist(
    tmp_path: Path,
) -> None:
    """Verify write does not attempt backup creation when target file is newly created."""
    target = tmp_path / "new_record.txt"

    GDATextIO.write(target, "newly authored", create_backup=True)

    assert target.exists()
    assert not (tmp_path / "backups").exists()


# ==============================================================================
# GROUP 3: Introspectable Contract
# Note: Verify help discovery contract via IntrospectableMixin
# ==============================================================================


@pytest.mark.unit
def test_text_io_inherits_and_exposes_introspectable_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify GDATextIO inherits IntrospectableMixin and executes .help()."""
    return_value = GDATextIO.help()
    captured = capsys.readouterr()
    output = return_value if isinstance(return_value, str) else captured.out

    assert "GDATextIO" in output
    assert "read" in output
    assert "write" in output
