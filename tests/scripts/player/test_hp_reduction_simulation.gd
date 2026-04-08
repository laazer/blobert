# test_hp_reduction_simulation.gd
#
# Primary behavioral tests for HP reduction on detach (M1-006).
# Covers SPEC-54 through SPEC-60.
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked via:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Spec coverage:
#   SPEC-54 — MovementState.current_hp field: typed float, default 100.0, 8th field
#   SPEC-55 — MovementSimulation config vars: max_hp, hp_cost_per_detach, min_hp
#   SPEC-56 — simulate() step 18: HP reduction formula, order of operations,
#             reads detach_eligible from step 17, same frame as detach
#   SPEC-57 — HP carry-forward when detach does not fire (plain assignment, no clamp)
#   SPEC-58 — HP floor clamp (min_hp) applied at reduction site only
#   SPEC-59 — simulate() signature unchanged (still 8 args)
#   SPEC-60 — No existing test migration required; HP tests set current_hp explicitly
#
# Checkpoint log (see CHECKPOINTS.md [M1-006]):
#   Test Designer — HP test scope: primary file only per ticket instruction
#   Test Designer — run_tests.gd adversarial entry: add now or defer
#   Test Designer — differential test strategy for non-HP fields
#   Test Designer — explicit current_hp assignment in all HP tests per AC-60.4

class_name HpReductionSimulationTests
extends "res://tests/utils/test_utils.gd"

const EPSILON: float = 1e-4

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _assert_exact(a: float, b: float, test_name: String) -> void:
	if a == b:
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b) + " (exact)")


# ---------------------------------------------------------------------------
# Factory helper — constructs a minimal grounded or airborne prior state.
# AC-60.4: HP tests always set current_hp explicitly below.
# ---------------------------------------------------------------------------

func _make_prior(vx: float, vy: float, on_floor: bool, has_chunk: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	s.has_chunks[0] = has_chunk
	return s


# ---------------------------------------------------------------------------
# SPEC-54 — MovementState.current_hp field declaration
# ---------------------------------------------------------------------------

# AC-54.3: MovementState.new() with no arguments produces current_hp == 100.0.
func test_spec54_current_hp_default_is_100() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_exact(state.current_hp, 100.0,
		"spec54/AC-54.3 — MovementState.new().current_hp == 100.0 (default literal)")


# AC-54.4: current_hp field is readable and writable from outside the class.
func test_spec54_current_hp_is_writable() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state.current_hp = 75.0
	_assert_exact(state.current_hp, 75.0,
		"spec54/AC-54.4 — current_hp field is writable (set to 75.0)")


# AC-54.5: Setting current_hp does not affect any other field on the same instance.
func test_spec54_current_hp_isolated_from_other_fields() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state.current_hp = 50.0
	_assert_true(state.velocity == Vector2.ZERO,
		"spec54/AC-54.5 — current_hp write does not affect velocity")
	_assert_false(state.is_on_floor,
		"spec54/AC-54.5 — current_hp write does not affect is_on_floor")
	_assert_exact(state.coyote_timer, 0.0,
		"spec54/AC-54.5 — current_hp write does not affect coyote_timer")
	_assert_false(state.jump_consumed,
		"spec54/AC-54.5 — current_hp write does not affect jump_consumed")
	_assert_false(state.is_wall_clinging,
		"spec54/AC-54.5 — current_hp write does not affect is_wall_clinging")
	_assert_exact(state.cling_timer, 0.0,
		"spec54/AC-54.5 — current_hp write does not affect cling_timer")
	_assert_true(state.has_chunks[0] == true,
		"spec54/AC-54.5 — current_hp write does not affect has_chunks[0]")


# AC-54.3 via simulate(): result of simulate() carries current_hp; field is accessible.
func test_spec54_simulate_result_current_hp_accessible() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4: explicit assignment
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_true(result != null,
		"spec54 — simulate() result is non-null and current_hp field is accessible")
	_assert_exact(result.current_hp, 100.0,
		"spec54/AC-54.3 — simulate() result.current_hp accessible and equals prior on no-detach")


# ---------------------------------------------------------------------------
# SPEC-55 — MovementSimulation config vars
# ---------------------------------------------------------------------------

# AC-55.1: max_hp default is 100.0.
func test_spec55_max_hp_default() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_exact(sim.max_hp, 100.0,
		"spec55/AC-55.1 — sim.max_hp default == 100.0")


# AC-55.2: hp_cost_per_detach default is 25.0.
func test_spec55_hp_cost_per_detach_default() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_exact(sim.hp_cost_per_detach, 25.0,
		"spec55/AC-55.2 — sim.hp_cost_per_detach default == 25.0")


# AC-55.3: min_hp default is 0.0.
func test_spec55_min_hp_default() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	_assert_exact(sim.min_hp, 0.0,
		"spec55/AC-55.3 — sim.min_hp default == 0.0")


# AC-55.4: All three config vars are independently mutable.
func test_spec55_config_vars_independently_mutable() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.max_hp = 200.0
	sim.hp_cost_per_detach = 10.0
	sim.min_hp = -5.0
	_assert_exact(sim.max_hp, 200.0,
		"spec55/AC-55.4 — max_hp writable to 200.0 independently")
	_assert_exact(sim.hp_cost_per_detach, 10.0,
		"spec55/AC-55.4 — hp_cost_per_detach writable to 10.0 independently")
	_assert_exact(sim.min_hp, -5.0,
		"spec55/AC-55.4 — min_hp writable to -5.0 independently")


# ---------------------------------------------------------------------------
# SPEC-56 — HP reduction formula and order of operations (step 18)
# Case 1: HP decreases by hp_cost_per_detach on a detach frame
# ---------------------------------------------------------------------------

# AC-56.1 (example 1): has_chunk=true + detach_just_pressed=true →
#   result.current_hp = max(0.0, 100.0 - 25.0) = 75.0
func test_spec56_hp_decreases_on_detach_frame() -> void:
	# AC-60.4: explicit current_hp assignment
	var sim: MovementSimulation = MovementSimulation.new()
	# defaults: hp_cost_per_detach=25.0, min_hp=0.0
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 75.0,
		"spec56/AC-56.1 — detach frame: 100.0 - 25.0 = 75.0")


