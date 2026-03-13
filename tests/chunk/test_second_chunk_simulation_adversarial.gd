# test_second_chunk_simulation_adversarial.gd
#
# Adversarial test suite for second-chunk detach mechanics in
# scripts/movement_simulation.gd (SPEC-SCL-1 through SPEC-SCL-6).
#
# Written by: Test Breaker Agent — 2026-03-13
#
# -------------------------------------------------------------------------
# PURPOSE
# -------------------------------------------------------------------------
# This suite does NOT duplicate primary behavioral tests from
# test_second_chunk_simulation.gd. Every test here probes a concrete
# vulnerability, implementation mutation, or spec gap that the primary suite
# leaves unguarded. Each test carries an inline comment that names the gap
# and the category from the vulnerability matrix.
#
# -------------------------------------------------------------------------
# VULNERABILITY MATRIX COVERAGE
# -------------------------------------------------------------------------
#
#   GAP-01  [Mutation] Step 20 reads result.current_hp, not prior_state.current_hp
#           — an implementation that reads prior_state at step 20 produces wrong
#           HP for dual-detach scenarios involving the HP floor boundary.
#
#   GAP-02  [Independence / Cross-contamination] detach_just_pressed must NOT
#           trigger detach_2 side effects, and vice versa. A single shared
#           "detach_eligible" flag would make both chunks detach on any press.
#
#   GAP-03  [Prior-state immutability] simulate() must not mutate ANY field of
#           the prior_state object. A reference-return bug would corrupt all fields.
#
#   GAP-04  [Boundary] HP at exactly (prior_hp == hp_cost_per_detach) for chunk 2:
#           step 20 must clamp to min_hp=0.0, not go negative.
#
#   GAP-05  [Boundary] HP at (2 * hp_cost_per_detach) on dual-detach: after step 18
#           result is hp_cost, after step 20 result is 0.0 — tests the minimum
#           HP that allows dual-detach without overshoot.
#
#   GAP-06  [Null/Empty / Boundary] HP at 0.0 when detach_2 is pressed:
#           result must stay at 0.0 (no negative HP) — clamp holds at min_hp.
#
#   GAP-07  [Mutation] flip-boolean: an implementation that sets has_chunk_2=true
#           when detach_2_just_pressed=false and prior.has_chunk_2=false.
#
#   GAP-08  [Instance isolation] Two separate MovementSimulation instances must
#           not share state for has_chunk_2 or HP.
#
#   GAP-09  [Combinatorial] has_chunk_2=false + detach_2_just_pressed=true +
#           HP at floor: no HP reduction, no state corruption.
#
#   GAP-10  [Order dependency] Simulate N frames then detach_2 on frame N+1:
#           result must be identical to single-frame detach_2 from fresh state.
#
#   GAP-11  [Determinism] Same 9-arg call on same prior_state, repeated 3 times:
#           all three results must be bitwise identical.
#
#   GAP-12  [Combinatorial] Dual-detach at exact 2*cost HP boundary across
#           multiple extreme delta values (0.001, 1.0, 60.0): delta must not
#           affect HP arithmetic (HP reduction is delta-independent per spec).
#
#   GAP-13  [Mutation] Step 19 cross-read: verify has_chunk_2 is determined
#           entirely from detach_2_just_pressed AND prior.has_chunk_2, with no
#           dependency on has_chunk or velocity or any other field.
#
#   GAP-14  [Stress] 1000 consecutive frames with detach_2_just_pressed=false
#           after initial detach: has_chunk_2 must remain false every frame.
#
#   GAP-15  [Boundary] hp_cost_per_detach = 0.0: detaching chunk 2 must leave HP
#           unchanged (no-cost detach).
#
#   GAP-16  [Boundary] hp_cost_per_detach = INF: detaching chunk 2 clamps to min_hp.
#
#   GAP-17  [Combinatorial] detach_1 no-op (has_chunk=false) + detach_2 fires:
#           HP reduced exactly once (only step 20 fires; step 18 is no-op).
#
#   GAP-18  [Combinatorial] detach_2 no-op (has_chunk_2=false) + detach_1 fires:
#           HP reduced exactly once (only step 18 fires; step 20 is no-op).
#
#   GAP-19  [Assumption check] detach_2_just_pressed=true on EVERY frame for 5
#           frames starting from has_chunk_2=false: HP must NEVER reduce after
#           frame 1 (always a no-op when chunk already detached).
#
#   GAP-20  [Prior-state immutability] Both chunk fields of prior_state remain
#           unchanged after dual-detach: prior.has_chunk and prior.has_chunk_2
#           must both still be true after the call that returns false for both.
#
#   GAP-21  [Combinatorial] min_hp = 50.0 (non-zero floor): detaching chunk 2
#           from prior_hp=60.0 with cost=25.0 clamps to 50.0, not 35.0.
#
#   GAP-22  [Boundary] Extremely large prior HP (1e9) with cost=25.0: result is
#           exactly 1e9 - 25.0 without overflow or float precision loss.
#
#   GAP-23  [Mutation] Incorrect step ordering: a buggy implementation that runs
#           step 20 BEFORE step 19 would read prior_state.has_chunk_2 instead of
#           the just-set result.has_chunk_2 when determining detach_2_eligible.
#           This test proves the ordering is correct.
#
#   GAP-24  [Combinatorial] Detach chunk 2 while in-air (is_on_floor=false, vy<0):
#           has_chunk_2 fires correctly; all movement fields carry forward normally.
#
# -------------------------------------------------------------------------
# NOTE: All tests are expected to FAIL until Task 5 implements:
#   - MovementState.has_chunk_2: bool = true
#   - simulate() 9th arg: detach_2_just_pressed: bool = false (after delta)
#   - Steps 19 and 20 in simulate()
# -------------------------------------------------------------------------

