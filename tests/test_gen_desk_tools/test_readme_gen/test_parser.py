"""Path: tests/test_gen_desk_tools/test_readme_gen/test_parser.py

Unit and regression tests for gen_desk_tools.readme_gen.parser.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gen_desk_tools.readme_gen.parser import extract_module_metadata

__version__ = "1.0.0+build.1"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: End-to-end AST extraction of docstring, __version__, and __all__.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_extract_module_metadata_parses_standard_module_header(tmp_path: Path) -> None:
    """Verify extract_module_metadata extracts description, version, and __all__."""
    mod = tmp_path / "sample.py"
    mod.write_text(
        '"""Path: src/sample.py\n\n'
        "Canonical summary line for sample module.\n\n"
        'Detailed operational role.\n"""\n\n'
        '__version__ = "1.2.3+build.4"\n'
        '__all__ = ["alpha", "beta"]\n',
        encoding="utf-8",
    )

    meta = extract_module_metadata(mod)

    assert meta["description"] == "Canonical summary line for sample module."
    assert meta["version"] == "1.2.3+build.4"
    assert meta["all_exports"] == "`alpha`, `beta`"


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Annotated assignments and filtering of non-metadata docstring lines.
# ==========================================================================


@pytest.mark.unit
def test_extract_module_metadata_supports_annotated_assignments(tmp_path: Path) -> None:
    """Verify AnnAssign declarations for __version__ and __all__ are extracted."""
    mod = tmp_path / "annotated.py"
    mod.write_text(
        '"""Name: annotated.py\n<!-- comment -->\n-->\n\nAnnotated summary."""\n'
        '__version__: str = "2.0.0+build.1"\n'
        '__all__: list[str] = ["gamma"]\n'
        "UNASSIGNED: int\n"
        "OTHER = 42\n",
        encoding="utf-8",
    )

    meta = extract_module_metadata(mod)

    assert meta["description"] == "Annotated summary."
    assert meta["version"] == "2.0.0+build.1"
    assert meta["all_exports"] == "`gamma`"


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Missing docstrings, header-only docstrings, tuple unpacking, non-list __all__.
# ==========================================================================


@pytest.mark.regression
def test_extract_module_metadata_handles_missing_docstring_and_unversioned(
    tmp_path: Path,
) -> None:
    """Verify modules without docstrings or __version__ return safe fallback defaults."""
    mod = tmp_path / "bare.py"
    mod.write_text("import os\n\ndef helper() -> None:\n    pass\n", encoding="utf-8")

    meta = extract_module_metadata(mod)

    assert meta["description"] == "No description available."
    assert meta["version"] == "Unversioned"
    assert meta["all_exports"] == ""


@pytest.mark.regression
def test_extract_module_metadata_header_only_docstring_falls_back(tmp_path: Path) -> None:
    """Verify a docstring containing only Path: metadata falls back to default description."""
    mod = tmp_path / "header_only.py"
    mod.write_text('"""Path: src/header_only.py\n"""\n', encoding="utf-8")

    meta = extract_module_metadata(mod)
    assert meta["description"] == "No description available."


@pytest.mark.regression
def test_extract_module_metadata_ignores_non_constant_version_and_non_list_all(
    tmp_path: Path,
) -> None:
    """Verify dynamic __version__, tuple unpacking, and non-list __all__ are safely skipped."""
    mod = tmp_path / "edge.py"
    mod.write_text(
        'a, b = 1, 2\n__version__ = get_version()\n__all__ = ("not_a_list",)\n',
        encoding="utf-8",
    )

    meta = extract_module_metadata(mod)

    assert meta["version"] == "Unversioned"
    assert meta["all_exports"] == ""


@pytest.mark.regression
def test_extract_module_metadata_filters_non_string_items_in_all(tmp_path: Path) -> None:
    """Verify non-string elements inside __all__ are omitted from formatted exports."""
    mod = tmp_path / "mixed_all.py"
    mod.write_text('__all__ = ["valid", 123, None]\n', encoding="utf-8")

    meta = extract_module_metadata(mod)
    assert meta["all_exports"] == "`valid`"


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Syntax errors and missing files recorded cleanly without raising.
# ==========================================================================


@pytest.mark.regression
def test_extract_module_metadata_syntax_error_records_extraction_error(
    tmp_path: Path,
) -> None:
    """Verify invalid Python syntax is caught and reported in the description field."""
    bad = tmp_path / "broken.py"
    bad.write_text("def broken(:\n", encoding="utf-8")

    meta = extract_module_metadata(bad)

    assert meta["description"].startswith("Extraction error:")
    assert meta["version"] == "Unversioned"


@pytest.mark.regression
def test_extract_module_metadata_missing_file_records_extraction_error(
    tmp_path: Path,
) -> None:
    """Verify a nonexistent file path is caught and reported in the description field."""
    meta = extract_module_metadata(tmp_path / "missing.py")
    assert meta["description"].startswith("Extraction error:")
