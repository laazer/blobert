#
# test_infection_state_fx_3d.gd
#
# Behavioral tests for 3D infection state FX wiring. Verifies that
# infection_state_fx_3d.gd:
#   - reacts to EnemyStateMachine state transitions by briefly blinking the
#     EnemyVisual when the enemy takes damage (weaken/infect), and
#   - hides the enemy node when the state reaches "dead" (including via absorb),
# without introducing new gameplay logic.
#
# Ticket: infection_interaction.md (3D presentation subset)
#

class_name InfectionStateFx3DTests
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


func _load_enemy_infection_3d_script() -> GDScript:
	return load("res://scripts/enemy_infection_3d.gd") as GDScript


func _load_infection_state_fx_3d_script() -> GDScript:
	return load("res://scripts/infection_state_fx_3d.gd") as GDScript


func _make_fx_setup_3d() -> Dictionary:
	var enemy_script: GDScript = _load_enemy_infection_3d_script()
	var fx_script: GDScript = _load_infection_state_fx_3d_script()
	if enemy_script == null or fx_script == null:
		return {}

	var enemy_node: Node3D = enemy_script.new() as Node3D
	if enemy_node == null:
		return {}

	var visual := MeshInstance3D.new()
	visual.name = "EnemyVisual"
	var fx_node: Node3D = fx_script.new() as Node3D

	enemy_node.add_child(visual)
	enemy_node.add_child(fx_node)

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
		"fx": fx_node,
		"esm": esm,
	}


func _drive_state_and_step(setup: Dictionary, state: String, delta: float = 0.0) -> void:
	var esm: EnemyStateMachine = setup.get("esm", null)
	var fx: Node3D = setup.get("fx", null)
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

	fx._process(delta)


func test_damage_transition_triggers_temporary_blink() -> void:
	var setup := _make_fx_setup_3d()
	if setup.is_empty():
		_fail("inf_fx3d_blink_setup", "could not create EnemyInfection3D + infection_state_fx_3d setup")
		return

	var visual: MeshInstance3D = setup.get("visual", null)
	var fx: Node3D = setup.get("fx", null)
	var esm: EnemyStateMachine = setup.get("esm", null)
	if visual == null or fx == null or esm == null:
		_fail("inf_fx3d_blink_null_nodes", "setup missing visual, fx, or esm")
		return

	# Ensure a stable starting point.
	esm.reset()
	fx._process(0.0)
	var initial_visible: bool = visual.visible

	# Simulate damage: weaken + infect, then step FX once to observe state change.
	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	fx._process(0.0)

	var saw_toggle: bool = false
	for i in 10:
		fx._process(0.05)
		if visual.visible != initial_visible:
			saw_toggle = true
			break

	_assert_true(
		saw_toggle,
		"inf_fx3d_blink_on_damage — EnemyVisual visibility toggles at least once after damage transition"
	)


func test_dead_state_hides_enemy_node() -> void:
	var setup := _make_fx_setup_3d()
	if setup.is_empty():
		_fail("inf_fx3d_dead_setup", "could not create EnemyInfection3D + infection_state_fx_3d setup")
		return

	var enemy: Node3D = setup.get("enemy", null)
	var fx: Node3D = setup.get("fx", null)
	var esm: EnemyStateMachine = setup.get("esm", null)
	if enemy == null or fx == null or esm == null:
		_fail("inf_fx3d_dead_null_nodes", "setup missing enemy, fx, or esm")
		return

	# Precondition: enemy initially visible.
	enemy.visible = true

	esm.reset()
	esm.apply_death_event()
	fx._process(0.0)

	_assert_true(
		not enemy.visible,
		"inf_fx3d_dead_hides_enemy — enemy node is hidden after ESM enters 'dead' state"
	)


func test_absorb_path_also_hides_enemy_node() -> void:
	var setup := _make_fx_setup_3d()
	if setup.is_empty():
		_fail("inf_fx3d_absorb_setup", "could not create EnemyInfection3D + infection_state_fx_3d setup")
		return

	var enemy: Node3D = setup.get("enemy", null)
	var fx: Node3D = setup.get("fx", null)
	var esm: EnemyStateMachine = setup.get("esm", null)
	if enemy == null or fx == null or esm == null:
		_fail("inf_fx3d_absorb_null_nodes", "setup missing enemy, fx, or esm")
		return

	var resolver_script: GDScript = load("res://scripts/infection_absorb_resolver.gd") as GDScript
	if resolver_script == null:
		_fail("inf_fx3d_absorb_resolver_load", "could not load infection_absorb_resolver.gd")
		return

	var resolver: InfectionAbsorbResolver = resolver_script.new() as InfectionAbsorbResolver
	if resolver == null:
		_fail("inf_fx3d_absorb_resolver_instance", "could not instantiate InfectionAbsorbResolver")
		return

	var inventory := Object.new()
	inventory.set_script(load("res://scripts/mutation_inventory.gd"))

	# Drive to infected then resolve absorb.
	esm.reset()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	resolver.resolve_absorb(esm, inventory)
	fx._process(0.0)

	_assert_true(
		not enemy.visible,
		"inf_fx3d_absorb_hides_enemy — enemy node is hidden after absorb-driven death transition"
	)


func run_all() -> int:
	print("--- test_infection_state_fx_3d.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_damage_transition_triggers_temporary_blink()
	test_dead_state_hides_enemy_node()
	test_absorb_path_also_hides_enemy_node()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

