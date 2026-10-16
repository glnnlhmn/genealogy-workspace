# Name: hashes.py
# Path: src/gda/util/hashes.py

"""Pure stateless hashing utilities and checksum validators.

Operational Role:
    Provides deterministic SHA-256 calculation for strings, raw bytes,
    and streaming disk files alongside hexadecimal validation matching
    schemas/defs/_shared_defs.schema.json.

Note:
    PRERELEASE: Module is under active development (version 0.0.1+build.1).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from gda.types.primitives import SHA256_PATTERN, SHA256_REGEX

__version__ = "0.0.1+build.1"

__all__ = [
    "SHA256_PATTERN",
    "SHA256_REGEX",
    "is_valid_sha256",
    "sha256_bytes",
    "sha256_file",
    "sha256_text",
]


def sha256_bytes(data: bytes) -> str:
    """Calculate the lowercase hexadecimal SHA-256 hash of a bytes sequence.

    Args:
        data: Raw binary bytes to hash.

    Returns:
        64-character lowercase hexadecimal hash digest.

    Raises:
        TypeError: If data is not an instance of bytes.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError(f"Expected bytes or bytearray, got {type(data).__name__}.")
    return hashlib.sha256(data).hexdigest().lower()


def sha256_text(text: str, encoding: str = "utf-8") -> str:
    """Calculate the lowercase hexadecimal SHA-256 hash of a string.

    Args:
        text: String content to encode and hash.
        encoding: Character encoding to apply before hashing. Defaults to 'utf-8'.

    Returns:
        64-character lowercase hexadecimal hash digest.

    Raises:
        TypeError: If text is not an instance of str.
    """
    if not isinstance(text, str):
        raise TypeError(f"Expected str, got {type(text).__name__}.")
    return sha256_bytes(text.encode(encoding))


def sha256_file(file_path: Path | str, chunk_size: int = 65536) -> str:
    """Calculate the lowercase hexadecimal SHA-256 hash of a file using chunked streaming.

    Args:
        file_path: Filesystem path to the target file.
        chunk_size: Size in bytes of sequential read chunks. Defaults to 64 KiB.

    Returns:
        64-character lowercase hexadecimal hash digest.

    Raises:
        FileNotFoundError: If the target file does not exist.
        IsADirectoryError: If the target path points to a directory.
        ValueError: If chunk_size is less than 1.
    """
    if chunk_size < 1:
        raise ValueError(f"chunk_size must be greater than zero, got {chunk_size}.")

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Target file does not exist: {path}")
    if path.is_dir():
        raise IsADirectoryError(f"Target path is a directory, not a file: {path}")

    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest().lower()


def is_valid_sha256(val: str | None) -> bool:
    """Verify whether a string conforms to canonical 64-character lowercase hex SHA-256.

    Args:
        val: Candidate hash string to inspect.

    Returns:
        True if string is a valid lowercase SHA-256 hexadecimal digest; False otherwise.
    """
    if not val or not isinstance(val, str):
        return False
    return bool(SHA256_REGEX.match(val.strip()))
