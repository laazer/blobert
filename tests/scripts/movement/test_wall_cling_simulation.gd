# test_wall_cling_simulation.gd
#
# Headless unit tests for wall cling mechanics in scripts/movement_simulation.gd.
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked via:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Spec coverage:
#   SPEC-25 — MovementState new fields: is_wall_clinging, cling_timer defaults and immutability
#   SPEC-26 — New config parameters: cling_gravity_scale, max_cling_time, wall_jump_height,
#             wall_jump_horizontal_speed defaults and mutability
#   SPEC-27 — simulate() 7-arg signature: backward-compatible with is_on_wall=false, wall_normal_x=0.0
#   SPEC-28 — Pressing-toward-wall detection formula: (safe_axis * wall_normal_x) < 0.0
#   SPEC-29 — Cling eligibility: all 5 conditions, each one blocking independently
#   SPEC-30 — Cling state update: timer accumulation, reset, immutability
#   SPEC-31 — Cling gravity modification: scaled vs. normal gravity
#   SPEC-32 — Wall jump eligibility: prior_state.is_wall_clinging, floor priority
#   SPEC-33 — Wall jump impulse: velocity.y, velocity.x, consumed, is_wall_clinging=false
#   SPEC-34 — Order of operations: regular jump priority, wall jump skips step 7, cling gravity gate
#   SPEC-36 — Frame-rate independence: cling_timer half-steps, cling gravity half-steps
#
# Checkpoint log (see CHECKPOINTS.md [M1-003]):
#   Test Designer — cling gravity test initial vy value
#   Test Designer — wall jump eligibility requires prior_state.is_wall_clinging
#   Test Designer — pressing_toward_wall tests via full simulate() round-trip
#   Test Designer — wall jump horizontal step 7 skip verification

class_name WallClingSimulationTests
extends "res://tests/utils/test_utils.gd"

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Factory helper.
# Constructs a MovementState with velocity and floor flag only.
# New fields (is_wall_clinging, cling_timer) default to false and 0.0 respectively.
# Tests that need non-default values set them explicitly after calling this helper.
# Signature matches existing suites (AC-35.5 — helper not modified).
# ---------------------------------------------------------------------------

func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ---------------------------------------------------------------------------
# SPEC-25 — MovementState new fields: defaults and immutability
# ---------------------------------------------------------------------------

# AC-25.1: is_wall_clinging defaults to false
func test_spec25_is_wall_clinging_default_is_false() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_false(state.is_wall_clinging,
		"spec25/AC-25.1 — MovementState.new().is_wall_clinging == false")


# AC-25.1: cling_timer defaults to 0.0
func test_spec25_cling_timer_default_is_zero() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_approx(state.cling_timer, 0.0,
		"spec25/AC-25.1 — MovementState.new().cling_timer == 0.0")


# AC-25.5: prior_state.is_wall_clinging not mutated by simulate()
# Set prior.is_wall_clinging=false, call simulate() with clinging conditions; check it stays false.
func test_spec25_prior_state_is_wall_clinging_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = false
	prior.cling_timer = 0.0
	prior.jump_consumed = false
	# All cling conditions met: is_on_wall=true, not floor, pressing toward wall,
	# not consumed, timer=0.0 < max_cling_time=1.5
	var _result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(prior.is_wall_clinging,
		"spec25/AC-25.5 — prior_state.is_wall_clinging not mutated (stays false)")


# AC-25.5: prior_state.cling_timer not mutated by simulate()
func test_spec25_prior_state_cling_timer_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.cling_timer = 0.5
	prior.jump_consumed = false
	var _result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_approx(prior.cling_timer, 0.5,
		"spec25/AC-25.5 — prior_state.cling_timer not mutated (stays 0.5)")


# AC-25.7: Total field count check — both new fields accessible via fresh state
# (Verifies fields are in MovementState, not at outer class scope)
func test_spec25_new_fields_accessible_on_fresh_state() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	# If the fields are at the wrong scope or missing this line would error.
	state.is_wall_clinging = true
	state.cling_timer = 1.0
	_assert_true(state.is_wall_clinging == true,
		"spec25/AC-25.7 — is_wall_clinging accessible and assignable on MovementState")
	_assert_approx(state.cling_timer, 1.0,
		"spec25/AC-25.7 — cling_timer accessible and assignable on MovementState")


# ---------------------------------------------------------------------------
# SPEC-26 — New configuration parameter defaults
# ---------------------------------------------------------------------------

# AC-26.1: cling_gravity_scale default is 0.1
func test_spec26_default_cling_gravity_scale() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.cling_gravity_scale, 0.1,
		"spec26/AC-26.1 — cling_gravity_scale default is 0.1")


# AC-26.2: max_cling_time default is 1.5
func test_spec26_default_max_cling_time() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.max_cling_time, 1.5,
		"spec26/AC-26.2 — max_cling_time default is 1.5")


# AC-26.3: wall_jump_height default is 100.0
func test_spec26_default_wall_jump_height() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.wall_jump_height, 100.0,
		"spec26/AC-26.3 — wall_jump_height default is 100.0")


# AC-26.4: wall_jump_horizontal_speed default is 180.0
func test_spec26_default_wall_jump_horizontal_speed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.wall_jump_horizontal_speed, 180.0,
		"spec26/AC-26.4 — wall_jump_horizontal_speed default is 180.0")


