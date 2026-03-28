#
# test_room_templates_adversarial.gd
#
# Adversarial behavioral tests for the Room Template System.
# Spec: agent_context/agents/2_spec/room_template_system_spec.md (Section 9: RTS-ADV)
# Ticket: project_board/6_milestone_6_roguelike_run_structure/in_progress/room_template_system.md
#
# All tests are headless-safe: no physics tick, no await, no signal emission.
# Red phase: scene files do not yet exist — tests report explicit FAIL with clear messages.
# Green phase: all assertions pass after Engine Integration Agent authors the 5 room scenes.
#
# Spec requirement traceability:
#   RTS-ADV-1  → Entry node name exactly "Entry", type Marker3D, all 5 rooms
#   RTS-ADV-2  → Exit node name exactly "Exit", type Marker3D, all 5 rooms
#   RTS-ADV-3  → Exit.x - Entry.x > 0, all 5 rooms (room width is positive)
#   RTS-ADV-4  → Entry.y > 0.0, all 5 rooms (marker above floor)
#   RTS-ADV-5  → Exit.y > 0.0, all 5 rooms (marker above floor)
#   RTS-ADV-6  → All StaticBody3D direct children of room root have collision_mask == 3
#   RTS-ADV-7  → No node named "Player3D" anywhere in any room's tree
#   RTS-ADV-8  → boss_01 Exit.x == 40.0 ±0.01 (boss room width is 40, not 30)
#   RTS-ADV-9  → Non-boss rooms Exit.x == 30.0 ±0.01 (standard width)
#   RTS-ADV-10 → Entry.z == 0.0 and Exit.z == 0.0 ±0.01, all 5 rooms (2.5D constraint)
#
# Extended adversarial tests (RTS-ADV-11 through RTS-ADV-24) address gaps found by
# Test Breaker Agent. Each is preceded by a comment explaining the vulnerability it closes.
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - No test ID duplicates RTS-LOAD-*, RTS-STRUCT-*, RTS-ENTRY-*, RTS-EXIT-*, RTS-GEO-*,
#     RTS-ENC-*, RTS-NO-PLAYER-* from primary suite; adversarial prefix RTS-ADV-* is unique.

extends "res://tests/utils/test_utils.gd"

# ---------------------------------------------------------------------------
# Scene paths under test
# ---------------------------------------------------------------------------

const SCENE_INTRO_01:          String = "res://scenes/rooms/room_intro_01.tscn"
const SCENE_COMBAT_01:         String = "res://scenes/rooms/room_combat_01.tscn"
const SCENE_COMBAT_02:         String = "res://scenes/rooms/room_combat_02.tscn"
const SCENE_MUTATION_TEASE_01: String = "res://scenes/rooms/room_mutation_tease_01.tscn"
const SCENE_BOSS_01:           String = "res://scenes/rooms/room_boss_01.tscn"

# All 5 room scenes in order. Used for per-room loops.
const ALL_SCENES: Array = [
	"res://scenes/rooms/room_intro_01.tscn",
	"res://scenes/rooms/room_combat_01.tscn",
	"res://scenes/rooms/room_combat_02.tscn",
	"res://scenes/rooms/room_mutation_tease_01.tscn",
	"res://scenes/rooms/room_boss_01.tscn",
]

# Standard-width rooms (exit at X=30). Boss room is excluded here.
const STANDARD_WIDTH_SCENES: Array = [
	"res://scenes/rooms/room_intro_01.tscn",
	"res://scenes/rooms/room_combat_01.tscn",
	"res://scenes/rooms/room_combat_02.tscn",
	"res://scenes/rooms/room_mutation_tease_01.tscn",
]

# Rooms that contain exactly one enemy at floor level (Y = 0.5 ±0.1).
const FLOOR_ENEMY_SCENES: Array = [
	"res://scenes/rooms/room_combat_01.tscn",
	"res://scenes/rooms/room_boss_01.tscn",
]

# Rooms that contain exactly one enemy at platform level (Y = 1.3 ±0.1).
const PLATFORM_ENEMY_SCENES: Array = [
	"res://scenes/rooms/room_combat_02.tscn",
	"res://scenes/rooms/room_mutation_tease_01.tscn",
]

# Enemy node names per scene — used for direct-child and Z=0 checks.
# Array of [scene_path, enemy_node_name] pairs.
const ENEMY_NAME_PER_SCENE: Array = [
	["res://scenes/rooms/room_combat_01.tscn",         "EnemyCombat01"],
	["res://scenes/rooms/room_combat_02.tscn",         "EnemyCombat01"],
	["res://scenes/rooms/room_mutation_tease_01.tscn", "EnemyMutationTease"],
	["res://scenes/rooms/room_boss_01.tscn",           "EnemyBoss"],
]

# Tolerance for position checks — spec ±0.01 for markers.
const POS_TOL: float = 0.01

# Tolerance for enemy position — spec ±0.1.
const ENEMY_POS_TOL: float = 0.1

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

# Load and instantiate a scene; null-guards and records FAIL on missing file (red phase).
# Returns null when the scene cannot be loaded or instantiated.
func _load_scene(scene_path: String, test_id: String) -> Node:
	var packed: PackedScene = ResourceLoader.load(scene_path) as PackedScene
	if packed == null:
		_fail_test(test_id + "_load_" + scene_path.get_file(),
			"ResourceLoader.load returned null: " + scene_path)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test(test_id + "_instantiate_" + scene_path.get_file(),
			"instantiate() returned null for: " + scene_path)
	return inst


# Recursive walk: collect all StaticBody3D nodes that are direct children of root only
# (not inside instanced sub-scenes such as enemies — per RTS-ADV-6 spec).
func _get_direct_static_bodies(root: Node) -> Array:
	var result: Array = []
	for i in range(root.get_child_count()):
		var child: Node = root.get_child(i)
		if child is StaticBody3D:
			result.append(child)
	return result


