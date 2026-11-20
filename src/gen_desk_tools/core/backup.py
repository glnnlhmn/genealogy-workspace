"""Path: src/gen_desk_tools/core/backup.py

Atomic file writes, protected-domain checks, and Safe Backup routing primitives.

Operational Role:
    Ensures all GenDesk Tools filesystem mutations write through sibling temporary
    files with atomic os.replace swaps and route pre-write .bk snapshots into
    isolated archive/backups_<project>/ directories.

Functions:
    atomic_write_text: Write UTF-8 text atomically via a sibling temp file.
    atomic_copy: Copy a file atomically while preserving metadata.
    is_protected_domain: Check whether a workspace path sits under a protected domain.
    resolve_backup_dir: Resolve the mirrored archive backup directory for a file.
    create_safe_backup: Create a timestamped pre-write .bk snapshot of a file.
"""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from gen_desk_tools.core.workspace import to_posix_rel

__version__ = "1.0.0+build.1"

__all__ = [
    "atomic_copy",
    "atomic_write_text",
    "create_safe_backup",
    "is_protected_domain",
    "resolve_backup_dir",
]


def atomic_write_text(target: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically to target using LF line endings and a sibling temp file."""
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    tmp_path = Path(tmp_name)

    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as handle:
            handle.write(content)
        os.replace(tmp_path, target)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def atomic_copy(src: Path, dst: Path) -> None:
    """Copy src to dst atomically while preserving file metadata.

    Raises:
        FileNotFoundError: If src does not exist or is not a regular file.
    """
    if not src.is_file():
        raise FileNotFoundError(f"Source file does not exist: {src}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=dst.parent,
        prefix=f".{dst.name}.",
        suffix=".tmp",
    )
    os.close(fd)
    tmp_path = Path(tmp_name)

    try:
        shutil.copy2(src, tmp_path)
        os.replace(tmp_path, dst)
    except Exception:
        if tmp_path.exists():
            tmp_path.unlink()
        raise


def is_protected_domain(path: Path, root: Path, cfg: dict[str, Any]) -> bool:
    """Return True if path matches or is nested under a configured protected domain."""
    rel_posix = to_posix_rel(path, root)
    domains: list[str] = cfg.get("code_domains", {}).get("protected_domains", [])

    for domain in domains:
        normalized = domain.replace("\\", "/").strip("/")
        if rel_posix == normalized or rel_posix.startswith(f"{normalized}/"):
            return True

    return False


def resolve_backup_dir(target: Path, root: Path, cfg: dict[str, Any]) -> Path:
    """Resolve the mirrored archive backup directory for a workspace file.

    Matches the longest configured prefix in cfg['backup_routing'] (falling back
    to 'default') and mirrors the target's relative parent directory beneath it.
    """
    rel_posix = to_posix_rel(target, root)
    archive_rel: str = cfg.get("workspace", {}).get("archive_dir", "archive")
    routing: dict[str, str] = cfg.get("backup_routing", {})

    # --- Longest-Prefix Route Selection ---
    candidates = [
        (prefix.replace("\\", "/").strip("/"), bucket)
        for prefix, bucket in routing.items()
        if prefix != "default"
    ]
    candidates.sort(key=lambda item: len(item[0]), reverse=True)

    bucket_name = routing.get("default", "backups_gen_desk_tools")
    for prefix, bucket in candidates:
        if rel_posix == prefix or rel_posix.startswith(f"{prefix}/"):
            bucket_name = bucket
            break

    # --- Mirror Relative Parent Structure ---
    rel_parent = Path(rel_posix).parent
    return root.resolve() / archive_rel / bucket_name / rel_parent


def create_safe_backup(
    target: Path,
    root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
    *,
    dry_run: bool = False,
    timestamp: str | None = None,
) -> Path | None:
    """Create a timestamped atomic pre-write Safe Backup snapshot of target.

    Returns None without error when target does not yet exist on disk.

    Args:
        dry_run: Compute and return the planned snapshot path without writing.
        timestamp: Optional UTC timestamp override (YYYYMMDD_HHMMSS) for determinism.
    """
    if not target.is_file():
        return None

    backup_dir = resolve_backup_dir(target, root, cfg)
    stamp = timestamp or datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"{target.name}.{stamp}.bk"

    if dry_run:
        if logger is not None:
            logger.info("[DRY-RUN] Would create Safe Backup: %s", backup_path)
        return backup_path

    atomic_copy(target, backup_path)
    if logger is not None:
        logger.info("Created Safe Backup: %s", backup_path)
    return backup_path
