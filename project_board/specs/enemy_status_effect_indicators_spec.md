# Enemy Floating Status Effect Indicators Specification

**Ticket:** `project_board/8_milestone_8_enemy_attacks/in_progress/02_enemy_status_effect_indicators.md`  
**Spec Version:** 1.0  
**Spec Author:** Spec Agent  
**Date:** 2026-05-17  
**Stage:** SPECIFICATION  

---

## Executive Summary

This specification defines the display-layer feature for rendering compact status effect indicator badges above the enemy health bar (from ticket 01_enemy_floating_health_bar, COMPLETE). Status indicators communicate active combat states (poison, slow, stun, weaken, infection) so players can make tactical decisions at a glance. The feature is display-only; status effect gameplay logic, trigger mechanisms, and lifecycle management are out of scope.

**Key Design Decisions:**
- Status icons displayed in horizontal container above health bar (leverages ticket 01 Control node architecture)
- Deterministic sort order: `stun > weaken > poison > slow > infection` (enum-backed, testable)
- Max visible count: 5 (configurable via @export)
- Overflow badge: `+N` label where N = count of hidden effects
- Polling or signal-based updates (conservative assumption: polling; signals optional upgrade)
- Fallback icon for unknown effect IDs (no missing-resource errors)

---

## Functional Requirements

### FR1: Status Icon Container Creation and Lifecycle

**Description:** A reusable status effect indicator component integrates with the world-space enemy health bar scene.

**Details:**
- New GDScript class: `EnemyStatusEffectIndicators` (extends `Control`)
- New Godot scene: `scenes/ui/enemy_status_effect_indicators.tscn` with:
  - Root: `Control` node (same layer as `EnemyHealthBar3D` progress bar)
  - Child: `HBoxContainer` for horizontal icon layout
  - Placeholder: Series of `TextureRect` nodes (one per max visible effect) + one `Label` for overflow badge
- Integration point: Status indicator added as child to `EnemyHealthBar3D` Control root, or as sibling positioned above the ProgressBar
- Lifecycle: Created in `_ready()`, parented to health bar scene, cleaned up when enemy dies or is despawned (via parent-child cleanup, no explicit disconnections required unless signals used)
- Initialization: `_ready()` configures container dimensions, creates indicator nodes, sets default visibility/opacity
- Cleanup: When parent health bar is removed, status indicator is removed automatically (Godot parent-child semantics)

**Acceptance Criteria:**
- Scene file `scenes/ui/enemy_status_effect_indicators.tscn` exists and loads without errors
- Script class `EnemyStatusEffectIndicators` compiles and instantiates without errors
- Container is created as a child of `EnemyHealthBar3D` Control node in the scene hierarchy
- Container has a minimum size/dimension suitable for displaying 5 icons (width = 5 × icon_size + spacing)
- Container is visible by default; visibility is toggled when effects are added/removed

**Rationale:** Reusable component pattern (matching health bar ticket 01) ensures maintainability and consistent styling. Control node architecture leverages existing 2D UI layer.

---

### FR2: Status Effect Array Interface Contract (Conservative Assumption)

**Description:** The display layer reads active status effects from the enemy node without managing lifecycle.

**Details:**

**Primary Interface (Assumed, Confirmed via Source):**
- Enemy node exposes **one** of the following (in priority order):
  1. **Array property:** `enemy.active_status_effects` → `Array[String]` or `Array[Dictionary]`
     - If `Array[String]`: each element is an effect ID (e.g., `"poison"`, `"stun"`)
     - If `Array[Dictionary]`: each element is `{ "id": "poison", ... }` with at minimum an `"id"` key
  2. **Meta property:** `enemy.get_meta("active_status_effects")` → same array contract as above
  3. **Getter method:** `enemy.get_active_status_effects()` → returns array of IDs or objects
  
**Fallback Assumption (if no array exists at implementation time):**
- If none of the above exist, display layer polls enemy `EnemyBase` or `EnemyStateMachine` properties:
  - Read `enemy.get_base_state()` → returns `EnemyBase.State` enum (NORMAL=0, WEAKENED=1, INFECTED=2)
  - Map enum state to status effect IDs: `WEAKENED → "weaken"`, `INFECTED → "infection"`, others → empty
  - This fallback is conservative and supports only state-based effects, not separate status effect systems (e.g., poison, slow)

**Gameplay System Context (Confirmed from Source):**
- `EnemyBase` defines state: `NORMAL`, `WEAKENED`, `INFECTED` (ticket: weakening_system_spec.md)
- `EnemyStateMachine` manages transitions: idle → weakened → infected → dead (pure simulation, no side effects)
- Future enhancements may add poison, slow, stun, other effects as separate gameplay systems; this spec future-proofs display layer to read them if available

**Display Layer Behavior:**
- Each `_process()` frame (or on signal callback), status indicator reads enemy active effect array
- Compares new array to last-seen array; if different, calls `_render_indicators()` to update UI
- Never modifies enemy state, never calls methods on enemy (read-only interface)
- Gracefully handles:
  - Null enemy reference (hides all indicators)
  - Empty array (no indicators shown)
  - Array with unknown IDs (falls back to unknown_effect.png for each, no errors)
  - Array with duplicates (renders each unique ID once, or allows duplicates per implementation detail)

