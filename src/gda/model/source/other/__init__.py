"""Path: src/gda/model/source/other/__init__.py

Flexible catch-all models for miscellaneous historical records, ephemera, and untyped items.

Operational Role:
    Exports OtherMiscellaneousRecord domain model.
"""

from __future__ import annotations

from gda.model.source.other.miscellaneous import OtherMiscellaneousRecord

__version__ = "1.0.0+build.2"

__all__ = [
    "OtherMiscellaneousRecord",  # gda.model.source.other.miscellaneous
]
