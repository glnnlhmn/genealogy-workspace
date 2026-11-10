"""Path: src/system/gen_desk_mgr/gd_backup_tools/auditor.py

Comprehensive 4-section workspace archive audit engine.

Operational Role:
    Evaluates archive snapshots against live working tree files across four
    distinct status partitions (BACKUP NEWER, NO BACKUP, BACK OKAY, NO ORIGIN)
    and formats human-readable diagnostic tables.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, NamedTuple

from system.gen_desk_mgr.gd_backup_tools.engine import (
    parse_backup_filename,
)

__version__ = "1.0.0+build.8"

GRACE_DELTA_SECONDS = 60.0


class AuditStatus(StrEnum):
    """Categorical audit outcome invariant."""

    BACKUP_NEWER = "BACKUP NEWER"
    NO_BACKUP = "NO BACKUP"
    BACK_OKAY = "BACK OKAY"
    NO_ORIGIN = "NO ORIGIN"


class AuditRecord(NamedTuple):
    """Encapsulates drift assessment for an audited file."""

    status: AuditStatus
    original_rel_path: str
    backup_filename: str | None
    backup_timestamp: datetime | None
    live_timestamp: datetime | None
    age_str: str
    delta_str: str


# Backward compatibility alias for legacy imports
NewerBackupRecord = AuditRecord


def format_age_from_now(ts: datetime | None, now: datetime | None = None) -> str:
    """Format elapsed age from current time into readable units."""
    if ts is None:
        return "-"
    current = now or datetime.now(UTC).replace(tzinfo=None)
    diff_sec = int((current - ts).total_seconds())
    if diff_sec < 0:
        return "0m"
    mins = diff_sec // 60
    if mins < 60:
        return f"{mins}m"
    hours = mins / 60
    if hours < 24:
        return f"{hours:.1f}h"
    days = hours / 24
    return f"{days:.1f}d"


def format_delta_minutes(bk_ts: datetime | None, live_ts: datetime | None) -> str:
    """Calculate delta in minutes between backup and live file timestamps."""
    if bk_ts is None or live_ts is None:
        return "-"
    diff_mins = int((bk_ts - live_ts).total_seconds() / 60)
    if diff_mins > 0:
        return f"+{diff_mins}m"
    return f"{diff_mins}m"


def resolve_original_path(bk_file: Path, archive_root: Path) -> Path:
    """Reconstruct canonical relative path of original file from backup file path."""
    orig_name, _ = parse_backup_filename(bk_file.name)
    try:
        rel_to_archive = bk_file.parent.relative_to(archive_root)
    except ValueError:
        return Path(orig_name)

    parts = list(rel_to_archive.parts)
    cleaned_parts: list[str] = []
    skip_next = False
    for i, p in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
        if p.startswith("backups_"):
            if i + 1 < len(parts) and re.match(r"^\d{8}_\d{6}$", parts[i + 1]):
                skip_next = True
            continue
        if p == "backups":
            continue
        cleaned_parts.append(p)

    return Path(*cleaned_parts) / orig_name


def audit_workspace(
    workspace_root: Path | str,
    cfg: dict[str, Any],
    target_rel_path: str | None = None,
    now: datetime | None = None,
) -> dict[AuditStatus, list[AuditRecord]]:
    """Scan archive and workspace files, partitioning records into 4 status sections."""
    root = Path(workspace_root).resolve()
    archive_dir_name = cfg.get("workspace", {}).get("archive_dir", "archive")
    archive_root = root / archive_dir_name
    current_time = now or datetime.now(UTC).replace(tzinfo=None)

    target_filter = Path(target_rel_path).as_posix().strip("/") if target_rel_path else None

    # 1. Index newest archive backups by canonical relative path (descending sort prioritizes newer)
    newest_backups: dict[str, tuple[Path, datetime]] = {}
    if archive_root.is_dir():
        for bk_path in sorted(archive_root.rglob("*.bk"), reverse=True):
            if not bk_path.is_file():
                continue
            orig_rel = resolve_original_path(bk_path, archive_root)
            orig_posix = orig_rel.as_posix()

            if target_filter:
                if not (orig_posix == target_filter or orig_posix.startswith(f"{target_filter}/")):
                    continue

            _, ts = parse_backup_filename(bk_path.name)
            if ts is None:
                ts = datetime.fromtimestamp(bk_path.stat().st_mtime, tz=UTC).replace(tzinfo=None)

            if orig_posix not in newest_backups or ts > newest_backups[orig_posix][1]:
                newest_backups[orig_posix] = (bk_path, ts)

    # 2. Index active files on disk in protected code domains
    protected_domains = cfg.get("code_domains", {}).get(
        "protected_domains", ["src", "tests", "schemas", "data/setup"]
    )
    live_files: dict[str, datetime] = {}
    for domain in protected_domains:
        domain_dir = root / domain
        if not domain_dir.is_dir():
            continue
        for f in domain_dir.rglob("*"):
            if not f.is_file():
                continue
            posix_rel = f.relative_to(root).as_posix()
            if target_filter:
                if not (posix_rel == target_filter or posix_rel.startswith(f"{target_filter}/")):
                    continue
            live_files[posix_rel] = datetime.fromtimestamp(f.stat().st_mtime, tz=UTC).replace(
                tzinfo=None
            )

    # 3. Categorize into 4 sections
    all_keys = sorted(set(newest_backups.keys()) | set(live_files.keys()))
    partitioned: dict[AuditStatus, list[AuditRecord]] = {
        AuditStatus.BACKUP_NEWER: [],
        AuditStatus.NO_BACKUP: [],
        AuditStatus.BACK_OKAY: [],
        AuditStatus.NO_ORIGIN: [],
    }

    for rel_path in all_keys:
        has_live = rel_path in live_files
        has_bk = rel_path in newest_backups

        live_mtime = live_files.get(rel_path)
        bk_path, bk_ts = newest_backups[rel_path] if has_bk else (None, None)
        bk_filename = bk_path.name if bk_path else None

        age_str = format_age_from_now(bk_ts, current_time)
        delta_str = format_delta_minutes(bk_ts, live_mtime)

        if has_live and not has_bk:
            rec = AuditRecord(
                status=AuditStatus.NO_BACKUP,
                original_rel_path=rel_path,
                backup_filename=None,
                backup_timestamp=None,
                live_timestamp=live_mtime,
                age_str="-",
                delta_str="-",
            )
            partitioned[AuditStatus.NO_BACKUP].append(rec)
        elif not has_live:
            rec = AuditRecord(
                status=AuditStatus.NO_ORIGIN,
                original_rel_path=rel_path,
                backup_filename=bk_filename,
                backup_timestamp=bk_ts,
                live_timestamp=None,
                age_str=age_str,
                delta_str="-",
            )
            partitioned[AuditStatus.NO_ORIGIN].append(rec)
        else:
            # Both live and backup exist: apply grace epsilon for sub-minute GSI intake jitter
            is_newer = (
                bk_ts is not None
                and live_mtime is not None
                and (bk_ts - live_mtime).total_seconds() >= GRACE_DELTA_SECONDS
            )
            if is_newer:
                rec = AuditRecord(
                    status=AuditStatus.BACKUP_NEWER,
                    original_rel_path=rel_path,
                    backup_filename=bk_filename,
                    backup_timestamp=bk_ts,
                    live_timestamp=live_mtime,
                    age_str=age_str,
                    delta_str=delta_str,
                )
                partitioned[AuditStatus.BACKUP_NEWER].append(rec)
            else:
                rec = AuditRecord(
                    status=AuditStatus.BACK_OKAY,
                    original_rel_path=rel_path,
                    backup_filename=bk_filename,
                    backup_timestamp=bk_ts,
                    live_timestamp=live_mtime,
                    age_str=age_str,
                    delta_str=delta_str,
                )
                partitioned[AuditStatus.BACK_OKAY].append(rec)

    return partitioned


def format_section_table(status: AuditStatus, records: list[AuditRecord]) -> str:
    """Format single section table using specified headers."""
    lines: list[str] = [
        f"=== SECTION: {status.value} (Count: {len(records)}) ===",
        f"{'Live status':<14} | {'Original w/Path':<50} | {'Backup':<38} | {'Age of backup':<13} | {'Backup Delta (mins)'}",
        "-" * 135,
    ]
    if not records:
        lines.append("  (No files in this category)")
    else:
        for r in records:
            bk_display = r.backup_filename if r.backup_filename else "-"
            lines.append(
                f"{r.status.value:<14} | {r.original_rel_path:<50} | {bk_display:<38} | {r.age_str:<13} | {r.delta_str}"
            )
    return "\n".join(lines)


def format_full_audit_report(partitioned: dict[AuditStatus, list[AuditRecord]]) -> str:
    """Render 4-section audit report string."""
    sections = [
        AuditStatus.BACKUP_NEWER,
        AuditStatus.NO_BACKUP,
        AuditStatus.BACK_OKAY,
        AuditStatus.NO_ORIGIN,
    ]
    report_blocks = [format_section_table(s, partitioned.get(s, [])) for s in sections]
    total_files = sum(len(records) for records in partitioned.values())
    report_blocks.append("-" * 135)
    report_blocks.append(f"Total files audited across workspace: {total_files}")
    return "\n\n".join(report_blocks)


def find_newer_backups(
    workspace_root: Path | str = ".",
    target_rel_path: str | None = None,
    archive_dir_name: str = "archive",
) -> list[AuditRecord]:
    """Compatibility wrapper returning newer/missing records."""
    cfg = {"workspace": {"archive_dir": archive_dir_name}}
    partitioned = audit_workspace(workspace_root, cfg, target_rel_path=target_rel_path)
    return partitioned[AuditStatus.BACKUP_NEWER] + partitioned[AuditStatus.NO_ORIGIN]


def format_audit_table(records: list[AuditRecord]) -> str:
    """Compatibility wrapper rendering standard table."""
    return format_section_table(AuditStatus.BACKUP_NEWER, records)