**Acceptance Criteria:**
- Display layer successfully reads active effects from enemy node via one of the primary interface methods (priority 1–3)
- If primary interfaces absent, fallback to `EnemyBase.State` enum mapping (priority 4)
- Reading effects does not cause runtime errors or crashes
- Unknown effect IDs render fallback icon, not missing-resource errors
- Null enemy reference handled gracefully (empty indicator set, no crash)

**Rationale:** Conservative assumption avoids blocking on status effect gameplay system; allows display layer to integrate with current `EnemyBase` state while future-proofing for full status effect system. Polling is simpler than signal contracts and doesn't require enemy scripts to define signals.

**Checkpoint Log Entry:**
```
### [M8-SEFI] SPECIFICATION — Status Effect Interface Contract
**Would have asked:** What is the enemy node's contract for exposing active status effects? 
  Array of IDs? Array of objects? Enum flags? Signals? 
**Assumption made:** Conservative polling. 
  1. Try array property: enemy.active_status_effects 
  2. Try meta: enemy.get_meta("active_status_effects") 
  3. Try getter: enemy.get_active_status_effects() 
  4. Fallback: Map enemy EnemyBase.State enum to effect IDs (WEAKENED→"weaken", INFECTED→"infection")
  Status effect gameplay system may not exist yet; this design unblocks display layer and supports future effects.
**Confidence:** MEDIUM (confirmed EnemyBase state exists; full status effect system TBD)
```

---

### FR3: Deterministic Status Effect Sort Order

**Description:** When multiple effects are active simultaneously, they render in a stable, deterministic order.

**Details:**
- Sort order defined as enum-backed priority (lower enum value = higher visual priority, renders first/leftmost):
  - `STUN = 0` (first/leftmost)
  - `WEAKEN = 1`
  - `POISON = 2`
  - `SLOW = 3`
  - `INFECTION = 4` (last/rightmost)
- Stable sort: Identical effect arrays always render in identical order (no random shuffling)
- Unknown effect IDs: Assigned enum value of `999` (renders last, after all known effects)
- Sort method: `_sort_effects(effects: Array) -> Array` (pure function, no side effects)
  - Accepts array of effect IDs (strings) or objects with `id` property
  - Returns sorted array in priority order (stun first)
  - Handles duplicates: if same effect appears twice, both are kept (not deduplicated; overflow badge shows full count)
  - Handles unknown IDs gracefully (assigned lowest priority, no crash)

**Example Sort Scenarios:**
- Input: `["poison", "stun"]` → Output: `["stun", "poison"]`
- Input: `["infection", "slow", "stun", "weaken"]` → Output: `["stun", "weaken", "slow", "infection"]`
- Input: `["stun", "unknown_effect", "poison"]` → Output: `["stun", "poison", "unknown_effect"]`
- Input: `["poison", "poison", "stun"]` → Output: `["stun", "poison", "poison"]` (duplicates preserved for overflow count)

**Acceptance Criteria:**
- `_sort_effects()` method exists and is callable
- Sort always returns stun before weaken before poison before slow before infection
- Identical input arrays always produce identical output (deterministic)
- Unknown effect IDs render at end of list (lowest priority)
- Duplicates are preserved in sorted array (not removed)
- Sort is O(n log n) or better, scales to 100+ effects without performance degradation

**Rationale:** Deterministic, enum-backed order ensures consistency across all clients/runs. Matches ticket wording ("stun > weaken > poison > slow > infection"). Testable and unambiguous.

---

### FR4: Max Visible Count Enforcement and Overflow Badge

**Description:** When active effects exceed max visible count, overflow is represented with a `+N` badge.

**Details:**
- **Max visible count:** `@export max_visible_count: int = 5` (configurable per instance)
  - Default: 5 effects visible simultaneously
  - Boundary values: valid range is 1 to 100 (0 is treated as 1; values > 100 are clamped to 100)
  - Scene-level override: inspector or runtime assignment `status_indicators.max_visible_count = 3`
- **Overflow badge:** If `active_count > max_visible_count`, show a Label with text `"+N"` where `N = active_count - max_visible_count`
  - Example: 7 active effects, max_visible=5 → show first 5 icons, then `"+2"` label
  - Badge is a `Label` node (TextureRect with simple number overlay, or built-in Label)
  - Badge is positioned to the right of the last visible icon
  - Badge visibility tied to overflow condition: if `active_count <= max_visible_count`, badge is hidden
- **Rendering order:**
  1. Sort effects per FR3
  2. Take first `max_visible_count` effects
  3. Render icons for those effects
  4. If hidden effects remain, show `"+N"` badge
  5. Hide any unused icon slots

**Example Rendering Scenarios:**
- Active: 3 effects (stun, weaken, poison), max_visible=5 → render 3 icons, no badge
- Active: 5 effects (stun, weaken, poison, slow, infection), max_visible=5 → render 5 icons, no badge
- Active: 7 effects (2× stun, weaken, poison, slow, infection, unknown), max_visible=5 → render first 5 (stun, stun, weaken, poison, slow), show `"+2"` badge
- Active: 0 effects, max_visible=5 → no icons, no badge

