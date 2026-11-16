"""Path: src/gda/entity/locations/__init__.py

Authoritative jurisdiction and location entity management subpackage.

Operational Role:
    Exposes top-level public interfaces for in-memory collection management,
    hierarchy builders, validation routines, persistence gateways, and
    domain error hierarchies.
"""

from __future__ import annotations

from gda.entity.locations.collection import Locations
from gda.entity.locations.errors import (
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
)
from gda.entity.locations.util import (
    build_jurisdiction_hierarchy,
    can_tombstone,
    can_undelete,
    clean_string,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    slugify,
    tombstone_location,
    undelete_location,
)
from gda.entity.locations.validation import (
    valid_collection_all,
    valid_collection_cycles,
    valid_collection_indexes,
    valid_collection_patterns,
    valid_collection_roots,
    valid_collection_tombstones,
    valid_display_text,
    valid_hierarchy,
    valid_urn,
    validate_urn_tier_sequence,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "LocationError",  # errors.py
    "LocationHierarchyError",  # errors.py
    "LocationNotFoundError",  # errors.py
    "Locations",  # collection.py
    "build_jurisdiction_hierarchy",  # util.py
    "can_tombstone",  # util.py
    "can_undelete",  # util.py
    "clean_string",  # util.py
    "export_file",  # util.py
    "import_file",  # util.py
    "load_from_db",  # util.py
    "save_to_db",  # util.py
    "slugify",  # util.py
    "tombstone_location",  # util.py
    "undelete_location",  # util.py
    "valid_collection_all",  # validation.py
    "valid_collection_cycles",  # validation.py
    "valid_collection_indexes",  # validation.py
    "valid_collection_patterns",  # validation.py
    "valid_collection_roots",  # validation.py
    "valid_collection_tombstones",  # validation.py
    "valid_display_text",  # validation.py
    "valid_hierarchy",  # validation.py
    "valid_urn",  # validation.py
    "validate_urn_tier_sequence",  # validation.py
]
