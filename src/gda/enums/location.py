"""Path: src/gda/enums/location.py

Categorical enumerations for jurisdictional boundaries and administrative tiers.

Operational Role:
    Defines controlled categorical tiers for civil and geographical entities.
"""

from __future__ import annotations

from enum import StrEnum

__version__ = "1.0.0+build.1"

__all__ = ["JurisdictionCategory"]


class JurisdictionCategory(StrEnum):
    """Hierarchical administrative categorization for civil jurisdictions."""

    COUNTRY = "COUNTRY"
    STATOID = "STATOID"
    COUNTY_EQUIVALENT = "COUNTY_EQUIVALENT"
    CIVIL_TOWNSHIP = "CIVIL_TOWNSHIP"
    MUNICIPALITY = "MUNICIPALITY"
    UNINCORPORATED_PLACE = "UNINCORPORATED_PLACE"
    SPECIAL_DISTRICT = "SPECIAL_DISTRICT"

    @property
    def administrative_rank(self) -> int:
        """Return numerical hierarchy ranking (lower number = higher administrative tier)."""
        ranks = {
            self.COUNTRY: 10,
            self.STATOID: 20,
            self.COUNTY_EQUIVALENT: 30,
            self.CIVIL_TOWNSHIP: 40,
            self.MUNICIPALITY: 40,
            self.UNINCORPORATED_PLACE: 50,
            self.SPECIAL_DISTRICT: 60,
        }
        return ranks[self]
