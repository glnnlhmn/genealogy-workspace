"""Path: src/gen_desk_tools/metrics/collectors/radon_collector.py

Radon static metrics collector (raw, cyclomatic complexity, maintainability).

Operational Role:
    Discovers Python modules per configured audit batch, computes per-file
    Radon raw line counts, maintainability index (MI), cyclomatic complexity
    (CC), and Grade C+ complexity hotspots (CC >= 11), and aggregates
    batch-level rollups for telemetry reporting with 4-tier diagnostic logging.

Classes:
    ComplexityHotspot: Code block with cyclomatic complexity >= 11 (Grade C+).
    FileRadonMetrics: Per-module Radon raw, MI, and CC telemetry snapshot.
    BatchRadonRollup: Aggregated Radon totals and averages for one batch.

Functions:
    discover_batch_files: Return sorted, deduplicated Python files in a batch.
    analyze_file_radon: Compute Radon raw, MI, and CC metrics for one module.
    collect_radon_metrics: Run Radon analysis across all selected batches.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit
from radon.raw import analyze

from gen_desk_tools.core.logging import VERBOSE
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.5"

__all__ = [
    "BatchRadonRollup",
    "ComplexityHotspot",
    "FileRadonMetrics",
    "analyze_file_radon",
    "collect_radon_metrics",
    "discover_batch_files",
]

logger = logging.getLogger(__name__)

COMPLEXITY_HOTSPOT_THRESHOLD = 11


@dataclass(frozen=True)
class ComplexityHotspot:
    """Single code block whose cyclomatic complexity is Grade C or lower."""

    batch_id: str
    file_path: str
    lineno: int
    kind: str
    symbol: str
    complexity: int
    grade: str


@dataclass(frozen=True)
class FileRadonMetrics:
    """Per-module Radon raw, maintainability, and complexity metrics."""

    batch_id: str
    file_path: str
    loc: int
    lloc: int
    sloc: int
    blank: int
    comments: int
    docstrings: int
    doc_pct: float
    mi_score: float
    mi_grade: str
    avg_cc: float
    max_cc: int
    max_cc_grade: str
    max_cc_symbol: str
    cc_c_plus_count: int
    hotspots: tuple[ComplexityHotspot, ...]


@dataclass(frozen=True)
class BatchRadonRollup:
    """Aggregated Radon metrics for a single configured audit batch."""

    batch_id: str
    scope: str
    tier: str
    file_count: int
    loc: int
    lloc: int
    sloc: int
    blank: int
    comments: int
    docstrings: int
    doc_pct: float
    avg_cc: float
    cc_c_plus_count: int
    mi_below_a_count: int


def discover_batch_files(workspace_root: Path, batch: BatchDefinition) -> tuple[Path, ...]:
    """Return sorted, deduplicated Python files belonging to a batch.

    Supports both individual .py paths and recursive directory entries while
    excluding __pycache__ artifacts, non-existent paths, and circular symlink
    traversal errors.
    """
    found: set[Path] = set()
    for rel_path in batch.paths:
        target = workspace_root / rel_path
        if not target.exists():
            logger.debug("Batch %s path does not exist (skipping): %s", batch.id, target)
            continue
        if target.is_file():
            if target.suffix == ".py":
                found.add(target)
            continue
        try:
            for py_file in target.rglob("*.py"):
                if "__pycache__" not in py_file.parts:
                    found.add(py_file)
        except (RecursionError, OSError) as exc:
            logger.error("Failed to traverse directory %s for batch %s: %s", target, batch.id, exc)
            continue

    discovered = tuple(sorted(found))
    logger.log(VERBOSE, "Discovered %d Python file(s) for batch %s", len(discovered), batch.id)
    return discovered


def _format_block_symbol(block: Any) -> tuple[str, str]:
    """Extract kind letter and qualified symbol name from a Radon CC block.

    Normalizes bound methods to kind "M" and prefixes them with their enclosing
    class name when available.
    """
    kind = "M" if getattr(block, "is_method", False) else str(block.letter)
    classname = getattr(block, "classname", None)
    name = f"{classname}.{block.name}" if classname else str(block.name)
    return kind, name


def _safe_doc_pct(comments: int, docstrings: int, sloc: int) -> float:
    """Compute rounded (comments + docstrings) / sloc percentage safely."""
    return round(((comments + docstrings) / sloc) * 100.0, 1) if sloc > 0 else 0.0


def _safe_mean(values: list[float], decimals: int) -> float:
    """Compute rounded arithmetic mean of values, returning 0.0 when empty."""
    return round(sum(values) / len(values), decimals) if values else 0.0


def analyze_file_radon(
    file_path: Path,
    workspace_root: Path,
    batch_id: str,
) -> FileRadonMetrics:
    """Compute Radon raw, MI, and CC metrics for a single Python source file.

    Empty modules without callable blocks report avg_cc=0.0, max_cc=0,
    max_cc_grade="A", and max_cc_symbol="-".

    Raises:
        OSError: If file_path cannot be read (e.g., missing file or directory).
        UnicodeDecodeError: If file_path contains non-UTF-8 bytes.
        ValueError: If file_path lies outside workspace_root.
        SyntaxError: If file_path contains unparseable Python syntax.
    """
    # --- Read Source & Resolve Workspace-Relative Path ---
    try:
        source = file_path.read_text(encoding="utf-8")
        rel_path = file_path.relative_to(workspace_root).as_posix()
        raw = analyze(source)
        mi_score = round(float(mi_visit(source, multi=True)), 2)
        blocks = list(cc_visit(source))
    except (OSError, UnicodeDecodeError, ValueError, SyntaxError) as exc:
        logger.error("Radon analysis failed for %s: %s", file_path, exc)
        raise

    doc_pct = _safe_doc_pct(int(raw.comments), int(raw.multi), int(raw.sloc))
    mi_grade = str(mi_rank(mi_score))

    # --- Cyclomatic Complexity & Peak Block Summary ---
    if blocks:
        avg_cc = _safe_mean([float(b.complexity) for b in blocks], 2)
        top_block = max(blocks, key=lambda b: b.complexity)
        top_kind, top_name = _format_block_symbol(top_block)
        max_cc = int(top_block.complexity)
        max_cc_grade = str(cc_rank(max_cc))
        max_cc_symbol = f"{top_kind} {top_name}:{top_block.lineno}"
    else:
        avg_cc = 0.0
        max_cc = 0
        max_cc_grade = "A"
        max_cc_symbol = "-"

    # --- Extract Grade C+ Complexity Hotspots ---
    hotspots: list[ComplexityHotspot] = []
    for block in blocks:
        if block.complexity >= COMPLEXITY_HOTSPOT_THRESHOLD:
            kind, name = _format_block_symbol(block)
            hotspots.append(
                ComplexityHotspot(
                    batch_id=batch_id,
                    file_path=rel_path,
                    lineno=int(block.lineno),
                    kind=kind,
                    symbol=name,
                    complexity=int(block.complexity),
                    grade=str(cc_rank(block.complexity)),
                )
            )

    logger.debug(
        "Analyzed %s: sloc=%d, mi=%.2f (%s), avg_cc=%.2f, hotspots=%d",
        rel_path,
        int(raw.sloc),
        mi_score,
        mi_grade,
        avg_cc,
        len(hotspots),
    )

    return FileRadonMetrics(
        batch_id=batch_id,
        file_path=rel_path,
        loc=int(raw.loc),
        lloc=int(raw.lloc),
        sloc=int(raw.sloc),
        blank=int(raw.blank),
        comments=int(raw.comments),
        docstrings=int(raw.multi),
        doc_pct=doc_pct,
        mi_score=mi_score,
        mi_grade=mi_grade,
        avg_cc=avg_cc,
        max_cc=max_cc,
        max_cc_grade=max_cc_grade,
        max_cc_symbol=max_cc_symbol,
        cc_c_plus_count=len(hotspots),
        hotspots=tuple(hotspots),
    )


def _sum_batch_raw_lines(
    file_metrics: list[FileRadonMetrics],
) -> tuple[int, int, int, int, int, int]:
    """Sum LOC, LLOC, SLOC, blank, comment, and docstring counts across files."""
    return (
        sum(m.loc for m in file_metrics),
        sum(m.lloc for m in file_metrics),
        sum(m.sloc for m in file_metrics),
        sum(m.blank for m in file_metrics),
        sum(m.comments for m in file_metrics),
        sum(m.docstrings for m in file_metrics),
    )


def _build_batch_rollup(
    batch: BatchDefinition,
    file_metrics: list[FileRadonMetrics],
) -> BatchRadonRollup:
    """Aggregate per-file Radon metrics into a single BatchRadonRollup.

    Averages cyclomatic complexity across only modules with non-zero avg_cc so
    empty __init__.py files do not artificially dilute batch complexity.
    """
    loc, lloc, sloc, blank, comments, docstrings = _sum_batch_raw_lines(file_metrics)
    non_zero_cc = [m.avg_cc for m in file_metrics if m.avg_cc > 0]

    return BatchRadonRollup(
        batch_id=batch.id,
        scope=batch.scope,
        tier=batch.tier,
        file_count=len(file_metrics),
        loc=loc,
        lloc=lloc,
        sloc=sloc,
        blank=blank,
        comments=comments,
        docstrings=docstrings,
        doc_pct=_safe_doc_pct(comments, docstrings, sloc),
        avg_cc=_safe_mean(non_zero_cc, 2),
        cc_c_plus_count=sum(m.cc_c_plus_count for m in file_metrics),
        mi_below_a_count=sum(1 for m in file_metrics if m.mi_grade != "A"),
    )


def collect_radon_metrics(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
    progress: ProgressReporter | None = None,
) -> tuple[tuple[FileRadonMetrics, ...], tuple[BatchRadonRollup, ...]]:
    """Run Radon analysis across all selected batches with optional progress.

    Skips individual files that fail to read or parse (logging an ERROR) so
    remaining modules still produce metrics. Returns a (file_metrics,
    batch_rollups) tuple preserving batch ordering.
    """
    logger.info("Starting Radon metrics collection across %d batch(es)", len(batches))

    # --- Pre-Discover Files for Accurate Progress Denominator ---
    batch_file_map = [(batch, discover_batch_files(workspace_root, batch)) for batch in batches]
    total_files = sum(len(files) for _, files in batch_file_map)
    processed = 0

    all_files: list[FileRadonMetrics] = []
    rollups: list[BatchRadonRollup] = []

    # --- Analyze Modules & Build Per-Batch Rollups ---
    for batch, files in batch_file_map:
        batch_metrics: list[FileRadonMetrics] = []
        for py_file in files:
            try:
                metric = analyze_file_radon(py_file, workspace_root, batch.id)
            except (OSError, UnicodeDecodeError, SyntaxError):
                logger.log(VERBOSE, "Skipping unanalyzable file %s in batch %s", py_file, batch.id)
            else:
                batch_metrics.append(metric)
                all_files.append(metric)
            processed += 1
            if progress is not None:
                progress.update(f"Radon ({batch.id})", current=processed, total=total_files)
        rollups.append(_build_batch_rollup(batch, batch_metrics))

    logger.info(
        "Completed Radon metrics collection: %d file(s) scored across %d batch(es)",
        len(all_files),
        len(rollups),
    )
    return tuple(all_files), tuple(rollups)
