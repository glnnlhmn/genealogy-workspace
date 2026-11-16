"""Path: tests/test_system/test_gsi.py

Test harness and regression test suite for the GSI intake engine.

Operational Role:
    Verifies TOML configuration parsing, workspace root discovery, protected
    domain detection, POSIX file logging, force-mode warnings, Safe Backup
    collision counters, hyphenated path parsing, multi-extension metadata
    extraction (.ipynb, .json, .toml, .py), execution routing, and CLI flags
    achieving 100% statement and branch coverage.
"""

from __future__ import annotations

import io
import json
import logging
import runpy
import sys
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from system.gsi.gsi import (
    _backup_destination,
    _determine_backup_directory,
    _execute_python,
    _execute_target,
    _is_protected_domain,
    _prompt_user_yes_no,
    get_workspace_root,
    load_gsi_config,
    main,
    parse_metadata_header,
    run_intake,
    setup_gsi_logger,
)

__version__ = "1.5.0+build.7"

# ==============================================================================
# GROUP 1: Configuration & Workspace Root Tests
# Note: Verification of load_gsi_config fallbacks, corrupt TOML, and root discovery
# ==============================================================================


@pytest.mark.unit
def test_load_gsi_config_fallback_defaults() -> None:
    """Verify default configuration loads when file path does not exist."""
    cfg = load_gsi_config(Path("/nonexistent/gsi_conf.toml"))
    assert cfg["workspace"]["download_dir"] == "download"
    assert "schemas" in cfg["code_domains"]["protected_domains"]
    assert "data/setup" in cfg["code_domains"]["protected_domains"]


@pytest.mark.unit
def test_load_gsi_config_default_lookup() -> None:
    """Verify default config lookup when path is None."""
    cfg = load_gsi_config(None)
    assert "workspace" in cfg


