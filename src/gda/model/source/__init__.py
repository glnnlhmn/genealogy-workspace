"""Path: src/gda/model/source/__init__.py

Archival documentary source record models across all historical domains.

Operational Role:
    Unified public export facade for Tier-3 documentary SourceRecord and
    EnumeratedRollRecord models across all 12 archival domains: cemetery,
    education, enumerated (census, directories, taxes), immigration, land,
    manuscripts, military (awards, casualty, draft, pension, service),
    orgs (membership, roster), other, probate, publications, and vital.
"""

from __future__ import annotations

from gda.model.source import (
    cemetery,
    education,
    enumerated,
    immigration,
    land,
    manuscripts,
    military,
    orgs,
    other,
    probate,
    publications,
    vital,
)
from gda.model.source.cemetery import (
    CemeteryMarkerRecord,
    CemeteryPlotEntry,
    CemeteryRegistryRecord,
    MarkerInterment,
    RegistryInterment,
)
from gda.model.source.education import AcademicCredentialRecord
from gda.model.source.enumerated import (
    AgriculturalScheduleEntry,
    AgriculturalScheduleRecord,
    AssessedProperty,
    CensusLineEntry,
    CensusScheduleRecord,
    DirectoryEntry,
    DirectoryRollRecord,
    EnumeratedRollRecord,
    HouseholdTallyEntry,
    ManufacturingScheduleEntry,
    ManufacturingScheduleRecord,
    MortalityScheduleEntry,
    MortalityScheduleRecord,
    Population1850_1870Entry,
    Population1880Entry,
    Population1900_1910Entry,
    Population1920Entry,
    Population1930Entry,
    Population1940Entry,
    Population1950Entry,
    PopulationLineEntry,
    PopulationSchedule1790_1840,
    PopulationSchedule1850_1870,
    PopulationSchedule1880,
    PopulationSchedule1900_1910,
    PopulationSchedule1920,
    PopulationSchedule1930,
    PopulationSchedule1940,
    PopulationSchedule1950,
    PopulationScheduleRecord,
    SeptennialCensusRecord,
    SlaveScheduleEntry,
    SlaveScheduleRecord,
    TaxAssessmentRecord,
    Veterans1890Entry,
    Veterans1890ScheduleRecord,
)
from gda.model.source.immigration import (
    ImmigrationManifestRecord,
    ManifestPassenger,
    NaturalizationRecord,
    NaturalizationWitness,
)
from gda.model.source.land import (
    DeedParty,
    LandDeedRecord,
    LandGrantRecord,
    LandParcel,
)
from gda.model.source.manuscripts import (
    BibleRegisterEntry,
    FamilyBibleRecord,
    NarrativeManuscriptRecord,
)
from gda.model.source.military import (
    BountyLandWarrantRecord,
    CivilWarDraftRecord,
    ColonialMilitiaRecord,
    CombatCasualtyRecord,
    EnlistmentMusterRecord,
    MilitaryAwardRecord,
    MilitaryBurialRecord,
    MilitaryCasualtyRecord,
    MilitaryDraftRecord,
    MilitaryPensionRecord,
    MilitaryServiceRecord,
    ModernSelectiveServiceRecord,
    PensionVeteranClaimRecord,
    PensionWidowDependentRecord,
    PrisonerOfWarRecord,
    SeparationDischargeRecord,
    WwiDraftCardRecord,
    WwiiDraftCardRecord,
    WwiiPhysicalMetrics,
    WwiPhysicalDescription,
)
from gda.model.source.orgs import (
    OrganizationMembershipRecord,
    OrganizationRosterEntry,
    OrganizationRosterRecord,
)
from gda.model.source.other import OtherMiscellaneousRecord
from gda.model.source.probate import (
    EstateInventoryRecord,
    InventoryLineItem,
    ProbateLedgerEntry,
    ProbateRecord,
    WillBequest,
)
from gda.model.source.publications import (
    NewspaperClipRecord,
    PeriodicalArticleRecord,
    Publication,
    PublicationEntry,
)
from gda.model.source.vital import (
    BaptismRecord,
    BirthRecord,
    DeathRecord,
    DivorceRecord,
    MarriageRecord,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "AcademicCredentialRecord",  # education
    "AgriculturalScheduleEntry",  # enumerated
    "AgriculturalScheduleRecord",  # enumerated
    "AssessedProperty",  # enumerated
    "BaptismRecord",  # vital
    "BibleRegisterEntry",  # manuscripts
    "BirthRecord",  # vital
    "BountyLandWarrantRecord",  # military
    "CemeteryMarkerRecord",  # cemetery
    "CemeteryPlotEntry",  # cemetery
    "CemeteryRegistryRecord",  # cemetery
    "CensusLineEntry",  # enumerated
    "CensusScheduleRecord",  # enumerated
    "CivilWarDraftRecord",  # military
    "ColonialMilitiaRecord",  # military
    "CombatCasualtyRecord",  # military
    "DeathRecord",  # vital
    "DeedParty",  # land
    "DirectoryEntry",  # enumerated
    "DirectoryRollRecord",  # enumerated
    "DivorceRecord",  # vital
    "EnlistmentMusterRecord",  # military
    "EnumeratedRollRecord",  # enumerated
    "EstateInventoryRecord",  # probate
    "FamilyBibleRecord",  # manuscripts
    "HouseholdTallyEntry",  # enumerated
    "ImmigrationManifestRecord",  # immigration
    "InventoryLineItem",  # probate
    "LandDeedRecord",  # land
    "LandGrantRecord",  # land
    "LandParcel",  # land
    "ManifestPassenger",  # immigration
    "ManufacturingScheduleEntry",  # enumerated
    "ManufacturingScheduleRecord",  # enumerated
    "MarkerInterment",  # cemetery
    "MarriageRecord",  # vital
    "MilitaryAwardRecord",  # military
    "MilitaryBurialRecord",  # military
    "MilitaryCasualtyRecord",  # military
    "MilitaryDraftRecord",  # military
    "MilitaryPensionRecord",  # military
    "MilitaryServiceRecord",  # military
    "ModernSelectiveServiceRecord",  # military
    "MortalityScheduleEntry",  # enumerated
    "MortalityScheduleRecord",  # enumerated
    "NarrativeManuscriptRecord",  # manuscripts
    "NaturalizationRecord",  # immigration
    "NaturalizationWitness",  # immigration
    "NewspaperClipRecord",  # publications
    "OrganizationMembershipRecord",  # orgs
    "OrganizationRosterEntry",  # orgs
    "OrganizationRosterRecord",  # orgs
    "OtherMiscellaneousRecord",  # other
    "PensionVeteranClaimRecord",  # military
    "PensionWidowDependentRecord",  # military
    "PeriodicalArticleRecord",  # publications
    "Population1850_1870Entry",  # enumerated
    "Population1880Entry",  # enumerated
    "Population1900_1910Entry",  # enumerated
    "Population1920Entry",  # enumerated
    "Population1930Entry",  # enumerated
    "Population1940Entry",  # enumerated
    "Population1950Entry",  # enumerated
    "PopulationLineEntry",  # enumerated
    "PopulationSchedule1790_1840",  # enumerated
    "PopulationSchedule1850_1870",  # enumerated
    "PopulationSchedule1880",  # enumerated
    "PopulationSchedule1900_1910",  # enumerated
    "PopulationSchedule1920",  # enumerated
    "PopulationSchedule1930",  # enumerated
    "PopulationSchedule1940",  # enumerated
    "PopulationSchedule1950",  # enumerated
    "PopulationScheduleRecord",  # enumerated
    "PrisonerOfWarRecord",  # military
    "ProbateLedgerEntry",  # probate
    "ProbateRecord",  # probate
    "Publication",  # publications
    "PublicationEntry",  # publications
    "RegistryInterment",  # cemetery
    "SeparationDischargeRecord",  # military
    "SeptennialCensusRecord",  # enumerated
    "SlaveScheduleEntry",  # enumerated
    "SlaveScheduleRecord",  # enumerated
    "TaxAssessmentRecord",  # enumerated
    "Veterans1890Entry",  # enumerated
    "Veterans1890ScheduleRecord",  # enumerated
    "WillBequest",  # probate
    "WwiDraftCardRecord",  # military
    "WwiPhysicalDescription",  # military
    "WwiiDraftCardRecord",  # military
    "WwiiPhysicalMetrics",  # military
    "cemetery",  # subpackage
    "education",  # subpackage
    "enumerated",  # subpackage
    "immigration",  # subpackage
    "land",  # subpackage
    "manuscripts",  # subpackage
    "military",  # subpackage
    "orgs",  # subpackage
    "other",  # subpackage
    "probate",  # subpackage
    "publications",  # subpackage
    "vital",  # subpackage
]
