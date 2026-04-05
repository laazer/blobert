# TICKET: split_animated_carapace_husk

Title: Move `AnimatedCarapaceHusk` to its own Python module (asset generation)

## Description

Split `AnimatedCarapaceHusk` out of `animated_enemies.py` into its own module under `src/enemies/` (same pattern as other animated splits).

## Acceptance Criteria

- `AnimatedCarapaceHusk` in a dedicated file; `carapace_husk` generation unchanged.
- Builder registry resolves `carapace_husk`.

## Dependencies

- None (coordinate registry merges with sibling split tickets)

## Specification

**Full spec:** [`project_board/specs/split_animated_carapace_husk_spec.md`](../../specs/split_animated_carapace_husk_spec.md)

## Execution Plan

| # | Task | Agent | Success criteria |
|---|------|-------|-------------------|
| 1 | Plan module boundary and import graph | Planner | `animated_carapace_husk.py` only; `animated_enemies` re-exports |
| 2 | Spec SCHS-1..3 | Spec | Linked spec file |
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

- Tests: Passed (`cd asset_generation/python && uv run pytest tests/ -q` — 362 passed, 209 subtests, 2026-04-05)
- Static QA: Ruff not required for this change set
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

Ticket complete: `AnimatedCarapaceHusk` in `src/enemies/animated_carapace_husk.py`; `animated_enemies` imports and registers `carapace_husk`. Log: `project_board/checkpoints/split_animated_carapace_husk/run-2026-04-05-autopilot.md`.
