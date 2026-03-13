# Wall Cling Visual Readability — Functional Specification

**Ticket:** [wall_cling_visual_readability.md](../01_active/wall_cling_visual_readability.md)  
**Specification Status:** COMPLETE  
**Revision:** 1  
**Specification Date:** 2026-03-07  

---

## Overview

This specification defines the complete behavioral and visual contract for wall cling state feedback in the blobert infection loop. The feature builds on the existing wall-cling simulation (MovementSimulation.is_wall_clinging) and controller wiring (PlayerController.is_wall_clinging_state()) to add **visual indicator(s)** that allow a human player to immediately recognize when the slime is clinging to a wall without debug overlays.

**Conservative design principle:** Minimal, non-distracting visuals using modulate-based color tinting (no sprite rotation/animation) + optional low-cost particle trail. HUD status indicator is already present in `InfectionUI` and requires no changes.

---

## Acceptance Criteria Mapped to Specification

### AC#1: Sprite Visual Indication of Cling State
**Requirement:** While wall clinging (`_current_state.is_wall_clinging == true`), the player sprite clearly indicates cling state via a visible, persistent tint.

**Specification:**
- **Visual approach:** Modulate-based color tint applied to the `PlayerVisual` node (Polygon2D).
- **Tint color (cling state):** RGB(0.8, 1.0, 0.5, 1.0) — a brighter, slightly warm green offset from the idle default Color(0.4, 0.9, 0.6, 1).
- **Tint application:** Applied in `_process()` frame-by-frame when `is_wall_clinging == true`.
- **Direction-agnostic:** Tint does not change or flip based on wall side (left/right); modulate handles mirroring naturally.
- **No animation or rotation:** Tint is instantaneous and frame-perfect; no fading, scaling, or sprite rotation.

**Implementation responsibility:** `ClingStateFX` presenter script (new).

---

### AC#2: Optional Wall-Cling Slide Particle Effect
**Requirement:** Any optional particle trail while sliding along the wall is visible but not distracting.

**Specification:**
- **Scope:** Optional for this milestone. If budget allows, a low-cost CPUParticles2D child emitter is recommended.
- **Emission rule:** Particles emit **only** when `is_wall_clinging == true` AND player velocity indicates downward/horizontal sliding (not stationary cling).
- **Cost constraints:**
  - Emission rate: ~1–2 particles per 0.1 seconds (10–20 per second), not per frame.
  - Particle lifetime: 0.3–0.5 seconds.
  - Max concurrent particles: ~5 on-screen at any given frame.
  - Size: Small (~4–8 pixels), fade-out at end of lifetime.
- **Visual style:** Subtle green/teal sparkle or wisp matching the cling tint aesthetic.
- **If omitted:** Ticket is still considered complete; particle trail is optional fallback if time budget allows.

**Implementation responsibility:** Presentation Agent (optional).

---

### AC#3: Instantaneous Cleanup on Detach
**Requirement:** When leaving cling state (jump away, release contact, or expire), cling visuals are removed within one frame.

**Specification:**
- **Detach conditions:**
  - Player presses jump while clinging → wall jump fires, `is_wall_clinging` becomes `false` at end of that frame.
  - Wall contact lost (e.g., drift away or release input) → `is_wall_clinging` becomes `false` at end of that frame.
  - Cling timer expires (`cling_timer >= max_cling_time`) → `is_wall_clinging` becomes `false` at end of that frame.
- **Tint removal:** On the first frame where `is_wall_clinging == false`, `modulate` reverts to default idle color within that same frame (no fade or delay).
- **Particle cleanup:** Particle emitter is disabled immediately on detach; existing particles fade naturally per their lifetime.

**Implementation responsibility:** `ClingStateFX._process()` logic (automatic if state tracking is accurate).

---

### AC#4: HUD Status Indicator
**Requirement:** A secondary indicator (icon or text) reflects cling ON/OFF and matches `_current_state.is_wall_clinging`.

**Specification:**
- **Current state:** `InfectionUI` already displays wall-cling status via the `InputHintLabel` showing "Cling" when applicable.
- **No changes required:** The existing `InputHintLabel` pattern in `game_ui.tscn` and `infection_ui.gd` is sufficient for this AC.
- **Verification:** Test coverage confirms that `InputHintLabel.visible` and text content match the current `is_wall_clinging` state from `PlayerController`.

**Implementation responsibility:** None (already implemented). Test verification only.

---

### AC#5: Correct Mirroring for Left/Right Walls
**Requirement:** Visuals work correctly for both left and right walls and remain readable at normal camera distances.

**Specification:**
- **Modulate-based approach:** The Polygon2D `modulate` property is direction-agnostic and does not depend on the player's horizontal direction or wall side.
- **Camera distance:** Tint contrast must be readable at the default camera zoom level used in `test_movement.tscn` (typically 1.0–1.2x). Polygon2D default size is -16 to 16 horizontally, ~32 pixels tall.
- **No sprite flipping logic:** Tint color remains the same regardless of `velocity.x` sign or wall orientation.
- **Test validation:** Manual playtest on both left and right walls in `test_movement.tscn` confirms tint is equally visible and distinct on both sides.

