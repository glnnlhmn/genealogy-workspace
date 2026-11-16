"""Path: tests/test_system/test_gen_readme.py

Atomized unit, regression, and smoke test suite for gen_readme.py.

Operational Role:
    Verifies TOML configuration loading, AST metadata extraction, interactive
    overwrite confirmation prompts, batch overwrite, force flag bypassing,
    CLI argument evaluation, and 100.00% statement and branch coverage.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from system.gen_readme.gen_readme import (
    extract_module_metadata,
    generate_package_readme,
    load_configuration,
    main,
    prompt_overwrite,
    resolve_workspace_root,
    run,
)

__version__ = "1.0.0+build.8"


# ==============================================================================
# GROUP 1: Configuration Loading & Parsing
# ==============================================================================


@pytest.mark.unit
def test_resolve_workspace_root_variants(tmp_path: Path) -> None:
    """Verify workspace root resolution via explicit path, parent anchors, and cwd fallback."""
    # 1. Explicit valid directory
    assert resolve_workspace_root(str(tmp_path)) == tmp_path.resolve()

    # 2. Explicit path that is not a directory (covers branch 30->33)
    non_dir = tmp_path / "not_a_dir.txt"
    non_dir.write_text("text", encoding="utf-8")
    mock_root = tmp_path / "mock_root"
    (mock_root / "src").mkdir(parents=True)
    (mock_root / "archive").mkdir(parents=True)
    fake_script = mock_root / "src" / "system" / "gen_readme" / "gen_readme.py"
    fake_script.parent.mkdir(parents=True)

    with patch("system.gen_readme.gen_readme.__file__", str(fake_script)):
        assert resolve_workspace_root(str(non_dir)) == mock_root.resolve()

    # 3. Parent traversal finding src and archive
    with patch("system.gen_readme.gen_readme.__file__", str(fake_script)):
        assert resolve_workspace_root(".") == mock_root.resolve()

    # 4. Parent traversal finding pyproject.toml
    proj_root = tmp_path / "proj_root"
    proj_root.mkdir(parents=True)
    (proj_root / "pyproject.toml").write_text("", encoding="utf-8")
    script_proj = proj_root / "tools" / "gen_readme.py"
    script_proj.parent.mkdir(parents=True)

    with patch("system.gen_readme.gen_readme.__file__", str(script_proj)):
        assert resolve_workspace_root(".") == proj_root.resolve()

    # 5. Fallback to cwd
    with patch("system.gen_readme.gen_readme.__file__", "/isolated/nowhere/script.py"):
        assert resolve_workspace_root(".") == Path.cwd().resolve()


@pytest.mark.unit
def test_load_configuration_valid_toml(tmp_path: Path) -> None:
    """Verify loading valid TOML configuration yields root path and package records."""
    config_file = tmp_path / "test_config.toml"
    config_content = """
    default_root = "."

    [[packages]]
    path = "src/pkg_a"
    title = "Package A"
    role = "Role description"
    test_path = "tests/test_a"
    quality_gate = "100.0%"
    """
    config_file.write_text(config_content, encoding="utf-8")

    root, packages = load_configuration(config_file)
    assert isinstance(root, Path)
    assert len(packages) == 1
    assert packages[0]["path"] == "src/pkg_a"


@pytest.mark.regression
def test_load_configuration_missing_file_raises_error(tmp_path: Path) -> None:
    """Verify attempting to load a non-existent configuration raises FileNotFoundError."""
    missing = tmp_path / "non_existent.toml"
    with pytest.raises(FileNotFoundError, match="Configuration file not found"):
        load_configuration(missing)


@pytest.mark.unit
def test_load_configuration_default_fallback(tmp_path: Path) -> None:
    """Verify fallback when packages list is omitted in TOML."""
    config_file = tmp_path / "empty_root.toml"
    config_file.write_text("packages = []\n", encoding="utf-8")

    root, packages = load_configuration(config_file)
    assert isinstance(root, Path)
    assert packages == []


# ==============================================================================
# GROUP 2: AST Module Inspection & Metadata Extraction Branches
# ==============================================================================


@pytest.mark.unit
def test_extract_module_metadata_complete(tmp_path: Path) -> None:
    """Verify extracting description, version, and __all__ exports via AST."""
    mod = tmp_path / "sample_module.py"
    mod.write_text(
        '"""Path: src/sample_module.py\n\nCanonical module summary line.\n\nExtra body."""\n'
        '__version__ = "1.2.3"\n'
        '__all__ = ["SymbolA", "SymbolB"]\n',
        encoding="utf-8",
    )

    meta = extract_module_metadata(mod)
    assert meta["description"] == "Canonical module summary line."
    assert meta["version"] == "1.2.3"
    assert meta["all_exports"] == "`SymbolA`, `SymbolB`"


@pytest.mark.unit
def test_extract_module_metadata_annotated_assignment(tmp_path: Path) -> None:
    """Verify extracting __version__ and __all__ via AnnAssign."""
    mod = tmp_path / "annotated.py"
    mod.write_text(
        '"""Path: src/annotated.py\n\nAnnotated module."""\n'
        '__version__: str = "2.0.0"\n'
        '__all__: list[str] = ["AnnotatedExport"]\n',
        encoding="utf-8",
    )

    meta = extract_module_metadata(mod)
    assert meta["description"] == "Annotated module."
    assert meta["version"] == "2.0.0"
    assert meta["all_exports"] == "`AnnotatedExport`"


@pytest.mark.regression
def test_extract_module_metadata_syntax_error(tmp_path: Path) -> None:
    """Verify handling files with syntax errors without unhandled exceptions."""
    broken = tmp_path / "broken.py"
    broken.write_text("def unclosed_block(", encoding="utf-8")

    meta = extract_module_metadata(broken)
    assert "Extraction error" in meta["description"]
    assert meta["version"] == "Unversioned"


@pytest.mark.unit
def test_extract_module_metadata_empty_file(tmp_path: Path) -> None:
    """Verify handling empty files returns default metadata."""
    empty = tmp_path / "empty.py"
    empty.write_text("", encoding="utf-8")

    meta = extract_module_metadata(empty)
    assert meta["description"] == "No description available."
    assert meta["version"] == "Unversioned"
    assert meta["all_exports"] == ""


@pytest.mark.regression
def test_extract_module_metadata_header_only_docstring(tmp_path: Path) -> None:
    """Verify docstring containing only Path: header leaves description as default."""
    mod = tmp_path / "header_only.py"
    mod.write_text('"""Path: src/header_only.py\n<!--Name: test-->\n"""\n', encoding="utf-8")

    meta = extract_module_metadata(mod)
    assert meta["description"] == "No description available."


@pytest.mark.regression
def test_extract_module_metadata_non_name_and_other_assign_targets(
    tmp_path: Path,
) -> None:
    """Verify unpackings, attribute assignments, and non-target variables."""
    mod = tmp_path / "assign_variants.py"
    mod.write_text(
        '"""Path: src/assign_variants.py\n\nAssign variants module."""\n'
        "a, b = 1, 2\n"
        "other_var = 'test'\n",
        encoding="utf-8",
    )

    meta = extract_module_metadata(mod)
    assert meta["description"] == "Assign variants module."
    assert meta["version"] == "Unversioned"


# ==============================================================================
# GROUP 3: README Content Assembly & Subpackages
# ==============================================================================


@pytest.mark.unit
def test_generate_package_readme_content_with_subpackages(tmp_path: Path) -> None:
    """Verify generating Markdown structure containing modules and linked subpackages."""
    pkg_dir = tmp_path / "src" / "sample"
    pkg_dir.mkdir(parents=True)

    # Submodule
    mod = pkg_dir / "worker.py"
    mod.write_text('"""Worker description."""\n__version__ = "1.0.0"\n', encoding="utf-8")

    # Subpackage 1: with __init__.py and child README
    subpkg1 = pkg_dir / "sub"
    subpkg1.mkdir()
    sub_init1 = subpkg1 / "__init__.py"
    sub_init1.write_text('"""Subpackage summary."""\n', encoding="utf-8")
    (subpkg1 / "README.md").write_text("# Sub Readme", encoding="utf-8")

    # Subpackage 2: directory with NO __init__.py (covers branch 137->143)
    subpkg2 = pkg_dir / "no_init_sub"
    subpkg2.mkdir()

    # Subpackage 3: directory with empty __init__.py lacking docstring (covers branch 139->143)
    subpkg3 = pkg_dir / "empty_init_sub"
    subpkg3.mkdir()
    (subpkg3 / "__init__.py").write_text("# no docstring\n", encoding="utf-8")

    # Package __init__
    init_file = pkg_dir / "__init__.py"
    init_file.write_text('__all__ = ["worker"]\n', encoding="utf-8")

    pkg_info = {
        "path": "src/sample",
        "title": "Sample Package",
        "role": "Role description",
        "test_path": "tests/test_sample",
        "quality_gate": "100.0%",
    }

    readme = generate_package_readme(pkg_info, tmp_path)
    assert "# Sample Package" in readme
    assert "## Subpackages" in readme
    assert "- **[sub/](sub/README.md)**: Subpackage summary." in readme
    assert "- **`no_init_sub/`**: Subpackage domain entities and enumerations." in readme
    assert "- **`empty_init_sub/`**: Subpackage domain entities and enumerations." in readme
    assert "| `worker.py` | `1.0.0` | Worker description. |" in readme
    assert "Exports: `worker`." in readme


@pytest.mark.unit
def test_generate_package_readme_zero_modules(tmp_path: Path) -> None:
    """Verify package with zero submodules exercises empty inventory branches."""
    pkg_dir = tmp_path / "src" / "zero_mod"
    pkg_dir.mkdir(parents=True)

    pkg_info = {
        "path": "src/zero_mod",
        "title": "Zero Module Package",
        "role": "Role",
        "test_path": "tests/zero_mod",
        "quality_gate": "100.0%",
    }

    readme = generate_package_readme(pkg_info, tmp_path)
    assert "# Zero Module Package" in readme
    assert "## Module Inventory & Descriptions" in readme


@pytest.mark.unit
def test_generate_package_readme_no_init_exports(tmp_path: Path) -> None:
    """Verify public exports section when __init__.py exists without __all__."""
    pkg_dir = tmp_path / "src" / "sample_no_all"
    pkg_dir.mkdir(parents=True)
    init_file = pkg_dir / "__init__.py"
    init_file.write_text("# empty\n", encoding="utf-8")

    pkg_info = {
        "path": "src/sample_no_all",
        "title": "No All Package",
        "role": "Role",
        "test_path": "tests/test_sample",
        "quality_gate": "100.0%",
    }

    readme = generate_package_readme(pkg_info, tmp_path)
    assert "Modules export public interfaces explicitly declared in `__all__`." in readme


@pytest.mark.unit
def test_generate_package_readme_without_init_file(tmp_path: Path) -> None:
    """Verify public exports section when __init__.py does not exist."""
    pkg_dir = tmp_path / "src" / "sample_no_init"
    pkg_dir.mkdir(parents=True)

    pkg_info = {
        "path": "src/sample_no_init",
        "title": "No Init Package",
        "role": "Role",
        "test_path": "tests/test_sample",
        "quality_gate": "100.0%",
    }

    readme = generate_package_readme(pkg_info, tmp_path)
    assert "Direct submodule imports supported." in readme


# ==============================================================================
# GROUP 4: Interactive Overwrite Confirmation Prompt
# ==============================================================================


@pytest.mark.unit
def test_prompt_overwrite_decisions(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify prompt_overwrite parses y, n, a, and q responses correctly."""
    target = tmp_path / "README.md"

    monkeypatch.setattr("builtins.input", lambda _: "y")
    assert prompt_overwrite(target) == "y"

    monkeypatch.setattr("builtins.input", lambda _: "yes")
    assert prompt_overwrite(target) == "y"

    monkeypatch.setattr("builtins.input", lambda _: "n")
    assert prompt_overwrite(target) == "n"

    monkeypatch.setattr("builtins.input", lambda _: "a")
    assert prompt_overwrite(target) == "a"

    monkeypatch.setattr("builtins.input", lambda _: "quit")
    assert prompt_overwrite(target) == "q"


