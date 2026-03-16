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
#   SPEC-25 — MovementState new fields: is_wall_clinging, cling_timer
#   SPEC-26 — New config parameters: cling_gravity_scale, max_cling_time, wall_jump_height, wall_jump_horizontal_speed
#   SPEC-27 — simulate() extended 7-arg signature with is_on_wall, wall_normal_x
#   SPEC-28 — Pressing-toward-wall detection formula
#   SPEC-29 — Cling eligibility: all 5 conditions
#   SPEC-30 — Cling state update: timer accumulation and reset
#   SPEC-31 — Cling gravity modification
#   SPEC-32 — Wall jump eligibility
#   SPEC-33 — Wall jump impulse
#   SPEC-34 — Order of operations (normative 11-step)
#   SPEC-35 — Call-site migration (handled by existing test files)
#   SPEC-36 — Frame-rate independence of wall cling timer and gravity
#   SPEC-46 — MovementState new field: has_chunk
#   SPEC-47 — has_chunk default value semantics
#   SPEC-48 — Detach step (step 17, final step): detach eligibility, result, order of operations
#   SPEC-49 — simulate() extended 8-arg signature with detach_just_pressed
#   SPEC-54 — MovementState new field: current_hp
#   SPEC-55 — HP config vars: max_hp, hp_cost_per_detach, min_hp
#   SPEC-56 — HP reduction step (step 18) on detach frames
#   SPEC-57 — HP carry-forward on non-detach frames
#   SPEC-58 — HP floor clamp using min_hp
#   SPEC-59 — simulate() signature remains 8 args (no HP args)
#   SPEC-61 — prior_state.current_hp immutability
#   SPEC-SCL-1 — MovementState new field: has_chunks (replaces has_chunk_2)
#   SPEC-SCL-2 — has_chunks default semantics; simulate() never sets has_chunks[i]=true
#   SPEC-SCL-3 — Detach step 2 (step 19): detach_2 eligibility, result, order of operations
#   SPEC-SCL-4 — simulate() extended 9-arg signature with detach_2_just_pressed as last arg
#   SPEC-SCL-5 — HP reduction step 2 (step 20) on detach_2 frames; reads result.current_hp
#   SPEC-SCL-6 — Independence invariant: has_chunks[0] and has_chunks[1] are fully independent

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
# AC-25.1: is_wall_clinging: bool = false
# AC-25.1: cling_timer: float = 0.0
# AC-46.1: has_chunks[0] = true (slot 1), has_chunks[1] = true (slot 2) at construction
# AC-54.3: current_hp: float = 100.0 (default literal)
# SPEC-SCL-1: has_chunks: Array = [true, true] (index 0 = slot 1, index 1 = slot 2)
# ---------------------------------------------------------------------------
class MovementState:
	var velocity: Vector2 = Vector2.ZERO
	var is_on_floor: bool = false
	var coyote_timer: float = 0.0
	var jump_consumed: bool = false
	var is_wall_clinging: bool = false
	var cling_timer: float = 0.0
	var has_chunks: Array = [true, true]  # index 0 = slot 1, index 1 = slot 2
	var current_hp: float = 100.0


# ---------------------------------------------------------------------------
# Configuration parameters (AC-3.1 through AC-3.7, AC-16.1 through AC-16.7,
# AC-26.1 through AC-26.8)
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

## Gravity multiplier while wall clinging. Scales the per-frame gravity
## contribution so the player slides down slowly. A value of 0.0 produces
## zero downward acceleration (hover). A value of 1.0 gives normal gravity.
## Default 0.1.
var cling_gravity_scale: float = 0.1

## Maximum duration (seconds) the player can cling to a wall per contact.
## Uses strict less-than comparison: cling_timer < max_cling_time.
## A value of 0.0 disables cling entirely (0.0 < 0.0 is false on first frame).
## Default 1.5.
var max_cling_time: float = 1.5

## Target apex height of a wall jump in pixels. Computed via the same
## kinematic formula as jump_height. Negative values are guarded to 0.0.
## Default 100.0.
var wall_jump_height: float = 100.0

