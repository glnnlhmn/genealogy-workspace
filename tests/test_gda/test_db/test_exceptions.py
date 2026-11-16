"""Path: tests/test_gda/test_db/test_exceptions.py

Behavioral contract and verification test suite for database exception hierarchy.

Validates default messages, error code taxonomies, structured detail dictionaries,
exit codes, inheritance relationships, __all__ export surface, and JSON-compatible
serialization contracts.
"""

from __future__ import annotations

import pytest

import gda.db.exceptions as db_exc_mod
from gda.core.errors import GenealogyDeskError
from gda.db.exceptions import (
    ConnectionTimeoutError,
    ConstraintViolationError,
    DatabaseConnectionError,
    DatabaseError,
    DatabaseOperationalError,
    DirtyStateError,
    EntityMappingError,
    RecordNotFoundError,
    SchemaMigrationError,
    TransactionError,
)

__version__ = "1.0.0+build.2"


# ==============================================================================
# GROUP 1: INHERITANCE HIERARCHY & ROOT CONTRACTS
# ==============================================================================


@pytest.mark.unit
def test_database_exceptions_dunder_all_contract() -> None:
    """Verify gda.db.exceptions.__all__ is sorted and exports all 10 exception classes."""
    expected = [
        "ConnectionTimeoutError",
        "ConstraintViolationError",
        "DatabaseConnectionError",
        "DatabaseError",
        "DatabaseOperationalError",
        "DirtyStateError",
        "EntityMappingError",
        "RecordNotFoundError",
        "SchemaMigrationError",
        "TransactionError",
    ]
    assert db_exc_mod.__all__ == expected
    assert db_exc_mod.__all__ == sorted(db_exc_mod.__all__)


@pytest.mark.unit
def test_database_error_inherits_from_genealogy_desk_error() -> None:
    """Verify DatabaseError inherits directly from the canonical GenealogyDeskError."""
    err = DatabaseError()
    assert isinstance(err, GenealogyDeskError)
    assert isinstance(err, Exception)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exception_cls", "parent_cls"),
    [
        (DatabaseConnectionError, DatabaseError),
        (ConnectionTimeoutError, DatabaseConnectionError),
        (TransactionError, DatabaseError),
        (ConstraintViolationError, DatabaseError),
        (RecordNotFoundError, DatabaseError),
        (SchemaMigrationError, DatabaseError),
        (DatabaseOperationalError, DatabaseError),
        (EntityMappingError, DatabaseError),
        (DirtyStateError, DatabaseError),
    ],
)
def test_database_exceptions_subclass_relationships(
    exception_cls: type[DatabaseError], parent_cls: type[DatabaseError]
) -> None:
    """Verify each database exception subclasses its designated architectural parent."""
    err = exception_cls()
    assert isinstance(err, parent_cls)
    assert isinstance(err, DatabaseError)
    assert isinstance(err, GenealogyDeskError)


# ==============================================================================
# GROUP 2: DEFAULT MESSAGES & CANONICAL ERROR CODES
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    ("exception_cls", "expected_code", "expected_message_fragment"),
    [
        (DatabaseError, "ERR_DATABASE", "unexpected database error"),
        (DatabaseConnectionError, "ERR_DB_CONNECTION", "Failed to establish"),
        (ConnectionTimeoutError, "ERR_DB_TIMEOUT", "timed out under lock"),
        (TransactionError, "ERR_DB_TRANSACTION", "transaction failed"),
        (ConstraintViolationError, "ERR_DB_CONSTRAINT", "constraint violation"),
        (RecordNotFoundError, "ERR_DB_RECORD_NOT_FOUND", "record was not found"),
        (SchemaMigrationError, "ERR_DB_MIGRATION", "migration failed"),
        (DatabaseOperationalError, "ERR_DB_OPERATIONAL", "driver operational error"),
        (EntityMappingError, "ERR_DB_ENTITY_MAPPING", "map database row"),
        (DirtyStateError, "ERR_DB_DIRTY_STATE", "dirty state conflict"),
    ],
)
def test_database_exceptions_default_instantiation(
    exception_cls: type[DatabaseError],
    expected_code: str,
    expected_message_fragment: str,
) -> None:
    """Verify zero-arg constructors supply canonical error codes and informative messages."""
    err = exception_cls()
    assert err.error_code == expected_code
    assert expected_message_fragment in err.message
    assert str(err) == err.message
    assert err.details == {}
    assert err.exit_code == 1
    assert err.timestamp.endswith("Z")


# ==============================================================================
# GROUP 3: CUSTOM PAYLOADS & CONTEXTUAL DETAILS
# ==============================================================================


@pytest.mark.regression
def test_database_error_custom_parameters_binding() -> None:
    """Verify callers can pass custom diagnostic messages, error codes, details, and exit_code."""
    custom_msg = "Corrupted header on database partition"
    custom_code = "ERR_DB_CORRUPTED_PARTITION"
    custom_details = {"partition": "main", "sector": 4096}

    err = DatabaseError(
        message=custom_msg,
        error_code=custom_code,
        details=custom_details,
        exit_code=2,
    )

    assert err.message == custom_msg
    assert err.error_code == custom_code
    assert err.details == custom_details
    assert err.exit_code == 2
    assert str(err) == custom_msg


@pytest.mark.regression
def test_constraint_violation_error_contextual_details() -> None:
    """Verify ConstraintViolationError accepts table and column violation metadata."""
    details = {"table": "locations", "column": "canonical_urn", "value": "urn:gda:loc:us"}
    err = ConstraintViolationError(
        message="Duplicate canonical_urn encountered.",
        details=details,
    )

    assert err.error_code == "ERR_DB_CONSTRAINT"
    assert err.details["table"] == "locations"
    assert err.details["column"] == "canonical_urn"


# ==============================================================================
# GROUP 4: SERIALIZATION & LOGGING PAYLOAD CONTRACTS
# ==============================================================================


@pytest.mark.unit
@pytest.mark.parametrize(
    "exception_cls",
    [
        DatabaseError,
        DatabaseConnectionError,
        ConnectionTimeoutError,
        TransactionError,
        ConstraintViolationError,
        RecordNotFoundError,
        SchemaMigrationError,
        DatabaseOperationalError,
        EntityMappingError,
        DirtyStateError,
    ],
)
def test_database_exceptions_to_dict_contract(
    exception_cls: type[DatabaseError],
) -> None:
    """Verify to_dict() returns a structured dictionary suitable for JSON logging."""
    err = exception_cls(details={"attempt": 1})
    payload = err.to_dict()

    assert isinstance(payload, dict)
    assert set(payload.keys()) == {
        "error_code",
        "message",
        "details",
        "timestamp",
        "exit_code",
    }
    assert payload["error_code"] == err.error_code
    assert payload["message"] == err.message
    assert payload["details"] == {"attempt": 1}
    assert payload["timestamp"] == err.timestamp
    assert payload["exit_code"] == 1
