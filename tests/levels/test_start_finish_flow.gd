#
# test_start_finish_flow.gd
#
# Start→Finish flow integration checks for Milestone 4 Prototype Level.
#
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/start_finish_flow.md
#
# Headless safety:
# - No physics tick, no await, no input simulation, no signal emission.
# - Scene is instantiated but not added to the SceneTree (unless a test explicitly
#   requires _ready(), which this file intentionally avoids).
#
# What this test suite CAN verify from the available spec:
# - The level scene contains all scope items (mutation tease, fusion opportunity,
#   light skill check, mini-boss) and the start/end markers (SpawnPosition, LevelExit).
# - Cross-zone progression order is consistent along the X axis.
# - `LevelExit` is wired to call `level_complete` (via script source_code or a
#   compiled-method fallback).
#
# What this suite cannot verify (spec gap):
# - Actual human completion time (6–8 minutes) and actual input-driven playthrough.
#   Headless tests in this repo are intentionally structural/deterministic.
#
extends Object

const LEVEL_SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"
const GAME_UI_PATH: String = "res://scenes/ui/game_ui.tscn"

var _pass_count: int = 0
var _fail_count: int = 0

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)

func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)

func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, fail_msg)

func _assert_eq_float(expected: float, actual: float, test_name: String) -> void:
	if absf(actual - expected) < 0.0001:
		_pass(test_name)
	else:
		_fail(test_name, "expected " + str(expected) + ", got " + str(actual))

func _load_packed_scene(scene_path: String) -> PackedScene:
	return load(scene_path) as PackedScene

func _load_level_scene() -> Node:
	var packed: PackedScene = _load_packed_scene(LEVEL_SCENE_PATH)
	_assert_true(packed != null, "stf_scene_load_guard", "ResourceLoader.load returned null for " + LEVEL_SCENE_PATH)
	if packed == null:
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("stf_scene_instantiate_guard", "instantiate() returned null for " + LEVEL_SCENE_PATH)
		return null
	return inst

