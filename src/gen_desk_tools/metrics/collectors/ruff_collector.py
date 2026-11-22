"""Path: src/gen_desk_tools/metrics/collectors/ruff_collector.py

Subprocess collector for Ruff JSON lint diagnostics.

Operational Role:
    Invokes ruff check in JSON output mode via
    gen_desk_tools.core.process.run_command against existing source paths
    across active audit batches, parses rule findings with fixability metadata,
    and maps each diagnostic back to its owning batch ID with 4-tier
    diagnostic logging and timeout/encoding resilience.

Classes:
    RuffDiagnostic: Single parsed Ruff lint finding with location and fix flag.
    RuffRunResult: Aggregated diagnostics, summary note, and exit code.

Functions:
    parse_ruff_json: Parse Ruff --output-format JSON stdout into records.
    run_ruff_check: Execute ruff check against active batch paths.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gen_desk_tools.core.logging import VERBOSE
from gen_desk_tools.core.process import run_command
from gen_desk_tools.metrics.config import BatchDefinition, MetricsConfig
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.4"

__all__ = [
    "RuffDiagnostic",
    "RuffRunResult",
    "parse_ruff_json",
    "run_ruff_check",
]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RuffDiagnostic:
    """Single parsed Ruff lint finding."""

    batch_id: str
    file_path: str
    lineno: int
    col: int
    rule_code: str
    message: str
    fixable: bool


@dataclass(frozen=True)
class RuffRunResult:
    """Aggregated result of a Ruff JSON lint execution."""

    diagnostics: tuple[RuffDiagnostic, ...]
    summary_note: str
    returncode: int


def _normalize_rel_path(raw_path: str, workspace_root: Path) -> str:
    """Normalize a Ruff filename to a workspace-relative POSIX string.

    Preserves external absolute paths as POSIX strings when they fall outside
    workspace_root.
    """
    candidate = Path(raw_path)
    if candidate.is_absolute():
        try:
            return candidate.relative_to(workspace_root).as_posix()
        except ValueError:
            return candidate.as_posix()
    return raw_path.replace("\\", "/").lstrip("./")


def _match_batch_id(rel_path: str, batches: tuple[BatchDefinition, ...]) -> str:
    """Resolve the owning batch ID for a normalized relative file path."""
    for batch in batches:
        for base in batch.paths:
            prefix = base.rstrip("/")
            if rel_path == prefix or rel_path.startswith(f"{prefix}/"):
                return batch.id
    return ""


def parse_ruff_json(
    output: str,
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
) -> tuple[RuffDiagnostic, ...]:
    """Parse Ruff --output-format JSON stdout into RuffDiagnostic records.

    Returns an empty tuple when output is blank or contains malformed JSON.
    """
    if not output.strip():
        return ()
    try:
        items = json.loads(output)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Ruff JSON output: %s", exc)
        return ()

    records: list[RuffDiagnostic] = []
    for item in items:
        rel_path = _normalize_rel_path(str(item.get("filename", "")), workspace_root)
        loc = item.get("location") or {}
        records.append(
            RuffDiagnostic(
                batch_id=_match_batch_id(rel_path, batches),
                file_path=rel_path,
                lineno=int(loc.get("row", 0)),
                col=int(loc.get("column", 0)),
                rule_code=str(item.get("code") or ""),
                message=str(item.get("message") or ""),
                fixable=bool(item.get("fix")),
            )
        )
    return tuple(records)


def _collect_existing_targets(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
) -> list[str]:
    """Collect deduplicated existing source paths across active batches."""
    targets: list[str] = []
    seen: set[str] = set()
    for batch in batches:
        for rel_path in batch.paths:
            if rel_path not in seen and (workspace_root / rel_path).exists():
                seen.add(rel_path)
                targets.append(rel_path)
    return targets


def run_ruff_check(
    config: MetricsConfig,
    batches: tuple[BatchDefinition, ...],
    *,
    progress: ProgressReporter | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> RuffRunResult:
    """Execute ruff check --output-format JSON against active batch paths.

    Returns a skipped result with returncode 0 when no batch targets exist, or
    a degraded result with returncode 1 if ruff cannot be launched, times out,
    or emits undecodable console bytes.

    Args:
        config: Active MetricsConfig for the workspace.
        batches: Scoped BatchDefinition records to lint.
        progress: Optional reporter receiving status updates.
        runner: Subprocess callable (defaults to subprocess.run) for testing.
    """
    logger.info("Starting ruff lint check across %d batch(es)", len(batches))

    # --- Resolve Existing Source Targets ---
    targets = _collect_existing_targets(config.workspace_root, batches)
    if not targets:
        logger.log(VERBOSE, "Skipping ruff lint check: no existing batch targets found")
        return RuffRunResult(diagnostics=(), summary_note="skipped (no targets)", returncode=0)

    logger.log(VERBOSE, "Running ruff lint check on %d target(s)", len(targets))
    if progress is not None:
        progress.update("Running ruff lint check")

    # --- Invoke Ruff Subprocess & Parse JSON ---
    cmd = [sys.executable, "-m", "ruff", "check", "--output-format", "json", *targets]
    logger.debug("Executing ruff command: %s", cmd)
    try:
        res = run_command(cmd, cwd=config.workspace_root, runner=runner)
    except subprocess.TimeoutExpired as exc:
        msg = f"ruff timed out after {exc.timeout}s"
        logger.error("Ruff check failed: %s", msg)
        return RuffRunResult(diagnostics=(), summary_note=msg, returncode=1)
    except UnicodeDecodeError as exc:
        msg = f"ruff output encoding error: {exc}"
        logger.error("Ruff check failed: %s", msg)
        return RuffRunResult(diagnostics=(), summary_note=msg, returncode=1)

    if res.error:
        logger.error("Ruff check unavailable: %s", res.error)
        return RuffRunResult(
            diagnostics=(),
            summary_note=f"ruff unavailable: {res.error}",
            returncode=1,
        )

    diagnostics = parse_ruff_json(res.stdout, config.workspace_root, batches)
    logger.info(
        "Completed ruff lint check: %d diagnostic(s) (returncode=%d)",
        len(diagnostics),
        res.returncode,
    )
    return RuffRunResult(
        diagnostics=diagnostics,
        summary_note=f"{len(diagnostics)} diagnostic(s)",
        returncode=res.returncode,
    )
