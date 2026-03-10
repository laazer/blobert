#
# test_infection_state_fx_adversarial.gd
#
# Adversarial behavioral tests for infection state FX. Covers edge cases and
# stress scenarios to ensure robustness:
#  - Repeated state transitions (idempotent transitions)
#  - Rapid state changes (slow FX wiring does not cause glitches)
#  - State label handling under edge cases (null labels, missing nodes)
#  - Visual feedback under invalid/unknown states
#  - Scene graph integrity (no orphaned nodes or double-updates)
#
# Ticket: visual_feedback_infection.md (Test Breaker Agent)
#

class_name InfectionStateFxAdversarialTests
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


# Test: Repeated weaken transitions should be idempotent (no visual glitches)
func test_repeated_weaken_transitions_are_stable() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_repeated_weaken_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)
	if visual == null or label == null:
		return

	var expected_color := Color(1.0, 0.85, 0.5, 1.0)

	# Apply weakened 3 times in a row
	for i in range(3):
		_drive_state_and_step(setup, "weakened")

	_assert_eq_color(expected_color, visual.modulate,
		"inf_fx_adv_repeated_weaken_color — color stable after 3x transitions")
	_assert_eq_string("Weakened", label.text,
		"inf_fx_adv_repeated_weaken_text — label text stable after 3x transitions")


# Test: Rapid state transitions should update visuals without lag
func test_rapid_state_transitions_update_correctly() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_rapid_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)
	if visual == null or label == null:
		return

	# Rapid sequence: idle -> weakened -> infected -> dead
	_drive_state_and_step(setup, "idle")
	_drive_state_and_step(setup, "weakened")
	_drive_state_and_step(setup, "infected")
	_drive_state_and_step(setup, "dead")

	_assert_eq_color(Color(0.25, 0.25, 0.25, 0.5), visual.modulate,
		"inf_fx_adv_rapid_final_color — rapid transition ends at dead color")
	_assert_eq_string("Dead", label.text,
		"inf_fx_adv_rapid_final_text — rapid transition ends at dead label")


# Test: Null label should not crash; FX should degrade gracefully
func test_missing_label_node_does_not_crash() -> void:
	var enemy_script: GDScript = _load_enemy_infection_script()
	var fx_script: GDScript = _load_infection_state_fx_script()
	if enemy_script == null or fx_script == null:
		_fail("inf_fx_adv_no_label_setup", "could not load scripts")
		return

	var enemy_node: Node2D = enemy_script.new() as Node2D
	if enemy_node == null:
		_fail("inf_fx_adv_no_label_setup", "could not create enemy")
		return

	var visual := ColorRect.new()
	visual.name = "EnemyVisual"
	var fx_node: Node = fx_script.new()

	enemy_node.add_child(visual)
	enemy_node.add_child(fx_node)
	# NOTE: No label added; _update_state_label should handle null gracefully

	if enemy_node.has_method("_ready"):
		enemy_node._ready()
	if fx_node.has_method("_ready"):
		fx_node._ready()

	var esm: EnemyStateMachine = null
	if enemy_node.has_method("get_esm"):
		esm = enemy_node.get_esm()

	if esm == null:
		_fail("inf_fx_adv_no_label_esm", "esm is null")
		return

	# Transition to weakened; should not crash even without label
	esm.reset()
	esm.apply_weaken_event()
	fx_node._process(0.0)

	_assert_eq_color(Color(1.0, 0.85, 0.5, 1.0), visual.modulate,
		"inf_fx_adv_no_label_color — visual updates even without label (NF6)")

	_pass("inf_fx_adv_no_label_no_crash — missing label does not crash (NF6)")


# Test: Unknown/invalid states should default to idle appearance
func test_unknown_state_defaults_to_idle_appearance() -> void:
	var fx_script: GDScript = load("res://scripts/infection/infection_state_fx.gd") as GDScript
	if fx_script == null:
		_fail("inf_fx_adv_unknown_state_load", "could not load infection_state_fx.gd")
		return

	var fx: Node = fx_script.new()

	# Test several unknown states
	var unknown_states := ["active", "broken", "xyz", ""]
	for state in unknown_states:
		var color = fx._modulate_for_state(state)
		_assert_eq_color(Color(1.0, 1.0, 1.0, 1.0), color,
			"inf_fx_adv_unknown_state_" + state + " — unknown state '%s' defaults to white" % state)


# Test: Label visibility should follow state exactly (not accumulate or glitch)
func test_label_visibility_follows_state() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_label_visibility_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		return

	# Cycle: idle (hidden) -> weakened (visible) -> idle (hidden) -> infected (visible) -> idle (hidden)
	_drive_state_and_step(setup, "idle")
	_assert_true(not label.visible, "inf_fx_adv_label_vis_1 — idle hides label")

	_drive_state_and_step(setup, "weakened")
	_assert_true(label.visible, "inf_fx_adv_label_vis_2 — weakened shows label")

	_drive_state_and_step(setup, "idle")
	_assert_true(not label.visible, "inf_fx_adv_label_vis_3 — idle hides label again")

	_drive_state_and_step(setup, "infected")
	_assert_true(label.visible, "inf_fx_adv_label_vis_4 — infected shows label")

	_drive_state_and_step(setup, "idle")
	_assert_true(not label.visible, "inf_fx_adv_label_vis_5 — idle hides label again")


