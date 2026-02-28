# Chunk detach

**Epic:** Milestone 1 – Core Movement Prototype  
**Status:** Backlog

---

## Description

Implement the mechanic where the slime can detach a chunk (e.g. on input). The chunk becomes a separate entity in the world; the main body and chunk are both represented and can be moved/used later.

## Acceptance criteria

- [ ] Detach input triggers chunk separation from main slime body
- [ ] Detached chunk exists in world as its own object (position, collision if needed)
- [ ] Main body state updates (e.g. “has chunk” flag) so recall and HP can hook in
- [ ] No crash or undefined state when detaching; behavior is deterministic
