"""Path: src/gen_desk_tools/metrics/collectors/coverage_collector.py

Pytest branch and statement coverage collector for gd_metrics.

Operational Role:
    Executes pytest-cov scoped to active audit batches using the configured
    basetemp sandbox, parses the resulting coverage.json artifact into
    normalized per-file metrics, and formats uncovered line numbers into
    compact range notation.

Classes:
    FileCoverageMetrics: Statement and branch coverage metrics for one module.
    CoverageRunResult: Outcome and parsed per-file telemetry of a coverage run.

Functions:
    format_missing_lines: Collapse sorted missing line numbers into ranges.
    parse_coverage_json: Parse a pytest-cov JSON report into normalized records.
    run_pytest_coverage: Execute pytest-cov for active batches and parse results.
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from gen_desk_tools.metrics.config import BatchDefinition, MetricsConfig
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"

__all__ = [
    "CoverageRunResult",
    "FileCoverageMetrics",
    "format_missing_lines",
    "parse_coverage_json",
    "run_pytest_coverage",
]


@dataclass(frozen=True)
class FileCoverageMetrics:
    """Statement and branch coverage metrics for a single source module."""

    file_path: str
    num_statements: int
    covered_lines: int
    missing_lines: str
    num_branches: int
    covered_branches: int
    stmt_cov_pct: float
    branch_cov_pct: float
    total_cov_pct: float


@dataclass(frozen=True)
class CoverageRunResult:
    """Outcome of a pytest-cov execution and its parsed per-file telemetry."""

    exit_code: int
    summary_note: str
    files: Mapping[str, FileCoverageMetrics]


def format_missing_lines(lines: list[int]) -> str:
    """Collapse missing line numbers into compact range notation.

    Returns "-" when lines is empty; otherwise deduplicates, sorts, and merges
    contiguous sequences (e.g., [10, 12, 13, 14] -> "10, 12-14").
    """
    if not lines:
        return "-"
    ordered = sorted(set(lines))
    ranges: list[str] = []
    start = prev = ordered[0]
    for num in ordered[1:]:
        if num == prev + 1:
            prev = num
            continue
        ranges.append(f"{start}-{prev}" if start != prev else str(start))
        start = prev = num
    ranges.append(f"{start}-{prev}" if start != prev else str(start))
    return ", ".join(ranges)


def _normalize_coverage_path(raw_path: str, workspace_root: Path) -> str:
    """Normalize a coverage.json file key to a workspace-relative POSIX path.

    Falls back to a POSIX absolute path when an absolute key lies outside
    workspace_root.
    """
    candidate = Path(raw_path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(workspace_root.resolve()).as_posix()
        except ValueError:
            return candidate.as_posix()
    return raw_path.replace("\\", "/")


def parse_coverage_json(
    json_path: Path,
    workspace_root: Path,
) -> dict[str, FileCoverageMetrics]:
    """Parse a pytest-cov JSON report into normalized FileCoverageMetrics.

    Returns an empty dictionary when json_path does not exist. Modules with
    zero statements or zero branches report 100.0% for those dimensions.
    """
    if not json_path.exists():
        return {}

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    parsed: dict[str, FileCoverageMetrics] = {}

    # --- Compute Per-File Statement, Branch & Combined Percentages ---
    for raw_path, entry in payload.get("files", {}).items():
        summary = entry.get("summary", {})
        num_stmts = int(summary.get("num_statements", 0))
        cov_lines = int(summary.get("covered_lines", 0))
        num_branches = int(summary.get("num_branches", 0))
        cov_branches = int(summary.get("covered_branches", 0))

        stmt_pct = round((cov_lines / num_stmts) * 100.0, 1) if num_stmts > 0 else 100.0
        branch_pct = round((cov_branches / num_branches) * 100.0, 1) if num_branches > 0 else 100.0
        total_den = num_stmts + num_branches
        total_pct = (
            round(((cov_lines + cov_branches) / total_den) * 100.0, 1) if total_den > 0 else 100.0
        )

        rel_path = _normalize_coverage_path(raw_path, workspace_root)
        parsed[rel_path] = FileCoverageMetrics(
            file_path=rel_path,
            num_statements=num_stmts,
            covered_lines=cov_lines,
            missing_lines=format_missing_lines(list(entry.get("missing_lines", []))),
            num_branches=num_branches,
            covered_branches=cov_branches,
            stmt_cov_pct=stmt_pct,
            branch_cov_pct=branch_pct,
            total_cov_pct=total_pct,
        )

    return parsed


def _collect_existing_targets(
    workspace_root: Path,
    batches: tuple[BatchDefinition, ...],
) -> tuple[list[str], list[str]]:
    """Return deduplicated existing test paths and source coverage targets."""
    test_targets: list[str] = []
    cov_targets: list[str] = []
    for batch in batches:
        for t_path in batch.test_paths:
            if (workspace_root / t_path).exists() and t_path not in test_targets:
                test_targets.append(t_path)
        for s_path in batch.paths:
            if (workspace_root / s_path).exists() and s_path not in cov_targets:
                cov_targets.append(s_path)
    return test_targets, cov_targets


def run_pytest_coverage(
    config: MetricsConfig,
    batches: tuple[BatchDefinition, ...],
    *,
    progress: ProgressReporter | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> CoverageRunResult:
    """Execute pytest-cov for the selected batches and parse coverage.json.

    Skips execution cleanly when no configured test directories exist on disk.

    Args:
        progress: Optional reporter receiving execution status updates.
        runner: Optional subprocess.run replacement injected for hermetic testing.
    """
    # --- Resolve Existing Test & Coverage Targets ---
    test_targets, cov_targets = _collect_existing_targets(config.workspace_root, batches)
    if not test_targets:
        return CoverageRunResult(
            exit_code=0,
            summary_note="No matching test directories found",
            files={},
        )

    # --- Build & Execute Pytest Command ---
    config.pytest_basetemp.mkdir(parents=True, exist_ok=True)
    cov_json_path = config.pytest_basetemp / "coverage.json"

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *test_targets,
        f"--basetemp={config.pytest_basetemp}",
        "--cov-branch",
        f"--cov-report=json:{cov_json_path}",
    ]
    for target in cov_targets:
        cmd.append(f"--cov={target}")

    if progress is not None:
        progress.update(f"Running pytest across {len(test_targets)} target(s)")

    exec_fn = subprocess.run if runner is None else runner
    completed = exec_fn(
        cmd,
        cwd=config.workspace_root,
        capture_output=True,
        text=True,
        check=False,
    )

    # --- Extract Final Summary Line & Parse JSON Artifact ---
    last_line = ""
    for line in reversed(completed.stdout.splitlines()):
        stripped = line.strip()
        if stripped:
            last_line = stripped
            break
    summary_note = last_line or f"pytest exited with code {completed.returncode}"
    files = parse_coverage_json(cov_json_path, config.workspace_root)

    return CoverageRunResult(
        exit_code=int(completed.returncode),
        summary_note=summary_note,
        files=files,
    )
