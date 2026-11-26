"""Path: tests/test_gda/test_core/test_core_hashes.py

Comprehensive unit, regression, integration, and property-based test suite
for gda.core.hashes.

Operational Role:
    Verifies pure stateless SHA-256 calculation for strings, bytes, bytearray
    buffers, and streaming disk files alongside chunk-size invariance,
    boundary/error handling, symlink/OS error resilience, hexadecimal
    validation predicates, and strict chunk_size guards.

Test Structure & Protocol:
    - Atomized & parametrized tests: 1:1 behavioral contract mapping.
    - Fully decorated: 5-marker taxonomy (smoke, unit, regression, integration, integrity).
    - Property-based: Hypothesis strategies imported from test_core/strategies.py.
    - Dependencies: In-memory evaluation and hermetic tmp_path / TemporaryDirectory sandboxing.
"""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from tests.test_gda.test_core.strategies import binary_and_chunk_size, bool_or_non_int

import gda.core.hashes as uhash

__version__ = "1.0.0+build.6"


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke contract check verifying gda.core.hashes public exports.
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.unit
def test_hashes_exposes_expected_public_interface() -> None:
    """Verify gda.core.hashes exports its canonical hashing and validation functions."""
    expected_exports = {
        "is_valid_sha256",
        "sha256_bytes",
        "sha256_file",
        "sha256_text",
    }
    assert set(uhash.__all__) == expected_exports


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Canonical digests for text, bytes, bytearray, and hex validation predicates.
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_text", "expected_digest"),
    [
        ("", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        ("hello world", "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"),
    ],
)
def test_sha256_text_matches_known_digest(raw_text: str, expected_digest: str) -> None:
    """Verify sha256_text matches the canonical SHA-256 digest for known strings."""
    assert uhash.sha256_text(raw_text) == expected_digest


@pytest.mark.unit
def test_sha256_bytes_matches_known_digest() -> None:
    """Verify sha256_bytes matches the canonical digest for raw binary payloads."""
    payload = b"genealogy data archive"
    expected = "07de635b58302d999867491f0ba01ef3fdfae57af08e7297f61fc58ec1793bf4"
    assert uhash.sha256_bytes(payload) == expected


@pytest.mark.unit
def test_sha256_bytes_accepts_bytearray_identically_to_bytes() -> None:
    """Verify sha256_bytes hashes bytearray payloads identically to bytes."""
    raw = b"mutable archive buffer"
    mutable = bytearray(raw)
    assert uhash.sha256_bytes(mutable) == uhash.sha256_bytes(raw)


@pytest.mark.unit
@pytest.mark.parametrize("padded", [True, False])
def test_is_valid_sha256_accepts_valid_lowercase_digest(padded: bool) -> None:
    """Verify is_valid_sha256 returns True for valid 64-char lowercase digests."""
    valid_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    candidate = f" {valid_hash} " if padded else valid_hash
    assert uhash.is_valid_sha256(candidate) is True


# ==============================================================================
# GROUP 3: Edge Cases & Boundary Conditions
# Note: Zero and negative chunk sizes.
# ==============================================================================


@pytest.mark.regression
@pytest.mark.parametrize("bad_chunk_size", [0, -1, -65536])
def test_sha256_file_rejects_zero_or_negative_chunk_size(
    tmp_path: Path,
    bad_chunk_size: int,
) -> None:
    """Verify sha256_file raises ValueError when chunk_size is zero or negative."""
    target = tmp_path / "sample.txt"
    target.write_text("data", encoding="utf-8")
    with pytest.raises(ValueError, match="chunk_size must be greater than zero"):
        uhash.sha256_file(target, chunk_size=bad_chunk_size)


# ==============================================================================
# GROUP 4: Error Handling & Validation Failures
# Note: Type guards, missing/directory targets, and strict chunk_size checks.
# ==============================================================================


@pytest.mark.regression
def test_sha256_text_raises_type_error_for_non_string() -> None:
    """Verify sha256_text raises TypeError when passed non-string arguments."""
    with pytest.raises(TypeError, match="Expected str"):
        uhash.sha256_text(12345)  # type: ignore[arg-type]


@pytest.mark.regression
def test_sha256_bytes_raises_type_error_for_non_bytes() -> None:
    """Verify sha256_bytes raises TypeError when passed non-bytes/bytearray arguments."""
    with pytest.raises(TypeError, match="Expected bytes or bytearray"):
        uhash.sha256_bytes("string_payload")  # type: ignore[arg-type]


@pytest.mark.regression
def test_sha256_file_raises_file_not_found(tmp_path: Path) -> None:
    """Verify sha256_file raises FileNotFoundError for non-existent paths."""
    missing_path = tmp_path / "non_existent.dat"
    with pytest.raises(FileNotFoundError, match="Target file does not exist"):
        uhash.sha256_file(missing_path)


