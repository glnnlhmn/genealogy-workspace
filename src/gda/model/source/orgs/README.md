<!--Path: src/gda/model/source/orgs/README.md-->
# Organizational Membership & Roster Source Records (src/gda/model/source/orgs)

## Architectural Role
Documentary membership certificates, lodge initiation/demit records, and multi-entry institutional membership rosters.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_model/test_source/test_orgs/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `membership.py` | `1.0.0+build.2` | Evidentiary record models for individual organization memberships and affiliations. |
| `roster.py` | `1.0.0+build.3` | Tabulated organization roster, lodge directory, and society roll domain models. |

## Public Exports & Consumption Contract
Exports: `OrganizationMembershipRecord`, `OrganizationRosterEntry`, `OrganizationRosterRecord`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 301340c22ac57f21 -->
