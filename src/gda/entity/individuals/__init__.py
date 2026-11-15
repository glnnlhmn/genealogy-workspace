"""Path: src/gda/entity/individuals/__init__.py

Authoritative individual persona entity management subpackage.

Operational Role:
    Exposes top-level public interfaces for in-memory individual collection
    management, surname and vital-place indexing, validation routines,
    persistence gateways, and domain error hierarchies.
"""

from __future__ import annotations

from gda.entity.individuals.collection import Individuals
from gda.entity.individuals.errors import (
    IndividualError,
    IndividualNotFoundError,
    IndividualValidationError,
)
from gda.entity.individuals.util import (
    can_tombstone,
    can_undelete,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_individual,
    undelete_individual,
)
from gda.entity.individuals.validation import (
    valid_collection_all,
    valid_collection_indexes,
    valid_collection_references,
    valid_collection_tombstones,
    valid_individual,
    valid_urn,
)

__version__ = "1.0.0+build.1"

__all__ = [
    "IndividualError",  # errors.py
    "IndividualNotFoundError",  # errors.py
    "IndividualValidationError",  # errors.py
    "Individuals",  # collection.py
    "can_tombstone",  # util.py
    "can_undelete",  # util.py
    "export_file",  # util.py
    "import_file",  # util.py
    "load_from_db",  # util.py
    "save_to_db",  # util.py
    "tombstone_individual",  # util.py
    "undelete_individual",  # util.py
    "valid_collection_all",  # validation.py
    "valid_collection_indexes",  # validation.py
    "valid_collection_references",  # validation.py
    "valid_collection_tombstones",  # validation.py
    "valid_individual",  # validation.py
    "valid_urn",  # validation.py
]
