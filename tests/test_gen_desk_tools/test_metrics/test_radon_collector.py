"""Path: tests/test_gen_desk_tools/test_metrics/test_radon_collector.py

Unit, regression, integration, and invariant tests for radon_collector.

Operational Role:
    Verifies batch file discovery (including deduplication and circular-link
    protection), per-file Radon raw/MI/CC calculations, hotspot extraction,
    resilience to SyntaxError and non-UTF-8 source files (GAP-10), 4-tier
    logging emission (ERROR, INFO, VERBOSE, DEBUG), rollup aggregation, and
    frozen dataclass immutability.
"""

from __future__ import annotations

import dataclasses
import io
import logging
from pathlib import Path

import pytest

from gen_desk_tools.metrics.collectors import radon_collector as radon_mod
from gen_desk_tools.metrics.collectors.radon_collector import (
    COMPLEXITY_HOTSPOT_THRESHOLD,
    BatchRadonRollup,
    ComplexityHotspot,
    FileRadonMetrics,
    analyze_file_radon,
    collect_radon_metrics,
    discover_batch_files,
)
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.4"

_RADON_LOGGER = "gen_desk_tools.metrics.collectors.radon_collector"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end hotspot extraction and multi-batch rollup aggregation.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_analyze_file_radon_detects_method_hotspot_above_threshold(tmp_path: Path) -> None:
    """Verify analyze_file_radon flags class and method blocks with CC >= 11."""
    branches = "\n".join(f"        if x == {i}:\n            return {i}" for i in range(12))
    code = (
        '"""Module docstring."""\n'
        "# inline comment\n"
        "class Worker:\n"
        "    def complex_method(self, x: int) -> int:\n"
        f"{branches}\n"
        "        return -1\n"
    )
    target = tmp_path / "worker.py"
    target.write_text(code, encoding="utf-8")

    result = analyze_file_radon(target, tmp_path, "B1")

    assert result.cc_c_plus_count == 2
    assert result.max_cc >= COMPLEXITY_HOTSPOT_THRESHOLD
    assert any(h.kind == "M" and h.symbol == "Worker.complex_method" for h in result.hotspots)
    assert any(h.kind == "C" and h.symbol == "Worker" for h in result.hotspots)


@pytest.mark.smoke
@pytest.mark.integration
def test_collect_radon_metrics_aggregates_rollups_and_reports_progress(tmp_path: Path) -> None:
    """Verify collect_radon_metrics aggregates totals and emits progress updates."""
    mod = tmp_path / "mod.py"
    mod.write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=("mod.py",), test_paths=()),
        BatchDefinition(id="B2", scope="cli", tier="T1", paths=("missing",), test_paths=()),
    )
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    file_metrics, rollups = collect_radon_metrics(tmp_path, batches, progress=reporter)

    assert len(file_metrics) == 1
    assert len(rollups) == 2
    assert rollups[0].file_count == 1
    assert rollups[0].avg_cc > 0
    assert rollups[1].file_count == 0
    assert rollups[1].doc_pct == 0.0
    assert "Radon (B1): 1/1 (100%)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface, standalone functions below threshold, and no-progress runs.
# ==========================================================================


@pytest.mark.unit
def test_radon_collector_exposes_expected_public_interface() -> None:
    """Verify radon_collector exports its expected public symbols and threshold."""
    expected = {
        "BatchRadonRollup",
        "ComplexityHotspot",
        "FileRadonMetrics",
        "analyze_file_radon",
        "collect_radon_metrics",
        "discover_batch_files",
    }
    assert expected.issubset(set(radon_mod.__all__))
    assert COMPLEXITY_HOTSPOT_THRESHOLD == 11


@pytest.mark.integration
def test_analyze_file_radon_standalone_function_below_threshold_has_no_hotspots(
    tmp_path: Path,
) -> None:
    """Verify standalone functions with CC < 11 report kind F and empty hotspots."""
    target = tmp_path / "helper.py"
    target.write_text(
        "def score(x: int) -> int:\n    if x > 0:\n        return x\n    return 0\n",
        encoding="utf-8",
    )

    result = analyze_file_radon(target, tmp_path, "B1")

    assert result.max_cc == 2
    assert result.max_cc_grade == "A"
    assert result.max_cc_symbol == "F score:1"
    assert result.cc_c_plus_count == 0
    assert result.hotspots == ()


