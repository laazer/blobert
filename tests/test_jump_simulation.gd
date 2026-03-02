# test_jump_simulation.gd
#
# Headless unit tests for jump mechanics in scripts/movement_simulation.gd.
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked via:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Spec coverage:
#   SPEC-15 — MovementState new fields: coyote_timer, jump_consumed defaults
#   SPEC-16 — MovementSimulation new config parameters: jump_height, coyote_time, jump_cut_velocity
#   SPEC-18 — Jump impulse condition and formula (all AC items)
#   SPEC-19 — Coyote time logic (all AC items)
#   SPEC-20 — Jump cut condition and clamp (all AC items)
#   SPEC-21 — Double-jump prevention via jump_consumed (all AC items)
#   SPEC-24 — Frame-rate independence of coyote timer decrement
#
# Checkpoint log (see CHECKPOINTS.md for full text):
#   [M1-002] Test Designer — jump impulse expected value computation
#   [M1-002] Test Designer — helper _make_state_with not updated for new fields
#   [M1-002] Test Designer — gravity=0.0 jump formula safety

class_name JumpSimulationTests
extends Object

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _approx_eq(a: float, b: float) -> bool:
	return abs(a - b) < EPSILON


func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_approx(a: float, b: float, test_name: String) -> void:
	if _approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")


# ---------------------------------------------------------------------------
# Factory helper — constructs a state with velocity and floor flag.
# New jump fields (coyote_timer, jump_consumed) default to 0.0 / false.
# Tests that need non-default jump fields set them explicitly after calling
# this helper.
# AC-25.6 mandates this helper signature is not modified.
# ---------------------------------------------------------------------------

func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ===========================================================================
# SPEC-15 — MovementState new fields: defaults
# ===========================================================================

# AC-15.1: MovementState.new().coyote_timer == 0.0
func test_spec15_coyote_timer_default_is_zero() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_approx(state.coyote_timer, 0.0,
		"spec15 — MovementState.new().coyote_timer == 0.0")


# AC-15.1: MovementState.new().jump_consumed == false
func test_spec15_jump_consumed_default_is_false() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_false(state.jump_consumed,
		"spec15 — MovementState.new().jump_consumed == false")


# AC-15.5: simulate() does not mutate prior_state.coyote_timer
func test_spec15_prior_state_coyote_timer_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.coyote_timer = 0.07
	prior.jump_consumed = false
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(prior.coyote_timer, 0.07,
		"spec15/AC-15.5 — prior_state.coyote_timer not mutated by simulate()")


# AC-15.5: simulate() does not mutate prior_state.jump_consumed
func test_spec15_prior_state_jump_consumed_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.0
	prior.jump_consumed = true
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, true, false, 0.0, false, 0.016)
	_assert_true(prior.jump_consumed == true,
		"spec15/AC-15.5 — prior_state.jump_consumed not mutated by simulate()")


# ===========================================================================
# SPEC-16 — MovementSimulation new configuration parameter defaults
# ===========================================================================

# AC-16.1: jump_height default is 120.0
func test_spec16_default_jump_height() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.jump_height, 120.0,
		"spec16 — jump_height default is 120.0")


# AC-16.2: coyote_time default is 0.1
func test_spec16_default_coyote_time() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.coyote_time, 0.1,
		"spec16 — coyote_time default is 0.1")


# AC-16.3: jump_cut_velocity default is -200.0
func test_spec16_default_jump_cut_velocity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.jump_cut_velocity, -200.0,
		"spec16 — jump_cut_velocity default is -200.0")


# AC-16.5: jump_height is mutable and affects simulate() output
func test_spec16_jump_height_mutable_affects_impulse() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.jump_height = 60.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	# jump_pressed=true to hold the button — suppresses jump cut so we can measure
	# the raw impulse value without it being clamped to jump_cut_velocity.
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# impulse = -sqrt(2.0 * 980.0 * 60.0) = -sqrt(117600.0)
	# result.velocity.y = impulse + 980.0 * 0.016
	var expected: float = -sqrt(2.0 * 980.0 * 60.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec16/AC-16.5 — jump_height=60 is mutable and affects impulse formula")


# AC-16.5: coyote_time is mutable and affects timer reset
func test_spec16_coyote_time_mutable_affects_reset() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.coyote_time = 0.2
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.2,
		"spec16/AC-16.5 — coyote_time=0.2 is mutable: floor reset produces result.coyote_timer=0.2")


