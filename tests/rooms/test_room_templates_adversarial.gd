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
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - No test ID duplicates RTS-LOAD-*, RTS-STRUCT-*, RTS-ENTRY-*, RTS-EXIT-*, RTS-GEO-*,
#     RTS-ENC-*, RTS-NO-PLAYER-* from primary suite; adversarial prefix RTS-ADV-* is unique.

extends Object

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

# Tolerance for position checks — spec ±0.01 for markers.
const POS_TOL: float = 0.01

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Assertion helpers
# ---------------------------------------------------------------------------

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


func _near(a: float, b: float, tol: float) -> bool:
	return absf(a - b) <= tol


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


# ---------------------------------------------------------------------------
# RTS-ADV-1: Entry node name is exactly "Entry" (not "EntryMarker", "entry", etc.)
#             AND node type is Marker3D — all 5 rooms
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

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
