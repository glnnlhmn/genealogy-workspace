"""Path: src/gda/__init__.py

Genealogy Digital Archive (GDA) core domain framework package.

Operational Role:
    Top-level package facade uniting the audited GDA architectural pillars:
    - core: Foundational configuration, controlled enumerations, errors,
      dates, hashes, logging, scalar/regex constants, and introspection.
    - db: SQLite analytical database layer, session/transaction management,
      modular DDL migrations, and bidirectional entity row mappers.
    - entity: In-memory domain entity collection managers, validators,
      graveyard lifecycle services, and persistence gateways.
    - io: Atomic file writing, UTF-8 text/JSON persistence, and Safe Backups.
    - model: Five-pillar domain model suite (atom, base, entity, source, xref).
    - util: SmartID/UUIDv4 minting, text sanitization, and phonetic algorithms.
"""

from __future__ import annotations

from gda import (
    core,
    db,
    entity,
    io,
    model,
    util,
)

__version__ = "1.0.0+build.3"

__all__ = [
    "core",
    "db",
    "entity",
    "io",
    "model",
    "util",
]
