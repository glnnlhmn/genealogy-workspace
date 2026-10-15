# Name: test_backup.py
# Path: tests/test_gda/test_io/test_backup.py

"""Unit and integration test suite for gda.io.backup.

Operational Role:
    Verifies Safe Backup snapshot generation, default and explicit destination
    resolution, sub-second collision resolution, chronological discovery,
    atomic restoration, and error contracts with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification of snapshot creation, discovery, and restoration.
    - Fully decorated: Standard pytest markers (@pytest.mark.unit, @pytest.mark.integration).
    - Dependencies: tmp_path hermetic sandboxing and monkeypatched error injections.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gda.io.backup import GDABackupManager
from gda.io.errors import BackupError

__version__ = "0.1.0+build.r1"

# ==============================================================================
# GROUP 1: Directory Resolution & Default Sibling Provisioning
# Note: Verification of zero hardcoded assumptions and auto-provisioning
# ==============================================================================


@pytest.mark.unit
def test_resolve_backup_dir_defaults_to_sibling_backups_folder(
    tmp_path: Path,
) -> None:
    """Verify default backup directory resolves to sibling backups/ folder."""
    target = tmp_path / "records" / "entities.json"
    resolved = GDABackupManager.resolve_backup_dir(target)
    expected = (tmp_path / "records" / "backups").resolve()

    assert resolved == expected
    assert resolved.is_dir()


@pytest.mark.unit
def test_resolve_backup_dir_uses_explicit_directory_when_provided(
    tmp_path: Path,
) -> None:
    """Verify custom backup directory argument is respected and ensured."""
    target = tmp_path / "records" / "entities.json"
    custom_dir = tmp_path / "custom_archive" / "store"
    resolved = GDABackupManager.resolve_backup_dir(target, backup_dir=custom_dir)

    assert resolved == custom_dir.resolve()
    assert resolved.is_dir()


# ==============================================================================
# GROUP 2: Snapshot Creation & Naming Invariants
# Note: Verification of creation, collision handling, and error conditions
# ==============================================================================


@pytest.mark.integration
def test_create_backup_generates_snapshot_in_default_location(
    tmp_path: Path,
) -> None:
    """Verify create_backup generates snapshot file with expected name pattern."""
    target = tmp_path / "registry.json"
    target.write_text('{"records": 42}', encoding="utf-8")

    backup_path = GDABackupManager.create_backup(target)

    assert backup_path.exists()
    assert backup_path.parent == tmp_path / "backups"
    assert backup_path.name.startswith("registry.json.")
    assert backup_path.name.endswith(".bk")
    assert backup_path.read_text(encoding="utf-8") == '{"records": 42}'


@pytest.mark.integration
def test_create_backup_resolves_subsecond_collisions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify subsecond collisions append sequential monotonic numeric counters."""
    target = tmp_path / "data.txt"
    target.write_text("v1", encoding="utf-8")

    fixed_time = "20261012_120000"
    mock_dt = MagicMock()
    mock_dt.strftime.return_value = fixed_time
    monkeypatch.setattr(
        "gda.io.backup.datetime", MagicMock(now=MagicMock(return_value=mock_dt))
    )

    b1 = GDABackupManager.create_backup(target)
    target.write_text("v2", encoding="utf-8")
    b2 = GDABackupManager.create_backup(target)
    target.write_text("v3", encoding="utf-8")
    b3 = GDABackupManager.create_backup(target)

    assert b1.name == f"data.txt.{fixed_time}.bk"
    assert b2.name == f"data.txt.{fixed_time}_1.bk"
    assert b3.name == f"data.txt.{fixed_time}_2.bk"
    assert b1.read_text(encoding="utf-8") == "v1"
    assert b2.read_text(encoding="utf-8") == "v2"
    assert b3.read_text(encoding="utf-8") == "v3"


@pytest.mark.unit
def test_create_backup_raises_when_target_missing(tmp_path: Path) -> None:
    """Verify BackupError is raised if target file does not exist."""
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(BackupError, match="target file .* does not exist"):
        GDABackupManager.create_backup(missing)


@pytest.mark.unit
def test_create_backup_raises_when_target_is_directory(tmp_path: Path) -> None:
    """Verify BackupError is raised if target path is a directory."""
    directory = tmp_path / "a_directory"
    directory.mkdir()
    with pytest.raises(BackupError, match="target path .* is a directory"):
        GDABackupManager.create_backup(directory)


