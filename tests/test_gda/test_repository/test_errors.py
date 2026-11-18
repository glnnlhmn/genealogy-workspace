"""Path: tests/test_gda/test_repository/test_errors.py

Unit tests for GDA repository domain exceptions.
"""

from __future__ import annotations

from gda.core.errors import GenealogyDeskError
from gda.repository.errors import (
    DuplicateRecordError,
    QueryValidationError,
    RecordNotFoundError,
    RepositoryError,
)


def test_repository_error_hierarchy() -> None:
    """Verify RepositoryError and subclasses inherit from GDAError."""
    base_err = RepositoryError("Base repo failure", details={"op": "select"})
    assert isinstance(base_err, GenealogyDeskError)
    assert base_err.message == "Base repo failure"
    assert base_err.details == {"op": "select"}

    q_err = QueryValidationError("Unsafe column", details={"col": "bad;drop"})
    assert isinstance(q_err, RepositoryError)
    assert q_err.details == {"col": "bad;drop"}


def test_record_not_found_error_defaults_and_custom_details() -> None:
    """Verify RecordNotFoundError populates table, field, and identifier metadata."""
    err_default = RecordNotFoundError("vital_births", "bir_001")
    assert err_default.table_name == "vital_births"
    assert err_default.field == "id"
    assert err_default.identifier == "bir_001"
    assert "vital_births" in err_default.message
    assert "id='bir_001'" in err_default.message
    assert err_default.details == {
        "table_name": "vital_births",
        "field": "id",
        "identifier": "bir_001",
    }

    err_custom = RecordNotFoundError(
        "vital_births",
        "urn:gda:birth:001",
        field="canonical_urn",
        details={"attempt": 2},
    )
    assert err_custom.field == "canonical_urn"
    assert err_custom.details["attempt"] == 2
    assert err_custom.details["field"] == "canonical_urn"


def test_duplicate_record_error_metadata() -> None:
    """Verify DuplicateRecordError captures table_name, identifier, and extra details."""
    err_basic = DuplicateRecordError("land_deeds", "deed_100")
    assert err_basic.table_name == "land_deeds"
    assert err_basic.identifier == "deed_100"
    assert "land_deeds" in err_basic.message
    assert err_basic.details == {
        "table_name": "land_deeds",
        "identifier": "deed_100",
    }

    err_extra = DuplicateRecordError(
        "land_deeds",
        "deed_100",
        details={"constraint": "PRIMARY KEY"},
    )
    assert err_extra.details["constraint"] == "PRIMARY KEY"
