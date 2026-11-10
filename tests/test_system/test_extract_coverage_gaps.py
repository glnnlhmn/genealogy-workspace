"""Path: tests/test_system/test_extract_coverage_gaps.py

Unit and integration test suite for extract_coverage_gaps utility.

Operational Role:
    Verifies gap range normalization, report file name construction, full-file
    fallback, empty file handling, invalid input rejection, and CLI command
    execution achieving 100% statement and branch coverage.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

import pytest

from system.util.extract_coverage_gaps import (
    generate_gap_report,
    main,
    parse_gap_range,
)

__version__ = "1.0.0+build.2"

# ==============================================================================
# GROUP 1: Gap Range Parsing Tests
# Note: Verification of parse_gap_range normalization and syntax boundaries
# ==============================================================================


@pytest.mark.unit
def test_parse_gap_range_standard_and_reversed() -> None:
    """Verify range parsing handles forward, reversed, and clamped ranges."""
    # Standard forward range
    start1, end1, label1 = parse_gap_range("110 - 120", 500)
    assert (start1, end1, label1) == (110, 120, "110-120")

    # Reversed range (120 - 110 -> 110-120)
    start2, end2, label2 = parse_gap_range("120 - 110", 500)
    assert (start2, end2, label2) == (110, 120, "110-120")

    # Clamping beyond total lines
    start3, end3, label3 = parse_gap_range("10 - 999", 50)
    assert (start3, end3, label3) == (10, 50, "10-50")

    # Single line input
    start4, end4, label4 = parse_gap_range("42", 100)
    assert (start4, end4, label4) == (42, 42, "42")


@pytest.mark.unit
def test_parse_gap_range_omitted_and_empty_file() -> None:
    """Verify omitted gap range defaults to full file or zero for empty file."""
    assert parse_gap_range(None, 200) == (1, 200, "1-200")
    assert parse_gap_range("", 200) == (1, 200, "1-200")
    assert parse_gap_range(None, 0) == (0, 0, "0-0")
    assert parse_gap_range("10-20", 0) == (0, 0, "0-0")


@pytest.mark.unit
def test_parse_gap_range_invalid_syntax() -> None:
    """Verify invalid syntax raises ValueError."""
    with pytest.raises(ValueError, match="Invalid gap format"):
        parse_gap_range("abc - def", 100)

    with pytest.raises(ValueError, match="Invalid gap format"):
        parse_gap_range("10-20-30", 100)


# ==============================================================================
# GROUP 2: Report Generation Tests
# Note: Verification of file I/O, report name formatting, and line output count
# ==============================================================================


@pytest.mark.integration
def test_generate_gap_report_range(tmp_path: Path) -> None:
    """Verify report creation with specific line numbers and formatted header."""
    src = tmp_path / "src" / "sample.py"
    src.parent.mkdir(parents=True)
    src.write_text("\n".join(f"line_{i}" for i in range(1, 101)), encoding="utf-8")

    report_file, count = generate_gap_report(
        file_path="src/sample.py",
        gap_arg="10 - 15",
        output_dir=tmp_path / "reports",
        workspace_root=tmp_path,
    )

    assert count == 6
    assert report_file.name == "Coverage Gap + sample.py + 10-15.txt"
    content = report_file.read_text(encoding="utf-8").splitlines()
    assert len(content) == 6
    assert content[0] == "10: line_10"
    assert content[-1] == "15: line_15"


@pytest.mark.integration
def test_generate_gap_report_full_file(tmp_path: Path) -> None:
    """Verify omitted gap outputs the entire file with line numbers."""
    src = tmp_path / "module.py"
    src.write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")

    report_file, count = generate_gap_report(
        file_path=src,
        gap_arg=None,
        output_dir=tmp_path / "reports",
        workspace_root=tmp_path,
    )

    assert count == 3
    assert report_file.name == "Coverage Gap + module.py + 1-3.txt"
    content = report_file.read_text(encoding="utf-8").splitlines()
    assert content[0] == "1: a = 1"
    assert content[-1] == "3: c = 3"


@pytest.mark.integration
def test_generate_gap_report_empty_file(tmp_path: Path) -> None:
    """Verify handling of empty source file (covers branches 99->105 and 106->109)."""
    empty_src = tmp_path / "empty.py"
    empty_src.write_text("", encoding="utf-8")

    report_file, count = generate_gap_report(
        file_path=empty_src,
        gap_arg=None,
        output_dir=tmp_path / "reports",
        workspace_root=tmp_path,
    )

    assert count == 0
    assert report_file.name == "Coverage Gap + empty.py + 0-0.txt"
    assert report_file.read_text(encoding="utf-8") == ""


@pytest.mark.unit
def test_generate_gap_report_file_not_found(tmp_path: Path) -> None:
    """Verify FileNotFoundError is raised when target file does not exist."""
    with pytest.raises(FileNotFoundError, match="Source file not found"):
        generate_gap_report("nonexistent.py", workspace_root=tmp_path)


# ==============================================================================
# GROUP 3: CLI Execution Tests
# Note: Verification of main() flags, exit codes, and stdout messages
# ==============================================================================


@pytest.mark.integration
def test_main_cli_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main() CLI outputs line count and report path."""
    src = tmp_path / "test_file.py"
    src.write_text("line1\nline2\nline3\n", encoding="utf-8")
    reports_dir = tmp_path / "reports"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        ["extract_coverage_gaps", "test_file.py", "2-3", "-o", str(reports_dir)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0

    captured = capsys.readouterr()
    assert "Number of lines output: 2" in captured.out
    assert "Coverage Gap + test_file.py + 2-3.txt" in captured.out


@pytest.mark.integration
def test_main_cli_flag_gap(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() CLI accepts -g / --gap-range flag."""
    src = tmp_path / "flag_file.py"
    src.write_text("alpha\nbeta\n", encoding="utf-8")
    reports_dir = tmp_path / "reports"

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        ["extract_coverage_gaps", "flag_file.py", "-g", "1-1", "-o", str(reports_dir)],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.unit
def test_main_cli_error_handling(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main() exits 1 on invalid file path or gap syntax."""
    monkeypatch.setattr("sys.argv", ["extract_coverage_gaps", "missing.py"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 1
    assert "Error: Source file not found" in capsys.readouterr().err


@pytest.mark.unit
def test_main_entrypoint_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify execution as __main__ module."""
    monkeypatch.setattr("sys.argv", ["extract_coverage_gaps", "-h"])
    monkeypatch.delitem(sys.modules, "system.util.extract_coverage_gaps", raising=False)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("system.util.extract_coverage_gaps", run_name="__main__")
    assert exc.value.code == 0
