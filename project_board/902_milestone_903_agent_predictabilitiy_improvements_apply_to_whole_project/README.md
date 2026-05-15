# Milestone 903 — Apply agent predictability improvements to committed code

## Depends on

- Tooling and gate contracts from: `project_board/902_milestone_902_agent_predictabilitiy_improvements/`.

## Overview

Roll out Milestone 902’s static analysis and governance checks across the repository’s committed sources so CI and local workflows enforce (or baseline) real violations on Python, GDScript, TypeScript/React, and cross-cutting duplication, without silently exempting new debt.

## Goals

- Bring committed code under the new toolchains with explicit baselines where legacy violations exist.
- Wire enforcement into canonical CI/hook entrypoints so the static analysis gate runs before diff-cover/review stages as described in the MVP.
- Replace blanket suppressions with scoped, owned suppressions tied to remediation tickets where feasible.

## Non-Goals

- Rebuilding the gate framework itself (owned by Milestone 902).
- Regenerating binary/procedural art assets unless a check explicitly requires formatting-only changes.

## Current Status

All work is **not started**. Tickets live under `00_backlog/`.

## Work Tracking

### 00_backlog

| Ticket file | One-line description |
| --- | --- |
| `00_backlog/01_python_committed_code_enforcement_and_baseline.md` | Make Python static analysis enforcement meaningful on committed pipeline/backend/tests with baselined legacy debt. |
| `00_backlog/02_gdscript_committed_code_format_lint_and_baseline.md` | Apply gdformat/gdlint to committed Godot scripts/scenes/tests with CI enforcement. |
| `00_backlog/03_frontend_committed_code_eslint_boundaries_and_baseline.md` | Apply eslint+typescript-eslint+sonarjs+boundaries+hooks rules to committed frontend sources with CI enforcement. |
| `00_backlog/04_cross_repo_duplication_jscpd_baseline.md` | Establish jscpd thresholds and baseline for duplication on committed code paths. |
| `00_backlog/05_ci_and_hooks_ordering_static_gate_before_review_stages.md` | Integrate static analysis gate ordering into `ci/scripts`, lefthook, and Taskfile workflows. |
| `00_backlog/06_suppression_grandfathering_and_ownership_cleanup.md` | Migrate blanket suppressions to scoped suppressions with owners/expiry aligned to baseline policy. |

### 01_active

None.

### 02_complete

None.
