"""Path: tests/test_gen_desk_tools/test_metrics/test_hygiene_collector.py

Unit, regression, integration, and invariant tests for hygiene_collector.

Operational Role:
    Verifies AST-based module hygiene checks (Path header, PEP 440 version,
    __all__, future annotations, README.md listing, test parity), __init__
    and __main__ exemptions, GAP-10 resilience to SyntaxError, OSError, and
    non-UTF-8 files, 4-tier logging emission, and ModuleHygieneRecord immutability.
"""

from __future__ import annotations

import dataclasses
import io
import logging
from pathlib import Path

import pytest

from gen_desk_tools.metrics.collectors import hygiene_collector as hygiene_mod
from gen_desk_tools.metrics.collectors.hygiene_collector import (
    ModuleHygieneRecord,
    collect_hygiene_metrics,
)
from gen_desk_tools.metrics.config import BatchDefinition
from gen_desk_tools.metrics.progress import ProgressReporter

__version__ = "1.0.0+build.4"

_HYGIENE_LOGGER = "gen_desk_tools.metrics.collectors.hygiene_collector"


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end compliant module scan, exemptions, and ProgressReporter.
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
# GROUP 2: Core Logic & Happy Paths
# Note: Public interface exports and __main__.py exemption behavior.
# ==========================================================================


@pytest.mark.unit
def test_hygiene_collector_exposes_expected_public_interface() -> None:
    """Verify hygiene_collector exports its expected public symbols."""
    expected = {
        "ModuleHygieneRecord",
        "collect_hygiene_metrics",
    }
    assert expected.issubset(set(hygiene_mod.__all__))


@pytest.mark.integration
def test_collect_hygiene_metrics_exempts_main_module_from_readme_and_tests(
    tmp_path: Path,
) -> None:
    """Verify __main__.py is exempt from README listing and test file parity."""
    pkg = tmp_path / "src" / "gda" / "cli"
    pkg.mkdir(parents=True)
    (pkg / "__main__.py").write_text(
        '"""Path: src/gda/cli/__main__.py\n\nEntrypoint.\n"""\n'
        "from __future__ import annotations\n"
        '__version__ = "1.0.0+build.1"\n',
        encoding="utf-8",
    )
    batches = (BatchDefinition("B1", "cli", "T1", ("src/gda/cli",), ()),)

    records = collect_hygiene_metrics(tmp_path, batches, progress=None)

    assert len(records) == 1
    assert records[0].readme_listed is True
    assert records[0].test_file_exists is True
    assert records[0].hygiene_flags == ()


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Empty batch tuples return empty records without error.
# ==========================================================================


@pytest.mark.regression
def test_collect_hygiene_metrics_empty_batches_returns_empty_tuple(tmp_path: Path) -> None:
    """Verify collect_hygiene_metrics returns an empty tuple when given no batches."""
    assert collect_hygiene_metrics(tmp_path, ()) == ()


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Missing metadata flags and GAP-10 resilience (SyntaxError / non-UTF-8 / OSError).
# ==========================================================================


