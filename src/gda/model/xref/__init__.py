"""Path: src/gda/model/xref/__init__.py

Cross-reference bridge and derived index models for the GDA domain layer.

Operational Role:
    Exports immutable cross-reference and index dataclasses for entity,
    fact, family, source, media, organization, geographic, and onomastic lookups.
"""

from __future__ import annotations

from gda.model.xref.fact_participant_xref import FactParticipantXRef
from gda.model.xref.individual_family_xref import IndividualFamilyXRef
from gda.model.xref.individual_organization_xref import IndividualOrganizationXRef
from gda.model.xref.individual_source_xref import IndividualSourceXRef
from gda.model.xref.individual_surname_xref import IndividualSurnameXRef
from gda.model.xref.location_xref import LocationXRef
from gda.model.xref.media_xref import MediaXRef
from gda.model.xref.site_xref import SiteXRef
from gda.model.xref.surname_xref import SurnameXRef

__version__ = "1.0.0+build.9"

__all__ = [
    "FactParticipantXRef",
    "IndividualFamilyXRef",
    "IndividualOrganizationXRef",
    "IndividualSourceXRef",
    "IndividualSurnameXRef",
    "LocationXRef",
    "MediaXRef",
    "SiteXRef",
    "SurnameXRef",
]
