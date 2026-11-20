"""Path: tests/test_gen_desk_tools/test_coverage_gaps/test_cli.py

Unit, regression, and integration tests for gen_desk_tools.coverage_gaps.cli and __main__.
"""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from gen_desk_tools.coverage_gaps import cli

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Parser construction and end-to-end CLI execution against gdt_workspace.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_build_parser_parses_file_path_gap_and_optional_flags() -> None:
    """Verify build_parser registers file_path, gap, -g/--gap-range, -o/--output-dir, and core flags."""
    parser = cli.build_parser()
    args = parser.parse_args(
        ["src/mod.py", "1-5", "-g", "2->4", "-o", "custom_reports", "--root", "/repo"]
    )

    assert args.file_path == "src/mod.py"
    assert args.gap == "1-5"
    assert args.flag_gap == "2->4"
    assert args.output_dir == "custom_reports"
    assert args.root == Path("/repo")


@pytest.mark.integration
def test_run_writes_report_and_returns_zero(
    gdt_workspace: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify run() extracts lines using -g override and default configured reports_dir."""
    src_file = gdt_workspace / "src" / "gen_desk_tools" / "demo.py"
    src_file.write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")
    parser = cli.build_parser()

    code = cli.run(
        parser.parse_args(
            ["--root", str(gdt_workspace), "src/gen_desk_tools/demo.py", "-g", "1->2"]
        )
    )

    out = capsys.readouterr().out
    assert code == 0
    assert "Number of lines output: 2" in out
    assert (gdt_workspace / "reports" / "Coverage Gap + demo.py + 1-2.txt").is_file()


# ==========================================================================
# GROUP 2: Error Branches, main(), & __main__ Shim
# Note: Invalid config path, missing source file, sys.exit propagation, and runpy.
# ==========================================================================


@pytest.mark.regression
def test_run_returns_one_on_config_error_or_missing_source(gdt_workspace: Path) -> None:
    """Verify run() returns 1 on invalid config path or missing target source file."""
    parser = cli.build_parser()

    assert (
        cli.run(
            parser.parse_args(
                [
                    "--root",
                    str(gdt_workspace),
                    "--config",
                    str(gdt_workspace / "missing.toml"),
                    "src/a.py",
                ]
            )
        )
        == 1
    )
    assert cli.run(parser.parse_args(["--root", str(gdt_workspace), "src/missing.py", "1-5"])) == 1


@pytest.mark.unit
def test_main_and_package_main_module_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify cli.main() exits with run()'s code and __main__ delegates to cli.main()."""
    with patch.object(cli, "run", return_value=0):
        with pytest.raises(SystemExit) as exc_info:
            cli.main(["src/a.py"])
        assert exc_info.value.code == 0

    called: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: called.append(True))

    importlib.import_module("gen_desk_tools.coverage_gaps.__main__")
    assert called == []

    monkeypatch.delitem(sys.modules, "gen_desk_tools.coverage_gaps.__main__", raising=False)
    runpy.run_module("gen_desk_tools.coverage_gaps", run_name="__main__")
    assert called == [True]