# AC-26.6: cling_gravity_scale is mutable and affects simulate() output
# Set cling_gravity_scale=0.5; clinging frame should produce half gravity per delta.
func test_spec26_cling_gravity_scale_mutable_affects_output() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.cling_gravity_scale = 0.5
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# gravity=980, scale=0.5, delta=0.016 → cling gravity delta = 980*0.5*0.016 = 7.84
	# Non-cling would be 980*0.016 = 15.68. Verify result is ~7.84 (cling), not ~15.68.
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec26/AC-26.6 setup — cling is active for mutability test")
	# Starting vy=0.0; after cling gravity: 0.0 + 980.0*0.5*0.016 = 7.84
	_assert_approx(result.velocity.y, 7.84,
		"spec26/AC-26.6 — cling_gravity_scale=0.5 mutable: vy = 0 + 980*0.5*0.016 = 7.84")


# AC-26.6: max_cling_time is mutable and blocks cling when set to 0.0
func test_spec26_max_cling_time_mutable_zero_disables_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.max_cling_time = 0.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.cling_timer = 0.0
	prior.jump_consumed = false
	# cling_timer=0.0 < max_cling_time=0.0 → 0.0 < 0.0 = false → not eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec26/AC-26.6 — max_cling_time=0.0 mutable: cling disabled (0.0 < 0.0 is false)")


# ---------------------------------------------------------------------------
# SPEC-27 — simulate() extended signature backward compatibility
# ---------------------------------------------------------------------------

# AC-27.2: Calling with is_on_wall=false, wall_normal_x=0.0 produces same behavior
# as the prior 5-arg signature. Gravity should apply normally; no cling state change.
func test_spec27_backward_compatible_no_wall_contact() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	# 7-arg call with is_on_wall=false, wall_normal_x=0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	# Normal gravity: vy = 0 + 980*0.016 = 15.68
	_assert_approx(result.velocity.y, 15.68,
		"spec27/AC-27.2 — no wall contact: gravity = 980*0.016 = 15.68 (normal)")
	_assert_false(result.is_wall_clinging,
		"spec27/AC-27.2 — no wall contact: is_wall_clinging = false")
	_assert_approx(result.cling_timer, 0.0,
		"spec27/AC-27.2 — no wall contact: cling_timer = 0.0")


# AC-27.2: Floor pass-through still works with 7-arg signature
func test_spec27_is_on_floor_passthrough_with_7arg_signature() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_true(result.is_on_floor == true,
		"spec27/AC-27.2 — is_on_floor passthrough preserved with 7-arg signature")


# ---------------------------------------------------------------------------
# SPEC-28 — Pressing-toward-wall detection
#
# Since pressing_toward_wall is an internal variable, tests verify it indirectly
# by observing result.is_wall_clinging when all other cling conditions are met.
# See CHECKPOINTS.md [M1-003] Test Designer checkpoint.
# ---------------------------------------------------------------------------

# AC-28.1: input_axis=1.0 (right), wall_normal_x=-1.0 (wall to right) → pressing toward → cling active
func test_spec28_pressing_right_into_right_wall_clings() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# is_on_wall=true, wall_normal_x=-1.0 (wall to right), input_axis=1.0
	# product = 1.0 * -1.0 = -1.0 < 0.0 → pressing_toward_wall = true → eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, true, -1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec28/AC-28.1 — input_axis=1.0, wall_normal_x=-1.0: pressing toward right wall → cling active")


# AC-28.2: input_axis=-1.0 (left), wall_normal_x=1.0 (wall to left) → pressing toward → cling active
func test_spec28_pressing_left_into_left_wall_clings() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# product = -1.0 * 1.0 = -1.0 < 0.0 → pressing_toward_wall = true → eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec28/AC-28.2 — input_axis=-1.0, wall_normal_x=1.0: pressing toward left wall → cling active")


# AC-28.3: input_axis=-1.0 (pressing away from right wall), wall_normal_x=-1.0 → not pressing toward → no cling
func test_spec28_pressing_away_from_right_wall_no_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# product = -1.0 * -1.0 = 1.0 > 0.0 → pressing_toward_wall = false → not eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, -1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec28/AC-28.3 — input_axis=-1.0, wall_normal_x=-1.0: pressing away from wall → no cling")


# AC-28.4: input_axis=0.0 (no input), wall_normal_x=-1.0 → product=0.0 (not < 0.0) → no cling
func test_spec28_no_input_no_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# product = 0.0 * -1.0 = 0.0, not < 0.0 → pressing_toward_wall = false → not eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, true, -1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec28/AC-28.4 — input_axis=0.0: product=0.0 (not < 0.0) → no cling even on wall")


# AC-28.5: wall_normal_x=0.0 (not on wall default) → always false regardless of input_axis
func test_spec28_wall_normal_x_zero_always_blocks_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# product = 1.0 * 0.0 = 0.0, not < 0.0 → pressing_toward_wall = false
	# Even with is_on_wall=true passed, normal_x=0 blocks it
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, true, 0.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec28/AC-28.5 — wall_normal_x=0.0: any input * 0.0 = 0.0 → not pressing toward → no cling")


# AC-28.6: Strict boundary — product exactly 0.0 → false (not <= 0.0)
func test_spec28_strict_less_than_zero_boundary() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	# input_axis=0.5 clamped stays 0.5; wall_normal_x=0.0 → product=0.0
	# 0.0 < 0.0 is false → no cling (strict less-than)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.5, false, false, true, 0.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec28/AC-28.6 — product exactly 0.0: strict < boundary → pressing_toward_wall=false")


# ---------------------------------------------------------------------------
# SPEC-29 — Cling eligibility: each condition independently blocks cling
# ---------------------------------------------------------------------------

# AC-29.1: All five conditions true → eligible, is_wall_clinging=true
func test_spec29_all_conditions_met_eligible() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	# is_on_wall=true, not on floor, pressing toward (axis=-1, normal=1.0), not consumed, timer<max
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec29/AC-29.1 — all 5 conditions met: is_wall_clinging=true")


