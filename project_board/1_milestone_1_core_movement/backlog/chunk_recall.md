# Chunk recall

**Epic:** Milestone 1 – Core Movement Prototype  
**Status:** Backlog

---

## Description

Implement recall of a detached chunk: on input, the chunk returns to the main slime (e.g. elastic tendril animation) and is reabsorbed. Player regains HP on reabsorption; no animation lock that blocks input.

## Acceptance criteria

- [ ] Recall occurs on input when a chunk is detached
- [ ] Tendril visibly stretches then snaps (or minimal visual feedback if placeholder)
- [ ] Player regains HP on reabsorption as specified by design
- [ ] No input delay or lock introduced by recall
- [ ] Recall mechanic is human-playable in-editor: main body, chunk, and any recall visuals are visible and clearly readable without debug overlays
