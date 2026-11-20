"""Path: tests/test_gen_desk_tools/test_readme_gen/test_cli.py

Unit and integration tests for gen_desk_tools.readme_gen.cli and __main__.
"""

from __future__ import annotations

import importlib
import runpy
import sys
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.readme_gen import cli

__version__ = "1.0.0+build.4"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: CLI argument parsing and dispatch through main() and __main__.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_build_parser_parses_positional_and_common_flags() -> None:
    """Verify build_parser registers positional target, -f, --packages-config, and core flags."""
    parser = cli.build_parser()
    args = parser.parse_args(
        ["gda", "-f", "-v", "--debug", "--packages-config", "manifest.toml", "--root", "/repo"]
    )

    assert args.target_pos == "gda"
    assert args.target_opt is None
    assert args.force is True
    assert args.verbose is True
    assert args.debug is True
    assert args.packages_config == Path("manifest.toml")
    assert args.root == Path("/repo")


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Named -t/--target precedence, exit-code propagation, and __main__ shim.
# ==========================================================================


@pytest.mark.unit
def test_main_dispatches_to_run_and_exits_with_status_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify main() prefers -t/--target over positional target and calls sys.exit."""
    captured: dict[str, Any] = {}

    def _fake_run(**kwargs: Any) -> int:
        captured.update(kwargs)
        return 0

    monkeypatch.setattr(cli, "run", _fake_run)

    with pytest.raises(SystemExit) as exc_info:
        cli.main(["positional_pkg", "-t", "cli", "-f"])

    assert exc_info.value.code == 0
    assert captured["target"] == "cli"
    assert captured["force"] is True


@pytest.mark.unit
def test_package_main_module_invokes_cli_main(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify python -m gen_desk_tools.readme_gen delegates to cli.main()."""
    called: list[bool] = []
    monkeypatch.setattr(cli, "main", lambda: called.append(True))

    # Exercise False branch (regular import), then clear sys.modules to avoid runpy RuntimeWarning
    importlib.import_module("gen_desk_tools.readme_gen.__main__")
    assert called == []

    monkeypatch.delitem(sys.modules, "gen_desk_tools.readme_gen.__main__", raising=False)
    runpy.run_module("gen_desk_tools.readme_gen", run_name="__main__")
    assert called == [True]
