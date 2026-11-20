"""Path: tests/test_gen_desk_tools/test_readme_gen/test_generator.py

Unit, regression, and integration tests for gen_desk_tools.readme_gen.generator.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from gen_desk_tools.readme_gen.generator import (
    compute_content_hash,
    generate_package_readme,
    is_unmodified_generated_readme,
    load_package_definitions,
    prompt_overwrite,
    resolve_target_packages,
    run,
)

__version__ = "1.0.0+build.2"


def _close_gdrm_logger() -> None:
    """Detach and close gdrm logger handlers to prevent Windows tmp_path locks."""
    logger = logging.getLogger("gdrm")
    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)


def _write_manifest(manifest_path: Path, packages_toml: str) -> None:
    """Write a UTF-8 TOML package manifest fixture."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(packages_toml, encoding="utf-8")


# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end run() generating a hashed README.md from a TOML manifest.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.integration
def test_run_generates_hashed_readme_from_manifest(gdt_workspace: Path) -> None:
    """Verify run() reads the manifest, renders Markdown with hash, and writes README.md."""
    pkg_dir = gdt_workspace / "src" / "gda" / "demo"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "mod.py").write_text(
        '"""Path: src/gda/demo/mod.py\n\nDemo module."""\n__version__ = "1.0.0+build.1"\n',
        encoding="utf-8",
    )
    manifest = gdt_workspace / "packages.toml"
    _write_manifest(
        manifest,
        'default_root = "."\n\n'
        "[[packages]]\n"
        'path = "src/gda/demo"\n'
        'title = "Demo Package"\n'
        'role = "Demo role."\n'
        'test_path = "tests/test_gda/test_demo"\n'
        'quality_gate = "100.0%"\n',
    )

    try:
        exit_code = run(root_dir=gdt_workspace, packages_config=manifest, verbose=True)
    finally:
        _close_gdrm_logger()

    readme = pkg_dir / "README.md"
    assert exit_code == 0
    assert readme.is_file()
    content = readme.read_text(encoding="utf-8")
    assert "# Demo Package" in content
    assert is_unmodified_generated_readme(content) is True


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Hashing, scope alias/prefix filtering, and Markdown rendering.
# ==========================================================================


@pytest.mark.unit
def test_is_unmodified_generated_readme_validates_embedded_hash() -> None:
    """Verify valid LF and CRLF embedded hashes return True while tampered bodies return False."""
    body = "# Title\n\nBody text."
    digest = compute_content_hash(body)
    valid_lf = f"{body}\n<!-- gdrm-hash: {digest} -->\n"
    valid_crlf = valid_lf.replace("\n", "\r\n")
    tampered = f"{body} edited\n<!-- gdrm-hash: {digest} -->\n"

    assert is_unmodified_generated_readme(valid_lf) is True
    assert is_unmodified_generated_readme(valid_crlf) is True
    assert is_unmodified_generated_readme(tampered) is False
    assert is_unmodified_generated_readme("# Manual README without hash\n") is False


@pytest.mark.unit
def test_resolve_target_packages_filters_by_alias_and_prefix(tmp_path: Path) -> None:
    """Verify subsystem aliases ('gda') and prefixes ('src') match all nested manifest entries."""
    manifest = [
        {"path": "src/gda/core"},
        {"path": "src/gda/model/atom"},
        {"path": "src/cli/main"},
    ]

    assert resolve_target_packages(manifest, tmp_path, target=None) == manifest
    assert resolve_target_packages(manifest, tmp_path, target="gda") == [
        {"path": "src/gda/core"},
        {"path": "src/gda/model/atom"},
    ]
    assert resolve_target_packages(manifest, tmp_path, target="src/cli/main") == [
        {"path": "src/cli/main"},
    ]


@pytest.mark.unit
def test_generate_package_readme_renders_subpackages_and_exports(tmp_path: Path) -> None:
    """Verify subpackage links, fallback descriptions, and __init__.__all__ exports render."""
    pkg = tmp_path / "src" / "pkg"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text('__all__ = ["PublicAPI"]\n', encoding="utf-8")
    (pkg / "alpha.py").write_text(
        '"""Alpha summary."""\n__version__ = "1.0.0+build.1"\n', encoding="utf-8"
    )

    sub_a = pkg / "sub_a"
    sub_a.mkdir()
    (sub_a / "__init__.py").write_text('"""Sub A summary."""\n', encoding="utf-8")
    (sub_a / "README.md").write_text("# Sub A\n", encoding="utf-8")

    sub_b = pkg / "sub_b"
    sub_b.mkdir()
    (sub_b / "__init__.py").write_text("x = 1\n", encoding="utf-8")

    (pkg / "sub_c").mkdir()
    (pkg / "_ignored").mkdir()

    pkg_info = {
        "path": "src/pkg",
        "title": "Pkg Title",
        "role": "Pkg Role",
        "test_path": "tests/test_pkg",
        "quality_gate": "100.0%",
    }
    rendered = generate_package_readme(pkg_info, tmp_path)

    assert "- **[sub_a/](sub_a/README.md)**: Sub A summary." in rendered
    assert "- **`sub_b/`**: Subpackage domain entities and enumerations." in rendered
    assert "- **`sub_c/`**: Subpackage domain entities and enumerations." in rendered
    assert "_ignored" not in rendered
    assert "Exports: `PublicAPI`." in rendered


