# test_movement_simulation.gd
#
# Headless unit tests for scripts/movement_simulation.gd.
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked standalone:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Spec coverage:
#   SPEC-1  — File and class structure (class_name, inner class, no engine refs)
#   SPEC-2  — MovementState inner class: defaults and immutability contract
#   SPEC-3  — Exported configuration parameter defaults
#   SPEC-4  — simulate() public API: is_on_floor pass-through, zero-delta, new object returned
#   SPEC-5  — Horizontal movement: all four cases (AC-5.1 through AC-5.5)
#   SPEC-6  — Vertical movement: gravity formula, unconditional application, no terminal velocity
#   SPEC-12 — Frame-rate independence (linear delta scaling, two-half-step == one-full-step)
#   SPEC-13 — Headless instantiability with no scene tree
#   SPEC-14 — (all local variables and helper signatures are typed throughout)

class_name MovementSimulationTests
extends Object

# ---------------------------------------------------------------------------
# CHECKPOINT [TD-001]: Epsilon for floating-point comparisons.
# Would have asked: what tolerance is acceptable for float equality in tests?
# Assumption: 1e-4 is tight enough to catch formula errors while absorbing
# IEEE-754 rounding in GDScript's float arithmetic.
# Confidence: High
# (Also logged in CHECKPOINTS.md)
# ---------------------------------------------------------------------------
const EPSILON: float = 1e-4

# Counts for summary reporting.
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


func _assert_approx(a: float, b: float, test_name: String) -> void:
	if _approx_eq(a, b):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (delta " + str(abs(a - b)) + ")")


func _assert_vec2_approx(a: Vector2, b: Vector2, test_name: String) -> void:
	if _approx_eq(a.x, b.x) and _approx_eq(a.y, b.y):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


# ---------------------------------------------------------------------------
# Factory helper — every test starts from an explicit, clean state.
# Direct construction (MovementSimulation.new() / MovementSimulation.MovementState.new())
# is used in tests where the default state is wanted, to keep each test's
# intent obvious at the call site. This helper is used when non-default
# field values are needed.
# ---------------------------------------------------------------------------

func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ===========================================================================
# SPEC-1 / SPEC-13 — Class structure and headless instantiability
# ===========================================================================

# AC-1.6 / AC-13.1: MovementSimulation.new() succeeds without a scene tree and
# returns a non-null object.
func test_spec1_instantiation_succeeds() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_true(sim != null,
		"spec1/13 — MovementSimulation.new() returns non-null object")


# AC-1.4: MovementSimulation.MovementState inner class is accessible via the
# outer class name.
func test_spec1_inner_class_accessible() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_true(state != null,
		"spec1 — MovementSimulation.MovementState.new() returns non-null object")


# AC-13.1 (smoke): The full simulate() round-trip runs without errors in headless
# context. This test would crash/error if any engine singleton were accessed.
func test_spec13_headless_smoke() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	var result: MovementSimulation.MovementState = sim.simulate(state, 1.0, false, false, 0.016)
	_assert_true(result != null,
		"spec13 — simulate() returns non-null in headless context")
	_assert_true(result.velocity.x > 0.0,
		"spec13 — simulate() returns positive velocity.x with positive input_axis in headless context")


# ===========================================================================
# SPEC-2 — MovementState inner class defaults
# ===========================================================================

# AC-2.1 / AC-2.3: Default velocity is Vector2.ZERO.
func test_spec2_default_velocity_is_zero() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_vec2_approx(state.velocity, Vector2.ZERO,
		"spec2 — MovementState default velocity is Vector2.ZERO")


# AC-2.2 / AC-2.3: Default is_on_floor is false.
func test_spec2_default_is_on_floor_is_false() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_true(state.is_on_floor == false,
		"spec2 — MovementState default is_on_floor is false")


# ===========================================================================
# SPEC-3 — Exported configuration parameter defaults
# ===========================================================================

# AC-3.1: max_speed default is 200.0.
func test_spec3_default_max_speed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.max_speed, 200.0,
		"spec3 — max_speed default is 200.0")


# AC-3.2: acceleration default is 800.0.
func test_spec3_default_acceleration() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.acceleration, 800.0,
		"spec3 — acceleration default is 800.0")


# AC-3.3: friction default is 1200.0.
func test_spec3_default_friction() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.friction, 1200.0,
		"spec3 — friction default is 1200.0")


# AC-3.4: air_deceleration default is 0.0.
func test_spec3_default_air_deceleration() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.air_deceleration, 0.0,
		"spec3 — air_deceleration default is 0.0")