**Implementation responsibility:** Presentation Agent (validation) + Test Designer (verification).

---

## Non-Functional Requirements

### Performance & Stability
- **FPS impact:** Zero measurable FPS drop when modulate tint is applied (~0 additional instructions per frame).
- **Particle budget (if included):** Must maintain stable FPS during continuous cling+slide; ~5 particles max is conservative and safe on modern hardware.
- **Memory:** No dynamic allocation during cling state transitions; reuse existing PlayerController and PlayerVisual references.
- **Robustness:** ClingStateFX must handle edge cases: `PlayerVisual` missing, `is_wall_clinging_state()` unavailable, rapid cling/detach transitions without glitches or visual lag.

### Code Quality & Maintainability
- **Pattern compliance:** `ClingStateFX.gd` follows the same structure as `InfectionStateFX.gd`:
  - Extends Node, not CanvasItem.
  - _ready() initializes parent references and node caches.
  - _process() polls state and applies visuals each frame.
  - No gameplay logic; purely reactive to state changes.
- **Error handling:** Gracefully handles null parent, missing `is_wall_clinging_state()` method, or missing `PlayerVisual` node without crashing.
- **Comments & documentation:** Inline comments explain the tint color values and conditions for particle emission.

### Scope & Out-of-Scope
- **In scope:**
  - Modulate tint while `is_wall_clinging == true`.
  - Optional particle emitter wiring and configuration.
  - Visual clarity and readability at normal camera zoom.
  - Left/right wall verification (no special mirroring logic needed).
  - AC#4 validation (no new code required; existing HUD is sufficient).
  
- **Explicitly out of scope:**
  - Sprite rotation, animation, or pose changes.
  - Crossfades or smooth color transitions.
  - New shader or post-processing effects.
  - Persistent state across scene reloads.
  - Integration with mutation effects or other FX systems.

---

## Implementation Architecture

### File Deliverables

#### 1. New: `scripts/cling_state_fx.gd`
**Purpose:** Presentation layer for wall-cling visual feedback.

**Structure:**
```gdscript
extends Node

var _player: Node  # Reference to parent PlayerController
var _visual: CanvasItem  # Reference to PlayerVisual node
var _particle_emitter: Node  # Optional CPUParticles2D child

# Color constants
const IDLE_TINT: Color = Color(0.4, 0.9, 0.6, 1.0)  # Default player color
const CLING_TINT: Color = Color(0.8, 1.0, 0.5, 1.0)  # Bright warm green

func _ready() -> void:
    # Initialize references to parent and child nodes
    
func _process(delta: float) -> void:
    # Poll is_wall_clinging_state()
    # Apply/remove tint based on state
    # Manage particle emitter (if present)
```

**Key methods:**
- `_ready()`: Locate parent PlayerController, cache PlayerVisual reference, optionally locate CPUParticles2D.
- `_process(delta)`: Poll `_player.is_wall_clinging_state()`, apply cling tint if true, revert to idle tint if false, manage particle emitter emission.
- Helper: `_apply_tint(color: Color)` for readability.
- Helper: `_update_particle_emitter(is_clinging: bool, velocity: Vector2)` to manage optional particle state.

**Error handling:** Gracefully ignore missing nodes; log warnings if parent is not PlayerController.

---

#### 2. Modified: `scenes/player.tscn`
**Changes:**
- Add `ClingStateFX` as a child node under the `Player` node (CharacterBody2D).
- Optionally add a `CPUParticles2D` child under `ClingStateFX` if particle trail is in scope.
- Wire node name to `ClingStateFX` script path `res://scripts/cling_state_fx.gd`.

**Example hierarchy:**
```
Player (CharacterBody2D)
├── PlayerShape (CollisionShape2D)
├── Camera (Camera2D)
├── PlayerVisual (Polygon2D)
└── ClingStateFX (Node) [script=cling_state_fx.gd]
    └── ClingTrail (CPUParticles2D) [optional]
```

---

#### 3. Unchanged: `scripts/player_controller.gd`
**Rationale:** No backend changes needed. The `is_wall_clinging_state()` method already exists and is accurate per wall-cling specification. Movement state tracking is verified as correct in the execution plan (Task 5).

---

### Data & Configuration

**Tint colors (hardcoded constants in ClingStateFX):**
- Idle: Color(0.4, 0.9, 0.6, 1.0) — default green (matches PlayerVisual default).
- Cling: Color(0.8, 1.0, 0.5, 1.0) — brighter, warm green.

