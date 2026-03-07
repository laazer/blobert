#
# test_infection_state_fx.gd
#
# Primary behavioral tests for infection state FX wiring and visual feedback.
# Verifies that infection_state_fx.gd reacts to EnemyStateMachine state by
# updating enemy visuals and state label text according to the
# visual_feedback_infection specification. Tests validate:
#  - State-to-modulate mapping (idle, weakened, infected, dead)
#  - State label visibility and exact text content
#  - State label color tints
#  - Readability constraints (no null/undefined states)
#
# Ticket: visual_feedback_infection.md (Spec Agent revision 2)
#

class_name InfectionStateFxTests
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


func _assert_eq_string(expected: String, actual: String, test_name: String) -> void:
	if actual == expected:
		_pass(test_name)
	else:
		_fail(test_name, "expected '" + expected + "', got '" + actual + "'")


func _assert_eq_color(expected: Color, actual: Color, test_name: String, tolerance: float = 0.01) -> void:
	var color_diff: float = abs(expected.r - actual.r) + abs(expected.g - actual.g) + abs(expected.b - actual.b) + abs(expected.a - actual.a)
	if color_diff < tolerance:
		_pass(test_name)
	else:
		_fail(test_name, "expected Color(%.2f, %.2f, %.2f, %.2f), got Color(%.2f, %.2f, %.2f, %.2f)" % [expected.r, expected.g, expected.b, expected.a, actual.r, actual.g, actual.b, actual.a])


func _load_enemy_infection_script() -> GDScript:
	return load("res://scripts/enemy_infection.gd") as GDScript


func _load_infection_state_fx_script() -> GDScript:
	return load("res://scripts/infection_state_fx.gd") as GDScript


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

	# Wire EnemyInfection (creates EnemyStateMachine) and FX script.
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


func test_idle_state_uses_default_visual_and_hides_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_idle_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "idle")

	if visual != null:
		_assert_eq_color(Color(1.0, 1.0, 1.0, 1.0), visual.modulate,
			"inf_fx_idle_visual_default — idle uses default white modulate (F3)")
	if label != null:
		_assert_true(not label.visible,
			"inf_fx_idle_label_hidden — state label hidden for idle/active states (F3)")


func test_weakened_state_tints_visual_and_shows_weakened_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_weakened_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "weakened")

	if visual != null:
		_assert_eq_color(Color(1.0, 0.85, 0.5, 1.0), visual.modulate,
			"inf_fx_weakened_visual_amber — weakened applies amber/tan tint (F1, NF5)")
	if label != null:
		_assert_true(label.visible,
			"inf_fx_weakened_label_visible — state label visible for weakened (F1)")
		_assert_eq_string("Weakened", label.text,
			"inf_fx_weakened_label_text — state label text is exactly 'Weakened' (F1, NF4)")


func test_infected_state_tints_visual_and_shows_infected_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_infected_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "infected")

	if visual != null:
		_assert_eq_color(Color(0.75, 0.5, 1.0, 1.0), visual.modulate,
			"inf_fx_infected_visual_purple — infected applies purple/violet tint (F2, NF5)")
	if label != null:
		_assert_true(label.visible,
			"inf_fx_infected_label_visible — state label visible for infected (F2)")
		_assert_eq_string("Infected", label.text,
			"inf_fx_infected_label_text — state label text is exactly 'Infected' (F2, NF4)")


func test_dead_state_darkens_visual_and_shows_dead_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_dead_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "dead")

	if visual != null:
		_assert_eq_color(Color(0.25, 0.25, 0.25, 0.5), visual.modulate,
			"inf_fx_dead_visual_dimmed — dead applies dark gray dimmed tint (F4, NF5)")
	if label != null:
		_assert_true(label.visible,
			"inf_fx_dead_label_visible — state label visible for dead (F4)")
		_assert_eq_string("Dead", label.text,
			"inf_fx_dead_label_text — state label text is exactly 'Dead' (F4, NF4)")


func test_weakened_and_infected_colors_are_visually_distinct() -> void:
	var setup1 := _make_fx_setup()
	var setup2 := _make_fx_setup()
	if setup1.is_empty() or setup2.is_empty():
		_fail("inf_fx_distinct_setup", "could not create two test setups")
		return

	var visual1: CanvasItem = setup1.get("visual", null)
	var visual2: CanvasItem = setup2.get("visual", null)

	_drive_state_and_step(setup1, "weakened")
	_drive_state_and_step(setup2, "infected")

	if visual1 != null and visual2 != null:
		# Weakened (1.0, 0.85, 0.5) vs Infected (0.75, 0.5, 1.0)
		# Should be visually distinct, not equal
		_assert_true(visual1.modulate != visual2.modulate,
			"inf_fx_distinct_colors — weakened amber and infected purple are different (F2, AC2)")