# AC-29.2: is_on_wall=false → not eligible
func test_spec29_not_on_wall_blocks_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	# is_on_wall=false, all other conditions would be met if on wall
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, false, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec29/AC-29.2 — is_on_wall=false: not eligible for cling")


# AC-29.3: is_on_floor=true → not eligible (floor takes precedence over wall)
func test_spec29_on_floor_blocks_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	# is_on_wall=true, but is_on_floor=true → condition 2 fails
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec29/AC-29.3 — is_on_floor=true: floor takes precedence → no cling")


# AC-29.4: pressing_toward_wall=false (pressing away) → not eligible
func test_spec29_pressing_away_blocks_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	# input_axis=1.0, wall_normal_x=1.0 → product=1.0 > 0.0 → not pressing toward
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec29/AC-29.4 — pressing away from wall: not eligible for cling")


# AC-29.5: jump_consumed=true → not eligible
func test_spec29_jump_consumed_blocks_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = true
	prior.cling_timer = 0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec29/AC-29.5 — jump_consumed=true: not eligible for cling")


# AC-29.6: cling_timer >= max_cling_time → not eligible (timer expired)
func test_spec29_timer_expired_blocks_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 1.5  # equals max_cling_time=1.5 → 1.5 < 1.5 is false → not eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec29/AC-29.6 — cling_timer=1.5 >= max_cling_time=1.5: expired → not eligible")


# AC-29.7: max_cling_time=0.0, cling_timer=0.0 → 0.0 < 0.0 = false → not eligible (cling disabled)
func test_spec29_max_cling_time_zero_disables_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.max_cling_time = 0.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec29/AC-29.7 — max_cling_time=0.0: 0.0 < 0.0 is false → cling disabled entirely")


# AC-29.8: cling_timer exactly one effective_delta below max_cling_time → still eligible (last frame)
# cling_timer=1.484 (= 1.5 - 0.016), max_cling_time=1.5 → 1.484 < 1.5 → eligible
func test_spec29_last_eligible_frame_before_expiry() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 1.484  # 1.5 - 0.016; still strictly less than 1.5
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec29/AC-29.8 — cling_timer=1.484 < max_cling_time=1.5: still eligible on last frame")


# ---------------------------------------------------------------------------
# SPEC-30 — Cling state update: timer accumulation and reset
# ---------------------------------------------------------------------------

# AC-30.1: First cling frame: prior.cling_timer=0.0, delta=0.016 → result.cling_timer=0.016
func test_spec30_cling_timer_accumulates_from_zero() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec30/AC-30.1 setup — cling active on first frame")
	_assert_approx(result.cling_timer, 0.016,
		"spec30/AC-30.1 — first cling frame: cling_timer = 0.0 + 0.016 = 0.016")


# AC-30.2: Continued cling: prior.cling_timer=0.5, delta=0.016 → result.cling_timer=0.516
func test_spec30_cling_timer_accumulates_from_prior_value() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.5
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_approx(result.cling_timer, 0.516,
		"spec30/AC-30.2 — cling from prior 0.5: result.cling_timer = 0.516")


# AC-30.3: Not clinging (pressing away) → result.cling_timer=0.0 regardless of prior.cling_timer
func test_spec30_cling_timer_resets_to_zero_when_not_eligible() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.8  # had been clinging before
	# pressing away from wall: no longer eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec30/AC-30.3 setup — not clinging when pressing away")
	_assert_approx(result.cling_timer, 0.0,
		"spec30/AC-30.3 — timer resets to 0.0 immediately when not eligible (prior was 0.8)")


# AC-30.3: Not on wall → result.cling_timer=0.0 regardless of prior
func test_spec30_cling_timer_resets_when_leaves_wall() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.4  # had been clinging before
	# is_on_wall=false → not eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, false, 1.0, [false, false], 0.016)
	_assert_approx(result.cling_timer, 0.0,
		"spec30/AC-30.3 — timer resets to 0.0 when is_on_wall=false (prior was 0.4)")


# AC-30.4: Timer expired frame → result.cling_timer=0.0 (not accumulated on expiry frame)
func test_spec30_cling_timer_zero_on_expiry_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 1.5  # at max_cling_time; 1.5 < 1.5 is false → not eligible
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec30/AC-30.4 — expiry frame: is_wall_clinging=false")
	_assert_approx(result.cling_timer, 0.0,
		"spec30/AC-30.4 — expiry frame: cling_timer resets to 0.0 (not accumulated)")


# AC-30.5: prior_state.cling_timer not mutated
func test_spec30_prior_cling_timer_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.3
	var _result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_approx(prior.cling_timer, 0.3,
		"spec30/AC-30.5 — prior_state.cling_timer not mutated by simulate() (stays 0.3)")


# AC-30.6: delta=0.0, clinging → result.cling_timer=prior.cling_timer (no change)
func test_spec30_zero_delta_cling_timer_unchanged() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.3
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.0)
	_assert_approx(result.cling_timer, 0.3,
		"spec30/AC-30.6 — delta=0.0: cling_timer unchanged when eligible (0.3 + 0.0 = 0.3)")


# ---------------------------------------------------------------------------
# SPEC-31 — Cling gravity modification
# ---------------------------------------------------------------------------

# AC-31.1: Clinging with cling_gravity_scale=0.1, vy=50.0 → scaled gravity contribution
# vy = 50.0 + 980.0 * 0.1 * 0.016 = 50.0 + 1.568 = 51.568
func test_spec31_cling_gravity_scaled_while_clinging() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# cling_gravity_scale default is 0.1
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 50.0, false)
	prior.jump_consumed = false
	prior.cling_timer = 0.0
	# Cling conditions met. Step 6 carries vy=50.0 forward (no jump).
	# After cling gravity: 50.0 + 980.0 * 0.1 * 0.016 = 51.568
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec31/AC-31.1 setup — cling active for gravity test")
	_assert_approx(result.velocity.y, 51.568,
		"spec31/AC-31.1 — clinging: vy = 50.0 + 980.0*0.1*0.016 = 51.568")


