"""Path: tests/test_gen_desk_tools/test_structure/test_cli.py

Unit, regression, and integration tests for gen_desk_tools.structure.cli and __main__.
"""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.structure import cli

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Argument Parsing
# Note: Default gda mode, subsystem flags, -t/--tests, and -l/--level.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_build_parser_and_resolve_mode_handle_defaults_and_flags() -> None:
    """Verify default mode is gda, default level is 7, and flags resolve accurately."""
    parser = cli.build_parser()

    default_args = parser.parse_args([])
    assert cli.resolve_mode(default_args) == "gda"
    assert default_args.level == 7
    assert default_args.tests is False

    custom_args = parser.parse_args(["--ancestry-desk", "-t", "-l", "4"])
    assert cli.resolve_mode(custom_args) == "ancestry_desk"
    assert custom_args.tests is True
    assert custom_args.level == 4


@pytest.mark.integration
def test_run_generates_report_and_returns_zero(
    gdt_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify run() writes the report into configured reports_dir and returns 0."""
    (gdt_workspace / "src" / "gen_desk_tools" / "demo.py").write_text("x = 1\n", encoding="utf-8")
    parser = cli.build_parser()

    code = cli.run(parser.parse_args(["--root", str(gdt_workspace), "--gd-tools", "-t"]))

    out = capsys.readouterr().out
    assert code == 0
    assert "Report file created:" in out
    assert (gdt_workspace / "reports" / "GenDeskStructure_gd_tools_tests.txt").is_file()


# ==========================================================================
# GROUP 2: Error Branches, main(), & __main__ Shim
# Note: Config load failure, scanner failure, sys.exit, and runpy execution.
# ==========================================================================


@pytest.mark.regression
def test_run_returns_one_on_config_or_scanner_errors(gdt_workspace: Path) -> None:
    """Verify run() returns 1 when config loading or report generation fails."""
    parser = cli.build_parser()

    bad_cfg = parser.parse_args(
        ["--root", str(gdt_workspace), "--config", str(gdt_workspace / "missing.toml")]
    )
    assert cli.run(bad_cfg) == 1

    with patch(
        "gen_desk_tools.structure.cli.generate_structure_report",
        side_effect=RuntimeError("git failed"),
    ):
        assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "-g"])) == 1


@pytest.mark.unit
def test_main_and_package_main_module_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify cli.main() exits with run()'s code and __main__ delegates to cli.main()."""
    with patch.object(cli, "run", return_value=0):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["--gd"])
        assert exc_info.value.code == 0

    called: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: called.append(True))

    importlib.import_module("gen_desk_tools.structure.__main__")
    assert called == []

    monkeypatch.delitem(sys.modules, "gen_desk_tools.structure.__main__", raising=False)
    runpy.run_module("gen_desk_tools.structure", run_name="__main__")
    assert called == [True]
