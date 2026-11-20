"""Path: src/gen_desk_tools/backup_mgr/restorer.py

Single-file and batch restoration engine for GenDesk Backup Manager (gdb).

Operational Role:
    Parses line-delimited restore manifests, verifies protected-domain
    authorization, discovers the newest archive Safe Backup snapshot (.bk)
    with Git HEAD fallback via gen_desk_tools.core.process.run_command, and
    atomically restores files via gen_desk_tools.core.backup.atomic_copy.

Functions:
    parse_restore_list: Parse a plain-text manifest of relative target paths.
    find_latest_archive_backup: Locate the newest .bk snapshot for a target file.
    restore_from_git: Attempt fallback restoration from Git HEAD.
    restore_file_entry: Restore a single protected-domain file from archive or Git.
    restore_batch_from_list: Restore all targets listed in a manifest file.
"""

from __future__ import annotations

import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple

from gen_desk_tools.backup_mgr.engine import parse_backup_filename
from gen_desk_tools.core.backup import atomic_copy, is_protected_domain
from gen_desk_tools.core.process import run_command
from gen_desk_tools.core.workspace import to_posix_rel

__version__ = "1.0.0+build.2"

__all__ = [
    "BackupCandidate",
    "find_latest_archive_backup",
    "parse_restore_list",
    "restore_batch_from_list",
    "restore_file_entry",
    "restore_from_git",
]


class BackupCandidate(NamedTuple):
    """Encapsulates discovered backup candidate metadata."""

    path: Path
    timestamp: datetime


def parse_restore_list(manifest_path: Path) -> list[str]:
    """Parse a text file containing line-delimited relative target paths."""
    if not manifest_path.is_file():
        return []

    targets: list[str] = []
    for line in manifest_path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#"):
            targets.append(cleaned.replace("\\", "/"))
    return targets


def find_latest_archive_backup(
    target_rel_path: str,
    archive_root: Path,
) -> BackupCandidate | None:
    """Search archive_root for the newest Safe Backup matching target_rel_path's filename."""
    if not archive_root.is_dir():
        return None

    target_name = Path(target_rel_path).name
    candidates: list[BackupCandidate] = []
    for bk_file in archive_root.rglob("*.bk"):
        if not bk_file.is_file():
            continue
        orig_name, ts = parse_backup_filename(bk_file.name)
        if orig_name == target_name:
            if ts is None:
                ts = datetime.fromtimestamp(bk_file.stat().st_mtime)
            candidates.append(BackupCandidate(path=bk_file, timestamp=ts))

    if not candidates:
        return None

    candidates.sort(key=lambda c: (c.timestamp, c.path.name), reverse=True)
    return candidates[0]


def restore_from_git(target_path: Path, root_dir: Path) -> bool:
    """Attempt to restore target_path directly from Git HEAD."""
    res = run_command(
        ["git", "checkout", "HEAD", "--", str(target_path)],
        cwd=root_dir,
        runner=subprocess.run,
    )
    return res.ok


def restore_file_entry(
    rel_path: str,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> tuple[bool, str]:
    """Restore a single protected-domain file from its newest archive backup or Git HEAD."""
    target = (root_dir / Path(rel_path)).resolve()
    try:
        posix_rel = to_posix_rel(target, root_dir)
    except ValueError:
        msg = f"REJECTED (outside workspace root): {rel_path}"
        if logger:
            logger.warning(msg)
        return False, msg

    if not is_protected_domain(target, root_dir, cfg):
        msg = f"REJECTED (outside protected code domains): {posix_rel}"
        if logger:
            logger.warning(msg)
        return False, msg

    archive_root = root_dir / str(cfg.get("workspace", {}).get("archive_dir", "archive"))
    candidate = find_latest_archive_backup(posix_rel, archive_root)

    if candidate is not None:
        atomic_copy(candidate.path, target)
        msg = f"RESTORED (archive): {posix_rel} <- {candidate.path.name}"
        if logger:
            logger.info(msg)
        return True, msg

    if restore_from_git(Path(posix_rel), root_dir):
        msg = f"RESTORED (git HEAD): {posix_rel}"
        if logger:
            logger.info(msg)
        return True, msg

    msg = f"FAILED (no archive backup or git HEAD entry): {posix_rel}"
    if logger:
        logger.error(msg)
    return False, msg


def restore_batch_from_list(
    manifest_path: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> tuple[int, int, list[str]]:
    """Restore all files listed in manifest_path and return (succeeded, failed, messages)."""
    targets = parse_restore_list(manifest_path)
    succeeded = 0
    failed = 0
    messages: list[str] = []

    for rel_path in targets:
        ok, msg = restore_file_entry(rel_path, root_dir, cfg, logger=logger)
        messages.append(msg)
        if ok:
            succeeded += 1
        else:
            failed += 1

    return succeeded, failed, messages
