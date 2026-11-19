"""Path: tests/test_system/gd_metrics/test_hygiene_collector.py

Unit and integration tests for system.gd_metrics.collectors.hygiene_collector.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from system.gd_metrics.collectors.hygiene_collector import collect_hygiene_metrics
from system.gd_metrics.config import BatchDefinition
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.2"


# ==========================================================================
# GROUP 1: Clean Module Hygiene & Progress Reporting
# Note: Verifies compliant modules, __init__ exemption, and prefixed test match.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_collect_hygiene_metrics_passes_compliant_module_and_init(tmp_path: Path) -> None:
    """Verify compliant modules, prefixed test files, and __init__.py pass cleanly."""
    pkg = tmp_path / "src" / "gda" / "core"
    pkg.mkdir(parents=True)
    (pkg / "README.md").write_text("# Core\n- alpha.py\n- beta.py\n", encoding="utf-8")
    (pkg / "alpha.py").write_text(
        '"""Path: src/gda/core/alpha.py\n\nAlpha module.\n"""\n'
        "from __future__ import annotations\n"
        '__version__ = "1.0.0+build.1"\n'
        '__all__ = ["X"]\n'
        "X, Y = 1, 2\n",
        encoding="utf-8",
    )
    (pkg / "beta.py").write_text(
        '"""Path: src/gda/core/beta.py\n\nBeta module.\n"""\n'
        "from __future__ import annotations\n"
        '__version__ = "1.0.0+build.1"\n',
        encoding="utf-8",
    )
    (pkg / "__init__.py").write_text(
        '"""Path: src/gda/core/__init__.py\n\nInit.\n"""\n'
        "from __future__ import annotations\n"
        '__version__ = "1.0.0+build.1"\n',
        encoding="utf-8",
    )
    test_dir = tmp_path / "tests" / "test_gda" / "test_core"
    test_dir.mkdir(parents=True)
    (test_dir / "test_core_alpha.py").write_text("def test_ok(): pass\n", encoding="utf-8")

    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    records = collect_hygiene_metrics(tmp_path, batches, progress=reporter)
    by_path = {r.file_path: r for r in records}

    assert by_path["src/gda/core/alpha.py"].hygiene_flags == ()
    assert by_path["src/gda/core/alpha.py"].has_all is True
    assert by_path["src/gda/core/beta.py"].hygiene_flags == ("MISSING_TEST_FILE",)
    assert by_path["src/gda/core/__init__.py"].hygiene_flags == ()
    assert "Module hygiene audit: 3/3 (100%)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Hygiene Violations, Syntax Errors & Non-src Paths
# Note: Verifies missing docstring, bad version, missing README/tests, syntax.
# ==========================================================================


@pytest.mark.regression
def test_collect_hygiene_metrics_flags_missing_metadata_and_syntax_error(tmp_path: Path) -> None:
    """Verify hygiene violations and SyntaxError files are flagged without crashing."""
    loose = tmp_path / "scripts"
    loose.mkdir(parents=True)
    (loose / "bad_meta.py").write_text("x = 1\n", encoding="utf-8")
    (loose / "broken.py").write_text("def oops(:\n", encoding="utf-8")
    batches = (BatchDefinition("B2", "system", "Sys", ("scripts",), ()),)

    records = collect_hygiene_metrics(tmp_path, batches, progress=None)
    by_path = {r.file_path: r for r in records}

    assert "MISSING_PATH_HEADER" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "INVALID_VERSION" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "NO_FUTURE_ANNOTATIONS" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "NOT_IN_README" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "MISSING_TEST_FILE" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert by_path["scripts/broken.py"].hygiene_flags == ("SYNTAX_ERROR",)
