"""Path: tests/test_system/test_gen_desk_mgr/test_auditor.py

Unit and integration test suite for the 4-section workspace audit engine.

Operational Role:
    Verifies original path resolution, status partitioning (BACKUP NEWER,
    NO BACKUP, BACK OKAY, NO ORIGIN), delta calculations, age formatting,
    compatibility wrappers, and report table generation achieving 100% coverage.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from system.gen_desk_mgr.gd_backup_tools.auditor import (
    AuditRecord,
    AuditStatus,
    NewerBackupRecord,
    audit_workspace,
    find_newer_backups,
    format_age_from_now,
    format_audit_table,
    format_delta_minutes,
    format_full_audit_report,
    resolve_original_path,
)
from system.gen_desk_mgr.gd_backup_tools.config import load_config

__version__ = "1.0.0+build.8"

# ==============================================================================
# GROUP 1: Path Resolution & Formatting Utilities
# Note: Verification of resolve_original_path, format_age_from_now, format_delta_minutes
# ==============================================================================


@pytest.mark.unit
def test_resolve_original_path_standard_migration_and_legacy(tmp_path: Path) -> None:
    """Verify path normalization across standard, migration, legacy 'backups', and fallback paths."""
    arch = tmp_path / "archive"
    bk = arch / "backups_gda" / "src" / "gda" / "test.py.20261109_120000.bk"
    orig = resolve_original_path(bk, arch)
    assert orig.as_posix() == "src/gda/test.py"

    bk_mig = (
        arch / "backups_migration" / "20261107_220718" / "schemas" / "core.json.20261107_220718.bk"
    )
    orig_mig = resolve_original_path(bk_mig, arch)
    assert orig_mig.as_posix() == "schemas/core.json"

    bk_legacy = arch / "backups" / "src" / "gda" / "legacy.py.20261109_120000.bk"
    orig_legacy = resolve_original_path(bk_legacy, arch)
    assert orig_legacy.as_posix() == "src/gda/legacy.py"

    fallback_bk = Path("/unrelated/file.py.20260101_000000.bk")
    orig_fb = resolve_original_path(fallback_bk, Path("/other/root"))
    assert orig_fb.name == "file.py"


@pytest.mark.unit
def test_format_age_and_delta() -> None:
    """Verify age rendering (minutes, hours, days) and delta signed minute strings."""
    assert format_age_from_now(None) == "-"
    now = datetime(2026, 11, 9, 12, 0, 0)
    assert format_age_from_now(now - timedelta(seconds=-10), now) == "0m"
    assert format_age_from_now(now - timedelta(minutes=25), now) == "25m"
    assert format_age_from_now(now - timedelta(hours=3), now) == "3.0h"
    assert format_age_from_now(now - timedelta(days=2), now) == "2.0d"

    assert format_delta_minutes(None, now) == "-"
    assert format_delta_minutes(now, None) == "-"
    bk_ts = now + timedelta(minutes=15)
    live_ts = now
    assert format_delta_minutes(bk_ts, live_ts) == "+15m"
    assert format_delta_minutes(live_ts, bk_ts) == "-15m"


# ==============================================================================
# GROUP 2: Workspace Audit Partitioning & Branch Coverage
# Note: Verification of the four mandatory status sections, missing archive, and older backups
# ==============================================================================


@pytest.mark.unit
def test_audit_workspace_missing_archive_dir(tmp_path: Path) -> None:
    """Verify branch 125->146 when archive directory does not exist on disk."""
    cfg = {"workspace": {"archive_dir": "missing_archive"}}
    partitioned = audit_workspace(tmp_path, cfg)
    assert sum(len(recs) for recs in partitioned.values()) == 0


@pytest.mark.integration
def test_audit_workspace_all_four_sections_and_branches(tmp_path: Path) -> None:
    """Verify audit_workspace partitions into all 4 sections and closes all loop branches."""
    cfg = load_config()

    src_dir = tmp_path / "src" / "gda"
    src_dir.mkdir(parents=True)
    arch_dir = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch_dir.mkdir(parents=True)
    (arch_dir / "not_a_file.bk").mkdir()

    base_time = datetime(2026, 11, 9, 12, 0, 0)

    # 1. Section 1: BACKUP NEWER (Live exists, backup newer by >= 60s)
    # Using explicit UTC tzinfo to eliminate local/UTC timezone drift
    f_newer = src_dir / "newer.py"
    f_newer.write_text("v1", encoding="utf-8")
    past_epoch = (base_time - timedelta(hours=1)).replace(tzinfo=UTC).timestamp()
    os.utime(f_newer, (past_epoch, past_epoch))
    (arch_dir / "newer.py.20261109_120000.bk").write_text("v2", encoding="utf-8")

    # Co-locate an older snapshot in the exact same directory (reverse sort guarantees it is evaluated 2nd, taking 142->126)
    (arch_dir / "newer.py.20250101_100000.bk").write_text("v0", encoding="utf-8")

    # Line 140: Snapshot with unparseable timestamp to test st_mtime fallback
    (arch_dir / "plain.bk").write_text("legacy_plain", encoding="utf-8")

    # 2. Section 2: NO BACKUP (Live exists, zero backups)
    f_nobk = src_dir / "nobackup.py"
    f_nobk.write_text("unbacked", encoding="utf-8")

    # Sibling file in live directory to exercise filter bypass branch
    f_other = src_dir / "other.py"
    f_other.write_text("other", encoding="utf-8")

    # 3. Section 3: BACK OKAY (Live exists, backup older or equal or within grace window)
    f_okay = src_dir / "okay.py"
    f_okay.write_text("v2", encoding="utf-8")
    future_epoch = (base_time + timedelta(hours=1)).replace(tzinfo=UTC).timestamp()
    os.utime(f_okay, (future_epoch, future_epoch))
    (arch_dir / "okay.py.20261109_120000.bk").write_text("v1", encoding="utf-8")

    # Sub-minute epsilon grace window: backup newer by only 30s (< 60s) -> classified as BACK OKAY
    f_grace = src_dir / "grace.py"
    f_grace.write_text("grace", encoding="utf-8")
    grace_epoch = (base_time - timedelta(seconds=30)).replace(tzinfo=UTC).timestamp()
    os.utime(f_grace, (grace_epoch, grace_epoch))
    (arch_dir / "grace.py.20261109_120000.bk").write_text("grace_bk", encoding="utf-8")

    # 4. Section 4: NO ORIGIN (Backup exists, live deleted)
    (arch_dir / "abandoned.py.20261109_120000.bk").write_text("v_old", encoding="utf-8")

    # Execute audit
    partitioned = audit_workspace(tmp_path, cfg, now=base_time)

    assert len(partitioned[AuditStatus.BACKUP_NEWER]) == 1
    assert partitioned[AuditStatus.BACKUP_NEWER][0].original_rel_path == "src/gda/newer.py"
    assert partitioned[AuditStatus.BACKUP_NEWER][0].backup_filename == "newer.py.20261109_120000.bk"

    assert len(partitioned[AuditStatus.NO_BACKUP]) == 2
    paths_nobk = [r.original_rel_path for r in partitioned[AuditStatus.NO_BACKUP]]
    assert "src/gda/nobackup.py" in paths_nobk
    assert "src/gda/other.py" in paths_nobk

    assert len(partitioned[AuditStatus.BACK_OKAY]) == 2
    paths_okay = [r.original_rel_path for r in partitioned[AuditStatus.BACK_OKAY]]
    assert "src/gda/okay.py" in paths_okay
    assert "src/gda/grace.py" in paths_okay

    assert len(partitioned[AuditStatus.NO_ORIGIN]) >= 1
    assert any(
        r.original_rel_path == "src/gda/abandoned.py" for r in partitioned[AuditStatus.NO_ORIGIN]
    )

    # Filtered audit: target matching newer.py while other files are skipped in loop
    filtered = audit_workspace(tmp_path, cfg, target_rel_path="src/gda/newer.py", now=base_time)
    assert len(filtered[AuditStatus.BACKUP_NEWER]) == 1
    assert len(filtered[AuditStatus.NO_BACKUP]) == 0


# ==============================================================================
# GROUP 3: Report Formatting & Compatibility Wrappers
# Note: Verification of format_full_audit_report and find_newer_backups
# ==============================================================================


@pytest.mark.unit
def test_format_full_audit_report_rendering() -> None:
    """Verify rendering of 4-section tables and total summaries."""
    rec = AuditRecord(
        status=AuditStatus.BACKUP_NEWER,
        original_rel_path="src/gda/core/config.py",
        backup_filename="config.py.20261109_120000.bk",
        backup_timestamp=datetime(2026, 11, 9, 12, 0, 0),
        live_timestamp=datetime(2026, 11, 9, 11, 0, 0),
        age_str="1.0h",
        delta_str="+60m",
    )
    partitioned = {
        AuditStatus.BACKUP_NEWER: [rec],
        AuditStatus.NO_BACKUP: [],
        AuditStatus.BACK_OKAY: [],
        AuditStatus.NO_ORIGIN: [],
    }

    report = format_full_audit_report(partitioned)
    assert "=== SECTION: BACKUP NEWER (Count: 1) ===" in report
    assert "=== SECTION: NO BACKUP (Count: 0) ===" in report
    assert "Live status    | Original w/Path" in report
    assert "config.py.20261109_120000.bk" in report
    assert "+60m" in report
    assert "Total files audited across workspace: 1" in report


@pytest.mark.integration
def test_compatibility_wrappers(tmp_path: Path) -> None:
    """Verify find_newer_backups and format_audit_table compatibility wrappers."""
    assert NewerBackupRecord is AuditRecord
    arch = tmp_path / "archive" / "backups_gda" / "src" / "gda"
    arch.mkdir(parents=True)
    (arch / "missing.py.20261109_120000.bk").write_text("data", encoding="utf-8")

    records = find_newer_backups(workspace_root=tmp_path)
    assert len(records) >= 1

    table = format_audit_table(records)
    assert "SECTION: BACKUP NEWER" in table
