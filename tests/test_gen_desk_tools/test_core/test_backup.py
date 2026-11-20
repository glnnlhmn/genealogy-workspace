"""Path: tests/test_gen_desk_tools/test_core/test_backup.py

Unit, regression, and integration tests for gen_desk_tools.core.backup.
"""

from __future__ import annotations

import logging
import os
import shutil
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.core.backup import (
    atomic_copy,
    atomic_write_text,
    create_safe_backup,
    is_protected_domain,
    resolve_backup_dir,
)

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end Safe Backup creation into mirrored archive directories.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_create_safe_backup_writes_mirrored_timestamped_snapshot(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify create_safe_backup copies an existing file into its mirrored archive bucket."""
    target = gdt_workspace / "src" / "gen_desk_tools" / "sample.py"
    target.write_text("print('v1')\n", encoding="utf-8")
    logger = logging.getLogger("test_backup_smoke")

    backup_path = create_safe_backup(
        target,
        gdt_workspace,
        gdt_config,
        logger=logger,
        timestamp="20261119_120000",
    )

    expected = (
        gdt_workspace
        / "archive"
        / "backups_gen_desk_tools"
        / "src"
        / "gen_desk_tools"
        / "sample.py.20261119_120000.bk"
    )
    assert backup_path == expected
    assert backup_path.is_file()
    assert backup_path.read_text(encoding="utf-8") == "print('v1')\n"


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Protected-domain matching and longest-prefix backup routing.
# ==========================================================================


@pytest.mark.unit
def test_is_protected_domain_matches_exact_and_nested_paths(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify exact domain roots and nested files return True."""
    assert is_protected_domain(Path("src"), gdt_workspace, gdt_config) is True
    assert is_protected_domain(Path("src/gda/core.py"), gdt_workspace, gdt_config) is True
    assert is_protected_domain(Path("data/setup/seed.sql"), gdt_workspace, gdt_config) is True


@pytest.mark.unit
def test_resolve_backup_dir_selects_longest_matching_prefix(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify more specific routing prefixes override shorter parent prefixes."""
    cfg = {
        **gdt_config,
        "backup_routing": {
            "src": "backups_generic_src",
            "src/gda": "backups_gda",
            "default": "backups_gen_desk_tools",
        },
    }
    target = gdt_workspace / "src" / "gda" / "model" / "person.py"

    result = resolve_backup_dir(target, gdt_workspace, cfg)
    assert result == (gdt_workspace / "archive" / "backups_gda" / "src" / "gda" / "model").resolve()


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Prefix collisions, default bucket fallbacks, dry-run, and missing targets.
# ==========================================================================


@pytest.mark.regression
def test_is_protected_domain_rejects_unprotected_and_prefix_collision_paths(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify sibling folders sharing a prefix (e.g., src_extra) are not treated as protected."""
    assert is_protected_domain(Path("docs/guide.md"), gdt_workspace, gdt_config) is False
    assert is_protected_domain(Path("src_extra/file.py"), gdt_workspace, gdt_config) is False


@pytest.mark.regression
def test_resolve_backup_dir_falls_back_to_default_bucket(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify unmapped workspace paths route to the configured default backup bucket."""
    target = gdt_workspace / "docs" / "notes.md"
    result = resolve_backup_dir(target, gdt_workspace, gdt_config)
    assert result == (gdt_workspace / "archive" / "backups_gen_desk_tools" / "docs").resolve()


@pytest.mark.regression
def test_create_safe_backup_nonexistent_target_returns_none(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify create_safe_backup returns None when backing up a file that does not exist yet."""
    missing = gdt_workspace / "src" / "gen_desk_tools" / "new_file.py"
    assert create_safe_backup(missing, gdt_workspace, gdt_config) is None


@pytest.mark.regression
def test_create_safe_backup_dry_run_skips_disk_write(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify dry_run returns the planned backup path without creating a file on disk."""
    target = gdt_workspace / "src" / "gen_desk_tools" / "dry.py"
    target.write_text("x = 1\n", encoding="utf-8")
    logger = logging.getLogger("test_backup_dry")

    # Exercise both logger=None and logger-provided dry-run branches
    planned_a = create_safe_backup(
        target, gdt_workspace, gdt_config, dry_run=True, timestamp="20261119_120001"
    )
    planned_b = create_safe_backup(
        target, gdt_workspace, gdt_config, logger=logger, dry_run=True, timestamp="20261119_120001"
    )

    assert planned_a == planned_b
    assert planned_a is not None and not planned_a.exists()


@pytest.mark.regression
def test_create_safe_backup_auto_timestamp_without_logger(
    gdt_workspace: Path,
    gdt_config: dict[str, Any],
) -> None:
    """Verify create_safe_backup generates a UTC timestamp and succeeds when logger is None."""
    target = gdt_workspace / "src" / "gen_desk_tools" / "auto_ts.py"
    target.write_text("y = 2\n", encoding="utf-8")

    backup_path = create_safe_backup(target, gdt_workspace, gdt_config)
    assert backup_path is not None
    assert backup_path.is_file()
    assert backup_path.name.startswith("auto_ts.py.")
    assert backup_path.name.endswith(".bk")


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Missing sources and orphaned temp-file cleanup on write/copy failures.
# ==========================================================================


@pytest.mark.regression
def test_atomic_copy_missing_source_raises_file_not_found(tmp_path: Path) -> None:
    """Verify atomic_copy raises FileNotFoundError when the source file does not exist."""
    with pytest.raises(FileNotFoundError, match="Source file does not exist"):
        atomic_copy(tmp_path / "missing.txt", tmp_path / "dest.txt")


@pytest.mark.regression
def test_atomic_write_text_replace_failure_cleans_temp_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify atomic_write_text removes its staging temp file when os.replace fails."""
    target = tmp_path / "locked.txt"

    # Simulate a Windows file-locking collision during atomic swap
    def _fail_replace(src: Path, dst: Path) -> None:
        raise OSError("Simulated lock failure")

    monkeypatch.setattr(os, "replace", _fail_replace)

    with pytest.raises(OSError, match="Simulated lock failure"):
        atomic_write_text(target, "content\n")

    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.regression
def test_atomic_write_text_cleanup_skips_already_removed_temp_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify atomic_write_text handles errors cleanly if the temp file was already removed."""
    target = tmp_path / "vanished.txt"

    def _unlink_then_fail(src: Path, dst: Path) -> None:
        Path(src).unlink()
        raise OSError("Simulated post-unlink failure")

    monkeypatch.setattr(os, "replace", _unlink_then_fail)

    with pytest.raises(OSError, match="Simulated post-unlink failure"):
        atomic_write_text(target, "content\n")


@pytest.mark.regression
def test_atomic_copy_failure_cleans_temp_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify atomic_copy removes its staging temp file when shutil.copy2 fails."""
    src = tmp_path / "src.txt"
    src.write_text("hello\n", encoding="utf-8")

    def _fail_copy(src_path: Path, dst_path: Path) -> None:
        raise OSError("Simulated copy failure")

    monkeypatch.setattr(shutil, "copy2", _fail_copy)

    with pytest.raises(OSError, match="Simulated copy failure"):
        atomic_copy(src, tmp_path / "dst.txt")

    assert list(tmp_path.glob("*.tmp")) == []


@pytest.mark.regression
def test_atomic_copy_cleanup_skips_already_removed_temp_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify atomic_copy handles errors cleanly if the temp file was already removed."""
    src = tmp_path / "src.txt"
    src.write_text("hello\n", encoding="utf-8")

    def _unlink_then_fail(src_path: Path, dst_path: Path) -> None:
        Path(dst_path).unlink()
        raise OSError("Simulated copy unlink failure")

    monkeypatch.setattr(shutil, "copy2", _unlink_then_fail)

    with pytest.raises(OSError, match="Simulated copy unlink failure"):
        atomic_copy(src, tmp_path / "dst.txt")


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Atomic text write creation and overwrite verification on disk.
# ==========================================================================


@pytest.mark.integration
def test_atomic_write_text_creates_parents_and_writes_lf_utf8(tmp_path: Path) -> None:
    """Verify atomic_write_text creates missing parent dirs and writes UTF-8 LF text."""
    target = tmp_path / "nested" / "dir" / "output.txt"
    atomic_write_text(target, "line1\nline2\n")

    assert target.read_bytes() == b"line1\nline2\n"
