"""Path: src/gda/model/__init__.py

Authoritative five-pillar domain model suite for the Genealogy Digital Archive.

Operational Role:
    Top-level package facade uniting the five architectural tiers of the GDA
    domain model:
    - atom: Tier-0 immutable scalar, temporal, geospatial, URN, and ID primitives.
    - base: Tier-1/2 composite value objects, base entities, and registry envelopes.
    - entity: Tier-3 master domain graph entities (Fact, Family, Individual,
      Location, Organization, Site).
    - source: Tier-3 documentary archival source records across 12 historical domains.
    - xref: Tier-4 derived cross-reference and relational index bridges.
"""

from __future__ import annotations

from gda.model import (
    atom,
    base,
    entity,
    source,
    xref,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "atom",  # subpackage
    "base",  # subpackage
    "entity",  # subpackage
    "source",  # subpackage
    "xref",  # subpackage
]
