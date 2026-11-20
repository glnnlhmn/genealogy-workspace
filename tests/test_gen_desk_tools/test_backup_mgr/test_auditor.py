"""Path: tests/test_gen_desk_tools/test_backup_mgr/test_auditor.py

Unit, regression, and integration tests for gen_desk_tools.backup_mgr.auditor.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from gen_desk_tools.backup_mgr.auditor import (
    AuditStatus,
    audit_workspace,
    format_age_from_now,
    format_delta_minutes,
    format_full_audit_report,
    resolve_original_path,
)
from gen_desk_tools.core.config import load_gdt_config

__version__ = "1.0.0+build.2"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: 4-section workspace audit partitioning and consolidated report rendering.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_audit_workspace_partitions_all_four_sections_and_renders_report(
    gdt_workspace: Path,
) -> None:
    """Verify audit_workspace populates all 4 status buckets and formats the report."""
    cfg = load_gdt_config(root_dir=gdt_workspace)
    src_dir = gdt_workspace / "src" / "gda"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "subdir").mkdir(exist_ok=True)
    arch_dir = gdt_workspace / "archive" / "backups_gda" / "src" / "gda"
    arch_dir.mkdir(parents=True, exist_ok=True)
    (arch_dir / "not_a_file.bk").mkdir(exist_ok=True)

    base = datetime(2026, 11, 19, 12, 0, 0)

    # 1. BACKUP NEWER (backup 1h newer than live; older duplicate exercises comparison branch)
    f_newer = src_dir / "newer.py"
    f_newer.write_text("v1", encoding="utf-8")
    old_epoch = (base - timedelta(hours=1)).replace(tzinfo=UTC).timestamp()
    os.utime(f_newer, (old_epoch, old_epoch))
    (arch_dir / "newer.py.20261119_120000.bk").write_text("v2", encoding="utf-8")
    (arch_dir / "newer.py.20250101_100000.bk").write_text("v0", encoding="utf-8")

    # 2. NO BACKUP
    (src_dir / "unbacked.py").write_text("x", encoding="utf-8")

    # 3. BACK OKAY (live newer than backup)
    f_okay = src_dir / "okay.py"
    f_okay.write_text("v2", encoding="utf-8")
    now_epoch = (base + timedelta(minutes=5)).replace(tzinfo=UTC).timestamp()
    os.utime(f_okay, (now_epoch, now_epoch))
    (arch_dir / "okay.py.20261119_120000.bk").write_text("v1", encoding="utf-8")

    # 4. NO ORIGIN (backup exists with no timestamp -> st_mtime fallback, no live file)
    (arch_dir / "deleted.py.bk").write_text("old", encoding="utf-8")

    partitioned = audit_workspace(
        gdt_workspace, cfg, target_rel_path="src/gda", now=base + timedelta(minutes=10)
    )
    report = format_full_audit_report(partitioned)

    assert len(partitioned[AuditStatus.BACKUP_NEWER]) == 1
    assert len(partitioned[AuditStatus.NO_BACKUP]) == 1
    assert len(partitioned[AuditStatus.BACK_OKAY]) == 1
    assert len(partitioned[AuditStatus.NO_ORIGIN]) == 1
    assert "=== BACKUP NEWER (1) ===" in report
    assert "=== NO ORIGIN (1) ===" in report


# ==========================================================================
# GROUP 2: Formatting & Path Resolution Helpers
# Note: Age/delta formatting and archive-to-source path reconstruction.
# ==========================================================================


@pytest.mark.unit
def test_format_age_and_delta_minutes_variants() -> None:
    """Verify age and signed delta formatting across minutes, hours, days, and None."""
    now = datetime(2026, 11, 19, 12, 0, 0)
    assert format_age_from_now(None) == "-"
    assert format_age_from_now(now + timedelta(seconds=30), now) == "0m"
    assert format_age_from_now(now - timedelta(minutes=20), now) == "20m"
    assert format_age_from_now(now - timedelta(hours=3), now) == "3.0h"
    assert format_age_from_now(now - timedelta(days=2), now) == "2.0d"

    assert format_delta_minutes(None, now) == "-"
    assert format_delta_minutes(now, None) == "-"
    assert format_delta_minutes(now + timedelta(minutes=15), now) == "+15m"
    assert format_delta_minutes(now - timedelta(minutes=15), now) == "-15m"


@pytest.mark.unit
def test_resolve_original_path_handles_standard_migration_legacy_and_outside(
    tmp_path: Path,
) -> None:
    """Verify resolve_original_path strips bucket prefixes and handles outside paths."""
    arch = tmp_path / "archive"
    p_std = arch / "backups_gda" / "src" / "gda" / "a.py.20261119_120000.bk"
    p_mig = arch / "backups_migration" / "20261107_220718" / "schemas" / "c.json.20261107_220718.bk"
    p_leg = arch / "backups" / "src" / "gda" / "b.py.20261119_120000.bk"
    p_out = tmp_path / "other" / "x.py.20261119_120000.bk"

    assert resolve_original_path(p_std, arch).as_posix() == "src/gda/a.py"
    assert resolve_original_path(p_mig, arch).as_posix() == "schemas/c.json"
    assert resolve_original_path(p_leg, arch).as_posix() == "src/gda/b.py"
    assert resolve_original_path(p_out, arch).as_posix() == "x.py"


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Missing archive directory, empty sections, and target path filtering.
# ==========================================================================


@pytest.mark.regression
def test_audit_workspace_missing_archive_and_filter_exclusions(tmp_path: Path) -> None:
    """Verify missing archive/ and non-matching filter targets render empty sections."""
    src_dir = tmp_path / "src" / "gda"
    src_dir.mkdir(parents=True)
    (src_dir / "keep.py").write_text("x", encoding="utf-8")
    (src_dir / "skip.py").write_text("y", encoding="utf-8")
    arch_dir = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch_dir.mkdir(parents=True)
    (arch_dir / "skip.py.20261119_120000.bk").write_text("y", encoding="utf-8")

    # Missing archive branch
    empty_res = audit_workspace(tmp_path, {"workspace": {"archive_dir": "no_such_archive"}})
    assert "(none)" in format_full_audit_report(empty_res)

    # Filter excluding skip.py in both archive and live loops
    filtered = audit_workspace(
        tmp_path,
        {"workspace": {"archive_dir": "archive"}, "code_domains": {"protected_domains": ["src"]}},
        target_rel_path="src/gda/keep.py",
    )
    assert [r.original_rel_path for r in filtered[AuditStatus.NO_BACKUP]] == ["src/gda/keep.py"]
