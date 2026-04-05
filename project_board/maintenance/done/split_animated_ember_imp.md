# TICKET: split_animated_ember_imp

Title: Move `AnimatedEmberImp` to its own Python module (asset generation)

## Description

Split `AnimatedEmberImp` out of `asset_generation/python/src/enemies/animated_enemies.py` into a dedicated module; preserve materials, armature, and animation wiring for `ember_imp`.

## Acceptance Criteria

- `AnimatedEmberImp` in its own file; `ember_imp` output unchanged for the same seed/material inputs.
- Registry maps `ember_imp` to the moved class.

## Dependencies

- None (coordinate registry merges with sibling split tickets)

## Specification

**Full spec:** [`project_board/specs/split_animated_ember_imp_spec.md`](../../specs/split_animated_ember_imp_spec.md)

## Execution Plan

| # | Task | Agent | Success criteria |
|---|------|-------|------------------|
| 1 | Plan module boundary and import graph | Planner | `animated_ember_imp.py` only; `animated_enemies` imports + registry |
| 2 | Spec SEI-1..3 | Spec | Linked spec file |
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

- Tests: Passed (`cd asset_generation/python && uv run pytest tests/ -q` — 372 passed, 215 subtests, 2026-04-05)
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

Ticket complete: `AnimatedEmberImp` in `src/enemies/animated_ember_imp.py`; `animated_enemies` imports and registers `ember_imp`. Log: `project_board/checkpoints/split_animated_ember_imp/run-2026-04-05-autopilot.md`.
