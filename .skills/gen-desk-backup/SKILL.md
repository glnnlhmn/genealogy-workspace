<!--Path: .skills/gen-desk-backup/SKILL.md-->
---
name: gen-desk-backup
description: Manage Safe Backups, 4-section audit reports, pruning, and file restoration across GDA code domains using gdb (src/gen_desk_tools/backup_mgr/). Use when the user needs to back up files, audit backup coverage, prune old snapshot versions, or restore code files from backups.
---

# GenDesk Backup Manager (`gdb`)

Operational guidance and command reference for executing Safe Backups, 4-section audits, retention pruning, and single/batch file restoration using `gdb` (`src/gen_desk_tools/backup_mgr/`).

## Tool Invocation Syntax

```bash
gdb [options] [target]
```

## Core Operations

### 1. Single File or Directory Safe Backup

```bash
# Back up a specific file
gdb src/gda/util/hashes.py

# Back up a directory recursively
gdb src/gda/core/

# Back up a directory non-recursively (immediate files only)
gdb --no-recursive src/gda/core/
```

### 2. Automated Full Code Domain Backup (`-a` / `--auto`)

```bash
# Dry-run inspection
gdb -a -n

# Execute automated backup
gdb -a
```

### 3. Four-Section Audit Report (`-s` / `-A`)

Compare live repository files against archive snapshots (`BACKUP NEWER`, `NO BACKUP`, `BACK OKAY`, `NO ORIGIN`):

```bash
gdb -s
```

### 4. Restore File(s) from Archive (`-r` / `-R`)

```bash
# Dry run first to verify snapshot target
gdb -r src/gda/util/hashes.py -n

# Execute restore
gdb -r src/gda/util/hashes.py

# Batch restore from list
gdb -R restore_targets.txt
```

### 5. Snapshot Retention Pruning (`-p` / `--prune`)

```bash
# Dry run prune to preview deletions
gdb -p -n

# Execute pruning
gdb -p
```

## Restoration Gotchas & Safeguards

- Always specify targets using relative paths anchored to the workspace root (`src/gda/...`, `tests/...`).
- Run with `-n` (`--dry-run`) first when performing restorations or pruning if unsure of the newest snapshot timestamp.
- Backups are stored with the naming pattern `[filename].[YYYYMMDD_HHMMSS].bk` in their routed archive bucket (`archive/backups_gda/`, `archive/backups_gen_desk_tools/`, etc.).
- When restoring files that were edited or corrupted, verify dependent tests pass immediately following restoration:
  ```bash
  pytest tests/test_gda/ -v
  ```
