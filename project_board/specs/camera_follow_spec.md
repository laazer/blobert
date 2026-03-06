# Camera Follow Specification
# M1-004 — basic_camera_follow.md
# SPEC-37 through SPEC-45
#
# Prerequisite specs: SPEC-1 through SPEC-36
#   SPEC-1  through SPEC-14: movement_controller.md / M1-001
#   SPEC-15 through SPEC-24: jump_tuning.md / M1-002
#   SPEC-25 through SPEC-36: wall_cling.md / M1-003
# Continuing numbering from SPEC-36.
#
# Files affected:
#   /Users/jacobbrandt/workspace/blobert/scripts/camera_follow.gd (new)
#   /Users/jacobbrandt/workspace/blobert/scenes/test_movement.tscn (modified)
#   /Users/jacobbrandt/workspace/blobert/tests/test_camera_follow.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/test_camera_follow_adversarial.gd (new)
#   /Users/jacobbrandt/workspace/blobert/tests/run_tests.gd (updated)

---

## Requirement SPEC-37: File and Class Structure

### 1. Spec Summary

- **Description:** A new GDScript file `scripts/camera_follow.gd` is created. It defines a class that extends `Camera2D` and declares the class name `CameraFollow`. The file contains: a `class_name` declaration, an `extends` declaration, a block of `@export` variable declarations (SPEC-38), and a `_ready()` function (SPEC-39). No other top-level functions, inner classes, signals, or constants are defined in this file.
- **Constraints:**
  - File path: `/Users/jacobbrandt/workspace/blobert/scripts/camera_follow.gd` (absolute). Must be at `res://scripts/camera_follow.gd` within the Godot project.
  - First line of the file: `class_name CameraFollow`
  - Second line of the file: `extends Camera2D`
  - The class must not define `_process()`, `_physics_process()`, `_input()`, or any other lifecycle function beyond `_ready()`.
  - The class must not import or reference any other script via `preload` or `load`.
  - The class must not declare any signals.
  - No movement math of any kind (lerp, move_toward, Vector2 arithmetic on position, etc.) is permitted in this file.
  - The file must pass `godot --headless --check-only` with zero errors and zero warnings.
  - GDScript must be statically typed throughout; every variable declaration must include a type annotation.
- **Assumptions:** No assumptions beyond those logged in CHECKPOINTS.md [M1-004].
- **Scope / Context:** Applies only to `/Users/jacobbrandt/workspace/blobert/scripts/camera_follow.gd`. The Camera2D node in `scenes/test_movement.tscn` is wired to this script in SPEC-43.

### 2. Acceptance Criteria

- **AC-37.1:** The file `/Users/jacobbrandt/workspace/blobert/scripts/camera_follow.gd` exists after implementation.
- **AC-37.2:** Line 1 of the file is exactly `class_name CameraFollow`.
- **AC-37.3:** Line 2 of the file is exactly `extends Camera2D`.
- **AC-37.4:** `CameraFollow` is resolvable as a class name within the Godot project (verifiable via `godot --headless --check-only` passing on any file that references `CameraFollow`).
- **AC-37.5:** The file contains exactly one function definition: `func _ready()`. No other `func` declarations are present.
- **AC-37.6:** The file contains no `preload`, `load`, `signal`, `_process`, `_physics_process`, or `_input` keywords.
- **AC-37.7:** `godot --headless --check-only` exits with code 0 and zero diagnostics for this file.
- **AC-37.8:** Every variable declaration in the file uses a GDScript type annotation (no bare `var name = value` without `: Type`).

### 3. Risk & Ambiguity Analysis

