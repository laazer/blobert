# Basic camera follow

**Epic:** Milestone 1 – Core Movement Prototype
**Status:** In Progress

---

## Description

Camera follows the slime (main body) so the player always has a clear view of the character. Optional: soft follow, dead zone, or bounds so it feels good in an empty room.

## Acceptance criteria

- [ ] Camera follows slime position (or designated follow target)
- [ ] Follow is smooth (no jitter) and keeps slime on screen
- [ ] Optional: configurable dead zone or bounds so camera doesn't move for tiny movements
- [ ] Playable for 10 minutes in empty room without camera issues
- [ ] Camera behavior is human-playable in-editor: slime, environment, and camera framing remain clearly visible and readable without debug overlays

---

## Dependencies

- M1-001 (movement_controller) — COMPLETE

---

## Execution Plan

### Overview

The existing `Camera2D` node is already a child of the `Player` CharacterBody2D in `scenes/test_movement.tscn`. It currently provides exact (zero-lag) following with no configuration. This plan enhances that node in-place using Godot's built-in Camera2D properties plus a thin configuration script (`scripts/camera_follow.gd`), owned by the Presentation Agent. No custom math, no simulation layer, and no new scene node is required.

The approach uses:
- `Camera2D.position_smoothing_enabled = true` + `position_smoothing_speed` for smooth follow (no jitter, no custom lerp)
- `Camera2D.drag_horizontal_enabled / drag_vertical_enabled` + drag margin properties for dead zone behaviour
- `Camera2D.limit_*` properties for level-bounds clamping
- All parameters `@export`-annotated for inspector tuning

Because this feature is pure Godot node wiring with no engine-agnostic simulation, there is no headless unit-testable logic layer. Verification is done via GDScript syntax validation (`godot --headless --check-only`) and a manual 10-minute play session.

---

### Task Table

