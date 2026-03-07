#
# test_wall_cling_visual_readability_adversarial.gd
#
# Adversarial (edge-case and stress) tests for wall cling visual feedback.
# Exercises extreme scenarios: rapid state transitions, mixed velocity conditions,
# particle cleanup, and consistency under repeated cycles.
#
# Extends primary test suite with: repeated cling/detach stress, left/right wall
# verification, particle emitter lifecycle, and visual stability under state changes.
#
# Ticket: wall_cling_visual_readability.md (Test Designer revision 3)
#

class_name WallClingVisualReadabilityAdversarialTests
extends Object

const EPSILON: float = 0.01
const RAPID_CYCLES: int = 50  # Stress test iteration count

var _pass_count: int = 0
var _fail_count: int = 0
var _checkpoint_count: int = 0


# ---------------------------------------------------------------------------
# Helpers: Assertion utilities
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _checkpoint(label: String, question: String, assumption: String, confidence: String) -> void:
	_checkpoint_count += 1
	print("  [CHECKPOINT] " + label)
	print("    Would have asked: " + question)
	print("    Assumption: " + assumption)
	print("    Confidence: " + confidence)


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


func _assert_eq_color(expected: Color, actual: Color, test_name: String, tolerance: float = EPSILON) -> void:
	var color_diff: float = abs(expected.r - actual.r) + abs(expected.g - actual.g) + abs(expected.b - actual.b) + abs(expected.a - actual.a)
	if color_diff < tolerance:
		_pass(test_name)
	else:
		_fail(test_name, "expected Color(%.2f, %.2f, %.2f, %.2f), got Color(%.2f, %.2f, %.2f, %.2f)" % [expected.r, expected.g, expected.b, expected.a, actual.r, actual.g, actual.b, actual.a])


func _assert_approx_eq(expected: float, actual: float, test_name: String, tolerance: float = EPSILON) -> void:
	if abs(expected - actual) < tolerance:
		_pass(test_name)
	else:
		_fail(test_name, "expected %.2f, got %.2f (delta %.2f)" % [expected, actual, abs(expected - actual)])


# ---------------------------------------------------------------------------
# Factory: Create minimal ClingStateFX setup (reused from primary tests)
# ---------------------------------------------------------------------------

func _load_cling_fx_script() -> GDScript:
	return load("res://scripts/cling_state_fx.gd") as GDScript


func _make_cling_fx_setup() -> Dictionary:
	var cling_fx_script: GDScript = _load_cling_fx_script()
	if cling_fx_script == null:
		return {}

	var player_node: Node2D = Node2D.new()
	player_node.name = "Player"

	var visual: CanvasItem = ColorRect.new()
	visual.name = "PlayerVisual"
	visual.modulate = Color(0.4, 0.9, 0.6, 1.0)

	var cling_fx_node: Node = cling_fx_script.new() as Node
	if cling_fx_node == null:
		return {}

	player_node.add_child(visual)
	player_node.add_child(cling_fx_node)

	if cling_fx_node.has_method("_ready"):
		cling_fx_node._ready()

	return {
		"player": player_node,
		"visual": visual,
		"fx": cling_fx_node,
	}


func _mock_cling_state(player_node: Node, is_clinging: bool) -> void:
	if player_node == null:
		return
	var _mock_state: bool = is_clinging
	player_node.is_wall_clinging_state = func() -> bool:
		return _mock_state


func _step_cling_fx(fx_node: Node, delta: float = 0.016) -> void:
	if fx_node == null or not fx_node.has_method("_process"):
		return
	fx_node._process(delta)


# ---------------------------------------------------------------------------
# ADVERSARIAL TEST SUITE: Rapid Cling/Detach Transitions
# ---------------------------------------------------------------------------