- **Risk R-37.1 (extends collision with Camera2D built-ins):** Because the class extends `Camera2D`, any `@export` variable that shadows a built-in `Camera2D` property name (e.g., naming an export `position_smoothing_speed` directly) will shadow or conflict with the built-in. SPEC-38 uses distinct export names (`smoothing_speed`, not `position_smoothing_speed`) to avoid this. Implementers must not rename exports to match Camera2D property names.
- **Risk R-37.2 (class_name registration in headless mode):** Godot requires at least one editor pass to populate the class name cache. Headless `--check-only` may fail if another file references `CameraFollow` by class name without a corresponding `preload`. SPEC-43 uses `ExtResource` script attachment (the standard tscn mechanism), which does not rely on class name resolution at parse time.
- **Risk R-37.3 (file not in res:// path):** If the file is placed outside the project root (e.g., at an absolute path not matching `res://`), Godot cannot load it. The file must be at exactly `<project_root>/scripts/camera_follow.gd`.

### 4. Clarifying Questions

None. All ambiguities resolved by CHECKPOINTS.md entries [M1-004].

---

## Requirement SPEC-38: Exported Configuration Parameters

### 1. Spec Summary

- **Description:** `CameraFollow` declares eleven `@export`-annotated variables. Each variable is the inspector-facing knob for a corresponding Godot `Camera2D` property. The variable names intentionally differ from the Godot property names they map to, to avoid name shadowing (see R-37.1). Each variable has an explicit type annotation and a default value matching the planner-approved defaults from the parameter table in `basic_camera_follow.md`. All variables are declared at the class body level (not inside any function).
- **Constraints:**
  - All eleven variables must use `@export` (not `@export_range`, `@export_category`, or `@export_group`). Plain `@export` is sufficient; inspector grouping may be added by the implementer as a non-breaking enhancement, but the spec does not require it.
  - Exact variable declarations (the implementer must use these precise identifiers, types, and default values):

    | Variable declaration | Godot Camera2D property mapped |
    |---|---|
    | `@export var smoothing_enabled: bool = true` | `position_smoothing_enabled` |
    | `@export var smoothing_speed: float = 5.0` | `position_smoothing_speed` |
    | `@export var drag_horizontal: bool = true` | `drag_horizontal_enabled` |
    | `@export var drag_vertical: bool = false` | `drag_vertical_enabled` |
    | `@export var drag_left_margin: float = 0.2` | `drag_left_margin` |
    | `@export var drag_right_margin: float = 0.2` | `drag_right_margin` |
    | `@export var drag_top_margin: float = 0.2` | `drag_top_margin` |
    | `@export var drag_bottom_margin: float = 0.2` | `drag_bottom_margin` |
    | `@export var limit_left: int = -10000000` | `limit_left` |
    | `@export var limit_right: int = 10000000` | `limit_right` |
    | `@export var limit_top: int = -10000000` | `limit_top` |
    | `@export var limit_bottom: int = 10000000` | `limit_bottom` |

  - Variable names are case-sensitive. `drag_left_margin` is not the same as `dragLeftMargin`.
  - Limit variables are typed `int` (not `float`). Godot's `Camera2D.limit_*` properties are integers.
  - Margin variables are typed `float`. Godot's `Camera2D.drag_*_margin` properties are floats in the range `[0.0, 1.0]` (fraction of half the viewport). Default value `0.2` is within this range.
  - No `@export` variable may have a `float` type with an `int` literal default (e.g., `= 5` must be `= 5.0`).
- **Assumptions:**
  - The Godot 4.x property names `drag_left_margin`, `drag_right_margin`, `drag_top_margin`, `drag_bottom_margin` are confirmed correct for Godot 4. (In Godot 3.x these were named differently. This spec targets Godot 4 only.)
  - `position_smoothing_enabled` and `position_smoothing_speed` are confirmed Godot 4 property names on `Camera2D`. (Godot 3 used `smoothing_enabled` and `smoothing_speed` without the `position_` prefix.)
  - Default limit values of `-10000000` and `10000000` match Godot 4's own default unclamped limit values for `Camera2D`.
- **Scope / Context:** Applies to the class body of `CameraFollow` in `scripts/camera_follow.gd`, above the `_ready()` function.

### 2. Acceptance Criteria

- **AC-38.1:** `CameraFollow.new().smoothing_enabled` equals `true`.
- **AC-38.2:** `CameraFollow.new().smoothing_speed` equals `5.0` (tolerance EPSILON = 1e-4).
- **AC-38.3:** `CameraFollow.new().drag_horizontal` equals `true`.
- **AC-38.4:** `CameraFollow.new().drag_vertical` equals `false`.
- **AC-38.5:** `CameraFollow.new().drag_left_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-38.6:** `CameraFollow.new().drag_right_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-38.7:** `CameraFollow.new().drag_top_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-38.8:** `CameraFollow.new().drag_bottom_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-38.9:** `CameraFollow.new().limit_left` equals `-10000000` (exact integer equality).
- **AC-38.10:** `CameraFollow.new().limit_right` equals `10000000` (exact integer equality).
- **AC-38.11:** `CameraFollow.new().limit_top` equals `-10000000` (exact integer equality).
- **AC-38.12:** `CameraFollow.new().limit_bottom` equals `10000000` (exact integer equality).
- **AC-38.13:** The total count of `@export` variables in the file is exactly twelve (one per row in the table above, plus the twelve listed).

  Correction: there are exactly **twelve** `@export` variables (`smoothing_enabled`, `smoothing_speed`, `drag_horizontal`, `drag_vertical`, `drag_left_margin`, `drag_right_margin`, `drag_top_margin`, `drag_bottom_margin`, `limit_left`, `limit_right`, `limit_top`, `limit_bottom`).

- **AC-38.14:** All four limit variables are typed `int` (not `float`). Assigning a `float` value (e.g., `1.5`) to any limit variable produces a GDScript type error in strict mode.
- **AC-38.15:** All four margin variables are typed `float`. Assigning an untyped integer (e.g., `1`) to any margin variable is valid only as implicit coercion; the stored value is a float.
- **AC-38.16:** Each `@export` variable is mutable: a test can assign a new value and read it back immediately with the new value.

### 3. Risk & Ambiguity Analysis

- **Risk R-38.1 (Godot 4 vs 3 property name divergence):** The Godot 4 Camera2D drag margin properties are `drag_left_margin`, `drag_right_margin`, `drag_top_margin`, `drag_bottom_margin`. In Godot 3 these were named differently (e.g., `drag_margin_left`). If the Godot binary on this machine is 3.x, the property assignments in `_ready()` will silently set non-existent properties without error. The implementer must verify the Godot binary version is 4.x before wiring.
- **Risk R-38.2 (margin range enforcement):** Godot clamps `drag_*_margin` values to `[0.0, 1.0]` at the engine level when assigned. An `@export` default of `0.2` is within range, but if an inspector user sets a value outside `[0.0, 1.0]`, Godot clamps it silently. The spec does not require the script to validate margin range; this is handled by the engine.
- **Risk R-38.3 (limit_left > limit_right inversion):** The spec does not constrain the relationship between `limit_left` and `limit_right` (or `limit_top` and `limit_bottom`). A user could set `limit_left = 500` and `limit_right = 100`, producing an inverted (zero-size or negative-size) bounding box. Godot's Camera2D behavior with inverted limits is undefined in the engine docs. The script does not validate this; the Test Breaker agent (Task 3) covers this edge case in adversarial tests.
- **Risk R-38.4 (int vs float type for limits):** An implementer who types limits as `float` rather than `int` will pass `--check-only` but may produce an implicit cast warning when assigning to `Camera2D.limit_*` (which are native int properties). The spec mandates `int` to be explicit and warning-free.

### 4. Clarifying Questions

None. All ambiguities resolved by CHECKPOINTS.md entries [M1-004].

---

## Requirement SPEC-39: `_ready()` Initialization

### 1. Spec Summary

- **Description:** `CameraFollow._ready()` assigns each of the twelve `@export` variable values to the corresponding Godot `Camera2D` built-in property. This is the only code in `_ready()`. The assignments are unconditional: they always run when the node enters the scene tree, overwriting any values previously set via the Godot editor inspector (scene file `.tscn` properties take precedence over script defaults, but `_ready()` runs after the scene tree is populated and re-applies the script values). No validation, no guards, no conditional branches, and no calls to `super._ready()` are required (unless Godot enforces it, in which case `super()` is called first before any assignment).
- **Constraints:**
  - The function signature is exactly `func _ready() -> void:`.
  - The function body contains exactly twelve assignment statements, one per `@export` variable, in the order listed in SPEC-38's parameter table.
  - Each assignment has the form `<Camera2D_property_name> = <export_variable_name>`. For example: `position_smoothing_enabled = smoothing_enabled`.
  - No local variables are declared inside `_ready()`.
  - No function calls are made inside `_ready()` (no helper function calls, no `super._ready()` unless strictly required by Godot 4's `Camera2D` base class).
  - No print, push_warning, push_error, or assertion calls are inside `_ready()`.
  - The complete mapping of assignment statements (left side = Camera2D property, right side = export variable):

    | Camera2D property (left side) | Export variable (right side) |
    |---|---|
    | `position_smoothing_enabled` | `smoothing_enabled` |
    | `position_smoothing_speed` | `smoothing_speed` |
    | `drag_horizontal_enabled` | `drag_horizontal` |
    | `drag_vertical_enabled` | `drag_vertical` |
    | `drag_left_margin` | `drag_left_margin` |
    | `drag_right_margin` | `drag_right_margin` |
    | `drag_top_margin` | `drag_top_margin` |
    | `drag_bottom_margin` | `drag_bottom_margin` |
    | `limit_left` | `limit_left` |
    | `limit_right` | `limit_right` |
    | `limit_top` | `limit_top` |
    | `limit_bottom` | `limit_bottom` |

  - Note: for `drag_*_margin` and `limit_*` variables, the export variable name coincides with the Camera2D property name. These are valid self-assignments of the same underlying property (since the node IS a `Camera2D`, assigning `drag_left_margin = drag_left_margin` has no effect at runtime beyond being a no-op that makes the `_ready()` body explicit and auditable). Alternatively, the implementer may omit these four drag margin assignments and four limit assignments if the exported property names already directly map to the inherited Camera2D property names. See Risk R-39.1.
- **Assumptions:**
  - `Camera2D` in Godot 4 does not require `super._ready()` to be called for the node to function correctly. If Godot 4's Camera2D base implementation requires `super()`, then `super()` is called as the first statement in `_ready()`. This is logged as a checkpoint ambiguity since Godot 4 RefCounted-derived nodes do not typically require super calls, but Node-derived nodes may if they use `_ready()` themselves.
  - The twelve assignments in `_ready()` fully configure the camera for the feature's requirements. No additional Godot Camera2D properties need to be set.
- **Scope / Context:** Applies to the `_ready()` function body in `scripts/camera_follow.gd`.

### 2. Acceptance Criteria

- **AC-39.1:** After `_ready()` is called on a `CameraFollow` node attached to the scene tree, `node.position_smoothing_enabled` equals the value of `node.smoothing_enabled` (default: `true`).
- **AC-39.2:** After `_ready()`, `node.position_smoothing_speed` equals the value of `node.smoothing_speed` (default: `5.0`, tolerance EPSILON = 1e-4).
- **AC-39.3:** After `_ready()`, `node.drag_horizontal_enabled` equals `node.drag_horizontal` (default: `true`).
- **AC-39.4:** After `_ready()`, `node.drag_vertical_enabled` equals `node.drag_vertical` (default: `false`).
- **AC-39.5:** After `_ready()`, `node.drag_left_margin` equals `node.drag_left_margin` value set by `@export` (default: `0.2`, tolerance EPSILON = 1e-4).
- **AC-39.6:** After `_ready()`, `node.drag_right_margin` equals `node.drag_right_margin` value set by `@export` (default: `0.2`, tolerance EPSILON = 1e-4).
- **AC-39.7:** After `_ready()`, `node.drag_top_margin` equals `node.drag_top_margin` value set by `@export` (default: `0.2`, tolerance EPSILON = 1e-4).
- **AC-39.8:** After `_ready()`, `node.drag_bottom_margin` equals `node.drag_bottom_margin` value set by `@export` (default: `0.2`, tolerance EPSILON = 1e-4).
- **AC-39.9:** After `_ready()`, `node.limit_left` equals `node.limit_left` value set by `@export` (default: `-10000000`, exact integer equality).
- **AC-39.10:** After `_ready()`, `node.limit_right` equals `node.limit_right` value set by `@export` (default: `10000000`, exact integer equality).
- **AC-39.11:** After `_ready()`, `node.limit_top` equals `node.limit_top` value set by `@export` (default: `-10000000`, exact integer equality).
- **AC-39.12:** After `_ready()`, `node.limit_bottom` equals `node.limit_bottom` value set by `@export` (default: `10000000`, exact integer equality).
- **AC-39.13:** If `smoothing_enabled` is changed to `false` before `_ready()` runs (e.g., set via the inspector in the scene file), `_ready()` correctly applies `false` to `position_smoothing_enabled`. Verifiable by constructing a node, setting `smoothing_enabled = false`, manually calling `_ready()`, and checking `position_smoothing_enabled == false`.
- **AC-39.14:** The function signature is exactly `func _ready() -> void:` with no parameters and an explicit `-> void` return type annotation.

### 3. Risk & Ambiguity Analysis

- **Risk R-39.1 (self-assignment for coincident property names):** For the four drag margin variables (`drag_left_margin`, `drag_right_margin`, `drag_top_margin`, `drag_bottom_margin`) and the four limit variables (`limit_left`, `limit_right`, `limit_top`, `limit_bottom`), the `@export` variable names in `CameraFollow` exactly match the inherited `Camera2D` property names. In GDScript, writing `drag_left_margin = drag_left_margin` in `_ready()` is a no-op at runtime (right-hand side reads the property, left-hand side writes the same property). This is intentional: it documents the intent explicitly. An implementer may choose to omit these eight redundant assignments to keep `_ready()` cleaner; this is acceptable and does not violate the AC's provided the `@export` defaults are the correct values (which they are by AC-38.5 through AC-38.12 and AC-38.9 through AC-38.12). The Test Designer agent must account for both presence and absence of these eight statements being valid.
- **Risk R-39.2 (super._ready() requirement):** Godot 4's `Camera2D` extends `Node2D` which extends `CanvasItem` which extends `Node`. The `Node._ready()` implementation is called by the engine before the script's `_ready()`. However, if `CameraFollow._ready()` calls `super()` explicitly, it triggers any `_ready()` implementation in intermediate classes. For a plain `Camera2D` with no custom C++ `_ready()` logic that must be triggered by GDScript, omitting `super()` is safe. The spec does not require `super()`, but it does not prohibit it.
- **Risk R-39.3 (editor-set properties vs _ready() override):** When a `CameraFollow` node is saved in a `.tscn` file with non-default inspector values for Camera2D properties (e.g., `position_smoothing_speed = 10.0` serialized in the tscn), those values are applied by Godot's scene loader before `_ready()` runs. `_ready()` then overwrites them with the `@export` variable values. If the designer changes `smoothing_speed` in the inspector to `10.0` but forgets that `_ready()` will override it, the in-editor value appears correct but the runtime value is the `@export` value. This is the intended behavior (the `@export` vars ARE the single source of truth), but it may surprise designers. The risk is confusion, not a bug.
- **Risk R-39.4 (wrong property names for Godot version):** If the Godot binary is not 4.x (see R-38.1), `position_smoothing_enabled` and `position_smoothing_speed` do not exist on `Camera2D`. `godot --headless --check-only` will report "Member not found" errors. This is a CI-time-detectable failure.

### 4. Clarifying Questions

None. All ambiguities resolved by CHECKPOINTS.md entries [M1-004].

---

## Requirement SPEC-40: Smoothing Behavior

### 1. Spec Summary

- **Description:** Camera position smoothing is implemented entirely via Godot's built-in `Camera2D` properties `position_smoothing_enabled` and `position_smoothing_speed`. No custom lerp, interpolation math, or `_process()` override is written in `camera_follow.gd`. When `position_smoothing_enabled = true`, Godot's engine internally smooths the camera position toward the target position (the parent `Player` node's global position) each frame at the rate controlled by `position_smoothing_speed`. The script's only role is to enable this behavior in `_ready()` from the exported `smoothing_enabled` and `smoothing_speed` variables.
- **Constraints:**
  - Default: `smoothing_enabled = true`, `smoothing_speed = 5.0`.
  - Valid range for `smoothing_speed`: any positive float. There is no engine-enforced maximum; very large values (e.g., 1000.0) approach instantaneous follow (effectively disabling smoothing). Very small values (e.g., 0.1) produce heavily lagged follow.
  - `smoothing_speed = 0.0` disables smoothing movement entirely (camera freezes in place regardless of player movement) when `position_smoothing_enabled = true`. This is defined Godot behavior.
  - When `smoothing_enabled = false`, `position_smoothing_enabled = false`, and the camera exactly tracks the parent node's position each frame with zero lag. This is the Godot Camera2D default.
  - No implementation of this behavior is permitted in GDScript. Smooth follow is engine-driven only.
  - The `smoothing_speed` type is `float`. Setting it to `5.0` is the baseline "feels good" default as decided by the planner; it is tunable via the inspector.
- **Assumptions:** Godot 4's `Camera2D` with `position_smoothing_enabled = true` and `position_smoothing_speed = 5.0` produces visually smooth follow at 60fps with no jitter for a horizontally moving platformer character. This is a design assumption, not verifiable headlessly; it is verified by the manual checklist (SPEC-44).
- **Scope / Context:** Behavioral description for how the camera moves at runtime. The corresponding implementation requirement is in SPEC-39 (the `_ready()` assignments). This spec entry exists to give Test Designer and Presentation agents explicit context about what the implementation is expected to achieve.

### 2. Acceptance Criteria

- **AC-40.1:** With `smoothing_enabled = true` and `smoothing_speed = 5.0`, the camera visually lags slightly behind the player during fast horizontal movement. This is not a jitter — it is intentional lag that smoothes out direction changes. Verified manually (see SPEC-44, MAN-01).
- **AC-40.2:** With `smoothing_enabled = false`, the camera position matches the player position exactly each frame with zero visual lag. Verified manually (SPEC-44, MAN-05).
- **AC-40.3:** Changing `smoothing_speed` to a higher value (e.g., `20.0`) produces noticeably tighter follow (less lag) compared to `5.0`. Verified manually (SPEC-44, MAN-05).
- **AC-40.4:** At no point during normal play does the camera exhibit positional jitter (rapid oscillation around the target position). Verified manually over 10 minutes (SPEC-44, MAN-02).
- **AC-40.5 (headless):** The `CameraFollow` script, when instantiated in a headless test environment, has `position_smoothing_enabled` set to `true` (the `@export` default value) after `_ready()` is called. This is a proxy for verifying the smoothing configuration is applied.
- **AC-40.6 (headless):** After calling `_ready()` on a `CameraFollow` node with `smoothing_speed = 12.5` (non-default), `position_smoothing_speed` equals `12.5` (tolerance EPSILON = 1e-4). This verifies that `_ready()` applies arbitrary non-default values, not just the hardcoded defaults.

### 3. Risk & Ambiguity Analysis

- **Risk R-40.1 (smoothing_speed = 0.0 freezes camera):** When `position_smoothing_enabled = true` and `position_smoothing_speed = 0.0`, Godot's built-in smoothing effectively freezes the camera because the blend factor is 0.0 per frame. The camera will not follow the player. This is an edge case that is valid (the parameter is `0.0` and behavior is deterministic) but produces a camera that appears broken. The script does not guard against this; it is the designer's responsibility. The adversarial test suite (Task 3) must cover this case.
- **Risk R-40.2 (smoothing vs. drag margin interaction):** When both `position_smoothing_enabled = true` and `drag_horizontal_enabled = true`, the Godot engine applies drag margins first (defining the dead zone threshold), then applies smoothing to the movement outside the dead zone. These are complementary and not conflicting, but the interaction may produce unexpected behavior if both settings are very conservative (large margins + very low smoothing speed). This interaction is a manual-play concern, not a headless-testable concern.
- **Risk R-40.3 (engine version behavior change):** Godot's implementation of `position_smoothing` changed between 4.0 and 4.1 in edge cases. The spec targets the behavior present in the Godot binary installed at the development machine. If behavior changes in a future engine upgrade, this spec requires no code change — only potential re-tuning of `smoothing_speed`.

### 4. Clarifying Questions

None.

---

## Requirement SPEC-41: Dead Zone / Drag Margin Behavior

### 1. Spec Summary

- **Description:** The camera dead zone is implemented via Godot's built-in `Camera2D` drag margin system. When `drag_horizontal_enabled = true`, the camera only moves horizontally when the player exits a central horizontal band defined by `drag_left_margin` and `drag_right_margin` (as fractions of half the viewport width). When `drag_vertical_enabled = false` (the default), the camera tracks vertical position immediately with no dead zone. The script sets these four margin properties in `_ready()` from the corresponding `@export` variables. No custom GDScript dead zone logic is written.
- **Constraints:**
  - Default horizontal drag: enabled (`drag_horizontal = true`). Default vertical drag: disabled (`drag_vertical = false`).
  - Margin values are floats in the range `[0.0, 1.0]`. `0.0` means the dead zone has zero width (camera always follows). `1.0` means the dead zone extends to the full half-viewport (camera never moves until player is at the screen edge). Default `0.2` means the dead zone occupies the central 40% of the viewport (20% on each side from center).
  - Godot property names: `drag_horizontal_enabled`, `drag_vertical_enabled`, `drag_left_margin`, `drag_right_margin`, `drag_top_margin`, `drag_bottom_margin`.
  - Godot clamps margin values to `[0.0, 1.0]` when assigned. The script does not perform this clamping.
  - When `drag_horizontal_enabled = false`, the margin values (`drag_left_margin`, `drag_right_margin`) are stored and applied to the Camera2D node but have no behavioral effect (drag is disabled). The `_ready()` assignments still apply all margin values unconditionally.
- **Assumptions:** The default asymmetry between horizontal drag (enabled) and vertical drag (disabled) is intentional for a 2D platformer. Horizontal lead space is a conventional platformer camera technique; vertical tracking should be immediate so the player always sees platforms above and below without a dead zone delay. This is the planner's decision (see CHECKPOINTS.md [M1-004] Planner — Dead zone mechanism).
- **Scope / Context:** Applies to the drag-related `@export` variables in `CameraFollow` and their application in `_ready()`. Behavioral verification is manual (SPEC-44, MAN-03).

### 2. Acceptance Criteria

- **AC-41.1:** After `_ready()` with defaults, `node.drag_horizontal_enabled` is `true`.
- **AC-41.2:** After `_ready()` with defaults, `node.drag_vertical_enabled` is `false`.
- **AC-41.3:** After `_ready()` with defaults, `node.drag_left_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-41.4:** After `_ready()` with defaults, `node.drag_right_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-41.5:** After `_ready()` with defaults, `node.drag_top_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-41.6:** After `_ready()` with defaults, `node.drag_bottom_margin` equals `0.2` (tolerance EPSILON = 1e-4).
- **AC-41.7 (headless, non-default):** If `drag_left_margin` is set to `0.4` before `_ready()` is called, then after `_ready()` `node.drag_left_margin` equals `0.4` (tolerance EPSILON = 1e-4). This confirms `_ready()` applies the current export value, not a hardcoded `0.2`.
- **AC-41.8 (manual):** With horizontal drag enabled at margin `0.2`, moving the player slowly (staying within the central 40% horizontal band) does not move the camera horizontally. Verified manually (SPEC-44, MAN-03).
- **AC-41.9 (manual):** Moving the player quickly past the 20% horizontal margin causes the camera to begin following. The camera resumes following on the correct side when the player exits the dead zone. Verified manually (SPEC-44, MAN-03).

### 3. Risk & Ambiguity Analysis

- **Risk R-41.1 (drag margin fraction vs pixel confusion):** Godot's `drag_*_margin` values are fractions of the half-viewport (range `[0.0, 1.0]`), not pixel values. A designer who sets `drag_left_margin = 100` expecting 100 pixels of dead zone will get a value clamped to `1.0` (full-screen dead zone). The spec uses a float type and `0.2` default which is clearly a fraction, not pixels. The inspector tooltip in the Godot editor also labels these as fractions. No spec change is needed; this is a documentation-level risk.
- **Risk R-41.2 (vertical drag enabled unexpectedly):** If the implementer accidentally sets `drag_vertical_enabled = true` with default margin `0.2`, the camera will have a vertical dead zone by default. In a platformer, this causes the player's feet to disappear below the camera dead zone boundary during jumps. The spec defaults to `drag_vertical = false` specifically to prevent this. AC-41.2 guards against this.
- **Risk R-41.3 (drag disabled but margins still assigned):** When `drag_horizontal_enabled = false`, assigning margin values is harmless but wasteful. There is no risk here since the engine ignores margin values when drag is disabled. The `_ready()` body assigns them unconditionally per SPEC-39's constraints.

### 4. Clarifying Questions

None.

---

## Requirement SPEC-42: Level Bounds Limiting

### 1. Spec Summary

- **Description:** The camera is prevented from showing the world beyond configurable rectangular level boundaries using Godot's built-in `Camera2D.limit_*` properties. The four limit properties (`limit_left`, `limit_right`, `limit_top`, `limit_bottom`) define the bounding rectangle in global pixel coordinates that constrains the camera's visible area. By default, all four limits are set to Godot's unclamped values (`-10000000` and `10000000`), which effectively disables bounding. When a level is designed with defined bounds, the `@export` variables are adjusted via the inspector on the Camera2D node in the scene.
- **Constraints:**
  - The `limit_*` exported variables have type `int`. The Godot `Camera2D.limit_*` properties are integers.
  - Default values: `limit_left = -10000000`, `limit_right = 10000000`, `limit_top = -10000000`, `limit_bottom = 10000000`. These match Godot 4's own default Camera2D limit values.
  - The coordinate system is Godot 2D global coordinates: positive X is right, positive Y is down. `limit_top` is therefore a negative number (above the origin) and `limit_bottom` is a positive number (below the origin) in a standard Godot 2D scene. The defaults make the bounding box enormous in both directions.
  - The script does not validate that `limit_left < limit_right` or `limit_top < limit_bottom`. Inverted limits (left >= right or top >= bottom) are the designer's responsibility and produce undefined camera behavior per Godot docs. The Test Breaker agent (Task 3) covers this edge case.
  - The script does not compute or derive limit values from any other scene node. Limit values are set exclusively from the four `@export` variables.
  - A level designer wishing to confine the camera to a specific room should set `limit_left` and `limit_right` to the pixel boundaries of the room (e.g., `limit_left = 0`, `limit_right = 2000` for a 2000-pixel-wide room), and similarly for `limit_top` and `limit_bottom`.
- **Assumptions:** No assumption about the size of the room in `scenes/test_movement.tscn`. The floor node is at `position.y = 300` and has a width of `2000` pixels (based on `RectangleShape2D` size `Vector2(2000, 20)` in the scene file), but no explicit room bounds are required. The test scene uses default (unclamped) limits.
- **Scope / Context:** Applies to the four `limit_*` `@export` variables in `CameraFollow` and their application in `_ready()`. Behavioral verification is manual (SPEC-44, MAN-04).

### 2. Acceptance Criteria

- **AC-42.1:** After `_ready()` with defaults, `node.limit_left` equals `-10000000` (exact integer equality).
- **AC-42.2:** After `_ready()` with defaults, `node.limit_right` equals `10000000` (exact integer equality).
- **AC-42.3:** After `_ready()` with defaults, `node.limit_top` equals `-10000000` (exact integer equality).
- **AC-42.4:** After `_ready()` with defaults, `node.limit_bottom` equals `10000000` (exact integer equality).
- **AC-42.5 (headless, non-default):** If `limit_right` is set to `800` before `_ready()` is called, then after `_ready()` `node.limit_right` equals `800` (exact integer equality). This confirms `_ready()` applies the current export value, not the hardcoded default.
- **AC-42.6 (headless, non-default):** If `limit_left` is set to `0`, `limit_right` to `2000`, `limit_top` to `-600`, and `limit_bottom` to `400` before `_ready()` is called, then after `_ready()` all four `node.limit_*` properties match the assigned values (exact integer equality).
- **AC-42.7 (manual):** With `limit_right = 2000` and the player running right, the camera stops scrolling when it reaches the right edge at pixel 2000 and does not show world outside that boundary. Verified manually (SPEC-44, MAN-04).

### 3. Risk & Ambiguity Analysis

- **Risk R-42.1 (int overflow):** `10000000` fits in a 32-bit signed integer (max ~2.1 billion). No overflow risk with the default value. Extreme values approaching `INT_MAX` (~2147483647) are valid but unlikely to be needed for game level bounds.
- **Risk R-42.2 (limit_left > limit_right causes camera flip or freeze):** Godot's Camera2D behavior with inverted limits is documented as undefined. In practice it typically causes the camera to be clamped to an impossible region (snaps to the invalid corner). This is an adversarial edge case; the spec does not require the script to guard against it, but the Test Breaker agent must cover it.
- **Risk R-42.3 (limits not yet wired for test_movement.tscn):** The test room uses a 2000-pixel-wide floor centered at origin (`position = Vector2(0, 300)`), so the floor extends from approximately x = -1000 to x = 1000. The default unclamped limits allow the camera to scroll beyond the floor into empty space. This is acceptable for Milestone 1 (the feature is basic follow, not level-bounded follow). A designer may set explicit bounds later. No action is required from the Presentation Agent for M1-004.

### 4. Clarifying Questions

None.

---

## Requirement SPEC-43: Scene Wiring

### 1. Spec Summary

- **Description:** The `Camera` node in `scenes/test_movement.tscn` (currently a plain `Camera2D` node with no script) is updated to have `scripts/camera_follow.gd` attached as its script. Additionally, the `Camera` node's `ExtResource` reference for the script is added to the scene file's header. No other nodes or resources in `test_movement.tscn` are modified. The scene must continue to open and run correctly in the Godot editor after the modification.
- **Constraints:**
  - The existing `Camera` node definition in the `.tscn` file is:
    ```
    [node name="Camera" type="Camera2D" parent="Player"]
    ```
    After modification it must be:
    ```
    [node name="Camera" type="Camera2D" parent="Player"]
    script = ExtResource("<id>")
    ```
    where `<id>` is the unique resource identifier assigned in the `[ext_resource]` declaration for `camera_follow.gd`.
  - An `[ext_resource]` declaration for `camera_follow.gd` must be added to the scene file header section (before the first `[node]` block). The format follows the existing pattern in the file:
    ```
    [ext_resource type="Script" path="res://scripts/camera_follow.gd" id="<id>_camfollow"]
    ```
    The `id` value must be unique within the file (different from `"1_playerctrl"` which is already used).
  - The `load_steps` count in the `[gd_scene]` header must be incremented by 1 to account for the new `ext_resource`. Current value is `5`; after modification it must be `6`.
  - The node name `Camera` is preserved. The node type `Camera2D` is preserved. The parent `Player` is preserved. No other node properties are added to the Camera node's block.
  - No other nodes in the scene file are modified.
  - The scene file must pass `godot --headless --check-only` with zero errors after modification.
- **Assumptions:**
  - The `@export` variable values stored in the scene file (via the inspector) are not required for the initial wiring. Because `_ready()` applies the `@export` defaults at runtime, the scene file does not need to serialize any non-default Camera2D property values. The Camera node block in the `.tscn` contains only `script = ExtResource(...)` and nothing else.
  - The `.tscn` file continues to use text format (format=3). No binary scene format is introduced.
- **Scope / Context:** Applies to `/Users/jacobbrandt/workspace/blobert/scenes/test_movement.tscn` only. The script file itself is created per SPEC-37.

### 2. Acceptance Criteria

- **AC-43.1:** The file `/Users/jacobbrandt/workspace/blobert/scenes/test_movement.tscn` contains an `[ext_resource]` declaration with `type="Script"` and `path="res://scripts/camera_follow.gd"`.
- **AC-43.2:** The `[node name="Camera" type="Camera2D" parent="Player"]` block in the scene file contains a `script = ExtResource(...)` line referencing the id from AC-43.1.
- **AC-43.3:** The `[gd_scene]` header line's `load_steps` value is exactly `6`.
- **AC-43.4:** No other node in the scene file is modified. The `TestMovement`, `Floor`, `FloorShape`, `Player`, and `PlayerShape` nodes remain identical to the original.
- **AC-43.5:** `godot --headless --check-only` on the scene file exits with code 0 and zero errors.
- **AC-43.6:** The Camera node's type remains `Camera2D` (not changed to `CameraFollow` or any other type). The script is attached via the `script` property, not by changing the node type.
- **AC-43.7:** The scene file uses the `uid` field from the original `[gd_scene]` line unchanged: `uid="uid://blobert_test_movement"`.

### 3. Risk & Ambiguity Analysis

- **Risk R-43.1 (id collision):** The existing scene uses `id="1_playerctrl"` for the player controller script. The new camera follow script must use a different id. A safe convention is `id="2_camfollow"` following the existing numeric prefix pattern. If an implementer accidentally reuses `"1_playerctrl"`, Godot will fail to load the scene with a duplicate resource error.
- **Risk R-43.2 (load_steps count mismatch):** If `load_steps` is not incremented, Godot logs a warning but typically still loads the scene. However, the `--check-only` pass may report a warning. The spec mandates `load_steps = 6` to keep the file correct.
- **Risk R-43.3 (hand-editing .tscn is fragile):** The `.tscn` format is line-sensitive. Inserting a node property or ext_resource in the wrong location (e.g., inside a node block instead of the header) causes a parse error. The Presentation Agent must insert the `[ext_resource]` declaration in the header section (before the first `[node]` block) and the `script = ...` property immediately after the `[node name="Camera" ...]` line.
- **Risk R-43.4 (scene UID format):** The existing scene uid is `uid://blobert_test_movement`, which is a hand-written placeholder, not a Godot-generated UID (which uses base64-like characters). The Presentation Agent must preserve this uid exactly — it must not regenerate it.

### 4. Clarifying Questions

None.

---

## Requirement SPEC-44: Manual Acceptance Checklist

### 1. Spec Summary

- **Description:** Several acceptance criteria for camera behavior (smoothness, dead zone feel, bounds clamping, absence of jitter over extended play) cannot be verified headlessly. These criteria are captured as a numbered manual checklist. The integration agent (Task 6) works through each item, marks items as `[PASS]`, `[FAIL]`, or `[manual — requires human]` as appropriate, and appends the results to the ticket. Items marked `[manual — requires human]` are escalated per CHECKPOINTS.md [M1-004] Planner — 10-minute play session.
- **Constraints:**
  - All checklist items must be evaluated before the ticket advances to COMPLETE.
  - Items verifiable headlessly (e.g., syntax checks, property assignment) are covered by SPEC-37 through SPEC-43 ACs and are NOT repeated in this checklist. This checklist contains only items requiring in-editor or human play verification.
  - Each checklist item has a unique identifier (MAN-01 through MAN-06).
- **Assumptions:** The Godot project can be opened and played in the editor on this machine using `/Applications/Godot.app`. If the project cannot be opened (e.g., missing import cache), the integration agent documents the failure and marks all checklist items `[manual — requires human]`.
- **Scope / Context:** Applies at the integration verification stage (Task 6). The Test Designer agent (Task 2) appends this checklist to the spec; the Presentation Agent (Task 6) fills in results.

### 2. Acceptance Criteria (Manual Checklist Items)

- **MAN-01 (Smooth follow):** Open `scenes/test_movement.tscn` in the Godot editor and press Play Scene. Move the player left and right using A/D or arrow keys. The camera should visibly lag slightly behind the player during fast movement — this is the smoothing effect. There is no abrupt snap or teleport of the camera. Expected result: smooth, continuous camera movement with a slight lag. Mark `[PASS]` if observed, `[FAIL]` if camera snaps or teleports, `[manual — requires human]` if the scene cannot be run.
- **MAN-02 (No jitter over extended play):** Run the test scene and move the player continuously for at least 10 minutes (or the maximum feasible duration in the testing context). During this period, the camera must not exhibit positional jitter (rapid back-and-forth oscillation of the camera position independent of player movement). Expected result: zero jitter events observed. If the session cannot run for 10 minutes headlessly, mark as `[manual — requires human]` and note the actual duration tested.
- **MAN-03 (Horizontal dead zone):** Run the test scene. Make slow, small horizontal movements (less than ~20% of the screen width). The camera should not move horizontally. Make a larger movement (more than ~20% of screen width). The camera should begin following. Expected result: camera stationary during small movements, following during large movements. Mark `[PASS]` or `[FAIL]`. If this behavior is difficult to observe due to smoothing lag, note it.
- **MAN-04 (Level bounds — optional, non-blocking):** If the inspector is used to set `limit_right = 1000` on the Camera node, run the scene and move the player right past x = 1000. The camera should stop scrolling at the right bound and not show empty space beyond it. Expected result: camera clamped at right boundary. Mark `[PASS]`, `[FAIL]`, or `[skipped — default unclamped limits]`. This item is non-blocking for the ticket; the test scene uses unclamped limits by default.
- **MAN-05 (Smoothing toggle):** Change `smoothing_enabled` to `false` in the inspector and replay the scene. The camera should now track the player exactly with zero lag. Re-enable and verify lag returns. Expected result: toggling `smoothing_enabled` changes camera behavior as described. Mark `[PASS]` or `[FAIL]`.
- **MAN-06 (Player always on screen):** During 10 minutes of normal play (or maximum feasible duration), the player character is always visible on screen. The camera never leaves the player off-screen. Expected result: player remains on screen at all times. Mark `[PASS]`, `[FAIL]`, or `[manual — requires human]` with the same session duration note as MAN-02.

### 3. Risk & Ambiguity Analysis

- **Risk R-44.1 (AI agent play session limitation):** An AI agent cannot perform a true interactive 10-minute play session. The integration agent must run the longest feasible headless or scripted simulation and mark any unverifiable items `[manual — requires human]`. The ticket remains in integration state until a human confirms `[PASS]` for those items or explicitly accepts `[manual — requires human]` as the terminal state for M1.
- **Risk R-44.2 (Visual judgment subjectivity):** "Smooth" and "no jitter" are subjective criteria. For MAN-01 and MAN-02, the operational definition is: (a) camera position delta per frame is continuous (no frame where camera position jumps by more than `position_smoothing_speed * max_player_speed * delta_time` pixels), and (b) camera position does not reverse direction within 3 consecutive frames while the player is moving in a single direction. These definitions allow a technically precise interpretation.
- **Risk R-44.3 (Dead zone hard to observe with smoothing active):** When both smoothing and drag margins are active, the camera smoothly interpolates toward the drag zone boundary rather than snapping. It may be difficult to visually distinguish "no movement within dead zone" from "very slow movement within dead zone" due to smoothing. MAN-03 notes this risk; the verifier should disable smoothing temporarily to confirm the dead zone is active.

### 4. Clarifying Questions

None.

---

## Requirement SPEC-45: Non-Functional Requirements

### 1. Spec Summary

- **Description:** All non-functional constraints that apply to `scripts/camera_follow.gd` and `scenes/test_movement.tscn` as modified by this feature. These constraints apply in addition to all functional requirements above and are enforced by the Static QA Agent (Task 5).
- **Constraints:**
  1. **Typed GDScript (NF-01):** Every variable declaration in `camera_follow.gd` must include a GDScript type annotation. Untyped declarations (`var x = 5` without `: int`) are not permitted. This applies to `@export` variables and any local variables that may be introduced.
  2. **Explicit default values (NF-02):** Every `@export` variable must have an explicit initializer (e.g., `= 5.0`). No `@export` variable may be declared without a default value.
  3. **No movement math (NF-03):** No movement computation of any kind is permitted in `camera_follow.gd`. Specifically, the following are prohibited: `lerp`, `move_toward`, `Vector2(`, any arithmetic involving `position`, `global_position`, `velocity`, or any custom interpolation formula. The only permitted write operations in the script body are the `@export` variable declarations and the property assignments in `_ready()`.
  4. **No Node references (NF-04):** `camera_follow.gd` must not store or use a reference to any other Node (e.g., `get_parent()`, `$Player`, `find_child()`, `get_node()`). The camera's follow behavior is achieved solely by being a child of the `Player` node in the scene tree (Godot's built-in parent-follow behavior for Camera2D nodes), not by scripted position tracking.
  5. **No dead code (NF-05):** No unused variables, unused imports, or unreachable code blocks are permitted in `camera_follow.gd`. The `@export` variables are all referenced in `_ready()`; any variable not used in `_ready()` is dead code and must be removed.
  6. **Syntax validity (NF-06):** `godot --headless --check-only` must exit with code 0 and zero diagnostic lines for `camera_follow.gd` and the modified `scenes/test_movement.tscn`.
  7. **File encoding (NF-07):** `camera_follow.gd` must use UTF-8 encoding with LF line endings (the Godot and git standard for this repository). No BOM, no CRLF.
  8. **No print statements (NF-08):** No `print()`, `print_rich()`, `push_warning()`, `push_error()`, or `OS.alert()` calls in `camera_follow.gd`.
- **Assumptions:** No assumptions.
- **Scope / Context:** Applies to all files created or modified as part of the M1-004 camera follow feature.

### 2. Acceptance Criteria

- **AC-45.1 (NF-01):** The Static QA Agent confirms zero untyped variable declarations in `camera_follow.gd` via GDScript strict-mode check.
- **AC-45.2 (NF-02):** The Static QA Agent confirms every `@export` variable has an explicit default value (verified by reading each declaration line).
- **AC-45.3 (NF-03):** The Static QA Agent confirms `camera_follow.gd` contains none of the prohibited keywords: `lerp`, `move_toward`, `Vector2(` used in movement context, arithmetic involving `position` as a write target. A `grep`-level scan of the file for these patterns is sufficient.
- **AC-45.4 (NF-04):** The Static QA Agent confirms `camera_follow.gd` contains none of: `get_parent`, `get_node`, `find_child`, `$` (node path shorthand), `NodePath(`. A `grep`-level scan is sufficient.
- **AC-45.5 (NF-05):** Every `@export` variable declared in `camera_follow.gd` appears exactly once in the `_ready()` function body as the right-hand side of an assignment. If any `@export` variable is declared but not used in `_ready()`, it is a dead code violation.
- **AC-45.6 (NF-06):** `godot --headless --check-only` exits with return code `0` and outputs zero lines matching `ERROR:` or `WARNING:` patterns for this project after all M1-004 files are in place.
- **AC-45.7 (NF-07):** The file `camera_follow.gd` when read as binary contains no `\r` bytes (0x0D) and no BOM bytes (0xEF 0xBB 0xBF at offset 0).
- **AC-45.8 (NF-08):** A grep of `camera_follow.gd` for the pattern `print\|push_warning\|push_error\|OS.alert` returns zero matches.

### 3. Risk & Ambiguity Analysis

- **Risk R-45.1 (NF-03 and self-assignment of coincident names):** As noted in R-39.1, `drag_left_margin = drag_left_margin` technically involves reading and writing the same property. This is not "movement math" — it is a property assignment. The NF-03 prohibition targets position interpolation math, not this pattern. The Static QA Agent should not flag this as a violation.
- **Risk R-45.2 (NF-05 and redundant drag/limit assignments):** If the implementer follows the SPEC-39 R-39.1 guidance and omits the eight redundant drag/limit self-assignments from `_ready()`, then those eight `@export` variables are technically "not used in `_ready()`." However, those `@export` variables are not dead code — they define the inspector-facing defaults that Godot applies when the scene file is loaded (before `_ready()` runs). The Static QA Agent must recognize that `@export` variables with names matching Camera2D built-in properties serve a dual purpose: they are both inspector parameters AND implicit property overrides via the scene serialization system. AC-45.5 is interpreted as: for the four non-coincident exports (`smoothing_enabled`, `smoothing_speed`, `drag_horizontal`, `drag_vertical`), the `@export` variable must appear in `_ready()`. For the eight coincident-name exports, their presence is acceptable with or without explicit `_ready()` assignment.
- **Risk R-45.3 (strict mode warnings):** Godot 4's GDScript strict mode (`@tool` + `class_name`) may emit warnings for properties assigned in `_ready()` that shadow built-in node properties if type annotations are mismatched. The implementer must ensure the type of each `@export` variable exactly matches the type of the corresponding Camera2D built-in property.

### 4. Clarifying Questions

None.

---

## Summary Table

| SPEC | Title | File(s) Affected | Headless Testable | Manual Required |
|---|---|---|---|---|
| SPEC-37 | File/class structure | `scripts/camera_follow.gd` | Yes (syntax check) | No |
| SPEC-38 | Exported configuration parameters | `scripts/camera_follow.gd` | Yes (property read) | No |
| SPEC-39 | `_ready()` initialization | `scripts/camera_follow.gd` | Yes (property assignment) | No |
| SPEC-40 | Smoothing behavior | `scripts/camera_follow.gd` | Partial (config only) | Yes (MAN-01, MAN-02, MAN-05) |
| SPEC-41 | Dead zone / drag margin behavior | `scripts/camera_follow.gd` | Partial (config only) | Yes (MAN-03) |
| SPEC-42 | Level bounds limiting | `scripts/camera_follow.gd` | Partial (config only) | Yes (MAN-04) |
| SPEC-43 | Scene wiring | `scenes/test_movement.tscn` | Yes (syntax check) | No |
| SPEC-44 | Manual acceptance checklist | (appended to ticket) | No | Yes (MAN-01 through MAN-06) |
| SPEC-45 | Non-functional requirements | `scripts/camera_follow.gd`, `scenes/test_movement.tscn` | Yes (static analysis) | No |
