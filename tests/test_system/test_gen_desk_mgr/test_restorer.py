"""Path: tests/test_system/test_gen_desk_mgr/test_restorer.py

Unit and integration test suite for GenDesk Backup Manager restoration engine.

Operational Role:
    Verifies text manifest parsing, code domain validation, Safe Backup snapshot
    discovery, atomic file restoration, Git fallback, dry-run simulation,
    unlogged branches, and batch error aggregation achieving 100% coverage.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from system.gen_desk_mgr.gd_backup_tools.config import load_config
from system.gen_desk_mgr.gd_backup_tools.restorer import (
    atomic_copy,
    find_latest_archive_backup,
    parse_restore_list,
    restore_batch_from_list,
    restore_file_entry,
    restore_from_git,
)

__version__ = "1.0.0+build.2"

# ==============================================================================
# GROUP 1: Manifest Parsing
# Note: Verification of parse_restore_list handling comments, blanks, and slashes
# ==============================================================================


@pytest.mark.unit
def test_parse_restore_list_nonexistent() -> None:
    """Verify returns empty list when manifest file does not exist."""
    assert parse_restore_list(Path("/nonexistent/manifest.txt")) == []


@pytest.mark.unit
def test_parse_restore_list_filters_blanks_and_comments(tmp_path: Path) -> None:
    """Verify empty lines and comments are ignored while normalising slashes."""
    manifest = tmp_path / "restore_list.txt"
    manifest.write_text(
        """
# Comment line
src/gda/core/config.py
   # Indented comment

tests\\test_gda\\test_config.py
schemas/core.json
""",
        encoding="utf-8",
    )
    targets = parse_restore_list(manifest)
    assert targets == [
        "src/gda/core/config.py",
        "tests/test_gda/test_config.py",
        "schemas/core.json",
    ]


# ==============================================================================
# GROUP 2: Archive Snapshot Discovery & Atomic Copy
# Note: Verification of snapshot retrieval, missing directories, and atomic writes
# ==============================================================================


@pytest.mark.unit
def test_find_latest_archive_backup_non_dir(tmp_path: Path) -> None:
    """Verify returns None if archive root is not a directory."""
    res = find_latest_archive_backup("src/gda/test.py", tmp_path / "missing_archive")
    assert res is None


@pytest.mark.unit
def test_find_latest_archive_backup_selection(tmp_path: Path) -> None:
    """Verify newest snapshot is discovered even among multiple historical versions."""
    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    (arch / "dir.bk").mkdir()

    (arch / "test.py.20250101_100000.bk").write_text("old", encoding="utf-8")
    (arch / "test.py.20261108_120000.bk").write_text("new", encoding="utf-8")
    (arch / "plain.bk").write_text("plain", encoding="utf-8")

    candidate = find_latest_archive_backup("src/gda/test.py", arch)
    assert candidate is not None
    assert candidate.path.name == "test.py.20261108_120000.bk"

    cand_plain = find_latest_archive_backup("plain", arch)
    assert cand_plain is not None

    assert find_latest_archive_backup("nonexistent.py", arch) is None


@pytest.mark.integration
def test_atomic_copy_success_and_exception_branches(tmp_path: Path) -> None:
    """Verify atomic_copy transfers content and exercises both branches 137->138 and 137->139."""
    src = tmp_path / "source.txt"
    src.write_text("restored payload", encoding="utf-8")
    dst = tmp_path / "sub" / "target.txt"

    atomic_copy(src, dst)
    assert dst.read_text(encoding="utf-8") == "restored payload"

    # Branch 137->138: tmp_path exists and is unlinked
    with patch("shutil.copyfileobj", side_effect=OSError("Write failure")):
        with pytest.raises(OSError):
            atomic_copy(src, dst)

    # Branch 137->139: tmp_path does not exist when exception occurs
    with patch("tempfile.mkstemp", return_value=(999, str(tmp_path / "nonexistent.tmp"))):
        with patch("os.fdopen", side_effect=OSError("Open fd failure")):
            with pytest.raises(OSError):
                atomic_copy(src, dst)


# ==============================================================================
# GROUP 3: Git Fallback & Single File Entry Restoration
# Note: Verification of git restoration, code domain checks, and dry-run
# ==============================================================================


@pytest.mark.unit
def test_restore_from_git_success_and_failure(tmp_path: Path) -> None:
    """Verify restore_from_git dispatches git command and handles exceptions."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        assert restore_from_git(Path("src/gda/file.py"), tmp_path) is True

        mock_run.return_value.returncode = 1
        assert restore_from_git(Path("src/gda/file.py"), tmp_path) is False

    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert restore_from_git(Path("src/gda/file.py"), tmp_path) is False


@pytest.mark.integration
def test_restore_file_entry_domain_rejection_with_and_without_logger(tmp_path: Path) -> None:
    """Verify files outside approved code domains are rejected with and without logger (covers 166->168)."""
    cfg = load_config()
    logger = logging.getLogger("test_restore")

    ok1, msg1 = restore_file_entry("outside/untracked.txt", tmp_path, cfg, logger=logger)
    assert ok1 is False and "REJECTED" in msg1

    # Without logger (covers branch 166->168)
    ok2, msg2 = restore_file_entry("outside/untracked.txt", tmp_path, cfg, logger=None)
    assert ok2 is False and "REJECTED" in msg2