**Acceptance Criteria:**
- `@export max_visible_count` property exists and is configurable
- When `active_count > max_visible_count`, exactly `max_visible_count` icons are visible
- Overflow badge shows correct count: `N = active_count - max_visible_count`
- Overflow badge is hidden when `active_count <= max_visible_count`
- Badge label text updates correctly when effect list changes dynamically (e.g., effect added/removed)
- Boundary: max_visible=1 shows only the highest-priority effect + overflow if > 1 active
- Boundary: max_visible=100 shows all effects (unless edge case of >= 100 active, then shows 100 + badge)

**Rationale:** Bounded visual complexity; prevents UI clutter while allowing players to see overflow count for strategic decisions. Configurable for different UI layouts.

---

### FR5: Real-Time Indicator Updates on Effect State Changes

**Description:** Status indicators update immediately when effects are added, removed, or refreshed.

**Details:**
- **Update trigger:** Status indicator polls enemy active effects in `_process()` (or reacts to signal callback)
- **Detection:** Compare current effect array to `_last_seen_effects`; if different, trigger re-render
- **Update methods:**
  - `_update_from_effects(effects: Array) -> void`: Main update entry point
    - Calls `_sort_effects()` to order effects
    - Calls `_render_indicators()` to rebuild UI
    - Updates `_last_seen_effects` to avoid redundant re-renders
  - `_render_indicators() -> void`: Rebuild UI nodes based on sorted, clamped effect list
    - Clear or reuse existing icon TextureRects
    - For each visible effect, call `_load_icon()` to get texture path and assign to TextureRect
    - Update overflow badge label text and visibility
    - Recalculate container dimensions if needed
  - `_load_icon(effect_id: String) -> Texture2D`: Resolve icon texture for given effect ID
    - Try canonical path: `res://assets/ui/status_effects/{effect_id}.png`
    - If not found, return fallback texture: `res://assets/ui/status_effects/unknown_effect.png`
    - Never return null; if fallback missing, return a placeholder texture (Godot `PlaceholderTexture2D` or simple colored square)
- **Refresh behavior:** If effect appears again (e.g., poison refreshed while already active), indicator stays visible without flashing or animation
- **Performance optimization:** `_last_seen_effects` caching prevents re-render if effect array unchanged
- **Rapid update handling:** Multiple effect changes in rapid succession (e.g., add poison, remove slow, add stun in same frame) are batched into single re-render at end of frame

**Example Update Scenarios:**
- Frame N: effects = [stun, weaken, poison]. Frame N+1: effects = [stun, weaken, poison] (same) → no re-render
- Frame N: effects = [stun, weaken]. Frame N+1: effects = [stun, weaken, poison] (effect added) → re-render with 3 icons
- Frame N: effects = [stun, weaken, poison]. Frame N+1: effects = [stun, poison] (weaken removed) → re-render with 2 icons
- Frame N: effects = [poison]. Frame N+1: effects = [stun, poison, slow, weaken, infection, unknown] (many added) → re-render with first 5 icons + "+1" badge

**Acceptance Criteria:**
- `_process()` calls `_update_from_effects()` each frame
- Icon additions/removals/changes visible within one frame (no lag)
- Effect addition: new icon appears immediately with correct texture
- Effect removal: icon disappears immediately, remaining icons shift left
- Effect refresh (readd): indicator does not flicker or animate (just stays visible)
- Sorting respects FR3 (stun always before weaken, etc.)
- Overflow badge updates correctly when effect count crosses max_visible threshold
- Performance: `_process()` does not allocate large temporary arrays (reuse buffers if possible)

**Rationale:** Real-time updates ensure players see tactical state changes (e.g., poison applied, slow removed) immediately. Caching prevents wasteful re-renders. Batching handles rapid changes gracefully.

---

### FR6: Unknown Effect ID Fallback Handling

**Description:** If an effect ID is not recognized, a safe fallback icon is rendered instead of missing-resource errors.

**Details:**
- **Fallback trigger:** If effect ID (string) is not in the canonical effect ID set (stun, weaken, poison, slow, infection), use fallback
- **Fallback icon path:** `res://assets/ui/status_effects/unknown_effect.png` (@export configurable: `fallback_icon_path`)
- **Loading logic in `_load_icon()`:**
  ```
  func _load_icon(effect_id: String) -> Texture2D:
      var canonical_path = "res://assets/ui/status_effects/{effect_id}.png"
      if ResourceLoader.exists(canonical_path):
          return load(canonical_path) as Texture2D
      else:
          if ResourceLoader.exists(fallback_icon_path):
              return load(fallback_icon_path) as Texture2D
          else:
              return PlaceholderTexture2D.new()  # Safe fallback if fallback also missing
  ```
- **Error handling:** No `push_error()` or warnings logged for unknown effect IDs (silent graceful degradation)
- **Fallback appearance:** A simple, recognizable icon (e.g., gray/neutral color, "?" symbol, or small square placeholder)
- **Tests:** Mock effect IDs like "nonexistent_effect" to verify fallback is rendered