@pytest.mark.integration
def test_collect_radon_metrics_without_progress_reporter_succeeds(tmp_path: Path) -> None:
    """Verify collect_radon_metrics works cleanly when progress is None."""
    mod = tmp_path / "simple.py"
    mod.write_text("x = 1\n", encoding="utf-8")
    batches = (
        BatchDefinition(id="B1", scope="gda", tier="T0", paths=("simple.py",), test_paths=()),
    )

    file_metrics, rollups = collect_radon_metrics(tmp_path, batches, progress=None)

    assert len(file_metrics) == 1
    assert rollups[0].avg_cc == 0.0


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Discovery filtering, deduplication, empty inputs, and RARE-01 loop guard.
# ==========================================================================


@pytest.mark.integration
def test_discover_batch_files_handles_files_dirs_pycache_and_missing(tmp_path: Path) -> None:
    """Verify discover_batch_files returns sorted .py files and ignores non-Python/cache."""
    pkg = tmp_path / "src" / "pkg"
    cache = pkg / "__pycache__"
    cache.mkdir(parents=True)
    (pkg / "b.py").write_text("x = 1\n", encoding="utf-8")
    (pkg / "a.py").write_text("y = 2\n", encoding="utf-8")
    (cache / "cached.py").write_text("z = 3\n", encoding="utf-8")
    (tmp_path / "single.py").write_text("s = 4\n", encoding="utf-8")
    (tmp_path / "readme.txt").write_text("ignore\n", encoding="utf-8")

    batch = BatchDefinition(
        id="B1",
        scope="gda",
        tier="Tier 0",
        paths=("src/pkg", "single.py", "readme.txt", "does/not/exist"),
        test_paths=(),
    )

    files = discover_batch_files(tmp_path, batch)

    assert [f.relative_to(tmp_path).as_posix() for f in files] == [
        "single.py",
        "src/pkg/a.py",
        "src/pkg/b.py",
    ]


@pytest.mark.regression
@pytest.mark.integration
def test_discover_batch_files_deduplicates_overlapping_paths(tmp_path: Path) -> None:
    """Verify overlapping directory and file paths yield each module only once."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "a.py").write_text("x = 1\n", encoding="utf-8")

    batch = BatchDefinition(
        id="B1",
        scope="gda",
        tier="T0",
        paths=("src/pkg", "src/pkg/a.py", "src/pkg"),
        test_paths=(),
    )

    files = discover_batch_files(tmp_path, batch)

    assert [f.relative_to(tmp_path).as_posix() for f in files] == ["src/pkg/a.py"]


@pytest.mark.regression
def test_analyze_file_radon_empty_file_returns_zero_metrics(tmp_path: Path) -> None:
    """Verify an empty Python file yields zero SLOC, MI Grade A, and no hotspots."""
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")

    result = analyze_file_radon(empty, tmp_path, "B1")

    assert result.sloc == 0
    assert result.doc_pct == 0.0
    assert result.max_cc == 0
    assert result.max_cc_symbol == "-"
    assert result.hotspots == ()


@pytest.mark.regression
def test_collect_radon_metrics_empty_batches_returns_empty_tuples(tmp_path: Path) -> None:
    """Verify collect_radon_metrics returns empty tuples when given no batches."""
    file_metrics, rollups = collect_radon_metrics(tmp_path, ())

    assert file_metrics == ()
    assert rollups == ()


@pytest.mark.regression
def test_discover_batch_files_guards_against_circular_symlink_loop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify RARE-01: circular symlink/rglob recursion error is caught cleanly."""
    # Simulate a circular directory symlink/junction without requiring Windows admin rights.
    cyclic_dir = tmp_path / "src" / "cyclic"
    cyclic_dir.mkdir(parents=True)
    valid_file = tmp_path / "valid.py"
    valid_file.write_text("x = 1\n", encoding="utf-8")

    original_rglob = Path.rglob

    def _cyclic_rglob(self: Path, pattern: str) -> object:
        if self == cyclic_dir:
            raise RecursionError("circular symlink loop")
        return original_rglob(self, pattern)

    monkeypatch.setattr(Path, "rglob", _cyclic_rglob)
    batch = BatchDefinition(
        id="B1",
        scope="gda",
        tier="T0",
        paths=("src/cyclic", "valid.py"),
        test_paths=(),
    )

    with caplog.at_level(logging.ERROR, logger=_RADON_LOGGER):
        files = discover_batch_files(tmp_path, batch)

    assert [f.relative_to(tmp_path).as_posix() for f in files] == ["valid.py"]
    assert any(r.levelname == "ERROR" for r in caplog.records)


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: GAP-10 resilience (SyntaxError / non-UTF-8) and direct path failures.
# ==========================================================================


