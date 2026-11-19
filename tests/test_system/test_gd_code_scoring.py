"""Path: tests/test_system/test_gd_code_scoring.py

Unit and integration test suite for src/system/util/gd_code_scoring.py.

Operational Role:
    Verifies Audit Batch path resolution, coverage JSON parsing and line-range
    compression, pytest and Ruff subprocess execution, per-file and per-batch
    radon raw/CC/MI/coverage aggregation, 4-section report rendering, CLI
    arguments, and __main__ execution at 100.00% statement and branch coverage.
"""

from __future__ import annotations

import json
import runpy
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from system.util.gd_code_scoring import (
    BatchRollupMetrics,
    BlockCCMetric,
    CoverageFileStat,
    DomainRawMetrics,
    FileMIMetric,
    FileTelemetryMetric,
    PytestExecutionResult,
    RuffExecutionResult,
    ScoringReportData,
    _compress_line_ranges,
    _discover_python_files,
    aggregate_batch_rollups,
    collect_cc_metrics,
    collect_domain_raw_metrics,
    collect_file_telemetry,
    collect_mi_metrics,
    format_scoring_report,
    generate_scoring_report,
    load_coverage_json,
    main,
    resolve_batch_id,
    run_pytest_coverage,
    run_ruff_updates,
)

__version__ = "1.0.0+build.8"


# ==========================================================================
# GROUP 1: Batch ID Resolution, Line Range Compression & Dataclass Properties
# Note: Verifies pure in-memory batch routing and metric property math.
# ==========================================================================


@pytest.mark.unit
def test_resolve_batch_id_all_canonical_batches_and_fallback() -> None:
    """Verify resolve_batch_id maps all GDA batches, optional groups, and unknown paths."""
    assert resolve_batch_id("src/gda/core/config.py") == "GDA-Batch-1"
    assert resolve_batch_id("src/gda/core/enums/vital.py") == "GDA-Batch-1"
    assert resolve_batch_id("src/gda/util/ids.py") == "GDA-Batch-2"
    assert resolve_batch_id("src/gda/io/atomic.py") == "GDA-Batch-2"
    assert resolve_batch_id("src/gda/model/atom/id.py") == "GDA-Batch-3"
    assert resolve_batch_id("src/gda/model/__init__.py") == "GDA-Batch-3"
    assert resolve_batch_id("src/gda/__init__.py") == "GDA-Batch-3"
    assert resolve_batch_id("src/gda/model/source/vital/birth.py") == "GDA-Batch-4"
    assert resolve_batch_id("src/gda/entity/individuals/collection.py") == "GDA-Batch-5"
    assert resolve_batch_id("src/gda/db/session.py") == "GDA-Batch-6"
    assert resolve_batch_id("src/gda/repository/base.py") == "GDA-Batch-7"
    assert resolve_batch_id("src/gda/engine/resolver.py") == "GDA-Batch-8"
    assert resolve_batch_id("src/gda/manager/vocab/__init__.py") == "GDA-Batch-8"
    assert resolve_batch_id("src/system/gsi/gsi.py") == "Group-S"
    assert resolve_batch_id("src/cli/commands/load_setup.py") == "Group-CLI"
    assert resolve_batch_id("src/ancestry_desk/views/__init__.py") == "Group-GenDesk"
    assert resolve_batch_id("tests/test_system/test_gsi.py") == "Tests"
    assert resolve_batch_id("scripts/custom_tool.py") == "Other"


@pytest.mark.unit
def test_compress_line_ranges_empty_contiguous_and_disjoint() -> None:
    """Verify _compress_line_ranges formats empty, single, and contiguous line spans."""
    assert _compress_line_ranges([]) == "-"
    assert _compress_line_ranges([7]) == "7"
    assert _compress_line_ranges([3, 4, 5, 9, 11, 12]) == "3-5, 9, 11-12"