**Acceptance Criteria:**
- Unknown effect ID does not cause runtime error or crash
- Unknown effect ID renders fallback icon (not missing-resource error)
- Fallback icon is visually distinct from known effect icons
- `@export fallback_icon_path` allows scene-level customization
- If fallback path also missing, PlaceholderTexture2D or simple placeholder is used (no crash)
- Multiple unknown IDs render multiple fallback icons (one per unknown effect)

**Rationale:** Defensive programming; future-proofs for new status effect types without breaking display layer. Silent degradation prevents log spam.

---

### FR7: Scene Integration with Enemy Health Bar

**Description:** Status indicator integrates as part of the world-space enemy health bar UI without conflicts or z-order issues.

**Details:**
- **Parent-child relationship:** Status indicator is a child of the `EnemyHealthBar3D` Control node (same node that holds ProgressBar and Timer)
- **Scene hierarchy (expected):**
  ```
  EnemyHealthBar3D (Control root)
  ├── ProgressBar (existing, FR-EH-Bar AC 1)
  ├── HideTimer (existing, FR-EH-Bar AC 3)
  └── EnemyStatusEffectIndicators (NEW, this ticket)
      └── HBoxContainer (icon layout)
          ├── TextureRect (icon 1)
          ├── TextureRect (icon 2)
          ├── ...
          └── Label (overflow badge)
  ```
- **Visual layering:** Both health bar (ProgressBar) and status indicators (TextureRects) are rendered in same Control node, so they share z-order automatically
- **Positioning:** Status indicator positioned above ProgressBar (via Control layout properties or offset)
  - Option 1: `EnemyHealthBar3D` uses VBoxContainer with ProgressBar and StatusIndicator as children → natural stacking
  - Option 2: Manual positioning via `Control.position` offset → +Y offset places status indicator above health bar
  - Implementation choice deferred to Test Designer; both approaches valid
- **Camera-facing (billboard):** Both health bar and status indicators inherit billboard behavior from parent `EnemyHealthBar3D._update_position_and_rotation()` (no additional camera-facing logic needed)
- **Cleanup:** When enemy dies or is despawned, parent health bar is removed; status indicator is removed automatically with it (no explicit cleanup needed)
- **Lifecycle coordination:** Status indicator enabled/disabled follows health bar enabled flag (optional; default both enabled if health bar enabled)

**Acceptance Criteria:**
- Status indicator appears above health bar in rendered output
- Both health bar and status indicators are visible simultaneously
- No z-order conflicts or rendering artifacts
- Status indicator moves with health bar (camera-facing behavior inherited)
- Status indicator cleaned up when health bar is removed (no orphan nodes)
- Scene hierarchy follows expected layout (status indicator is child of health bar or sibling in same container)

**Rationale:** Parent-child relationship ensures consistent cleanup and camera-facing behavior. Reuses health bar's spatial/camera logic, avoiding duplication.

---

## Non-Functional Requirements

### NFR1: Performance and Responsiveness

**Requirement:** Status indicator updates must not cause frame rate degradation or introduce input latency.

**Details:**
- `_process()` update is O(n) where n = number of active effects; acceptable for n <= 100
- Icon texture loading is cached (once loaded, reused across frames; no redundant `load()` calls)
- `_render_indicators()` reuses existing TextureRect nodes (does not create/destroy each frame)
- Overflow badge label updated in-place (no re-allocation)
- No async tasks, coroutines, or I/O in hot path
- Recommended: maintain 60 FPS during active status effect changes

**Measurement:** In test scenarios with 100+ concurrent status indicators and rapid effect changes, frame time should not exceed 16ms (60 FPS baseline).

---

### NFR2: Determinism and Idempotency

**Requirement:** Repeated or equivalent operations must produce identical results.

**Details:**
- `_sort_effects()` is a pure function: given same input array, always returns same sorted array (no randomness, no side effects)
- `_render_indicators()` is idempotent: calling twice with same effect array produces identical UI state
- Multiple calls to `_load_icon()` with same effect ID return same texture (or consistent fallback)
- Effect array mutations (add/remove/refresh) always converge to valid state (no partial updates or inconsistent rendering)
- Edge case: if effect array changes mid-`_process()`, indicator uses array state at start of frame (no race conditions)

**Test examples:**
- Sort identical arrays multiple times; verify output is identical
- Render same effect list 10 times; verify UI state unchanged after first render
- Remove and re-add same effect; verify rendering consistent before/after

---

### NFR3: Robustness and Null Safety

**Requirement:** Null or invalid inputs must not cause crashes.

**Details:**
- Null enemy reference: indicator hides all icons, shows no overflow badge
- Empty effect array: no icons shown, no overflow badge shown
- Null effect array (instead of empty): treated as empty (no crash)
- Invalid effect ID (string): renders fallback icon
- Missing TextureRect or HBoxContainer nodes in scene: gracefully handle missing nodes (skip rendering, no crash)
- Rapid enemy despawn (while indicator updating): no crash, indicator cleaned up in next frame
- Max_visible = 0: clamped to 1 (always show at least 1 icon if 1+ effects active)