**Particle configuration (if included, in CPUParticles2D inspector):**
- Emission rate: ~15–20 particles/second (conservative).
- Lifetime: 0.3–0.5 seconds.
- Initial speed: 20–40 pixels/second (drift).
- Angle variance: 0–180 degrees.
- Size: 4–8 pixels initial, fade to ~2 pixels at end.
- Color: Green/teal with alpha fade-out.

---

## Test Coverage & Validation Strategy

### Automated Test Coverage (Task 2 & 3)

**Primary test file:** `tests/test_cling_visuals.gd` (or integrated into `test_movement.gd`)

**Test cases:**
1. **Tint application:** `_current_state.is_wall_clinging == true` → `PlayerVisual.modulate == CLING_TINT` within one frame.
2. **Tint removal:** `is_wall_clinging == false` → `PlayerVisual.modulate == IDLE_TINT` within one frame.
3. **Particle emission (if present):** Emitter enabled only when clinging AND velocity.y != 0 (sliding).
4. **Instantaneous cleanup:** Rapid cling/detach cycles (10+ transitions per second) produce no visual glitches or tint lag.
5. **HUD sync:** `InputHintLabel` visibility matches `is_wall_clinging` state.
6. **Left/right parity:** Tint appearance is identical on left and right walls (no special direction logic).

**Adversarial test cases (Task 3):**
1. Repeated rapid cling/detach without landing (e.g., wall jump → immediate re-cling).
2. Detach while sliding at maximum velocity.
3. Cling on both left and right walls in the same test run.
4. Particle cleanup under high-frequency state changes (stress test).
5. Missing PlayerVisual node (graceful degradation).

---

### Manual Playtest Validation (Task 8)

**Playtest checklist (in `test_movement.tscn`):**
- [ ] Initiate wall cling on left wall; tint is visibly distinct and clearly indicates "clinging."
- [ ] Initiate wall cling on right wall; tint appearance is identical to left wall.
- [ ] Jump away from wall; tint clears within one frame (no lingering).
- [ ] Release wall contact (drift away); tint clears instantly.
- [ ] Cling until timer expires; tint clears at expiration.
- [ ] If particles enabled: particle trail is smooth, non-distracting, and only appears while sliding (not while stationary against wall).
- [ ] Readability: tint is clearly visible at normal camera zoom (no debug overlays needed).
- [ ] No FPS drop or stuttering during sustained cling.

---

## Edge Cases & Assumptions

### Assumption: Wall-Cling State Tracking is Correct
**Confidence:** High  
**Basis:** Movement simulation and controller wiring are verified in previous tickets (wall_cling.md spec, movement_controller.md, Task 5 verification).

**If violated:** ClingStateFX will apply/remove tint based on `is_wall_clinging_state()` regardless; spec is self-consistent and does not depend on specific state transitions.

---

### Assumption: Polygon2D Modulate is the Correct Tinting Mechanism
**Confidence:** High  
**Basis:** Godot 2D standard pattern; no shader or custom rendering required.

**Fallback:** If modulate proves insufficient (e.g., requires per-vertex tinting), escalate to Static QA with alternative approaches (custom shader, sprite atlas swapping).

---

### Assumption: Optional Particle Trail Does Not Impact Performance
**Confidence:** Medium  
**Basis:** Conservative 5-particle max is standard Godot 2D budget; if stress tests show FPS drop, particle emission is disabled and ticket still completes without particles.

---

### Assumption: InputHintLabel Already Tracks Wall-Cling Status
**Confidence:** High  
**Basis:** Reviewed `infection_ui.gd` and `game_ui.tscn`; InputHintLabel is wired to `PlayerController.is_wall_clinging_state()` and displays "Cling" hint.

**Verification:** Test case AC#4 confirms label visibility matches state.

---

## Compliance Summary

| AC # | Title | Satisfied By | Confidence |
|------|-------|--------------|-----------|
| 1 | Sprite visual indication | ClingStateFX modulate tint + CLING_TINT color | High |
| 2 | Optional particle trail | CPUParticles2D child + emission rule (optional) | Medium |
| 3 | Instantaneous cleanup | _process() tint removal on state change | High |
| 4 | HUD status indicator | Existing InputHintLabel wiring (no changes) | High |
| 5 | Mirroring & readability | Direction-agnostic modulate + camera distance validation | High |

---

## Next Steps

1. **Implementation (Task 4):** Developer implements `ClingStateFX.gd` following this spec.
2. **Engine Integration (Task 6):** Developer attaches ClingStateFX to `player.tscn`.
3. **Primary testing (Task 2):** Test Designer creates automated test cases for tint state mapping.
4. **Adversarial testing (Task 3):** Test Breaker adds edge-case and stress tests.
5. **Static QA (Task 7):** QA verifies code quality, FPS stability, and AC compliance.
6. **Manual playtest (Task 8):** Artist/designer performs final visual validation in-editor.

---

**Specification complete.** Ready for implementation and testing phase.