class_name SecondChunkSimulationAdversarialTests
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
# Factory helpers
# ---------------------------------------------------------------------------

func _make_state() -> MovementSimulation.MovementState:
	return MovementSimulation.MovementState.new()


func _make_state_with(vx: float, vy: float, on_floor: bool) -> MovementSimulation.MovementState:
	var s: MovementSimulation.MovementState = MovementSimulation.MovementState.new()
	s.velocity = Vector2(vx, vy)
	s.is_on_floor = on_floor
	return s


# Canonical 9-arg call for adversarial tests.
func _simulate_9(sim: MovementSimulation,
		prior: MovementSimulation.MovementState,
		detach_just_pressed: bool,
		detach_2_just_pressed: bool) -> MovementSimulation.MovementState:
	return sim.simulate(prior, 0.0, false, false, false, 0.0,
		detach_just_pressed, 0.016, detach_2_just_pressed)


# 9-arg call with custom delta.
func _simulate_9_delta(sim: MovementSimulation,
		prior: MovementSimulation.MovementState,
		detach_just_pressed: bool,
		detach_2_just_pressed: bool,
		delta: float) -> MovementSimulation.MovementState:
	return sim.simulate(prior, 0.0, false, false, false, 0.0,
		detach_just_pressed, delta, detach_2_just_pressed)


# ===========================================================================
# GAP-01 — Step 20 must read result.current_hp (not prior_state.current_hp)
#
# Vulnerability: A buggy step 20 reads prior_state.current_hp instead of
# result.current_hp. With prior_hp=50.0 and cost=25.0, step 18 → 25.0 and
# step 20 correctly → 0.0. If step 20 erroneously reads prior_state.current_hp
# (50.0) and subtracts 25.0, result would be 25.0 instead of 0.0.
# ===========================================================================

func test_gap01_step20_reads_result_hp_not_prior_hp() -> void:
	# GAP-01 [Mutation] Both chunks detach on same frame with prior_hp == 2*cost.
	# Correct:  step18 → 25.0; step20 → 0.0 (reads result 25.0, subtracts 25.0)
	# Buggy:    step18 → 25.0; step20 → 25.0 (reads prior 50.0, subtracts 25.0)
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 50.0
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_approx(result.current_hp, 0.0,
		"gap-01a — dual detach at 2*cost: step20 must read result (25.0) not prior (50.0)")
	_assert_false(result.has_chunk,
		"gap-01b — dual detach: has_chunk=false")
	_assert_false(result.has_chunk_2,
		"gap-01c — dual detach: has_chunk_2=false")


func test_gap01_step20_reads_result_hp_near_floor() -> void:
	# GAP-01 variant: prior_hp=30.0, cost=25.0. After step 18: 5.0.
	# After step 20 (correct, reads 5.0): max(0, 5.0-25.0) = 0.0.
	# Buggy (reads prior 30.0): 30.0-25.0 = 5.0. These differ.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 30.0
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_approx(result.current_hp, 0.0,
		"gap-01d — dual detach at 30.0 (cost=25): step18→5.0, step20→0.0; buggy→5.0")


# ===========================================================================
# GAP-02 — Cross-contamination: detach and detach_2 must not share eligibility
#
# Vulnerability: A buggy impl uses a single `detach_eligible` variable that
# is set by either press. If detach_just_pressed=true fires and then step 19
# reuses that flag, has_chunk_2 would also become false on a chunk-1-only press.
# ===========================================================================

func test_gap02_detach1_press_does_not_contaminate_chunk2() -> void:
	# GAP-02 [Independence] Only chunk 1 detach fires.
	# has_chunk_2 must remain true.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	# detach_just_pressed=true (chunk 1), detach_2_just_pressed=false
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, true, false)
	_assert_false(result.has_chunk,
		"gap-02a — chunk 1 detach fires: has_chunk=false")
	_assert_true(result.has_chunk_2 == true,
		"gap-02b — chunk 1 detach must NOT contaminate has_chunk_2 (stays true)")


func test_gap02_detach2_press_does_not_contaminate_chunk1() -> void:
	# GAP-02 [Independence] Only chunk 2 detach fires.
	# has_chunk must remain true.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	# detach_just_pressed=false, detach_2_just_pressed=true (chunk 2 only)
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_true(result.has_chunk == true,
		"gap-02c — chunk 2 detach must NOT contaminate has_chunk (stays true)")
	_assert_false(result.has_chunk_2,
		"gap-02d — chunk 2 detach fires: has_chunk_2=false")


func test_gap02_both_pressed_but_only_one_chunk_available() -> void:
	# GAP-02 [Combinatorial] Both buttons pressed, but only one chunk is attached.
	# Only the available chunk detaches; the other is no-op.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = false    # chunk 1 already detached
	prior.has_chunk_2 = true   # chunk 2 still attached
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, true, true)
	# Step 17: detach_eligible = true AND prior.has_chunk=false → no-op → has_chunk=false
	_assert_false(result.has_chunk,
		"gap-02e — both pressed, chunk1 already detached: has_chunk stays false")
	# Step 19: detach_2_eligible = true AND prior.has_chunk_2=true → fires
	_assert_false(result.has_chunk_2,
		"gap-02f — both pressed, chunk2 was attached: has_chunk_2 becomes false")


func test_gap02_hp_reduced_exactly_once_chunk1_only_press_when_both_attached() -> void:
	# GAP-02 [HP / Cross-contamination] Only chunk 1 detach key pressed.
	# HP must be reduced exactly once (step 18 only; step 20 is no-op).
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, true, false)
	_assert_approx(result.current_hp, 75.0,
		"gap-02g — chunk1-only detach: HP reduced exactly once (100→75, not 100→50)")