# AC-56.3: Step 18 fires on the same frame as step 17.
# A single simulate() call with detach=true and has_chunk=true simultaneously
# produces result.has_chunk=false AND result.current_hp=75.0.
func test_spec56_hp_and_detach_same_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_false(result.has_chunks[0],
		"spec56/AC-56.3 — detach frame: result.has_chunks[0]=false (step 17 fired)")
	_assert_exact(result.current_hp, 75.0,
		"spec56/AC-56.3 — detach frame: result.current_hp=75.0 (step 18 fired on same frame)")


# AC-56.2 (detach_just_pressed=false case): HP unchanged when no detach.
func test_spec56_hp_unchanged_when_detach_not_pressed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 75.0  # AC-60.4: non-default to prove carry-forward
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(result.current_hp, 75.0,
		"spec56/AC-56.2 — detach_just_pressed=false: current_hp carries forward unchanged")


# AC-56.2 (has_chunk=false case): HP unchanged when chunk already detached,
# even if detach_just_pressed=true (the no-op detach path).
func test_spec56_hp_unchanged_when_no_chunk() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, false)
	prior.current_hp = 75.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 75.0,
		"spec56/AC-56.2 — has_chunk=false + detach=true: HP unchanged (no-op detach)")


# ---------------------------------------------------------------------------
# SPEC-57 — HP carry-forward when detach does not fire
# ---------------------------------------------------------------------------

# AC-57.1: detach_just_pressed=false + has_chunk=true → carry-forward.
func test_spec57_carry_forward_no_press() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 75.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(result.current_hp, 75.0,
		"spec57/AC-57.1 — detach=false + has_chunk=true: current_hp=75.0 carries forward")


# AC-57.2: detach_just_pressed=true + has_chunk=false → no-op; carry-forward.
func test_spec57_carry_forward_chunk_already_gone() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, false)
	prior.current_hp = 75.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 75.0,
		"spec57/AC-57.2 — detach=true + has_chunk=false: current_hp=75.0 carries forward")


# AC-57.3: detach_just_pressed=false + has_chunk=false → carry-forward.
func test_spec57_carry_forward_both_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, false)
	prior.current_hp = 60.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(result.current_hp, 60.0,
		"spec57/AC-57.3 — detach=false + has_chunk=false: current_hp=60.0 carries forward")