# AC-31.2: Not clinging (same initial vy=50.0, identical params) → normal gravity
# vy = 50.0 + 980.0 * 0.016 = 65.68
func test_spec31_normal_gravity_when_not_clinging() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 50.0, false)
	prior.jump_consumed = false
	# is_on_wall=false → not clinging → normal gravity
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result.velocity.y, 65.68,
		"spec31/AC-31.2 — not clinging: vy = 50.0 + 980.0*0.016 = 65.68 (normal gravity)")


# AC-31.3: cling_gravity_scale=0.0 while clinging → zero gravity contribution (hover)
func test_spec31_zero_gravity_scale_produces_hover() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.cling_gravity_scale = 0.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec31/AC-31.3 setup — cling active")
	_assert_approx(result.velocity.y, 0.0,
		"spec31/AC-31.3 — cling_gravity_scale=0.0: gravity contribution=0.0, vy unchanged")


# AC-31.4: cling_gravity_scale=1.0 while clinging → same as normal gravity
# vy = 0.0 + 980.0 * 1.0 * 0.016 = 15.68
func test_spec31_gravity_scale_one_equals_normal_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.cling_gravity_scale = 1.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_approx(result.velocity.y, 15.68,
		"spec31/AC-31.4 — cling_gravity_scale=1.0: same as normal gravity = 980*1.0*0.016 = 15.68")


# AC-31.5: sim.cling_gravity_scale=0.5 mutable: gravity contribution = 980*0.5*0.016 = 7.84
func test_spec31_custom_gravity_scale_runtime_change() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.cling_gravity_scale = 0.5
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_approx(result.velocity.y, 7.84,
		"spec31/AC-31.5 — cling_gravity_scale=0.5: vy = 0.0 + 980.0*0.5*0.016 = 7.84")


# AC-31.6: Wall jump frame → result.is_wall_clinging=false → normal gravity applied (not cling gravity)
# prior.is_wall_clinging=true, jump_just_pressed=true → wall jump fires
# Wall jump sets is_wall_clinging=false; gravity step sees false → applies normal 980*delta
func test_spec31_wall_jump_frame_uses_normal_gravity_not_cling_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.cling_gravity_scale = 0.1  # cling gravity is 1/10 of normal; normal = 980*0.016=15.68
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	# Wall jump fires: result.is_wall_clinging set to false → gravity step = 980*0.016=15.68 (normal)
	# Wall jump vy impulse = -sqrt(2*980*100) = -sqrt(196000) ≈ -442.7189
	# After normal gravity: -442.7189 + 15.68 ≈ -427.0389
	# With held jump button (jump_pressed=true) to suppress jump cut
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	_assert_false(result.is_wall_clinging,
		"spec31/AC-31.6 — wall jump frame: is_wall_clinging=false after wall jump fires")
	_assert_approx(result.velocity.y, expected_vy,
		"spec31/AC-31.6 — wall jump frame: normal gravity applied (not cling gravity)")


# AC-31.7: delta=0.0 → gravity contribution=0.0 regardless of cling or scale
func test_spec31_zero_delta_no_gravity_contribution() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 20.0, false)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.0)
	_assert_approx(result.velocity.y, 20.0,
		"spec31/AC-31.7 — delta=0.0: gravity contribution=0.0 even while clinging (vy unchanged)")


# ---------------------------------------------------------------------------
# SPEC-32 — Wall jump eligibility
# ---------------------------------------------------------------------------

# AC-32.1: All three conditions met → wall_jump fires
# prior.is_wall_clinging=true, jump_just_pressed=true, jump_consumed=false
func test_spec32_wall_jump_fires_when_all_conditions_met() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	# Wall normal pointing left (wall to right) → player launches left; hold jump to suppress cut
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	# Wall jump fires: vy = -sqrt(2*980*100) + 980*0.016
	var expected_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"spec32/AC-32.1 — wall jump fires: vy = -sqrt(196000) + 980*0.016")
	_assert_true(result.jump_consumed == true,
		"spec32/AC-32.1 — wall jump fires: result.jump_consumed=true")
	_assert_false(result.is_wall_clinging,
		"spec32/AC-32.1 — wall jump fires: result.is_wall_clinging=false")


# AC-32.2: jump_just_pressed=false → wall jump does not fire
func test_spec32_no_wall_jump_when_jump_not_just_pressed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	# jump_just_pressed=false → wall_jump_eligible=false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, true, -1.0, [false, false], 0.016)
	# No wall jump: vy = prior.vy + cling_gravity (since still clinging this frame eligible)
	# is_wall_clinging should still be true if all cling conditions met, not the wall jump path
	_assert_false(result.jump_consumed,
		"spec32/AC-32.2 — jump_just_pressed=false: jump_consumed stays false (no wall jump)")


# AC-32.3: prior_state.is_wall_clinging=false → wall jump does not fire
# Even if eligible_for_cling=true this frame, prior frame had no cling
func test_spec32_no_wall_jump_when_not_clinging_on_prior_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = false  # not clinging last frame
	prior.jump_consumed = false
	# All current frame cling conditions met, jump_just_pressed=true,
	# but prior_state.is_wall_clinging=false → wall_jump_eligible=false
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, true, true, true, 1.0, [false, false], 0.016)
	# Result vy: no floor, no coyote → no regular jump either
	# Expect just gravity (+ cling gravity since this frame is eligible for cling)
	# No wall jump impulse: result.velocity.y should NOT be approximately -sqrt(196000)+gravity*delta
	var wall_jump_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	_assert_true(abs(result.velocity.y - wall_jump_vy) > EPSILON,
		"spec32/AC-32.3 — prior.is_wall_clinging=false: no wall jump on first contact frame")
	_assert_false(result.jump_consumed,
		"spec32/AC-32.3 — prior.is_wall_clinging=false: jump_consumed stays false")


