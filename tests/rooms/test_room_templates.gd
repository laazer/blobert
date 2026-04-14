#
# test_room_templates.gd
#
# Primary behavioral tests for the Room Template System.
# Spec: agent_context/agents/2_spec/room_template_system_spec.md
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/room_template_system.md
#
# All tests are headless-safe: no physics tick, no await, no signal emission.
# Red phase: scene files do not yet exist — all tests report explicit FAIL with missing path.
# Green phase: all assertions pass after Engine Integration Agent authors the 5 room scenes.
#
# Spec requirement traceability:
#   RTS-LOAD-1..5  → RTS-LOAD  (AC: ResourceLoader.load non-null, instantiate, free)
#   RTS-STRUCT-1..5 → RTS-STRUCT (AC: root is Node3D with correct name)
#   RTS-ENTRY-1..5  → RTS-ENTRY  (AC: Entry Marker3D at (0,1,0) ±0.01)
#   RTS-EXIT-1..5   → RTS-EXIT   (AC: Exit Marker3D at (30,1,0) or (40,1,0) ±0.01)
#   RTS-GEO-1..5    → RTS-GEO    (AC: floor StaticBody3D BoxShape3D size, top surface Y in [-0.1,0.1])
#   RTS-ENC-1..5    → RTS-ENC    (AC: enemy count and node name per room)
#   RTS-NO-PLAYER-1 → RTS-NO-PLAYER (AC: forbidden nodes absent from all 5 rooms)
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - Test IDs use RTS-* prefix; no duplicates with T-1..T-72, SDR-*, RSM-*, EB-* namespaces.

extends "res://tests/utils/test_utils.gd"

# ---------------------------------------------------------------------------
# Scene paths under test
# ---------------------------------------------------------------------------

const SCENE_INTRO_01:         String = "res://scenes/rooms/room_intro_01.tscn"
const SCENE_COMBAT_01:        String = "res://scenes/rooms/room_combat_01.tscn"
const SCENE_COMBAT_02:        String = "res://scenes/rooms/room_combat_02.tscn"
const SCENE_MUTATION_TEASE_01: String = "res://scenes/rooms/room_mutation_tease_01.tscn"
const SCENE_BOSS_01:          String = "res://scenes/rooms/room_boss_01.tscn"

# Enemy scene path that all instanced enemies must reference.
const ENEMY_SCENE_PATH: String = "res://scenes/enemy/enemy_infection_3d.tscn"

# Node names that must NOT appear anywhere in any room scene tree.
const FORBIDDEN_NODE_NAMES: Array[String] = [
	"Player3D",
	"RespawnZone",
	"InfectionInteractionHandler",
	"InfectionUI",
]

# Tolerance for position checks (metres) — spec specifies ±0.01 for markers.
const POS_TOL: float = 0.01

# Tolerance for enemy position — spec specifies ±0.1.
const ENEMY_POS_TOL: float = 0.1

# Tolerance for geometry size checks — spec specifies ±0.01.
const GEO_TOL: float = 0.01

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

# Load a packed scene; null-guards and records FAIL on missing file (red phase).
func _load_packed(scene_path: String, test_prefix: String) -> PackedScene:
	var packed: PackedScene = ResourceLoader.load(scene_path) as PackedScene
	if packed == null:
		_fail_test(test_prefix + "_load", "ResourceLoader.load returned null: " + scene_path)
	return packed


# Instantiate a packed scene; null-guards and records FAIL.
func _instantiate(packed: PackedScene, test_prefix: String) -> Node:
	if packed == null:
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test(test_prefix + "_instantiate", "instantiate() returned null")
	return inst


# Get first CollisionShape3D child of a node, or null.
func _get_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null


# Compute floor top surface Y: static_body.position.y + col_shape.transform.origin.y + box.size.y / 2
func _floor_top_y(floor_node: StaticBody3D) -> float:
	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null:
		return -9999.0
	var shape: BoxShape3D = col.shape as BoxShape3D
	if shape == null:
		return -9999.0
	return floor_node.position.y + col.transform.origin.y + shape.size.y / 2.0


# Recursive search: find any node in the tree with one of the forbidden names.
# Returns an array of [node_name, node_path_string] for each violation found.
func _find_forbidden_nodes(node: Node, forbidden: Array[String]) -> Array:
	var violations: Array = []
	if node == null:
		return violations
	if node.name in forbidden:
		violations.append([node.name, str(node.get_path())])
	for i in range(node.get_child_count()):
		violations.append_array(_find_forbidden_nodes(node.get_child(i), forbidden))
	return violations


# Check if any node in the tree (recursive) is named with a substring of enemy scene name.
# Used to verify intro room has no enemy children.
func _count_enemy_nodes_recursive(node: Node) -> int:
	if node == null:
		return 0
	var count: int = 0
	if "Enemy" in node.name:
		count += 1
	for i in range(node.get_child_count()):
		count += _count_enemy_nodes_recursive(node.get_child(i))
	return count


