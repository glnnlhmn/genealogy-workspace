"""Path: tests/test_gda/test_model/test_atom/test_atom_contract.py

Public interface and contract verification suite for the gda.model.atom package.

Operational Role:
    Freezes and validates that all 34 atomic value objects and identifier
    primitives are exposed in gda.model.atom.__all__, follow alphabetical
    sorting across package and submodules, adhere to the IntrospectableMixin
    contract, enforce immutability invariants, and preserve exact sealed
    public member contracts.

Test Structure & Protocol:
    - Atomized tests: 1:1 behavioral contract mapping.
    - Fully decorated: Every test carries @pytest.mark.smoke alongside @pytest.mark.unit / @pytest.mark.integrity.
    - Zero production disk I/O.
"""

from __future__ import annotations

import dataclasses
import inspect
from dataclasses import FrozenInstanceError
from enum import Enum
from typing import Any

import pytest

import gda.model.atom as atom_pkg
import gda.model.atom.date as atom_date
import gda.model.atom.gender as atom_gender
import gda.model.atom.geo as atom_geo
import gda.model.atom.id as atom_id
import gda.model.atom.scalar as atom_scalar
import gda.model.atom.urn as atom_urn
import gda.model.atom.year as atom_year
from gda.core.introspectable import IntrospectableMixin

__version__ = "1.0.0+build.2"

AUTHORITATIVE_ATOM_EXPORTS: frozenset[str] = frozenset(
    {
        # date.py (2)
        "DateString",
        "IsoTimestamp",
        # gender.py (1)
        "GenderAtom",
        # geo.py (2)
        "Latitude",
        "Longitude",
        # id.py (15)
        "AtomID",
        "DraftRecordID",
        "FactID",
        "FamilyID",
        "IndividualID",
        "LocationID",
        "MediaID",
        "NoteID",
        "OrganizationID",
        "RepositoryID",
        "ServiceRecordID",
        "SiteID",
        "SourceID",
        "TranscriptID",
        "UUIDv4Str",
        # scalar.py (5)
        "AhnentafelNumber",
        "ConfidenceScore",
        "NewsCategoryCode",
        "PubCode",
        "QuayScore",
        # urn.py (6)
        "ArchivalURN",
        "CemeteryPlotUrn",
        "CensusUrn",
        "MilitaryDraftUrn",
        "SourceURN",
        "VitalCertificateUrn",
        # year.py (3)
        "BirthYear",
        "DeathYear",
        "HistoricalYear",
    }
)


# ==============================================================================
# GROUP 1: PUBLIC EXPORT INTEGRITY & ALPHABETICAL ORDER
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_atom_package_all_is_sorted_and_matches_authoritative_contract() -> None:
    """Verify gda.model.atom.__all__ and all submodule __all__ lists are sorted and complete."""
    assert frozenset(atom_pkg.__all__) == AUTHORITATIVE_ATOM_EXPORTS
    assert len(atom_pkg.__all__) == 34
    assert atom_pkg.__all__ == sorted(atom_pkg.__all__)

    for mod in (
        atom_date,
        atom_gender,
        atom_geo,
        atom_id,
        atom_scalar,
        atom_urn,
        atom_year,
    ):
        assert hasattr(mod, "__all__")
        assert mod.__all__ == sorted(mod.__all__)


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_atom_package_all_symbols_exportable() -> None:
    """Verify that every symbol listed in __all__ exists and is importable from atom."""
    for symbol_name in atom_pkg.__all__:
        assert hasattr(atom_pkg, symbol_name), f"Missing symbol {symbol_name} in atom package"
        obj = getattr(atom_pkg, symbol_name)
        assert obj is not None


# ==============================================================================
# GROUP 2: INTROSPECTION ARCHITECTURE CONTRACT
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_atom_exported_classes_implement_introspection() -> None:
    """Verify that every non-enum class exported in __all__ inherits IntrospectableMixin."""
    for symbol_name in atom_pkg.__all__:
        obj = getattr(atom_pkg, symbol_name)
        if inspect.isclass(obj) and not issubclass(obj, Enum):
            assert issubclass(obj, IntrospectableMixin), (
                f"Class {symbol_name} must inherit IntrospectableMixin"
            )


# ==============================================================================
# GROUP 3: IMMUTABILITY ENFORCEMENT CONTRACT
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
def test_atom_primitives_enforce_immutability(all_valid_atoms: list[Any]) -> None:
    """Verify that instantiated atom primitives raise errors when attributes are modified."""
    assert len(all_valid_atoms) == len(atom_pkg.__all__)
    for instance in all_valid_atoms:
        first_attr = next(iter(instance.__dict__.keys()), "value")
        with pytest.raises((FrozenInstanceError, TypeError, AttributeError)):
            setattr(instance, first_attr, "mutated_value")


# ==============================================================================
# GROUP 4: EXACT SEALED PUBLIC INTERFACE CONTRACT
# ==============================================================================


