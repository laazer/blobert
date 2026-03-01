# player_controller.gd
#
# Engine-integration layer for blobert's movement system.
# Wires MovementSimulation to Godot's physics loop and input system.
#
# Spec coverage implemented:
#   SPEC-7  — File and class structure (extends CharacterBody2D, class_name PlayerController)
#   SPEC-8  — _physics_process() four-step data flow
#   SPEC-9  — Member variables and _ready() initialization
#
# Architectural constraints (enforced here):
#   - No movement math in this file. All velocity computation lives in MovementSimulation.
#   - Input.get_axis() called exactly once per physics frame, in _physics_process() only.
#   - move_and_slide() called exactly once per physics frame, in _physics_process() only.
#   - MovementSimulation is instantiated directly (not as a node), keeping it engine-agnostic.

class_name PlayerController
extends CharacterBody2D

# Preload the simulation script under the same name as its class_name declaration.
# This const shadows the global class_name "MovementSimulation" in this file's scope
# and allows using it as a type hint: var x: MovementSimulation and accessing the
# inner class as MovementSimulation.MovementState. This pattern works in all contexts
# (headless --check-only, headless runner, in-editor) without a warm class_name cache.
const MovementSimulation = preload("res://scripts/movement_simulation.gd")


# ---------------------------------------------------------------------------
# Member variables (AC-9.1, AC-9.2)
#
# Both are private by naming convention (underscore prefix).
# Neither is @export — they are internal implementation details.
# Initializers are omitted from the declaration lines; initialization
# occurs in _ready() (AC-9.4 through AC-9.6).
# ---------------------------------------------------------------------------

## The pure simulation instance. Holds all movement configuration parameters.
## Initialized in _ready() via MovementSimulation.new().
var _simulation: MovementSimulation

## The persistent per-frame kinematic state. Passed as prior_state to simulate()
## each frame and updated with the engine-corrected post-slide velocity at the
## end of each frame. Initialized in _ready() with default (zero) state.
var _current_state: MovementSimulation.MovementState


# ---------------------------------------------------------------------------
# Jump configuration parameters (SPEC-23 / AC-23.*)
#
# Exposed via @export so values are editable in the Godot inspector.
# Copied to _simulation in _ready() after instantiation.
# ---------------------------------------------------------------------------

## Target apex height of a jump in pixels. Passed to MovementSimulation.jump_height.
@export var jump_height: float = 120.0

## Coyote time window in seconds. Passed to MovementSimulation.coyote_time.
@export var coyote_time: float = 0.1

## Minimum upward velocity cap when jump is released early. Passed to
## MovementSimulation.jump_cut_velocity. Negative = upward in Godot 2D.
@export var jump_cut_velocity: float = -200.0


# ---------------------------------------------------------------------------
# _ready() — Lifecycle initialization (SPEC-9)
#
# AC-9.3: Signature is func _ready() -> void.
# AC-9.4: Instantiates _simulation via MovementSimulation.new().
# AC-9.5: Overrides _simulation.gravity with the project's actual gravity setting.
# AC-9.6: Allocates the initial _current_state with default (zero) values.
# AC-9.7: No other movement-related initialization occurs here.
# ---------------------------------------------------------------------------
func _ready() -> void:
	_simulation = MovementSimulation.new()

	# Read the project's 2D gravity setting and override the simulation default.
	# This ensures the simulation matches the physics world without hardcoding 980.0
	# in the controller. ProjectSettings is an engine call isolated to this file.
	var project_gravity: float = float(ProjectSettings.get_setting("physics/2d/default_gravity", 980.0))
	_simulation.gravity = project_gravity

	# Copy jump configuration parameters to the simulation instance.
	# These are set from the @export vars so the inspector can tune them.
	_simulation.jump_height = jump_height
	_simulation.coyote_time = coyote_time
	_simulation.jump_cut_velocity = jump_cut_velocity

	# Allocate the initial persistent state. velocity defaults to Vector2.ZERO
	# and is_on_floor defaults to false — correct starting state for the first frame.
	_current_state = MovementSimulation.MovementState.new()


# ---------------------------------------------------------------------------
# _physics_process() — Per-frame movement pipeline (SPEC-8)
#
# Executes a strict four-step sequence every physics frame. Steps must occur
# in this exact order. No coroutines, no deferred calls.
#
# AC-8.1 Step 1: Read input axis.
# AC-8.2 Step 2: Update prior state's is_on_floor from the engine.
# AC-8.3 Step 3: Call simulate() to compute next velocity.
# AC-8.4 Step 4: Apply simulated velocity, slide, capture post-slide result.
# AC-8.5: After this method completes, _current_state.velocity == self.velocity.
# AC-8.6: No input reading, velocity arithmetic, or move_and_slide() outside here.
# ---------------------------------------------------------------------------
func _physics_process(delta: float) -> void:
	# --- Step 1: Read input (AC-8.1, AC-23.1) ---
	# Input.get_axis returns a value in [-1.0, 1.0].
	# Simultaneous left+right yields 0.0 (Godot built-in behavior).
	var input_axis: float = Input.get_axis("move_left", "move_right")
	var jump_pressed: bool = Input.is_action_pressed("jump")
	var jump_just_pressed: bool = Input.is_action_just_pressed("jump")

	# --- Step 2: Build prior state (AC-8.2) ---
	# Update is_on_floor from the engine's floor detection result.
	# velocity was set at the end of the previous frame (Step 4) and is
	# already correct. On the first frame, velocity is Vector2.ZERO (from _ready()).
	_current_state.is_on_floor = is_on_floor()

	# --- Step 3: Simulate (AC-8.3) ---
	# Delegate all velocity math to the pure simulation. The controller
	# contains no movement formulas (AC-7.4).
	var next_state: MovementSimulation.MovementState = _simulation.simulate(
		_current_state, input_axis, jump_pressed, jump_just_pressed, delta
	)

	# --- Step 4: Apply and slide (AC-8.4) ---
	# Write the simulated velocity to CharacterBody2D.velocity, then let
	# the physics engine resolve collisions via move_and_slide(). After the
	# slide, self.velocity reflects the engine-corrected (post-collision) value.
	velocity = next_state.velocity
	move_and_slide()

	# Capture the engine-corrected post-slide velocity for next frame's prior state.
	# This is the key handoff between the engine and the simulation: the engine's
	# collision resolution (e.g., zeroing velocity.y on floor contact) feeds back
	# into the simulation as the starting velocity for the next tick.
	_current_state.velocity = velocity

	# Copy jump state fields back to _current_state so they persist across frames.
	# Without this, coyote_timer and jump_consumed always start from their default
	# values on the next frame, silently breaking coyote time and double-jump prevention.
	# (AC-23.3)
	_current_state.coyote_timer = next_state.coyote_timer
	_current_state.jump_consumed = next_state.jump_consumed