# AC-32.4: jump_consumed=true → wall jump blocked
func test_spec32_wall_jump_blocked_by_jump_consumed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = true  # already consumed
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, true, true, -1.0, [false, false], 0.016)
	var wall_jump_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	_assert_true(abs(result.velocity.y - wall_jump_vy) > EPSILON,
		"spec32/AC-32.4 — jump_consumed=true: wall jump blocked")


# AC-32.5: On floor + clinging + jump_just_pressed → regular jump fires (not wall jump)
# Regular jump uses jump_height=120.0; wall jump uses wall_jump_height=100.0
func test_spec32_regular_jump_takes_priority_over_wall_jump_on_floor() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.is_wall_clinging = true  # was clinging somehow (e.g., convex corner)
	prior.jump_consumed = false
	# Regular jump eligible (on floor, not consumed) → regular jump fires, not wall jump
	# Regular jump vy: -sqrt(2*980*120) + 980*0.016
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	var regular_jump_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	var wall_jump_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, regular_jump_vy,
		"spec32/AC-32.5 — on floor: regular jump fires (uses jump_height=120, not wall_jump_height=100)")
	_assert_true(abs(result.velocity.y - wall_jump_vy) > EPSILON,
		"spec32/AC-32.5 — on floor: result.vy ≠ wall jump vy (different heights)")


# ---------------------------------------------------------------------------
# SPEC-33 — Wall jump impulse: velocity values, consumed, is_wall_clinging
# ---------------------------------------------------------------------------

# AC-33.1: Full wall jump with default params, wall_normal_x=-1.0 (wall to right)
# vy = -sqrt(2*980*100) + 980*0.016 ≈ -427.0389; vx = -1.0*180.0 = -180.0
func test_spec33_wall_jump_impulse_default_params_right_wall() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	var expected_vx: float = -1.0 * 180.0  # = -180.0
	_assert_approx(result.velocity.y, expected_vy,
		"spec33/AC-33.1 — wall jump vy = -sqrt(196000) + 980*0.016 ≈ -427.0389")
	_assert_approx(result.velocity.x, expected_vx,
		"spec33/AC-33.1 — wall jump vx = -1.0 * 180.0 = -180.0")


# AC-33.2: wall_normal_x=1.0 (wall to left) → vx = 1.0*180.0 = 180.0 (launch right)
func test_spec33_wall_jump_impulse_left_wall_launches_right() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, 1.0, [false, false], 0.016)
	_assert_approx(result.velocity.x, 180.0,
		"spec33/AC-33.2 — wall to left (normal_x=1.0): vx = 1.0*180.0 = 180.0 (launch right)")


# AC-33.3: After wall jump: jump_consumed=true, is_wall_clinging=false
func test_spec33_wall_jump_sets_consumed_and_clears_clinging() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	_assert_true(result.jump_consumed == true,
		"spec33/AC-33.3 — after wall jump: result.jump_consumed=true")
	_assert_false(result.is_wall_clinging,
		"spec33/AC-33.3 — after wall jump: result.is_wall_clinging=false")


# AC-33.4: prior_state immutability on wall jump frame
func test_spec33_prior_state_not_mutated_on_wall_jump_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	_assert_true(prior.is_wall_clinging == true,
		"spec33/AC-33.4 — prior_state.is_wall_clinging not mutated (stays true)")
	_assert_false(prior.jump_consumed,
		"spec33/AC-33.4 — prior_state.jump_consumed not mutated (stays false)")


# AC-33.5: wall_jump_height=0.0 → vy = -sqrt(0.0) + gravity*delta = 15.68, not NaN
func test_spec33_zero_wall_jump_height_no_nan() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.wall_jump_height = 0.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	_assert_true(not is_nan(result.velocity.y),
		"spec33/AC-33.5 — wall_jump_height=0.0: velocity.y is not NaN")
	_assert_true(is_finite(result.velocity.y),
		"spec33/AC-33.5 — wall_jump_height=0.0: velocity.y is finite")
	# vy = -sqrt(0.0) + 980.0 * 0.016 = 0.0 + 15.68 = 15.68
	_assert_approx(result.velocity.y, 15.68,
		"spec33/AC-33.5 — wall_jump_height=0.0: vy = 0.0 + 980*0.016 = 15.68")
	# jump_consumed still set even for zero-height wall jump
	_assert_true(result.jump_consumed == true,
		"spec33/AC-33.5 — wall_jump_height=0.0: jump_consumed=true even on zero-height wall jump")


# AC-33.6: wall_jump_horizontal_speed mutable at runtime
# sim.wall_jump_horizontal_speed=250.0, wall_normal_x=-1.0 → vx=-250.0
func test_spec33_custom_wall_jump_horizontal_speed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.wall_jump_horizontal_speed = 250.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	_assert_approx(result.velocity.x, -250.0,
		"spec33/AC-33.6 — wall_jump_horizontal_speed=250.0: vx = -1.0 * 250.0 = -250.0")


# AC-33.7: wall_jump_height=50.0 mutable at runtime
# vy = -sqrt(2*980*50) + 980*0.016 = -sqrt(98000) + 15.68 ≈ -313.05 + 15.68 = -297.37
func test_spec33_custom_wall_jump_height() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.wall_jump_height = 50.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 50.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"spec33/AC-33.7 — wall_jump_height=50.0: vy = -sqrt(98000) + 15.68 ≈ -297.37")