@pytest.mark.unit
def test_generate_package_readme_handles_init_without_all_and_missing_init(
    tmp_path: Path,
) -> None:
    """Verify export footer adapts when __init__.py lacks __all__ or does not exist."""
    pkg_a = tmp_path / "pkg_a"
    pkg_a.mkdir()
    (pkg_a / "__init__.py").write_text("x = 1\n", encoding="utf-8")
    pkg_b = tmp_path / "pkg_b"
    pkg_b.mkdir()

    base_info: dict[str, Any] = {
        "title": "T",
        "role": "R",
        "test_path": "tests/t",
        "quality_gate": "100%",
    }
    rendered_a = generate_package_readme({**base_info, "path": "pkg_a"}, tmp_path)
    rendered_b = generate_package_readme({**base_info, "path": "pkg_b"}, tmp_path)

    assert "explicitly declared in `__all__`" in rendered_a
    assert "Direct submodule imports supported." in rendered_b


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Unlisted directory synthesis, manifest without default_root, prompt choices.
# ==========================================================================


@pytest.mark.regression
def test_resolve_target_packages_synthesizes_unlisted_relative_and_absolute_dirs(
    tmp_path: Path,
) -> None:
    """Verify unlisted existing directories produce synthesized package metadata."""
    unlisted = tmp_path / "src" / "custom"
    unlisted.mkdir(parents=True)

    rel_result = resolve_target_packages([], tmp_path, target="src/custom")
    abs_result = resolve_target_packages([], tmp_path, target=str(unlisted))

    assert rel_result[0]["path"] == "src/custom"
    assert abs_result[0]["path"] == str(unlisted).replace("\\", "/")


@pytest.mark.regression
def test_load_package_definitions_without_default_root_returns_none(tmp_path: Path) -> None:
    """Verify manifests omitting default_root return None for the root element."""
    manifest = tmp_path / "packages.toml"
    _write_manifest(manifest, '[[packages]]\npath = "src/a"\n')

    default_root, packages = load_package_definitions(manifest)

    assert default_root is None
    assert packages == [{"path": "src/a"}]


@pytest.mark.regression
@pytest.mark.parametrize(
    ("raw_input", "expected"),
    [("y", "y"), ("yes", "y"), ("n", "n"), ("no", "n"), ("a", "a"), ("all", "a"), ("q", "q")],
)
def test_prompt_overwrite_accepts_all_valid_choices(
    raw_input: str,
    expected: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify prompt_overwrite normalizes y/n/a/q responses."""
    monkeypatch.setattr("builtins.input", lambda _prompt: raw_input)
    assert prompt_overwrite(Path("README.md")) == expected


@pytest.mark.regression
def test_prompt_overwrite_reprompts_on_invalid_and_handles_eof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify invalid input reprompts and EOFError returns 'q'."""
    responses = iter(["invalid", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))
    assert prompt_overwrite(Path("README.md")) == "q"

    def _raise_eof(_prompt: str) -> str:
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)
    assert prompt_overwrite(Path("README.md")) == "q"


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Missing manifests, unknown targets, and bad GDT config paths.
# ==========================================================================


@pytest.mark.regression
def test_load_package_definitions_missing_file_raises_file_not_found(tmp_path: Path) -> None:
    """Verify load_package_definitions raises FileNotFoundError for a missing manifest."""
    with pytest.raises(FileNotFoundError, match="Package manifest not found"):
        load_package_definitions(tmp_path / "missing.toml")


