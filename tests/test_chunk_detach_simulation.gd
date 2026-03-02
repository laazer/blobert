# test_chunk_detach_simulation.gd
#
# Headless unit tests for chunk detach mechanics in scripts/movement_simulation.gd.
#
# This file is a plain Object subclass. It does not extend Node or SceneTree.
# The entry point is run_all(), which is called by tests/run_tests.gd.
#
# It may also be invoked via:
#   godot --headless --path /Users/jacobbrandt/workspace/blobert -s tests/run_tests.gd
#
# Spec coverage:
#   SPEC-46 — MovementState has_chunk field: typed bool, default true, 7th field
#   SPEC-47 — has_chunk default semantics: true=attached, false=detached;
#             simulate() never sets result.has_chunk = true; prior_state not mutated
#   SPEC-48 — Detach step: detach_eligible = detach_just_pressed AND prior.has_chunk;
#             carry-forward when not detaching; detach does not affect other fields
#   SPEC-49 — simulate() 8-argument signature: detach_just_pressed as 7th positional arg
#   SPEC-50 — Call-site migration: existing calls pass false for detach_just_pressed
#   SPEC-53 — Non-functional: typed vars, no dead code, no engine API in simulate()
#
# Checkpoint log (see CHECKPOINTS.md [M1-005]):
#   Test Designer — detach does not affect velocity assertions (SPEC-48 side-effects)
#   Test Designer — simulate()-never-sets-true test design strategy
#   Test Designer — determinism test inputs chosen to span airborne and grounded

class_name ChunkDetachSimulationTests
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


func _assert_vec2_approx(a: Vector2, b: Vector2, test_name: String) -> void:
	if _approx_eq(a.x, b.x) and _approx_eq(a.y, b.y):
		_pass(test_name)
	else:
		_fail(test_name, "got " + str(a) + " expected " + str(b))


# ---------------------------------------------------------------------------
# Factory helper — constructs a state with velocity and floor flag.
# New chunk field (has_chunk) defaults to true per SPEC-46.
# Tests that need has_chunk=false set it explicitly after calling this helper.
# ---------------------------------------------------------------------------

func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# ===========================================================================
# SPEC-46 — MovementState has_chunk field declaration
# ===========================================================================

# AC-46.1: MovementState.new() produces has_chunk == true (default value).
func test_spec46_has_chunk_default_is_true() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	_assert_true(state.has_chunk == true,
		"spec46 — MovementState.new().has_chunk == true (default)")


# AC-46.2: has_chunk field is writable — can be set to false explicitly.
# (Verifies the field is a plain var, not read-only.)
func test_spec46_has_chunk_is_writable() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state.has_chunk = false
	_assert_false(state.has_chunk,
		"spec46 — has_chunk field is writable (can be set to false)")


# AC-46.3: has_chunk field is writable back to true.
func test_spec46_has_chunk_writable_true() -> void:
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state.has_chunk = false
	state.has_chunk = true
	_assert_true(state.has_chunk == true,
		"spec46 — has_chunk field is writable back to true")


# AC-46.4: A freshly constructed MovementSimulation instance can be used immediately;
# has_chunk is available on the returned state without extra setup.
func test_spec46_simulate_result_has_chunk_accessible() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	# detach_just_pressed=false: has_chunk should carry forward (true → true)
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result.has_chunk == true,
		"spec46 — result.has_chunk accessible and carries forward from default true")


# ===========================================================================
# SPEC-47 — has_chunk default semantics and simulate() never sets true
# ===========================================================================

# AC-47.1: simulate() does not mutate prior_state.has_chunk when has_chunk=true.
func test_spec47_prior_state_has_chunk_not_mutated_when_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = true
	var _result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_true(prior.has_chunk == true,
		"spec47 — prior_state.has_chunk=true not mutated by simulate() (detach fired)")


# AC-47.2: simulate() does not mutate prior_state.has_chunk when has_chunk=false.
func test_spec47_prior_state_has_chunk_not_mutated_when_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = false
	var _result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(prior.has_chunk,
		"spec47 — prior_state.has_chunk=false not mutated by simulate()")