# Test: Dead alpha should always be < 1.0
func test_dead_state_always_has_reduced_alpha() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_dead_alpha_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	if visual == null:
		return

	_drive_state_and_step(setup, "dead")
	_assert_true(visual.modulate.a < 1.0 and visual.modulate.a >= 0.0,
		"inf_fx_adv_dead_alpha — dead state alpha is 0 < alpha < 1 (F4)")


# Test: Multiple state transitions in one frame should not cause duplicate updates
func test_no_duplicate_label_updates() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_dup_update_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		return

	# Set to weakened
	_drive_state_and_step(setup, "weakened")
	var first_text := label.text

	# Call _process again without changing state
	var fx: Node = setup.get("fx")
	fx._process(0.0)

	_assert_eq_string(first_text, label.text,
		"inf_fx_adv_dup_update — label text unchanged by extra _process call (NF3)")


# Test: Visual nodes should not be orphaned after state changes
func test_no_orphaned_visual_nodes() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_orphan_setup", "could not create setup")
		return

	var fx: Node = setup.get("fx")
	var enemy: Node = setup.get("enemy")
	if fx == null or enemy == null:
		return

	# Cycle through all states
	_drive_state_and_step(setup, "weakened")
	_drive_state_and_step(setup, "infected")
	_drive_state_and_step(setup, "dead")

	# FX node should still be a child of enemy
	_assert_true(fx.get_parent() == enemy,
		"inf_fx_adv_orphan_fx_parent — FX node remains child of enemy after transitions (NF6)")

	# Label should still be a child of FX
	var label: Label = setup.get("label")
	if label != null:
		_assert_true(label.get_parent() == fx,
			"inf_fx_adv_orphan_label_parent — label node remains child of FX after transitions (NF6)")


# Test: Color values should be exact (not approximate or interpolated mid-frame)
func test_color_values_are_exact() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_adv_exact_color_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	if visual == null:
		return

	# Check each state color is exact
	_drive_state_and_step(setup, "idle")
	var idle_exact := visual.modulate == Color(1.0, 1.0, 1.0, 1.0)

	_drive_state_and_step(setup, "weakened")
	var weakened_exact := visual.modulate == Color(1.0, 0.85, 0.5, 1.0)

	_drive_state_and_step(setup, "infected")
	var infected_exact := visual.modulate == Color(0.75, 0.5, 1.0, 1.0)

	_drive_state_and_step(setup, "dead")
	var dead_exact := visual.modulate == Color(0.25, 0.25, 0.25, 0.5)

	_assert_true(idle_exact and weakened_exact and infected_exact and dead_exact,
		"inf_fx_adv_exact_color_all — all color values are exact (NF5, F1–F4)")


# Test: Transition from any state to dead should apply dead visual
func test_any_state_to_dead_applies_dead_visual() -> void:
	var setup1 := _make_fx_setup()
	var setup2 := _make_fx_setup()
	var setup3 := _make_fx_setup()
	if setup1.is_empty() or setup2.is_empty() or setup3.is_empty():
		_fail("inf_fx_adv_any_to_dead_setup", "could not create setups")
		return

	var expected_dead := Color(0.25, 0.25, 0.25, 0.5)

	# idle -> dead
	_drive_state_and_step(setup1, "idle")
	setup1.get("esm").apply_death_event()
	setup1.get("fx")._process(0.0)
	_assert_eq_color(expected_dead, setup1.get("visual").modulate,
		"inf_fx_adv_idle_to_dead — idle -> dead applies dead color (NF3)")

	# weakened -> dead (direct, not through infected)
	_drive_state_and_step(setup2, "weakened")
	setup2.get("esm").apply_death_event()
	setup2.get("fx")._process(0.0)
	_assert_eq_color(expected_dead, setup2.get("visual").modulate,
		"inf_fx_adv_weakened_to_dead — weakened -> dead applies dead color (NF3)")

	# infected -> dead
	_drive_state_and_step(setup3, "infected")
	setup3.get("esm").apply_death_event()
	setup3.get("fx")._process(0.0)
	_assert_eq_color(expected_dead, setup3.get("visual").modulate,
		"inf_fx_adv_infected_to_dead — infected -> dead applies dead color (NF3)")


func run_all() -> int:
	print("--- test_infection_state_fx_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_repeated_weaken_transitions_are_stable()
	test_rapid_state_transitions_update_correctly()
	test_missing_label_node_does_not_crash()
	test_unknown_state_defaults_to_idle_appearance()
	test_label_visibility_follows_state()
	test_dead_state_always_has_reduced_alpha()
	test_no_duplicate_label_updates()
	test_no_orphaned_visual_nodes()
	test_color_values_are_exact()
	test_any_state_to_dead_applies_dead_visual()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

