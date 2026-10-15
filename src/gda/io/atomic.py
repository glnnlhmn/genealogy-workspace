# Name: atomic.py
# Path: src/gda/io/atomic.py

"""Same-directory atomic file staging and replacement engine.

Operational Role:
    Provides context-managed atomic staging to prevent corrupt writes, partial
    payloads, or lock contention during destructive filesystem persistence.
    Stages temporary files via .[filename].[uuid].tmp in the target directory,
    ensuring POSIX and Windows rename atomicity across volumes. Flushes and
    synchronizes buffers via os.fsync() prior to atomic os.replace commit, with
    bounded exponential backoff retries against Windows sharing violations.
"""

from __future__ import annotations

import os
import time
import uuid
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import IO, Any

from gda.core.introspectable import IntrospectableMixin
from gda.io.errors import AtomicWriteError, DirectoryCreationError

__version__ = "0.1.0+build.r6"


class AtomicWriter(IntrospectableMixin):
    """Manager for atomic temporary staging and atomic path replacement."""

    DEFAULT_RETRIES: int = 3
    DEFAULT_BACKOFF_FACTOR: float = 0.05

    @classmethod
    def ensure_directory(cls, directory: Path | str) -> Path:
        """Auto-create parent directory hierarchies if missing.

        Args:
            directory: Target directory path to verify or create.

        Returns:
            Resolved Path object of the ensured directory.

        Raises:
            DirectoryCreationError: If directory creation fails due to OS or permission errors.
        """
        dir_path = Path(directory).resolve()
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as err:
                raise DirectoryCreationError(
                    f"Failed to create directory structure '{dir_path}': {err}"
                ) from err
        return dir_path

    @classmethod
    def replace_with_retry(
        cls,
        source: Path | str,
        destination: Path | str,
        max_retries: int = DEFAULT_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
    ) -> None:
        """Replace target file atomically with retry protection for Windows file locks.

        Args:
            source: Staged temporary file path.
            destination: Final canonical destination file path.
            max_retries: Maximum replacement attempts before raising.
            backoff_factor: Exponential base delay applied between retries.

        Raises:
            AtomicWriteError: If replacement fails after exhausting all retry attempts.
        """
        src = Path(source).resolve()
        dst = Path(destination).resolve()

        if not src.exists():
            raise AtomicWriteError(
                f"Atomic source staging file '{src}' does not exist."
            )

        cls.ensure_directory(dst.parent)

        delay = backoff_factor
        last_error: OSError | None = None

        for attempt in range(1, max_retries + 1):
            try:
                os.replace(src, dst)
                return
            except (OSError, PermissionError) as err:
                last_error = err
                if attempt < max_retries:
                    time.sleep(delay)
                    delay *= 2.0

        raise AtomicWriteError(
            f"Atomic replacement failed for '{dst}' after {max_retries} attempts: {last_error}"
        ) from last_error


