"""Path: src/gda/entity/organizations/__init__.py

Authoritative voluntary association and institutional organization entity management subpackage.

Operational Role:
    Exposes top-level public interfaces for in-memory collection management,
    optional parent/child chapter hierarchies, validation routines, persistence
    gateways, and domain error hierarchies.
"""

from __future__ import annotations

from gda.entity.organizations.collection import Organizations
from gda.entity.organizations.errors import (
    OrganizationError,
    OrganizationHierarchyError,
    OrganizationNotFoundError,
    OrganizationValidationError,
)
from gda.entity.organizations.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_organization,
    undelete_organization,
)
from gda.entity.organizations.validation import (
    valid_collection_all,
    valid_collection_hierarchy,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_organization,
    valid_urn,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "OrganizationError",  # errors.py
    "OrganizationHierarchyError",  # errors.py
    "OrganizationNotFoundError",  # errors.py
    "OrganizationValidationError",  # errors.py
    "Organizations",  # collection.py
    "can_tombstone",  # util.py
    "can_undelete",  # util.py
    "export_file",  # util.py
    "import_file",  # util.py
    "load_from_db",  # util.py
    "save_to_db",  # util.py
    "tombstone_organization",  # util.py
    "undelete_organization",  # util.py
    "valid_collection_all",  # validation.py
    "valid_collection_hierarchy",  # validation.py
    "valid_collection_indexes",  # validation.py
    "valid_collection_references",  # validation.py
    "valid_collection_tombstones",  # validation.py
    "valid_organization",  # validation.py
    "valid_urn",  # validation.py
]
