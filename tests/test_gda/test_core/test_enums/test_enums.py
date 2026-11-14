"""Path: tests/test_gda/test_core/test_enums/test_enums.py

Comprehensive behavioral test suite verifying all authoritative enumeration contracts.

Operational Role:
    Verifies that all StrEnum and IntEnum definitions in gda.core.enums conform to
    their expected tokens, base classes, exact sealed public interface contracts,
    JSON serializability, Pydantic V2 validation, and strict rejection boundaries.

Test Structure & Protocol:
    - Atomized tests: 1:1 verification per behavioral contract.
    - Fully decorated: Explicitly decorated with registered pytest markers.
    - Dependencies: In-memory only; zero physical disk I/O.
"""

from __future__ import annotations

import json
from enum import Enum, IntEnum, StrEnum
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

import gda.core.enums as ge

__version__ = "1.2.0+build.1"


# ==============================================================================
# GROUP 1: General Enum Invariants & Structural Integrity
# ==============================================================================


@pytest.mark.unit
@pytest.mark.integrity
def test_all_enums_inherit_proper_base_types(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify every registered enum inherits strictly from StrEnum or IntEnum."""
    for enum_cls in all_enum_classes:
        is_str = issubclass(enum_cls, StrEnum)
        is_int = issubclass(enum_cls, IntEnum)
        assert is_str or is_int, f"{enum_cls.__name__} does not inherit from StrEnum or IntEnum"


@pytest.mark.unit
@pytest.mark.integrity
def test_all_enum_canonical_values_are_unique(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify unique values exist across canonical members within each enum class."""
    for enum_cls in all_enum_classes:
        values = [member.value for member in enum_cls]
        unique_values = set(values)
        assert len(values) == len(unique_values), (
            f"{enum_cls.__name__} contains duplicate member values across canonical definitions"
        )


@pytest.mark.unit
@pytest.mark.integrity
def test_all_enum_classes_are_exported_in_dunder_all(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify that every unique enum class is represented in gda.core.enums.__all__."""
    exported_names = set(ge.__all__)
    for enum_cls in all_enum_classes:
        assert enum_cls.__name__ in exported_names, f"{enum_cls.__name__} missing from __all__"


# ==============================================================================
# GROUP 2: Exact Sealed Public Interface Contract (82 Items)
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
def test_enums_package_exact_public_interface() -> None:
    """Verify gda.core.enums.__all__ matches the exact sealed public contract of 82 items."""
    exact_expected_contract = {
        # Core Domain (7)
        "AssociatedRole",
        "FactType",
        "IDType",
        "QualityAssessment",
        "QuayScore",
        "Sex",
        "SmartIDPrefix",
        # Date & Census Domain (4)
        "CensusYearUS",
        "DateModifier",
        "MODIFIER_ALIASES",
        "normalize_modifier",
        # Vital Domain (12)
        "BirthPlurality",
        "DispositionType",
        "DivorceDecreeType",
        "HistoricNameType",
        "LegalPlaintiff",
        "MannerOfDeath",
        "MaritalHistoryDissolution",
        "MaritalStatus",
        "PedigreeType",
        "UnionDissolutionType",
        "UnionType",
        "VitalModifier",
        # Location Domain (2)
        "JurisdictionCategory",
        "LocationType",
        # Site Domain (5)
        "MarkerCondition",
        "MarkerMaterial",
        "MarkerType",
        "OperationalStatus",
        "SiteType",
        # Fiscal Domain (4)
        "CitizenshipStatus",
        "HomeOwnership",
        "ResidentialStatus",
        "TaxpayerClassification",
        # Land Domain (2)
        "DeedPartyRole",
        "LandGrantBasis",
        # Probate Domain (3)
        "BequestType",
        "EstatePropertyCategory",
        "ProbateLedgerEntryKind",
        # Archival Domain (12)
        "DocumentSide",
        "EyeColor",
        "HairColor",
        "Legibility",
        "NoteType",
        "PhysicalBuild",
        "PublicationFrequency",
        "SelectiveServiceClass",
        "TestimonyMedium",
        "TextQuality",
        "TranscriptLegibility",
        "WwiCardType",
        # Sources Domain (6)
        "EducationLevel",
        "MilitaryConflict",
        "MilitaryDraftType",
        "MilitaryWar",
        "SourceRecordCategory",
        "SourceRecordType",
        # Military Domain (22)
        "AwardScope",
        "BountyLandAct",
        "CasualtyCategory",
        "CivilWarConscriptionAllegiance",
        "CivilWarEnrollmentClass",
        "ColonialMilitiaClass",
        "ColonialWarPeriod",
        "DraftCardTier",
        "IntermentCemeteryType",
        "MilitaryAwardTier",
        "MilitaryBranch",
        "ModernDraftEra",
        "MusterRollType",
        "PensionClaimantRole",
        "PensionPaymentAuthority",
        "PowCampType",
        "SeparationCharacter",
        "SeparationFormType",
        "ServiceComponent",
        "SssClassification",
        "WwiCitizenshipStatus",
        "WwiiDraftWave",
        # Orgs Domain (3)
        "AffiliationType",
        "MembershipStatus",
        "OrganizationCategory",
    }

    actual_exported = set(ge.__all__)
    missing = exact_expected_contract - actual_exported
    extra = actual_exported - exact_expected_contract

    assert not missing and not extra, (
        f"Public interface drift in gda.core.enums:\n"
        f"  Missing expected: {missing}\n"
        f"  Unexpected additions: {extra}"
    )
    assert len(ge.__all__) == len(exact_expected_contract)
    assert ge.__all__ == sorted(ge.__all__)


# ==============================================================================
# GROUP 3: Cross-Domain Boundary Specifications
# ==============================================================================


@pytest.mark.unit
def test_location_type_and_site_type_boundary() -> None:
    """Verify LocationType (jurisdictions) is strictly partitioned from SiteType (venues)."""
    assert ge.LocationType.COUNTY == "COUNTY"
    assert ge.LocationType.STATE == "STATE"
    assert ge.SiteType.CEMETERY == "CEMETERY"
    assert ge.SiteType.CHURCH == "CHURCH"
    assert "COUNTY" not in [m.value for m in ge.SiteType]
    assert "STATE" not in [m.value for m in ge.SiteType]


@pytest.mark.unit
def test_census_years_are_strictly_valid_historical_integers() -> None:
    """Verify CensusYearUS members evaluate to canonical decennial census integers."""
    assert ge.CensusYearUS.Y1790 == 1790
    assert ge.CensusYearUS.Y1880 == 1880
    assert ge.CensusYearUS.Y1950 == 1950
    for year in ge.CensusYearUS:
        assert isinstance(year.value, int)
        assert 1790 <= year.value <= 1950


@pytest.mark.unit
def test_fiscal_taxpayer_classification_tokens() -> None:
    """Verify TaxpayerClassification matches historical tax roll categories."""
    assert ge.TaxpayerClassification.FREEHOLDER == "Freeholder"
    assert ge.TaxpayerClassification.TENANT == "Tenant"
    assert ge.TaxpayerClassification.SINGLE_FREEMAN == "Single Freeman"
    assert ge.TaxpayerClassification.INMATE == "Inmate"
    assert ge.TaxpayerClassification.WIDOW == "Widow"


# ==============================================================================
# GROUP 4: Native JSON Serialization & String Formats
# ==============================================================================


@pytest.mark.unit
def test_strenum_native_json_dump_emits_raw_string() -> None:
    """Verify that StrEnum members serialize directly to raw strings in JSON."""
    payload = {
        "sex": ge.Sex.MALE,
        "fact": ge.FactType.BIRTH,
        "marker": ge.MarkerType.UPRIGHT_HEADSTONE,
    }
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    assert decoded["sex"] == "Male"
    assert decoded["fact"] == "BIRTH"
    assert decoded["marker"] == "Upright Headstone"


@pytest.mark.unit
def test_intenum_native_json_dump_emits_raw_integer() -> None:
    """Verify that IntEnum members serialize directly to numeric integers in JSON."""
    payload = {
        "quay": ge.QuayScore.DIRECT_PRIMARY,
        "census_year": ge.CensusYearUS.Y1850,
    }
    encoded = json.dumps(payload)
    decoded = json.loads(encoded)

    assert decoded["quay"] == 3
    assert decoded["census_year"] == 1850


@pytest.mark.unit
def test_strenum_str_comparison_and_formatting() -> None:
    """Verify StrEnum members behave identically to native str in equality and formatting."""
    assert ge.Sex.MALE == "Male"
    assert f"Sex is {ge.Sex.FEMALE}" == "Sex is Female"
    assert ge.Sex.MALE.startswith("M")


# ==============================================================================
# GROUP 5: Pydantic V2 Validation & Coercion
# ==============================================================================


@pytest.mark.unit
def test_pydantic_validates_raw_string_into_enum_instance(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic coerces raw strings and ints into corresponding enum instances."""
    instance = pydantic_enum_model_cls(**valid_enum_payload)

    assert instance.sex is ge.Sex.MALE
    assert instance.quay is ge.QuayScore.DIRECT_PRIMARY
    assert instance.fact_type is ge.FactType.BIRTH
    assert instance.census_year is ge.CensusYearUS.Y1880
    assert instance.location_type is ge.LocationType.COUNTY
    assert instance.vital_modifier is ge.VitalModifier.STILLBORN


@pytest.mark.unit
def test_pydantic_accepts_enum_instances_directly(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic accepts pre-instantiated enum members directly."""
    payload = dict(valid_enum_payload)
    payload["sex"] = ge.Sex.FEMALE
    payload["quay"] = ge.QuayScore.SECONDARY

    instance = pydantic_enum_model_cls(**payload)
    assert instance.sex is ge.Sex.FEMALE
    assert instance.quay is ge.QuayScore.SECONDARY


@pytest.mark.unit
def test_pydantic_rejects_invalid_token_with_validation_error(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic raises ValidationError when encountering unregistered tokens."""
    payload = dict(valid_enum_payload)
    payload["sex"] = "NonExistentSex"

    with pytest.raises(ValidationError):
        pydantic_enum_model_cls(**payload)


@pytest.mark.unit
def test_pydantic_handles_optional_and_none_values(
    pydantic_enum_model_cls: type[BaseModel],
    valid_enum_payload: dict[str, Any],
) -> None:
    """Verify Pydantic accepts None for nullable/optional enum fields."""
    payload = dict(valid_enum_payload)
    payload["optional_sex"] = None
    payload["optional_quay"] = None

    instance = pydantic_enum_model_cls(**payload)
    assert instance.optional_sex is None
    assert instance.optional_quay is None

    payload["optional_sex"] = "Unknown"
    instance_with_val = pydantic_enum_model_cls(**payload)
    assert instance_with_val.optional_sex is ge.Sex.UNKNOWN


# ==============================================================================
# GROUP 6: Defensive Boundaries & Strictness
# ==============================================================================


@pytest.mark.unit
@pytest.mark.regression
def test_strenum_strict_case_sensitivity_rejection() -> None:
    """Verify StrEnum raises ValueError on lowercase or invalid casing."""
    with pytest.raises(ValueError):
        ge.Sex("male")

    with pytest.raises(ValueError):
        ge.FactType("birth")


@pytest.mark.unit
@pytest.mark.regression
def test_strenum_whitespace_tolerance_rejection() -> None:
    """Verify StrEnum rejects untrimmed whitespace to enforce upstream sanitization."""
    with pytest.raises(ValueError):
        ge.Sex(" Male ")

    with pytest.raises(ValueError):
        ge.FactType("BIRTH ")