func test_state_label_colors_match_spec() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_label_colors_setup", "could not create setup")
		return

	var label: Label = setup.get("label", null)
	if label == null:
		_fail("inf_fx_label_colors", "label is null")
		return

	# Test weakened label color
	_drive_state_and_step(setup, "weakened")
	_assert_eq_color(Color(1.0, 0.9, 0.6, 1.0), label.modulate,
		"inf_fx_weakened_label_color — weakened label is light amber (F1)")

	# Test infected label color
	_drive_state_and_step(setup, "infected")
	_assert_eq_color(Color(0.85, 0.65, 1.0, 1.0), label.modulate,
		"inf_fx_infected_label_color — infected label is light purple (F2)")

	# Test dead label color
	_drive_state_and_step(setup, "dead")
	_assert_eq_color(Color(0.5, 0.5, 0.5, 0.8), label.modulate,
		"inf_fx_dead_label_color — dead label is medium gray (F4)")


func test_state_transitions_update_visuals_reactively() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_transitions_setup", "could not create setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)
	if visual == null or label == null:
		return

	# Start idle
	_drive_state_and_step(setup, "idle")
	var idle_modulate := visual.modulate
	var idle_label_visible := label.visible

	# Transition to weakened
	_drive_state_and_step(setup, "weakened")
	var weakened_modulate := visual.modulate
	var weakened_label_visible := label.visible

	_assert_true(idle_modulate != weakened_modulate,
		"inf_fx_idle_to_weakened_visual — visual changes on transition (NF3)")
	_assert_true(not idle_label_visible and weakened_label_visible,
		"inf_fx_idle_to_weakened_label — label becomes visible on transition (NF3)")

	# Transition to infected
	_drive_state_and_step(setup, "infected")
	var infected_modulate := visual.modulate

	_assert_true(weakened_modulate != infected_modulate,
		"inf_fx_weakened_to_infected_visual — visual changes on transition (NF3)")

	# Transition to dead
	_drive_state_and_step(setup, "dead")
	var dead_modulate := visual.modulate

	_assert_true(infected_modulate != dead_modulate,
		"inf_fx_infected_to_dead_visual — visual changes on transition (NF3)")


func test_modulate_for_state_returns_correct_colors() -> void:
	var fx_script: GDScript = load("res://scripts/infection_state_fx.gd") as GDScript
	if fx_script == null:
		_fail("inf_fx_modulate_func_load", "could not load infection_state_fx.gd")
		return

	var fx: Node = fx_script.new()
	if not fx.has_method("_modulate_for_state"):
		_fail("inf_fx_modulate_func_exists", "infection_state_fx does not have _modulate_for_state")
		return

	# Test idle
	var idle_color = fx._modulate_for_state("idle")
	_assert_eq_color(Color(1.0, 1.0, 1.0, 1.0), idle_color,
		"inf_fx_modulate_idle — _modulate_for_state('idle') returns white (F3)")

	# Test weakened
	var weakened_color = fx._modulate_for_state("weakened")
	_assert_eq_color(Color(1.0, 0.85, 0.5, 1.0), weakened_color,
		"inf_fx_modulate_weakened — _modulate_for_state('weakened') returns amber (F1)")

	# Test infected
	var infected_color = fx._modulate_for_state("infected")
	_assert_eq_color(Color(0.75, 0.5, 1.0, 1.0), infected_color,
		"inf_fx_modulate_infected — _modulate_for_state('infected') returns purple (F2)")

	# Test dead
	var dead_color = fx._modulate_for_state("dead")
	_assert_eq_color(Color(0.25, 0.25, 0.25, 0.5), dead_color,
		"inf_fx_modulate_dead — _modulate_for_state('dead') returns dark gray (F4)")

	# Test unknown state (should return white/idle)
	var unknown_color = fx._modulate_for_state("unknown")
	_assert_eq_color(Color(1.0, 1.0, 1.0, 1.0), unknown_color,
		"inf_fx_modulate_unknown — _modulate_for_state(unknown) returns white default (F3)")


func run_all() -> int:
	print("--- test_infection_state_fx.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_idle_state_uses_default_visual_and_hides_label()
	test_weakened_state_tints_visual_and_shows_weakened_label()
	test_infected_state_tints_visual_and_shows_infected_label()
	test_dead_state_darkens_visual_and_shows_dead_label()
	test_weakened_and_infected_colors_are_visually_distinct()
	test_state_label_colors_match_spec()
	test_state_transitions_update_visuals_reactively()
	test_modulate_for_state_returns_correct_colors()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

