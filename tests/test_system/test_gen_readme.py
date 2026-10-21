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

import pytest

from system.gen_readme import (
    extract_module_metadata,
    generate_package_readme,
    load_configuration,
    main,
    prompt_overwrite,
    run,
)

__version__ = "1.0.0+build.3"


# ==============================================================================
# GROUP 1: Configuration Loading & Parsing
# ==============================================================================


@pytest.mark.unit
def test_load_configuration_valid_toml(tmp_path: Path) -> None:
    """Verify loading valid TOML configuration yields root path and package records."""
    config_file = tmp_path / "test_config.toml"
    config_content = """
    default_root = "/custom/root"

    [[packages]]
    path = "src/pkg_a"
    title = "Package A"
    role = "Role description"
    test_path = "tests/test_a"
    quality_gate = "100.0%"
    """
    config_file.write_text(config_content, encoding="utf-8")

    root, packages = load_configuration(config_file)
    assert root == Path("/custom/root")
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
    """Verify fallback to current directory when default_root is omitted in TOML."""
    config_file = tmp_path / "empty_root.toml"
    config_file.write_text("packages = []\n", encoding="utf-8")

    root, packages = load_configuration(config_file)
    assert root == Path(".")
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
    mod.write_text('"""Path: src/header_only.py\n"""\n', encoding="utf-8")

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
    """Verify generating Markdown structure containing modules and subpackages."""
    pkg_dir = tmp_path / "src" / "sample"
    pkg_dir.mkdir(parents=True)

    # Submodule
    mod = pkg_dir / "worker.py"
    mod.write_text(
        '"""Worker description."""\n__version__ = "1.0.0"\n', encoding="utf-8"
    )

    # Subpackage
    subpkg = pkg_dir / "sub"
    subpkg.mkdir()
    sub_init = subpkg / "__init__.py"
    sub_init.write_text('"""Subpackage summary."""\n', encoding="utf-8")

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
    assert "- **`sub/`**: Subpackage summary." in readme
    assert "| `worker.py` | `1.0.0` | Worker description. |" in readme
    assert "Exports: `worker`." in readme


@pytest.mark.unit
def test_generate_package_readme_zero_modules(tmp_path: Path) -> None:
    """Verify package with zero submodules exercises branches 119->123 and 121->123."""
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
    assert (
        "Modules export public interfaces explicitly declared in `__all__`." in readme
    )


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
def test_prompt_overwrite_decisions(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
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
def test_prompt_overwrite_eof_returns_quit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify encountering EOFError gracefully returns 'q'."""
    target = tmp_path / "README.md"

    def raise_eof(_: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", raise_eof)
    assert prompt_overwrite(target) == "q"


# ==============================================================================
# GROUP 5: Execution Orchestration (run) & Force Flag
# ==============================================================================


@pytest.mark.smoke
def test_run_end_to_end_fresh_write(tmp_path: Path) -> None:
    """Verify run generates README when none exists without prompting."""
    pkg_dir = tmp_path / "src" / "core"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "tool.py").write_text('"""Core tool."""\n', encoding="utf-8")

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/core"\n'
        'title = "Core"\n'
        'role = "Core Role"\n'
        'test_path = "tests/core"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    exit_code = run(config_path=cfg)
    assert exit_code == 0
    readme = pkg_dir / "README.md"
    assert readme.exists()
    assert "# Core" in readme.read_text(encoding="utf-8")


@pytest.mark.unit
def test_run_empty_packages_list_skips_loop(tmp_path: Path) -> None:
    """Verify run with empty package configuration exercises loop exit branch 206->209."""
    cfg = tmp_path / "empty_packages.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\npackages = []\n',
        encoding="utf-8",
    )
    exit_code = run(config_path=cfg)
    assert exit_code == 0


@pytest.mark.regression
def test_run_overwrite_prompt_skip(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify declining overwrite via interactive prompt preserves original content."""
    pkg_dir = tmp_path / "src" / "core"
    pkg_dir.mkdir(parents=True)
    readme = pkg_dir / "README.md"
    readme.write_text("ORIGINAL CONTENT", encoding="utf-8")

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/core"\n'
        'title = "Core"\n'
        'role = "Core Role"\n'
        'test_path = "tests/core"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr("builtins.input", lambda _: "n")
    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert readme.read_text(encoding="utf-8") == "ORIGINAL CONTENT"


@pytest.mark.unit
def test_run_force_flag_bypasses_prompt(tmp_path: Path) -> None:
    """Verify --force overwrites existing README without prompting."""
    pkg_dir = tmp_path / "src" / "core"
    pkg_dir.mkdir(parents=True)
    readme = pkg_dir / "README.md"
    readme.write_text("OLD", encoding="utf-8")

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/core"\n'
        'title = "Core"\n'
        'role = "Core Role"\n'
        'test_path = "tests/core"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    exit_code = run(force=True, config_path=cfg)
    assert exit_code == 0
    assert "# Core" in readme.read_text(encoding="utf-8")


@pytest.mark.unit
def test_run_overwrite_all_option(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify selecting 'all' overwrites the first and subsequent files without prompting."""
    p1 = tmp_path / "src" / "p1"
    p2 = tmp_path / "src" / "p2"
    p1.mkdir(parents=True)
    p2.mkdir(parents=True)
    r1 = p1 / "README.md"
    r2 = p2 / "README.md"
    r1.write_text("OLD1", encoding="utf-8")
    r2.write_text("OLD2", encoding="utf-8")

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/p1"\n'
        'title = "P1"\n'
        'role = "R1"\n'
        'test_path = "tests/p1"\n'
        'quality_gate = "100%"\n\n'
        "[[packages]]\n"
        'path = "src/p2"\n'
        'title = "P2"\n'
        'role = "R2"\n'
        'test_path = "tests/p2"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    prompts = iter(["all"])
    monkeypatch.setattr("builtins.input", lambda _: next(prompts))
    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert "# P1" in r1.read_text(encoding="utf-8")
    assert "# P2" in r2.read_text(encoding="utf-8")


@pytest.mark.unit
def test_run_quit_aborts_immediately(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify selecting 'quit' terminates execution early."""
    pkg_dir = tmp_path / "src" / "core"
    pkg_dir.mkdir(parents=True)
    readme = pkg_dir / "README.md"
    readme.write_text("OLD", encoding="utf-8")

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/core"\n'
        'title = "Core"\n'
        'role = "Core Role"\n'
        'test_path = "tests/core"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr("builtins.input", lambda _: "q")
    exit_code = run(config_path=cfg)
    assert exit_code == 0
    assert readme.read_text(encoding="utf-8") == "OLD"


@pytest.mark.regression
def test_run_missing_config_returns_error(tmp_path: Path) -> None:
    """Verify run returns error code 1 when configuration cannot be loaded."""
    exit_code = run(config_path=tmp_path / "nonexistent.toml")
    assert exit_code == 1


@pytest.mark.regression
def test_run_target_not_found_returns_error(tmp_path: Path) -> None:
    """Verify run returns error code 1 when targeted package is neither in config nor on disk."""
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\npackages = []\n',
        encoding="utf-8",
    )

    exit_code = run(target="src/invalid_package", config_path=cfg)
    assert exit_code == 1


@pytest.mark.unit
def test_run_unconfigured_directory_target(tmp_path: Path) -> None:
    """Verify targeting an existing directory not in TOML config synthesizes entry dynamically."""
    custom_dir = tmp_path / "src" / "custom"
    custom_dir.mkdir(parents=True)
    (custom_dir / "app.py").write_text('"""App module."""\n', encoding="utf-8")

    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\npackages = []\n',
        encoding="utf-8",
    )

    exit_code = run(target="src/custom", config_path=cfg)
    assert exit_code == 0
    readme = custom_dir / "README.md"
    assert readme.exists()
    assert "# Package Documentation (src/custom)" in readme.read_text(encoding="utf-8")


