"""Path: src/gen_desk_tools/backup_mgr/engine.py

Safe Backup creation engine and automated code-domain scanner for GenDesk Backup Manager (gdb).

Operational Role:
    Parses timestamped Safe Backup filenames and creates atomic snapshots (.bk)
    for single files, directory trees, and automated protected-domain scans
    delegating routing and atomic copy primitives to gen_desk_tools.core.backup.

Functions:
    parse_backup_filename: Extract original filename and UTC/local timestamp from a .bk name.
    create_single_backup: Create an atomic Safe Backup for a single protected-domain file.
    backup_folder: Back up all protected-domain files in a directory (recursive or flat).
    run_auto_backup: Snapshot all protected-domain files currently lacking a backup.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from gen_desk_tools.core.backup import create_safe_backup, is_protected_domain
from gen_desk_tools.core.workspace import to_posix_rel

__version__ = "1.0.0+build.1"

__all__ = [
    "BK_PATTERN",
    "backup_folder",
    "create_single_backup",
    "parse_backup_filename",
    "run_auto_backup",
]

BK_PATTERN = re.compile(r"^(.*?)\.(\d{8}_\d{6})(?:_\d+)?\.bk$")


def parse_backup_filename(filename: str) -> tuple[str, datetime | None]:
    """Extract original filename and embedded timestamp from a Safe Backup filename."""
    match = BK_PATTERN.match(filename)
    if not match:
        if filename.endswith(".bk"):
            return filename[:-3], None
        return filename, None

    orig_name, ts_str = match.group(1), match.group(2)
    try:
        return orig_name, datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
    except ValueError:
        return orig_name, None


def create_single_backup(
    target_file: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> Path | None:
    """Create an atomic Safe Backup for a single file inside a protected code domain."""
    target = target_file.resolve()
    if not target.is_file():
        return None
    if not is_protected_domain(target, root_dir, cfg):
        return None
    return create_safe_backup(target, root_dir, cfg, logger=logger)


def backup_folder(
    target_dir: Path,
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    recursive: bool = True,
    logger: logging.Logger | None = None,
) -> list[Path]:
    """Back up all protected-domain files within target_dir."""
    folder = target_dir.resolve()
    if not folder.is_dir():
        return []

    iterator = folder.rglob("*") if recursive else folder.iterdir()
    created: list[Path] = []
    for item in sorted(iterator):
        if not item.is_file():
            continue
        bk = create_single_backup(item, root_dir, cfg, logger=logger)
        if bk is not None:
            created.append(bk)
    return created


def run_auto_backup(
    root_dir: Path,
    cfg: dict[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> list[Path]:
    """Scan all protected domains and back up files that currently have no archive snapshot."""
    archive_dir_name = str(cfg.get("workspace", {}).get("archive_dir", "archive"))
    archive_root = root_dir / archive_dir_name

    # Index existing backup base filenames by relative parent directory
    existing_names: set[str] = set()
    if archive_root.is_dir():
        for bk_file in archive_root.rglob("*.bk"):
            if bk_file.is_file():
                orig_name, _ = parse_backup_filename(bk_file.name)
                existing_names.add(orig_name)

    protected = cfg.get("code_domains", {}).get(
        "protected_domains", ["src", "tests", "schemas", "data/setup"]
    )
    created: list[Path] = []
    for domain in protected:
        domain_dir = root_dir / domain
        if not domain_dir.is_dir():
            continue
        for live_file in sorted(domain_dir.rglob("*")):
            if not live_file.is_file():
                continue
            if live_file.name in existing_names:
                continue
            bk = create_single_backup(live_file, root_dir, cfg, logger=logger)
            if bk is not None:
                created.append(bk)
                if logger:
                    logger.info("AUTO_BACKUP: %s", to_posix_rel(live_file, root_dir))
    return created