# Verify the .tscn file text references the enemy scene path for a given room.
# Returns true if the file text contains the expected enemy scene path substring.
func _room_tscn_references_enemy(room_path: String) -> bool:
	var f: FileAccess = FileAccess.open(room_path, FileAccess.READ)
	if f == null:
		return false
	var text: String = f.get_as_text()
	f.close()
	return "enemy_infection_3d.tscn" in text


# ---------------------------------------------------------------------------
# RTS-LOAD-1: room_intro_01 loads, instantiates, and frees without error
# ---------------------------------------------------------------------------
func test_rts_load_1_intro_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_INTRO_01, "RTS-LOAD-1")
	if packed == null:
		return
	var inst: Node = _instantiate(packed, "RTS-LOAD-1")
	if inst == null:
		return
	_pass_test("RTS-LOAD-1_instantiate_ok")
	inst.free()
	_pass_test("RTS-LOAD-1_free_ok")


# ---------------------------------------------------------------------------
# RTS-LOAD-2: room_combat_01 loads, instantiates, and frees without error
# ---------------------------------------------------------------------------
func test_rts_load_2_combat_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_01, "RTS-LOAD-2")
	if packed == null:
		return
	var inst: Node = _instantiate(packed, "RTS-LOAD-2")
	if inst == null:
		return
	_pass_test("RTS-LOAD-2_instantiate_ok")
	inst.free()
	_pass_test("RTS-LOAD-2_free_ok")


# ---------------------------------------------------------------------------
# RTS-LOAD-3: room_combat_02 loads, instantiates, and frees without error
# ---------------------------------------------------------------------------
func test_rts_load_3_combat_02() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_02, "RTS-LOAD-3")
	if packed == null:
		return
	var inst: Node = _instantiate(packed, "RTS-LOAD-3")
	if inst == null:
		return
	_pass_test("RTS-LOAD-3_instantiate_ok")
	inst.free()
	_pass_test("RTS-LOAD-3_free_ok")


# ---------------------------------------------------------------------------
# RTS-LOAD-4: room_mutation_tease_01 loads, instantiates, and frees without error
# ---------------------------------------------------------------------------
func test_rts_load_4_mutation_tease_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_MUTATION_TEASE_01, "RTS-LOAD-4")
	if packed == null:
		return
	var inst: Node = _instantiate(packed, "RTS-LOAD-4")
	if inst == null:
		return
	_pass_test("RTS-LOAD-4_instantiate_ok")
	inst.free()
	_pass_test("RTS-LOAD-4_free_ok")


# ---------------------------------------------------------------------------
# RTS-LOAD-5: room_boss_01 loads, instantiates, and frees without error
# ---------------------------------------------------------------------------
func test_rts_load_5_boss_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_BOSS_01, "RTS-LOAD-5")
	if packed == null:
		return
	var inst: Node = _instantiate(packed, "RTS-LOAD-5")
	if inst == null:
		return
	_pass_test("RTS-LOAD-5_instantiate_ok")
	inst.free()
	_pass_test("RTS-LOAD-5_free_ok")


# ---------------------------------------------------------------------------
# RTS-STRUCT-1: root is Node3D named "RoomIntro01"
# ---------------------------------------------------------------------------
func test_rts_struct_1_intro_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_INTRO_01, "RTS-STRUCT-1")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-STRUCT-1")
	if root == null:
		return
	_assert_true(root is Node3D, "RTS-STRUCT-1_root_is_node3d",
		"root type is " + root.get_class() + ", expected Node3D")
	_assert_eq_str(root.name, "RoomIntro01", "RTS-STRUCT-1_root_name")
	root.free()


# ---------------------------------------------------------------------------
# RTS-STRUCT-2: root is Node3D named "RoomCombat01"
# ---------------------------------------------------------------------------
func test_rts_struct_2_combat_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_01, "RTS-STRUCT-2")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-STRUCT-2")
	if root == null:
		return
	_assert_true(root is Node3D, "RTS-STRUCT-2_root_is_node3d",
		"root type is " + root.get_class() + ", expected Node3D")
	_assert_eq_str(root.name, "RoomCombat01", "RTS-STRUCT-2_root_name")
	root.free()


# ---------------------------------------------------------------------------
# RTS-STRUCT-3: root is Node3D named "RoomCombat02"
# ---------------------------------------------------------------------------
func test_rts_struct_3_combat_02() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_02, "RTS-STRUCT-3")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-STRUCT-3")
	if root == null:
		return
	_assert_true(root is Node3D, "RTS-STRUCT-3_root_is_node3d",
		"root type is " + root.get_class() + ", expected Node3D")
	_assert_eq_str(root.name, "RoomCombat02", "RTS-STRUCT-3_root_name")
	root.free()


