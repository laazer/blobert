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

## Reference to the spawned chunk node. null when no chunk has been detached.
## Set on the frame the true→false has_chunk transition occurs (SPEC-52).
var _chunk_node: RigidBody2D = null

## Preloaded chunk scene. Instantiated on detach (SPEC-52).
const _CHUNK_SCENE = preload("res://scenes/chunk.tscn")


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
# Wall cling configuration parameters (SPEC-26 / Task 5)
#
# Exposed via @export so values are editable in the Godot inspector.
# Defaults match the simulation defaults. Copied to _simulation in _ready().
# ---------------------------------------------------------------------------

## Gravity multiplier while wall clinging. 0.0 = hover, 1.0 = normal gravity.
@export var cling_gravity_scale: float = 0.1

## Maximum duration (seconds) the player can cling to a wall per contact.
## A value of 0.0 disables cling entirely.
@export var max_cling_time: float = 1.5

## Target apex height of a wall jump in pixels.
@export var wall_jump_height: float = 100.0

## Horizontal launch speed in pixels per second when wall jumping.
@export var wall_jump_horizontal_speed: float = 180.0


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
	var project_gravity: float = ProjectSettings.get_setting("physics/2d/default_gravity", 980.0) as float
	_simulation.gravity = project_gravity

	# Copy jump configuration parameters to the simulation instance.
	# These are set from the @export vars so the inspector can tune them.
	_simulation.jump_height = jump_height
	_simulation.coyote_time = coyote_time
	_simulation.jump_cut_velocity = jump_cut_velocity

	# Copy wall cling configuration parameters to the simulation instance.
	_simulation.cling_gravity_scale = cling_gravity_scale
	_simulation.max_cling_time = max_cling_time
	_simulation.wall_jump_height = wall_jump_height
	_simulation.wall_jump_horizontal_speed = wall_jump_horizontal_speed

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
	# --- Step 1: Read input (AC-8.1, AC-23.1, SPEC-52) ---
	# Input.get_axis returns a value in [-1.0, 1.0].
	# Simultaneous left+right yields 0.0 (Godot built-in behavior).
	var input_axis: float = Input.get_axis("move_left", "move_right")
	var jump_pressed: bool = Input.is_action_pressed("jump")
	var jump_just_pressed: bool = Input.is_action_just_pressed("jump")
	var detach_just_pressed: bool = Input.is_action_just_pressed("detach")

	# --- Step 2: Build prior state (AC-8.2) ---
	# Update is_on_floor from the engine's floor detection result.
	# velocity was set at the end of the previous frame (Step 4) and is
	# already correct. On the first frame, velocity is Vector2.ZERO (from _ready()).
	_current_state.is_on_floor = is_on_floor()

	# Read wall contact state from the engine for this frame.
	# is_on_wall() returns true when CharacterBody2D is in contact with a wall.
	# get_wall_normal() returns Vector2.ZERO when not on a wall; guard .x access
	# behind is_on_wall() and pass 0.0 when not contacting a wall (per R2 in ticket).
	var is_on_wall_now: bool = is_on_wall()
	var wall_normal_x: float = 0.0
	if is_on_wall_now:
		wall_normal_x = get_wall_normal().x

	# --- Step 3: Simulate (AC-8.3) ---
	# Delegate all velocity math to the pure simulation. The controller
	# contains no movement formulas (AC-7.4).
	# SPEC-52: detach_just_pressed is read from Input above and passed here.
	var next_state: MovementSimulation.MovementState = _simulation.simulate(
		_current_state, input_axis, jump_pressed, jump_just_pressed, is_on_wall_now, wall_normal_x, detach_just_pressed, delta
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

	# Copy wall cling state fields back to _current_state so they persist across frames.
	# Mirrors the coyote_timer pattern: simulation output feeds into the next frame's
	# prior_state so cling duration and active-cling flag carry forward correctly.
	# ORDERING NOTE: is_on_floor must be updated (line 146) before these copy-backs.
	# If is_on_floor=true, simulate() will block cling_eligible regardless of
	# is_wall_clinging — preventing a phantom cling frame on the landing tick.
	_current_state.is_wall_clinging = next_state.is_wall_clinging
	_current_state.cling_timer = next_state.cling_timer

	# Copy has_chunk back to _current_state so the detach state persists across
	# frames (SPEC-52 item 4). Without this copy-back, has_chunk would reset to
	# its default (true) every frame via MovementState.new() in simulate().
	var prev_has_chunk: bool = _current_state.has_chunk
	_current_state.has_chunk = next_state.has_chunk

	# Spawn the chunk scene on the true→false transition (SPEC-52 item 5).
	# The chunk is added as a child of get_parent() so it does not move with
	# the player. It is positioned at the player's global_position at the
	# detach frame. _chunk_node is stored for future null-safe access.
	if prev_has_chunk and not _current_state.has_chunk:
		var chunk: RigidBody2D = _CHUNK_SCENE.instantiate()
		chunk.global_position = global_position
		get_parent().add_child(chunk)
		_chunk_node = chunk
