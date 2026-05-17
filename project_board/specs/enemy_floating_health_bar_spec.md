# SPECIFICATION: Enemy Floating Health Bar (World-Space)

**Ticket:** `project_board/8_milestone_8_enemy_attacks/in_progress/01_enemy_floating_health_bar.md`  
**Spec Version:** 1  
**Last Updated:** 2026-05-16  
**Spec Agent:** Autonomous

---

## 1. SPEC SUMMARY

### Description
A world-space 3D UI component that renders above each spawned enemy to display current health as a visual bar. The bar must track the enemy's position in 3D space, update in real-time as the enemy takes damage or healing, and manage visibility based on health state (visible when damaged, hidden when at full health). The feature must support camera-facing billboard behavior so the bar remains readable from any camera angle and automatically clean up on enemy death/despawn.

### Constraints

1. **Health System Coupling:** The feature depends on an `EnemyHealthComponent` or equivalent that tracks `current_hp` and `max_hp` for each enemy. This component must emit damage/heal signals that the health bar observes.
2. **Enemy Node Contract:** Enemies are spawned as `EnemyInfection3D` (CharacterBody3D subclass). The health bar must attach as a child or sibling of the enemy and move with it (or use a constraint system).
3. **Camera Orientation:** The health bar visual (ProgressBar or equivalent UI element) must use Godot's billboard mode or manual rotation so it faces the camera at all times.
4. **3D Space Rendering:** Health bars render in world space (3D coordinates), not screen space. The UI element must be a SubViewport + CanvasLayer or a MeshInstance3D with a material-based UI, or use a WorldEnvironment + custom shader approach. **No screen-space CanvasLayer overlay in this ticket.** (Clarification: UI is in world-space; if implemented via SubViewport, the SubViewport itself is a world-space node.)
5. **No HP Text:** This ticket renders fill bar only; numeric HP values are explicitly out of scope.
6. **No Team/Faction Coloring:** The bar uses a single, neutral color (e.g., green-to-red gradient). Multi-faction or team-based color schemes are out of scope.
7. **No Boss Oversizing:** All health bars render at the same relative scale. Boss-specific bar sizing is out of scope.
8. **No Multiplayer Sync:** Multiplayer authority/network sync behavior is out of scope.
9. **Debug Flag:** The feature can be toggled globally via a project setting or debug export variable for performance testing.

### Assumptions

1. **Health Component Existence:** `EnemyInfection3D` or its parent `EnemyBase` will be extended to include a health component with `current_hp`, `max_hp` properties and `hp_changed` (or equivalent) signal before or during implementation.
2. **Signal Availability:** The health component will emit a signal on damage/heal; the health bar will observe and react.
3. **Enemy Hierarchy:** Health bar can be attached as a direct child of `EnemyInfection3D` or as a sibling with a lookup mechanism (e.g., parent reference).
4. **Position Anchor:** "Anchored above the head/body center" means a local offset (e.g., `local_position = Vector3(0, 1.2, 0)` relative to enemy root).
5. **Camera Existence:** At least one active camera exists in the scene (`Camera3D` node with `current = true`).
6. **Immediate Update:** "Updates immediately on damage/heal" means within one physics/process frame of the signal.

### Scope

- **In Scope:**
  - World-space health bar scene/script (`scenes/ui/enemy_health_bar_3d.tscn` + accompanying script)
  - Health component for enemies (`scripts/enemies/enemy_health_component.gd` or similar)
  - Billboard/camera-facing behavior each frame
  - Damage/heal event wiring and signal observation
  - Visibility lifecycle (visible when damaged, hidden after idle timeout)
  - Cleanup on enemy death/despawn
  - Debug toggle via project setting/export variable
  - Test coverage (HP ratio updates, visibility transitions, cleanup)

- **Out of Scope:**
  - Numeric HP text rendering
  - Team/faction-based coloring
  - Boss-specific bar sizing or styling
  - Multiplayer authority/RPC behavior
  - Health bar appearances in non-3D contexts (UI canvas, minimaps, etc.)
  - Floating damage numbers or other combat UI effects