# AC-47.3: simulate() never sets result.has_chunk = true via the detach step.
# After detach fires (prior.has_chunk=true + detach_just_pressed=true), result.has_chunk=false.
# On the next frame with detach_just_pressed=false and prior.has_chunk=false: result stays false.
# No path in simulate() should produce result.has_chunk=true.
func test_spec47_simulate_never_sets_has_chunk_true_after_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Frame 1: detach fires → result.has_chunk becomes false
	var prior_f1: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior_f1.has_chunk = true
	var result_f1: MovementSimulation.MovementState = sim.simulate(
		prior_f1, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result_f1.has_chunk,
		"spec47 — after detach fires, result_f1.has_chunk=false")

	# Frame 2: carry-forward with prior.has_chunk=false → result.has_chunk must remain false
	var result_f2: MovementSimulation.MovementState = sim.simulate(
		result_f1, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_false(result_f2.has_chunk,
		"spec47 — simulate() does not restore has_chunk to true on next frame")


# AC-47.4: simulate() never sets result.has_chunk = true — tested with varied inputs.
# Try every combination of detach_just_pressed with prior.has_chunk=false
# to confirm no input combination causes simulate() to set result.has_chunk=true.
func test_spec47_simulate_never_sets_has_chunk_true_any_input() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, -100.0, false)
	prior.has_chunk = false

	# detach_just_pressed=false: carry-forward expected
	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior, 1.0, true, false, false, 0.0, false, 0.016)
	_assert_false(result_a.has_chunk,
		"spec47 — has_chunk=false + detach=false: never set to true")

	# detach_just_pressed=true: still no-op when prior.has_chunk=false
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior, 1.0, true, false, false, 0.0, true, 0.016)
	_assert_false(result_b.has_chunk,
		"spec47 — has_chunk=false + detach=true: still never set to true (no recall in M1-005)")


# AC-47.5: simulate() never sets result.has_chunk = true — grounded frame with jump.
func test_spec47_simulate_never_sets_has_chunk_true_on_jump_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.has_chunk = false
	prior.jump_consumed = false
	# Jump fires on this frame; has_chunk must remain false
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, true, true, false, 0.0, false, 0.016)
	_assert_false(result.has_chunk,
		"spec47 — has_chunk=false stays false even on regular jump frame")


# ===========================================================================
# SPEC-48 — Detach step: condition, result, and order of operations
# ===========================================================================

# AC-48.1: detach fires when detach_just_pressed=true AND prior.has_chunk=true.
# Result: result.has_chunk == false.
func test_spec48_detach_fires_when_just_pressed_and_has_chunk_true() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = true
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result.has_chunk,
		"spec48/AC-48.1 — detach_just_pressed=true + has_chunk=true → result.has_chunk=false")


# AC-48.2: detach is a no-op when detach_just_pressed=false, even if prior.has_chunk=true.
# Result: result.has_chunk carries forward as true.
func test_spec48_detach_noop_when_just_pressed_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = true
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result.has_chunk == true,
		"spec48/AC-48.2 — detach_just_pressed=false + has_chunk=true: carry-forward true")


# AC-48.3: detach is a no-op when prior.has_chunk=false (already detached),
# even if detach_just_pressed=true.
# Result: result.has_chunk carries forward as false.
func test_spec48_detach_noop_when_prior_has_chunk_false() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = false
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result.has_chunk,
		"spec48/AC-48.3 — detach_just_pressed=true + has_chunk=false: no-op, carries false")