@pytest.mark.regression
@pytest.mark.integration
def test_collect_radon_metrics_skips_syntax_error_file_and_logs_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-10: SyntaxError in one file logs ERROR and scores remaining files."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "good.py").write_text("def ok() -> int:\n    return 1\n", encoding="utf-8")
    (pkg / "broken.py").write_text("def oops(:\n", encoding="utf-8")
    batches = (BatchDefinition(id="B1", scope="gda", tier="T0", paths=("src/pkg",), test_paths=()),)

    with caplog.at_level(logging.ERROR, logger=_RADON_LOGGER):
        file_metrics, rollups = collect_radon_metrics(tmp_path, batches)

    assert [m.file_path for m in file_metrics] == ["src/pkg/good.py"]
    assert rollups[0].file_count == 1
    assert any(r.levelname == "ERROR" and "broken.py" in r.message for r in caplog.records)


@pytest.mark.regression
@pytest.mark.integration
def test_collect_radon_metrics_skips_non_utf8_file_and_logs_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-10: non-UTF-8 bytes in one file log ERROR and score remaining files."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "good.py").write_text("x = 42\n", encoding="utf-8")
    (pkg / "corrupt.py").write_bytes(b"\xff\xfe\x00\x01")
    batches = (BatchDefinition(id="B1", scope="gda", tier="T0", paths=("src/pkg",), test_paths=()),)

    with caplog.at_level(logging.ERROR, logger=_RADON_LOGGER):
        file_metrics, rollups = collect_radon_metrics(tmp_path, batches)

    assert [m.file_path for m in file_metrics] == ["src/pkg/good.py"]
    assert rollups[0].file_count == 1
    assert any(r.levelname == "ERROR" and "corrupt.py" in r.message for r in caplog.records)


@pytest.mark.regression
def test_analyze_file_radon_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """Verify analyze_file_radon raises FileNotFoundError for a nonexistent file."""
    with pytest.raises(FileNotFoundError):
        analyze_file_radon(tmp_path / "missing.py", tmp_path, "B1")


@pytest.mark.regression
def test_analyze_file_radon_directory_path_raises_os_error(tmp_path: Path) -> None:
    """Verify analyze_file_radon raises OSError when given a directory instead of a file."""
    folder = tmp_path / "not_a_file.py"
    folder.mkdir()

    with pytest.raises(OSError):
        analyze_file_radon(folder, tmp_path, "B1")


@pytest.mark.regression
def test_analyze_file_radon_external_file_raises_value_error(tmp_path: Path) -> None:
    """Verify analyze_file_radon raises ValueError when file_path is outside workspace_root."""
    ws = tmp_path / "workspace"
    ws.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("x = 1\n", encoding="utf-8")

    with pytest.raises(ValueError):
        analyze_file_radon(outside, ws, "B1")


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG, ERROR) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_collect_radon_metrics_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify collect_radon_metrics emits INFO, VERBOSE, and DEBUG log records."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text("def ok() -> int:\n    return 1\n", encoding="utf-8")
    batches = (BatchDefinition(id="B1", scope="gda", tier="T0", paths=("src/pkg",), test_paths=()),)

    with caplog.at_level(logging.DEBUG, logger=_RADON_LOGGER):
        collect_radon_metrics(tmp_path, batches)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


@pytest.mark.regression
@pytest.mark.integration
def test_analyze_file_radon_emits_error_log_record_on_read_failure(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify analyze_file_radon logs an ERROR record before raising on missing file."""
    with caplog.at_level(logging.ERROR, logger=_RADON_LOGGER):
        with pytest.raises(FileNotFoundError):
            analyze_file_radon(tmp_path / "missing.py", tmp_path, "B1")

    assert any(record.levelname == "ERROR" for record in caplog.records)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Frozen dataclass immutability across all Radon metric records.
# ==========================================================================


@pytest.mark.integrity
def test_radon_dataclasses_are_immutable() -> None:
    """Verify ComplexityHotspot, FileRadonMetrics, and BatchRadonRollup reject mutation."""
    hotspot = ComplexityHotspot("B1", "src/a.py", 1, "F", "fn", 12, "C")
    file_rec = FileRadonMetrics(
        "B1", "src/a.py", 10, 5, 6, 2, 1, 1, 33.3, 80.0, "A", 2.0, 2, "A", "F fn:1", 0, ()
    )
    rollup = BatchRadonRollup("B1", "gda", "T0", 1, 10, 5, 6, 2, 1, 1, 33.3, 2.0, 0, 0)

    with pytest.raises(dataclasses.FrozenInstanceError):
        hotspot.complexity = 99  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        file_rec.sloc = 0  # type: ignore[misc]
    with pytest.raises(dataclasses.FrozenInstanceError):
        rollup.file_count = 99  # type: ignore[misc]
