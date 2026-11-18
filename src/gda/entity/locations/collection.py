"""Path: src/gda/entity/locations/collection.py

Authoritative in-memory collection and relational graph manager for location records.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    undeleting, and navigating jurisdictional hierarchies of Location entities.
    Provides manager-ready graveyard inspection, supersession resolution,
    category/child/alias lookups, and dirty-entity tracking.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path

from gda.core.dates import utc_now_iso
from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.enums.location import JurisdictionCategory
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.entity.locations.errors import LocationNotFoundError
from gda.entity.locations.util import (
    build_jurisdiction_hierarchy,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_location,
    undelete_location,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.audit import AuditStamp
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.location import Location
from gda.util.ids import extract_max_smart_id, mint_smart_id, verify_id
from gda.util.text import clean_string, slugify

__version__ = "1.0.0+build.43"

__all__ = [
    "Locations",
]


class Locations(IntrospectableMixin):
    """Authoritative in-memory collection and relational graph for location entities."""

    def __init__(self, locations: list[Location] | None = None) -> None:
        """Initialize location registry and secondary URN, alias, category, and parent indexes."""
        self._registry: dict[LocationID, Location] = {}
        self._urn_index: dict[str, LocationID] = {}
        self._alias_index: dict[str, set[LocationID]] = defaultdict(set)
        self._category_index: dict[JurisdictionCategory, set[LocationID]] = defaultdict(set)
        self._parent_index: dict[LocationID, set[LocationID]] = defaultdict(set)
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
        """Reset dirty state flag on collection and all registered entities."""
        self._is_dirty = False
        for loc_id, loc in list(self._registry.items()):
            if loc.is_dirty:
                self._registry[loc_id] = loc.mark_clean()

    def dirty_entities(self) -> list[Location]:
        """Return all registered locations currently marked dirty in memory."""
        return [loc for loc in self._registry.values() if loc.is_dirty]

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) locations in the collection."""
        return sum(1 for loc in self._registry.values() if not loc.tombstone.is_deprecated)

    def __iter__(self) -> Iterator[Location]:
        """Iterate over active (non-tombstoned) locations in the collection."""
        for loc in self._registry.values():
            if not loc.tombstone.is_deprecated:
                yield loc

    def iter_all(self) -> Iterator[Location]:
        """Iterate over all locations, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_id(self, item: LocationID | str) -> LocationID | None:
        """Resolve a LocationID, string ID, or canonical URN into a LocationID if registered."""
        if isinstance(item, LocationID):
            return item if item in self._registry else None
        if isinstance(item, str):
            token = item.strip()
            if verify_id(token, id_type=IDType.SMART_ID, smart_id_prefix=SmartIDPrefix.LOC):
                cand = LocationID(token)
                return cand if cand in self._registry else None
            urn_cand = self._urn_index.get(token)
            return urn_cand if urn_cand and urn_cand in self._registry else None
        return None

    def __contains__(self, item: LocationID | str) -> bool:
        """Check if an active location exists by LocationID, string ID, or canonical URN."""
        loc_id = self._resolve_id(item)
        return loc_id is not None and not self._registry[loc_id].tombstone.is_deprecated

    def __getitem__(self, item: LocationID | str) -> Location:
        """Retrieve an active location by LocationID, string ID, or canonical URN."""
        loc_id = self._resolve_id(item)
        if not loc_id:
            raise LocationNotFoundError(f"Location not found: {item}")

        loc = self._registry[loc_id]
        if loc.tombstone.is_deprecated:
            raise LocationNotFoundError(f"Location has been tombstoned: {item}")
        return loc

    def get(self, item: LocationID | str, default: Location | None = None) -> Location | None:
        """Retrieve an active location by identifier, returning default if absent."""
        try:
            return self[item]
        except LocationNotFoundError:
            return default

    def get_any(
        self,
        item: LocationID | str,
        default: Location | None = None,
    ) -> Location | None:
        """Retrieve a location by ID or URN regardless of whether it is active or tombstoned."""
        loc_id = self._resolve_id(item)
        return self._registry[loc_id] if loc_id is not None else default

    def find_tombstoned(self) -> list[Location]:
        """Return all retired (tombstoned) locations in the graveyard."""
        return [loc for loc in self._registry.values() if loc.tombstone.is_deprecated]

    def resolve_active(self, item: LocationID | str) -> Location | None:
        """Follow superseded_by chains from an identifier to its current active Location."""
        curr = self.get_any(item)
        seen: set[LocationID] = set()
        while curr is not None and curr.tombstone.is_deprecated:
            if curr.id in seen or curr.tombstone.superseded_by is None:
                return None
            seen.add(curr.id)
            curr = self._registry.get(curr.tombstone.superseded_by)
        return curr

    def add(self, location: Location) -> None:
        """Add a location entity to registry and update lookup indexes."""
        if not isinstance(location, Location):
            raise TypeError(f"Expected Location instance, got {type(location).__name__}")

        self._registry[location.id] = location
        self._urn_index[location.canonical_urn] = location.id
        self._category_index[location.category].add(location.id)

        if location.parent_id is not None:
            self._parent_index[location.parent_id].add(location.id)

        for alias in location.aliases:
            self._alias_index[alias.lower()].add(location.id)

        self._is_dirty = True

    def update(self, location: Location) -> None:
        """Replace an existing entity in the collection, re-indexing aliases, URNs, and hierarchy."""
        if not isinstance(location, Location):
            raise TypeError(f"Expected Location instance, got {type(location).__name__}")

        target_id = location.id
        if target_id not in self._registry:
            raise LocationNotFoundError(
                f"Cannot update location '{target_id}'; not found in registry."
            )

        old_loc = self._registry[target_id]

        new_aliases = {a.lower() for a in location.aliases}
        for old_alias in old_loc.aliases:
            key = old_alias.lower()
            if key not in new_aliases and key in self._alias_index:
                self._alias_index[key].discard(target_id)
                if not self._alias_index[key]:
                    del self._alias_index[key]

        if old_loc.canonical_urn != location.canonical_urn:
            self._urn_index.pop(old_loc.canonical_urn, None)

        if old_loc.category != location.category:
            self._category_index[old_loc.category].discard(target_id)
            if not self._category_index[old_loc.category]:
                del self._category_index[old_loc.category]

        if old_loc.parent_id is not None and old_loc.parent_id != location.parent_id:
            self._parent_index[old_loc.parent_id].discard(target_id)
            if not self._parent_index[old_loc.parent_id]:
                del self._parent_index[old_loc.parent_id]

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

    def undelete(self, item: LocationID | str) -> Location:
        """Restore a tombstoned location back to active status and mark dirty."""
        restored = undelete_location(collection=self, loc_id=item)
        self._is_dirty = True
        return restored

    def find_by_alias(self, alias: str) -> list[Location]:
        """Query all active locations matching a normalized alias."""
        cleaned = clean_string(alias)
        if not cleaned:
            return []
        loc_ids = self._alias_index.get(cleaned.lower(), set())
        return [
            self._registry[lid]
            for lid in loc_ids
            if lid in self._registry and not self._registry[lid].tombstone.is_deprecated
        ]

    def find_by_category(self, category: JurisdictionCategory | str) -> list[Location]:
        """Query all active locations matching a specific jurisdiction category."""
        cat = (
            category
            if isinstance(category, JurisdictionCategory)
            else JurisdictionCategory(category)
        )
        loc_ids = self._category_index.get(cat, set())
        return [
            self._registry[lid]
            for lid in loc_ids
            if lid in self._registry and not self._registry[lid].tombstone.is_deprecated
        ]

    def find_children(self, parent_id: LocationID | str) -> list[Location]:
        """Query all active direct child locations of a parent jurisdiction."""
        p_id = parent_id if isinstance(parent_id, LocationID) else LocationID(parent_id)
        loc_ids = self._parent_index.get(p_id, set())
        return [
            self._registry[lid]
            for lid in loc_ids
            if lid in self._registry and not self._registry[lid].tombstone.is_deprecated
        ]

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
        self._category_index.clear()
        self._parent_index.clear()
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

        next_num = extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.LOC) + 1
        loc_id = LocationID(mint_smart_id(SmartIDPrefix.LOC, next_num))

        now = IsoTimestamp(utc_now_iso())
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
