"""Path: tests/test_gda/test_model/test_military/test_military_topology.py

Architectural topology, interface lock, and re-export verification suite for gda.model.military.

Operational Role:
    Verifies that all military record domains (draft, service, pension, casualty, awards)
    export canonical entities cleanly without circular imports, upward dependencies,
    or __all__ drift, and enforce strict frozen Pydantic dataclass configuration.
"""

from __future__ import annotations

import ast
import inspect
from dataclasses import is_dataclass
from pathlib import Path

import pytest

import gda.model.military as military_root
import gda.model.military.awards as awards_mod
import gda.model.military.casualty as casualty_mod
import gda.model.military.draft as draft_mod
import gda.model.military.pension as pension_mod
import gda.model.military.service as service_mod
from gda.core.introspectable import IntrospectableMixin
from gda.model.base.source import SourceRecord
from gda.model.military import (
    AwardScope,
    BountyLandAct,
    BountyLandWarrantRecord,
    CasualtyCategory,
    CivilWarConscriptionAllegiance,
    CivilWarDraftRecord,
    CivilWarEnrollmentClass,
    ColonialMilitiaClass,
    ColonialMilitiaRecord,
    ColonialWarPeriod,
    CombatCasualtyRecord,
    DraftCardTier,
    EnlistmentMusterRecord,
    IntermentCemeteryType,
    MilitaryAwardRecord,
    MilitaryAwardTier,
    MilitaryBranch,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    MilitaryDraftRecord,
    MilitaryPensionRecord,
    MilitaryServiceRecord,
    ModernDraftEra,
    ModernSelectiveServiceRecord,
    MusterRollType,
    PensionClaimantRole,
    PensionPaymentAuthority,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
    PowCampType,
    PrisonerOfWarRecord,
    SeparationCharacter,
    SeparationDischargeRecord,
    SeparationFormType,
    ServiceComponent,
    SssClassification,
    WwiCitizenshipStatus,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiDraftWave,
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)

__version__ = "2.0.0+build.1"

_EXPECTED_ENTITIES = (
    # Draft
    MilitaryDraftRecord,
    ColonialMilitiaRecord,
    CivilWarDraftRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    ModernSelectiveServiceRecord,
    # Service
    MilitaryServiceRecord,
    EnlistmentMusterRecord,
    SeparationDischargeRecord,
    # Pension
    MilitaryPensionRecord,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
    BountyLandWarrantRecord,
    # Casualty
    MilitaryCasualtyRecord,
    CombatCasualtyRecord,
    PrisonerOfWarRecord,
    MilitaryBurialRecord,
    # Awards
    MilitaryAwardRecord,
)

_EXPECTED_VALUE_OBJECTS = (
    WwiPhysicalDescription,
    WwiiPhysicalMetrics,
)

_FORBIDDEN_IMPORTS = (
    "gda.enums",
    "gda.model.xref",
    "gda.entity",
    "gda.manager",
    "gda.db",
    "gda.engine",
    "cli",
    "ancestry_desk",
)


@pytest.mark.smoke
@pytest.mark.integrity
def test_military_root_reexports_match_subpackages() -> None:
    """Verify military root re-exports encapsulate subpackages without drift."""
    subpackages = [draft_mod, service_mod, pension_mod, casualty_mod, awards_mod]
    accumulated_sub_all: set[str] = set()

    for mod in subpackages:
        assert hasattr(mod, "__all__"), f"Module {mod.__name__} missing __all__"
        sub_all = list(mod.__all__)
        assert sub_all == sorted(sub_all), f"{mod.__name__}.__all__ must be sorted"
        accumulated_sub_all.update(sub_all)

    root_all = list(military_root.__all__)
    assert root_all == sorted(root_all), "gda.model.military.__all__ must be sorted"
    missing_in_root = accumulated_sub_all - set(root_all)
    assert not missing_in_root, f"Symbols missing from military root __all__: {missing_in_root}"


@pytest.mark.integrity
def test_military_canonical_entities_instantiable() -> None:
    """Verify all primary domain entities extend SourceRecord and IntrospectableMixin."""
    for cls in _EXPECTED_ENTITIES:
        assert hasattr(military_root, cls.__name__)
        assert inspect.isclass(cls)
        assert issubclass(cls, SourceRecord), f"{cls.__name__} must extend SourceRecord"
        assert issubclass(cls, IntrospectableMixin), (
            f"{cls.__name__} must extend IntrospectableMixin"
        )

    for vo_cls in _EXPECTED_VALUE_OBJECTS:
        assert hasattr(military_root, vo_cls.__name__)
        assert issubclass(vo_cls, IntrospectableMixin)