---

## 2. ACCEPTANCE CRITERIA

### AC-EFHB-01: Enemy Health Component Exists and Tracks HP
**Description:** Each enemy must have a health component that tracks `current_hp` and `max_hp`.  
**Measurable:** The component is instantiated on enemy spawn and has public getter methods `get_current_hp()` and `get_max_hp()` returning floats.  
**Example:**
```gdscript
var hp_component = enemy.get_node_or_null("HealthComponent")
assert(hp_component.get_current_hp() > 0)
assert(hp_component.get_max_hp() > 0)
```

---

### AC-EFHB-02: Health Component Emits Damage/Heal Signals
**Description:** When HP changes (damage or heal), the component emits a signal that includes new HP value.  
**Measurable:** Signal exists (e.g., `hp_changed(new_hp: float)`) and is emitted whenever `current_hp` is updated.  
**Example:**
```gdscript
var signal_received = false
enemy.hp_component.hp_changed.connect(func(_new_hp): signal_received = true)
enemy.hp_component.take_damage(10.0)
assert(signal_received == true)
```

---

### AC-EFHB-03: Health Bar Scene Exists with Correct Structure
**Description:** A reusable world-space health bar scene exists at `res://scenes/ui/enemy_health_bar_3d.tscn`.  
**Measurable:** Scene file is present, loads without errors, and instantiates to a Node3D with a visible health bar UI element.  
**Example:**
```gdscript
var bar_scene = load("res://scenes/ui/enemy_health_bar_3d.tscn") as PackedScene
assert(bar_scene != null)
var bar = bar_scene.instantiate() as Node3D
assert(bar != null)
```

---

### AC-EFHB-04: Health Bar Follows Enemy 3D Position
**Description:** The health bar is positioned in world space, anchored above the enemy's center, and moves with the enemy.  
**Measurable:** Bar's global position tracks enemy's global position + offset. When enemy moves, bar moves with it (same frame or next frame).  
**Example:**
```gdscript
var enemy_pos = enemy.global_position
var bar_pos = health_bar.global_position
var expected_offset = Vector3(0, 1.2, 0)
assert(bar_pos.distance_to(enemy_pos + expected_offset) < 0.1)

enemy.global_position += Vector3(5, 0, 0)
await get_tree().process_frame
assert(bar_pos.distance_to(enemy.global_position + expected_offset) < 0.1)
```

---

### AC-EFHB-05: Health Bar Faces Camera (Billboard Behavior)
**Description:** The health bar visual (mesh/UI quad) rotates to face the camera each frame so it remains readable from any viewing angle.  
**Measurable:** Bar's normal vector points toward the camera. Manual rotation or Godot's `billboard` node property can achieve this.  
**Example:**
```gdscript
var cam = get_viewport().get_camera_3d()
var bar_to_cam = (cam.global_position - bar.global_position).normalized()
var bar_normal = bar.global_transform.basis.z  # or equivalently the bar's facing
assert(bar_to_cam.dot(bar_normal) > 0.9)  # nearly parallel
```

---

### AC-EFHB-06: Bar Fill Reflects HP Ratio in Real-Time
**Description:** The bar's fill percentage is `current_hp / max_hp * 100`. Updates occur immediately (within one frame) of an HP change signal.  
**Measurable:** ProgressBar or equivalent's `value` property = (current_hp / max_hp) * 100. Test by damaging enemy and checking bar fill.  
**Example:**
```gdscript
var bar = health_bar.get_node("ProgressBar") as ProgressBar
assert(bar.value == 0)  # full health, bar filled
assert(bar.max_value == 100)

enemy.hp_component.take_damage(25.0)  # 25 damage to 100 max
await get_tree().process_frame
assert(bar.value == 75)  # 75 HP remaining = 75% fill
```

---

