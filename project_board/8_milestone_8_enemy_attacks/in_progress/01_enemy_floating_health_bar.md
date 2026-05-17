Title:
Enemy Floating Health Bar (World-Space)

Description:
Add a world-space health bar above each active enemy so the player can quickly read damage impact during combat. The bar should track enemy position in 3D space, update in real time from current HP, and hide when the enemy is at full health unless recently damaged.

Acceptance Criteria:
- Each spawned enemy renders a floating health bar anchored above its head/body center
- Bar fill is driven by enemy current HP / max HP and updates immediately on damage/heal
- Bar is visible for damaged enemies and hidden for full-health enemies after a short timeout
- Bar always faces the camera (billboard behavior) and remains readable while moving
- Bar is removed when the enemy dies or is despawned (no orphan UI nodes)
- Feature can be toggled with a project/debug flag for performance testing

Scope Notes:
- No numeric HP text in this ticket; fill bar only
- No team/faction coloring in this ticket
- No boss-specific oversized bars in this ticket
- Multiplayer authority/sync behavior is out of scope

## Implementation Notes

**Godot Runtime (`scripts/`, `scenes/`)**
- Add a reusable world-space UI scene for health bars (for example `scenes/ui/enemy_health_bar_3d.tscn`)
- Wire enemy HP change events from enemy health/state component to the UI node
- Attach/detach health bar lifecycle to enemy spawn/despawn hooks
- Implement camera-facing billboard update each frame or via node billboard mode

**Tests**
- Add coverage verifying HP ratio updates the bar correctly
- Add coverage verifying full-health auto-hide and damaged re-show behavior
- Add coverage verifying bar cleanup on enemy death/despawn

## WORKFLOW STATE

- **Stage:** IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE
- **Revision:** 6
- **Last Updated By:** Engine Integration Agent
- **Next Responsible Agent:** Acceptance Criteria Gatekeeper Agent
- **Status:** Proceed

## Test Coverage Summary

**Test Suite Composition:**
- Primary tests: `test_enemy_health_bar_3d.gd` (20 tests, smoke + behavioral)
- Adversarial part 1: `test_enemy_health_bar_3d_adversarial.gd` (15 tests)
  - Null/empty inputs, boundary values, invalid data, visibility state machines, lifecycle cleanup
- Adversarial part 2: `test_enemy_health_bar_3d_adversarial_part2.gd` (13 tests)
  - Debug flag behavior, fill ratio mutations, stress scenarios, determinism, positioning
- Integration tests: `test_enemy_health_bar_3d_integration_adversarial.gd` (16 tests)
  - Signal handling, damage events, enemy-bar wiring, scene lifecycle, concurrent enemies, transforms

**Total:** 64 executable adversarial tests covering:
- Null/empty handling (3 tests)
- Boundary conditions: min/max/zero/negative/huge/tiny values (5 tests)
- Invalid floating point: NaN, infinity, negative max_hp (3 tests)
- Visibility state machines: rapid cycles, timeouts (3+3 tests)
- Lifecycle: orphan prevention, reparenting, pause handling (3+3+1 tests)
- Debug flags: persistence, inversion (2 tests)
- Fill ratio mutations: monotonic increase/decrease, precision (3 tests)
- Stress/load: multiple bars, rapid spawn/despawn (2+1 tests)
- Determinism: idempotence, consistency (2+1 tests)
- Billboard positioning: offsets, repeatability (2 tests)
- Signal/damage events: connections, single/multiple damages, zero damage (2+3 tests)
- Wiring patterns: attachment, transform inheritance, concurrent enemies (3+2+1 tests)

**Key Vulnerabilities Exposed:**
- Division by zero on zero max_hp
- Negative HP clamping
- NaN/infinity handling in fill calculations
- Orphaned nodes on early enemy despawn
- Concurrent bar state interference
- Visibility timeout stacking
- Transform offset preservation under rotation/scaling
- Deterministic initialization

All tests are deterministic and reproducible. Current failures are expected (scene/implementation not yet created). Implementation must pass all adversarial tests to ensure robustness.
