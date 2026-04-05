# TICKET: split_animated_acid_spitter

Title: Move `AnimatedAcidSpitter` to its own Python module (asset generation)

## Description

Split `AnimatedAcidSpitter` out of `animated_enemies.py` into its own module under `src/enemies/` (same pattern as other animated splits).

## Acceptance Criteria

- `AnimatedAcidSpitter` in a dedicated file; `acid_spitter` build behavior unchanged.
- `AnimatedEnemyBuilder` / registry includes `acid_spitter`.

## Dependencies

- None (coordinate registry merges with sibling split tickets)

## Specification

**Full spec:** [`project_board/specs/split_animated_acid_spitter_spec.md`](../../specs/split_animated_acid_spitter_spec.md)

## Execution Plan

| # | Task | Agent | Success criteria |
|---|------|-------|-------------------|
| 1 | Plan module boundary and import graph | Planner | `animated_acid_spitter.py` only; `animated_enemies` re-exports |
| 2 | Spec SAAS-1..3 | Spec | Linked spec file |
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

- Tests: Passed (`cd asset_generation/python && uv run pytest tests/ -q` — 345 passed, 198 subtests, 2026-04-05)
- Static QA: Ruff unavailable in uv env on runner; not run
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

Ticket complete: `AnimatedAcidSpitter` in `src/enemies/animated_acid_spitter.py`; `animated_enemies` imports and registers `acid_spitter`. Log: `project_board/checkpoints/split_animated_acid_spitter/run-2026-04-05-autopilot.md`.
