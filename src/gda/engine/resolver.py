"""Path: src/gda/engine/resolver.py

Active in-memory graph indexers and bidirectional relationship resolvers.

Operational Role:
    Provides high-performance, in-memory graph resolution infrastructure for
    genealogical traversals. 'IndividualFamilyResolver' indexes individual personas,
    union partnerships, parentage, and child pedigree classifications, enabling
    O(1) kinship lookups, dynamic incremental indexing, and safe entity eviction.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from gda.core.dates import utc_now_iso
from gda.core.enums.vital import PedigreeType
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FamilyID, IndividualID
from gda.model.entity.family import Family
from gda.model.entity.individual import Individual
from gda.model.xref.individual_family_xref import IndividualFamilyXRef

__version__ = "1.0.0+build.5"

__all__ = ["IndividualFamilyResolver"]

_logger = GDALogger(__name__)


class IndividualFamilyResolver(IntrospectableMixin):
    """In-memory bidirectional kinship indexer and family tree resolver."""

    def __init__(self) -> None:
        """Initialize empty graph index tables and compilation timestamp."""
        self._last_compiled: IsoTimestamp = IsoTimestamp(utc_now_iso())
        self._edges: dict[str, IndividualFamilyXRef] = {}
        self._individuals: set[IndividualID] = set()

        self._ind_to_fam_partner: dict[IndividualID, set[FamilyID]] = defaultdict(set)
        self._ind_to_fam_child: dict[IndividualID, set[FamilyID]] = defaultdict(set)
        self._fam_to_partners: dict[FamilyID, list[IndividualID]] = defaultdict(list)
        self._fam_to_children: dict[FamilyID, list[tuple[IndividualID, PedigreeType]]] = (
            defaultdict(list)
        )

    @property
    def last_compiled(self) -> IsoTimestamp:
        """Return the compilation timestamp of the index state."""
        return self._last_compiled

    @property
    def edge_count(self) -> int:
        """Return the total count of indexed cross-reference edges."""
        return len(self._edges)

    def _mark_updated(self) -> None:
        """Advance the index compilation timestamp."""
        self._last_compiled = IsoTimestamp(utc_now_iso())

    @classmethod
    def from_collections(
        cls,
        individuals: Iterable[Individual] = (),
        families: Iterable[Family] = (),
    ) -> IndividualFamilyResolver:
        """Hydrate graph index from collections of Individual and Family entities."""
        resolver = cls()
        for ind in individuals:
            resolver.index_individual(ind)
        for fam in families:
            resolver.index_family(fam)
        return resolver

    @classmethod
    def from_xrefs(cls, xrefs: Iterable[IndividualFamilyXRef]) -> IndividualFamilyResolver:
        """Hydrate graph index directly from an iterable of pre-formed IndividualFamilyXRef edges."""
        resolver = cls()
        for edge in xrefs:
            resolver.add_xref(edge)
        return resolver

    def add_xref(self, edge: IndividualFamilyXRef) -> None:
        """Add a single pre-formed IndividualFamilyXRef edge into index tables."""
        key = edge.xref_key
        if key in self._edges:
            return

        self._edges[key] = edge
        if edge.is_partner:
            self._ind_to_fam_partner[edge.individual_id].add(edge.family_id)
            if edge.individual_id not in self._fam_to_partners[edge.family_id]:
                self._fam_to_partners[edge.family_id].append(edge.individual_id)
        else:
            pedigree = edge.pedigree if edge.pedigree is not None else PedigreeType.BIRTH
            self._ind_to_fam_child[edge.individual_id].add(edge.family_id)
            entry = (edge.individual_id, pedigree)
            if entry not in self._fam_to_children[edge.family_id]:
                self._fam_to_children[edge.family_id].append(entry)

        self._mark_updated()

    def index_individual(self, individual: Individual) -> None:
        """Register an Individual domain entity in the resolver."""
        self._individuals.add(individual.id)
        self._mark_updated()

    def index_family(self, family: Family) -> None:
        """Index a Family entity, domestic partners, and children links."""
        fam_id = family.id

        for partner_id in family.partner_ids:
            edge = IndividualFamilyXRef(
                family_id=fam_id,
                individual_id=partner_id,
                is_partner=True,
            )
            self.add_xref(edge)

        for idx, child_link in enumerate(family.children, start=1):
            child_id = child_link.child_id
            pedigree = child_link.pedigree or PedigreeType.BIRTH
            edge = IndividualFamilyXRef(
                family_id=fam_id,
                individual_id=child_id,
                is_partner=False,
                pedigree=pedigree,
                child_order=idx,
            )
            self.add_xref(edge)

    def evict_entity(self, entity_id: IndividualID | FamilyID) -> None:
        """Safely remove all cross-reference edges and index mappings for an entity."""
        keys_to_delete = [
            k
            for k, edge in self._edges.items()
            if edge.individual_id == entity_id or edge.family_id == entity_id
        ]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        if isinstance(entity_id, IndividualID):
            self._individuals.discard(entity_id)
            self._ind_to_fam_partner.pop(entity_id, None)
            self._ind_to_fam_child.pop(entity_id, None)

            for fam_id, partners in list(self._fam_to_partners.items()):
                self._fam_to_partners[fam_id] = [p for p in partners if p != entity_id]

            for fam_id, children in list(self._fam_to_children.items()):
                self._fam_to_children[fam_id] = [c for c in children if c[0] != entity_id]

        else:
            self._fam_to_partners.pop(entity_id, None)
            self._fam_to_children.pop(entity_id, None)

            for fams in list(self._ind_to_fam_partner.values()):
                fams.discard(entity_id)
            for fams in list(self._ind_to_fam_child.values()):
                fams.discard(entity_id)

        self._mark_updated()

    def get_families_as_partner(self, individual_id: IndividualID) -> tuple[FamilyID, ...]:
        """Return tuple of FamilyIDs where individual is registered as a partner."""
        return tuple(sorted(self._ind_to_fam_partner.get(individual_id, set())))

    def get_families_as_child(self, individual_id: IndividualID) -> tuple[FamilyID, ...]:
        """Return tuple of FamilyIDs where individual is registered as a child."""
        return tuple(sorted(self._ind_to_fam_child.get(individual_id, set())))

    def get_spouses(self, individual_id: IndividualID) -> tuple[IndividualID, ...]:
        """Return tuple of all co-partner IndividualIDs across shared families."""
        spouses: set[IndividualID] = set()
        for fam_id in self._ind_to_fam_partner.get(individual_id, set()):
            for partner in self._fam_to_partners.get(fam_id, []):
                if partner != individual_id:
                    spouses.add(partner)
        return tuple(sorted(spouses))

    def get_children(self, individual_id: IndividualID) -> tuple[IndividualID, ...]:
        """Return tuple of all child IndividualIDs across partner families."""
        children: set[IndividualID] = set()
        for fam_id in self._ind_to_fam_partner.get(individual_id, set()):
            for child_id, _ in self._fam_to_children.get(fam_id, []):
                children.add(child_id)
        return tuple(sorted(children))

    def get_parents(self, individual_id: IndividualID) -> tuple[IndividualID, ...]:
        """Return tuple of all parental IndividualIDs for an individual child."""
        parents: set[IndividualID] = set()
        for fam_id in self._ind_to_fam_child.get(individual_id, set()):
            for parent_id in self._fam_to_partners.get(fam_id, []):
                parents.add(parent_id)
        return tuple(sorted(parents))

    def get_pedigree_for_child(
        self, child_id: IndividualID, family_id: FamilyID
    ) -> PedigreeType | None:
        """Return lineage pedigree classification for a child in a given family."""
        for c_id, pedigree in self._fam_to_children.get(family_id, []):
            if c_id == child_id:
                return pedigree
        return None

    def export_xrefs(self) -> list[IndividualFamilyXRef]:
        """Export all current indexed edges as a list of IndividualFamilyXRef objects."""
        return list(self._edges.values())