# ---------------------------------------------------------------------------
# RTS-STRUCT-4: root is Node3D named "RoomMutationTease01"
# ---------------------------------------------------------------------------
func test_rts_struct_4_mutation_tease_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_MUTATION_TEASE_01, "RTS-STRUCT-4")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-STRUCT-4")
	if root == null:
		return
	_assert_true(root is Node3D, "RTS-STRUCT-4_root_is_node3d",
		"root type is " + root.get_class() + ", expected Node3D")
	_assert_eq_str(root.name, "RoomMutationTease01", "RTS-STRUCT-4_root_name")
	root.free()


# ---------------------------------------------------------------------------
# RTS-STRUCT-5: root is Node3D named "RoomBoss01"
# ---------------------------------------------------------------------------
func test_rts_struct_5_boss_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_BOSS_01, "RTS-STRUCT-5")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-STRUCT-5")
	if root == null:
		return
	_assert_true(root is Node3D, "RTS-STRUCT-5_root_is_node3d",
		"root type is " + root.get_class() + ", expected Node3D")
	_assert_eq_str(root.name, "RoomBoss01", "RTS-STRUCT-5_root_name")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENTRY-1: intro_01 Entry Marker3D is direct child at (0, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_entry_1_intro_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_INTRO_01, "RTS-ENTRY-1")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENTRY-1")
	if root == null:
		return
	var entry: Node = root.get_node_or_null("Entry")
	_assert_true(entry != null, "RTS-ENTRY-1_entry_exists", "Entry node not found as direct child")
	if entry != null:
		_assert_true(entry is Marker3D, "RTS-ENTRY-1_entry_is_marker3d",
			"Entry type is " + entry.get_class() + ", expected Marker3D")
		_assert_vec3_near((entry as Node3D).position, Vector3(0.0, 1.0, 0.0), POS_TOL, "RTS-ENTRY-1_entry_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENTRY-2: combat_01 Entry Marker3D is direct child at (0, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_entry_2_combat_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_01, "RTS-ENTRY-2")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENTRY-2")
	if root == null:
		return
	var entry: Node = root.get_node_or_null("Entry")
	_assert_true(entry != null, "RTS-ENTRY-2_entry_exists", "Entry node not found as direct child")
	if entry != null:
		_assert_true(entry is Marker3D, "RTS-ENTRY-2_entry_is_marker3d",
			"Entry type is " + entry.get_class() + ", expected Marker3D")
		_assert_vec3_near((entry as Node3D).position, Vector3(0.0, 1.0, 0.0), POS_TOL, "RTS-ENTRY-2_entry_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENTRY-3: combat_02 Entry Marker3D is direct child at (0, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_entry_3_combat_02() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_02, "RTS-ENTRY-3")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENTRY-3")
	if root == null:
		return
	var entry: Node = root.get_node_or_null("Entry")
	_assert_true(entry != null, "RTS-ENTRY-3_entry_exists", "Entry node not found as direct child")
	if entry != null:
		_assert_true(entry is Marker3D, "RTS-ENTRY-3_entry_is_marker3d",
			"Entry type is " + entry.get_class() + ", expected Marker3D")
		_assert_vec3_near((entry as Node3D).position, Vector3(0.0, 1.0, 0.0), POS_TOL, "RTS-ENTRY-3_entry_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENTRY-4: mutation_tease_01 Entry Marker3D is direct child at (0, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_entry_4_mutation_tease_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_MUTATION_TEASE_01, "RTS-ENTRY-4")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENTRY-4")
	if root == null:
		return
	var entry: Node = root.get_node_or_null("Entry")
	_assert_true(entry != null, "RTS-ENTRY-4_entry_exists", "Entry node not found as direct child")
	if entry != null:
		_assert_true(entry is Marker3D, "RTS-ENTRY-4_entry_is_marker3d",
			"Entry type is " + entry.get_class() + ", expected Marker3D")
		_assert_vec3_near((entry as Node3D).position, Vector3(0.0, 1.0, 0.0), POS_TOL, "RTS-ENTRY-4_entry_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENTRY-5: boss_01 Entry Marker3D is direct child at (0, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_entry_5_boss_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_BOSS_01, "RTS-ENTRY-5")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENTRY-5")
	if root == null:
		return
	var entry: Node = root.get_node_or_null("Entry")
	_assert_true(entry != null, "RTS-ENTRY-5_entry_exists", "Entry node not found as direct child")
	if entry != null:
		_assert_true(entry is Marker3D, "RTS-ENTRY-5_entry_is_marker3d",
			"Entry type is " + entry.get_class() + ", expected Marker3D")
		_assert_vec3_near((entry as Node3D).position, Vector3(0.0, 1.0, 0.0), POS_TOL, "RTS-ENTRY-5_entry_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-EXIT-1: intro_01 Exit Marker3D is direct child at (30, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_exit_1_intro_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_INTRO_01, "RTS-EXIT-1")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-EXIT-1")
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("Exit")
	_assert_true(exit_node != null, "RTS-EXIT-1_exit_exists", "Exit node not found as direct child")
	if exit_node != null:
		_assert_true(exit_node is Marker3D, "RTS-EXIT-1_exit_is_marker3d",
			"Exit type is " + exit_node.get_class() + ", expected Marker3D")
		_assert_vec3_near((exit_node as Node3D).position, Vector3(30.0, 1.0, 0.0), POS_TOL, "RTS-EXIT-1_exit_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-EXIT-2: combat_01 Exit Marker3D is direct child at (30, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_exit_2_combat_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_01, "RTS-EXIT-2")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-EXIT-2")
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("Exit")
	_assert_true(exit_node != null, "RTS-EXIT-2_exit_exists", "Exit node not found as direct child")
	if exit_node != null:
		_assert_true(exit_node is Marker3D, "RTS-EXIT-2_exit_is_marker3d",
			"Exit type is " + exit_node.get_class() + ", expected Marker3D")
		_assert_vec3_near((exit_node as Node3D).position, Vector3(30.0, 1.0, 0.0), POS_TOL, "RTS-EXIT-2_exit_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-EXIT-3: combat_02 Exit Marker3D is direct child at (30, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_exit_3_combat_02() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_02, "RTS-EXIT-3")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-EXIT-3")
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("Exit")
	_assert_true(exit_node != null, "RTS-EXIT-3_exit_exists", "Exit node not found as direct child")
	if exit_node != null:
		_assert_true(exit_node is Marker3D, "RTS-EXIT-3_exit_is_marker3d",
			"Exit type is " + exit_node.get_class() + ", expected Marker3D")
		_assert_vec3_near((exit_node as Node3D).position, Vector3(30.0, 1.0, 0.0), POS_TOL, "RTS-EXIT-3_exit_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-EXIT-4: mutation_tease_01 Exit Marker3D is direct child at (30, 1, 0) ±0.01
# ---------------------------------------------------------------------------
func test_rts_exit_4_mutation_tease_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_MUTATION_TEASE_01, "RTS-EXIT-4")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-EXIT-4")
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("Exit")
	_assert_true(exit_node != null, "RTS-EXIT-4_exit_exists", "Exit node not found as direct child")
	if exit_node != null:
		_assert_true(exit_node is Marker3D, "RTS-EXIT-4_exit_is_marker3d",
			"Exit type is " + exit_node.get_class() + ", expected Marker3D")
		_assert_vec3_near((exit_node as Node3D).position, Vector3(30.0, 1.0, 0.0), POS_TOL, "RTS-EXIT-4_exit_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-EXIT-5: boss_01 Exit Marker3D is direct child at (40, 1, 0) ±0.01
# (boss room is wider: 40 units, not 30)
# ---------------------------------------------------------------------------
func test_rts_exit_5_boss_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_BOSS_01, "RTS-EXIT-5")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-EXIT-5")
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("Exit")
	_assert_true(exit_node != null, "RTS-EXIT-5_exit_exists", "Exit node not found as direct child")
	if exit_node != null:
		_assert_true(exit_node is Marker3D, "RTS-EXIT-5_exit_is_marker3d",
			"Exit type is " + exit_node.get_class() + ", expected Marker3D")
		_assert_vec3_near((exit_node as Node3D).position, Vector3(40.0, 1.0, 0.0), POS_TOL, "RTS-EXIT-5_exit_position")
	root.free()