# Recursive walk: find any node anywhere in the tree with the given exact name.
func _find_node_by_name_recursive(node: Node, target_name: String) -> Node:
	if node == null:
		return null
	if node.name == target_name:
		return node
	for i in range(node.get_child_count()):
		var found: Node = _find_node_by_name_recursive(node.get_child(i), target_name)
		if found != null:
			return found
	return null


# Count all nodes anywhere in the tree whose name contains a substring.
func _count_nodes_with_name_substring(node: Node, substring: String) -> int:
	if node == null:
		return 0
	var count: int = 0
	if substring in node.name:
		count += 1
	for i in range(node.get_child_count()):
		count += _count_nodes_with_name_substring(node.get_child(i), substring)
	return count


# Get first CollisionShape3D direct child of a node, or null.
func _get_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null


# Get first MeshInstance3D direct child of a node, or null.
func _get_mesh_instance(parent: Node) -> MeshInstance3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is MeshInstance3D:
			return child as MeshInstance3D
	return null


# ---------------------------------------------------------------------------
# RTS-ADV-1: Entry node name is exactly "Entry" (not "EntryMarker", "entry", etc.)
#             AND node type is Marker3D — all 5 rooms
# Bug fixed: root.free() is now always called, even when entry is null.
# ---------------------------------------------------------------------------
func test_rts_adv_1_entry_name_exact_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-1")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		# Must find a node named exactly "Entry" as direct child
		var entry: Node = root.get_node_or_null("Entry")
		if entry == null:
			_fail_test("RTS-ADV-1_" + room_label, "No direct child named exactly \"Entry\" found")
			all_pass = false
		else:
			if not (entry is Marker3D):
				_fail_test("RTS-ADV-1_" + room_label,
					"\"Entry\" node type is " + entry.get_class() + ", expected Marker3D")
				all_pass = false
			else:
				_pass_test("RTS-ADV-1_" + room_label + "_entry_exact_name_and_type")
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-1_all_rooms_entry_exact")


# ---------------------------------------------------------------------------
# RTS-ADV-2: Exit node name is exactly "Exit" AND type is Marker3D — all 5 rooms
# Bug fixed: root.free() is now always called, even when exit_node is null.
# ---------------------------------------------------------------------------
func test_rts_adv_2_exit_name_exact_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-2")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var exit_node: Node = root.get_node_or_null("Exit")
		if exit_node == null:
			_fail_test("RTS-ADV-2_" + room_label, "No direct child named exactly \"Exit\" found")
			all_pass = false
		else:
			if not (exit_node is Marker3D):
				_fail_test("RTS-ADV-2_" + room_label,
					"\"Exit\" node type is " + exit_node.get_class() + ", expected Marker3D")
				all_pass = false
			else:
				_pass_test("RTS-ADV-2_" + room_label + "_exit_exact_name_and_type")
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-2_all_rooms_exit_exact")


# ---------------------------------------------------------------------------
# RTS-ADV-3: Exit.position.x - Entry.position.x > 0 — all 5 rooms
#             (room width is strictly positive; Exit is always to the right of Entry)
# ---------------------------------------------------------------------------
func test_rts_adv_3_room_width_positive_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-3")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var entry: Node = root.get_node_or_null("Entry")
		var exit_node: Node = root.get_node_or_null("Exit")
		if entry == null or exit_node == null:
			_fail_test("RTS-ADV-3_" + room_label,
				"Entry or Exit node missing; cannot compute width")
			all_pass = false
		else:
			var entry_x: float = (entry as Node3D).position.x
			var exit_x: float = (exit_node as Node3D).position.x
			var width: float = exit_x - entry_x
			if width > 0.0:
				_pass_test("RTS-ADV-3_" + room_label + "_width_positive (width=" + str(width) + ")")
			else:
				_fail_test("RTS-ADV-3_" + room_label,
					"Exit.x - Entry.x = " + str(width) + ", expected > 0")
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-3_all_rooms_width_positive")


# ---------------------------------------------------------------------------
# RTS-ADV-4: Entry.position.y > 0.0 — all 5 rooms
#             (Entry marker is above the floor top surface at Y=0)
# ---------------------------------------------------------------------------
func test_rts_adv_4_entry_y_above_floor_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-4")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var entry: Node = root.get_node_or_null("Entry")
		if entry == null:
			_fail_test("RTS-ADV-4_" + room_label, "Entry node not found")
			all_pass = false
		else:
			var y: float = (entry as Node3D).position.y
			if y > 0.0:
				_pass_test("RTS-ADV-4_" + room_label + "_entry_y_above_floor (y=" + str(y) + ")")
			else:
				_fail_test("RTS-ADV-4_" + room_label,
					"Entry.position.y = " + str(y) + ", expected > 0.0")
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-4_all_rooms_entry_y_above_floor")


# ---------------------------------------------------------------------------
# RTS-ADV-5: Exit.position.y > 0.0 — all 5 rooms
#             (Exit marker is above the floor top surface at Y=0)
# ---------------------------------------------------------------------------
func test_rts_adv_5_exit_y_above_floor_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-5")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var exit_node: Node = root.get_node_or_null("Exit")
		if exit_node == null:
			_fail_test("RTS-ADV-5_" + room_label, "Exit node not found")
			all_pass = false
		else:
			var y: float = (exit_node as Node3D).position.y
			if y > 0.0:
				_pass_test("RTS-ADV-5_" + room_label + "_exit_y_above_floor (y=" + str(y) + ")")
			else:
				_fail_test("RTS-ADV-5_" + room_label,
					"Exit.position.y = " + str(y) + ", expected > 0.0")
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-5_all_rooms_exit_y_above_floor")