| # | Task Objective | Assigned Agent | Input | Expected Output | Dependencies | Success Criteria | Risks / Assumptions |
|---|----------------|----------------|-------|-----------------|--------------|-----------------|---------------------|
| 1 | Write the camera follow configuration spec | Spec Agent | This ticket; scene file `scenes/test_movement.tscn`; Godot 4 Camera2D property reference; context from CHECKPOINTS.md | `agent_context/projects/blobert/specs/camera_follow_spec.md` covering: exported parameters, their types, defaults, valid ranges, Camera2D property mapping, and scene-wiring contract | None | Spec document exists; all acceptance criteria are addressed by at least one SPEC entry; no ambiguous parameter defaults remain | Drag margin property names differ between Godot 4.0 and 4.x; spec must confirm exact property names (e.g. `drag_left_margin` vs `drag_horizontal_offset`) |
| 2 | Design tests for camera follow script | Test Designer Agent | `camera_follow_spec.md` from Task 1 | `tests/test_camera_follow.gd` — headless-safe tests for any pure logic in `camera_follow.gd` (e.g. limit clamping helper, parameter validation); plus an explicit manual verification checklist appended to the spec for in-editor checks | Task 1 | Test file passes `godot --headless --check-only` syntax validation; manual checklist covers: smooth follow visible, no jitter for 10 minutes, dead zone (small movements do not move camera), bounds prevent camera leaving floor area | Camera2D smoothing and drag are engine-driven — most behavior cannot be tested headlessly; tests cover only any pure GDScript helper functions in the script |
| 3 | Write adversarial / edge-case tests for camera follow | Test Breaker Agent | `camera_follow_spec.md` from Task 1; `tests/test_camera_follow.gd` from Task 2 | `tests/test_camera_follow_adversarial.gd` — adversarial tests targeting: zero smoothing speed, extreme limit values, NaN/@export parameter assignment, limit_left > limit_right inversion, zero-size dead zone | Tasks 1, 2 | Adversarial test file passes syntax validation; at least 5 distinct edge-case scenarios covered; each test has a comment explaining what implementation flaw it targets | If `camera_follow.gd` has no pure logic (all wiring), adversarial file may contain only structural/syntax-safe stubs — that is acceptable |
| 4 | Implement `scripts/camera_follow.gd` and wire scene | Presentation Agent | `camera_follow_spec.md` from Task 1; `tests/test_camera_follow.gd` + `tests/test_camera_follow_adversarial.gd` from Tasks 2–3; `scenes/test_movement.tscn` | `scripts/camera_follow.gd` implementing the spec; `scenes/test_movement.tscn` updated to attach script to the Camera node and set exported properties; all tests pass syntax validation | Tasks 1, 2, 3 | `godot --headless --check-only` exits 0; `tests/run_tests.gd` updated to include camera follow suites and runner exits 0; Camera node in scene has script attached with non-default smoothing and drag margins visible in inspector | Scene file uses text format — direct `[node]` property edits are fragile; agent must verify property names against Godot 4 source; do not break existing Player/Floor node structure |
| 5 | Static QA pass on all camera follow files | Static QA Agent | `scripts/camera_follow.gd`; `scenes/test_movement.tscn`; `tests/test_camera_follow.gd`; `tests/test_camera_follow_adversarial.gd` | QA report (appended to ticket as a comment block or to `agent_context/projects/blobert/qa/`); all files corrected to pass `godot --headless --check-only` with zero errors/warnings | Task 4 | `godot --headless --check-only` exits 0 with no warnings on all modified files; typed GDScript enforced (no untyped variables); `@export` parameters use correct type hints; no dead code | Static QA has no in-game play capability — visual smoothing quality cannot be verified here |
| 6 | Integration verification and 10-minute manual session | Presentation Agent (or Generalist Agent if human input required) | All files from Tasks 4–5; Godot project at `/Users/jacobbrandt/workspace/blobert` | Ticket acceptance criteria checkboxes filled in; Validation Status updated; any remaining issues logged as Blocking Issues | Task 5 | All four acceptance criteria checked off; agent documents that it ran the test scene for 10 simulated minutes (or maximum feasible headless duration) without NaN positions or camera drift; if full manual play is impossible headlessly, checklist items are marked with `[manual]` and escalated to Human | True 10-minute human play test cannot be done by an AI agent headlessly; this task may set status to Needs Clarification if the session requirement is strictly human |

---

### File Ownership

| File | Owner Agent | Action |
|------|-------------|--------|
| `scripts/camera_follow.gd` | Presentation Agent | Create |
| `scenes/test_movement.tscn` | Presentation Agent | Modify (attach script to Camera node, set properties) |
| `tests/test_camera_follow.gd` | Test Designer Agent | Create |
| `tests/test_camera_follow_adversarial.gd` | Test Breaker Agent | Create |
| `tests/run_tests.gd` | Presentation Agent (Task 4) | Modify (add camera follow suites) |
| `agent_context/projects/blobert/specs/camera_follow_spec.md` | Spec Agent | Create |

---

### Design Decisions Locked by Planner

1. **Smoothing mechanism:** Godot built-in `Camera2D.position_smoothing_enabled` + `position_smoothing_speed`. No custom lerp script. Rationale: zero custom math, no risk of drift or NaN accumulation.
2. **Dead zone mechanism:** Godot built-in `Camera2D.drag_horizontal_enabled` / `drag_vertical_enabled` + drag margin properties. No custom GDScript dead zone check.
3. **Bounds mechanism:** `Camera2D.limit_left`, `limit_right`, `limit_top`, `limit_bottom` properties. Defaults: unclamped (Godot default values: -10000000 / 10000000) until a level bounds resource is defined. All four limits are `@export` parameters on the script.
4. **Script architecture:** `camera_follow.gd` extends `Camera2D`, sets its own properties in `_ready()` from `@export` vars. No Node references, no signal wiring required for basic follow.
5. **No simulation layer:** Camera is a Presentation concern. There is no engine-agnostic simulation for camera position — this would be over-engineering for a built-in feature.

