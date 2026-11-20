<!--Path: src/gen_desk_tools/backup_mgr/README.md-->
# GenDesk Backup Manager (gdb)

## Architectural Role
Safe Backup snapshot creation, four-section backup status audits, retention pruning, and single-file or batch restoration from archive backups or Git HEAD.

## Quality Gate & Verification Status
- **Quality Gate:** 100.00% Statement & Branch Coverage
- **Verification Suite:** `tests/test_gen_desk_tools/test_backup_mgr/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `auditor.py` | `1.0.0+build.2` | Four-section workspace archive status and audit engine for GenDesk Backup Manager (gdb). |
| `cli.py` | `1.0.0+build.3` | Command-line interface entrypoint for GenDesk Backup Manager (gdb). |
| `engine.py` | `1.0.0+build.2` | Safe Backup creation engine and automated code-domain scanner for GenDesk Backup Manager (gdb). |
| `pruner.py` | `1.0.0+build.2` | Safe Backup retention evaluator and snapshot pruning engine for GenDesk Backup Manager (gdb). |
| `restorer.py` | `1.0.0+build.2` | Single-file and batch restoration engine for GenDesk Backup Manager (gdb). |

## Public Exports & Consumption Contract
Exports: `AuditRecord`, `AuditStatus`, `BackupCandidate`, `PruneCandidate`, `audit_workspace`, `backup_folder`, `build_parser`, `create_single_backup`, `execute_prune`, `find_latest_archive_backup`, `find_prune_candidates`, `format_full_audit_report`, `format_section_table`, `main`, `parse_backup_filename`, `parse_restore_list`, `resolve_original_path`, `restore_batch_from_list`, `restore_file_entry`, `restore_from_git`, `run`, `run_auto_backup`.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 9f13208b2d231b5c -->