# AC-48.4: has_chunk carry-forward across multiple no-detach frames.
# Three consecutive frames with detach_just_pressed=false — has_chunk remains true.
func test_spec48_has_chunk_carry_forward_multiple_frames() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state.has_chunk = true
	state = sim.simulate(state, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(state.has_chunk == true,
		"spec48 — carry-forward frame 1: has_chunk still true")
	state = sim.simulate(state, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(state.has_chunk == true,
		"spec48 — carry-forward frame 2: has_chunk still true")
	state = sim.simulate(state, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(state.has_chunk == true,
		"spec48 — carry-forward frame 3: has_chunk still true")


# AC-48.5: has_chunk=false carry-forward across multiple no-detach frames.
func test_spec48_false_carry_forward_multiple_frames() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	state.has_chunk = false
	state = sim.simulate(state, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_false(state.has_chunk,
		"spec48 — false carry-forward frame 1")
	state = sim.simulate(state, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_false(state.has_chunk,
		"spec48 — false carry-forward frame 2")


# AC-48.6: Detach does NOT affect velocity.
# Prior velocity (100, -50), detach fires → result velocity must be unaffected by detach step.
# (Gravity, friction etc. still apply normally; the detach step adds no extra velocity change.)
func test_spec48_detach_does_not_affect_velocity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Reference: same scenario WITHOUT detach
	var prior_no_detach: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_no_detach.has_chunk = true
	var result_no_detach: MovementSimulation.MovementState = sim.simulate(
		prior_no_detach, 0.0, false, false, false, 0.0, false, 0.016)

	# Detach scenario: same everything, only detach_just_pressed=true
	var prior_detach: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_detach.has_chunk = true
	var result_detach: MovementSimulation.MovementState = sim.simulate(
		prior_detach, 0.0, false, false, false, 0.0, true, 0.016)

	# Detach must not change velocity compared to no-detach
	_assert_approx(result_detach.velocity.x, result_no_detach.velocity.x,
		"spec48/AC-48.6 — detach does not affect velocity.x")
	_assert_approx(result_detach.velocity.y, result_no_detach.velocity.y,
		"spec48/AC-48.6 — detach does not affect velocity.y")


# AC-48.7: Detach does NOT affect is_on_floor.
func test_spec48_detach_does_not_affect_is_on_floor() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Grounded case
	var prior_g: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior_g.has_chunk = true
	var result_g: MovementSimulation.MovementState = sim.simulate(
		prior_g, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_true(result_g.is_on_floor == true,
		"spec48/AC-48.7 — detach does not affect is_on_floor (grounded → still true)")

	# Airborne case
	var prior_a: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_a.has_chunk = true
	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior_a, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result_a.is_on_floor,
		"spec48/AC-48.7 — detach does not affect is_on_floor (airborne → still false)")


# AC-48.8: Detach does NOT affect coyote_timer.
func test_spec48_detach_does_not_affect_coyote_timer() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Reference: airborne, coyote_timer=0.08, no detach
	var prior_ref: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_ref.coyote_timer = 0.08
	prior_ref.has_chunk = true
	var result_ref: MovementSimulation.MovementState = sim.simulate(
		prior_ref, 0.0, false, false, false, 0.0, false, 0.016)

	# Same scenario with detach
	var prior_d: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_d.coyote_timer = 0.08
	prior_d.has_chunk = true
	var result_d: MovementSimulation.MovementState = sim.simulate(
		prior_d, 0.0, false, false, false, 0.0, true, 0.016)

	_assert_approx(result_d.coyote_timer, result_ref.coyote_timer,
		"spec48/AC-48.8 — detach does not affect coyote_timer")


# AC-48.9: Detach does NOT affect jump_consumed.
func test_spec48_detach_does_not_affect_jump_consumed() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# jump_consumed=true, no detach vs. detach
	var prior_ref: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_ref.jump_consumed = true
	prior_ref.has_chunk = true
	var result_ref: MovementSimulation.MovementState = sim.simulate(
		prior_ref, 0.0, false, false, false, 0.0, false, 0.016)

	var prior_d: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_d.jump_consumed = true
	prior_d.has_chunk = true
	var result_d: MovementSimulation.MovementState = sim.simulate(
		prior_d, 0.0, false, false, false, 0.0, true, 0.016)

	_assert_true(result_d.jump_consumed == result_ref.jump_consumed,
		"spec48/AC-48.9 — detach does not affect jump_consumed")


# AC-48.10: Detach does NOT affect is_wall_clinging.
func test_spec48_detach_does_not_affect_is_wall_clinging() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# is_wall_clinging=true requires specific conditions: airborne, on_wall,
	# pressing toward wall, not consumed, timer < max. Use is_wall_clinging=false
	# baseline (the common case) and verify detach doesn't flip it.
	var prior_ref: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_ref.has_chunk = true
	var result_ref: MovementSimulation.MovementState = sim.simulate(
		prior_ref, 0.0, false, false, false, 0.0, false, 0.016)

	var prior_d: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_d.has_chunk = true
	var result_d: MovementSimulation.MovementState = sim.simulate(
		prior_d, 0.0, false, false, false, 0.0, true, 0.016)

	_assert_true(result_d.is_wall_clinging == result_ref.is_wall_clinging,
		"spec48/AC-48.10 — detach does not affect is_wall_clinging")


# AC-48.11: Detach does NOT affect cling_timer.
func test_spec48_detach_does_not_affect_cling_timer() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# cling_timer is 0.0 in non-cling scenarios; detach must not alter it
	var prior_ref: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_ref.has_chunk = true
	var result_ref: MovementSimulation.MovementState = sim.simulate(
		prior_ref, 0.0, false, false, false, 0.0, false, 0.016)

	var prior_d: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_d.has_chunk = true
	var result_d: MovementSimulation.MovementState = sim.simulate(
		prior_d, 0.0, false, false, false, 0.0, true, 0.016)

	_assert_approx(result_d.cling_timer, result_ref.cling_timer,
		"spec48/AC-48.11 — detach does not affect cling_timer")


# AC-48.12: Detach fires correctly regardless of is_on_floor state.
# A player on the floor can detach just as well as an airborne player.
func test_spec48_detach_works_when_grounded() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.has_chunk = true
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result.has_chunk,
		"spec48/AC-48.12 — detach fires on grounded frame (has_chunk becomes false)")


# AC-48.13: Detach fires correctly when airborne (no floor).
func test_spec48_detach_works_when_airborne() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, -200.0, false)
	prior.has_chunk = true
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, true, false, false, 0.0, true, 0.016)
	_assert_false(result.has_chunk,
		"spec48/AC-48.13 — detach fires during airborne state (has_chunk becomes false)")


# AC-48.14: Detach fires correctly during wall cling.
func test_spec48_detach_works_during_wall_cling() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	# Set up cling conditions: airborne, on wall, pressing toward wall (axis=-1 + normal=1)
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.has_chunk = true
	prior.is_wall_clinging = true
	prior.cling_timer = 0.3
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, -1.0, false, false, true, 1.0, true, 0.016)
	_assert_false(result.has_chunk,
		"spec48/AC-48.14 — detach fires during wall cling (has_chunk becomes false)")


# ===========================================================================
# SPEC-49 — simulate() 8-argument signature
# ===========================================================================

# AC-49.1: 8-arg simulate() call succeeds without parse/runtime error.
# This test also validates SPEC-50 call-site pattern: passing false for detach_just_pressed.
func test_spec49_eight_arg_signature_callable() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	# Full 8-arg call: prior_state, input_axis, jump_pressed, jump_just_pressed,
	#                  is_on_wall, wall_normal_x, detach_just_pressed, delta
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result != null,
		"spec49 — 8-arg simulate() call succeeds and returns non-null")


