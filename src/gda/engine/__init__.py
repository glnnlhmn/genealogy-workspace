"""Path: src/gda/engine/__init__.py

Kinship graph analysis, plausibility engines, and relationship resolvers.
"""

from __future__ import annotations

from gda.engine.fact_resolver import FactParticipantResolver
from gda.engine.media_resolver import MediaXRefResolver
from gda.engine.resolver import IndividualFamilyResolver

__version__ = "1.0.0+build.4"

__all__ = [
    "FactParticipantResolver",
    "IndividualFamilyResolver",
    "MediaXRefResolver",
]