# AC-3.5: gravity default is 980.0.
func test_spec3_default_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_approx(sim.gravity, 980.0,
		"spec3 — gravity default is 980.0")


# ===========================================================================
# SPEC-4 — simulate() public API: is_on_floor pass-through, zero-delta, immutability
# ===========================================================================

# AC-4.3: is_on_floor passes through as true when prior is true.
func test_spec4_is_on_floor_passthrough_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_true(result.is_on_floor == true,
		"spec4 — is_on_floor passed through as true")


# AC-4.3: is_on_floor passes through as false when prior is false.
func test_spec4_is_on_floor_passthrough_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_true(result.is_on_floor == false,
		"spec4 — is_on_floor passed through as false")


# AC-4.2: simulate() returns a new object distinct from prior_state.
func test_spec4_returns_new_object() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_true(result != prior,
		"spec4 — simulate() returns a distinct object, not prior_state")


# AC-4.2: prior_state.velocity.x is not mutated by simulate().
func test_spec4_prior_state_velocity_x_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, 10.0, true)
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_approx(prior.velocity.x, 50.0,
		"spec4 — prior_state.velocity.x not mutated by simulate()")


# AC-4.2: prior_state.velocity.y is not mutated by simulate().
func test_spec4_prior_state_velocity_y_not_mutated() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, 10.0, true)
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_approx(prior.velocity.y, 10.0,
		"spec4 — prior_state.velocity.y not mutated by simulate()")


# AC-4.4: delta == 0.0 produces no change in velocity.x (grounded with input).
func test_spec4_zero_delta_no_change_x_grounded_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(75.0, 20.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.0)
	_assert_approx(result.velocity.x, 75.0,
		"spec4 — zero delta, grounded+input: velocity.x unchanged")


# AC-4.4: delta == 0.0 produces no change in velocity.y (gravity * 0.0 == 0.0).
func test_spec4_zero_delta_no_change_y() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 20.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.0)
	_assert_approx(result.velocity.y, 20.0,
		"spec4 — zero delta: velocity.y unchanged (gravity * 0 == 0)")


# AC-4.4: delta == 0.0, airborne with input — velocity.x still unchanged.
func test_spec4_zero_delta_no_change_x_airborne_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.0)
	_assert_approx(result.velocity.x, 100.0,
		"spec4 — zero delta, airborne+input: velocity.x unchanged")


# ===========================================================================
# SPEC-5 — Horizontal movement: all four mutually exclusive cases
# ===========================================================================

# AC-5.1 (Case 1 — Grounded with input):
# Accelerates toward max_speed using move_toward(vx, input_axis * max_speed, accel * delta).
# Spec example: vx=0, axis=1, max_speed=200, accel=800, delta=0.016 → vx=12.8
func test_spec5_case1_grounded_input_from_rest() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	# move_toward(0.0, 200.0, 12.8) = 12.8
	_assert_approx(result.velocity.x, 12.8,
		"spec5/case1 — grounded+input from rest: velocity.x = 12.8")


# AC-5.1: move_toward caps at target, not at max_speed explicitly.
# Spec example: vx=190, axis=1, delta=0.016 → step=12.8 > remaining=10 → vx=200.0
func test_spec5_case1_grounded_input_caps_at_target() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(190.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 200.0,
		"spec5/case1 — grounded+input near max_speed: caps at target 200.0")


# AC-5.1: Negative input_axis accelerates in the negative direction.
func test_spec5_case1_grounded_negative_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, 0.016)
	# move_toward(0.0, -200.0, 12.8) = -12.8
	_assert_approx(result.velocity.x, -12.8,
		"spec5/case1 — grounded+negative input from rest: velocity.x = -12.8")


# AC-5.1: Partial input_axis (0.5) targets half max_speed.
func test_spec5_case1_grounded_partial_axis() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	# target = 0.5 * 200.0 = 100.0; step = 800.0 * 0.016 = 12.8
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.5, false, false, 0.016)
	_assert_approx(result.velocity.x, 12.8,
		"spec5/case1 — grounded+axis=0.5 from rest: step=12.8 toward target=100.0")


# AC-5.2 (Case 2 — Grounded with no input / friction):
# Decelerates toward zero using move_toward(vx, 0.0, friction * delta).
# Spec example: vx=100, friction=1200, delta=0.016 → step=19.2, vx=80.8
func test_spec5_case2_grounded_no_input_friction() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 80.8,
		"spec5/case2 — grounded+no input friction: velocity.x = 80.8")