@pytest.mark.unit
@pytest.mark.smoke
@pytest.mark.integrity
@pytest.mark.parametrize(
    ("cls_name", "exact_expected_members"),
    [
        # Identifier Primitives
        (
            "AtomID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "IndividualID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "FactID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "LocationID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "SiteID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "FamilyID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "NoteID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "OrganizationID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "RepositoryID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "DraftRecordID",
            {"value", "expected_prefix", "prefix", "suffix", "number", "EXPECTED_PREFIX", "help"},
        ),
        (
            "UUIDv4Str",
            {"value", "help"},
        ),
        (
            "SourceID",
            {"value", "help"},
        ),
        (
            "MediaID",
            {"value", "help"},
        ),
        (
            "ServiceRecordID",
            {"value", "help"},
        ),
        (
            "TranscriptID",
            {"value", "help"},
        ),
        # Calendar Year Primitives
        (
            "HistoricalYear",
            {"value", "MIN_YEAR", "MAX_YEAR", "help"},
        ),
        (
            "BirthYear",
            {"value", "MIN_YEAR", "MAX_YEAR", "help"},
        ),
        (
            "DeathYear",
            {"value", "MIN_YEAR", "MAX_YEAR", "help"},
        ),
        # Atomic Date & Timestamp Primitives
        (
            "DateString",
            {"value", "help"},
        ),
        (
            "IsoTimestamp",
            {"value", "help"},
        ),
        # Gender Primitives
        (
            "GenderAtom",
            {
                "value",
                "is_male",
                "is_female",
                "is_undetermined",
                "VALID_CODES",
                "help",
            },
        ),
        # Geospatial Primitives
        (
            "Latitude",
            {"value", "MIN_VAL", "MAX_VAL", "help"},
        ),
        (
            "Longitude",
            {"value", "MIN_VAL", "MAX_VAL", "help"},
        ),
        # Scalar Primitives
        (
            "QuayScore",
            {"value", "MIN_VAL", "MAX_VAL", "help"},
        ),
        (
            "AhnentafelNumber",
            {
                "value",
                "MIN_VAL",
                "is_male",
                "is_female",
                "father_index",
                "mother_index",
                "child_index",
                "help",
            },
        ),
        (
            "ConfidenceScore",
            {"value", "MIN_VAL", "MAX_VAL", "help"},
        ),
        (
            "PubCode",
            {"value", "help"},
        ),
        (
            "NewsCategoryCode",
            {"value", "help"},
        ),
        # Archival URN Primitives
        (
            "ArchivalURN",
            {"value", "parts", "nid", "EXPECTED_SCHEME", "EXPECTED_NID", "URN_REGEX", "help"},
        ),
        (
            "SourceURN",
            {
                "value",
                "parts",
                "nid",
                "year",
                "jurisdiction",
                "locator",
                "EXPECTED_SCHEME",
                "EXPECTED_NID",
                "URN_REGEX",
                "help",
            },
        ),
        (
            "CensusUrn",
            {
                "value",
                "parts",
                "nid",
                "census_year",
                "jurisdiction",
                "enumeration_locator",
                "EXPECTED_SCHEME",
                "EXPECTED_NID",
                "URN_REGEX",
                "help",
            },
        ),
        (
            "MilitaryDraftUrn",
            {
                "value",
                "parts",
                "nid",
                "draft_year",
                "jurisdiction",
                "card_locator",
                "EXPECTED_SCHEME",
                "EXPECTED_NID",
                "URN_REGEX",
                "help",
            },
        ),
        (
            "VitalCertificateUrn",
            {
                "value",
                "parts",
                "nid",
                "event_type",
                "certificate_year",
                "jurisdiction",
                "certificate_number",
                "EXPECTED_SCHEME",
                "EXPECTED_NID",
                "URN_REGEX",
                "help",
            },
        ),
        (
            "CemeteryPlotUrn",
            {
                "value",
                "parts",
                "nid",
                "facility_code",
                "plot_locator",
                "EXPECTED_SCHEME",
                "EXPECTED_NID",
                "URN_REGEX",
                "help",
            },
        ),
    ],
)
def test_atom_class_exact_public_interface(cls_name: str, exact_expected_members: set[str]) -> None:
    """Verify that exported atom classes expose exactly their expected public interface."""
    cls_obj = getattr(atom_pkg, cls_name)
    assert inspect.isclass(cls_obj), f"{cls_name} is not a class"

    field_names = (
        {f.name for f in dataclasses.fields(cls_obj)}
        if dataclasses.is_dataclass(cls_obj)
        else set()
    )
    all_members = set(dir(cls_obj)) | field_names
    actual_public = {m for m in all_members if not m.startswith("_")}

    missing = exact_expected_members - actual_public
    extra = actual_public - exact_expected_members

    assert not missing and not extra, (
        f"Public interface drift in {cls_name}:\n"
        f"  Missing expected: {missing}\n"
        f"  Unexpected additions: {extra}"
    )
