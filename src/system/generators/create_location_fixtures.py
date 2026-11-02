"""Path: src/system/generators/create_location_fixtures.py

Automated generator for location intake golden and failure test fixtures.

Operational Role:
    Emits standardized JSON test fixtures adhering to 'location_intake.schema.json'
    into tests/fixtures/locations/golden/ and tests/fixtures/locations/failure/.
"""

from __future__ import annotations

import json
from pathlib import Path

__version__ = "1.0.0+build.1"

FIXTURES: dict[str, dict] = {
    # -------------------------------------------------------------------------
    # Golden Matrix Fixtures
    # -------------------------------------------------------------------------
    "tests/fixtures/locations/golden/combo_10_single_token_state_georgia.json": {
        "schema_version": "1.0.0",
        "record_type": "location_intake",
        "locations": [
            {
                "raw_text": "Georgia",
            }
        ],
        "_path": "tests/fixtures/locations/golden/combo_10_single_token_state_georgia.json",
    },
    "tests/fixtures/locations/golden/combo_11_single_token_sovereign_france.json": {
        "schema_version": "1.0.0",
        "record_type": "location_intake",
        "locations": [
            {
                "raw_text": "France",
            }
        ],
        "_path": "tests/fixtures/locations/golden/combo_11_single_token_sovereign_france.json",
    },
    "tests/fixtures/locations/golden/combo_12_single_token_explicit_county_suffix.json": {
        "schema_version": "1.0.0",
        "record_type": "location_intake",
        "locations": [
            {
                "raw_text": "Dauphin County",
            }
        ],
        "_path": "tests/fixtures/locations/golden/combo_12_single_token_explicit_county_suffix.json",
    },
    # -------------------------------------------------------------------------
    # Failure & Ambiguity Fixtures
    # -------------------------------------------------------------------------
    "tests/fixtures/locations/failure/edge_04_single_token_ambiguous_county.json": {
        "schema_version": "1.0.0",
        "record_type": "location_intake",
        "locations": [
            {
                "raw_text": "Franklin",
            }
        ],
        "_path": "tests/fixtures/locations/failure/edge_04_single_token_ambiguous_county.json",
    },
    "tests/fixtures/locations/failure/edge_05_single_token_unknown_garbage.json": {
        "schema_version": "1.0.0",
        "record_type": "location_intake",
        "locations": [
            {
                "raw_text": "Atlantis",
            }
        ],
        "_path": "tests/fixtures/locations/failure/edge_05_single_token_unknown_garbage.json",
    },
}


def main() -> None:
    """Generate all specified fixture files on disk."""
    created = 0
    for rel_path, data in FIXTURES.items():
        fpath = Path(rel_path)
        fpath.parent.mkdir(parents=True, exist_ok=True)
        with open(fpath, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)
            fp.write("\n")
        created += 1
        print(f"Emitted: {fpath}")

    print(f"Successfully generated {created} location fixtures.")


if __name__ == "__main__":
    main()
