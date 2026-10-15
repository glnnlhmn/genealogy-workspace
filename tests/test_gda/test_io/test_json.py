# Name: test_json.py
# Path: tests/test_gda/test_io/test_json.py

"""Unit and integration test suite for gda.io.json.

Operational Role:
    Verifies deterministic JSON decoding, encoding, Safe Backup triggering,
    formatting invariants, and typed error mappings with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract verification per condition.
    - Fully decorated: Standard pytest markers (@pytest.mark.unit, @pytest.mark.integration).
    - Dependencies: tmp_path hermetic sandboxing and monkeypatched error injections.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from gda.io.backup import GDABackupManager
from gda.io.errors import FileReadError, SerializationError
from gda.io.json import GDAJsonIO

__version__ = "0.1.0+build.r1"

# ==============================================================================
# GROUP 1: JSON Reading & Deserialization
# Note: Verification of file loading, missing path, and syntax decoding errors
# ==============================================================================


@pytest.mark.integration
def test_read_loads_valid_json_payload(tmp_path: Path) -> None:
    """Verify read loads and parses valid JSON into native data structures."""
    target = tmp_path / "data.json"
    target.write_text('{"name": "Müller", "count": 10}\n', encoding="utf-8")

    result = GDAJsonIO.read(target)
    assert result == {"name": "Müller", "count": 10}


@pytest.mark.unit
def test_read_raises_file_read_error_when_missing(tmp_path: Path) -> None:
    """Verify read raises FileReadError when target file does not exist."""
    missing = tmp_path / "nonexistent.json"
    with pytest.raises(FileReadError, match="Target JSON file .* does not exist"):
        GDAJsonIO.read(missing)


@pytest.mark.unit
def test_read_raises_file_read_error_when_target_is_directory(
    tmp_path: Path,
) -> None:
    """Verify read raises FileReadError when target path points to a directory."""
    directory = tmp_path / "a_directory"
    directory.mkdir()
    with pytest.raises(FileReadError, match="Target JSON path .* is a directory"):
        GDAJsonIO.read(directory)


@pytest.mark.unit
def test_read_raises_file_read_error_on_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify read raises FileReadError when filesystem read encounters OSError."""
    target = tmp_path / "unreadable.json"
    target.write_text("{}", encoding="utf-8")

    def mock_read_text(self: Path, *args: object, **kwargs: object) -> str:
        raise OSError("I/O device error")

    monkeypatch.setattr(Path, "read_text", mock_read_text)
    with pytest.raises(FileReadError, match="Failed to read JSON file"):
        GDAJsonIO.read(target)


@pytest.mark.integration
def test_read_raises_serialization_error_on_malformed_json(
    tmp_path: Path,
) -> None:
    """Verify read raises SerializationError on malformed JSON syntax."""
    target = tmp_path / "malformed.json"
    target.write_text('{"unclosed": "brace"', encoding="utf-8")

    with pytest.raises(SerializationError, match="Failed to decode JSON"):
        GDAJsonIO.read(target)


# ==============================================================================
# GROUP 2: JSON Writing, Invariants & Safe Backups
# Note: Verification of deterministic output, backups, and serialization failures
# ==============================================================================


@pytest.mark.integration
def test_write_persists_deterministic_json_with_trailing_newline(
    tmp_path: Path,
) -> None:
    """Verify write outputs 2-space indented, sorted, unescaped Unicode JSON with trailing newline."""
    target = tmp_path / "nested" / "output.json"
    payload = {"z_key": "Grüße", "a_key": 1}

    result = GDAJsonIO.write(target, payload)

    assert result == target.resolve()
    assert target.exists()

    expected_text = '{\n  "a_key": 1,\n  "z_key": "Grüße"\n}\n'
    assert target.read_text(encoding="utf-8") == expected_text


@pytest.mark.unit
def test_write_raises_serialization_error_on_non_serializable_object(
    tmp_path: Path,
) -> None:
    """Verify write raises SerializationError when payload contains non-serializable objects."""
    target = tmp_path / "fail.json"
    non_serializable = {"unsupported": object()}

    with pytest.raises(SerializationError, match="Failed to serialize data to JSON"):
        GDAJsonIO.write(target, non_serializable)


@pytest.mark.integration
def test_write_creates_safe_backup_when_flag_enabled_and_file_exists(
    tmp_path: Path,
) -> None:
    """Verify write triggers Safe Backup snapshot before overwriting existing file."""
    target = tmp_path / "record.json"
    target.write_text('{"version": 1}\n', encoding="utf-8")

    custom_backup_dir = tmp_path / "my_backups"
    payload = {"version": 2}

    GDAJsonIO.write(
        target,
        payload,
        create_backup=True,
        backup_dir=custom_backup_dir,
    )

    assert target.read_text(encoding="utf-8") == '{\n  "version": 2\n}\n'
    backups = GDABackupManager.list_backups(target, backup_dir=custom_backup_dir)
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == '{"version": 1}\n'


@pytest.mark.integration
def test_write_skips_safe_backup_when_target_does_not_exist(
    tmp_path: Path,
) -> None:
    """Verify write does not attempt backup creation when target is newly provisioned."""
    target = tmp_path / "brand_new.json"
    payload = {"status": "fresh"}

    GDAJsonIO.write(target, payload, create_backup=True)

    assert target.exists()
    assert not (tmp_path / "backups").exists()


# ==============================================================================
# GROUP 3: Introspectable Contract
# Note: Verify help discovery contract via IntrospectableMixin
# ==============================================================================


@pytest.mark.unit
def test_json_io_inherits_and_exposes_introspectable_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify GDAJsonIO inherits IntrospectableMixin and executes .help()."""
    return_value = GDAJsonIO.help()
    captured = capsys.readouterr()
    output = return_value if isinstance(return_value, str) else captured.out

    assert "GDAJsonIO" in output
    assert "read" in output
    assert "write" in output
