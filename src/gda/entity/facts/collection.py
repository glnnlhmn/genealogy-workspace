"""Path: src/gda/entity/facts/collection.py

Authoritative in-memory collection and relational lookup manager for evidentiary facts.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    undeleting, and indexing Fact entities across primary subjects (Individuals
    and Families), event classifications, geographic locations, physical sites,
    and secondary participants. Supports graveyard inspection, supersession
    resolution, and dirty-entity tracking.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.core.enums.core import FactType, IDType, SmartIDPrefix
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.entity.facts.errors import FactNotFoundError, FactValidationError
from gda.entity.facts.util import (
    _resolve_subject_id,
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_fact,
    undelete_fact,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, FamilyID, IndividualID, LocationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import EventDate, TimePeriod
from gda.model.base.note import Note
from gda.model.base.source import SourceReference
from gda.model.base.tombstone import Tombstone
from gda.model.entity.fact import Fact, FactParticipant
from gda.util.ids import extract_max_smart_id, mint_smart_id, verify_id
from gda.util.text import clean_string, slugify

if TYPE_CHECKING:
    from gda.entity.families.collection import Families
    from gda.entity.individuals.collection import Individuals
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.3"

__all__ = [
    "Facts",
]


class Facts(IntrospectableMixin):
    """Authoritative in-memory collection and relational lookup index for fact entities."""

    def __init__(self, facts: list[Fact] | None = None) -> None:
        """Initialize fact registry and secondary URN, subject, type, location, site, and participant indexes."""
        self._registry: dict[FactID, Fact] = {}
        self._urn_index: dict[str, FactID] = {}
        self._subject_index: dict[IndividualID | FamilyID, set[FactID]] = defaultdict(set)
        self._type_index: dict[FactType, set[FactID]] = defaultdict(set)
        self._location_index: dict[LocationID, set[FactID]] = defaultdict(set)
        self._site_index: dict[SiteID, set[FactID]] = defaultdict(set)
        self._participant_index: dict[IndividualID, set[FactID]] = defaultdict(set)
        self._is_dirty: bool = False

        if facts:
            for fact in facts:
                self.add(fact)

    @classmethod
    def from_database(cls) -> Facts:
        """Factory method initializing a collection and loading fact records from SQLite."""
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
        for fact_id, fact in list(self._registry.items()):
            if fact.is_dirty:
                self._registry[fact_id] = fact.mark_clean()

    def dirty_entities(self) -> list[Fact]:
        """Return all registered facts currently marked dirty in memory."""
        return [fact for fact in self._registry.values() if fact.is_dirty]

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) facts in the collection."""
        return sum(1 for fact in self._registry.values() if not fact.tombstone.is_deprecated)

    def __iter__(self) -> Iterator[Fact]:
        """Iterate over active (non-tombstoned) facts in the collection."""
        for fact in self._registry.values():
            if not fact.tombstone.is_deprecated:
                yield fact

    def iter_all(self) -> Iterator[Fact]:
        """Iterate over all facts, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_id(self, item: FactID | str) -> FactID | None:
        """Resolve a FactID, string ID, or canonical URN into a FactID if registered."""
        if isinstance(item, FactID):
            return item if item in self._registry else None
        if isinstance(item, str):
            token = item.strip()
            if verify_id(token, id_type=IDType.SMART_ID, smart_id_prefix=SmartIDPrefix.FID):
                cand = FactID(token)
                return cand if cand in self._registry else None
            urn_cand = self._urn_index.get(token)
            return urn_cand if urn_cand and urn_cand in self._registry else None
        return None

    def __contains__(self, item: FactID | str) -> bool:
        """Check if an active fact exists by FactID, string ID, or canonical URN."""
        fact_id = self._resolve_id(item)
        return fact_id is not None and not self._registry[fact_id].tombstone.is_deprecated

    def __getitem__(self, item: FactID | str) -> Fact:
        """Retrieve an active fact by FactID, string ID, or canonical URN."""
        fact_id = self._resolve_id(item)
        if not fact_id:
            raise FactNotFoundError(f"Fact not found: {item}")

        fact = self._registry[fact_id]
        if fact.tombstone.is_deprecated:
            raise FactNotFoundError(f"Fact has been tombstoned: {item}")
        return fact

    def get(
        self,
        item: FactID | str,
        default: Fact | None = None,
    ) -> Fact | None:
        """Retrieve an active fact by identifier, returning default if absent."""
        try:
            return self[item]
        except FactNotFoundError:
            return default

    def get_any(
        self,
        item: FactID | str,
        default: Fact | None = None,
    ) -> Fact | None:
        """Retrieve a fact by ID or URN regardless of whether it is active or tombstoned."""
        fact_id = self._resolve_id(item)
        return self._registry[fact_id] if fact_id is not None else default

    def find_tombstoned(self) -> list[Fact]:
        """Return all retired (tombstoned) facts in the graveyard."""
        return [fact for fact in self._registry.values() if fact.tombstone.is_deprecated]

    def resolve_active(self, item: FactID | str) -> Fact | None:
        """Follow superseded_by chains from an identifier to its current active Fact."""
        curr = self.get_any(item)
        seen: set[FactID] = set()
        while curr is not None and curr.tombstone.is_deprecated:
            if curr.id in seen or curr.tombstone.superseded_by is None:
                return None
            seen.add(curr.id)
            curr = self._registry.get(curr.tombstone.superseded_by)
        return curr

    def add(self, fact: Fact) -> None:
        """Add a fact entity to registry and update all secondary lookup indexes."""
        if not isinstance(fact, Fact):
            raise TypeError(f"Expected Fact instance, got {type(fact).__name__}")

        self._registry[fact.id] = fact
        self._urn_index[fact.canonical_urn] = fact.id
        self._subject_index[fact.primary_subject_id].add(fact.id)
        self._type_index[fact.fact_type].add(fact.id)

        if fact.location_id is not None:
            self._location_index[fact.location_id].add(fact.id)

        if fact.site_id is not None:
            self._site_index[fact.site_id].add(fact.id)

        for participant in fact.participants:
            self._participant_index[participant.individual_id].add(fact.id)

        self._is_dirty = True

    def update(self, fact: Fact) -> None:
        """Replace an existing fact in the collection, re-indexing URNs, subjects, FKs, and participants."""
        if not isinstance(fact, Fact):
            raise TypeError(f"Expected Fact instance, got {type(fact).__name__}")

        target_id = fact.id
        if target_id not in self._registry:
            raise FactNotFoundError(f"Cannot update fact '{target_id}'; not found in registry.")

        old_fact = self._registry[target_id]

        if old_fact.canonical_urn != fact.canonical_urn:
            self._urn_index.pop(old_fact.canonical_urn, None)

        if old_fact.primary_subject_id != fact.primary_subject_id:
            self._subject_index[old_fact.primary_subject_id].discard(target_id)
            if not self._subject_index[old_fact.primary_subject_id]:
                del self._subject_index[old_fact.primary_subject_id]

        if old_fact.fact_type != fact.fact_type:
            self._type_index[old_fact.fact_type].discard(target_id)
            if not self._type_index[old_fact.fact_type]:
                del self._type_index[old_fact.fact_type]

        if old_fact.location_id is not None and old_fact.location_id != fact.location_id:
            self._location_index[old_fact.location_id].discard(target_id)
            if not self._location_index[old_fact.location_id]:
                del self._location_index[old_fact.location_id]

        if old_fact.site_id is not None and old_fact.site_id != fact.site_id:
            self._site_index[old_fact.site_id].discard(target_id)
            if not self._site_index[old_fact.site_id]:
                del self._site_index[old_fact.site_id]

        new_part_ids = set(fact.participant_ids)
        for old_part_id in old_fact.participant_ids:
            if old_part_id not in new_part_ids:
                self._participant_index[old_part_id].discard(target_id)
                if not self._participant_index[old_part_id]:
                    del self._participant_index[old_part_id]

        self.add(fact)

    def soft_delete(
        self,
        item: FactID | str,
        reason: str | None = None,
        superseded_by: FactID | str | None = None,
    ) -> Fact:
        """Soft-delete a fact entity and mark the collection dirty."""
        retired = tombstone_fact(
            collection=self,
            fact_id=item,
            reason=reason or "Fact retired",
            superseded_by=superseded_by,
        )
        self._is_dirty = True
        return retired

    def undelete(
        self,
        item: FactID | str,
        locations_collection: Locations | None = None,
        sites_collection: Sites | None = None,
        individuals_collection: Individuals | None = None,
        families_collection: Families | None = None,
    ) -> Fact:
        """Restore a tombstoned fact back to active status and mark dirty."""
        restored = undelete_fact(
            collection=self,
            fact_id=item,
            locations_collection=locations_collection,
            sites_collection=sites_collection,
            individuals_collection=individuals_collection,
            families_collection=families_collection,
        )
        self._is_dirty = True
        return restored

    def find_by_subject(
        self,
        subject_id: IndividualID | FamilyID | str,
    ) -> list[Fact]:
        """Query all active facts for a primary subject, sorted chronologically by sort_key."""
        subj = _resolve_subject_id(subject_id)
        fact_ids = self._subject_index.get(subj, set())
        results = [
            self._registry[fid]
            for fid in fact_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
        ]
        results.sort(key=lambda f: f.sort_key)
        return results

    def find_by_type(self, fact_type: FactType | str) -> list[Fact]:
        """Query all active facts matching a specific event classification."""
        ft = fact_type if isinstance(fact_type, FactType) else FactType(str(fact_type).upper())
        fact_ids = self._type_index.get(ft, set())
        return [
            self._registry[fid]
            for fid in fact_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
        ]

    def find_by_location(self, location_id: LocationID | str) -> list[Fact]:
        """Query all active facts anchored to a macro-jurisdictional LocationID."""
        loc_id = location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        fact_ids = self._location_index.get(loc_id, set())
        return [
            self._registry[fid]
            for fid in fact_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
        ]

    def find_by_site(self, site_id: SiteID | str) -> list[Fact]:
        """Query all active facts anchored to a micro-physical SiteID."""
        s_id = site_id if isinstance(site_id, SiteID) else SiteID(site_id)
        fact_ids = self._site_index.get(s_id, set())
        return [
            self._registry[fid]
            for fid in fact_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
        ]

    def find_by_participant(self, individual_id: IndividualID | str) -> list[Fact]:
        """Query all active facts in which an individual participated in a secondary role."""
        ind_id = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(individual_id)
        )
        fact_ids = self._participant_index.get(ind_id, set())
        return [
            self._registry[fid]
            for fid in fact_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
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
        self._subject_index.clear()
        self._type_index.clear()
        self._location_index.clear()
        self._site_index.clear()
        self._participant_index.clear()
        loaded = load_from_db(self)
        self.mark_clean()
        return loaded

    def import_file(self, path: Path | str) -> int:
        """Import fact entities from a formatted JSON file via util helper."""
        return import_file(self, path)

    def export_file(self, path: Path | str, include_graveyard: bool = True) -> int:
        """Export fact entities to a JSON file via util helper."""
        return export_file(self, path, include_graveyard=include_graveyard)

    def create(
        self,
        fact_type: FactType | str,
        title: str,
        primary_subject_id: IndividualID | FamilyID | str,
        canonical_urn: str | None = None,
        date: EventDate | TimePeriod | str | dict[str, Any] | None = None,
        location_id: LocationID | str | None = None,
        site_id: SiteID | str | None = None,
        value: str | None = None,
        description: str | None = None,
        narrative: str | None = None,
        participants: list[FactParticipant | dict[str, Any]] | None = None,
        citations: list[SourceReference | dict[str, Any]] | None = None,
        notes: list[Note] | None = None,
        locations_collection: Locations | None = None,
        sites_collection: Sites | None = None,
        individuals_collection: Individuals | None = None,
        families_collection: Families | None = None,
    ) -> Fact:
        """Create, register, and index a new Fact entity using sequential smart ID minting."""
        cleaned_title = clean_string(title)
        if not cleaned_title:
            raise ModelFormatError("Fact title cannot be blank or whitespace.")

        res_type = (
            fact_type
            if isinstance(fact_type, FactType)
            else FactType(str(fact_type).strip().upper())
        )
        res_subj = _resolve_subject_id(primary_subject_id)

        if isinstance(res_subj, IndividualID) and individuals_collection is not None:
            if res_subj not in individuals_collection:
                raise FactValidationError(
                    f"Primary subject individual '{res_subj}' does not exist or is tombstoned."
                )
        elif isinstance(res_subj, FamilyID) and families_collection is not None:
            if res_subj not in families_collection:
                raise FactValidationError(
                    f"Primary subject family '{res_subj}' does not exist or is tombstoned."
                )

        res_loc_id: LocationID | None = None
        if location_id is not None:
            res_loc_id = (
                location_id if isinstance(location_id, LocationID) else LocationID(location_id)
            )
            if locations_collection is not None and res_loc_id not in locations_collection:
                raise FactValidationError(
                    f"Governing location '{res_loc_id}' does not exist or is tombstoned."
                )

        res_site_id: SiteID | None = None
        if site_id is not None:
            res_site_id = site_id if isinstance(site_id, SiteID) else SiteID(site_id)
            if sites_collection is not None and res_site_id not in sites_collection:
                raise FactValidationError(
                    f"Venue site '{res_site_id}' does not exist or is tombstoned."
                )

        next_num = extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.FID) + 1
        fact_id = FactID(mint_smart_id(SmartIDPrefix.FID, next_num))

        if canonical_urn:
            urn = canonical_urn.strip()
        else:
            subj_slug = str(res_subj).lower().replace("-", "_")
            type_slug = slugify(res_type.value, delimiter="_")
            urn = f"urn:gda:fact:{subj_slug}:{type_slug}_f{fact_id.suffix.lower()}"

        now = IsoTimestamp(utc_now_iso())
        audit = AuditStamp(created_at=now, updated_at=now)

        fact = Fact.create(
            fact_id=fact_id,
            canonical_urn=urn,
            fact_type=res_type,
            title=cleaned_title,
            primary_subject_id=res_subj,
            date=date,
            location_id=res_loc_id,
            site_id=res_site_id,
            value=value,
            description=description,
            narrative=narrative,
            participants=participants,
            citations=citations,
            audit=audit,
            notes=notes or [],
            tombstone=Tombstone[FactID](),
        )

        if individuals_collection is not None:
            for pid in fact.participant_ids:
                if pid not in individuals_collection:
                    raise FactValidationError(
                        f"Participant individual '{pid}' does not exist or is tombstoned."
                    )

        self.add(fact)
        return fact
