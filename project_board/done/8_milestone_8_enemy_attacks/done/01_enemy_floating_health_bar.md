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

**Test Results (AC 6 Debug Toggle Verification)**
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
- test_enemy_health_bar_3d_debug_toggle.gd: 9 tests (AC 6 feature toggle verification)
  - enabled=true: update_from_enemy() changes fill (observable state change)
  - enabled=true: on_enemy_damaged() shows bar (observable state change)
  - enabled=true: on_enemy_healed() updates fill (observable state change)
  - enabled=false: on_enemy_damaged() does NOT show bar (guard clause works)
  - enabled=false: on_enemy_healed() does NOT update fill (guard clause works)
  - enabled=false: _process() does NOT update position (guard clause works)
  - Runtime toggle: disabled flag can be toggled at runtime
  - Multiple calls with disabled: no observable state changes (all guard clauses work)
- test_enemy_health_bar_3d_integration_adversarial.gd: 17 tests (real integration)
  - Signal initialization and multi-connection handling
  - Damage event flows (single, multiple, zero damage)
  - Enemy-bar wiring (attachment, transform following, reparenting)
  - Scene lifecycle (spawn, death, pause)
  - Concurrent bar independence
  - Transform behavior under enemy rotation/scale

## WORKFLOW STATE

- **Stage:** COMPLETE
- **Revision:** 9
- **Last Updated By:** Test Designer Agent
- **Validation Status:**
  - **Tests:** 71 behavior-driven tests (5 test files) verify all core ACs including AC 6:
    - Primary tests (13): update_from_enemy(), on_enemy_damaged(), connect_to_enemy() with various HP states, visibility timeout behavior
    - Adversarial part 1 (21): Null/empty reference handling, extreme HP values, invalid floats (NaN/infinity), rapid state cycles, lifecycle cleanup patterns
    - Adversarial part 2 (11): Fill monotonicity, fractional precision, concurrent bar independence, rapid spawn/despawn cycles, determinism checks
    - Debug toggle tests (9): enabled=true executes methods normally, enabled=false guards prevent observable state changes, toggle behavior at runtime
    - Integration (17): Signal wiring patterns, damage event flows (single/multiple/zero), enemy-bar attachment and transform following, scene lifecycle (spawn/death/pause), concurrent scenarios
  - **AC Coverage Map:**
    - AC 1 (floating bar anchored above enemy): Integration tests verify enemy-bar wiring, attachment, transform following
    - AC 2 (HP ratio fill, immediate updates): Primary + adversarial tests verify update_from_enemy() fill updates, on_enemy_damaged() visibility/fill changes, boundary HP values
    - AC 3 (visible when damaged, hidden at full health after timeout): Tests verify visibility state machine, timeout behavior, rapid cycles, default hidden state
    - AC 4 (billboard behavior, readable while moving): Integration tests verify camera projection via _update_position_and_rotation(), transform following under enemy rotation/scale
    - AC 5 (removed on death/despawn, no orphans): Adversarial lifecycle tests, integration scene lifecycle tests verify parent-child cleanup via Godot tree
    - AC 6 (debug flag toggle): Debug toggle test file verifies guard clauses prevent execution when disabled (on_enemy_damaged, on_enemy_healed, _process), and methods execute normally when enabled=true. Tests confirm no observable state changes (visibility, fill) when disabled.
  - **Static QA:** No GDScript linter issues identified in implementation or tests
  - **Integration:** Implementation integrates with Godot scene tree (Control node, ProgressBar, Timer children). Signal connections tested (connect_to_enemy, damage event flow). Transform updates via _process/_update_position_and_rotation() each frame. Lifecycle cleanup via parent-child relationships and explicit signal disconnection.
- **Blocking Issues:** None. AC 6 debug toggle test suite complete and all tests passing.
- **Escalation Notes:** AC 6 (debug flag toggle) now fully tested with 9 focused behavior-driven tests covering enabled=true execution, enabled=false guard clauses, and runtime toggle behavior. All tests passing (exit code 0).

## NEXT ACTION

- **Next Responsible Agent:** Learning Agent
- **Status:** COMPLETE - ticket ready for learning/documentation
- **Reason:** All acceptance criteria verified and tested. AC 6 debug toggle feature now has explicit unit test evidence via test_enemy_health_bar_3d_debug_toggle.gd (9 tests). Feature is production-ready.
- **Test Evidence:** Test file `tests/ui/test_enemy_health_bar_3d_debug_toggle.gd` runs all 9 tests with exit code 0 (success). Tests verify:
  - enabled=true: update_from_enemy() changes fill, on_enemy_damaged() shows bar, on_enemy_healed() updates fill
  - enabled=false: on_enemy_damaged() does not show bar, on_enemy_healed() does not update fill, _process() does not update position
  - Runtime toggle: disabled flag can be toggled and guard clauses respond correctly

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
- Debug toggle tests: `test_enemy_health_bar_3d_debug_toggle.gd` (9 tests, AC 6 verification)
  - Feature enabled behavior: update_from_enemy(), on_enemy_damaged(), on_enemy_healed() execute and produce observable state changes
  - Feature disabled behavior: guard clauses prevent method execution, no observable state changes occur
  - Runtime toggle: enabled flag can be toggled at runtime and guard clauses respond immediately
- Integration tests: `test_enemy_health_bar_3d_integration_adversarial.gd` (17 tests)
  - Signal wiring and multi-connection patterns, damage event sequences (single/multiple/zero)
  - Enemy-bar attachment and transform following, scene lifecycle (spawn/death/pause), concurrent scenarios

**Total:** 71 behavior-driven tests covering:
- Method behavior: update_from_enemy() fill updates, on_enemy_damaged() visibility, connect_to_enemy() signal binding (13 tests)
- Null/empty safety: null enemy, missing HP properties, null signal handling (3 tests)
- Boundary values: zero/max/negative/huge/tiny HP ratios (5 tests)
- Invalid data: NaN/infinity HP handling (2 tests)
- Visibility state: rapid cycles, timeout behavior, default hidden state (6 tests)
- Lifecycle: parent-child cleanup, reparenting, concurrent bars (5 tests)
- Determinism: idempotent updates, consistent toggles, monotonic fill progression (6 tests)
- Debug toggle (AC 6): enabled vs disabled behavior, guard clause verification, runtime toggle behavior (9 tests)
- Integration: signal connections, damage events, transform following, scene pause (17 tests)

**Key Test Patterns:**
- All tests call actual methods (update_from_enemy, on_enemy_damaged, connect_to_enemy, on_enemy_healed) instead of checking scene structure
- Observable state changes verified: progress bar fill values, visibility state, parent-child relationships
- No documentation/prose assertions; all assertions verify runtime behavior
- Explicit _ready() calls ensure bar initialization (timer/progress_bar creation)
- Integration tests verify signal-based damage event flows and enemy-bar wiring patterns
- Debug toggle tests verify enabled flag controls method execution via guard clauses (lines 84, 125, 145 in implementation)
