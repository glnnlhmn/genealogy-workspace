"""Path: tests/test_gen_desk_tools/test_backup_mgr/test_restorer.py

Unit, regression, and integration tests for gen_desk_tools.backup_mgr.restorer.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.backup_mgr.restorer import (
    find_latest_archive_backup,
    parse_restore_list,
    restore_batch_from_list,
    restore_file_entry,
    restore_from_git,
)
from gen_desk_tools.core.config import load_gdt_config

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single-file restoration from newest archive Safe Backup snapshot.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_restore_file_entry_restores_newest_archive_snapshot(gdt_workspace: Path) -> None:
    """Verify restore_file_entry atomically restores the newest .bk snapshot."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    arch = gdt_workspace / "archive" / "backups_gen_desk_tools" / "src" / "gen_desk_tools"
    arch.mkdir(parents=True)
    (arch / "mod.py.20261118_100000.bk").write_text("old", encoding="utf-8")
    (arch / "mod.py.20261119_120000.bk").write_text("latest", encoding="utf-8")

    ok, msg = restore_file_entry(
        "src/gen_desk_tools/mod.py",
        gdt_workspace,
        cfg,
        logger=logging.getLogger("test_restorer"),
    )

    assert ok is True
    assert "RESTORED (archive)" in msg
    assert (gdt_workspace / "src" / "gen_desk_tools" / "mod.py").read_text(
        encoding="utf-8"
    ) == "latest"


# ==========================================================================
# GROUP 2: Manifest Parsing, Snapshot Discovery & Git Fallback
# Note: parse_restore_list, find_latest_archive_backup, and restore_from_git.
# ==========================================================================


@pytest.mark.unit
def test_parse_restore_list_filters_comments_and_normalizes_slashes(tmp_path: Path) -> None:
    """Verify parse_restore_list handles missing files, comments, blanks, and backslashes."""
    assert parse_restore_list(tmp_path / "missing.txt") == []

    manifest = tmp_path / "list.txt"
    manifest.write_text("# comment\n\nsrc\\gda\\a.py\ntests/test_gda/b.py\n", encoding="utf-8")
    assert parse_restore_list(manifest) == ["src/gda/a.py", "tests/test_gda/b.py"]


@pytest.mark.unit
def test_find_latest_archive_backup_variants(tmp_path: Path) -> None:
    """Verify snapshot discovery handles missing dirs, non-files, plain .bk, and misses."""
    assert find_latest_archive_backup("src/a.py", tmp_path / "missing") is None

    arch = tmp_path / "archive"
    arch.mkdir()
    (arch / "dir.bk").mkdir()
    (arch / "other.py.20261119_120000.bk").write_text("x", encoding="utf-8")
    (arch / "plain.bk").write_text("p", encoding="utf-8")

    assert find_latest_archive_backup("src/plain", arch) is not None
    assert find_latest_archive_backup("src/none.py", arch) is None


@pytest.mark.unit
def test_restore_from_git_success_failure_and_oserror(tmp_path: Path) -> None:
    """Verify restore_from_git returns True on exit 0 and False on failure or OSError."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        assert restore_from_git(Path("src/a.py"), tmp_path) is True
        mock_run.return_value.returncode = 1
        assert restore_from_git(Path("src/a.py"), tmp_path) is False

    with patch("subprocess.run", side_effect=FileNotFoundError("no git")):
        assert restore_from_git(Path("src/a.py"), tmp_path) is False


# ==========================================================================
# GROUP 3: Policy Rejections & Batch Restoration
# Note: Root escape, unprotected domain, Git fallback, and batch aggregation.
# ==========================================================================


@pytest.mark.regression
def test_restore_file_entry_rejections_and_git_fallback(gdt_workspace: Path) -> None:
    """Verify root escapes, unprotected domains, Git fallback, and total misses."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    logger = logging.getLogger("test_restorer_edges")

    # Outside workspace root (logged and unlogged)
    assert restore_file_entry("../../outside.py", gdt_workspace, cfg, logger=logger)[0] is False
    assert restore_file_entry("../../outside.py", gdt_workspace, cfg, logger=None)[0] is False

    # Outside protected domains (logged and unlogged)
    assert restore_file_entry("docs/note.md", gdt_workspace, cfg, logger=logger)[0] is False
    assert restore_file_entry("docs/note.md", gdt_workspace, cfg, logger=None)[0] is False

    # Git HEAD fallback (logged and unlogged)
    with patch("gen_desk_tools.backup_mgr.restorer.restore_from_git", return_value=True):
        assert restore_file_entry("src/gda/git.py", gdt_workspace, cfg, logger=logger)[0] is True
        assert restore_file_entry("src/gda/git.py", gdt_workspace, cfg, logger=None)[0] is True

    # No archive and no Git HEAD (logged and unlogged)
    with patch("gen_desk_tools.backup_mgr.restorer.restore_from_git", return_value=False):
        assert restore_file_entry("src/gda/none.py", gdt_workspace, cfg, logger=logger)[0] is False
        assert restore_file_entry("src/gda/none.py", gdt_workspace, cfg, logger=None)[0] is False


@pytest.mark.integration
def test_restore_batch_from_list_aggregates_successes_and_failures(gdt_workspace: Path) -> None:
    """Verify restore_batch_from_list counts succeeded and failed entries accurately."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    arch = gdt_workspace / "archive" / "backups_gen_desk_tools" / "src" / "gen_desk_tools"
    arch.mkdir(parents=True)
    (arch / "ok.py.20261119_120000.bk").write_text("ok", encoding="utf-8")

    manifest = gdt_workspace / "restore.txt"
    manifest.write_text("src/gen_desk_tools/ok.py\ndocs/rejected.md\n", encoding="utf-8")

    succ, fail, msgs = restore_batch_from_list(manifest, gdt_workspace, cfg, logger=None)

    assert (succ, fail) == (1, 1)
    assert len(msgs) == 2