@pytest.mark.unit
def test_load_gsi_config_corrupt_toml(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify corrupt TOML emits warning and falls back to default settings."""
    bad_toml = tmp_path / "bad_gsi_conf.toml"
    bad_toml.write_text("NOT_VALID_TOML = [unclosed", encoding="utf-8")
    cfg = load_gsi_config(bad_toml)
    captured = capsys.readouterr()
    assert "Warning: Failed to parse" in captured.out
    assert cfg["workspace"]["download_dir"] == "download"


@pytest.mark.unit
def test_load_gsi_config_non_dict_override(tmp_path: Path) -> None:
    """Verify scalar TOML values override default sections."""
    custom_toml = tmp_path / "custom.toml"
    custom_toml.write_text('custom_scalar = "custom_value"\n', encoding="utf-8")
    cfg = load_gsi_config(custom_toml)
    assert cfg.get("custom_scalar") == "custom_value"


@pytest.mark.unit
def test_get_workspace_root_variants(tmp_path: Path) -> None:
    """Verify workspace root resolution across config, parent directories, and fallback."""
    # 1. Explicit valid root directory
    cfg = {"workspace": {"root": str(tmp_path)}}
    assert get_workspace_root(cfg) == tmp_path.resolve()

    # 2. Explicit non-existent root path (covers branch 99->102)
    cfg_non_dir = {"workspace": {"root": str(tmp_path / "missing_dir")}}
    root_non_dir = get_workspace_root(cfg_non_dir)
    assert isinstance(root_non_dir, Path)

    # 3. Parent traversal finding src and archive
    fake_root = tmp_path / "mock_workspace"
    (fake_root / "src").mkdir(parents=True)
    (fake_root / "archive").mkdir(parents=True)
    script_in_sub = fake_root / "src" / "system" / "gsi" / "gsi.py"
    script_in_sub.parent.mkdir(parents=True)

    with patch("system.gsi.gsi.__file__", str(script_in_sub)):
        discovered_root = get_workspace_root({"workspace": {"root": "."}})
        assert discovered_root == fake_root.resolve()

    # 4. Parent traversal finding pyproject.toml
    proj_root = tmp_path / "proj_root"
    proj_root.mkdir(parents=True)
    (proj_root / "pyproject.toml").write_text("", encoding="utf-8")
    script_proj = proj_root / "tools" / "gsi.py"
    script_proj.parent.mkdir(parents=True)

    with patch("system.gsi.gsi.__file__", str(script_proj)):
        discovered_proj = get_workspace_root({"workspace": {"root": "."}})
        assert discovered_proj == proj_root.resolve()

    # 5. Fallback to cwd
    with patch("system.gsi.gsi.__file__", "/isolated/nowhere/gsi.py"):
        fallback_root = get_workspace_root({"workspace": {"root": "."}})
        assert fallback_root == Path.cwd().resolve()


# ==============================================================================
# GROUP 2: Routing, Protected Domains & Safe Backups
# Note: Verification of backup routing, domain checks, collisions, and logger setup
# ==============================================================================


@pytest.mark.unit
def test_determine_backup_directory_routes_and_defaults(tmp_path: Path) -> None:
    """Verify routing prefixes, dedicated subdirectories, and default fallback."""
    cfg = load_gsi_config(Path("/nonexistent"))

    schema_file = tmp_path / "schemas" / "entity" / "person.json"
    setup_file = tmp_path / "data" / "setup" / "01_sites.json"
    default_file = tmp_path / "other" / "misc.txt"

    bk_schema = _determine_backup_directory(schema_file, tmp_path, cfg)
    assert bk_schema.as_posix().endswith("archive/backups_schemas/schemas/entity")

    bk_setup = _determine_backup_directory(setup_file, tmp_path, cfg)
    assert bk_setup.as_posix().endswith("archive/backups_data_setup/data/setup")

    bk_default = _determine_backup_directory(default_file, tmp_path, cfg)
    assert bk_default.as_posix().endswith("archive/backups_system/other")


@pytest.mark.unit
def test_is_protected_domain(tmp_path: Path) -> None:
    """Verify protected domain detection identifies src, tests, schemas, and data/setup."""
    cfg = load_gsi_config(Path("/nonexistent"))

    assert _is_protected_domain(tmp_path / "src/gda/core/config.py", tmp_path, cfg) is True
    assert _is_protected_domain(tmp_path / "tests/test_gda/test_config.py", tmp_path, cfg) is True
    assert _is_protected_domain(tmp_path / "schemas/core.json", tmp_path, cfg) is True
    assert _is_protected_domain(tmp_path / "data/setup/sites.json", tmp_path, cfg) is True
    assert _is_protected_domain(tmp_path / "docs/readme.txt", tmp_path, cfg) is False


@pytest.mark.unit
def test_backup_destination_collision_resolution(tmp_path: Path) -> None:
    """Verify backup file adds monotonic counter if timestamp filename exists (covers 316-317)."""
    cfg = load_gsi_config(Path("/nonexistent"))
    target = tmp_path / "src" / "gda" / "test.py"
    target.parent.mkdir(parents=True)
    target.write_text("code", encoding="utf-8")

    logger = logging.getLogger("gsi_test")
    logger.addHandler(logging.NullHandler())

    fixed_utc = datetime(2026, 11, 10, 12, 0, 0, tzinfo=UTC)
    with patch("system.gsi.gsi.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_utc
        mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

        bk1 = _backup_destination(target, tmp_path, cfg, logger)
        bk2 = _backup_destination(target, tmp_path, cfg, logger)

    assert bk1.exists()
    assert bk2.exists()
    assert bk1 != bk2
    assert "_1.bk" in bk2.name


@pytest.mark.unit
def test_setup_gsi_logger(tmp_path: Path) -> None:
    """Verify setup_gsi_logger configures file handler and returns logger."""
    cfg = {"logging": {"log_file": "logs/test_gsi.log"}}
    logger = setup_gsi_logger(tmp_path, cfg)
    assert logger.name == "gsi"
    assert (tmp_path / "logs" / "test_gsi.log").exists()


# ==============================================================================
# GROUP 3: Header Parsing & Hyphenated Path Tests
# Note: Verification of .py, .ipynb, .json, .toml, and generic headers
# ==============================================================================


@pytest.mark.unit
def test_parse_metadata_header_hyphenated_filenames(tmp_path: Path) -> None:
    """Verify paths containing hyphens, underscores, and plus signs are not truncated."""
    py_candidate = tmp_path / "download_py.py"
    py_candidate.write_text(
        '"""Path: src/system/my-tool-runner.py\n\nDoc.\n"""\n__version__ = "1.0.0+build.1"\n',
        encoding="utf-8",
    )
    name1, path1 = parse_metadata_header(py_candidate, tmp_path)
    assert name1 == "my-tool-runner.py"
    assert path1 == tmp_path / "src" / "system" / "my-tool-runner.py"

    md_candidate = tmp_path / "download_md.md"
    md_candidate.write_text(
        "<!--Path: prompts/topics/topic-test-harness.md-->\n# Test Harness\n",
        encoding="utf-8",
    )
    name2, path2 = parse_metadata_header(md_candidate, tmp_path)
    assert name2 == "topic-test-harness.md"
    assert path2 == tmp_path / "prompts" / "topics" / "topic-test-harness.md"

    json_candidate = tmp_path / "download_json.json"
    json_candidate.write_text(
        '{\n  "_path": "data/setup/01-initial-locations.json",\n  "type": "object"\n}\n',
        encoding="utf-8",
    )
    name3, path3 = parse_metadata_header(json_candidate, tmp_path)
    assert name3 == "01-initial-locations.json"
    assert path3 == tmp_path / "data" / "setup" / "01-initial-locations.json"


@pytest.mark.unit
def test_parse_metadata_header_unreadable_file(tmp_path: Path) -> None:
    """Verify unreadable or nonexistent file returns (None, None)."""
    assert parse_metadata_header(tmp_path / "nonexistent.py", tmp_path) == (None, None)


@pytest.mark.unit
def test_parse_metadata_header_notebook_branches(tmp_path: Path) -> None:
    """Verify all notebook branches: metadata present, path-only cells, and fallbacks."""
    nb_file = tmp_path / "nb.ipynb"

    # 1. Metadata dict has path and name (bypasses cell parsing: covers 171->202)
    nb_meta = {
        "metadata": {"_path": "src/gda/analysis.ipynb", "_name": "analysis.ipynb"},
        "cells": [],
    }
    nb_file.write_text(json.dumps(nb_meta), encoding="utf-8")
    name1, path1 = parse_metadata_header(nb_file, tmp_path)
    assert name1 == "analysis.ipynb"
    assert path1 == tmp_path / "src" / "gda" / "analysis.ipynb"

    # 2. Empty cells list (covers branch 171->202 when cells is empty)
    nb_no_cells = {
        "metadata": {},
        "cells": [],
    }
    nb_file.write_text(json.dumps(nb_no_cells), encoding="utf-8")
    assert parse_metadata_header(nb_file, tmp_path) == (None, None)

    # 3. Cell has # Path: but no # Name: (covers branch 183->185)
    nb_path_only = {
        "metadata": {},
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Path: src/gda/path_only_cell.ipynb\n"],
            }
        ],
    }
    nb_file.write_text(json.dumps(nb_path_only), encoding="utf-8")
    name2, path2 = parse_metadata_header(nb_file, tmp_path)
    assert name2 == "path_only_cell.ipynb"
    assert path2 == tmp_path / "src" / "gda" / "path_only_cell.ipynb"

    # 4. Cell has # Name: but no # Path: (covers branch 185->202)
    nb_name_only = {
        "metadata": {},
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Name: name_only.ipynb\n"],
            }
        ],
    }
    nb_file.write_text(json.dumps(nb_name_only), encoding="utf-8")
    assert parse_metadata_header(nb_file, tmp_path) == (None, None)

    # 5. Cell has both # Name: and # Path: in code cell
    nb_both = {
        "metadata": {},
        "cells": [
            {
                "cell_type": "code",
                "source": ["# Name: code_cell.ipynb\n", "# Path: src/gda/code_cell.ipynb\n"],
            }
        ],
    }
    nb_file.write_text(json.dumps(nb_both), encoding="utf-8")
    name3, path3 = parse_metadata_header(nb_file, tmp_path)
    assert name3 == "code_cell.ipynb"
    assert path3 == tmp_path / "src" / "gda" / "code_cell.ipynb"

    # 6. Corrupt notebook JSON
    nb_file.write_text("CORRUPT_JSON", encoding="utf-8")
    assert parse_metadata_header(nb_file, tmp_path) == (None, None)


@pytest.mark.unit
def test_parse_metadata_header_toml_and_json_branches(tmp_path: Path) -> None:
    """Verify JSON/TOML branches: path only, name only, and parsing exceptions."""
    # 1. JSON with only _name (covers branch 197->202)
    j_name_only = tmp_path / "name_only.json"
    j_name_only.write_text(
        '{\n  "_name": "doc.json",\n  "description": "Doc"\n}\n<!--Path: schemas/doc.json-->\n',
        encoding="utf-8",
    )
    name1, path1 = parse_metadata_header(j_name_only, tmp_path)
    assert name1 == "doc.json"
    assert path1 == tmp_path / "schemas" / "doc.json"

    # 2. JSON/TOML regex exception (covers lines 199-200)
    t_file = tmp_path / "sample.toml"
    t_file.write_text('path = "schemas/sample.toml"\n', encoding="utf-8")
    with patch("system.gsi.gsi.re.search", side_effect=Exception("Regex fault")):
        assert parse_metadata_header(t_file, tmp_path) == (None, None)


@pytest.mark.unit
def test_parse_metadata_header_generic_comments_and_outside_root(tmp_path: Path) -> None:
    """Verify generic comment headers and name already found branch (covers 220->229)."""
    # 1. Generic comment with both # Name: and # Path:
    f1 = tmp_path / "generic.sh"
    f1.write_text(
        "# Name: script.sh\n# Path: src/system/script.sh\n#!/bin/bash\necho 1\n",
        encoding="utf-8",
    )
    name1, path1 = parse_metadata_header(f1, tmp_path)
    assert name1 == "script.sh"
    assert path1 == tmp_path / "src" / "system" / "script.sh"

    # 2. Docstring header where name is already extracted (covers branch 220->229)
    f2 = tmp_path / "has_name.py"
    f2.write_text(
        '# Name: named_module.py\n"""Path: src/system/named_module.py\n"""\n',
        encoding="utf-8",
    )
    name2, path2 = parse_metadata_header(f2, tmp_path)
    assert name2 == "named_module.py"
    assert path2 == tmp_path / "src" / "system" / "named_module.py"

    # 3. Path escaping root
    f_esc = tmp_path / "escape.py"
    f_esc.write_text('"""Path: ../../outside.py\n"""\n', encoding="utf-8")
    assert parse_metadata_header(f_esc, tmp_path) == (None, None)

    # 4. Missing path header
    f_none = tmp_path / "empty.py"
    f_none.write_text('"""Empty module.\n"""\n', encoding="utf-8")
    assert parse_metadata_header(f_none, tmp_path) == (None, None)


@pytest.mark.unit
def test_parse_metadata_header_directory_target(tmp_path: Path) -> None:
    """Verify target path ending with slash resolves to directory/target_name."""
    f = tmp_path / "dir_target.py"
    f.write_text(
        '# Name: target.py\n# Path: src/system/\n"""Module doc."""\n',
        encoding="utf-8",
    )
    name, path = parse_metadata_header(f, tmp_path)
    assert name == "target.py"
    assert path == tmp_path / "src" / "system" / "target.py"


# ==============================================================================
# GROUP 4: Interactive Prompts & Target Execution
# Note: Verification of _prompt_user_yes_no, _execute_python, and _execute_target
# ==============================================================================


@pytest.mark.unit
def test_prompt_user_yes_no(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify prompt returns True for y/yes and False for other inputs."""
    monkeypatch.setattr("sys.stdin", io.StringIO("y\n"))
    assert _prompt_user_yes_no("Confirm?") is True

    monkeypatch.setattr("sys.stdin", io.StringIO("YES\n"))
    assert _prompt_user_yes_no("Confirm?") is True

    monkeypatch.setattr("sys.stdin", io.StringIO("n\n"))
    assert _prompt_user_yes_no("Confirm?") is False


@pytest.mark.unit
def test_execute_python_variants(tmp_path: Path) -> None:
    """Verify dispatching test runner for test_ files vs standard python execution."""
    test_file = tmp_path / "test_sample.py"
    regular_file = tmp_path / "sample.py"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        assert _execute_python(test_file, tmp_path) == 0
        cmd1 = mock_run.call_args_list[0][0][0]
        assert "-m" in cmd1 and "pytest" in cmd1

        assert _execute_python(regular_file, tmp_path) == 0
        cmd2 = mock_run.call_args_list[1][0][0]
        assert "pytest" not in cmd2


@pytest.mark.unit
def test_execute_target_file_types(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify execution routing across .py, .ps1, .sh, and unsupported extensions."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        # .py
        assert _execute_target(tmp_path / "mod.py", tmp_path) == 0

        # .ps1
        assert _execute_target(tmp_path / "script.ps1", tmp_path) == 0
        assert "powershell.exe" in mock_run.call_args_list[-1][0][0]

        # .sh
        assert _execute_target(tmp_path / "script.sh", tmp_path) == 0
        assert "bash" in mock_run.call_args_list[-1][0][0]

        # Unsupported
        assert _execute_target(tmp_path / "notes.txt", tmp_path) == 0
        assert "Notice: Non-executable" in capsys.readouterr().out


# ==============================================================================
# GROUP 5: Intake Execution & Pipeline Lifecycle
# Note: Verification of run_intake, filtering, cleanup, overwriting, and loop edges
# ==============================================================================


@pytest.mark.integration
def test_run_intake_creates_log_and_backup(tmp_path: Path) -> None:
    """Verify run_intake logs BACKUP_CREATED and FILE_CREATED using POSIX forward slashes."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)
    dest_file = tmp_path / "src" / "gda" / "test_file.py"
    dest_file.parent.mkdir(parents=True)
    dest_file.write_text("old version", encoding="utf-8")

    staged1 = download_dir / "candidate1.py"
    staged1.write_text(
        '"""Path: src/gda/test_file.py\n\nDoc.\n"""\n__version__ = "1.0.0"\n',
        encoding="utf-8",
    )
    staged2 = download_dir / "candidate2.py"
    staged2.write_text(
        '"""Path: src/gda/other_file.py\n\nDoc.\n"""\n__version__ = "1.0.0"\n',
        encoding="utf-8",
    )

    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
download_dir = "download"
logs_dir = "logs"
archive_dir = "archive"

[logging]
log_file = "logs/gsi.log"

[backup_routing]
"src/gda" = "backups_gda"
default = "backups_system"

[code_domains]
protected_domains = ["src"]
""",
        encoding="utf-8",
    )

    status = run_intake(config_path=toml_file)
    assert status == 0
    assert dest_file.read_text(encoding="utf-8").startswith('"""Path: src/gda/test_file.py')

    log_path = tmp_path / "logs" / "gsi.log"
    assert log_path.exists()
    log_content = log_path.read_text(encoding="utf-8")

    assert "BACKUP_CREATED: archive/backups_gda/src/gda/test_file.py." in log_content
    assert "FILE_CREATED: src/gda/test_file.py" in log_content
    assert "FILE_CREATED: src/gda/other_file.py" in log_content


@pytest.mark.integration
def test_run_intake_missing_download_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify run_intake returns 1 if download directory does not exist."""
    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\ndownload_dir = "absent"\n',
        encoding="utf-8",
    )
    assert run_intake(config_path=toml_file) == 1
    assert "Error: Download directory not found" in capsys.readouterr().out


@pytest.mark.integration
def test_run_intake_empty_candidates_and_prefix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify run_intake handles empty candidate directory and prefix filtering."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)
    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\ndownload_dir = "download"\n',
        encoding="utf-8",
    )

    assert run_intake(config_path=toml_file) == 0
    assert "No intake candidates found" in capsys.readouterr().out

    (download_dir / "target_a.py").write_text('"""Path: src/a.py\n"""', encoding="utf-8")
    (download_dir / "other_b.py").write_text('"""Path: src/b.py\n"""', encoding="utf-8")
    assert run_intake(prefix="target", config_path=toml_file) == 0
    assert not (download_dir / "target_a.py").exists()
    assert (download_dir / "other_b.py").exists()


@pytest.mark.integration
def test_run_intake_clean_unparseable_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Verify run_intake clean mode purges unparseable files or declines purge."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)
    bad_file = download_dir / "bad.py"
    bad_file.write_text("no headers", encoding="utf-8")

    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\ndownload_dir = "download"\n',
        encoding="utf-8",
    )

    # Clean False: Skip file
    assert run_intake(clean=False, config_path=toml_file) == 0
    assert bad_file.exists()
    assert "Skipping bad.py" in capsys.readouterr().out

    # Clean True: Decline purge
    monkeypatch.setattr("sys.stdin", io.StringIO("n\n"))
    assert run_intake(clean=True, config_path=toml_file) == 0
    assert bad_file.exists()

    # Clean True: Confirm purge
    monkeypatch.setattr("sys.stdin", io.StringIO("y\n"))
    assert run_intake(clean=True, config_path=toml_file) == 0
    assert not bad_file.exists()
    assert "Purged: bad.py" in capsys.readouterr().out


@pytest.mark.integration
def test_run_intake_unprotected_overwrite_confirmation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify overwrite confirmation prompt for unprotected destinations (covers 453->457)."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)
    doc_file = tmp_path / "docs" / "readme.txt"
    doc_file.parent.mkdir(parents=True)
    doc_file.write_text("old text", encoding="utf-8")

    staged = download_dir / "readme.txt"
    staged.write_text("# Path: docs/readme.txt\nnew text", encoding="utf-8")

    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\ndownload_dir = "download"\n',
        encoding="utf-8",
    )

    # 1. Reject overwrite
    monkeypatch.setattr("sys.stdin", io.StringIO("n\n"))
    assert run_intake(config_path=toml_file) == 0
    assert doc_file.read_text(encoding="utf-8") == "old text"

    # 2. Accept overwrite (covers branch 453->457)
    monkeypatch.setattr("sys.stdin", io.StringIO("y\n"))
    assert run_intake(config_path=toml_file) == 0
    assert "new text" in doc_file.read_text(encoding="utf-8")


@pytest.mark.integration
def test_run_intake_force_mode_variants(tmp_path: Path) -> None:
    """Verify force mode on protected domains (448->457) and unprotected domains (451->457)."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)

    # 1. Protected file (covers 448->457)
    target = tmp_path / "src" / "gda" / "forced.py"
    target.parent.mkdir(parents=True)
    target.write_text("v1", encoding="utf-8")

    staged1 = download_dir / "forced.py"
    staged1.write_text('"""Path: src/gda/forced.py\n"""\nv2', encoding="utf-8")

    # 2. Unprotected file with force=True (covers 451->457)
    unprotected = tmp_path / "docs" / "forced_doc.txt"
    unprotected.parent.mkdir(parents=True)
    unprotected.write_text("doc1", encoding="utf-8")

    staged2 = download_dir / "forced_doc.txt"
    staged2.write_text("# Path: docs/forced_doc.txt\ndoc2", encoding="utf-8")

    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
download_dir = "download"
logs_dir = "logs"
archive_dir = "archive"

[logging]
log_file = "logs/gsi.log"

[code_domains]
protected_domains = ["src"]
""",
        encoding="utf-8",
    )

    assert run_intake(force=True, config_path=toml_file) == 0
    assert "v2" in target.read_text(encoding="utf-8")
    assert "doc2" in unprotected.read_text(encoding="utf-8")
    assert not (tmp_path / "archive").exists()


@pytest.mark.integration
def test_run_intake_force_mode_logs_warning(tmp_path: Path) -> None:
    """Verify --force flag logs an explicit warning mode entry."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)
    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
download_dir = "download"
logs_dir = "logs"
[logging]
log_file = "logs/gsi.log"
""",
        encoding="utf-8",
    )

    status = run_intake(force=True, config_path=toml_file)
    assert status == 0

    log_path = tmp_path / "logs" / "gsi.log"
    assert log_path.exists()
    log_content = log_path.read_text(encoding="utf-8")
    assert "EXECUTION_MODE: FORCE=TRUE" in log_content


@pytest.mark.integration
def test_run_intake_run_target_multi_candidate_loop(tmp_path: Path) -> None:
    """Verify run_target executes across multiple files and loops back (covers 465->431)."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)

    (download_dir / "a.py").write_text('"""Path: src/system/a.py\n"""\n', encoding="utf-8")
    (download_dir / "b.py").write_text('"""Path: src/system/b.py\n"""\n', encoding="utf-8")

    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\ndownload_dir = "download"\n',
        encoding="utf-8",
    )

    with patch("system.gsi.gsi._execute_target", return_value=0) as mock_exec:
        assert run_intake(run_target=True, config_path=toml_file) == 0
        assert mock_exec.call_count == 2


