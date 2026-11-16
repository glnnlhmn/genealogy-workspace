"""Path: tests/test_gda/test_entity/test_entity_contract.py

Authoritative top-level package contract and cross-entity integration test suite for gda.entity.

Operational Role:
    Verifies the 6-subpackage topology of gda.entity, enforces the sorted
    28-symbol __all__ contract of gda.entity.__init__.py, tests end-to-end
    cross-entity relational workflows across Locations, Sites, Organizations,
    Individuals, Families, and Facts, and verifies zero legacy imports across
    the entire gda.entity package tree.
"""

from __future__ import annotations

import ast
import inspect
import pkgutil
from pathlib import Path

import pytest

import gda.entity as entity_pkg
from gda.core.enums.core import AssociatedRole, FactType
from gda.core.enums.orgs import OrganizationCategory
from gda.core.enums.site import SiteType
from gda.core.enums.vital import PedigreeType
from gda.core.errors import GenealogyDeskError
from gda.core.introspectable import IntrospectableMixin
from gda.entity import (
    FactError,
    FactNotFoundError,
    Facts,
    FactValidationError,
    Families,
    FamilyError,
    FamilyNotFoundError,
    FamilyValidationError,
    IndividualError,
    IndividualNotFoundError,
    Individuals,
    IndividualValidationError,
    LocationError,
    LocationHierarchyError,
    LocationNotFoundError,
    Locations,
    OrganizationError,
    OrganizationHierarchyError,
    OrganizationNotFoundError,
    Organizations,
    OrganizationValidationError,
    SiteError,
    SiteNotFoundError,
    Sites,
    SiteValidationError,
    facts,
    families,
    individuals,
    locations,
    organizations,
    sites,
)
from gda.model.entity.fact import FactParticipant

__version__ = "1.0.0+build.1"

_EXPECTED_SUBPACKAGES = {
    "facts",
    "families",
    "individuals",
    "locations",
    "organizations",
    "sites",
}

AUTHORITATIVE_ENTITY_ROOT_EXPORTS = [
    "FactError",
    "FactNotFoundError",
    "FactValidationError",
    "Facts",
    "Families",
    "FamilyError",
    "FamilyNotFoundError",
    "FamilyValidationError",
    "IndividualError",
    "IndividualNotFoundError",
    "IndividualValidationError",
    "Individuals",
    "LocationError",
    "LocationHierarchyError",
    "LocationNotFoundError",
    "Locations",
    "OrganizationError",
    "OrganizationHierarchyError",
    "OrganizationNotFoundError",
    "OrganizationValidationError",
    "Organizations",
    "SiteError",
    "SiteNotFoundError",
    "SiteValidationError",
    "Sites",
    "facts",
    "families",
    "individuals",
    "locations",
    "organizations",
    "sites",
]


