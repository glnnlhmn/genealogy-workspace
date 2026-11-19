"""Path: tests/test_system/gd_metrics/test_coverage_collector.py

Unit and integration tests for system.gd_metrics.collectors.coverage_collector.
"""

from __future__ import annotations

import io
import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from system.gd_metrics.collectors.coverage_collector import (
    format_missing_lines,
    parse_coverage_json,
    run_pytest_coverage,
)
from system.gd_metrics.config import BatchDefinition, load_config
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.1"


# ==========================================================================
# GROUP 1: Missing Line Formatting & JSON Parsing
# Note: Verifies range collapsing, missing files, and path normalization.
# ==========================================================================


@pytest.mark.unit
def test_format_missing_lines_handles_empty_and_ranges() -> None:
    """Verify format_missing_lines collapses contiguous runs and handles empty input."""
    assert format_missing_lines([]) == "-"
    assert format_missing_lines([10, 12, 13, 14, 18, 19]) == "10, 12-14, 18-19"


@pytest.mark.unit
def test_parse_coverage_json_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    """Verify parse_coverage_json returns an empty dict when JSON does not exist."""
    assert parse_coverage_json(tmp_path / "missing.json", tmp_path) == {}


@pytest.mark.integration
def test_parse_coverage_json_normalizes_paths_and_computes_percentages(tmp_path: Path) -> None:
    """Verify parse_coverage_json handles relative, inside-root, and outside-root paths."""
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
# GROUP 2: Pytest Coverage Runner Execution
# Note: Verifies command construction, no-target fallback, and mocked runner.
# ==========================================================================


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
    assert result.files["src/pkg/mod.py"].total_cov_pct == 100.0
    assert "Running pytest across 1 target(s)" in buf.getvalue()


@pytest.mark.regression
def test_run_pytest_coverage_empty_stdout_uses_exit_code_fallback(tmp_path: Path) -> None:
    """Verify empty pytest stdout falls back to an exit-code summary note."""
    (tmp_path / "tests" / "t1").mkdir(parents=True)
    cfg = load_config(workspace_root=tmp_path, env={})
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=(), test_paths=("tests/t1",)),
    )

    def fake_runner(cmd: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 2, stdout="   \n", stderr="err")

    result = run_pytest_coverage(cfg, batches, progress=None, runner=fake_runner)

    assert result.exit_code == 2
    assert result.summary_note == "pytest exited with code 2"