@pytest.mark.unit
def test_metric_dataclass_properties_positive_and_zero_denominators(tmp_path: Path) -> None:
    """Verify CoverageFileStat, DomainRawMetrics, FileTelemetryMetric, and BatchRollupMetrics properties."""
    cov_pos = CoverageFileStat(
        covered_lines=18,
        num_statements=20,
        covered_branches=3,
        num_branches=5,
        missing_lines_str="10-11",
    )
    assert cov_pos.stmt_cov_pct == 90.0
    assert cov_pos.branch_cov_pct == 60.0
    assert cov_pos.total_cov_pct == 84.0

    cov_zero = CoverageFileStat(
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        missing_lines_str="-",
    )
    assert cov_zero.stmt_cov_pct == 100.0
    assert cov_zero.branch_cov_pct == 100.0
    assert cov_zero.total_cov_pct == 100.0

    dm_pos = DomainRawMetrics(
        label="src/gda",
        file_count=2,
        loc=120,
        lloc=80,
        sloc=100,
        blank=10,
        comments=5,
        docstrings=15,
    )
    assert dm_pos.total_doc_lines == 20
    assert dm_pos.doc_to_sloc_pct == 20.0

    dm_zero = DomainRawMetrics(
        label="empty",
        file_count=0,
        loc=0,
        lloc=0,
        sloc=0,
        blank=0,
        comments=0,
        docstrings=0,
    )
    assert dm_zero.doc_to_sloc_pct == 0.0
    assert _discover_python_files(tmp_path / "nonexistent") == []

    ft_no_cov = FileTelemetryMetric(
        batch_id="GDA-Batch-1",
        file_path="src/gda/core/__init__.py",
        loc=0,
        lloc=0,
        sloc=0,
        blank=0,
        comments=0,
        docstrings=0,
        mi_score=100.0,
        mi_grade="A",
        block_count=0,
        sum_cc=0,
        max_cc=0,
        max_cc_grade="A",
        max_cc_symbol="-",
        cc_c_plus_count=0,
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        missing_lines_str="-",
        has_coverage=False,
    )
    assert ft_no_cov.doc_to_sloc_pct == 0.0
    assert ft_no_cov.avg_cc == 0.0
    assert ft_no_cov.total_cov_pct == 0.0

    ft_zero_cov = FileTelemetryMetric(
        batch_id="GDA-Batch-1",
        file_path="src/gda/core/__init__.py",
        loc=1,
        lloc=0,
        sloc=0,
        blank=1,
        comments=0,
        docstrings=0,
        mi_score=100.0,
        mi_grade="A",
        block_count=2,
        sum_cc=6,
        max_cc=4,
        max_cc_grade="A",
        max_cc_symbol="F fn:1",
        cc_c_plus_count=0,
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        missing_lines_str="-",
        has_coverage=True,
    )
    assert ft_zero_cov.avg_cc == 3.0
    assert ft_zero_cov.total_cov_pct == 100.0

    br_no_cov = BatchRollupMetrics(
        batch_id="GDA-Batch-1",
        file_count=1,
        loc=0,
        lloc=0,
        sloc=0,
        blank=0,
        comments=0,
        docstrings=0,
        block_count=0,
        sum_cc=0,
        cc_c_plus_count=0,
        mi_below_a_count=0,
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        has_coverage=False,
    )
    assert br_no_cov.doc_to_sloc_pct == 0.0
    assert br_no_cov.avg_cc == 0.0
    assert br_no_cov.stmt_cov_pct == 0.0
    assert br_no_cov.branch_cov_pct == 0.0
    assert br_no_cov.total_cov_pct == 0.0

    br_zero_denom = BatchRollupMetrics(
        batch_id="GDA-Batch-1",
        file_count=1,
        loc=0,
        lloc=0,
        sloc=0,
        blank=0,
        comments=0,
        docstrings=0,
        block_count=0,
        sum_cc=0,
        cc_c_plus_count=0,
        mi_below_a_count=0,
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        has_coverage=True,
    )
    assert br_zero_denom.stmt_cov_pct == 100.0
    assert br_zero_denom.branch_cov_pct == 100.0
    assert br_zero_denom.total_cov_pct == 100.0


# ==========================================================================
# GROUP 2: Subprocess Runners & Coverage JSON Ingestion
# Note: Verifies Ruff and Pytest wrappers and malformed JSON defensive guards.
# ==========================================================================


@pytest.mark.unit
def test_run_ruff_updates_with_and_without_targets(tmp_path: Path) -> None:
    """Verify run_ruff_updates handles missing target dirs and subprocess execution."""
    res_empty = run_ruff_updates(tmp_path, targets=("missing_dir",))
    assert res_empty.ran_ruff is True
    assert res_empty.format_returncode == 0
    assert "No target directories" in res_empty.format_output

    (tmp_path / "src").mkdir()
    mock_fmt = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    mock_chk = subprocess.CompletedProcess(args=[], returncode=0, stdout="1 file fixed", stderr="")
    with patch("subprocess.run", side_effect=[mock_fmt, mock_chk]) as mock_run:
        res = run_ruff_updates(tmp_path, targets=("src",))
        assert mock_run.call_count == 2
        assert res.format_output == "All files formatted cleanly."
        assert res.check_output == "1 file fixed"


