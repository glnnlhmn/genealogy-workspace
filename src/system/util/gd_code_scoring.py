"""Path: src/system/util/gd_code_scoring.py

Unified code quality, line count, cyclomatic complexity, and maintainability scoring tool.

Operational Role:
    Executes Ruff formatting and lint autofixes across workspace targets, computes
    raw line metrics (LOC, LLOC, SLOC, Blank, Inline Comments, Docstrings, and
    Comment-to-SLOC ratios) via radon.raw, evaluates Cyclomatic Complexity (CC)
    via radon.complexity and Maintainability Index (MI) via radon.metrics, and
    emits a single consolidated report (reports/gd_code_scoring_report.txt)
    designed for direct review in Gemini. Displays live stage progress to the
    terminal unless --silent (-q) is specified.

Usage:
    python src/system/util/gd_code_scoring.py [--no-ruff] [--silent] [--output PATH] [--root PATH]
"""

from __future__ import annotations

import argparse
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
    "BlockCCMetric",
    "DomainRawMetrics",
    "FileMIMetric",
    "RuffExecutionResult",
    "ScoringReportData",
    "collect_cc_metrics",
    "collect_domain_raw_metrics",
    "collect_mi_metrics",
    "format_scoring_report",
    "generate_scoring_report",
    "main",
    "run_ruff_updates",
]

DEFAULT_REPORT_PATH: str = "reports/gd_code_scoring_report.txt"

# Canonical domain roots evaluated for raw SLOC and comment density tables
DEFAULT_DOMAINS: tuple[tuple[str, str], ...] = (
    ("src/gda", "src/gda"),
    ("src/cli", "src/cli"),
    ("src/ancestry_desk", "src/ancestry_desk"),
    ("src/system", "src/system"),
    ("tests", "tests"),
)


@dataclass(frozen=True, kw_only=True)
class RuffExecutionResult:
    """Outcome of running Ruff format and lint check steps."""

    ran_ruff: bool
    format_returncode: int
    format_output: str
    check_returncode: int
    check_output: str


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

    file_path: str
    block_type: str
    name: str
    lineno: int
    complexity: int
    grade: str


@dataclass(frozen=True, kw_only=True)
class FileMIMetric:
    """Maintainability Index (MI) score and letter grade for a Python module."""

    file_path: str
    mi_score: float
    grade: str


@dataclass(frozen=True, kw_only=True)
class ScoringReportData:
    """Complete dataset assembled for the unified GDA code scoring report."""

    generated_at: str
    workspace_root: Path
    ruff_result: RuffExecutionResult
    raw_metrics: list[DomainRawMetrics]
    cc_metrics: list[BlockCCMetric]
    mi_metrics: list[FileMIMetric]


def _notify(msg: str, *, silent: bool = False) -> None:
    """Print a live status notice to stdout unless silent mode is active."""
    if not silent:
        print(msg, flush=True)


def _discover_python_files(target_dir: Path) -> list[Path]:
    """Return sorted list of Python files under target_dir excluding caches."""
    if not target_dir.is_dir():
        return []
    # Filter out __pycache__ or hidden virtual environment directories
    return sorted(
        p
        for p in target_dir.rglob("*.py")
        if "__pycache__" not in p.parts and not any(part.startswith(".") for part in p.parts)
    )


