"""Path: tests/test_gen_desk_tools/test_script_importer/test_cli.py

Unit and integration tests for gen_desk_tools.script_importer.cli and __main__.
"""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.script_importer import cli

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: CLI argument registration and parsing via build_parser().
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_build_parser_parses_force_clean_and_common_flags() -> None:
    """Verify build_parser registers -f, -c, -v, --debug, --config, and --root."""
    parser = cli.build_parser()
    args = parser.parse_args(
        ["-f", "-c", "-v", "--debug", "--config", "custom.toml", "--root", "/repo"]
    )

    assert args.force is True
    assert args.clean is True
    assert args.verbose is True
    assert args.debug is True
    assert args.config == Path("custom.toml")
    assert args.root == Path("/repo")


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Exit-code propagation in main() and python -m __main__ execution shim.
# ==========================================================================


@pytest.mark.unit
def test_main_dispatches_to_run_intake_and_exits(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() forwards parsed arguments to run_intake() and calls sys.exit."""
    captured: dict[str, Any] = {}

    def _fake_run_intake(**kwargs: Any) -> int:
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(cli, "run_intake", _fake_run_intake)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["-f", "-c"])

    assert exc_info.value.code == 0
    assert captured["force"] is True
    assert captured["clean"] is True


@pytest.mark.unit
def test_package_main_module_invokes_cli_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify python -m gen_desk_tools.script_importer delegates to cli.main()."""
    called: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: called.append(True))

    importlib.import_module("gen_desk_tools.script_importer.__main__")
    assert called == []

    monkeypatch.delitem(sys.modules, "gen_desk_tools.script_importer.__main__", raising=False)
    runpy.run_module("gen_desk_tools.script_importer", run_name="__main__")
    assert called == [True]
