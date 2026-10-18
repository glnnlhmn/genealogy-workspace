<!-- Name: README.md -->
<!-- Path: src/gda/entity/README.md -->

# GDA Domain Record Entities (`gda.entity`)

## Operational Role & Purpose
Defines domain record state representations, field mutations, and localized validation logic for primary digital archive records.

## Core Entity Representations
- `person.py`: Person record state, personal names, demographic attributes, and lifetime milestones.
- `fact.py`: Atomic evidentiary assertions, citation references, and in-place tombstoning support.
- `location.py`: Jurisdictional geocoding records, historical boundary markers, and hierarchy.
- `site.py`: Repositories, cemeteries, libraries, archives, and physical record sites.

## Architectural Governance
- **State Representation**: Enforces field validation and identity encapsulation for individual records.
- **Manager Decoupling**: Entities do not interact directly with physical databases, collection caches, or global registries; collection orchestration is handled exclusively by `gda.manager`.

## Development Status
Active development.