@pytest.mark.unit
def test_run_pytest_coverage_missing_and_present_target(tmp_path: Path) -> None:
    """Verify run_pytest_coverage handles missing target directory and mocked execution."""
    res_missing = run_pytest_coverage(tmp_path, source_target="nonexistent_src")
    assert res_missing.ran_pytest is False
    assert res_missing.cov_json_path is None

    (tmp_path / "src").mkdir()
    cov_rel = "gtemp/pytest_tmp/cov.json"
    cov_abs = tmp_path / cov_rel
    cov_abs.parent.mkdir(parents=True, exist_ok=True)
    cov_abs.write_text("{}", encoding="utf-8")

    mock_proc = subprocess.CompletedProcess(
        args=[],
        returncode=0,
        stdout="10 passed in 0.50s\n",
        stderr="",
    )
    with patch("subprocess.run", return_value=mock_proc):
        res_ok = run_pytest_coverage(tmp_path, cov_json_rel_path=cov_rel, source_target="src")
        assert res_ok.ran_pytest is True
        assert res_ok.returncode == 0
        assert "10 passed" in res_ok.summary_output
        assert res_ok.cov_json_path == cov_abs


@pytest.mark.regression
def test_load_coverage_json_valid_and_malformed_inputs(tmp_path: Path) -> None:
    """Verify load_coverage_json parses valid coverage payloads and guards malformed structures."""
    assert load_coverage_json(tmp_path, "missing.json") == {}

    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{corrupt", encoding="utf-8")
    assert load_coverage_json(tmp_path, bad_json) == {}

    non_dict_files = tmp_path / "non_dict.json"
    non_dict_files.write_text(json.dumps({"files": ["not-a-dict"]}), encoding="utf-8")
    assert load_coverage_json(tmp_path, non_dict_files) == {}

    valid_cov = tmp_path / "valid_cov.json"
    abs_file_key = (tmp_path / "src" / "gda" / "core" / "dates.py").as_posix()
    payload = {
        "files": {
            "skip_non_dict": "invalid",
            abs_file_key: {
                "summary": "not-a-dict",
                "missing_lines": "not-a-list",
            },
            "src\\gda\\core\\config.py": {
                "summary": {
                    "covered_lines": 45,
                    "num_statements": 50,
                    "covered_branches": 8,
                    "num_branches": 10,
                },
                "missing_lines": [12, 13, 14, 30],
            },
        }
    }
    valid_cov.write_text(json.dumps(payload), encoding="utf-8")
    parsed = load_coverage_json(tmp_path, valid_cov)
    assert "src/gda/core/dates.py" in parsed
    assert parsed["src/gda/core/dates.py"].num_statements == 0
    assert "src/gda/core/config.py" in parsed
    assert parsed["src/gda/core/config.py"].missing_lines_str == "12-14, 30"


# ==========================================================================
# GROUP 3: End-to-End Telemetry Collection & Report Formatting
# Note: Verifies multi-batch aggregation, hotspot rendering, and CLI flags.
# ==========================================================================


@pytest.mark.integration
def test_collect_metrics_and_generate_report_populated(tmp_path: Path) -> None:
    """Verify raw, CC, MI, and coverage collection and report generation on a sample workspace."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    core_pkg = tmp_path / "src" / "gda" / "core"
    core_pkg.mkdir(parents=True)
    custom_pkg = tmp_path / "src" / "custom_other"
    custom_pkg.mkdir(parents=True)
    tests_pkg = tmp_path / "tests"
    tests_pkg.mkdir(parents=True)

    cache_dir = core_pkg / "__pycache__"
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
    (core_pkg / "sample.py").write_text(sample_code, encoding="utf-8")
    (core_pkg / "__init__.py").write_text("", encoding="utf-8")
    (custom_pkg / "extra.py").write_text("x = 1\n", encoding="utf-8")
    (tests_pkg / "test_sample.py").write_text(
        "def test_ok() -> None:\n    assert True\n",
        encoding="utf-8",
    )

    cov_file = tmp_path / "gtemp" / "pytest_tmp" / "coverage.json"
    cov_file.parent.mkdir(parents=True, exist_ok=True)
    cov_file.write_text(
        json.dumps(
            {
                "files": {
                    "src/gda/core/sample.py": {
                        "summary": {
                            "covered_lines": 7,
                            "num_statements": 8,
                            "covered_branches": 1,
                            "num_branches": 2,
                        },
                        "missing_lines": [11],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    raw_list = collect_domain_raw_metrics(
        tmp_path,
        domains=(("src/gda", "src/gda"), ("src/missing", "src/missing"), ("tests", "tests")),
    )
    assert len(raw_list) == 2

    cc_list = collect_cc_metrics(tmp_path, source_dirs=("src",))
    assert {"C", "M", "F"} <= {b.block_type for b in cc_list}

    mi_list = collect_mi_metrics(tmp_path, source_dirs=("src",))
    assert len(mi_list) == 3

    out_file, data = generate_scoring_report(
        workspace_root=tmp_path,
        output_path="reports/custom_score.txt",
        run_ruff=False,
        run_pytest=False,
        cov_json_path=cov_file,
    )
    assert out_file.is_file()
    text = out_file.read_text(encoding="utf-8")
    assert "DEFERRED TO BATCH GATES" in text
    assert "GDA-Batch-1" in text
    assert "Other" in text
    assert "None! All blocks achieved Grade A or B" in text
    assert "None! 100% of modules achieved Grade A" in text
    assert len(data.batch_rollups) == 2

    with (
        patch("system.util.gd_code_scoring.run_ruff_updates") as mock_ruff,
        patch("system.util.gd_code_scoring.run_pytest_coverage") as mock_pytest,
    ):
        mock_ruff.return_value = RuffExecutionResult(
            ran_ruff=True,
            format_returncode=0,
            format_output="Formatted",
            check_returncode=0,
            check_output="Checked",
        )
        mock_pytest.return_value = PytestExecutionResult(
            ran_pytest=True,
            returncode=0,
            summary_output="12 passed",
            cov_json_path=cov_file,
        )
        abs_out = tmp_path / "reports" / "abs_score.txt"
        out_file2, _ = generate_scoring_report(
            workspace_root=tmp_path,
            output_path=abs_out,
            run_ruff=True,
            run_pytest=True,
            cov_json_path="gtemp/pytest_tmp/missing_cov.json",
        )
        assert out_file2 == abs_out
        rendered2 = abs_out.read_text(encoding="utf-8")
        assert "Ruff Format    : exit=0 (Formatted)" in rendered2
        assert "Pytest Cov     : exit=0 (12 passed)" in rendered2


@pytest.mark.unit
def test_collect_file_telemetry_high_complexity_branch(tmp_path: Path) -> None:
    """Verify collect_file_telemetry hits the comp >= 11 branch for CC C+ counter (line 656)."""
    src_pkg = tmp_path / "src" / "gda" / "core"
    src_pkg.mkdir(parents=True)

    high_cc_code = '"""High complexity module."""\n\ndef complex_func(x: int) -> int:\n'
    for i in range(12):
        high_cc_code += f"    if x == {i}:\n        return {i}\n"
    high_cc_code += "    return -1\n"

    (src_pkg / "complex_module.py").write_text(high_cc_code, encoding="utf-8")

    file_tel, cc_metrics, mi_metrics = collect_file_telemetry(
        tmp_path,
        source_dirs=("src",),
        coverage_map={},
    )

    match_item = next((ft for ft in file_tel if "complex_module.py" in ft.file_path), None)
    assert match_item is not None
    assert match_item.cc_c_plus_count >= 1


@pytest.mark.unit
def test_format_scoring_report_with_hotspots_and_no_coverage(tmp_path: Path) -> None:
    """Verify report formatting when high-CC blocks and low-MI modules exist without coverage."""
    ft_item = FileTelemetryMetric(
        batch_id="GDA-Batch-4",
        file_path="src/gda/model/source/vital/death.py",
        loc=200,
        lloc=120,
        sloc=160,
        blank=20,
        comments=10,
        docstrings=10,
        mi_score=14.25,
        mi_grade="B",
        block_count=1,
        sum_cc=15,
        max_cc=15,
        max_cc_grade="C",
        max_cc_symbol="F heavy_func:42",
        cc_c_plus_count=1,
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        missing_lines_str="-",
        has_coverage=False,
    )
    rollups = aggregate_batch_rollups([ft_item])

    hotspot_data = ScoringReportData(
        generated_at="2026-11-18T00:00:00Z",
        workspace_root=tmp_path,
        ruff_result=RuffExecutionResult(
            ran_ruff=False,
            format_returncode=0,
            format_output="Skipped",
            check_returncode=0,
            check_output="Skipped",
        ),
        pytest_result=PytestExecutionResult(
            ran_pytest=False,
            returncode=0,
            summary_output="SKIPPED",
            cov_json_path=None,
        ),
        raw_metrics=[],
        batch_rollups=rollups,
        file_telemetry=[ft_item],
        cc_metrics=[
            BlockCCMetric(
                batch_id="GDA-Batch-4",
                file_path="src/gda/model/source/vital/death.py",
                block_type="F",
                name="heavy_func",
                lineno=42,
                complexity=15,
                grade="C",
            )
        ],
        mi_metrics=[
            FileMIMetric(
                batch_id="GDA-Batch-4",
                file_path="src/gda/model/source/vital/death.py",
                mi_score=14.25,
                grade="B",
            )
        ],
    )
    rendered = format_scoring_report(hotspot_data)
    assert (
        "[GDA-Batch-4 ] [C (15)] src/gda/model/source/vital/death.py:42 (F heavy_func)" in rendered
    )
    assert "[GDA-Batch-4 ] [B (14.25)] src/gda/model/source/vital/death.py" in rendered
    assert "N/A" in rendered

    ft_zero_stmt = FileTelemetryMetric(
        batch_id="GDA-Batch-1",
        file_path="src/gda/core/__init__.py",
        loc=1,
        lloc=0,
        sloc=0,
        blank=1,
        comments=0,
        docstrings=0,
        mi_score=100.0,
        mi_grade="A",
        block_count=0,
        sum_cc=0,
        max_cc=0,
        max_cc_grade="A",
        max_cc_symbol="-",
        cc_c_plus_count=0,
        covered_lines=0,
        num_statements=0,
        covered_branches=0,
        num_branches=0,
        missing_lines_str="-",
        has_coverage=True,
    )
    empty_cov_data = ScoringReportData(
        generated_at="2026-11-18T00:00:00Z",
        workspace_root=tmp_path,
        ruff_result=hotspot_data.ruff_result,
        pytest_result=hotspot_data.pytest_result,
        raw_metrics=[],
        batch_rollups=aggregate_batch_rollups([ft_zero_stmt]),
        file_telemetry=[ft_zero_stmt],
        cc_metrics=[],
        mi_metrics=[],
    )
    rendered_zero = format_scoring_report(empty_cov_data)
    assert "100.0%" in rendered_zero

    ft_untested_file, _, _ = collect_file_telemetry(
        tmp_path,
        source_dirs=("nonexistent",),
        coverage_map={},
    )
    assert ft_untested_file == []


@pytest.mark.smoke
def test_cli_main_execution_and_verbose_and_debug_modes(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main() CLI entrypoint parses flags and supports quiet, verbose, and debug modes."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='cli'\n", encoding="utf-8")
    rc = main(["--root", str(tmp_path), "--no-pytest", "-o", "reports/cli_out.txt"])
    assert rc == 0
    captured = capsys.readouterr().out
    assert "Unified Code Scoring Report written to:" in captured

    rc_v = main(
        [
            "--root",
            str(tmp_path),
            "--no-pytest",
            "--no-ruff",
            "--verbose",
            "-o",
            "reports/cli_out_v.txt",
        ]
    )
    assert rc_v == 0
    captured_v = capsys.readouterr().out
    assert "GDA WORKSPACE PHASE 0 CODE SCORING & COVERAGE TELEMETRY REPORT" in captured_v

    rc_dbg = main(
        [
            "--root",
            str(tmp_path),
            "--no-pytest",
            "--no-ruff",
            "--debug",
            "-o",
            "reports/cli_out_dbg.txt",
        ]
    )
    assert rc_dbg == 0
    captured_dbg = capsys.readouterr().out
    assert "GDA WORKSPACE PHASE 0 CODE SCORING & COVERAGE TELEMETRY REPORT" in captured_dbg


@pytest.mark.unit
def test_main_block_execution_via_runpy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify executing gd_code_scoring.py as __main__ covers the module entry guard cleanly."""
    (tmp_path / "pyproject.toml").write_text("[project]\nname='main_test'\n", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["gd_code_scoring.py", "--root", str(tmp_path), "--no-pytest", "--no-ruff"],
    )
    sys.modules.pop("system.util.gd_code_scoring", None)
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("system.util.gd_code_scoring", run_name="__main__")
    assert exc_info.value.code == 0