# ---------------------------------------------------------------------------
# RTS-GEO-1: intro_01 IntroFloor StaticBody3D, BoxShape3D (30,1,10) ±0.01,
#             top surface Y in [-0.1, 0.1]
# ---------------------------------------------------------------------------
func test_rts_geo_1_intro_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_INTRO_01, "RTS-GEO-1")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-GEO-1")
	if root == null:
		return
	var floor_node: Node = root.get_node_or_null("IntroFloor")
	_assert_true(floor_node != null, "RTS-GEO-1_intro_floor_exists", "IntroFloor not found")
	if floor_node != null:
		_assert_true(floor_node is StaticBody3D, "RTS-GEO-1_intro_floor_is_staticbody3d",
			"IntroFloor type is " + floor_node.get_class() + ", expected StaticBody3D")
		var col: CollisionShape3D = _get_collision_shape(floor_node)
		_assert_true(col != null, "RTS-GEO-1_intro_floor_has_collision_shape", "No CollisionShape3D child found")
		if col != null:
			var shape: BoxShape3D = col.shape as BoxShape3D
			_assert_true(shape != null, "RTS-GEO-1_intro_floor_shape_is_boxshape3d",
				"CollisionShape3D.shape is not BoxShape3D")
			if shape != null:
				_assert_true(
					_near(shape.size.x, 30.0, GEO_TOL) and _near(shape.size.y, 1.0, GEO_TOL) and _near(shape.size.z, 10.0, GEO_TOL),
					"RTS-GEO-1_intro_floor_box_size",
					"BoxShape3D.size expected (30,1,10) ±" + str(GEO_TOL) + ", got " + str(shape.size)
				)
			var top_y: float = _floor_top_y(floor_node as StaticBody3D)
			_assert_true(top_y >= -0.1 and top_y <= 0.1, "RTS-GEO-1_intro_floor_top_surface_y",
				"IntroFloor top surface Y = " + str(top_y) + ", expected in [-0.1, 0.1]")
	root.free()


