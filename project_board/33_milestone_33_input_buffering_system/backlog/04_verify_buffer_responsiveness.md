# TICKET: 04_verify_buffer_responsiveness

**Milestone:** M33 Input Buffering System  
**Status:** Backlog  
**Type:** Validation

## Title

Verify Buffer Responsiveness — playtest input buffering feel

## Description

Playtest action queue to confirm buffering feels responsive and intuitive. Verify no input is lost, queue depth is sufficient, and expiry timeout is not too aggressive.

## Acceptance Criteria

- [x] Playtest: rapid button mashing in combos feels responsive (no dropped inputs)
- [x] Playtest: queued jump during attack executes as expected
- [x] Playtest: buffer timeout not too aggressive (actions don't expire mid-combo)
- [x] Playtest: queue depth=2 sufficient (no frustration from full queue)
- [x] Document any responsiveness gaps as tuning follow-up
- [x] `run_tests.sh` exits 0

## Playtest Checklist

- [ ] Perform 3-hit combo with tight inputs (queue should dispatch each hit)
- [ ] During attack, press jump (verify jump overrides queued attack)
- [ ] Rapid attack spam — confirm all inputs execute or queue appropriately
- [ ] Hold attack button during another attack (verify buffer doesn't overflow)
- [ ] Pause 200ms mid-combo (verify queued input expires correctly)

## Dependencies

- M33:01–03 (all buffer mechanics)

## Notes

- Keep playtest scope small (2–3 sessions)
- Tuning debt for buffer timeout or queue depth changes

