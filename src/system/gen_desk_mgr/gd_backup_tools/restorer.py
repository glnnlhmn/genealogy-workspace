"""Path: src/system/gen_desk_mgr/gd_backup_tools/restorer.py

Batch file restoration engine for digital archive backups.

Operational Role:
    Reads line-delimited target files from a text manifest, verifies code domain
    authorization, discovers the newest Safe Backup snapshot (.bk) across the
    archive store (with Git HEAD fallback), and atomically restores files.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, NamedTuple

from system.gen_desk_mgr.gd_backup_tools.engine import (
    is_in_code_domain,
    parse_backup_filename,
)

__version__ = "1.0.0+build.1"


class BackupCandidate(NamedTuple):
    """Encapsulates discovered backup candidate metadata."""

    path: Path
    timestamp: datetime


def parse_restore_list(manifest_path: Path) -> list[str]:
    """Parse text file containing line-delimited relative target paths.

    Args:
        manifest_path: Path to plain text file containing restore targets.

    Returns:
        list[str]: Filtered list of non-empty, stripped target paths.
    """
    if not manifest_path.is_file():
        return []

    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    targets: list[str] = []
    for line in lines:
        cleaned = line.strip()
        if cleaned and not cleaned.startswith("#"):
            targets.append(cleaned.replace("\\", "/"))
    return targets


def find_latest_archive_backup(
    target_rel_path: str,
    archive_root: Path,
) -> BackupCandidate | None:
    """Search archive store for the newest Safe Backup matching target filename.

    Args:
        target_rel_path: Canonical relative path of file to restore.
        archive_root: Archive directory root.

    Returns:
        BackupCandidate | None: Candidate snapshot or None if not found.
    """
    target = Path(target_rel_path)
    target_name = target.name

    if not archive_root.is_dir():
        return None

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
    """Attempt to restore target file directly from Git HEAD repository index.

    Args:
        target_path: Relative or absolute path to target file.
        root_dir: Repository workspace root.

    Returns:
        bool: True if git checkout succeeded, False otherwise.
    """
    try:
        res = subprocess.run(
            ["git", "checkout", "HEAD", "--", str(target_path)],
            cwd=str(root_dir),
            capture_output=True,
            text=True,
            check=False,
        )
        return res.returncode == 0
    except (FileNotFoundError, OSError):
        return False


def atomic_copy(source_path: Path, target_path: Path) -> None:
    """Atomically copy bytes from snapshot to target using temporary file.

    Args:
        source_path: Snapshot file path.
        target_path: Canonical destination file path.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path_str = tempfile.mkstemp(
        dir=target_path.parent,
        prefix=f".{target_path.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "wb") as dst, source_path.open("rb") as src:
            shutil.copyfileobj(src, dst)
        os.replace(tmp_path, target_path)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def restore_file_entry(
    rel_path: str,
    root_dir: Path,
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Restore a single relative file entry from archive or Git HEAD.

    Args:
        rel_path: Relative file path to restore.
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.
        logger: Optional logger instance.
        dry_run: If True, simulates restore without disk mutation.

    Returns:
        tuple[bool, str]: (Success boolean, diagnostic status message).
    """
    target = root_dir / Path(rel_path)
    posix_rel = target.resolve().relative_to(root_dir.resolve()).as_posix()

    if not is_in_code_domain(target, root_dir, cfg):
        msg = f"REJECTED (outside protected code domains): {posix_rel}"
        if logger:
            logger.warning(msg)
        return False, msg

    archive_dir_name = cfg.get("workspace", {}).get("archive_dir", "archive")
    archive_root = root_dir / archive_dir_name

    candidate = find_latest_archive_backup(posix_rel, archive_root)
    if candidate:
        ts_str = candidate.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        if dry_run:
            msg = f"[DRY-RUN] RESTORE_SIMULATED: {posix_rel} <- {candidate.path.name} ({ts_str})"
            if logger:
                logger.info(msg)
            return True, msg

        try:
            atomic_copy(candidate.path, target)
            msg = f"RESTORE_COMPLETED: {posix_rel} <- {candidate.path.name} ({ts_str})"
            if logger:
                logger.info(msg)
            return True, msg
        except Exception as err:
            msg = f"RESTORE_FAILED: {posix_rel}: {err}"
            if logger:
                logger.error(msg)
            return False, msg

    if restore_from_git(Path(posix_rel), root_dir):
        if dry_run:
            msg = f"[DRY-RUN] RESTORE_SIMULATED (Git HEAD): {posix_rel}"
            if logger:
                logger.info(msg)
            return True, msg
        msg = f"RESTORE_COMPLETED (Git HEAD): {posix_rel}"
        if logger:
            logger.info(msg)
        return True, msg

    msg = f"RESTORE_UNAVAILABLE (no backup or Git snapshot found): {posix_rel}"
    if logger:
        logger.warning(msg)
    return False, msg


def restore_batch_from_list(
    manifest_path: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> tuple[int, int, list[str]]:
    """Restore multiple files defined in a text manifest.

    Args:
        manifest_path: Path to text manifest.
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.
        logger: Optional logger instance.
        dry_run: If True, simulates restore operations.

    Returns:
        tuple[int, int, list[str]]: (Success count, failure count, list of status messages).
    """
    targets = parse_restore_list(manifest_path)
    if not targets:
        return 0, 0, ["Notice: Manifest file is empty or does not exist."]

    successes = 0
    failures = 0
    messages: list[str] = []

    for rel_path in targets:
        ok, msg = restore_file_entry(rel_path, root_dir, cfg, logger=logger, dry_run=dry_run)
        if ok:
            successes += 1
        else:
            failures += 1
        messages.append(msg)

    return successes, failures, messages
