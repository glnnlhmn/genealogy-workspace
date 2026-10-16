<!-- Name: README.md -->
<!-- Path: src/gda/model/README.md -->

# GDA Canonical Model Package (`gda.model`)

## Operational Role & Purpose
Houses the centralized Pydantic domain models, reference resolution engines, controlled vocabulary governance, and partitioned entity schemas.

## Package Architecture & Boundaries
Consolidated from legacy plural modeling packages into a singular canonical package:
- `reference.py`: URN validation, citation resolution, and reference authority management.
- `vocabulary.py`: Master controlled vocabulary lookup and taxonomy governance.
- `types.py`: High-level data types and composite structures.
- `entity/`: Typed Pydantic models representing primary domain entities (person, fact, location, site).
- `base/`: Base validation classes, serialization mixins, and common model wrappers.
- `enumerated/`: Typed enumeration models wrapping canonical enums.
- `media/`: Digital media, asset metadata, and cryptographic checksum models.
- `military/`: Military service records, regiments, and conflict classifications.
- `orgs/`: Historical religious, fraternal, municipal, and commercial organization schemas.
- `vital/`: Vital statistics and milestone lifecycle schemas.

## Architectural Contracts
- **Pydantic Validation**: All schemas inherit from Pydantic `BaseModel` to enforce rigorous typing and structural constraints.
- **I/O Decoupling**: Models contain zero direct physical I/O or database access logic. Persistence operations are strictly delegated to `gda.io` and `gda.data`.