"""Path: src/gda/entity/facts/__init__.py

Authoritative evidentiary fact entity management subpackage.

Operational Role:
    Exposes top-level public interfaces for in-memory fact collection
    management, timeline and participant indexing, validation routines,
    persistence gateways, and domain error hierarchies.
"""

from __future__ import annotations

from gda.entity.facts.collection import Facts
from gda.entity.facts.errors import (
    FactError,
    FactNotFoundError,
    FactValidationError,
)
from gda.entity.facts.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_fact,
    undelete_fact,
)
from gda.entity.facts.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_fact,
    valid_urn,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "FactError",  # errors.py
    "FactNotFoundError",  # errors.py
    "FactValidationError",  # errors.py
    "Facts",  # collection.py
    "can_tombstone",  # util.py
    "can_undelete",  # util.py
    "export_file",  # util.py
    "import_file",  # util.py
    "load_from_db",  # util.py
    "save_to_db",  # util.py
    "tombstone_fact",  # util.py
    "undelete_fact",  # util.py
    "valid_collection_all",  # validation.py
    "valid_collection_indexes",  # validation.py
    "valid_collection_references",  # validation.py
    "valid_collection_tombstones",  # validation.py
    "valid_fact",  # validation.py
    "valid_urn",  # validation.py
]