# AC-5.2: move_toward clamps at 0.0, does not overshoot into negative territory.
# Spec example: vx=10.0, step=19.2 → result=0.0
func test_spec5_case2_friction_clamps_at_zero() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(10.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 0.0,
		"spec5/case2 — friction with vx=10 and step>remaining: result is 0.0, not negative")


# AC-5.2: Negative velocity decelerates toward zero (not below zero).
func test_spec5_case2_friction_negative_velocity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(-100.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	# move_toward(-100.0, 0.0, 19.2) = -80.8
	_assert_approx(result.velocity.x, -80.8,
		"spec5/case2 — friction on negative velocity: velocity.x = -80.8")


# AC-5.2: Already at zero with no input — stays at zero.
func test_spec5_case2_friction_already_at_rest() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 0.0,
		"spec5/case2 — friction when already at rest: stays 0.0")


# AC-5.3 (Case 3 — Airborne with input):
# Same formula as Case 1 (acceleration used in air).
# move_toward(0, 200, 12.8) = 12.8
func test_spec5_case3_airborne_input_from_rest() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 12.8,
		"spec5/case3 — airborne+input from rest: velocity.x = 12.8 (same formula as grounded)")


# AC-5.3: Airborne with negative input accelerates in negative direction.
func test_spec5_case3_airborne_negative_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, -1.0, false, false, 0.016)
	_assert_approx(result.velocity.x, -12.8,
		"spec5/case3 — airborne+negative input from rest: velocity.x = -12.8")


# AC-5.4 (Case 4 — Airborne with no input, default air_deceleration=0.0):
# move_toward(vx, 0.0, 0.0 * delta) = vx unchanged.
func test_spec5_case4_airborne_no_input_zero_air_decel() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 100.0,
		"spec5/case4 — airborne+no input+air_decel=0: velocity.x preserved = 100.0")


# AC-5.4: Airborne with no input and non-zero air_deceleration decelerates.
# Spec example: air_decel=400, vx=100, delta=0.016 → step=6.4, vx=93.6
func test_spec5_case4_airborne_no_input_with_air_decel() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.air_deceleration = 400.0
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 93.6,
		"spec5/case4 — airborne+no input+air_decel=400: velocity.x = 93.6")


# AC-5.5: abs(velocity.x) never exceeds max_speed after many frames of continuous input.
func test_spec5_velocity_x_never_exceeds_max_speed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	for _i: int in range(200):
		state = sim.simulate(state, 1.0, false, false, 0.016)
	_assert_true(abs(state.velocity.x) <= sim.max_speed + EPSILON,
		"spec5 — velocity.x never exceeds max_speed after 200 frames of continuous input")


# AC-5.5: max_speed boundary with a custom (non-default) value.
func test_spec5_max_speed_respected_custom_value() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.max_speed = 50.0
	sim.acceleration = 800.0
	var state: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	for _i: int in range(100):
		state = sim.simulate(state, 1.0, false, false, 0.016)
	_assert_true(abs(state.velocity.x) <= sim.max_speed + EPSILON,
		"spec5 — velocity.x never exceeds custom max_speed=50.0")


# ===========================================================================
# SPEC-6 — Vertical movement (gravity)
# ===========================================================================

# AC-6.1 / AC-6.2: result.velocity.y = prior.velocity.y + gravity * delta.
# Spec example: vy=0, gravity=980, delta=0.016 → vy=15.68
func test_spec6_gravity_from_zero() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.y, 15.68,
		"spec6 — gravity from vy=0, delta=0.016: result.velocity.y = 15.68")


# AC-6.1: Gravity accumulates additively across frames.
# Frame 1: vy = 0 + 15.68 = 15.68. Frame 2: vy = 15.68 + 15.68 = 31.36.
func test_spec6_gravity_accumulates_across_frames() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	state = sim.simulate(state, 0.0, false, false, 0.016)
	state = sim.simulate(state, 0.0, false, false, 0.016)
	_assert_approx(state.velocity.y, 31.36,
		"spec6 — gravity accumulates: after 2 frames vy = 31.36")


# AC-6.3: Gravity is applied even when is_on_floor is true (unconditional).
func test_spec6_gravity_applied_on_floor() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.y, 15.68,
		"spec6 — gravity applied unconditionally even when is_on_floor=true: vy = 15.68")


