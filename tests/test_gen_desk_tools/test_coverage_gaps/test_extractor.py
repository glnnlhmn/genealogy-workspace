"""Path: tests/test_gen_desk_tools/test_coverage_gaps/test_extractor.py

Unit, regression, and integration tests for gen_desk_tools.coverage_gaps.extractor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gen_desk_tools.coverage_gaps.extractor import generate_gap_report, parse_gap_range

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Primary range extraction and formatted line-numbered report creation.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_generate_gap_report_extracts_numbered_range_into_reports_dir(tmp_path: Path) -> None:
    """Verify generate_gap_report writes right-aligned line numbers for a requested range."""
    src_file = tmp_path / "src" / "sample.py"
    src_file.parent.mkdir(parents=True)
    src_file.write_text("line1\nline2\nline3\nline4\n", encoding="utf-8")

    report_path, count = generate_gap_report(
        "src/sample.py",
        "2-3",
        output_dir="reports",
        workspace_root=tmp_path,
    )

    assert count == 2
    assert report_path == tmp_path / "reports" / "Coverage Gap + sample.py + 2-3.txt"
    assert report_path.read_text(encoding="utf-8") == "2: line2\n3: line3\n"


# ==========================================================================
# GROUP 2: Range Parsing Logic
# Note: Single lines, reversed ranges, pytest-cov branch arrows, and clamping.
# ==========================================================================


@pytest.mark.unit
def test_parse_gap_range_handles_full_file_single_line_and_branch_arrows() -> None:
    """Verify parse_gap_range normalizes None, single lines, reversed spans, and arrows."""
    assert parse_gap_range(None, 10) == (1, 10, "1-10")
    assert parse_gap_range("   ", 10) == (1, 10, "1-10")
    assert parse_gap_range("5", 10) == (5, 5, "5")
    assert parse_gap_range("99", 10) == (10, 10, "10")
    assert parse_gap_range("8 - 3", 10) == (3, 8, "3-8")
    assert parse_gap_range("4->7", 10) == (4, 7, "4-7")


@pytest.mark.regression
def test_parse_gap_range_handles_empty_file_and_invalid_syntax() -> None:
    """Verify empty-file zero bounds and ValueError on malformed range strings."""
    assert parse_gap_range(None, 0) == (0, 0, "0-0")
    assert parse_gap_range("5", 0) == (0, 0, "0")
    assert parse_gap_range("2-5", 0) == (0, 0, "0-0")

    with pytest.raises(ValueError, match="Invalid gap format"):
        parse_gap_range("abc-def", 10)


# ==========================================================================
# GROUP 3: Edge Cases & Error Handling
# Note: Absolute paths, empty source files, and missing file errors.
# ==========================================================================


@pytest.mark.regression
def test_generate_gap_report_handles_empty_file_and_absolute_paths(tmp_path: Path) -> None:
    """Verify empty source files produce a 0-line report and accept absolute output paths."""
    empty_file = tmp_path / "empty.py"
    empty_file.write_text("", encoding="utf-8")
    abs_out = tmp_path / "custom_out"

    report_path, count = generate_gap_report(
        empty_file,
        None,
        output_dir=abs_out,
        workspace_root=tmp_path,
    )

    assert count == 0
    assert report_path == abs_out / "Coverage Gap + empty.py + 0-0.txt"
    assert report_path.read_text(encoding="utf-8") == ""


@pytest.mark.regression
def test_generate_gap_report_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """Verify generate_gap_report raises FileNotFoundError when target file does not exist."""
    with pytest.raises(FileNotFoundError, match="Source file not found"):
        generate_gap_report("src/missing.py", "1-5", workspace_root=tmp_path)