func _load_game_ui() -> Node:
	var packed: PackedScene = _load_packed_scene(GAME_UI_PATH)
	if packed == null:
		_fail("stf_game_ui_load_guard", "ResourceLoader.load returned null for " + GAME_UI_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail("stf_game_ui_instantiate_guard", "instantiate() returned null for " + GAME_UI_PATH)
		return null
	return inst

func _get_first_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null

func _require_box_shape_collision_shape(node: Node, test_name_prefix: String) -> BoxShape3D:
	var col: CollisionShape3D = _get_first_collision_shape(node)
	if col == null:
		_fail(test_name_prefix + "_has_collision_shape", "Missing CollisionShape3D child on " + str(node))
		return null
	if col.shape == null:
		_fail(test_name_prefix + "_shape_nonnull", "CollisionShape3D.shape is null on " + str(node))
		return null
	if not (col.shape is BoxShape3D):
		_fail(
			test_name_prefix + "_shape_is_box",
			"CollisionShape3D.shape is " + col.shape.get_class() + ", expected BoxShape3D"
		)
		return null
	return col.shape as BoxShape3D

func _world_x_edges_for_box(node: Node, test_name_prefix: String) -> Dictionary:
	# Returns {left: float, right: float}
	var box: BoxShape3D = _require_box_shape_collision_shape(node, test_name_prefix)
	if box == null:
		return {}

	var col: CollisionShape3D = _get_first_collision_shape(node)
	if col == null:
		return {}

	var n3: Node3D = node as Node3D
	var center_x: float = n3.position.x + col.position.x
	var half_w: float = box.size.x * 0.5
	return {
		"left": center_x - half_w,
		"right": center_x + half_w,
	}

func _require_node(root: Node, node_name: String, test_name: String, expected_class: String = "") -> Node:
	var node: Node = root.get_node_or_null(node_name)
	_assert_true(node != null, test_name, node_name + " node not found in level scene")
	if node == null:
		return null
	if expected_class != "":
		_assert_true(node.get_class() == expected_class, test_name + "_class", "Expected class " + expected_class + ", got " + node.get_class())
	return node

func test_stf_loads_and_has_core_nodes() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# Start marker + player.
	_require_node(root, "SpawnPosition", "stf_spawn_position_exists", "Marker3D")
	_require_node(root, "Player3D", "stf_player3d_exists", "CharacterBody3D")

	# UI and environment (human-playable editor requirement).
	_assert_true(root.get_node_or_null("InfectionUI") != null, "stf_infection_ui_exists", "InfectionUI node missing (game_ui.tscn expected to be instanced)")
	_assert_true(root.get_node_or_null("WorldEnvironment") != null, "stf_world_environment_exists", "WorldEnvironment node missing")
	_assert_true(root.get_node_or_null("DirectionalLight3D") != null, "stf_directional_light_exists", "DirectionalLight3D node missing")

	# Integration: all scope items and end marker exist.
	var required_nodes: Array[String] = [
		# Mutation tease
		"MutationTeaseFloor",
		"MutationTeasePlatform",
		"EnemyMutationTease",
		# Fusion opportunity
		"FusionFloor",
		"FusionPlatformA",
		"FusionPlatformB",
		"EnemyFusionA",
		"EnemyFusionB",
		"InfectionInteractionHandler",
		# Light skill check
		"SkillCheckFloorBase",
		"SkillCheckPlatform1",
		"SkillCheckPlatform2",
		"SkillCheckPlatform3",
		"RespawnZone",
		# Mini-boss
		"MiniBossFloor",
		"EnemyMiniBoss",
		"ExitFloor",
		# End marker
		"LevelExit",
	]
	for node_name in required_nodes:
		_assert_true(root.get_node_or_null(node_name) != null, "stf_required_" + node_name.to_lower() + "_exists", "Required node '" + node_name + "' missing")

	# Game UI should be loadable (required for visible/signposting).
	var ui: Node = _load_game_ui()
	if ui != null:
		_assert_true(ui.get_class() == "CanvasLayer", "stf_game_ui_is_canvas_layer", "game_ui.tscn root is " + ui.get_class() + ", expected CanvasLayer")
		ui.free()

	root.free()

func test_stf_cross_zone_progression_ordering() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# Ensure adjacency/order along X ensures clear intended traversal:
	# - MutationTeaseFloor precedes FusionFloor.
	# - SkillCheckPlatform1 begins after FusionPlatformB.
	# - MiniBossFloor begins after SkillCheckPlatform3.
	# - ExitFloor begins after MiniBossFloor's right edge.
	#
	# These invariants are the strictest defensible "flow direction/signposting"
	# checks we can do without input-driven playthrough.

	var mutation_tease_floor: Node = root.get_node_or_null("MutationTeaseFloor")
	var fusion_floor: Node = root.get_node_or_null("FusionFloor")
	_assert_true(mutation_tease_floor != null, "stf_order_mutation_tease_floor_exists")
	_assert_true(fusion_floor != null, "stf_order_fusion_floor_exists")
	if mutation_tease_floor == null or fusion_floor == null:
		root.free()
		return

	var edges_m: Dictionary = _world_x_edges_for_box(mutation_tease_floor, "stf_mutation_tease_floor")
	var edges_f: Dictionary = _world_x_edges_for_box(fusion_floor, "stf_fusion_floor")
	_assert_true(edges_m.size() > 0 and edges_f.size() > 0, "stf_order_mutation_fusion_edges_computed", "Failed to compute box edges for MutationTeaseFloor/FusionFloor")
	if edges_m.size() == 0 or edges_f.size() == 0:
		root.free()
		return

	_assert_true(
		edges_m["right"] <= edges_f["left"],
		"stf_order_mutation_tease_precedes_fusion",
		"MutationTeaseFloor right edge (" + str(edges_m["right"]) + ") must be <= FusionFloor left edge (" + str(edges_f["left"]) + ")"
	)

	var fusion_platform_b: Node = root.get_node_or_null("FusionPlatformB")
	var skill_check_p1: Node = root.get_node_or_null("SkillCheckPlatform1")
	_assert_true(fusion_platform_b != null, "stf_order_fusion_platform_b_exists")
	_assert_true(skill_check_p1 != null, "stf_order_skill_check_platform1_exists")
	if fusion_platform_b == null or skill_check_p1 == null:
		root.free()
		return

	_assert_true(
		(skill_check_p1 as Node3D).position.x > (fusion_platform_b as Node3D).position.x,
		"stf_order_skill_check_after_fusion_platform_b",
		"SkillCheckPlatform1.x (" + str((skill_check_p1 as Node3D).position.x) + ") must be > FusionPlatformB.x (" + str((fusion_platform_b as Node3D).position.x) + ")"
	)

	var skill_check_p3: Node = root.get_node_or_null("SkillCheckPlatform3")
	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	_assert_true(skill_check_p3 != null, "stf_order_skill_check_platform3_exists")
	_assert_true(mini_boss_floor != null, "stf_order_mini_boss_floor_exists")
	if skill_check_p3 == null or mini_boss_floor == null:
		root.free()
		return

	_assert_true(
		(skill_check_p3 as Node3D).position.x < (mini_boss_floor as Node3D).position.x,
		"stf_order_mini_boss_after_skill_check_p3",
		"SkillCheckPlatform3.x (" + str((skill_check_p3 as Node3D).position.x) + ") must be < MiniBossFloor.x (" + str((mini_boss_floor as Node3D).position.x) + ")"
	)

	var exit_floor: Node = root.get_node_or_null("ExitFloor")
	_assert_true(exit_floor != null, "stf_order_exit_floor_exists")
	if exit_floor == null:
		root.free()
		return

	var edges_boss: Dictionary = _world_x_edges_for_box(mini_boss_floor, "stf_mini_boss_floor")
	_assert_true(edges_boss.size() > 0, "stf_order_boss_edges_computed", "Failed to compute MiniBossFloor box edges")
	if edges_boss.size() == 0:
		root.free()
		return

	_assert_true(
		(exit_floor as Node3D).position.x > edges_boss["right"],
		"stf_order_exit_floor_after_boss_arena",
		"ExitFloor.x (" + str((exit_floor as Node3D).position.x) + ") must be > MiniBossFloor right edge (" + str(edges_boss["right"]) + ")"
	)

	root.free()

func test_stf_level_exit_triggers_level_complete_wiring() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	_assert_true(level_exit != null, "stf_level_exit_exists")
	if level_exit == null:
		root.free()
		return

	_assert_level_exit_has_level_complete(level_exit)

	root.free()

# Helper to avoid duplication of wiring logic while keeping the test names consistent.
func _assert_level_exit_has_level_complete(level_exit: Node) -> void:
	_assert_true(level_exit is Area3D, "stf_level_exit_is_area3d_assertion", "LevelExit is " + level_exit.get_class() + ", expected Area3D")

	var col: CollisionShape3D = _get_first_collision_shape(level_exit)
	_assert_true(col != null, "stf_level_exit_has_collision_shape_assertion", "LevelExit has no CollisionShape3D child")
	if col == null:
		return
	_assert_true(col.shape != null and col.shape is BoxShape3D, "stf_level_exit_collision_shape_is_box_assertion", "LevelExit CollisionShape3D.shape is not BoxShape3D")

	var script_obj: Script = level_exit.get_script() as Script
	_assert_true(script_obj != null, "stf_level_exit_has_script_assertion", "LevelExit has no script attached")
	if script_obj == null:
		return

	var source: String = script_obj.source_code
	if source != null and source != "":
		_assert_true(
			source.contains("level_complete"),
			"stf_level_exit_source_contains_level_complete_assertion",
			"LevelExit script source_code does not contain 'level_complete'"
		)
	else:
		_assert_true(
			level_exit.has_method("_on_body_entered"),
			"stf_level_exit_has_on_body_entered_fallback_assertion",
			"LevelExit script.source_code is empty and _on_body_entered() is missing"
		)

func test_stf_respawn_zone_retry_wiring_exists() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	_assert_true(zone != null, "stf_respawn_zone_exists")
	if zone == null:
		root.free()
		return

	_assert_true(zone is Area3D, "stf_respawn_zone_is_area3d", "RespawnZone is " + zone.get_class() + ", expected Area3D")

	var script_res: Script = zone.get_script() as Script
	_assert_true(script_res != null, "stf_respawn_zone_has_script", "RespawnZone has no script attached")
	if script_res == null:
		root.free()
		return
	_assert_true(
		script_res.resource_path.contains("respawn_zone.gd"),
		"stf_respawn_zone_script_path_contains_respawn_zone_gd",
		"RespawnZone script resource_path '" + script_res.resource_path + "' does not contain 'respawn_zone.gd'"
	)

	var spawn_point_val = zone.get("spawn_point")
	_assert_true(
		spawn_point_val != null and String(spawn_point_val) != "",
		"stf_respawn_zone_spawn_point_nonempty",
		"RespawnZone.spawn_point is null or empty NodePath"
	)

	if spawn_point_val != null and String(spawn_point_val) != "":
		var resolved: Node = zone.get_node_or_null(spawn_point_val as NodePath)
		_assert_true(
			resolved != null,
			"stf_respawn_zone_spawn_point_resolves",
			"RespawnZone.spawn_point NodePath '" + str(spawn_point_val) + "' did not resolve to a node"
		)

	root.free()

func run_all() -> int:
	print("--- tests/levels/test_start_finish_flow.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ST-1: level loads and contains all required segments + end marker + UI hooks.
	test_stf_loads_and_has_core_nodes()

	# ST-2: cross-zone progression order across mutation → fusion → skill check → mini-boss → exit.
	test_stf_cross_zone_progression_ordering()

	# ST-3: LevelExit wiring includes level_complete path.
	test_stf_level_exit_triggers_level_complete_wiring()

	# ST-4: Respawn zone wiring exists (retry safety around skill check pit).
	test_stf_respawn_zone_retry_wiring_exists()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count

