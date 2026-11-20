"""Path: tests/test_gen_desk_tools/test_radon_report/test_cli.py

Unit, regression, and integration tests for gen_desk_tools.radon_report.cli.
"""

from __future__ import annotations

import importlib
import runpy
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.radon_report.cli import build_parser, main, run

__version__ = "1.0.0+build.2"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end CLI invocation via main() and python -m execution.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_main_executes_default_mode_and_exits_zero(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify main() generates the default gd_tools Radon report and exits with code 0."""
    pkg = tmp_path / "src" / "gen_desk_tools"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text("VALUE = 42\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc_info:
        main(["--root", str(tmp_path), "--reports-dir", "gtemp", "-o", "cli_radon.txt"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Radon report written to" in captured.out
    assert (tmp_path / "gtemp" / "cli_radon.txt").is_file()


@pytest.mark.integration
def test_module_entrypoint_invokes_cli_main(tmp_path: Path) -> None:
    """Verify python -m gen_desk_tools.radon_report delegates to cli.main()."""
    with patch("sys.argv", ["gdradon", "--root", str(tmp_path), "--reports-dir", "gtemp"]):
        with pytest.raises(SystemExit) as exc_info:
            runpy.run_module("gen_desk_tools.radon_report.__main__", run_name="__main__")
    assert exc_info.value.code == 0


# ==========================================================================
# GROUP 2: Argument Parsing & Error Branches
# Note: Parser options, non-__main__ import branch, and failure paths.
# ==========================================================================


@pytest.mark.unit
def test_build_parser_parses_structure_aligned_flags() -> None:
    """Verify build_parser accepts -m, --include-tests, --reports-dir, -n, and -o."""
    args = build_parser().parse_args(
        ["-m", "gda", "--include-tests", "--reports-dir", "out", "-n", "C", "-o", "r.txt"]
    )
    assert args.mode == "gda"
    assert args.include_tests is True
    assert args.reports_dir == Path("out")
    assert args.min_grade == "C"
    assert args.output == "r.txt"


@pytest.mark.regression
def test_importing_main_module_does_not_execute_entrypoint() -> None:
    """Verify importing __main__ without __name__ == '__main__' skips main()."""
    mod = importlib.import_module("gen_desk_tools.radon_report.__main__")
    assert mod.__name__ == "gen_desk_tools.radon_report.__main__"


@pytest.mark.regression
def test_run_returns_one_when_config_or_generation_fails(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify run() returns exit code 1 on missing root or scanner runtime exceptions."""
    bad_args = build_parser().parse_args(["--root", str(tmp_path / "missing_root")])
    assert run(bad_args) == 1
    assert "Failed to load GDT configuration" in capsys.readouterr().err

    valid_args = build_parser().parse_args(["--root", str(tmp_path)])
    with patch(
        "gen_desk_tools.radon_report.cli.generate_radon_report",
        side_effect=RuntimeError("boom"),
    ):
        assert run(valid_args) == 1
    assert "Failed to generate Radon report: boom" in capsys.readouterr().err