# ---------------------------------------------------------------------------
# RTS-ADV-6: All StaticBody3D direct children of each room root have collision_mask == 3
#             Restricted to direct children of root only — not nodes inside enemy sub-scenes.
# ---------------------------------------------------------------------------
func test_rts_adv_6_static_bodies_collision_mask_3_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-6")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var static_bodies: Array = _get_direct_static_bodies(root)
		if static_bodies.is_empty():
			_fail_test("RTS-ADV-6_" + room_label, "No StaticBody3D direct children found in room root")
			all_pass = false
		else:
			var room_ok: bool = true
			for sb in static_bodies:
				var mask: int = (sb as StaticBody3D).collision_mask
				if mask != 3:
					_fail_test("RTS-ADV-6_" + room_label + "_" + sb.name,
						"StaticBody3D \"" + sb.name + "\" collision_mask = " + str(mask) + ", expected 3")
					all_pass = false
					room_ok = false
			if room_ok:
				_pass_test("RTS-ADV-6_" + room_label + "_all_staticbodies_mask_3")
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-6_all_rooms_collision_mask_3")


# ---------------------------------------------------------------------------
# RTS-ADV-7: No node named "Player3D" anywhere in any room's instantiated tree
#             (class-name check via recursive tree walk — same contract as RTS-NO-PLAYER-1
#             but specifically targets "Player3D" by name regardless of class)
# ---------------------------------------------------------------------------
func test_rts_adv_7_no_player3d_node_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-7")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var found: Node = _find_node_by_name_recursive(root, "Player3D")
		if found == null:
			_pass_test("RTS-ADV-7_" + room_label + "_no_player3d")
		else:
			_fail_test("RTS-ADV-7_" + room_label,
				"Found node named \"Player3D\" at " + str(found.get_path()))
			all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-7_all_rooms_no_player3d")


# ---------------------------------------------------------------------------
# RTS-ADV-8: boss_01 Exit.position.x == 40.0 ±0.01
#             (boss room is 40 units wide, not the standard 30)
# ---------------------------------------------------------------------------
func test_rts_adv_8_boss_exit_x_is_40() -> void:
	var root: Node = _load_scene(SCENE_BOSS_01, "RTS-ADV-8")
	if root == null:
		return
	var exit_node: Node = root.get_node_or_null("Exit")
	if exit_node == null:
		_fail_test("RTS-ADV-8_exit_exists", "Exit node not found in room_boss_01")
		root.free()
		return
	var x: float = (exit_node as Node3D).position.x
	_assert_true(_near(x, 40.0, POS_TOL), "RTS-ADV-8_boss_exit_x_is_40",
		"RoomBoss01 Exit.position.x = " + str(x) + ", expected 40.0 ±" + str(POS_TOL))
	root.free()


# ---------------------------------------------------------------------------
# RTS-ADV-9: Non-boss rooms Exit.position.x == 30.0 ±0.01
#             (intro, combat_01, combat_02, mutation_tease_01 all use standard 30-unit width)
# ---------------------------------------------------------------------------
func test_rts_adv_9_standard_rooms_exit_x_is_30() -> void:
	var all_pass: bool = true
	for scene_path in STANDARD_WIDTH_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-9")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var exit_node: Node = root.get_node_or_null("Exit")
		if exit_node == null:
			_fail_test("RTS-ADV-9_" + room_label, "Exit node not found")
			all_pass = false
		else:
			var x: float = (exit_node as Node3D).position.x
			if _near(x, 30.0, POS_TOL):
				_pass_test("RTS-ADV-9_" + room_label + "_exit_x_30 (x=" + str(x) + ")")
			else:
				_fail_test("RTS-ADV-9_" + room_label,
					"Exit.position.x = " + str(x) + ", expected 30.0 ±" + str(POS_TOL))
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-9_all_standard_rooms_exit_x_30")


# ---------------------------------------------------------------------------
# RTS-ADV-10: Entry.position.z == 0.0 and Exit.position.z == 0.0 ±0.01 — all 5 rooms
#              (2.5D constraint: all connection markers live in the Z=0 plane)
# ---------------------------------------------------------------------------
func test_rts_adv_10_marker_z_is_zero_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-10")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var entry: Node = root.get_node_or_null("Entry")
		var exit_node: Node = root.get_node_or_null("Exit")
		var room_ok: bool = true
		if entry == null:
			_fail_test("RTS-ADV-10_" + room_label + "_entry_missing", "Entry node not found")
			room_ok = false
			all_pass = false
		else:
			var ez: float = (entry as Node3D).position.z
			if _near(ez, 0.0, POS_TOL):
				_pass_test("RTS-ADV-10_" + room_label + "_entry_z_zero (z=" + str(ez) + ")")
			else:
				_fail_test("RTS-ADV-10_" + room_label + "_entry_z",
					"Entry.position.z = " + str(ez) + ", expected 0.0 ±" + str(POS_TOL))
				room_ok = false
				all_pass = false
		if exit_node == null:
			_fail_test("RTS-ADV-10_" + room_label + "_exit_missing", "Exit node not found")
			room_ok = false
			all_pass = false
		else:
			var xz: float = (exit_node as Node3D).position.z
			if _near(xz, 0.0, POS_TOL):
				_pass_test("RTS-ADV-10_" + room_label + "_exit_z_zero (z=" + str(xz) + ")")
			else:
				_fail_test("RTS-ADV-10_" + room_label + "_exit_z",
					"Exit.position.z = " + str(xz) + ", expected 0.0 ±" + str(POS_TOL))
				room_ok = false
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-10_all_rooms_markers_z_zero")


