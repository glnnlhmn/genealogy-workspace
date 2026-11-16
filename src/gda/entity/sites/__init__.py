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

__version__ = "1.0.0+build.2"

__all__ = [
    "SiteError",  # errors.py
    "SiteNotFoundError",  # errors.py
    "SiteValidationError",  # errors.py
    "Sites",  # collection.py
    "can_tombstone",  # util.py
    "can_undelete",  # util.py
    "export_file",  # util.py
    "import_file",  # util.py
    "load_from_db",  # util.py
    "save_to_db",  # util.py
    "tombstone_site",  # util.py
    "undelete_site",  # util.py
    "valid_collection_all",  # validation.py
    "valid_collection_indexes",  # validation.py
    "valid_collection_locations",  # validation.py
    "valid_collection_tombstones",  # validation.py
    "valid_site",  # validation.py
    "valid_site_address",  # validation.py
    "valid_urn",  # validation.py
]
