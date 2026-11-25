"""Path: tests/test_gen_desk_tools/test_metrics/test_import_collector.py

Unit, regression, integration, and invariant tests for import_collector.

Operational Role:
    Verifies AST import extraction, stdlib filtering, GDA unidirectional
    architectural boundary checks, RARE-06 dynamic/star/relative import
    resolution, GAP-10 resilience to SyntaxError and non-UTF-8 files,
    4-tier logging emission, and ImportEdgeRecord immutability.
"""

from __future__ import annotations

import dataclasses
import io
import logging
from pathlib import Path

import pytest

from gen_desk_tools.metrics.collectors import import_collector as import_mod
from gen_desk_tools.metrics.collectors.import_collector import (
    ImportEdgeRecord,
    collect_import_graph,
)
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.5"

_IMPORT_LOGGER = "gen_desk_tools.metrics.collectors.import_collector"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end boundary detection, stdlib filtering, and progress updates.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_collect_import_graph_detects_boundary_violations_and_filters_stdlib(
    tmp_path: Path,
) -> None:
    """Verify stdlib imports are omitted while third-party and boundary violations stay."""
    core_dir = tmp_path / "src" / "gda" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "errors.py").write_text(
        "import json\n"
        "import pydantic\n"
        "from gda.core import config\n"
        "from gda.io import backup\n"
        "from . import local_only\n",
        encoding="utf-8",
    )
    (core_dir / "broken.py").write_text("def bad(:\n", encoding="utf-8")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    edges = collect_import_graph(tmp_path, batches, progress=reporter)
    by_target = {e.imported_module: e for e in edges}

    assert "json" not in by_target
    assert by_target["pydantic"].target_layer == "third_party"
    assert by_target["pydantic"].boundary_violation is False
    assert by_target["gda.core"].boundary_violation is False
    assert by_target["gda.io"].boundary_violation is True
    assert "gda.core cannot import gda.io" in by_target["gda.io"].violation_reason
    assert "Import dependency graph: 2/2 (100%)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports, GDA tier allowlist, and non-GDA layers.
# ==========================================================================


@pytest.mark.unit
def test_import_collector_exposes_expected_public_interface() -> None:
    """Verify import_collector exports its expected public symbols."""
    expected = {
        "ImportEdgeRecord",
        "collect_import_graph",
    }
    assert expected.issubset(set(import_mod.__all__))


@pytest.mark.unit
def test_collect_import_graph_handles_non_gda_layers_without_progress(tmp_path: Path) -> None:
    """Verify system modules importing gda are not flagged as boundary violations."""
    sys_dir = tmp_path / "src" / "system"
    sys_dir.mkdir(parents=True)
    (sys_dir / "__init__.py").write_text("import gda.core\n", encoding="utf-8")
    batches = (BatchDefinition("Group-S", "system", "Sys", ("src/system",), ()),)

    edges = collect_import_graph(tmp_path, batches, progress=None)

    assert len(edges) == 1
    assert edges[0].source_module == "system"
    assert edges[0].source_layer == "system"
    assert edges[0].boundary_violation is False


@pytest.mark.unit
def test_collect_import_graph_enforces_gda_io_layer_allowlist(tmp_path: Path) -> None:
    """Verify gda.io may import gda.core but is flagged when importing gda.model."""
    io_dir = tmp_path / "src" / "gda" / "io"
    io_dir.mkdir(parents=True)
    (io_dir / "writer.py").write_text(
        "from gda.core import config\nfrom gda.model import person\n",
        encoding="utf-8",
    )
    batches = (BatchDefinition("B2", "gda", "T1", ("src/gda/io",), ()),)

    edges = collect_import_graph(tmp_path, batches, progress=None)
    by_target = {e.imported_module: e for e in edges}

    assert by_target["gda.core"].boundary_violation is False
    assert by_target["gda.model"].boundary_violation is True
    assert "gda.io cannot import gda.model" in by_target["gda.model"].violation_reason


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Empty batches and RARE-06 dynamic, star, and multi-level relative imports.
# ==========================================================================