@pytest.mark.integration
def test_restore_file_entry_archive_success_and_dry_run_modes(tmp_path: Path) -> None:
    """Verify restoration from archive in real/dry-run with and without logger (covers 178->180, 185->187)."""
    cfg = load_config()
    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    bk = arch / "mod.py.20261108_120000.bk"
    bk.write_text("restored content", encoding="utf-8")

    logger = logging.getLogger("test_restore")

    # Dry-run with and without logger (covers branch 178->180)
    ok_dry1, _ = restore_file_entry("src/gda/mod.py", tmp_path, cfg, logger=logger, dry_run=True)
    assert ok_dry1 is True

    ok_dry2, _ = restore_file_entry("src/gda/mod.py", tmp_path, cfg, logger=None, dry_run=True)
    assert ok_dry2 is True

    # Real restore with and without logger (covers branch 185->187)
    ok_real1, _ = restore_file_entry("src/gda/mod.py", tmp_path, cfg, logger=logger, dry_run=False)
    assert ok_real1 is True
    assert (tmp_path / "src" / "gda" / "mod.py").read_text(encoding="utf-8") == "restored content"

    ok_real2, _ = restore_file_entry("src/gda/mod.py", tmp_path, cfg, logger=None, dry_run=False)
    assert ok_real2 is True


@pytest.mark.integration
def test_restore_file_entry_archive_exception_modes(tmp_path: Path) -> None:
    """Verify atomic copy exceptions with and without logger (covers 190->192)."""
    cfg = load_config()
    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    (arch / "err.py.20261108_120000.bk").write_text("data", encoding="utf-8")

    logger = logging.getLogger("test_restore")
    with patch(
        "system.gen_desk_mgr.gd_backup_tools.restorer.atomic_copy",
        side_effect=OSError("Disk write error"),
    ):
        ok1, msg1 = restore_file_entry(
            "src/gda/err.py", tmp_path, cfg, logger=logger, dry_run=False
        )
        assert ok1 is False and "RESTORE_FAILED" in msg1

        ok2, msg2 = restore_file_entry("src/gda/err.py", tmp_path, cfg, logger=None, dry_run=False)
        assert ok2 is False and "RESTORE_FAILED" in msg2


@pytest.mark.integration
def test_restore_file_entry_git_fallback_and_unavailable_modes(tmp_path: Path) -> None:
    """Verify Git fallback & unavailable paths with and without logger (covers 197->199, 201->203, 206->208)."""
    cfg = load_config()
    logger = logging.getLogger("test_restore")

    # Git fallback dry-run with and without logger (covers branch 197->199)
    with patch("system.gen_desk_mgr.gd_backup_tools.restorer.restore_from_git", return_value=True):
        ok_g_dry1, _ = restore_file_entry(
            "src/gda/g.py", tmp_path, cfg, logger=logger, dry_run=True
        )
        assert ok_g_dry1 is True

        ok_g_dry2, _ = restore_file_entry("src/gda/g.py", tmp_path, cfg, logger=None, dry_run=True)
        assert ok_g_dry2 is True

        # Git fallback real with and without logger (covers branch 201->203)
        ok_g_real1, _ = restore_file_entry(
            "src/gda/g.py", tmp_path, cfg, logger=logger, dry_run=False
        )
        assert ok_g_real1 is True

        ok_g_real2, _ = restore_file_entry(
            "src/gda/g.py", tmp_path, cfg, logger=None, dry_run=False
        )
        assert ok_g_real2 is True

    # Unavailable with and without logger (covers branch 206->208)
    with patch("system.gen_desk_mgr.gd_backup_tools.restorer.restore_from_git", return_value=False):
        ok_u1, msg_u1 = restore_file_entry("src/gda/absent.py", tmp_path, cfg, logger=logger)
        assert ok_u1 is False and "RESTORE_UNAVAILABLE" in msg_u1

        ok_u2, msg_u2 = restore_file_entry("src/gda/absent.py", tmp_path, cfg, logger=None)
        assert ok_u2 is False and "RESTORE_UNAVAILABLE" in msg_u2


# ==============================================================================
# GROUP 4: Batch Restoration Pipeline
# Note: Verification of restore_batch_from_list handling empty and mixed manifests
# ==============================================================================


@pytest.mark.integration
def test_restore_batch_from_list_empty_and_mixed(tmp_path: Path) -> None:
    """Verify restore_batch_from_list aggregates counts and handles empty lists."""
    cfg = load_config()
    empty_manifest = tmp_path / "empty.txt"
    empty_manifest.write_text("# Only comments\n\n", encoding="utf-8")

    succ0, fail0, msgs0 = restore_batch_from_list(empty_manifest, tmp_path, cfg)
    assert succ0 == 0 and fail0 == 0
    assert "Notice:" in msgs0[0]

    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    (arch / "valid.py.20261108_120000.bk").write_text("v", encoding="utf-8")

    manifest = tmp_path / "manifest.txt"
    manifest.write_text(
        """
src/gda/valid.py
outside/invalid.txt
""",
        encoding="utf-8",
    )

    logger = logging.getLogger("test_batch")
    succ, fail, msgs = restore_batch_from_list(
        manifest, tmp_path, cfg, logger=logger, dry_run=False
    )
    assert succ == 1
    assert fail == 1
    assert len(msgs) == 2