@pytest.mark.regression
def test_sha256_file_raises_is_a_directory_error(tmp_path: Path) -> None:
    """Verify sha256_file raises IsADirectoryError when passed a directory path."""
    with pytest.raises(IsADirectoryError, match="Target path is a directory"):
        uhash.sha256_file(tmp_path)


@pytest.mark.regression
@pytest.mark.parametrize("bool_chunk", [True, False])
def test_sha256_file_rejects_boolean_chunk_size(
    tmp_path: Path,
    bool_chunk: bool,
) -> None:
    """Verify sha256_file rejects bool chunk_size via strict int guard."""
    target = tmp_path / "sample.txt"
    target.write_bytes(b"payload")
    with pytest.raises((TypeError, ValueError)):
        uhash.sha256_file(target, chunk_size=bool_chunk)


@pytest.mark.regression
@given(bad_chunk=bool_or_non_int())
def test_sha256_file_rejects_non_int_chunk_size_property(bad_chunk: Any) -> None:
    """Verify sha256_file raises TypeError or ValueError for non-int chunk_size."""
    if isinstance(bad_chunk, int) and not isinstance(bad_chunk, bool):
        return
    with pytest.raises((TypeError, ValueError)):
        uhash.sha256_file(Path("unused.bin"), chunk_size=bad_chunk)


@pytest.mark.regression
@pytest.mark.parametrize(
    "invalid_val",
    [
        "B94D27B9934D3E08A52E52D7DA7DABFAC484EFE37A5380EE9088F7ACE2EFCDE9",
        "b94d27b9934d3e08a52e52d7da7dabfac484efe3",
        "g" * 64,
        None,
        "",
        12345,
    ],
)
def test_is_valid_sha256_rejects_invalid_inputs(invalid_val: Any) -> None:
    """Verify is_valid_sha256 returns False for uppercase, wrong length, non-hex, or non-str."""
    assert uhash.is_valid_sha256(invalid_val) is False


# ==============================================================================
# GROUP 5: Filesystem, CLI & Integration
# Note: Streaming file I/O, symlinks, and OS read errors in hermetic tmp_path.
# ==============================================================================


@pytest.mark.integration
def test_sha256_file_matches_text_hash(tmp_path: Path) -> None:
    """Verify sha256_file yields the exact same hash as sha256_text for file contents."""
    sample_file = tmp_path / "sample.txt"
    content = "Streaming file content verification payload."
    sample_file.write_text(content, encoding="utf-8")
    assert uhash.sha256_file(sample_file) == uhash.sha256_text(content)


@pytest.mark.integration
def test_sha256_file_handles_custom_chunk_size(tmp_path: Path) -> None:
    """Verify sha256_file reads correctly across multiple small chunks."""
    sample_file = tmp_path / "chunked.txt"
    sample_file.write_bytes(b"A" * 1024)
    assert uhash.sha256_file(sample_file, chunk_size=128) == uhash.sha256_bytes(b"A" * 1024)


@pytest.mark.integration
@pytest.mark.regression
def test_sha256_file_follows_symlink_to_target_file(tmp_path: Path) -> None:
    """Verify sha256_file hashes the target file when given a symlink path."""
    target = tmp_path / "original.bin"
    link = tmp_path / "alias.bin"
    payload = b"symlinked archive payload"
    target.write_bytes(payload)
    try:
        link.symlink_to(target)
    except OSError as exc:
        pytest.skip(f"Symlink creation not permitted in environment: {exc}")

    assert uhash.sha256_file(link) == uhash.sha256_bytes(payload)


@pytest.mark.integration
@pytest.mark.regression
def test_sha256_file_propagates_permission_error_on_open(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify sha256_file propagates PermissionError when opening a locked file."""
    locked_file = tmp_path / "locked.bin"
    locked_file.write_bytes(b"content")

    def _deny_open(self: Path, *args: Any, **kwargs: Any) -> Any:
        raise PermissionError(f"Access denied: {self}")

    monkeypatch.setattr(Path, "open", _deny_open)
    with pytest.raises(PermissionError, match="Access denied"):
        uhash.sha256_file(locked_file)


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Chunk-size invariance property governed by active Hypothesis profile.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.integration
@given(case=binary_and_chunk_size())
def test_sha256_file_is_invariant_to_chunk_size(
    case: tuple[bytes, int],
) -> None:
    """Verify sha256_file matches reference SHA-256 across payloads and chunk sizes."""
    payload, chunk_size = case
    with tempfile.TemporaryDirectory() as tmp_dir:
        target = Path(tmp_dir) / "prop_stream.bin"
        target.write_bytes(payload)
        expected = hashlib.sha256(payload).hexdigest()
        assert uhash.sha256_file(target, chunk_size=chunk_size) == expected
