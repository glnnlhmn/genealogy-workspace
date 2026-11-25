"""Path: tests/test_gen_desk_tools/test_metrics/test_coverage_collector.py

Unit, regression, integration, and invariant tests for coverage_collector.

Operational Role:
    Verifies missing-line range formatting, coverage.json parsing and path
    normalization, pytest-cov execution, GAP-08 timeout handling, GAP-09
    corrupt/missing coverage output on non-zero exit, RARE-05 non-UTF-8
    subprocess output, 4-tier logging emission, and dataclass immutability.
"""

from __future__ import annotations

import dataclasses
import io
import json
import logging
import subprocess
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.metrics.collectors import coverage_collector as cov_mod
from gen_desk_tools.metrics.collectors.coverage_collector import (
    CoverageRunResult,
    FileCoverageMetrics,
    format_missing_lines,
    parse_coverage_json,
    run_pytest_coverage,
)
from gen_desk_tools.metrics.config import BatchDefinition, load_config
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"

_COV_LOGGER = "gen_desk_tools.metrics.collectors.coverage_collector"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end pytest-cov invocation and coverage.json parsing.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_pytest_coverage_invokes_runner_and_parses_json(tmp_path: Path) -> None:
    """Verify run_pytest_coverage invokes pytest with --cov and parses coverage.json."""
    (tmp_path / "src" / "pkg").mkdir(parents=True)
    (tmp_path / "tests" / "test_pkg").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(
            id="B1",
            scope="gda",
            tier="T0",
            paths=("src/pkg", "src/pkg"),
            test_paths=("tests/test_pkg", "tests/test_pkg"),
        ),
    )
    captured_cmd: list[str] = []

    def fake_runner(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured_cmd.extend(cmd)
        cov_json = cfg.pytest_basetemp / "coverage.json"
        cov_json.write_text(
            json.dumps(
                {
                    "files": {
                        "src/pkg/mod.py": {
                            "summary": {
                                "num_statements": 4,
                                "covered_lines": 4,
                                "num_branches": 2,
                                "covered_branches": 2,
                            },
                            "missing_lines": [],
                        }
                    }
                }
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(cmd, 0, stdout="1 passed in 0.10s\n\n", stderr="")

    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf, verbose=True)

    result = run_pytest_coverage(cfg, batches, progress=reporter, runner=fake_runner)

    assert result.exit_code == 0
    assert result.summary_note == "1 passed in 0.10s"
    assert "--cov=src/pkg" in captured_cmd
    assert f"--basetemp={cfg.pytest_basetemp}" in captured_cmd
    assert result.files["src/pkg/mod.py"].total_cov_pct == 100.0
    assert "Running pytest across 1 target(s)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface, missing-line range formatting, and JSON parsing.
# ==========================================================================


@pytest.mark.unit
def test_coverage_collector_exposes_expected_public_interface() -> None:
    """Verify coverage_collector exports its expected public symbols."""
    expected = {
        "CoverageRunResult",
        "FileCoverageMetrics",
        "format_missing_lines",
        "parse_coverage_json",
        "run_pytest_coverage",
    }
    assert expected.issubset(set(cov_mod.__all__))


@pytest.mark.unit
def test_format_missing_lines_handles_empty_and_ranges() -> None:
    """Verify format_missing_lines deduplicates, sorts, and collapses contiguous runs."""
    assert format_missing_lines([]) == "-"
    assert format_missing_lines([10, 12, 13, 14, 18, 19]) == "10, 12-14, 18-19"
    assert format_missing_lines([14, 12, 13, 12, 10]) == "10, 12-14"


@pytest.mark.integration
def test_parse_coverage_json_normalizes_paths_and_computes_percentages(tmp_path: Path) -> None:
    """Verify parse_coverage_JSON handles relative, inside-root, and outside-root paths."""
    inside = (tmp_path / "src" / "a.py").resolve()
    outside = (tmp_path.parent / "external_other.py").resolve()
    payload = {
        "files": {
            str(inside): {
                "summary": {
                    "num_statements": 10,
                    "covered_lines": 8,
                    "num_branches": 4,
                    "covered_branches": 2,
                },
                "missing_lines": [3, 4],
            },
            r"src\b.py": {
                "summary": {
                    "num_statements": 0,
                    "covered_lines": 0,
                    "num_branches": 0,
                    "covered_branches": 0,
                },
                "missing_lines": [],
            },
            str(outside): {
                "summary": {
                    "num_statements": 2,
                    "covered_lines": 2,
                    "num_branches": 0,
                    "covered_branches": 0,
                },
                "missing_lines": [],
            },
        }
    }
    cov_file = tmp_path / "coverage.json"
    cov_file.write_text(json.dumps(payload), encoding="utf-8")

    parsed = parse_coverage_json(cov_file, tmp_path)

    assert parsed["src/a.py"].stmt_cov_pct == 80.0
    assert parsed["src/a.py"].branch_cov_pct == 50.0
    assert parsed["src/a.py"].total_cov_pct == 71.4
    assert parsed["src/a.py"].missing_lines == "3-4"
    assert parsed["src/b.py"].total_cov_pct == 100.0
    assert outside.as_posix() in parsed


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Missing coverage JSON, absent test targets, and empty stdout fallback.
# ==========================================================================


@pytest.mark.unit
def test_parse_coverage_json_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    """Verify parse_coverage_JSON returns an empty dict when JSON does not exist."""
    assert parse_coverage_json(tmp_path / "missing.json", tmp_path) == {}


@pytest.mark.unit
def test_run_pytest_coverage_no_existing_test_targets_skips_execution(tmp_path: Path) -> None:
    """Verify run_pytest_coverage returns early when no configured test paths exist."""
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(
            id="B1",
            scope="gda",
            tier="T0",
            paths=("src/missing",),
            test_paths=("tests/missing",),
        ),
    )

    result = run_pytest_coverage(cfg, batches)

    assert result.exit_code == 0
    assert "No matching test directories" in result.summary_note
    assert result.files == {}


@pytest.mark.regression
def test_run_pytest_coverage_empty_stdout_uses_exit_code_fallback(tmp_path: Path) -> None:
    """Verify empty pytest stdout falls back to an exit-code summary note."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def fake_runner(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 2, stdout=" \n", stderr="err")

    result = run_pytest_coverage(cfg, batches, progress=None, runner=fake_runner)

    assert result.exit_code == 2
    assert result.summary_note == "pytest exited with code 2"


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: GAP-08 timeout, GAP-09 corrupt JSON on failure, RARE-05 encoding, OSError.
# ==========================================================================


@pytest.mark.regression
def test_parse_coverage_json_corrupt_json_logs_error_and_returns_empty_dict(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-09: malformed coverage.json logs ERROR and returns empty dict."""
    corrupt_json = tmp_path / "coverage.json"
    corrupt_json.write_text("{truncated json", encoding="utf-8")

    with caplog.at_level(logging.ERROR, logger=_COV_LOGGER):
        parsed = parse_coverage_json(corrupt_json, tmp_path)

    assert parsed == {}
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_pytest_coverage_nonzero_exit_with_corrupt_json_records_failure(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-09: failed test run with corrupt coverage.json surfaces exit code cleanly."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def _failing_runner(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        (cfg.pytest_basetemp / "coverage.json").write_text("{bad", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 1, stdout="1 failed in 0.20s\n", stderr="")

    with caplog.at_level(logging.ERROR, logger=_COV_LOGGER):
        result = run_pytest_coverage(cfg, batches, progress=None, runner=_failing_runner)

    assert result.exit_code == 1
    assert "1 failed" in result.summary_note
    assert result.files == {}
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_pytest_coverage_handles_os_error_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify run_pytest_coverage catches OSError, logs ERROR, and returns degraded result."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def _boom(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise OSError("pytest binary missing")

    with caplog.at_level(logging.ERROR, logger=_COV_LOGGER):
        result = run_pytest_coverage(cfg, batches, progress=None, runner=_boom)

    assert result.exit_code == 1
    assert "pytest unavailable" in result.summary_note.lower()
    assert result.files == {}
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_pytest_coverage_handles_timeout_expired_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-08: subprocess.TimeoutExpired logs ERROR and returns degraded result."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def _hang(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(cmd=["pytest"], timeout=120)

    with caplog.at_level(logging.ERROR, logger=_COV_LOGGER):
        result = run_pytest_coverage(cfg, batches, progress=None, runner=_hang)

    assert result.exit_code == 1
    assert "timeout" in result.summary_note.lower() or "timed out" in result.summary_note.lower()
    assert result.files == {}
    assert any(r.levelname == "ERROR" for r in caplog.records)


@pytest.mark.regression
def test_run_pytest_coverage_handles_non_utf8_subprocess_output_gracefully(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify RARE-05: UnicodeDecodeError from non-UTF-8 output logs ERROR cleanly."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def _bad_encoding(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[str]:
        raise UnicodeDecodeError("utf-8", b"\x80\x81", 0, 1, "invalid start byte")

    with caplog.at_level(logging.ERROR, logger=_COV_LOGGER):
        result = run_pytest_coverage(cfg, batches, progress=None, runner=_bad_encoding)

    assert result.exit_code == 1
    assert "encoding" in result.summary_note.lower() or "decode" in result.summary_note.lower()
    assert result.files == {}
    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_run_pytest_coverage_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify run_pytest_coverage emits INFO, VERBOSE, and DEBUG log records."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def _fake_runner(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, stdout="1 passed in 0.05s\n", stderr="")

    with caplog.at_level(logging.DEBUG, logger=_COV_LOGGER):
        run_pytest_coverage(cfg, batches, progress=None, runner=_fake_runner)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Frozen dataclass immutability for FileCoverageMetrics and CoverageRunResult.
# ==========================================================================


# TODO:  Fix error in this test
@pytest.mark.integrity
def test_coverage_dataclasses_are_immutable() -> None:
    """Verify FileCoverageMetrics and CoverageRunResult reject in-place mutation."""
    file_cov = FileCoverageMetrics("src/a.py", 10, 10, "-", 2, 2, 100.0, 100.0, 100.0)
    run_res = CoverageRunResult(exit_code=0, summary_note="ok", files={"src/a.py": file_cov})

    with pytest.raises(dataclasses.FrozenInstanceError):
        file_cov.stmt_cov_pct = 0.0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        run_res.exit_code = 1  # type: ignore[misc]
