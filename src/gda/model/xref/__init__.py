"""Path: src/gda/model/xref/__init__.py

Cross-reference and relational edge models for the genealogical digital archive.
"""

from __future__ import annotations

from gda.model.xref.fact_participant_xref import FactParticipantXRef
from gda.model.xref.individual_family_xref import IndividualFamilyXRef
from gda.model.xref.media_xref import MediaXRef

__version__ = "1.0.0+build.4"

__all__ = [
    "FactParticipantXRef",
    "IndividualFamilyXRef",
    "MediaXRef",
]
