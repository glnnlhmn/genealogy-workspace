"""Path: src/gda/entity/families/__init__.py

Authoritative domestic family unit entity management subpackage.

Operational Role:
    Exposes top-level public interfaces for in-memory family collection
    management, partner and child indexing, validation routines, persistence
    gateways, and domain error hierarchies.
"""

from __future__ import annotations

from gda.entity.families.collection import Families
from gda.entity.families.errors import (
    FamilyError,
    FamilyNotFoundError,
    FamilyValidationError,
)
from gda.entity.families.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_family,
    undelete_family,
)
from gda.entity.families.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_family,
    valid_urn,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "Families",  # collection.py
    "FamilyError",  # errors.py
    "FamilyNotFoundError",  # errors.py
    "FamilyValidationError",  # errors.py
    "can_tombstone",  # util.py
    "can_undelete",  # util.py
    "export_file",  # util.py
    "import_file",  # util.py
    "load_from_db",  # util.py
    "save_to_db",  # util.py
    "tombstone_family",  # util.py
    "undelete_family",  # util.py
    "valid_collection_all",  # validation.py
    "valid_collection_indexes",  # validation.py
    "valid_collection_references",  # validation.py
    "valid_collection_tombstones",  # validation.py
    "valid_family",  # validation.py
    "valid_urn",  # validation.py
]