@pytest.mark.regression
def test_prompt_overwrite_invalid_input_retry(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify invalid input prompts until a valid response is given."""
    target = tmp_path / "README.md"
    inputs = iter(["invalid", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))
    assert prompt_overwrite(target) == "n"


@pytest.mark.regression
def test_prompt_overwrite_eof_returns_quit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Verify encountering EOFError gracefully returns 'q'."""
    target = tmp_path / "README.md"

    def raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert prompt_overwrite(target) == "q"


# ==============================================================================
# GROUP 5: Execution Orchestration (run) & Flags
# ==============================================================================


@pytest.mark.smoke
def test_run_end_to_end_fresh_write(tmp_path: Path) -> None:
    """Verify run generates README when none exists."""
    cfg = tmp_path / "conf.toml"
    pkg = tmp_path / "src" / "my_pkg"
    pkg.mkdir(parents=True)
    (pkg / "mod.py").write_text('"""Doc."""\n__version__ = "1.0"\n', encoding="utf-8")

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/my_pkg"\n'
        'title = "My Package"\n'
        'role = "Role"\n'
        'test_path = "tests/test_my_pkg"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert (pkg / "README.md").exists()


@pytest.mark.regression
def test_run_target_subsystem_filter(tmp_path: Path) -> None:
    """Verify target argument limits README generation to specific package."""
    cfg = tmp_path / "conf.toml"
    p1 = tmp_path / "src" / "pkg1"
    p2 = tmp_path / "src" / "pkg2"
    p1.mkdir(parents=True)
    p2.mkdir(parents=True)

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/pkg1"\n'
        'title = "P1"\n'
        'role = "R1"\n'
        'test_path = "tests/test_p1"\n'
        'quality_gate = "100.0%"\n'
        "[[packages]]\n"
        'path = "src/pkg2"\n'
        'title = "P2"\n'
        'role = "R2"\n'
        'test_path = "tests/test_p2"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    exit_code = run(target="src/pkg1", config_path=cfg)
    assert exit_code == 0
    assert (p1 / "README.md").exists()
    assert not (p2 / "README.md").exists()


@pytest.mark.regression
def test_run_target_unregistered_directory_fallback(tmp_path: Path) -> None:
    """Verify target directory not in config synthesizes fallback metadata."""
    cfg = tmp_path / "conf.toml"
    cfg.write_text(f'default_root = "{tmp_path.as_posix()}"\npackages = []\n', encoding="utf-8")

    custom_pkg = tmp_path / "src" / "unregistered"
    custom_pkg.mkdir(parents=True)

    exit_code = run(target="src/unregistered", config_path=cfg)
    assert exit_code == 0
    assert (custom_pkg / "README.md").exists()


@pytest.mark.regression
def test_run_target_unregistered_absolute_path(tmp_path: Path) -> None:
    """Verify unregistered target supplied as an absolute path covers branch 222->225."""
    cfg = tmp_path / "conf.toml"
    cfg.write_text(f'default_root = "{tmp_path.as_posix()}"\npackages = []\n', encoding="utf-8")

    abs_pkg = tmp_path / "src" / "abs_unregistered"
    abs_pkg.mkdir(parents=True)

    exit_code = run(target=str(abs_pkg.resolve()), config_path=cfg)
    assert exit_code == 0
    assert (abs_pkg / "README.md").exists()


@pytest.mark.regression
def test_run_target_nonexistent_returns_error(tmp_path: Path) -> None:
    """Verify target path not existing in config or filesystem returns 1."""
    cfg = tmp_path / "conf.toml"
    cfg.write_text(f'default_root = "{tmp_path.as_posix()}"\npackages = []\n', encoding="utf-8")

    exit_code = run(target="src/does_not_exist", config_path=cfg)
    assert exit_code == 1


@pytest.mark.regression
def test_run_config_load_failure(tmp_path: Path) -> None:
    """Verify invalid config path returns 1."""
    exit_code = run(config_path=tmp_path / "missing.toml")
    assert exit_code == 1


@pytest.mark.unit
def test_run_missing_target_dir_quiet_and_verbose(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify missing package directory when verbose is False (branch 248->250) and True."""
    cfg = tmp_path / "conf.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/missing_folder"\n'
        'title = "Missing"\n'
        'role = "Role"\n'
        'test_path = "tests/test_missing"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    # 1. Quiet mode: verbose=False skips print (branch 248->250)
    exit_quiet = run(verbose=False, config_path=cfg)
    assert exit_quiet == 0
    assert "[SKIP] Directory not found:" not in capsys.readouterr().out

    # 2. Verbose mode: verbose=True prints notice
    exit_verbose = run(verbose=True, config_path=cfg)
    assert exit_verbose == 0
    assert "[SKIP] Directory not found:" in capsys.readouterr().out


@pytest.mark.unit
def test_run_existing_readme_user_declines_quiet_and_verbose(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify declining overwrite ('n') with verbose=False (branch 256->258) and True."""
    cfg = tmp_path / "conf.toml"
    pkg = tmp_path / "src" / "declined"
    pkg.mkdir(parents=True)
    existing_readme = pkg / "README.md"
    existing_readme.write_text("# Old", encoding="utf-8")

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/declined"\n'
        'title = "Declined"\n'
        'role = "Role"\n'
        'test_path = "tests/test_declined"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    # 1. Quiet mode: verbose=False skips skip notice (covers branch 256->258)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    exit_code_quiet = run(verbose=False, config_path=cfg)
    assert exit_code_quiet == 0
    assert existing_readme.read_text(encoding="utf-8") == "# Old"
    assert "[SKIP] User declined overwrite:" not in capsys.readouterr().out

    # 2. Verbose mode: verbose=True prints skip notice
    exit_code_verbose = run(verbose=True, config_path=cfg)
    assert exit_code_verbose == 0
    assert "[SKIP] User declined overwrite:" in capsys.readouterr().out


@pytest.mark.unit
def test_run_existing_readme_user_confirms_single_overwrite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify confirming single overwrite ('y') executes line 257 without entering 'a' or 'q'."""
    cfg = tmp_path / "conf.toml"
    p1 = tmp_path / "src" / "p1"
    p2 = tmp_path / "src" / "p2"
    p1.mkdir(parents=True)
    p2.mkdir(parents=True)
    (p1 / "README.md").write_text("# P1 Old", encoding="utf-8")
    (p2 / "README.md").write_text("# P2 Old", encoding="utf-8")

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/p1"\n'
        'title = "P1"\n'
        'role = "Role"\n'
        'test_path = "tests/test_p1"\n'
        'quality_gate = "100.0%"\n'
        "[[packages]]\n"
        'path = "src/p2"\n'
        'title = "P2"\n'
        'role = "Role"\n'
        'test_path = "tests/test_p2"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    # First package receives 'y' (overwriting P1 and hitting line 257), second package receives 'n'
    inputs = iter(["y", "n"])
    monkeypatch.setattr("builtins.input", lambda _: next(inputs))

    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert "# P1 Old" not in (p1 / "README.md").read_text(encoding="utf-8")
    assert (p2 / "README.md").read_text(encoding="utf-8") == "# P2 Old"


@pytest.mark.unit
def test_run_existing_readme_batch_overwrite_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify choosing 'all' ('a') executes line 257-258 and sets overwrite_all to True."""
    cfg = tmp_path / "conf.toml"
    p1 = tmp_path / "src" / "p1"
    p2 = tmp_path / "src" / "p2"
    p1.mkdir(parents=True)
    p2.mkdir(parents=True)
    (p1 / "README.md").write_text("# P1 Old", encoding="utf-8")
    (p2 / "README.md").write_text("# P2 Old", encoding="utf-8")

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/p1"\n'
        'title = "P1"\n'
        'role = "Role"\n'
        'test_path = "tests/test_p1"\n'
        'quality_gate = "100.0%"\n'
        "[[packages]]\n"
        'path = "src/p2"\n'
        'title = "P2"\n'
        'role = "Role"\n'
        'test_path = "tests/test_p2"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    # First package receives 'a'; sets overwrite_all, so second package requires no input
    monkeypatch.setattr("builtins.input", lambda _: "a")
    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert "# P1 Old" not in (p1 / "README.md").read_text(encoding="utf-8")
    assert "# P2 Old" not in (p2 / "README.md").read_text(encoding="utf-8")


@pytest.mark.unit
def test_run_existing_readme_user_aborts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify choosing 'quit' ('q') executes line 257->259->261 and cancels execution."""
    cfg = tmp_path / "conf.toml"
    pkg = tmp_path / "src" / "aborted"
    pkg.mkdir(parents=True)
    (pkg / "README.md").write_text("# Original", encoding="utf-8")

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/aborted"\n'
        'title = "Aborted"\n'
        'role = "Role"\n'
        'test_path = "tests/test_aborted"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr("builtins.input", lambda _: "q")
    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert "[ABORT] Documentation generation cancelled by user." in capsys.readouterr().out


# ==============================================================================
# GROUP 6: CLI Argument Parsing & Entrypoint
# ==============================================================================


@pytest.mark.integration
def test_main_cli_execution_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main entrypoint handles CLI flags and exits cleanly."""
    cfg = tmp_path / "conf.toml"
    pkg = tmp_path / "src" / "cli_pkg"
    pkg.mkdir(parents=True)

    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n'
        "[[packages]]\n"
        'path = "src/cli_pkg"\n'
        'title = "CLI Package"\n'
        'role = "Role"\n'
        'test_path = "tests/test_cli_pkg"\n'
        'quality_gate = "100.0%"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "sys.argv",
        [
            "gen_readme",
            "src/cli_pkg",
            "--force",
            "--verbose",
            "-c",
            str(cfg),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert (pkg / "README.md").exists()


@pytest.mark.unit
def test_gen_readme_module_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify execution as __main__ module."""
    monkeypatch.setattr("sys.argv", ["gen_readme", "-h"])
    monkeypatch.delitem(sys.modules, "system.gen_readme.gen_readme", raising=False)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("system.gen_readme.gen_readme", run_name="__main__")
    assert exc.value.code == 0
