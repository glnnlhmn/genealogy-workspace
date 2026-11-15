"""Path: src/gda/entity/organizations/collection.py

Authoritative in-memory collection and relational lookup manager for organization records.

Operational Role:
    Acts as the primary domain API facade for creating, querying, tombstoning,
    undeleting, and navigating optional institutional hierarchies of Organization
    entities. Supports standalone local chapters (parent_org_id=None) as well
    as multi-tier parent/child bodies, optional LocationID and meeting SiteID
    references, multi-entity alias lookup, and graveyard inspection helpers.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

from gda.core.dates import utc_now_iso
from gda.core.enums.core import SmartIDPrefix
from gda.core.enums.orgs import OrganizationCategory
from gda.core.errors import ModelFormatError
from gda.core.introspectable import IntrospectableMixin
from gda.entity.organizations.errors import (
    OrganizationNotFoundError,
    OrganizationValidationError,
)
from gda.entity.organizations.util import (
    export_file,
    import_file,
    load_from_db,
    save_to_db,
    tombstone_organization,
    undelete_organization,
)
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import LocationID, OrganizationID, SiteID
from gda.model.base.audit import AuditStamp
from gda.model.base.date import TimePeriod
from gda.model.base.name import NameThing
from gda.model.base.note import Note
from gda.model.base.tombstone import Tombstone
from gda.model.entity.organization import Organization
from gda.util.ids import extract_max_smart_id, mint_smart_id
from gda.util.text import clean_string, slugify

if TYPE_CHECKING:
    from gda.entity.locations.collection import Locations
    from gda.entity.sites.collection import Sites

__version__ = "1.0.0+build.3"

__all__ = [
    "Organizations",
]


class Organizations(IntrospectableMixin):
    """Authoritative in-memory collection and relational lookup index for organization entities."""

    def __init__(self, organizations: list[Organization] | None = None) -> None:
        """Initialize organization registry and secondary URN, alias, category, location, site, and parent indexes."""
        self._registry: dict[OrganizationID, Organization] = {}
        self._urn_index: dict[str, OrganizationID] = {}
        self._alias_index: dict[str, set[OrganizationID]] = defaultdict(set)
        self._category_index: dict[OrganizationCategory, set[OrganizationID]] = defaultdict(set)
        self._location_index: dict[LocationID, set[OrganizationID]] = defaultdict(set)
        self._site_index: dict[SiteID, set[OrganizationID]] = defaultdict(set)
        self._parent_index: dict[OrganizationID, set[OrganizationID]] = defaultdict(set)
        self._is_dirty: bool = False

        if organizations:
            for org in organizations:
                self.add(org)

    @classmethod
    def from_database(cls) -> Organizations:
        """Factory method initializing a collection and loading organization records from SQLite."""
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
        for org_id, org in list(self._registry.items()):
            if org.is_dirty:
                self._registry[org_id] = org.mark_clean()

    def dirty_entities(self) -> list[Organization]:
        """Return all registered organizations currently marked dirty in memory."""
        return [org for org in self._registry.values() if org.is_dirty]

    def __len__(self) -> int:
        """Return the count of active (non-tombstoned) organizations in the collection."""
        return sum(1 for org in self._registry.values() if not org.tombstone.is_deprecated)

    def __iter__(self) -> Iterator[Organization]:
        """Iterate over active (non-tombstoned) organizations in the collection."""
        for org in self._registry.values():
            if not org.tombstone.is_deprecated:
                yield org

    def iter_all(self) -> Iterator[Organization]:
        """Iterate over all organizations, including tombstoned records."""
        yield from self._registry.values()

    def _resolve_id(self, item: OrganizationID | str) -> OrganizationID | None:
        """Resolve an OrganizationID, string ID, or canonical URN into an OrganizationID if registered."""
        if isinstance(item, OrganizationID):
            return item if item in self._registry else None
        if isinstance(item, str):
            if item.startswith("ORG-"):
                cand = OrganizationID(item)
                return cand if cand in self._registry else None
            cand = self._urn_index.get(item)
            return cand if cand and cand in self._registry else None
        return None

    def __contains__(self, item: OrganizationID | str) -> bool:
        """Check if an active organization exists by OrganizationID, string ID, or canonical URN."""
        org_id = self._resolve_id(item)
        return org_id is not None and not self._registry[org_id].tombstone.is_deprecated

    def __getitem__(self, item: OrganizationID | str) -> Organization:
        """Retrieve an active organization by OrganizationID, string ID, or canonical URN."""
        org_id = self._resolve_id(item)
        if not org_id:
            raise OrganizationNotFoundError(f"Organization not found: {item}")

        org = self._registry[org_id]
        if org.tombstone.is_deprecated:
            raise OrganizationNotFoundError(f"Organization has been tombstoned: {item}")
        return org

    def get(
        self,
        item: OrganizationID | str,
        default: Organization | None = None,
    ) -> Organization | None:
        """Retrieve an active organization by identifier, returning default if absent."""
        try:
            return self[item]
        except OrganizationNotFoundError:
            return default

    def get_any(
        self,
        item: OrganizationID | str,
        default: Organization | None = None,
    ) -> Organization | None:
        """Retrieve an organization by ID or URN regardless of whether it is active or tombstoned."""
        org_id = self._resolve_id(item)
        return self._registry[org_id] if org_id is not None else default

    def find_tombstoned(self) -> list[Organization]:
        """Return all retired (tombstoned) organizations in the graveyard."""
        return [org for org in self._registry.values() if org.tombstone.is_deprecated]

    def resolve_active(self, item: OrganizationID | str) -> Organization | None:
        """Follow superseded_by chains from an identifier to its current active Organization."""
        curr = self.get_any(item)
        seen: set[OrganizationID] = set()
        while curr is not None and curr.tombstone.is_deprecated:
            if curr.id in seen or curr.tombstone.superseded_by is None:
                return None
            seen.add(curr.id)
            curr = self._registry.get(curr.tombstone.superseded_by)
        return curr

    def add(self, organization: Organization) -> None:
        """Add an organization entity to registry and update all secondary lookup indexes."""
        if not isinstance(organization, Organization):
            raise TypeError(f"Expected Organization instance, got {type(organization).__name__}")

        self._registry[organization.id] = organization
        self._urn_index[organization.canonical_urn] = organization.id
        self._category_index[organization.category].add(organization.id)

        if organization.location_id is not None:
            self._location_index[organization.location_id].add(organization.id)

        if organization.meeting_site_id is not None:
            self._site_index[organization.meeting_site_id].add(organization.id)

        if organization.parent_org_id is not None:
            self._parent_index[organization.parent_org_id].add(organization.id)

        for alias in organization.aliases:
            self._alias_index[alias.lower()].add(organization.id)

        self._is_dirty = True

    def update(self, organization: Organization) -> None:
        """Replace an existing entity in the collection, re-indexing aliases, URNs, and foreign keys."""
        if not isinstance(organization, Organization):
            raise TypeError(f"Expected Organization instance, got {type(organization).__name__}")

        target_id = organization.id
        if target_id not in self._registry:
            raise OrganizationNotFoundError(
                f"Cannot update organization '{target_id}'; not found in registry."
            )

        old_org = self._registry[target_id]

        new_aliases = {a.lower() for a in organization.aliases}
        for old_alias in old_org.aliases:
            key = old_alias.lower()
            if key not in new_aliases and key in self._alias_index:
                self._alias_index[key].discard(target_id)
                if not self._alias_index[key]:
                    del self._alias_index[key]

        if old_org.canonical_urn != organization.canonical_urn:
            self._urn_index.pop(old_org.canonical_urn, None)

        if old_org.category != organization.category:
            self._category_index[old_org.category].discard(target_id)
            if not self._category_index[old_org.category]:
                del self._category_index[old_org.category]

        if old_org.location_id is not None and old_org.location_id != organization.location_id:
            self._location_index[old_org.location_id].discard(target_id)
            if not self._location_index[old_org.location_id]:
                del self._location_index[old_org.location_id]

        if (
            old_org.meeting_site_id is not None
            and old_org.meeting_site_id != organization.meeting_site_id
        ):
            self._site_index[old_org.meeting_site_id].discard(target_id)
            if not self._site_index[old_org.meeting_site_id]:
                del self._site_index[old_org.meeting_site_id]

        if (
            old_org.parent_org_id is not None
            and old_org.parent_org_id != organization.parent_org_id
        ):
            self._parent_index[old_org.parent_org_id].discard(target_id)
            if not self._parent_index[old_org.parent_org_id]:
                del self._parent_index[old_org.parent_org_id]

        self.add(organization)

    def soft_delete(
        self,
        item: OrganizationID | str,
        reason: str | None = None,
        superseded_by: OrganizationID | str | None = None,
    ) -> Organization:
        """Soft-delete an organization entity, reparenting active children if superseded."""
        retired = tombstone_organization(
            collection=self,
            org_id=item,
            reason=reason or "Organization retired",
            superseded_by=superseded_by,
        )
        self._is_dirty = True
        return retired

    def undelete(
        self,
        item: OrganizationID | str,
        locations_collection: Locations | None = None,
        sites_collection: Sites | None = None,
    ) -> Organization:
        """Restore a tombstoned organization back to active status and mark dirty."""
        restored = undelete_organization(
            collection=self,
            org_id=item,
            locations_collection=locations_collection,
            sites_collection=sites_collection,
        )
        self._is_dirty = True
        return restored

    def find_by_alias(self, alias: str) -> list[Organization]:
        """Query all active organizations matching a normalized alias."""
        cleaned = clean_string(alias)
        if not cleaned:
            return []
        org_ids = self._alias_index.get(cleaned.lower(), set())
        return [
            self._registry[oid]
            for oid in org_ids
            if oid in self._registry and not self._registry[oid].tombstone.is_deprecated
        ]

    def find_by_category(self, category: OrganizationCategory | str) -> list[Organization]:
        """Query all active organizations matching a specific functional classification."""
        cat = (
            category
            if isinstance(category, OrganizationCategory)
            else OrganizationCategory(category)
        )
        org_ids = self._category_index.get(cat, set())
        return [
            self._registry[oid]
            for oid in org_ids
            if oid in self._registry and not self._registry[oid].tombstone.is_deprecated
        ]

    def find_by_location(self, location_id: LocationID | str) -> list[Organization]:
        """Query all active organizations operating within a governing jurisdiction."""
        loc_id = location_id if isinstance(location_id, LocationID) else LocationID(location_id)
        org_ids = self._location_index.get(loc_id, set())
        return [
            self._registry[oid]
            for oid in org_ids
            if oid in self._registry and not self._registry[oid].tombstone.is_deprecated
        ]

    def find_by_site(self, site_id: SiteID | str) -> list[Organization]:
        """Query all active organizations meeting at a specific physical site."""
        s_id = site_id if isinstance(site_id, SiteID) else SiteID(site_id)
        org_ids = self._site_index.get(s_id, set())
        return [
            self._registry[oid]
            for oid in org_ids
            if oid in self._registry and not self._registry[oid].tombstone.is_deprecated
        ]

    def find_children(self, parent_org_id: OrganizationID | str) -> list[Organization]:
        """Query all active direct child chapters of a parent organization."""
        p_id = (
            parent_org_id
            if isinstance(parent_org_id, OrganizationID)
            else OrganizationID(parent_org_id)
        )
        org_ids = self._parent_index.get(p_id, set())
        return [
            self._registry[oid]
            for oid in org_ids
            if oid in self._registry and not self._registry[oid].tombstone.is_deprecated
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
        self._location_index.clear()
        self._site_index.clear()
        self._parent_index.clear()
        loaded = load_from_db(self)
        self.mark_clean()
        return loaded

    def import_file(self, path: Path | str) -> int:
        """Import organization entities from a formatted JSON file via util helper."""
        return import_file(self, path)

    def export_file(self, path: Path | str, include_graveyard: bool = True) -> int:
        """Export organization entities to a JSON file via util helper."""
        return export_file(self, path, include_graveyard=include_graveyard)

    def create(
        self,
        name: str,
        category: OrganizationCategory | str,
        canonical_urn: str | None = None,
        parent_org_id: OrganizationID | str | None = None,
        predecessor_ids: list[OrganizationID | str] | None = None,
        successor_ids: list[OrganizationID | str] | None = None,
        location_id: LocationID | str | None = None,
        meeting_site_id: SiteID | str | None = None,
        period: TimePeriod | None = None,
        alternate_names: list[str] | None = None,
        notes: list[Note] | None = None,
        is_active: bool = True,
        locations_collection: Locations | None = None,
        sites_collection: Sites | None = None,
    ) -> Organization:
        """Create, register, and index a new Organization entity (parent_org_id is optional)."""
        cleaned_name = clean_string(name)
        if not cleaned_name:
            raise ModelFormatError("Organization name cannot be blank or whitespace.")

        res_cat = (
            category
            if isinstance(category, OrganizationCategory)
            else OrganizationCategory(category)
        )

        res_parent_id: OrganizationID | None = None
        parent_urn_prefix: str | None = None
        if parent_org_id is not None:
            parent_org = self[parent_org_id]
            res_parent_id = parent_org.id
            parent_urn_prefix = parent_org.canonical_urn

        res_loc_id: LocationID | None = None
        if location_id is not None:
            res_loc_id = (
                location_id if isinstance(location_id, LocationID) else LocationID(location_id)
            )
            if locations_collection is not None and res_loc_id not in locations_collection:
                raise OrganizationValidationError(
                    f"Governing location '{res_loc_id}' does not exist or is tombstoned."
                )

        res_site_id: SiteID | None = None
        if meeting_site_id is not None:
            res_site_id = (
                meeting_site_id if isinstance(meeting_site_id, SiteID) else SiteID(meeting_site_id)
            )
            if sites_collection is not None and res_site_id not in sites_collection:
                raise OrganizationValidationError(
                    f"Meeting site '{res_site_id}' does not exist or is tombstoned."
                )

        next_num = extract_max_smart_id(self._registry.keys(), prefix=SmartIDPrefix.ORG) + 1
        org_id = OrganizationID(mint_smart_id(SmartIDPrefix.ORG, next_num))

        if canonical_urn:
            urn = canonical_urn.strip()
        elif parent_urn_prefix:
            base_slug = slugify(cleaned_name, delimiter="_")
            urn = f"{parent_urn_prefix}:{base_slug}"
        elif res_loc_id is not None:
            base_slug = slugify(cleaned_name, delimiter="_")
            loc_slug = str(res_loc_id).lower().replace("-", "_")
            urn = f"urn:gda:org:{loc_slug}:{base_slug}_o{org_id.suffix.lower()}"
        else:
            base_slug = slugify(cleaned_name, delimiter="_")
            urn = f"urn:gda:org:{base_slug}_o{org_id.suffix.lower()}"

        now = IsoTimestamp(utc_now_iso())
        audit = AuditStamp(created_at=now, updated_at=now)

        name_obj = NameThing.create(raw=cleaned_name, canonical=cleaned_name)
        if alternate_names:
            for alt in alternate_names:
                c = clean_string(alt)
                if c:
                    name_obj = name_obj.add_alias(c)

        org = Organization.create(
            org_id=org_id,
            audit=audit,
            name=name_obj,
            category=res_cat,
            canonical_urn=urn,
            parent_org_id=res_parent_id,
            predecessor_ids=predecessor_ids,
            successor_ids=successor_ids,
            location_id=res_loc_id,
            meeting_site_id=res_site_id,
            period=period,
            notes=notes or [],
            is_active=is_active,
            tombstone=Tombstone[OrganizationID](),
        )

        self.add(org)
        return org