---

### Parameter Defaults (Recommended — Spec Agent to confirm)

| Parameter | Type | Default | Godot Property Mapped |
|-----------|------|---------|----------------------|
| `smoothing_enabled` | `bool` | `true` | `position_smoothing_enabled` |
| `smoothing_speed` | `float` | `5.0` | `position_smoothing_speed` |
| `drag_horizontal` | `bool` | `true` | `drag_horizontal_enabled` |
| `drag_vertical` | `bool` | `false` | `drag_vertical_enabled` |
| `drag_left_margin` | `float` | `0.2` | `drag_left_margin` |
| `drag_right_margin` | `float` | `0.2` | `drag_right_margin` |
| `drag_top_margin` | `float` | `0.2` | `drag_top_margin` |
| `drag_bottom_margin` | `float` | `0.2` | `drag_bottom_margin` |
| `limit_left` | `int` | `-10000000` | `limit_left` |
| `limit_right` | `int` | `10000000` | `limit_right` |
| `limit_top` | `int` | `-10000000` | `limit_top` |
| `limit_bottom` | `int` | `10000000` | `limit_bottom` |

---

## Specification

Full specification: `/Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/camera_follow_spec.md`

### SPEC-37: File and Class Structure
`scripts/camera_follow.gd` — line 1: `class_name CameraFollow`, line 2: `extends Camera2D`. Contains only `@export` variable declarations and one `func _ready() -> void:`. No other functions, signals, or imports. Must pass `godot --headless --check-only` with zero diagnostics.

### SPEC-38: Exported Configuration Parameters
Twelve `@export`-annotated, statically-typed variables with the following exact declarations and defaults:

| Declaration | Default | Maps to Camera2D property |
|---|---|---|
| `@export var smoothing_enabled: bool = true` | `true` | `position_smoothing_enabled` |
| `@export var smoothing_speed: float = 5.0` | `5.0` | `position_smoothing_speed` |
| `@export var drag_horizontal: bool = true` | `true` | `drag_horizontal_enabled` |
| `@export var drag_vertical: bool = false` | `false` | `drag_vertical_enabled` |
| `@export var drag_left_margin: float = 0.2` | `0.2` | `drag_left_margin` |
| `@export var drag_right_margin: float = 0.2` | `0.2` | `drag_right_margin` |
| `@export var drag_top_margin: float = 0.2` | `0.2` | `drag_top_margin` |
| `@export var drag_bottom_margin: float = 0.2` | `0.2` | `drag_bottom_margin` |
| `@export var limit_left: int = -10000000` | `-10000000` | `limit_left` |
| `@export var limit_right: int = 10000000` | `10000000` | `limit_right` |
| `@export var limit_top: int = -10000000` | `-10000000` | `limit_top` |
| `@export var limit_bottom: int = 10000000` | `10000000` | `limit_bottom` |

### SPEC-39: `_ready()` Initialization
`func _ready() -> void:` assigns each of the twelve `@export` variables to the corresponding Camera2D built-in property. Exactly twelve assignment statements, one per export. No local variables, no function calls, no conditionals. Mapping: `position_smoothing_enabled = smoothing_enabled`, `position_smoothing_speed = smoothing_speed`, `drag_horizontal_enabled = drag_horizontal`, `drag_vertical_enabled = drag_vertical`, and the eight coincident-name properties (e.g., `drag_left_margin = drag_left_margin`).

### SPEC-40: Smoothing Behavior
Implemented exclusively via Godot built-in `position_smoothing_enabled` + `position_smoothing_speed`. No custom lerp or `_process()` override. Default `smoothing_speed = 5.0` produces smooth lag at 60fps with no jitter. Behavior verified manually (MAN-01, MAN-02, MAN-05).

### SPEC-41: Dead Zone / Drag Margin Behavior
Implemented via Godot built-in drag margin system. Default: horizontal drag enabled at 0.2 margin, vertical drag disabled. Margins are floats in `[0.0, 1.0]`. Engine clamps margins to this range. Behavior verified manually (MAN-03, MAN-09).

