"""Path: tests/test_system/gd_metrics/test_pytest_analyzer.py

Unit and integration tests for system.gd_metrics.collectors.pytest_analyzer.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from system.gd_metrics.collectors.pytest_analyzer import analyze_pytest_suite
from system.gd_metrics.config import BatchDefinition
from system.gd_metrics.progress import ProgressReporter

__version__ = "1.0.0+build.3"


# ==========================================================================
# GROUP 1: Conftest Hierarchy & Fixture Reuse Tracking
# Note: Verifies ancestor conftest discovery, reuse counts, unused & shadowed.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_analyze_pytest_suite_maps_conftest_fixtures_and_reuse_counts(tmp_path: Path) -> None:
    """Verify analyze_pytest_suite tracks ancestor conftest fixtures, reuse, and shadowing."""
    tests_root = tmp_path / "tests"
    sub_dir = tests_root / "test_gda"
    cache_dir = sub_dir / "__pycache__"
    cache_dir.mkdir(parents=True)

    (tests_root / "conftest.py").write_text(
        "import pytest\n"
        "@pytest.fixture(scope='session', ids=['a'])\n"
        "def shared_db():\n"
        "    return 'db'\n"
        "@pytest.fixture(autouse=True, params=[1, 2], name='auto_env')\n"
        "def _auto_env(shared_db):\n"
        "    return shared_db\n"
        "@custom_decorator\n"
        "def helper_func():\n"
        "    return 1\n",
        encoding="utf-8",
    )
    (sub_dir / "conftest.py").write_text(
        "from pytest import fixture\n"
        "@fixture\n"
        "def shared_db():\n"
        "    return 'override'\n"
        "@fixture\n"
        "def unused_fix():\n"
        "    return 0\n"
        "x = 1\n",
        encoding="utf-8",
    )
    (sub_dir / "helpers.py").write_text("VALUE = 1\n", encoding="utf-8")
    (cache_dir / "test_cached.py").write_text("def test_ignore(): pass\n", encoding="utf-8")
    (sub_dir / "test_sample.py").write_text(
        "import pytest\n"
        "FIX_NAME = 'shared_db'\n"
        "@custom_dec\n"
        "@pytest.mark.unit\n"
        "@pytest.mark.parametrize('x', [1])\n"
        "@pytest.mark.usefixtures('shared_db', FIX_NAME)\n"
        "def test_one(shared_db, x):\n"
        "    assert shared_db\n",
        encoding="utf-8",
    )

    batches = (
        BatchDefinition(
            id="GDA-Batch-1",
            scope="gda",
            tier="T0",
            paths=("src/gda",),
            test_paths=("tests/test_gda", "tests/missing"),
        ),
    )
    buf = io.StringIO()
    reporter = ProgressReporter(total_stages=1, stream=buf)

    result = analyze_pytest_suite(
        tmp_path,
        batches,
        registered_markers=("unit", "smoke"),
        progress=reporter,
    )

    by_key = {(f.conftest_path, f.name): f for f in result.fixtures}
    assert by_key[("tests/conftest.py", "shared_db")].reuse_count == 3
    assert by_key[("tests/conftest.py", "shared_db")].is_shadowed is True
    assert by_key[("tests/conftest.py", "shared_db")].shadowed_by == ("tests/test_gda/conftest.py",)
    assert by_key[("tests/conftest.py", "auto_env")].autouse is True
    assert by_key[("tests/conftest.py", "auto_env")].parameterized is True
    assert by_key[("tests/conftest.py", "auto_env")].is_unused is False
    assert by_key[("tests/test_gda/conftest.py", "unused_fix")].is_unused is True
    assert result.marker_summaries[0].unregistered_markers == ()
    assert result.total_unused_fixtures == 1
    assert "Pytest AST analysis: 1/1 (100%)" in buf.getvalue()


# ==========================================================================
# GROUP 2: Marker Hygiene, Class Tests & Ancestor Walk Boundaries
# Note: Verifies unmarked tests, unregistered markers, smoke inflation, edges.
# ==========================================================================


@pytest.mark.integration
def test_analyze_pytest_suite_detects_marker_hygiene_and_class_tests(tmp_path: Path) -> None:
    """Verify unmarked tests, unregistered markers, and smoke inflation are flagged."""
    t_dir = tmp_path / "alt_tests" / "test_sys"
    t_dir.mkdir(parents=True)
    (t_dir / "test_markers.py").write_text(
        "import pytest\n"
        "@pytest.mark.smoke\n"
        "def test_s1(): pass\n"
        "@pytest.mark.smoke\n"
        "def test_s2(): pass\n"
        "@pytest.mark.smoke\n"
        "@pytest.mark.slow\n"
        "def test_s3(): pass\n"
        "@pytest.mark.parametrize('v', [1])\n"
        "def test_unmarked(v): pass\n"
        "@pytest.mark.regression\n"
        "class TestSuite:\n"
        "    def test_in_class(self): pass\n"
        "    def helper(self): pass\n",
        encoding="utf-8",
    )
    batches = (
        BatchDefinition(
            id="Group-S",
            scope="system",
            tier="Sys",
            paths=(),
            test_paths=("alt_tests/test_sys",),
        ),
    )

    result = analyze_pytest_suite(tmp_path, batches, progress=None)

    summary = result.marker_summaries[0]
    assert summary.test_count == 5
    assert summary.unmarked_count == 1
    assert summary.smoke_count == 3
    assert summary.regression_count == 1
    assert summary.smoke_inflation is True
    assert summary.unregistered_markers == ("slow",)


@pytest.mark.regression
def test_analyze_pytest_suite_handles_syntax_errors_gracefully(tmp_path: Path) -> None:
    """Verify SyntaxError in conftest.py or test file is recorded without crashing."""
    t_dir = tmp_path / "tests" / "test_bad"
    t_dir.mkdir(parents=True)
    (t_dir / "conftest.py").write_text("def broken(:\n", encoding="utf-8")
    (t_dir / "test_broken.py").write_text("def test_bad(:\n", encoding="utf-8")
    batches = (
        BatchDefinition(
            id="B-Bad",
            scope="system",
            tier="Sys",
            paths=(),
            test_paths=("tests/test_bad",),
        ),
    )

    result = analyze_pytest_suite(tmp_path, batches)

    assert result.fixtures == ()
    assert len(result.marker_summaries) == 1
    assert "SyntaxError" in result.marker_summaries[0].parse_error
