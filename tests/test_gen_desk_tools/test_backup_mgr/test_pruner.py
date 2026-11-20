"""Path: tests/test_gen_desk_tools/test_backup_mgr/test_pruner.py

Unit, regression, and integration tests for gen_desk_tools.backup_mgr.pruner.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.backup_mgr.pruner import execute_prune, find_prune_candidates

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Retention candidate discovery and deletion under max_versions.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_execute_prune_deletes_snapshots_exceeding_max_versions(tmp_path: Path) -> None:
    """Verify execute_prune removes older snapshots beyond max_versions."""
    arch = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch.mkdir(parents=True)
    for day in range(1, 4):
        (arch / f"mod.py.2026110{day}_120000.bk").write_text(f"v{day}", encoding="utf-8")

    cfg = {"retention": {"max_versions": 1, "max_age_days": 0}}
    logger = logging.getLogger("test_pruner_smoke")
    pruned = execute_prune(tmp_path / "archive", cfg, logger=logger)

    assert len(pruned) == 2
    assert (arch / "mod.py.20261103_120000.bk").is_file()
    assert not (arch / "mod.py.20261101_120000.bk").exists()


# ==========================================================================
# GROUP 2: Retention Policy Boundaries & Error Handling
# Note: Age overflow, recent snapshot retention, st_mtime fallback, and unlink errors.
# ==========================================================================


@pytest.mark.unit
def test_find_prune_candidates_version_age_and_missing_archive(tmp_path: Path) -> None:
    """Verify version overflow, age overflow, recent skips, and missing archive handling."""
    assert find_prune_candidates(tmp_path / "missing", {}) == []

    arch = tmp_path / "archive" / "backups_gda"
    arch.mkdir(parents=True)
    (arch / "dir.bk").mkdir()
    (arch / "plain.bk").write_text("p", encoding="utf-8")
    (arch / "mod.py.20250101_120000.bk").write_text("old1", encoding="utf-8")
    (arch / "mod.py.20250102_120000.bk").write_text("old2", encoding="utf-8")
    (arch / "mod.py.20261119_120000.bk").write_text("new", encoding="utf-8")

    cfg = {"retention": {"max_versions": 2, "max_age_days": 30}}
    candidates = find_prune_candidates(
        tmp_path / "archive", cfg, now=datetime(2026, 11, 19, 13, 0, 0)
    )
    pruned_names = {c.path.name for c in candidates}

    assert "mod.py.20250101_120000.bk" in pruned_names
    assert "mod.py.20250102_120000.bk" in pruned_names
    assert "mod.py.20261119_120000.bk" not in pruned_names


@pytest.mark.regression
def test_execute_prune_handles_unlink_errors_with_and_without_logger(tmp_path: Path) -> None:
    """Verify execute_prune catches unlink errors safely whether logger is provided or None."""
    arch = tmp_path / "archive"
    arch.mkdir(parents=True)
    (arch / "mod.py.20250101_120000.bk").write_text("old", encoding="utf-8")
    cfg = {"retention": {"max_versions": 0, "max_age_days": 1}}

    with patch.object(Path, "unlink", side_effect=PermissionError("locked")):
        res_logged = execute_prune(arch, cfg, logger=logging.getLogger("test_prune_err"))
        res_unlogged = execute_prune(arch, cfg, logger=None)

    assert len(res_logged) == 1
    assert len(res_unlogged) == 1
    # Also cover successful unlink with logger=None
    assert len(execute_prune(arch, cfg, logger=None)) == 1