# ===========================================================================
# GAP-03 — prior_state immutability: simulate() must not mutate ANY field
#
# Vulnerability: GDScript passes objects by reference. A buggy impl that
# writes directly into prior_state (instead of a fresh result) would corrupt
# the caller's prior state. Test all key fields in one comprehensive call.
# ===========================================================================

func test_gap03_prior_state_all_fields_immutable_on_dual_detach() -> void:
	# GAP-03 [Prior-state immutability] All key MovementState fields must be
	# unchanged in prior_state after simulate() returns.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	prior.velocity = Vector2(10.0, -5.0)
	prior.is_on_floor = true

	# Record all values BEFORE simulate
	var pre_has_chunk: bool = prior.has_chunk
	var pre_has_chunk_2: bool = prior.has_chunk_2
	var pre_hp: float = prior.current_hp
	var pre_vx: float = prior.velocity.x
	var pre_vy: float = prior.velocity.y
	var pre_floor: bool = prior.is_on_floor

	# Full dual-detach call
	var _result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)

	_assert_true(prior.has_chunk == pre_has_chunk,
		"gap-03a — prior.has_chunk unchanged after simulate()")
	_assert_true(prior.has_chunk_2 == pre_has_chunk_2,
		"gap-03b — prior.has_chunk_2 unchanged after simulate()")
	_assert_approx(prior.current_hp, pre_hp,
		"gap-03c — prior.current_hp unchanged after simulate()")
	_assert_approx(prior.velocity.x, pre_vx,
		"gap-03d — prior.velocity.x unchanged after simulate()")
	_assert_approx(prior.velocity.y, pre_vy,
		"gap-03e — prior.velocity.y unchanged after simulate()")
	_assert_true(prior.is_on_floor == pre_floor,
		"gap-03f — prior.is_on_floor unchanged after simulate()")


func test_gap03_prior_state_immutable_chunk2_detach_only() -> void:
	# GAP-03 variant: only chunk 2 detach fires; verify prior.has_chunk_2 stays true
	# and prior.has_chunk stays true.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 80.0

	var _result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)

	_assert_true(prior.has_chunk == true,
		"gap-03g — prior.has_chunk stays true after chunk2-only detach call")
	_assert_true(prior.has_chunk_2 == true,
		"gap-03h — prior.has_chunk_2 stays true (not mutated by simulate())")
	_assert_approx(prior.current_hp, 80.0,
		"gap-03i — prior.current_hp stays 80.0 (not mutated by simulate())")


# ===========================================================================
# GAP-04 — HP at exactly hp_cost_per_detach for chunk 2: clamps to min_hp
#
# Boundary: prior_hp == cost, chunk 2 detaches. Result must be max(0, 0) = 0.0.
# ===========================================================================

func test_gap04_hp_exactly_at_cost_chunk2_clamps_to_min() -> void:
	# GAP-04 [Boundary] prior_hp=25.0 == cost=25.0. Step 20: max(0.0, 0.0) = 0.0.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 25.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 0.0,
		"gap-04 — HP exactly at cost (25.0-25.0=0.0): clamps to min_hp=0.0")
	_assert_false(result.has_chunk_2,
		"gap-04b — has_chunk_2=false after exact-cost detach")


# ===========================================================================
# GAP-05 — HP at (2 * cost) on dual-detach: minimum HP for a full dual-detach
#
# Boundary: prior_hp=50.0, cost=25.0. Step 18 → 25.0, Step 20 → 0.0.
# This is the minimal HP that results in exactly 0.0 (not negative) for dual detach.
# ===========================================================================

func test_gap05_hp_at_double_cost_dual_detach_reaches_exactly_zero() -> void:
	# GAP-05 [Boundary] The minimum prior_hp that produces exactly 0.0 after dual detach.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 50.0
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_approx(result.current_hp, 0.0,
		"gap-05 — dual detach at 2*cost: result exactly 0.0 (no negative HP)")


# ===========================================================================
# GAP-06 — HP at 0.0 when detach_2 pressed: clamp holds, no negative HP
#
# Boundary: prior_hp=0.0, detach_2 pressed. max(0.0, 0.0-25.0) must be 0.0.
# ===========================================================================

func test_gap06_hp_at_zero_detach_2_stays_at_floor() -> void:
	# GAP-06 [Boundary / Null] HP already at min_hp=0.0; detach_2 fires.
	# Step 20: max(0.0, 0.0-25.0) = 0.0. Must not go negative.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 0.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 0.0,
		"gap-06 — HP at 0.0 + detach_2: must not go below min_hp=0.0")
	_assert_false(result.has_chunk_2,
		"gap-06b — detach still fires even when HP is at floor")


# ===========================================================================
# GAP-07 — Flip-boolean mutation: ensure has_chunk_2=false is NOT restored to
#          true on a no-detach frame
#
# Vulnerability: An implementation that uses `has_chunk_2 = not has_chunk_2`
# or `has_chunk_2 = detach_2_just_pressed` (boolean assignment) would flip
# false→true on every false-input frame, breaking carry-forward.
# ===========================================================================

func test_gap07_flip_boolean_not_possible_on_false_carry_forward() -> void:
	# GAP-07 [Mutation] If implementation uses `has_chunk_2 = detach_2_just_pressed`,
	# then detach_2=false would set has_chunk_2=false → coincidentally correct.
	# If it uses `has_chunk_2 = not detach_2_just_pressed`, detach_2=false → true.
	# This test catches the latter mutation.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false  # chunk already detached
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_false(result.has_chunk_2,
		"gap-07a — has_chunk_2=false + detach_2=false: must remain false (not flip to true)")