# AC-6.4: delta=0.0 — gravity contribution is zero; vy unchanged.
func test_spec6_zero_delta_no_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 50.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.0)
	_assert_approx(result.velocity.y, 50.0,
		"spec6 — zero delta: gravity * 0 = 0, velocity.y unchanged = 50.0")


# AC-6.5: No terminal velocity cap — vy grows without bound in freefall.
# 300 frames at delta=0.016 (4.8s) → vy = 980 * 4.8 = 4704.0 (approximately).
func test_spec6_no_terminal_velocity_cap() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	for _i: int in range(300):
		state = sim.simulate(state, 0.0, false, false, 0.016)
	_assert_true(state.velocity.y > 4000.0,
		"spec6 — no terminal velocity cap: vy > 4000 after 300 frames of freefall")


# AC-6.1: Gravity respects the configured gravity parameter, not a hardcoded constant.
func test_spec6_gravity_uses_configured_parameter() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.gravity = 500.0
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	# 0.0 + 500.0 * 0.016 = 8.0
	_assert_approx(result.velocity.y, 8.0,
		"spec6 — gravity uses configured parameter: gravity=500, delta=0.016 → vy = 8.0")


# ===========================================================================
# SPEC-12 — Frame-rate independence
# ===========================================================================

# AC-12.1: One step with delta=0.016, accel=800, input=1 from rest → vx=12.8.
func test_spec12_single_step_acceleration() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 12.8,
		"spec12 — single step delta=0.016: velocity.x = 800*0.016 = 12.8")


# AC-12.2: Two half-steps of delta=0.008 produce the same velocity.x as one full step.
# Chosen delta range is safe: step (6.4 or 12.8) << remaining distance (200.0), no overshoot.
# Half-step 1: move_toward(0.0, 200.0, 6.4) = 6.4
# Half-step 2: move_toward(6.4, 200.0, 6.4) = 12.8
# Full step:   move_toward(0.0, 200.0, 12.8) = 12.8  → both equal 12.8
func test_spec12_two_half_steps_match_one_full_step_acceleration() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var mid: MovementSimulation.MovementState = sim.simulate(prior_a, 1.0, false, false, 0.008)
	var result_half: MovementSimulation.MovementState = sim.simulate(mid, 1.0, false, false, 0.008)

	var prior_b: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_b, 1.0, false, false, 0.016)

	_assert_approx(result_half.velocity.x, result_full.velocity.x,
		"spec12 — two half-step acceleration matches one full-step (no overshoot in linear region)")


# AC-12.2: Two half-steps of friction equal one full step (linear region, no overshoot).
# vx=100, friction=1200:
#   Full step: move_toward(100, 0, 19.2) = 80.8
#   Half-step 1: move_toward(100, 0, 9.6) = 90.4
#   Half-step 2: move_toward(90.4, 0, 9.6) = 80.8  → equal
func test_spec12_two_half_steps_match_one_full_step_friction() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior_a: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, true)
	var mid: MovementSimulation.MovementState = sim.simulate(prior_a, 0.0, false, false, 0.008)
	var result_half: MovementSimulation.MovementState = sim.simulate(mid, 0.0, false, false, 0.008)

	var prior_b: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, true)
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_b, 0.0, false, false, 0.016)

	_assert_approx(result_half.velocity.x, result_full.velocity.x,
		"spec12 — two half-step friction matches one full-step (no overshoot in linear region)")


# AC-12.3: One step with delta=0.016, gravity=980, vy=0 → vy=15.68.
func test_spec12_single_step_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.y, 15.68,
		"spec12 — single step gravity delta=0.016: velocity.y = 980*0.016 = 15.68")


# AC-12.3: Two half-steps of gravity equal one full step (gravity is purely additive).
# Half-step 1: vy = 0 + 980*0.008 = 7.84
# Half-step 2: vy = 7.84 + 980*0.008 = 15.68
# Full step:   vy = 0 + 980*0.016 = 15.68  → equal exactly
func test_spec12_two_half_steps_match_one_full_step_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var mid: MovementSimulation.MovementState = sim.simulate(prior_a, 0.0, false, false, 0.008)
	var result_half: MovementSimulation.MovementState = sim.simulate(mid, 0.0, false, false, 0.008)

	var prior_b: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result_full: MovementSimulation.MovementState = sim.simulate(prior_b, 0.0, false, false, 0.016)

	_assert_approx(result_half.velocity.y, result_full.velocity.y,
		"spec12 — two half-step gravity exactly matches one full-step (additive formula)")