# AC-33.8: Wall jump with jump_pressed=false (tap) → jump cut applies
# vy ≈ -427.04; jump_cut_velocity=-200.0; -427.04 < -200.0 → clamped to -200.0
func test_spec33_wall_jump_cut_applies_on_tap() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	# jump_pressed=false (released immediately after press)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, true, true, -1.0, [false, false], 0.016)
	# Wall jump vy ≈ -427.04 < jump_cut_velocity=-200.0 → clamped to -200.0
	_assert_approx(result.velocity.y, -200.0,
		"spec33/AC-33.8 — wall jump tap: vy=-427.04 < -200 → jump cut clamps to -200.0")


# AC-33.9: Wall jump with jump_pressed=true (held) → jump cut does not trigger
func test_spec33_no_jump_cut_when_jump_held() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	# jump_pressed=true → jump cut condition NOT jump_pressed=false → no cut
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 100.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"spec33/AC-33.9 — wall jump held: full impulse retained, no jump cut")


# ---------------------------------------------------------------------------
# SPEC-34 — Order of operations
# ---------------------------------------------------------------------------

# AC-34.1: On floor + clinging + jump_just_pressed → regular jump velocity (not wall jump)
# Regular jump: -sqrt(2*980*120) + 980*0.016
# Wall jump would be: -sqrt(2*980*100) + 980*0.016
# These are different values; result must match regular jump formula.
func test_spec34_regular_jump_takes_priority_over_wall_jump() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	var regular_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, regular_vy,
		"spec34/AC-34.1 — on floor + clinging: regular jump (jump_height=120) takes priority")


# AC-34.2: Wall jump fires → step 7 (horizontal formula) must NOT run; vx = wall_normal_x * speed
# Setup: prior.velocity.x=100.0 (would produce friction result ~80.8 from step 7)
# but wall jump fires → vx = -1.0 * 180.0 = -180.0 (completely different)
func test_spec34_wall_jump_skips_horizontal_step_7() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# prior vx=100.0: if step 7 ran, friction → ~80.8; wall jump → -180.0
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	_assert_approx(result.velocity.x, -180.0,
		"spec34/AC-34.2 — wall jump fires: vx = -1.0*180.0 = -180.0 (step 7 skipped)")


# AC-34.3: Wall jump frame → is_wall_clinging=false and gravity uses normal (not cling) rate
func test_spec34_wall_jump_frame_is_wall_clinging_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.016)
	_assert_false(result.is_wall_clinging,
		"spec34/AC-34.3 — wall jump frame: result.is_wall_clinging=false")


# AC-34.5: Wall jump + tap (jump_pressed=false) → jump cut still applies on wall jump frame
func test_spec34_jump_cut_still_applies_on_wall_jump_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	# jump_pressed=false → cut applies; wall jump vy ≈ -427.04 < -200 → clamped to -200
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, true, true, -1.0, [false, false], 0.016)
	_assert_approx(result.velocity.y, -200.0,
		"spec34/AC-34.5 — wall jump + tap: jump cut applies to wall jump vertical impulse")


# AC-34.6: is_on_wall=false, wall_normal_x=0.0 → behavior identical to M1-002 5-arg behavior
# (normal gravity, no cling, no wall jump — verified via gravity value check)
func test_spec34_no_wall_contact_preserves_all_prior_behaviors() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.0
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result.velocity.y, 15.68,
		"spec34/AC-34.6 — no wall contact: velocity.y = 980*0.016 = 15.68 (normal gravity)")
	_assert_false(result.is_wall_clinging,
		"spec34/AC-34.6 — no wall contact: is_wall_clinging=false")
	_assert_approx(result.cling_timer, 0.0,
		"spec34/AC-34.6 — no wall contact: cling_timer=0.0")


# AC-34.7: is_on_floor pass-through not affected by wall cling logic
func test_spec34_is_on_floor_passthrough_unaffected_by_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_true(result.is_wall_clinging,
		"spec34/AC-34.7 setup — cling active")
	_assert_false(result.is_on_floor,
		"spec34/AC-34.7 — is_on_floor passthrough: still false on clinging frame")


# ---------------------------------------------------------------------------
# SPEC-36 — Frame-rate independence
# ---------------------------------------------------------------------------

# AC-36.1: cling_timer two half-steps match one full step
# prior.cling_timer=0.0, full step delta=0.016 → cling_timer=0.016
# two half-steps delta=0.008 each: step1=0.008, step2=0.016 → both = 0.016
func test_spec36_cling_timer_two_half_steps_match_one_full_step() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Full step
	var prior_full: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_full.jump_consumed = false
	prior_full.cling_timer = 0.0
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_full, -1.0, false, false, true, 1.0, [false, false], 0.016)

	# Half-step 1
	var prior_half: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_half.jump_consumed = false
	prior_half.cling_timer = 0.0
	var mid: MovementSimulation.MovementState = sim.simulate(prior_half, -1.0, false, false, true, 1.0, [false, false], 0.008)
	# mid.cling_timer = 0.008; set up second half-step state
	var prior_half2: MovementSimulation.MovementState = _make_state_with(0.0, mid.velocity.y, false)
	prior_half2.jump_consumed = false
	prior_half2.cling_timer = mid.cling_timer
	var result_half: MovementSimulation.MovementState = sim.simulate(prior_half2, -1.0, false, false, true, 1.0, [false, false], 0.008)

	_assert_approx(result_half.cling_timer, result_full.cling_timer,
		"spec36/AC-36.1 — cling_timer: two half-steps (0.008+0.008) = one full step (0.016) = 0.016")


