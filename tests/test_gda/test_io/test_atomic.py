# Name: test_atomic.py
# Path: tests/test_gda/test_io/test_atomic.py

"""Unit and integration test suite for gda.io.atomic.

Operational Role:
    Verifies same-directory atomic staging, parent directory auto-creation,
    buffer flushing with os.fsync(), Windows lock retry mechanics,
    exception-triggered rollback and cleanup, and text/bytes/stream convenience
    helpers with 100% statement and branch coverage.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification of staging, rollback, retry, streaming, and introspection.
    - Fully decorated: Standard pytest markers (@pytest.mark.unit, @pytest.mark.integration).
    - Dependencies: tmp_path hermetic sandboxing and monkeypatched error injections.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from gda.io.atomic import (
    AtomicWriter,
    atomic_write,
    atomic_write_bytes,
    atomic_write_stream,
    atomic_write_text,
)
from gda.io.errors import AtomicWriteError, DirectoryCreationError

__version__ = "0.1.0+build.r9"

# ==============================================================================
# GROUP 1: Parent Directory Auto-Creation
# Note: Verification of directory bootstrapping and permission failure handling
# ==============================================================================


@pytest.mark.unit
def test_ensure_directory_creates_missing_hierarchy(tmp_path: Path) -> None:
    """Verify missing nested parent directories are automatically created."""
    deep_path = tmp_path / "deep" / "nested" / "target"
    result = AtomicWriter.ensure_directory(deep_path)
    assert result.is_dir()
    assert result == deep_path.resolve()


@pytest.mark.unit
def test_ensure_directory_idempotent_on_existing_dir(tmp_path: Path) -> None:
    """Verify calling ensure_directory on existing paths succeeds cleanly."""
    existing_dir = tmp_path / "already_exists"
    existing_dir.mkdir(parents=True)
    result = AtomicWriter.ensure_directory(existing_dir)
    assert result == existing_dir.resolve()


@pytest.mark.unit
def test_ensure_directory_raises_on_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify DirectoryCreationError is raised when mkdir raises OSError."""

    def mock_mkdir(*args: object, **kwargs: object) -> None:
        raise OSError("Access denied")

    monkeypatch.setattr(Path, "mkdir", mock_mkdir)
    with pytest.raises(
        DirectoryCreationError, match="Failed to create directory structure"
    ):
        AtomicWriter.ensure_directory(tmp_path / "denied_dir")


# ==============================================================================
# GROUP 2: Atomic File Replacement & Retry Logic
# Note: Verification of atomic rename, missing source, and retry-with-backoff
# ==============================================================================


@pytest.mark.unit
def test_replace_with_retry_raises_when_source_missing(tmp_path: Path) -> None:
    """Verify AtomicWriteError is raised if the source staging file does not exist."""
    missing_src = tmp_path / "missing_staged.tmp"
    dst = tmp_path / "final.txt"
    with pytest.raises(
        AtomicWriteError, match="Atomic source staging file .* does not exist"
    ):
        AtomicWriter.replace_with_retry(missing_src, dst)


@pytest.mark.integration
def test_replace_with_retry_succeeds_immediately(tmp_path: Path) -> None:
    """Verify clean single-pass replacement succeeds when destination is unlocked."""
    src = tmp_path / "temp_file.tmp"
    dst = tmp_path / "final_dest.txt"
    src.write_text("initial payload", encoding="utf-8")

    AtomicWriter.replace_with_retry(src, dst)
    assert not src.exists()
    assert dst.exists()
    assert dst.read_text(encoding="utf-8") == "initial payload"