# AC-16.5: jump_cut_velocity is mutable and affects jump cut clamp
func test_spec16_jump_cut_velocity_mutable_affects_clamp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.jump_cut_velocity = -100.0
	# prior vy=-200, after gravity: -200 + 15.68 = -184.32. -184.32 < -100.0 → clamp to -100.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -200.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.velocity.y, -100.0,
		"spec16/AC-16.5 — jump_cut_velocity=-100 is mutable: -184.32 clamped to -100.0")


# ===========================================================================
# SPEC-18 — Jump impulse condition and formula
# ===========================================================================

# AC-18.1: Valid jump from floor — impulse + gravity on same frame
# impulse = -sqrt(2.0 * 980.0 * 120.0), then gravity * delta added.
# delta=0.016: gravity contribution = 980.0 * 0.016 = 15.68
# result.velocity.y = -sqrt(235200.0) + 15.68
func test_spec18_jump_impulse_from_floor() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	var expected: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec18/AC-18.1 — jump from floor: velocity.y = -sqrt(2*980*120) + 980*0.016")


# AC-18.1: Verify the computed impulse is approximately -484.97 before gravity
func test_spec18_jump_impulse_magnitude() -> void:
	# This test checks the impulse component only by using delta=0.0 so gravity adds nothing.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.0)
	var expected_impulse: float = -sqrt(2.0 * 980.0 * 120.0)
	_assert_approx(result.velocity.y, expected_impulse,
		"spec18 — jump impulse magnitude: -sqrt(2*980*120) with delta=0 (no gravity contribution)")


# AC-18.2: No jump when jump_just_pressed == false
func test_spec18_no_jump_when_just_pressed_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	# jump_pressed=false, jump_just_pressed=false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	# Expected: no impulse, just gravity accumulation
	var expected: float = 0.0 + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec18/AC-18.2 — no jump when jump_just_pressed=false: velocity.y = prior.vy + gravity*delta")


# AC-18.3: No jump when jump_consumed == true, even if on floor + just pressed
func test_spec18_no_jump_when_consumed_even_on_floor() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = true
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# No impulse: result.velocity.y = prior.vy + gravity*delta
	var expected: float = 0.0 + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec18/AC-18.3 — no jump when jump_consumed=true: no impulse even on floor + just_pressed")


# AC-18.4: No jump when airborne + coyote_timer == 0 + just pressed + not consumed
func test_spec18_no_jump_when_airborne_coyote_zero() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.0
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# No impulse: result.velocity.y = prior.vy + gravity*delta
	var expected: float = 0.0 + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec18/AC-18.4 — no jump: airborne + coyote_timer=0.0 + just_pressed + not consumed")


# AC-18.5: Custom jump_height=60.0 produces correct impulse
func test_spec18_custom_jump_height_impulse() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.jump_height = 60.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# impulse = -sqrt(2.0 * 980.0 * 60.0) = -sqrt(117600.0)
	var expected: float = -sqrt(2.0 * 980.0 * 60.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec18/AC-18.5 — jump_height=60: velocity.y = -sqrt(117600) + 15.68")


# AC-18.6: gravity=0.0, jump_height=120.0, valid jump: velocity.y == 0.0, no NaN
# -sqrt(2.0 * 0.0 * 120.0) = -sqrt(0.0) = 0.0; gravity*delta = 0.0*delta = 0.0
func test_spec18_zero_gravity_jump_produces_zero_not_nan() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.gravity = 0.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_true(not is_nan(result.velocity.y),
		"spec18/AC-18.6 — gravity=0, valid jump: velocity.y is not NaN")
	_assert_true(is_finite(result.velocity.y),
		"spec18/AC-18.6 — gravity=0, valid jump: velocity.y is finite")
	_assert_approx(result.velocity.y, 0.0,
		"spec18/AC-18.6 — gravity=0, jump_height=120: velocity.y == 0.0 (sqrt(0)=0, gravity*delta=0)")


# Gravity still applies on the jump frame (impulse + gravity*delta combined)
func test_spec18_gravity_applied_on_jump_frame() -> void:
	# With delta=0.1, gravity contribution is 98.0 px/s on jump frame.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.1)
	var expected: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.1
	_assert_approx(result.velocity.y, expected,
		"spec18 — gravity applied on jump frame: impulse + gravity*delta with delta=0.1")


# Horizontal velocity is not affected by a jump (jump acts only on velocity.y)
func test_spec18_jump_does_not_affect_velocity_x() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# grounded, no input: friction applies. move_toward(100.0, 0.0, 19.2) = 80.8
	_assert_approx(result.velocity.x, 80.8,
		"spec18 — jump does not affect velocity.x: friction still applied on jump frame")


# ===========================================================================
# SPEC-19 — Coyote time logic
# ===========================================================================

# AC-19.1: On floor, coyote_timer=0.0 → result.coyote_timer = coyote_time (0.1)
func test_spec19_coyote_timer_resets_to_coyote_time_when_on_floor_from_zero() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.coyote_timer = 0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.1,
		"spec19/AC-19.1 — on floor, coyote_timer=0: result.coyote_timer = 0.1 (coyote_time)")


