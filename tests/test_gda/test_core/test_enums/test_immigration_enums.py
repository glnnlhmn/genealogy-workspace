"""Path: tests/test_gda/test_core/test_enums/test_immigration_enums.py

Targeted behavioral test suite verifying immigration and naturalization enums.

Operational Role:
    Validates ArrivalPassageClass and NaturalizationStage enum member tokens,
    StrEnum inheritance, and package re-export parity.
"""

from __future__ import annotations

import pytest

import gda.core.enums as enums_pkg
import gda.core.enums.immigration as imm_enums
from gda.core.enums.immigration import (
    ArrivalPassageClass,
    NaturalizationStage,
)

__version__ = "1.0.0+build.1"


@pytest.mark.unit
@pytest.mark.smoke
def test_arrival_passage_class_tokens() -> None:
    """Verify passenger and crew passage classifications on arrival manifests."""
    assert ArrivalPassageClass.STEERAGE == "STEERAGE"
    assert ArrivalPassageClass.CABIN == "CABIN"
    assert ArrivalPassageClass.SECOND_CABIN == "SECOND_CABIN"
    assert ArrivalPassageClass.CREW == "CREW"
    assert ArrivalPassageClass.OVERLAND == "OVERLAND"
    assert ArrivalPassageClass.OTHER == "OTHER"
    assert len(ArrivalPassageClass) == 6


@pytest.mark.unit
def test_naturalization_stage_tokens_and_reexports() -> None:
    """Verify procedural naturalization stage tokens and package re-export parity."""
    assert imm_enums.__all__ == sorted(imm_enums.__all__)
    for name in imm_enums.__all__:
        assert getattr(enums_pkg, name) is getattr(imm_enums, name)

    assert NaturalizationStage.DECLARATION_OF_INTENTION == "DECLARATION_OF_INTENTION"
    assert NaturalizationStage.PETITION == "PETITION"
    assert NaturalizationStage.DEPOSITION_OF_WITNESS == "DEPOSITION_OF_WITNESS"
    assert NaturalizationStage.OATH_OF_ALLEGIANCE == "OATH_OF_ALLEGIANCE"
    assert NaturalizationStage.CERTIFICATE == "CERTIFICATE"
    assert NaturalizationStage.DENIAL_OR_DISMISSAL == "DENIAL_OR_DISMISSAL"
    assert len(NaturalizationStage) == 6
