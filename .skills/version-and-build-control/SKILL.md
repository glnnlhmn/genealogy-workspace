<!--Path: .skills/version-and-build-control/SKILL.md-->
---
name: version-and-build-control
description: Enforces X.X.X+build.# version numbering, build-counter bump rules on file regeneration, explicit version change resets, and Git release alignment across code and versioned files. Use when creating, editing, or regenerating versioned files, reviewing version bumps, or preparing Git commits and releases.
---

# Version and Build Control

Rules for `X.X.X+build.#` version strings, build-counter increments, and Git release boundaries.

## When to Use

- Creating or regenerating any code file or file carrying a version number.
- Fixing a defect or stray character in a file and regenerating it.
- Checking whether an unchanged file should keep its current build number.
- Preparing commits or Git release tags (`vX.Y.Z`) involving versioned files.

## Version Format & Rules

1. **Format:** Use `X.X.X+build.#` (for example, `1.0.0+build.1`). Omit any leading `v` inside code `__version__` strings.
2. **Default Build-Only Increments:** Only increment the `+build.#` counter unless explicitly instructed to change the `X.X.X` version number.
3. **Bump on Every Change:** Increment `+build.#` every time a file is regenerated with a change, including minor fixes such as removing a stray character.
4. **No Bump When Unchanged:** Do not increment `+build.#` if a file is not changed (ignoring line-ending or file-mode noise).
5. **Initial Value & Reset:** Start new versioned files at `+build.1`, and reset `+build.#` to `1` whenever `X.X.X` is explicitly changed.
6. **Scope Across Versioned Files:** Apply `X.X.X+build.#` to all version control numbers in files where all code files carry version numbers, while leaving external data/schema contract fields (such as `SchemaVersion` in profile data) untouched unless explicitly instructed.

## Git & Release Alignment

- **Independent Baselines:** Keep file `X.X.X+build.#` versions independent from Git release tags (`vX.Y.Z`) unless explicitly asked to change a file's version number.
- **Targeted Bumps Only:** Bump `+build.#` only on files that actually change during feature work, maintenance, or release commits; never mass-bump untouched files.

## Gotchas

- Never bump `+build.#` on a file that had zero content changes during a batch run or edit pass.
- Do not confuse external data/schema contract versions with code/file build counters unless explicitly told to update them.
