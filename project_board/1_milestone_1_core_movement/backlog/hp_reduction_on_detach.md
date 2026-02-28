# HP reduction on detach

**Epic:** Milestone 1 – Core Movement Prototype  
**Status:** Backlog

---

## Description

When the slime detaches a chunk, reduce the player’s current HP by a defined amount (or percentage) so detach has a clear cost and ties into the infection/mutation loop later.

## Acceptance criteria

- [ ] HP decreases by configured amount/percentage when chunk is detached
- [ ] HP does not go below minimum (e.g. 0 or 1) if design specifies a floor
- [ ] HP state is consistent with chunk state (detached vs reabsorbed)
- [ ] No exploit (e.g. repeated detach/recall for unintended HP gain)