### AC-EFHB-07: Full-Health Bar Hidden After Timeout
**Description:** When enemy HP equals max HP, the health bar is hidden (invisible). It remains hidden until the enemy takes damage again.  
**Measurable:** Bar visibility is toggled via `visible = false` when `current_hp == max_hp`. A timer or signal check enforces this.  
**Example:**
```gdscript
assert(health_bar.visible == true)  # assuming enemy spawned at full health with bar visible initially
await get_tree().create_timer(0.5).timeout  # wait past any initial animation grace period
assert(health_bar.visible == false)  # bar hides at full health

enemy.hp_component.take_damage(1.0)  # take any damage
await get_tree().process_frame
assert(health_bar.visible == true)  # bar reappears
```

---

### AC-EFHB-08: Damaged Enemy Bar Shows Immediately
**Description:** When a full-health enemy takes damage, the bar becomes visible immediately (next frame or same frame).  
**Measurable:** On `hp_changed` signal, if `current_hp < max_hp`, set `visible = true`.  
**Example:**
```gdscript
# Enemy starts at full health with bar hidden
assert(health_bar.visible == false)

enemy.hp_component.take_damage(1.0)
await get_tree().process_frame
assert(health_bar.visible == true)
```

---

### AC-EFHB-09: Bar Removed on Enemy Death
**Description:** When enemy dies (state transitions to `dead` or destroyed), the health bar is freed/removed from the scene tree.  
**Measurable:** Bar node no longer exists in tree; `is_valid()` returns false or `get_parent() == null`.  
**Example:**
```gdscript
var bar_node = health_bar
assert(is_instance_valid(bar_node) == true)

enemy.hp_component.apply_death_event()  # or equivalent
await get_tree().process_frame
assert(is_instance_valid(bar_node) == false)
```

---

