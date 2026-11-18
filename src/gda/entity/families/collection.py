"""Path: src/gda/entity/families/collection.py

Authoritative in-memory collection and relational lookup manager for family units.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    undeleting, and indexing Family entities across spousal partners, filial
    child links, union classifications, and canonical URNs. Supports graveyard
    inspection, supersession resolution, and dirty-entity tracking.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING, Any

from gda.core.dates import utc_now_iso
from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.enums.vital import PedigreeType, UnionType
from gda.core.introspectable import IntrospectableMixin
from gda.entity.families.errors import FamilyNotFoundError, FamilyValidationError
from gda.entity.families.util import (
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_family,
    undelete_family,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.base.audit import AuditStamp
from gda.model.base.family import ChildLink, FamilyUnion, _normalize_union_type
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.family import Family
from gda.util.ids import extract_max_smart_id, mint_smart_id, verify_id

if TYPE_CHECKING:
    from gda.entity.individuals.collection import Individuals

__version__ = "1.0.0+build.4"

__all__ = [
    "Families",
]


class Families(IntrospectableMixin):
    """Authoritative in-memory collection and relational lookup index for family entities."""

    def __init__(self, families: list[Family] | None = None) -> None:
        """Initialize family registry and secondary URN, partner, child, and union_type indexes."""
        self._registry: dict[FamilyID, Family] = {}
        self._urn_index: dict[str, FamilyID] = {}
        self._partner_index: dict[IndividualID, set[FamilyID]] = defaultdict(set)
        self._child_index: dict[IndividualID, set[FamilyID]] = defaultdict(set)
        self._union_type_index: dict[UnionType, set[FamilyID]] = defaultdict(set)
        self._is_dirty: bool = False

        if families:
            for fam in families:
                self.add(fam)

    @classmethod
    def from_database(cls) -> Families:
        """Factory method initializing a collection and loading family records from SQLite."""
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
        for fam_id, fam in list(self._registry.items()):
            if fam.is_dirty:
                self._registry[fam_id] = fam.mark_clean()

    def dirty_entities(self) -> list[Family]:
        """Return all registered families currently marked dirty in memory."""
        return [fam for fam in self._registry.values() if fam.is_dirty]

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) families in the collection."""
        return sum(1 for fam in self._registry.values() if not fam.tombstone.is_deprecated)

    def __iter__(self) -> Iterator[Family]:
        """Iterate over active (non-tombstoned) families in the collection."""
        for fam in self._registry.values():
            if not fam.tombstone.is_deprecated:
                yield fam

    def iter_all(self) -> Iterator[Family]:
        """Iterate over all families, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_id(self, item: FamilyID | str) -> FamilyID | None:
        """Resolve a FamilyID, string ID, or canonical URN into a FamilyID if registered."""
        if isinstance(item, FamilyID):
            return item if item in self._registry else None
        if isinstance(item, str):
            token = item.strip()
            if verify_id(token, id_type=IDType.SMART_ID, smart_id_prefix=SmartIDPrefix.FAM):
                cand = FamilyID(token)
                return cand if cand in self._registry else None
            urn_cand = self._urn_index.get(token)
            return urn_cand if urn_cand and urn_cand in self._registry else None
        return None

    def __contains__(self, item: FamilyID | str) -> bool:
        """Check if an active family exists by FamilyID, string ID, or canonical URN."""
        fam_id = self._resolve_id(item)
        return fam_id is not None and not self._registry[fam_id].tombstone.is_deprecated

    def __getitem__(self, item: FamilyID | str) -> Family:
        """Retrieve an active family by FamilyID, string ID, or canonical URN."""
        fam_id = self._resolve_id(item)
        if not fam_id:
            raise FamilyNotFoundError(f"Family not found: {item}")

        fam = self._registry[fam_id]
        if fam.tombstone.is_deprecated:
            raise FamilyNotFoundError(f"Family has been tombstoned: {item}")
        return fam

    def get(
        self,
        item: FamilyID | str,
        default: Family | None = None,
    ) -> Family | None:
        """Retrieve an active family by identifier, returning default if absent."""
        try:
            return self[item]
        except FamilyNotFoundError:
            return default

    def get_any(
        self,
        item: FamilyID | str,
        default: Family | None = None,
    ) -> Family | None:
        """Retrieve a family by ID or URN regardless of whether it is active or tombstoned."""
        fam_id = self._resolve_id(item)
        return self._registry[fam_id] if fam_id is not None else default

    def find_tombstoned(self) -> list[Family]:
        """Return all retired (tombstoned) families in the graveyard."""
        return [fam for fam in self._registry.values() if fam.tombstone.is_deprecated]

    def resolve_active(self, item: FamilyID | str) -> Family | None:
        """Follow superseded_by chains from an identifier to its current active Family."""
        curr = self.get_any(item)
        seen: set[FamilyID] = set()
        while curr is not None and curr.tombstone.is_deprecated:
            if curr.id in seen or curr.tombstone.superseded_by is None:
                return None
            seen.add(curr.id)
            curr = self._registry.get(curr.tombstone.superseded_by)
        return curr

    def add(self, family: Family) -> None:
        """Add a family entity to registry and update all secondary lookup indexes."""
        if not isinstance(family, Family):
            raise TypeError(f"Expected Family instance, got {type(family).__name__}")

        self._registry[family.id] = family
        self._urn_index[family.canonical_urn] = family.id
        self._union_type_index[family.union_type].add(family.id)

        for pid in family.partner_ids:
            self._partner_index[pid].add(family.id)

        for cid in family.child_ids:
            self._child_index[cid].add(family.id)

        self._is_dirty = True

    def update(self, family: Family) -> None:
        """Replace an existing family in the collection, re-indexing URNs, partners, children, and union_type."""
        if not isinstance(family, Family):
            raise TypeError(f"Expected Family instance, got {type(family).__name__}")

        target_id = family.id
        if target_id not in self._registry:
            raise FamilyNotFoundError(f"Cannot update family '{target_id}'; not found in registry.")

        old_fam = self._registry[target_id]

        if old_fam.canonical_urn != family.canonical_urn:
            self._urn_index.pop(old_fam.canonical_urn, None)

        if old_fam.union_type != family.union_type:
            self._union_type_index[old_fam.union_type].discard(target_id)
            if not self._union_type_index[old_fam.union_type]:
                del self._union_type_index[old_fam.union_type]

        new_partners = set(family.partner_ids)
        for old_pid in set(old_fam.partner_ids) - new_partners:
            self._partner_index[old_pid].discard(target_id)
            if not self._partner_index[old_pid]:
                del self._partner_index[old_pid]

        new_children = set(family.child_ids)
        for old_cid in set(old_fam.child_ids) - new_children:
            self._child_index[old_cid].discard(target_id)
            if not self._child_index[old_cid]:
                del self._child_index[old_cid]

        self.add(family)

    def soft_delete(
        self,
        item: FamilyID | str,
        reason: str | None = None,
        superseded_by: FamilyID | str | None = None,
    ) -> Family:
        """Soft-delete a family entity and mark the collection dirty."""
        retired = tombstone_family(
            collection=self,
            family_id=item,
            reason=reason or "Family retired",
            superseded_by=superseded_by,
        )
        self._is_dirty = True
        return retired

    def undelete(
        self,
        item: FamilyID | str,
        individuals_collection: Individuals | None = None,
    ) -> Family:
        """Restore a tombstoned family back to active status and mark dirty."""
        restored = undelete_family(
            collection=self,
            family_id=item,
            individuals_collection=individuals_collection,
        )
        self._is_dirty = True
        return restored

    def find_by_partner(self, individual_id: IndividualID | str) -> list[Family]:
        """Query all active families in which an individual is a partner, sorted by sort_key."""
        ind_id = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(individual_id)
        )
        fam_ids = self._partner_index.get(ind_id, set())
        results = [
            self._registry[fid]
            for fid in fam_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
        ]
        results.sort(key=lambda fam: fam.sort_key)
        return results

    def find_by_child(self, individual_id: IndividualID | str) -> list[Family]:
        """Query all active families in which an individual is a child, sorted by sort_key."""
        ind_id = (
            individual_id
            if isinstance(individual_id, IndividualID)
            else IndividualID(individual_id)
        )
        fam_ids = self._child_index.get(ind_id, set())
        results = [
            self._registry[fid]
            for fid in fam_ids
            if fid in self._registry and not self._registry[fid].tombstone.is_deprecated
        ]
        results.sort(key=lambda fam: fam.sort_key)
        return results

    def find_by_union_type(self, union_type: UnionType | str) -> list[Family]:
        """Query all active families matching a specific union classification."""
        u_type = _normalize_union_type(union_type)
        fam_ids = self._union_type_index.get(u_type, set())
        return [
            self._registry[fid]
            for fid in fam_ids
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
        self._partner_index.clear()
        self._child_index.clear()
        self._union_type_index.clear()
        loaded = load_from_db(self)
        self.mark_clean()
        return loaded

    def import_file(self, path: Path | str) -> int:
        """Import family entities from a formatted JSON file via util helper."""
        return import_file(self, path)

    def export_file(self, path: Path | str, include_graveyard: bool = True) -> int:
        """Export family entities to a JSON file via util helper."""
        return export_file(self, path, include_graveyard=include_graveyard)

    def create(
        self,
        partner_ids: list[IndividualID | str] | None = None,
        children: list[ChildLink | tuple[IndividualID | str, PedigreeType | str] | dict[str, Any]]
        | None = None,
        union: FamilyUnion | dict[str, Any] | None = None,
        canonical_urn: str | None = None,
        notes: list[Note] | None = None,
        individuals_collection: Individuals | None = None,
    ) -> Family:
        """Create, register, and index a new Family entity using sequential smart ID minting."""
        res_partners = [
            pid if isinstance(pid, IndividualID) else IndividualID(pid)
            for pid in (partner_ids or [])
        ]

        if individuals_collection is not None:
            for pid in res_partners:
                if pid not in individuals_collection:
                    raise FamilyValidationError(
                        f"Partner individual '{pid}' does not exist or is tombstoned."
                    )

        next_num = extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.FAM) + 1
        fam_id = FamilyID(mint_smart_id(SmartIDPrefix.FAM, next_num))

        if canonical_urn and canonical_urn.strip():
            urn = canonical_urn.strip()
        elif res_partners:
            partner_slug = "_".join(str(p).lower().replace("-", "_") for p in res_partners)
            urn = f"urn:gda:fam:{partner_slug}_f{fam_id.suffix.lower()}"
        else:
            urn = f"urn:gda:fam:union_f{fam_id.suffix.lower()}"

        now = IsoTimestamp(utc_now_iso())
        audit = AuditStamp(created_at=now, updated_at=now)

        fam = Family.create(
            family_id=fam_id,
            canonical_urn=urn,
            partner_ids=res_partners,
            children=children,
            union=union,
            audit=audit,
            notes=notes or [],
            tombstone=Tombstone[FamilyID](),
        )

        if individuals_collection is not None:
            for cid in fam.child_ids:
                if cid not in individuals_collection:
                    raise FamilyValidationError(
                        f"Child individual '{cid}' does not exist or is tombstoned."
                    )

        self.add(fam)
        return fam
