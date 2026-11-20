"""Path: src/gen_desk_tools/backup_mgr/auditor.py

Four-section workspace archive status and audit engine for GenDesk Backup Manager (gdb).

Operational Role:
    Compares archive Safe Backup snapshots (.bk) against live working-tree files
    across protected domains, partitioning results into BACKUP NEWER, NO BACKUP,
    BACK OKAY, and NO ORIGIN, and rendering formatted diagnostic tables.

Functions:
    resolve_original_path: Reconstruct canonical relative path from an archive .bk path.
    audit_workspace: Partition workspace and archive state into the 4 audit sections.
    format_section_table: Render a single audit section as an aligned ASCII table.
    format_full_audit_report: Render the complete 4-section status report.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, NamedTuple

from gen_desk_tools.backup_mgr.engine import parse_backup_filename
from gen_desk_tools.core.workspace import to_posix_rel

__version__ = "1.0.0+build.1"

__all__ = [
    "GRACE_DELTA_SECONDS",
    "AuditRecord",
    "AuditStatus",
    "audit_workspace",
    "format_age_from_now",
    "format_delta_minutes",
    "format_full_audit_report",
    "format_section_table",
    "resolve_original_path",
]

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
    return f"{hours / 24:.1f}d"


def format_delta_minutes(bk_ts: datetime | None, live_ts: datetime | None) -> str:
    """Calculate signed delta in minutes between backup and live file timestamps."""
    if bk_ts is None or live_ts is None:
        return "-"
    diff_mins = int((bk_ts - live_ts).total_seconds() / 60)
    return f"+{diff_mins}m" if diff_mins > 0 else f"{diff_mins}m"


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
    for i, part in enumerate(parts):
        if skip_next:
            skip_next = False
            continue
        if part.startswith("backups_"):
            if i + 1 < len(parts) and re.match(r"^\d{8}_\d{6}$", parts[i + 1]):
                skip_next = True
            continue
        if part == "backups":
            continue
        cleaned_parts.append(part)

    return Path(*cleaned_parts) / orig_name


def _matches_filter(posix_path: str, target_filter: str | None) -> bool:
    """Return True when target_filter is None or matches posix_path."""
    if not target_filter:
        return True
    return posix_path == target_filter or posix_path.startswith(f"{target_filter}/")


def audit_workspace(
    workspace_root: Path | str,
    cfg: dict[str, Any],
    *,
    target_rel_path: str | None = None,
    now: datetime | None = None,
) -> dict[AuditStatus, list[AuditRecord]]:
    """Scan archive and protected domains, partitioning records into 4 status sections."""
    root = Path(workspace_root).resolve()
    archive_root = root / str(cfg.get("workspace", {}).get("archive_dir", "archive"))
    current_time = now or datetime.now(UTC).replace(tzinfo=None)
    target_filter = Path(target_rel_path).as_posix().strip("/") if target_rel_path else None

    # 1. Index newest archive backups by canonical relative path
    newest_backups: dict[str, tuple[Path, datetime]] = {}
    if archive_root.is_dir():
        for bk_path in sorted(archive_root.rglob("*.bk"), reverse=True):
            if not bk_path.is_file():
                continue
            orig_posix = resolve_original_path(bk_path, archive_root).as_posix()
            if not _matches_filter(orig_posix, target_filter):
                continue

            _, ts = parse_backup_filename(bk_path.name)
            if ts is None:
                ts = datetime.fromtimestamp(bk_path.stat().st_mtime, tz=UTC).replace(tzinfo=None)
            if orig_posix not in newest_backups or ts > newest_backups[orig_posix][1]:
                newest_backups[orig_posix] = (bk_path, ts)

    # 2. Index active files on disk in protected code domains
    protected = cfg.get("code_domains", {}).get(
        "protected_domains", ["src", "tests", "schemas", "data/setup"]
    )
    live_files: dict[str, datetime] = {}
    for domain in protected:
        domain_dir = root / domain
        if not domain_dir.is_dir():
            continue
        for item in domain_dir.rglob("*"):
            if not item.is_file():
                continue
            posix_rel = to_posix_rel(item, root)
            if not _matches_filter(posix_rel, target_filter):
                continue
            live_files[posix_rel] = datetime.fromtimestamp(item.stat().st_mtime, tz=UTC).replace(
                tzinfo=None
            )

    # 3. Partition union of live and backed-up paths into 4 status buckets
    partitioned: dict[AuditStatus, list[AuditRecord]] = {status: [] for status in AuditStatus}
    for rel_path in sorted(set(live_files) | set(newest_backups)):
        live_ts = live_files.get(rel_path)
        bk_entry = newest_backups.get(rel_path)
        bk_name = bk_entry[0].name if bk_entry else None
        bk_ts = bk_entry[1] if bk_entry else None

        if live_ts is not None and bk_ts is None:
            status = AuditStatus.NO_BACKUP
        elif live_ts is None and bk_ts is not None:
            status = AuditStatus.NO_ORIGIN
        elif bk_ts is not None and live_ts is not None:
            delta_sec = (bk_ts - live_ts).total_seconds()
            status = (
                AuditStatus.BACKUP_NEWER
                if delta_sec >= GRACE_DELTA_SECONDS
                else AuditStatus.BACK_OKAY
            )
        else:  # pragma: no cover - unreachable given union of non-empty dicts
            continue

        partitioned[status].append(
            AuditRecord(
                status=status,
                original_rel_path=rel_path,
                backup_filename=bk_name,
                backup_timestamp=bk_ts,
                live_timestamp=live_ts,
                age_str=format_age_from_now(bk_ts, current_time),
                delta_str=format_delta_minutes(bk_ts, live_ts),
            )
        )

    return partitioned


def format_section_table(status: AuditStatus, records: list[AuditRecord]) -> str:
    """Format a single audit status section as an aligned ASCII table."""
    lines = [f"=== {status.value} ({len(records)}) ==="]
    if not records:
        lines.append("  (none)")
        return "\n".join(lines)

    path_w = max(len("File"), *(len(r.original_rel_path) for r in records))
    bk_w = max(len("Latest Backup"), *(len(r.backup_filename or "-") for r in records))
    header = f"  {'File':<{path_w}}  {'Latest Backup':<{bk_w}}  {'Age':>6}  {'Delta':>7}"
    lines.append(header)
    lines.append(f"  {'-' * path_w}  {'-' * bk_w}  {'-' * 6}  {'-' * 7}")
    for rec in records:
        bk_label = rec.backup_filename or "-"
        lines.append(
            f"  {rec.original_rel_path:<{path_w}}  {bk_label:<{bk_w}}  "
            f"{rec.age_str:>6}  {rec.delta_str:>7}"
        )
    return "\n".join(lines)


def format_full_audit_report(partitioned: dict[AuditStatus, list[AuditRecord]]) -> str:
    """Render all four audit sections into a single consolidated report."""
    sections = [format_section_table(status, partitioned.get(status, [])) for status in AuditStatus]
    return "\n\n".join(sections)