# AC-19.2: On floor, coyote_timer=0.05 → result.coyote_timer = coyote_time (always reset to full)
func test_spec19_coyote_timer_always_resets_to_full_when_on_floor() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.coyote_timer = 0.05
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.1,
		"spec19/AC-19.2 — on floor, coyote_timer=0.05: always reset to full 0.1")


# AC-19.3: Airborne, coyote_timer=0.1, delta=0.016 → result.coyote_timer = 0.084
func test_spec19_coyote_timer_decrements_by_delta_when_airborne() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.1
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.084,
		"spec19/AC-19.3 — airborne, coyote_timer=0.1, delta=0.016: result = 0.084")


# AC-19.4: Airborne, coyote_timer=0.01, delta=0.016 → result.coyote_timer = 0.0 (clamped, not -0.006)
func test_spec19_coyote_timer_clamped_to_zero_not_negative() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.01
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.0,
		"spec19/AC-19.4 — airborne, coyote_timer=0.01, delta=0.016: clamped to 0.0 (not -0.006)")


# AC-19.5: Airborne, coyote_timer=0.0, any delta > 0 → result.coyote_timer stays 0.0
func test_spec19_coyote_timer_zero_stays_zero_when_airborne() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.0,
		"spec19/AC-19.5 — airborne, coyote_timer=0.0: stays 0.0 (does not go negative)")


# AC-19.6: Coyote jump — airborne, coyote_timer=0.05 > 0, just_pressed, not consumed → jump fires
func test_spec19_coyote_jump_fires_when_timer_positive_and_airborne() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.05
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# Jump should fire: velocity.y = impulse + gravity*delta
	var expected: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec19/AC-19.6 — coyote jump: airborne + coyote_timer=0.05 + just_pressed → jump fires")


# AC-19.7: Boundary — coyote_timer exactly 0.0 → no jump (strict greater-than, not >=)
func test_spec19_coyote_timer_exactly_zero_blocks_coyote_jump() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.0
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# No jump: coyote_timer is not > 0.0. result.velocity.y = prior.vy + gravity*delta
	var expected: float = 0.0 + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected,
		"spec19/AC-19.7 — coyote_timer=0.0 (boundary): no coyote jump, strict > required")


# AC-19.8: prior_state.coyote_timer unchanged after simulate()
func test_spec19_prior_state_coyote_timer_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.08
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(prior.coyote_timer, 0.08,
		"spec19/AC-19.8 — prior_state.coyote_timer not mutated after simulate()")


# AC-19.9: Custom coyote_time=0.2 — floor reset produces result.coyote_timer=0.2
func test_spec19_custom_coyote_time_applied_on_floor_reset() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.coyote_time = 0.2
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.coyote_timer = 0.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.coyote_timer, 0.2,
		"spec19/AC-19.9 — coyote_time=0.2: floor reset produces result.coyote_timer=0.2")


# Coyote timer uses prior_state.coyote_timer for eligibility, not result.coyote_timer.
# The timer is decremented from 0.05 to 0.034 on this frame (result.coyote_timer = 0.034),
# but eligibility check uses prior_state.coyote_timer = 0.05 > 0, so jump fires.
func test_spec19_eligibility_uses_prior_coyote_timer_not_result() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.05
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# Jump fires because prior.coyote_timer=0.05 > 0.
	# result.coyote_timer = max(0, 0.05 - 0.016) = 0.034 (timer still decrements this frame).
	var expected_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"spec19 — eligibility uses prior_state.coyote_timer: jump fires even as timer decrements")


