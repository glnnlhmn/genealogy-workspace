"""Path: tests/test_gda/test_db/test_exceptions.py

Behavioral contract and verification test suite for database exception hierarchy.

Validates default messages, error code taxonomies, structured detail dictionaries,
inheritance relationships, and JSON-compatible serialization contracts.
"""

from __future__ import annotations

import pytest

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

__version__ = "1.0.0+build.1"


# ==============================================================================
# GROUP 1: INHERITANCE HIERARCHY & ROOT CONTRACTS
# Note: Verify all specialized database errors derive from GenealogyDeskError
# ==============================================================================


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
# Note: Verify default zero-argument instantiation across all exception classes
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
    assert err.timestamp.endswith("Z")


# ==============================================================================
# GROUP 3: CUSTOM PAYLOADS & CONTEXTUAL DETAILS
# Note: Verify custom messages, diagnostic details, and caller error code overrides
# ==============================================================================


@pytest.mark.regression
def test_database_error_custom_parameters_binding() -> None:
    """Verify callers can pass custom diagnostic messages, error codes, and details."""
    custom_msg = "Corrupted header on database partition"
    custom_code = "ERR_DB_CORRUPTED_PARTITION"
    custom_details = {"partition": "main", "sector": 4096}

    err = DatabaseError(
        message=custom_msg, error_code=custom_code, details=custom_details
    )

    assert err.message == custom_msg
    assert err.error_code == custom_code
    assert err.details == custom_details
    assert str(err) == custom_msg


@pytest.mark.regression
def test_constraint_violation_error_contextual_details() -> None:
    """Verify ConstraintViolationError accepts structured relational violation details."""
    details = {
        "table": "facts",
        "constraint": "fk_facts_individual_id",
        "rejected_id": "IND-9999",
    }
    err = ConstraintViolationError(
        message="Foreign key constraint failure on facts table.",
        details=details,
    )

    assert err.error_code == "ERR_DB_CONSTRAINT"
    assert err.details["table"] == "facts"
    assert err.details["rejected_id"] == "IND-9999"


# ==============================================================================
# GROUP 4: SERIALIZATION & AUDIT CONTRACT (to_dict)
# Note: Verify serialized dictionary adheres strictly to system contract
# ==============================================================================


@pytest.mark.unit
def test_database_exception_serialization_to_dict() -> None:
    """Verify to_dict returns compliant dictionary payload matching core error schema."""
    details = {"table": "individuals", "primary_key": "IND-0001"}
    err = RecordNotFoundError(
        message="Individual IND-0001 does not exist.",
        details=details,
    )

    payload = err.to_dict()

    assert payload["error_code"] == "ERR_DB_RECORD_NOT_FOUND"
    assert payload["message"] == "Individual IND-0001 does not exist."
    assert payload["details"] == details
    assert isinstance(payload["timestamp"], str)
    assert payload["timestamp"].endswith("Z")
