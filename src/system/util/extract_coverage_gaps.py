"""Path: src/system/util/extract_coverage_gaps.py

Extract missing source lines and branch gap context with line numbers to reports/.

Operational Role:
    Extracts targeted line ranges (or entire files) with formatted line numbers
    from source code relative to workspace root and writes standardized gap reports
    to reports/Coverage Gap + <file_name> + <lines>.txt.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

__version__ = "1.0.0+build.1"


def parse_gap_range(gap_arg: str | None, total_lines: int) -> tuple[int, int, str]:
    """Parse and normalize line range specification into (start, end, label).

    Args:
        gap_arg: String line range (e.g., '110-120', '120 - 110', or None).
        total_lines: Total count of lines present in target file.

    Returns:
        tuple[int, int, str]: 1-based start line, end line, and range label string.

    Raises:
        ValueError: If line range syntax is invalid.
    """
    if not gap_arg or not gap_arg.strip():
        if total_lines == 0:
            return 0, 0, "0-0"
        return 1, total_lines, f"1-{total_lines}"

    m = re.match(r"^\s*(\d+)\s*[-–—]\s*(\d+)\s*$", gap_arg.strip())
    if not m:
        if gap_arg.strip().isdigit():
            n = int(gap_arg.strip())
            n = max(1, min(total_lines, n))
            return n, n, f"{n}"
        raise ValueError(f"Invalid gap format: '{gap_arg}'. Expected 'start-end' (e.g. 110-120).")

    n1, n2 = int(m.group(1)), int(m.group(2))
    start = min(n1, n2)
    end = max(n1, n2)

    if total_lines > 0:
        start = max(1, min(total_lines, start))
        end = max(1, min(total_lines, end))
    else:
        start, end = 0, 0

    return start, end, f"{start}-{end}"


def generate_gap_report(
    file_path: Path | str,
    gap_arg: str | None = None,
    output_dir: Path | str = "reports",
    workspace_root: Path | str = ".",
) -> tuple[Path, int]:
    """Extract line range with line numbers and write report file.

    Args:
        file_path: Relative or absolute path to target source file.
        gap_arg: Optional line range string (e.g. '110-120').
        output_dir: Directory where report is generated.
        workspace_root: Workspace root directory anchor.

    Returns:
        tuple[Path, int]: Path to created report file and total lines written.

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

    out_dir = Path(output_dir) if Path(output_dir).is_absolute() else (root / Path(output_dir))
    out_dir.mkdir(parents=True, exist_ok=True)

    report_filename = f"Coverage Gap + {resolved_target.name} + {lines_label}.txt"
    report_path = out_dir / report_filename

    extracted_lines: list[str] = []
    if total_lines > 0 and start <= end:
        width = len(str(end))
        for line_no in range(start, end + 1):
            line_content = source_lines[line_no - 1]
            extracted_lines.append(f"{line_no:{width}d}: {line_content}")

    report_content = "\n".join(extracted_lines)
    if extracted_lines:
        report_content += "\n"

    report_path.write_text(report_content, encoding="utf-8")
    return report_path, len(extracted_lines)


def main(argv: list[str] | None = None) -> None:
    """CLI orchestrator for single-gap coverage extraction."""
    parser = argparse.ArgumentParser(
        prog="extract_coverage_gaps",
        description="Extract target source line gaps with line numbers into reports/.",
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Target source file path relative to repository root (required).",
    )
    parser.add_argument(
        "gap",
        nargs="?",
        default=None,
        help="Optional line range (e.g. '110 - 120' or '120 - 110'). Omit to output entire file.",
    )
    parser.add_argument(
        "-g",
        "--gap-range",
        type=str,
        default=None,
        dest="flag_gap",
        help="Alternative flag for line range.",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default="reports",
        help="Destination directory for reports (default: 'reports').",
    )

    args = parser.parse_args(argv)

    gap_input = args.flag_gap if args.flag_gap is not None else args.gap

    try:
        report_file, lines_count = generate_gap_report(
            file_path=args.file_path,
            gap_arg=gap_input,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Number of lines output: {lines_count}")
    print(f"Report file created: {report_file.as_posix()}")
    sys.exit(0)


if __name__ == "__main__":
    main()
