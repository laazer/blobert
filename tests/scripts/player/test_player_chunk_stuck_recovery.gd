#
# PlayerController3D recovers chunk slots when the stuck enemy is removed or dies.

extends "res://tests/utils/test_utils.gd"

const _CONTROLLER_PATH: String = "res://scripts/player/player_controller_3d.gd"
const _HANDLER_PATH: String = "res://scripts/infection/infection_interaction_handler.gd"
const _ENEMY_PATH: String = "res://scripts/enemy/enemy_infection_3d.gd"

var _pass_count: int = 0
var _fail_count: int = 0


func _build_scene() -> Dictionary:
	var ctrl_script: GDScript = load(_CONTROLLER_PATH) as GDScript
	var handler_script: GDScript = load(_HANDLER_PATH) as GDScript
	var enemy_script: GDScript = load(_ENEMY_PATH) as GDScript
	if ctrl_script == null or handler_script == null or enemy_script == null:
		_fail("chunk_recovery_scripts", "could not load player, handler, or enemy script")
		return {}
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail("chunk_recovery_tree", "no SceneTree")
		return {}
	var root: Node3D = Node3D.new()
	tree.root.add_child(root)
	var handler: Node = handler_script.new() as Node
	handler.name = "InfectionInteractionHandler"
	root.add_child(handler)
	var enemy: CharacterBody3D = enemy_script.new() as CharacterBody3D
	enemy.name = "TestEnemy"
	root.add_child(enemy)
	var player: CharacterBody3D = ctrl_script.new() as CharacterBody3D
	player.name = "Player3D"
	root.add_child(player)
	return {"root": root, "player": player, "enemy": enemy}


func _teardown(scene: Dictionary) -> void:
	var root: Variant = scene.get("root")
	if root != null and is_instance_valid(root):
		(root as Node).free()


func test_process_chunk_slot_aborts_when_stuck_enemy_missing() -> void:
	var scene: Dictionary = _build_scene()
	if scene.is_empty():
		return
	var player: CharacterBody3D = scene["player"]
	var chunk: RigidBody3D = RigidBody3D.new()
	chunk.add_to_group("chunk")
	scene["root"].add_child(chunk)
	player.set("_chunks", [chunk, null])
	player.set("_chunk_stuck", [true, false])
	player.set("_chunk_stuck_enemy", [null, null])
	player.set("_chunk_dot_ticks_remaining", [3, 0])
	player.set("_chunk_dot_time_accum", [0.0, 0.0])
	player.get("_current_state").has_chunks[0] = false
	player.call("_process_chunk_slot", 0, false, player.get("_current_state"), 0.016)
	var stuck: Array = player.get("_chunk_stuck")
	_assert_false(bool(stuck[0]), "chunk_stuck_cleared_when_stuck_enemy_null")
	_assert_true(bool(player.get("_recall_in_progress")[0]), "recall_started_after_abort")
	_teardown(scene)


func test_second_detach_press_starts_recall_while_e_still_held() -> void:
	var scene: Dictionary = _build_scene()
	if scene.is_empty():
		return
	var player: CharacterBody3D = scene["player"]
	var chunk: RigidBody3D = RigidBody3D.new()
	chunk.add_to_group("chunk")
	scene["root"].add_child(chunk)
	player.set("_chunks", [chunk, null])
	player.set("_detach_spawn_blocks_recall", [1, 0])
	player.get("_current_state").has_chunks[0] = false
	player.call("_process_chunk_slot", 0, true, player.get("_current_state"), 0.016)
	var recall_after_spawn_frame: Array = player.get("_recall_in_progress")
	_assert_false(
		bool(recall_after_spawn_frame[0]),
		"recall_blocked_on_detach_spawn_frame",
	)
	player.set("_detach_spawn_blocks_recall", [0, 0])
	player.call("_process_chunk_slot", 0, true, player.get("_current_state"), 0.016)
	recall_after_spawn_frame = player.get("_recall_in_progress")
	_assert_true(
		bool(recall_after_spawn_frame[0]),
		"recall_starts_on_second_detach_press_while_key_held",
	)
	_teardown(scene)


func test_apply_dot_step_aborts_on_dead_enemy() -> void:
	var scene: Dictionary = _build_scene()
	if scene.is_empty():
		return
	var player: CharacterBody3D = scene["player"]
	var enemy: EnemyInfection3D = scene["enemy"] as EnemyInfection3D
	player.set("_chunks", [RigidBody3D.new(), null])
	player.get("_chunks")[0].add_to_group("chunk")
	scene["root"].add_child(player.get("_chunks")[0])
	player.set("_chunk_stuck", [true, false])
	player.set("_chunk_stuck_enemy", [enemy, null])
	player.set("_chunk_dot_ticks_remaining", [3, 0])
	enemy.get_esm().apply_death_event()
	player.call("_apply_chunk_dot_step", 0)
	var stuck: Array = player.get("_chunk_stuck")
	_assert_false(bool(stuck[0]), "dot_step_aborts_when_enemy_dead")
	_teardown(scene)


func run_all() -> int:
	_pass_count = 0
	_fail_count = 0
	test_process_chunk_slot_aborts_when_stuck_enemy_missing()
	test_second_detach_press_starts_recall_while_e_still_held()
	test_apply_dot_step_aborts_on_dead_enemy()
	return _fail_count