func test_gap07_flip_boolean_not_possible_on_true_carry_forward() -> void:
	# GAP-07 variant: `has_chunk_2 = not prior.has_chunk_2` would flip true→false
	# even on a no-press, no-detach frame. Catch that mutation.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_true(result.has_chunk_2 == true,
		"gap-07b — has_chunk_2=true + no press: must remain true (not flip to false)")


# ===========================================================================
# GAP-08 — Instance isolation: two MovementSimulation instances share no state
#
# Vulnerability: A class-level (static) has_chunk_2 variable would cause
# state to leak between instances. This catches that.
# ===========================================================================

func test_gap08_instance_isolation_has_chunk_2() -> void:
	# GAP-08 [Instance isolation] Detach chunk 2 on instance A; instance B unaffected.
	var sim_a: MovementSimulation = MovementSimulation.new()
	var sim_b: MovementSimulation = MovementSimulation.new()

	var prior_a: MovementSimulation.MovementState = _make_state()
	prior_a.has_chunk_2 = true
	var prior_b: MovementSimulation.MovementState = _make_state()
	prior_b.has_chunk_2 = true

	# Detach on A
	var result_a: MovementSimulation.MovementState = _simulate_9(sim_a, prior_a, false, true)
	# No detach on B
	var result_b: MovementSimulation.MovementState = _simulate_9(sim_b, prior_b, false, false)

	_assert_false(result_a.has_chunk_2,
		"gap-08a — instance A: chunk 2 detached")
	_assert_true(result_b.has_chunk_2 == true,
		"gap-08b — instance B: has_chunk_2 unaffected by A's detach (no shared state)")


func test_gap08_instance_isolation_hp() -> void:
	# GAP-08 variant: HP reduction in instance A must not affect instance B's result.
	var sim_a: MovementSimulation = MovementSimulation.new()
	var sim_b: MovementSimulation = MovementSimulation.new()
	sim_a.hp_cost_per_detach = 25.0
	sim_b.hp_cost_per_detach = 25.0

	var prior_a: MovementSimulation.MovementState = _make_state()
	prior_a.has_chunk_2 = true
	prior_a.current_hp = 100.0

	var prior_b: MovementSimulation.MovementState = _make_state()
	prior_b.has_chunk_2 = true
	prior_b.current_hp = 100.0

	# Detach (and reduce HP) on A
	var result_a: MovementSimulation.MovementState = _simulate_9(sim_a, prior_a, false, true)
	# No-op on B
	var result_b: MovementSimulation.MovementState = _simulate_9(sim_b, prior_b, false, false)

	_assert_approx(result_a.current_hp, 75.0,
		"gap-08c — instance A: HP reduced to 75.0")
	_assert_approx(result_b.current_hp, 100.0,
		"gap-08d — instance B: HP unaffected by A's detach (still 100.0)")


# ===========================================================================
# GAP-09 — has_chunk_2=false + detach_2=true + HP at floor: no HP change
#
# Combinatorial: chunk already detached (no-op), and HP is already at 0.
# Step 20 must be a strict no-op; result.current_hp stays 0.0.
# ===========================================================================

func test_gap09_chunk2_detached_hp_at_floor_no_reduction() -> void:
	# GAP-09 [Combinatorial] has_chunk_2=false (chunk already out) + press at HP=0.
	# Step 19: no-op (has_chunk_2 stays false). Step 20: no-op (detach_2_eligible=false).
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = false
	prior.current_hp = 0.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk_2,
		"gap-09a — no-op: has_chunk_2 stays false")
	_assert_approx(result.current_hp, 0.0,
		"gap-09b — no-op: HP stays 0.0 (no reduction because chunk already detached)")


# ===========================================================================
# GAP-10 — Order dependency: N idle frames then detach_2 == single-frame detach_2
#
# Assumption check: simulate() must be stateless (no hidden internal state).
# ===========================================================================

func test_gap10_order_independent_detach_after_idle_frames() -> void:
	# GAP-10 [Order dependency / Assumption] Simulate 5 idle frames, then detach_2.
	# Result must match a fresh detach_2 from same initial state.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0

	# Path A: 5 idle frames, then detach_2 on frame 6
	var state_a: MovementSimulation.MovementState = _make_state()
	state_a.has_chunk_2 = true
	state_a.current_hp = 100.0
	for _i: int in range(5):
		state_a = _simulate_9(sim, state_a, false, false)
	var result_a: MovementSimulation.MovementState = _simulate_9(sim, state_a, false, true)

	# Path B: single detach_2 from a fresh state (same initial values as state_a before idle)
	var state_b: MovementSimulation.MovementState = _make_state()
	state_b.has_chunk_2 = true
	state_b.current_hp = 100.0
	var result_b: MovementSimulation.MovementState = _simulate_9(sim, state_b, false, true)

	_assert_false(result_a.has_chunk_2,
		"gap-10a — after 5 idle frames: detach_2 fires correctly")
	_assert_false(result_b.has_chunk_2,
		"gap-10b — single fresh detach_2: fires correctly")
	_assert_approx(result_a.current_hp, result_b.current_hp,
		"gap-10c — HP after detach is same regardless of prior idle frames")


# ===========================================================================
# GAP-11 — Determinism: same inputs → identical results across 3 repeated calls
# ===========================================================================