# ---------------------------------------------------------------------------
# RTS-GEO-2: combat_01 CombatFloor StaticBody3D, BoxShape3D (30,1,10) ±0.01,
#             top surface Y in [-0.1, 0.1]
# ---------------------------------------------------------------------------
func test_rts_geo_2_combat_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_01, "RTS-GEO-2")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-GEO-2")
	if root == null:
		return
	var floor_node: Node = root.get_node_or_null("CombatFloor")
	_assert_true(floor_node != null, "RTS-GEO-2_combat_floor_exists", "CombatFloor not found")
	if floor_node != null:
		_assert_true(floor_node is StaticBody3D, "RTS-GEO-2_combat_floor_is_staticbody3d",
			"CombatFloor type is " + floor_node.get_class() + ", expected StaticBody3D")
		var col: CollisionShape3D = _get_collision_shape(floor_node)
		_assert_true(col != null, "RTS-GEO-2_combat_floor_has_collision_shape", "No CollisionShape3D child found")
		if col != null:
			var shape: BoxShape3D = col.shape as BoxShape3D
			_assert_true(shape != null, "RTS-GEO-2_combat_floor_shape_is_boxshape3d",
				"CollisionShape3D.shape is not BoxShape3D")
			if shape != null:
				_assert_true(
					_near(shape.size.x, 30.0, GEO_TOL) and _near(shape.size.y, 1.0, GEO_TOL) and _near(shape.size.z, 10.0, GEO_TOL),
					"RTS-GEO-2_combat_floor_box_size",
					"BoxShape3D.size expected (30,1,10) ±" + str(GEO_TOL) + ", got " + str(shape.size)
				)
			var top_y: float = _floor_top_y(floor_node as StaticBody3D)
			_assert_true(top_y >= -0.1 and top_y <= 0.1, "RTS-GEO-2_combat_floor_top_surface_y",
				"CombatFloor top surface Y = " + str(top_y) + ", expected in [-0.1, 0.1]")
	root.free()


# ---------------------------------------------------------------------------
# RTS-GEO-3: combat_02 CombatFloor (30,1,10) + CombatPlatform (4,1,6),
#             floor top Y in [-0.1, 0.1], platform top Y in [0.6, 1.0]
# ---------------------------------------------------------------------------
func test_rts_geo_3_combat_02() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_02, "RTS-GEO-3")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-GEO-3")
	if root == null:
		return

	# Primary floor
	var floor_node: Node = root.get_node_or_null("CombatFloor")
	_assert_true(floor_node != null, "RTS-GEO-3_combat_floor_exists", "CombatFloor not found")
	if floor_node != null:
		_assert_true(floor_node is StaticBody3D, "RTS-GEO-3_combat_floor_is_staticbody3d",
			"CombatFloor type is " + floor_node.get_class() + ", expected StaticBody3D")
		var col: CollisionShape3D = _get_collision_shape(floor_node)
		if col != null:
			var shape: BoxShape3D = col.shape as BoxShape3D
			if shape != null:
				_assert_true(
					_near(shape.size.x, 30.0, GEO_TOL) and _near(shape.size.y, 1.0, GEO_TOL) and _near(shape.size.z, 10.0, GEO_TOL),
					"RTS-GEO-3_combat_floor_box_size",
					"BoxShape3D.size expected (30,1,10), got " + str(shape.size)
				)
			var top_y: float = _floor_top_y(floor_node as StaticBody3D)
			_assert_true(top_y >= -0.1 and top_y <= 0.1, "RTS-GEO-3_combat_floor_top_surface_y",
				"CombatFloor top surface Y = " + str(top_y) + ", expected in [-0.1, 0.1]")

	# Elevated platform
	var platform_node: Node = root.get_node_or_null("CombatPlatform")
	_assert_true(platform_node != null, "RTS-GEO-3_combat_platform_exists", "CombatPlatform not found")
	if platform_node != null:
		_assert_true(platform_node is StaticBody3D, "RTS-GEO-3_combat_platform_is_staticbody3d",
			"CombatPlatform type is " + platform_node.get_class() + ", expected StaticBody3D")
		var p_col: CollisionShape3D = _get_collision_shape(platform_node)
		if p_col != null:
			var p_shape: BoxShape3D = p_col.shape as BoxShape3D
			if p_shape != null:
				_assert_true(
					_near(p_shape.size.x, 4.0, GEO_TOL) and _near(p_shape.size.y, 1.0, GEO_TOL) and _near(p_shape.size.z, 6.0, GEO_TOL),
					"RTS-GEO-3_combat_platform_box_size",
					"CombatPlatform BoxShape3D.size expected (4,1,6), got " + str(p_shape.size)
				)
			# Platform top Y = node.y + offset.y + half_height = 0 + 0.3 + 0.5 = 0.8; tolerance [0.6, 1.0]
			var p_top_y: float = (platform_node as StaticBody3D).position.y + p_col.transform.origin.y + p_col.shape.size.y / 2.0
			_assert_true(p_top_y >= 0.6 and p_top_y <= 1.0, "RTS-GEO-3_combat_platform_top_surface_y",
				"CombatPlatform top surface Y = " + str(p_top_y) + ", expected in [0.6, 1.0]")
	root.free()


