"""Path: src/system/gen_desk_mgr/gd_backup_tools/engine.py

Core Safe Backup creation engine and automated code domain scanner.

Operational Role:
    Generates atomic timestamped snapshots (.bk) for single files, folders,
    and folder trees within approved code domains. Executes automated backup scans
    detecting and snapshotting any protected files that lack current backups.
"""

from __future__ import annotations

import logging
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

__version__ = "1.0.0+build.12"

BK_PATTERN = re.compile(r"^(.*?)\.(\d{8}_\d{6})(?:_\d+)?\.bk$")


def parse_backup_filename(filename: str) -> tuple[str, datetime | None]:
    """Extract original filename and embedded timestamp from Safe Backup filename.

    Args:
        filename: Name of the candidate backup file.

    Returns:
        Tuple of (original_filename, parsed_datetime_or_None).
    """
    match = BK_PATTERN.match(filename)
    if not match:
        if filename.endswith(".bk"):
            return filename[:-3], None
        return filename, None

    orig_name, ts_str = match.group(1), match.group(2)
    try:
        ts = datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
        return orig_name, ts
    except ValueError:
        return orig_name, None


def is_in_code_domain(target_path: Path, root_dir: Path, cfg: dict[str, Any]) -> bool:
    """Verify that target file path falls strictly inside approved code_domains.

    Args:
        target_path: File path targeted for backup.
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.

    Returns:
        bool: True if file is inside an approved code domain; False otherwise.
    """
    try:
        rel_posix = target_path.resolve().relative_to(root_dir.resolve()).as_posix()
    except ValueError:
        return False

    protected = cfg.get("code_domains", {}).get(
        "protected_domains", ["src", "tests", "schemas", "data/setup"]
    )
    return any(rel_posix == p or rel_posix.startswith(f"{p}/") for p in protected)


def resolve_backup_destination(
    target_file: Path,
    root_dir: Path,
    cfg: dict[str, Any],
) -> Path:
    """Determine archive backup destination directory for a given target file.

    Args:
        target_file: File path targeted for backup.
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.

    Returns:
        Path: Archive directory destination.
    """
    rel_posix = target_file.resolve().relative_to(root_dir.resolve()).as_posix()
    routing = cfg.get("backup_routing", {})
    archive_dir_name = str(cfg.get("workspace", {}).get("archive_dir", "archive"))

    chosen_project: str | None = None
    for prefix, project in routing.items():
        if prefix != "default" and (rel_posix == prefix or rel_posix.startswith(f"{prefix}/")):
            chosen_project = str(project)
            break

    if not chosen_project:
        chosen_project = str(routing.get("default", "backups_system"))

    parent_rel = target_file.resolve().parent.relative_to(root_dir.resolve())
    return root_dir / archive_dir_name / chosen_project / parent_rel


def create_single_backup(
    target_file: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> Path | None:
    """Create atomic timestamped Safe Backup for a single file.

    Args:
        target_file: Canonical path to target file.
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.
        logger: Optional logger instance.
        dry_run: If True, simulates backup without disk mutation.

    Returns:
        Path to generated backup or None if bypassed/invalid.
    """
    target = target_file.resolve()
    if not target.is_file():
        return None

    if not is_in_code_domain(target, root_dir, cfg):
        return None

    dest_folder = resolve_backup_destination(target, root_dir, cfg)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{target.name}.{ts}"

    candidate = dest_folder / f"{base_name}.bk"
    counter = 1
    while candidate.exists():
        candidate = dest_folder / f"{base_name}_{counter}.bk"
        counter += 1

    if dry_run:
        if logger:
            logger.info(f"[DRY-RUN] BACKUP_SIMULATED: {candidate.relative_to(root_dir).as_posix()}")
        return candidate

    dest_folder.mkdir(parents=True, exist_ok=True)

    fd, tmp_path_str = tempfile.mkstemp(
        dir=dest_folder,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "wb") as dst, target.open("rb") as src:
            shutil.copyfileobj(src, dst)
        os.replace(tmp_path, candidate)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise

    if logger:
        logger.info(f"BACKUP_CREATED: {candidate.relative_to(root_dir).as_posix()}")

    return candidate


def backup_folder(
    folder_path: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    recursive: bool = True,
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Back up all files residing within a folder or folder tree.

    Args:
        folder_path: Target directory path.
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.
        recursive: If True, descends into subdirectories; otherwise single folder.
        logger: Optional logger instance.
        dry_run: If True, simulates operations.

    Returns:
        list[Path]: Discovered or created backup paths.
    """
    resolved_folder = folder_path.resolve()
    if not resolved_folder.is_dir():
        return []

    results: list[Path] = []
    iterator = resolved_folder.rglob("*") if recursive else resolved_folder.glob("*")

    for item in sorted(iterator):
        if item.is_file() and is_in_code_domain(item, root_dir, cfg):
            bk = create_single_backup(item, root_dir, cfg, logger=logger, dry_run=dry_run)
            if bk:
                results.append(bk)

    return results


def run_auto_backup(
    root_dir: Path,
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> list[Path]:
    """Scan all approved code domains and back up files lacking current snapshots.

    Args:
        root_dir: Workspace root directory.
        cfg: Configuration dictionary.
        logger: Optional logger instance.
        dry_run: If True, simulates operations.

    Returns:
        list[Path]: Discovered or generated backup paths.
    """
    protected_domains = cfg.get("code_domains", {}).get(
        "protected_domains", ["src", "tests", "schemas", "data/setup"]
    )
    archive_dir_name = cfg.get("workspace", {}).get("archive_dir", "archive")
    archive_root = root_dir / archive_dir_name

    latest_backups: dict[str, datetime] = {}
    if archive_root.is_dir():
        for bk_file in archive_root.rglob("*.bk"):
            if bk_file.is_file():
                orig_name, ts = parse_backup_filename(bk_file.name)
                if orig_name and ts:
                    if orig_name not in latest_backups or ts > latest_backups[orig_name]:
                        latest_backups[orig_name] = ts

    created_backups: list[Path] = []

    for domain in protected_domains:
        domain_dir = root_dir / domain
        if not domain_dir.is_dir():
            continue

        for file_path in sorted(domain_dir.rglob("*")):
            if not file_path.is_file():
                continue

            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            latest_ts = latest_backups.get(file_path.name)

            if latest_ts is None or file_mtime > latest_ts:
                bk = create_single_backup(file_path, root_dir, cfg, logger=logger, dry_run=dry_run)
                created_backups.append(bk)  # type: ignore[arg-type]

    return created_backups