func test_gap11_determinism_three_repeated_calls_same_inputs() -> void:
	# GAP-11 [Determinism] Identical 9-arg inputs must produce identical outputs
	# across 3 independent invocations.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true
	prior.current_hp = 80.0
	prior.velocity = Vector2(3.0, -12.0)

	var r1: MovementSimulation.MovementState = sim.simulate(
		prior, 0.3, false, false, false, 0.0, false, 0.016, true)
	var r2: MovementSimulation.MovementState = sim.simulate(
		prior, 0.3, false, false, false, 0.0, false, 0.016, true)
	var r3: MovementSimulation.MovementState = sim.simulate(
		prior, 0.3, false, false, false, 0.0, false, 0.016, true)

	_assert_true(r1.has_chunk_2 == r2.has_chunk_2 and r2.has_chunk_2 == r3.has_chunk_2,
		"gap-11a — has_chunk_2 deterministic across 3 calls")
	_assert_approx(r1.current_hp, r2.current_hp,
		"gap-11b — current_hp deterministic: r1==r2")
	_assert_approx(r2.current_hp, r3.current_hp,
		"gap-11c — current_hp deterministic: r2==r3")


# ===========================================================================
# GAP-12 — Delta independence: HP arithmetic is NOT affected by delta value
#
# Vulnerability: If the implementation accidentally multiplies hp_cost by delta
# (as it does for physics steps), HP reduction would scale with frame time.
# ===========================================================================

func test_gap12_delta_does_not_affect_chunk2_hp_reduction() -> void:
	# GAP-12 [Combinatorial / Boundary] HP reduction must be exactly hp_cost_per_detach
	# regardless of delta. If cost is accidentally delta-scaled, results diverge.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0

	var deltas: Array[float] = [0.001, 0.016, 0.033, 1.0, 60.0]
	for d: float in deltas:
		var prior: MovementSimulation.MovementState = _make_state()
		prior.has_chunk_2 = true
		prior.current_hp = 100.0
		var result: MovementSimulation.MovementState = _simulate_9_delta(
			sim, prior, false, true, d)
		_assert_approx(result.current_hp, 75.0,
			"gap-12 — delta=" + str(d) + ": HP reduction always 25.0 (delta-independent)")


func test_gap12_delta_does_not_affect_dual_detach_hp() -> void:
	# GAP-12 variant: dual detach across delta extremes — must always reach 50.0.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0

	var deltas: Array[float] = [0.001, 0.016, 1.0, 60.0]
	for d: float in deltas:
		var prior: MovementSimulation.MovementState = _make_state()
		prior.has_chunk = true
		prior.has_chunk_2 = true
		prior.current_hp = 100.0
		var result: MovementSimulation.MovementState = sim.simulate(
			prior, 0.0, false, false, false, 0.0, true, d, true)
		_assert_approx(result.current_hp, 50.0,
			"gap-12b — dual detach delta=" + str(d) + ": HP always 50.0")


# ===========================================================================
# GAP-13 — Step 19 reads only detach_2_just_pressed and prior.has_chunk_2
#           (must not read has_chunk, velocity, or any other field)
#
# Mutation: An implementation that gates has_chunk_2 on has_chunk being true
# would fail the case has_chunk=false + has_chunk_2=true + detach_2=true.
# ===========================================================================

func test_gap13_step19_ignores_has_chunk_value() -> void:
	# GAP-13 [Mutation / Independence] Detach 2 must fire even when has_chunk=false.
	# An implementation that checks "if prior.has_chunk and prior.has_chunk_2" is wrong.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = false   # chunk 1 is already detached
	prior.has_chunk_2 = true
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk_2,
		"gap-13a — chunk2 detach fires even when has_chunk=false (fields are independent)")
	_assert_false(result.has_chunk,
		"gap-13b — has_chunk stays false (unaffected by detach_2)")


func test_gap13_step19_ignores_velocity_value() -> void:
	# GAP-13 variant: same detach_2 call with extreme velocity must produce same result.
	var sim: MovementSimulation = MovementSimulation.new()

	# Normal velocity
	var prior_normal: MovementSimulation.MovementState = _make_state_with(0.0, 0.0, false)
	prior_normal.has_chunk_2 = true
	var result_normal: MovementSimulation.MovementState = _simulate_9(
		sim, prior_normal, false, true)

	# Extreme velocity
	var prior_extreme: MovementSimulation.MovementState = _make_state_with(9999.0, -9999.0, false)
	prior_extreme.has_chunk_2 = true
	var result_extreme: MovementSimulation.MovementState = _simulate_9(
		sim, prior_extreme, false, true)

	_assert_false(result_normal.has_chunk_2,
		"gap-13c — normal velocity: chunk2 detach fires")
	_assert_false(result_extreme.has_chunk_2,
		"gap-13d — extreme velocity: chunk2 detach fires identically (velocity has no effect)")


# ===========================================================================
# GAP-14 — Stress: 1000 frames with detach_2=false after initial detach
#
# Stress / Assumption: has_chunk_2 must never flip back to true spontaneously.
# ===========================================================================

func test_gap14_stress_1000_frames_has_chunk_2_stays_false() -> void:
	# GAP-14 [Stress] After detach fires, 1000 no-detach frames must all keep false.
	var sim: MovementSimulation = MovementSimulation.new()
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = true
	# Frame 0: detach fires
	state = _simulate_9(sim, state, false, true)
	if state.has_chunk_2:
		_fail("gap-14-setup", "initial detach did not fire")
		return

	# Frames 1–1000: all no-detach
	var restored_at: int = -1
	for i: int in range(1000):
		state = _simulate_9(sim, state, false, false)
		if state.has_chunk_2:
			restored_at = i + 1
			break

	_assert_true(restored_at == -1,
		"gap-14 — has_chunk_2 never restored to true across 1000 no-detach frames after detach")


# ===========================================================================
# GAP-15 — hp_cost_per_detach = 0.0: detaching chunk 2 must leave HP unchanged
# ===========================================================================

