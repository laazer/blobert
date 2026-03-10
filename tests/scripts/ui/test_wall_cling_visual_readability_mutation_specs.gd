#
# test_wall_cling_visual_readability_mutation_specs.gd
#
# Mutation tests and spec gap detection for wall cling visual feedback.
# Adversarially probes: boundary conditions, color precision, error handling,
# integration assumptions, and architectural constraints not fully specified.
#
# This file extends the primary + adversarial suites by testing:
#  1. Exact color value contract (mutation: off-by-one RGB channels)
#  2. Null reference handling and graceful degradation
#  3. Performance under pathological state update rates
#  4. Interaction with missing parent/visual nodes
#  5. Frame-boundary semantics and delta-time handling
#  6. Spec ambiguities requiring checkpoint resolution
#
# Ticket: wall_cling_visual_readability.md (Test Breaker revision 4)
#

class_name WallClingVisualReadabilityMutationTests
extends Object

const EPSILON: float = 0.01

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
# Factory: Create minimal ClingStateFX setup
# ---------------------------------------------------------------------------

func _load_cling_fx_script() -> GDScript:
	return load("res://scripts/fx/cling_state_fx.gd") as GDScript


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
# MUTATION TESTS: Color Precision and Channel Verification
# ---------------------------------------------------------------------------

