<!--Path: src/system/hooks/README.md-->
# Package Documentation (src/system/hooks)

## Architectural Role
Architectural subsystem package.

## Quality Gate & Verification Status
- **Quality Gate:** >= 95.0% Statement & Branch Coverage
- **Verification Suite:** `tests/test_hooks/`
- **Operational Invariant:** In-memory verification, hermetic test isolation, zero warnings.

## Module Inventory & Descriptions
| Module | Version | Canonical Description |
| :--- | :--- | :--- |
| `pre_commit.py` | `1.1.0+build.r1` | Staged-File & Targeted Component Pre-Commit Hook Executor. |
| `pre_push.py` | `1.0.0+build.8` | Git pre-push hook orchestrator enforcing branch protection and test gates. |

## Public Exports & Consumption Contract
Direct submodule imports supported.

---
Generated dynamically by `gen_desk_tools.readme_gen` (`gdrm`).
<!-- gdrm-hash: 250946e81fb9bb70 -->
