"""Path: src/gda/core/hashes.py

Stateless SHA-256 cryptographic hashing and digest validation utilities.

Operational Role:
    Provides Tier 0 pure hashing primitives for UTF-8 strings, binary buffers
    (bytes and bytearray), and streaming disk files, alongside canonical
    64-character lowercase SHA-256 hex digest validation.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from gda.core.types import SHA256_REGEX, is_strict_int

__version__ = "1.0.0+build.2"

__all__ = [
    "is_valid_sha256",
    "sha256_bytes",
    "sha256_file",
    "sha256_text",
]


def sha256_text(text: str) -> str:
    """Compute the lowercase hexadecimal SHA-256 digest of a UTF-8 string.

    Args:
        text: Input string to encode as UTF-8 and hash.

    Returns:
        A 64-character lowercase hexadecimal SHA-256 digest.

    Raises:
        TypeError: If text is not a str instance.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_bytes(data: bytes | bytearray) -> str:
    """Compute the lowercase hexadecimal SHA-256 digest of a binary buffer.

    Args:
        data: Input bytes or bytearray payload.

    Returns:
        A 64-character lowercase hexadecimal SHA-256 digest.

    Raises:
        TypeError: If data is not a bytes or bytearray instance.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"Expected bytes or bytearray, got {type(data).__name__}.")
    return hashlib.sha256(data).hexdigest()


def sha256_file(file_path: str | Path, chunk_size: int = 65536) -> str:
    """Stream a file from disk and compute its lowercase SHA-256 hex digest.

    Args:
        file_path: Path to the target file.
        chunk_size: Positive integer read buffer size in bytes (default 64 KiB).

    Returns:
        A 64-character lowercase hexadecimal SHA-256 digest.

    Raises:
        TypeError: If chunk_size is not a strict int (rejects bool/float/str).
        ValueError: If chunk_size is less than 1.
        FileNotFoundError: If file_path does not exist.
        IsADirectoryError: If file_path points to a directory.
    """
    # Guard chunk_size type and bounds before touching the filesystem.
    if not is_strict_int(chunk_size):
        raise TypeError(f"chunk_size must be an int, got {type(chunk_size).__name__}.")
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be greater than zero, got {chunk_size}.")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Target file does not exist: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Target path is a directory: {path}")

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def is_valid_sha256(value: Any) -> bool:
    """Verify whether a value is a canonical 64-character lowercase SHA-256 hex string.

    Leading and trailing whitespace is stripped prior to regex validation.

    Args:
        value: Arbitrary candidate value to check.

    Returns:
        True if value is a string matching SHA256_REGEX after stripping,
        otherwise False.
    """
    if not isinstance(value, str):
        return False
    return SHA256_REGEX.match(value.strip()) is not None