**Test coverage:**
- Null enemy, empty effects, invalid IDs, missing nodes, despawn mid-update

---

### NFR4: Configuration and Tuning

**Requirement:** Visual and behavioral parameters must be configurable via `@export` properties.

**Details:**
- `@export enabled: bool = true` (feature toggle, matches health bar AC 6)
- `@export max_visible_count: int = 5` (max simultaneously visible effects)
- `@export icon_size: Vector2 = Vector2(32, 32)` (pixel dimensions of each TextureRect)
- `@export spacing: int = 4` (pixels between icons in HBoxContainer)
- `@export fallback_icon_path: String = "res://assets/ui/status_effects/unknown_effect.png"`
- All @export vars live-update: changing in inspector while game is running applies immediately (no restart needed)
- Default values chosen for clarity and readability at standard camera distance

**Tuning examples:**
- Set `max_visible_count = 3` to show only top-3 effects
- Set `icon_size = Vector2(24, 24)` for smaller icons (more fit in viewport)
- Set `spacing = 8` for wider gaps between icons

---

### NFR5: Code Quality and Maintainability

**Requirement:** Implementation follows project conventions and existing health bar patterns.

**Details:**
- Class name: `EnemyStatusEffectIndicators` (CapitalCase, descriptive)
- Private methods prefixed with `_` (matching health bar script style)
- Public methods: `update_from_enemy()`, `set_active_effects()`, `on_effect_added()`, `on_effect_removed()` (matching health bar API)
- Internal state variables: `_last_seen_effects`, `_enemy`, `_icon_container`, `_overflow_badge` (clear naming)
- No unexplained tuning literals; all constants named (e.g., `MAX_EFFECTS_HARD_LIMIT = 1000`)
- Comments on complex logic (sort algorithm, overflow badge calculation)
- GDScript linter passes: `task hooks:gd-review` completes with no errors

---

## Acceptance Criteria (Detailed, Testable)

### AC1: Status Icon Container Initialization
- **Criterion:** Status indicator scene (`enemy_status_effect_indicators.tscn`) loads without errors; script compiles.
- **Test:** Load scene in Godot, verify no import/compilation errors in editor console.
- **Evidence:** Scene file exists at canonical path; test instantiates scene and calls `_ready()` without errors.

### AC2: Multi-Effect Render Order (Deterministic Sort)
- **Criterion:** When 3+ effects are active, they render in stun > weaken > poison > slow > infection order.
- **Test:** Create status indicator with effects array `["poison", "stun", "slow", "weaken"]`; verify rendered left-to-right as `["stun", "weaken", "poison", "slow"]`.
- **Evidence:** Visual inspection or automated test: verify icon 0 is stun, icon 1 is weaken, icon 2 is poison, icon 3 is slow.

### AC3: Overflow Badge Behavior
- **Criterion:** When active effects exceed `max_visible_count`, an overflow badge displays the hidden count.
- **Test:** Set max_visible=2 and active effects to `["stun", "weaken", "poison", "slow"]` (4 effects).
- **Expected:** 2 icons visible (stun, weaken); overflow badge shows "+2".
- **Evidence:** Icon count == min(active_count, max_visible); badge text == (active_count - max_visible).

### AC4: Fallback Icon for Unknown Effects
- **Criterion:** Unknown effect IDs render a safe fallback icon, not missing-resource errors.
- **Test:** Set active effects to `["poison", "nonexistent_effect", "stun"]`.
- **Expected:** 3 icons visible: poison icon, fallback icon (for nonexistent), stun icon. No console errors.
- **Evidence:** No `ResourceLoader` or missing-resource errors; fallback texture is loaded successfully.

### AC5: Real-Time Effect Add/Remove/Refresh Updates
- **Criterion:** Indicator visuals update within one frame when effects are added, removed, or refreshed.
- **Test:** Start with `["stun"]` active. Next frame, update to `["stun", "weaken", "poison"]` (added 2).
- **Expected:** All 3 icons visible after update; rendering lag <= 1 frame.
- **Evidence:** Icon count changes from 1 to 3; layout updates synchronously in same frame.
- **Refresh test:** Active effects `["poison"]` → refresh poison (same effect) → poison icon remains visible without animation.

### AC6: Max Visible Count Enforcement
- **Criterion:** Exactly `max_visible_count` icons are shown when active effects >= max_visible.
- **Test:** Set max_visible=5 and active effects to `["stun", "weaken", "poison", "slow", "infection", "unknown1", "unknown2"]` (7 effects).
- **Expected:** 5 icons visible (the sorted top-5); overflow badge shows "+2".
- **Evidence:** Child node count (visible icons) == 5; badge text == "2".

### AC7: Integration with Health Bar (No Z-Order Issues)
- **Criterion:** Status indicator and health bar are both visible simultaneously above the enemy, with correct visual layering.
- **Test:** Spawn enemy with health bar + status indicators enabled; verify both rendered above enemy head.
- **Expected:** Health bar visible (ProgressBar fill); status icons visible above it; no occlusion or z-fighting.
- **Evidence:** Screenshot/visual test at standard camera distance shows both health bar and icons in correct position and depth.

