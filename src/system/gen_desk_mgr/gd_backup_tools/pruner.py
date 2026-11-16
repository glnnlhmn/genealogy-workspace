"""Path: src/system/gen_desk_mgr/gd_backup_tools/pruner.py

Safe Backup retention evaluator and snapshot pruning engine.

Operational Role:
    Evaluates historical Safe Backup snapshots (.bk) across the archive store,
    pruning older versions when snapshot counts exceed max_versions or when
    snapshot timestamps exceed max_age_days.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple

from system.gen_desk_mgr.gd_backup_tools.engine import parse_backup_filename

__version__ = "1.0.0+build.2"


class PruneCandidate(NamedTuple):
    """Holds candidate snapshot details targeted for pruning."""

    path: Path
    original_name: str
    timestamp: datetime
    reason: str


def find_prune_candidates(
    archive_root: Path,
    cfg: dict[str, Any],
) -> list[PruneCandidate]:
    """Identify historical backup snapshots exceeding retention policies.

    Args:
        archive_root: Root archive directory path.
        cfg: Configuration dictionary carrying retention settings.

    Returns:
        list[PruneCandidate]: List of snapshot files meeting pruning criteria.
    """
    if not archive_root.is_dir():
        return []

    retention = cfg.get("retention", {})
    max_versions = retention.get("max_versions", 5)
    max_age_days = retention.get("max_age_days", 90)

    now = datetime.now()
    age_cutoff = now - timedelta(days=max_age_days) if max_age_days > 0 else None

    # Group snapshots by canonical parent directory + original filename
    snapshots_by_target: dict[str, list[tuple[Path, datetime]]] = {}

    for bk_file in archive_root.rglob("*.bk"):
        if not bk_file.is_file():
            continue

        orig_name, ts = parse_backup_filename(bk_file.name)
        if ts is None:
            ts = datetime.fromtimestamp(bk_file.stat().st_mtime)

        key = f"{bk_file.parent.as_posix()}::{orig_name}"
        snapshots_by_target.setdefault(key, []).append((bk_file, ts))

    prune_candidates: list[PruneCandidate] = []

    for key, entries in snapshots_by_target.items():
        # Sort newest snapshot first
        entries.sort(key=lambda item: item[1], reverse=True)
        orig_name = key.split("::", 1)[1]

        # 1. Version count retention
        if max_versions > 0 and len(entries) > max_versions:
            overflow = entries[max_versions:]
            for path, ts in overflow:
                prune_candidates.append(
                    PruneCandidate(
                        path=path,
                        original_name=orig_name,
                        timestamp=ts,
                        reason=f"Exceeds max_versions ({max_versions})",
                    )
                )

        # 2. Maximum age retention
        if age_cutoff is not None:
            for path, ts in entries:
                if any(c.path == path for c in prune_candidates):
                    continue
                if ts < age_cutoff:
                    prune_candidates.append(
                        PruneCandidate(
                            path=path,
                            original_name=orig_name,
                            timestamp=ts,
                            reason=f"Exceeds max_age_days ({max_age_days}d)",
                        )
                    )

    return prune_candidates


def execute_prune(
    archive_root: Path,
    cfg: dict[str, Any],
    logger: logging.Logger | None = None,
    dry_run: bool = False,
) -> list[PruneCandidate]:
    """Execute removal of backup snapshots violating retention rules.

    Args:
        archive_root: Archive directory root path.
        cfg: Configuration dictionary.
        logger: Optional logger instance.
        dry_run: If True, identifies candidates without disk deletion.

    Returns:
        list[PruneCandidate]: Candidates pruned (or simulated).
    """
    candidates = find_prune_candidates(archive_root, cfg)

    for item in candidates:
        if dry_run:
            if logger:
                logger.info(f"[DRY-RUN] PRUNE_SIMULATED: {item.path.as_posix()} ({item.reason})")
        else:
            try:
                item.path.unlink(missing_ok=True)
                if logger:
                    logger.info(f"PRUNED: {item.path.as_posix()} ({item.reason})")
            except Exception as err:
                if logger:
                    logger.error(f"PRUNE_FAILED: {item.path.as_posix()}: {err}")

    return candidates