@pytest.mark.unit
def test_replace_with_retry_retries_and_succeeds(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify replace_with_retry backs off and recovers after multiple transient OSErrors."""
    src = tmp_path / "temp_file.tmp"
    dst = tmp_path / "final_dest.txt"
    src.write_text("retry payload", encoding="utf-8")

    attempts = 0

    def mock_replace(s: Path | str, d: Path | str) -> None:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise OSError("WinError 32: Sharing violation")
        Path(d).write_text(Path(s).read_text(encoding="utf-8"), encoding="utf-8")
        Path(s).unlink()

    monkeypatch.setattr("os.replace", mock_replace)
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    AtomicWriter.replace_with_retry(src, dst, max_retries=4, backoff_factor=0.01)
    assert attempts == 3
    assert sleep_mock.call_count == 2
    assert dst.read_text(encoding="utf-8") == "retry payload"


@pytest.mark.unit
def test_replace_with_retry_single_retry_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify replace_with_retry recovers on second attempt with exactly one retry sleep."""
    src = tmp_path / "temp_file_single.tmp"
    dst = tmp_path / "final_dest_single.txt"
    src.write_text("retry single", encoding="utf-8")

    attempts = 0

    def mock_replace(s: Path | str, d: Path | str) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise PermissionError("Transient file lock")
        Path(d).write_text(Path(s).read_text(encoding="utf-8"), encoding="utf-8")
        Path(s).unlink()

    monkeypatch.setattr("os.replace", mock_replace)
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    AtomicWriter.replace_with_retry(src, dst, max_retries=2, backoff_factor=0.01)
    assert attempts == 2
    assert sleep_mock.call_count == 1
    assert dst.read_text(encoding="utf-8") == "retry single"


@pytest.mark.unit
def test_replace_with_retry_exhausts_and_raises(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify AtomicWriteError is raised when replacement attempts are exhausted."""
    src = tmp_path / "temp_file.tmp"
    dst = tmp_path / "final_dest.txt"
    src.write_text("payload", encoding="utf-8")

    def mock_replace(s: Path | str, d: Path | str) -> None:
        raise OSError("Locked forever")

    monkeypatch.setattr("os.replace", mock_replace)
    monkeypatch.setattr("time.sleep", lambda _: None)

    with pytest.raises(
        AtomicWriteError, match="Atomic replacement failed .* after 3 attempts"
    ):
        AtomicWriter.replace_with_retry(src, dst, max_retries=3, backoff_factor=0.001)


@pytest.mark.unit
def test_replace_with_retry_exhausts_on_first_attempt(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify replace_with_retry raises on max_retries=1 without invoking sleep."""
    src = tmp_path / "temp_file_single_fail.tmp"
    dst = tmp_path / "final_dest_single_fail.txt"
    src.write_text("payload", encoding="utf-8")

    def mock_replace(s: Path | str, d: Path | str) -> None:
        raise OSError("Immediate lock failure")

    monkeypatch.setattr("os.replace", mock_replace)
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    with pytest.raises(
        AtomicWriteError, match="Atomic replacement failed .* after 1 attempts"
    ):
        AtomicWriter.replace_with_retry(src, dst, max_retries=1, backoff_factor=0.01)

    assert sleep_mock.call_count == 0


# ==============================================================================
# GROUP 3: atomic_write Context Manager Lifecycle
# Note: Verification of staging location, fsync, cleanup on failure, and success write
# ==============================================================================


@pytest.mark.integration
def test_atomic_write_stages_in_same_directory(tmp_path: Path) -> None:
    """Verify atomic_write creates staging temp file in the same parent directory."""
    target = tmp_path / "sub" / "output.json"
    with atomic_write(target) as stream:
        staged_files = list((tmp_path / "sub").glob(".*.tmp"))
        assert len(staged_files) == 1
        assert staged_files[0].name.startswith(".output.json.")
        assert staged_files[0].name.endswith(".tmp")
        stream.write('{"status": "ok"}')

    assert target.exists()
    assert target.read_text(encoding="utf-8") == '{"status": "ok"}'
    assert not list((tmp_path / "sub").glob(".*.tmp"))


@pytest.mark.unit
def test_atomic_write_raises_on_open_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify AtomicWriteError is raised if opening the temporary staging file fails."""

    def mock_open(*args: object, **kwargs: object) -> object:
        raise OSError("Permission denied")

    monkeypatch.setattr("builtins.open", mock_open)
    with pytest.raises(AtomicWriteError, match="Failed to open temporary staging file"):
        with atomic_write(tmp_path / "target.txt"):
            pass


@pytest.mark.integration
def test_atomic_write_cleans_up_on_block_exception(tmp_path: Path) -> None:
    """Verify atomic_write closes stream and deletes staging file on inner block error."""
    target = tmp_path / "failed_output.txt"

    with pytest.raises(ValueError, match="Synthetic failure inside write block"):
        with atomic_write(target) as stream:
            stream.write("partial text")
            raise ValueError("Synthetic failure inside write block")

    assert not target.exists()
    assert not list(tmp_path.glob(".*.tmp"))


@pytest.mark.integration
def test_atomic_write_handles_fsync_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify atomic_write succeeds even if os.fsync raises an expected OSError."""
    target = tmp_path / "fsync_test.txt"

    def mock_fsync(fd: int) -> None:
        raise OSError("Invalid argument on non-disk device")

    monkeypatch.setattr(os, "fsync", mock_fsync)
    with atomic_write(target) as stream:
        stream.write("fsync payload")

    assert target.exists()
    assert target.read_text(encoding="utf-8") == "fsync payload"


@pytest.mark.integration
def test_atomic_write_cleans_up_and_ignores_unlink_and_close_os_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify atomic_write suppresses secondary OSError during failure cleanup."""
    target = tmp_path / "target_suppress.txt"

    original_unlink = Path.unlink

    def mock_unlink(self: Path, *args: object, **kwargs: object) -> None:
        if self.name.startswith(".target_suppress.txt."):
            raise OSError("Access denied during cleanup")
        original_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", mock_unlink)

    with pytest.raises(RuntimeError, match="Primary error"):
        with atomic_write(target) as stream:
            stream.write("data")
            raise RuntimeError("Primary error")


@pytest.mark.integration
def test_atomic_write_suppresses_close_os_error_during_cleanup(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Verify atomic_write suppresses OSError when closing stream during exception unwinding."""
    target = tmp_path / "target_close_fail.txt"

    class FailingCloseIO:
        def __init__(self, raw: object) -> None:
            self._raw = raw
            self.closed = False

        def write(self, data: str) -> int:
            return self._raw.write(data)  # type: ignore[attr-defined]

        def flush(self) -> None:
            self._raw.flush()  # type: ignore[attr-defined]

        def fileno(self) -> int:
            return self._raw.fileno()  # type: ignore[attr-defined]

        def close(self) -> None:
            self.closed = True
            try:
                self._raw.close()  # type: ignore[attr-defined]
            finally:
                raise OSError("Synthetic close error after releasing OS lock")

    real_open = open

    def mock_open(*args: object, **kwargs: object) -> object:
        handle = real_open(*args, **kwargs)  # type: ignore[arg-type]
        return FailingCloseIO(handle)

    monkeypatch.setattr("builtins.open", mock_open)

    with pytest.raises(RuntimeError, match="Block failure"):
        with atomic_write(target) as stream:
            stream.write("testing close failure branch")
            raise RuntimeError("Block failure")

    assert not target.exists()
    assert not list(tmp_path.glob(".*.tmp"))


# ==============================================================================
# GROUP 4: Convenience Helpers (Text, Bytes & Streaming)
# Note: Verification of atomic_write_text, atomic_write_bytes, and atomic_write_stream
# ==============================================================================


@pytest.mark.integration
def test_atomic_write_text_persists_utf8_content(tmp_path: Path) -> None:
    """Verify atomic_write_text writes UTF-8 string cleanly to target."""
    dest = tmp_path / "nested" / "sample.txt"
    content = "Genealogy Archive Record: Müller, £100, 1850"
    result = atomic_write_text(dest, content, encoding="utf-8")

    assert result == dest.resolve()
    assert dest.exists()
    assert dest.read_text(encoding="utf-8") == content


@pytest.mark.integration
def test_atomic_write_bytes_persists_binary_data(tmp_path: Path) -> None:
    """Verify atomic_write_bytes persists raw byte payload without corruption."""
    dest = tmp_path / "binary" / "sample.bin"
    binary_data = b"\x00\xff\xfe\xfd\x10\x20\x30"
    result = atomic_write_bytes(dest, binary_data)

    assert result == dest.resolve()
    assert dest.exists()
    assert dest.read_bytes() == binary_data


@pytest.mark.integration
def test_atomic_write_stream_persists_chunked_data(tmp_path: Path) -> None:
    """Verify atomic_write_stream persists chunked iterable payloads seamlessly."""
    dest = tmp_path / "streamed" / "output.dat"
    chunks = [b"chunk_1_", b"chunk_2_", b"chunk_3"]
    result = atomic_write_stream(dest, iter(chunks))

    assert result == dest.resolve()
    assert dest.exists()
    assert dest.read_bytes() == b"chunk_1_chunk_2_chunk_3"


# ==============================================================================
# GROUP 5: Introspectable Contract
# Note: Verify help discovery contract via IntrospectableMixin
# ==============================================================================


@pytest.mark.unit
def test_atomic_writer_inherits_and_exposes_introspectable_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Verify AtomicWriter inherits IntrospectableMixin and executes .help()."""
    return_value = AtomicWriter.help()
    captured = capsys.readouterr()
    output = return_value if isinstance(return_value, str) else captured.out

    assert "AtomicWriter" in output
    assert "replace_with_retry" in output