@pytest.mark.regression
def test_resolve_target_packages_unknown_target_raises_file_not_found(tmp_path: Path) -> None:
    """Verify unknown targets absent from both manifest and disk raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="not found in configuration or filesystem"):
        resolve_target_packages([], tmp_path, target="src/nonexistent")


@pytest.mark.regression
def test_run_returns_one_on_config_or_manifest_failure(gdt_workspace: Path) -> None:
    """Verify run() returns exit code 1 when GDT config or package manifest loading fails."""
    code_bad_cfg = run(
        root_dir=gdt_workspace,
        config_path=gdt_workspace / "missing_gdt.toml",
    )
    assert code_bad_cfg == 1

    try:
        code_bad_manifest = run(
            root_dir=gdt_workspace,
            packages_config=gdt_workspace / "missing_packages.toml",
        )
    finally:
        _close_gdrm_logger()

    assert code_bad_manifest == 1


# ==========================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Unchanged skip, hash auto-update, hand-edit prompting, and auto root discovery.
# ==========================================================================


@pytest.mark.integration
def test_run_skips_unchanged_and_auto_updates_unmodified_generated_readme(
    gdt_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify identical READMEs skip and unmodified generated READMEs auto-update on code change."""
    pkg_dir = gdt_workspace / "src" / "gda" / "auto"
    pkg_dir.mkdir(parents=True)
    mod = pkg_dir / "item.py"
    mod.write_text('"""V1 summary."""\n__version__ = "1.0.0+build.1"\n', encoding="utf-8")

    manifest = gdt_workspace / "packages.toml"
    _write_manifest(
        manifest,
        "[[packages]]\n"
        'path = "src/gda/auto"\n'
        'title = "Auto"\n'
        'role = "Role"\n'
        'test_path = "tests/auto"\n'
        'quality_gate = "100%"\n'
        "[[packages]]\n"
        'path = "src/gda/missing_dir"\n'
        'title = "Missing"\n'
        'role = "Role"\n'
        'test_path = "tests/missing"\n'
        'quality_gate = "100%"\n',
    )
    monkeypatch.chdir(gdt_workspace)

    try:
        assert run(packages_config=manifest) == 0
        assert run(packages_config=manifest) == 0
        mod.write_text('"""V2 summary."""\n__version__ = "1.0.0+build.2"\n', encoding="utf-8")
        assert run(packages_config=manifest) == 0
    finally:
        _close_gdrm_logger()

    assert "1.0.0+build.2" in (pkg_dir / "README.md").read_text(encoding="utf-8")


@pytest.mark.integration
def test_run_hand_edited_readme_prompt_decisions_yes_skip_all_and_quit(
    gdt_workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify hand-edited READMEs prompt and honor 'y', 'n', 'a', and 'q'."""
    pkg_1 = gdt_workspace / "src" / "p1"
    pkg_2 = gdt_workspace / "src" / "p2"
    pkg_1.mkdir(parents=True)
    pkg_2.mkdir(parents=True)
    (pkg_1 / "README.md").write_text("# Hand-edited 1\n", encoding="utf-8")
    (pkg_2 / "README.md").write_text("# Hand-edited 2\n", encoding="utf-8")

    manifest = gdt_workspace / "packages.toml"
    _write_manifest(
        manifest,
        '[[packages]]\npath = "src/p1"\ntitle = "P1"\nrole = "R"\ntest_path = "t"\nquality_gate = "100%"\n'
        '[[packages]]\npath = "src/p2"\ntitle = "P2"\nrole = "R"\ntest_path = "t"\nquality_gate = "100%"\n',
    )

    try:
        # Decline first ('n'), then abort on second ('q')
        choices = iter(["n", "q"])
        monkeypatch.setattr("builtins.input", lambda _p: next(choices))
        assert run(root_dir=gdt_workspace, packages_config=manifest) == 0
        assert (pkg_1 / "README.md").read_text(encoding="utf-8") == "# Hand-edited 1\n"
        assert (pkg_2 / "README.md").read_text(encoding="utf-8") == "# Hand-edited 2\n"

        # Accept first ('y') only, then decline second ('n')
        choices_yn = iter(["y", "n"])
        monkeypatch.setattr("builtins.input", lambda _p: next(choices_yn))
        assert run(root_dir=gdt_workspace, packages_config=manifest) == 0
        assert "# P1" in (pkg_1 / "README.md").read_text(encoding="utf-8")
        assert (pkg_2 / "README.md").read_text(encoding="utf-8") == "# Hand-edited 2\n"

        # Restore hand-edit on p1 and choose 'a' (all) -> overwrites both without re-prompting
        (pkg_1 / "README.md").write_text("# Hand-edited 1 again\n", encoding="utf-8")
        monkeypatch.setattr("builtins.input", lambda _p: "a")
        assert run(root_dir=gdt_workspace, packages_config=manifest) == 0
        assert "# P1" in (pkg_1 / "README.md").read_text(encoding="utf-8")
        assert "# P2" in (pkg_2 / "README.md").read_text(encoding="utf-8")
    finally:
        _close_gdrm_logger()
