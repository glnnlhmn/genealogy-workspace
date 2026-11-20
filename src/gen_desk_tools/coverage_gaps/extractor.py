"""Path: src/gen_desk_tools/coverage_gaps/extractor.py

Line-range parser and coverage gap report generator for GenDesk Coverage Gaps (gaps).

Operational Role:
    Parses line ranges (single line, start-end, or pytest-cov branch arrow
    start->end) and extracts formatted, line-numbered source context atomically
    into reports/Coverage Gap + <filename> + <range>.txt via core primitives.

Functions:
    parse_gap_range: Normalize a line-range specification into (start, end, label).
    generate_gap_report: Extract formatted source lines and write the gap report file.
"""

from __future__ import annotations

import re
from pathlib import Path

from gen_desk_tools.core.backup import atomic_write_text
from gen_desk_tools.core.workspace import resolve_report_path

__version__ = "1.0.0+build.2"

__all__ = [
    "generate_gap_report",
    "parse_gap_range",
]

_RANGE_RE = re.compile(r"^\s*(\d+)\s*(?:->|[-–—])\s*(\d+)\s*$")


def parse_gap_range(gap_arg: str | None, total_lines: int) -> tuple[int, int, str]:
    """Parse and normalize a line-range specification into (start, end, label).

    Args:
        gap_arg: Range string ('110-120', '222->226', '67') or None for full file.
        total_lines: Total line count of the target source file.

    Returns:
        Tuple of (1-based start line, 1-based end line, normalized range label).

    Raises:
        ValueError: If gap_arg does not match a valid line or range format.
    """
    if not gap_arg or not gap_arg.strip():
        if total_lines == 0:
            return 0, 0, "0-0"
        return 1, total_lines, f"1-{total_lines}"

    cleaned = gap_arg.strip()
    match = _RANGE_RE.match(cleaned)
    if not match:
        if cleaned.isdigit():
            if total_lines == 0:
                return 0, 0, "0"
            line_no = max(1, min(total_lines, int(cleaned)))
            return line_no, line_no, str(line_no)
        raise ValueError(
            f"Invalid gap format: '{gap_arg}'. Expected 'start-end', 'start->end', or a line number."
        )

    n1, n2 = int(match.group(1)), int(match.group(2))
    start, end = min(n1, n2), max(n1, n2)

    if total_lines > 0:
        start = max(1, min(total_lines, start))
        end = max(1, min(total_lines, end))
    else:
        start, end = 0, 0

    return start, end, f"{start}-{end}"


def generate_gap_report(
    file_path: Path | str,
    gap_arg: str | None = None,
    *,
    output_dir: Path | str = "reports",
    workspace_root: Path | str = ".",
) -> tuple[Path, int]:
    """Extract line-numbered source context and write the standardized gap report.

    Args:
        file_path: Relative or absolute path to the target source file.
        gap_arg: Optional line range string; omits to extract the entire file.
        output_dir: Destination directory for the report (relative to workspace_root or absolute).
        workspace_root: Canonical workspace root directory.

    Returns:
        Tuple of (created report Path, number of lines written).

    Raises:
        FileNotFoundError: If file_path does not exist on disk.
    """
    root = Path(workspace_root).resolve()
    target = Path(file_path)
    resolved_target = target if target.is_absolute() else (root / target)

    if not resolved_target.is_file():
        raise FileNotFoundError(f"Source file not found: {file_path}")

    source_lines = resolved_target.read_text(encoding="utf-8").splitlines()
    total_lines = len(source_lines)

    start, end, lines_label = parse_gap_range(gap_arg, total_lines)

    filename = f"Coverage Gap + {resolved_target.name} + {lines_label}.txt"
    report_path = resolve_report_path(root, {}, filename, override_dir=Path(output_dir))

    extracted_lines: list[str] = []
    if total_lines > 0 and start <= end:
        width = len(str(end))
        for line_no in range(start, end + 1):
            extracted_lines.append(f"{line_no:{width}d}: {source_lines[line_no - 1]}")

    report_content = "\n".join(extracted_lines) + ("\n" if extracted_lines else "")
    atomic_write_text(report_path, report_content)
    return report_path, len(extracted_lines)
