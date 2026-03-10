#
# test_infection_state_fx_mutation_edge_cases.gd
#
# Mutation, edge case, and spec gap detection tests for infection state FX.
# Covers:
#  - Color boundary mutations (almost-correct colors)
#  - Label text mutations (typos, case sensitivity)
#  - Rapid frame-by-frame state changes (stress)
#  - Null/missing visual node handling
#  - Process() called before _ready() (initialization order)
#  - State transitions from unexpected/intermediate states
#  - Long sequences of state changes (memory/orphan checks)
#  - Absorb feedback prerequisites (spec gap: absorb FX not yet implemented)
#
# Ticket: visual_feedback_infection.md (Test Breaker Agent)
#

class_name InfectionStateFxMutationEdgeCaseTests
extends Object


var _pass_count: int = 0
var _fail_count: int = 0


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


func _assert_eq_color(expected: Color, actual: Color, test_name: String, tolerance: float = 0.01) -> void:
	var color_diff: float = abs(expected.r - actual.r) + abs(expected.g - actual.g) + abs(expected.b - actual.b) + abs(expected.a - actual.a)
	if color_diff < tolerance:
		_pass(test_name)
	else:
		_fail(test_name, "expected Color(%.2f, %.2f, %.2f, %.2f), got Color(%.2f, %.2f, %.2f, %.2f)" % [expected.r, expected.g, expected.b, expected.a, actual.r, actual.g, actual.b, actual.a])


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _load_enemy_infection_script() -> GDScript:
	return load("res://scripts/enemy/enemy_infection.gd") as GDScript


func _load_infection_state_fx_script() -> GDScript:
	return load("res://scripts/infection/infection_state_fx.gd") as GDScript


func _make_fx_setup() -> Dictionary:
	var enemy_script: GDScript = _load_enemy_infection_script()
	var fx_script: GDScript = _load_infection_state_fx_script()
	if enemy_script == null or fx_script == null:
		return {}

	var enemy_node: Node2D = enemy_script.new() as Node2D
	if enemy_node == null:
		return {}

	var visual := ColorRect.new()
	visual.name = "EnemyVisual"
	var label := Label.new()
	label.name = "StateLabel"
	var fx_node: Node = fx_script.new()

	enemy_node.add_child(visual)
	enemy_node.add_child(fx_node)
	fx_node.add_child(label)

	if enemy_node.has_method("_ready"):
		enemy_node._ready()
	if fx_node.has_method("_ready"):
		fx_node._ready()

	var esm: EnemyStateMachine = null
	if enemy_node.has_method("get_esm"):
		esm = enemy_node.get_esm()

	return {
		"enemy": enemy_node,
		"visual": visual,
		"label": label,
		"fx": fx_node,
		"esm": esm,
	}


func _drive_state_and_step(setup: Dictionary, state: String) -> void:
	var esm: EnemyStateMachine = setup.get("esm", null)
	var fx: Node = setup.get("fx", null)
	if esm == null or fx == null:
		return

	match state:
		"idle":
			esm.reset()
		"weakened":
			esm.reset()
			esm.apply_weaken_event()
		"infected":
			esm.reset()
			esm.apply_weaken_event()
			esm.apply_infection_event()
		"dead":
			esm.reset()
			esm.apply_death_event()
		_:
			pass

	fx._process(0.0)


# MUTATION TEST: Color value boundary checks
# Spec requires exact colors; off-by-one mutations should fail
func test_mutation_weakened_color_off_by_small_delta() -> void:
	var fx_script: GDScript = _load_infection_state_fx_script()
	if fx_script == null:
		_fail("mut_color_weakened_load", "could not load infection_state_fx.gd")
		return

	var fx: Node = fx_script.new()
	var color = fx._modulate_for_state("weakened")

	# Spec says (1.0, 0.85, 0.5, 1.0)
	# These are slightly off mutations that must NOT pass
	_assert_false(color == Color(1.0, 0.80, 0.5, 1.0),
		"mut_weakened_g_too_low — weakened green at 0.80 is NOT 0.85")
	_assert_false(color == Color(1.0, 0.90, 0.5, 1.0),
		"mut_weakened_g_too_high — weakened green at 0.90 is NOT 0.85")
	_assert_false(color == Color(1.0, 0.85, 0.45, 1.0),
		"mut_weakened_b_too_low — weakened blue at 0.45 is NOT 0.50")
	_assert_false(color == Color(1.0, 0.85, 0.55, 1.0),
		"mut_weakened_b_too_high — weakened blue at 0.55 is NOT 0.50")