# AC-57.6: HP does not drift over multiple no-detach frames.
func test_spec57_hp_stable_across_multiple_no_detach_frames() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	state.current_hp = 60.0  # AC-60.4
	state = sim.simulate(state, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(state.current_hp, 60.0,
		"spec57/AC-57.6 — no-detach frame 1: current_hp=60.0 stable")
	state = sim.simulate(state, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(state.current_hp, 60.0,
		"spec57/AC-57.6 — no-detach frame 2: current_hp=60.0 stable")
	state = sim.simulate(state, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(state.current_hp, 60.0,
		"spec57/AC-57.6 — no-detach frame 3: current_hp=60.0 stable")
	state = sim.simulate(state, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(state.current_hp, 60.0,
		"spec57/AC-57.6 — no-detach frame 4: current_hp=60.0 stable")


# ---------------------------------------------------------------------------
# SPEC-58 — HP floor clamp (min_hp) applied at reduction site only
# ---------------------------------------------------------------------------

# AC-58.2 / AC-56.1 (example 2): HP below cost → clamped to min_hp=0.0.
# prior_hp=10.0, cost=25.0, min_hp=0.0 → result = max(0.0, 10.0-25.0) = 0.0
func test_spec58_hp_clamped_to_floor_when_cost_exceeds_hp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# defaults: hp_cost_per_detach=25.0, min_hp=0.0
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 10.0  # AC-60.4: explicitly below cost
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 0.0,
		"spec58/AC-58.2 — prior_hp=10.0 - cost=25.0 clamped to min_hp=0.0 (not -15.0)")


# AC-58.3 + AC-58.4: HP exactly at floor (0.0); detach still fires.
# prior_hp=0.0, cost=25.0, min_hp=0.0 → result = max(0.0, 0.0-25.0) = 0.0
# has_chunk also becomes false (detach is not gated by HP level).
func test_spec58_hp_at_floor_stays_at_floor_and_detach_fires() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 0.0  # AC-60.4: already at floor
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 0.0,
		"spec58/AC-58.3 — prior_hp=0.0 + detach: result.current_hp stays at 0.0 (floor)")
	_assert_false(result.has_chunks[0],
		"spec58/AC-58.4 — detach fires even when HP is at floor (not gated by HP)")


# AC-56.7 / AC-58.2: delta=0.0 with detach — HP still reduces.
# HP reduction is not delta-dependent; formula fires regardless of zero delta.
func test_spec56_hp_reduces_with_delta_zero() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.0)
	_assert_exact(result.current_hp, 75.0,
		"spec56/AC-56.7 — delta=0.0 + detach: HP still reduces from 100.0 to 75.0")
	_assert_false(result.has_chunks[0],
		"spec56/AC-56.7 — delta=0.0 + detach: has_chunks[0]=false on same frame")


# AC-56.8: Custom hp_cost_per_detach — formula uses configured value not hardcoded 25.0.
# hp_cost=10.0, prior_hp=80.0, min_hp=0.0 → result = max(0.0, 80.0-10.0) = 70.0
func test_spec56_custom_hp_cost_per_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 10.0
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 80.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 70.0,
		"spec56/AC-56.8 — custom hp_cost=10.0: 80.0-10.0=70.0 (not 80.0-25.0=55.0)")


# AC-55.3 / AC-58: Custom min_hp value — floor is respected with non-default floor.
# min_hp=5.0, cost=25.0, prior_hp=20.0 → result = max(5.0, 20.0-25.0) = max(5.0, -5.0) = 5.0
func test_spec58_custom_min_hp_floor_respected() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.min_hp = 5.0
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 20.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 5.0,
		"spec58/AC-55.3 — custom min_hp=5.0: result clamped to 5.0 (not -5.0)")


# AC-55.5 / SPEC-55: max_hp has NO effect on HP reduction.
# Setting max_hp to an unusual value must not alter the formula result.
# prior_hp=100.0, cost=25.0, min_hp=0.0, max_hp=50.0 (below prior_hp!) →
# result = max(0.0, 100.0-25.0) = 75.0  (not clamped to max_hp=50.0)
func test_spec55_max_hp_does_not_affect_hp_reduction() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	sim.max_hp = 50.0  # unusual: below prior_hp
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result.current_hp, 75.0,
		"spec55/AC-55.5 — max_hp=50.0 is NOT enforced as upper clamp: result=75.0 not 50.0")


# ---------------------------------------------------------------------------
# SPEC-56 AC-56.4 — HP step does not affect other MovementState fields
# Differential test: detach frame vs. non-detach frame, all non-HP fields equal.
# ---------------------------------------------------------------------------

