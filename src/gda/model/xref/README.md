<!--Path: src/gda/model/xref/README.md-->
# Cross-Reference & Derived Relational Index Models (src/gda/model/xref)

## Architectural Role
Tier-4 decoupled, immutable relational edge dataclasses connecting individuals, families, organizations, facts, locations, sites, sources, media, and surnames with deterministic compound keys.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_xref/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `fact_participant_xref.py` | `1.0.0+build.4` | Cross-reference bridge and index model linking evidentiary facts to participating individuals. |
| `individual_family_xref.py` | `1.0.0+build.5` | Cross-reference bridge and index model linking individuals to nuclear family units. |
| `individual_organization_xref.py` | `1.0.0+build.2` | Cross-reference bridge and index model linking institutional organizations to affiliated individuals. |
| `individual_source_xref.py` | `1.0.0+build.2` | Cross-reference bridge and index model linking archival sources to individuals. |
| `individual_surname_xref.py` | `1.0.0+build.4` | Cross-reference bridge and index model linking normalized surnames to individuals. |
| `location_xref.py` | `1.0.0+build.2` | Cross-reference bridge and index model linking civil jurisdictions to entities and sources. |
| `media_xref.py` | `1.0.0+build.4` | Cross-reference bridge and index model linking digital media assets to entities and sources. |
| `site_xref.py` | `1.0.0+build.2` | Cross-reference bridge and index model linking physical venues (Sites) to entities and sources. |
| `surname_xref.py` | `1.0.0+build.3` | Onomastic surname equivalence and orthographic variant expansion index model. |

## Public Exports & Consumption Contract
Exports: `FactParticipantXRef`, `IndividualFamilyXRef`, `IndividualOrganizationXRef`, `IndividualSourceXRef`, `IndividualSurnameXRef`, `LocationTargetID`, `LocationXRef`, `MediaTargetID`, `MediaXRef`, `SiteTargetID`, `SiteXRef`, `SurnameXRef`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 52fe2ed48953c2ba -->