# AC-49.2: detach_just_pressed=true (7th positional) does affect has_chunk.
# Verifies positional argument is correctly placed before delta.
func test_spec49_detach_just_pressed_is_seventh_positional_arg() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = true
	# If detach_just_pressed were the 8th arg (after delta), this would not fire detach.
	# If it is the 7th arg (before delta), detach fires and result.has_chunk=false.
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result.has_chunk,
		"spec49 — detach_just_pressed is 7th positional (before delta): detach fires")


# ===========================================================================
# SPEC-50 — Call-site migration: existing tests use false for detach_just_pressed
# ===========================================================================

# AC-50.1: Passing false for detach_just_pressed leaves all existing physics behavior intact.
# This test mirrors a movement-only scenario from prior suites to confirm migration correctness.
func test_spec50_migration_false_preserves_movement_behavior() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	# Standard grounded+input scenario from SPEC-5 case 1
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 1.0, false, false, false, 0.0, false, 0.016)
	# move_toward(0.0, 200.0, 12.8) = 12.8
	_assert_approx(result.velocity.x, 12.8,
		"spec50 — false for detach_just_pressed: grounded+input vx=12.8 (SPEC-5 case 1 preserved)")


# AC-50.2: Passing false for detach_just_pressed leaves gravity behavior intact.
func test_spec50_migration_false_preserves_gravity() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	# gravity=980 * delta=0.016 = 15.68
	_assert_approx(result.velocity.y, 15.68,
		"spec50 — false for detach_just_pressed: gravity still 15.68 (SPEC-6 preserved)")