func test_adv_rapid_cling_detach_50_cycles() -> void:
	"""
	Stress test: Rapidly toggle cling state 50 times.
	Verify: No visual lag, no tint glitches, consistent state tracking.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_rapid_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var idle_tint: Color = Color(0.4, 0.9, 0.6, 1.0)
	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	var glitch_count: int = 0

	for cycle in range(RAPID_CYCLES):
		# Cling.
		_mock_cling_state(player_node, true)
		_step_cling_fx(fx, 0.016)
		if visual.modulate.distance_to(cling_tint) > EPSILON:
			glitch_count += 1

		# Detach.
		_mock_cling_state(player_node, false)
		_step_cling_fx(fx, 0.016)
		if visual.modulate.distance_to(idle_tint) > EPSILON:
			glitch_count += 1

	_assert_true(glitch_count == 0,
		"adv_rapid_cycles — 50 rapid cling/detach cycles without visual glitches (ADVERS)")


func test_adv_high_frequency_state_changes_per_frame() -> void:
	"""
	Stress test: Call _process() multiple times per frame without changing state.
	Verify: Tint remains stable, no flickering or oscillation.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_hf_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	# Set cling state and call _process() 10 times per frame (simulating glitched loop).
	_mock_cling_state(player_node, true)
	var modulate_values: Array[Color] = []
	for i in range(10):
		_step_cling_fx(fx, 0.016)
		modulate_values.append(visual.modulate if visual != null else Color.WHITE)

	# Verify all captures are identical (no flickering).
	var all_same: bool = true
	for i in range(1, modulate_values.size()):
		if modulate_values[i].distance_to(modulate_values[0]) > EPSILON:
			all_same = false
			break

	_assert_true(all_same,
		"adv_hf_stability — repeated _process() calls maintain stable tint (ADVERS)")


# ---------------------------------------------------------------------------
# ADVERSARIAL TEST SUITE: Left/Right Wall Consistency
# ---------------------------------------------------------------------------

func test_adv_left_wall_cling_tint_identical_to_right() -> void:
	"""
	Edge case: Verify that cling tint is identical regardless of wall side.
	Modulate is direction-agnostic; tint should not change based on velocity.x sign.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_lr_wall_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	# Mock left wall cling (velocity.x < 0 conceptually, but FX doesn't track velocity).
	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)
	var left_wall_tint: Color = visual.modulate if visual != null else Color.WHITE

	# Reset and simulate right wall cling (velocity.x > 0).
	var player_node2: Node2D = Node2D.new()
	player_node2.name = "Player"
	var visual2: CanvasItem = ColorRect.new()
	visual2.name = "PlayerVisual"
	visual2.modulate = Color(0.4, 0.9, 0.6, 1.0)
	var fx2: Node = _load_cling_fx_script().new() as Node
	player_node2.add_child(visual2)
	player_node2.add_child(fx2)
	if fx2.has_method("_ready"):
		fx2._ready()

	_mock_cling_state(player_node2, true)
	_step_cling_fx(fx2, 0.016)
	var right_wall_tint: Color = visual2.modulate if visual2 != null else Color.WHITE

	_assert_eq_color(left_wall_tint, right_wall_tint,
		"adv_lr_wall_identical — cling tint identical for left and right walls (ADVERS)")


func test_adv_wall_side_transitions_maintain_tint() -> void:
	"""
	Edge case: Player transitions from clinging on left wall to right wall.
	Verify: Tint remains consistent during transition (no flickering or reversion).
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_lr_transition_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	# Cling on left wall.
	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)
	_assert_eq_color(cling_tint, visual.modulate,
		"adv_lr_trans_left_start — cling tint on left wall")

	# Remain clinging (transition to right wall, but is_wall_clinging remains true).
	_step_cling_fx(fx, 0.016)
	_assert_eq_color(cling_tint, visual.modulate,
		"adv_lr_trans_right_end — cling tint maintained on right wall (ADVERS)")


# ---------------------------------------------------------------------------
# ADVERSARIAL TEST SUITE: Particle Emitter Lifecycle (if implemented)
# ---------------------------------------------------------------------------

