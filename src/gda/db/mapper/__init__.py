"""Path: src/gda/db/mapper/__init__.py

Public facade and registry for GDA bidirectional SQLite row mappers.

Operational Role:
    Aggregates modular entity, archival source, and cross-reference row mappers
    and exposes the get_mapper() lookup registry across all 43 mapper classes
    and their polymorphic domain subclasses.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from gda.db.exceptions import EntityMappingError
from gda.db.mapper.base import (
    BaseRowMapper,
    _extract_id_str,
    _extract_year_from_text,
)
from gda.db.mapper.education_manuscripts_orgs_other import (
    AcademicCredentialRecordMapper,
    FamilyBibleRecordMapper,
    NarrativeManuscriptRecordMapper,
    OrganizationMembershipRecordMapper,
    OrganizationRosterRecordMapper,
    OtherMiscellaneousRecordMapper,
)
from gda.db.mapper.enumerated_publications import (
    _POPULATION_SCHEDULE_REGISTRY,
    _SUPPLEMENTAL_SCHEDULE_REGISTRY,
    _TAX_RECORD_REGISTRY,
    DirectoryRollRecordMapper,
    NewspaperClipRecordMapper,
    PeriodicalArticleRecordMapper,
    PopulationScheduleMapper,
    PublicationMapper,
    SupplementalScheduleMapper,
    TaxAssessmentRecordMapper,
)
from gda.db.mapper.facts import FactRowMapper
from gda.db.mapper.immigration_military import (
    _CASUALTY_RECORD_REGISTRY,
    _DRAFT_RECORD_REGISTRY,
    _PENSION_RECORD_REGISTRY,
    _SERVICE_RECORD_REGISTRY,
    BountyLandWarrantRecordMapper,
    ImmigrationManifestRecordMapper,
    MilitaryAwardRecordMapper,
    MilitaryCasualtyRecordMapper,
    MilitaryDraftRecordMapper,
    MilitaryPensionRecordMapper,
    MilitaryServiceRecordMapper,
    NaturalizationRecordMapper,
)
from gda.db.mapper.organizations import OrganizationRowMapper
from gda.db.mapper.personas import FamilyRowMapper, IndividualRowMapper
from gda.db.mapper.places import LocationRowMapper, SiteRowMapper
from gda.db.mapper.probate_land import (
    EstateInventoryRecordMapper,
    LandDeedRecordMapper,
    LandGrantRecordMapper,
    ProbateRecordMapper,
)
from gda.db.mapper.vital_cemetery import (
    BaptismRecordMapper,
    BirthRecordMapper,
    CemeteryMarkerRecordMapper,
    CemeteryRegistryRecordMapper,
    DeathRecordMapper,
    DivorceRecordMapper,
    MarriageRecordMapper,
)
from gda.db.mapper.xref import (
    FactParticipantXRefMapper,
    IndividualFamilyXRefMapper,
    IndividualOrganizationXRefMapper,
    IndividualSourceXRefMapper,
    IndividualSurnameXRefMapper,
    LocationXRefMapper,
    MediaXRefMapper,
    SiteXRefMapper,
    SurnameXRefMapper,
)

__version__ = "1.0.0+build.9"

__all__ = [
    "AcademicCredentialRecordMapper",
    "BaptismRecordMapper",
    "BaseRowMapper",
    "BirthRecordMapper",
    "BountyLandWarrantRecordMapper",
    "CemeteryMarkerRecordMapper",
    "CemeteryRegistryRecordMapper",
    "DeathRecordMapper",
    "DirectoryRollRecordMapper",
    "DivorceRecordMapper",
    "EstateInventoryRecordMapper",
    "FactParticipantXRefMapper",
    "FactRowMapper",
    "FamilyBibleRecordMapper",
    "FamilyRowMapper",
    "ImmigrationManifestRecordMapper",
    "IndividualFamilyXRefMapper",
    "IndividualOrganizationXRefMapper",
    "IndividualRowMapper",
    "IndividualSourceXRefMapper",
    "IndividualSurnameXRefMapper",
    "LandDeedRecordMapper",
    "LandGrantRecordMapper",
    "LocationRowMapper",
    "LocationXRefMapper",
    "MarriageRecordMapper",
    "MediaXRefMapper",
    "MilitaryAwardRecordMapper",
    "MilitaryCasualtyRecordMapper",
    "MilitaryDraftRecordMapper",
    "MilitaryPensionRecordMapper",
    "MilitaryServiceRecordMapper",
    "NarrativeManuscriptRecordMapper",
    "NaturalizationRecordMapper",
    "NewspaperClipRecordMapper",
    "OrganizationMembershipRecordMapper",
    "OrganizationRosterRecordMapper",
    "OrganizationRowMapper",
    "OtherMiscellaneousRecordMapper",
    "PeriodicalArticleRecordMapper",
    "PopulationScheduleMapper",
    "ProbateRecordMapper",
    "PublicationMapper",
    "SiteRowMapper",
    "SiteXRefMapper",
    "SupplementalScheduleMapper",
    "SurnameXRefMapper",
    "TaxAssessmentRecordMapper",
    "_extract_id_str",
    "_extract_year_from_text",
    "get_mapper",
]

_ALL_MAPPER_INSTANCES: tuple[BaseRowMapper[Any], ...] = (
    # Core Entities (6)
    LocationRowMapper(),
    SiteRowMapper(),
    OrganizationRowMapper(),
    IndividualRowMapper(),
    FamilyRowMapper(),
    FactRowMapper(),
    # Vital & Cemetery (7)
    BaptismRecordMapper(),
    BirthRecordMapper(),
    DeathRecordMapper(),
    DivorceRecordMapper(),
    MarriageRecordMapper(),
    CemeteryMarkerRecordMapper(),
    CemeteryRegistryRecordMapper(),
    # Probate & Land (4)
    ProbateRecordMapper(),
    EstateInventoryRecordMapper(),
    LandDeedRecordMapper(),
    LandGrantRecordMapper(),
    # Immigration & Military (8)
    ImmigrationManifestRecordMapper(),
    NaturalizationRecordMapper(),
    MilitaryDraftRecordMapper(),
    MilitaryServiceRecordMapper(),
    MilitaryPensionRecordMapper(),
    BountyLandWarrantRecordMapper(),
    MilitaryCasualtyRecordMapper(),
    MilitaryAwardRecordMapper(),
    # Enumerated & Publications (7)
    PopulationScheduleMapper(),
    SupplementalScheduleMapper(),
    DirectoryRollRecordMapper(),
    TaxAssessmentRecordMapper(),
    PublicationMapper(),
    NewspaperClipRecordMapper(),
    PeriodicalArticleRecordMapper(),
    # Education, Manuscripts, Orgs & Other (6)
    AcademicCredentialRecordMapper(),
    FamilyBibleRecordMapper(),
    NarrativeManuscriptRecordMapper(),
    OrganizationMembershipRecordMapper(),
    OrganizationRosterRecordMapper(),
    OtherMiscellaneousRecordMapper(),
    # Cross-References (9)
    FactParticipantXRefMapper(),
    IndividualFamilyXRefMapper(),
    IndividualOrganizationXRefMapper(),
    IndividualSourceXRefMapper(),
    IndividualSurnameXRefMapper(),
    LocationXRefMapper(),
    MediaXRefMapper(),
    SiteXRefMapper(),
    SurnameXRefMapper(),
)


def _bind_polymorphic_subclasses(
    registry: dict[type[Any], BaseRowMapper[Any]],
    mapper: BaseRowMapper[Any],
    subclasses: Iterable[type[Any]],
) -> None:
    """Bind polymorphic concrete subclasses to their shared parent row mapper."""
    for cls in subclasses:
        registry[cls] = mapper


def _build_mapper_registry() -> dict[type[Any], BaseRowMapper[Any]]:
    """Build lookup dictionary mapping all 43 model classes and polymorphic subclasses."""
    registry: dict[type[Any], BaseRowMapper[Any]] = {
        mapper.model_cls: mapper for mapper in _ALL_MAPPER_INSTANCES
    }
    _bind_polymorphic_subclasses(
        registry,
        registry[PopulationScheduleMapper().model_cls],
        _POPULATION_SCHEDULE_REGISTRY.values(),
    )
    _bind_polymorphic_subclasses(
        registry,
        registry[SupplementalScheduleMapper().model_cls],
        _SUPPLEMENTAL_SCHEDULE_REGISTRY.values(),
    )
    _bind_polymorphic_subclasses(
        registry,
        registry[TaxAssessmentRecordMapper().model_cls],
        _TAX_RECORD_REGISTRY.values(),
    )
    _bind_polymorphic_subclasses(
        registry,
        registry[MilitaryDraftRecordMapper().model_cls],
        _DRAFT_RECORD_REGISTRY.values(),
    )
    _bind_polymorphic_subclasses(
        registry,
        registry[MilitaryServiceRecordMapper().model_cls],
        _SERVICE_RECORD_REGISTRY.values(),
    )
    _bind_polymorphic_subclasses(
        registry,
        registry[MilitaryPensionRecordMapper().model_cls],
        _PENSION_RECORD_REGISTRY.values(),
    )
    _bind_polymorphic_subclasses(
        registry,
        registry[MilitaryCasualtyRecordMapper().model_cls],
        _CASUALTY_RECORD_REGISTRY.values(),
    )
    return registry


_MAPPER_REGISTRY: dict[type[Any], BaseRowMapper[Any]] = _build_mapper_registry()


def get_mapper[T](model_cls: type[T]) -> BaseRowMapper[T]:
    """Retrieve the registered row mapper for a domain entity, source, or XRef class."""
    mapper = _MAPPER_REGISTRY.get(model_cls)
    if mapper is None:
        raise EntityMappingError(
            f"No registered row mapper for entity class '{model_cls.__name__}'.",
            details={"model_cls": model_cls.__name__},
        )
    return mapper