@pytest.mark.integration
def test_run_intake_run_target_failure(tmp_path: Path) -> None:
    """Verify run_target non-zero exit code aborts pipeline execution."""
    download_dir = tmp_path / "download"
    download_dir.mkdir(parents=True)
    staged = download_dir / "fail.py"
    staged.write_text('"""Path: src/system/fail.py\n"""\n', encoding="utf-8")

    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f'[workspace]\nroot = "{tmp_path.as_posix()}"\ndownload_dir = "download"\n',
        encoding="utf-8",
    )

    with patch("system.gsi.gsi._execute_target", return_value=1):
        assert run_intake(run_target=True, config_path=toml_file) == 1


# ==============================================================================
# GROUP 6: CLI Execution & Module Entrypoint
# Note: Verification of main() flags and __name__ == "__main__"
# ==============================================================================


@pytest.mark.unit
def test_main_cli_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main() entrypoint executes with custom config flag."""
    download_dir = tmp_path / "download"
    download_dir.mkdir()
    toml_file = tmp_path / "gsi_conf.toml"
    toml_file.write_text(
        f"""
[workspace]
root = "{tmp_path.as_posix()}"
download_dir = "download"
logs_dir = "logs"
""",
        encoding="utf-8",
    )

    monkeypatch.setattr("sys.argv", ["gsi", "--config", str(toml_file)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


@pytest.mark.unit
def test_gsi_module_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify script execution under runpy as __main__."""
    monkeypatch.setattr("sys.argv", ["gsi", "-h"])
    monkeypatch.delitem(sys.modules, "system.gsi.gsi", raising=False)
    with pytest.raises(SystemExit) as exc:
        runpy.run_module("system.gsi.gsi", run_name="__main__")
    assert exc.value.code == 0