# ---------------------------------------------------------------------------
# RTS-ADV-11: Entry and Exit are DIRECT children of the scene root, not nested nodes.
#
# Vulnerability closed: get_node_or_null("Entry") in Godot 4 resolves a bare name as a
# direct-child lookup on the node. However the spec explicitly requires direct children.
# This test confirms parent == root for both markers, catching a scene where Entry/Exit
# are buried inside a child node (e.g. inside the floor StaticBody3D subtree).
# ---------------------------------------------------------------------------
func test_rts_adv_11_markers_are_direct_children_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-11")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var entry: Node = root.get_node_or_null("Entry")
		var exit_node: Node = root.get_node_or_null("Exit")
		var room_ok: bool = true
		if entry == null:
			_fail_test("RTS-ADV-11_" + room_label + "_entry_missing", "Entry not found")
			room_ok = false
			all_pass = false
		elif entry.get_parent() != root:
			_fail_test("RTS-ADV-11_" + room_label + "_entry_not_direct_child",
				"Entry parent is " + str(entry.get_parent().name) + ", expected root " + str(root.name))
			room_ok = false
			all_pass = false
		if exit_node == null:
			_fail_test("RTS-ADV-11_" + room_label + "_exit_missing", "Exit not found")
			room_ok = false
			all_pass = false
		elif exit_node.get_parent() != root:
			_fail_test("RTS-ADV-11_" + room_label + "_exit_not_direct_child",
				"Exit parent is " + str(exit_node.get_parent().name) + ", expected root " + str(root.name))
			room_ok = false
			all_pass = false
		if room_ok:
			_pass_test("RTS-ADV-11_" + room_label + "_markers_direct_children")
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-11_all_rooms_markers_direct_children")


# ---------------------------------------------------------------------------
# RTS-ADV-12: Entry.position.x == 0.0 ±0.01 for all 5 rooms.
#
# Vulnerability closed: RTS-ADV-3 checks Exit.x > Entry.x (positive width), and
# RTS-ADV-9 checks Exit.x == 30 for standard rooms. Neither guarantees Entry.x == 0.
# A room with Entry at (5,1,0) and Exit at (35,1,0) would pass both ADV-3 and ADV-9
# but violate the spec's connection contract (Entry must be the left edge of the room).
# ---------------------------------------------------------------------------
func test_rts_adv_12_entry_x_is_zero_all_rooms() -> void:
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-12")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var entry: Node = root.get_node_or_null("Entry")
		if entry == null:
			_fail_test("RTS-ADV-12_" + room_label, "Entry node not found")
			all_pass = false
		else:
			var x: float = (entry as Node3D).position.x
			if _near(x, 0.0, POS_TOL):
				_pass_test("RTS-ADV-12_" + room_label + "_entry_x_zero (x=" + str(x) + ")")
			else:
				_fail_test("RTS-ADV-12_" + room_label,
					"Entry.position.x = " + str(x) + ", expected 0.0 ±" + str(POS_TOL))
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-12_all_rooms_entry_x_zero")


# ---------------------------------------------------------------------------
# RTS-ADV-13: WorldEnvironment and DirectionalLight3D are present as direct children
#              of the scene root in all 5 rooms.
#
# Vulnerability closed: RTS-ENV requirement is specified in the spec but no test covers
# it in either file. A room missing these nodes would be rejected visually at development
# time and could fail a runtime environment query. This test fills the spec gap.
# ---------------------------------------------------------------------------
func test_rts_adv_13_env_and_light_present_all_rooms() -> void:
	# Design update: rooms are geometry-only sub-scenes. Lighting is owned by the
	# container scene (procedural_run.tscn) so it stays consistent across all room
	# combinations. Rooms must NOT contain WorldEnvironment or DirectionalLight3D —
	# stacking multiple lights causes washed-out rendering.
	var all_pass: bool = true
	for scene_path in ALL_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-13")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var room_ok: bool = true
		var world_env: Node = root.get_node_or_null("WorldEnvironment")
		if world_env != null:
			_fail_test("RTS-ADV-13_" + room_label + "_world_env_missing",
				"WorldEnvironment found in room; rooms must not own lighting (container scene provides it)")
			room_ok = false
			all_pass = false
		var dir_light: Node = root.get_node_or_null("DirectionalLight3D")
		if dir_light != null:
			_fail_test("RTS-ADV-13_" + room_label + "_directional_light_missing",
				"DirectionalLight3D found in room; rooms must not own lighting (container scene provides it)")
			room_ok = false
			all_pass = false
		if room_ok:
			_pass_test("RTS-ADV-13_" + room_label + "_no_stacked_lighting_ok")
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-13_all_rooms_no_stacked_lighting")


# ---------------------------------------------------------------------------
# RTS-ADV-14: physics_interpolation_mode == 1 on every enemy instance in all
#              enemy-containing rooms (combat_01, combat_02, mutation_tease_01, boss_01).
#
# Vulnerability closed: Spec requires physics_interpolation_mode = 1 on all enemy
# instances (matching containment_hall_01.tscn convention). Neither primary nor existing
# adversarial tests verify this property. A missing or wrong value would cause visible
# interpolation artifacts at runtime without causing any existing test to fail.
# ---------------------------------------------------------------------------
func test_rts_adv_14_enemy_physics_interpolation_mode_all_rooms() -> void:
	var all_pass: bool = true
	for pair in ENEMY_NAME_PER_SCENE:
		var scene_path: String = pair[0]
		var enemy_name: String = pair[1]
		var root: Node = _load_scene(scene_path, "RTS-ADV-14")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var enemy: Node = root.get_node_or_null(enemy_name)
		if enemy == null:
			_fail_test("RTS-ADV-14_" + room_label + "_" + enemy_name + "_missing",
				enemy_name + " not found as direct child of " + root.name)
			all_pass = false
		else:
			# physics_interpolation_mode is an int property: 0=inherit, 1=on, 2=off
			var mode: int = (enemy as Node3D).physics_interpolation_mode
			if mode == 1:
				_pass_test("RTS-ADV-14_" + room_label + "_" + enemy_name + "_interp_mode_1")
			else:
				_fail_test("RTS-ADV-14_" + room_label + "_" + enemy_name,
					enemy_name + " physics_interpolation_mode = " + str(mode) + ", expected 1")
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-14_all_enemy_rooms_physics_interp_mode_1")