@pytest.mark.regression
def test_collect_hygiene_metrics_flags_missing_metadata_and_syntax_error(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify hygiene violations and SyntaxError files are flagged without crashing."""
    loose = tmp_path / "scripts"
    loose.mkdir(parents=True)
    (loose / "bad_meta.py").write_text("x = 1\n", encoding="utf-8")
    (loose / "broken.py").write_text("def oops(:\n", encoding="utf-8")
    batches = (BatchDefinition("B2", "system", "Sys", ("scripts",), ()),)

    with caplog.at_level(logging.ERROR, logger=_HYGIENE_LOGGER):
        records = collect_hygiene_metrics(tmp_path, batches, progress=None)

    by_path = {r.file_path: r for r in records}
    assert "MISSING_PATH_HEADER" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "INVALID_VERSION" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "NO_FUTURE_ANNOTATIONS" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "NOT_IN_README" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert "MISSING_TEST_FILE" in by_path["scripts/bad_meta.py"].hygiene_flags
    assert by_path["scripts/broken.py"].hygiene_flags == ("SYNTAX_ERROR",)
    assert any(r.levelname == "ERROR" and "broken.py" in r.message for r in caplog.records)


@pytest.mark.regression
@pytest.mark.integration
def test_collect_hygiene_metrics_handles_non_utf8_file_without_crashing(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify GAP-10: non-UTF-8 bytes log ERROR, flag the file, and audit remaining files."""
    pkg = tmp_path / "src" / "gda" / "core"
    pkg.mkdir(parents=True)
    (pkg / "good.py").write_text(
        '"""Path: src/gda/core/good.py\n\nGood.\n"""\n'
        "from __future__ import annotations\n"
        '__version__ = "1.0.0+build.1"\n',
        encoding="utf-8",
    )
    (pkg / "corrupt.py").write_bytes(b"\xff\xfe\x00\x01")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    with caplog.at_level(logging.ERROR, logger=_HYGIENE_LOGGER):
        records = collect_hygiene_metrics(tmp_path, batches, progress=None)

    by_path = {r.file_path: r for r in records}
    assert "src/gda/core/good.py" in by_path
    assert "ENCODING_ERROR" in by_path["src/gda/core/corrupt.py"].hygiene_flags
    assert any(r.levelname == "ERROR" and "corrupt.py" in r.message for r in caplog.records)


@pytest.mark.regression
@pytest.mark.integration
def test_collect_hygiene_metrics_handles_os_error_without_crashing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify OSError during file read logs ERROR, flags READ_ERROR, and continues."""
    pkg = tmp_path / "src" / "gda" / "core"
    pkg.mkdir(parents=True)
    (pkg / "good.py").write_text("x = 1\n", encoding="utf-8")
    locked = pkg / "locked.py"
    locked.write_text("x = 2\n", encoding="utf-8")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    original_read_text = Path.read_text

    def _guarded_read_text(self: Path, *args: object, **kwargs: object) -> str:
        if self == locked:
            raise PermissionError("access denied")
        return original_read_text(self, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "read_text", _guarded_read_text)

    with caplog.at_level(logging.ERROR, logger=_HYGIENE_LOGGER):
        records = collect_hygiene_metrics(tmp_path, batches, progress=None)

    by_path = {r.file_path: r for r in records}
    assert "src/gda/core/good.py" in by_path
    assert by_path["src/gda/core/locked.py"].hygiene_flags == ("READ_ERROR",)
    assert any(r.levelname == "ERROR" and "locked.py" in r.message for r in caplog.records)


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: 4-tier logging emission (INFO, VERBOSE, DEBUG) via caplog.
# ==========================================================================


@pytest.mark.integration
def test_collect_hygiene_metrics_emits_info_verbose_and_debug_log_records(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify collect_hygiene_metrics emits INFO, VERBOSE, and DEBUG log records."""
    pkg = tmp_path / "src" / "gda" / "core"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text("x = 1\n", encoding="utf-8")
    batches = (BatchDefinition("B1", "gda", "T0", ("src/gda/core",), ()),)

    with caplog.at_level(logging.DEBUG, logger=_HYGIENE_LOGGER):
        collect_hygiene_metrics(tmp_path, batches, progress=None)

    levels = {record.levelname for record in caplog.records}
    assert {"INFO", "VERBOSE", "DEBUG"}.issubset(levels)


# ==========================================================================
# GROUP 6: Integrity & Invariants
# Note: Frozen dataclass immutability for ModuleHygieneRecord.
# ==========================================================================


@pytest.mark.integrity
def test_module_hygiene_record_is_immutable() -> None:
    """Verify ModuleHygieneRecord rejects in-place attribute mutation."""
    rec = ModuleHygieneRecord(
        "B1", "src/gda/core/a.py", True, "1.0.0+build.1", True, True, True, True, True, ()
    )

    with pytest.raises(dataclasses.FrozenInstanceError):
        rec.pep440_valid = False  # type: ignore[misc]
