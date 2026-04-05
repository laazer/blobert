# TICKET: split_animated_adhesion_bug

Title: Move `AnimatedAdhesionBug` to its own Python module (asset generation)

## Description

`asset_generation/python/src/enemies/animated_enemies.py` holds six concrete animated enemy classes plus the builder. Move `AnimatedAdhesionBug` to a dedicated module (e.g. `src/enemies/animated/adhesion_bug.py` or `animated_adhesion_bug.py`) extending `BaseEnemy`, re-export or register from a small registry so `AnimatedEnemyBuilder.create_enemy("adhesion_bug", ...)` behavior is unchanged.

## Acceptance Criteria

- `AnimatedAdhesionBug` lives in its own file; no behavioral change to mesh/armature/attack profile for `adhesion_bug`.
- Imports resolve; existing entry points that build animated enemies still work.
- Python tests or documented smoke command for that enemy type still passes if present.

## Dependencies

- None (can land before or in parallel with other split tickets; coordinate on registry file to avoid merge pain)

## Specification

**Full spec:** [`project_board/specs/split_animated_adhesion_bug_spec.md`](../../specs/split_animated_adhesion_bug_spec.md)

## Execution Plan

| # | Task | Agent | Success criteria |
|---|------|-------|------------------|
| 1 | Module boundary + import graph | Planner | `animated_adhesion_bug.py` only; `animated_enemies` imports + registry |
| 2 | Spec SAAB-1..3 | Spec | Linked spec file |
| 3 | Tests `__module__` + canonical registry | Test Designer / Breaker | New tests pass |
| 4 | Implement split + docs | Implementation Generalist | `uv run pytest tests/ -q` green |
| 5 | AC gate + commit | AC Gatekeeper | Stage COMPLETE |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passed (`cd asset_generation/python && uv run pytest tests/ -q` — 360 passed, 209 subtests, 2026-04-05)
- Static QA: Not separately run (Ruff optional in env)
- Integration: Full Python suite as above

## Blocking Issues

- None

## Escalation Notes

- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Status
Proceed

## Reason

Ticket complete: `AnimatedAdhesionBug` in `src/enemies/animated_adhesion_bug.py`; `animated_enemies` imports and registers `adhesion_bug`. Log: `project_board/checkpoints/split_animated_adhesion_bug/run-2026-04-05-autopilot.md`.
