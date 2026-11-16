"""Path: tests/test_gda/test_db/test_db_contract.py

Interface contract and end-to-end integration test suite for the gda.db package facade.

Operational Role:
    1:1 verification suite for src/gda/db/__init__.py. Validates the public
    __all__ export manifest, alphabetical sorting, symbol identity across
    submodules (exceptions, session, schema, mapper), version metadata, and
    end-to-end SQLite round-trip persistence across all 6 gda.entity collections.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import gda.db as db_pkg
from gda.core.config import DatabaseConfig
from gda.core.enums.core import FactType
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.site import SiteType
from gda.db import (
    MIGRATION_REGISTRY,
    BaseRowMapper,
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationalError,
    DatabaseSessionManager,
    DirtyStateError,
    EntityMappingError,
    FactRowMapper,
    FamilyRowMapper,
    IndividualRowMapper,
    LocationRowMapper,
    Migration,
    OrganizationRowMapper,
    RecordNotFoundError,
    SchemaManager,
    SchemaMigrationError,
    SiteRowMapper,
    TransactionError,
    get_mapper,
)
from gda.entity import Facts, Families, Individuals, Locations, Organizations, Sites

__version__ = "1.0.0+build.1"


@pytest.mark.unit
def test_db_root_facade_dunder_all_and_sorting_contract() -> None:
    """Verify gda.db.__all__ is sorted and every exported symbol is resolvable."""
    expected = [
        "BaseRowMapper",
        "ConnectionTimeoutError",
        "ConstraintViolationError",
        "DatabaseConnectionError",
        "DatabaseError",
        "DatabaseOperationalError",
        "DatabaseSessionManager",
        "DirtyStateError",
        "EntityMappingError",
        "FactRowMapper",
        "FamilyRowMapper",
        "IndividualRowMapper",
        "LocationRowMapper",
        "MIGRATION_REGISTRY",
        "Migration",
        "OrganizationRowMapper",
        "RecordNotFoundError",
        "SchemaManager",
        "SchemaMigrationError",
        "SiteRowMapper",
        "TransactionError",
        "get_mapper",
    ]
    assert db_pkg.__all__ == expected
    assert db_pkg.__all__ == sorted(db_pkg.__all__)
    assert hasattr(db_pkg, "__version__")

    for symbol in db_pkg.__all__:
        assert hasattr(db_pkg, symbol), f"Missing exported symbol on gda.db: {symbol}"


@pytest.mark.unit
def test_db_root_facade_reexport_identity() -> None:
    """Verify symbols imported from gda.db match their submodule definitions."""
    assert issubclass(ConnectionTimeoutError, DatabaseConnectionError)
    assert issubclass(ConstraintViolationError, DatabaseError)
    assert issubclass(DatabaseOperationalError, DatabaseError)
    assert issubclass(DirtyStateError, DatabaseError)
    assert issubclass(EntityMappingError, DatabaseError)
    assert issubclass(RecordNotFoundError, DatabaseError)
    assert issubclass(SchemaMigrationError, DatabaseError)
    assert issubclass(TransactionError, DatabaseError)
    assert issubclass(LocationRowMapper, BaseRowMapper)
    assert issubclass(SiteRowMapper, BaseRowMapper)
    assert issubclass(OrganizationRowMapper, BaseRowMapper)
    assert issubclass(IndividualRowMapper, BaseRowMapper)
    assert issubclass(FamilyRowMapper, BaseRowMapper)
    assert issubclass(FactRowMapper, BaseRowMapper)
    assert callable(get_mapper)
    assert isinstance(MIGRATION_REGISTRY, list)
    assert all(isinstance(m, Migration) for m in MIGRATION_REGISTRY)
    assert DatabaseSessionManager is not None
    assert SchemaManager is not None


@pytest.mark.integration
def test_db_end_to_end_all_six_entity_collections_round_trip(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify all 6 gda.entity collections persist and reload via gda.db against SQLite."""
    db_path = tmp_path / "contract_e2e.db"
    orig_init = DatabaseSessionManager.__init__

    def _patched_init(self: DatabaseSessionManager, *args: object, **kwargs: object) -> None:
        orig_init(self, db_path=db_path, config=DatabaseConfig(db_path=db_path))

    monkeypatch.setattr(DatabaseSessionManager, "__init__", _patched_init)

    locs = Locations()
    bow = locs.create_hierarchy(country="USA", state="NH", county="Merrimack", township="Bow")
    assert locs.save_to_db() == 4

    sits = Sites()
    hall = sits.create(name="Bow Town Hall", category=SiteType.GOVERNMENT, location_id=bow.id)
    assert sits.save_to_db() == 1

    orgs = Organizations()
    vfw = orgs.create(
        name="VFW Post 411",
        category=OrganizationCategory.VETERANS,
        location_id=bow.id,
        meeting_site_id=hall.id,
    )
    assert orgs.save_to_db() == 1

    inds = Individuals()
    ind = inds.create(
        name="John Adams",
        gender="M",
        birth_date="1735-10-30",
        birth_place_id=bow.id,
    )
    assert inds.save_to_db() == 1

    fams = Families()
    fam = fams.create(partner_ids=[ind.id])
    assert fams.save_to_db() == 1

    fcts = Facts()
    fct = fcts.create(
        fact_type=FactType.BIRTH,
        title="Birth of John Adams",
        primary_subject_id=ind.id,
        location_id=bow.id,
        site_id=hall.id,
    )
    assert fcts.save_to_db() == 1

    assert Locations.from_database()[bow.id] == bow
    assert Sites.from_database()[hall.id] == hall
    assert Organizations.from_database()[vfw.id] == vfw
    assert Individuals.from_database()[ind.id] == ind
    assert Families.from_database()[fam.id] == fam
    assert Facts.from_database()[fct.id] == fct