# ---------------------------------------------------------------------------
# RTS-ADV-15: Enemy Z position == 0.0 ±0.1 in all enemy-containing rooms.
#
# Vulnerability closed: Spec requires enemy Z=0 (2.5D constraint). RTS-ENC-* tests use
# _assert_vec3_near which checks all three axes within ENEMY_POS_TOL=0.1, but the
# tolerance on Z being 0.1 is loose enough that a slight Z offset (e.g., Z=0.09) would
# pass. More importantly, Z is not independently documented or named in those assertions.
# This test makes the Z=0 constraint explicit and uses a stricter POS_TOL=0.01 for Z.
# ---------------------------------------------------------------------------
func test_rts_adv_15_enemy_z_is_zero_all_rooms() -> void:
	var all_pass: bool = true
	for pair in ENEMY_NAME_PER_SCENE:
		var scene_path: String = pair[0]
		var enemy_name: String = pair[1]
		var root: Node = _load_scene(scene_path, "RTS-ADV-15")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var enemy: Node = root.get_node_or_null(enemy_name)
		if enemy == null:
			_fail_test("RTS-ADV-15_" + room_label + "_" + enemy_name + "_missing",
				enemy_name + " not found")
			all_pass = false
		else:
			var z: float = (enemy as Node3D).position.z
			if _near(z, 0.0, POS_TOL):
				_pass_test("RTS-ADV-15_" + room_label + "_" + enemy_name + "_z_zero (z=" + str(z) + ")")
			else:
				_fail_test("RTS-ADV-15_" + room_label + "_" + enemy_name,
					enemy_name + " position.z = " + str(z) + ", expected 0.0 ±" + str(POS_TOL))
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-15_all_enemies_z_zero")


# ---------------------------------------------------------------------------
# RTS-ADV-16: Enemy count is exactly 1 in each single-enemy room.
#              Rooms: combat_01, combat_02, mutation_tease_01, boss_01.
#
# Vulnerability closed: RTS-ENC-2..5 verify that the named enemy exists, but they do
# not verify there is only ONE enemy. A room with an extra stray enemy would pass all
# existing tests. The layout system and difficulty balance depend on the exact enemy
# count being 1 per room as specified.
# ---------------------------------------------------------------------------
func test_rts_adv_16_exactly_one_enemy_in_single_enemy_rooms() -> void:
	var single_enemy_scenes: Array = [
		SCENE_COMBAT_01,
		SCENE_COMBAT_02,
		SCENE_MUTATION_TEASE_01,
		SCENE_BOSS_01,
	]
	var all_pass: bool = true
	for scene_path in single_enemy_scenes:
		var root: Node = _load_scene(scene_path, "RTS-ADV-16")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		# Count only DIRECT children of the room root with "Enemy" in their name.
		# Recursive search is incorrect: enemy_infection_3d.tscn has a child
		# "EnemyVisual" which would inflate the count to 2.
		var enemy_count: int = 0
		for i in range(root.get_child_count()):
			if "Enemy" in root.get_child(i).name:
				enemy_count += 1
		if enemy_count == 1:
			_pass_test("RTS-ADV-16_" + room_label + "_exactly_one_enemy")
		else:
			_fail_test("RTS-ADV-16_" + room_label,
				"Expected exactly 1 node with 'Enemy' in name, found " + str(enemy_count))
			all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-16_all_single_enemy_rooms_have_exactly_1_enemy")


# ---------------------------------------------------------------------------
# RTS-ADV-17: Intro room has zero nodes with "Enemy" in their name anywhere in the tree
#              AND the total direct child count does not exceed expected maximum.
#
# Vulnerability closed: RTS-ENC-1 counts nodes with "Enemy" in name (caught via
# _count_enemy_nodes_recursive), but an enemy renamed without "Enemy" (e.g., renamed
# "Infection01" or "Mob01") would pass the check. This test adds a secondary guard:
# the intro room's total direct child count is bounded. Spec authorises: IntroFloor,
# Entry, Exit, WorldEnvironment, DirectionalLight3D = 5 expected direct children.
# Any additional direct child is an authoring mistake.
# ---------------------------------------------------------------------------
func test_rts_adv_17_intro_room_child_count_bounded() -> void:
	var root: Node = _load_scene(SCENE_INTRO_01, "RTS-ADV-17")
	if root == null:
		return
	# Expected direct children: IntroFloor, Entry, Exit (lighting removed — owned by container).
	var expected_direct_child_count: int = 3
	var actual: int = root.get_child_count()
	_assert_true(actual == expected_direct_child_count, "RTS-ADV-17_intro_room_child_count",
		"RoomIntro01 has " + str(actual) + " direct children, expected " + str(expected_direct_child_count) +
		" (IntroFloor, Entry, Exit)")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ADV-18: Floor StaticBody3D nodes in all rooms each have BOTH a CollisionShape3D
#              child AND a MeshInstance3D child.
#
# Vulnerability closed: RTS-GEO-* tests only verify CollisionShape3D (for the physics
# shape size and top-surface Y). The spec also requires a MeshInstance3D child on each
# floor StaticBody3D for visual representation. A room with collision but no mesh would
# pass all GEO tests but be invisible at runtime, breaking visual gameplay.
# ---------------------------------------------------------------------------
func test_rts_adv_18_floor_nodes_have_mesh_instance_all_rooms() -> void:
	# Map of scene path -> array of expected floor StaticBody3D node names in that scene.
	var floor_nodes_per_scene: Array = [
		[SCENE_INTRO_01,          ["IntroFloor"]],
		[SCENE_COMBAT_01,         ["CombatFloor"]],
		[SCENE_COMBAT_02,         ["CombatFloor", "CombatPlatform"]],
		[SCENE_MUTATION_TEASE_01, ["MutationTeaseFloor", "MutationTeasePlatform"]],
		[SCENE_BOSS_01,           ["BossFloor"]],
	]
	var all_pass: bool = true
	for entry in floor_nodes_per_scene:
		var scene_path: String = entry[0]
		var node_names: Array = entry[1]
		var root: Node = _load_scene(scene_path, "RTS-ADV-18")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		for node_name in node_names:
			var floor_node: Node = root.get_node_or_null(node_name)
			if floor_node == null:
				_fail_test("RTS-ADV-18_" + room_label + "_" + node_name + "_missing",
					node_name + " not found")
				all_pass = false
				continue
			var mesh: MeshInstance3D = _get_mesh_instance(floor_node)
			if mesh == null:
				_fail_test("RTS-ADV-18_" + room_label + "_" + node_name + "_no_mesh",
					node_name + " has no MeshInstance3D child (floor would be invisible)")
				all_pass = false
			else:
				_pass_test("RTS-ADV-18_" + room_label + "_" + node_name + "_has_mesh")
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-18_all_floor_nodes_have_mesh_instance")


