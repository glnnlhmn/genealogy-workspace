"""Path: src/gda/entity/sites/collection.py

Authoritative in-memory collection and relational lookup manager for site records.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    undeleting, and retrieving Site entities situated within civil jurisdictions.
    Provides manager-ready graveyard inspection, supersession resolution,
    multi-entity alias lookup, and dirty-entity tracking.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from gda.core.dates import utc_now_iso
from gda.core.enums.core import IDType, SmartIDPrefix
from gda.core.enums.site import SiteType
from gda.core.introspectable import IntrospectableMixin
from gda.entity.sites.errors import SiteNotFoundError, SiteValidationError
from gda.entity.sites.util import (
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_site,
    undelete_site,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, SiteID
from gda.model.base.address import Address
from gda.model.base.audit import AuditStamp
from gda.model.base.date import TimePeriod
from gda.model.base.geo import Coordinates
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.site import Site
from gda.util.ids import extract_max_smart_id, mint_smart_id, verify_id
from gda.util.text import clean_string, slugify

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations

__version__ = "1.0.0+build.8"

__all__ = [
    "Sites",
]


class Sites(IntrospectableMixin):
    """Authoritative in-memory collection and relational lookup index for site entities."""

    def __init__(self, sites: list[Site] | None = None) -> None:
        """Initialize site registry, URN, alias, location, and category indexes."""
        self._registry: dict[SiteID, Site] = {}
        self._urn_index: dict[str, SiteID] = {}
        self._alias_index: dict[str, set[SiteID]] = defaultdict(set)
        self._location_index: dict[LocationID, set[SiteID]] = defaultdict(set)
        self._category_index: dict[SiteType, set[SiteID]] = defaultdict(set)
        self._is_dirty: bool = False

        if sites:
            for s in sites:
                self.add(s)

    @classmethod
    def from_database(cls) -> Sites:
        """Factory method initializing a collection and loading site records from SQLite."""
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
        for site_id, site in list(self._registry.items()):
            if site.is_dirty:
                self._registry[site_id] = site.mark_clean()

    def dirty_entities(self) -> list[Site]:
        """Return all registered sites currently marked dirty in memory."""
        return [site for site in self._registry.values() if site.is_dirty]

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) sites in the collection."""
        return sum(1 for site in self._registry.values() if not site.tombstone.is_deprecated)

    def __iter__(self) -> Iterator[Site]:
        """Iterate over active (non-tombstoned) sites in the collection."""
        for site in self._registry.values():
            if not site.tombstone.is_deprecated:
                yield site

    def iter_all(self) -> Iterator[Site]:
        """Iterate over all sites, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_id(self, item: SiteID | str) -> SiteID | None:
        """Resolve a SiteID, string ID, or canonical URN into a SiteID if registered."""
        if isinstance(item, SiteID):
            return item if item in self._registry else None
        if isinstance(item, str):
            token = item.strip()
            if verify_id(token, id_type=IDType.SMART_ID, smart_id_prefix=SmartIDPrefix.SID):
                cand = SiteID(token)
                return cand if cand in self._registry else None
            urn_cand = self._urn_index.get(token)
            return urn_cand if urn_cand and urn_cand in self._registry else None
        return None

    def __contains__(self, item: SiteID | str) -> bool:
        """Check if an active site exists by SiteID, string ID, or canonical URN."""
        site_id = self._resolve_id(item)
        return site_id is not None and not self._registry[site_id].tombstone.is_deprecated

    def __getitem__(self, item: SiteID | str) -> Site:
        """Retrieve an active site by SiteID, string ID, or canonical URN."""
        site_id = self._resolve_id(item)
        if not site_id:
            raise SiteNotFoundError(f"Site not found: {item}")

        site = self._registry[site_id]
        if site.tombstone.is_deprecated:
            raise SiteNotFoundError(f"Site has been tombstoned: {item}")
        return site

    def get(self, item: SiteID | str, default: Site | None = None) -> Site | None:
        """Retrieve an active site by identifier, returning default if absent."""
        try:
            return self[item]
        except SiteNotFoundError:
            return default

    def get_any(self, item: SiteID | str, default: Site | None = None) -> Site | None:
        """Retrieve a site by ID or URN regardless of whether it is active or tombstoned."""
        site_id = self._resolve_id(item)
        return self._registry[site_id] if site_id is not None else default

    def find_tombstoned(self) -> list[Site]:
        """Return all retired (tombstoned) sites in the graveyard."""
        return [site for site in self._registry.values() if site.tombstone.is_deprecated]

    def resolve_active(self, item: SiteID | str) -> Site | None:
        """Follow superseded_by chains from an identifier to its current active Site."""
        curr = self.get_any(item)
        seen: set[SiteID] = set()
        while curr is not None and curr.tombstone.is_deprecated:
            if curr.id in seen or curr.tombstone.superseded_by is None:
                return None
            seen.add(curr.id)
            curr = self._registry.get(curr.tombstone.superseded_by)
        return curr

    def add(self, site: Site) -> None:
        """Add a site entity to registry and update all secondary lookup indexes."""
        if not isinstance(site, Site):
            raise TypeError(f"Expected Site instance, got {type(site).__name__}")

        self._registry[site.id] = site
        self._urn_index[site.canonical_urn] = site.id
        self._location_index[site.location_id].add(site.id)
        self._category_index[site.category].add(site.id)

        for alias in site.aliases:
            self._alias_index[alias.lower()].add(site.id)

        self._is_dirty = True

    def update(self, site: Site) -> None:
        """Replace an existing entity in the collection, re-indexing aliases and URNs."""
        if not isinstance(site, Site):
            raise TypeError(f"Expected Site instance, got {type(site).__name__}")

        target_id = site.id
        if target_id not in self._registry:
            raise SiteNotFoundError(f"Cannot update site '{target_id}'; not found in registry.")

        old_site = self._registry[target_id]

        new_aliases = {a.lower() for a in site.aliases}
        for old_alias in old_site.aliases:
            key = old_alias.lower()
            if key not in new_aliases and key in self._alias_index:
                self._alias_index[key].discard(target_id)
                if not self._alias_index[key]:
                    del self._alias_index[key]

        if old_site.canonical_urn != site.canonical_urn:
            self._urn_index.pop(old_site.canonical_urn, None)

        if old_site.location_id != site.location_id:
            self._location_index[old_site.location_id].discard(target_id)
            if not self._location_index[old_site.location_id]:
                del self._location_index[old_site.location_id]

        if old_site.category != site.category:
            self._category_index[old_site.category].discard(target_id)
            if not self._category_index[old_site.category]:
                del self._category_index[old_site.category]

        self.add(site)

    def soft_delete(
        self,
        item: SiteID | str,
        reason: str | None = None,
        superseded_by: SiteID | str | None = None,
    ) -> Site:
        """Soft-delete a site entity and mark the collection dirty."""
        retired = tombstone_site(
            collection=self,
            site_id=item,
            reason=reason or "Site retired",
            superseded_by=superseded_by,
        )
        self._is_dirty = True
        return retired

    def undelete(
        self,
        item: SiteID | str,
        locations_collection: Locations | None = None,
    ) -> Site:
        """Restore a tombstoned site back to active status and mark dirty."""
        restored = undelete_site(
            collection=self,
            site_id=item,
            locations_collection=locations_collection,
        )
        self._is_dirty = True
        return restored

    def find_by_alias(self, alias: str) -> list[Site]:
        """Query all active sites matching a normalized alias."""
        cleaned = clean_string(alias)
        if not cleaned:
            return []
        site_ids = self._alias_index.get(cleaned.lower(), set())
        return [
            self._registry[sid]
            for sid in site_ids
            if sid in self._registry and not self._registry[sid].tombstone.is_deprecated
        ]

    def find_by_location(self, location_id: LocationID | str) -> list[Site]:
        """Query all active sites situated within a governing jurisdiction."""
        loc_id = location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        site_ids = self._location_index.get(loc_id, set())
        return [
            self._registry[sid]
            for sid in site_ids
            if sid in self._registry and not self._registry[sid].tombstone.is_deprecated
        ]

    def find_by_category(self, category: SiteType | str) -> list[Site]:
        """Query all active sites matching a specific functional classification."""
        cat = category if isinstance(category, SiteType) else SiteType(category)
        site_ids = self._category_index.get(cat, set())
        return [
            self._registry[sid]
            for sid in site_ids
            if sid in self._registry and not self._registry[sid].tombstone.is_deprecated
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
        self._location_index.clear()
        self._category_index.clear()
        loaded = load_from_db(self)
        self.mark_clean()
        return loaded

    def import_file(self, path: Path | str) -> int:
        """Import site entities from a formatted JSON file via util helper."""
        return import_file(self, path)

    def export_file(self, path: Path | str, include_graveyard: bool = True) -> int:
        """Export site entities to a JSON file via util helper."""
        return export_file(self, path, include_graveyard=include_graveyard)

    def create(
        self,
        name: str,
        category: SiteType | str,
        location_id: LocationID | str,
        canonical_urn: str | None = None,
        address: Address | None = None,
        coordinates: Coordinates | None = None,
        period: TimePeriod | None = None,
        alternate_names: list[str] | None = None,
        notes: list[Note] | None = None,
        is_active: bool = True,
        locations_collection: Locations | None = None,
    ) -> Site:
        """Create, register, and index a new Site entity using sequential smart ID and suffix."""
        res_cat = category if isinstance(category, SiteType) else SiteType(category)
        res_loc_id = location_id if isinstance(location_id, LocationID) else LocationID(location_id)

        if locations_collection is not None:
            if res_loc_id not in locations_collection:
                raise SiteValidationError(
                    f"Governing location '{res_loc_id}' does not exist or is tombstoned."
                )

        next_num = extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.SID) + 1
        site_id = SiteID(mint_smart_id(SmartIDPrefix.SID, next_num))

        if canonical_urn:
            urn = canonical_urn.strip()
        else:
            base_slug = slugify(name, delimiter="_")
            loc_slug = str(res_loc_id).lower().replace("-", "_")
            urn = f"urn:gda:site:{loc_slug}:{base_slug}_s{site_id.suffix.lower()}"

        now = IsoTimestamp(utc_now_iso())
        audit = AuditStamp(created_at=now, updated_at=now)

        name_obj = NameThing.create(raw=name, canonical=name)
        if alternate_names:
            for alt in alternate_names:
                name_obj = name_obj.add_alias(alt)

        site = Site.create(
            site_id=site_id,
            audit=audit,
            name=name_obj,
            category=res_cat,
            canonical_urn=urn,
            location_id=res_loc_id,
            address=address,
            coordinates=coordinates,
            period=period,
            notes=notes or [],
            is_active=is_active,
            tombstone=Tombstone[SiteID](),
        )

        self.add(site)
        return site