# AC-56.4: Non-detach fields are identical between a detach frame and a no-detach frame
# (given identical prior_state and all inputs except detach_just_pressed).
func test_spec56_hp_reduction_does_not_affect_other_fields() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Reference: no detach
	var prior_ref: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior_ref.current_hp = 100.0  # AC-60.4
	var result_ref: MovementSimulation.MovementState = sim.simulate(prior_ref, 0.0, false, false, false, 0.0, [false, false], 0.016)

	# Detach scenario: identical prior and inputs, only detach_just_pressed differs
	var prior_det: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior_det.current_hp = 100.0  # AC-60.4
	var result_det: MovementSimulation.MovementState = sim.simulate(prior_det, 0.0, false, false, false, 0.0, [true, false], 0.016)

	# HP must differ (detach reduces it)
	_assert_exact(result_det.current_hp, 75.0,
		"spec56/AC-56.4 — detach frame: current_hp=75.0 (confirms reduction fired)")

	# All non-HP fields must be identical across the two results
	_assert_true(result_det.velocity.x == result_ref.velocity.x,
		"spec56/AC-56.4 — velocity.x unaffected by HP reduction step")
	_assert_approx(result_det.velocity.y, result_ref.velocity.y,
		"spec56/AC-56.4 — velocity.y unaffected by HP reduction step")
	_assert_true(result_det.is_on_floor == result_ref.is_on_floor,
		"spec56/AC-56.4 — is_on_floor unaffected by HP reduction step")
	_assert_approx(result_det.coyote_timer, result_ref.coyote_timer,
		"spec56/AC-56.4 — coyote_timer unaffected by HP reduction step")
	_assert_true(result_det.jump_consumed == result_ref.jump_consumed,
		"spec56/AC-56.4 — jump_consumed unaffected by HP reduction step")
	_assert_true(result_det.is_wall_clinging == result_ref.is_wall_clinging,
		"spec56/AC-56.4 — is_wall_clinging unaffected by HP reduction step")
	_assert_approx(result_det.cling_timer, result_ref.cling_timer,
		"spec56/AC-56.4 — cling_timer unaffected by HP reduction step")


# ---------------------------------------------------------------------------
# SPEC-61 / NFR-61.C — prior_state immutability: current_hp not mutated
# ---------------------------------------------------------------------------

# AC-56.5 / NFR-61.C: prior_state.current_hp is not modified by simulate().
# Verified by recording current_hp before and after the call.
func test_spec61_prior_state_current_hp_not_mutated_on_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4: explicit starting value
	var hp_before: float = prior.current_hp
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(prior.current_hp, hp_before,
		"spec61/NFR-61.C — prior_state.current_hp=100.0 not mutated by simulate() (detach fired)")


# AC-56.5 / NFR-61.C: prior_state.current_hp not mutated on no-detach frame either.
func test_spec61_prior_state_current_hp_not_mutated_on_no_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 75.0  # AC-60.4
	var hp_before: float = prior.current_hp
	var _result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(prior.current_hp, hp_before,
		"spec61/NFR-61.C — prior_state.current_hp=75.0 not mutated by simulate() (no-detach)")


# ---------------------------------------------------------------------------
# SPEC-59 — simulate() signature unchanged (still 8 args)
# ---------------------------------------------------------------------------

# AC-59.1 / AC-59.4: An 8-arg simulate() call succeeds and returns a valid state.
# This also confirms no 9th argument is required to exercise HP behavior.
func test_spec59_eight_arg_signature_callable_with_hp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.current_hp = 100.0  # AC-60.4
	# Full 8-arg call covering the HP reduction path:
	# prior_state, input_axis, jump_pressed, jump_just_pressed,
	# is_on_wall, wall_normal_x, detach_just_pressed, delta
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_true(result != null,
		"spec59/AC-59.1 — 8-arg simulate() succeeds and returns non-null with HP behavior")
	_assert_exact(result.current_hp, 75.0,
		"spec59/AC-59.1 — 8-arg call produces correct HP result without any 9th arg")


# ---------------------------------------------------------------------------
# SPEC-56: Two consecutive detach presses — frame 2 is a no-op, HP does not change
# Covers Task 2 case 12.
# ---------------------------------------------------------------------------

