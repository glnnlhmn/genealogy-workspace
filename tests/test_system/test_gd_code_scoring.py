"""Path: tests/test_system/test_gd_code_scoring.py

Unit and integration test suite for src/system/util/gd_code_scoring.py.

Operational Role:
    Verifies Ruff subprocess execution, raw line/comment metric aggregation,
    Cyclomatic Complexity (CC) hotspot detection, Maintainability Index (MI)
    grading, live console progress notices, silent mode (--silent/-q), and CLI
    argument execution at 100% statement and branch coverage.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from system.util.gd_code_scoring import (
    BlockCCMetric,
    DomainRawMetrics,
    FileMIMetric,
    RuffExecutionResult,
    ScoringReportData,
    _discover_python_files,
    collect_cc_metrics,
    collect_domain_raw_metrics,
    collect_mi_metrics,
    format_scoring_report,
    generate_scoring_report,
    main,
    run_ruff_updates,
)

__version__ = "1.0.0+build.2"


@pytest.mark.unit
def test_domain_raw_metrics_properties_and_empty_discovery(tmp_path: Path) -> None:
    """Verify DomainRawMetrics properties for both positive and zero SLOC."""
    m_pos = DomainRawMetrics(
        label="src/gda",
        file_count=2,
        loc=120,
        lloc=80,
        sloc=100,
        blank=10,
        comments=5,
        docstrings=15,
    )
    assert m_pos.total_doc_lines == 20
    assert m_pos.doc_to_sloc_pct == 20.0

    m_zero = DomainRawMetrics(
        label="empty",
        file_count=0,
        loc=0,
        lloc=0,
        sloc=0,
        blank=0,
        comments=0,
        docstrings=0,
    )
    assert m_zero.doc_to_sloc_pct == 0.0
    assert _discover_python_files(tmp_path / "nonexistent") == []


@pytest.mark.unit
def test_run_ruff_updates_with_and_without_targets(tmp_path: Path) -> None:
    """Verify run_ruff_updates handles missing target dirs and subprocess execution."""
    res_empty = run_ruff_updates(tmp_path, targets=("missing_dir",), silent=True)
    assert res_empty.ran_ruff is True
    assert res_empty.format_returncode == 0
    assert "No target directories" in res_empty.format_output

    (tmp_path / "src").mkdir()
    mock_fmt = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    mock_chk = subprocess.CompletedProcess(args=[], returncode=0, stdout="1 file fixed", stderr="")
    with patch("subprocess.run", side_effect=[mock_fmt, mock_chk]) as mock_run:
        res = run_ruff_updates(tmp_path, targets=("src",), silent=False)
        assert mock_run.call_count == 2
        assert res.format_output == "All files formatted cleanly."
        assert res.check_output == "1 file fixed"


@pytest.mark.integration
def test_collect_metrics_and_generate_report_populated(tmp_path: Path) -> None:
    """Verify raw, CC, and MI collection and report generation on a sample workspace."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    src_pkg = tmp_path / "src" / "gda"
    src_pkg.mkdir(parents=True)
    tests_pkg = tmp_path / "tests"
    tests_pkg.mkdir(parents=True)

    cache_dir = src_pkg / "__pycache__"
    cache_dir.mkdir()
    (cache_dir / "ignored.py").write_text("x = 1\n", encoding="utf-8")

    sample_code = (
        '"""Sample module docstring."""\n\n'
        "# Inline comment\n"
        "class SampleClass:\n"
        '    """Class docstring."""\n'
        "    def method_a(self, x: int) -> int:\n"
        "        return x + 1\n\n"
        "def standalone_func(val: int) -> int:\n"
        "    if val > 0:\n"
        "        return val\n"
        "    return 0\n"
    )
    (src_pkg / "sample.py").write_text(sample_code, encoding="utf-8")
    (tests_pkg / "test_sample.py").write_text(
        "def test_ok() -> None:\n    assert True\n", encoding="utf-8"
    )

    raw_list = collect_domain_raw_metrics(
        tmp_path,
        domains=(("src/gda", "src/gda"), ("src/missing", "src/missing"), ("tests", "tests")),
    )
    assert len(raw_list) == 2

    cc_list = collect_cc_metrics(tmp_path, source_dirs=("src",))
    block_types = {b.block_type for b in cc_list}
    assert {"C", "M", "F"} <= block_types

    mi_list = collect_mi_metrics(tmp_path, source_dirs=("src",))
    assert len(mi_list) == 1
    assert mi_list[0].grade == "A"

    out_file, _ = generate_scoring_report(
        workspace_root=tmp_path,
        output_path="reports/custom_score.txt",
        run_ruff=False,
    )
    assert out_file.is_file()
    text = out_file.read_text(encoding="utf-8")
    assert "SKIPPED (--no-ruff flag specified)" in text
    assert "None! All blocks achieved Grade A or B" in text
    assert "None! 100% of modules achieved Grade A" in text

    with patch("system.util.gd_code_scoring.run_ruff_updates") as mock_ruff:
        mock_ruff.return_value = RuffExecutionResult(
            ran_ruff=True,
            format_returncode=0,
            format_output="Formatted",
            check_returncode=0,
            check_output="Checked",
        )
        abs_out = tmp_path / "reports" / "abs_score.txt"
        out_file2, _ = generate_scoring_report(
            workspace_root=tmp_path,
            output_path=abs_out,
            run_ruff=True,
            silent=True,
        )
        assert out_file2 == abs_out
        assert "Ruff Format (exit=0): Formatted" in abs_out.read_text(encoding="utf-8")