# AC-50.3: Passing false for detach_just_pressed leaves has_chunk unchanged from prior.
func test_spec50_migration_false_carries_has_chunk_forward() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior.has_chunk = true  # default, but explicit
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result.has_chunk == true,
		"spec50 — false for detach_just_pressed: has_chunk carries forward (true → true)")


# ===========================================================================
# SPEC-53 — Non-functional: no engine API in simulate(); typed vars
# ===========================================================================

# NF-04 / AC-53.1: simulate() completes without engine API or scene tree access.
# If simulate() called any engine singleton (Input, SceneTree, etc.), this headless
# call would crash or produce an error.
func test_spec53_simulate_is_engine_agnostic() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	# Exercise both detach paths headlessly
	var result_with_detach: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	var result_without_detach: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result_with_detach != null,
		"spec53/NF-04 — simulate() with detach=true completes headlessly")
	_assert_true(result_without_detach != null,
		"spec53/NF-04 — simulate() with detach=false completes headlessly")


# NF-05 / AC-53.2: has_chunk and detach_just_pressed are both exercised in at least one
# code path (no dead code). Verified implicitly by the preceding tests; this test
# makes it explicit by triggering both the eligible and non-eligible branches.
func test_spec53_no_dead_code_both_branches_exercised() -> void:
	var sim: MovementSimulation = MovementSimulation.new()

	# Branch 1: detach_eligible = true (prior.has_chunk=true AND detach_just_pressed=true)
	var prior_a: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior_a.has_chunk = true
	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior_a, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_false(result_a.has_chunk,
		"spec53/NF-05 — eligible branch: detach fires, has_chunk=false")

	# Branch 2: detach_eligible = false (carry-forward)
	var prior_b: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	prior_b.has_chunk = true
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior_b, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result_b.has_chunk == true,
		"spec53/NF-05 — non-eligible branch: carry-forward, has_chunk=true")


# ===========================================================================
# Determinism
# ===========================================================================

# Identical inputs must produce identical has_chunk output (airborne, has_chunk=true).
func test_determinism_has_chunk_identical_inputs_airborne() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(50.0, -100.0, false)
	prior.has_chunk = true
	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior, 0.5, true, false, false, 0.0, true, 0.02)
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior, 0.5, true, false, false, 0.0, true, 0.02)
	_assert_true(result_a.has_chunk == result_b.has_chunk,
		"determinism — has_chunk: identical airborne inputs produce identical output")


# Identical inputs must produce identical has_chunk output (grounded, no detach).
func test_determinism_has_chunk_identical_inputs_grounded_no_detach() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.has_chunk = true
	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result_a.has_chunk == result_b.has_chunk,
		"determinism — has_chunk: identical grounded inputs produce identical output")


# Identical inputs must produce identical has_chunk output (already detached, no detach press).
func test_determinism_has_chunk_identical_inputs_already_detached() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.has_chunk = false
	var result_a: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	var result_b: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, false, 0.016)
	_assert_true(result_a.has_chunk == result_b.has_chunk,
		"determinism — has_chunk: identical inputs with has_chunk=false produce identical output")


# ===========================================================================
# Order-of-operations guard
# ===========================================================================

# The detach step is the FINAL step. All other fields (velocity, coyote_timer, etc.)
# must be computed normally before detach runs. Verify by checking that a detach
# frame still applies gravity correctly to velocity.y.
func test_order_of_ops_detach_is_last_step_gravity_still_applies() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior.has_chunk = true
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	# Even though detach fired, gravity must still apply: vy = 0 + 980*0.016 = 15.68
	_assert_approx(result.velocity.y, 15.68,
		"order_of_ops — detach is last step: gravity still applied (vy=15.68)")
	_assert_false(result.has_chunk,
		"order_of_ops — detach fired correctly in last step (has_chunk=false)")


