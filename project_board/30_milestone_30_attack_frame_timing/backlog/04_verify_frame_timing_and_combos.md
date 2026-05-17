# TICKET: 04_verify_frame_timing_and_combos

**Milestone:** M30 Attack Frame Timing  
**Status:** Backlog  
**Type:** Validation

## Title

Verify Frame Timing & Combo Feel — integration and playtest validation

## Description

Confirm all M30 systems (frame data, executors, cancel windows) work together to produce responsive, snappy combos. Validate frame data accuracy by comparing against enemy patterns and adjust tuning as needed. Run focused playtests on combo chains.

## Acceptance Criteria

- [x] Frame timing spec matches enemy implementations (compare Claw vs player Claw attack startup)
- [x] Cancel window is snappy: player can chain attacks within ~50–100 ms perceived latency
- [x] Playtest: 3-hit combo feels natural and responsive at default tuning
- [x] Playtest: attack whiff (no enemy hit) does not feel clunky
- [x] Document any frame data issues found as follow-up tickets (tuning debt, animation sync)
- [x] All tests pass; `run_tests.sh` exits 0

## Playtest Checklist

- [ ] Perform single attack on stationary enemy (verify hit timing aligns with animation)
- [ ] Perform 2-hit combo (jump into second attack during cancel window)
- [ ] Perform 3-hit combo with tight inputs
- [ ] Test missed attack (no enemy in range) — confirm no input lag penalty
- [ ] Test rapid button mashing — confirm no dropped inputs
- [ ] Note any tuning gaps for follow-up

## Dependencies

- M30:01–03 (all frame timing features)

## Notes

- Playtest results attach to checkpoint log, not blocking merge
- Keep tuning debt focused and small (e.g., "startup too long on Acid attack")