### AC8: Null Enemy Reference Graceful Handling
- **Criterion:** If enemy reference is null, indicator hides all icons without crashing.
- **Test:** Set `status_indicator._enemy = null`; call `_update_from_effects()`.
- **Expected:** No icons visible; no overflow badge; no error in console.
- **Evidence:** Container visible = false, or icon TextureRects all hidden.

### AC9: Empty Effect List Handling
- **Criterion:** If active effects array is empty, no icons or overflow badge displayed.
- **Test:** Call `_update_from_effects([])`.
- **Expected:** No icons visible; no overflow badge.
- **Evidence:** All icon TextureRects hidden; overflow badge label hidden.

### AC10: Boundary Value Tests
- **Criterion:** Edge cases for max_visible_count, effect count, and icon size are handled correctly.
- **Test variants:**
  - max_visible = 1 with 5 active effects → 1 icon + "+4" badge
  - max_visible = 100 with 50 active effects → 50 icons, no badge
  - icon_size = (0, 0) → no visual distortion, icons still positioned correctly
  - active effects = 1000 → render first 5 (or max_visible), overflow badge shows "+995"
- **Expected:** No crashes; correct icon count and overflow calculation.
- **Evidence:** Each variant produces expected UI state without errors.

---

## Risk & Ambiguity Analysis

### Risk 1: Status Effect Interface Not Yet Defined (HIGH SEVERITY)

**Risk:** Status effect gameplay system (poison, slow, stun effects) may not exist yet. Enemy node may not expose active effects in any form.

**Impact:** 
- Without a defined interface, implementation must make assumptions about where/how to read effects from enemy.
- Tests cannot be written until fixture interface is known.
- Implementation may need rework if actual interface differs from assumption.

**Mitigation (Documented in FR2):**
- Conservative polling approach: try multiple interface methods (array property → meta property → getter method) in priority order.
- Fallback to `EnemyBase.State` enum (NORMAL, WEAKENED, INFECTED) to map to effect IDs.
- This approach unblocks display layer without gating on full gameplay system.
- Checkpoint assumption documented; Test Designer will create mock enemy fixture with assumed interface.

**Confidence:** MEDIUM (EnemyBase state system confirmed; full status effect system TBD)

---

### Risk 2: Icon Assets Not Available (MEDIUM SEVERITY)

**Risk:** PNG files for poison, slow, stun, weaken, infection icons may not exist at `res://assets/ui/status_effects/`.

**Impact:** 
- Display layer attempts to load missing textures; fallback required.
- Tests must mock/provide placeholder textures.
- Visual appearance may be subpar if only fallback icons used.

**Mitigation:**
- Fallback icon path configured (@export) and graceful loading logic in `_load_icon()` (FR6).
- Tests use placeholder textures (or create simple colored squares via Godot primitives).
- Placeholder icons acceptable initially per ticket scope note: "Precise icon art polish can iterate later; placeholders are acceptable initially."

**Confidence:** MEDIUM (assets not confirmed; fallback strategy in place)

---

### Risk 3: Performance Impact of Frequent Re-Renders (MEDIUM SEVERITY)

**Risk:** If effect array changes every frame and `_render_indicators()` is not efficient, performance could degrade.

**Impact:** 
- Frame time increases with many concurrent status indicators.
- Gameplay responsiveness affected.

**Mitigation (NFR1):**
- Implement `_last_seen_effects` cache to skip re-render if array unchanged.
- Reuse TextureRect nodes instead of creating/destroying each frame.
- Tests verify caching works (measure calls to `_render_indicators()` and verify idempotency).

**Confidence:** HIGH (mitigation straightforward and testable)

---

### Risk 4: Scene Hierarchy Changes Break Integration (MEDIUM SEVERITY)

**Risk:** If enemy or health bar scene structure changes (e.g., ProgressBar moved, parent node renamed), attachment logic may break.

**Impact:** 
- Status indicator fails to attach to health bar.
- Orphan UI nodes created.
- Display layer may not render.

**Mitigation:**
- Leverage parent-child lifecycle (Godot semantics); no hardcoded node path queries.
- Scene integration verified in tests (Integration stage, Task 6).
- If changes needed, STATIC_QA reviews scene hierarchy for consistency.

**Confidence:** HIGH (parent-child design is robust)

---

### Risk 5: Determinism of Sort Order Under Rapid Mutations (MEDIUM SEVERITY)

**Risk:** If effect array is mutated rapidly (add/remove/refresh in quick succession), sort order might become non-deterministic or inconsistent.

**Impact:** 
- Effects render in inconsistent order across frames.
- Player confusion about effect priorities.
- Tests may fail non-deterministically.

**Mitigation (NFR2):**
- `_sort_effects()` is pure function: no side effects, deterministic output.
- `_last_seen_effects` caching ensures render is called once per unique array state, not per mutation.
- Tests verify determinism: identical arrays always sort identically.

**Confidence:** HIGH (pure function design ensures determinism)

---

### Ambiguity 1: Signals vs Polling for Real-Time Updates

**Ambiguity:** Should status indicator subscribe to enemy signals (e.g., `status_added`, `status_removed`) or poll each frame?

