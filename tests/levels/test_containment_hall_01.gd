#
# test_containment_hall_01.gd
#
# Structural behavioral tests for the Containment Hall 01 scene.
# Spec: agent_context/agents/2_spec/containment_hall_01_spec.md
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/containment_hall_01_layout.md
#
# All tests are headless-safe: no physics tick, no await, no signal emission required.
# Red phase: scene does not yet exist — all tests that need the scene will report FAIL.
# Green phase: Engine Integration Agent delivers the scene and all assertions pass.
#
# Spec requirement traceability:
#   T-1   → SCENE-1 (AC-SCENE-1.1, AC-SCENE-1.2)
#   T-2   → NODE-1  (AC-NODE-1.2) SPAWN-1 (AC-SPAWN-1.1)
#   T-3   → SPAWN-1 (AC-SPAWN-1.2)
#   T-4   → NODE-1  (AC-NODE-1.4) EXIT-1  (AC-EXIT-1.1)
#   T-5   → EXIT-1  (AC-EXIT-1.2)
#   T-6   → EXIT-1  (AC-EXIT-1.3)
#   T-7   → NODE-1  (AC-NODE-1.3) RESPAWN-1 (AC-RESPAWN-1.1)
#   T-8   → RESPAWN-1 (AC-RESPAWN-1.3) — NodePath non-empty + name check
#   T-9   → WIRE-1 (AC-WIRE-1.1, AC-WIRE-1.3)
#   T-10  → NODE-1 (AC-NODE-1.7) GEO-1 (AC-GEO-1.1)
#   T-11  → COL-1 (AC-COL-1.1) — all StaticBody3D floor/wall nodes have non-zero BoxShape3D
#   T-12  → NODE-1 (AC-NODE-1.8) ENC-1 (AC-ENC-1.1)
#   T-13  → NODE-1 (AC-NODE-1.6)
#   T-14  → NODE-1 (AC-NODE-1.5)
#   T-15  → SCENE-1 (AC-SCENE-1.2) — root node name
#   T-16  → NODE-1 (AC-NODE-1.1) WIRE-1 (AC-WIRE-1.2)
#   T-17  → RESPAWN-1 (AC-RESPAWN-1.4, AC-RESPAWN-1.5)
#   T-18  → GEO-1 (AC-GEO-1.2, AC-GEO-1.3)
#   T-19  → GEO-2 (AC-GEO-2.2, AC-GEO-2.3)
#   T-20  → GEO-3 (AC-GEO-3.2, AC-GEO-3.3)
#   T-21  → GEO-4 (AC-GEO-4.1, AC-GEO-4.4)
#   T-22  → GEO-5 (AC-GEO-5.1)
#   T-23  → GEO-6 (AC-GEO-6.1)
#   T-24  → ENC-1 (AC-ENC-1.2 through AC-ENC-1.5) — enemy positions within tolerance
#   T-25  → COL-1 (AC-COL-1.1) — collision_mask == 3 on all StaticBody3D nodes
#   T-26  → ENV-1 (AC-ENV-1.1, AC-ENV-1.2)
#   T-27  → GEO-4 (AC-GEO-4.2, AC-GEO-4.3) — platform gap verification
#   T-28  → RESPAWN-1 (AC-RESPAWN-1.4) — RespawnZone shape Y extent >= 8
#   T-29  → GEO-2 (AC-GEO-2.4) — platform top surface within jump reach
#   T-30  → EXIT-1 (AC-EXIT-1.5) — LevelExit X position in exit corridor

extends Object

# Scene path under test.
const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"

# Tolerance for position checks (metres).
const POS_TOL: float = 0.5

# Strict tolerance used where spec says ±0.01 m or ±0.1 m.
const POS_TOL_STRICT: float = 0.1

# All StaticBody3D node names required by spec NODE-1.
const STATIC_BODY_NAMES: Array[String] = [
	"EntryFloor",
	"EntryLeftWall",
	"EntryRightBoundary",
	"MutationTeaseFloor",
	"MutationTeasePlatform",
	"FusionFloor",
	"FusionPlatformA",
	"FusionPlatformB",
	"SkillCheckFloorBase",
	"SkillCheckPlatform1",
	"SkillCheckPlatform2",
	"SkillCheckPlatform3",
	"MiniBossFloor",
	"ExitFloor",
]

# Enemy node names required by spec NODE-1 / ENC-1.
const ENEMY_NODE_NAMES: Array[String] = [
	"EnemyMutationTease",
	"EnemyFusionA",
	"EnemyFusionB",
	"EnemyMiniBoss",
]

