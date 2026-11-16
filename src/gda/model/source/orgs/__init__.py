"""Path: src/gda/model/source/orgs/__init__.py

Organizational affiliation and enumerated membership roster source records.

Operational Role:
    Exposes archival source record models for individual organizational
    memberships (OrganizationMembershipRecord) and multi-entry institutional
    rosters (OrganizationRosterEntry, OrganizationRosterRecord).
"""

from __future__ import annotations

from gda.model.source.orgs.membership import OrganizationMembershipRecord
from gda.model.source.orgs.roster import (
    OrganizationRosterEntry,
    OrganizationRosterRecord,
)

__version__ = "1.0.0+build.4"

__all__ = [
    "OrganizationMembershipRecord",  # gda.model.source.orgs.membership
    "OrganizationRosterEntry",  # gda.model.source.orgs.roster
    "OrganizationRosterRecord",  # gda.model.source.orgs.roster
]
