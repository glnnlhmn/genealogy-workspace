<!--Path: src/gda/core/constants/README.md-->
# Domain, Military & Census Constants (src/gda/core/constants)

## Architectural Role
Immutable bounds, code sets, and era year sets. Covers domain limits, military draft and service ranges, and census schedule years.

## Quality Gate & Verification Status
- **Quality Gate:** 100.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_core/test_constants/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `census.py` | `1.0.0+build.1` | Enumerated census schedule and tax assessment bounds and historical year sets. |
| `domain.py` | `1.0.0+build.1` | Domain bounds, year limits, coordinate ranges, and score invariants. |
| `military.py` | `1.0.0+build.1` | Military service, pension, and conscription scalar bounds and historical era year sets. |

## Public Exports & Consumption Contract
Exports: `CENSUS_SHEET_SIDES`, `CIVIL_WAR_DRAFT_YEARS`, `COLONIAL_MILITIA_MAX_YEAR`, `COLONIAL_MILITIA_MIN_YEAR`, `GENDER_CODES`, `MAX_BOUNTY_LAND_ACREAGE`, `MAX_CENSUS_LINE_NUMBER`, `MAX_CONFIDENCE_SCORE`, `MAX_ENLISTMENT_TERM_MONTHS`, `MAX_FOREIGN_SERVICE_MONTHS`, `MAX_HEIGHT_INCHES`, `MAX_HISTORICAL_YEAR`, `MAX_LATITUDE`, `MAX_LONGITUDE`, `MAX_MINOR_CHILDREN_COUNT`, `MAX_QUAY_SCORE`, `MAX_VIETNAM_LOTTERY_NUMBER`, `MAX_WEIGHT_LBS`, `MIN_AHNENTAFEL`, `MIN_CONFIDENCE_SCORE`, `MIN_ENLISTMENT_TERM_MONTHS`, `MIN_HEIGHT_INCHES`, `MIN_HISTORICAL_YEAR`, `MIN_LATITUDE`, `MIN_LONGITUDE`, `MIN_QUAY_SCORE`, `MIN_VIETNAM_LOTTERY_NUMBER`, `MIN_WEIGHT_LBS`, `MODERN_SSS_MIN_YEAR`, `TAX_ASSESSMENT_MIN_YEAR`, `US_AGRICULTURAL_SCHEDULE_YEARS`, `US_FEDERAL_CENSUS_1850_1870_YEARS`, `US_FEDERAL_CENSUS_1900_1910_YEARS`, `US_FEDERAL_CENSUS_TALLY_YEARS`, `US_FEDERAL_CENSUS_YEARS`, `US_MANUFACTURING_SCHEDULE_YEARS`, `US_MORTALITY_SCHEDULE_YEARS`, `US_SLAVE_SCHEDULE_YEARS`, `US_VETERANS_SCHEDULE_YEAR`, `WWII_DRAFT_YEARS`, `WWI_DRAFT_YEARS`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 1afcec6962d466dc -->
