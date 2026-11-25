"""Path: tests/test_gda/test_core/test_enums/test_enums_contract.py

Authoritative package-level facade and invariant contract suite for gda.core.enums.

Operational Role:
    Freezes the sealed 83-item public interface of gda.core.enums.__all__,
    verifies native JSON/string serialization and cross-domain boundaries,
    and enforces Phase 3 architectural invariants: GDAStrEnum/GDAIntEnum
    inheritance, authoritative submodule placement, unique member values,
    and universal UPPER_SNAKE_CASE StrEnum tokens.

Test Structure & Protocol:
    - Atomized tests: 1:1 structural contract assertions.
    - Fully decorated: 5-marker taxonomy (smoke, unit, integrity).
    - Companion module: test_enums_coercion.py (coercion, Pydantic, Hypothesis).
"""

from __future__ import annotations

import json
import re
from enum import Enum, IntEnum, StrEnum

import pytest

import gda.core.enums as ge

__version__ = "1.0.0+build.6"

_MEMBER_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_UPPER_TOKEN_RE = re.compile(r"^[A-Z0-9][A-Z0-9_-]*$")

AUTHORITATIVE_ENUM_EXPORTS: frozenset[str] = frozenset(
    {
        # Base & Coercion (3)
        "GDAIntEnum",
        "GDAStrEnum",
        "coerce_enum",
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
        # Vital Domain (15 — includes relocated EyeColor, HairColor, PhysicalBuild, EducationLevel)
        "BirthPlurality",
        "DispositionType",
        "DivorceDecreeType",
        "EducationLevel",
        "EyeColor",
        "HairColor",
        "HistoricNameType",
        "LegalPlaintiff",
        "MannerOfDeath",
        "MaritalStatus",
        "PedigreeType",
        "PhysicalBuild",
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
        # Immigration Domain (2)
        "ArrivalPassageClass",
        "NaturalizationStage",
        # Land Domain (2)
        "DeedPartyRole",
        "LandGrantBasis",
        # Probate Domain (3)
        "BequestType",
        "EstatePropertyCategory",
        "ProbateLedgerEntryKind",
        # Archival Domain (6)
        "DocumentSide",
        "Legibility",
        "NoteType",
        "PublicationFrequency",
        "TestimonyMedium",
        "TextQuality",
        # Sources Domain (2)
        "SourceRecordCategory",
        "SourceRecordType",
        # Military Domain (25 — includes relocated WwiCardType, MilitaryDraftType, MilitaryWar)
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
        "MilitaryDraftType",
        "MilitaryWar",
        "ModernDraftEra",
        "MusterRollType",
        "PensionClaimantRole",
        "PensionPaymentAuthority",
        "PowCampType",
        "SeparationCharacter",
        "SeparationFormType",
        "ServiceComponent",
        "SssClassification",
        "WwiCardType",
        "WwiCitizenshipStatus",
        "WwiiDraftWave",
        # Orgs Domain (3)
        "AffiliationType",
        "MembershipStatus",
        "OrganizationCategory",
    }
)


# ==============================================================================
# GROUP 1: Smoke & Primary Entrypoints
# Note: Single smoke gate freezing gda.core.enums.__all__ (83 items).
# ==============================================================================


@pytest.mark.smoke
@pytest.mark.integrity
def test_enums_package_exact_public_interface() -> None:
    """Verify gda.core.enums.__all__ matches the exact sealed 83-item contract."""
    actual = set(ge.__all__)
    missing = AUTHORITATIVE_ENUM_EXPORTS - actual
    extra = actual - AUTHORITATIVE_ENUM_EXPORTS
    assert not missing and not extra, (
        f"Public interface drift in gda.core.enums:\n  Missing: {missing}\n  Extra: {extra}"
    )
    assert len(ge.__all__) == len(AUTHORITATIVE_ENUM_EXPORTS)
    assert ge.__all__ == sorted(ge.__all__)


# ==============================================================================
# GROUP 2: Core Logic & Happy Paths
# Note: Native JSON serialization, str formatting, and cross-domain boundaries.
# ==============================================================================