**Resolution (Documented in FR2, Checkpoint):**
- Assume polling (conservative, does not require enemy scripts to define signals).
- Design supports both: if signals are available on enemy, they can be connected; polling is fallback/primary.
- Implementation uses polling by default; signal subscription is optional enhancement.

**Confidence:** MEDIUM (both approaches valid; polling safer without signal contract)

---

### Ambiguity 2: Duplicate Effects in Array

**Ambiguity:** If same effect ID appears twice in active effects array (e.g., two poison instances), should indicator show one icon or two?

**Resolution (Documented in FR3, FR4):**
- Preserve duplicates: show multiple icons if array contains duplicates.
- Example: `["stun", "stun", "poison"]` → render 2 stun icons + 1 poison icon.
- Overflow badge count includes duplicates: `active_count = 3`, so if max_visible=2, badge shows "+1".
- Rationale: Future status effect system may need to display duplicate effects (e.g., multiple poison instances with different durations/intensities).

**Confidence:** HIGH (approach is explicit, testable, supports future features)

---

### Ambiguity 3: Effect Array Ordering (Input to Sort)

**Ambiguity:** Is the input effect array pre-sorted, or in arbitrary order? Does sort order depend on array order or only on effect ID priority?

**Resolution (Documented in FR3):**
- Input array order is arbitrary (no assumption about input order).
- Sort uses only effect ID priority (enum-backed), not input array position.
- Identical effect IDs in input array remain in same relative order post-sort (stable sort).

**Confidence:** HIGH (specified in FR3; stable sort is standard)

---

## Testing Strategy (High-Level)

### Primary Test Suite (Task 2: TEST_DESIGN)
- **Focus:** Core functionality, happy-path scenarios, acceptance criteria coverage
- **Scope:** 15–20 tests covering:
  - Container initialization (lifecycle, scene loading)
  - Multi-effect sort order (3+ effect combinations)
  - Overflow badge (visible/hidden, count correct)
  - Fallback icon (unknown effects)
  - Real-time updates (add/remove/refresh)
  - Max visible count enforcement
  - Health bar integration (visual layering, camera-facing)
  - Edge cases (null enemy, empty array)

### Adversarial Test Suite (Task 3: TEST_BREAK)
- **Focus:** Boundary values, negative cases, robustness
- **Scope:** 20–30 tests covering:
  - Null/invalid enemy references
  - Malformed effect data (missing ID, invalid type, duplicates)
  - Extreme cases (100+ effects, very rapid changes)
  - Invalid icon paths, asset load failures
  - Sort stability under rapid mutations
  - Memory/performance (many concurrent indicators)
  - Boundary max_visible values (0, 1, 100)
  - Overflow badge edge cases (hidden count = 0, 1, 1000)
  - Determinism (identical sequences produce identical output)
  - State machine (empty → 1 → many → empty transitions)

### Total Coverage: 35–50 tests, organized by concern (lifecycle, sorting, overflow, fallback, integration, robustness)

---

## Implementation Checklist

### Code & Scene Files
- [ ] Scene file: `scenes/ui/enemy_status_effect_indicators.tscn` (Control root, HBoxContainer, icon slots, badge label)
- [ ] Script file: `scripts/ui/enemy_status_effect_indicators.gd` (class `EnemyStatusEffectIndicators`, methods: `_ready()`, `_process()`, `update_from_enemy()`, `set_active_effects()`, `_update_from_effects()`, `_render_indicators()`, `_sort_effects()`, `_load_icon()`, `_update_overflow_badge()`)
- [ ] Test suite files: Primary test file (15–20 tests), Adversarial test file (20–30 tests)
- [ ] Integration: Status indicator added to `EnemyHealthBar3D` scene or wired up via script

### @export Configuration Properties
- [ ] `enabled: bool = true`
- [ ] `max_visible_count: int = 5`
- [ ] `icon_size: Vector2 = Vector2(32, 32)`
- [ ] `spacing: int = 4`
- [ ] `fallback_icon_path: String = "res://assets/ui/status_effects/unknown_effect.png"`

### Acceptance Criteria
- [ ] AC1: Scene loads without errors
- [ ] AC2: Multi-effect render order correct (stun > weaken > poison > slow > infection)
- [ ] AC3: Overflow badge shows correct hidden count
- [ ] AC4: Fallback icon used for unknown effects (no missing-resource errors)
- [ ] AC5: Real-time updates on effect add/remove/refresh (within 1 frame)
- [ ] AC6: Max visible count enforced correctly
- [ ] AC7: Integration with health bar (both visible, correct layering)
- [ ] AC8: Null enemy handled gracefully (no crash, hides icons)
- [ ] AC9: Empty effect array handled correctly (no icons/badge)
- [ ] AC10: Boundary values tested (max_visible edge cases, effect count extremes)

### Quality Gates
- [ ] GDScript linter passes: `task hooks:gd-review`
- [ ] All primary + adversarial tests pass: `timeout 300 godot --headless -s tests/run_tests.gd`
- [ ] Godot import refresh successful: `timeout 120 godot --headless --import`
- [ ] No orphan UI nodes on enemy despawn
- [ ] No frame time degradation at 60 FPS baseline

