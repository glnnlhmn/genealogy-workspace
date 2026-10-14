# Architecture Blueprint: Consolidated GDA Engine

## Package Boundaries
1. **gda.core**: Zero internal imports. Foundational config, logging, fs, and introspection.
2. **gda.io**: PyArrow tabular ingestion, integrity manifests, and JSON schema catalog.
3. **gda.model**: Domain entities (Person, Fact, Location, Site), value types, reference & vocab managers.
