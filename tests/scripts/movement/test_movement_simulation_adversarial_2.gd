# test_movement_simulation_adversarial_2.gd
#
# TB-014–TB-018 continuation of the movement adversarial suite (split from
# test_movement_simulation_adversarial.gd for MAX_FILE_LINES policy).

class_name MovementSimulationAdversarialTests2
extends "res://tests/utils/test_utils.gd"

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ---------------------------------------------------------------------------
# [M1-001] TB-014 — Input axis exactly at boundary values (-1.0, 0.0, 1.0)
#
# VULNERABILITY: While values near boundaries are tested, the exact float
# boundaries have been tested individually but not in a combined immutability/
# symmetry check. Specifically: is simulate(state, -1.0, d) the exact negation
# of simulate(state, 1.0, d) when starting from rest? This verifies symmetry.
# ---------------------------------------------------------------------------

func test_tb014_input_axis_symmetry_positive_vs_negative_from_rest() -> void:
	# From rest: simulate with +1.0 and -1.0 should produce equal-and-opposite vx.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior_pos: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var prior_neg: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result_pos: MovementSimulation.MovementState = sim.simulate(prior_pos, 1.0, false, false, false, 0.0, [false, false], 0.016)
	var result_neg: MovementSimulation.MovementState = sim.simulate(prior_neg, -1.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result_pos.velocity.x, -result_neg.velocity.x,
		"tb014 — input_axis symmetry: simulate(+1.0) produces -simulate(-1.0) from rest")


func test_tb014_input_axis_exactly_zero_grounded_applies_friction_not_acceleration() -> void:
	# VULNERABILITY: An impl with an off-by-one comparison (e.g., using < 0.0001
	# instead of == 0.0 to detect "no input") might incorrectly apply acceleration
	# toward 0.0 when input_axis is exactly 0.0. This test verifies that the
	# friction path (not the acceleration-toward-zero path) is taken.
	# The result should be identical to the friction test (vx=100 → 80.8).
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, true)
	# input_axis is EXACTLY 0.0 (not a small float).
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result.velocity.x, 80.8,
		"tb014 — input_axis exactly 0.0: friction applied (vx=100 → 80.8), not acceleration toward 0")


# ---------------------------------------------------------------------------
# [M1-001] TB-015 — Multi-frame state machine correctness (floor → air transition)
#
# VULNERABILITY: No existing test verifies a sequence where is_on_floor
# transitions from true to false mid-sequence and the correct formula
# (grounded vs. airborne) is applied each frame.
# ---------------------------------------------------------------------------

func test_tb015_transition_from_grounded_to_airborne_applies_correct_formulas() -> void:
	# Frame 1: grounded + input → vx accelerates (AC-5.1), gravity applies.
	# Frame 2: airborne + input → vx continues with same acceleration (AC-5.3), gravity adds.
	# This verifies that the is_on_floor flag correctly switches the formula path.
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1 — grounded
	var state_ground: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result1: MovementSimulation.MovementState = sim.simulate(state_ground, 1.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result1.velocity.x, 12.8,
		"tb015 — frame 1 grounded: velocity.x = 12.8")
	_assert_approx(result1.velocity.y, 15.68,
		"tb015 — frame 1 grounded: gravity applied, vy = 15.68")

	# Frame 2 — airborne (is_on_floor toggled to false)
	var state_air: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state_air.velocity = result1.velocity
	state_air.is_on_floor = false  # simulate the character leaving the floor
	var result2: MovementSimulation.MovementState = sim.simulate(state_air, 1.0, false, false, false, 0.0, [false, false], 0.016)
	# vx: move_toward(12.8, 200.0, 12.8) = 25.6 (same acceleration formula applies airborne)
	_assert_approx(result2.velocity.x, 25.6,
		"tb015 — frame 2 airborne: velocity.x = 25.6 (same accel formula)")
	# vy: 15.68 + 15.68 = 31.36
	_assert_approx(result2.velocity.y, 31.36,
		"tb015 — frame 2 airborne: gravity accumulates, vy = 31.36")


func test_tb015_transition_from_airborne_to_grounded_applies_friction_not_air_decel() -> void:
	# Moving at vx=100, is_on_floor transitions from false to true.
	# Airborne with no input: air_decel=0.0 preserves velocity.
	# Grounded with no input: friction applies (vx: 100 → 80.8).
	# Test verifies friction (not air_decel=0) is used when is_on_floor=true.
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1 — airborne, no input: vx preserved
	var state_air: MovementSimulation.MovementState = _make_state_with(100.0, 0.0, false)
	var result_air: MovementSimulation.MovementState = sim.simulate(state_air, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result_air.velocity.x, 100.0,
		"tb015 — airborne no input: vx preserved at 100.0")

	# Frame 2 — grounded, no input: friction applies
	var state_ground: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state_ground.velocity = result_air.velocity
	state_ground.is_on_floor = true
	var result_ground: MovementSimulation.MovementState = sim.simulate(state_ground, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_approx(result_ground.velocity.x, 80.8,
		"tb015 — grounded no input after airborne: friction applies, vx = 80.8 (not preserved)")


# ---------------------------------------------------------------------------
# [M1-001] TB-016 — simulate() return value identity: no stale reference
#
# VULNERABILITY: An implementation that returns `prior_state` itself (instead
# of a new object) but modifies it in place would pass the existing
# test_spec4_returns_new_object test IF it allocated a new object in any
# branch. But consider an impl where some paths return `prior_state` directly:
# subsequent modification of the prior state by the caller would corrupt the
# result. This test holds onto the result and checks it is not the same object
# AS prior_state under multiple call conditions.
# ---------------------------------------------------------------------------

func test_tb016_returned_object_is_not_prior_state_regardless_of_delta() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, 30.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.0)
	# Even with delta=0 (no change), the spec requires a new object.
	_assert_true(result != prior,
		"tb016 — delta=0.0: returned object is still distinct from prior_state")


