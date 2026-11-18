"""Path: tests/test_gda/test_repository/test_query.py

Unit tests for QueryBuilder, SQL identifier validation, and UPSERT/INSERT SQL helpers.
"""

from __future__ import annotations

import pytest

from gda.repository.errors import QueryValidationError
from gda.repository.query import (
    FilterOp,
    QueryBuilder,
    SortOrder,
    build_insert_sql,
    build_upsert_sql,
    validate_sql_identifier,
)


def test_validate_sql_identifier_valid_and_invalid() -> None:
    """Verify validate_sql_identifier accepts safe names and rejects unsafe input."""
    assert validate_sql_identifier("locations") == "locations"
    assert validate_sql_identifier("_private_col_1") == "_private_col_1"

    for bad in ("", "123col", "users; DROP TABLE", "table.col", "col-name", None):
        with pytest.raises(QueryValidationError):
            validate_sql_identifier(bad)  # type: ignore[arg-type]


def test_query_builder_init_and_properties() -> None:
    """Verify QueryBuilder properties and empty column list validation."""
    qb_all = QueryBuilder("sites")
    assert qb_all.table_name == "sites"
    assert qb_all.columns == ()

    qb_cols = QueryBuilder("sites", columns=["id", "canonical_urn"])
    assert qb_cols.columns == ("id", "canonical_urn")

    with pytest.raises(QueryValidationError, match="cannot be empty"):
        QueryBuilder("sites", columns=[])


def test_query_builder_select_where_order_limit_offset() -> None:
    """Verify full SELECT compilation with filters, IN, NULL, ORDER BY, LIMIT, and OFFSET."""
    qb = (
        QueryBuilder("individuals", columns=("id", "surname"))
        .where("birth_year", 1850, FilterOp.GE)
        .where("surname", "Lehman", "=")
        .where("category", ["A", "B"], FilterOp.IN)
        .where_null("deprecated_at", is_null=True)
        .where_null("canonical_urn", is_null=False)
        .order_by("birth_year", SortOrder.DESC)
        .order_by("id", "asc")
        .limit(25)
        .offset(50)
    )
    sql, params = qb.build_select()
    assert sql == (
        "SELECT id, surname FROM individuals "
        "WHERE birth_year >= ? AND surname = ? AND category IN (?, ?) "
        "AND deprecated_at IS NULL AND canonical_urn IS NOT NULL "
        "ORDER BY birth_year DESC, id ASC LIMIT ? OFFSET ?;"
    )
    assert params == (1850, "Lehman", "A", "B", 25, 50)


def test_query_builder_unfiltered_select_and_count() -> None:
    """Verify unfiltered SELECT * and SELECT COUNT(*) compilation."""
    qb = QueryBuilder("organizations")
    select_sql, select_params = qb.build_select()
    assert select_sql == "SELECT * FROM organizations;"
    assert select_params == ()

    count_sql, count_params = qb.build_count()
    assert count_sql == "SELECT COUNT(*) FROM organizations;"
    assert count_params == ()


def test_query_builder_delete_safety_guards() -> None:
    """Verify build_delete blocks unconditional deletes unless explicitly allowed."""
    qb_empty = QueryBuilder("facts")
    with pytest.raises(QueryValidationError, match="unconditional DELETE"):
        qb_empty.build_delete()

    sql_all, params_all = qb_empty.build_delete(allow_unconditional=True)
    assert sql_all == "DELETE FROM facts;"
    assert params_all == ()

    qb_filtered = QueryBuilder("facts").where("id", "fac_123")
    sql_del, params_del = qb_filtered.build_delete()
    assert sql_del == "DELETE FROM facts WHERE id = ?;"
    assert params_del == ("fac_123",)


def test_query_builder_validation_errors() -> None:
    """Verify QueryBuilder raises QueryValidationError on invalid operators and bounds."""
    qb = QueryBuilder("locations")

    with pytest.raises(QueryValidationError, match="Unsupported filter operator"):
        qb.where("id", "loc_1", op="BETWEEN")

    with pytest.raises(QueryValidationError, match="requires a non-string sequence"):
        qb.where("id", "not-a-list", op=FilterOp.IN)

    with pytest.raises(QueryValidationError, match="cannot be empty"):
        qb.where_in("id", [])

    with pytest.raises(QueryValidationError, match="Invalid sort direction"):
        qb.order_by("id", "SIDEWAYS")

    with pytest.raises(QueryValidationError, match="LIMIT must be a non-negative integer"):
        qb.limit(-1)

    with pytest.raises(QueryValidationError, match="LIMIT must be a non-negative integer"):
        qb.limit(True)

    with pytest.raises(QueryValidationError, match="OFFSET must be a non-negative integer"):
        qb.offset(-5)

    with pytest.raises(QueryValidationError, match="OFFSET must be a non-negative integer"):
        qb.offset(False)

    qb_offset_only = QueryBuilder("locations").offset(10)
    with pytest.raises(QueryValidationError, match="OFFSET cannot be specified without"):
        qb_offset_only.build_select()


def test_build_insert_and_upsert_sql() -> None:
    """Verify build_insert_sql and build_upsert_sql handle multi-column and PK-only tables."""
    insert_sql = build_insert_sql("sites", ["id", "name"])
    assert insert_sql == "INSERT INTO sites (id, name) VALUES (:id, :name);"

    with pytest.raises(QueryValidationError, match="empty column list"):
        build_insert_sql("sites", [])

    upsert_sql = build_upsert_sql("sites", ["id", "name", "urn"], primary_key="id")
    assert upsert_sql == (
        "INSERT INTO sites (id, name, urn) VALUES (:id, :name, :urn) "
        "ON CONFLICT(id) DO UPDATE SET name = excluded.name, urn = excluded.urn;"
    )

    pk_only_sql = build_upsert_sql("tags", ["id"], primary_key="id")
    assert pk_only_sql == "INSERT INTO tags (id) VALUES (:id) ON CONFLICT(id) DO NOTHING;"

    with pytest.raises(QueryValidationError, match="empty column list"):
        build_upsert_sql("sites", [])

    with pytest.raises(QueryValidationError, match="Primary key 'id' must be present"):
        build_upsert_sql("sites", ["name", "urn"], primary_key="id")
