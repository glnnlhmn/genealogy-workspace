<!-- Name: README.md -->
<!-- Path: src/gda/engine/README.md -->

# GDA Computational & Algorithmic Engines (`gda.engine`)

## Operational Role & Purpose
Houses domain calculation engines, kinship resolution graphs, demographic plausibility auditors, and business-rule validation pipelines.

## Architectural Governance
- **Stateless Computation**: Focuses on algorithmic analysis and graph traversal rather than persistence or raw data storage.
- **Core Engine Subpackages**:
  - `kinship/`: Reciprocal relationship mapping, degree-of-consanguinity calculations, and family tree graph traversals.
  - `plausibility/`: Biological plausibility checks (e.g., mother child-bearing age ranges, lifespan bounds, chronological sequence validation).
- **Rule Enforcement**: Evaluates domain entities against strict historical and demographic sanity rules to flag genealogical anomalies.

## Development Status
Active development. Implements algorithmic solvers, graph analyzers, and rule engines.