"""Path: tests/test_gen_desk_tools/test_radon_report/test_scanner.py

Unit, regression, and integration tests for gen_desk_tools.radon_report.scanner.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from gen_desk_tools.radon_report.scanner import (
    build_combined_radon_report,
    format_radon_section,
    generate_radon_report,
)

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end combined CC/MI/RAW report generation on a real Python file.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_generate_radon_report_writes_combined_sections_to_reports_dir(tmp_path: Path) -> None:
    """Verify generate_radon_report writes CC, MI, and RAW sections for a target mode."""
    pkg_dir = tmp_path / "src" / "gen_desk_tools"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "sample.py").write_text(
        '"""Sample module."""\n\ndef add(a: int, b: int) -> int:\n    return a + b\n',
        encoding="utf-8",
    )

    report_path, line_count = generate_radon_report(
        mode="gd_tools",
        workspace_root=tmp_path,
        reports_dir="reports",
        output_filename="radon_out.txt",
    )

    text = report_path.read_text(encoding="utf-8")
    assert report_path == tmp_path / "reports" / "radon_out.txt"
    assert line_count > 10
    assert "=== RADON CC ===" in text
    assert "=== RADON MI ===" in text
    assert "=== RADON RAW ===" in text
    assert "sample.py" in text


# ==========================================================================
# GROUP 2: Section Formatting & Mode Resolution
# Note: Subprocess flag forwarding, stderr fallback, empty targets, and modes.
# ==========================================================================


@pytest.mark.unit
def test_format_radon_section_forwards_min_grade_and_handles_stderr(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify format_radon_section passes -n min_grade for cc/mi and falls back to stderr."""
    seen_cmds: list[list[str]] = []

    def fake_run(cmd: list[str], **kwargs: Any) -> SimpleNamespace:
        seen_cmds.append(cmd)
        if "mi" in cmd:
            return SimpleNamespace(returncode=1, stdout="", stderr="mi warning")
        return SimpleNamespace(returncode=0, stdout="block output\n", stderr="")

    monkeypatch.setattr("subprocess.run", fake_run)

    cc_out = format_radon_section("cc", ["src"], tmp_path, min_grade="C")
    mi_out = format_radon_section("mi", ["src"], tmp_path, min_grade="B")
    raw_out = format_radon_section("raw", ["src"], tmp_path, min_grade="C")

    assert cc_out == "=== RADON CC ===\nblock output"
    assert mi_out == "=== RADON MI ===\nmi warning"
    assert raw_out == "=== RADON RAW ===\nblock output"
    assert "-n" in seen_cmds[0] and "C" in seen_cmds[0]
    assert "-n" in seen_cmds[1] and "B" in seen_cmds[1]
    assert "-n" not in seen_cmds[2]


@pytest.mark.unit
def test_format_radon_section_empty_output_returns_header_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify format_radon_section returns only the section header when output is empty."""
    monkeypatch.setattr(
        "subprocess.run",
        lambda cmd, **kw: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )

    assert format_radon_section("cc", ["src"], tmp_path) == "=== RADON CC ==="


@pytest.mark.unit
def test_build_combined_radon_report_empty_targets_returns_blank_sections(tmp_path: Path) -> None:
    """Verify build_combined_radon_report emits empty headers when no targets exist."""
    report = build_combined_radon_report([], tmp_path)
    assert report == "=== RADON CC ===\n\n=== RADON MI ===\n\n=== RADON RAW ===\n"


@pytest.mark.integration
def test_generate_radon_report_all_and_include_tests_modes(tmp_path: Path) -> None:
    """Verify 'all' mode and include_tests=True resolve both src and test directories."""
    src_gda = tmp_path / "src" / "gda"
    test_gda = tmp_path / "tests" / "test_gda"
    src_gda.mkdir(parents=True)
    test_gda.mkdir(parents=True)
    (src_gda / "core.py").write_text("x = 1\n", encoding="utf-8")
    (test_gda / "test_core.py").write_text("def test_x(): pass\n", encoding="utf-8")

    tests_report, _ = generate_radon_report(
        mode="gda",
        include_tests=True,
        workspace_root=tmp_path,
        reports_dir="gtemp",
    )
    all_report, _ = generate_radon_report(
        mode="all",
        workspace_root=tmp_path,
        reports_dir="gtemp",
    )

    assert tests_report.name == "GenDeskRadon_gda_tests.txt"
    assert "test_core.py" in tests_report.read_text(encoding="utf-8")
    assert all_report.name == "GenDeskRadon_all.txt"
    assert "core.py" in all_report.read_text(encoding="utf-8")


# ==========================================================================
# GROUP 3: Error Handling & Validation Failures
# Note: Unsupported metric names and unknown subsystem modes.
# ==========================================================================


@pytest.mark.regression
def test_format_radon_section_invalid_metric_raises_value_error(tmp_path: Path) -> None:
    """Verify format_radon_section rejects unsupported Radon metric names."""
    with pytest.raises(ValueError, match="Unsupported Radon metric"):
        format_radon_section("hal", ["src"], tmp_path)


@pytest.mark.regression
def test_generate_radon_report_unknown_mode_raises_value_error(tmp_path: Path) -> None:
    """Verify generate_radon_report rejects unknown subsystem mode strings."""
    with pytest.raises(ValueError, match="Unknown radon report mode"):
        generate_radon_report(mode="nonexistent_mode", workspace_root=tmp_path)