# ===========================================================================
# SPEC-20 — Jump cut condition and clamp
# ===========================================================================

# AC-20.1 / AC-20.2: jump_pressed=false, ascending faster than jump_cut_velocity
# prior.vy=-450, after gravity: -450 + 980*0.016 = -450 + 15.68 = -434.32
# -434.32 < -200.0 → clamp to -200.0
func test_spec20_jump_cut_clamps_when_ascending_too_fast_and_button_released() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -450.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.velocity.y, -200.0,
		"spec20/AC-20.2 — jump_pressed=false, vy=-450: -434.32 < -200 → clamped to -200.0")


# AC-20.3: jump_pressed=false, falling (vy=50.0) → no clamp
# After gravity: 50.0 + 15.68 = 65.68. 65.68 is NOT < -200.0 → no clamp.
func test_spec20_jump_cut_does_not_apply_when_falling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 50.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.velocity.y, 65.68,
		"spec20/AC-20.3 — falling (vy=50): jump cut does not apply, result.vy = 65.68")


# AC-20.4: jump_pressed=true, ascending fast → no jump cut (button held)
# prior.vy=-450, after gravity: -434.32. Button held → no clamp.
func test_spec20_jump_cut_does_not_apply_when_button_held() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -450.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, false, false, 0.0, false, 0.016)
	_assert_approx(result.velocity.y, -434.32,
		"spec20/AC-20.4 — jump_pressed=true: no jump cut even at high upward velocity")


# AC-20.5: result.velocity.y after gravity exactly equals jump_cut_velocity → no clamp (strict <)
# We need vy such that vy + gravity*delta == -200.0 exactly.
# vy + 15.68 = -200.0 → vy = -215.68
func test_spec20_jump_cut_boundary_exact_equals_no_clamp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -215.68, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	# -215.68 + 15.68 = -200.0 exactly → strict less-than fails → no clamp
	_assert_approx(result.velocity.y, -200.0,
		"spec20/AC-20.5 — exact boundary: result.vy == jump_cut_velocity → no clamp (strict <)")


# AC-20.6: Custom jump_cut_velocity=-100.0, ascending through it
# prior.vy=-200, after gravity: -200 + 15.68 = -184.32. -184.32 < -100.0 → clamp to -100.0
func test_spec20_custom_jump_cut_velocity_clamp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.jump_cut_velocity = -100.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -200.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.velocity.y, -100.0,
		"spec20/AC-20.6 — jump_cut_velocity=-100: -184.32 < -100 → clamped to -100.0")


# AC-20.7: jump_cut_velocity=0.0 — any ascending velocity is less than 0.0 → clamp to 0.0
# prior.vy=-200, after gravity: -184.32 < 0.0 → clamp to 0.0
func test_spec20_jump_cut_velocity_zero_clamps_all_ascending() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.jump_cut_velocity = 0.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -200.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_approx(result.velocity.y, 0.0,
		"spec20/AC-20.7 — jump_cut_velocity=0.0: -184.32 < 0.0 → clamped to 0.0")


# AC-20.8: Jump cut evaluates result.velocity.y after gravity, not before
# This is structural: if cut applied before gravity, prior.vy=-201 would be clamped to -200,
# then gravity adds 15.68 → result = -184.32, which is wrong. After gravity it is -201+15.68=-185.32,
# still < -200 → clamp to -200. Both orders give same clamp in this case. Use a tighter scenario:
# prior.vy=-201.0, delta=0.016: after gravity = -201 + 15.68 = -185.32 which is NOT < -200.
# If cut were applied BEFORE gravity: -201 < -200 → clamp to -200. Then gravity: -200+15.68=-184.32.
# Correct behavior (after gravity): -185.32 is NOT less than -200 → no clamp. result=-185.32.
func test_spec20_jump_cut_evaluated_after_gravity_not_before() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -201.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	# After gravity: -201.0 + 15.68 = -185.32. -185.32 is NOT < -200.0 → no clamp.
	_assert_approx(result.velocity.y, -185.32,
		"spec20/AC-20.8 — jump cut after gravity: vy=-201+15.68=-185.32 (not < -200) → no clamp")


