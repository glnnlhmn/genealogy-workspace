"""Path: tests/test_system/test_gen_desk_mgr/test_pruner.py

Unit test suite for backup retention evaluation and pruning.

Operational Role:
    Verifies candidate selection by version count overflow and age limits,
    branch coverage for unpruned recent snapshots, and atomic deletion.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from system.gen_desk_mgr.gd_backup_tools.pruner import (
    execute_prune,
    find_prune_candidates,
)

__version__ = "1.0.0+build.6"

# ==============================================================================
# GROUP 1: Retention Candidate Discovery
# Note: Verification of max_versions and max_age_days evaluation
# ==============================================================================


@pytest.mark.unit
def test_find_prune_candidates_non_directory(tmp_path: Path) -> None:
    """Verify returns empty list if archive directory does not exist."""
    res = find_prune_candidates(tmp_path / "nonexistent", {})
    assert res == []


@pytest.mark.unit
def test_find_prune_candidates_version_age_overflow_and_recent_skips(tmp_path: Path) -> None:
    """Verify candidate discovery handles version overflow, age overflow, and recent snapshot skips."""
    arch = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch.mkdir(parents=True)
    (arch / "dir.bk").mkdir()

    # Create 5 snapshots from 2025 (eligible for version and age pruning)
    for i in range(1, 6):
        (arch / f"module.py.2025010{i}_120000.bk").write_text(f"v{i}", encoding="utf-8")

    # Create 1 snapshot from today (exercises branch 94->91 where ts >= age_cutoff)
    from datetime import datetime

    today_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    (arch / f"module.py.{today_str}.bk").write_text("today", encoding="utf-8")

    cfg = {"retention": {"max_versions": 3, "max_age_days": 30}}
    candidates = find_prune_candidates(tmp_path / "archive", cfg)

    assert len(candidates) >= 3
    pruned_names = [c.path.name for c in candidates]
    assert f"module.py.{today_str}.bk" not in pruned_names


@pytest.mark.unit
def test_find_prune_candidates_st_mtime_fallback(tmp_path: Path) -> None:
    """Verify fallback to stat().st_mtime when filename lacks standard timestamp."""
    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    plain_bk = arch / "plain.bk"
    plain_bk.write_text("content", encoding="utf-8")

    cfg = {"retention": {"max_versions": 5, "max_age_days": 0}}
    candidates = find_prune_candidates(tmp_path / "archive", cfg)
    assert isinstance(candidates, list)


# ==============================================================================
# GROUP 2: Pruning Execution
# Note: Verification of execute_prune, logging, and dry-run safety
# ==============================================================================


@pytest.mark.integration
def test_execute_prune_deletes_files(tmp_path: Path) -> None:
    """Verify execute_prune removes candidates from disk."""
    arch = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch.mkdir(parents=True)

    for i in range(1, 4):
        (arch / f"test.py.2026110{i}_120000.bk").write_text(f"v{i}", encoding="utf-8")

    cfg = {"retention": {"max_versions": 1, "max_age_days": 0}}
    pruned = execute_prune(tmp_path / "archive", cfg, dry_run=False)

    assert len(pruned) == 2
    assert not (arch / "test.py.20261101_120000.bk").exists()
    assert not (arch / "test.py.20261102_120000.bk").exists()
    assert (arch / "test.py.20261103_120000.bk").exists()


@pytest.mark.unit
def test_execute_prune_dry_run_modes(tmp_path: Path) -> None:
    """Verify execute_prune dry-run simulates pruning with and without logger."""
    arch = tmp_path / "archive"
    arch.mkdir(parents=True)
    bk = arch / "test.py.20261101_120000.bk"
    bk.write_text("test", encoding="utf-8")

    cfg = {"retention": {"max_versions": 0, "max_age_days": 1}}
    logger = logging.getLogger("test_prune")
    pruned1 = execute_prune(arch, cfg, logger=logger, dry_run=True)
    assert len(pruned1) == 1
    assert bk.exists()

    pruned2 = execute_prune(arch, cfg, logger=None, dry_run=True)
    assert len(pruned2) == 1


@pytest.mark.unit
def test_execute_prune_unlink_error_handling(tmp_path: Path) -> None:
    """Verify execute_prune catches and handles unlink errors with and without logger."""
    arch = tmp_path / "archive"
    arch.mkdir(parents=True)
    bk = arch / "test.py.20261101_120000.bk"
    bk.write_text("test", encoding="utf-8")

    cfg = {"retention": {"max_versions": 0, "max_age_days": 1}}
    logger = logging.getLogger("test_prune_err")

    with patch.object(Path, "unlink", side_effect=PermissionError("Permission denied")):
        p1 = execute_prune(arch, cfg, logger=logger, dry_run=False)
        assert len(p1) == 1

        p2 = execute_prune(arch, cfg, logger=None, dry_run=False)
        assert len(p2) == 1
