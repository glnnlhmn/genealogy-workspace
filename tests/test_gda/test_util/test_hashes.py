# Name: test_hashes.py
# Path: tests/test_gda/test_util/test_hashes.py

"""Comprehensive unit test suite for gda.util.hashes.

Operational Role:
    Verifies pure stateless SHA-256 calculation for strings, bytes, and streaming
    files, along with boundary checks, invalid parameter handling, and regex validation.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Decorated with @pytest.mark.unit and @pytest.mark.smoke.
    - Dependencies: In-memory evaluation and hermetic tmp_path sandboxing.

Note:
    PRERELEASE: Test suite is under active development (version 0.0.1+build.2).
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gda.util.hashes as uhash

__version__ = "0.0.1+build.2"

# ==============================================================================
# GROUP 1: In-Memory SHA-256 Calculation (Bytes & Text)
# Note: Verification against canonical known hash vectors
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_sha256_text_matches_known_digest() -> None:
    """Verify sha256_text matches the canonical NIST digest for known strings."""
    # SHA-256 of empty string:
    empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert uhash.sha256_text("") == empty_hash

    # SHA-256 of "hello world":
    hello_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert uhash.sha256_text("hello world") == hello_hash


@pytest.mark.unit
def test_sha256_text_raises_type_error_for_non_string() -> None:
    """Verify sha256_text raises TypeError when passed non-string arguments."""
    with pytest.raises(TypeError, match="Expected str"):
        uhash.sha256_text(12345)  # type: ignore[arg-type]


@pytest.mark.unit
@pytest.mark.smoke
def test_sha256_bytes_matches_known_digest() -> None:
    """Verify sha256_bytes matches the canonical digest for raw binary payloads."""
    payload = b"genealogy data archive"
    expected = "07de635b58302d999867491f0ba01ef3fdfae57af08e7297f61fc58ec1793bf4"
    assert uhash.sha256_bytes(payload) == expected


@pytest.mark.unit
def test_sha256_bytes_raises_type_error_for_non_bytes() -> None:
    """Verify sha256_bytes raises TypeError when passed non-bytes arguments."""
    with pytest.raises(TypeError, match="Expected bytes or bytearray"):
        uhash.sha256_bytes("string_payload")  # type: ignore[arg-type]


# ==============================================================================
# GROUP 2: File Streaming SHA-256 Calculation
# Note: Chunked reading, missing file handling, and directory boundary checks
# ==============================================================================


@pytest.mark.unit
def test_sha256_file_matches_text_hash(tmp_path: Path) -> None:
    """Verify sha256_file yields the exact same hash as sha256_text for file contents."""
    sample_file = tmp_path / "sample.txt"
    content = "Streaming file content verification payload."
    sample_file.write_text(content, encoding="utf-8")

    assert uhash.sha256_file(sample_file) == uhash.sha256_text(content)


@pytest.mark.unit
def test_sha256_file_handles_custom_chunk_size(tmp_path: Path) -> None:
    """Verify sha256_file reads correctly across multiple small chunks."""
    sample_file = tmp_path / "chunked.txt"
    sample_file.write_bytes(b"A" * 1024)

    digest = uhash.sha256_file(sample_file, chunk_size=128)
    assert digest == uhash.sha256_bytes(b"A" * 1024)


@pytest.mark.unit
def test_sha256_file_raises_value_error_for_invalid_chunk_size(tmp_path: Path) -> None:
    """Verify sha256_file raises ValueError when chunk_size is less than 1."""
    sample_file = tmp_path / "sample.txt"
    sample_file.write_text("data", encoding="utf-8")

    with pytest.raises(ValueError, match="chunk_size must be greater than zero"):
        uhash.sha256_file(sample_file, chunk_size=0)


@pytest.mark.unit
def test_sha256_file_raises_file_not_found(tmp_path: Path) -> None:
    """Verify sha256_file raises FileNotFoundError for non-existent paths."""
    missing_path = tmp_path / "non_existent.dat"
    with pytest.raises(FileNotFoundError, match="Target file does not exist"):
        uhash.sha256_file(missing_path)


@pytest.mark.unit
def test_sha256_file_raises_is_a_directory_error(tmp_path: Path) -> None:
    """Verify sha256_file raises IsADirectoryError when passed a directory path."""
    with pytest.raises(IsADirectoryError, match="Target path is a directory"):
        uhash.sha256_file(tmp_path)


# ==============================================================================
# GROUP 3: SHA-256 Validation Predicates (is_valid_sha256)
# Note: Lowercase hex compliance and rejection boundaries
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
def test_is_valid_sha256_accepts_valid_lowercase_digest() -> None:
    """Verify is_valid_sha256 returns True for valid 64-character lowercase digests."""
    valid_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    assert uhash.is_valid_sha256(valid_hash) is True
    assert uhash.is_valid_sha256(f"  {valid_hash}  ") is True


@pytest.mark.unit
def test_is_valid_sha256_rejects_uppercase_digest() -> None:
    """Verify is_valid_sha256 strictly rejects uppercase hex characters."""
    upper_hash = "B94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9"
    assert uhash.is_valid_sha256(upper_hash) is False


@pytest.mark.unit
def test_is_valid_sha256_rejects_invalid_lengths_and_non_hex() -> None:
    """Verify is_valid_sha256 returns False for wrong length or non-hex characters."""
    assert uhash.is_valid_sha256("b94d27b9934d3e08a52e52d7da7dabfac484efe3") is False
    assert uhash.is_valid_sha256("g" * 64) is False
    assert uhash.is_valid_sha256(None) is False
    assert uhash.is_valid_sha256("") is False
    assert uhash.is_valid_sha256(12345) is False  # type: ignore[arg-type]