# ---------------------------------------------------------------------------
# RTS-GEO-4: mutation_tease_01 MutationTeaseFloor (30,1,10) + MutationTeasePlatform (4,1,6),
#             floor top Y in [-0.1, 0.1], platform top Y in [0.6, 1.0]
# ---------------------------------------------------------------------------
func test_rts_geo_4_mutation_tease_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_MUTATION_TEASE_01, "RTS-GEO-4")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-GEO-4")
	if root == null:
		return

	# Primary floor
	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")
	_assert_true(floor_node != null, "RTS-GEO-4_mutation_tease_floor_exists", "MutationTeaseFloor not found")
	if floor_node != null:
		_assert_true(floor_node is StaticBody3D, "RTS-GEO-4_mutation_tease_floor_is_staticbody3d",
			"MutationTeaseFloor type is " + floor_node.get_class() + ", expected StaticBody3D")
		var col: CollisionShape3D = _get_collision_shape(floor_node)
		if col != null:
			var shape: BoxShape3D = col.shape as BoxShape3D
			if shape != null:
				_assert_true(
					_near(shape.size.x, 30.0, GEO_TOL) and _near(shape.size.y, 1.0, GEO_TOL) and _near(shape.size.z, 10.0, GEO_TOL),
					"RTS-GEO-4_mutation_tease_floor_box_size",
					"BoxShape3D.size expected (30,1,10), got " + str(shape.size)
				)
			var top_y: float = _floor_top_y(floor_node as StaticBody3D)
			_assert_true(top_y >= -0.1 and top_y <= 0.1, "RTS-GEO-4_mutation_tease_floor_top_surface_y",
				"MutationTeaseFloor top surface Y = " + str(top_y) + ", expected in [-0.1, 0.1]")

	# Elevated platform
	var platform_node: Node = root.get_node_or_null("MutationTeasePlatform")
	_assert_true(platform_node != null, "RTS-GEO-4_mutation_tease_platform_exists", "MutationTeasePlatform not found")
	if platform_node != null:
		_assert_true(platform_node is StaticBody3D, "RTS-GEO-4_mutation_tease_platform_is_staticbody3d",
			"MutationTeasePlatform type is " + platform_node.get_class() + ", expected StaticBody3D")
		var p_col: CollisionShape3D = _get_collision_shape(platform_node)
		if p_col != null:
			var p_shape: BoxShape3D = p_col.shape as BoxShape3D
			if p_shape != null:
				_assert_true(
					_near(p_shape.size.x, 4.0, GEO_TOL) and _near(p_shape.size.y, 1.0, GEO_TOL) and _near(p_shape.size.z, 6.0, GEO_TOL),
					"RTS-GEO-4_mutation_tease_platform_box_size",
					"MutationTeasePlatform BoxShape3D.size expected (4,1,6), got " + str(p_shape.size)
				)
			var p_top_y: float = (platform_node as StaticBody3D).position.y + p_col.transform.origin.y + p_col.shape.size.y / 2.0
			_assert_true(p_top_y >= 0.6 and p_top_y <= 1.0, "RTS-GEO-4_mutation_tease_platform_top_surface_y",
				"MutationTeasePlatform top surface Y = " + str(p_top_y) + ", expected in [0.6, 1.0]")
	root.free()


# ---------------------------------------------------------------------------
# RTS-GEO-5: boss_01 BossFloor StaticBody3D, BoxShape3D (40,1,10) ±0.01,
#             top surface Y in [-0.1, 0.1]
# ---------------------------------------------------------------------------
func test_rts_geo_5_boss_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_BOSS_01, "RTS-GEO-5")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-GEO-5")
	if root == null:
		return
	var floor_node: Node = root.get_node_or_null("BossFloor")
	_assert_true(floor_node != null, "RTS-GEO-5_boss_floor_exists", "BossFloor not found")
	if floor_node != null:
		_assert_true(floor_node is StaticBody3D, "RTS-GEO-5_boss_floor_is_staticbody3d",
			"BossFloor type is " + floor_node.get_class() + ", expected StaticBody3D")
		var col: CollisionShape3D = _get_collision_shape(floor_node)
		_assert_true(col != null, "RTS-GEO-5_boss_floor_has_collision_shape", "No CollisionShape3D child found")
		if col != null:
			var shape: BoxShape3D = col.shape as BoxShape3D
			_assert_true(shape != null, "RTS-GEO-5_boss_floor_shape_is_boxshape3d",
				"CollisionShape3D.shape is not BoxShape3D")
			if shape != null:
				_assert_true(
					_near(shape.size.x, 40.0, GEO_TOL) and _near(shape.size.y, 1.0, GEO_TOL) and _near(shape.size.z, 10.0, GEO_TOL),
					"RTS-GEO-5_boss_floor_box_size",
					"BoxShape3D.size expected (40,1,10) ±" + str(GEO_TOL) + ", got " + str(shape.size)
				)
			var top_y: float = _floor_top_y(floor_node as StaticBody3D)
			_assert_true(top_y >= -0.1 and top_y <= 0.1, "RTS-GEO-5_boss_floor_top_surface_y",
				"BossFloor top surface Y = " + str(top_y) + ", expected in [-0.1, 0.1]")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENC-1: intro_01 has zero enemy children
