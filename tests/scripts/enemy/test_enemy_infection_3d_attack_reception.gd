#
# Headless tests: EnemyInfection3D exposes attack-executor damage contract
# (enemies group, take_damage, get_base_state) for sandbox verification.

extends "res://tests/utils/test_utils.gd"

const _ENEMY_SCRIPT_PATH: String = "res://scripts/enemy/enemy_infection_3d.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func _make_enemy() -> CharacterBody3D:
	var script_res: GDScript = load(_ENEMY_SCRIPT_PATH) as GDScript
	if script_res == null:
		_fail("setup", "could not load enemy_infection_3d.gd")
		return null
	var enemy: CharacterBody3D = script_res.new() as CharacterBody3D
	if enemy == null:
		_fail("setup", "could not instantiate EnemyInfection3D")
		return null
	return enemy


func test_enemy_infection_joins_enemies_group_on_ready() -> void:
	var enemy: CharacterBody3D = _make_enemy()
	if enemy == null:
		return
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(enemy)
	enemy._ready()
	_assert_true(enemy.is_in_group("enemies"), "infection_enemy_in_enemies_group")
	enemy.free()


func test_take_damage_weakens_esm_at_half_hp() -> void:
	var enemy: CharacterBody3D = _make_enemy()
	if enemy == null:
		return
	enemy.max_hp = 10.0
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(enemy)
	enemy._ready()
	enemy.take_damage(6.0, Vector3.ZERO)
	var esm: EnemyStateMachine = enemy.get_esm()
	_assert_eq(esm.get_state(), EnemyStateMachine.STATE_WEAKENED, "take_damage_weakens_esm")
	_assert_eq(enemy.get_base_state(), 1, "get_base_state_weakened")
	enemy.free()


func test_get_base_state_infected_matches_esm() -> void:
	var enemy: CharacterBody3D = _make_enemy()
	if enemy == null:
		return
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	tree.root.add_child(enemy)
	enemy._ready()
	var esm: EnemyStateMachine = enemy.get_esm()
	esm.apply_weaken_event()
	esm.apply_infection_event()
	_assert_eq(enemy.get_base_state(), 2, "get_base_state_infected")
	enemy.free()


func run_all() -> int:
	_pass_count = 0
	_fail_count = 0
	test_enemy_infection_joins_enemies_group_on_ready()
	test_take_damage_weakens_esm_at_half_hp()
	test_get_base_state_infected_matches_esm()
	return _fail_count
