#
# test_light_skill_check.gd
#
# Behavioral tests for the Light Skill Check zone within containment_hall_01.tscn.
# Spec: agent_context/agents/2_spec/light_skill_check_spec.md
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/light_skill_check.md
#
# All tests are headless-safe: no physics tick, no await, no input simulation, no signals.
# Red phase: any scene node absent or geometry wrong will produce explicit FAIL messages.
# Green phase: all assertions pass after scene is authored to spec.
#
# Spec requirement traceability:
#   T-43  → SKC-GEO-1 (AC-SKC-GEO-1.1, 1.2, 1.3, 1.4)    — SkillCheckFloorBase pit floor geometry
#   T-44  → SKC-GEO-2 (AC-SKC-GEO-2.1, 2.2, 2.3, 2.4)    — SkillCheckPlatform1 geometry + top surface Y
#   T-45  → SKC-GEO-3 (AC-SKC-GEO-3.1, 3.2, 3.3, 3.4)    — SkillCheckPlatform2 geometry + top surface Y
#   T-46  → SKC-GEO-4 (AC-SKC-GEO-4.1, 4.2, 4.3, 4.4, 4.8) — SkillCheckPlatform3 geometry + wider than P1/P2
#   T-47  → SKC-GEO-3 (AC-SKC-GEO-3.5, 3.6, 3.7)          — P1→P2 gap > 0 and ≤ 1.5 m, approx 1.0 m
#   T-48  → SKC-GEO-4 (AC-SKC-GEO-4.5, 4.6, 4.7)          — P2→P3 gap > 0 and ≤ 1.5 m, approx 1.0 m
#   T-49  → SKC-RETRY-1 (AC-SKC-RETRY-1.1 through 1.7)     — RespawnZone script, NodePath, BoxShape3D coverage
#   T-50  → SKC-RETRY-2 (AC-SKC-RETRY-2.1, 2.2, 2.3, 2.4) — SpawnPosition type, pre-zone X, corridor-level Y
#   T-51  → SKC-PLACE-1 (AC-SKC-PLACE-1.1, 1.2, 1.3, 1.4)  — Platform X ordering, center-to-center spacing ≥ 3 m
#   T-52  → SKC-PLACE-2 (AC-SKC-PLACE-2.1, 2.2, 2.3)       — After fusion, before mini-boss; floor base in [40, 50]
#
# NOTE: collision_mask == 3 for all StaticBody3D nodes is already covered by T-25 in
# test_containment_hall_01.gd. No collision_mask assertion is made in this file.
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - No test name duplicates any T-1 through T-42 assertion name.

extends "res://tests/utils/test_utils.gd"