#             (no node with "Enemy" in name anywhere in tree)
# ---------------------------------------------------------------------------
func test_rts_enc_1_intro_no_enemies() -> void:
	var packed: PackedScene = _load_packed(SCENE_INTRO_01, "RTS-ENC-1")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENC-1")
	if root == null:
		return
	var enemy_count: int = _count_enemy_nodes_recursive(root)
	_assert_true(enemy_count == 0, "RTS-ENC-1_intro_no_enemies",
		"Found " + str(enemy_count) + " node(s) with 'Enemy' in name; expected 0")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ENC-2: combat_01 has no embedded Enemy* runtime instance
#             and scene does not authoritatively reference enemy_infection_3d.tscn
# ---------------------------------------------------------------------------
func test_rts_enc_2_combat_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_01, "RTS-ENC-2")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENC-2")
	if root == null:
		return
	for child in root.get_children():
		var child_name: String = str(child.name)
		var is_spawn_anchor: bool = child_name.begins_with("EnemySpawn_")
		var is_entry_or_exit: bool = child_name == "Entry" or child_name == "Exit"
		var is_embedded_enemy: bool = child_name.begins_with("Enemy") and not is_spawn_anchor and not is_entry_or_exit
		_assert_false(is_embedded_enemy, "RTS-ENC-2_no_embedded_enemy_child_" + child_name,
			"RoomCombat01 must not embed authoritative enemy nodes")
	root.free()
	_assert_false(_room_tscn_references_enemy(SCENE_COMBAT_01), "RTS-ENC-2_no_embedded_enemy_scene_path_in_tscn",
		"room_combat_01.tscn should not authoritatively reference enemy_infection_3d.tscn")


# ---------------------------------------------------------------------------
# RTS-ENC-3: combat_02 has no embedded Enemy* runtime instance
#             and scene does not authoritatively reference enemy_infection_3d.tscn
# ---------------------------------------------------------------------------
func test_rts_enc_3_combat_02() -> void:
	var packed: PackedScene = _load_packed(SCENE_COMBAT_02, "RTS-ENC-3")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENC-3")
	if root == null:
		return
	for child in root.get_children():
		var child_name: String = str(child.name)
		var is_spawn_anchor: bool = child_name.begins_with("EnemySpawn_")
		var is_entry_or_exit: bool = child_name == "Entry" or child_name == "Exit"
		var is_embedded_enemy: bool = child_name.begins_with("Enemy") and not is_spawn_anchor and not is_entry_or_exit
		_assert_false(is_embedded_enemy, "RTS-ENC-3_no_embedded_enemy_child_" + child_name,
			"RoomCombat02 must not embed authoritative enemy nodes")
	root.free()
	_assert_false(_room_tscn_references_enemy(SCENE_COMBAT_02), "RTS-ENC-3_no_embedded_enemy_scene_path_in_tscn",
		"room_combat_02.tscn should not authoritatively reference enemy_infection_3d.tscn")


# ---------------------------------------------------------------------------
# RTS-ENC-4: mutation_tease_01 has EnemyMutationTease as direct child at (15, 1.3, 0) ±0.1
#             (on elevated platform)
# ---------------------------------------------------------------------------
func test_rts_enc_4_mutation_tease_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_MUTATION_TEASE_01, "RTS-ENC-4")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENC-4")
	if root == null:
		return
	var enemy: Node = root.get_node_or_null("EnemyMutationTease")
	_assert_true(enemy != null, "RTS-ENC-4_enemy_mutation_tease_exists",
		"EnemyMutationTease not found as direct child of RoomMutationTease01")
	if enemy != null:
		_assert_vec3_near((enemy as Node3D).position, Vector3(15.0, 1.3, 0.0), ENEMY_POS_TOL,
			"RTS-ENC-4_enemy_mutation_tease_position")
	root.free()
	_assert_true(_room_tscn_references_enemy(SCENE_MUTATION_TEASE_01), "RTS-ENC-4_enemy_scene_path_in_tscn",
		"room_mutation_tease_01.tscn does not reference enemy_infection_3d.tscn")