### AC-EFHB-10: Bar Removed on Enemy Despawn
**Description:** When enemy is removed from the scene (freed or queue_free'd), the health bar is also removed.  
**Measurable:** If enemy is freed, the bar (as a child or tracked sibling) is also freed.  
**Example:**
```gdscript
var bar_node = health_bar
enemy.queue_free()
await get_tree().process_frame
assert(is_instance_valid(bar_node) == false)
```

---

### AC-EFHB-11: Debug Toggle Disables/Enables Health Bars Globally
**Description:** A project setting (e.g., `debug/enemy_health_bar_enabled`) or debug export variable controls feature visibility.  
**Measurable:** When toggle is off, no health bars render. When on, they render normally. The toggle can be changed at runtime.  
**Example:**
```gdscript
ProjectSettings.set_setting("debug/enemy_health_bar_enabled", false)
# All existing bars become invisible or are skipped
var new_bar = health_bar_scene.instantiate()
parent.add_child(new_bar)
assert(new_bar.visible == false or new_bar not in scene)

ProjectSettings.set_setting("debug/enemy_health_bar_enabled", true)
# Bars reappear or are re-enabled
assert(new_bar.visible == true or new_bar in scene)
```

---

### AC-EFHB-12: Test Coverage — HP Ratio Updates
**Description:** Automated test verifies that bar fill updates correctly on damage.  
**Measurable:** Test exists in `tests/scripts/ui/test_enemy_health_bar_3d.gd` (or similar) and covers at least three HP values (full, half, near-empty).  
**Example:**
```gdscript
func test_health_bar_hp_ratio_updates_on_damage() -> void:
    # Full health
    assert(bar.value == 100)
    
    # Half damage
    enemy.hp_component.take_damage(50.0)
    await get_tree().process_frame
    assert(bar.value == 50)
    
    # Near empty
    enemy.hp_component.take_damage(49.0)
    await get_tree().process_frame
    assert(bar.value == 1)
```

---

### AC-EFHB-13: Test Coverage — Visibility Transitions
**Description:** Automated test verifies full-health hide, damaged show, and initial state.  
**Measurable:** Test exists and checks visibility at spawn (full health), after damage, and after healing back to full.  
**Example:**
```gdscript
func test_health_bar_visibility_on_damage_and_heal() -> void:
    # At spawn (full health), bar is initially invisible after grace period
    await get_tree().create_timer(0.5).timeout
    assert(bar.visible == false)
    
    # Take damage
    enemy.hp_component.take_damage(1.0)
    await get_tree().process_frame
    assert(bar.visible == true)
    
    # Heal back to full
    enemy.hp_component.take_heal(1.0)
    await get_tree().process_frame
    assert(bar.visible == false)
```

---

### AC-EFHB-14: Test Coverage — Bar Cleanup on Death
**Description:** Automated test verifies bar is freed when enemy dies.  
**Measurable:** Test exists and confirms health bar node is no longer valid after enemy death.  
**Example:**
```gdscript
func test_health_bar_cleanup_on_enemy_death() -> void:
    var bar = health_bar
    assert(is_instance_valid(bar) == true)
    
    enemy.hp_component.apply_death_event()
    await get_tree().process_frame
    
    assert(is_instance_valid(bar) == false)
```

---

### AC-EFHB-15: Test Coverage — Bar Cleanup on Despawn
**Description:** Automated test verifies bar is freed when enemy is removed from scene.  
**Measurable:** Test exists and confirms health bar is freed when enemy is freed.  
**Example:**
```gdscript
func test_health_bar_cleanup_on_enemy_despawn() -> void:
    var bar = health_bar
    enemy.queue_free()
    await get_tree().process_frame
    
    assert(is_instance_valid(bar) == false)
```

---

### AC-EFHB-16: Full Test Suite Passes
**Description:** All tests run and pass; `ci/scripts/run_tests.sh` exits with code 0.  
**Measurable:** Godot test harness reports `=== ALL TESTS PASSED ===` and no errors in stderr.  
**Example:**
```bash
timeout 300 ci/scripts/run_tests.sh
# Exit code 0; output contains "ALL TESTS PASSED"
```

---

## 3. RISK & AMBIGUITY ANALYSIS

### Risk-1: Health Component Implementation Timing
**Risk:** No health component currently exists on enemies; it must be created first.  
**Impact:** Implementation agent must create `EnemyHealthComponent` before wiring the bar. This is a blocking dependency.  
**Mitigation:** Spec defines the expected interface (`get_current_hp()`, `get_max_hp()`, `hp_changed` signal) so the health component and health bar can be developed in parallel or the health component can be added as part of this ticket's scope.  
**Evidence:** Current enemy code has no HP tracking; `EnemyStateMMachine` tracks state but not health values.

---

### Risk-2: World-Space UI Rendering Approach
**Risk:** Godot's world-space UI is not a single built-in feature. Three possible approaches exist:
- **SubViewport-based:** CanvasLayer inside a SubViewport, rendered to a 3D quad or mesh.
- **MeshInstance3D + Custom Material:** Material-based rendering of a progress bar shape.
- **Billboard-Mode Rect3D Node:** If Godot 4+ supports a 2D-in-3D billboard rect (TBD).

**Impact:** Test Designer and Implementation must choose the approach. Spec does not mandate the exact technique.  
**Mitigation:** Acceptance criteria focus on behavior (bar follows enemy, faces camera, updates HP) rather than implementation detail. Any approach that satisfies the criteria is valid.  
**Evidence:** No existing world-space UI in the codebase; all current UI is screen-space CanvasLayer (`scenes/ui/game_ui.tscn`).

---

### Risk-3: Camera Orientation Correctness
**Risk:** Billboard rotation may be incorrect if camera culling, view projection, or Godot's coordinate system assumptions are misunderstood.  
**Impact:** Bar may face wrong direction or rotate erratically.  
**Mitigation:** Acceptance criteria (AC-EFHB-05) define a testable condition: bar normal nearly parallel to camera-to-bar vector. Test this directly.  
**Evidence:** StandardMaterial3D in Godot 4 has a `billboard` property, but it may not work as expected for 2D UI quads; manual rotation in `_process` is the safer fallback.

---

### Risk-4: Visibility Timeout Duration Not Specified
**Risk:** Ticket says "hide when at full health after a short timeout" but does not specify the timeout duration (e.g., 0.5s, 1.0s, 2.0s).  
**Impact:** Implementation agent must choose a value. Different values affect gameplay feel.  
**Mitigation:** Spec defines the behavior (full health → hide) but leaves the exact timeout as an implementation detail. Test Designer should parameterize the timeout and test both edges (just before and just after).  
**Evidence:** No timeout value in ticket description or existing code.

---

### Risk-5: Heal Method Missing from Health Component
**Risk:** Current code only shows damage; heal logic is not defined in `EnemyHealthComponent`.  
**Impact:** Test AC-EFHB-13 references `take_heal()`, which may not exist yet.  
**Mitigation:** Health component must support both `take_damage()` and `take_heal()` (or healing is not testable). Spec includes heal method in AC-EFHB-02 implicitly (signal on any HP change).  
**Evidence:** No heal method found in player or enemy HP tracking.

---

### Risk-6: Multiple Health Bars Per Enemy (Edge Case)
**Risk:** If health bar is attached as a child during enemy `_ready()` and enemies can respawn or be cloned, multiple bars may accumulate.  
**Impact:** Orphan health bars in the scene tree; memory leak and visual clutter.  
**Mitigation:** Cleanup logic must ensure only one bar exists per enemy. Either attach at spawn and free on despawn, or use a lookup+destroy pattern.  
**Evidence:** No existing orphan-prevention logic in player/chunk/enemy lifecycle code.

---

### Risk-7: Debug Toggle Scope
**Risk:** "Debug toggle" could mean global (all enemies), per-enemy, or per-scene. Spec assumes global, but clarity is needed.  
**Impact:** If per-enemy, each health bar needs an independent flag check; if global, one setting controls all.  
**Mitigation:** AC-EFHB-11 defines global toggle via ProjectSettings. If per-enemy toggle is needed, it can be added later.  
**Evidence:** Ticket says "toggle with a project/debug flag" → global assumption is reasonable.

---

### Risk-8: Performance Under Many Enemies
**Risk:** World-space UI rendering for each enemy (10+) may have frame-rate impact, especially if billboard rotation is done per-bar per-frame.  
**Impact:** Frame drops in high-enemy-count scenarios.  
**Mitigation:** Debug toggle exists to disable bars for performance profiling. Optimization (batching, shared camera-facing shader) is out of scope but can be added later.  
**Evidence:** No performance baseline or enemy count limit in spec; test should include a multi-enemy scenario.

---

### Risk-9: Health Bar Positioning Assumption (Above vs. Center)
**Risk:** "Anchored above head/body center" could mean 1.0m, 1.2m, or 2.0m. If enemy model height varies, offset may need adjustment per enemy type.  
**Impact:** Bar may clip into enemy model or appear too far away for some enemy families.  
**Mitigation:** Spec assumes a fixed offset (e.g., 1.2m above enemy root) as a reasonable default. Per-enemy offsets can be added later via an export variable on the health bar script.  
**Evidence:** Generated enemies have varying heights; no asset metadata on exact model heights in generated GLB files.

---

### Risk-10: Signal Timing and Frame Synchronization
**Risk:** If enemy takes damage in `_physics_process` and health bar updates in `_process`, a one-frame delay could occur.  
**Impact:** Visual desync between damage event and bar update (minor).  
**Mitigation:** Spec requires "immediate" update; tests must verify next-frame consistency.  
**Evidence:** No existing pattern in codebase for health signal wiring.

---

## 4. CLARIFYING QUESTIONS

### Question-1: Health Component Ownership
**Q:** Should the health component be a child node (e.g., `EnemyInfection3D/HealthComponent`) or part of the enemy script?  
**A-Assumption:** Component is a child node so the health bar and other systems can observe it independently. Attach during enemy `_ready()` or in the scene.

---

### Question-2: Max HP Per Enemy Type
**Q:** Do different enemy families (acid spitter, adhesion bug, claw crawler, carapace husk) have different max HP values?  
**A-Assumption:** All enemies have the same max HP (100.0) for initial implementation. Per-family tuning can be added later via export variables.

---

### Question-3: Healing Events
**Q:** Under what gameplay conditions do enemies heal? (DoT reversal, player mutation, etc.)  
**A-Assumption:** Healing is not a current gameplay mechanic for enemies. Health component supports `take_heal()` for future extensibility but is not called in M8. Tests may include healing for completeness.

---

### Question-4: Health Bar Lifecycle
**Q:** Should the health bar scene be instantiated in the enemy's `_ready()` or by a separate spawner/manager?  
**A-Assumption:** Health bar is instantiated as a child of `EnemyInfection3D` in the enemy's `_ready()` (simplest ownership model).

---

### Question-5: Visibility Timeout Grace Period
**Q:** How long should an enemy at full health remain visible before the bar hides? (e.g., 0.2s, 0.5s, 1.0s?)  
**A-Assumption:** Use a reasonable value like 0.5s to 1.0s. Implementation agent chooses; Test Designer parameterizes for robustness.

---

### Question-6: Camera Independence
**Q:** If multiple cameras exist in the scene, which one should the bar face?  
**A-Assumption:** Bar faces the current viewport camera (`get_viewport().get_camera_3d()`). If no camera or multiple cameras, use the first active one.

---

### Question-7: Bar Visual Style
**Q:** Should the bar be a simple rectangle, rounded corners, gradient-filled, or with borders?  
**A-Assumption:** Simple rectangle, possibly with a border. Style is a later polish task. Spec only requires a fill percentage.

---

### Question-8: Z-Fighting and Depth
**Q:** If the bar is a world-space quad, how should depth testing and Z-offset be handled to prevent clipping/fighting?  
**A-Assumption:** Place bar slightly forward of enemy (Z offset into camera view) or use a small render priority offset. Material depth testing handles this.

---

### Question-9: Scale/Size of Health Bar
**Q:** Should the health bar scale with the enemy model, or is it a fixed world size?  
**A-Assumption:** Fixed size in world units (e.g., 0.5m wide, 0.1m tall). Relative scaling to enemy size can be added later if needed.

---

### Question-10: Visibility Beyond Frustum
**Q:** If the enemy is off-screen or behind the camera, should the health bar still render (or be culled)?  
**A-Assumption:** Standard Godot camera culling applies; if enemy is culled, bar is culled. No special logic needed.

---

## 5. IMPLEMENTATION NOTES

### File Structure
```
scripts/enemies/enemy_health_component.gd         # Health tracking (HP, signals)
scenes/ui/enemy_health_bar_3d.tscn               # Health bar scene (root: Node3D)
scripts/ui/enemy_health_bar_3d.gd                # Health bar behavior (billboard, visibility)
scenes/enemy/enemy_infection_3d.tscn             # May be updated to include health bar instantiation
tests/scripts/ui/test_enemy_health_bar_3d.gd     # Test suite
```

### Health Component Interface (Normative)
```gdscript
class_name EnemyHealthComponent
extends Node

signal hp_changed(new_hp: float)
signal enemy_died

var current_hp: float
var max_hp: float

func take_damage(amount: float) -> void:
    current_hp = maxf(0.0, current_hp - amount)
    hp_changed.emit(current_hp)
    if current_hp <= 0.0:
        enemy_died.emit()

func take_heal(amount: float) -> void:
    current_hp = minf(max_hp, current_hp + amount)
    hp_changed.emit(current_hp)

func apply_death_event() -> void:
    current_hp = 0.0
    hp_changed.emit(0.0)
    enemy_died.emit()

func get_current_hp() -> float:
    return current_hp

func get_max_hp() -> float:
    return max_hp
```

### Health Bar Script Outline (Normative)
```gdscript
class_name EnemyHealthBar3D
extends Node3D

@export var show_timeout_seconds: float = 0.5
@export var position_offset: Vector3 = Vector3(0, 1.2, 0)

var _enemy: EnemyInfection3D
var _health_component: EnemyHealthComponent
var _progress_bar: ProgressBar
var _hide_timer: float = 0.0
var _is_at_full_health: bool = false

func _ready() -> void:
    _enemy = get_parent() as EnemyInfection3D
    _health_component = _enemy.get_node_or_null("HealthComponent") as EnemyHealthComponent
    _progress_bar = get_node_or_null("ProgressBar") as ProgressBar
    
    if _health_component != null:
        _health_component.hp_changed.connect(_on_hp_changed)
        _health_component.enemy_died.connect(_on_enemy_died)
        _update_bar_fill()

func _process(delta: float) -> void:
    if not _is_enabled():
        return
    
    # Update position
    if _enemy != null:
        global_position = _enemy.global_position + position_offset
    
    # Face camera
    _face_camera()
    
    # Handle visibility timeout
    if _is_at_full_health:
        _hide_timer += delta
        if _hide_timer >= show_timeout_seconds:
            visible = false

func _is_enabled() -> bool:
    return ProjectSettings.get_setting("debug/enemy_health_bar_enabled", true)

func _on_hp_changed(new_hp: float) -> void:
    _update_bar_fill()
    if _health_component.current_hp < _health_component.max_hp:
        _is_at_full_health = false
        visible = true
        _hide_timer = 0.0
    else:
        _is_at_full_health = true
        _hide_timer = 0.0

func _on_enemy_died() -> void:
    queue_free()

def _update_bar_fill() -> void:
    if _progress_bar == null or _health_component == null:
        return
    var fill_percent = (_health_component.current_hp / _health_component.max_hp) * 100.0
    _progress_bar.value = fill_percent

def _face_camera() -> void:
    var cam = get_viewport().get_camera_3d()
    if cam == null:
        return
    var direction = (cam.global_position - global_position).normalized()
    # Rotate to face camera (billboard behavior)
    # Implementation depends on 3D node structure; manual or built-in billboard mode
```

### Scene File Guidance
The `scenes/ui/enemy_health_bar_3d.tscn` should contain:
- Root: `Node3D` with script `EnemyHealthBar3D`
- Child: `ProgressBar` or equivalent fill visual (UI element rendered in world space via SubViewport or MeshInstance3D)
- Optionally: `SubViewport` container if using SubViewport-based rendering

---

## 6. DEPENDENCIES

- **On:** Enemy health component (`EnemyHealthComponent`) must exist and emit `hp_changed` signal.
- **On:** `EnemyInfection3D` or parent must allow child node attachment.
- **On:** Godot 4.x with `ProgressBar`, `SubViewport`, or equivalent UI rendering in world space.

---

## 7. TRACEABILITY

| Requirement | Acceptance Criteria | Test File |
|---|---|---|
| Health system exists | AC-EFHB-01, AC-EFHB-02 | test_enemy_health_bar_3d.gd |
| Bar scene exists | AC-EFHB-03 | test_enemy_health_bar_3d.gd |
| Bar follows enemy | AC-EFHB-04 | test_enemy_health_bar_3d.gd |
| Bar faces camera | AC-EFHB-05 | test_enemy_health_bar_3d.gd |
| HP ratio in bar | AC-EFHB-06, AC-EFHB-12 | test_enemy_health_bar_3d.gd |
| Full health hiding | AC-EFHB-07, AC-EFHB-13 | test_enemy_health_bar_3d.gd |
| Damaged re-show | AC-EFHB-08, AC-EFHB-13 | test_enemy_health_bar_3d.gd |
| Death cleanup | AC-EFHB-09, AC-EFHB-14 | test_enemy_health_bar_3d.gd |
| Despawn cleanup | AC-EFHB-10, AC-EFHB-15 | test_enemy_health_bar_3d.gd |
| Debug toggle | AC-EFHB-11 | test_enemy_health_bar_3d.gd |
| All tests pass | AC-EFHB-16 | ci/scripts/run_tests.sh |

---

## 8. NON-FUNCTIONAL REQUIREMENTS

| NFR | Constraint | Rationale |
|---|---|---|
| **Performance** | Health bar updates in < 1ms per enemy | Avoid frame drops with 5+ enemies |
| **Memory** | No orphan health bar nodes; cleanup on despawn | Prevent memory leaks in long-running game |
| **Scalability** | Feature disableable via global toggle | Allow performance testing with/without bars |
| **Maintainability** | Health component and bar are separate scripts | Allow independent testing and reuse |
| **Testability** | All behavior covered by automated tests | Ensure no regression and ease future changes |

---

## END OF SPECIFICATION