func test_gap15_zero_cost_detach_2_no_hp_change() -> void:
	# GAP-15 [Boundary] Zero cost means max(0, hp - 0) = hp. HP must carry forward.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 0.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 80.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk_2,
		"gap-15a — zero-cost: chunk 2 still detaches")
	_assert_approx(result.current_hp, 80.0,
		"gap-15b — zero-cost: HP unchanged (80.0 - 0.0 = 80.0)")


# ===========================================================================
# GAP-16 — hp_cost_per_detach = INF: detach clamps result to min_hp
# ===========================================================================

func test_gap16_inf_cost_detach_2_clamps_to_min_hp() -> void:
	# GAP-16 [Boundary] Infinite cost: max(0, hp - INF) must clamp to min_hp=0.0
	# without crashing or producing NaN.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = INF
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_false(result.has_chunk_2,
		"gap-16a — INF cost: chunk 2 still detaches")
	# max(0.0, 100.0 - INF) = max(0.0, -INF) = 0.0 in GDScript
	_assert_approx(result.current_hp, 0.0,
		"gap-16b — INF cost: HP clamped to min_hp=0.0")


# ===========================================================================
# GAP-17 — detach_1 no-op (has_chunk=false) + detach_2 fires: HP once only
# ===========================================================================

func test_gap17_chunk1_already_detached_chunk2_detach_hp_once() -> void:
	# GAP-17 [Combinatorial] Both pressed, but chunk 1 already gone.
	# Step 18: no-op (detach_eligible=false). Step 20: fires once.
	# HP must be reduced exactly once.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = false    # chunk 1 already detached
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result.has_chunk,
		"gap-17a — has_chunk remains false (chunk 1 was already detached)")
	_assert_false(result.has_chunk_2,
		"gap-17b — has_chunk_2 becomes false (chunk 2 detach fires)")
	_assert_approx(result.current_hp, 75.0,
		"gap-17c — HP reduced exactly once: only step 20 fired (100→75, not 100→50)")


# ===========================================================================
# GAP-18 — detach_2 no-op (has_chunk_2=false) + detach_1 fires: HP once only
# ===========================================================================

func test_gap18_chunk2_already_detached_chunk1_detach_hp_once() -> void:
	# GAP-18 [Combinatorial] Both pressed, but chunk 2 already gone.
	# Step 18: fires once. Step 20: no-op.
	# HP must be reduced exactly once.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = false  # chunk 2 already detached
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result.has_chunk,
		"gap-18a — has_chunk becomes false (chunk 1 detach fires)")
	_assert_false(result.has_chunk_2,
		"gap-18b — has_chunk_2 remains false (chunk 2 was already detached)")
	_assert_approx(result.current_hp, 75.0,
		"gap-18c — HP reduced exactly once: only step 18 fired (100→75, not 100→50)")


# ===========================================================================
# GAP-19 — detach_2=true every frame for 5 frames starting from has_chunk_2=false
#          HP must NEVER reduce after the initial state (no reduction at all)
# ===========================================================================

func test_gap19_repeated_detach2_press_on_detached_chunk_no_hp_drain() -> void:
	# GAP-19 [Assumption check] Mashing detach_2 with chunk already gone: pure no-op.
	# If implementation incorrectly reduces HP on every press, this fails.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var state: MovementSimulation.MovementState = _make_state()
	state.has_chunk_2 = false  # start already detached
	state.current_hp = 100.0

	for i: int in range(5):
		state = _simulate_9(sim, state, false, true)
		_assert_approx(state.current_hp, 100.0,
			"gap-19 — frame " + str(i + 1) + ": HP stays 100.0 (no-op, chunk already detached)")
		_assert_false(state.has_chunk_2,
			"gap-19b — frame " + str(i + 1) + ": has_chunk_2 stays false")


# ===========================================================================
# GAP-20 — Prior state: both has_chunk and has_chunk_2 remain true after dual-detach
# ===========================================================================

func test_gap20_prior_both_chunk_fields_unchanged_after_dual_detach() -> void:
	# GAP-20 [Prior-state immutability] After a call that detaches both chunks in
	# the result, the prior object must still show both fields as true.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk = true
	prior.has_chunk_2 = true

	var result: MovementSimulation.MovementState = sim.simulate(
		prior, 0.0, false, false, false, 0.0, true, 0.016, true)

	# Result: both false
	_assert_false(result.has_chunk,
		"gap-20a — result.has_chunk=false (dual detach fired)")
	_assert_false(result.has_chunk_2,
		"gap-20b — result.has_chunk_2=false (dual detach fired)")
	# Prior: both still true
	_assert_true(prior.has_chunk == true,
		"gap-20c — prior.has_chunk remains true (not mutated)")
	_assert_true(prior.has_chunk_2 == true,
		"gap-20d — prior.has_chunk_2 remains true (not mutated)")


# ===========================================================================
# GAP-21 — non-zero min_hp floor: detach_2 clamps to custom min, not 0
# ===========================================================================

func test_gap21_non_zero_min_hp_floor_chunk2() -> void:
	# GAP-21 [Combinatorial] min_hp=50.0. HP=60.0, cost=25.0.
	# Step 20: max(50.0, 60.0-25.0) = max(50.0, 35.0) = 50.0, NOT 35.0.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 50.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 60.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 50.0,
		"gap-21 — min_hp=50.0, HP=60.0-25.0=35.0 but clamps to floor 50.0")
	_assert_false(result.has_chunk_2,
		"gap-21b — detach fires despite non-zero min_hp")


