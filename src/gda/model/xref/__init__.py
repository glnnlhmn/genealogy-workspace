"""Path: src/gda/model/xref/__init__.py

Cross-reference bridge and derived index models for the GDA domain layer.

Operational Role:
    Exports immutable cross-reference and index dataclasses and target ID type
    aliases for entity, fact, family, source, media, organization, geographic,
    and onomastic lookups.
"""

from __future__ import annotations

from gda.model.xref.fact_participant_xref import FactParticipantXRef
from gda.model.xref.individual_family_xref import IndividualFamilyXRef
from gda.model.xref.individual_organization_xref import IndividualOrganizationXRef
from gda.model.xref.individual_source_xref import IndividualSourceXRef
from gda.model.xref.individual_surname_xref import IndividualSurnameXRef
from gda.model.xref.location_xref import LocationTargetID, LocationXRef
from gda.model.xref.media_xref import MediaTargetID, MediaXRef
from gda.model.xref.site_xref import SiteTargetID, SiteXRef
from gda.model.xref.surname_xref import SurnameXRef

__version__ = "1.0.0+build.10"

__all__ = [
    "FactParticipantXRef",  # fact_participant_xref.py
    "IndividualFamilyXRef",  # individual_family_xref.py
    "IndividualOrganizationXRef",  # individual_organization_xref.py
    "IndividualSourceXRef",  # individual_source_xref.py
    "IndividualSurnameXRef",  # individual_surname_xref.py
    "LocationTargetID",  # location_xref.py
    "LocationXRef",  # location_xref.py
    "MediaTargetID",  # media_xref.py
    "MediaXRef",  # media_xref.py
    "SiteTargetID",  # site_xref.py
    "SiteXRef",  # site_xref.py
    "SurnameXRef",  # surname_xref.py
]