def run_ruff_updates(
    workspace_root: Path,
    targets: tuple[str, ...] = ("src", "tests"),
    *,
    silent: bool = False,
) -> RuffExecutionResult:
    """Execute ruff format and ruff check --fix on workspace targets."""
    existing_targets = [t for t in targets if (workspace_root / t).exists()]
    if not existing_targets:
        _notify("  -> No target directories found for Ruff.", silent=silent)
        return RuffExecutionResult(
            ran_ruff=True,
            format_returncode=0,
            format_output="No target directories found for ruff.",
            check_returncode=0,
            check_output="No target directories found for ruff.",
        )

    _notify(f"  -> Running 'ruff format' on {', '.join(existing_targets)}...", silent=silent)
    fmt_proc = subprocess.run(
        [sys.executable, "-m", "ruff", "format", *existing_targets],
        cwd=str(workspace_root),
        capture_output=True,
        text=True,
        check=False,
    )
    fmt_out = (fmt_proc.stdout + "\n" + fmt_proc.stderr).strip()

    _notify(f"  -> Running 'ruff check --fix' on {', '.join(existing_targets)}...", silent=silent)
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
    *,
    silent: bool = False,
) -> list[DomainRawMetrics]:
    """Compute raw line and comment counts across configured workspace domains."""
    results: list[DomainRawMetrics] = []
    for label, rel_path in domains:
        target_dir = workspace_root / rel_path
        py_files = _discover_python_files(target_dir)
        if not py_files:
            continue

        _notify(
            f"  -> Scanning domain '{label}' ({len(py_files)} Python files)...",
            silent=silent,
        )
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
    *,
    silent: bool = False,
) -> list[BlockCCMetric]:
    """Collect Cyclomatic Complexity (CC) metrics for all blocks under source_dirs."""
    metrics: list[BlockCCMetric] = []
    for rel_dir in source_dirs:
        py_files = _discover_python_files(workspace_root / rel_dir)
        total_files = len(py_files)
        for idx, py_file in enumerate(py_files, start=1):
            if idx % 75 == 0 or idx == total_files:
                _notify(
                    f"  -> CC analysis progress ({rel_dir}): {idx}/{total_files} files...",
                    silent=silent,
                )
            rel_path = py_file.relative_to(workspace_root).as_posix()
            source_text = py_file.read_text(encoding="utf-8")
            for blk in cc_visit(source_text):
                b_type, b_name = _format_block_label(blk)
                comp = int(blk.complexity)
                metrics.append(
                    BlockCCMetric(
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
    *,
    silent: bool = False,
) -> list[FileMIMetric]:
    """Collect Maintainability Index (MI) scores for all modules under source_dirs."""
    metrics: list[FileMIMetric] = []
    for rel_dir in source_dirs:
        py_files = _discover_python_files(workspace_root / rel_dir)
        total_files = len(py_files)
        for idx, py_file in enumerate(py_files, start=1):
            if idx % 75 == 0 or idx == total_files:
                _notify(
                    f"  -> MI analysis progress ({rel_dir}): {idx}/{total_files} files...",
                    silent=silent,
                )
            rel_path = py_file.relative_to(workspace_root).as_posix()
            source_text = py_file.read_text(encoding="utf-8")
            score = float(mi_visit(source_text, multi=True))
            metrics.append(
                FileMIMetric(
                    file_path=rel_path,
                    mi_score=score,
                    grade=str(mi_rank(score)),
                )
            )
    return metrics


def _render_ruff_section(ruff_result: RuffExecutionResult) -> list[str]:
    """Format Section 1 (Ruff Format & Lint status)."""
    lines = [
        "1. RUFF FORMAT & LINT AUTO-UPDATE SUMMARY",
        "-" * 94,
    ]
    if not ruff_result.ran_ruff:
        lines.append("Ruff execution : SKIPPED (--no-ruff flag specified)")
    else:
        lines.append(
            f"Ruff Format (exit={ruff_result.format_returncode}): {ruff_result.format_output}"
        )
        lines.append(
            f"Ruff Check  (exit={ruff_result.check_returncode}): {ruff_result.check_output}"
        )
    return lines


def _render_raw_section(raw_metrics: list[DomainRawMetrics]) -> list[str]:
    """Format Section 2 (Raw Line Counts & Documentation Ratio table)."""
    lines = [
        "",
        "2. LINE COUNTS & DOCUMENTATION RATIO (radon raw)",
        "-" * 94,
        f"{'Domain':18s} | {'Files':>5s} | {'LOC':>7s} | {'LLOC':>7s} | "
        f"{'SLOC':>7s} | {'Blank':>6s} | {'# Cmt':>6s} | {'Docstr':>7s} | {'(C+Doc)/SLOC':>12s}",
        "-" * 94,
    ]

    tot_files = tot_loc = tot_lloc = tot_sloc = tot_blank = tot_cmt = tot_doc = 0
    for dm in raw_metrics:
        tot_files += dm.file_count
        tot_loc += dm.loc
        tot_lloc += dm.lloc
        tot_sloc += dm.sloc
        tot_blank += dm.blank
        tot_cmt += dm.comments
        tot_doc += dm.docstrings
        lines.append(
            f"{dm.label:18s} | {dm.file_count:5d} | {dm.loc:7d} | {dm.lloc:7d} | "
            f"{dm.sloc:7d} | {dm.blank:6d} | {dm.comments:6d} | {dm.docstrings:7d} | "
            f"{dm.doc_to_sloc_pct:11.1f}%"
        )

    tot_pct = ((tot_cmt + tot_doc) / tot_sloc * 100.0) if tot_sloc > 0 else 0.0
    lines.append("-" * 94)
    lines.append(
        f"{'TOTAL WORKSPACE':18s} | {tot_files:5d} | {tot_loc:7d} | {tot_lloc:7d} | "
        f"{tot_sloc:7d} | {tot_blank:6d} | {tot_cmt:6d} | {tot_doc:7d} | {tot_pct:11.1f}%"
    )
    return lines


def _format_cc_hotspots(cc_metrics: list[BlockCCMetric]) -> list[str]:
    """Render list of blocks with Cyclomatic Complexity >= 11."""
    high_cc = sorted(
        (b for b in cc_metrics if b.complexity >= 11),
        key=lambda x: (-x.complexity, x.file_path, x.lineno),
    )
    if not high_cc:
        return ["  None! All blocks achieved Grade A or B (CC <= 10)."]
    return [
        f"  [{b.grade} ({b.complexity:2d})] {b.file_path}:{b.lineno} ({b.block_type} {b.name})"
        for b in high_cc
    ]


def _render_cc_section(cc_metrics: list[BlockCCMetric]) -> list[str]:
    """Format Section 3 (Cyclomatic Complexity distribution and hotspots)."""
    total_blocks = len(cc_metrics)
    avg_cc = sum(b.complexity for b in cc_metrics) / total_blocks if total_blocks > 0 else 0.0
    avg_grade = cc_rank(avg_cc) if total_blocks > 0 else "A"

    cc_counts: dict[str, int] = dict.fromkeys(("A", "B", "C", "D", "E", "F"), 0)
    for b in cc_metrics:
        cc_counts[b.grade] = cc_counts.get(b.grade, 0) + 1

    denom = float(total_blocks) if total_blocks > 0 else 1.0
    dist_parts = [
        f"{g}={cc_counts[g]} ({(cc_counts[g] / denom * 100.0 if total_blocks else 0.0):.1f}%)"
        for g in ("A", "B", "C", "D", "E", "F")
    ]
    return [
        "",
        "3. CYCLOMATIC COMPLEXITY SUMMARY (radon cc)",
        "-" * 94,
        f"Total Blocks Analyzed : {total_blocks}",
        f"Average Complexity    : {avg_grade} ({avg_cc:.2f})",
        "Grade Distribution    : " + ", ".join(dist_parts),
        "",
        "Blocks with Complexity >= 11 (Grade C or lower):",
        *_format_cc_hotspots(cc_metrics),
    ]


def _format_low_mi_modules(mi_metrics: list[FileMIMetric]) -> list[str]:
    """Render list of modules scored below Grade A (MI < 20.0)."""
    low_mi = sorted(
        (m for m in mi_metrics if m.grade != "A"),
        key=lambda x: (x.mi_score, x.file_path),
    )
    if not low_mi:
        return ["  None! 100% of modules achieved Grade A (MI >= 20.0)."]
    return [f"  [{m.grade} ({m.mi_score:5.2f})] {m.file_path}" for m in low_mi]


def _render_mi_section(mi_metrics: list[FileMIMetric]) -> list[str]:
    """Format Sections 4 & 5 (Maintainability Index summary and full module listing)."""
    total_mi = len(mi_metrics)
    mi_counts: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    for m in mi_metrics:
        mi_counts[m.grade] = mi_counts.get(m.grade, 0) + 1

    denom = float(total_mi) if total_mi > 0 else 1.0
    dist_parts = [
        f"{g}={mi_counts[g]} ({(mi_counts[g] / denom * 100.0 if total_mi else 0.0):.1f}%)"
        for g in ("A", "B", "C")
    ]
    return [
        "",
        "4. MAINTAINABILITY INDEX SUMMARY (radon mi)",
        "-" * 94,
        f"Total Modules Analyzed : {total_mi}",
        "Grade Distribution     : " + ", ".join(dist_parts),
        "",
        "Modules Scored Below Grade A (MI < 20.0):",
        *_format_low_mi_modules(mi_metrics),
        "",
        "5. COMPLETE MODULE MAINTAINABILITY INDEX LISTING",
        "-" * 94,
        *(f"{m.file_path} - {m.grade} ({m.mi_score:.2f})" for m in mi_metrics),
        "",
    ]


def format_scoring_report(data: ScoringReportData) -> str:
    """Render the complete multi-section GDA Code Scoring Report as text."""
    lines: list[str] = [
        "=" * 94,
        "GDA WORKSPACE CODE SCORING & QUALITY REPORT",
        f"Generated At   : {data.generated_at}",
        f"Workspace Root : {data.workspace_root}",
        "=" * 94,
        "",
        *_render_ruff_section(data.ruff_result),
        *_render_raw_section(data.raw_metrics),
        *_render_cc_section(data.cc_metrics),
        *_render_mi_section(data.mi_metrics),
    ]
    return "\n".join(lines)


def generate_scoring_report(
    workspace_root: Path | str = ".",
    output_path: Path | str | None = None,
    *,
    run_ruff: bool = True,
    silent: bool = False,
    domains: tuple[tuple[str, str], ...] = DEFAULT_DOMAINS,
    source_dirs: tuple[str, ...] = ("src",),
) -> tuple[Path, ScoringReportData]:
    """Execute Ruff and Radon analyses and write the unified report to disk."""
    root = resolve_workspace_root(str(workspace_root))
    _notify(f"[gd_code_scoring] Workspace root: {root}", silent=silent)

    if run_ruff:
        _notify("[1/5] Running Ruff format & lint auto-updates...", silent=silent)
        ruff_res = run_ruff_updates(root, silent=silent)
    else:
        _notify("[1/5] Skipping Ruff format & lint (--no-ruff specified).", silent=silent)
        ruff_res = RuffExecutionResult(
            ran_ruff=False,
            format_returncode=0,
            format_output="Skipped",
            check_returncode=0,
            check_output="Skipped",
        )

    _notify("[2/5] Computing raw line & documentation counts (radon raw)...", silent=silent)
    raw_metrics = collect_domain_raw_metrics(root, domains=domains, silent=silent)

    _notify("[3/5] Evaluating Cyclomatic Complexity across blocks (radon cc)...", silent=silent)
    cc_metrics = collect_cc_metrics(root, source_dirs=source_dirs, silent=silent)

    _notify("[4/5] Evaluating Maintainability Index across modules (radon mi)...", silent=silent)
    mi_metrics = collect_mi_metrics(root, source_dirs=source_dirs, silent=silent)

    report_data = ScoringReportData(
        generated_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        workspace_root=root,
        ruff_result=ruff_res,
        raw_metrics=raw_metrics,
        cc_metrics=cc_metrics,
        mi_metrics=mi_metrics,
    )

    target_out = Path(output_path) if output_path is not None else Path(DEFAULT_REPORT_PATH)
    resolved_out = target_out if target_out.is_absolute() else (root / target_out)
    resolved_out.parent.mkdir(parents=True, exist_ok=True)

    _notify(f"[5/5] Writing unified report to {resolved_out}...", silent=silent)
    report_text = format_scoring_report(report_data)
    resolved_out.write_text(report_text, encoding="utf-8")

    return resolved_out, report_data


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser for gd_code_scoring."""
    parser = argparse.ArgumentParser(
        prog="gd_code_scoring",
        description=(
            "Run Ruff formatting/fixes and generate a unified Radon SLOC, "
            "Cyclomatic Complexity, and Maintainability Index report."
        ),
    )
    parser.add_argument(
        "--root",
        type=str,
        default=".",
        help="Workspace root directory (default: auto-detected from pyproject.toml).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=DEFAULT_REPORT_PATH,
        help=f"Output report file path (default: '{DEFAULT_REPORT_PATH}').",
    )
    parser.add_argument(
        "--no-ruff",
        action="store_true",
        help="Skip running 'ruff format' and 'ruff check --fix' before scoring.",
    )
    parser.add_argument(
        "-q",
        "--silent",
        action="store_true",
        help="Suppress live console progress messages.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for gd_code_scoring."""
    parser = build_parser()
    args = parser.parse_args(argv)

    report_path, data = generate_scoring_report(
        workspace_root=args.root,
        output_path=args.output,
        run_ruff=not args.no_ruff,
        silent=args.silent,
    )

    if not args.silent:
        total_blocks = len(data.cc_metrics)
        avg_cc = (
            sum(b.complexity for b in data.cc_metrics) / total_blocks if total_blocks > 0 else 0.0
        )
        print(f"Unified Code Scoring Report written to: {report_path}", flush=True)
        print(
            f"Analyzed {len(data.mi_metrics)} source modules and {total_blocks} code blocks "
            f"(Average CC: {avg_cc:.2f}).",
            flush=True,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
