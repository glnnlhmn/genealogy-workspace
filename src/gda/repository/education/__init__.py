"""Path: src/gda/repository/education/__init__.py

SQLite repository and in-memory collection for Education archival source records.
"""

from __future__ import annotations

from gda.repository.education.collection import AcademicCredentialCollection
from gda.repository.education.repository import AcademicCredentialRepository

__version__ = "1.0.0+build.2"

__all__ = [
    "AcademicCredentialCollection",
    "AcademicCredentialRepository",
]