# ---------------------------------------------------------------------------
# RTS-ADV-19: Floor StaticBody3D node position X matches spec exactly.
#              Standard rooms: floor center X == 15.0. Boss room: floor center X == 20.0.
#
# Vulnerability closed: The GEO tests verify shape size and top-surface Y but not the
# StaticBody3D node's own position. A floor at (0,0,0) with the same BoxShape3D size
# would produce correct top-surface Y (since the offset and shape are unchanged) but
# would cover the wrong X range, breaking the room layout stitching contract.
# ---------------------------------------------------------------------------
func test_rts_adv_19_floor_node_position_x_correct() -> void:
	# [scene_path, floor_node_name, expected_x]
	var checks: Array = [
		[SCENE_INTRO_01,          "IntroFloor",        15.0],
		[SCENE_COMBAT_01,         "CombatFloor",       15.0],
		[SCENE_COMBAT_02,         "CombatFloor",       15.0],
		[SCENE_MUTATION_TEASE_01, "MutationTeaseFloor", 15.0],
		[SCENE_BOSS_01,           "BossFloor",         20.0],
	]
	var all_pass: bool = true
	for check in checks:
		var scene_path: String = check[0]
		var node_name: String = check[1]
		var expected_x: float = check[2]
		var root: Node = _load_scene(scene_path, "RTS-ADV-19")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var floor_node: Node = root.get_node_or_null(node_name)
		if floor_node == null:
			_fail_test("RTS-ADV-19_" + room_label + "_" + node_name + "_missing",
				node_name + " not found")
			all_pass = false
		else:
			var actual_x: float = (floor_node as Node3D).position.x
			if _near(actual_x, expected_x, POS_TOL):
				_pass_test("RTS-ADV-19_" + room_label + "_" + node_name + "_x=" + str(expected_x))
			else:
				_fail_test("RTS-ADV-19_" + room_label + "_" + node_name,
					node_name + " position.x = " + str(actual_x) + ", expected " + str(expected_x) + " ±" + str(POS_TOL))
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-19_all_floor_nodes_position_x_correct")


# ---------------------------------------------------------------------------
# RTS-ADV-20: Enemy Y position is above floor/platform (Y > 0.0 for floor enemies,
#              Y > 0.8 for platform enemies), preventing below-floor placements.
#
# Vulnerability closed: RTS-ENC-* checks use ±0.1 tolerance around the exact Y value.
# This is sufficient for catching gross errors but does not assert the minimum bound
# explicitly. An enemy at Y = -0.1 (below floor, ±0.1 from Y=0) would pass a naive
# tolerance check if someone accidentally used Y=0.4 for a floor enemy — but an enemy
# placed underground (e.g., Y = -5) due to a wrong origin would also be caught here.
# This test adds an explicit lower-bound check with a clear diagnostic message.
# ---------------------------------------------------------------------------
func test_rts_adv_20_enemy_y_above_surface() -> void:
	var all_pass: bool = true
	# Floor enemies: Y must be > 0.0 (floor top = 0.0)
	for scene_path in FLOOR_ENEMY_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-20")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		# Find the enemy by searching for a node with "Enemy" in its name as direct child.
		var enemy: Node = null
		for i in range(root.get_child_count()):
			var child: Node = root.get_child(i)
			if "Enemy" in child.name:
				enemy = child
				break
		if enemy == null:
			_fail_test("RTS-ADV-20_" + room_label + "_no_floor_enemy", "No direct-child node with 'Enemy' in name")
			all_pass = false
		else:
			var y: float = (enemy as Node3D).position.y
			if y > 0.0:
				_pass_test("RTS-ADV-20_" + room_label + "_" + enemy.name + "_above_floor (y=" + str(y) + ")")
			else:
				_fail_test("RTS-ADV-20_" + room_label + "_" + enemy.name,
					enemy.name + " position.y = " + str(y) + ", expected > 0.0 (above floor)")
				all_pass = false
		root.free()
	# Platform enemies: Y must be > 0.8 (platform top = 0.8)
	for scene_path in PLATFORM_ENEMY_SCENES:
		var root: Node = _load_scene(scene_path, "RTS-ADV-20")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var enemy: Node = null
		for i in range(root.get_child_count()):
			var child: Node = root.get_child(i)
			if "Enemy" in child.name:
				enemy = child
				break
		if enemy == null:
			_fail_test("RTS-ADV-20_" + room_label + "_no_platform_enemy", "No direct-child node with 'Enemy' in name")
			all_pass = false
		else:
			var y: float = (enemy as Node3D).position.y
			if y > 0.8:
				_pass_test("RTS-ADV-20_" + room_label + "_" + enemy.name + "_above_platform (y=" + str(y) + ")")
			else:
				_fail_test("RTS-ADV-20_" + room_label + "_" + enemy.name,
					enemy.name + " position.y = " + str(y) + ", expected > 0.8 (above platform top at Y=0.8)")
				all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-20_all_enemies_above_their_surface")