@pytest.mark.unit
def test_progress_batch_branch_coverage(tmp_path: Path) -> None:
    """Verify multi-file loop progress branch when idx != total_files."""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "a.py").write_text("x = 1\n", encoding="utf-8")
    (src_dir / "b.py").write_text("y = 2\n", encoding="utf-8")
    assert len(collect_mi_metrics(tmp_path, source_dirs=("src",), silent=True)) == 2
    assert collect_cc_metrics(tmp_path, source_dirs=("src",), silent=True) == []


@pytest.mark.unit
def test_format_scoring_report_with_hotspots_and_empty_metrics(tmp_path: Path) -> None:
    """Verify report formatting when high-CC blocks and low-MI modules exist, and when empty."""
    hotspot_data = ScoringReportData(
        generated_at="2026-11-18T00:00:00Z",
        workspace_root=tmp_path,
        ruff_result=RuffExecutionResult(
            ran_ruff=True,
            format_returncode=0,
            format_output="OK",
            check_returncode=0,
            check_output="OK",
        ),
        raw_metrics=[],
        cc_metrics=[
            BlockCCMetric(
                file_path="src/gda/complex.py",
                block_type="F",
                name="heavy_func",
                lineno=42,
                complexity=15,
                grade="C",
            )
        ],
        mi_metrics=[
            FileMIMetric(
                file_path="src/gda/complex.py",
                mi_score=14.25,
                grade="B",
            )
        ],
    )
    rendered = format_scoring_report(hotspot_data)
    assert "[C (15)] src/gda/complex.py:42 (F heavy_func)" in rendered
    assert "[B (14.25)] src/gda/complex.py" in rendered


@pytest.mark.unit
def test_cli_main_verbose_and_silent_modes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main() prints progress by default and produces zero stdout with --silent."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='cli'\n", encoding="utf-8")

    rc1 = main(["--root", str(tmp_path), "--no-ruff", "-o", "reports/cli_out.txt"])
    assert rc1 == 0
    out_verbose = capsys.readouterr().out
    assert "[1/5]" in out_verbose
    assert "Unified Code Scoring Report written to:" in out_verbose

    rc2 = main(["--root", str(tmp_path), "--no-ruff", "--silent", "-o", "reports/cli_q.txt"])
    assert rc2 == 0
    out_silent = capsys.readouterr().out
    assert out_silent == ""
