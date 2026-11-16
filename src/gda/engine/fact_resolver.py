"""Path: src/gda/engine/fact_resolver.py

Active in-memory fact participant inverted indexer and relationship resolver.

Operational Role:
    Provides in-memory inverted index resolution infrastructure for event
    participants. 'FactParticipantResolver' manages bidirectional mappings between
    individual persons and domain fact assertions, enabling O(1) witness/informant
    lookups, dynamic incremental indexing, and safe entity eviction.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from gda.core.dates import utc_now_iso
from gda.core.enums.core import AssociatedRole
from gda.core.introspectable import IntrospectableMixin
from gda.core.logging import GDALogger
from gda.model.atom.date import IsoTimestamp
from gda.model.atom.id import FactID, IndividualID
from gda.model.atom.year import HistoricalYear
from gda.model.entity.fact import Fact
from gda.model.xref.fact_participant_xref import FactParticipantXRef

__version__ = "1.0.0+build.2"

__all__ = ["FactParticipantResolver"]

_logger = GDALogger(__name__)


class FactParticipantResolver(IntrospectableMixin):
    """In-memory inverted indexer resolving individuals to fact participation roles."""

    def __init__(self) -> None:
        """Initialize empty graph index tables and compilation timestamp."""
        self._last_compiled: IsoTimestamp = IsoTimestamp(utc_now_iso())
        self._edges: dict[str, FactParticipantXRef] = {}

        self._ind_to_facts: dict[IndividualID, set[tuple[FactID, AssociatedRole]]] = defaultdict(
            set
        )
        self._fact_to_participants: dict[FactID, list[tuple[IndividualID, AssociatedRole]]] = (
            defaultdict(list)
        )

    @property
    def last_compiled(self) -> IsoTimestamp:
        """Return the compilation timestamp of the index state."""
        return self._last_compiled

    @property
    def edge_count(self) -> int:
        """Return the total count of indexed fact participant edges."""
        return len(self._edges)

    def _mark_updated(self) -> None:
        """Advance the index compilation timestamp."""
        self._last_compiled = IsoTimestamp(utc_now_iso())

    @classmethod
    def from_facts(cls, facts: Iterable[Fact]) -> FactParticipantResolver:
        """Hydrate graph index directly from an iterable of Fact domain entities."""
        resolver = cls()
        for fact in facts:
            resolver.index_fact(fact)
        return resolver

    @classmethod
    def from_xrefs(cls, xrefs: Iterable[FactParticipantXRef]) -> FactParticipantResolver:
        """Hydrate graph index directly from an iterable of pre-formed FactParticipantXRef edges."""
        resolver = cls()
        for edge in xrefs:
            resolver.add_xref(edge)
        return resolver

    def add_xref(self, edge: FactParticipantXRef) -> None:
        """Add a single pre-formed FactParticipantXRef edge into index tables."""
        key = edge.xref_key
        if key in self._edges:
            return

        self._edges[key] = edge
        self._ind_to_facts[edge.individual_id].add((edge.fact_id, edge.role))

        entry = (edge.individual_id, edge.role)
        if entry not in self._fact_to_participants[edge.fact_id]:
            self._fact_to_participants[edge.fact_id].append(entry)

        self._mark_updated()

    def index_fact(self, fact: Fact) -> None:
        """Index all secondary participants recorded on a Fact domain entity."""
        raw_year = fact.year_lower_bound
        year_atom = HistoricalYear(raw_year) if raw_year is not None else None

        for participant in fact.participants:
            edge = FactParticipantXRef(
                fact_id=fact.id,
                individual_id=participant.individual_id,
                role=participant.role,
                fact_type=fact.fact_type,
                is_primary_subject=False,
                temporal_year=year_atom,
                location_id=fact.location_id,
                site_id=fact.site_id,
            )
            self.add_xref(edge)

    def evict_individual(self, individual_id: IndividualID) -> None:
        """Safely remove all participation edges and index mappings for an individual."""
        keys_to_delete = [
            k for k, edge in self._edges.items() if edge.individual_id == individual_id
        ]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        associated_facts = self._ind_to_facts.pop(individual_id, set())
        for fid, _ in associated_facts:
            self._fact_to_participants[fid] = [
                (iid, r) for iid, r in self._fact_to_participants[fid] if iid != individual_id
            ]

        self._mark_updated()

    def evict_fact(self, fact_id: FactID) -> None:
        """Safely remove all participant edges and index mappings for a fact."""
        keys_to_delete = [k for k, edge in self._edges.items() if edge.fact_id == fact_id]

        if not keys_to_delete:
            return

        for k in keys_to_delete:
            del self._edges[k]

        participants = self._fact_to_participants.pop(fact_id, [])
        for iid, role in participants:
            self._ind_to_facts[iid].discard((fact_id, role))

        self._mark_updated()

    def get_facts_as_participant(
        self,
        individual_id: IndividualID,
        role: AssociatedRole | None = None,
    ) -> tuple[FactID, ...]:
        """Return tuple of FactIDs where individual participated, optionally filtered by role."""
        entries = self._ind_to_facts.get(individual_id, set())
        if role is not None:
            return tuple(sorted(fid for fid, r in entries if r == role))
        return tuple(sorted({fid for fid, _ in entries}))

    def get_participants_for_fact(
        self, fact_id: FactID
    ) -> tuple[tuple[IndividualID, AssociatedRole], ...]:
        """Return ordered tuple of all participants and roles linked to a fact assertion."""
        return tuple(self._fact_to_participants.get(fact_id, []))

    def get_roles_for_individual(self, individual_id: IndividualID) -> tuple[AssociatedRole, ...]:
        """Return sorted tuple of unique roles an individual has served in across all facts."""
        entries = self._ind_to_facts.get(individual_id, set())
        return tuple(sorted({r for _, r in entries}, key=lambda x: x.value))

    def export_xrefs(self) -> list[FactParticipantXRef]:
        """Export all current indexed edges as a list of FactParticipantXRef objects."""
        return list(self._edges.values())