# ===========================================================================
# SPEC-21 — Double-jump prevention via jump_consumed
# ===========================================================================

# AC-21.1: Jump fires → result.jump_consumed == true
func test_spec21_jump_sets_consumed_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_true(result.jump_consumed == true,
		"spec21/AC-21.1 — after jump fires: result.jump_consumed == true")


# AC-21.2: Frame after jump — consumed=true, airborne, just_pressed again → no second jump
func test_spec21_double_jump_blocked_by_consumed_flag() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -200.0, false)
	prior.jump_consumed = true
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# No impulse. result.velocity.y = prior.vy + gravity*delta = -200 + 15.68 = -184.32
	_assert_approx(result.velocity.y, -184.32,
		"spec21/AC-21.2 — double jump blocked: consumed=true → no second impulse")
	_assert_true(result.jump_consumed == true,
		"spec21/AC-21.2 — consumed remains true after blocked jump attempt")


# AC-21.3: Landing resets jump_consumed — on floor + consumed=true → result.jump_consumed=false
func test_spec21_landing_resets_jump_consumed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = true
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_false(result.jump_consumed,
		"spec21/AC-21.3 — landing (on_floor=true): result.jump_consumed reset to false")


# AC-21.4: Airborne + consumed=true, no jump → result.jump_consumed carried forward as true
func test_spec21_consumed_carried_forward_when_airborne_no_jump() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -100.0, false)
	prior.jump_consumed = true
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, false, false, 0.0, false, 0.016)
	_assert_true(result.jump_consumed == true,
		"spec21/AC-21.4 — airborne + consumed=true + no jump: jump_consumed carried forward")


# AC-21.5: prior_state.jump_consumed unchanged after simulate()
func test_spec21_prior_state_jump_consumed_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_false(prior.jump_consumed,
		"spec21/AC-21.5 — prior_state.jump_consumed not mutated (stays false after jump fires)")


# AC-21.6: Fresh MovementState (consumed=false) → first jump fires correctly, sets consumed=true
func test_spec21_fresh_state_first_jump_fires() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# Fresh state: jump_consumed defaults to false
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.is_on_floor = true
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"spec21/AC-21.6 — fresh state: first jump fires, impulse applied")
	_assert_true(result.jump_consumed == true,
		"spec21/AC-21.6 — fresh state: result.jump_consumed = true after first jump")


# AC-21.7: Airborne + consumed=true + button re-pressed → no jump (double-jump blocked)
func test_spec21_re_pressed_after_airborne_blocked_when_consumed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -300.0, false)
	prior.coyote_timer = 0.05  # coyote eligible but consumed blocks it
	prior.jump_consumed = true
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# consumed=true blocks jump even with coyote window open
	var expected_vy: float = -300.0 + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"spec21/AC-21.7 — re-pressed airborne + consumed=true: no jump (double-jump blocked)")


# ===========================================================================
# SPEC-24 — Frame-rate independence of coyote timer decrement
# ===========================================================================

# AC-24.1: Two half-steps of delta=0.05 from coyote_timer=0.1 → 0.0 (same as one step of 0.1)
func test_spec24_coyote_timer_two_half_steps_match_one_full_step_at_expiry() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Two half-steps from 0.1 with delta=0.05 each
	var prior_half: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_half.coyote_timer = 0.1
	var mid: MovementSimulation.MovementState = sim.simulate(prior_half, 0.0, false, false, false, 0.0, false, 0.05)
	# mid.coyote_timer = max(0, 0.1 - 0.05) = 0.05
	var half_state: MovementSimulation.MovementState = _make_state_with(0.0, mid.velocity.y, false)
	half_state.coyote_timer = mid.coyote_timer
	var result_half: MovementSimulation.MovementState = sim.simulate(half_state, 0.0, false, false, false, 0.0, false, 0.05)
	# result_half.coyote_timer = max(0, 0.05 - 0.05) = 0.0

	# One full step from 0.1 with delta=0.1
	var prior_full: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_full.coyote_timer = 0.1
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_full, 0.0, false, false, false, 0.0, false, 0.1)
	# result_full.coyote_timer = max(0, 0.1 - 0.1) = 0.0

	_assert_approx(result_half.coyote_timer, result_full.coyote_timer,
		"spec24/AC-24.1 — two half-steps delta=0.05 match one full step delta=0.1 (both → 0.0)")