---

## Traceability Matrix

| AC # | AC Description | Primary Test(s) | Adversarial Test(s) | FR(s) | NFR(s) |
|------|---|---|---|---|---|
| AC1 | Scene loads without errors | test_scene_loads | test_null_scene | FR1 | NFR5 |
| AC2 | Multi-effect render order | test_sort_order_multi_effect, test_sort_order_all_effects | test_sort_stability_rapid, test_unknown_effect_sort_order | FR3 | NFR2 |
| AC3 | Overflow badge shows correct count | test_overflow_badge_visible, test_overflow_badge_text | test_overflow_boundary_1, test_overflow_large_list | FR4 | NFR2 |
| AC4 | Fallback icon for unknown effects | test_fallback_icon_unknown_effect | test_fallback_icon_missing_asset, test_fallback_icon_duplicate_unknown | FR6 | NFR3 |
| AC5 | Real-time updates on effect changes | test_effect_add, test_effect_remove, test_effect_refresh | test_rapid_effect_cycles, test_concurrent_updates | FR5 | NFR1, NFR2 |
| AC6 | Max visible count enforced | test_max_visible_exactly_n | test_max_visible_boundary_0, test_max_visible_boundary_100 | FR4 | NFR2 |
| AC7 | Integration with health bar | test_integration_health_bar_position, test_integration_no_z_order_conflicts | test_integration_health_bar_despawn | FR7 | NFR3 |
| AC8 | Null enemy gracefully handled | test_null_enemy_hides_icons | test_null_enemy_no_crash | FR2 | NFR3 |
| AC9 | Empty effect array handled | test_empty_effects_no_icons, test_empty_effects_no_badge | test_empty_effects_repeated | FR5 | NFR3 |
| AC10 | Boundary values tested | test_boundary_max_visible_1, test_boundary_effect_count_1 | test_boundary_max_visible_100, test_boundary_effect_count_1000 | FR4, FR5 | NFR1, NFR3 |

---

## Outstanding Items & Deferred Decisions

### Items for Test Designer (Task 2)
1. Confirm assumed status effect interface (FR2) by examining actual enemy node or mocking it in tests.
2. Create test fixture with mock enemy node exposing `active_status_effects` array (or appropriate fallback).
3. Decide: polling in `_process()` or signal-based subscription (both supported by spec).

### Items for Implementation (Task 4)
1. Verify asset paths: `res://assets/ui/status_effects/{effect_id}.png` and fallback path; create placeholders if needed.
2. Integrate status indicator with `EnemyHealthBar3D` (parent-child relationship or wired initialization).
3. Handle the exact status effect interface (array property, meta, getter, or enum fallback) once actual enemy contract confirmed.

### Items for Integration Testing (Task 6)
1. Verify status indicators render above health bar in live game scenario (3D scene with spawned enemies).
2. Confirm no performance degradation at 60 FPS with 10+ concurrent enemies with status indicators.
3. Verify cleanup on enemy death/despawn (no orphan UI nodes).

### Future Enhancements (Out of Scope for This Ticket)
1. Tooltip or hover text showing effect details (specified as out-of-scope in ticket).
2. Per-effect duration countdown text (out-of-scope).
3. Dynamic sort order based on remaining duration or severity (this spec uses static sort order).
4. Animated transitions (fade/slide) when effects are added/removed (not required; instant updates acceptable).
5. Audio feedback on effect state changes (out-of-scope for display layer).

---

## Specification Sign-Off

**Spec Version:** 1.0  
**Status:** COMPLETE  
**Ambiguities Resolved:** 6 (checkpoint assumptions documented, all blocking issues addressed)  
**No TBD Sections:** ✓  
**Acceptance Criteria Count:** 10 (detailed, measurable, testable)  
**Functional Requirements:** 7 (FR1–FR7)  
**Non-Functional Requirements:** 5 (NFR1–NFR5)  

---

## Appendix: Checkpoint Assumptions Summary

| # | Ambiguity | Assumption | Confidence | Status |
|---|---|---|---|---|
| 1 | Status effect interface contract | Conservative polling: try array property → meta → getter method → fallback to EnemyBase.State enum | MEDIUM | DOCUMENTED |
| 2 | Signal vs polling updates | Assume polling (conservative); design supports both; polling is primary | MEDIUM | DOCUMENTED |
| 3 | Icon asset paths | Assume `res://assets/ui/status_effects/{effect_id}.png`; fallback to configurable unknown icon | MEDIUM | DOCUMENTED |
| 4 | Deterministic sort order | Static enum-backed policy (stun > weaken > poison > slow > infection) | HIGH | FROZEN |
| 5 | Overflow badge count | Show "+N" where N = (active_count - max_visible) | HIGH | FROZEN |
| 6 | Duplicate effects in array | Preserve duplicates; show multiple icons if array contains duplicates | HIGH | DOCUMENTED |

---

**Prepared by:** Spec Agent  
**Date:** 2026-05-17  
**Ready for:** Test Designer Agent (Task 2: TEST_DESIGN)
