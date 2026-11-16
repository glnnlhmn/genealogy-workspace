"""Path: src/gda/model/source/education/__init__.py

Historical diplomas, graduation certificates, yearbooks, and educational credentials.

Operational Role:
    Exports AcademicCredentialRecord domain model.
"""

from __future__ import annotations

from gda.model.source.education.credential import AcademicCredentialRecord

__version__ = "1.0.0+build.3"

__all__ = [
    "AcademicCredentialRecord",  # gda.model.source.education.credential
]