# ---------------------------------------------------------------------------
# RTS-ENC-5: boss_01 has EnemyBoss as direct child at (20, 0.5, 0) ±0.1
#             with scale (1.75, 1.75, 1.75) ±0.01
# ---------------------------------------------------------------------------
func test_rts_enc_5_boss_01() -> void:
	var packed: PackedScene = _load_packed(SCENE_BOSS_01, "RTS-ENC-5")
	if packed == null:
		return
	var root: Node = _instantiate(packed, "RTS-ENC-5")
	if root == null:
		return
	var enemy: Node = root.get_node_or_null("EnemyBoss")
	_assert_true(enemy != null, "RTS-ENC-5_enemy_boss_exists",
		"EnemyBoss not found as direct child of RoomBoss01")
	if enemy != null:
		_assert_vec3_near((enemy as Node3D).position, Vector3(20.0, 0.5, 0.0), ENEMY_POS_TOL,
			"RTS-ENC-5_enemy_boss_position")
		var expected_scale: Vector3 = Vector3(1.75, 1.75, 1.75)
		var actual_scale: Vector3 = (enemy as Node3D).scale
		_assert_true(
			_near(actual_scale.x, expected_scale.x, GEO_TOL) and
			_near(actual_scale.y, expected_scale.y, GEO_TOL) and
			_near(actual_scale.z, expected_scale.z, GEO_TOL),
			"RTS-ENC-5_enemy_boss_scale",
			"EnemyBoss scale expected ~(1.75,1.75,1.75), got " + str(actual_scale)
		)
	root.free()
	_assert_true(_room_tscn_references_enemy(SCENE_BOSS_01), "RTS-ENC-5_enemy_scene_path_in_tscn",
		"room_boss_01.tscn does not reference enemy_infection_3d.tscn")


# ---------------------------------------------------------------------------
# RTS-NO-PLAYER-1: none of the 5 rooms contain Player3D, RespawnZone,
#                  InfectionInteractionHandler, or InfectionUI anywhere in their tree
# ---------------------------------------------------------------------------
func test_rts_no_player_1_all_rooms() -> void:
	var all_scenes: Array[String] = [
		SCENE_INTRO_01,
		SCENE_COMBAT_01,
		SCENE_COMBAT_02,
		SCENE_MUTATION_TEASE_01,
		SCENE_BOSS_01,
	]
	var total_violations: int = 0
	for scene_path in all_scenes:
		var packed: PackedScene = ResourceLoader.load(scene_path) as PackedScene
		if packed == null:
			_fail_test("RTS-NO-PLAYER-1_load_" + scene_path.get_file(), "scene null: " + scene_path)
			total_violations += 1
			continue
		var root: Node = packed.instantiate()
		if root == null:
			_fail_test("RTS-NO-PLAYER-1_instantiate_" + scene_path.get_file(), "instantiate returned null")
			total_violations += 1
			continue
		var violations: Array = _find_forbidden_nodes(root, FORBIDDEN_NODE_NAMES)
		for v in violations:
			_fail_test("RTS-NO-PLAYER-1_forbidden_node",
				scene_path.get_file() + " contains forbidden node \"" + str(v[0]) + "\" at " + str(v[1]))
			total_violations += 1
		root.free()
	if total_violations == 0:
		_pass_test("RTS-NO-PLAYER-1_all_rooms_clean")


# ---------------------------------------------------------------------------
# run_all: entry point called by the test runner
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_room_templates.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_rts_load_1_intro_01()
	test_rts_load_2_combat_01()
	test_rts_load_3_combat_02()
	test_rts_load_4_mutation_tease_01()
	test_rts_load_5_boss_01()

	test_rts_struct_1_intro_01()
	test_rts_struct_2_combat_01()
	test_rts_struct_3_combat_02()
	test_rts_struct_4_mutation_tease_01()
	test_rts_struct_5_boss_01()

	test_rts_entry_1_intro_01()
	test_rts_entry_2_combat_01()
	test_rts_entry_3_combat_02()
	test_rts_entry_4_mutation_tease_01()
	test_rts_entry_5_boss_01()

	test_rts_exit_1_intro_01()
	test_rts_exit_2_combat_01()
	test_rts_exit_3_combat_02()
	test_rts_exit_4_mutation_tease_01()
	test_rts_exit_5_boss_01()

	test_rts_geo_1_intro_01()
	test_rts_geo_2_combat_01()
	test_rts_geo_3_combat_02()
	test_rts_geo_4_mutation_tease_01()
	test_rts_geo_5_boss_01()

	test_rts_enc_1_intro_no_enemies()
	test_rts_enc_2_combat_01()
	test_rts_enc_3_combat_02()
	test_rts_enc_4_mutation_tease_01()
	test_rts_enc_5_boss_01()

	test_rts_no_player_1_all_rooms()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