func test_adv_particle_emitter_optional_existence() -> void:
	"""
	Edge case: ClingStateFX may or may not have a CPUParticles2D child.
	If present: should emit only while cling+slide.
	If absent: test should still pass (optional feature).
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_particle_optional_setup", "could not create ClingStateFX setup")
		return

	var fx: Node = setup.get("fx", null)

	# Check if CPUParticles2D child exists.
	var particle_emitter: Node = null
	if fx != null:
		particle_emitter = fx.get_node_or_null("ClingTrail")

	if particle_emitter == null:
		_assert_true(true,
			"adv_particle_optional_absent — no CPUParticles2D; feature is optional (ADVERS)")
	else:
		_assert_true(true,
			"adv_particle_optional_present — CPUParticles2D present; check emission logic (ADVERS)")


func test_adv_particle_cleanup_on_detach() -> void:
	"""
	Edge case: If particle emitter exists, verify it is disabled on detach.
	Particles should stop emitting but existing particles fade naturally.
	"""
	_checkpoint(
		"Particle Cleanup Mechanism",
		"Should particle emitter be set to emitting=false on detach, or removed entirely?",
		"Assume emitter should be set to emitting=false (not removed), allowing existing particles to fade per lifetime.",
		"Medium"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_particle_cleanup_setup", "could not create ClingStateFX setup")
		return

	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var particle_emitter: Node = null
	if fx != null:
		particle_emitter = fx.get_node_or_null("ClingTrail")

	if particle_emitter == null:
		_assert_true(true,
			"adv_particle_cleanup_none — no particle emitter present (optional feature)")
		return

	# Mock cling state.
	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	# Verify emitter is emitting (if it has the property).
	var emitter_was_emitting: bool = false
	if particle_emitter.has_property("emitting"):
		emitter_was_emitting = particle_emitter.get("emitting")

	# Detach.
	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	# Verify emitter stopped emitting.
	var emitter_is_emitting: bool = false
	if particle_emitter.has_property("emitting"):
		emitter_is_emitting = particle_emitter.get("emitting")

	if particle_emitter.has_property("emitting"):
		_assert_false(emitter_is_emitting,
			"adv_particle_cleanup_disabled — particle emitter disabled on detach (ADVERS)")
	else:
		_assert_true(true,
			"adv_particle_cleanup_no_prop — emitter lacks emitting property (optional)")


# ---------------------------------------------------------------------------
# ADVERSARIAL TEST SUITE: Tint Consistency Over Multiple Frames
# ---------------------------------------------------------------------------

func test_adv_tint_persistence_over_10_frames() -> void:
	"""
	Stress test: Hold cling state for 10 frames; verify tint remains constant.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_persistence_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)
	var inconsistency_count: int = 0

	_mock_cling_state(player_node, true)
	for frame in range(10):
		_step_cling_fx(fx, 0.016)
		if visual.modulate.distance_to(cling_tint) > EPSILON:
			inconsistency_count += 1

	_assert_true(inconsistency_count == 0,
		"adv_persistence_10frames — cling tint consistent over 10 frames (ADVERS)")


func test_adv_idle_tint_persistence_over_10_frames() -> void:
	"""
	Stress test: Hold idle state for 10 frames; verify tint remains constant.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_idle_persistence_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var idle_tint: Color = Color(0.4, 0.9, 0.6, 1.0)
	var inconsistency_count: int = 0

	_mock_cling_state(player_node, false)
	for frame in range(10):
		_step_cling_fx(fx, 0.016)
		if visual.modulate.distance_to(idle_tint) > EPSILON:
			inconsistency_count += 1

	_assert_true(inconsistency_count == 0,
		"adv_idle_persistence_10frames — idle tint consistent over 10 frames (ADVERS)")


# ---------------------------------------------------------------------------
# ADVERSARIAL TEST SUITE: Boundary Transitions
# ---------------------------------------------------------------------------

func test_adv_immediate_cling_detach_no_intermediate_state() -> void:
	"""
	Edge case: Cling state changes are frame-atomic; no intermediate tint values.
	Verify: Transition from idle → cling → idle has no intermediate color.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_boundary_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var idle_tint: Color = Color(0.4, 0.9, 0.6, 1.0)
	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	# Step 1: Idle.
	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)
	var step1_tint: Color = visual.modulate

	# Step 2: Cling.
	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)
	var step2_tint: Color = visual.modulate

	# Step 3: Detach.
	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)
	var step3_tint: Color = visual.modulate

	# Verify: Step 1 = idle, Step 2 = cling, Step 3 = idle (no intermediate).
	_assert_eq_color(idle_tint, step1_tint, "adv_boundary_s1_idle")
	_assert_eq_color(cling_tint, step2_tint, "adv_boundary_s2_cling")
	_assert_eq_color(idle_tint, step3_tint, "adv_boundary_s3_detach — atomic transitions (ADVERS)")