@contextmanager
def atomic_write(
    file_path: Path | str,
    mode: str = "w",
    encoding: str | None = "utf-8",
    max_retries: int = AtomicWriter.DEFAULT_RETRIES,
    backoff_factor: float = AtomicWriter.DEFAULT_BACKOFF_FACTOR,
) -> Generator[IO[Any]]:
    """Context manager staging file writes atomically in the destination directory.

    Stages payloads via .[filename].[uuid].tmp, calls flush() and os.fsync() prior to
    committing via os.replace, and cleans up orphaned staging files on unhandled exceptions.

    Args:
        file_path: Destination path for the file.
        mode: Open mode ('w', 'wb', 'a', etc.). Defaults to 'w'.
        encoding: File encoding standard. Defaults to 'utf-8'. Ignored in binary mode.
        max_retries: Retry attempts for Windows file-locking retry protection.
        backoff_factor: Exponential backoff delay factor in seconds.

    Yields:
        Open file stream ready for writing.

    Raises:
        AtomicWriteError: If staging file allocation, syncing, or replacement fails.
        DirectoryCreationError: If parent directory creation fails.
    """
    target = Path(file_path).resolve()
    AtomicWriter.ensure_directory(target.parent)

    token = uuid.uuid4().hex
    temp_name = f".{target.name}.{token}.tmp"
    temp_path = target.parent / temp_name

    open_kwargs: dict[str, Any] = {}
    if "b" not in mode:
        open_kwargs["encoding"] = encoding

    file_handle: IO[Any] | None = None
    try:
        try:
            file_handle = open(temp_path, mode, **open_kwargs)
        except (OSError, PermissionError) as err:
            raise AtomicWriteError(
                f"Failed to open temporary staging file '{temp_path}': {err}"
            ) from err

        yield file_handle

        file_handle.flush()
        try:
            os.fsync(file_handle.fileno())
        except (OSError, ValueError):
            pass
        file_handle.close()
        file_handle = None

        AtomicWriter.replace_with_retry(
            source=temp_path,
            destination=target,
            max_retries=max_retries,
            backoff_factor=backoff_factor,
        )
    except Exception:
        if file_handle is not None and not file_handle.closed:
            try:
                file_handle.close()
            except OSError:
                pass
        if temp_path.exists():
            try:
                temp_path.unlink()
            except OSError:
                pass
        raise


def atomic_write_text(
    target_path: Path | str,
    content: str,
    encoding: str = "utf-8",
    max_retries: int = AtomicWriter.DEFAULT_RETRIES,
    backoff_factor: float = AtomicWriter.DEFAULT_BACKOFF_FACTOR,
) -> Path:
    """Convenience helper to write text content atomically to disk.

    Args:
        target_path: Destination path for writing text.
        content: Verbatim text string to persist.
        encoding: Text encoding standard (defaults to "utf-8").
        max_retries: Retry attempts for Windows file-locking retry protection.
        backoff_factor: Exponential backoff delay factor in seconds.

    Returns:
        Path: Resolved target file path on success.

    Raises:
        AtomicWriteError: If file writing or replacement fails.
    """
    target = Path(target_path).resolve()
    with atomic_write(
        file_path=target,
        mode="w",
        encoding=encoding,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    ) as stream:
        stream.write(content)
    return target


def atomic_write_bytes(
    target_path: Path | str,
    data: bytes,
    max_retries: int = AtomicWriter.DEFAULT_RETRIES,
    backoff_factor: float = AtomicWriter.DEFAULT_BACKOFF_FACTOR,
) -> Path:
    """Convenience helper to write raw binary bytes atomically to disk.

    Args:
        target_path: Destination path for writing bytes.
        data: Verbatim byte sequence to persist.
        max_retries: Retry attempts for Windows file-locking retry protection.
        backoff_factor: Exponential backoff delay factor in seconds.

    Returns:
        Path: Resolved target file path on success.

    Raises:
        AtomicWriteError: If binary file writing or replacement fails.
    """
    target = Path(target_path).resolve()
    with atomic_write(
        file_path=target,
        mode="wb",
        encoding=None,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    ) as stream:
        stream.write(data)
    return target


def atomic_write_stream(
    target_path: Path | str,
    chunks: Iterable[bytes],
    max_retries: int = AtomicWriter.DEFAULT_RETRIES,
    backoff_factor: float = AtomicWriter.DEFAULT_BACKOFF_FACTOR,
) -> Path:
    """Convenience helper to stream chunks of binary data atomically to disk.

    Args:
        target_path: Destination path for streaming chunks.
        chunks: Iterable sequence of byte payloads.
        max_retries: Retry attempts for Windows file-locking retry protection.
        backoff_factor: Exponential backoff delay factor in seconds.

    Returns:
        Path: Resolved target file path on success.

    Raises:
        AtomicWriteError: If streaming write or replacement fails.
    """
    target = Path(target_path).resolve()
    with atomic_write(
        file_path=target,
        mode="wb",
        encoding=None,
        max_retries=max_retries,
        backoff_factor=backoff_factor,
    ) as stream:
        for chunk in chunks:
            stream.write(chunk)
    return target