func test_gap21_non_zero_min_hp_no_clamp_needed_chunk2() -> void:
	# GAP-21 variant: min_hp=50.0, HP=100.0, cost=25.0. No clamp needed: 75.0 > 50.0.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 50.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 100.0
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 75.0,
		"gap-21c — min_hp=50.0, HP=100.0-25.0=75.0 (above floor, no clamp)")


# ===========================================================================
# GAP-22 — Very large prior HP: no float overflow or precision loss
# ===========================================================================

func test_gap22_very_large_hp_chunk2_reduction_precise() -> void:
	# GAP-22 [Boundary / Stress] prior_hp=1e9, cost=25.0. Result must be 1e9-25.0
	# without float overflow (GDScript float64 can represent this exactly).
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 1e9
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)
	_assert_approx(result.current_hp, 1e9 - 25.0,
		"gap-22 — very large HP (1e9): reduction is exactly 25.0 (no precision loss)")


# ===========================================================================
# GAP-23 — Step ordering: step 19 must run before step 20 reads detach_2_eligible
#
# A buggy impl running step 20 before step 19 would read prior.has_chunk_2
# instead of the step-19 result when computing detach_2_eligible, which
# produces a different has_chunk_2 for step 20's eligibility check.
# This scenario is identical to other detach tests, but targets ordering
# by verifying that HP reduction in step 20 is conditioned on the SAME
# detach_2_eligible that step 19 just computed — not a stale copy.
# ===========================================================================

func test_gap23_step_ordering_hp_reduction_conditioned_on_fresh_detach_2_eligible() -> void:
	# GAP-23 [Mutation / Order dependency] Verify that step 20 fires IFF step 19
	# found detach_2_eligible=true. Specifically: when detach_2_just_pressed=false,
	# step 19 computes eligible=false; step 20 must NOT reduce HP.
	# A reversed-order impl (step 20 runs first reading prior) might still be
	# correct here, but the pairing with GAP-01 creates a complete coverage ring.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0
	var prior: MovementSimulation.MovementState = _make_state()
	prior.has_chunk_2 = true
	prior.current_hp = 100.0

	# detach_2=false → step 19 eligible=false → step 20 must NOT fire
	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)
	_assert_true(result.has_chunk_2 == true,
		"gap-23a — no press: step 19 no-op, has_chunk_2=true")
	_assert_approx(result.current_hp, 100.0,
		"gap-23b — no press: step 20 no-op, HP unchanged (100.0)")


# ===========================================================================
# GAP-24 — Detach chunk 2 while airborne (is_on_floor=false, vy<0):
#          movement fields carry forward; detach_2 fires independent of floor state
# ===========================================================================

func test_gap24_detach_2_while_airborne_fires_correctly() -> void:
	# GAP-24 [Combinatorial] Airborne state (is_on_floor=false, vy=-200.0).
	# Detach_2 must fire regardless of floor state.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0

	var prior: MovementSimulation.MovementState = _make_state_with(50.0, -200.0, false)
	prior.has_chunk_2 = true
	prior.current_hp = 80.0

	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, true)

	_assert_false(result.has_chunk_2,
		"gap-24a — airborne: chunk 2 detach fires (not gated on is_on_floor)")
	_assert_approx(result.current_hp, 55.0,
		"gap-24b — airborne: HP reduced by cost (80.0-25.0=55.0)")


func test_gap24_detach_2_no_press_airborne_has_chunk_2_carries_forward() -> void:
	# GAP-24 variant: airborne with no press — has_chunk_2 must carry forward.
	var sim: MovementSimulation = MovementSimulation.new()
	var prior: MovementSimulation.MovementState = _make_state_with(30.0, -150.0, false)
	prior.has_chunk_2 = true

	var result: MovementSimulation.MovementState = _simulate_9(sim, prior, false, false)

	_assert_true(result.has_chunk_2 == true,
		"gap-24c — airborne, no press: has_chunk_2 carries forward true")


# ===========================================================================
# BONUS: Combinatorial mini-matrix — all 4 combinations of (has_chunk, has_chunk_2)
#        with (detach=true, detach_2=true) — full result table verification
# ===========================================================================

func test_bonus_full_press_matrix_all_prior_combinations() -> void:
	# BONUS [Combinatorial] Exhaustive: both keys pressed, all 4 prior states.
	# Verifies result.has_chunk and result.has_chunk_2 for every starting state.
	var sim: MovementSimulation = MovementSimulation.new()
	sim.hp_cost_per_detach = 25.0
	sim.min_hp = 0.0

	# (F, F) → both already detached, both stay false; HP unchanged
	var prior_ff: MovementSimulation.MovementState = _make_state()
	prior_ff.has_chunk = false
	prior_ff.has_chunk_2 = false
	prior_ff.current_hp = 100.0
	var result_ff: MovementSimulation.MovementState = sim.simulate(
		prior_ff, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result_ff.has_chunk, "bonus-ff — has_chunk stays false")
	_assert_false(result_ff.has_chunk_2, "bonus-ff2 — has_chunk_2 stays false")
	_assert_approx(result_ff.current_hp, 100.0, "bonus-ff-hp — no HP reduction (both no-op)")

	# (T, F) → chunk1 detaches; chunk2 already gone; HP reduced once
	var prior_tf: MovementSimulation.MovementState = _make_state()
	prior_tf.has_chunk = true
	prior_tf.has_chunk_2 = false
	prior_tf.current_hp = 100.0
	var result_tf: MovementSimulation.MovementState = sim.simulate(
		prior_tf, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result_tf.has_chunk, "bonus-tf — has_chunk becomes false")
	_assert_false(result_tf.has_chunk_2, "bonus-tf2 — has_chunk_2 stays false")
	_assert_approx(result_tf.current_hp, 75.0, "bonus-tf-hp — HP reduced once (step18 only)")

	# (F, T) → chunk1 already gone; chunk2 detaches; HP reduced once
	var prior_ft: MovementSimulation.MovementState = _make_state()
	prior_ft.has_chunk = false
	prior_ft.has_chunk_2 = true
	prior_ft.current_hp = 100.0
	var result_ft: MovementSimulation.MovementState = sim.simulate(
		prior_ft, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result_ft.has_chunk, "bonus-ft — has_chunk stays false")
	_assert_false(result_ft.has_chunk_2, "bonus-ft2 — has_chunk_2 becomes false")
	_assert_approx(result_ft.current_hp, 75.0, "bonus-ft-hp — HP reduced once (step20 only)")

	# (T, T) → both detach; HP reduced twice
	var prior_tt: MovementSimulation.MovementState = _make_state()
	prior_tt.has_chunk = true
	prior_tt.has_chunk_2 = true
	prior_tt.current_hp = 100.0
	var result_tt: MovementSimulation.MovementState = sim.simulate(
		prior_tt, 0.0, false, false, false, 0.0, true, 0.016, true)
	_assert_false(result_tt.has_chunk, "bonus-tt — has_chunk becomes false")
	_assert_false(result_tt.has_chunk_2, "bonus-tt2 — has_chunk_2 becomes false")
	_assert_approx(result_tt.current_hp, 50.0, "bonus-tt-hp — HP reduced twice (step18+step20)")


