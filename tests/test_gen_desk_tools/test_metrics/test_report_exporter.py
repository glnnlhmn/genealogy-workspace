"""Path: tests/test_gen_desk_tools/test_metrics/test_report_exporter.py

Unit, regression, and integration tests for report_exporter.

Operational Role:
    Verifies atomic UTF-8 JSON report generation, schema metadata fields,
    RARE-02 Windows/Google Drive transient file-lock retry and exhaustion
    handling, and 4-tier logging emission.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.metrics.config import load_config
from gen_desk_tools.metrics.exporters import report_exporter as report_mod
from gen_desk_tools.metrics.exporters.report_exporter import write_local_json_report

__version__ = "1.0.0+build.4"

_REPORT_LOGGER = "gen_desk_tools.metrics.exporters.report_exporter"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end JSON report write and schema verification.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_write_local_json_report_writes_expected_schema(tmp_path: Path) -> None:
    """Verify write_local_json_report writes UTC metadata, scopes, and tabs."""
    cfg = load_config(workspace_root=tmp_path, env={})
    payloads: dict[str, list[list[Any]]] = {
        "Master_Scorecard": [["Batch", "Files"], ["B1", 2]],
    }

    out_path = write_local_json_report(cfg, payloads)

    assert out_path.exists()
    assert out_path.name == "gd_metrics_report.json"
    data = json.loads(out_path.read_text(encoding="utf-8"))
    assert data["workspace_root"] == tmp_path.as_posix()
    assert data["scopes"] == list(cfg.scopes)
    assert data["tabs"] == payloads
    assert data["generated_at"].endswith("Z")


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports.
# ==========================================================================


@pytest.mark.unit
def test_report_exporter_exposes_expected_public_interface() -> None:
    """Verify report_exporter exports its expected public symbols."""
    assert "write_local_json_report" in report_mod.__all__


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: RARE-02 transient WinError 32 / PermissionError retry and exhaustion.
# ==========================================================================


@pytest.mark.regression
def test_write_local_json_report_retries_transient_file_lock_and_succeeds(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify RARE-02: transient PermissionError (WinError 32) retries and succeeds."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    cfg = load_config(workspace_root=tmp_path, env={})
    real_atomic_write = report_mod.atomic_write_text
    attempts = {"count": 0}

    def _flaky_write(path: Path, content: str) -> None:
        attempts["count"] += 1
        if attempts["count"] < report_mod._MAX_WRITE_ATTEMPTS:
            raise PermissionError("[WinError 32] file in use by Google Drive")
        real_atomic_write(path, content)

    monkeypatch.setattr(report_mod, "atomic_write_text", _flaky_write)

    out_path = write_local_json_report(cfg, {"Tab1": [["A"]]})

    assert attempts["count"] == report_mod._MAX_WRITE_ATTEMPTS
    assert out_path.exists()


@pytest.mark.regression
def test_write_local_json_report_logs_error_and_raises_when_lock_persists(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify RARE-02: persistent PermissionError logs ERROR and raises after retries."""
    monkeypatch.setattr("time.sleep", lambda _s: None)
    cfg = load_config(workspace_root=tmp_path, env={})

    def _always_locked(_path: Path, _content: str) -> None:
        raise PermissionError("[WinError 32] locked")

    monkeypatch.setattr(report_mod, "atomic_write_text", _always_locked)

    with (
        caplog.at_level(logging.ERROR, logger=_REPORT_LOGGER),
        pytest.raises(PermissionError, match="locked"),
    ):
        write_local_json_report(cfg, {"Tab1": [["A"]]})

    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_write_local_json_report_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify write_local_json_report emits INFO, VERBOSE, and DEBUG log records."""
    cfg = load_config(workspace_root=tmp_path, env={})

    with caplog.at_level(logging.DEBUG, logger=_REPORT_LOGGER):
        write_local_json_report(cfg, {"Tab1": [["Header"], ["Row"]]})

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)
