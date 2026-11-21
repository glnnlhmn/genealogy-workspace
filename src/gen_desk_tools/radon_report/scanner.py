"""Path: src/gen_desk_tools/radon_report/scanner.py

Combined Radon static analysis report generator (CC, MI, and RAW) for GenDesk Tools.

Operational Role:
    Runs Radon cyclomatic complexity (cc), maintainability index (mi), and raw
    line metrics across a target directory or mode and writes a consolidated
    report file using gen_desk_tools.core primitives.

Functions:
    format_radon_section: Run a single Radon subcommand and format its output block.
    build_combined_radon_report: Assemble CC, MI, and RAW sections into report text.
    generate_radon_report: Write the combined Radon report to the target directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from gen_desk_tools.core.backup import atomic_write_text
from gen_desk_tools.core.process import run_command
from gen_desk_tools.core.workspace import MODE_TARGETS, resolve_report_path

__version__ = "1.0.0+build.2"

__all__ = [
    "DEFAULT_MAX_DEPTH",
    "MODE_TARGETS",
    "build_combined_radon_report",
    "format_radon_section",
    "generate_radon_report",
]

DEFAULT_MAX_DEPTH: int = 7


def format_radon_section(
    metric: str,
    targets: list[str],
    workspace_root: Path,
    *,
    min_grade: str | None = None,
) -> str:
    """Execute a Radon metric subcommand ('cc', 'mi', or 'raw') and return a formatted block."""
    metric_lower = metric.lower()
    if metric_lower == "cc":
        cmd = [sys.executable, "-m", "radon", "cc", "-s", "-a"]
        if min_grade:
            cmd.extend(["-n", min_grade])
        title = "=== RADON CC ==="
    elif metric_lower == "mi":
        cmd = [sys.executable, "-m", "radon", "mi", "-s"]
        if min_grade:
            cmd.extend(["-n", min_grade])
        title = "=== RADON MI ==="
    elif metric_lower == "raw":
        cmd = [sys.executable, "-m", "radon", "raw", "-s"]
        title = "=== RADON RAW ==="
    else:
        raise ValueError(f"Unsupported Radon metric: '{metric}'. Expected 'cc', 'mi', or 'raw'.")

    res = run_command([*cmd, *targets], cwd=workspace_root, runner=subprocess.run)
    body = res.stdout.rstrip()
    if not body and res.stderr.strip():
        body = res.stderr.strip()
    return f"{title}\n{body}" if body else title


def _resolve_mode_targets(
    mode: str,
    root: Path,
    *,
    include_tests: bool = False,
) -> tuple[list[str], str]:
    """Resolve existing target paths and default report filename for a given mode."""
    if mode == "all":
        existing = [p for p in ("src", "tests") if (root / p).exists()]
        return (existing or ["."]), "GenDeskRadon_all.txt"
    if mode in MODE_TARGETS:
        src_rel, test_rel = MODE_TARGETS[mode]
        candidates = [src_rel, test_rel] if include_tests else [src_rel]
        existing = [rel for rel in candidates if (root / rel).exists()]
        suffix = "_tests" if include_tests else ""
        return existing, f"GenDeskRadon_{mode}{suffix}.txt"

    valid = ", ".join(sorted([*MODE_TARGETS, "all"]))
    raise ValueError(f"Unknown radon report mode: '{mode}'. Expected one of: {valid}.")


def build_combined_radon_report(
    targets: list[str],
    workspace_root: Path,
    *,
    min_grade: str | None = None,
) -> str:
    """Build the combined CC, MI, and RAW report string for existing targets."""
    if not targets:
        return "=== RADON CC ===\n\n=== RADON MI ===\n\n=== RADON RAW ===\n"
    sections = [
        format_radon_section("cc", targets, workspace_root, min_grade=min_grade),
        format_radon_section("mi", targets, workspace_root, min_grade=min_grade),
        format_radon_section("raw", targets, workspace_root, min_grade=min_grade),
    ]
    return "\n\n".join(sections) + "\n"


def generate_radon_report(
    mode: str = "gd_tools",
    *,
    include_tests: bool = False,
    workspace_root: Path | str = ".",
    reports_dir: Path | str = "reports",
    min_grade: str | None = None,
    output_filename: str | None = None,
) -> tuple[Path, int]:
    """Generate a combined Radon CC/MI/RAW report and write it atomically."""
    root = Path(workspace_root).resolve()
    targets, default_filename = _resolve_mode_targets(mode, root, include_tests=include_tests)
    content = build_combined_radon_report(targets, root, min_grade=min_grade)
    filename = output_filename or default_filename
    report_path = resolve_report_path(root, {}, filename, override_dir=Path(reports_dir))
    atomic_write_text(report_path, content)
    line_count = len(content.splitlines())
    return report_path, line_count
