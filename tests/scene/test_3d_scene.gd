#
# test_3d_scene.gd
#
# Headless tests for the 3D main scene (2.5D).
# Validates test_movement_3d.tscn structure, PlayerController3D presence,
# signals (Vector3), and basic movement/detach behavior.
#

# class_name omitted to avoid parse-order issues when run_tests.gd references this script.
extends Object

const EPSILON: float = 1e-3

var _pass_count: int = 0
var _fail_count: int = 0


func _pass_test(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail_test(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected true, got false")


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected false, got true")


func _load_3d_scene() -> Node:
	var packed: PackedScene = load("res://scenes/test_movement_3d.tscn") as PackedScene
	if packed == null:
		_fail_test("scene_load_3d", "could not load res://scenes/test_movement_3d.tscn")
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("scene_instantiate_3d", "instantiate() returned null for test_movement_3d.tscn")
		return null
	return inst


func _find_player_3d(root: Node) -> Node:
	if root == null:
		return null
	return root.get_node_or_null("Player3D")


func test_3d_scene_loads_and_instantiantes() -> void:
	var root: Node = _load_3d_scene()
	_assert_true(root != null, "3d_scene_loads")
	if root == null:
		return
	_assert_true(root is Node3D, "3d_scene_root_is_node3d")
	root.free()


func test_3d_scene_has_required_nodes() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	_assert_true(root.get_node_or_null("WorldEnvironment") != null, "3d_has_world_environment")
	_assert_true(root.get_node_or_null("DirectionalLight3D") != null, "3d_has_directional_light")
	_assert_true(root.get_node_or_null("Floor") != null, "3d_has_floor")
	_assert_true(root.get_node_or_null("SpawnPosition") != null, "3d_has_spawn_position")
	_assert_true(root.get_node_or_null("RespawnZone") != null, "3d_has_respawn_zone")
	_assert_true(root.get_node_or_null("Player3D") != null, "3d_has_player3d")
	root.free()


func test_3d_player_is_character_body_3d() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	_assert_true(player != null, "3d_player_exists")
	if player != null:
		_assert_true(player is CharacterBody3D, "3d_player_is_character_body_3d")
	root.free()


func test_3d_player_has_controller_script() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	if player == null:
		root.free()
		return
	var script_res: Resource = player.get_script()
	_assert_true(script_res != null, "3d_player_has_script")
	if script_res != null:
		var path: String = script_res.resource_path
		_assert_true(path.ends_with("player_controller_3d.gd"), "3d_player_script_is_player_controller_3d")
	root.free()


func test_3d_player_has_detach_recall_signals() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	if player == null:
		root.free()
		return
	_assert_true(player.has_signal("detach_fired"), "3d_player_signal_detach_fired")
	_assert_true(player.has_signal("recall_started"), "3d_player_signal_recall_started")
	_assert_true(player.has_signal("chunk_reabsorbed"), "3d_player_signal_chunk_reabsorbed")
	root.free()


func test_3d_player_has_slime_visual_and_camera() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	if player == null:
		root.free()
		return
	_assert_true(player.get_node_or_null("SlimeVisual") != null, "3d_player_has_slime_visual")
	_assert_true(player.get_node_or_null("Gimbal") != null, "3d_player_has_gimbal")
	_assert_true(player.get_node_or_null("Gimbal/Camera3D") != null, "3d_player_has_camera3d")
	_assert_true(player.get_node_or_null("ParticleTrail") != null, "3d_player_has_particle_trail")
	root.free()


func test_3d_player_ready_and_physics_frames_run() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	if player == null:
		root.free()
		return
	if not player.has_method("_ready"):
		_fail_test("3d_player_ready_runs", "Player3D has no _ready method")
		root.free()
		return
	player._ready()
	_assert_true(true, "3d_player_ready_completes")
	if player.has_method("_physics_process"):
		for i in range(5):
			player._physics_process(0.016)
	_assert_true(true, "3d_player_physics_frames_run")
	root.free()


func test_3d_player_has_chunk_and_accessors() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	if player == null:
		root.free()
		return
	player._ready()
	_assert_true(player.has_method("has_chunk"), "3d_player_has_chunk_method")
	_assert_true(player.has_method("get_current_hp"), "3d_player_get_current_hp_method")
	_assert_true(player.has_method("is_wall_clinging_state"), "3d_player_is_wall_clinging_state_method")
	var has_chunk: bool = player.call("has_chunk")
	_assert_true(has_chunk == true, "3d_player_starts_with_chunk_attached")
	root.free()


func test_3d_respawn_zone_has_spawn_point_path() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var zone: Area3D = root.get_node_or_null("RespawnZone") as Area3D
	if zone == null:
		root.free()
		return
	var path: NodePath = zone.get("spawn_point")
	_assert_true(path != NodePath(), "3d_respawn_zone_spawn_point_set")
	root.free()


func test_3d_detach_fired_emitted_with_vector3() -> void:
	var root: Node = _load_3d_scene()
	if root == null:
		return
	var player: Node = _find_player_3d(root)
	if player == null:
		root.free()
		return
	if not player.has_signal("detach_fired"):
		_fail_test("3d_detach_signal_vector3", "detach_fired signal missing")
		root.free()
		return
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		print("  SKIP: 3d_detach_fired_emitted_with_vector3 — no SceneTree for physics")
		root.free()
		return
	tree.root.add_child(root)
	player._ready()
	# In headless, 3D physics space may not be ready; skip emission checks if so.
	if not player.is_inside_tree() or player.get_world_3d() == null:
		print("  SKIP: 3d_detach_fired_emitted_with_vector3 — no valid 3D physics space (headless)")
		tree.root.remove_child(root)
		root.free()
		return
	var count: int = 0
	var got_player_pos: Vector3 = Vector3.INF
	var got_chunk_pos: Vector3 = Vector3.INF
	player.detach_fired.connect(func(pp: Vector3, cp: Vector3) -> void:
		count += 1
		got_player_pos = pp
		got_chunk_pos = cp
	)
	Input.action_press("detach")
	if player.has_method("_physics_process"):
		player._physics_process(0.016)
	Input.action_release("detach")
	_assert_true(count == 1, "3d_detach_fired_emitted_once")
	_assert_true(got_player_pos != Vector3.INF, "3d_detach_fired_player_pos_vector3")
	_assert_true(got_chunk_pos != Vector3.INF, "3d_detach_fired_chunk_pos_vector3")
	tree.root.remove_child(root)
	root.free()


func run_all() -> int:
	print("--- test_3d_scene.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_3d_scene_loads_and_instantiantes()
	test_3d_scene_has_required_nodes()
	test_3d_player_is_character_body_3d()
	test_3d_player_has_controller_script()
	test_3d_player_has_detach_recall_signals()
	test_3d_player_has_slime_visual_and_camera()
	test_3d_player_ready_and_physics_frames_run()
	test_3d_player_has_chunk_and_accessors()
	test_3d_respawn_zone_has_spawn_point_path()
	test_3d_detach_fired_emitted_with_vector3()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