var _pass_count: int = 0
var _fail_count: int = 0


func _pass_test(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail_test(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
	if condition:
		_pass_test(test_name)
	else:
		_fail_test(test_name, fail_msg)


func _assert_eq(a: Variant, b: Variant, test_name: String) -> void:
	if a == b:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected " + str(b) + ", got " + str(a))


# Load and instantiate the scene. Returns null and records the failure when
# the scene file is absent (red phase).
func _load_scene() -> Node:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	if packed == null:
		push_error("FAIL: scene not found — " + SCENE_PATH)
		_fail_test("scene_file_exists", "ResourceLoader.load returned null for " + SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("scene_instantiates", "instantiate() returned null")
		return null
	return inst


# Helper: get the CollisionShape3D child of a node, or null.
func _get_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null


# Helper: assert a BoxShape3D is non-zero on all axes.
func _assert_box_shape_nonzero(shape: BoxShape3D, test_name: String) -> void:
	if shape == null:
		_fail_test(test_name, "shape is null or not BoxShape3D")
		return
	_assert_true(
		shape.size.x > 0.0 and shape.size.y > 0.0 and shape.size.z > 0.0,
		test_name,
		"BoxShape3D size has zero component: " + str(shape.size)
	)


# ---------------------------------------------------------------------------
# T-1: Scene file loads without error (non-null) — SCENE-1 AC-SCENE-1.1
# ---------------------------------------------------------------------------
func test_t1_scene_file_loads() -> void:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	_assert_true(packed != null, "T-1_scene_file_loads",
		"ResourceLoader.load returned null — scene file absent (expected in red phase)")
	if packed != null:
		var inst: Node = packed.instantiate()
		_assert_true(inst != null, "T-1_scene_instantiates")
		if inst != null:
			inst.free()


# ---------------------------------------------------------------------------
# T-2: SpawnPosition Marker3D exists — NODE-1 AC-NODE-1.2, SPAWN-1 AC-SPAWN-1.1
# ---------------------------------------------------------------------------
func test_t2_spawn_position_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("SpawnPosition")
	_assert_true(node != null, "T-2_spawn_position_exists",
		"SpawnPosition node not found")
	if node != null:
		_assert_true(node is Marker3D, "T-2_spawn_position_is_marker3d",
			"SpawnPosition is " + node.get_class() + ", expected Marker3D")
	root.free()


# ---------------------------------------------------------------------------
# T-3: SpawnPosition is at approximately (-25, 1, 0) within 0.5 m — SPAWN-1 AC-SPAWN-1.2
# ---------------------------------------------------------------------------
func test_t3_spawn_position_coordinates() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("SpawnPosition")
	if node == null:
		_fail_test("T-3_spawn_position_coords", "SpawnPosition node not found")
		root.free()
		return
	var pos: Vector3 = (node as Node3D).position
	var expected: Vector3 = Vector3(-25.0, 1.0, 0.0)
	_assert_true(
		abs(pos.x - expected.x) <= POS_TOL and
		abs(pos.y - expected.y) <= POS_TOL and
		abs(pos.z - expected.z) <= POS_TOL,
		"T-3_spawn_position_coords",
		"SpawnPosition.position = " + str(pos) + ", expected ~" + str(expected) + " (tol " + str(POS_TOL) + ")"
	)
	root.free()


# ---------------------------------------------------------------------------
# T-4: LevelExit Area3D exists — NODE-1 AC-NODE-1.4, EXIT-1 AC-EXIT-1.1
# ---------------------------------------------------------------------------
func test_t4_level_exit_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("LevelExit")
	_assert_true(node != null, "T-4_level_exit_exists", "LevelExit node not found")
	if node != null:
		_assert_true(node is Area3D, "T-4_level_exit_is_area3d",
			"LevelExit is " + node.get_class() + ", expected Area3D")
	root.free()


# ---------------------------------------------------------------------------
# T-5: LevelExit has a CollisionShape3D child — EXIT-1 AC-EXIT-1.2
# ---------------------------------------------------------------------------
func test_t5_level_exit_has_collision_shape() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("LevelExit")
	if exit_node == null:
		_fail_test("T-5_level_exit_collision_shape", "LevelExit node not found")
		root.free()
		return
	var col: CollisionShape3D = _get_collision_shape(exit_node)
	_assert_true(col != null, "T-5_level_exit_has_collision_shape3d",
		"LevelExit has no CollisionShape3D child")
	if col != null:
		_assert_true(col.shape != null and col.shape is BoxShape3D,
			"T-5_level_exit_collision_shape_is_box",
			"LevelExit CollisionShape3D.shape is not a BoxShape3D")
		if col.shape is BoxShape3D:
			_assert_box_shape_nonzero(col.shape as BoxShape3D, "T-5_level_exit_box_nonzero")
	root.free()


# ---------------------------------------------------------------------------
# T-6: LevelExit has monitoring = true — EXIT-1 AC-EXIT-1.3
# ---------------------------------------------------------------------------
func test_t6_level_exit_monitoring() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("LevelExit")
	if exit_node == null:
		_fail_test("T-6_level_exit_monitoring", "LevelExit node not found")
		root.free()
		return
	_assert_true((exit_node as Area3D).monitoring == true, "T-6_level_exit_monitoring",
		"LevelExit.monitoring is false")
	root.free()


# ---------------------------------------------------------------------------
# T-7: RespawnZone Area3D exists — NODE-1 AC-NODE-1.3, RESPAWN-1 AC-RESPAWN-1.1
# ---------------------------------------------------------------------------
func test_t7_respawn_zone_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("RespawnZone")
	_assert_true(node != null, "T-7_respawn_zone_exists", "RespawnZone node not found")
	if node != null:
		_assert_true(node is Area3D, "T-7_respawn_zone_is_area3d",
			"RespawnZone is " + node.get_class() + ", expected Area3D")
	root.free()


# ---------------------------------------------------------------------------
# T-8: RespawnZone spawn_point NodePath is non-empty and references SpawnPosition
#       RESPAWN-1 AC-RESPAWN-1.3 (headless-safe portion)
#
# Checkpoint note: full NodePath resolution requires scene tree insertion.
# This test checks (a) path is non-empty and (b) the path string contains
# "SpawnPosition". Full resolution is an integration concern.
# ---------------------------------------------------------------------------
func test_t8_respawn_zone_spawn_point_path() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var zone: Node = root.get_node_or_null("RespawnZone")
	if zone == null:
		_fail_test("T-8_respawn_spawn_point_path", "RespawnZone node not found")
		root.free()
		return
	var path: NodePath = zone.get("spawn_point")
	_assert_true(path != NodePath(), "T-8_respawn_spawn_point_nonempty",
		"RespawnZone.spawn_point is an empty NodePath")
	if path != NodePath():
		var path_str: String = String(path)
		_assert_true(path_str.contains("SpawnPosition"), "T-8_respawn_spawn_point_references_spawn_position",
			"spawn_point path '" + path_str + "' does not contain 'SpawnPosition'")
	root.free()


# ---------------------------------------------------------------------------
# T-9: InfectionInteractionHandler node exists as direct child of root
#       WIRE-1 AC-WIRE-1.1, AC-WIRE-1.3
# ---------------------------------------------------------------------------
func test_t9_infection_interaction_handler_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("InfectionInteractionHandler")
	_assert_true(node != null, "T-9_infection_handler_exists",
		"InfectionInteractionHandler node not found as direct child of scene root")
	if node != null:
		# Verify it is a direct child (depth == 1 from root).
		_assert_true(node.get_parent() == root, "T-9_infection_handler_direct_child",
			"InfectionInteractionHandler is not a direct child of ContainmentHall01")
	root.free()


# ---------------------------------------------------------------------------
# T-10: At least one StaticBody3D floor node exists (EntryFloor by name)
#        NODE-1 AC-NODE-1.7, GEO-1 AC-GEO-1.1
# ---------------------------------------------------------------------------
func test_t10_entry_floor_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("EntryFloor")
	_assert_true(node != null, "T-10_entry_floor_exists", "EntryFloor node not found")
	if node != null:
		_assert_true(node is StaticBody3D, "T-10_entry_floor_is_static_body3d",
			"EntryFloor is " + node.get_class() + ", expected StaticBody3D")
	root.free()


# ---------------------------------------------------------------------------
# T-11: All StaticBody3D floor/wall nodes have non-zero BoxShape3D
#        NODE-1 AC-NODE-1.7, COL-1 (shape existence prerequisite)
# ---------------------------------------------------------------------------
func test_t11_all_static_bodies_have_nonzero_box_shape() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	for node_name in STATIC_BODY_NAMES:
		var node: Node = root.get_node_or_null(node_name)
		if node == null:
			_fail_test("T-11_" + node_name + "_exists", node_name + " node not found")
			continue
		if not (node is StaticBody3D):
			_fail_test("T-11_" + node_name + "_type", node_name + " is " + node.get_class() + ", expected StaticBody3D")
			continue
		var col: CollisionShape3D = _get_collision_shape(node)
		if col == null:
			_fail_test("T-11_" + node_name + "_has_collision_shape", node_name + " has no CollisionShape3D child")
			continue
		if col.shape == null:
			_fail_test("T-11_" + node_name + "_shape_assigned", node_name + "/CollisionShape3D.shape is null")
			continue
		if not (col.shape is BoxShape3D):
			_fail_test("T-11_" + node_name + "_shape_is_box",
				node_name + "/CollisionShape3D.shape is " + col.shape.get_class() + ", expected BoxShape3D")
			continue
		_assert_box_shape_nonzero(col.shape as BoxShape3D, "T-11_" + node_name + "_nonzero_extents")
	root.free()


# ---------------------------------------------------------------------------
# T-12: At least 4 enemy instances exist by exact node name
#        NODE-1 AC-NODE-1.8, ENC-1 AC-ENC-1.1
# ---------------------------------------------------------------------------
func test_t12_four_enemy_instances_exist() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var found_count: int = 0
	for enemy_name in ENEMY_NODE_NAMES:
		var node: Node = root.get_node_or_null(enemy_name)
		if node != null:
			found_count += 1
			_pass_test("T-12_enemy_" + enemy_name + "_exists")
		else:
			_fail_test("T-12_enemy_" + enemy_name + "_exists", enemy_name + " not found")
	_assert_true(found_count >= 4, "T-12_at_least_4_enemies",
		"Found " + str(found_count) + " of 4 required enemy nodes")
	root.free()


# ---------------------------------------------------------------------------
# T-13: Player3D instance exists in the scene — NODE-1 AC-NODE-1.6
# ---------------------------------------------------------------------------
func test_t13_player3d_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("Player3D")
	_assert_true(node != null, "T-13_player3d_exists", "Player3D node not found")
	if node != null:
		_assert_true(node is CharacterBody3D, "T-13_player3d_is_character_body3d",
			"Player3D is " + node.get_class() + ", expected CharacterBody3D")
	root.free()


# ---------------------------------------------------------------------------
# T-14: InfectionUI (GameUI) CanvasLayer node exists — NODE-1 AC-NODE-1.5
# ---------------------------------------------------------------------------
func test_t14_infection_ui_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("InfectionUI")
	_assert_true(node != null, "T-14_infection_ui_exists",
		"InfectionUI node not found (instanced game_ui.tscn)")
	root.free()


# ---------------------------------------------------------------------------
# T-15: Scene root node name is "ContainmentHall01" and type is Node3D
#        SCENE-1 AC-SCENE-1.2
# ---------------------------------------------------------------------------
func test_t15_root_node_name_and_type() -> void:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("T-15_root_node_name", "Scene not found — cannot check root name")
		return
	var root: Node = packed.instantiate()
	if root == null:
		_fail_test("T-15_root_node_name", "instantiate() returned null")
		return
	_assert_eq(root.name, "ContainmentHall01", "T-15_root_name_is_containment_hall_01")
	_assert_true(root is Node3D, "T-15_root_is_node3d",
		"Scene root is " + root.get_class() + ", expected Node3D")
	root.free()


# ---------------------------------------------------------------------------
# T-16: InfectionInteractionHandler has infection_interaction_handler.gd script
#        WIRE-1 AC-WIRE-1.2
# ---------------------------------------------------------------------------
func test_t16_infection_handler_script_path() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("InfectionInteractionHandler")
	if node == null:
		_fail_test("T-16_infection_handler_script", "InfectionInteractionHandler not found")
		root.free()
		return
	var script_res: Resource = node.get_script()
	_assert_true(script_res != null, "T-16_infection_handler_has_script",
		"InfectionInteractionHandler has no script attached")
	if script_res != null:
		var path: String = script_res.resource_path
		_assert_true(path.contains("infection_interaction_handler.gd"),
			"T-16_infection_handler_script_name",
			"Script path '" + path + "' does not contain 'infection_interaction_handler.gd'")
	root.free()


# ---------------------------------------------------------------------------
# T-17: RespawnZone CollisionShape3D BoxShape3D Y extent >= 8, monitoring == true
#        RESPAWN-1 AC-RESPAWN-1.4, AC-RESPAWN-1.5
# ---------------------------------------------------------------------------
func test_t17_respawn_zone_shape_and_monitoring() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var zone: Node = root.get_node_or_null("RespawnZone")
	if zone == null:
		_fail_test("T-17_respawn_zone_shape", "RespawnZone not found")
		root.free()
		return
	_assert_true((zone as Area3D).monitoring == true, "T-17_respawn_zone_monitoring",
		"RespawnZone.monitoring is false")
	var col: CollisionShape3D = _get_collision_shape(zone)
	if col == null:
		_fail_test("T-17_respawn_zone_collision_shape", "RespawnZone has no CollisionShape3D")
		root.free()
		return
	if col.shape == null or not (col.shape is BoxShape3D):
		_fail_test("T-17_respawn_zone_box_shape", "RespawnZone shape is not BoxShape3D")
		root.free()
		return
	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(box.size.y >= 8.0, "T-17_respawn_zone_y_extent_ge_8",
		"RespawnZone BoxShape3D.size.y = " + str(box.size.y) + ", expected >= 8.0 m")
	root.free()


# ---------------------------------------------------------------------------
# T-18: EntryFloor BoxShape3D size.x >= 18, size.z >= 8; X center in [-22, -18]
#        GEO-1 AC-GEO-1.2, AC-GEO-1.3
# ---------------------------------------------------------------------------
func test_t18_entry_floor_geometry() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("EntryFloor")
	if node == null:
		_fail_test("T-18_entry_floor_geometry", "EntryFloor not found")
		root.free()
		return
	var col: CollisionShape3D = _get_collision_shape(node)
	if col == null or col.shape == null or not (col.shape is BoxShape3D):
		_fail_test("T-18_entry_floor_box", "EntryFloor has no valid BoxShape3D")
		root.free()
		return
	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(box.size.x >= 18.0, "T-18_entry_floor_width_ge_18",
		"EntryFloor BoxShape3D.size.x = " + str(box.size.x) + ", expected >= 18.0")
	_assert_true(box.size.z >= 8.0, "T-18_entry_floor_depth_ge_8",
		"EntryFloor BoxShape3D.size.z = " + str(box.size.z) + ", expected >= 8.0")
	var x_pos: float = (node as Node3D).position.x
	_assert_true(x_pos >= -22.0 and x_pos <= -18.0, "T-18_entry_floor_x_center_in_range",
		"EntryFloor position.x = " + str(x_pos) + ", expected in [-22, -18]")
	root.free()


# ---------------------------------------------------------------------------
# T-19: MutationTeasePlatform BoxShape3D size.x >= 2, size.z >= 4
#        GEO-2 AC-GEO-2.2, AC-GEO-2.3
# ---------------------------------------------------------------------------
func test_t19_mutation_tease_platform_geometry() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("MutationTeasePlatform")
	if node == null:
		_fail_test("T-19_mutation_tease_platform", "MutationTeasePlatform not found")
		root.free()
		return
	var col: CollisionShape3D = _get_collision_shape(node)
	if col == null or col.shape == null or not (col.shape is BoxShape3D):
		_fail_test("T-19_mutation_tease_platform_box", "MutationTeasePlatform has no valid BoxShape3D")
		root.free()
		return
	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(box.size.x >= 2.0, "T-19_mutation_tease_platform_width_ge_2",
		"MutationTeasePlatform size.x = " + str(box.size.x) + ", expected >= 2.0")
	_assert_true(box.size.z >= 4.0, "T-19_mutation_tease_platform_depth_ge_4",
		"MutationTeasePlatform size.z = " + str(box.size.z) + ", expected >= 4.0")
	root.free()


# ---------------------------------------------------------------------------
# T-20: FusionPlatformA and FusionPlatformB both exist; horizontal center
#        separation >= 8 m
#        GEO-3 AC-GEO-3.2, AC-GEO-3.3
# ---------------------------------------------------------------------------
func test_t20_fusion_platforms_exist_and_separated() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var plat_a: Node = root.get_node_or_null("FusionPlatformA")
	var plat_b: Node = root.get_node_or_null("FusionPlatformB")
	_assert_true(plat_a != null, "T-20_fusion_platform_a_exists", "FusionPlatformA not found")
	_assert_true(plat_b != null, "T-20_fusion_platform_b_exists", "FusionPlatformB not found")
	if plat_a != null and plat_b != null:
		var x_a: float = (plat_a as Node3D).position.x
		var x_b: float = (plat_b as Node3D).position.x
		var separation: float = abs(x_b - x_a)
		_assert_true(separation >= 8.0, "T-20_fusion_platforms_separation_ge_8m",
			"FusionPlatformA.x=" + str(x_a) + " FusionPlatformB.x=" + str(x_b) +
			" separation=" + str(separation) + ", expected >= 8.0 m")
	root.free()


# ---------------------------------------------------------------------------
# T-21: SkillCheckPlatform1, 2, 3 exist; each width (size.x) >= 3.0 m
#        GEO-4 AC-GEO-4.1, AC-GEO-4.4
# ---------------------------------------------------------------------------
func test_t21_skill_check_platforms_exist_and_wide_enough() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var platform_names: Array[String] = ["SkillCheckPlatform1", "SkillCheckPlatform2", "SkillCheckPlatform3"]
	for name in platform_names:
		var node: Node = root.get_node_or_null(name)
		if node == null:
			_fail_test("T-21_" + name + "_exists", name + " not found")
			continue
		_pass_test("T-21_" + name + "_exists")
		var col: CollisionShape3D = _get_collision_shape(node)
		if col == null or col.shape == null or not (col.shape is BoxShape3D):
			_fail_test("T-21_" + name + "_box", name + " has no valid BoxShape3D")
			continue
		var box: BoxShape3D = col.shape as BoxShape3D
		_assert_true(box.size.x >= 3.0, "T-21_" + name + "_width_ge_3m",
			name + " size.x = " + str(box.size.x) + ", expected >= 3.0")
	root.free()


# ---------------------------------------------------------------------------
# T-22: MiniBossFloor exists as StaticBody3D — GEO-5 AC-GEO-5.1
# ---------------------------------------------------------------------------
func test_t22_mini_boss_floor_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("MiniBossFloor")
	_assert_true(node != null, "T-22_mini_boss_floor_exists", "MiniBossFloor not found")
	if node != null:
		_assert_true(node is StaticBody3D, "T-22_mini_boss_floor_is_static_body",
			"MiniBossFloor is " + node.get_class())
		# Verify X center approximately 67.5 with 2 m tolerance.
		var x_pos: float = (node as Node3D).position.x
		_assert_true(abs(x_pos - 67.5) <= 2.0, "T-22_mini_boss_floor_x_center",
			"MiniBossFloor position.x = " + str(x_pos) + ", expected ~67.5 (tol 2.0)")
	root.free()


# ---------------------------------------------------------------------------
# T-23: ExitFloor exists; X center approximately 87.5
#        GEO-6 AC-GEO-6.1
# ---------------------------------------------------------------------------
func test_t23_exit_floor_exists() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("ExitFloor")
	_assert_true(node != null, "T-23_exit_floor_exists", "ExitFloor not found")
	if node != null:
		var x_pos: float = (node as Node3D).position.x
		_assert_true(abs(x_pos - 87.5) <= 2.0, "T-23_exit_floor_x_center",
			"ExitFloor position.x = " + str(x_pos) + ", expected ~87.5 (tol 2.0)")
	root.free()


# ---------------------------------------------------------------------------
# T-24: Enemy positions within tolerance
#        ENC-1 AC-ENC-1.2 through AC-ENC-1.5
# ---------------------------------------------------------------------------
func test_t24_enemy_positions() -> void:
	var root: Node = _load_scene()
	if root == null:
		return

	var expected_positions: Dictionary = {
		"EnemyMutationTease": Vector3(0.0, 1.3, 0.0),
		"EnemyFusionA": Vector3(15.0, 1.3, 0.0),
		"EnemyFusionB": Vector3(28.0, 1.3, 0.0),
		"EnemyMiniBoss": Vector3(67.0, 0.5, 0.0),
	}

	for enemy_name in expected_positions:
		var node: Node = root.get_node_or_null(enemy_name)
		if node == null:
			_fail_test("T-24_" + enemy_name + "_pos", enemy_name + " not found")
			continue
		var actual_pos: Vector3 = (node as Node3D).position
		var exp: Vector3 = expected_positions[enemy_name]
		_assert_true(
			abs(actual_pos.x - exp.x) <= POS_TOL_STRICT and
			abs(actual_pos.y - exp.y) <= POS_TOL_STRICT and
			abs(actual_pos.z - exp.z) <= POS_TOL_STRICT,
			"T-24_" + enemy_name + "_position",
			enemy_name + " position = " + str(actual_pos) +
			", expected ~" + str(exp) + " (tol " + str(POS_TOL_STRICT) + ")"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-25: collision_mask == 3 on all StaticBody3D floor/platform/wall nodes
#        COL-1 AC-COL-1.1
# ---------------------------------------------------------------------------
func test_t25_static_bodies_collision_mask_3() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	for node_name in STATIC_BODY_NAMES:
		var node: Node = root.get_node_or_null(node_name)
		if node == null:
			_fail_test("T-25_" + node_name + "_mask", node_name + " not found")
			continue
		if not (node is StaticBody3D):
			_fail_test("T-25_" + node_name + "_mask", node_name + " is not StaticBody3D")
			continue
		var mask: int = (node as StaticBody3D).collision_mask
		_assert_true(mask == 3, "T-25_" + node_name + "_collision_mask_3",
			node_name + ".collision_mask = " + str(mask) + ", expected 3")
	root.free()


# ---------------------------------------------------------------------------
# T-26: WorldEnvironment and DirectionalLight3D exist as direct children
#        ENV-1 AC-ENV-1.1, AC-ENV-1.2
# ---------------------------------------------------------------------------
func test_t26_world_environment_and_light_exist() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	_assert_true(root.get_node_or_null("WorldEnvironment") != null,
		"T-26_world_environment_exists", "WorldEnvironment node not found")
	_assert_true(root.get_node_or_null("DirectionalLight3D") != null,
		"T-26_directional_light_exists", "DirectionalLight3D node not found")
	root.free()


# ---------------------------------------------------------------------------
# T-27: Skill-check platform gaps are <= 1.5 m
#        GEO-4 AC-GEO-4.2, AC-GEO-4.3
#
# Gap measured as: (next_platform_left_edge) - (prev_platform_right_edge)
# where edge = node.position.x ± (box.size.x / 2).
# CollisionShape3D transform offset is accounted for if present.
# ---------------------------------------------------------------------------
func test_t27_skill_check_platform_gaps() -> void:
	var root: Node = _load_scene()
	if root == null:
		return

	var platform_names: Array[String] = ["SkillCheckPlatform1", "SkillCheckPlatform2", "SkillCheckPlatform3"]
	var rights: Array[float] = []
	var lefts: Array[float] = []
	var valid: bool = true

	for name in platform_names:
		var node: Node = root.get_node_or_null(name)
		if node == null:
			_fail_test("T-27_gap_" + name + "_missing", name + " not found")
			valid = false
			continue
		var col: CollisionShape3D = _get_collision_shape(node)
		if col == null or col.shape == null or not (col.shape is BoxShape3D):
			_fail_test("T-27_gap_" + name + "_no_box", name + " has no valid BoxShape3D")
			valid = false
			continue
		var box: BoxShape3D = col.shape as BoxShape3D
		var node_x: float = (node as Node3D).position.x
		var col_offset_x: float = col.position.x
		var center_x: float = node_x + col_offset_x
		var half_w: float = box.size.x * 0.5
		lefts.append(center_x - half_w)
		rights.append(center_x + half_w)

	if not valid:
		root.free()
		return

	# Gap 1: Platform1 right edge to Platform2 left edge.
	var gap1: float = lefts[1] - rights[0]
	_assert_true(gap1 <= 1.5, "T-27_gap1_le_1p5m",
		"Gap between SkillCheckPlatform1 and SkillCheckPlatform2 = " + str(gap1) + " m, expected <= 1.5 m")
	_assert_true(gap1 > 0.0, "T-27_gap1_positive",
		"Platforms 1 and 2 overlap (gap = " + str(gap1) + ")")

	# Gap 2: Platform2 right edge to Platform3 left edge.
	var gap2: float = lefts[2] - rights[1]
	_assert_true(gap2 <= 1.5, "T-27_gap2_le_1p5m",
		"Gap between SkillCheckPlatform2 and SkillCheckPlatform3 = " + str(gap2) + " m, expected <= 1.5 m")
	_assert_true(gap2 > 0.0, "T-27_gap2_positive",
		"Platforms 2 and 3 overlap (gap = " + str(gap2) + ")")

	root.free()


# ---------------------------------------------------------------------------
# T-28: RespawnZone BoxShape3D Y extent >= 8 (adversarial guard, per ticket Task 4)
#        RESPAWN-1 AC-RESPAWN-1.4
# (Redundant with T-17 by design — explicit adversarial assertion separate from
#  the structural existence check for clarity in the Test Breaker phase.)
# ---------------------------------------------------------------------------
func test_t28_respawn_zone_shape_y_ge_8() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var zone: Node = root.get_node_or_null("RespawnZone")
	if zone == null:
		_fail_test("T-28_respawn_shape_y", "RespawnZone not found")
		root.free()
		return
	var col: CollisionShape3D = _get_collision_shape(zone)
	if col == null or col.shape == null or not (col.shape is BoxShape3D):
		_fail_test("T-28_respawn_shape_y", "RespawnZone has no valid BoxShape3D")
		root.free()
		return
	var y_size: float = (col.shape as BoxShape3D).size.y
	_assert_true(y_size >= 8.0, "T-28_respawn_zone_y_size_ge_8",
		"RespawnZone shape size.y = " + str(y_size) + ", expected >= 8.0 to catch falling player")
	root.free()


# ---------------------------------------------------------------------------
# T-29: MutationTeasePlatform top surface world Y in range [0.5, 1.0]
#        GEO-2 AC-GEO-2.4 — platform is reachable and above floor
# ---------------------------------------------------------------------------
func test_t29_mutation_tease_platform_top_surface_height() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("MutationTeasePlatform")
	if node == null:
		_fail_test("T-29_platform_top_surface", "MutationTeasePlatform not found")
		root.free()
		return
	var col: CollisionShape3D = _get_collision_shape(node)
	if col == null or col.shape == null or not (col.shape is BoxShape3D):
		_fail_test("T-29_platform_top_surface", "MutationTeasePlatform has no valid BoxShape3D")
		root.free()
		return
	var box: BoxShape3D = col.shape as BoxShape3D
	var node_y: float = (node as Node3D).position.y
	var col_offset_y: float = col.position.y
	var top_surface_y: float = node_y + col_offset_y + (box.size.y * 0.5)
	_assert_true(top_surface_y >= 0.5 and top_surface_y <= 1.0,
		"T-29_mutation_platform_top_y_in_range",
		"MutationTeasePlatform top surface Y = " + str(top_surface_y) +
		", expected in [0.5, 1.0] (above floor, below jump apex 1.2 m)")
	root.free()


# ---------------------------------------------------------------------------
# T-30: LevelExit global_position.x >= 88 (within exit corridor)
#        EXIT-1 AC-EXIT-1.5
# ---------------------------------------------------------------------------
func test_t30_level_exit_x_position() -> void:
	var root: Node = _load_scene()
	if root == null:
		return
	var node: Node = root.get_node_or_null("LevelExit")
	if node == null:
		_fail_test("T-30_level_exit_x", "LevelExit not found")
		root.free()
		return
	var x_pos: float = (node as Node3D).position.x
	_assert_true(x_pos >= 88.0, "T-30_level_exit_x_ge_88",
		"LevelExit position.x = " + str(x_pos) + ", expected >= 88.0 (exit corridor)")
	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_containment_hall_01.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_t1_scene_file_loads()
	test_t2_spawn_position_exists()
	test_t3_spawn_position_coordinates()
	test_t4_level_exit_exists()
	test_t5_level_exit_has_collision_shape()
	test_t6_level_exit_monitoring()
	test_t7_respawn_zone_exists()
	test_t8_respawn_zone_spawn_point_path()
	test_t9_infection_interaction_handler_exists()
	test_t10_entry_floor_exists()
	test_t11_all_static_bodies_have_nonzero_box_shape()
	test_t12_four_enemy_instances_exist()
	test_t13_player3d_exists()
	test_t14_infection_ui_exists()
	test_t15_root_node_name_and_type()
	test_t16_infection_handler_script_path()
	test_t17_respawn_zone_shape_and_monitoring()
	test_t18_entry_floor_geometry()
	test_t19_mutation_tease_platform_geometry()
	test_t20_fusion_platforms_exist_and_separated()
	test_t21_skill_check_platforms_exist_and_wide_enough()
	test_t22_mini_boss_floor_exists()
	test_t23_exit_floor_exists()
	test_t24_enemy_positions()
	test_t25_static_bodies_collision_mask_3()
	test_t26_world_environment_and_light_exist()
	test_t27_skill_check_platform_gaps()
	test_t28_respawn_zone_shape_y_ge_8()
	test_t29_mutation_tease_platform_top_surface_height()
	test_t30_level_exit_x_position()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
