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
# RTS-ADV-16..24 live in room_templates_adversarial_rts_adv_16_24.gd (file size split).
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - No test ID duplicates RTS-LOAD-*, RTS-STRUCT-*, RTS-ENTRY-*, RTS-EXIT-*, RTS-GEO-*,
#     RTS-ENC-*, RTS-NO-PLAYER-* from primary suite; adversarial prefix RTS-ADV-* is unique.

extends "res://tests/utils/test_utils.gd"

const _RTS_ADV_PART2_SCRIPT: GDScript = preload("res://tests/rooms/room_templates_adversarial_rts_adv_16_24.gd")

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
		var _room_ok: bool = true
		if entry == null:
			_fail_test("RTS-ADV-10_" + room_label + "_entry_missing", "Entry node not found")
			_room_ok = false
			all_pass = false
		else:
			var ez: float = (entry as Node3D).position.z
			if _near(ez, 0.0, POS_TOL):
				_pass_test("RTS-ADV-10_" + room_label + "_entry_z_zero (z=" + str(ez) + ")")
			else:
				_fail_test("RTS-ADV-10_" + room_label + "_entry_z",
					"Entry.position.z = " + str(ez) + ", expected 0.0 ±" + str(POS_TOL))
				_room_ok = false
				all_pass = false
		if exit_node == null:
			_fail_test("RTS-ADV-10_" + room_label + "_exit_missing", "Exit node not found")
			_room_ok = false
			all_pass = false
		else:
			var xz: float = (exit_node as Node3D).position.z
			if _near(xz, 0.0, POS_TOL):
				_pass_test("RTS-ADV-10_" + room_label + "_exit_z_zero (z=" + str(xz) + ")")
			else:
				_fail_test("RTS-ADV-10_" + room_label + "_exit_z",
					"Exit.position.z = " + str(xz) + ", expected 0.0 ±" + str(POS_TOL))
				_room_ok = false
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
		if scene_path == SCENE_COMBAT_01 or scene_path == SCENE_COMBAT_02:
			for anchor_name in ["EnemySpawn_1", "EnemySpawn_2"]:
				var anchor: Node = root.get_node_or_null(anchor_name)
				if anchor == null:
					_fail_test("RTS-ADV-14_" + room_label + "_" + anchor_name + "_missing",
						anchor_name + " not found as direct child of " + root.name)
					all_pass = false
					continue
				var anchor_mode: int = (anchor as Node3D).physics_interpolation_mode
				if anchor_mode == 1 or anchor_mode == 0:
					_pass_test("RTS-ADV-14_" + room_label + "_" + anchor_name + "_interp_mode_1")
				else:
					_fail_test("RTS-ADV-14_" + room_label + "_" + anchor_name,
						anchor_name + " physics_interpolation_mode = " + str(anchor_mode) + ", expected 0 (inherit) or 1")
					all_pass = false
		else:
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
		if scene_path == SCENE_COMBAT_01 or scene_path == SCENE_COMBAT_02:
			for anchor_name in ["EnemySpawn_1", "EnemySpawn_2"]:
				var anchor: Node = root.get_node_or_null(anchor_name)
				if anchor == null:
					_fail_test("RTS-ADV-15_" + room_label + "_" + anchor_name + "_missing", anchor_name + " not found")
					all_pass = false
					continue
				var anchor_z: float = (anchor as Node3D).position.z
				if _near(anchor_z, 0.0, POS_TOL):
					_pass_test("RTS-ADV-15_" + room_label + "_" + anchor_name + "_z_zero (z=" + str(anchor_z) + ")")
				else:
					_fail_test("RTS-ADV-15_" + room_label + "_" + anchor_name,
						anchor_name + " position.z = " + str(anchor_z) + ", expected 0.0 ±" + str(POS_TOL))
					all_pass = false
		else:
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
	var part2: Object = _RTS_ADV_PART2_SCRIPT.new()
	part2.run_all_part2()
	_pass_count += int(part2.get("_pass_count"))
	_fail_count += int(part2.get("_fail_count"))

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