@pytest.mark.unit
def test_strenum_and_intenum_native_json_and_str_behavior() -> None:
    """Verify StrEnum emits UPPER_SNAKE_CASE strings and IntEnum emits raw ints in JSON."""
    payload = {
        "sex": ge.Sex.MALE,
        "fact": ge.FactType.BIRTH,
        "marker": ge.MarkerType.UPRIGHT_HEADSTONE,
        "quay": ge.QuayScore.DIRECT_PRIMARY,
        "census_year": ge.CensusYearUS.Y1850,
    }
    decoded = json.loads(json.dumps(payload))
    assert decoded["sex"] == "MALE"
    assert decoded["fact"] == "BIRTH"
    assert decoded["marker"] == "UPRIGHT_HEADSTONE"
    assert decoded["quay"] == 3
    assert decoded["census_year"] == 1850
    assert f"Sex is {ge.Sex.FEMALE}" == "Sex is FEMALE"


@pytest.mark.unit
def test_location_site_boundary_and_census_year_bounds() -> None:
    """Verify LocationType/SiteType disjointness and CensusYearUS integer bounds."""
    assert ge.LocationType.COUNTY == "COUNTY"
    assert ge.SiteType.CEMETERY == "CEMETERY"
    site_values = {m.value for m in ge.SiteType}
    assert "COUNTY" not in site_values
    assert "STATE" not in site_values

    for year in ge.CensusYearUS:
        assert isinstance(year.value, int)
        assert 1790 <= year.value <= 1950


# ==============================================================================
# GROUP 6: Integrity & Invariants
# Note: Base classes, submodule placement, UPPER_SNAKE_CASE, and uniqueness.
# ==============================================================================


@pytest.mark.integrity
@pytest.mark.unit
def test_all_enums_inherit_gda_base_classes(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify every enum inherits from GDAStrEnum or GDAIntEnum (Phase 3 TDD Red)."""
    gda_str = getattr(ge, "GDAStrEnum", None)
    gda_int = getattr(ge, "GDAIntEnum", None)
    assert gda_str is not None and issubclass(gda_str, StrEnum), "GDAStrEnum missing"
    assert gda_int is not None and issubclass(gda_int, IntEnum), "GDAIntEnum missing"

    for enum_cls in all_enum_classes:
        if enum_cls in (gda_str, gda_int):
            continue
        assert issubclass(enum_cls, (gda_str, gda_int)), (
            f"{enum_cls.__name__} must inherit from GDAStrEnum or GDAIntEnum"
        )


@pytest.mark.integrity
@pytest.mark.unit
def test_relocated_enums_reside_in_authoritative_submodules() -> None:
    """Verify relocated enums live in their target domain submodules (Phase 3 TDD Red)."""
    expected_modules = {
        "WwiCardType": "gda.core.enums.military",
        "MilitaryDraftType": "gda.core.enums.military",
        "MilitaryWar": "gda.core.enums.military",
        "EyeColor": "gda.core.enums.vital",
        "HairColor": "gda.core.enums.vital",
        "PhysicalBuild": "gda.core.enums.vital",
        "EducationLevel": "gda.core.enums.vital",
    }
    mismatches = {
        name: getattr(ge, name).__module__
        for name, target_mod in expected_modules.items()
        if getattr(ge, name).__module__ != target_mod
    }
    assert not mismatches, f"Enums in wrong submodules: {mismatches}"


@pytest.mark.integrity
@pytest.mark.unit
def test_all_strenum_members_use_upper_snake_case(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify all StrEnum names and values use uppercase tokens with no whitespace (Phase 3)."""
    violations: list[str] = []
    for enum_cls in all_enum_classes:
        if not issubclass(enum_cls, StrEnum):
            continue
        for member in enum_cls:
            if not _MEMBER_NAME_RE.match(member.name):
                violations.append(f"{enum_cls.__name__}.{member.name} (name)")
            if not _UPPER_TOKEN_RE.match(member.value):
                violations.append(f"{enum_cls.__name__}.{member.name}={member.value!r}")
    assert not violations, f"Non-UPPER_SNAKE_CASE StrEnum tokens: {violations[:10]}"


@pytest.mark.integrity
@pytest.mark.unit
def test_all_enum_canonical_values_are_unique(
    all_enum_classes: tuple[type[Enum], ...],
) -> None:
    """Verify unique values exist across canonical members within each enum class."""
    for enum_cls in all_enum_classes:
        values = [member.value for member in enum_cls]
        assert len(values) == len(set(values)), (
            f"{enum_cls.__name__} contains duplicate member values"
        )
