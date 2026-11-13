"""Path: src/gda/model/orgs/__init__.py

Institutional, religious, fraternal, cultural, and civil organization models.

Operational Role:
    Exports the canonical Organization entity model alongside evidentiary
    OrganizationMembershipRecord and tabulated OrganizationRosterRecord /
    OrganizationRosterEntry domain models.
"""

from __future__ import annotations

from gda.model.orgs.membership import OrganizationMembershipRecord
from gda.model.orgs.organization import Organization, OrganizationEntityModel
from gda.model.orgs.roster import OrganizationRosterEntry, OrganizationRosterRecord

__version__ = "1.1.0+build.1"

__all__ = [
    "Organization",
    "OrganizationEntityModel",
    "OrganizationMembershipRecord",
    "OrganizationRosterEntry",
    "OrganizationRosterRecord",
]