## Horizontal launch speed in pixels per second when wall jumping.
## Applied as: result.velocity.x = wall_normal_x * wall_jump_horizontal_speed.
## A value of 0.0 produces a purely vertical wall jump.
## Default 180.0.
var wall_jump_horizontal_speed: float = 180.0


# ---------------------------------------------------------------------------
# HP configuration parameters (SPEC-55)
#
# These are used by the HP reduction step (step 18) and are exercised by
# tests in test_hp_reduction_simulation.gd. All three are independently
# mutable and have explicit float defaults.
# ---------------------------------------------------------------------------

## Maximum HP cap used only as an upper bound for recall/other systems;
## it does NOT participate in the detach HP reduction formula (SPEC-55.5).
var max_hp: float = 100.0

## HP cost applied once per successful detach frame (SPEC-56). The detach
## step computes a boolean detach_eligible; when true, current_hp is reduced
## by this amount and clamped at min_hp.
var hp_cost_per_detach: float = 25.0

## Minimum HP floor applied at the reduction site only (SPEC-58). Detach
## frames compute max(min_hp, prior_hp - hp_cost_per_detach). Other systems
## are free to clamp or cap against max_hp separately.
var min_hp: float = 0.0


# ---------------------------------------------------------------------------
# simulate()
#
# Public API entry point. Reads prior_state and input, returns a new
# MovementState. Does NOT mutate prior_state.
#
# Normative order of operations (SPEC-34 extended to 17 steps — SPEC-48):
#   1.  Compute effective_delta = max(0.0, delta)
#   2.  Sanitize input_axis (NaN → 0.0; clamp to ±1.0)
#   3.  Sanitize wall_normal_x (NaN → 0.0; clamp to ±1.0) — prevents NaN propagation
#   4.  Compute pressing_toward_wall = (safe_axis * safe_wall_normal_x) < 0.0
#   5.  Coyote timer (same as M1-002):
#         if prior_state.is_on_floor → result.coyote_timer = coyote_time
#         else → result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)
#   6.  jump_consumed carry-forward / landing reset (same as M1-002):
#         if prior_state.is_on_floor → result.jump_consumed = false
#         else → result.jump_consumed = prior_state.jump_consumed
#   7.  Regular jump eligibility:
#         jump_just_pressed AND (is_on_floor OR coyote_timer > 0) AND NOT prior_state.jump_consumed
#   8.  Cling eligibility:
#         is_on_wall AND NOT is_on_floor AND pressing_toward_wall
#         AND NOT prior_state.jump_consumed AND prior_state.cling_timer < max_cling_time
#         NOTE: uses prior_state.cling_timer (before updating).
#   9.  Update cling state:
#         if cling_eligible → result.is_wall_clinging=true,
#                             result.cling_timer = prior_state.cling_timer + effective_delta
#         else → result.is_wall_clinging=false, result.cling_timer=0.0
#  10.  Wall jump eligibility:
#         jump_just_pressed AND prior_state.is_wall_clinging AND NOT prior_state.jump_consumed
#  11.  Branch on jump path:
#         If regular_jump_eligible → apply jump impulse (SPEC-18 formula),
#                                    result.jump_consumed=true, result.is_wall_clinging=false,
#                                    then fall through to horizontal step (step 12)
#         Elif wall_jump_eligible → result.velocity.y = -sqrt(2*gravity*safe_wj_height) + gravity*delta;
#                                   result.velocity.x = safe_wall_normal_x * wall_jump_horizontal_speed;
#                                   result.jump_consumed=true; result.is_wall_clinging=false;
#                                   SKIP step 12 (horizontal formula)
#         Else → carry result.velocity.y from prior; run step 12 (horizontal formula)
#  12.  Horizontal velocity (SPEC-5, cases 1–4) — skipped when wall jump fired
#  13.  Apply gravity:
#         if result.is_wall_clinging → result.velocity.y += gravity * cling_gravity_scale * effective_delta
#         else → result.velocity.y += gravity * effective_delta
#  14.  Jump cut (SPEC-20):
#         if NOT jump_pressed AND result.velocity.y < jump_cut_velocity → clamp
#  15.  is_on_floor pass-through: result.is_on_floor = prior_state.is_on_floor
#  16.  (formerly step 15 — renumbered for clarity; same operation)
#         Note: step 15 is the is_on_floor pass-through above; this comment
#         block continues the sequence for the detach step below.
#  17.  Chunk detach (SPEC-48):
#         detach_eligible = detach_just_pressed AND prior_state.has_chunks[0]
#         if detach_eligible → result.has_chunks[0] = false
#         else → result.has_chunks[0] = prior_state.has_chunks[0] (carry-forward)
#         Reads: detach_just_pressed, prior_state.has_chunks[0]
#         Writes: result.has_chunks[0] only — no other fields affected
#  18.  HP reduction on detach (SPEC-56):
#         if detach_eligible →
#             result.current_hp = max(min_hp, prior_state.current_hp - hp_cost_per_detach)
#         else →
#             result.current_hp = prior_state.current_hp
#         Reads: detach_eligible, prior_state.current_hp, hp_cost_per_detach, min_hp
#         Writes: result.current_hp only — no other fields affected
#  19.  Chunk 2 detach (SPEC-SCL-3):
#         detach_2_eligible = detach_2_just_pressed AND prior_state.has_chunks[1]
#         if detach_2_eligible → result.has_chunks[1] = false
#         else → result.has_chunks[1] = prior_state.has_chunks[1] (carry-forward)
#         Reads: detach_2_just_pressed, prior_state.has_chunks[1]
#         Writes: result.has_chunks[1] only — no other fields affected
#         Independence: has_chunks[1] is fully independent of has_chunks[0] (SPEC-SCL-6)
#  20.  HP reduction for chunk 2 detach (SPEC-SCL-5):
#         if detach_2_eligible →
#             result.current_hp = max(min_hp, result.current_hp - hp_cost_per_detach)
#         else →
#             result.current_hp = result.current_hp (no change from step 18 output)
#         Reads: detach_2_eligible, result.current_hp (output of step 18), hp_cost_per_detach, min_hp
#         Writes: result.current_hp only — no other fields affected
#         Note: reads result.current_hp (not prior_state.current_hp) so dual-detach
#         on the same frame produces cumulative HP reductions (SPEC-SCL-5 key detail).
#
# AC-27.1: Exact signature.
# AC-49.1: detach_just_pressed is position 7 (before delta).
# SPEC-SCL-4: detach_2_just_pressed is position 9 (last, after delta); default=false
#             preserves all existing 8-argument call sites.
# AC-4.2:  Allocates and returns a new MovementState; prior_state is read-only.
# AC-4.3:  result.is_on_floor == prior_state.is_on_floor (pass-through).
# AC-4.4:  delta == 0.0 → no velocity change (from gravity/timer terms).
# ---------------------------------------------------------------------------
func simulate(prior_state: MovementState, input_axis: float, jump_pressed: bool, jump_just_pressed: bool, is_on_wall: bool, wall_normal_x: float, detach_just_pressed: bool, delta: float, detach_2_just_pressed: bool = false) -> MovementState:
	# --- 1. Sanitize delta ---
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

	# --- 3. Sanitize wall_normal_x (SPEC-34 step 3) ---
	#
	# NaN wall_normal_x must not propagate into pressing_toward_wall evaluation
	# or wall jump velocity formula. Inf must be clamped to ±1.0 for the same
	# reason. After sanitization, safe_wall_normal_x is always in [-1.0, 1.0].
	var safe_wall_normal_x: float
	if is_nan(wall_normal_x):
		safe_wall_normal_x = 0.0
	else:
		safe_wall_normal_x = clamp(wall_normal_x, -1.0, 1.0)

	# --- 4. Pressing-toward-wall detection (SPEC-28) ---
	#
	# Product is negative only when input_axis and wall_normal_x have opposite
	# signs — exactly the condition of pushing into the wall.
	# wall_normal_x=0.0 always produces 0.0*axis=0.0 which is not < 0.0,
	# so cling is correctly blocked when the normal is zero.
	var pressing_toward_wall: bool = (safe_axis * safe_wall_normal_x) < 0.0

	# --- 5. Allocate result ---
	var result: MovementState = MovementState.new()

	# --- 6. Coyote timer update (SPEC-19) ---
	#
	# Reset timer to full window when grounded; decrement when airborne.
	# The eligibility check in step 9 reads prior_state.coyote_timer (not
	# result.coyote_timer), so this update does not affect the current frame's
	# jump eligibility — only the next frame's.
	if prior_state.is_on_floor:
		# AC-19.1, AC-19.2: Floor frame always resets to full window.
		result.coyote_timer = coyote_time
	else:
		# AC-19.3, AC-19.4, AC-19.5: Airborne: decrement, clamped to zero.
		result.coyote_timer = max(0.0, prior_state.coyote_timer - effective_delta)

	# --- 7. jump_consumed carry-forward / landing reset (SPEC-21) ---
	#
	# On a grounded frame (prior_state.is_on_floor), reset consumed so the
	# player can jump again. While airborne, carry the flag forward.
	# Steps 11 or 13 may override this to true if a jump fires this frame.
	if prior_state.is_on_floor:
		# AC-21.3: Landing (or staying grounded) resets consumed.
		result.jump_consumed = false
	else:
		# AC-21.4: Carry forward when airborne (no jump this frame yet).
		result.jump_consumed = prior_state.jump_consumed

	# --- 8. Cling eligibility (SPEC-29) ---
	#
	# Five simultaneous conditions (all must be true):
	#   (a) is_on_wall == true
	#   (b) NOT prior_state.is_on_floor (floor takes priority — SPEC-34)
	#   (c) pressing_toward_wall == true
	#   (d) NOT prior_state.jump_consumed (mid-air jump blocks cling)
	#   (e) prior_state.cling_timer < max_cling_time (strict less-than; 0.0<0.0 is false)
	#
	# Uses prior_state.cling_timer (before update) so eligibility is evaluated
	# against the accumulated time up to this frame.
	var cling_eligible: bool = (
		is_on_wall
		and not prior_state.is_on_floor
		and pressing_toward_wall
		and not prior_state.jump_consumed
		and prior_state.cling_timer < max_cling_time
	)

	# --- 9. Update cling state (SPEC-30) ---
	#
	# If eligible: activate cling and accumulate timer by effective_delta.
	# If not eligible: deactivate cling and reset timer to 0.0 immediately.
	# The reset is unconditional on non-eligible frames — this ensures that
	# returning to the wall after a break starts a fresh timer (AC-30.3).
	if cling_eligible:
		result.is_wall_clinging = true
		result.cling_timer = prior_state.cling_timer + effective_delta
	else:
		result.is_wall_clinging = false
		result.cling_timer = 0.0

	# --- 10. Wall jump eligibility (SPEC-32) ---
	#
	# Reads prior_state.is_wall_clinging — at least one confirmed cling frame
	# is required before a wall jump is available. This prevents wall jumping
	# on the very first frame of contact.
	var wall_jump_eligible: bool = (
		jump_just_pressed
		and prior_state.is_wall_clinging
		and not prior_state.jump_consumed
	)

	# --- 11. Regular jump eligibility (SPEC-18) ---
	#
	# Eligibility requires all three conditions simultaneously:
	#   (a) jump_just_pressed is true (fresh press on this frame)
	#   (b) grounded OR coyote window still open (prior_state.coyote_timer > 0.0)
	#   (c) jump not already consumed during this airborne phase
	#
	# Note: reads prior_state.coyote_timer (not result.coyote_timer) to preserve
	# the ordering constraint (AC-19.6, AC-19.7).
	var floor_or_coyote: bool = prior_state.is_on_floor or (prior_state.coyote_timer > 0.0)
	var regular_jump_eligible: bool = jump_just_pressed and floor_or_coyote and (not prior_state.jump_consumed)

	# --- 12. Apply jump path (SPEC-34 step 11) ---
	#
	# Priority order: regular jump > wall jump > no jump.
	# Regular jump fires when grounded or within coyote window — takes
	# absolute precedence over wall jump per SPEC-34 AC-34.1.
	#
	# Wall jump skips step 12 (horizontal formula) entirely — the formula
	# is replaced by the wall_normal_x * speed assignment (SPEC-34 AC-34.2).
	var wall_jump_fired: bool = false

	if regular_jump_eligible:
		# Guard against sqrt(negative) producing NaN for invalid jump_height.
		var safe_jump_height: float = jump_height if jump_height > 0.0 else 0.0
		# AC-18.1, AC-18.5: Kinematic peak-height formula.
		result.velocity.y = -sqrt(2.0 * gravity * safe_jump_height)
		# AC-21.1: Mark jump as consumed so double-jump is blocked.
		result.jump_consumed = true
		# Regular jump clears cling state (cannot be clinging while regular-jumping).
		result.is_wall_clinging = false

	elif wall_jump_eligible:
		# Guard against sqrt(negative) producing NaN for invalid wall_jump_height.
		var safe_wall_jump_height: float = wall_jump_height if wall_jump_height > 0.0 else 0.0
		# SPEC-33: Wall jump vertical impulse (kinematic formula, same structure as regular jump).
		# Gravity is added immediately after (step 13) so the formula becomes:
		# result.velocity.y = -sqrt(2*gravity*safe_wall_jump_height) + gravity*effective_delta
		# We assign the impulse here; gravity step adds the delta term below.
		result.velocity.y = -sqrt(2.0 * gravity * safe_wall_jump_height)
		# SPEC-33: Wall jump horizontal impulse replaces step 12 entirely.
		# wall_normal_x points away from the wall; multiplying by positive speed
		# launches the player away from the wall.
		result.velocity.x = safe_wall_normal_x * wall_jump_horizontal_speed
		result.jump_consumed = true
		result.is_wall_clinging = false
		wall_jump_fired = true

	else:
		# No jump — carry vertical velocity forward.
		result.velocity.y = prior_state.velocity.y

	# --- 13. Horizontal velocity (SPEC-5) — SKIPPED when wall jump fired ---
	#
	# Wall jump replaces this step entirely with a fixed horizontal impulse.
	# When wall jump did not fire, apply the four-case horizontal formula.
	#
	#   Case 1 (AC-5.1): Grounded + input → accelerate toward target
	#   Case 2 (AC-5.2): Grounded + no input → friction toward zero
	#   Case 3 (AC-5.3): Airborne + input → accelerate toward target (same formula as Case 1)
	#   Case 4 (AC-5.4): Airborne + no input → air deceleration toward zero
	if not wall_jump_fired:
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

	# --- 14. Gravity (SPEC-6 and SPEC-31) ---
	#
	# Applied unconditionally after jump impulse. The gravity step gate is
	# result.is_wall_clinging (the current frame's cling state, not prior_state).
	# When wall jump fires, result.is_wall_clinging is already set to false,
	# so normal gravity applies on wall-jump frames (SPEC-31 AC-31.6).
	#
	# On the regular jump frame: result.velocity.y = impulse + gravity*delta.
	# On the wall jump frame: result.velocity.y = impulse + gravity*delta.
	# On non-jump cling frames: result.velocity.y += gravity * cling_gravity_scale * delta.
	# On non-jump non-cling frames: result.velocity.y += gravity * delta.
	if result.is_wall_clinging:
		result.velocity.y += gravity * cling_gravity_scale * effective_delta
	else:
		result.velocity.y += gravity * effective_delta

	# --- 15. Jump cut (SPEC-20) ---
	#
	# If the jump button is not held and the character is ascending faster
	# than the cut threshold, clamp upward velocity to the cut velocity.
	# This allows variable-height jumping by releasing the button early.
	# Applies to both regular jumps and wall jumps.
	# Condition uses strict less-than so exact boundary is a no-op (AC-20.5).
	if not jump_pressed and result.velocity.y < jump_cut_velocity:
		result.velocity.y = jump_cut_velocity

	# --- 16. is_on_floor pass-through (AC-4.3) ---
	#
	# The engine controller updates is_on_floor after move_and_slide().
	# The simulation only passes it through; the controller writes the real
	# contact result back to _current_state after each physics frame.
	result.is_on_floor = prior_state.is_on_floor

	# --- 17. Chunk detach (SPEC-48) ---
	#
	# Appended as the final step after all physics steps are complete.
	# detach_eligible requires both a fresh detach press AND the chunk still
	# being attached. When prior_state.has_chunks[0] is already false, a detach
	# press is a deterministic no-op — it does not error or re-detach.
	#
	# simulate() never sets result.has_chunks[0] = true. Only M1-007 (recall),
	# executed by the controller, performs the false → true transition
	# (SPEC-47). The array initializer (has_chunks: Array = [true, true]) provides
	# the only true source at construction time.
	#
	# This step reads only: detach_just_pressed, prior_state.has_chunks[0]
	# This step writes only: result.has_chunks[0]
	# No velocity, timer, floor, or cling fields are read or written here.
	var detach_eligible: bool = detach_just_pressed and prior_state.has_chunks[0]
	if detach_eligible:
		result.has_chunks[0] = false
	else:
		result.has_chunks[0] = prior_state.has_chunks[0]

	# --- 18. HP reduction on detach (SPEC-56) ---
	#
	# Single-source HP reduction step. Uses the same detach_eligible flag
	# computed above so HP reduction fires on exactly the same frames as the
	# true→false has_chunk transition. Non-detach frames (including no-op
	# detach presses when has_chunk is already false) carry current_hp forward
	# exactly (SPEC-57).
	#
	# Formula (SPEC-56 / SPEC-58):
	#   raw_hp = prior_state.current_hp - hp_cost_per_detach
	#   result.current_hp = max(min_hp, raw_hp)
	#
	# max_hp is intentionally *not* applied here (SPEC-55.5); it is reserved
	# for upper-bound clamping by recall or other systems.
	if detach_eligible:
		var raw_hp: float = prior_state.current_hp - hp_cost_per_detach
		result.current_hp = max(min_hp, raw_hp)
	else:
		result.current_hp = prior_state.current_hp

	# --- 19. Chunk 2 detach (SPEC-SCL-3) ---
	#
	# Independent second-chunk detach step. Mirrors step 17 exactly but
	# operates on has_chunks[1] and detach_2_just_pressed. The two chunk slots
	# are strictly independent: no step reads has_chunks[0] to determine
	# has_chunks[1] behavior or vice versa (SPEC-SCL-6).
	#
	# simulate() never sets result.has_chunks[1] = true. Only the controller
	# (PlayerController3D) performs the false→true transition on recall
	# completion (SPEC-SCL-2). The array initializer (has_chunks: Array = [true, true])
	# provides the only true source at construction time.
	#
	# This step reads only: detach_2_just_pressed, prior_state.has_chunks[1]
	# This step writes only: result.has_chunks[1]
	var detach_2_eligible: bool = detach_2_just_pressed and prior_state.has_chunks[1]
	if detach_2_eligible:
		result.has_chunks[1] = false
	else:
		result.has_chunks[1] = prior_state.has_chunks[1]

	# --- 20. HP reduction for chunk 2 detach (SPEC-SCL-5) ---
	#
	# Second HP reduction step, conditioned on detach_2_eligible. Reads
	# result.current_hp (the output of step 18), NOT prior_state.current_hp.
	# This is the critical ordering detail: if both chunks are detached on the
	# same frame (dual-detach), the HP reductions are cumulative:
	#   - Step 18: result.current_hp = max(min_hp, prior_hp - cost)
	#   - Step 20: result.current_hp = max(min_hp, result.current_hp - cost)
	# So dual-detach deducts 2*cost (subject to min_hp clamp at each step).
	#
	# Non-detach frames and no-op detach_2 presses (has_chunk_2 already false)
	# leave result.current_hp unchanged from step 18's output.
	#
	# This step reads only: detach_2_eligible, result.current_hp, hp_cost_per_detach, min_hp
	# This step writes only: result.current_hp
	if detach_2_eligible:
		var raw_hp_2: float = result.current_hp - hp_cost_per_detach
		result.current_hp = max(min_hp, raw_hp_2)
	else:
		pass  # result.current_hp unchanged from step 18 output

	return result
