"""Path: tests/test_system/test_gen_desk_mgr/test_engine.py

Unit and integration test suite for backup engine and auto-backup scanner.

Operational Role:
    Verifies single-file backups, directory tree backups, code domain security
    checks, collision tiebreakers, error handling, temp cleanup branches, and
    automated backup generation achieving 100% statement and branch coverage.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from system.gen_desk_mgr.gd_backup_tools.config import load_config
from system.gen_desk_mgr.gd_backup_tools.engine import (
    backup_folder,
    create_single_backup,
    is_in_code_domain,
    parse_backup_filename,
    resolve_backup_destination,
    run_auto_backup,
)

__version__ = "1.0.0+build.9"

# ==============================================================================
# GROUP 1: Parsing and Code Domain Boundary Checks
# Note: Verification of parse_backup_filename and domain containment
# ==============================================================================


@pytest.mark.unit
def test_parse_backup_filename_variants() -> None:
    """Verify filename parser handles timestamps, .bk fallback, and non-matches."""
    orig, ts = parse_backup_filename("file.py.20261108_120000.bk")
    assert orig == "file.py"
    assert ts is not None

    orig_plain, ts_none = parse_backup_filename("plain.bk")
    assert orig_plain == "plain"
    assert ts_none is None

    orig_raw, ts_raw = parse_backup_filename("plain.txt")
    assert orig_raw == "plain.txt"
    assert ts_raw is None

    orig_bad, ts_bad = parse_backup_filename("file.py.99999999_999999.bk")
    assert orig_bad == "file.py"
    assert ts_bad is None


@pytest.mark.unit
def test_is_in_code_domain_valid(tmp_path: Path) -> None:
    """Verify valid files within protected domains pass verification."""
    cfg = load_config()
    target = tmp_path / "src" / "gda" / "test.py"
    assert is_in_code_domain(target, tmp_path, cfg) is True

    test_target = tmp_path / "tests" / "test_gda" / "test_file.py"
    assert is_in_code_domain(test_target, tmp_path, cfg) is True


@pytest.mark.unit
def test_is_in_code_domain_rejected_outside(tmp_path: Path) -> None:
    """Verify files outside protected code domains are rejected."""
    cfg = load_config()
    outside = tmp_path / "archive" / "backups_gda" / "file.bk"
    assert is_in_code_domain(outside, tmp_path, cfg) is False


@pytest.mark.unit
def test_is_in_code_domain_value_error(tmp_path: Path) -> None:
    """Verify False returned when relative_to raises ValueError."""
    cfg = load_config()
    diff_root = Path("Z:/different/drive/file.py")
    assert is_in_code_domain(diff_root, tmp_path, cfg) is False


# ==============================================================================
# GROUP 2: Backup Destination Resolution & Single Backup
# Note: Verification of routing overrides, collision counter, and atomic replace
# ==============================================================================


@pytest.mark.unit
def test_resolve_backup_destination_default_fallback(tmp_path: Path) -> None:
    """Verify default project fallback when prefix is not explicitly listed."""
    cfg = {
        "workspace": {"archive_dir": "archive"},
        "backup_routing": {"default": "backups_custom"},
    }
    target = tmp_path / "other" / "doc.txt"
    dest = resolve_backup_destination(target, tmp_path, cfg)
    assert "backups_custom/other" in dest.as_posix()


@pytest.mark.integration
def test_create_single_backup_success(tmp_path: Path) -> None:
    """Verify create_single_backup atomically creates snapshot in archive."""
    cfg = load_config()
    target = tmp_path / "src" / "gda" / "module.py"
    target.parent.mkdir(parents=True)
    target.write_text("print('test')", encoding="utf-8")

    logger = logging.getLogger("test_engine")
    bk = create_single_backup(target, tmp_path, cfg, logger=logger)
    assert bk is not None
    assert bk.is_file()
    assert "archive/backups_gda/src/gda/module.py." in bk.as_posix()


@pytest.mark.unit
def test_create_single_backup_non_file_or_disallowed_domain(tmp_path: Path) -> None:
    """Verify returns None if target is directory or outside protected domains."""
    cfg = load_config()
    assert create_single_backup(tmp_path / "nonexistent.py", tmp_path, cfg) is None

    outside = tmp_path / "untracked" / "file.txt"
    outside.parent.mkdir(parents=True)
    outside.write_text("outside", encoding="utf-8")
    assert create_single_backup(outside, tmp_path, cfg) is None


@pytest.mark.integration
def test_create_single_backup_collision_counter(tmp_path: Path) -> None:
    """Verify collision counter increments if target snapshot already exists."""
    cfg = load_config()
    target = tmp_path / "src" / "gda" / "collision.py"
    target.parent.mkdir(parents=True)
    target.write_text("v1", encoding="utf-8")

    dest_folder = resolve_backup_destination(target, tmp_path, cfg)
    dest_folder.mkdir(parents=True)

    fixed_now = "20261108_120000"
    with patch("system.gen_desk_mgr.gd_backup_tools.engine.datetime") as mock_dt:
        mock_dt.now.return_value.strftime.return_value = fixed_now
        bk1 = create_single_backup(target, tmp_path, cfg)
        bk2 = create_single_backup(target, tmp_path, cfg)

    assert bk1 is not None and bk2 is not None
    assert bk1.name == f"collision.py.{fixed_now}.bk"
    assert bk2.name == f"collision.py.{fixed_now}_1.bk"


@pytest.mark.unit
def test_create_single_backup_dry_run_modes(tmp_path: Path) -> None:
    """Verify dry-run mode returns candidate path without creating file with/without logger."""
    cfg = load_config()
    target = tmp_path / "src" / "gda" / "dry.py"
    target.parent.mkdir(parents=True)
    target.write_text("dry run", encoding="utf-8")

    logger = logging.getLogger("test_dry")
    bk1 = create_single_backup(target, tmp_path, cfg, logger=logger, dry_run=True)
    assert bk1 is not None and not bk1.exists()

    bk2 = create_single_backup(target, tmp_path, cfg, logger=None, dry_run=True)
    assert bk2 is not None and not bk2.exists()


@pytest.mark.integration
def test_create_single_backup_exception_cleanup(tmp_path: Path) -> None:
    """Verify temporary file cleanup covering branches 160->161 and 160->162."""
    cfg = load_config()
    target = tmp_path / "src" / "gda" / "err.py"
    target.parent.mkdir(parents=True)
    target.write_text("code", encoding="utf-8")

    # Branch 160->161: tmp_path exists and is unlinked
    with patch("shutil.copyfileobj", side_effect=OSError("Disk write error")):
        with pytest.raises(OSError):
            create_single_backup(target, tmp_path, cfg)

    # Branch 160->162: tmp_path does not exist when exception handler runs
    with patch("tempfile.mkstemp", return_value=(999, str(tmp_path / "nonexistent.tmp"))):
        with patch("os.fdopen", side_effect=OSError("Fd open failure")):
            with pytest.raises(OSError):
                create_single_backup(target, tmp_path, cfg)


# ==============================================================================
# GROUP 3: Folder Backup & Automated Scanner
# Note: Verification of directory recursion and missing/stale backup discovery
# ==============================================================================


@pytest.mark.integration
def test_backup_folder_tree_recursive_and_flat(tmp_path: Path) -> None:
    """Verify backup_folder handles recursive descent, flat scans, and skipped files."""
    cfg = load_config()
    tree = tmp_path / "src" / "gda" / "sub"
    nested = tree / "inner"
    nested.mkdir(parents=True)
    (tree / "a.py").write_text("a", encoding="utf-8")
    (nested / "b.py").write_text("b", encoding="utf-8")

    assert backup_folder(tmp_path / "missing_dir", tmp_path, cfg) == []

    flat_results = backup_folder(tree, tmp_path, cfg, recursive=False)
    assert len(flat_results) == 1

    rec_results = backup_folder(tree, tmp_path, cfg, recursive=True)
    assert len(rec_results) == 2

    # Branch 203->198: create_single_backup returns None during folder scan
    with patch(
        "system.gen_desk_mgr.gd_backup_tools.engine.create_single_backup",
        return_value=None,
    ):
        empty_results = backup_folder(tree, tmp_path, cfg, recursive=False)
        assert empty_results == []


@pytest.mark.integration
def test_run_auto_backup_branch_coverage_closure(tmp_path: Path) -> None:
    """Verify run_auto_backup closes branches 239->235 and 261->249 deterministically."""
    cfg = load_config()

    gda_dir = tmp_path / "src" / "gda"
    gda_dir.mkdir(parents=True)

    # Two files in alphabetical order:
    # 1. 01_up_to_date.py: up-to-date (will skip lines 256-260 and loop back to line 249)
    # 2. 02_needs_backup.py: needs backup (will execute lines 256-260)
    f_up_to_date = gda_dir / "01_up_to_date.py"
    f_up_to_date.write_text("content 1", encoding="utf-8")
    past_epoch_2024 = 1704110400.0  # 2024-01-01
    os.utime(f_up_to_date, (past_epoch_2024, past_epoch_2024))

    f_needs_backup = gda_dir / "02_needs_backup.py"
    f_needs_backup.write_text("content 2", encoding="utf-8")

    arch_dir = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch_dir.mkdir(parents=True)
    (arch_dir / "non_file_dir.bk").mkdir()
    (arch_dir / "plain.bk").write_text("legacy", encoding="utf-8")

    # To guarantee branch 239->235 executes:
    # rglob encounters snapshot A first (newer), then snapshot B (older) for 01_up_to_date.py
    sub_a = arch_dir / "a_dir"
    sub_b = arch_dir / "b_dir"
    sub_a.mkdir()
    sub_b.mkdir()

    (sub_a / "01_up_to_date.py.20251201_120000.bk").write_text("newest", encoding="utf-8")
    (sub_b / "01_up_to_date.py.20250101_120000.bk").write_text("older", encoding="utf-8")

    # When run_auto_backup executes:
    # 1. Archive scan:
    #    - sub_a/01_up_to_date... recorded first into latest_backups.
    #    - sub_b/01_up_to_date... triggers branch 239->235 (ts <= latest_backups).
    # 2. Domain scan:
    #    - 01_up_to_date.py has mtime 2024 <= latest_ts 2025: skips if-block, reaches line 261,
    #      and LOOPS BACK to line 249 for 02_needs_backup.py (closes branch 261->249!).
    #    - 02_needs_backup.py has latest_ts None: creates backup and completes loop.
    backups = run_auto_backup(tmp_path, cfg)
    assert len(backups) == 1
    assert "02_needs_backup.py" in backups[0].name
