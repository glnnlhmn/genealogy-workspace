"""Path: src/gen_desk_tools/backup_mgr/pruner.py

Safe Backup retention evaluator and snapshot pruning engine for GenDesk Backup Manager (gdb).

Operational Role:
    Evaluates historical Safe Backup snapshots (.bk) across the archive store
    and removes older versions exceeding retention.max_versions or
    retention.max_age_days.

Functions:
    find_prune_candidates: Identify snapshots violating configured retention limits.
    execute_prune: Delete prune candidates from disk and log outcomes.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, NamedTuple

from gen_desk_tools.backup_mgr.engine import parse_backup_filename

__version__ = "1.0.0+build.2"

__all__ = [
    "PruneCandidate",
    "execute_prune",
    "find_prune_candidates",
]


class PruneCandidate(NamedTuple):
    """Holds candidate snapshot details targeted for pruning."""

    path: Path
    original_name: str
    timestamp: datetime
    reason: str


def _group_archive_snapshots(archive_root: Path) -> dict[str, list[tuple[Path, datetime]]]:
    """Group archive .bk snapshots by parent directory and original filename."""
    snapshots_by_target: dict[str, list[tuple[Path, datetime]]] = {}
    for bk_file in archive_root.rglob("*.bk"):
        if not bk_file.is_file():
            continue
        orig_name, ts = parse_backup_filename(bk_file.name)
        if ts is None:
            ts = datetime.fromtimestamp(bk_file.stat().st_mtime)
        key = f"{bk_file.parent.as_posix()}::{orig_name}"
        snapshots_by_target.setdefault(key, []).append((bk_file, ts))
    return snapshots_by_target


def _evaluate_group_retention(
    orig_name: str,
    entries: list[tuple[Path, datetime]],
    *,
    max_versions: int,
    max_age_days: int,
    age_cutoff: datetime | None,
) -> list[PruneCandidate]:
    """Evaluate max_versions and max_age_days retention limits for one file group."""
    ordered = sorted(entries, key=lambda item: item[1], reverse=True)
    candidates: list[PruneCandidate] = []
    seen_paths: set[Path] = set()

    if max_versions > 0 and len(ordered) > max_versions:
        for path, ts in ordered[max_versions:]:
            seen_paths.add(path)
            candidates.append(
                PruneCandidate(
                    path=path,
                    original_name=orig_name,
                    timestamp=ts,
                    reason=f"Exceeds max_versions ({max_versions})",
                )
            )

    if age_cutoff is not None:
        for path, ts in ordered:
            if path in seen_paths or ts >= age_cutoff:
                continue
            seen_paths.add(path)
            candidates.append(
                PruneCandidate(
                    path=path,
                    original_name=orig_name,
                    timestamp=ts,
                    reason=f"Exceeds max_age_days ({max_age_days}d)",
                )
            )

    return candidates


def find_prune_candidates(
    archive_root: Path,
    cfg: dict[str, Any],
    *,
    now: datetime | None = None,
) -> list[PruneCandidate]:
    """Identify historical backup snapshots exceeding retention policies."""
    if not archive_root.is_dir():
        return []

    retention = cfg.get("retention", {})
    max_versions = int(retention.get("max_versions", 5))
    max_age_days = int(retention.get("max_age_days", 90))
    current = now or datetime.now()
    age_cutoff = current - timedelta(days=max_age_days) if max_age_days > 0 else None

    snapshots_by_target = _group_archive_snapshots(archive_root)
    prune_candidates: list[PruneCandidate] = []

    for key, entries in sorted(snapshots_by_target.items()):
        orig_name = key.split("::", 1)[1]
        prune_candidates.extend(
            _evaluate_group_retention(
                orig_name,
                entries,
                max_versions=max_versions,
                max_age_days=max_age_days,
                age_cutoff=age_cutoff,
            )
        )

    return prune_candidates


def execute_prune(
    archive_root: Path,
    cfg: dict[str, Any],
    *,
    logger: logging.Logger | None = None,
) -> list[PruneCandidate]:
    """Delete backup snapshots violating retention rules and return processed candidates."""
    candidates = find_prune_candidates(archive_root, cfg)
    for item in candidates:
        try:
            item.path.unlink(missing_ok=True)
            if logger:
                logger.info("PRUNED: %s (%s)", item.path.as_posix(), item.reason)
        except Exception as err:
            if logger:
                logger.error("PRUNE_FAILED: %s: %s", item.path.as_posix(), err)
    return candidates