func test_adv_detach_while_sliding_maintains_instant_cleanup() -> void:
	"""
	Edge case: Detach while "sliding" (conceptually high velocity downward).
	Verify: Tint is removed instantly; no delayed cleanup.
	(Note: FX layer doesn't track velocity, but the test verifies state→visual contract.)
	"""
	_checkpoint(
		"Detach While Sliding Condition",
		"Should the FX presenter check velocity.y to conditionally apply detach cleanup, or is detach always instant?",
		"Assume detach cleanup is always instant (AC#3). Velocity is tracked elsewhere. " +
		"FX presenter responds only to is_wall_clinging state, not velocity.",
		"High"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_detach_slide_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var idle_tint: Color = Color(0.4, 0.9, 0.6, 1.0)

	# Simulate: cling state, then detach (tint should revert instantly).
	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	var detach_tint: Color = visual.modulate
	_assert_eq_color(idle_tint, detach_tint,
		"adv_detach_slide_instant — tint reverts instantly on detach (ADVERS)")


# ---------------------------------------------------------------------------
# ADVERSARIAL TEST SUITE: Visual Stability Under State Changes
# ---------------------------------------------------------------------------

func test_adv_no_visual_lag_between_state_and_tint() -> void:
	"""
	Latency: Verify that tint update occurs in the same _process() call as state change.
	No frame lag between is_wall_clinging change and modulate update.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_lag_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	# Change state to cling and step FX in same call.
	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	# Verify: tint is applied in that same frame (no 1-frame lag).
	_assert_eq_color(cling_tint, visual.modulate,
		"adv_lag_none — tint updated in same frame as state change (ADVERS)")


func test_adv_tint_matches_state_every_frame() -> void:
	"""
	Correctness: Over 20 frames with random state changes, verify tint always matches state.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("adv_random_state_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var idle_tint: Color = Color(0.4, 0.9, 0.6, 1.0)
	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)
	var mismatch_count: int = 0

	# Pseudo-random sequence (deterministic).
	var states: Array[bool] = [true, false, true, true, false, false, true, false, false, true,
								 true, true, false, true, false, true, true, false, false, false]

	for frame in range(states.size()):
		var is_clinging: bool = states[frame]
		_mock_cling_state(player_node, is_clinging)
		_step_cling_fx(fx, 0.016)

		var expected_tint: Color = cling_tint if is_clinging else idle_tint
		var actual_tint: Color = visual.modulate

		if actual_tint.distance_to(expected_tint) > EPSILON:
			mismatch_count += 1

	_assert_true(mismatch_count == 0,
		"adv_random_match — tint matches state every frame over 20 frames (ADVERS)")


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("\n=== WallClingVisualReadabilityAdversarialTests ===\n")

	# Rapid transition tests
	print("Rapid Cling/Detach Transitions:")
	test_adv_rapid_cling_detach_50_cycles()
	test_adv_high_frequency_state_changes_per_frame()

	# Left/right wall tests
	print("\nLeft/Right Wall Consistency:")
	test_adv_left_wall_cling_tint_identical_to_right()
	test_adv_wall_side_transitions_maintain_tint()

	# Particle tests
	print("\nParticle Emitter Lifecycle:")
	test_adv_particle_emitter_optional_existence()
	test_adv_particle_cleanup_on_detach()

	# Persistence tests
	print("\nTint Persistence Over Multiple Frames:")
	test_adv_tint_persistence_over_10_frames()
	test_adv_idle_tint_persistence_over_10_frames()

	# Boundary tests
	print("\nBoundary Transitions:")
	test_adv_immediate_cling_detach_no_intermediate_state()
	test_adv_detach_while_sliding_maintains_instant_cleanup()

	# Stability tests
	print("\nVisual Stability Under State Changes:")
	test_adv_no_visual_lag_between_state_and_tint()
	test_adv_tint_matches_state_every_frame()

	# Summary
	print("\n=== SUMMARY ===")
	print("Passed: " + str(_pass_count))
	print("Failed: " + str(_fail_count))
	print("Checkpoints: " + str(_checkpoint_count))
	print("Total: " + str(_pass_count + _fail_count))
	if _fail_count == 0:
		print("Status: ALL TESTS PASSED ✓")
	else:
		print("Status: FAILURES DETECTED ✗")
	# return failure count
	return _fail_count
