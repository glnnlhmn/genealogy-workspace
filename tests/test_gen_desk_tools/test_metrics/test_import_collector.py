"""Path: tests/test_gen_desk_tools/test_metrics/test_import_collector.py

Unit and integration tests for gen_desk_tools.metrics.collectors.import_collector.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from gen_desk_tools.metrics.collectors.import_collector import collect_import_graph
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"


# ==========================================================================
# GROUP 1: Import Graph & Architectural Boundary Violations
# Note: Verifies stdlib filtering, third-party edges, and boundary checks.
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
