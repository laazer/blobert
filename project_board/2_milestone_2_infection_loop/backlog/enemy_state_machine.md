# Enemy state machine

**Epic:** Milestone 2 – Infection Loop  
**Status:** Backlog

---

## Description

Implement an enemy state machine (e.g. idle, patrol, alert, weakened, infected) so enemies can transition through states required for the weaken → infect → absorb loop.

## Acceptance criteria

- [ ] Enemies have defined states and transitions (at least: normal, weakened, infected)
- [ ] State changes are driven by gameplay events (damage, infection, etc.)
- [ ] No invalid or stuck states; behavior is deterministic and testable
- [ ] Fits into existing or planned enemy spawn/placement
