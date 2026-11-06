"""Path: src/gda/entity/locations/__init__.py

Locations domain entity package exposing collection, utility, and validation entry points.
"""

from __future__ import annotations

from gda.entity.locations.collection import Locations
from gda.entity.locations.errors import (
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
)
from gda.entity.locations.util import (
    clean_string,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    slugify,
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
)

__version__ = "1.0.0+build.5"

__all__ = [
    "LocationError",
    "LocationHierarchyError",
    "LocationNotFoundError",
    "Locations",
    "clean_string",
    "export_file",
    "import_file",
    "load_from_db",
    "save_to_db",
    "slugify",
    "valid_collection_all",
    "valid_collection_cycles",
    "valid_collection_indexes",
    "valid_collection_patterns",
    "valid_collection_roots",
    "valid_collection_tombstones",
    "valid_display_text",
    "valid_hierarchy",
    "valid_urn",
]