@pytest.mark.unit
def test_run_skips_missing_directory_in_config(tmp_path: Path) -> None:
    """Verify run safely skips entries defined in TOML whose directories do not exist on disk."""
    cfg = tmp_path / "config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/ghost"\n'
        'title = "Ghost"\n'
        'role = "Missing"\n'
        'test_path = "tests/ghost"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    exit_code = run(config_path=cfg)
    assert exit_code == 0


# ==============================================================================
# GROUP 6: CLI Argument Parsing & Entrypoint (main)
# ==============================================================================


@pytest.mark.unit
def test_main_cli_execution_with_positional_arg(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify CLI entrypoint dispatches positional target cleanly."""
    pkg_dir = tmp_path / "src" / "cli_pkg"
    pkg_dir.mkdir(parents=True)

    cfg = tmp_path / "cli_config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/cli_pkg"\n'
        'title = "CLI Package"\n'
        'role = "Role"\n'
        'test_path = "tests/cli"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    test_args = ["gen_readme.py", "src/cli_pkg", "--force", "-c", str(cfg)]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert (pkg_dir / "README.md").exists()


@pytest.mark.unit
def test_main_cli_execution_with_target_flag(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify CLI entrypoint dispatches -t / --target named parameter (branch 244->248)."""
    pkg_dir = tmp_path / "src" / "cli_flag_pkg"
    pkg_dir.mkdir(parents=True)

    cfg = tmp_path / "cli_flag_config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\n'
        "[[packages]]\n"
        'path = "src/cli_flag_pkg"\n'
        'title = "CLI Flag Package"\n'
        'role = "Role"\n'
        'test_path = "tests/cli_flag"\n'
        'quality_gate = "100%"\n',
        encoding="utf-8",
    )

    test_args = ["gen_readme.py", "-t", "src/cli_flag_pkg", "-f", "-c", str(cfg)]
    monkeypatch.setattr(sys, "argv", test_args)

    with pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 0
    assert (pkg_dir / "README.md").exists()


@pytest.mark.unit
def test_main_dunder_entrypoint_invoked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify if __name__ == '__main__' branch executes via runpy without warnings."""
    cfg = tmp_path / "dunder_config.toml"
    cfg.write_text(
        f'default_root = "{tmp_path.as_posix()}"\n\npackages = []\n',
        encoding="utf-8",
    )
    test_args = ["gen_readme.py", "-c", str(cfg)]
    monkeypatch.setattr(sys, "argv", test_args)

    # Evict system.gen_readme from sys.modules prior to runpy to eliminate RuntimeWarning
    sys.modules.pop("system.gen_readme", None)

    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("system.gen_readme", run_name="__main__")
    assert exc_info.value.code == 0