# Case 12: After detach fires on frame 1 (has_chunk=true → false, HP reduces),
# frame 2 with detach_just_pressed=true and prior.has_chunk=false is a no-op:
# HP must NOT change again on frame 2.
func test_spec56_second_detach_press_is_noop_for_hp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1: detach fires
	var prior_f1: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior_f1.current_hp = 100.0  # AC-60.4
	var result_f1: MovementSimulation.MovementState = sim.simulate(prior_f1, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_false(result_f1.has_chunks[0],
		"spec56 — frame 1: detach fired, has_chunks[0]=false")
	_assert_exact(result_f1.current_hp, 75.0,
		"spec56 — frame 1: HP reduced from 100.0 to 75.0")

	# Frame 2: detach_just_pressed=true but has_chunk=false → no-op
	# HP must remain at 75.0 (not reduce again to 50.0)
	var result_f2: MovementSimulation.MovementState = sim.simulate(result_f1, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_false(result_f2.has_chunks[0],
		"spec56 — frame 2: has_chunks[0] still false (no recall in M1-006)")
	_assert_exact(result_f2.current_hp, 75.0,
		"spec56 — frame 2: HP unchanged at 75.0 (second detach is no-op when has_chunk=false)")


# ---------------------------------------------------------------------------
# Gravity still applies on a detach frame (order-of-operations guard)
# ---------------------------------------------------------------------------

# SPEC-56 step ordering: physics steps (gravity etc.) happen before step 18.
# Detach frame with delta=0.016: gravity must still produce vy=15.68.
func test_order_of_ops_gravity_still_applies_on_detach_frame_with_hp() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4
	var result: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	# gravity=980 * delta=0.016 = 15.68
	_assert_approx(result.velocity.y, 15.68,
		"order_of_ops — gravity (15.68) still applied correctly on HP-reduction detach frame")
	_assert_exact(result.current_hp, 75.0,
		"order_of_ops — HP also reduced on same frame: 75.0 confirms step 18 ran")


# ---------------------------------------------------------------------------
# Determinism — same inputs produce same current_hp output
# ---------------------------------------------------------------------------

# Identical inputs on detach frame → identical current_hp results.
func test_determinism_hp_identical_inputs_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, false, true)
	prior.current_hp = 100.0  # AC-60.4
	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [true, false], 0.016)
	_assert_exact(result_a.current_hp, result_b.current_hp,
		"determinism — identical detach inputs produce identical current_hp output")


# Identical inputs on no-detach frame → identical current_hp results.
func test_determinism_hp_identical_inputs_no_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_prior(0.0, 0.0, true, true)
	prior.current_hp = 60.0  # AC-60.4
	var result_a: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(prior, 0.0, false, false, false, 0.0, [false, false], 0.016)
	_assert_exact(result_a.current_hp, result_b.current_hp,
		"determinism — identical no-detach inputs produce identical current_hp output")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_hp_reduction_simulation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-54: MovementState.current_hp field declaration
	test_spec54_current_hp_default_is_100()
	test_spec54_current_hp_is_writable()
	test_spec54_current_hp_isolated_from_other_fields()
	test_spec54_simulate_result_current_hp_accessible()

	# SPEC-55: MovementSimulation config vars
	test_spec55_max_hp_default()
	test_spec55_hp_cost_per_detach_default()
	test_spec55_min_hp_default()
	test_spec55_config_vars_independently_mutable()

	# SPEC-56: HP reduction formula (step 18)
	test_spec56_hp_decreases_on_detach_frame()
	test_spec56_hp_and_detach_same_frame()
	test_spec56_hp_unchanged_when_detach_not_pressed()
	test_spec56_hp_unchanged_when_no_chunk()
	test_spec56_hp_reduces_with_delta_zero()
	test_spec56_custom_hp_cost_per_detach()
	test_spec56_hp_reduction_does_not_affect_other_fields()
	test_spec56_second_detach_press_is_noop_for_hp()

	# SPEC-57: HP carry-forward
	test_spec57_carry_forward_no_press()
	test_spec57_carry_forward_chunk_already_gone()
	test_spec57_carry_forward_both_false()
	test_spec57_hp_stable_across_multiple_no_detach_frames()

	# SPEC-58: HP floor clamp
	test_spec58_hp_clamped_to_floor_when_cost_exceeds_hp()
	test_spec58_hp_at_floor_stays_at_floor_and_detach_fires()
	test_spec58_custom_min_hp_floor_respected()

	# SPEC-55 max_hp does not affect reduction
	test_spec55_max_hp_does_not_affect_hp_reduction()

	# SPEC-61 / NFR-61.C: prior_state immutability
	test_spec61_prior_state_current_hp_not_mutated_on_detach()
	test_spec61_prior_state_current_hp_not_mutated_on_no_detach()

	# SPEC-59: 8-arg signature
	test_spec59_eight_arg_signature_callable_with_hp()

	# Order-of-operations guards
	test_order_of_ops_gravity_still_applies_on_detach_frame_with_hp()

	# Determinism
	test_determinism_hp_identical_inputs_detach()
	test_determinism_hp_identical_inputs_no_detach()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