func test_tb016_returned_object_is_not_prior_state_with_zero_input_airborne() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_true(result != prior,
		"tb016 — airborne+no input: returned object distinct from prior_state")


# ---------------------------------------------------------------------------
# [M1-001] TB-017 — Mutation stress: many simultaneous independent simulations
#
# VULNERABILITY: If MovementSimulation stores any mutable state between calls
# (e.g., a cached velocity or a previous delta), then running two separate
# simulation instances simultaneously and interleaving their calls would produce
# different results than calling them in sequence. This tests that the
# simulation is truly stateless across calls.
# ---------------------------------------------------------------------------

func test_tb017_two_independent_sim_instances_produce_identical_results() -> void:
	var sim_a: MovementSimulation = MovementSimulation.new()
	var sim_b: MovementSimulation = MovementSimulation.new()

	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var prior_b: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)

	# Interleave calls on two different instances.
	var r_a1: MovementSimulation.MovementState = sim_a.simulate(prior_a, 1.0, false, false, false, 0.0, [false, false], 0.016)
	var r_b1: MovementSimulation.MovementState = sim_b.simulate(prior_b, 1.0, false, false, false, 0.0, [false, false], 0.016)
	var r_a2: MovementSimulation.MovementState = sim_a.simulate(r_a1, 1.0, false, false, false, 0.0, [false, false], 0.016)
	var r_b2: MovementSimulation.MovementState = sim_b.simulate(r_b1, 1.0, false, false, false, 0.0, [false, false], 0.016)

	_assert_approx(r_a2.velocity.x, r_b2.velocity.x,
		"tb017 — two independent sim instances interleaved: produce identical velocity.x")
	_assert_approx(r_a2.velocity.y, r_b2.velocity.y,
		"tb017 — two independent sim instances interleaved: produce identical velocity.y")


func test_tb017_shared_sim_instance_produces_same_result_as_fresh_instance() -> void:
	# If sim holds hidden state, using the same instance twice with the same
	# prior_state and inputs should produce the same result as a fresh instance.
	var sim_shared: MovementSimulation = MovementSimulation.new()
	var sim_fresh: MovementSimulation = MovementSimulation.new()

	# Warm up the shared sim with 10 frames.
	var warmup_state: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	for _i: int in range(10):
		warmup_state = sim_shared.simulate(warmup_state, 1.0, false, false, false, 0.0, [false, false], 0.016)

	# Now both sims should produce the same result from the same fresh prior state.
	var test_prior: MovementSimulation.MovementState = _make_state_with(50.0, 20.0, false)
	var result_shared: MovementSimulation.MovementState = sim_shared.simulate(test_prior, 0.5, false, false, false, 0.0, [false, false], 0.016)
	var result_fresh: MovementSimulation.MovementState = sim_fresh.simulate(test_prior, 0.5, false, false, false, 0.0, [false, false], 0.016)

	_assert_approx(result_shared.velocity.x, result_fresh.velocity.x,
		"tb017 — warmed-up sim vs. fresh sim: identical velocity.x from same inputs")
	_assert_approx(result_shared.velocity.y, result_fresh.velocity.y,
		"tb017 — warmed-up sim vs. fresh sim: identical velocity.y from same inputs")


# ---------------------------------------------------------------------------
# [M1-001] TB-018 — Partial-frame acceleration: output is proportional to delta
#
# VULNERABILITY: Tests the linear delta scaling invariant with extreme sub-frame
# deltas (very small delta), ensuring the formula doesn't break down at low
# resolutions. Some implementations have minimum-delta guards that unintentionally
# quantize the movement.
# ---------------------------------------------------------------------------

func test_tb018_very_small_delta_produces_proportionally_small_velocity_change() -> void:
	# delta = 0.001 (1ms), accel = 800.0, step = 0.8.
	# move_toward(0.0, 200.0, 0.8) = 0.8.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 1.0, false, false, false, 0.0, [false, false], 0.001)
	_assert_approx(result.velocity.x, 0.8,
		"tb018 — very small delta (0.001s): velocity.x = 800 * 0.001 = 0.8")


func test_tb018_very_small_delta_gravity_proportional() -> void:
	# delta = 0.001, gravity = 980.0: vy = 0.0 + 980 * 0.001 = 0.98.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.001)
	_assert_approx(result.velocity.y, 0.98,
		"tb018 — very small delta (0.001s): velocity.y = 980 * 0.001 = 0.98")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_movement_simulation_adversarial_2.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_tb014_input_axis_symmetry_positive_vs_negative_from_rest()
	test_tb014_input_axis_exactly_zero_grounded_applies_friction_not_acceleration()

	test_tb015_transition_from_grounded_to_airborne_applies_correct_formulas()
	test_tb015_transition_from_airborne_to_grounded_applies_friction_not_air_decel()

	test_tb016_returned_object_is_not_prior_state_regardless_of_delta()
	test_tb016_returned_object_is_not_prior_state_with_zero_input_airborne()

	test_tb017_two_independent_sim_instances_produce_identical_results()
	test_tb017_shared_sim_instance_produces_same_result_as_fresh_instance()

	test_tb018_very_small_delta_produces_proportionally_small_velocity_change()
	test_tb018_very_small_delta_gravity_proportional()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