# AC-36.2: Cling gravity two half-steps match one full step
# gravity=980.0, cling_gravity_scale=0.1, vy=0.0, delta=0.016
# full step: delta_vy = 980*0.1*0.016 = 1.568
# two half-steps (delta=0.008 each): each delta_vy = 980*0.1*0.008 = 0.784; total = 1.568
func test_spec36_cling_gravity_two_half_steps_match_one_full_step() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# cling_gravity_scale default 0.1

	# Full step from vy=0
	var prior_full: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_full.jump_consumed = false
	prior_full.cling_timer = 0.0
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_full, -1.0, false, false, true, 1.0, [false, false], 0.016)

	# Half-step 1 from vy=0
	var prior_h1: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_h1.jump_consumed = false
	prior_h1.cling_timer = 0.0
	var mid: MovementSimulation.MovementState = sim.simulate(prior_h1, -1.0, false, false, true, 1.0, [false, false], 0.008)

	# Half-step 2 from mid
	var prior_h2: MovementSimulation.MovementState = _make_state_with(0.0, mid.velocity.y, false)
	prior_h2.jump_consumed = false
	prior_h2.cling_timer = mid.cling_timer
	var result_half: MovementSimulation.MovementState = sim.simulate(prior_h2, -1.0, false, false, true, 1.0, [false, false], 0.008)

	_assert_approx(result_half.velocity.y, result_full.velocity.y,
		"spec36/AC-36.2 — cling gravity: two half-steps = one full step (additive, linear)")


# AC-36.3: Wall jump vertical impulse is frame-rate independent
# impulse = -sqrt(2*980*100) regardless of delta; verified by isolating impulse (delta=0)
func test_spec36_wall_jump_vertical_impulse_is_delta_independent() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# delta=0 to isolate the impulse (no gravity contribution)
	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_a.is_wall_clinging = true
	prior_a.jump_consumed = false
	var result_a: MovementSimulation.MovementState = sim.simulate(prior_a, 0.0, true, true, true, -1.0, [false, false], 0.0)

	# delta=0.1; subtract gravity contribution to isolate impulse
	var prior_b: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_b.is_wall_clinging = true
	prior_b.jump_consumed = false
	var result_b: MovementSimulation.MovementState = sim.simulate(prior_b, 0.0, true, true, true, -1.0, [false, false], 0.1)

	var impulse_from_a: float = result_a.velocity.y  # = -sqrt(196000), no gravity added
	var impulse_from_b: float = result_b.velocity.y - 980.0 * 0.1  # subtract gravity*delta

	_assert_approx(impulse_from_a, impulse_from_b,
		"spec36/AC-36.3 — wall jump vertical impulse identical regardless of delta")


# AC-36.4: Wall jump horizontal impulse is delta-independent
# vx = wall_normal_x * wall_jump_horizontal_speed regardless of delta
func test_spec36_wall_jump_horizontal_impulse_is_delta_independent() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_a.is_wall_clinging = true
	prior_a.jump_consumed = false
	var result_a: MovementSimulation.MovementState = sim.simulate(prior_a, 0.0, true, true, true, -1.0, [false, false], 0.0)

	var prior_b: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_b.is_wall_clinging = true
	prior_b.jump_consumed = false
	var result_b: MovementSimulation.MovementState = sim.simulate(prior_b, 0.0, true, true, true, -1.0, [false, false], 0.1)

	_assert_approx(result_a.velocity.x, result_b.velocity.x,
		"spec36/AC-36.4 — wall jump horizontal impulse: vx identical regardless of delta")
	_assert_approx(result_a.velocity.x, -180.0,
		"spec36/AC-36.4 — wall jump horizontal impulse = -1.0 * 180.0 = -180.0")


# AC-36.5: delta=0.0 — all new computations produce no-change / full-impulse behavior
func test_spec36_zero_delta_all_new_computations_correct() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Cling timer does not increment at delta=0.0
	var prior_cling: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_cling.jump_consumed = false
	prior_cling.cling_timer = 0.5
	var result_cling: MovementSimulation.MovementState = sim.simulate(prior_cling, -1.0, false, false, true, 1.0, [false, false], 0.0)
	_assert_approx(result_cling.cling_timer, 0.5,
		"spec36/AC-36.5 — delta=0.0: cling_timer does not increment (stays 0.5)")

	# Wall jump impulse applied at full magnitude even at delta=0.0
	var prior_wj: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_wj.is_wall_clinging = true
	prior_wj.jump_consumed = false
	var result_wj: MovementSimulation.MovementState = sim.simulate(prior_wj, 0.0, true, true, true, -1.0, [false, false], 0.0)
	var expected_vy_at_zero_delta: float = -sqrt(2.0 * 980.0 * 100.0)  # + gravity*0.0 = 0
	_assert_approx(result_wj.velocity.y, expected_vy_at_zero_delta,
		"spec36/AC-36.5 — delta=0.0: wall jump impulse applied at full magnitude")
	_assert_approx(result_wj.velocity.x, -180.0,
		"spec36/AC-36.5 — delta=0.0: wall jump horizontal impulse = -180.0")


# ---------------------------------------------------------------------------
# Determinism guard
# ---------------------------------------------------------------------------

# Calling simulate() twice with identical wall-cling inputs produces identical results.
func test_determinism_wall_cling_identical_calls() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 20.0, false)
	prior.is_wall_clinging = false
	prior.cling_timer = 0.3
	prior.jump_consumed = false
	var result_a: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, true, 1.0, [false, false], 0.016)
	_assert_approx(result_a.velocity.x, result_b.velocity.x,
		"determinism — wall cling: identical inputs produce identical velocity.x")
	_assert_approx(result_a.velocity.y, result_b.velocity.y,
		"determinism — wall cling: identical inputs produce identical velocity.y")
	_assert_true(result_a.is_wall_clinging == result_b.is_wall_clinging,
		"determinism — wall cling: identical inputs produce identical is_wall_clinging")
	_assert_approx(result_a.cling_timer, result_b.cling_timer,
		"determinism — wall cling: identical inputs produce identical cling_timer")