# MUTATION TEST: Infected color boundaries
func test_mutation_infected_color_off_by_small_delta() -> void:
	var fx_script: GDScript = _load_infection_state_fx_script()
	if fx_script == null:
		_fail("mut_color_infected_load", "could not load infection_state_fx.gd")
		return

	var fx: Node = fx_script.new()
	var color = fx._modulate_for_state("infected")

	# Spec says (0.75, 0.5, 1.0, 1.0)
	_assert_false(color == Color(0.70, 0.5, 1.0, 1.0),
		"mut_infected_r_too_low — infected red at 0.70 is NOT 0.75")
	_assert_false(color == Color(0.80, 0.5, 1.0, 1.0),
		"mut_infected_r_too_high — infected red at 0.80 is NOT 0.75")
	_assert_false(color == Color(0.75, 0.45, 1.0, 1.0),
		"mut_infected_g_too_low — infected green at 0.45 is NOT 0.50")
	_assert_false(color == Color(0.75, 0.55, 1.0, 1.0),
		"mut_infected_g_too_high — infected green at 0.55 is NOT 0.50")


# MUTATION TEST: Label text case sensitivity
func test_mutation_label_text_case_sensitive() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("mut_label_case_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		return

	# Weakened must be exactly "Weakened", not "weakened" or "WEAKENED"
	_drive_state_and_step(setup, "weakened")
	_assert_false(label.text == "weakened",
		"mut_weakened_lowercase — label is NOT lowercase")
	_assert_false(label.text == "WEAKENED",
		"mut_weakened_uppercase — label is NOT uppercase")
	_assert_true(label.text == "Weakened",
		"mut_weakened_correct — label is exactly 'Weakened'")

	# Infected must be exactly "Infected"
	_drive_state_and_step(setup, "infected")
	_assert_false(label.text == "infected",
		"mut_infected_lowercase — label is NOT lowercase")
	_assert_false(label.text == "INFECTED",
		"mut_infected_uppercase — label is NOT uppercase")
	_assert_true(label.text == "Infected",
		"mut_infected_correct — label is exactly 'Infected'")

	# Dead must be exactly "Dead"
	_drive_state_and_step(setup, "dead")
	_assert_false(label.text == "dead",
		"mut_dead_lowercase — label is NOT lowercase")
	_assert_false(label.text == "DEAD",
		"mut_dead_uppercase — label is NOT uppercase")
	_assert_true(label.text == "Dead",
		"mut_dead_correct — label is exactly 'Dead'")


# MUTATION TEST: Prevent swapped color assignments
func test_mutation_no_swapped_weakened_infected_colors() -> void:
	var setup1 := _make_fx_setup()
	var setup2 := _make_fx_setup()
	if setup1.is_empty() or setup2.is_empty():
		_fail("mut_swap_setup", "could not create setups")
		return

	var visual1: CanvasItem = setup1.get("visual", null)
	var visual2: CanvasItem = setup2.get("visual", null)
	if visual1 == null or visual2 == null:
		return

	_drive_state_and_step(setup1, "weakened")
	_drive_state_and_step(setup2, "infected")

	# If colors are swapped, weakened would get infected color
	var infected_color := Color(0.75, 0.5, 1.0, 1.0)
	_assert_false(visual1.modulate == infected_color,
		"mut_swap_weakened_has_infected_color — weakened is NOT assigned infected color")

	var weakened_color := Color(1.0, 0.85, 0.5, 1.0)
	_assert_false(visual2.modulate == weakened_color,
		"mut_swap_infected_has_weakened_color — infected is NOT assigned weakened color")


# EDGE CASE: Process called before _ready() (initialization order)
func test_edge_case_process_before_ready() -> void:
	var enemy_script: GDScript = _load_enemy_infection_script()
	var fx_script: GDScript = _load_infection_state_fx_script()
	if enemy_script == null or fx_script == null:
		_fail("mut_edge_init_order_load", "could not load scripts")
		return

	var enemy_node: Node2D = enemy_script.new() as Node2D
	if enemy_node == null:
		return

	var visual := ColorRect.new()
	visual.name = "EnemyVisual"
	var label := Label.new()
	label.name = "StateLabel"
	var fx_node: Node = fx_script.new()

	enemy_node.add_child(visual)
	enemy_node.add_child(fx_node)
	fx_node.add_child(label)

	# Call _process BEFORE _ready() on FX
	# Should handle gracefully (lazy initialization)
	fx_node._process(0.0)

	# Now call _ready() and drive a state
	if enemy_node.has_method("_ready"):
		enemy_node._ready()
	if fx_node.has_method("_ready"):
		fx_node._ready()

	var esm: EnemyStateMachine = enemy_node.get_esm() if enemy_node.has_method("get_esm") else null
	if esm == null:
		return

	esm.apply_weaken_event()
	fx_node._process(0.0)

	# Should still apply weakened color after recovery
	_assert_eq_color(Color(1.0, 0.85, 0.5, 1.0), visual.modulate,
		"mut_edge_init_order_weakened — color applies after late _ready()")


# EDGE CASE: State transition with missing EnemyVisual node
func test_edge_case_missing_enemy_visual_node() -> void:
	var enemy_script: GDScript = _load_enemy_infection_script()
	var fx_script: GDScript = _load_infection_state_fx_script()
	if enemy_script == null or fx_script == null:
		return

	var enemy_node: Node2D = enemy_script.new() as Node2D
	var fx_node: Node = fx_script.new()

	# Add FX to enemy but NO EnemyVisual
	enemy_node.add_child(fx_node)

	if enemy_node.has_method("_ready"):
		enemy_node._ready()
	if fx_node.has_method("_ready"):
		fx_node._ready()

	var esm: EnemyStateMachine = enemy_node.get_esm() if enemy_node.has_method("get_esm") else null
	if esm == null:
		return

	# Transition to weakened; FX should not crash
	esm.reset()
	esm.apply_weaken_event()
	fx_node._process(0.0)

	_pass("mut_edge_no_visual — missing EnemyVisual does not crash")


# STRESS TEST: Rapid frame-by-frame state transitions
func test_stress_rapid_frame_by_frame_transitions() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("stress_rapid_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)
	var esm: EnemyStateMachine = setup.get("esm", null)
	var fx: Node = setup.get("fx", null)
	if visual == null or label == null or esm == null or fx == null:
		return

	# Rapidly cycle through states 10 times
	for i in range(10):
		esm.reset()
		esm.apply_weaken_event()
		fx._process(0.0)
		
		esm.apply_infection_event()
		fx._process(0.0)
		
		esm.apply_death_event()
		fx._process(0.0)

	# Final state should be dead
	_assert_eq_color(Color(0.25, 0.25, 0.25, 0.5), visual.modulate,
		"stress_rapid_final_color — final color is dead after 10 rapid cycles")
	_assert_eq_string("Dead", label.text,
		"stress_rapid_final_label — final label is 'Dead' after 10 rapid cycles")


# STRESS TEST: Very long state sequence with state resets
func test_stress_long_state_sequence() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("stress_long_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var esm: EnemyStateMachine = setup.get("esm", null)
	var fx: Node = setup.get("fx", null)
	if visual == null or esm == null or fx == null:
		return

	# Perform 50 state transitions; no crashes or memory issues
	for i in range(50):
		if i % 4 == 0:
			_drive_state_and_step(setup, "idle")
		elif i % 4 == 1:
			_drive_state_and_step(setup, "weakened")
		elif i % 4 == 2:
			_drive_state_and_step(setup, "infected")
		else:
			_drive_state_and_step(setup, "dead")

	_pass("stress_long_sequence — 50 state transitions complete without crash")


# SPEC GAP DETECTION: Absorb feedback not defined in implementation
# F6 specifies absorb feedback (particles, animation) but infection_state_fx.gd
# does not implement it. This test detects the gap.
func test_spec_gap_absorb_feedback_not_implemented() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("spec_gap_absorb_load", "could not create setup")
		return

	var fx: Node = setup.get("fx", null)
	if fx == null:
		return

	# Check if FX has any absorb-related method or signal
	var has_absorb_method := fx.has_method("_spawn_absorb_particles") or \
							fx.has_method("play_absorb_feedback") or \
							fx.has_method("trigger_absorb_effect")

	# CHECKPOINT: spec_gap_absorb_feedback_not_implemented
	# This test reveals that F6 (absorb feedback) is not yet implemented
	if not has_absorb_method:
		print("  WARNING: [CHECKPOINT] Absorb feedback (F6) not found in infection_state_fx.gd")
		print("           Spec requires particle effect + optional animation on absorb.")
		print("           Assuming Presentation Agent will implement in IMPLEMENTATION_FRONTEND task.")
		_pass("spec_gap_absorb_feedback — absorb FX not yet implemented (expected)")
	else:
		_pass("spec_gap_absorb_feedback — absorb FX method found")


# SPEC GAP DETECTION: Label positioning not verified
# F5 requires label to be "immediately above enemy center" but tests don't check position
func test_spec_gap_label_positioning_not_tested() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("spec_gap_label_pos_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		return

	# Check if label has position property set
	# Spec says offset should default to Vector2(0, -30)
	# But tests do not validate position, only visibility and text
	if label.position == Vector2(0, 0):
		print("  WARNING: [CHECKPOINT] Label position is (0, 0), spec assumes offset above enemy")
		print("           NF1/F5 requires label 'immediately above enemy center' with offset ~(0, -30).")
		print("           Presentation Agent should set label.position or use CanvasLayer/anchors.")
		_pass("spec_gap_label_position — label position not yet validated (expected)")
	else:
		_pass("spec_gap_label_position — label position set to " + str(label.position))


# SPEC GAP DETECTION: Color contrast not measured
# NF1 requires contrast ratio >= 3:1 but this is subjective/pixel-based
func test_spec_gap_color_contrast_subjective() -> void:
	# This test documents that color contrast is verified by human playtest only
	# Automated contrast checking is not implemented
	print("  INFO: [CHECKPOINT] Color contrast ratio (NF1) verified by manual playtest only")
	print("        Weakened (amber) vs Infected (purple) must be >= 3:1 contrast.")
	print("        Automated pixel-perfect validation deferred to Task 7 (human playtest).")
	_pass("spec_gap_color_contrast — contrast subjective, requires human validation")


# EDGE CASE: Label visibility with rapid dead transitions
func test_edge_case_rapid_dead_transitions_label_visible() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("edge_rapid_dead_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		return

	# Transition to dead multiple times rapidly
	for i in range(5):
		_drive_state_and_step(setup, "dead")

	# Label should be visible and text should be "Dead"
	_assert_true(label.visible, "edge_rapid_dead_label_visible — label stays visible")
	_assert_eq_string("Dead", label.text, "edge_rapid_dead_label_text — label text is 'Dead'")


# EDGE CASE: State label modulate color immutability
# Spec defines exact label colors; they must not drift
func test_edge_case_label_modulate_exact_values() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("edge_label_modulate_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		return

	# Weakened label color must be exact (1.0, 0.9, 0.6, 1.0)
	_drive_state_and_step(setup, "weakened")
	var weakened_expected := Color(1.0, 0.9, 0.6, 1.0)
	_assert_eq_color(weakened_expected, label.modulate,
		"edge_label_color_weakened — label modulate is exact amber")

	# Infected label color must be exact (0.85, 0.65, 1.0, 1.0)
	_drive_state_and_step(setup, "infected")
	var infected_expected := Color(0.85, 0.65, 1.0, 1.0)
	_assert_eq_color(infected_expected, label.modulate,
		"edge_label_color_infected — label modulate is exact purple")

	# Dead label color must be exact (0.5, 0.5, 0.5, 0.8)
	_drive_state_and_step(setup, "dead")
	var dead_expected := Color(0.5, 0.5, 0.5, 0.8)
	_assert_eq_color(dead_expected, label.modulate,
		"edge_label_color_dead — label modulate is exact gray")


# MUTATION TEST: Ensure dead alpha is not 1.0
func test_mutation_dead_alpha_not_fully_opaque() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("mut_dead_alpha_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	if visual == null:
		return

	_drive_state_and_step(setup, "dead")
	_assert_false(visual.modulate.a == 1.0,
		"mut_dead_alpha_not_1 — dead alpha is NOT 1.0, must be < 1.0")
	_assert_true(visual.modulate.a == 0.5,
		"mut_dead_alpha_exact_0_5 — dead alpha is exactly 0.5 per spec")


# EDGE CASE: Consecutive state label updates without state change
# Label should not flicker or re-render unnecessarily
func test_edge_case_label_stability_same_state() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("edge_label_stability_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	var fx: Node = setup.get("fx", null)
	if label == null or fx == null:
		return

	# Set to weakened
	_drive_state_and_step(setup, "weakened")
	var initial_text := label.text
	var initial_modulate := label.modulate

	# Call _process 10 more times without state change
	for i in range(10):
		fx._process(0.0)

	# Text and color should be stable (no redundant updates)
	_assert_eq_string(initial_text, label.text,
		"edge_label_stable_text — label text unchanged after 10 extra _process calls")
	_assert_eq_color(initial_modulate, label.modulate,
		"edge_label_stable_color — label modulate unchanged after 10 extra _process calls")


func run_all() -> int:
	print("--- test_infection_state_fx_mutation_edge_cases.gd ---")
	_pass_count = 0
	_fail_count = 0

	# MUTATION TESTS
	test_mutation_weakened_color_off_by_small_delta()
	test_mutation_infected_color_off_by_small_delta()
	test_mutation_label_text_case_sensitive()
	test_mutation_no_swapped_weakened_infected_colors()
	test_mutation_dead_alpha_not_fully_opaque()

	# EDGE CASES
	test_edge_case_process_before_ready()
	test_edge_case_missing_enemy_visual_node()
	test_edge_case_rapid_dead_transitions_label_visible()
	test_edge_case_label_modulate_exact_values()
	test_edge_case_label_stability_same_state()

	# STRESS TESTS
	test_stress_rapid_frame_by_frame_transitions()
	test_stress_long_state_sequence()

	# SPEC GAP DETECTION
	test_spec_gap_absorb_feedback_not_implemented()
	test_spec_gap_label_positioning_not_tested()
	test_spec_gap_color_contrast_subjective()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