@pytest.mark.integrity
@pytest.mark.parametrize(
    "model_cls",
    (*_EXPECTED_ENTITIES, *_EXPECTED_VALUE_OBJECTS),
    ids=lambda c: c.__name__,
)
def test_military_models_enforce_strict_frozen_pydantic_config(model_cls: type) -> None:
    """Verify all gda.model.military dataclasses enforce frozen=True, extra='forbid', strict=True."""
    assert is_dataclass(model_cls)
    assert model_cls.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
    pydantic_cfg = getattr(model_cls, "__pydantic_config__", {})
    assert pydantic_cfg.get("frozen") is True
    assert pydantic_cfg.get("extra") == "forbid"
    assert pydantic_cfg.get("strict") is True


@pytest.mark.integrity
def test_military_enums_values_and_members() -> None:
    """Verify canonical enum invariants across all five domains."""
    # Awards
    assert MilitaryAwardTier.MEDAL_OF_HONOR == "MEDAL_OF_HONOR"
    assert AwardScope.VALOR_IN_COMBAT == "VALOR_IN_COMBAT"

    # Casualty
    assert CasualtyCategory.KILLED_IN_ACTION == "KILLED_IN_ACTION"
    assert PowCampType.OFFICER_CAMP == "OFFICER_CAMP"
    assert IntermentCemeteryType.NATIONAL_CEMETERY == "NATIONAL_CEMETERY"

    # Pension
    assert PensionClaimantRole.VETERAN == "VETERAN"
    assert PensionPaymentAuthority.US_BUREAU_OF_PENSIONS == "US_BUREAU_OF_PENSIONS"
    assert BountyLandAct.ACT_OF_1855 == "ACT_OF_1855"

    # Service
    assert MilitaryBranch.ARMY == "ARMY"
    assert ServiceComponent.REGULAR == "REGULAR"
    assert SeparationCharacter.HONORABLE == "HONORABLE"
    assert SeparationFormType.DD_214 == "DD_214"
    assert MusterRollType.MUSTER_IN == "MUSTER_IN"

    # Draft
    assert DraftCardTier.WWI_FIRST == "WWI_FIRST"
    assert DraftCardTier.WWII_FOURTH == "WWII_FOURTH"
    assert ColonialMilitiaClass.TRAINBAND == "TRAINBAND"
    assert ColonialWarPeriod.REVOLUTIONARY_WAR == "REVOLUTIONARY_WAR"
    assert CivilWarEnrollmentClass.CLASS_1 == "CLASS_1"
    assert CivilWarConscriptionAllegiance.UNION == "UNION"
    assert WwiCitizenshipStatus.NATIVE_BORN == "NATIVE_BORN"
    assert WwiiDraftWave.FIRST == "FIRST"
    assert ModernDraftEra.POST_1980_REGISTRATION == "POST_1980_REGISTRATION"
    assert SssClassification.ONE_A == "1-A"


@pytest.mark.integrity
def test_military_package_has_zero_upward_or_legacy_imports() -> None:
    """Verify gda.model.military never imports legacy gda.enums or higher-level packages."""
    pkg_dir = Path(inspect.getfile(military_root)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert not alias.name.startswith(_FORBIDDEN_IMPORTS), (
                        f"Forbidden import in {py_path}: '{alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(_FORBIDDEN_IMPORTS), (
                    f"Forbidden import in {py_path}: '{node.module}'"
                )


@pytest.mark.integrity
def test_no_legacy_domain_paths_exist() -> None:
    """Verify no stray domain directories exist in source or test trees."""
    root = Path(__file__).resolve().parent.parent.parent.parent.parent
    invalid_src = root / "src" / "gda" / "model" / "domain"
    invalid_tests = root / "tests" / "test_gda" / "test_model" / "test_domain"

    assert not invalid_src.exists(), f"Found invalid source path: {invalid_src}"
    assert not invalid_tests.exists(), f"Found invalid test path: {invalid_tests}"
