"""Path: src/gda/entity/locations.py

Authoritative in-memory repository and graph manager for civil jurisdictions.

Operational Role:
    Implements the in-memory entity collection archetype for Location entities.
    Provides fast primary indexing by LocationID and unique canonical URN, parent-child
    hierarchical graph traversal, lineage resolution, date-bounded historical naming
    evaluation, and unified in-place graveyard management with recursive redirection.

Classes:
    Locations: Authoritative in-memory collection and graph manager for Location entities.
"""

from __future__ import annotations

import dataclasses
import fnmatch
import re
from collections import defaultdict
from collections.abc import Collection, Iterable, Iterator
from difflib import SequenceMatcher
from typing import Any

from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.enums.vital import NameStatus
from gda.model.atom.date import DateString, EventDate, IsoTimestamp
from gda.model.atom.id import LocationID
from gda.model.base.tombstone import TombstoneRecord
from gda.model.entity.location import JurisdictionCategory, Location

__version__ = "1.0.0+build.4"

__all__ = ["Locations"]


class Locations(IntrospectableMixin, Collection[Location]):
    """Authoritative in-memory repository and graph manager for civil jurisdictions.

    Inherits IntrospectableMixin for runtime self-documentation and implements the standard
    Python Collection[Location] container protocol. All active entities and tombstoned
    records are retained within a single unified index, with active filtering applied by default.
    """

    def __init__(self, items: Iterable[Location] | None = None) -> None:
        """Initialize an empty or pre-populated in-memory Locations collection.

        Args:
            items: Optional iterable of validated Location domain entities to pre-populate.
        """
        self._by_id: dict[LocationID, Location] = {}
        self._by_urn: dict[str, LocationID] = {}
        self._children: dict[LocationID, set[LocationID]] = defaultdict(set)
        self._is_dirty: bool = False

        if items is not None:
            for item in items:
                self.add(item)
            self._is_dirty = False

    # =========================================================================
    # Standard Collection Protocols & Container Semantics
    # =========================================================================

    def __len__(self) -> int:
        """Return the count of active, non-deprecated locations in memory."""
        return self.count_active

    def __contains__(self, key: Any) -> bool:
        """Check whether an active location with the given identifier exists.

        Args:
            key: LocationID instance or string identifier.

        Returns:
            True if the identifier matches an active entity; False otherwise.
        """
        loc_id = self._coerce_id(key)
        if loc_id is None or loc_id not in self._by_id:
            return False
        return not self._by_id[loc_id].tombstone.is_deprecated

    def __iter__(self) -> Iterator[Location]:
        """Iterate over all active, non-deprecated locations sorted by sort_key."""
        active_items = [
            entity
            for entity in self._by_id.values()
            if not entity.tombstone.is_deprecated
        ]
        active_items.sort(key=lambda item: item.sort_key)
        yield from active_items

    def __getitem__(self, key: LocationID | str) -> Location:
        """Retrieve an active location by ID, resolving graveyard redirects transparently.

        Args:
            key: Canonical LocationID or string representation.

        Returns:
            The matching active Location entity or the terminal canonical active entity.

        Raises:
            KeyError: If the ID is unregistered or resolves to a defunct tombstone.
        """
        loc = self.get(key, resolve_redirects=True)
        if loc is None:
            raise KeyError(
                f"Location '{key}' not found in active registry or resolvable graveyard."
            )
        return loc

    def get(
        self,
        key: LocationID | str,
        default: Location | None = None,
        *,
        resolve_redirects: bool = True,
    ) -> Location | None:
        """Retrieve a Location by LocationID, handling optional graveyard redirection.

        Args:
            key: Primary LocationID or string token.
            default: Fallback value returned if entity is missing or unresolvable.
            resolve_redirects: If True, follows tombstone supersession chains to
                return the terminal active Location entity. If False, returns None
                for deprecated entities unless explicitly in active registry.

        Returns:
            Matching Location entity if active/resolvable; otherwise default.
        """
        loc_id = self._coerce_id(key)
        if loc_id is None or loc_id not in self._by_id:
            return default

        entity = self._by_id[loc_id]
        if not entity.tombstone.is_deprecated:
            return entity

        if resolve_redirects:
            canonical_id = self.resolve_id(loc_id)
            if canonical_id is not None and canonical_id in self._by_id:
                return self._by_id[canonical_id]

        return default

    def add(self, location: Location) -> None:
        """Register or update a validated Location entity and synchronize all indexes.

        Args:
            location: Validated Location entity.

        Raises:
            TypeError: If location is not an instance of Location.
        """
        if not isinstance(location, Location):
            raise TypeError(
                f"Expected Location instance, got {type(location).__name__}."
            )

        loc_id = location.id
        old_record = self._by_id.get(loc_id)

        # Evict old secondary index mappings if replacing an existing record
        if old_record is not None:
            if old_record.canonical_urn in self._by_urn:
                del self._by_urn[old_record.canonical_urn]
            if old_record.parent_id is not None:
                self._children[old_record.parent_id].discard(loc_id)

        self._by_id[loc_id] = location
        self._by_urn[location.canonical_urn] = loc_id
        if location.parent_id is not None:
            self._children[location.parent_id].add(loc_id)

        self._is_dirty = True

    def remove(self, key: LocationID | str) -> bool:
        """Hard-evict a location entirely from memory and clear all secondary index bindings.

        Args:
            key: LocationID or string identifier.

        Returns:
            True if an entity was present and removed; False otherwise.
        """
        loc_id = self._coerce_id(key)
        if loc_id is None or loc_id not in self._by_id:
            return False

        entity = self._by_id.pop(loc_id)
        self._by_urn.pop(entity.canonical_urn, None)
        if entity.parent_id is not None:
            self._children[entity.parent_id].discard(loc_id)
            if not self._children[entity.parent_id]:
                del self._children[entity.parent_id]

        if loc_id in self._children:
            del self._children[loc_id]

        self._is_dirty = True
        return True

    def clear(self) -> None:
        """Purge all stored locations and clear all secondary indexes."""
        self._by_id.clear()
        self._by_urn.clear()
        self._children.clear()
        self._is_dirty = True

    def keys(self) -> tuple[LocationID, ...]:
        """Return a tuple of all active, non-deprecated LocationIDs."""
        return tuple(entity.id for entity in self)

    def values(self) -> tuple[Location, ...]:
        """Return a tuple of all active, non-deprecated Location entities."""
        return tuple(self)

    def items(self) -> tuple[tuple[LocationID, Location], ...]:
        """Return a tuple of (LocationID, Location) pairs for active entities."""
        return tuple((entity.id, entity) for entity in self)

    # =========================================================================
    # Graveyard & Tombstone Management
    # =========================================================================

    @property
    def is_dirty(self) -> bool:
        """Return True if in-memory mutations remain unpersisted."""
        return self._is_dirty

    @property
    def count_active(self) -> int:
        """Return total count of active, non-deprecated locations in memory."""
        return sum(1 for e in self._by_id.values() if not e.tombstone.is_deprecated)

    @property
    def count_graveyard(self) -> int:
        """Return total count of tombstoned/deprecated locations in memory."""
        return sum(1 for e in self._by_id.values() if e.tombstone.is_deprecated)

    @property
    def total_count(self) -> int:
        """Return combined total count across active and graveyard partitions."""
        return len(self._by_id)

    def iter_graveyard(self) -> Iterator[Location]:
        """Yield strictly soft-deleted/deprecated location records."""
        for entity in self._by_id.values():
            if entity.tombstone.is_deprecated:
                yield entity

    def iter_all(self) -> Iterator[Location]:
        """Yield every location record across both active and graveyard partitions."""
        yield from self._by_id.values()

    def resolve_id(self, loc_id: LocationID | str) -> LocationID | None:
        """Follow superseded_by chains through tombstoned records with cycle detection.

        Args:
            loc_id: Starting location identifier.

        Returns:
            Active canonical LocationID if resolved; None if target is defunct or circular.
        """
        curr = self._coerce_id(loc_id)
        if curr is None:
            return None

        visited: set[LocationID] = set()
        while curr is not None and curr in self._by_id:
            if curr in visited:
                return None
            visited.add(curr)

            rec = self._by_id[curr]
            if not rec.tombstone.is_deprecated:
                return curr

            succ = rec.tombstone.superseded_by
            if succ is None:
                return None
            curr = succ

        return None

    def deprecate(
        self,
        loc_id: LocationID | str,
        superseded_by: LocationID | str | None = None,
    ) -> Location:
        """Apply a soft-delete tombstone to a location in-place with optional successor.

        Args:
            loc_id: LocationID or string of target entity to deprecate.
            superseded_by: Optional successor LocationID pointing to the canonical entity.

        Returns:
            The newly created immutable tombstoned Location instance.

        Raises:
            KeyError: If loc_id is unregistered or superseded_by is unregistered.
            ValueError: If superseded_by references loc_id directly.
        """
        target_id = self._coerce_id(loc_id)
        if target_id is None or target_id not in self._by_id:
            raise KeyError(f"Location '{loc_id}' not found in registry.")

        succ_id: LocationID | None = None
        if superseded_by is not None:
            succ_id = self._coerce_id(superseded_by)
            if succ_id is None:
                raise KeyError(f"Invalid superseded_by identifier '{superseded_by}'.")
            if succ_id == target_id:
                raise ValueError(f"Location '{target_id}' cannot supersede itself.")
            if succ_id not in self._by_id:
                raise KeyError(f"Target superseded_by location '{succ_id}' not found.")

        current = self._by_id[target_id]
        updated_tombstone = TombstoneRecord[LocationID](
            is_deprecated=True,
            deprecated_at=IsoTimestamp.now_utc(),
            superseded_by=succ_id,
        )

        tombstoned_loc = dataclasses.replace(current, tombstone=updated_tombstone)
        self.add(tombstoned_loc)
        return tombstoned_loc

    def restore(self, loc_id: LocationID | str) -> Location:
        """Clear tombstone flags and restore a deprecated location to active status.

        Args:
            loc_id: LocationID or string of target entity to restore.

        Returns:
            The restored immutable active Location instance.

        Raises:
            KeyError: If loc_id is not registered in memory.
        """
        target_id = self._coerce_id(loc_id)
        if target_id is None or target_id not in self._by_id:
            raise KeyError(f"Location '{loc_id}' not found in registry.")

        current = self._by_id[target_id]
        cleared_tombstone = TombstoneRecord[LocationID](
            is_deprecated=False,
            deprecated_at=None,
            superseded_by=None,
        )

        restored_loc = dataclasses.replace(current, tombstone=cleared_tombstone)
        self.add(restored_loc)
        return restored_loc

    # =========================================================================
    # Jurisdictional Graph & Relational Traversals
    # =========================================================================

    def get_by_urn(self, urn: str) -> Location | None:
        """Retrieve a location by its unique canonical URN in O(1) time.

        Args:
            urn: Canonical URN string (e.g., 'urn:gda:loc:us:nh:merrimack:bow').

        Returns:
            Active Location entity if found; None otherwise.
        """
        clean_urn = urn.strip().lower()
        loc_id = self._by_urn.get(clean_urn)
        if loc_id is None:
            return None
        return self.get(loc_id, resolve_redirects=True)

    def get_children(
        self,
        parent_id: LocationID | str,
        include_graveyard: bool = False,
    ) -> tuple[Location, ...]:
        """Retrieve all direct child jurisdictions governed by parent_id.

        Args:
            parent_id: LocationID or string of governing parent jurisdiction.
            include_graveyard: If True, includes tombstoned child entities.

        Returns:
            Tuple of child Location entities ordered by sort_key.
        """
        p_id = self._coerce_id(parent_id)
        if p_id is None or p_id not in self._children:
            return ()

        child_ids = self._children[p_id]
        results: list[Location] = []
        for c_id in child_ids:
            if c_id in self._by_id:
                rec = self._by_id[c_id]
                if include_graveyard or not rec.tombstone.is_deprecated:
                    results.append(rec)

        results.sort(key=lambda loc: loc.sort_key)
        return tuple(results)

    def get_ancestors(
        self,
        loc_id: LocationID | str,
        include_graveyard: bool = False,
    ) -> tuple[Location, ...]:
        """Traverse upward through parent_id links from target to root country.

        Args:
            loc_id: LocationID or string of the starting location.
            include_graveyard: If True, includes tombstoned ancestor records.

        Returns:
            Tuple of ancestor Location entities ordered upward from immediate parent to root.
        """
        curr_id = self._coerce_id(loc_id)
        if curr_id is None or curr_id not in self._by_id:
            return ()

        ancestors: list[Location] = []
        visited: set[LocationID] = {curr_id}
        curr = self._by_id[curr_id]

        while curr.parent_id is not None:
            p_id: LocationID = curr.parent_id
            if p_id in visited or p_id not in self._by_id:
                break
            visited.add(p_id)

            parent_loc = self._by_id[p_id]
            if include_graveyard or not parent_loc.tombstone.is_deprecated:
                ancestors.append(parent_loc)
            curr = parent_loc

        return tuple(ancestors)

    def get_predecessors(self, loc_id: LocationID | str) -> tuple[Location, ...]:
        """Resolve all recorded historical predecessor location entities.

        Args:
            loc_id: Canonical LocationID or string identifier.

        Returns:
            Tuple of active predecessor Location entities.
        """
        loc = self.get(loc_id, resolve_redirects=True)
        if loc is None or not loc.predecessor_ids:
            return ()

        results: list[Location] = []
        for pid in loc.predecessor_ids:
            pred = self.get(pid, resolve_redirects=True)
            if pred is not None:
                results.append(pred)
        return tuple(results)

    def get_successors(self, loc_id: LocationID | str) -> tuple[Location, ...]:
        """Resolve all recorded partition or merger successor location entities.

        Args:
            loc_id: Canonical LocationID or string identifier.

        Returns:
            Tuple of active successor Location entities.
        """
        loc = self.get(loc_id, resolve_redirects=True)
        if loc is None or not loc.successor_ids:
            return ()

        results: list[Location] = []
        for sid in loc.successor_ids:
            succ = self.get(sid, resolve_redirects=True)
            if succ is not None:
                results.append(succ)
        return tuple(results)

    # =========================================================================
    # Temporal Evaluation & Hierarchy Formatting
    # =========================================================================

    def get_name_at_date(
        self,
        loc_id: LocationID | str,
        date: DateString | EventDate | str,
    ) -> str:
        """Resolve historical naming variant in effect at a given date.

        Adheres strictly to HistoricalName properties: valid_period, status, and display_name.

        Args:
            loc_id: Canonical LocationID or string identifier.
            date: ISO date string, year string, DateString, or EventDate.

        Returns:
            Historical name valid at date if recorded; otherwise canonical modern name.
        """
        loc = self.get(loc_id, resolve_redirects=True)
        if loc is None:
            return ""

        query_year = self._extract_year(date)
        if query_year is None:
            return loc.name

        for hist in loc.historical_names:
            if hist.valid_period is not None:
                start_year = (
                    self._extract_year(hist.valid_period.start_date)
                    if hist.valid_period.start_date
                    else None
                )
                end_year = (
                    self._extract_year(hist.valid_period.end_date)
                    if hist.valid_period.end_date
                    else None
                )

                in_range = True
                if start_year is not None and query_year < start_year:
                    in_range = False
                if end_year is not None and query_year > end_year:
                    in_range = False

                if in_range and hist.status == NameStatus.PRIMARY:
                    return hist.display_name

        return loc.name

    def format_hierarchy(
        self,
        loc_id: LocationID | str,
        at_date: DateString | EventDate | str | None = None,
        reverse: bool = False,
    ) -> str:
        """Format full comma-delimited jurisdictional path from local entity to root country.

        Args:
            loc_id: Canonical LocationID or string identifier.
            at_date: Optional historical evaluation date to resolve contemporary names.
            reverse: If True, formats country-to-local; otherwise local-to-country.

        Returns:
            Comma-delimited jurisdictional path string.
        """
        loc = self.get(loc_id, resolve_redirects=True)
        if loc is None:
            return ""

        ancestors = self.get_ancestors(loc.id, include_graveyard=False)
        chain = [loc] + list(ancestors)

        parts: list[str] = []
        for item in chain:
            if at_date is not None:
                parts.append(self.get_name_at_date(item.id, at_date))
            else:
                parts.append(item.name)

        if reverse:
            parts.reverse()

        return ", ".join(parts)

    # =========================================================================
    # Search & Filter Mechanisms
    # =========================================================================

    def find_by_name(
        self,
        name: str,
        parent_id: LocationID | str | None = None,
        include_alternate: bool = True,
    ) -> tuple[Location, ...]:
        """Find active locations matching name exactly, optionally scoped to a parent.

        Args:
            name: Exact primary name, historical variant, or alternate name to match.
            parent_id: Optional parent jurisdiction filter.
            include_alternate: If True, evaluates alternate_names alongside primary name.

        Returns:
            Tuple of matching Location entities ordered by sort_key.
        """
        clean_name = name.strip().lower()
        target_parent = self._coerce_id(parent_id) if parent_id is not None else None
        results: list[Location] = []

        for entity in self:
            if target_parent is not None and entity.parent_id != target_parent:
                continue

            matched = entity.name.lower() == clean_name
            if not matched and include_alternate:
                if any(alt.lower() == clean_name for alt in entity.alternate_names):
                    matched = True
                elif any(
                    hist.display_name.lower() == clean_name
                    for hist in entity.historical_names
                ):
                    matched = True
                elif any(
                    hist.raw_name.lower() == clean_name
                    for hist in entity.historical_names
                ):
                    matched = True
                elif any(
                    any(
                        alt_sp.lower() == clean_name
                        for alt_sp in hist.alternate_spellings
                    )
                    for hist in entity.historical_names
                ):
                    matched = True

            if matched:
                results.append(entity)

        results.sort(key=lambda item: item.sort_key)
        return tuple(results)

    def search(
        self,
        query: str,
        category: JurisdictionCategory | None = None,
        include_graveyard: bool = False,
        fuzzy: bool = True,
        threshold: float = 0.75,
    ) -> tuple[Location, ...]:
        """Search locations matching query against names and URNs with relevance scoring.

        Args:
            query: Free-text search string or wildcard pattern (*, ?).
            category: Optional administrative JurisdictionCategory filter.
            include_graveyard: If True, includes tombstoned locations in search pool.
            fuzzy: If True, evaluates difflib sequence similarity.
            threshold: Minimum similarity threshold ratio (0.0 to 1.0).

        Returns:
            Tuple of matching Location entities sorted descending by relevance score.
        """
        clean_query = query.strip().lower()
        if not clean_query:
            return ()

        candidates = (
            self._by_id.values() if include_graveyard else (item for item in self)
        )
        scored: list[tuple[float, Location]] = []

        for entity in candidates:
            if category is not None and entity.category != category:
                continue

            cand_strings = [entity.name, entity.canonical_urn] + entity.alternate_names
            for hist in entity.historical_names:
                cand_strings.append(hist.raw_name)
                if hist.canonical_name:
                    cand_strings.append(hist.canonical_name)
                cand_strings.extend(hist.alternate_spellings)

            best_score = 0.0
            matched = False

            for cand in cand_strings:
                cand_lower = cand.lower()
                if any(ch in clean_query for ch in ["*", "?", "["]):
                    if fnmatch.fnmatch(cand_lower, clean_query):
                        matched = True
                        best_score = max(best_score, 1.0)
                        break
                elif clean_query == cand_lower:
                    matched = True
                    best_score = max(best_score, 1.0)
                    break
                elif clean_query in cand_lower:
                    matched = True
                    ratio = len(clean_query) / len(cand_lower)
                    best_score = max(best_score, ratio)
                elif fuzzy:
                    sim = SequenceMatcher(None, clean_query, cand_lower).ratio()
                    if sim >= threshold:
                        matched = True
                        best_score = max(best_score, sim)

            if matched:
                scored.append((best_score, entity))

        scored.sort(
            key=lambda pair: (pair[0], -pair[1].category_rank, pair[1].name),
            reverse=True,
        )
        return tuple(item for _, item in scored)

    # =========================================================================
    # Serialization Payloads & Helpers
    # =========================================================================

    def to_list(self, include_graveyard: bool = False) -> list[Location]:
        """Export collection entities to a standard list.

        Args:
            include_graveyard: If True, includes tombstoned entities; otherwise active only.

        Returns:
            List of Location entities.
        """
        if include_graveyard:
            return list(self._by_id.values())
        return list(self)

    @classmethod
    def from_list(cls, locations: Iterable[Location]) -> Locations:
        """Construct a new Locations collection instance from an iterable of entities.

        Args:
            locations: Iterable collection of validated Location entities.

        Returns:
            Instantiated Locations collection.
        """
        return cls(items=locations)

    # =========================================================================
    # Internal Type Coercion & Utility Helpers
    # =========================================================================

    @staticmethod
    def _coerce_id(val: Any) -> LocationID | None:
        """Coerce an identifier token into a validated LocationID, returning None if invalid."""
        if isinstance(val, LocationID):
            return val
        if isinstance(val, str) and val.startswith("LOC-"):
            try:
                return LocationID(val)
            except (ModelFormatError, TypeError, ValueError):
                return None
        return None

    @staticmethod
    def _extract_year(date: Any) -> int | None:
        """Extract a 4-digit Gregorian integer year from dates or temporal strings."""
        if date is None:
            return None
        if isinstance(date, EventDate):
            raw = date.date.value
        elif isinstance(date, DateString):
            raw = date.value
        elif isinstance(date, str):
            raw = date.strip()
        else:
            return None

        m = re.search(r"\b(\d{4})\b", raw)
        return int(m.group(1)) if m else None