# is_on_floor pass-through still works on a detach frame.
func test_order_of_ops_is_on_floor_passthrough_on_detach_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.has_chunk = true
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016)
	_assert_true(result.is_on_floor == true,
		"order_of_ops — is_on_floor passes through correctly on detach frame")
	_assert_false(result.has_chunk,
		"order_of_ops — has_chunk=false on same detach frame")


# Jump fires correctly on a detach frame (detach and jump can coexist on the same frame).
# Only has_chunk should change; jump impulse must be unaffected.
func test_order_of_ops_jump_and_detach_same_frame() -> void:
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, true)
	prior.has_chunk = true
	prior.jump_consumed = false
	# Both jump and detach inputs on same frame
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, true, true, false, 0.0, true, 0.016)
	# Jump impulse: -sqrt(2*980*120) + 980*0.016
	var expected_vy: float = -sqrt(2.0 * 980.0 * 120.0) + 980.0 * 0.016
	_assert_approx(result.velocity.y, expected_vy,
		"order_of_ops — jump impulse fires correctly on same frame as detach")
	_assert_false(result.has_chunk,
		"order_of_ops — detach also fires on same frame as jump (has_chunk=false)")
	_assert_true(result.jump_consumed == true,
		"order_of_ops — jump_consumed set true on same frame as detach")


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_chunk_detach_simulation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# SPEC-46: has_chunk field declaration
	test_spec46_has_chunk_default_is_true()
	test_spec46_has_chunk_is_writable()
	test_spec46_has_chunk_writable_true()
	test_spec46_simulate_result_has_chunk_accessible()

	# SPEC-47: has_chunk default semantics; simulate() never sets true
	test_spec47_prior_state_has_chunk_not_mutated_when_true()
	test_spec47_prior_state_has_chunk_not_mutated_when_false()
	test_spec47_simulate_never_sets_has_chunk_true_after_detach()
	test_spec47_simulate_never_sets_has_chunk_true_any_input()
	test_spec47_simulate_never_sets_has_chunk_true_on_jump_frame()

	# SPEC-48: Detach step
	test_spec48_detach_fires_when_just_pressed_and_has_chunk_true()
	test_spec48_detach_noop_when_just_pressed_false()
	test_spec48_detach_noop_when_prior_has_chunk_false()
	test_spec48_has_chunk_carry_forward_multiple_frames()
	test_spec48_false_carry_forward_multiple_frames()
	test_spec48_detach_does_not_affect_velocity()
	test_spec48_detach_does_not_affect_is_on_floor()
	test_spec48_detach_does_not_affect_coyote_timer()
	test_spec48_detach_does_not_affect_jump_consumed()
	test_spec48_detach_does_not_affect_is_wall_clinging()
	test_spec48_detach_does_not_affect_cling_timer()
	test_spec48_detach_works_when_grounded()
	test_spec48_detach_works_when_airborne()
	test_spec48_detach_works_during_wall_cling()

	# SPEC-49: 8-arg signature
	test_spec49_eight_arg_signature_callable()
	test_spec49_detach_just_pressed_is_seventh_positional_arg()

	# SPEC-50: Call-site migration
	test_spec50_migration_false_preserves_movement_behavior()
	test_spec50_migration_false_preserves_gravity()
	test_spec50_migration_false_carries_has_chunk_forward()

	# SPEC-53: Non-functional
	test_spec53_simulate_is_engine_agnostic()
	test_spec53_no_dead_code_both_branches_exercised()

	# Determinism
	test_determinism_has_chunk_identical_inputs_airborne()
	test_determinism_has_chunk_identical_inputs_grounded_no_detach()
	test_determinism_has_chunk_identical_inputs_already_detached()

	# Order-of-operations guards
	test_order_of_ops_detach_is_last_step_gravity_still_applies()
	test_order_of_ops_is_on_floor_passthrough_on_detach_frame()
	test_order_of_ops_jump_and_detach_same_frame()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
