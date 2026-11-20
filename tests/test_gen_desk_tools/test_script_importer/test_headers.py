"""Path: tests/test_gen_desk_tools/test_script_importer/test_headers.py

Unit and regression tests for gen_desk_tools.script_importer.headers.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from gen_desk_tools.script_importer.headers import parse_metadata_header

__version__ = "1.0.0+build.2"

# ==========================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Primary Line-1 Python docstring routing header extraction.
# ==========================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_parse_metadata_header_python_docstring_resolves_destination(tmp_path: Path) -> None:
    """Verify Line-1 Python docstring Path: header extracts filename and resolved path."""
    staged = tmp_path / "staged.py"
    staged.write_text(
        '"""Path: src/gen_desk_tools/sample.py\n\nSample module.\n"""\n',
        encoding="utf-8",
    )

    name, dest = parse_metadata_header(staged, tmp_path)

    assert name == "sample.py"
    assert dest == (tmp_path / "src" / "gen_desk_tools" / "sample.py").resolve()


# ==========================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Multi-format parsing across Markdown, YAML, JSON, TOML, .txt, and Notebooks.
# ==========================================================================


@pytest.mark.unit
def test_parse_metadata_header_markdown_html_comment_extracts_path(tmp_path: Path) -> None:
    """Verify Markdown Line-1 HTML comment header strips trailing delimiters cleanly."""
    staged = tmp_path / "doc.md"
    staged.write_text("<!--Path: docs/guide.md-->\n# Guide\n", encoding="utf-8")

    name, dest = parse_metadata_header(staged, tmp_path)

    assert name == "guide.md"
    assert dest == (tmp_path / "docs" / "guide.md").resolve()


@pytest.mark.unit
def test_parse_metadata_header_markdown_yaml_frontmatter_extracts_skill_path(
    tmp_path: Path,
) -> None:
    """Verify Markdown YAML frontmatter _path routes skill files without breaking Line 1."""
    staged = tmp_path / "skill.md"
    staged.write_text(
        "---\nname: example-skill\n_path: .skills/example-skill/SKILL.md\n---\n\n# Example Skill\n",
        encoding="utf-8",
    )

    name, dest = parse_metadata_header(staged, tmp_path)

    assert name == "example-skill"
    assert dest == (tmp_path / ".skills" / "example-skill" / "SKILL.md").resolve()


@pytest.mark.unit
def test_parse_metadata_header_json_toml_yaml_and_txt_extract_structured_paths(
    tmp_path: Path,
) -> None:
    """Verify JSON, TOML, YAML, and .txt downloads resolve _path and path keys."""
    json_file = tmp_path / "payload.json"
    json_file.write_text('{"_path": "schemas/item.json", "type": "object"}\n', encoding="utf-8")

    toml_file = tmp_path / "cfg.toml"
    toml_file.write_text('_path = "config/tool.toml"\n', encoding="utf-8")

    yaml_file = tmp_path / "meta.yml"
    yaml_file.write_text("_path: config/meta.yml\n", encoding="utf-8")

    txt_toml = tmp_path / "gemini-code-123.txt"
    txt_toml.write_text('_path = "gtemp/gsi_test/sample_settings.toml"\n', encoding="utf-8")

    assert (
        parse_metadata_header(json_file, tmp_path)[1] == (tmp_path / "schemas/item.json").resolve()
    )
    assert (
        parse_metadata_header(toml_file, tmp_path)[1] == (tmp_path / "config/tool.toml").resolve()
    )
    assert parse_metadata_header(yaml_file, tmp_path)[1] == (tmp_path / "config/meta.yml").resolve()
    assert (
        parse_metadata_header(txt_toml, tmp_path)[1]
        == (tmp_path / "gtemp/gsi_test/sample_settings.toml").resolve()
    )


@pytest.mark.unit
def test_parse_metadata_header_ipynb_reads_metadata_and_cell_fallback(tmp_path: Path) -> None:
    """Verify Jupyter Notebooks resolve paths from metadata or first-cell comment headers."""
    nb_meta = tmp_path / "meta.ipynb"
    nb_meta.write_text(
        json.dumps({"metadata": {"_name": "nb.ipynb", "_path": "notebooks/nb.ipynb"}, "cells": []}),
        encoding="utf-8",
    )

    nb_cell = tmp_path / "cell.ipynb"
    nb_cell.write_text(
        json.dumps(
            {
                "metadata": {},
                "cells": [
                    {
                        "cell_type": "markdown",
                        "source": ["<!-- Name: report.ipynb -->\n", "<!-- Path: notebooks/ -->\n"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    name_m, dest_m = parse_metadata_header(nb_meta, tmp_path)
    name_c, dest_c = parse_metadata_header(nb_cell, tmp_path)

    assert (name_m, dest_m) == ("nb.ipynb", (tmp_path / "notebooks/nb.ipynb").resolve())
    assert (name_c, dest_c) == ("report.ipynb", (tmp_path / "notebooks/report.ipynb").resolve())


# ==========================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Directory paths, frontmatter fallback, and Notebooks without headers.
# ==========================================================================


@pytest.mark.regression
def test_parse_metadata_header_directory_path_appends_explicit_name(tmp_path: Path) -> None:
    """Verify a Path: pointing to an existing directory combines with Name: cleanly."""
    target_dir = tmp_path / "scripts"
    target_dir.mkdir()
    staged = tmp_path / "raw.sh"
    staged.write_text("# Name: run.sh\n# Path: scripts\necho ok\n", encoding="utf-8")

    name, dest = parse_metadata_header(staged, tmp_path)

    assert name == "run.sh"
    assert dest == (target_dir / "run.sh").resolve()


@pytest.mark.regression
def test_parse_metadata_header_markdown_frontmatter_without_path_falls_back_to_comment(
    tmp_path: Path,
) -> None:
    """Verify frontmatter with name only preserves target_name while falling back to HTML Path:."""
    staged = tmp_path / "hybrid.md"
    staged.write_text(
        "---\nname: custom.md\n---\n<!--Path: docs/-->\n# Body\n",
        encoding="utf-8",
    )

    name, dest = parse_metadata_header(staged, tmp_path)

    assert name == "custom.md"
    assert dest == (tmp_path / "docs" / "custom.md").resolve()


@pytest.mark.regression
def test_parse_metadata_header_ipynb_without_path_in_metadata_or_cells_returns_none(
    tmp_path: Path,
) -> None:
    """Verify Notebooks lacking metadata and cell headers return (None, None)."""
    nb_empty_cells = tmp_path / "empty.ipynb"
    nb_empty_cells.write_text(json.dumps({"metadata": {}, "cells": []}), encoding="utf-8")

    nb_plain_cell = tmp_path / "plain.ipynb"
    nb_plain_cell.write_text(
        json.dumps({"metadata": {}, "cells": [{"cell_type": "code", "source": ["x = 1\n"]}]}),
        encoding="utf-8",
    )

    assert parse_metadata_header(nb_empty_cells, tmp_path) == (None, None)
    assert parse_metadata_header(nb_plain_cell, tmp_path) == (None, None)


# ==========================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Unreadable files, corrupt Notebooks, missing headers, and root escapes.
# ==========================================================================


@pytest.mark.regression
def test_parse_metadata_header_unreadable_or_corrupt_files_return_none(tmp_path: Path) -> None:
    """Verify missing files and malformed .ipynb JSON return (None, None) safely."""
    bad_nb = tmp_path / "broken.ipynb"
    bad_nb.write_text("{not valid json", encoding="utf-8")

    assert parse_metadata_header(tmp_path / "missing.py", tmp_path) == (None, None)
    assert parse_metadata_header(bad_nb, tmp_path) == (None, None)


@pytest.mark.regression
def test_parse_metadata_header_missing_header_or_root_escape_returns_none(
    tmp_path: Path,
) -> None:
    """Verify headerless files and paths escaping the workspace root are rejected."""
    no_header = tmp_path / "plain.txt"
    no_header.write_text("just some text\n", encoding="utf-8")

    escape = tmp_path / "escape.py"
    escape.write_text('"""Path: ../../outside.py"""\n', encoding="utf-8")

    assert parse_metadata_header(no_header, tmp_path) == (None, None)
    assert parse_metadata_header(escape, tmp_path) == (None, None)
