"""Path: tests/test_gen_desk_tools/test_backup_mgr/test_engine.py

Unit, regression, and integration tests for gen_desk_tools.backup_mgr.engine.
"""

from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.backup_mgr.engine import (
    backup_folder,
    create_single_backup,
    parse_backup_filename,
    run_auto_backup,
)
from gen_desk_tools.core.config import load_gdt_config

__version__ = "1.0.0+build.2"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Primary single-file Safe Backup creation inside a protected domain.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_create_single_backup_protected_file_creates_snapshot(gdt_workspace: Path) -> None:
    """Verify create_single_backup writes a timestamped .bk snapshot into archive/."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    target = gdt_workspace / "src" / "gen_desk_tools" / "sample.py"
    target.write_text("x = 1\n", encoding="utf-8")

    bk = create_single_backup(target, gdt_workspace, cfg)

    assert bk is not None
    assert bk.is_file()
    assert bk.read_text(encoding="utf-8") == "x = 1\n"


# ==========================================================================
# GROUP 2: Filename Parsing & Folder Backups
# Note: Timestamp extraction, recursive vs. flat directory backups, and auto-scan.
# ==========================================================================


@pytest.mark.unit
def test_parse_backup_filename_handles_valid_invalid_and_plain_names() -> None:
    """Verify parse_backup_filename parses timestamps, .bk fallbacks, and invalid dates."""
    orig, ts = parse_backup_filename("mod.py.20261119_120000.bk")
    assert orig == "mod.py"
    assert ts is not None and ts.year == 2026

    assert parse_backup_filename("mod.py.99999999_999999.bk") == ("mod.py", None)
    assert parse_backup_filename("plain.bk") == ("plain", None)
    assert parse_backup_filename("plain.txt") == ("plain.txt", None)


@pytest.mark.integration
def test_backup_folder_recursive_and_non_recursive_modes(gdt_workspace: Path) -> None:
    """Verify backup_folder respects recursive flag and ignores subdirectories."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    pkg = gdt_workspace / "src" / "gen_desk_tools" / "pkg"
    sub = pkg / "nested"
    sub.mkdir(parents=True)
    (pkg / "top.py").write_text("a = 1\n", encoding="utf-8")
    (sub / "deep.py").write_text("b = 2\n", encoding="utf-8")

    flat = backup_folder(pkg, gdt_workspace, cfg, recursive=False)
    deep = backup_folder(pkg, gdt_workspace, cfg, recursive=True)

    assert len(flat) == 1
    assert len(deep) == 2


@pytest.mark.integration
def test_run_auto_backup_snapshots_only_unbacked_protected_files(gdt_workspace: Path) -> None:
    """Verify run_auto_backup skips already-backed files and backs up missing ones."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    src_dir = gdt_workspace / "src" / "gen_desk_tools"
    (src_dir / "sub").mkdir(parents=True, exist_ok=True)
    backed = src_dir / "already.py"
    backed.write_text("v1\n", encoding="utf-8")
    fresh = src_dir / "fresh.py"
    fresh.write_text("v2\n", encoding="utf-8")

    # Pre-seed archive with a backup for already.py plus a non-file .bk directory
    arch_dir = gdt_workspace / "archive" / "backups_gen_desk_tools" / "src" / "gen_desk_tools"
    arch_dir.mkdir(parents=True, exist_ok=True)
    (arch_dir / "already.py.20261119_120000.bk").write_text("v1\n", encoding="utf-8")
    (arch_dir / "dir.bk").mkdir()

    logger = logging.getLogger("test_engine_auto")
    created = run_auto_backup(gdt_workspace, cfg, logger=logger)
    names = [p.name for p in created]

    assert any(n.startswith("fresh.py.") for n in names)
    assert not any(n.startswith("already.py.") for n in names)


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Non-existent targets, unprotected domains, missing archive, and skipped backups.
# ==========================================================================


@pytest.mark.regression
def test_create_single_backup_and_backup_folder_reject_invalid_targets(
    gdt_workspace: Path,
) -> None:
    """Verify missing paths and unprotected-domain files return None or empty lists."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    outside = gdt_workspace / "docs" / "note.md"
    outside.parent.mkdir(parents=True, exist_ok=True)
    outside.write_text("# doc\n", encoding="utf-8")

    assert create_single_backup(gdt_workspace / "missing.py", gdt_workspace, cfg) is None
    assert create_single_backup(outside, gdt_workspace, cfg) is None
    assert backup_folder(gdt_workspace / "missing_dir", gdt_workspace, cfg) == []
    assert backup_folder(outside.parent, gdt_workspace, cfg) == []


@pytest.mark.regression
def test_run_auto_backup_without_archive_dir_or_logger(gdt_workspace: Path) -> None:
    """Verify run_auto_backup succeeds when archive/ does not yet exist and logger is None."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    cfg["workspace"]["archive_dir"] = "archive_new"
    cfg["code_domains"]["protected_domains"] = ["src", "missing_domain"]
    (gdt_workspace / "src" / "gen_desk_tools" / "solo.py").write_text("x = 1\n", encoding="utf-8")

    created = run_auto_backup(gdt_workspace, cfg, logger=None)

    assert len(created) >= 1


@pytest.mark.regression
def test_run_auto_backup_skips_when_single_backup_returns_none(gdt_workspace: Path) -> None:
    """Verify run_auto_backup ignores files where create_single_backup returns None."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    (gdt_workspace / "src" / "gen_desk_tools" / "skipped.py").write_text(
        "x = 1\n", encoding="utf-8"
    )

    with patch("gen_desk_tools.backup_mgr.engine.create_single_backup", return_value=None):
        created = run_auto_backup(gdt_workspace, cfg, logger=None)

    assert created == []
