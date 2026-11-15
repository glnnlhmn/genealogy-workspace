"""Path: src/gda/entity/individuals/collection.py

Authoritative in-memory collection and relational lookup manager for individuals.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    undeleting, and indexing Individual persona entities across onomastic
    surnames (birth and married), multi-entity aliases, vital origin/conclusion
    places (Locations and Sites), and canonical URNs. Supports graveyard
    inspection, supersession resolution, and dirty-entity tracking.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.core.enums.core import Sex, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.entity.individuals.errors import (
    IndividualNotFoundError,
    IndividualValidationError,
)
from gda.entity.individuals.util import (
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_individual,
    undelete_individual,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.gender import GenderAtom
from gda.model.atom.id import IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate
from gda.model.base.name import NamePerson
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.individual import Individual, _resolve_place_id
from gda.util.ids import extract_max_smart_id, mint_smart_id
from gda.util.text import clean_string, slugify

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.3"

__all__ = [
    "Individuals",
]


def _extract_surname_keys(ind: Individual) -> set[str]:
    """Extract lowercase primary and married surname index keys for an Individual."""
    keys: set[str] = set()
    if ind.surname:
        keys.add(ind.surname.lower())
    for m_name in ind.married_names:
        keys.add(m_name.lower())
    return keys


def _extract_location_keys(ind: Individual) -> set[LocationID]:
    """Extract LocationIDs referenced by birth_place_id or death_place_id."""
    keys: set[LocationID] = set()
    if isinstance(ind.birth_place_id, LocationID):
        keys.add(ind.birth_place_id)
    if isinstance(ind.death_place_id, LocationID):
        keys.add(ind.death_place_id)
    return keys


def _extract_site_keys(ind: Individual) -> set[SiteID]:
    """Extract SiteIDs referenced by birth_place_id or death_place_id."""
    keys: set[SiteID] = set()
    if isinstance(ind.birth_place_id, SiteID):
        keys.add(ind.birth_place_id)
    if isinstance(ind.death_place_id, SiteID):
        keys.add(ind.death_place_id)
    return keys


def _validate_place_in_collections(
    place_id: LocationID | SiteID | None,
    label: str,
    locations_collection: Locations | None,
    sites_collection: Sites | None,
) -> None:
    """Validate an optional LocationID or SiteID against provided collections."""
    if isinstance(place_id, LocationID) and locations_collection is not None:
        if place_id not in locations_collection:
            raise IndividualValidationError(
                f"{label} location '{place_id}' does not exist or is tombstoned."
            )
    elif isinstance(place_id, SiteID) and sites_collection is not None:
        if place_id not in sites_collection:
            raise IndividualValidationError(
                f"{label} site '{place_id}' does not exist or is tombstoned."
            )


class Individuals(IntrospectableMixin):
    """Authoritative in-memory collection and relational lookup index for individual entities."""

    def __init__(self, individuals: list[Individual] | None = None) -> None:
        """Initialize individual registry and secondary URN, alias, surname, location, and site indexes."""
        self._registry: dict[IndividualID, Individual] = {}
        self._urn_index: dict[str, IndividualID] = {}
        self._alias_index: dict[str, set[IndividualID]] = defaultdict(set)
        self._surname_index: dict[str, set[IndividualID]] = defaultdict(set)
        self._location_index: dict[LocationID, set[IndividualID]] = defaultdict(set)
        self._site_index: dict[SiteID, set[IndividualID]] = defaultdict(set)
        self._is_dirty: bool = False

        if individuals:
            for ind in individuals:
                self.add(ind)

    @classmethod
    def from_database(cls) -> Individuals:
        """Factory method initializing a collection and loading individual records from SQLite."""
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
        for ind_id, ind in list(self._registry.items()):
            if ind.is_dirty:
                self._registry[ind_id] = ind.mark_clean()

    def dirty_entities(self) -> list[Individual]:
        """Return all registered individuals currently marked dirty in memory."""
        return [ind for ind in self._registry.values() if ind.is_dirty]

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) individuals in the collection."""
        return sum(1 for ind in self._registry.values() if not ind.tombstone.is_deprecated)

    def __iter__(self) -> Iterator[Individual]:
        """Iterate over active (non-tombstoned) individuals in the collection."""
        for ind in self._registry.values():
            if not ind.tombstone.is_deprecated:
                yield ind

    def iter_all(self) -> Iterator[Individual]:
        """Iterate over all individuals, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_id(self, item: IndividualID | str) -> IndividualID | None:
        """Resolve an IndividualID, string ID, or canonical URN into an IndividualID if registered."""
        if isinstance(item, IndividualID):
            return item if item in self._registry else None
        if isinstance(item, str):
            if item.startswith("IND-"):
                cand = IndividualID(item)
                return cand if cand in self._registry else None
            cand = self._urn_index.get(item)
            return cand if cand and cand in self._registry else None
        return None

    def __contains__(self, item: IndividualID | str) -> bool:
        """Check if an active individual exists by IndividualID, string ID, or canonical URN."""
        ind_id = self._resolve_id(item)
        return ind_id is not None and not self._registry[ind_id].tombstone.is_deprecated

    def __getitem__(self, item: IndividualID | str) -> Individual:
        """Retrieve an active individual by IndividualID, string ID, or canonical URN."""
        ind_id = self._resolve_id(item)
        if not ind_id:
            raise IndividualNotFoundError(f"Individual not found: {item}")

        ind = self._registry[ind_id]
        if ind.tombstone.is_deprecated:
            raise IndividualNotFoundError(f"Individual has been tombstoned: {item}")
        return ind

    def get(
        self,
        item: IndividualID | str,
        default: Individual | None = None,
    ) -> Individual | None:
        """Retrieve an active individual by identifier, returning default if absent."""
        try:
            return self[item]
        except IndividualNotFoundError:
            return default

    def get_any(
        self,
        item: IndividualID | str,
        default: Individual | None = None,
    ) -> Individual | None:
        """Retrieve an individual by ID or URN regardless of whether it is active or tombstoned."""
        ind_id = self._resolve_id(item)
        return self._registry[ind_id] if ind_id is not None else default

    def find_tombstoned(self) -> list[Individual]:
        """Return all retired (tombstoned) individuals in the graveyard."""
        return [ind for ind in self._registry.values() if ind.tombstone.is_deprecated]

    def resolve_active(self, item: IndividualID | str) -> Individual | None:
        """Follow superseded_by chains from an identifier to its current active Individual."""
        curr = self.get_any(item)
        seen: set[IndividualID] = set()
        while curr is not None and curr.tombstone.is_deprecated:
            if curr.id in seen or curr.tombstone.superseded_by is None:
                return None
            seen.add(curr.id)
            curr = self._registry.get(curr.tombstone.superseded_by)
        return curr

    def add(self, individual: Individual) -> None:
        """Add an individual entity to registry and update all secondary lookup indexes."""
        if not isinstance(individual, Individual):
            raise TypeError(f"Expected Individual instance, got {type(individual).__name__}")

        self._registry[individual.id] = individual
        self._urn_index[individual.canonical_urn] = individual.id

        for s_key in _extract_surname_keys(individual):
            self._surname_index[s_key].add(individual.id)

        for loc_id in _extract_location_keys(individual):
            self._location_index[loc_id].add(individual.id)

        for site_id in _extract_site_keys(individual):
            self._site_index[site_id].add(individual.id)

        for alias in individual.aliases:
            self._alias_index[alias.lower()].add(individual.id)

        self._is_dirty = True

    def update(self, individual: Individual) -> None:
        """Replace an existing individual in the collection, re-indexing URNs, names, and places."""
        if not isinstance(individual, Individual):
            raise TypeError(f"Expected Individual instance, got {type(individual).__name__}")

        target_id = individual.id
        if target_id not in self._registry:
            raise IndividualNotFoundError(
                f"Cannot update individual '{target_id}'; not found in registry."
            )

        old_ind = self._registry[target_id]

        new_aliases = {a.lower() for a in individual.aliases}
        for old_alias in old_ind.aliases:
            key = old_alias.lower()
            if key not in new_aliases and key in self._alias_index:
                self._alias_index[key].discard(target_id)
                if not self._alias_index[key]:
                    del self._alias_index[key]

        if old_ind.canonical_urn != individual.canonical_urn:
            self._urn_index.pop(old_ind.canonical_urn, None)

        new_surnames = _extract_surname_keys(individual)
        for old_s_key in _extract_surname_keys(old_ind) - new_surnames:
            self._surname_index[old_s_key].discard(target_id)
            if not self._surname_index[old_s_key]:
                del self._surname_index[old_s_key]

        new_locs = _extract_location_keys(individual)
        for old_loc in _extract_location_keys(old_ind) - new_locs:
            self._location_index[old_loc].discard(target_id)
            if not self._location_index[old_loc]:
                del self._location_index[old_loc]

        new_sites = _extract_site_keys(individual)
        for old_site in _extract_site_keys(old_ind) - new_sites:
            self._site_index[old_site].discard(target_id)
            if not self._site_index[old_site]:
                del self._site_index[old_site]

        self.add(individual)

    def soft_delete(
        self,
        item: IndividualID | str,
        reason: str | None = None,
        superseded_by: IndividualID | str | None = None,
    ) -> Individual:
        """Soft-delete an individual entity and mark the collection dirty."""
        retired = tombstone_individual(
            collection=self,
            individual_id=item,
            reason=reason or "Individual retired",
            superseded_by=superseded_by,
        )
        self._is_dirty = True
        return retired

    def undelete(
        self,
        item: IndividualID | str,
        locations_collection: Locations | None = None,
        sites_collection: Sites | None = None,
    ) -> Individual:
        """Restore a tombstoned individual back to active status and mark dirty."""
        restored = undelete_individual(
            collection=self,
            individual_id=item,
            locations_collection=locations_collection,
            sites_collection=sites_collection,
        )
        self._is_dirty = True
        return restored

    def find_by_alias(self, alias: str) -> list[Individual]:
        """Query all active individuals matching a normalized alias, sorted by sort_key."""
        cleaned = clean_string(alias)
        if not cleaned:
            return []
        ind_ids = self._alias_index.get(cleaned.lower(), set())
        results = [
            self._registry[iid]
            for iid in ind_ids
            if iid in self._registry and not self._registry[iid].tombstone.is_deprecated
        ]
        results.sort(key=lambda ind: ind.sort_key)
        return results

    def find_by_surname(self, surname: str) -> list[Individual]:
        """Query all active individuals matching a birth or married surname, sorted by sort_key."""
        cleaned = clean_string(surname)
        if not cleaned:
            return []
        ind_ids = self._surname_index.get(cleaned.lower(), set())
        results = [
            self._registry[iid]
            for iid in ind_ids
            if iid in self._registry and not self._registry[iid].tombstone.is_deprecated
        ]
        results.sort(key=lambda ind: ind.sort_key)
        return results

    def find_by_location(self, location_id: LocationID | str) -> list[Individual]:
        """Query all active individuals with birth or death anchored to a LocationID."""
        loc_id = location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        ind_ids = self._location_index.get(loc_id, set())
        return [
            self._registry[iid]
            for iid in ind_ids
            if iid in self._registry and not self._registry[iid].tombstone.is_deprecated
        ]

    def find_by_site(self, site_id: SiteID | str) -> list[Individual]:
        """Query all active individuals with birth or death anchored to a SiteID."""
        s_id = site_id if isinstance(site_id, SiteID) else SiteID(site_id)
        ind_ids = self._site_index.get(s_id, set())
        return [
            self._registry[iid]
            for iid in ind_ids
            if iid in self._registry and not self._registry[iid].tombstone.is_deprecated
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
        self._surname_index.clear()
        self._location_index.clear()
        self._site_index.clear()
        loaded = load_from_db(self)
        self.mark_clean()
        return loaded

    def import_file(self, path: Path | str) -> int:
        """Import individual entities from a formatted JSON file via util helper."""
        return import_file(self, path)

    def export_file(self, path: Path | str, include_graveyard: bool = True) -> int:
        """Export individual entities to a JSON file via util helper."""
        return export_file(self, path, include_graveyard=include_graveyard)

    def create(
        self,
        name: NamePerson | str,
        canonical_urn: str | None = None,
        gender: GenderAtom | Sex | str | None = None,
        birth_date: EventDate | str | dict[str, Any] | None = None,
        death_date: EventDate | str | dict[str, Any] | None = None,
        birth_place_id: LocationID | SiteID | str | None = None,
        death_place_id: LocationID | SiteID | str | None = None,
        is_deceased: bool = True,
        alternate_names: list[str] | None = None,
        married_names: list[str] | None = None,
        notes: list[Note] | None = None,
        locations_collection: Locations | None = None,
        sites_collection: Sites | None = None,
    ) -> Individual:
        """Create, register, and index a new Individual entity using sequential smart ID minting."""
        if isinstance(name, NamePerson):
            name_obj = name
        else:
            cleaned_name = clean_string(str(name))
            if not cleaned_name:
                raise ModelFormatError("Individual name cannot be blank or whitespace.")
            tokens = cleaned_name.split()
            if len(tokens) >= 2:
                name_obj = NamePerson.create(
                    raw=cleaned_name,
                    given=" ".join(tokens[:-1]),
                    surname=tokens[-1],
                )
            else:
                name_obj = NamePerson.create(raw=cleaned_name, given=tokens[0])

        if alternate_names:
            for alt in alternate_names:
                c = clean_string(alt)
                if c:
                    name_obj = name_obj.add_alias(c)

        if married_names:
            for m_name in married_names:
                c = clean_string(m_name)
                if c:
                    name_obj = name_obj.add_married(c)

        res_birth_place = _resolve_place_id(birth_place_id)
        res_death_place = _resolve_place_id(death_place_id)

        _validate_place_in_collections(
            res_birth_place, "Birth place", locations_collection, sites_collection
        )
        _validate_place_in_collections(
            res_death_place, "Death place", locations_collection, sites_collection
        )

        next_num = extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.IND) + 1
        ind_id = IndividualID(mint_smart_id(SmartIDPrefix.IND, next_num))

        if canonical_urn:
            urn = canonical_urn.strip()
        else:
            name_slug = slugify(name_obj.canonical, delimiter="_")
            urn = f"urn:gda:ind:{name_slug}_i{ind_id.suffix.lower()}"

        now = IsoTimestamp(utc_now_iso())
        audit = AuditStamp(created_at=now, updated_at=now)

        ind = Individual.create(
            individual_id=ind_id,
            name=name_obj,
            canonical_urn=urn,
            gender=gender,
            birth_date=birth_date,
            death_date=death_date,
            birth_place_id=res_birth_place,
            death_place_id=res_death_place,
            is_deceased=is_deceased,
            audit=audit,
            notes=notes or [],
            tombstone=Tombstone[IndividualID](),
        )

        self.add(ind)
        return ind
