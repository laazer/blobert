# TICKET: split_animated_tar_slug

Title: Move `AnimatedTarSlug` to its own Python module (asset generation)

## Description

Split `AnimatedTarSlug` out of `asset_generation/python/src/enemies/animated_enemies.py` into a dedicated module; keep `BaseEnemy` subclass contract and registration for `AnimatedEnemyBuilder`.

## Acceptance Criteria

- `AnimatedTarSlug` in its own file; `tar_slug` generation behavior unchanged.
- Builder/registry resolves `tar_slug` correctly.
- Any smoke or test path covering `tar_slug` still passes.

## Dependencies

- None (coordinate registry merges with sibling split tickets)

## Specification

**Full spec:** [`project_board/specs/split_animated_tar_slug_spec.md`](../../specs/split_animated_tar_slug_spec.md)

## Execution Plan

| # | Task | Agent | Success criteria |
|---|------|-------|------------------|
| 1 | Plan module boundary and import graph | Planner | `animated_tar_slug.py` only; `animated_enemies` imports + registry |
| 2 | Spec STS-1..3 | Spec | Linked spec file |
| 3 | Tests for `__module__` + registry canonical class | Test Designer / Breaker | New tests pass |
| 4 | Implement split + doc tree | Implementation Generalist | `uv run pytest tests/ -q` green |
| 5 | AC gate + commit | AC Gatekeeper / Human | Stage COMPLETE |

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
7

## Last Updated By
Acceptance Criteria Gatekeeper Agent

## Validation Status

- Tests: Passed (`cd asset_generation/python && uv run pytest tests/ -q` — 380 passed, 221 subtests, 2026-04-05)
- Static QA: Not run (same as sibling split tickets)
- Integration: Same command as full Python suite

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

Ticket complete: `AnimatedTarSlug` in `src/enemies/animated_tar_slug.py`; `animated_enemies` imports and registers `tar_slug`. Log: `project_board/checkpoints/split_animated_tar_slug/run-2026-04-05-autopilot.md`.