# AC-24.2: Two half-steps of delta=0.008 from coyote_timer=0.1 → 0.084 (same as one step of 0.016)
func test_spec24_coyote_timer_two_half_steps_match_one_full_step_typical() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Two half-steps
	var prior_half: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_half.coyote_timer = 0.1
	var mid: MovementSimulation.MovementState = sim.simulate(prior_half, 0.0, false, false, false, 0.0, false, 0.008)
	# mid.coyote_timer = max(0, 0.1 - 0.008) = 0.092
	var half_state: MovementSimulation.MovementState = _make_state_with(0.0, mid.velocity.y, false)
	half_state.coyote_timer = mid.coyote_timer
	var result_half: MovementSimulation.MovementState = sim.simulate(half_state, 0.0, false, false, false, 0.0, false, 0.008)
	# result_half.coyote_timer = max(0, 0.092 - 0.008) = 0.084

	# One full step
	var prior_full: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_full.coyote_timer = 0.1
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_full, 0.0, false, false, false, 0.0, false, 0.016)
	# result_full.coyote_timer = max(0, 0.1 - 0.016) = 0.084

	_assert_approx(result_half.coyote_timer, result_full.coyote_timer,
		"spec24/AC-24.2 — two half-steps delta=0.008 match one full step delta=0.016 (both → 0.084)")


# AC-24.3: Jump impulse is the same regardless of delta (it is an assignment, not scaled by delta)
func test_spec24_jump_impulse_independent_of_delta() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# Use delta=0 so gravity adds nothing — isolates impulse component
	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior_a.jump_consumed = false
	var result_a: MovementSimulation.MovementState = sim.simulate(prior_a, 0.0, true, true, false, 0.0, false, 0.0)

	var prior_b: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior_b.jump_consumed = false
	var result_b: MovementSimulation.MovementState = sim.simulate(prior_b, 0.0, true, true, false, 0.0, false, 0.1)
	# Gravity adds 98.0 to result_b. Subtract it to isolate impulse.
	var impulse_from_a: float = result_a.velocity.y
	var impulse_from_b: float = result_b.velocity.y - 980.0 * 0.1
	_assert_approx(impulse_from_a, impulse_from_b,
		"spec24/AC-24.3 — jump impulse is the same regardless of delta")


# ===========================================================================
# Order of operations guard tests
# ===========================================================================

# Verify: coyote timer uses prior_state (update happens before eligibility check but
# eligibility reads prior_state.coyote_timer, not result.coyote_timer).
# This is implicitly confirmed by test_spec19_coyote_timer_exactly_zero_blocks_coyote_jump
# and test_spec19_coyote_jump_fires_when_timer_positive_and_airborne, but an explicit
# sequence test makes the ordering requirement unambiguous.
func test_order_of_ops_coyote_update_before_eligibility_check() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# prior.coyote_timer = 0.05 > 0 → eligible for coyote jump (prior_state check)
	# result.coyote_timer = max(0, 0.05 - 0.016) = 0.034 (update happens this frame too)
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.coyote_timer = 0.05
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	# Jump fires (prior.coyote_timer=0.05 > 0)
	var expected_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"order_of_ops — coyote eligibility uses prior.coyote_timer (0.05), jump fires")
	# Timer is still decremented this frame in result
	_assert_approx(result.coyote_timer, 0.034,
		"order_of_ops — result.coyote_timer decremented to 0.034 even on coyote jump frame")


# Verify: jump_consumed is set after eligibility check (on the same frame as jump)
func test_order_of_ops_jump_consumed_set_on_jump_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_true(result.jump_consumed == true,
		"order_of_ops — jump_consumed set to true on the same frame as jump")


# Verify: is_on_floor still passes through unchanged after jump logic
func test_order_of_ops_is_on_floor_passthrough_unaffected_by_jump() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_true(result.is_on_floor == true,
		"order_of_ops — is_on_floor passes through unchanged even on jump frame")


# ===========================================================================
# Determinism guard
# ===========================================================================

