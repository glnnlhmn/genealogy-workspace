<!--Path: src/gda/entity/README.md-->
# Domain Entity Collection Managers & Relational Authorities (src/gda/entity)

## Architectural Role
Top-level package facade uniting the six in-memory domain entity collection managers (Facts, Families, Individuals, Locations, Organizations, Sites), relational validators, graveyard lifecycle operators, and persistence gateways.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_entity/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Subpackages
- **[facts/](facts/README.md)**: Authoritative evidentiary fact entity management subpackage.
- **[families/](families/README.md)**: Authoritative domestic family unit entity management subpackage.
- **[individuals/](individuals/README.md)**: Authoritative individual persona entity management subpackage.
- **[locations/](locations/README.md)**: Authoritative jurisdiction and location entity management subpackage.
- **[organizations/](organizations/README.md)**: Authoritative voluntary association and institutional organization entity management subpackage.
- **[sites/](sites/README.md)**: Authoritative physical site entity management subpackage.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |

## Public Exports & Consumption Contract
Exports: `FactError`, `FactNotFoundError`, `FactValidationError`, `Facts`, `Families`, `FamilyError`, `FamilyNotFoundError`, `FamilyValidationError`, `IndividualError`, `IndividualNotFoundError`, `IndividualValidationError`, `Individuals`, `LocationError`, `LocationHierarchyError`, `LocationNotFoundError`, `Locations`, `OrganizationError`, `OrganizationHierarchyError`, `OrganizationNotFoundError`, `OrganizationValidationError`, `Organizations`, `SiteError`, `SiteNotFoundError`, `SiteValidationError`, `Sites`, `facts`, `families`, `individuals`, `locations`, `organizations`, `sites`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: a3fcbf5530f90d45 -->
