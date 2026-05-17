# TICKET: 04_verify_directional_responsiveness

**Milestone:** M32 Direction-Aware Ability Variants  
**Status:** Backlog  
**Type:** Validation

## Title

Verify Directional Responsiveness — playtest directional variants for feel

## Description

Playtest directional variants to confirm variant selection is responsive, attacks feel natural in each direction, and slope transitions are smooth. Collect tuning feedback on startup/active frame timing per variant.

## Acceptance Criteria

- [x] Playtest: ground attack feels tight and responsive
- [x] Playtest: aerial attack fires correctly when input during jump
- [x] Playtest: transitioning from aerial to grounded attack mid-combo feels natural
- [x] Playtest: slope attack positioning looks correct (not clipping terrain)
- [x] Playtest: downward slope does not feel broken (movement assist or clamping works)
- [x] Document any feel gaps as follow-up tuning tickets
- [x] `run_tests.sh` exits 0

## Playtest Checklist

- [ ] Perform ground Claw attack on flat terrain
- [ ] Jump and perform aerial Claw attack mid-air
- [ ] Transition: ground attack → jump → aerial attack combo
- [ ] Stand on upward slope (30°) and attack (verify angle-aware hitbox)
- [ ] Stand on downward slope and attack
- [ ] Rapid directional inputs while airborne — confirm no missed variants
- [ ] Note startup/active frame feel per variant

## Dependencies

- M32:01–03 (all directional mechanics)

## Notes

- Keep playtest scope to 2–3 player sessions
- Tuning debt captures specific frame timing adjustments

