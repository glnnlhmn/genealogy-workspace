"""Path: tests/test_gda/test_util/test_util_contract.py

Authoritative public interface and contract verification suite for gda.util.

Operational Role:
    Freezes and validates the public API surface of the gda.util package.
    Verifies symbol parity, strict alphabetical __all__ ordering across package
    and submodules, and callable function parameter signatures.
"""

from __future__ import annotations

import inspect

import pytest

import gda.util
import gda.util.ids as util_ids
import gda.util.text as util_text

__version__ = "1.0.0+build.1"

AUTHORITATIVE_UTIL_EXPORTS: frozenset[str] = frozenset(
    {
        # ids.py (5)
        "extract_max_smart_id",
        "mint_smart_id",
        "mint_uuid",
        "parse_smart_id",
        "verify_id",
        # text.py (6)
        "clean_string",
        "clean_whitespace",
        "normalize_ascii",
        "phonetic_nysiis",
        "phonetic_soundex",
        "slugify",
    }
)


@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.unit
def test_util_exports_exact_authoritative_symbols() -> None:
    """Verify gda.util exports the exact 11 authoritative symbols with zero drift."""
    assert frozenset(gda.util.__all__) == AUTHORITATIVE_UTIL_EXPORTS
    assert len(gda.util.__all__) == 11
    for symbol in AUTHORITATIVE_UTIL_EXPORTS:
        fn = getattr(gda.util, symbol, None)
        assert callable(fn), f"Symbol {symbol} in gda.util must be callable"


@pytest.mark.integrity
@pytest.mark.unit
def test_util_all_and_submodule_alls_are_sorted_alphabetically() -> None:
    """Verify gda.util and its submodules declare alphabetically sorted __all__ lists."""
    assert gda.util.__all__ == sorted(gda.util.__all__)
    for mod in (util_ids, util_text):
        assert hasattr(mod, "__all__")
        assert mod.__all__ == sorted(mod.__all__)
        assert hasattr(mod, "__version__")
        assert "+build." in mod.__version__


@pytest.mark.integrity
@pytest.mark.unit
def test_util_callable_signatures_contract() -> None:
    """Verify parameter signatures of all public functions in gda.util."""
    assert list(inspect.signature(gda.util.verify_id).parameters) == [
        "val",
        "id_type",
        "smart_id_prefix",
    ]
    assert list(inspect.signature(gda.util.mint_uuid).parameters) == []
    assert list(inspect.signature(gda.util.mint_smart_id).parameters) == [
        "prefix",
        "sequence_num",
        "padding",
    ]
    assert list(inspect.signature(gda.util.parse_smart_id).parameters) == ["val"]
    assert list(inspect.signature(gda.util.extract_max_smart_id).parameters) == [
        "id_items",
        "prefix",
        "ignore_errors",
    ]
    assert list(inspect.signature(gda.util.clean_string).parameters) == ["val"]
    assert list(inspect.signature(gda.util.clean_whitespace).parameters) == ["text"]
    assert list(inspect.signature(gda.util.normalize_ascii).parameters) == ["text"]
    assert list(inspect.signature(gda.util.slugify).parameters) == [
        "text",
        "delimiter",
        "allow_colons",
    ]
    assert list(inspect.signature(gda.util.phonetic_soundex).parameters) == ["name"]
    assert list(inspect.signature(gda.util.phonetic_nysiis).parameters) == ["name"]