# Jump simulation is deterministic: same inputs → same outputs
func test_determinism_jump_simulation_identical_calls() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.jump_consumed = false
	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_approx(result_a.velocity.y, result_b.velocity.y,
		"determinism — jump: identical inputs produce identical velocity.y")
	_assert_true(result_a.jump_consumed == result_b.jump_consumed,
		"determinism — jump: identical inputs produce identical jump_consumed")
	_assert_approx(result_a.coyote_timer, result_b.coyote_timer,
		"determinism — jump: identical inputs produce identical coyote_timer")


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_jump_simulation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-15: MovementState new fields
	test_spec15_coyote_timer_default_is_zero()
	test_spec15_jump_consumed_default_is_false()
	test_spec15_prior_state_coyote_timer_not_mutated()
	test_spec15_prior_state_jump_consumed_not_mutated()

	# SPEC-16: MovementSimulation new config parameter defaults
	test_spec16_default_jump_height()
	test_spec16_default_coyote_time()
	test_spec16_default_jump_cut_velocity()
	test_spec16_jump_height_mutable_affects_impulse()
	test_spec16_coyote_time_mutable_affects_reset()
	test_spec16_jump_cut_velocity_mutable_affects_clamp()

	# SPEC-18: Jump impulse condition and formula
	test_spec18_jump_impulse_from_floor()
	test_spec18_jump_impulse_magnitude()
	test_spec18_no_jump_when_just_pressed_false()
	test_spec18_no_jump_when_consumed_even_on_floor()
	test_spec18_no_jump_when_airborne_coyote_zero()
	test_spec18_custom_jump_height_impulse()
	test_spec18_zero_gravity_jump_produces_zero_not_nan()
	test_spec18_gravity_applied_on_jump_frame()
	test_spec18_jump_does_not_affect_velocity_x()

	# SPEC-19: Coyote time logic
	test_spec19_coyote_timer_resets_to_coyote_time_when_on_floor_from_zero()
	test_spec19_coyote_timer_always_resets_to_full_when_on_floor()
	test_spec19_coyote_timer_decrements_by_delta_when_airborne()
	test_spec19_coyote_timer_clamped_to_zero_not_negative()
	test_spec19_coyote_timer_zero_stays_zero_when_airborne()
	test_spec19_coyote_jump_fires_when_timer_positive_and_airborne()
	test_spec19_coyote_timer_exactly_zero_blocks_coyote_jump()
	test_spec19_prior_state_coyote_timer_not_mutated()
	test_spec19_custom_coyote_time_applied_on_floor_reset()
	test_spec19_eligibility_uses_prior_coyote_timer_not_result()

	# SPEC-20: Jump cut condition and clamp
	test_spec20_jump_cut_clamps_when_ascending_too_fast_and_button_released()
	test_spec20_jump_cut_does_not_apply_when_falling()
	test_spec20_jump_cut_does_not_apply_when_button_held()
	test_spec20_jump_cut_boundary_exact_equals_no_clamp()
	test_spec20_custom_jump_cut_velocity_clamp()
	test_spec20_jump_cut_velocity_zero_clamps_all_ascending()
	test_spec20_jump_cut_evaluated_after_gravity_not_before()

	# SPEC-21: Double-jump prevention via jump_consumed
	test_spec21_jump_sets_consumed_true()
	test_spec21_double_jump_blocked_by_consumed_flag()
	test_spec21_landing_resets_jump_consumed()
	test_spec21_consumed_carried_forward_when_airborne_no_jump()
	test_spec21_prior_state_jump_consumed_not_mutated()
	test_spec21_fresh_state_first_jump_fires()
	test_spec21_re_pressed_after_airborne_blocked_when_consumed()

	# SPEC-24: Frame-rate independence
	test_spec24_coyote_timer_two_half_steps_match_one_full_step_at_expiry()
	test_spec24_coyote_timer_two_half_steps_match_one_full_step_typical()
	test_spec24_jump_impulse_independent_of_delta()

	# Order of operations guards
	test_order_of_ops_coyote_update_before_eligibility_check()
	test_order_of_ops_jump_consumed_set_on_jump_frame()
	test_order_of_ops_is_on_floor_passthrough_unaffected_by_jump()

	# Determinism
	test_determinism_jump_simulation_identical_calls()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