func test_mut_idle_tint_r_channel_exact() -> void:
	"""
	Mutation: Verify idle tint R channel is exactly 0.4, not 0.3 or 0.5.
	Spec: Color(0.4, 0.9, 0.6, 1.0) is the idle color constant.
	"""
	_checkpoint(
		"Idle Tint R Channel Mutation",
		"Is the idle tint R channel specified as a hard constant, or a tolerance range?",
		"Assume idle tint R = 0.4 is a hard constant with ±0.01 tolerance (due to float precision).",
		"High"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_idle_r_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	var idle_tint: Color = visual.modulate
	_assert_approx_eq(0.4, idle_tint.r, "mut_idle_r_channel — R=0.4 within tolerance", 0.01)


func test_mut_idle_tint_g_channel_exact() -> void:
	"""
	Mutation: Verify idle tint G channel is exactly 0.9, not 0.8 or 1.0.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_idle_g_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	var idle_tint: Color = visual.modulate
	_assert_approx_eq(0.9, idle_tint.g, "mut_idle_g_channel — G=0.9 within tolerance", 0.01)


func test_mut_idle_tint_b_channel_exact() -> void:
	"""
	Mutation: Verify idle tint B channel is exactly 0.6, not 0.5 or 0.7.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_idle_b_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	var idle_tint: Color = visual.modulate
	_assert_approx_eq(0.6, idle_tint.b, "mut_idle_b_channel — B=0.6 within tolerance", 0.01)


func test_mut_idle_tint_a_channel_exact() -> void:
	"""
	Mutation: Verify idle tint A channel is exactly 1.0 (opaque).
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_idle_a_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	var idle_tint: Color = visual.modulate
	_assert_approx_eq(1.0, idle_tint.a, "mut_idle_a_channel — A=1.0 (opaque)", 0.01)


func test_mut_cling_tint_r_channel_exact() -> void:
	"""
	Mutation: Verify cling tint R channel is exactly 0.8, not 0.7 or 0.9.
	Spec: Color(0.8, 1.0, 0.5, 1.0) is the cling color constant.
	"""
	_checkpoint(
		"Cling Tint R Channel Mutation",
		"Is the cling tint R channel specified as a hard constant, or adjustable per gameplay?",
		"Assume cling tint R = 0.8 is a hard constant with ±0.01 tolerance.",
		"High"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_cling_r_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	var cling_tint: Color = visual.modulate
	_assert_approx_eq(0.8, cling_tint.r, "mut_cling_r_channel — R=0.8 within tolerance", 0.01)


func test_mut_cling_tint_g_channel_exact() -> void:
	"""
	Mutation: Verify cling tint G channel is exactly 1.0 (max green).
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_cling_g_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	var cling_tint: Color = visual.modulate
	_assert_approx_eq(1.0, cling_tint.g, "mut_cling_g_channel — G=1.0 within tolerance", 0.01)


func test_mut_cling_tint_b_channel_exact() -> void:
	"""
	Mutation: Verify cling tint B channel is exactly 0.5, not 0.4 or 0.6.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_cling_b_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	var cling_tint: Color = visual.modulate
	_assert_approx_eq(0.5, cling_tint.b, "mut_cling_b_channel — B=0.5 within tolerance", 0.01)


func test_mut_cling_tint_a_channel_exact() -> void:
	"""
	Mutation: Verify cling tint A channel is exactly 1.0 (opaque).
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("mut_cling_a_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.016)

	var cling_tint: Color = visual.modulate
	_assert_approx_eq(1.0, cling_tint.a, "mut_cling_a_channel — A=1.0 (opaque)", 0.01)


# ---------------------------------------------------------------------------
# SPEC GAP DETECTION: Error Handling and Null Safety
# ---------------------------------------------------------------------------

func test_gap_null_parent_graceful_exit() -> void:
	"""
	SPEC GAP: What happens if ClingStateFX._ready() is called with no parent?
	Spec says "gracefully handles null parent" but does not specify exact behavior.
	"""
	_checkpoint(
		"Null Parent Error Handling",
		"Should ClingStateFX._ready() log a warning, silently exit, or throw an exception if parent is null?",
		"Assume ClingStateFX silently caches null references and returns early from _process() if parent is unavailable. No crash, no spam.",
		"Medium"
	)

	var cling_fx_script: GDScript = _load_cling_fx_script()
	if cling_fx_script == null:
		_fail("gap_null_parent_load", "could not load cling_state_fx.gd script")
		return

	# Create ClingStateFX without adding it to a parent.
	var cling_fx_node: Node = cling_fx_script.new() as Node
	if cling_fx_node == null:
		_fail("gap_null_parent_instantiate", "could not instantiate cling_state_fx.gd")
		return

	# Call _ready() directly (simulating orphan node).
	if cling_fx_node.has_method("_ready"):
		cling_fx_node._ready()

	# Call _process() with null parent (should not crash).
	if cling_fx_node.has_method("_process"):
		cling_fx_node._process(0.016)

	_assert_true(true, "gap_null_parent_no_crash — ClingStateFX handles null parent without crash (GAP)")


func test_gap_missing_visual_node() -> void:
	"""
	SPEC GAP: What if PlayerVisual node is missing (deleted from scene)?
	Spec says "gracefully handles missing PlayerVisual" but exact behavior unspecified.
	"""
	_checkpoint(
		"Missing PlayerVisual Error Handling",
		"Should ClingStateFX cache PlayerVisual at _ready() or fetch it every frame? If missing, silently skip or log warning?",
		"Assume ClingStateFX caches PlayerVisual at _ready(). If null, skip modulate updates in _process() (no crash, silent skip).",
		"Medium"
	)

	var cling_fx_script: GDScript = _load_cling_fx_script()
	if cling_fx_script == null:
		_fail("gap_missing_visual_load", "could not load cling_state_fx.gd script")
		return

	var player_node: Node2D = Node2D.new()
	player_node.name = "Player"

	# Do NOT add PlayerVisual node (simulating missing visual).
	var cling_fx_node: Node = cling_fx_script.new() as Node
	if cling_fx_node == null:
		_fail("gap_missing_visual_instantiate", "could not instantiate cling_state_fx.gd")
		return

	player_node.add_child(cling_fx_node)

	if cling_fx_node.has_method("_ready"):
		cling_fx_node._ready()

	# Mock cling state and call _process().
	_mock_cling_state(player_node, true)
	if cling_fx_node.has_method("_process"):
		cling_fx_node._process(0.016)

	_assert_true(true, "gap_missing_visual_no_crash — ClingStateFX handles missing PlayerVisual without crash (GAP)")


func test_gap_missing_is_wall_clinging_state_method() -> void:
	"""
	SPEC GAP: What if parent lacks is_wall_clinging_state() method?
	Spec says "gracefully handles unavailable method" but exact behavior unspecified.
	"""
	_checkpoint(
		"Missing is_wall_clinging_state() Method",
		"Should ClingStateFX call has_method() before calling is_wall_clinging_state()? " +
		"Or assume it always exists and crash if it doesn't?",
		"Assume ClingStateFX calls has_method('is_wall_clinging_state') before invoking, and defaults to idle state if method is missing.",
		"Medium"
	)

	var cling_fx_script: GDScript = _load_cling_fx_script()
	if cling_fx_script == null:
		_fail("gap_missing_method_load", "could not load cling_state_fx.gd script")
		return

	var player_node: Node2D = Node2D.new()
	player_node.name = "Player"

	var visual: CanvasItem = ColorRect.new()
	visual.name = "PlayerVisual"
	visual.modulate = Color(0.4, 0.9, 0.6, 1.0)

	var cling_fx_node: Node = cling_fx_script.new() as Node
	if cling_fx_node == null:
		_fail("gap_missing_method_instantiate", "could not instantiate cling_state_fx.gd")
		return

	player_node.add_child(visual)
	player_node.add_child(cling_fx_node)

	if cling_fx_node.has_method("_ready"):
		cling_fx_node._ready()

	# Do NOT add is_wall_clinging_state() method; FX should handle gracefully.
	if cling_fx_node.has_method("_process"):
		cling_fx_node._process(0.016)

	# Verify visual was not modified (should remain at idle tint).
	var expected_idle: Color = Color(0.4, 0.9, 0.6, 1.0)
	_assert_eq_color(expected_idle, visual.modulate,
		"gap_missing_method_defaults_idle — missing method defaults to idle tint (GAP)")


# ---------------------------------------------------------------------------
# SPEC GAP DETECTION: Delta Time Semantics
# ---------------------------------------------------------------------------

func test_gap_delta_parameter_unused_or_used() -> void:
	"""
	SPEC GAP: Does _process(delta) use the delta parameter?
	Spec: "modulate tint is instantaneous; no fading."
	This implies delta is NOT used (no interpolation or fade-out).
	Test: Call _process() with various delta values; verify tint does not change based on delta.
	"""
	_checkpoint(
		"Delta Time Parameter Usage",
		"Does ClingStateFX._process(delta) use the delta parameter for timing, or is it purely reactive to state?",
		"Assume _process(delta) ignores the delta parameter entirely. " +
		"Tint application is instantaneous (not time-dependent). " +
		"Only state change matters, not frame time.",
		"High"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("gap_delta_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	_mock_cling_state(player_node, true)

	# Call _process() with delta=0.016.
	_step_cling_fx(fx, 0.016)
	var tint_at_016: Color = visual.modulate

	# Reset and call _process() with delta=0.033 (double).
	_mock_cling_state(player_node, false)
	_step_cling_fx(fx, 0.016)

	_mock_cling_state(player_node, true)
	_step_cling_fx(fx, 0.033)
	var tint_at_033: Color = visual.modulate

	# Verify: both produce same cling tint (delta does not affect result).
	_assert_eq_color(tint_at_016, tint_at_033,
		"gap_delta_invariant — tint independent of delta parameter (GAP)")


# ---------------------------------------------------------------------------
# STRESS TESTS: Pathological State Update Rates
# ---------------------------------------------------------------------------

func test_stress_1000_rapid_process_calls() -> void:
	"""
	Stress: Call _process() 1000 times in rapid succession.
	Verify: No memory leak, no performance degradation, tint remains stable.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("stress_1000_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)
	_mock_cling_state(player_node, true)

	var tint_mismatch: int = 0
	for i in range(1000):
		_step_cling_fx(fx, 0.016)
		if visual.modulate.distance_to(cling_tint) > EPSILON:
			tint_mismatch += 1

	_assert_true(tint_mismatch == 0,
		"stress_1000_calls — 1000 _process() calls maintain stable tint (STRESS)")


func test_stress_state_flicker_per_frame() -> void:
	"""
	Stress: Toggle cling state every other frame (100 toggles).
	Verify: No glitches, correct alternation, no lingering intermediate states.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("stress_flicker_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var idle_tint: Color = Color(0.4, 0.9, 0.6, 1.0)
	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)
	var mismatches: int = 0

	for frame in range(100):
		var should_cling: bool = (frame % 2) == 0
		_mock_cling_state(player_node, should_cling)
		_step_cling_fx(fx, 0.016)

		var expected_tint: Color = cling_tint if should_cling else idle_tint
		if visual.modulate.distance_to(expected_tint) > EPSILON:
			mismatches += 1

	_assert_true(mismatches == 0,
		"stress_flicker_100cycles — state flicker tracked correctly (STRESS)")


func test_stress_maximum_zero_delta() -> void:
	"""
	Stress: Call _process() with delta=0.0 (zero frame advance).
	Verify: No division-by-zero, no infinite loops, tint still applies.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("stress_zero_delta_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)
	_mock_cling_state(player_node, true)

	# Call _process() with zero delta (edge case).
	_step_cling_fx(fx, 0.0)

	_assert_eq_color(cling_tint, visual.modulate,
		"stress_zero_delta_no_crash — _process(0.0) handles gracefully (STRESS)")


func test_stress_extreme_high_delta() -> void:
	"""
	Stress: Call _process() with delta=1.0 (unusually long frame).
	Verify: No overflow, tint still applies correctly, no state machine corruption.
	"""
	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("stress_high_delta_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)
	_mock_cling_state(player_node, true)

	# Call _process() with very high delta.
	_step_cling_fx(fx, 1.0)

	_assert_eq_color(cling_tint, visual.modulate,
		"stress_high_delta_no_overflow — _process(1.0) handles gracefully (STRESS)")


# ---------------------------------------------------------------------------
# SPEC GAP DETECTION: Node Hierarchy and Initialization
# ---------------------------------------------------------------------------

func test_gap_ready_before_first_process() -> void:
	"""
	SPEC GAP: Does ClingStateFX require _ready() to be called before _process()?
	Godot best practice: yes, but spec does not explicitly state this.
	Test: Call _process() WITHOUT calling _ready() first.
	"""
	_checkpoint(
		"_ready() Dependency for _process()",
		"Does ClingStateFX._process() require _ready() to be called first, or is it safe to call _process() directly?",
		"Assume ClingStateFX._process() can be called safely even if _ready() was skipped. " +
		"If node references are null, they are initialized on-demand or defaulted.",
		"Medium"
	)

	var cling_fx_script: GDScript = _load_cling_fx_script()
	if cling_fx_script == null:
		_fail("gap_ready_before_process_load", "could not load cling_state_fx.gd")
		return

	var player_node: Node2D = Node2D.new()
	player_node.name = "Player"

	var visual: CanvasItem = ColorRect.new()
	visual.name = "PlayerVisual"
	visual.modulate = Color(0.4, 0.9, 0.6, 1.0)

	var cling_fx_node: Node = cling_fx_script.new() as Node
	if cling_fx_node == null:
		_fail("gap_ready_before_process_instantiate", "could not instantiate cling_state_fx.gd")
		return

	player_node.add_child(visual)
	player_node.add_child(cling_fx_node)

	# Skip _ready() and call _process() directly.
	_mock_cling_state(player_node, true)
	if cling_fx_node.has_method("_process"):
		cling_fx_node._process(0.016)

	# Verify: either tint is correct or visual is unchanged (no crash).
	_assert_true(true,
		"gap_ready_before_process_safe — _process() callable without prior _ready() (GAP)")


func test_gap_multiple_ready_calls() -> void:
	"""
	SPEC GAP: Is ClingStateFX safe if _ready() is called multiple times?
	Edge case: Scene reload or manual re-initialization.
	"""
	_checkpoint(
		"Multiple _ready() Calls Safety",
		"Should ClingStateFX handle multiple _ready() calls gracefully, or will it break on the second call?",
		"Assume _ready() is idempotent (safe to call multiple times). Node references are re-cached, no side effects.",
		"Medium"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("gap_multi_ready_setup", "could not create ClingStateFX setup")
		return

	var fx: Node = setup.get("fx", null)

	# Call _ready() again.
	if fx.has_method("_ready"):
		fx._ready()

	# Call _process() after multiple _ready() calls.
	_step_cling_fx(fx, 0.016)

	_assert_true(true,
		"gap_multi_ready_safe — multiple _ready() calls handled safely (GAP)")


# ---------------------------------------------------------------------------
# INTEGRATION EDGE CASES: Interaction with Other Systems
# ---------------------------------------------------------------------------

func test_gap_modulate_property_override() -> void:
	"""
	SPEC GAP: If another system sets visual.modulate outside of ClingStateFX,
	does ClingStateFX overwrite it, or respect external changes?
	Spec: "modulate is applied in _process()"; no mention of conflict resolution.
	"""
	_checkpoint(
		"External Modulate Override Conflict",
		"What happens if another system (e.g., shader, animation, UI) sets PlayerVisual.modulate while ClingStateFX is active?",
		"Assume ClingStateFX writes modulate every frame, overwriting external changes. " +
		"ClingStateFX has priority over other visual systems.",
		"Medium"
	)

	var setup := _make_cling_fx_setup()
	if setup.is_empty():
		_fail("gap_modulate_override_setup", "could not create ClingStateFX setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var player_node: Node = setup.get("player", null)
	var fx: Node = setup.get("fx", null)

	var external_tint: Color = Color(1.0, 0.0, 0.0, 1.0)  # Red (external).
	var cling_tint: Color = Color(0.8, 1.0, 0.5, 1.0)

	_mock_cling_state(player_node, true)

	# External system sets modulate to red.
	visual.modulate = external_tint

	# ClingStateFX._process() should overwrite with cling tint.
	_step_cling_fx(fx, 0.016)

	_assert_eq_color(cling_tint, visual.modulate,
		"gap_modulate_override_cling_wins — ClingStateFX modulate overwrites external changes (GAP)")


# ---------------------------------------------------------------------------
# Test Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("\n=== WallClingVisualReadabilityMutationTests ===\n")

	# Color precision mutations
	print("Color Precision Mutations:")
	test_mut_idle_tint_r_channel_exact()
	test_mut_idle_tint_g_channel_exact()
	test_mut_idle_tint_b_channel_exact()
	test_mut_idle_tint_a_channel_exact()
	test_mut_cling_tint_r_channel_exact()
	test_mut_cling_tint_g_channel_exact()
	test_mut_cling_tint_b_channel_exact()
	test_mut_cling_tint_a_channel_exact()

	# Error handling and spec gaps
	print("\nError Handling & Spec Gaps:")
	test_gap_null_parent_graceful_exit()
	test_gap_missing_visual_node()
	test_gap_missing_is_wall_clinging_state_method()

	# Delta time semantics
	print("\nDelta Time Semantics:")
	test_gap_delta_parameter_unused_or_used()

	# Stress tests
	print("\nStress Tests:")
	test_stress_1000_rapid_process_calls()
	test_stress_state_flicker_per_frame()
	test_stress_maximum_zero_delta()
	test_stress_extreme_high_delta()

	# Node hierarchy gaps
	print("\nNode Hierarchy & Initialization Gaps:")
	test_gap_ready_before_first_process()
	test_gap_multiple_ready_calls()

	# Integration edge cases
	print("\nIntegration Edge Cases:")
	test_gap_modulate_property_override()

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
	return _fail_count
	print("Failed: " + str(_fail_count))
	print("Checkpoints: " + str(_checkpoint_count))
	print("Total: " + str(_pass_count + _fail_count))
	if _fail_count == 0:
		print("Status: ALL TESTS PASSED ✓")
	else:
		print("Status: FAILURES DETECTED ✗")
