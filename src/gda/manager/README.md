<!-- Name: README.md -->
<!-- Path: src/gda/manager/README.md -->

# GDA Collection & Authority Management (`gda.manager`)

## Operational Role & Purpose
Provides collection-level managers, transactional orchestrators, and cache coordinators for reference indexing and controlled vocabulary governance.

## Architectural Governance
- **Collection Management**: Coordinates complex transactions across entity collections, managing cached indexes and resolving entity links.
- **Key Subpackages**:
  - `referencer/`: Reference resolution and cross-entity reference validation.
  - `vocab/`: Vocabulary management, kinship taxonomies, and schema enumeration drift detection.
- **Decoupling**: Consumes entity state models from `gda.entity` and Pydantic schemas from `gda.model` without embedding low-level database operations.

## Development Status
Active development. Serves as the middle-tier transaction layer between entity state and database interfaces.