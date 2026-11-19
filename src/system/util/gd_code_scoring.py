"""Path: src/system/util/gd_code_scoring.py

Unified Phase 0 telemetry collector for raw line metrics, complexity, MI, and pytest coverage.

Operational Role:
    Evaluates Python modules across canonical GDA Audit Batches (GDA-Batch-1 through
    GDA-Batch-8) and optional non-GDA subsystem groups (Group-S, Group-CLI,
    Group-GenDesk). Computes raw line counts and documentation ratios via radon.raw,
    Cyclomatic Complexity (CC) via radon.complexity, Maintainability Index (MI) via
    radon.metrics, and statement/branch coverage via pytest-cov JSON output.
    Ruff and Mypy are deferred to individual batch verification gates (Ruff remains
    available only via the explicit opt-in --run-ruff flag). Emits a consolidated
    4-section report (reports/gd_code_scoring_report.txt) mapped 1:1 to the Master
    Audit Telemetry Google Sheet tabs.

Usage:
    python src/system/util/gd_code_scoring.py [--no-pytest] [--cov-json PATH] [--output PATH]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from radon.complexity import cc_rank, cc_visit
from radon.metrics import mi_rank, mi_visit
from radon.raw import analyze

from system.util.check_structure import resolve_workspace_root

__version__ = "1.0.0+build.4"

__all__ = [
    "AUDIT_BATCH_RULES",
    "BatchRollupMetrics",
    "BlockCCMetric",
    "CoverageFileStat",
    "DomainRawMetrics",
    "FileMIMetric",
    "FileTelemetryMetric",
    "PytestExecutionResult",
    "RuffExecutionResult",
    "ScoringReportData",
    "aggregate_batch_rollups",
    "collect_cc_metrics",
    "collect_domain_raw_metrics",
    "collect_file_telemetry",
    "collect_mi_metrics",
    "format_scoring_report",
    "generate_scoring_report",
    "load_coverage_json",
    "main",
    "resolve_batch_id",
    "run_pytest_coverage",
    "run_ruff_updates",
]

DEFAULT_REPORT_PATH: str = "reports/gd_code_scoring_report.txt"
DEFAULT_COV_JSON_PATH: str = "gtemp/pytest_tmp/coverage.json"

# Ordered prefix rules mapping relative POSIX file paths to canonical Audit Batch IDs.
AUDIT_BATCH_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("GDA-Batch-1", ("src/gda/core/",)),
    ("GDA-Batch-2", ("src/gda/util/", "src/gda/io/")),
    (
        "GDA-Batch-3",
        (
            "src/gda/model/atom/",
            "src/gda/model/base/",
            "src/gda/model/entity/",
            "src/gda/model/xref/",
            "src/gda/model/__init__.py",
            "src/gda/__init__.py",
        ),
    ),
    ("GDA-Batch-4", ("src/gda/model/source/",)),
    ("GDA-Batch-5", ("src/gda/entity/",)),
    ("GDA-Batch-6", ("src/gda/db/",)),
    ("GDA-Batch-7", ("src/gda/repository/",)),
    ("GDA-Batch-8", ("src/gda/engine/", "src/gda/manager/")),
    ("Group-S", ("src/system/",)),
    ("Group-CLI", ("src/cli/",)),
    ("Group-GenDesk", ("src/ancestry_desk/",)),
    ("Tests", ("tests/",)),
)

CANONICAL_BATCH_ORDER: tuple[str, ...] = (
    "GDA-Batch-1",
    "GDA-Batch-2",
    "GDA-Batch-3",
    "GDA-Batch-4",
    "GDA-Batch-5",
    "GDA-Batch-6",
    "GDA-Batch-7",
    "GDA-Batch-8",
    "Group-S",
    "Group-CLI",
    "Group-GenDesk",
)

DEFAULT_DOMAINS: tuple[tuple[str, str], ...] = (
    ("src/gda", "src/gda"),
    ("src/cli", "src/cli"),
    ("src/ancestry_desk", "src/ancestry_desk"),
    ("src/system", "src/system"),
    ("tests", "tests"),
)


@dataclass(frozen=True, kw_only=True)
class RuffExecutionResult:
    """Outcome of running optional Ruff format and lint check steps."""

    ran_ruff: bool
    format_returncode: int
    format_output: str
    check_returncode: int
    check_output: str


@dataclass(frozen=True, kw_only=True)
class PytestExecutionResult:
    """Outcome of running or loading pytest-cov JSON coverage telemetry."""

    ran_pytest: bool
    returncode: int
    summary_output: str
    cov_json_path: Path | None


@dataclass(frozen=True, kw_only=True)
class CoverageFileStat:
    """Statement and branch coverage telemetry extracted for a single source file."""

    covered_lines: int
    num_statements: int
    covered_branches: int
    num_branches: int
    missing_lines_str: str

    @property
    def stmt_cov_pct(self) -> float:
        """Return statement coverage percentage (0.0 to 100.0)."""
        if self.num_statements <= 0:
            return 100.0
        return (self.covered_lines / self.num_statements) * 100.0

    @property
    def branch_cov_pct(self) -> float:
        """Return branch coverage percentage (0.0 to 100.0)."""
        if self.num_branches <= 0:
            return 100.0
        return (self.covered_branches / self.num_branches) * 100.0

    @property
    def total_cov_pct(self) -> float:
        """Return combined statement + branch coverage percentage (0.0 to 100.0)."""
        denom = self.num_statements + self.num_branches
        if denom <= 0:
            return 100.0
        return ((self.covered_lines + self.covered_branches) / denom) * 100.0


@dataclass(frozen=True, kw_only=True)
class DomainRawMetrics:
    """Aggregated raw line-count and documentation metrics for a workspace domain."""

    label: str
    file_count: int
    loc: int
    lloc: int
    sloc: int
    blank: int
    comments: int
    docstrings: int

    @property
    def total_doc_lines(self) -> int:
        """Return combined inline comment and multiline docstring line count."""
        return self.comments + self.docstrings

    @property
    def doc_to_sloc_pct(self) -> float:
        """Calculate (Comments + Docstrings) / SLOC percentage."""
        return (self.total_doc_lines / self.sloc * 100.0) if self.sloc > 0 else 0.0


@dataclass(frozen=True, kw_only=True)
class BlockCCMetric:
    """Cyclomatic complexity metric for an individual class, function, or method."""

    batch_id: str
    file_path: str
    block_type: str
    name: str
    lineno: int
    complexity: int
    grade: str


@dataclass(frozen=True, kw_only=True)
class FileMIMetric:
    """Maintainability Index (MI) score and letter grade for a Python module."""

    batch_id: str
    file_path: str
    mi_score: float
    grade: str


@dataclass(frozen=True, kw_only=True)
class FileTelemetryMetric:
    """Unified per-file telemetry combining radon raw, CC, MI, and pytest coverage."""

    batch_id: str
    file_path: str
    loc: int
    lloc: int
    sloc: int
    blank: int
    comments: int
    docstrings: int
    mi_score: float
    mi_grade: str
    block_count: int
    sum_cc: int
    max_cc: int
    max_cc_grade: str
    max_cc_symbol: str
    cc_c_plus_count: int
    covered_lines: int
    num_statements: int
    covered_branches: int
    num_branches: int
    missing_lines_str: str
    has_coverage: bool

    @property
    def doc_to_sloc_pct(self) -> float:
        """Calculate (Comments + Docstrings) / SLOC percentage for this module."""
        return ((self.comments + self.docstrings) / self.sloc * 100.0) if self.sloc > 0 else 0.0

    @property
    def avg_cc(self) -> float:
        """Calculate average cyclomatic complexity across blocks in this module."""
        return (self.sum_cc / self.block_count) if self.block_count > 0 else 0.0

    @property
    def total_cov_pct(self) -> float:
        """Calculate combined statement and branch coverage percentage for this module."""
        if not self.has_coverage:
            return 0.0
        denom = self.num_statements + self.num_branches
        if denom <= 0:
            return 100.0
        return ((self.covered_lines + self.covered_branches) / denom) * 100.0


@dataclass(frozen=True, kw_only=True)
class BatchRollupMetrics:
    """Aggregated telemetry row for a canonical GDA Audit Batch or subsystem group."""

    batch_id: str
    file_count: int
    loc: int
    lloc: int
    sloc: int
    blank: int
    comments: int
    docstrings: int
    block_count: int
    sum_cc: int
    cc_c_plus_count: int
    mi_below_a_count: int
    covered_lines: int
    num_statements: int
    covered_branches: int
    num_branches: int
    has_coverage: bool

    @property
    def doc_to_sloc_pct(self) -> float:
        """Return (Comments + Docstrings) / SLOC percentage for the batch."""
        return ((self.comments + self.docstrings) / self.sloc * 100.0) if self.sloc > 0 else 0.0

    @property
    def avg_cc(self) -> float:
        """Return mean block cyclomatic complexity for the batch."""
        return (self.sum_cc / self.block_count) if self.block_count > 0 else 0.0

    @property
    def stmt_cov_pct(self) -> float:
        """Return batch statement coverage percentage."""
        if not self.has_coverage:
            return 0.0
        if self.num_statements <= 0:
            return 100.0
        return (self.covered_lines / self.num_statements) * 100.0

    @property
    def branch_cov_pct(self) -> float:
        """Return batch branch coverage percentage."""
        if not self.has_coverage:
            return 0.0
        if self.num_branches <= 0:
            return 100.0
        return (self.covered_branches / self.num_branches) * 100.0

    @property
    def total_cov_pct(self) -> float:
        """Return batch combined statement and branch coverage percentage."""
        if not self.has_coverage:
            return 0.0
        denom = self.num_statements + self.num_branches
        if denom <= 0:
            return 100.0
        return ((self.covered_lines + self.covered_branches) / denom) * 100.0


@dataclass(frozen=True, kw_only=True)
class ScoringReportData:
    """Complete dataset assembled for the unified Phase 0 GDA code scoring report."""

    generated_at: str
    workspace_root: Path
    ruff_result: RuffExecutionResult
    pytest_result: PytestExecutionResult
    raw_metrics: list[DomainRawMetrics]
    batch_rollups: list[BatchRollupMetrics]
    file_telemetry: list[FileTelemetryMetric]
    cc_metrics: list[BlockCCMetric]
    mi_metrics: list[FileMIMetric]


def resolve_batch_id(rel_posix_path: str) -> str:
    """Map a workspace-relative POSIX file path to its canonical Audit Batch ID."""
    normalized = rel_posix_path.replace("\\", "/").lstrip("./")
    for batch_id, prefixes in AUDIT_BATCH_RULES:
        for prefix in prefixes:
            if normalized == prefix or normalized.startswith(prefix):
                return batch_id
    return "Other"


def _discover_python_files(target_dir: Path) -> list[Path]:
    """Return sorted list of Python files under target_dir excluding caches and hidden dirs."""
    if not target_dir.is_dir():
        return []
    return sorted(
        p
        for p in target_dir.rglob("*.py")
        if "__pycache__" not in p.parts and not any(part.startswith(".") for part in p.parts)
    )


def _compress_line_ranges(line_numbers: list[int]) -> str:
    """Compress a sorted list of integer line numbers into compact range notation."""
    if not line_numbers:
        return "-"
    unique_sorted = sorted(set(line_numbers))
    ranges: list[str] = []
    start = prev = unique_sorted[0]
    for num in unique_sorted[1:]:
        if num == prev + 1:
            prev = num
        else:
            ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
            start = prev = num
    ranges.append(f"{start}-{prev}" if start != prev else f"{start}")
    return ", ".join(ranges)


def load_coverage_json(
    workspace_root: Path,
    cov_json_path: Path | str,
) -> dict[str, CoverageFileStat]:
    """Parse a pytest-cov / coverage.py JSON file into a relative-POSIX-path dictionary."""
    resolved_path = (
        cov_json_path if isinstance(cov_json_path, Path) else workspace_root / cov_json_path
    )
    if not resolved_path.is_file():
        return {}

    try:
        payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    files_section = payload.get("files", {})
    if not isinstance(files_section, dict):
        return {}

    cov_map: dict[str, CoverageFileStat] = {}
    for raw_key, file_info in files_section.items():
        if not isinstance(file_info, dict):
            continue
        summary = file_info.get("summary", {})
        if not isinstance(summary, dict):
            summary = {}
        missing_list = file_info.get("missing_lines", [])
        if not isinstance(missing_list, list):
            missing_list = []

        norm_key = str(raw_key).replace("\\", "/").lstrip("./")
        root_posix = workspace_root.as_posix().rstrip("/") + "/"
        if norm_key.startswith(root_posix):
            norm_key = norm_key[len(root_posix) :]

        cov_map[norm_key] = CoverageFileStat(
            covered_lines=int(summary.get("covered_lines", 0)),
            num_statements=int(summary.get("num_statements", 0)),
            covered_branches=int(summary.get("covered_branches", 0)),
            num_branches=int(summary.get("num_branches", 0)),
            missing_lines_str=_compress_line_ranges([int(x) for x in missing_list]),
        )
    return cov_map


def run_pytest_coverage(
    workspace_root: Path,
    cov_json_rel_path: str = DEFAULT_COV_JSON_PATH,
    source_target: str = "src",
) -> PytestExecutionResult:
    """Execute pytest with statement and branch coverage JSON export (basetemp configured in pyproject.toml)."""
    target_path = workspace_root / source_target
    if not target_path.exists():
        return PytestExecutionResult(
            ran_pytest=False,
            returncode=0,
            summary_output=f"No '{source_target}' directory found for pytest coverage.",
            cov_json_path=None,
        )

    cov_json_abs = workspace_root / cov_json_rel_path
    cov_json_abs.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        f"--cov={source_target}",
        "--cov-branch",
        f"--cov-report=json:{cov_json_abs.as_posix()}",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )
    combined = (proc.stdout + "\n" + proc.stderr).strip()
    last_lines = " | ".join(line.strip() for line in combined.splitlines()[-3:] if line.strip())
    return PytestExecutionResult(
        ran_pytest=True,
        returncode=proc.returncode,
        summary_output=last_lines or "Pytest coverage run completed.",
        cov_json_path=cov_json_abs if cov_json_abs.is_file() else None,
    )


def run_ruff_updates(
    workspace_root: Path,
    targets: tuple[str, ...] = ("src", "tests"),
) -> RuffExecutionResult:
    """Execute optional ruff format and ruff check --fix on workspace targets."""
    existing_targets = [t for t in targets if (workspace_root / t).exists()]
    if not existing_targets:
        return RuffExecutionResult(
            ran_ruff=True,
            format_returncode=0,
            format_output="No target directories found for ruff.",
            check_returncode=0,
            check_output="No target directories found for ruff.",
        )

    fmt_proc = subprocess.run(
        [sys.executable, "-m", "ruff", "format", *existing_targets],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )
    fmt_out = (fmt_proc.stdout + "\n" + fmt_proc.stderr).strip()

    chk_proc = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--fix", *existing_targets],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )
    chk_out = (chk_proc.stdout + "\n" + chk_proc.stderr).strip()

    return RuffExecutionResult(
        ran_ruff=True,
        format_returncode=fmt_proc.returncode,
        format_output=fmt_out or "All files formatted cleanly.",
        check_returncode=chk_proc.returncode,
        check_output=chk_out or "All checks passed.",
    )


def collect_domain_raw_metrics(
    workspace_root: Path,
    domains: tuple[tuple[str, str], ...] = DEFAULT_DOMAINS,
) -> list[DomainRawMetrics]:
    """Compute raw line and comment counts across configured workspace domains."""
    results: list[DomainRawMetrics] = []
    for label, rel_path in domains:
        target_dir = workspace_root / rel_path
        py_files = _discover_python_files(target_dir)
        if not py_files:
            continue

        loc = lloc = sloc = blank = comments = multi = 0
        for py_file in py_files:
            source_text = py_file.read_text(encoding="utf-8")
            raw_stat = analyze(source_text)
            loc += raw_stat.loc
            lloc += raw_stat.lloc
            sloc += raw_stat.sloc
            blank += raw_stat.blank
            comments += raw_stat.comments
            multi += raw_stat.multi

        results.append(
            DomainRawMetrics(
                label=label,
                file_count=len(py_files),
                loc=loc,
                lloc=lloc,
                sloc=sloc,
                blank=blank,
                comments=comments,
                docstrings=multi,
            )
        )
    return results


def _format_block_label(block: Any) -> tuple[str, str]:
    """Determine single-letter block type ('C', 'M', 'F') and qualified name."""
    classname = getattr(block, "classname", None)
    if hasattr(block, "methods"):
        return "C", str(block.name)
    if classname:
        return "M", f"{classname}.{block.name}"
    return "F", str(block.name)


def collect_cc_metrics(
    workspace_root: Path,
    source_dirs: tuple[str, ...] = ("src",),
) -> list[BlockCCMetric]:
    """Collect Cyclomatic Complexity (CC) metrics for all blocks under source_dirs."""
    metrics: list[BlockCCMetric] = []
    for rel_dir in source_dirs:
        for py_file in _discover_python_files(workspace_root / rel_dir):
            rel_path = py_file.relative_to(workspace_root).as_posix()
            batch_id = resolve_batch_id(rel_path)
            source_text = py_file.read_text(encoding="utf-8")
            blocks = cc_visit(source_text)
            for blk in blocks:
                b_type, b_name = _format_block_label(blk)
                comp = int(blk.complexity)
                metrics.append(
                    BlockCCMetric(
                        batch_id=batch_id,
                        file_path=rel_path,
                        block_type=b_type,
                        name=b_name,
                        lineno=int(blk.lineno),
                        complexity=comp,
                        grade=str(cc_rank(comp)),
                    )
                )
    return metrics


def collect_mi_metrics(
    workspace_root: Path,
    source_dirs: tuple[str, ...] = ("src",),
) -> list[FileMIMetric]:
    """Collect Maintainability Index (MI) scores for all modules under source_dirs."""
    metrics: list[FileMIMetric] = []
    for rel_dir in source_dirs:
        for py_file in _discover_python_files(workspace_root / rel_dir):
            rel_path = py_file.relative_to(workspace_root).as_posix()
            batch_id = resolve_batch_id(rel_path)
            source_text = py_file.read_text(encoding="utf-8")
            score = float(mi_visit(source_text, multi=True))
            metrics.append(
                FileMIMetric(
                    batch_id=batch_id,
                    file_path=rel_path,
                    mi_score=score,
                    grade=str(mi_rank(score)),
                )
            )
    return metrics


def collect_file_telemetry(
    workspace_root: Path,
    source_dirs: tuple[str, ...] = ("src",),
    coverage_map: dict[str, CoverageFileStat] | None = None,
) -> tuple[list[FileTelemetryMetric], list[BlockCCMetric], list[FileMIMetric]]:
    """Collect unified per-file raw, CC, MI, and pytest coverage metrics in a single pass."""
    cov_lookup = coverage_map or {}
    has_any_cov = bool(cov_lookup)

    file_telemetry: list[FileTelemetryMetric] = []
    cc_list: list[BlockCCMetric] = []
    mi_list: list[FileMIMetric] = []

    for rel_dir in source_dirs:
        for py_file in _discover_python_files(workspace_root / rel_dir):
            rel_path = py_file.relative_to(workspace_root).as_posix()
            batch_id = resolve_batch_id(rel_path)
            source_text = py_file.read_text(encoding="utf-8")

            raw_stat = analyze(source_text)
            mi_score = float(mi_visit(source_text, multi=True))
            mi_grade = str(mi_rank(mi_score))
            mi_list.append(
                FileMIMetric(
                    batch_id=batch_id,
                    file_path=rel_path,
                    mi_score=mi_score,
                    grade=mi_grade,
                )
            )

            blocks = cc_visit(source_text)
            block_count = len(blocks)
            sum_cc = 0
            max_cc = 0
            max_cc_grade = "A"
            max_cc_symbol = "-"
            cc_c_plus = 0

            for blk in blocks:
                b_type, b_name = _format_block_label(blk)
                comp = int(blk.complexity)
                grade = str(cc_rank(comp))
                sum_cc += comp
                if comp >= 11:
                    cc_c_plus += 1
                if comp > max_cc:
                    max_cc = comp
                    max_cc_grade = grade
                    max_cc_symbol = f"{b_type} {b_name}:{int(blk.lineno)}"

                cc_list.append(
                    BlockCCMetric(
                        batch_id=batch_id,
                        file_path=rel_path,
                        block_type=b_type,
                        name=b_name,
                        lineno=int(blk.lineno),
                        complexity=comp,
                        grade=grade,
                    )
                )

            cov_stat = cov_lookup.get(rel_path)
            if cov_stat is not None:
                cov_lines = cov_stat.covered_lines
                num_stmts = cov_stat.num_statements
                cov_branches = cov_stat.covered_branches
                num_branches = cov_stat.num_branches
                missing_str = cov_stat.missing_lines_str
                file_has_cov = True
            else:
                cov_lines = 0
                num_stmts = 0
                cov_branches = 0
                num_branches = 0
                missing_str = "-"
                file_has_cov = has_any_cov and raw_stat.sloc == 0

            file_telemetry.append(
                FileTelemetryMetric(
                    batch_id=batch_id,
                    file_path=rel_path,
                    loc=raw_stat.loc,
                    lloc=raw_stat.lloc,
                    sloc=raw_stat.sloc,
                    blank=raw_stat.blank,
                    comments=raw_stat.comments,
                    docstrings=raw_stat.multi,
                    mi_score=mi_score,
                    mi_grade=mi_grade,
                    block_count=block_count,
                    sum_cc=sum_cc,
                    max_cc=max_cc,
                    max_cc_grade=max_cc_grade,
                    max_cc_symbol=max_cc_symbol,
                    cc_c_plus_count=cc_c_plus,
                    covered_lines=cov_lines,
                    num_statements=num_stmts,
                    covered_branches=cov_branches,
                    num_branches=num_branches,
                    missing_lines_str=missing_str,
                    has_coverage=file_has_cov,
                )
            )

    return file_telemetry, cc_list, mi_list


def aggregate_batch_rollups(
    file_telemetry: list[FileTelemetryMetric],
) -> list[BatchRollupMetrics]:
    """Roll up per-file telemetry into canonical GDA Audit Batch summary rows."""
    grouped: dict[str, list[FileTelemetryMetric]] = {}
    for ft in file_telemetry:
        grouped.setdefault(ft.batch_id, []).append(ft)

    ordered_keys = list(CANONICAL_BATCH_ORDER)
    for extra_key in sorted(grouped):
        if extra_key not in ordered_keys:
            ordered_keys.append(extra_key)

    rollups: list[BatchRollupMetrics] = []
    for batch_id in ordered_keys:
        items = grouped.get(batch_id, [])
        if not items:
            continue
        rollups.append(
            BatchRollupMetrics(
                batch_id=batch_id,
                file_count=len(items),
                loc=sum(i.loc for i in items),
                lloc=sum(i.lloc for i in items),
                sloc=sum(i.sloc for i in items),
                blank=sum(i.blank for i in items),
                comments=sum(i.comments for i in items),
                docstrings=sum(i.docstrings for i in items),
                block_count=sum(i.block_count for i in items),
                sum_cc=sum(i.sum_cc for i in items),
                cc_c_plus_count=sum(i.cc_c_plus_count for i in items),
                mi_below_a_count=sum(1 for i in items if i.mi_score < 20.0),
                covered_lines=sum(i.covered_lines for i in items),
                num_statements=sum(i.num_statements for i in items),
                covered_branches=sum(i.covered_branches for i in items),
                num_branches=sum(i.num_branches for i in items),
                has_coverage=any(i.has_coverage for i in items),
            )
        )
    return rollups


def _render_batch_scorecard_section(data: ScoringReportData) -> list[str]:
    """Render Section 1: Canonical Audit Batch Rollup Scorecard."""
    lines: list[str] = [
        "1. CANONICAL AUDIT BATCH ROLLUP SCORECARD (radon raw + cc + mi + pytest --cov)",
        "-" * 134,
        (
            f"{'Batch ID':14s} | {'Files':>5s} | {'LOC':>6s} | {'LLOC':>6s} | "
            f"{'SLOC':>6s} | {'Blank':>5s} | {'# Cmt':>5s} | {'Docstr':>6s} | "
            f"{'(C+Doc)/SLOC':>12s} | {'AvgCC':>5s} | {'CC C+':>5s} | {'MI<A':>4s} | "
            f"{'StmtCov':>7s} | {'BrCov':>7s} | {'TotCov':>7s}"
        ),
        "-" * 134,
    ]

    tot_files = tot_loc = tot_lloc = tot_sloc = tot_blank = tot_cmt = tot_doc = 0
    tot_blocks = tot_sum_cc = tot_cc_c = tot_mi_b = 0
    tot_cov_l = tot_stmts = tot_cov_b = tot_br = 0
    any_cov = False

    for br in data.batch_rollups:
        tot_files += br.file_count
        tot_loc += br.loc
        tot_lloc += br.lloc
        tot_sloc += br.sloc
        tot_blank += br.blank
        tot_cmt += br.comments
        tot_doc += br.docstrings
        tot_blocks += br.block_count
        tot_sum_cc += br.sum_cc
        tot_cc_c += br.cc_c_plus_count
        tot_mi_b += br.mi_below_a_count
        tot_cov_l += br.covered_lines
        tot_stmts += br.num_statements
        tot_cov_b += br.covered_branches
        tot_br += br.num_branches
        if br.has_coverage:
            any_cov = True

        stmt_str = f"{br.stmt_cov_pct:6.1f}%" if br.has_coverage else "   N/A "
        br_str = f"{br.branch_cov_pct:6.1f}%" if br.has_coverage else "   N/A "
        tot_str = f"{br.total_cov_pct:6.1f}%" if br.has_coverage else "   N/A "

        lines.append(
            f"{br.batch_id:14s} | {br.file_count:5d} | {br.loc:6d} | {br.lloc:6d} | "
            f"{br.sloc:6d} | {br.blank:5d} | {br.comments:5d} | {br.docstrings:6d} | "
            f"{br.doc_to_sloc_pct:11.1f}% | {br.avg_cc:5.2f} | {br.cc_c_plus_count:5d} | "
            f"{br.mi_below_a_count:4d} | {stmt_str:>7s} | {br_str:>7s} | {tot_str:>7s}"
        )

    tot_doc_pct = ((tot_cmt + tot_doc) / tot_sloc * 100.0) if tot_sloc > 0 else 0.0
    tot_avg_cc = (tot_sum_cc / tot_blocks) if tot_blocks > 0 else 0.0
    if any_cov:
        s_pct = (tot_cov_l / tot_stmts * 100.0) if tot_stmts > 0 else 100.0
        b_pct = (tot_cov_b / tot_br * 100.0) if tot_br > 0 else 100.0
        denom = tot_stmts + tot_br
        t_pct = ((tot_cov_l + tot_cov_b) / denom * 100.0) if denom > 0 else 100.0
        s_str, b_str, t_str = f"{s_pct:6.1f}%", f"{b_pct:6.1f}%", f"{t_pct:6.1f}%"
    else:
        s_str = b_str = t_str = "   N/A "

    lines.append("-" * 134)
    lines.append(
        f"{'TOTAL (SRC)':14s} | {tot_files:5d} | {tot_loc:6d} | {tot_lloc:6d} | "
        f"{tot_sloc:6d} | {tot_blank:5d} | {tot_cmt:5d} | {tot_doc:6d} | "
        f"{tot_doc_pct:11.1f}% | {tot_avg_cc:5.2f} | {tot_cc_c:5d} | "
        f"{tot_mi_b:4d} | {s_str:>7s} | {b_str:>7s} | {t_str:>7s}"
    )
    return lines


def _render_cc_section(data: ScoringReportData) -> list[str]:
    """Render Section 2: Cyclomatic Complexity Summary & Hotspots (CC >= 11)."""
    total_blocks = len(data.cc_metrics)
    avg_cc = sum(b.complexity for b in data.cc_metrics) / total_blocks if total_blocks > 0 else 0.0
    avg_grade = cc_rank(avg_cc) if total_blocks > 0 else "A"

    cc_counts: dict[str, int] = dict.fromkeys(("A", "B", "C", "D", "E", "F"), 0)
    for b in data.cc_metrics:
        cc_counts[b.grade] = cc_counts.get(b.grade, 0) + 1

    lines: list[str] = [
        "",
        "2. CYCLOMATIC COMPLEXITY SUMMARY & HOTSPOTS (radon cc)",
        "-" * 134,
        f"Total Blocks Analyzed : {total_blocks}",
        f"Average Complexity    : {avg_grade} ({avg_cc:.2f})",
        "Grade Distribution    : "
        + ", ".join(
            f"{g}={cc_counts[g]} ({(cc_counts[g] / total_blocks * 100.0) if total_blocks else 0.0:.1f}%)"
            for g in ("A", "B", "C", "D", "E", "F")
        ),
        "",
        "Blocks with Complexity >= 11 (Grade C or lower):",
    ]

    hotspots = sorted(
        (b for b in data.cc_metrics if b.complexity >= 11),
        key=lambda x: (-x.complexity, x.file_path, x.lineno),
    )
    if not hotspots:
        lines.append("  None! All blocks achieved Grade A or B (CC <= 10).")
    else:
        for h in hotspots:
            lines.append(
                f"  [{h.batch_id:12s}] [{h.grade} ({h.complexity:2d})] "
                f"{h.file_path}:{h.lineno} ({h.block_type} {h.name})"
            )
    return lines


def _render_mi_section(data: ScoringReportData) -> list[str]:
    """Render Section 3: Maintainability Index Summary & Hotspots (MI < 20.0)."""
    total_mods = len(data.mi_metrics)
    mi_counts: dict[str, int] = dict.fromkeys(("A", "B", "C"), 0)
    for m in data.mi_metrics:
        mi_counts[m.grade] = mi_counts.get(m.grade, 0) + 1

    lines: list[str] = [
        "",
        "3. MAINTAINABILITY INDEX SUMMARY & HOTSPOTS (radon mi)",
        "-" * 134,
        f"Total Modules Analyzed : {total_mods}",
        "Grade Distribution     : "
        + ", ".join(
            f"{g}={mi_counts[g]} ({(mi_counts[g] / total_mods * 100.0) if total_mods else 0.0:.1f}%)"
            for g in ("A", "B", "C")
        ),
        "",
        "Modules Scored Below Grade A (MI < 20.0):",
    ]

    low_mi = sorted(
        (m for m in data.mi_metrics if m.mi_score < 20.0),
        key=lambda x: (x.mi_score, x.file_path),
    )
    if not low_mi:
        lines.append("  None! 100% of modules achieved Grade A (MI >= 20.0).")
    else:
        for m in low_mi:
            lines.append(f"  [{m.batch_id:12s}] [{m.grade} ({m.mi_score:5.2f})] {m.file_path}")
    return lines


def _render_file_telemetry_section(data: ScoringReportData) -> list[str]:
    """Render Section 4: Complete Per-File Telemetry Table for Master Sheet ingestion."""
    lines: list[str] = [
        "",
        "4. COMPLETE PER-FILE TELEMETRY TABLE (Master Sheet Tab 2: Raw_Module_Telemetry)",
        "-" * 134,
        (
            f"{'Batch ID':12s} | {'File Path':52s} | {'LOC':>5s} | {'LLOC':>5s} | "
            f"{'SLOC':>5s} | {'Blank':>5s} | {'Cmt':>4s} | {'Doc':>4s} | {'Doc%':>6s} | "
            f"{'MI':>9s} | {'MaxCC':>7s} | {'MaxCC Symbol':24s} | {'TotCov':>7s} | {'Missing Lines'}"
        ),
        "-" * 134,
    ]

    for ft in data.file_telemetry:
        cov_str = f"{ft.total_cov_pct:6.1f}%" if ft.has_coverage else "   N/A "
        mi_str = f"{ft.mi_grade} ({ft.mi_score:5.1f})"
        cc_str = f"{ft.max_cc_grade} ({ft.max_cc:2d})"
        lines.append(
            f"{ft.batch_id:12s} | {ft.file_path:52s} | {ft.loc:5d} | {ft.lloc:5d} | "
            f"{ft.sloc:5d} | {ft.blank:5d} | {ft.comments:4d} | {ft.docstrings:4d} | "
            f"{ft.doc_to_sloc_pct:5.1f}% | {mi_str:>9s} | {cc_str:>7s} | "
            f"{ft.max_cc_symbol[:24]:24s} | {cov_str:>7s} | {ft.missing_lines_str}"
        )
    return lines


def format_scoring_report(data: ScoringReportData) -> str:
    """Render the complete 4-section Phase 0 GDA Code Scoring Report as text."""
    lines: list[str] = [
        "=" * 134,
        "GDA WORKSPACE PHASE 0 CODE SCORING & COVERAGE TELEMETRY REPORT",
        f"Generated At   : {data.generated_at}",
        f"Workspace Root : {data.workspace_root}",
    ]

    if data.pytest_result.ran_pytest:
        lines.append(
            f"Pytest Cov     : exit={data.pytest_result.returncode} ({data.pytest_result.summary_output})"
        )
    else:
        lines.append(f"Pytest Cov     : {data.pytest_result.summary_output}")

    if data.ruff_result.ran_ruff:
        lines.append(
            f"Ruff Format    : exit={data.ruff_result.format_returncode} ({data.ruff_result.format_output})"
        )
        lines.append(
            f"Ruff Check     : exit={data.ruff_result.check_returncode} ({data.ruff_result.check_output})"
        )
    else:
        lines.append("Ruff / Mypy    : DEFERRED TO BATCH GATES (--run-ruff not specified)")

    lines.extend(["=" * 134, ""])
    lines.extend(_render_batch_scorecard_section(data))
    lines.extend(_render_cc_section(data))
    lines.extend(_render_mi_section(data))
    lines.extend(_render_file_telemetry_section(data))
    lines.append("")
    return "\n".join(lines)


def generate_scoring_report(
    workspace_root: Path | None = None,
    output_path: Path | str = DEFAULT_REPORT_PATH,
    run_ruff: bool = False,
    run_pytest: bool = True,
    cov_json_path: Path | str = DEFAULT_COV_JSON_PATH,
) -> tuple[Path, ScoringReportData]:
    """Execute Phase 0 telemetry collection and write the unified report file."""
    root = workspace_root if workspace_root is not None else resolve_workspace_root()

    if run_ruff:
        ruff_res = run_ruff_updates(root)
    else:
        ruff_res = RuffExecutionResult(
            ran_ruff=False,
            format_returncode=0,
            format_output="Deferred to batch verification gates.",
            check_returncode=0,
            check_output="Deferred to batch verification gates.",
        )

    cov_rel_str = str(cov_json_path)
    if run_pytest:
        pytest_res = run_pytest_coverage(root, cov_json_rel_path=cov_rel_str)
    else:
        existing_cov = cov_json_path if isinstance(cov_json_path, Path) else root / cov_json_path
        pytest_res = PytestExecutionResult(
            ran_pytest=False,
            returncode=0,
            summary_output=(
                f"Loaded existing {cov_rel_str}"
                if existing_cov.is_file()
                else "SKIPPED (--no-pytest flag specified)"
            ),
            cov_json_path=existing_cov if existing_cov.is_file() else None,
        )

    cov_map = load_coverage_json(root, cov_json_path)
    raw_metrics = collect_domain_raw_metrics(root)
    file_telemetry, cc_metrics, mi_metrics = collect_file_telemetry(
        root,
        source_dirs=("src",),
        coverage_map=cov_map,
    )
    batch_rollups = aggregate_batch_rollups(file_telemetry)

    report_data = ScoringReportData(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        workspace_root=root,
        ruff_result=ruff_res,
        pytest_result=pytest_res,
        raw_metrics=raw_metrics,
        batch_rollups=batch_rollups,
        file_telemetry=file_telemetry,
        cc_metrics=cc_metrics,
        mi_metrics=mi_metrics,
    )

    resolved_out = output_path if isinstance(output_path, Path) else root / output_path
    resolved_out.parent.mkdir(parents=True, exist_ok=True)
    resolved_out.write_text(format_scoring_report(report_data), encoding="utf-8")
    return resolved_out, report_data


def _build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser for gd_code_scoring.py."""
    parser = argparse.ArgumentParser(
        description="Generate the Phase 0 GDA code scoring and pytest coverage telemetry report.",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Explicit workspace root directory (defaults to auto-resolved root).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=DEFAULT_REPORT_PATH,
        help=f"Output report file path (default: {DEFAULT_REPORT_PATH}).",
    )
    parser.add_argument(
        "--no-pytest",
        action="store_true",
        help="Skip running pytest --cov (will still ingest --cov-json if the file exists).",
    )
    parser.add_argument(
        "--cov-json",
        type=str,
        default=DEFAULT_COV_JSON_PATH,
        help=f"Coverage JSON path to write/read (default: {DEFAULT_COV_JSON_PATH}).",
    )
    parser.add_argument(
        "--run-ruff",
        action="store_true",
        help="Opt-in to execute ruff format and ruff check --fix during Phase 0.",
    )
    parser.add_argument(
        "--no-ruff",
        action="store_true",
        help="Legacy flag retained for CLI compatibility (Ruff is now off by default).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print the full generated report text to stdout.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable diagnostic debug output.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for Phase 0 GDA code scoring and coverage report generation."""
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    should_run_ruff = bool(args.run_ruff and not args.no_ruff)
    out_file, data = generate_scoring_report(
        workspace_root=args.root,
        output_path=args.output,
        run_ruff=should_run_ruff,
        run_pytest=not args.no_pytest,
        cov_json_path=args.cov_json,
    )

    if args.verbose or args.debug:
        print(out_file.read_text(encoding="utf-8"))
    print(
        f"Unified Code Scoring Report written to: {out_file} "
        f"({len(data.file_telemetry)} modules across {len(data.batch_rollups)} batches)"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