### SPEC-42: Level Bounds Limiting
Implemented via Godot built-in `limit_*` properties (integer pixel coordinates). Defaults match Godot's unclamped values (`-10000000` / `10000000`). No script validation of limit relationships. Behavior verified manually (MAN-04).

### SPEC-43: Scene Wiring
`scenes/test_movement.tscn` is modified to: (1) add `[ext_resource type="Script" path="res://scripts/camera_follow.gd" id="2_camfollow"]` in the header, (2) add `script = ExtResource("2_camfollow")` to the `[node name="Camera" type="Camera2D" parent="Player"]` block, (3) increment `load_steps` from `5` to `6`. No other nodes are modified. Scene passes `godot --headless --check-only` after modification.

### SPEC-44: Manual Acceptance Checklist
Six manual checklist items (MAN-01 through MAN-06) defined in the full spec at `camera_follow_spec.md`. Each item is marked `[PASS]`, `[FAIL]`, or `[manual — requires human]` by the integration agent (Task 6). Items MAN-02 and MAN-06 (10-minute session) are expected to be marked `[manual — requires human]` if the session cannot be completed headlessly.

### SPEC-45: Non-Functional Requirements
All `@export` variables typed with explicit defaults (NF-01, NF-02). No movement math in file (NF-03). No Node references (NF-04). No dead code — every export is used in `_ready()` (NF-05). Zero `godot --headless --check-only` diagnostics (NF-06). UTF-8/LF encoding (NF-07). No print statements (NF-08).

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
IMPLEMENTATION_GENERALIST

## Revision
5

## Last Updated By
Test Breaker Agent

## Validation Status
- Tests: Not Run
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Presentation Agent

## Required Input Schema
```json
{
  "ticket_path": "string — absolute path to this ticket file",
  "spec_path": "string — /Users/jacobbrandt/workspace/blobert/agent_context/projects/blobert/specs/camera_follow_spec.md",
  "primary_tests_path": "string — /Users/jacobbrandt/workspace/blobert/tests/test_camera_follow.gd",
  "adversarial_tests_path": "string — /Users/jacobbrandt/workspace/blobert/tests/test_camera_follow_adversarial.gd",
  "scene_path": "string — /Users/jacobbrandt/workspace/blobert/scenes/test_movement.tscn"
}
```

## Status
Proceed

## Reason
Test Breaker Agent has produced `tests/test_camera_follow_adversarial.gd` with 62 adversarial tests across 10 groups (Groups A–J). Coverage: zero/negative/INF smoothing_speed (A-01 through A-07, I-01 through I-02), smoothing_enabled=false path and bidirectional second-_ready()-overrides (B-01 through B-04), drag_horizontal/drag_vertical non-default toggle paths (C-01 through C-03), drag margins at 0.0/1.0/out-of-range/negative values (D-01 through D-05), degenerate limit boxes including all-same-point/inverted/zero-width/zero-height/INT32_MAX/INT32_MIN (E-01 through E-11), full idempotency and export-var-override sweep for all 12 parameters (F-01 through F-04), mutability sweep for the 9 @export vars not covered by the primary suite (G-01 through G-09), non-default _ready() application for the 8 remaining parameters not covered by the primary suite (H-01 through H-07), and structural integrity checks including free-without-ready, pre-ready readability, static-state isolation, and triple-call idempotency (J-01 through J-04). Conservative-assumption tests marked with # CHECKPOINT. All design decisions logged to CHECKPOINTS.md under [M1-004] Test Breaker entries TB-CF-001 through TB-CF-008. `tests/run_tests.gd` updated with the CameraFollow Adversarial suite block. Presentation Agent must now implement `scripts/camera_follow.gd` per SPEC-37 through SPEC-45 and wire it into `scenes/test_movement.tscn` per SPEC-43.
