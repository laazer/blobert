#
# test_infection_state_fx.gd
#
# Primary behavioral tests for infection state FX wiring. Verifies that
# infection_state_fx.gd reacts to EnemyStateMachine state by updating enemy
# visuals and optional state label text, without introducing new gameplay
# logic. Covers minimal R5 plumbing of the infection loop into presentation.
#
# Ticket: infection_interaction.md
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
		_assert_true(visual.modulate == Color(1.0, 1.0, 1.0, 1.0),
			"inf_fx_idle_visual_default — idle uses default white modulate")
	if label != null:
		_assert_true(not label.visible,
			"inf_fx_idle_label_hidden — state label hidden for idle/active states")


func test_weakened_state_tints_visual_and_shows_weakened_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_weakened_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "weakened")

	if visual != null:
		_assert_true(visual.modulate != Color(1.0, 1.0, 1.0, 1.0),
			"inf_fx_weakened_visual_tinted — weakened visual differs from idle/default")
	if label != null:
		_assert_true(label.visible,
			"inf_fx_weakened_label_visible — state label visible for weakened")
		_assert_eq_string("Weakened", label.text,
			"inf_fx_weakened_label_text — state label text is 'Weakened'")


func test_infected_state_tints_visual_and_shows_infected_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_infected_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "infected")

	if visual != null:
		_assert_true(visual.modulate != Color(1.0, 1.0, 1.0, 1.0),
			"inf_fx_infected_visual_tinted — infected visual differs from idle/default")
	if label != null:
		_assert_true(label.visible,
			"inf_fx_infected_label_visible — state label visible for infected")
		_assert_eq_string("Infected", label.text,
			"inf_fx_infected_label_text — state label text is 'Infected'")


func test_dead_state_darkens_visual_and_shows_dead_label() -> void:
	var setup := _make_fx_setup()
	if setup.is_empty():
		_fail("inf_fx_dead_setup", "could not create EnemyInfection + infection_state_fx setup")
		return

	var visual: CanvasItem = setup.get("visual", null)
	var label: Label = setup.get("label", null)

	_drive_state_and_step(setup, "dead")

	if visual != null:
		_assert_true(visual.modulate.a < 1.0,
			"inf_fx_dead_visual_dimmed — dead visual alpha < 1 for dim/hidden effect")
	if label != null:
		_assert_true(label.visible,
			"inf_fx_dead_label_visible — state label visible for dead")
		_assert_eq_string("Dead", label.text,
			"inf_fx_dead_label_text — state label text is 'Dead'")


func run_all() -> int:
	print("--- test_infection_state_fx.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_idle_state_uses_default_visual_and_hides_label()
	test_weakened_state_tints_visual_and_shows_weakened_label()
	test_infected_state_tints_visual_and_shows_infected_label()
	test_dead_state_darkens_visual_and_shows_dead_label()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

