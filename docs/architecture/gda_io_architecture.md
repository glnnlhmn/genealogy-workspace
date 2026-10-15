<!--
Name: gda_io_architecture.md
Path: docs/architecture/gda_io_architecture.md
-->

# Architecture & Design Specification: `gda.io` Foundation

## 1. Overview & Architectural Role
`gda.io` is the dedicated filesystem, atomic persistence, and serialization engine for the Genealogy Digital Archive. It isolates all physical disk mutations, temporary staging, format normalization, and the Safe Backup Protocol from domain models.

### Core Architectural Invariants
* **Zero Folder Assumptions:** No hardcoded paths (`data/`, `logs/`, `backups/`). All directories are passed as explicit arguments or resolved relative to a target file's parent directory. Parent directories are auto-provisioned (`parents=True, exist_ok=True`).
* **Same-Volume Atomic Staging:** To guarantee that `os.replace` remains atomic across drive volumes (e.g., `G:` to `C:`), temporary files (`.[filename].[uuid].tmp`) are always staged in the destination directory of the target file.
* **Windows & Drive Protections:** Transient file sharing collisions (Windows Error 32) and Google Drive locks are mitigated via exponential backoff retries. Buffers are flushed and synchronized with `os.fsync()` before file replacement.
* **Separation of Formats:** Dedicated, single-responsibility modules for JSON and UTF-8 text (establishing the blueprint for upcoming CSV and TSV engines).
* **Framework Integration:** Classes inherit `IntrospectableMixin` and raise typed exceptions rooted in `GenealogyDeskError`.

---

## 2. Module Inventory & Contracts

### 2.1 `gda.io.errors`
* `GDAIOError(GenealogyDeskError)`: Root base exception (`ERR_IO_FAILURE`).
* `AtomicWriteError(GDAIOError)`: Staging, syncing, or file-swap failures (`ERR_IO_ATOMIC_WRITE`).
* `BackupError(GDAIOError)`: Safe Backup creation or restore failures (`ERR_IO_BACKUP`).
* `FileReadError(GDAIOError)`: Missing files or read/decode failures (`ERR_IO_READ`).
* `SerializationError(GDAIOError)`: Malformed structured syntax (`ERR_IO_SERIALIZATION`).

### 2.2 `gda.io.atomic`
* `atomic_write(file_path, mode="w", encoding="utf-8", max_retries=3, backoff_factor=0.05)`:
  * Context manager staging writes via `.[filename].[uuid].tmp` in the target directory.
  * Flushes and syncs (`flush()`, `os.fsync()`) before committing via `os.replace`.
  * Catches `PermissionError` / `OSError` with bounded exponential backoff retries.
  * Cleans up orphaned temporary files on unhandled exceptions.

### 2.3 `gda.io.backup` (`GDABackupManager`)
* Inherits `IntrospectableMixin`.
* `create_backup(target_path, backup_dir=None) -> Path`:
  * Generates an atomic snapshot formatted as `[filename].[YYYYMMDD_HHMMSS].bk`.
  * Protects against sub-second collisions using microsecond timestamps or monotonic collision counters.
  * If `backup_dir` is omitted, defaults to a `backups/` sibling folder in the target file's parent directory.
* `list_backups(target_path, backup_dir=None) -> list[Path]`:
  * Discovers all matching snapshots sorted chronologically (newest first).
* `restore_backup(backup_path, target_path) -> Path`:
  * Restores a snapshot file to the target location atomically.

### 2.4 `gda.io.json` (`GDAJsonIO`)
* Inherits `IntrospectableMixin`.
* `read(file_path) -> Any`:
  * Reads and parses UTF-8 JSON into native structures, mapping errors to `FileReadError` or `SerializationError`.
* `write(file_path, data, indent=2, sort_keys=True, create_backup=False, backup_dir=None) -> Path`:
  * Deterministic serialization: UTF-8, 2-space indentation, sorted keys, unescaped Unicode (`ensure_ascii=False`), trailing newline.
  * Triggers Safe Backup prior to writing when `create_backup=True`.
  * Commits via `atomic_write`.

### 2.5 `gda.io.text` (`GDATextIO`)
* Inherits `IntrospectableMixin`.
* `read(file_path, encoding="utf-8") -> str`:
  * Reads text/markdown files with verified UTF-8 normalization.
* `write(file_path, content, encoding="utf-8", create_backup=False, backup_dir=None) -> Path`:
  * Writes plain text or markdown atomically with optional Safe Backup creation.

---

## 3. Verification & Quality Plan
* **Test Placement:** `tests/test_gda/test_io/`
* **Coverage Guarantee:** 100% statement and branch test coverage.
* **Linter Standards:** Ruff-compliant with strict module-level import ordering (`E402`) and no `# Version:` comments in lines 1–2.