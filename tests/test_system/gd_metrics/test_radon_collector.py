"""Path: tests/test_system/gd_metrics/test_radon_collector.py

Unit and integration tests for system.gd_metrics.collectors.radon_collector.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from system.gd_metrics.collectors.radon_collector import (
    analyze_file_radon,
    collect_radon_metrics,
    discover_batch_files,
)
from system.gd_metrics.config import BatchDefinition
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"


# ==========================================================================
# GROUP 1: Batch File Discovery
# Note: Verifies file, directory, __pycache__, and missing path filtering.
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


# ==========================================================================
# GROUP 2: Per-File Radon Analysis & Hotspot Detection
# Note: Verifies empty modules, methods, and CC >= 11 hotspot extraction.
# ==========================================================================


@pytest.mark.unit
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
    assert result.max_cc >= 11
    assert any(h.kind == "M" and h.symbol == "Worker.complex_method" for h in result.hotspots)
    assert any(h.kind == "C" and h.symbol == "Worker" for h in result.hotspots)


# ==========================================================================
# GROUP 3: Batch Collection & Rollup Aggregation
# Note: Verifies multi-batch rollups and live ProgressReporter integration.
# ==========================================================================


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


@pytest.mark.unit
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