const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Load the level scene. Returns null and records failure when the file is absent.
func _load_level_scene() -> Node:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("scene_load_guard", "ResourceLoader.load returned null for " + SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("scene_instantiate_guard", "instantiate() returned null for " + SCENE_PATH)
		return null
	return inst


# Get the first CollisionShape3D child of a node, or null.
func _get_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null


# ---------------------------------------------------------------------------
# T-43: SkillCheckFloorBase — exists as StaticBody3D; position.x ≈ 45 ±1.0;
#        BoxShape3D size (20, 1, 10) exact; top surface Y < -1.0 (pit floor confirmation)
# Spec: SKC-GEO-1 (AC-SKC-GEO-1.1, 1.2, 1.3, 1.4)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t43_skill_check_floor_base_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("SkillCheckFloorBase")
	_assert_true(
		floor_node != null,
		"T-43_skill_check_floor_base_exists",
		"SkillCheckFloorBase node not found in scene — SKC-GEO-1 AC-SKC-GEO-1.1"
	)
	if floor_node == null:
		root.free()
		return

	_assert_true(
		floor_node is StaticBody3D,
		"T-43_skill_check_floor_base_is_static_body3d",
		"SkillCheckFloorBase is " + floor_node.get_class() + ", expected StaticBody3D — SKC-GEO-1 AC-SKC-GEO-1.1"
	)

	var pos: Vector3 = (floor_node as Node3D).position
	_assert_true(
		abs(pos.x - 45.0) <= 1.0,
		"T-43_skill_check_floor_base_position_x",
		"SkillCheckFloorBase.position.x = " + str(pos.x) + ", expected 45.0 ±1.0 — SKC-GEO-1 AC-SKC-GEO-1.2"
	)

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	_assert_true(
		col != null,
		"T-43_skill_check_floor_base_has_collision_shape",
		"SkillCheckFloorBase has no CollisionShape3D child — SKC-GEO-1 AC-SKC-GEO-1.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-43_skill_check_floor_base_collision_shape_is_box",
		"SkillCheckFloorBase CollisionShape3D.shape is not BoxShape3D — SKC-GEO-1 AC-SKC-GEO-1.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(20.0, box.size.x, "T-43_skill_check_floor_base_box_size_x — expected 20.0 — SKC-GEO-1 AC-SKC-GEO-1.3")
	_assert_eq_float(1.0, box.size.y, "T-43_skill_check_floor_base_box_size_y — expected 1.0 — SKC-GEO-1 AC-SKC-GEO-1.3")
	_assert_eq_float(10.0, box.size.z, "T-43_skill_check_floor_base_box_size_z — expected 10.0 — SKC-GEO-1 AC-SKC-GEO-1.3")

	# Top surface world Y = node.position.y + col.position.y + (box.size.y * 0.5)
	# Confirms this is the pit floor, not at corridor level.
	var top_surface_y: float = pos.y + col.position.y + (box.size.y * 0.5)
	_assert_true(
		top_surface_y < -1.0,
		"T-43_skill_check_floor_base_top_surface_y_is_pit_floor",
		"SkillCheckFloorBase top surface Y = " + str(top_surface_y) + ", expected < -1.0 (pit floor) — SKC-GEO-1 AC-SKC-GEO-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-44: SkillCheckPlatform1 — exists as StaticBody3D; position.x ≈ 39 ±0.5;
#        BoxShape3D size (4, 1, 6) exact; top surface Y in [-0.1, 0.1]
# Spec: SKC-GEO-2 (AC-SKC-GEO-2.1, 2.2, 2.3, 2.4)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t44_skill_check_platform1_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat: Node = root.get_node_or_null("SkillCheckPlatform1")
	_assert_true(
		plat != null,
		"T-44_skill_check_platform1_exists",
		"SkillCheckPlatform1 node not found in scene — SKC-GEO-2 AC-SKC-GEO-2.1"
	)
	if plat == null:
		root.free()
		return

	_assert_true(
		plat is StaticBody3D,
		"T-44_skill_check_platform1_is_static_body3d",
		"SkillCheckPlatform1 is " + plat.get_class() + ", expected StaticBody3D — SKC-GEO-2 AC-SKC-GEO-2.1"
	)

	var pos: Vector3 = (plat as Node3D).position
	_assert_true(
		abs(pos.x - 39.0) <= 0.5,
		"T-44_skill_check_platform1_position_x",
		"SkillCheckPlatform1.position.x = " + str(pos.x) + ", expected 39.0 ±0.5 — SKC-GEO-2 AC-SKC-GEO-2.2"
	)

	var col: CollisionShape3D = _get_collision_shape(plat)
	_assert_true(
		col != null,
		"T-44_skill_check_platform1_has_collision_shape",
		"SkillCheckPlatform1 has no CollisionShape3D child — SKC-GEO-2 AC-SKC-GEO-2.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-44_skill_check_platform1_collision_shape_is_box",
		"SkillCheckPlatform1 CollisionShape3D.shape is not BoxShape3D — SKC-GEO-2 AC-SKC-GEO-2.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(4.0, box.size.x, "T-44_skill_check_platform1_box_size_x — expected 4.0 — SKC-GEO-2 AC-SKC-GEO-2.3")
	_assert_eq_float(1.0, box.size.y, "T-44_skill_check_platform1_box_size_y — expected 1.0 — SKC-GEO-2 AC-SKC-GEO-2.3")
	_assert_eq_float(6.0, box.size.z, "T-44_skill_check_platform1_box_size_z — expected 6.0 — SKC-GEO-2 AC-SKC-GEO-2.3")

	# Top surface world Y = node.position.y + col.position.y + (box.size.y * 0.5)
	var top_surface_y: float = pos.y + col.position.y + (box.size.y * 0.5)
	_assert_true(
		top_surface_y >= -0.1 and top_surface_y <= 0.1,
		"T-44_skill_check_platform1_top_surface_y_in_range",
		"SkillCheckPlatform1 top surface Y = " + str(top_surface_y) + ", expected in [-0.1, 0.1] — SKC-GEO-2 AC-SKC-GEO-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-45: SkillCheckPlatform2 — exists as StaticBody3D; position.x ≈ 44 ±0.5;
#        BoxShape3D size (4, 1, 6) exact; top surface Y in [-0.1, 0.1]
# Spec: SKC-GEO-3 (AC-SKC-GEO-3.1, 3.2, 3.3, 3.4)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t45_skill_check_platform2_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat: Node = root.get_node_or_null("SkillCheckPlatform2")
	_assert_true(
		plat != null,
		"T-45_skill_check_platform2_exists",
		"SkillCheckPlatform2 node not found in scene — SKC-GEO-3 AC-SKC-GEO-3.1"
	)
	if plat == null:
		root.free()
		return

	_assert_true(
		plat is StaticBody3D,
		"T-45_skill_check_platform2_is_static_body3d",
		"SkillCheckPlatform2 is " + plat.get_class() + ", expected StaticBody3D — SKC-GEO-3 AC-SKC-GEO-3.1"
	)

	var pos: Vector3 = (plat as Node3D).position
	_assert_true(
		abs(pos.x - 44.0) <= 0.5,
		"T-45_skill_check_platform2_position_x",
		"SkillCheckPlatform2.position.x = " + str(pos.x) + ", expected 44.0 ±0.5 — SKC-GEO-3 AC-SKC-GEO-3.2"
	)

	var col: CollisionShape3D = _get_collision_shape(plat)
	_assert_true(
		col != null,
		"T-45_skill_check_platform2_has_collision_shape",
		"SkillCheckPlatform2 has no CollisionShape3D child — SKC-GEO-3 AC-SKC-GEO-3.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-45_skill_check_platform2_collision_shape_is_box",
		"SkillCheckPlatform2 CollisionShape3D.shape is not BoxShape3D — SKC-GEO-3 AC-SKC-GEO-3.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(4.0, box.size.x, "T-45_skill_check_platform2_box_size_x — expected 4.0 — SKC-GEO-3 AC-SKC-GEO-3.3")
	_assert_eq_float(1.0, box.size.y, "T-45_skill_check_platform2_box_size_y — expected 1.0 — SKC-GEO-3 AC-SKC-GEO-3.3")
	_assert_eq_float(6.0, box.size.z, "T-45_skill_check_platform2_box_size_z — expected 6.0 — SKC-GEO-3 AC-SKC-GEO-3.3")

	# Top surface world Y = node.position.y + col.position.y + (box.size.y * 0.5)
	var top_surface_y: float = pos.y + col.position.y + (box.size.y * 0.5)
	_assert_true(
		top_surface_y >= -0.1 and top_surface_y <= 0.1,
		"T-45_skill_check_platform2_top_surface_y_in_range",
		"SkillCheckPlatform2 top surface Y = " + str(top_surface_y) + ", expected in [-0.1, 0.1] — SKC-GEO-3 AC-SKC-GEO-3.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-46: SkillCheckPlatform3 — exists as StaticBody3D; position.x ≈ 51 ±0.5;
#        BoxShape3D size (8, 1, 6) exact; top surface Y in [-0.1, 0.1];
#        size.x (8) > Platform1 size.x (4) and Platform2 size.x (4) — landing pad wider than approach
# Spec: SKC-GEO-4 (AC-SKC-GEO-4.1, 4.2, 4.3, 4.4, 4.8)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t46_skill_check_platform3_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat3: Node = root.get_node_or_null("SkillCheckPlatform3")
	_assert_true(
		plat3 != null,
		"T-46_skill_check_platform3_exists",
		"SkillCheckPlatform3 node not found in scene — SKC-GEO-4 AC-SKC-GEO-4.1"
	)
	if plat3 == null:
		root.free()
		return

	_assert_true(
		plat3 is StaticBody3D,
		"T-46_skill_check_platform3_is_static_body3d",
		"SkillCheckPlatform3 is " + plat3.get_class() + ", expected StaticBody3D — SKC-GEO-4 AC-SKC-GEO-4.1"
	)

	var pos: Vector3 = (plat3 as Node3D).position
	_assert_true(
		abs(pos.x - 51.0) <= 0.5,
		"T-46_skill_check_platform3_position_x",
		"SkillCheckPlatform3.position.x = " + str(pos.x) + ", expected 51.0 ±0.5 — SKC-GEO-4 AC-SKC-GEO-4.2"
	)

	var col3: CollisionShape3D = _get_collision_shape(plat3)
	_assert_true(
		col3 != null,
		"T-46_skill_check_platform3_has_collision_shape",
		"SkillCheckPlatform3 has no CollisionShape3D child — SKC-GEO-4 AC-SKC-GEO-4.3"
	)
	if col3 == null:
		root.free()
		return

	_assert_true(
		col3.shape != null and col3.shape is BoxShape3D,
		"T-46_skill_check_platform3_collision_shape_is_box",
		"SkillCheckPlatform3 CollisionShape3D.shape is not BoxShape3D — SKC-GEO-4 AC-SKC-GEO-4.3"
	)
	if not (col3.shape is BoxShape3D):
		root.free()
		return

	var box3: BoxShape3D = col3.shape as BoxShape3D
	_assert_eq_float(8.0, box3.size.x, "T-46_skill_check_platform3_box_size_x — expected 8.0 — SKC-GEO-4 AC-SKC-GEO-4.3")
	_assert_eq_float(1.0, box3.size.y, "T-46_skill_check_platform3_box_size_y — expected 1.0 — SKC-GEO-4 AC-SKC-GEO-4.3")
	_assert_eq_float(6.0, box3.size.z, "T-46_skill_check_platform3_box_size_z — expected 6.0 — SKC-GEO-4 AC-SKC-GEO-4.3")

	# Top surface world Y = node.position.y + col.position.y + (box.size.y * 0.5)
	var top_surface_y: float = pos.y + col3.position.y + (box3.size.y * 0.5)
	_assert_true(
		top_surface_y >= -0.1 and top_surface_y <= 0.1,
		"T-46_skill_check_platform3_top_surface_y_in_range",
		"SkillCheckPlatform3 top surface Y = " + str(top_surface_y) + ", expected in [-0.1, 0.1] — SKC-GEO-4 AC-SKC-GEO-4.4"
	)

	# Platform3 must be wider than Platform1 and Platform2 (landing pad design requirement).
	# Fetch P1 and P2 box widths for the comparison.
	var plat1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var plat2: Node = root.get_node_or_null("SkillCheckPlatform2")
	if plat1 != null and plat2 != null:
		var col1: CollisionShape3D = _get_collision_shape(plat1)
		var col2: CollisionShape3D = _get_collision_shape(plat2)
		if col1 != null and col1.shape is BoxShape3D and col2 != null and col2.shape is BoxShape3D:
			var box1: BoxShape3D = col1.shape as BoxShape3D
			var box2: BoxShape3D = col2.shape as BoxShape3D
			_assert_true(
				box3.size.x > box1.size.x,
				"T-46_skill_check_platform3_wider_than_platform1",
				"SkillCheckPlatform3 box.size.x (" + str(box3.size.x) + ") must be > Platform1 box.size.x (" + str(box1.size.x) + ") — SKC-GEO-4 AC-SKC-GEO-4.8"
			)
			_assert_true(
				box3.size.x > box2.size.x,
				"T-46_skill_check_platform3_wider_than_platform2",
				"SkillCheckPlatform3 box.size.x (" + str(box3.size.x) + ") must be > Platform2 box.size.x (" + str(box2.size.x) + ") — SKC-GEO-4 AC-SKC-GEO-4.8"
			)
		else:
			_fail_test(
				"T-46_platform1_platform2_shapes_available_for_width_compare",
				"SkillCheckPlatform1 or SkillCheckPlatform2 CollisionShape3D/BoxShape3D missing — cannot compare widths — SKC-GEO-4 AC-SKC-GEO-4.8"
			)
	else:
		_fail_test(
			"T-46_platform1_platform2_exist_for_width_compare",
			"SkillCheckPlatform1 or SkillCheckPlatform2 not found — cannot compare widths — SKC-GEO-4 AC-SKC-GEO-4.8"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-47: P1→P2 gap reachability — gap (P2 left edge − P1 right edge) > 0 and ≤ 1.5 m;
#        approx 1.0 m ±0.3 m. Uses CollisionShape3D X offsets and box half-widths.
# Spec: SKC-GEO-3 (AC-SKC-GEO-3.5, 3.6, 3.7)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t47_p1_to_p2_gap_reachability() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var plat2: Node = root.get_node_or_null("SkillCheckPlatform2")

	if plat1 == null or plat2 == null:
		_fail_test(
			"T-47_p1_p2_nodes_exist",
			"SkillCheckPlatform1 or SkillCheckPlatform2 not found — cannot compute P1→P2 gap — SKC-GEO-3"
		)
		root.free()
		return

	var col1: CollisionShape3D = _get_collision_shape(plat1)
	var col2: CollisionShape3D = _get_collision_shape(plat2)

	if col1 == null or col2 == null or not (col1.shape is BoxShape3D) or not (col2.shape is BoxShape3D):
		_fail_test(
			"T-47_p1_p2_shapes_exist",
			"SkillCheckPlatform1 or SkillCheckPlatform2 has missing or non-BoxShape3D CollisionShape3D — SKC-GEO-3"
		)
		root.free()
		return

	var box1: BoxShape3D = col1.shape as BoxShape3D
	var box2: BoxShape3D = col2.shape as BoxShape3D

	var pos1x: float = (plat1 as Node3D).position.x
	var pos2x: float = (plat2 as Node3D).position.x

	# Right edge of P1: node.x + col.x + (box.size.x / 2)
	var right_edge_p1: float = pos1x + col1.position.x + (box1.size.x / 2.0)
	# Left edge of P2: node.x + col.x - (box.size.x / 2)
	var left_edge_p2: float = pos2x + col2.position.x - (box2.size.x / 2.0)
	var gap: float = left_edge_p2 - right_edge_p1

	_assert_true(
		gap > 0.0,
		"T-47_p1_to_p2_gap_is_positive",
		"P1→P2 gap = " + str(gap) + " m, must be > 0 (platforms must not overlap) — SKC-GEO-3 AC-SKC-GEO-3.5"
	)
	_assert_true(
		gap <= 1.5,
		"T-47_p1_to_p2_gap_le_1p5m",
		"P1→P2 gap = " + str(gap) + " m, must be ≤ 1.5 m (within safe jump range) — SKC-GEO-3 AC-SKC-GEO-3.6"
	)
	_assert_true(
		abs(gap - 1.0) <= 0.3,
		"T-47_p1_to_p2_gap_approx_1m",
		"P1→P2 gap = " + str(gap) + " m, expected 1.0 ±0.3 m (right_p1=" + str(right_edge_p1) + " left_p2=" + str(left_edge_p2) + ") — SKC-GEO-3 AC-SKC-GEO-3.7"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-48: P2→P3 gap reachability — gap (P3 left edge − P2 right edge) > 0 and ≤ 1.5 m;
#        approx 1.0 m ±0.3 m. Uses CollisionShape3D X offsets and box half-widths.
# Spec: SKC-GEO-4 (AC-SKC-GEO-4.5, 4.6, 4.7)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t48_p2_to_p3_gap_reachability() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat2: Node = root.get_node_or_null("SkillCheckPlatform2")
	var plat3: Node = root.get_node_or_null("SkillCheckPlatform3")

	if plat2 == null or plat3 == null:
		_fail_test(
			"T-48_p2_p3_nodes_exist",
			"SkillCheckPlatform2 or SkillCheckPlatform3 not found — cannot compute P2→P3 gap — SKC-GEO-4"
		)
		root.free()
		return

	var col2: CollisionShape3D = _get_collision_shape(plat2)
	var col3: CollisionShape3D = _get_collision_shape(plat3)

	if col2 == null or col3 == null or not (col2.shape is BoxShape3D) or not (col3.shape is BoxShape3D):
		_fail_test(
			"T-48_p2_p3_shapes_exist",
			"SkillCheckPlatform2 or SkillCheckPlatform3 has missing or non-BoxShape3D CollisionShape3D — SKC-GEO-4"
		)
		root.free()
		return

	var box2: BoxShape3D = col2.shape as BoxShape3D
	var box3: BoxShape3D = col3.shape as BoxShape3D

	var pos2x: float = (plat2 as Node3D).position.x
	var pos3x: float = (plat3 as Node3D).position.x

	# Right edge of P2: node.x + col.x + (box.size.x / 2)
	var right_edge_p2: float = pos2x + col2.position.x + (box2.size.x / 2.0)
	# Left edge of P3: node.x + col.x - (box.size.x / 2)
	var left_edge_p3: float = pos3x + col3.position.x - (box3.size.x / 2.0)
	var gap: float = left_edge_p3 - right_edge_p2

	_assert_true(
		gap > 0.0,
		"T-48_p2_to_p3_gap_is_positive",
		"P2→P3 gap = " + str(gap) + " m, must be > 0 (platforms must not overlap) — SKC-GEO-4 AC-SKC-GEO-4.5"
	)
	_assert_true(
		gap <= 1.5,
		"T-48_p2_to_p3_gap_le_1p5m",
		"P2→P3 gap = " + str(gap) + " m, must be ≤ 1.5 m (within safe jump range) — SKC-GEO-4 AC-SKC-GEO-4.6"
	)
	_assert_true(
		abs(gap - 1.0) <= 0.3,
		"T-48_p2_to_p3_gap_approx_1m",
		"P2→P3 gap = " + str(gap) + " m, expected 1.0 ±0.3 m (right_p2=" + str(right_edge_p2) + " left_p3=" + str(left_edge_p3) + ") — SKC-GEO-4 AC-SKC-GEO-4.7"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-49: RespawnZone — exists as Area3D; script path contains "respawn_zone.gd";
#        spawn_point property is non-empty NodePath that resolves to a valid node;
#        CollisionShape3D BoxShape3D size.x ≥ 20; size.y ≥ 6; col Y offset < 0
# Spec: SKC-RETRY-1 (AC-SKC-RETRY-1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7)
# ---------------------------------------------------------------------------
func test_t49_respawn_zone() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	_assert_true(
		zone != null,
		"T-49_respawn_zone_exists",
		"RespawnZone node not found in scene — SKC-RETRY-1 AC-SKC-RETRY-1.1"
	)
	if zone == null:
		root.free()
		return

	_assert_true(
		zone is Area3D,
		"T-49_respawn_zone_is_area3d",
		"RespawnZone is " + zone.get_class() + ", expected Area3D — SKC-RETRY-1 AC-SKC-RETRY-1.1"
	)

	# AC-SKC-RETRY-1.2: script path contains "respawn_zone.gd"
	var script_res: Script = zone.get_script() as Script
	_assert_true(
		script_res != null,
		"T-49_respawn_zone_has_script",
		"RespawnZone has no script attached — SKC-RETRY-1 AC-SKC-RETRY-1.2"
	)
	if script_res != null:
		_assert_true(
			script_res.resource_path.contains("respawn_zone.gd"),
			"T-49_respawn_zone_script_path_contains_respawn_zone_gd",
			"RespawnZone script path '" + script_res.resource_path + "' does not contain 'respawn_zone.gd' — SKC-RETRY-1 AC-SKC-RETRY-1.2"
		)

	# AC-SKC-RETRY-1.3: spawn_point NodePath is non-empty
	# Use get() for exported property access — safe even if property name differs.
	var spawn_point_val = zone.get("spawn_point")
	_assert_true(
		spawn_point_val != null and String(spawn_point_val) != "",
		"T-49_respawn_zone_spawn_point_non_empty",
		"RespawnZone.spawn_point is null or empty NodePath — SKC-RETRY-1 AC-SKC-RETRY-1.3"
	)

	# AC-SKC-RETRY-1.4: NodePath resolves to a valid node (relative to RespawnZone itself,
	# because spawn_point is "../SpawnPosition" — going up to scene root then finding SpawnPosition).
	if spawn_point_val != null and String(spawn_point_val) != "":
		var resolved: Node = zone.get_node_or_null(spawn_point_val as NodePath)
		_assert_true(
			resolved != null,
			"T-49_respawn_zone_spawn_point_resolves",
			"RespawnZone.spawn_point NodePath '" + str(spawn_point_val) + "' does not resolve to a valid node — SKC-RETRY-1 AC-SKC-RETRY-1.4"
		)

	# AC-SKC-RETRY-1.5, 1.6, 1.7: CollisionShape3D BoxShape3D covers the zone adequately
	var col: CollisionShape3D = _get_collision_shape(zone)
	_assert_true(
		col != null,
		"T-49_respawn_zone_has_collision_shape",
		"RespawnZone has no CollisionShape3D child — SKC-RETRY-1 AC-SKC-RETRY-1.5"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-49_respawn_zone_collision_shape_is_box",
		"RespawnZone CollisionShape3D.shape is not BoxShape3D — SKC-RETRY-1 AC-SKC-RETRY-1.5"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(
		box.size.x >= 20.0,
		"T-49_respawn_zone_box_size_x_ge_20",
		"RespawnZone BoxShape3D size.x = " + str(box.size.x) + ", must be ≥ 20.0 (wide enough to catch falls in zone) — SKC-RETRY-1 AC-SKC-RETRY-1.5"
	)
	_assert_true(
		box.size.y >= 6.0,
		"T-49_respawn_zone_box_size_y_ge_6",
		"RespawnZone BoxShape3D size.y = " + str(box.size.y) + ", must be ≥ 6.0 (deep enough: corridor Y=0 to pit Y=-4) — SKC-RETRY-1 AC-SKC-RETRY-1.6"
	)
	_assert_true(
		col.position.y < 0.0,
		"T-49_respawn_zone_col_y_offset_negative",
		"RespawnZone CollisionShape3D local Y offset = " + str(col.position.y) + ", must be < 0.0 (zone center below corridor level) — SKC-RETRY-1 AC-SKC-RETRY-1.7"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-50: SpawnPosition — exists as Marker3D; position.x < 35 (before skill check zone);
#        position.y >= 0 (not in pit); position.y <= 3 (not floating)
# Spec: SKC-RETRY-2 (AC-SKC-RETRY-2.1, 2.2, 2.3, 2.4)
# ---------------------------------------------------------------------------
func test_t50_spawn_position() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var spawn: Node = root.get_node_or_null("SpawnPosition")
	_assert_true(
		spawn != null,
		"T-50_spawn_position_exists",
		"SpawnPosition node not found in scene — SKC-RETRY-2 AC-SKC-RETRY-2.1"
	)
	if spawn == null:
		root.free()
		return

	_assert_true(
		spawn is Marker3D,
		"T-50_spawn_position_is_marker3d",
		"SpawnPosition is " + spawn.get_class() + ", expected Marker3D — SKC-RETRY-2 AC-SKC-RETRY-2.1"
	)

	var pos: Vector3 = (spawn as Node3D).position
	_assert_true(
		pos.x < 35.0,
		"T-50_spawn_position_x_before_skill_check_zone",
		"SpawnPosition.position.x = " + str(pos.x) + ", must be < 35.0 (before skill check zone entrance) — SKC-RETRY-2 AC-SKC-RETRY-2.2"
	)
	_assert_true(
		pos.y >= 0.0,
		"T-50_spawn_position_y_not_in_pit",
		"SpawnPosition.position.y = " + str(pos.y) + ", must be >= 0.0 (player must not spawn in pit) — SKC-RETRY-2 AC-SKC-RETRY-2.3"
	)
	_assert_true(
		pos.y <= 3.0,
		"T-50_spawn_position_y_not_floating",
		"SpawnPosition.position.y = " + str(pos.y) + ", must be <= 3.0 (player must respawn at corridor height, not floating) — SKC-RETRY-2 AC-SKC-RETRY-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-51: Platform X ordering — P1.x < P2.x < P3.x; center-to-center spacing ≥ 3 m
# Spec: SKC-PLACE-1 (AC-SKC-PLACE-1.1, 1.2, 1.3, 1.4)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t51_platform_x_ordering() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var plat2: Node = root.get_node_or_null("SkillCheckPlatform2")
	var plat3: Node = root.get_node_or_null("SkillCheckPlatform3")

	if plat1 == null or plat2 == null or plat3 == null:
		_fail_test(
			"T-51_all_platforms_exist",
			"One or more of SkillCheckPlatform1/2/3 not found — cannot verify X ordering — SKC-PLACE-1"
		)
		root.free()
		return

	var p1x: float = (plat1 as Node3D).position.x
	var p2x: float = (plat2 as Node3D).position.x
	var p3x: float = (plat3 as Node3D).position.x

	_assert_true(
		p1x < p2x,
		"T-51_platform1_x_less_than_platform2_x",
		"SkillCheckPlatform1.x (" + str(p1x) + ") must be < SkillCheckPlatform2.x (" + str(p2x) + ") — SKC-PLACE-1 AC-SKC-PLACE-1.1"
	)
	_assert_true(
		p2x < p3x,
		"T-51_platform2_x_less_than_platform3_x",
		"SkillCheckPlatform2.x (" + str(p2x) + ") must be < SkillCheckPlatform3.x (" + str(p3x) + ") — SKC-PLACE-1 AC-SKC-PLACE-1.2"
	)
	_assert_true(
		p2x - p1x >= 3.0,
		"T-51_p2_minus_p1_spacing_ge_3m",
		"SkillCheckPlatform2.x - Platform1.x = " + str(p2x - p1x) + " m, must be ≥ 3.0 m — SKC-PLACE-1 AC-SKC-PLACE-1.3"
	)
	_assert_true(
		p3x - p2x >= 3.0,
		"T-51_p3_minus_p2_spacing_ge_3m",
		"SkillCheckPlatform3.x - Platform2.x = " + str(p3x - p2x) + " m, must be ≥ 3.0 m — SKC-PLACE-1 AC-SKC-PLACE-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-52: Level flow placement — P1.x > FusionPlatformB.x; P3.x < MiniBossFloor.x;
#        SkillCheckFloorBase.x in [40, 50]
# Spec: SKC-PLACE-2 (AC-SKC-PLACE-2.1, 2.2, 2.3)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t52_level_flow_placement() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var plat3: Node = root.get_node_or_null("SkillCheckPlatform3")
	var fusion_b: Node = root.get_node_or_null("FusionPlatformB")
	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	var floor_base: Node = root.get_node_or_null("SkillCheckFloorBase")

	# AC-SKC-PLACE-2.1: SkillCheckPlatform1.x > FusionPlatformB.x
	if plat1 == null:
		_fail_test(
			"T-52_skill_check_platform1_exists_for_flow",
			"SkillCheckPlatform1 not found — cannot verify level flow placement — SKC-PLACE-2 AC-SKC-PLACE-2.1"
		)
	elif fusion_b == null:
		_fail_test(
			"T-52_fusion_platform_b_exists_for_flow",
			"FusionPlatformB not found — cannot verify skill check comes after fusion — SKC-PLACE-2 AC-SKC-PLACE-2.1"
		)
	else:
		var p1x: float = (plat1 as Node3D).position.x
		var fbx: float = (fusion_b as Node3D).position.x
		_assert_true(
			p1x > fbx,
			"T-52_skill_check_platform1_after_fusion_platform_b",
			"SkillCheckPlatform1.x (" + str(p1x) + ") must be > FusionPlatformB.x (" + str(fbx) + ") — skill check comes after fusion — SKC-PLACE-2 AC-SKC-PLACE-2.1"
		)

	# AC-SKC-PLACE-2.2: SkillCheckPlatform3.x < MiniBossFloor.x
	if plat3 == null:
		_fail_test(
			"T-52_skill_check_platform3_exists_for_flow",
			"SkillCheckPlatform3 not found — cannot verify level flow placement — SKC-PLACE-2 AC-SKC-PLACE-2.2"
		)
	elif mini_boss_floor == null:
		_fail_test(
			"T-52_mini_boss_floor_exists_for_flow",
			"MiniBossFloor not found — cannot verify skill check comes before mini-boss — SKC-PLACE-2 AC-SKC-PLACE-2.2"
		)
	else:
		var p3x: float = (plat3 as Node3D).position.x
		var mbx: float = (mini_boss_floor as Node3D).position.x
		_assert_true(
			p3x < mbx,
			"T-52_skill_check_platform3_before_mini_boss_floor",
			"SkillCheckPlatform3.x (" + str(p3x) + ") must be < MiniBossFloor.x (" + str(mbx) + ") — skill check comes before mini-boss — SKC-PLACE-2 AC-SKC-PLACE-2.2"
		)

	# AC-SKC-PLACE-2.3: SkillCheckFloorBase.x in [40, 50]
	if floor_base == null:
		_fail_test(
			"T-52_skill_check_floor_base_exists_for_flow",
			"SkillCheckFloorBase not found — cannot verify floor base is centered under skill check zone — SKC-PLACE-2 AC-SKC-PLACE-2.3"
		)
	else:
		var fbx2: float = (floor_base as Node3D).position.x
		_assert_true(
			fbx2 >= 40.0 and fbx2 <= 50.0,
			"T-52_skill_check_floor_base_x_in_zone_range",
			"SkillCheckFloorBase.position.x = " + str(fbx2) + ", expected in [40.0, 50.0] — centered under skill check zone — SKC-PLACE-2 AC-SKC-PLACE-2.3"
		)

	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_light_skill_check.gd ---")
	_pass_count = 0
	_fail_count = 0

	# T-43: SkillCheckFloorBase pit floor geometry (SKC-GEO-1)
	test_t43_skill_check_floor_base_geometry()

	# T-44: SkillCheckPlatform1 geometry + top surface Y (SKC-GEO-2)
	test_t44_skill_check_platform1_geometry()

	# T-45: SkillCheckPlatform2 geometry + top surface Y (SKC-GEO-3)
	test_t45_skill_check_platform2_geometry()

	# T-46: SkillCheckPlatform3 geometry + top surface Y + wider than P1/P2 (SKC-GEO-4)
	test_t46_skill_check_platform3_geometry()

	# T-47: P1→P2 gap reachability (SKC-GEO-3)
	test_t47_p1_to_p2_gap_reachability()

	# T-48: P2→P3 gap reachability (SKC-GEO-4)
	test_t48_p2_to_p3_gap_reachability()

	# T-49: RespawnZone script, NodePath, BoxShape3D coverage (SKC-RETRY-1)
	test_t49_respawn_zone()

	# T-50: SpawnPosition type, pre-zone X, corridor-level Y (SKC-RETRY-2)
	test_t50_spawn_position()

	# T-51: Platform X ordering, center-to-center spacing ≥ 3 m (SKC-PLACE-1)
	test_t51_platform_x_ordering()

	# T-52: After fusion, before mini-boss; floor base in [40, 50] (SKC-PLACE-2)
	test_t52_level_flow_placement()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