func test_determinism_wall_jump_identical_calls() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, 10.0, false)
	prior.is_wall_clinging = true
	prior.jump_consumed = false
	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.02)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, true, -1.0, [false, false], 0.02)
	_assert_approx(result_a.velocity.x, result_b.velocity.x,
		"determinism — wall jump: identical inputs produce identical velocity.x")
	_assert_approx(result_a.velocity.y, result_b.velocity.y,
		"determinism — wall jump: identical inputs produce identical velocity.y")
	_assert_true(result_a.jump_consumed == result_b.jump_consumed,
		"determinism — wall jump: identical inputs produce identical jump_consumed")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_wall_cling_simulation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-25: MovementState new fields
	test_spec25_is_wall_clinging_default_is_false()
	test_spec25_cling_timer_default_is_zero()
	test_spec25_prior_state_is_wall_clinging_not_mutated()
	test_spec25_prior_state_cling_timer_not_mutated()
	test_spec25_new_fields_accessible_on_fresh_state()

	# SPEC-26: New config parameter defaults
	test_spec26_default_cling_gravity_scale()
	test_spec26_default_max_cling_time()
	test_spec26_default_wall_jump_height()
	test_spec26_default_wall_jump_horizontal_speed()
	test_spec26_cling_gravity_scale_mutable_affects_output()
	test_spec26_max_cling_time_mutable_zero_disables_cling()

	# SPEC-27: Extended signature backward compatibility
	test_spec27_backward_compatible_no_wall_contact()
	test_spec27_is_on_floor_passthrough_with_7arg_signature()

	# SPEC-28: Pressing-toward-wall detection
	test_spec28_pressing_right_into_right_wall_clings()
	test_spec28_pressing_left_into_left_wall_clings()
	test_spec28_pressing_away_from_right_wall_no_cling()
	test_spec28_no_input_no_cling()
	test_spec28_wall_normal_x_zero_always_blocks_cling()
	test_spec28_strict_less_than_zero_boundary()

	# SPEC-29: Cling eligibility (each condition)
	test_spec29_all_conditions_met_eligible()
	test_spec29_not_on_wall_blocks_cling()
	test_spec29_on_floor_blocks_cling()
	test_spec29_pressing_away_blocks_cling()
	test_spec29_jump_consumed_blocks_cling()
	test_spec29_timer_expired_blocks_cling()
	test_spec29_max_cling_time_zero_disables_cling()
	test_spec29_last_eligible_frame_before_expiry()

	# SPEC-30: Cling state update
	test_spec30_cling_timer_accumulates_from_zero()
	test_spec30_cling_timer_accumulates_from_prior_value()
	test_spec30_cling_timer_resets_to_zero_when_not_eligible()
	test_spec30_cling_timer_resets_when_leaves_wall()
	test_spec30_cling_timer_zero_on_expiry_frame()
	test_spec30_prior_cling_timer_not_mutated()
	test_spec30_zero_delta_cling_timer_unchanged()

	# SPEC-31: Cling gravity
	test_spec31_cling_gravity_scaled_while_clinging()
	test_spec31_normal_gravity_when_not_clinging()
	test_spec31_zero_gravity_scale_produces_hover()
	test_spec31_gravity_scale_one_equals_normal_gravity()
	test_spec31_custom_gravity_scale_runtime_change()
	test_spec31_wall_jump_frame_uses_normal_gravity_not_cling_gravity()
	test_spec31_zero_delta_no_gravity_contribution()

	# SPEC-32: Wall jump eligibility
	test_spec32_wall_jump_fires_when_all_conditions_met()
	test_spec32_no_wall_jump_when_jump_not_just_pressed()
	test_spec32_no_wall_jump_when_not_clinging_on_prior_frame()
	test_spec32_wall_jump_blocked_by_jump_consumed()
	test_spec32_regular_jump_takes_priority_over_wall_jump_on_floor()

	# SPEC-33: Wall jump impulse
	test_spec33_wall_jump_impulse_default_params_right_wall()
	test_spec33_wall_jump_impulse_left_wall_launches_right()
	test_spec33_wall_jump_sets_consumed_and_clears_clinging()
	test_spec33_prior_state_not_mutated_on_wall_jump_frame()
	test_spec33_zero_wall_jump_height_no_nan()
	test_spec33_custom_wall_jump_horizontal_speed()
	test_spec33_custom_wall_jump_height()
	test_spec33_wall_jump_cut_applies_on_tap()
	test_spec33_no_jump_cut_when_jump_held()

	# SPEC-34: Order of operations
	test_spec34_regular_jump_takes_priority_over_wall_jump()
	test_spec34_wall_jump_skips_horizontal_step_7()
	test_spec34_wall_jump_frame_is_wall_clinging_false()
	test_spec34_jump_cut_still_applies_on_wall_jump_frame()
	test_spec34_no_wall_contact_preserves_all_prior_behaviors()
	test_spec34_is_on_floor_passthrough_unaffected_by_cling()

	# SPEC-36: Frame-rate independence
	test_spec36_cling_timer_two_half_steps_match_one_full_step()
	test_spec36_cling_gravity_two_half_steps_match_one_full_step()
	test_spec36_wall_jump_vertical_impulse_is_delta_independent()
	test_spec36_wall_jump_horizontal_impulse_is_delta_independent()
	test_spec36_zero_delta_all_new_computations_correct()

	# Determinism
	test_determinism_wall_cling_identical_calls()
	test_determinism_wall_jump_identical_calls()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
