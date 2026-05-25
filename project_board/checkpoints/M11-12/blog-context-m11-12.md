## Blog Context Capsule — M11-12

- **Ticket:** M11-12 Verify Cooldown Behavior Across Player State Transitions
- **Goal:** Verify and test that cooldown tracking is correct across all player states (IDLE, WALK, JUMP, FALL, WALL_CLING, HURT, DEAD) with per-mutation independence
- **Outcome:** COMPLETE
- **Commits:** a112309 (implementation + tests), 920ddec (ticket close), 00316d5 (checkpoint artifacts)
- **Checkpoint log:** project_board/checkpoints/M11-12/
- **Key insights:**
  - Original ticket specified "manual tests" — the pipeline correctly converted to 83 automated behavioral tests (46 primary + 37 adversarial), proving the verification ticket pattern works
  - Only 1 real code bug found: `reset_hp()` was missing `_mutation_cooldowns.clear()` — death/respawn didn't reset attack cooldowns
  - Adversarial testing discovered a defensive gap: negative engine delta could increase cooldowns (fixed with `maxf(0.0, delta)` guard)
  - `player_controller_3d.gd` hit the 900-line limit (902 after +2 lines), requiring inline optimization to get to 899 — this file is at capacity