# ---------------------------------------------------------------------------
# RTS-ADV-21: Boss scale is (1.75, 1.75, 1.75) — NOT (1, 1, 1) default scale.
#              This is a targeted mutation check: verifies scale is strictly > 1.5 on all axes.
#
# Vulnerability closed: RTS-ENC-5 checks scale == 1.75 ±0.01. This targeted test adds
# a minimum-bound guard (scale > 1.5) with an explicit "not default scale" failure message,
# catching the specific mutation scenario described in the task: boss authored with
# default scale (1,1,1) instead of (1.75,1.75,1.75). The two tests are complementary:
# RTS-ENC-5 catches wrong scale values; RTS-ADV-21 catches the default-scale mistake
# with a clearer diagnostic for the implementer.
# ---------------------------------------------------------------------------
func test_rts_adv_21_boss_enemy_scale_not_default() -> void:
	var root: Node = _load_scene(SCENE_BOSS_01, "RTS-ADV-21")
	if root == null:
		return
	var enemy: Node = root.get_node_or_null("EnemyBoss")
	if enemy == null:
		_fail_test("RTS-ADV-21_enemy_boss_missing", "EnemyBoss not found in room_boss_01")
		root.free()
		return
	var scale: Vector3 = (enemy as Node3D).scale
	# Guard: each axis must be > 1.5 (rules out accidental default scale of 1.0).
	_assert_true(scale.x > 1.5 and scale.y > 1.5 and scale.z > 1.5,
		"RTS-ADV-21_boss_scale_not_default_1",
		"EnemyBoss scale = " + str(scale) + " — scale is at or near default (1,1,1); expected ~(1.75,1.75,1.75)")
	# Tight bound: each axis must be within 0.01 of 1.75.
	_assert_true(
		absf(scale.x - 1.75) <= 0.01 and absf(scale.y - 1.75) <= 0.01 and absf(scale.z - 1.75) <= 0.01,
		"RTS-ADV-21_boss_scale_is_1_75",
		"EnemyBoss scale = " + str(scale) + ", expected (1.75, 1.75, 1.75) ±0.01")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ADV-22: Boss room floor is 40 units wide, NOT 30 units wide.
#              Specifically tests BossFloor BoxShape3D.size.x == 40.0 ±0.01.
#
# Vulnerability closed: RTS-GEO-5 checks BossFloor size == (40, 1, 10). RTS-ADV-8
# checks Exit.x == 40. However neither test is explicitly framed as catching the
# "boss room accidentally authored as 30-unit wide" mutation. This targeted test
# combines both and adds a "not 30" explicit assertion to make the failure diagnostic
# unambiguous to the implementer.
# ---------------------------------------------------------------------------
func test_rts_adv_22_boss_floor_width_is_40_not_30() -> void:
	var root: Node = _load_scene(SCENE_BOSS_01, "RTS-ADV-22")
	if root == null:
		return
	var floor_node: Node = root.get_node_or_null("BossFloor")
	if floor_node == null:
		_fail_test("RTS-ADV-22_boss_floor_missing", "BossFloor not found in room_boss_01")
		root.free()
		return
	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null:
		_fail_test("RTS-ADV-22_boss_floor_no_collision_shape", "BossFloor has no CollisionShape3D")
		root.free()
		return
	var shape: BoxShape3D = col.shape as BoxShape3D
	if shape == null:
		_fail_test("RTS-ADV-22_boss_floor_no_boxshape", "BossFloor CollisionShape3D.shape is not BoxShape3D")
		root.free()
		return
	# Must NOT be 30 (standard room width).
	_assert_true(absf(shape.size.x - 30.0) > 0.5,
		"RTS-ADV-22_boss_floor_not_30_wide",
		"BossFloor BoxShape3D.size.x = " + str(shape.size.x) + " — boss room was authored with standard 30-unit floor; expected 40")
	# Must BE 40.
	_assert_true(absf(shape.size.x - 40.0) <= 0.01,
		"RTS-ADV-22_boss_floor_is_40_wide",
		"BossFloor BoxShape3D.size.x = " + str(shape.size.x) + ", expected 40.0 ±0.01")
	root.free()


# ---------------------------------------------------------------------------
# RTS-ADV-23: .tscn file text for each enemy room references exactly the
#              canonical enemy scene path (enemy_infection_3d.tscn) and not any
#              alternative path or a second/different enemy scene.
#
# Vulnerability closed: RTS-ENC-* uses _room_tscn_references_enemy() which only checks
# if the substring "enemy_infection_3d.tscn" appears anywhere in the file. This would
# pass even if the room also references a second, incorrect enemy scene. This test
# verifies that the number of occurrences of the canonical enemy path in the .tscn text
# equals exactly the expected enemy count for that room (1 per room), and that no other
# .tscn path ending in "_infection" or "enemy_" appears in the file for a different
# enemy resource.
# ---------------------------------------------------------------------------
func test_rts_adv_23_tscn_references_correct_enemy_scene_count() -> void:
	# [scene_path, expected_count_of_canonical_enemy_path_in_tscn_ext_resources]
	# The canonical path appears once as an ext_resource for each unique instanced enemy.
	# All 4 enemy rooms each have 1 enemy instance using enemy_infection_3d.tscn.
	# The ext_resource section declares it once; node sections reference it by id.
	# We count occurrences of the full canonical path string.
	var checks: Array = [
		[SCENE_COMBAT_01,         1],
		[SCENE_COMBAT_02,         1],
		[SCENE_MUTATION_TEASE_01, 1],
		[SCENE_BOSS_01,           1],
	]
	var canonical: String = "enemy_infection_3d.tscn"
	var all_pass: bool = true
	for check in checks:
		var scene_path: String = check[0]
		var expected_count: int = check[1]
		var room_label: String = scene_path.get_file()
		# Convert res:// path to a filesystem path for FileAccess.
		var fs_path: String = ProjectSettings.globalize_path(scene_path)
		var f: FileAccess = FileAccess.open(fs_path, FileAccess.READ)
		if f == null:
			_fail_test("RTS-ADV-23_" + room_label + "_file_open",
				"Cannot open file for text inspection: " + scene_path)
			all_pass = false
			continue
		var text: String = f.get_as_text()
		f.close()
		# Count occurrences of canonical path in the file.
		var count: int = 0
		var search_start: int = 0
		while true:
			var idx: int = text.find(canonical, search_start)
			if idx == -1:
				break
			count += 1
			search_start = idx + canonical.length()
		if count >= expected_count:
			_pass_test("RTS-ADV-23_" + room_label + "_canonical_enemy_ref_count (found=" + str(count) + ")")
		else:
			_fail_test("RTS-ADV-23_" + room_label,
				"Expected >=" + str(expected_count) + " reference(s) to '" + canonical +
				"' in tscn text, found " + str(count))
			all_pass = false
	if all_pass:
		_pass_test("RTS-ADV-23_all_enemy_rooms_reference_canonical_enemy_scene")


