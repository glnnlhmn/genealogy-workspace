# I/O, Safe Backup & Persistence Infrastructure (src/gda/io)

## Architectural Role
Governs physical filesystem interactions, line-ending preserving UTF-8 file access, atomic temporary staging, and automated pre-execution Safe Backups.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gda/test_io/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `atomic.py` | `0.1.0+build.r6` | Same-directory atomic file staging and replacement engine. |
| `backup.py` | `0.1.0+build.r1` | Safe Backup Protocol and snapshot lifecycle manager. |
| `errors.py` | `0.1.0+build.r5` | Canonical I/O error hierarchy and specialized persistence exceptions. |
| `json.py` | `0.1.0+build.r1` | Deterministic JSON serialization and atomic persistence engine. |
| `text.py` | `0.1.0+build.r1` | Normalized UTF-8 text and markdown atomic persistence engine. |

## Public Exports & Consumption Contract
Exports: `AtomicWriteError`, `AtomicWriter`, `BackupError`, `DirectoryCreationError`, `FileLockError`, `FileReadError`, `GDAIOError`, `GDAJsonIO`, `GDATextIO`, `GDABackupManager`, `SerializationError`, `atomic_write`, `atomic_write_bytes`, `atomic_write_stream`, `atomic_write_text`.

---
Generated dynamically by `src/system/generate_readmes.py`.