@pytest.mark.regression
def test_collect_import_graph_empty_batches_returns_empty_tuple(tmp_path: Path) -> None:
    """Verify collect_import_graph returns an empty tuple when given no batches."""
    assert collect_import_graph(tmp_path, ()) == ()


@pytest.mark.regression
@pytest.mark.integration
def test_collect_import_graph_detects_dynamic_star_and_relative_imports(
    tmp_path: Path,
) -> None:
    """Verify RARE-06: dynamic, star, and multi-level relative imports resolve layers."""
    sub_dir = tmp_path / "src" / "gda" / "core" / "sub"
    sub_dir.mkdir(parents=True)
    (sub_dir / "tricky.py").write_text(
        "import importlib\n"
        "from gda.enums import *\n"
        "from ...io import backup\n"
        "from .....external_pkg import thing\n"
        'mod = importlib.import_module("gda.model.person")\n'
        'dyn_name = "gda.model.event"\n'
        "importlib.import_module(dyn_name)\n"
        'print("ok")\n',
        encoding="utf-8",
    )
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    edges = collect_import_graph(tmp_path, batches, progress=None)
    by_target = {e.imported_module: e for e in edges}

    assert by_target["gda.enums"].boundary_violation is True
    assert by_target["gda.io"].boundary_violation is True
    assert by_target["gda.model.person"].boundary_violation is True
    assert by_target["external_pkg"].target_layer == "third_party"


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: GAP-10 resilience to SyntaxError and non-UTF-8 source files.
# ==========================================================================


@pytest.mark.regression
@pytest.mark.integration
def test_collect_import_graph_skips_syntax_error_and_logs_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-10: SyntaxError logs ERROR and analyzes remaining valid files."""
    core_dir = tmp_path / "src" / "gda" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "good.py").write_text("import pydantic\n", encoding="utf-8")
    (core_dir / "broken.py").write_text("def oops(:\n", encoding="utf-8")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    with caplog.at_level(logging.ERROR, logger=_IMPORT_LOGGER):
        edges = collect_import_graph(tmp_path, batches, progress=None)

    assert [e.imported_module for e in edges] == ["pydantic"]
    assert any(r.levelname == "ERROR" and "broken.py" in r.message for r in caplog.records)


@pytest.mark.regression
@pytest.mark.integration
def test_collect_import_graph_skips_non_utf8_file_and_logs_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-10: non-UTF-8 bytes log ERROR and analyze remaining valid files."""
    core_dir = tmp_path / "src" / "gda" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "good.py").write_text("import pydantic\n", encoding="utf-8")
    (core_dir / "corrupt.py").write_bytes(b"\xff\xfe\x00\x01")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    with caplog.at_level(logging.ERROR, logger=_IMPORT_LOGGER):
        edges = collect_import_graph(tmp_path, batches, progress=None)

    assert [e.imported_module for e in edges] == ["pydantic"]
    assert any(r.levelname == "ERROR" and "corrupt.py" in r.message for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_collect_import_graph_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify collect_import_graph emits INFO, VERBOSE, and DEBUG log records."""
    core_dir = tmp_path / "src" / "gda" / "core"
    core_dir.mkdir(parents=True)
    (core_dir / "mod.py").write_text("import pydantic\n", encoding="utf-8")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    with caplog.at_level(logging.DEBUG, logger=_IMPORT_LOGGER):
        collect_import_graph(tmp_path, batches, progress=None)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Frozen dataclass immutability for ImportEdgeRecord.
# ==========================================================================


# TODO: repair test test_import_edge_record_is_immutable
@pytest.mark.integrity
def test_import_edge_record_is_immutable() -> None:
    """Verify ImportEdgeRecord rejects in-place attribute mutation."""
    edge = ImportEdgeRecord("B1", "gda.core.a", "gda.io.b", "gda.core", "gda.io", True, "violation")

    with pytest.raises(dataclasses.FrozenInstanceError):
        edge.boundary_violation = False  # type: ignore[misc]
