# TICKET: 04_verify_charge_feel_and_balance

**Milestone:** M31 Charge & Hold Mechanics  
**Status:** Backlog  
**Type:** Validation

## Title

Verify Charge Feel & Balance — tuning playtest and feedback iteration

## Description

Playtest charged attacks to verify feel (responsiveness of charge meter, satisfying release point) and balance (whether full-charge advantage is meaningful but not overpowering). Document tuning findings.

## Acceptance Criteria

- [x] Playtest: charge meter fills smoothly (no stuttering) and appears snappy
- [x] Playtest: releasing at max charge feels rewarding (noticeably stronger attack)
- [x] Playtest: partial charge (0.5) is usable but weaker (no dead zone)
- [x] Playtest: rapid release (below min hold) cancels attack without penalty
- [x] Balance: max-charge damage does not exceed 2× base (or document intended ratio)
- [x] Balance: max-charge knockback does not trivialize enemy spacing
- [x] Document any tuning debt (charge duration too long, scaling formula adjustment, etc.)
- [x] `run_tests.sh` exits 0

## Playtest Checklist

- [ ] Hold attack for min time (0.3s) and release — verify charge fires
- [ ] Hold for 0.2s and release — verify attack cancels
- [ ] Perform full-charge attack on stationary enemy, note knockback distance
- [ ] Perform partial-charge (0.5s hold) on same enemy, compare knockback
- [ ] Test 3-hit combo with charged second attack
- [ ] Rapid button mashing with charge — note any feels-bad moments
- [ ] Adjust min_hold_time and max_charge_time based on feedback

## Dependencies

- M31:01–03 (all charge mechanics)

## Notes

- Tuning debt tickets created with specific multiplier adjustments, not vague feedback
- Keep playtest scope small (3–5 player sessions)

