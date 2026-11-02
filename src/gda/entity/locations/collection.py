"""Path: src/gda/entity/locations/collection.py

Authoritative in-memory collection and relational graph manager for location records.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    and navigating jurisdictional hierarchies of Location entities. Delegates
    persistence, hierarchy construction, and graveyard lifecycle to specialized
    sibling utility modules in gda.entity.locations.util.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.entity.locations.errors import LocationNotFoundError
from gda.entity.locations.util import (
    build_jurisdiction_hierarchy,
    clean_string,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    slugify,
    tombstone_location,
)
from gda.enums.core import SmartIDPrefix
from gda.enums.location import JurisdictionCategory
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location
from gda.util.ids import extract_max_smart_id, mint_smart_id

if TYPE_CHECKING:
    pass

__version__ = "1.0.0+build.36"

__all__ = ["Locations"]


class Locations(IntrospectableMixin):
    """Authoritative in-memory collection and relational graph for location entities."""

    def __init__(self, locations: list[Location] | None = None) -> None:
        """Initialize location registry, alias index, and URN index."""
        self._registry: dict[LocationID, Location] = {}
        self._urn_index: dict[str, LocationID] = {}
        self._alias_index: dict[str, LocationID] = {}
        self._is_dirty: bool = False

        if locations:
            for loc in locations:
                self.add(loc)

    @classmethod
    def from_database(cls) -> Locations:
        """Factory method initializing a collection and loading records from SQLite."""
        instance = cls()
        load_from_db(instance)
        return instance

    @property
    def is_dirty(self) -> bool:
        """Indicate whether the in-memory collection contains unpersisted changes."""
        return self._is_dirty

    def mark_clean(self) -> None:
        """Reset dirty state flag following database synchronization."""
        self._is_dirty = False

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) locations in the collection."""
        return sum(
            1 for loc in self._registry.values() if not loc.tombstone.is_deprecated
        )

    def __iter__(self) -> Iterator[Location]:
        """Iterate over active (non-tombstoned) locations in the collection."""
        for loc in self._registry.values():
            if not loc.tombstone.is_deprecated:
                yield loc

    def iter_all(self) -> Iterator[Location]:
        """Iterate over all locations, including tombstoned records."""
        yield from self._registry.values()

    def __contains__(self, item: LocationID | str) -> bool:
        """Check if an active location exists by LocationID, string ID, or canonical URN."""
        if isinstance(item, LocationID):
            loc = self._registry.get(item)
            return loc is not None and not loc.tombstone.is_deprecated
        if isinstance(item, str):
            if item.startswith("LOC-"):
                loc = self._registry.get(LocationID(item))
                return loc is not None and not loc.tombstone.is_deprecated
            loc_id = self._urn_index.get(item)
            if loc_id:
                loc = self._registry.get(loc_id)
                return loc is not None and not loc.tombstone.is_deprecated
        return False

    def __getitem__(self, item: LocationID | str) -> Location:
        """Retrieve an active location by LocationID, string ID, or canonical URN."""
        loc_id: LocationID | None = None
        if isinstance(item, LocationID):
            loc_id = item
        elif isinstance(item, str):
            if item.startswith("LOC-"):
                loc_id = LocationID(item)
            else:
                loc_id = self._urn_index.get(item)

        if not loc_id or loc_id not in self._registry:
            raise LocationNotFoundError(f"Location not found: {item}")

        loc = self._registry[loc_id]
        if loc.tombstone.is_deprecated:
            raise LocationNotFoundError(f"Location has been tombstoned: {item}")
        return loc

    def get(
        self, item: LocationID | str, default: Location | None = None
    ) -> Location | None:
        """Retrieve an active location by identifier, returning default if absent."""
        try:
            return self[item]
        except LocationNotFoundError:
            return default

    def add(self, location: Location) -> None:
        """Add a location entity to registry and update lookup indexes."""
        if not isinstance(location, Location):
            raise TypeError(
                f"Expected Location instance, got {type(location).__name__}"
            )

        self._registry[location.id] = location
        self._urn_index[location.canonical_urn] = location.id

        for alias in location.aliases:
            cleaned = clean_string(alias)
            if cleaned:
                self._alias_index[cleaned.lower()] = location.id

        self._is_dirty = True

    def update(self, location: Location) -> None:
        """Replace an existing entity in the collection, re-indexing aliases and URNs."""
        if not isinstance(location, Location):
            raise TypeError(
                f"Expected Location instance, got {type(location).__name__}"
            )

        target_id = location.id
        if target_id not in self._registry:
            raise LocationNotFoundError(
                f"Cannot update location '{target_id}'; not found in registry."
            )

        old_loc = self._registry[target_id]

        for old_alias in old_loc.aliases:
            cleaned = clean_string(old_alias)
            if cleaned:
                key = cleaned.lower()
                if self._alias_index.get(key) == target_id:
                    del self._alias_index[key]

        if old_loc.canonical_urn != location.canonical_urn:
            self._urn_index.pop(old_loc.canonical_urn, None)

        self.add(location)

    def soft_delete(
        self,
        item: LocationID | str,
        reason: str | None = None,
        superseded_by: LocationID | str | None = None,
    ) -> Location:
        """Soft-delete a location, enforcing category parity and cascading URN updates."""
        retired = tombstone_location(
            collection=self,
            loc_id=item,
            reason=reason or "Jurisdiction retired",
            superseded_by=superseded_by,
        )
        self._is_dirty = True
        return retired

    def load_from_db(self) -> int:
        """Populate this collection directly from SQLite via util helper."""
        return load_from_db(self)

    def save_to_db(self) -> int:
        """Persist this collection directly to SQLite via util helper and refresh clean state."""
        written = save_to_db(self)
        self.mark_clean()
        return written

    def refresh(self) -> int:
        """Reload the collection state entirely from the database."""
        self._registry.clear()
        self._urn_index.clear()
        self._alias_index.clear()
        loaded = load_from_db(self)
        self.mark_clean()
        return loaded

    def import_file(self, path: Path | str) -> int:
        """Import location entities from a formatted JSON file via util helper."""
        return import_file(self, path)

    def export_file(self, path: Path | str, include_graveyard: bool = True) -> int:
        """Export location entities to a JSON file via util helper."""
        return export_file(self, path, include_graveyard=include_graveyard)

    def create(
        self,
        name: str,
        category: JurisdictionCategory,
        parent_id: LocationID | str | None = None,
        alternate_names: list[str] | None = None,
        notes: list[Note] | None = None,
        is_primary_local_authority: bool = False,
        is_unincorporated: bool = False,
    ) -> Location:
        """Create, register, and index a new Location entity using max + 1 ID minting."""
        cleaned_name = clean_string(name)
        if not cleaned_name:
            raise ModelFormatError("Location name cannot be blank or whitespace.")

        parent_loc_id: LocationID | None = None
        parent_urn: str = "urn:gda:loc"
        if parent_id:
            parent_loc = self[parent_id]
            parent_loc_id = parent_loc.id
            parent_urn = parent_loc.canonical_urn

        segment = slugify(cleaned_name, delimiter="_")
        canonical_urn = f"{parent_urn}:{segment}"

        next_num = (
            extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.LOC) + 1
        )
        loc_id = LocationID(mint_smart_id(SmartIDPrefix.LOC, next_num))

        now = IsoTimestamp.now_utc()
        audit = AuditStamp(created_at=now, updated_at=now)

        name_obj = NameThing.create(raw=cleaned_name, canonical=cleaned_name)
        if alternate_names:
            for alt in alternate_names:
                c = clean_string(alt)
                if c:
                    name_obj = name_obj.add_alias(c)

        location = Location.create(
            location_id=loc_id,
            audit=audit,
            name=name_obj,
            category=category,
            canonical_urn=canonical_urn,
            parent_id=parent_loc_id,
            notes=notes or [],
            is_primary_local_authority=is_primary_local_authority,
            is_unincorporated=is_unincorporated,
            tombstone=Tombstone[LocationID](),
        )

        self.add(location)
        return location

    def create_hierarchy(
        self,
        country: str,
        state: str | None = None,
        county: str | None = None,
        township: str | None = None,
        local: str | None = None,
    ) -> Location:
        """Create or resolve descending jurisdictional tiers via util builder."""
        return build_jurisdiction_hierarchy(
            collection=self,
            country=country,
            state=state,
            county=county,
            township=township,
            local=local,
        )
