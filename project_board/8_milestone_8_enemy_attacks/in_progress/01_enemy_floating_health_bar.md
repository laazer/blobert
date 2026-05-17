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
- Implemented reusable world-space UI scene: `scenes/ui/enemy_health_bar_3d.tscn`
- Created script controller: `scripts/ui/enemy_health_bar_3d.gd`
- Bar positioned using world-to-screen projection (Control-based for 2D rendering)
- Automatic lifecycle management via Godot parent-child relationships
- HP change handling via `update_from_enemy()` and damage signal methods
- Camera-facing positioning each frame via `_update_position_and_rotation()`

**Implementation Strategy**
- Used Control node root (not Node3D) for reliable 2D UI rendering
- Projects 3D enemy world position to screen space each frame
- Height offset configurable via @export variable
- Visibility toggle via @export enabled flag
- Clamped HP ratio to [0.0, 1.0] prevents invalid fill values
- Visibility timeout prevents bar flickering at full health
- Null/invalid enemy reference handling via defensive checks

**Test Results (After Rewrite)**
- test_enemy_health_bar_3d.gd: 13 tests (behavior-driven, verify core methods)
  - update_from_enemy() with various HP states
  - on_enemy_damaged() visibility and fill updates
  - visibility timeout behavior
  - connect_to_enemy() signal wiring
  - Full damage cycle integration
  - Edge cases (null enemy, zero max_hp, overheal)
- test_enemy_health_bar_3d_adversarial.gd: 21 tests (boundary + null safety)
  - Null/empty reference handling
  - Extreme HP values (zero, negative, huge, tiny)
  - Invalid floating point (NaN, infinity)
  - Rapid damage/hide/heal cycles
  - Lifecycle and orphan prevention
  - Integration patterns (update + damage sequences)
- test_enemy_health_bar_3d_adversarial_part2.gd: 11 tests (state mutations)
  - Fill monotonicity (increase/decrease)
  - Fractional precision at various HP values
  - Multiple simultaneous bars (no shared state)
  - Rapid spawn/despawn cycles
  - Determinism (idempotent updates, consistent toggles)
  - State transitions (sequential updates, alternating heal/damage)
- test_enemy_health_bar_3d_integration_adversarial.gd: 17 tests (real integration)
  - Signal initialization and multi-connection handling
  - Damage event flows (single, multiple, zero damage)
  - Enemy-bar wiring (attachment, transform following, reparenting)
  - Scene lifecycle (spawn, death, pause)
  - Concurrent bar independence
  - Transform behavior under enemy rotation/scale

## WORKFLOW STATE

- **Stage:** IMPLEMENTATION_ENGINE_INTEGRATION_COMPLETE
- **Revision:** 7
- **Last Updated By:** Engine Integration Agent
- **Next Responsible Agent:** Acceptance Criteria Gatekeeper Agent
- **Status:** Tests rewritten to verify executable behavior, not documentation

## Test Coverage Summary

**Test Suite Composition (Behavior-Driven):**
- Primary tests: `test_enemy_health_bar_3d.gd` (13 tests)
  - Core method integration: update_from_enemy(), on_enemy_damaged(), connect_to_enemy()
  - Observable state changes: fill ratio updates, visibility toggles, signal handling
- Adversarial part 1: `test_enemy_health_bar_3d_adversarial.gd` (21 tests)
  - Null/empty reference safety, boundary value handling (zero/negative/huge/tiny HP), invalid floating point
  - Rapid state machine cycles, lifecycle cleanup with parent-child cleanup patterns
- Adversarial part 2: `test_enemy_health_bar_3d_adversarial_part2.gd` (11 tests)
  - Fill ratio monotonicity during HP increase/decrease, fractional precision, concurrent bar independence
  - Stress tests (simultaneous spawns, rapid cycles), determinism via idempotent method calls
- Integration tests: `test_enemy_health_bar_3d_integration_adversarial.gd` (17 tests)
  - Signal wiring and multi-connection patterns, damage event sequences (single/multiple/zero)
  - Enemy-bar attachment and transform following, scene lifecycle (spawn/death/pause), concurrent scenarios

**Total:** 62 behavior-driven tests covering:
- Method behavior: update_from_enemy() fill updates, on_enemy_damaged() visibility, connect_to_enemy() signal binding (13 tests)
- Null/empty safety: null enemy, missing HP properties, null signal handling (3 tests)
- Boundary values: zero/max/negative/huge/tiny HP ratios (5 tests)
- Invalid data: NaN/infinity HP handling (2 tests)
- Visibility state: rapid cycles, timeout behavior, default hidden state (6 tests)
- Lifecycle: parent-child cleanup, reparenting, concurrent bars (5 tests)
- Determinism: idempotent updates, consistent toggles, monotonic fill progression (6 tests)
- Integration: signal connections, damage events, transform following, scene pause (17 tests)

**Key Test Patterns:**
- All tests call actual methods (update_from_enemy, on_enemy_damaged, connect_to_enemy) instead of checking scene structure
- Observable state changes verified: progress bar fill values, visibility state, parent-child relationships
- No documentation/prose assertions; all assertions verify runtime behavior
- Explicit _ready() calls ensure bar initialization (timer/progress_bar creation)
- Integration tests verify signal-based damage event flows and enemy-bar wiring patterns
