"""Path: src/gen_desk_tools/metrics/collectors/mypy_collector.py

Subprocess collector for mypy static type-check diagnostics.

Operational Role:
    Invokes mypy in machine-readable output mode via
    gen_desk_tools.core.process.run_command against existing source paths
    across active audit batches, parses line-level error/warning/note records,
    and maps each diagnostic back to its owning batch ID with 4-tier
    diagnostic logging and timeout/encoding resilience.

Classes:
    MypyDiagnostic: Single parsed mypy error, warning, or note record.
    MypyRunResult: Aggregated diagnostics, summary note, and exit code.

Functions:
    parse_mypy_output: Parse mypy stdout lines into MypyDiagnostic tuples.
    run_mypy_check: Execute mypy against active batch paths and parse output.
"""

from __future__ import annotations

import logging
import re
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

__version__ = "1.0.0+build.5"

__all__ = [
    "MypyDiagnostic",
    "MypyRunResult",
    "parse_mypy_output",
    "run_mypy_check",
]

logger = logging.getLogger(__name__)

# Matches "path:line[:col]: severity: message [optional-error-code]".
_MYPY_LINE_RE = re.compile(
    r"^(.+?):(\d+)(?::\d+)?:\s*(error|warning|note):\s*(.+?)(?:\s+\[([^\]]+)\])?$"
)


@dataclass(frozen=True)
class MypyDiagnostic:
    """Single parsed mypy diagnostic record."""

    batch_id: str
    file_path: str
    lineno: int
    severity: str
    error_code: str
    message: str


@dataclass(frozen=True)
class MypyRunResult:
    """Aggregated result of a mypy subprocess execution."""

    diagnostics: tuple[MypyDiagnostic, ...]
    summary_note: str
    returncode: int


def _normalize_rel_path(raw_path: str, workspace_root: Path) -> str:
    """Normalize a mypy file path to a workspace-relative POSIX string.

    Preserves external absolute paths as POSIX strings if they fall outside
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


def parse_mypy_output(
    output: str,
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
) -> tuple[MypyDiagnostic, ...]:
    """Parse mypy stdout lines into structured MypyDiagnostic records.

    Non-diagnostic summary or blank lines that do not match _MYPY_LINE_RE are
    ignored cleanly.
    """
    records: list[MypyDiagnostic] = []
    for raw_line in output.splitlines():
        match = _MYPY_LINE_RE.match(raw_line.strip())
        if match is None:
            continue
        rel_path = _normalize_rel_path(match.group(1), workspace_root)
        records.append(
            MypyDiagnostic(
                batch_id=_match_batch_id(rel_path, batches),
                file_path=rel_path,
                lineno=int(match.group(2)),
                severity=match.group(3),
                error_code=match.group(5) or "",
                message=match.group(4).strip(),
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


def run_mypy_check(
    config: MetricsConfig,
    batches: tuple[BatchDefinition, ...],
    *,
    progress: ProgressReporter | None = None,
    runner: Callable[..., Any] = subprocess.run,
) -> MypyRunResult:
    """Execute mypy against active batch paths and parse diagnostics.

    Returns a skipped result with returncode 0 when no batch targets exist, or
    a degraded result with returncode 1 if mypy cannot be launched, times out,
    or emits undecodable console bytes.

    Args:
        config: Active MetricsConfig for the workspace.
        batches: Scoped BatchDefinition records to type-check.
        progress: Optional reporter receiving status updates.
        runner: Subprocess callable (defaults to subprocess.run) for testing.
    """
    logger.info("Starting mypy static type check across %d batch(es)", len(batches))

    # --- Resolve Existing Source Targets ---
    targets = _collect_existing_targets(config.workspace_root, batches)
    if not targets:
        logger.log(VERBOSE, "Skipping mypy check: no existing batch targets found")
        return MypyRunResult(diagnostics=(), summary_note="skipped (no targets)", returncode=0)

    logger.log(VERBOSE, "Running mypy static type check on %d target(s)", len(targets))
    if progress is not None:
        progress.update("Running mypy static type check")

    # --- Invoke Mypy Subprocess & Parse Stdout ---
    cmd = [
        sys.executable,
        "-m",
        "mypy",
        "--no-pretty",
        "--hide-error-context",
        "--show-error-codes",
        "--no-error-summary",
        *targets,
    ]
    logger.debug("Executing mypy command: %s", cmd)
    try:
        res = run_command(cmd, cwd=config.workspace_root, runner=runner)
    except subprocess.TimeoutExpired as exc:
        msg = f"mypy timed out after {exc.timeout}s"
        logger.error("Mypy check failed: %s", msg)
        return MypyRunResult(diagnostics=(), summary_note=msg, returncode=1)
    except UnicodeDecodeError as exc:
        msg = f"mypy output encoding error: {exc}"
        logger.error("Mypy check failed: %s", msg)
        return MypyRunResult(diagnostics=(), summary_note=msg, returncode=1)

    if res.error:
        logger.error("Mypy check unavailable: %s", res.error)
        return MypyRunResult(
            diagnostics=(),
            summary_note=f"mypy unavailable: {res.error}",
            returncode=1,
        )

    diagnostics = parse_mypy_output(res.stdout, config.workspace_root, batches)
    logger.info(
        "Completed mypy static type check: %d diagnostic(s) (returncode=%d)",
        len(diagnostics),
        res.returncode,
    )
    return MypyRunResult(
        diagnostics=diagnostics,
        summary_note=f"{len(diagnostics)} diagnostic(s)",
        returncode=res.returncode,
    )
