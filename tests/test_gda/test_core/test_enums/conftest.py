"""Path: tests/test_gda/test_core/test_enums/conftest.py

Shared pytest fixtures for the gda.core.enums verification suite.

Operational Role:
    Supplies handcrafted in-memory fixtures including comprehensive enum class
    registries, exact public export contract bounds, and Pydantic validation
    harness models for testing serialization, coercion, and rejection boundaries
    without disk I/O.
"""

from __future__ import annotations

import inspect
from enum import Enum
from typing import Any

import pytest
from pydantic import BaseModel

import gda.core.enums as ge

__version__ = "1.0.0+build.6"


@pytest.fixture(scope="session")
def all_enum_classes() -> tuple[type[Enum], ...]:
    """Provide a tuple of every unique authoritative enumeration class exported by gda.core.enums."""
    classes: list[type[Enum]] = []
    seen: set[type[Enum]] = set()
    for name in ge.__all__:
        attr = getattr(ge, name, None)
        if inspect.isclass(attr) and issubclass(attr, Enum):
            if attr not in seen:
                seen.add(attr)
                classes.append(attr)
    return tuple(classes)


@pytest.fixture(scope="session")
def all_exported_symbols_count() -> int:
    """Return the exact count of items declared in gda.core.enums.__all__."""
    return 53


class SampleEnumModel(BaseModel):
    """Pydantic test fixture model containing representative enum fields from each domain."""

    # Core
    sex: ge.Sex
    quay: ge.QuayScore
    fact_type: ge.FactType

    # Sources & Date
    record_cat: ge.SourceRecordCategory
    census_year: ge.CensusYearUS
    date_modifier: ge.DateModifier = ge.DateModifier.EXACT

    # Vital
    union_type: ge.UnionType = ge.UnionType.UNKNOWN
    manner_of_death: ge.MannerOfDeath
    historic_name_type: ge.HistoricNameType = ge.HistoricNameType.PRIMARY
    vital_modifier: ge.VitalModifier = ge.VitalModifier.INFANT

    # Location & Site
    location_type: ge.LocationType
    jurisdiction_cat: ge.JurisdictionCategory = ge.JurisdictionCategory.COUNTY_EQUIVALENT
    site_type: ge.SiteType

    # Archival
    note_type: ge.NoteType
    document_side: ge.DocumentSide = ge.DocumentSide.FRONT
    text_quality: ge.TextQuality = ge.TextQuality.VERBATIM
    legibility: ge.Legibility = ge.Legibility.CLEAR

    # Fiscal
    taxpayer_class: ge.TaxpayerClassification

    # Optional / Nullable handling
    optional_sex: ge.Sex | None = None
    optional_quay: ge.QuayScore | None = None


@pytest.fixture(scope="session")
def pydantic_enum_model_cls() -> type[BaseModel]:
    """Provide the Pydantic validation test model class."""
    return SampleEnumModel


@pytest.fixture
def valid_enum_payload() -> dict[str, Any]:
    """Provide a raw dictionary with valid strings and integers matching SampleEnumModel."""
    return {
        "sex": "Male",
        "quay": 3,
        "fact_type": "BIRTH",
        "record_cat": "VITAL",
        "census_year": 1880,
        "date_modifier": "ABT",
        "union_type": "MARRIED",
        "manner_of_death": "Natural",
        "historic_name_type": "PRIMARY",
        "vital_modifier": "STILLBORN",
        "location_type": "COUNTY",
        "jurisdiction_cat": "COUNTY_EQUIVALENT",
        "site_type": "CEMETERY",
        "note_type": "RESEARCH",
        "document_side": "FRONT",
        "text_quality": "VERBATIM",
        "legibility": "CLEAR",
        "taxpayer_class": "Freeholder",
        "optional_sex": None,
        "optional_quay": None,
    }