@pytest.mark.unit
def test_create_backup_raises_on_read_or_write_failure(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify BackupError is raised if atomic write fails during snapshot creation."""
    target = tmp_path / "corrupt.txt"
    target.write_text("payload", encoding="utf-8")

    def mock_write_bytes(*args: object, **kwargs: object) -> Path:
        raise OSError("Disk write failed")

    monkeypatch.setattr("gda.io.backup.atomic_write_bytes", mock_write_bytes)

    with pytest.raises(BackupError, match="Failed to create backup"):
        GDABackupManager.create_backup(target)


# ==============================================================================
# GROUP 3: Chronological Backup Discovery (list_backups)
# Note: Verification of sorting, regex filtering, and missing directory handling
# ==============================================================================


@pytest.mark.unit
def test_list_backups_returns_empty_when_directory_missing(
    tmp_path: Path,
) -> None:
    """Verify list_backups returns empty list when no backup directory exists."""
    target = tmp_path / "sample.json"
    assert GDABackupManager.list_backups(target) == []


@pytest.mark.integration
def test_list_backups_filters_and_sorts_chronologically(
    tmp_path: Path,
) -> None:
    """Verify list_backups ignores non-matching files and sorts newest first."""
    target = tmp_path / "notes.txt"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()

    b1 = backup_dir / "notes.txt.20260101_100000.bk"
    b2 = backup_dir / "notes.txt.20260102_120000.bk"
    b3 = backup_dir / "notes.txt.20260102_120000_1.bk"
    other_file = backup_dir / "notes.txt.bak"
    unrelated_bk = backup_dir / "other.txt.20260101_100000.bk"

    for p in (b1, b2, b3, other_file, unrelated_bk):
        p.write_text("dummy", encoding="utf-8")

    discovered = GDABackupManager.list_backups(target, backup_dir=backup_dir)

    assert discovered == [b3, b2, b1]


# ==============================================================================
# GROUP 4: Atomic Restoration (restore_backup)
# Note: Verification of snapshot restoration, overwrite, and error branches
# ==============================================================================


@pytest.mark.integration
def test_restore_backup_replaces_target_atomically(tmp_path: Path) -> None:
    """Verify restore_backup overwrites target with snapshot payload."""
    target = tmp_path / "live_data.json"
    target.write_text('{"state": "mutated"}', encoding="utf-8")

    backup_file = tmp_path / "snapshot.bk"
    backup_file.write_text('{"state": "golden"}', encoding="utf-8")

    result = GDABackupManager.restore_backup(backup_file, target)

    assert result == target.resolve()
    assert target.read_text(encoding="utf-8") == '{"state": "golden"}'


@pytest.mark.unit
def test_restore_backup_raises_when_source_missing(tmp_path: Path) -> None:
    """Verify restore_backup raises BackupError if snapshot file does not exist."""
    missing_bk = tmp_path / "missing.bk"
    target = tmp_path / "live.txt"
    with pytest.raises(BackupError, match="source .* does not exist"):
        GDABackupManager.restore_backup(missing_bk, target)


@pytest.mark.unit
def test_restore_backup_raises_when_source_is_directory(
    tmp_path: Path,
) -> None:
    """Verify restore_backup raises BackupError if snapshot path is a directory."""
    directory_bk = tmp_path / "dir.bk"
    directory_bk.mkdir()
    target = tmp_path / "live.txt"
    with pytest.raises(BackupError, match="source .* is a directory"):
        GDABackupManager.restore_backup(directory_bk, target)


@pytest.mark.unit
def test_restore_backup_raises_on_atomic_write_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify restore_backup raises BackupError when atomic_write_bytes fails."""
    backup_file = tmp_path / "snap.bk"
    backup_file.write_text("content", encoding="utf-8")
    target = tmp_path / "live.txt"

    def mock_write_bytes(*args: object, **kwargs: object) -> Path:
        raise OSError("Permission denied")

    monkeypatch.setattr("gda.io.backup.atomic_write_bytes", mock_write_bytes)

    with pytest.raises(BackupError, match="Failed to restore backup"):
        GDABackupManager.restore_backup(backup_file, target)


# ==============================================================================
# GROUP 5: Introspectable Contract
# Note: Verify help discovery contract via IntrospectableMixin
# ==============================================================================


@pytest.mark.unit
def test_backup_manager_inherits_and_exposes_introspectable_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify GDABackupManager inherits IntrospectableMixin and executes .help()."""
    return_value = GDABackupManager.help()
    captured = capsys.readouterr()
    output = return_value if isinstance(return_value, str) else captured.out

    assert "GDABackupManager" in output
    assert "create_backup" in output
    assert "restore_backup" in output
