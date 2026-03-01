# movement_simulation.gd
#
# Pure movement simulation for blobert. No Node, Input, or engine singleton
# references. Fully testable headlessly.
#
# Spec coverage implemented:
#   SPEC-1  — File and class structure
#   SPEC-2  — MovementState inner class
#   SPEC-3  — Exported configuration parameters
#   SPEC-4  — simulate() public API
#   SPEC-5  — Horizontal movement formula (all four cases)
#   SPEC-6  — Vertical movement formula (gravity, unconditional)
#   SPEC-12 — Frame-rate independence (all rates scaled by delta)
#   SPEC-13 — Headless instantiability (no engine singletons)
#   SPEC-14 — Typed GDScript throughout
#   SPEC-15 — MovementState new fields: coyote_timer, jump_consumed
#   SPEC-16 — MovementSimulation new config parameters: jump_height, coyote_time, jump_cut_velocity
#   SPEC-17 — simulate() extended signature with jump_pressed, jump_just_pressed
#   SPEC-18 — Jump impulse condition and formula
#   SPEC-19 — Coyote time logic
#   SPEC-20 — Jump cut condition and clamp
#   SPEC-21 — Double-jump prevention via jump_consumed
#   SPEC-24 — Frame-rate independence of new timer logic

class_name MovementSimulation
extends RefCounted


# ---------------------------------------------------------------------------
# Inner class: MovementState
#
# Holds the complete kinematic state of the character at a single point in
# time. simulate() reads this as read-only input and constructs a fresh
# instance as output — prior_state is never mutated.
#
# AC-2.1: velocity: Vector2 = Vector2.ZERO
# AC-2.2: is_on_floor: bool = false
# AC-2.3: MovementState.new() with no arguments produces those defaults.
# AC-15.2: coyote_timer: float = 0.0
# AC-15.3: jump_consumed: bool = false
# AC-15.7: Total field count is exactly four.
# ---------------------------------------------------------------------------
class MovementState:
	var velocity: Vector2 = Vector2.ZERO
	var is_on_floor: bool = false
	var coyote_timer: float = 0.0
	var jump_consumed: bool = false


# ---------------------------------------------------------------------------
# Configuration parameters (AC-3.1 through AC-3.7, AC-16.1 through AC-16.7)
#
# Plain var declarations — this class extends RefCounted, not Node, so
# @export and @export_category have no inspector effect and are omitted.
# Inspector-facing configuration lives on PlayerController (a Node).
# All values are float with explicit defaults.
# Undefined behavior for negative values; zero is valid.
# ---------------------------------------------------------------------------

## Maximum horizontal speed in pixels per second.
## move_toward caps at this target naturally — no explicit clamp required,
## though the result is bounded by the target passed to move_toward.
var max_speed: float = 200.0

## Rate of horizontal velocity increase toward max_speed when directional
## input is held, in pixels per second squared.
## Applied via move_toward when on floor OR airborne with input.
var acceleration: float = 800.0

## Rate of horizontal velocity decrease toward zero when no directional
## input is given and is_on_floor is true, in pixels per second squared.
var friction: float = 1200.0

## Rate of horizontal velocity decrease toward zero when airborne and no
## directional input is given, in pixels per second squared.
## Default 0.0 = no air friction in Milestone 1.
var air_deceleration: float = 0.0

## Gravitational acceleration in pixels per second squared.
## Applied unconditionally every tick (including when is_on_floor is true).
## Positive values accelerate downward (Godot 2D screen-space Y increases
## downward). Default matches Godot 4's 2D physics default gravity.
var gravity: float = 980.0

## Target apex height of a jump in pixels. The jump impulse is derived
## at runtime via the kinematic formula: impulse = sqrt(2 * gravity * jump_height).
## A value of 0.0 produces a zero impulse (no height). Negative values are
## undefined behavior; the implementation guards sqrt(negative) as a zero impulse.
var jump_height: float = 120.0

## Coyote time window in seconds. After leaving the floor, the player may
## still jump for this many seconds. A value of 0.0 disables coyote time.
## Negative values are undefined behavior.
var coyote_time: float = 0.1

