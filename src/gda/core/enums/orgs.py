"""Path: src/gda/core/enums/orgs.py

Categorical enumerations for voluntary associations, religious bodies, and societies.

Operational Role:
    Defines controlled vocabularies for organization typologies (fraternal lodges,
    religious congregations and movements, choirs/cultural societies, civic clubs,
    labor guilds, veterans' posts), affiliation roles, and membership statuses.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.1"

__all__ = [
    "AffiliationType",
    "MembershipStatus",
    "OrganizationCategory",
]


class OrganizationCategory(StrEnum):
    """Taxonomic classification of human associations, societies, and institutions."""

    FRATERNAL = "FRATERNAL"
    RELIGIOUS = "RELIGIOUS"
    CULTURAL_ARTS = "CULTURAL_ARTS"
    CIVIC_SERVICE = "CIVIC_SERVICE"
    LABOR_GUILD = "LABOR_GUILD"
    VETERANS = "VETERANS"
    MUTUAL_AID = "MUTUAL_AID"
    EDUCATIONAL = "EDUCATIONAL"
    POLITICAL = "POLITICAL"
    OTHER = "OTHER"


class MembershipStatus(StrEnum):
    """Standing or lifecycle status of an individual's affiliation with an organization."""

    ACTIVE = "ACTIVE"
    CHARTER = "CHARTER"
    INITIATED = "INITIATED"
    DEMITTED = "DEMITTED"
    SUSPENDED = "SUSPENDED"
    EXPELLED = "EXPELLED"
    INACTIVE = "INACTIVE"
    DECEASED = "DECEASED"
    HONORARY = "HONORARY"
    UNKNOWN = "UNKNOWN"


class AffiliationType(StrEnum):
    """Functional capacity in which an individual participated in an organization."""

    MEMBER = "MEMBER"
    OFFICER = "OFFICER"
    CLERGY_MINISTER = "CLERGY_MINISTER"
    DIRECTOR_LEADER = "DIRECTOR_LEADER"
    CANDIDATE_NOVICE = "CANDIDATE_NOVICE"
    BENEFACTOR_PATRON = "BENEFACTOR_PATRON"
    GUEST_VISITOR = "GUEST_VISITOR"
    OTHER = "OTHER"