@pytest.mark.smoke
@pytest.mark.integration
def test_entity_root_cross_package_relational_pipeline() -> None:
    """Verify end-to-end relational integrity across all 6 gda.entity collections."""
    locs = Locations()
    sits = Sites()
    orgs = Organizations()
    inds = Individuals()
    fams = Families()
    fcts = Facts()

    # 1. Build 4-tier jurisdiction in Locations
    bow = locs.create_hierarchy(
        country="United States",
        state="New Hampshire",
        county="Merrimack",
        township="Bow",
    )

    # 2. Create physical Site in Bow
    church = sits.create(
        name="Old First Parish Church",
        category=SiteType.CHURCH,
        location_id=bow.id,
        locations_collection=locs,
    )

    # 3. Create standalone local VFW Post in Bow meeting at the Site
    vfw = orgs.create(
        name="VFW Post 411",
        category=OrganizationCategory.VETERANS,
        location_id=bow.id,
        meeting_site_id=church.id,
        locations_collection=locs,
        sites_collection=sits,
    )
    assert vfw.parent_org_id is None

    # 4. Create Individuals (husband, wife, child, witness)
    husband = inds.create(
        name="John Adams",
        gender="M",
        birth_date="1735-10-30",
        birth_place_id=bow.id,
        locations_collection=locs,
        sites_collection=sits,
    )
    wife = inds.create(
        name="Abigail Smith",
        gender="F",
        birth_date="1744-11-22",
        married_names=["Adams"],
        birth_place_id=bow.id,
        death_place_id=church.id,
        locations_collection=locs,
        sites_collection=sits,
    )
    child = inds.create(
        name="John Quincy Adams",
        gender="M",
        birth_date="1767-07-11",
        birth_place_id=bow.id,
        locations_collection=locs,
    )
    witness = inds.create(
        name="Samuel Adams",
        gender="M",
        birth_date="1722-09-27",
    )

    # 5. Create Family linking husband, wife, and child
    fam = fams.create(
        partner_ids=[husband.id, wife.id],
        children=[(child.id, PedigreeType.BIRTH)],
        individuals_collection=inds,
    )

    # 6. Create Facts anchored to both Individual and Family subjects
    birth_fact = fcts.create(
        fact_type=FactType.BIRTH,
        title="Birth of John Quincy Adams",
        primary_subject_id=child.id,
        date="1767-07-11",
        location_id=bow.id,
        site_id=church.id,
        participants=[FactParticipant.create(witness.id, AssociatedRole.WITNESS)],
        locations_collection=locs,
        sites_collection=sits,
        individuals_collection=inds,
        families_collection=fams,
    )
    marriage_fact = fcts.create(
        fact_type=FactType.MARRIAGE,
        title="Marriage of John and Abigail",
        primary_subject_id=fam.id,
        date="1764-10-25",
        location_id=bow.id,
        site_id=church.id,
        locations_collection=locs,
        sites_collection=sits,
        individuals_collection=inds,
        families_collection=fams,
    )

    assert locations.valid_collection_all(locs) is True
    assert sites.valid_collection_all(sits, locations_collection=locs) is True
    assert (
        organizations.valid_collection_all(orgs, locations_collection=locs, sites_collection=sits)
        is True
    )
    assert (
        individuals.valid_collection_all(inds, locations_collection=locs, sites_collection=sits)
        is True
    )
    assert families.valid_collection_all(fams, individuals_collection=inds) is True
    assert (
        facts.valid_collection_all(
            fcts,
            locations_collection=locs,
            sites_collection=sits,
            individuals_collection=inds,
            families_collection=fams,
        )
        is True
    )
    assert fcts.find_by_subject(child.id) == [birth_fact]
    assert fcts.find_by_subject(fam.id) == [marriage_fact]


@pytest.mark.unit
@pytest.mark.integrity
def test_entity_root_topology_and_dunder_all_contract() -> None:
    """Verify gda.entity subpackage topology and sorted 31-symbol __all__ contract."""
    discovered = {m.name for m in pkgutil.iter_modules(entity_pkg.__path__)}
    assert discovered == _EXPECTED_SUBPACKAGES

    assert entity_pkg.__all__ == AUTHORITATIVE_ENTITY_ROOT_EXPORTS
    assert entity_pkg.__all__ == sorted(entity_pkg.__all__)
    for attr in AUTHORITATIVE_ENTITY_ROOT_EXPORTS:
        assert hasattr(entity_pkg, attr), f"Export '{attr}' missing from gda.entity"


@pytest.mark.unit
@pytest.mark.integrity
def test_entity_root_exported_collections_and_errors_inheritance() -> None:
    """Verify all 6 collection managers and 19 domain exceptions inherit from canonical bases."""
    for coll_cls in (Locations, Sites, Organizations, Facts, Individuals, Families):
        assert issubclass(coll_cls, IntrospectableMixin)

    for err_cls in (
        FactError,
        FactNotFoundError,
        FactValidationError,
        FamilyError,
        FamilyNotFoundError,
        FamilyValidationError,
        IndividualError,
        IndividualNotFoundError,
        IndividualValidationError,
        LocationError,
        LocationHierarchyError,
        LocationNotFoundError,
        OrganizationError,
        OrganizationHierarchyError,
        OrganizationNotFoundError,
        OrganizationValidationError,
        SiteError,
        SiteNotFoundError,
        SiteValidationError,
    ):
        assert issubclass(err_cls, GenealogyDeskError)


@pytest.mark.unit
@pytest.mark.integrity
def test_entity_root_version_and_zero_legacy_imports() -> None:
    """Verify 1.0.0+build.X version metadata and zero legacy imports across all of gda.entity."""
    assert entity_pkg.__version__.startswith("1.0.0+build.")
    pkg_dir = Path(inspect.getfile(entity_pkg)).parent
    for py_path in pkg_dir.rglob("*.py"):
        tree = ast.parse(py_path.read_text(encoding="utf-8"), filename=str(py_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                assert not node.module.startswith(
                    ("gda.enums", "gda.util.tombstone", "gda.model.atom.geo")
                ), f"Forbidden legacy import in {py_path}: '{node.module}'"
