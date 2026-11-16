"""Path: src/gda/repository/__init__.py

Unified persistence, query, and in-memory collection layer for GDA.
"""

from __future__ import annotations

from gda.repository.base import BaseSQLiteRepository
from gda.repository.cemetery import (
    CemeteryMarkerCollection,
    CemeteryMarkerRepository,
    CemeteryRegistryCollection,
    CemeteryRegistryRepository,
)
from gda.repository.collection import BaseSourceCollection
from gda.repository.education import (
    AcademicCredentialCollection,
    AcademicCredentialRepository,
)
from gda.repository.entity import (
    FactRepository,
    FamilyRepository,
    IndividualRepository,
    LocationRepository,
    OrganizationRepository,
    SiteRepository,
)
from gda.repository.enumerated import (
    DirectoryRollCollection,
    DirectoryRollRepository,
    PopulationScheduleCollection,
    PopulationScheduleRepository,
    SupplementalScheduleCollection,
    SupplementalScheduleRepository,
    TaxAssessmentCollection,
    TaxAssessmentRepository,
)
from gda.repository.errors import (
    DuplicateRecordError,
    QueryValidationError,
    RecordNotFoundError,
    RepositoryError,
)
from gda.repository.immigration import (
    ImmigrationManifestCollection,
    ImmigrationManifestRepository,
    NaturalizationCollection,
    NaturalizationRepository,
)
from gda.repository.land import (
    LandDeedCollection,
    LandDeedRepository,
    LandGrantCollection,
    LandGrantRepository,
)
from gda.repository.manuscripts import (
    FamilyBibleCollection,
    FamilyBibleRepository,
    NarrativeManuscriptCollection,
    NarrativeManuscriptRepository,
)
from gda.repository.military import (
    BountyLandWarrantCollection,
    BountyLandWarrantRepository,
    MilitaryAwardCollection,
    MilitaryAwardRepository,
    MilitaryCasualtyCollection,
    MilitaryCasualtyRepository,
    MilitaryDraftCollection,
    MilitaryDraftRepository,
    MilitaryPensionCollection,
    MilitaryPensionRepository,
    MilitaryServiceCollection,
    MilitaryServiceRepository,
)
from gda.repository.orgs import (
    OrganizationMembershipCollection,
    OrganizationMembershipRepository,
    OrganizationRosterCollection,
    OrganizationRosterRepository,
)
from gda.repository.other import (
    OtherMiscellaneousCollection,
    OtherMiscellaneousRepository,
)
from gda.repository.probate import (
    EstateInventoryCollection,
    EstateInventoryRepository,
    ProbateCollection,
    ProbateRepository,
)
from gda.repository.publications import (
    NewspaperClipCollection,
    NewspaperClipRepository,
    PeriodicalArticleCollection,
    PeriodicalArticleRepository,
    PublicationCollection,
    PublicationRepository,
)
from gda.repository.query import (
    FilterOp,
    QueryBuilder,
    SortOrder,
    build_insert_sql,
    build_upsert_sql,
    validate_sql_identifier,
)
from gda.repository.vital import (
    BaptismCollection,
    BaptismRepository,
    BirthCollection,
    BirthRepository,
    DeathCollection,
    DeathRepository,
    DivorceCollection,
    DivorceRepository,
    MarriageCollection,
    MarriageRepository,
)
from gda.repository.xref import (
    FactParticipantXRefRepository,
    IndividualFamilyXRefRepository,
    IndividualOrganizationXRefRepository,
    IndividualSourceXRefRepository,
    IndividualSurnameXRefRepository,
    LocationXRefRepository,
    MediaXRefRepository,
    SiteXRefRepository,
    SurnameXRefRepository,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "AcademicCredentialCollection",
    "AcademicCredentialRepository",
    "BaptismCollection",
    "BaptismRepository",
    "BaseSQLiteRepository",
    "BaseSourceCollection",
    "BirthCollection",
    "BirthRepository",
    "BountyLandWarrantCollection",
    "BountyLandWarrantRepository",
    "CemeteryMarkerCollection",
    "CemeteryMarkerRepository",
    "CemeteryRegistryCollection",
    "CemeteryRegistryRepository",
    "DeathCollection",
    "DeathRepository",
    "DirectoryRollCollection",
    "DirectoryRollRepository",
    "DivorceCollection",
    "DivorceRepository",
    "DuplicateRecordError",
    "EstateInventoryCollection",
    "EstateInventoryRepository",
    "FactParticipantXRefRepository",
    "FactRepository",
    "FamilyBibleCollection",
    "FamilyBibleRepository",
    "FamilyRepository",
    "FilterOp",
    "ImmigrationManifestCollection",
    "ImmigrationManifestRepository",
    "IndividualFamilyXRefRepository",
    "IndividualOrganizationXRefRepository",
    "IndividualRepository",
    "IndividualSourceXRefRepository",
    "IndividualSurnameXRefRepository",
    "LandDeedCollection",
    "LandDeedRepository",
    "LandGrantCollection",
    "LandGrantRepository",
    "LocationRepository",
    "LocationXRefRepository",
    "MarriageCollection",
    "MarriageRepository",
    "MediaXRefRepository",
    "MilitaryAwardCollection",
    "MilitaryAwardRepository",
    "MilitaryCasualtyCollection",
    "MilitaryCasualtyRepository",
    "MilitaryDraftCollection",
    "MilitaryDraftRepository",
    "MilitaryPensionCollection",
    "MilitaryPensionRepository",
    "MilitaryServiceCollection",
    "MilitaryServiceRepository",
    "NarrativeManuscriptCollection",
    "NarrativeManuscriptRepository",
    "NaturalizationCollection",
    "NaturalizationRepository",
    "NewspaperClipCollection",
    "NewspaperClipRepository",
    "OrganizationMembershipCollection",
    "OrganizationMembershipRepository",
    "OrganizationRepository",
    "OrganizationRosterCollection",
    "OrganizationRosterRepository",
    "OtherMiscellaneousCollection",
    "OtherMiscellaneousRepository",
    "PeriodicalArticleCollection",
    "PeriodicalArticleRepository",
    "PopulationScheduleCollection",
    "PopulationScheduleRepository",
    "ProbateCollection",
    "ProbateRepository",
    "PublicationCollection",
    "PublicationRepository",
    "QueryBuilder",
    "QueryValidationError",
    "RecordNotFoundError",
    "RepositoryError",
    "SiteRepository",
    "SiteXRefRepository",
    "SortOrder",
    "SupplementalScheduleCollection",
    "SupplementalScheduleRepository",
    "SurnameXRefRepository",
    "TaxAssessmentCollection",
    "TaxAssessmentRepository",
    "build_insert_sql",
    "build_upsert_sql",
    "validate_sql_identifier",
]