## Minimum upward velocity cap (pixels/second) when jump is released early.
## Negative values are upward in Godot 2D screen space. Default -200.0 gives
## a short hop of approximately 20px when the button is tapped and released.
## A value of 0.0 means releasing the button immediately zeroes all upward
## velocity. Positive values are undefined behavior (config error).
var jump_cut_velocity: float = -200.0


# ---------------------------------------------------------------------------
# simulate()
#
# Public API entry point. Reads prior_state and input, returns a new
# MovementState. Does NOT mutate prior_state.
#
# Normative order of operations (SPEC normative summary):
#   1. Compute effective_delta = max(0.0, delta)
#   2. Sanitize input_axis (NaN → 0.0; Inf/-Inf → clamp ±1.0)
#   3. Allocate result: MovementState
#   4. Coyote timer update (SPEC-19):
#        if prior_state.is_on_floor → result.coyote_timer = coyote_time
#        else → result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)
#   5. jump_consumed carry-forward / landing reset (SPEC-21):
#        if prior_state.is_on_floor → result.jump_consumed = false
#        else → result.jump_consumed = prior_state.jump_consumed
#   6. Jump eligibility and impulse (SPEC-18):
#        eligible = jump_just_pressed AND (prior_state.is_on_floor OR prior_state.coyote_timer > 0.0)
#                   AND NOT prior_state.jump_consumed
#        if eligible → result.velocity.y = -sqrt(2 * gravity * jump_height); result.jump_consumed = true
#        else → result.velocity.y = prior_state.velocity.y
#   7. Horizontal velocity (SPEC-5, cases 1-4)
#   8. Gravity (SPEC-6): result.velocity.y += gravity * effective_delta
#   9. Jump cut (SPEC-20):
#        if NOT jump_pressed AND result.velocity.y < jump_cut_velocity
#            → result.velocity.y = jump_cut_velocity
#  10. is_on_floor pass-through (AC-4.3): result.is_on_floor = prior_state.is_on_floor
#  11. Return result
#
# AC-17.1: Exact signature.
# AC-4.2:  Allocates and returns a new MovementState; prior_state is read-only.
# AC-4.3:  result.is_on_floor == prior_state.is_on_floor (pass-through).
# AC-4.4:  delta == 0.0 → no velocity change.
# AC-4.5:  Only move_toward, clamp, is_nan, max, sqrt, and arithmetic appear here.
# ---------------------------------------------------------------------------
func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, delta: float) -> MovementState:
	# --- 1. Sanitize delta (robustness) ---
	#
	# Clamp delta to [0.0, +inf). Negative delta is undefined behavior per the
	# spec; clamping to zero makes the simulation idempotent (no state change)
	# rather than corrupting state with anti-gravity or reversed acceleration.
	var effective_delta: float = max(0.0, delta)

	# --- 2. Sanitize input_axis ---
	#
	# NaN cannot be safely clamped (NaN comparisons are always false), so it
	# must be explicitly detected and replaced. Inf/-Inf is handled correctly
	# by clamp().
	var safe_axis: float
	if is_nan(input_axis):
		safe_axis = 0.0
	else:
		safe_axis = clamp(input_axis, -1.0, 1.0)

	# --- 3. Construct result (never mutate prior_state) ---
	var result: MovementState = MovementState.new()

	# --- 4. Coyote timer update (SPEC-19) ---
	#
	# Reset timer to full window when grounded; decrement when airborne.
	# The eligibility check in step 6 reads prior_state.coyote_timer (not
	# result.coyote_timer), so this update does not affect the current frame's
	# jump eligibility — only the next frame's.
	if prior_state.is_on_floor:
		# AC-19.1, AC-19.2: Floor frame always resets to full window.
		result.coyote_timer = coyote_time
	else:
		# AC-19.3, AC-19.4, AC-19.5: Airborne: decrement, clamped to zero.
		result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)

	# --- 5. jump_consumed carry-forward / landing reset (SPEC-21) ---
	#
	# On a grounded frame (prior_state.is_on_floor), reset consumed so the
	# player can jump again. While airborne, carry the flag forward.
	# Step 6 may override this to true if a jump fires this frame.
	if prior_state.is_on_floor:
		# AC-21.3: Landing (or staying grounded) resets consumed.
		result.jump_consumed = false
	else:
		# AC-21.4: Carry forward when airborne (no jump this frame yet).
		result.jump_consumed = prior_state.jump_consumed

	# --- 6. Jump eligibility and impulse (SPEC-18) ---
	#
	# Eligibility requires all three conditions simultaneously:
	#   (a) jump_just_pressed is true (fresh press on this frame)
	#   (b) grounded OR coyote window still open (prior_state.coyote_timer > 0.0)
	#   (c) jump not already consumed during this airborne phase
	#
	# Note: eligibility reads prior_state.coyote_timer (not result.coyote_timer)
	# to preserve the ordering constraint: timer update happens first but
	# eligibility is evaluated against the pre-update value (AC-19.6, AC-19.7).
	var floor_or_coyote: bool = prior_state.is_on_floor or (prior_state.coyote_timer > 0.0)
	var eligible: bool = jump_just_pressed and floor_or_coyote and (not prior_state.jump_consumed)

	if eligible:
		# Guard against sqrt(negative) producing NaN for invalid jump_height.
		# Negative jump_height is undefined behavior per SPEC-16; treat as zero
		# impulse to preserve the finiteness invariant.
		var safe_jump_height: float = jump_height if jump_height > 0.0 else 0.0
		# AC-18.1, AC-18.5: Kinematic peak-height formula.
		result.velocity.y = -sqrt(2.0 * gravity * safe_jump_height)
		# AC-21.1: Mark jump as consumed so double-jump is blocked.
		result.jump_consumed = true
	else:
		# AC-18.2, AC-18.3, AC-18.4: Carry forward vertical velocity unchanged.
		result.velocity.y = prior_state.velocity.y

	# --- 7. Horizontal velocity (SPEC-5) ---
	#
	# Four mutually exclusive cases based on is_on_floor and input_axis:
	#
	#   Case 1 (AC-5.1): Grounded + input → accelerate toward target
	#   Case 2 (AC-5.2): Grounded + no input → friction toward zero
	#   Case 3 (AC-5.3): Airborne + input → accelerate toward target (same formula as Case 1)
	#   Case 4 (AC-5.4): Airborne + no input → air deceleration toward zero
	if safe_axis != 0.0:
		# Cases 1 and 3: directional input held (grounded or airborne).
		var target_vx: float = safe_axis * max_speed
		result.velocity.x = move_toward(prior_state.velocity.x, target_vx, acceleration * effective_delta)
	elif prior_state.is_on_floor:
		# Case 2: grounded, no input — apply friction.
		result.velocity.x = move_toward(prior_state.velocity.x, 0.0, friction * effective_delta)
	else:
		# Case 4: airborne, no input — apply air deceleration.
		result.velocity.x = move_toward(prior_state.velocity.x, 0.0, air_deceleration * effective_delta)

	# --- 8. Gravity (SPEC-6) ---
	#
	# Applied unconditionally after the jump impulse. On the jump frame,
	# result.velocity.y = impulse + gravity * delta.
	result.velocity.y += gravity * effective_delta

	# --- 9. Jump cut (SPEC-20) ---
	#
	# If the jump button is not held and the character is ascending faster
	# than the cut threshold, clamp upward velocity to the cut velocity.
	# This allows variable-height jumping by releasing the button early.
	# Condition uses strict less-than so exact boundary is a no-op (AC-20.5).
	# Does not apply when falling (positive velocity.y cannot be < -200.0 by default).
	if not jump_pressed and result.velocity.y < jump_cut_velocity:
		result.velocity.y = jump_cut_velocity

	# --- 10. is_on_floor pass-through (AC-4.3) ---
	#
	# The engine controller updates is_on_floor after move_and_slide().
	# The simulation only passes it through; the controller writes the real
	# contact result back to _current_state after each physics frame.
	result.is_on_floor = prior_state.is_on_floor

	return result