# AC-12.4: delta=0.0 — no velocity change in either axis.
func test_spec12_zero_delta_no_velocity_change() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 50.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.0)
	_assert_approx(result.velocity.x, 100.0,
		"spec12 — zero delta: no velocity.x change")
	_assert_approx(result.velocity.y, 50.0,
		"spec12 — zero delta: no velocity.y change")


# ===========================================================================
# Combined axis independence
# ===========================================================================

# Both axes are computed independently per simulate() call.
# Airborne+input: vx=12.8, vy=15.68.
func test_combined_horizontal_and_vertical_independence_airborne_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 12.8,
		"combined — airborne+input: velocity.x = 12.8")
	_assert_approx(result.velocity.y, 15.68,
		"combined — airborne+input: velocity.y = 15.68 (gravity)")


# Grounded+no input: friction on vx, gravity on vy (gravity is unconditional).
func test_combined_grounded_no_input_gravity_still_applied() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, 0.016)
	_assert_approx(result.velocity.x, 80.8,
		"combined — grounded+no input: velocity.x = 80.8 (friction)")
	_assert_approx(result.velocity.y, 15.68,
		"combined — grounded+no input: velocity.y = 15.68 (gravity applied on floor)")


# ===========================================================================
# Determinism
# ===========================================================================

# Calling simulate() twice with identical arguments must produce identical results.
func test_determinism_identical_calls_produce_identical_results() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(55.0, 30.0, false)
	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.7, false, false, 0.02)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.7, false, false, 0.02)
	_assert_approx(result_a.velocity.x, result_b.velocity.x,
		"determinism — identical inputs produce identical velocity.x")
	_assert_approx(result_a.velocity.y, result_b.velocity.y,
		"determinism — identical inputs produce identical velocity.y")
	_assert_true(result_a.is_on_floor == result_b.is_on_floor,
		"determinism — identical inputs produce identical is_on_floor")


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_movement_simulation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-1 / SPEC-13
	test_spec1_instantiation_succeeds()
	test_spec1_inner_class_accessible()
	test_spec13_headless_smoke()

	# SPEC-2
	test_spec2_default_velocity_is_zero()
	test_spec2_default_is_on_floor_is_false()

	# SPEC-3
	test_spec3_default_max_speed()
	test_spec3_default_acceleration()
	test_spec3_default_friction()
	test_spec3_default_air_deceleration()
	test_spec3_default_gravity()

	# SPEC-4
	test_spec4_is_on_floor_passthrough_true()
	test_spec4_is_on_floor_passthrough_false()
	test_spec4_returns_new_object()
	test_spec4_prior_state_velocity_x_not_mutated()
	test_spec4_prior_state_velocity_y_not_mutated()
	test_spec4_zero_delta_no_change_x_grounded_input()
	test_spec4_zero_delta_no_change_y()
	test_spec4_zero_delta_no_change_x_airborne_input()

	# SPEC-5
	test_spec5_case1_grounded_input_from_rest()
	test_spec5_case1_grounded_input_caps_at_target()
	test_spec5_case1_grounded_negative_input()
	test_spec5_case1_grounded_partial_axis()
	test_spec5_case2_grounded_no_input_friction()
	test_spec5_case2_friction_clamps_at_zero()
	test_spec5_case2_friction_negative_velocity()
	test_spec5_case2_friction_already_at_rest()
	test_spec5_case3_airborne_input_from_rest()
	test_spec5_case3_airborne_negative_input()
	test_spec5_case4_airborne_no_input_zero_air_decel()
	test_spec5_case4_airborne_no_input_with_air_decel()
	test_spec5_velocity_x_never_exceeds_max_speed()
	test_spec5_max_speed_respected_custom_value()

	# SPEC-6
	test_spec6_gravity_from_zero()
	test_spec6_gravity_accumulates_across_frames()
	test_spec6_gravity_applied_on_floor()
	test_spec6_zero_delta_no_gravity()
	test_spec6_no_terminal_velocity_cap()
	test_spec6_gravity_uses_configured_parameter()

	# SPEC-12
	test_spec12_single_step_acceleration()
	test_spec12_two_half_steps_match_one_full_step_acceleration()
	test_spec12_two_half_steps_match_one_full_step_friction()
	test_spec12_single_step_gravity()
	test_spec12_two_half_steps_match_one_full_step_gravity()
	test_spec12_zero_delta_no_velocity_change()

	# Combined axis independence
	test_combined_horizontal_and_vertical_independence_airborne_input()
	test_combined_grounded_no_input_gravity_still_applied()

	# Determinism
	test_determinism_identical_calls_produce_identical_results()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
