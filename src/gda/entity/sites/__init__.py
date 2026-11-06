"""Path: src/gda/entity/sites/__init__.py

Authoritative physical site entity management subpackage.

Operational Role:
    Exposes top-level public interfaces for in-memory collection management,
    validation routines, persistence gateways, and domain error hierarchies.
"""

from __future__ import annotations

from gda.entity.sites.collection import Sites
from gda.entity.sites.errors import (
    SiteError,
    SiteNotFoundError,
    SiteValidationError,
)
from gda.entity.sites.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_site,
    undelete_site,
)
from gda.entity.sites.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_locations,
    valid_collection_tombstones,
    valid_site,
    valid_site_address,
    valid_urn,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "SiteError",
    "SiteNotFoundError",
    "SiteValidationError",
    "Sites",
    "can_tombstone",
    "can_undelete",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "tombstone_site",
    "undelete_site",
    "valid_collection_all",
    "valid_collection_indexes",
    "valid_collection_locations",
    "valid_collection_tombstones",
    "valid_site",
    "valid_site_address",
    "valid_urn",
]