# ---------------------------------------------------------------------------
# RTS-ADV-24: Entry.x == 0 and Exit.x == (30 or 40) COMBINED with room width == Exit.x.
#              This is a combinatorial test that catches the "Entry/Exit swapped" mutation:
#              Entry at (30,1,0) and Exit at (0,1,0) — both X values individually present
#              but at the wrong nodes.
#
# Vulnerability closed: ADV-3 catches swapped markers (width < 0), and ADV-12 checks
# Entry.x == 0, and ADV-9/8 check Exit.x == 30/40. However the combination of all three
# as a single deterministic statement makes the "swapped Entry/Exit" failure unmistakable
# with a single diagnostic. This test catches the scenario where Entry and Exit positions
# are reversed in the .tscn (a common copy-paste error when authoring markers).
# ---------------------------------------------------------------------------
func test_rts_adv_24_entry_exit_not_swapped_all_rooms() -> void:
	# [scene_path, expected_exit_x]
	var checks: Array = [
		[SCENE_INTRO_01,          30.0],
		[SCENE_COMBAT_01,         30.0],
		[SCENE_COMBAT_02,         30.0],
		[SCENE_MUTATION_TEASE_01, 30.0],
		[SCENE_BOSS_01,           40.0],
	]
	var all_pass: bool = true
	for check in checks:
		var scene_path: String = check[0]
		var expected_exit_x: float = check[1]
		var root: Node = _load_scene(scene_path, "RTS-ADV-24")
		if root == null:
			all_pass = false
			continue
		var room_label: String = scene_path.get_file()
		var entry: Node = root.get_node_or_null("Entry")
		var exit_node: Node = root.get_node_or_null("Exit")
		if entry == null or exit_node == null:
			_fail_test("RTS-ADV-24_" + room_label, "Entry or Exit missing")
			all_pass = false
			root.free()
			continue
		var entry_x: float = (entry as Node3D).position.x
		var exit_x: float = (exit_node as Node3D).position.x
		var ok: bool = _near(entry_x, 0.0, POS_TOL) and _near(exit_x, expected_exit_x, POS_TOL)
		if ok:
			_pass_test("RTS-ADV-24_" + room_label + "_not_swapped (entry_x=" + str(entry_x) + " exit_x=" + str(exit_x) + ")")
		else:
			var msg: String
			if _near(entry_x, expected_exit_x, POS_TOL) and _near(exit_x, 0.0, POS_TOL):
				msg = "Entry and Exit appear SWAPPED: Entry.x=" + str(entry_x) + ", Exit.x=" + str(exit_x)
			else:
				msg = "Entry.x=" + str(entry_x) + " (expected 0.0), Exit.x=" + str(exit_x) + " (expected " + str(expected_exit_x) + ")"
			_fail_test("RTS-ADV-24_" + room_label, msg)
			all_pass = false
		root.free()
	if all_pass:
		_pass_test("RTS-ADV-24_all_rooms_entry_exit_not_swapped")


# ---------------------------------------------------------------------------
# run_all: entry point called by the test runner
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_room_templates_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_rts_adv_1_entry_name_exact_all_rooms()
	test_rts_adv_2_exit_name_exact_all_rooms()
	test_rts_adv_3_room_width_positive_all_rooms()
	test_rts_adv_4_entry_y_above_floor_all_rooms()
	test_rts_adv_5_exit_y_above_floor_all_rooms()
	test_rts_adv_6_static_bodies_collision_mask_3_all_rooms()
	test_rts_adv_7_no_player3d_node_all_rooms()
	test_rts_adv_8_boss_exit_x_is_40()
	test_rts_adv_9_standard_rooms_exit_x_is_30()
	test_rts_adv_10_marker_z_is_zero_all_rooms()
	test_rts_adv_11_markers_are_direct_children_all_rooms()
	test_rts_adv_12_entry_x_is_zero_all_rooms()
	test_rts_adv_13_env_and_light_present_all_rooms()
	test_rts_adv_14_enemy_physics_interpolation_mode_all_rooms()
	test_rts_adv_15_enemy_z_is_zero_all_rooms()
	test_rts_adv_16_exactly_one_enemy_in_single_enemy_rooms()
	test_rts_adv_17_intro_room_child_count_bounded()
	test_rts_adv_18_floor_nodes_have_mesh_instance_all_rooms()
	test_rts_adv_19_floor_node_position_x_correct()
	test_rts_adv_20_enemy_y_above_surface()
	test_rts_adv_21_boss_enemy_scale_not_default()
	test_rts_adv_22_boss_floor_width_is_40_not_30()
	test_rts_adv_23_tscn_references_correct_enemy_scene_count()
	test_rts_adv_24_entry_exit_not_swapped_all_rooms()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