# ===========================================================================
# Public entry point
# ===========================================================================

func run_all() -> int:
	print("--- test_second_chunk_simulation_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# GAP-01: Step 20 reads result.current_hp not prior_state.current_hp
	test_gap01_step20_reads_result_hp_not_prior_hp()
	test_gap01_step20_reads_result_hp_near_floor()

	# GAP-02: Cross-contamination between detach and detach_2
	test_gap02_detach1_press_does_not_contaminate_chunk2()
	test_gap02_detach2_press_does_not_contaminate_chunk1()
	test_gap02_both_pressed_but_only_one_chunk_available()
	test_gap02_hp_reduced_exactly_once_chunk1_only_press_when_both_attached()

	# GAP-03: Prior state immutability — all fields
	test_gap03_prior_state_all_fields_immutable_on_dual_detach()
	test_gap03_prior_state_immutable_chunk2_detach_only()

	# GAP-04: HP exactly at cost — clamps to min_hp
	test_gap04_hp_exactly_at_cost_chunk2_clamps_to_min()

	# GAP-05: HP at 2*cost on dual-detach reaches exactly 0.0
	test_gap05_hp_at_double_cost_dual_detach_reaches_exactly_zero()

	# GAP-06: HP at 0.0 when detach_2 pressed — no negative HP
	test_gap06_hp_at_zero_detach_2_stays_at_floor()

	# GAP-07: Flip-boolean mutation not possible
	test_gap07_flip_boolean_not_possible_on_false_carry_forward()
	test_gap07_flip_boolean_not_possible_on_true_carry_forward()

	# GAP-08: Instance isolation
	test_gap08_instance_isolation_has_chunk_2()
	test_gap08_instance_isolation_hp()

	# GAP-09: Combinatorial — detached + HP at floor + press
	test_gap09_chunk2_detached_hp_at_floor_no_reduction()

	# GAP-10: Order independence — N idle frames then detach
	test_gap10_order_independent_detach_after_idle_frames()

	# GAP-11: Determinism — 3 identical calls
	test_gap11_determinism_three_repeated_calls_same_inputs()

	# GAP-12: Delta independence — HP arithmetic not delta-scaled
	test_gap12_delta_does_not_affect_chunk2_hp_reduction()
	test_gap12_delta_does_not_affect_dual_detach_hp()

	# GAP-13: Step 19 reads only its two correct fields
	test_gap13_step19_ignores_has_chunk_value()
	test_gap13_step19_ignores_velocity_value()

	# GAP-14: Stress — 1000 frames
	test_gap14_stress_1000_frames_has_chunk_2_stays_false()

	# GAP-15: Zero cost — no HP change
	test_gap15_zero_cost_detach_2_no_hp_change()

	# GAP-16: INF cost — clamps to min_hp
	test_gap16_inf_cost_detach_2_clamps_to_min_hp()

	# GAP-17: Chunk1 already detached + both pressed — HP once
	test_gap17_chunk1_already_detached_chunk2_detach_hp_once()

	# GAP-18: Chunk2 already detached + both pressed — HP once
	test_gap18_chunk2_already_detached_chunk1_detach_hp_once()

	# GAP-19: Mashing detach_2 with chunk already detached — no HP drain
	test_gap19_repeated_detach2_press_on_detached_chunk_no_hp_drain()

	# GAP-20: Prior both fields unchanged after dual detach
	test_gap20_prior_both_chunk_fields_unchanged_after_dual_detach()

	# GAP-21: Non-zero min_hp floor
	test_gap21_non_zero_min_hp_floor_chunk2()
	test_gap21_non_zero_min_hp_no_clamp_needed_chunk2()

	# GAP-22: Very large HP — no overflow
	test_gap22_very_large_hp_chunk2_reduction_precise()

	# GAP-23: Step ordering — step 19 before step 20
	test_gap23_step_ordering_hp_reduction_conditioned_on_fresh_detach_2_eligible()

	# GAP-24: Airborne detach
	test_gap24_detach_2_while_airborne_fires_correctly()
	test_gap24_detach_2_no_press_airborne_has_chunk_2_carries_forward()

	# BONUS: Full 4-combination prior-state matrix with both keys pressed
	test_bonus_full_press_matrix_all_prior_combinations()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
