#
# test_mutation_tease_room.gd
#
# Behavioral tests for the Mutation Tease Room zone within containment_hall_01.tscn.
# Spec: agent_context/agents/2_spec/mutation_tease_room_spec.md
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/mutation_tease_room.md
#
# All tests are headless-safe: no physics tick, no await, no input simulation, no signals.
# Scene root is NOT added to the SceneTree. root.free() is called before each method returns.
# Red phase: any scene node absent or geometry wrong will produce explicit FAIL messages.
# Green phase: all assertions pass after scene is confirmed to match spec geometry.
#
# Spec requirement traceability:
#   T-63  → MTR-GEO-1 (AC-MTR-GEO-1.1, 1.2, 1.3)
#             MutationTeaseFloor type, position.x ≈ 0 ±1.0, BoxShape3D size (20,1,10) exact
#   T-64  → MTR-GEO-1 (AC-MTR-GEO-1.4)
#             MutationTeaseFloor top surface world Y in [-0.1, 0.1] (floor at corridor level)
#   T-65  → MTR-GEO-2 (AC-MTR-GEO-2.1, 2.2, 2.3)
#             MutationTeasePlatform type, position.x ≈ 0 ±2.0, BoxShape3D size (4,1,6) exact
#   T-66  → MTR-GEO-2 (AC-MTR-GEO-2.4)
#             MutationTeasePlatform top surface world Y in [0.5, 1.5] (elevated above corridor)
#   T-67  → MTR-ENC-1 (AC-MTR-ENC-1.1, 1.2)
#             EnemyMutationTease node exists; get_scene_file_path() contains "enemy_infection_3d.tscn"
#   T-68  → MTR-ENC-1 (AC-MTR-ENC-1.3)
#             EnemyMutationTease.position.y > MutationTeasePlatform.position.y
#   T-69  → MTR-FLOW-1 (AC-MTR-FLOW-1.1)
#             MutationTeaseFloor right edge <= FusionFloor left edge (zones adjacent at X=10.0)
#   T-70  → MTR-FLOW-2 (AC-MTR-FLOW-2.1, 2.2, 2.3, 2.4)
#             EnemyMutationTease name distinct from EnemyFusionA, EnemyFusionB, EnemyMiniBoss
#   T-71  → MTR-GEO-2 (AC-MTR-GEO-2.5)
#             MutationTeasePlatform.position.y >= MutationTeaseFloor.position.y
#   T-72  → MTR-GEO-1 (AC-MTR-GEO-1.5) — TRACEABILITY STUB ONLY
#             collision_mask covered by T-25 in test_containment_hall_01.gd; no new assertion
#
# Adversarial tests (ADV-MTR-01 through ADV-MTR-06):
#   ADV-MTR-01: MutationTeaseFloor BoxShape3D non-zero extents (size.x, .y, .z all > 0)
#   ADV-MTR-02: MutationTeasePlatform BoxShape3D non-zero extents
#   ADV-MTR-03: EnemyMutationTease.position.y > 0 (enemy not embedded in floor at Y=0 or below)
#   ADV-MTR-04: All four enemy node names pairwise distinct + exact expected name strings
#   ADV-MTR-05: MutationTeaseFloor.position.x within [-12, 12] (gross zone bounds check)
#   ADV-MTR-06: MutationTeasePlatform top surface Y > MutationTeaseFloor top surface Y
#
# NOTE: collision_mask == 3 for all StaticBody3D nodes is already covered by T-25 in
# test_containment_hall_01.gd. No collision_mask assertion is made in this file.
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - No test name duplicates any T-1 through T-62 assertion name.
#   - node.name used for enemy distinctness checks (not get_path() — NFR-6, see CHECKPOINTS.md).

extends Object

const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
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


func _assert_eq_float(expected: float, actual: float, test_name: String) -> void:
	if absf(actual - expected) < 0.0001:
		_pass_test(test_name)
	else:
		_fail_test(test_name, "expected " + str(expected) + ", got " + str(actual))


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
# T-63: MutationTeaseFloor — exists as StaticBody3D; position.x ≈ 0 ±1.0;
#        BoxShape3D size (20, 1, 10) exact
# Spec: MTR-GEO-1 (AC-MTR-GEO-1.1, 1.2, 1.3)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t63_mutation_tease_floor_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")
	_assert_true(
		floor_node != null,
		"T-63_mutation_tease_floor_exists",
		"MutationTeaseFloor node not found in scene — MTR-GEO-1 AC-MTR-GEO-1.1"
	)
	if floor_node == null:
		root.free()
		return

	_assert_true(
		floor_node is StaticBody3D,
		"T-63_mutation_tease_floor_is_static_body3d",
		"MutationTeaseFloor is " + floor_node.get_class() + ", expected StaticBody3D — MTR-GEO-1 AC-MTR-GEO-1.1"
	)

	var pos: Vector3 = (floor_node as Node3D).position
	_assert_true(
		abs(pos.x) <= 1.0,
		"T-63_mutation_tease_floor_position_x",
		"MutationTeaseFloor.position.x = " + str(pos.x) + ", expected 0 ±1.0 — MTR-GEO-1 AC-MTR-GEO-1.2"
	)

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	_assert_true(
		col != null,
		"T-63_mutation_tease_floor_has_collision_shape",
		"MutationTeaseFloor has no CollisionShape3D child — MTR-GEO-1 AC-MTR-GEO-1.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-63_mutation_tease_floor_collision_shape_is_box",
		"MutationTeaseFloor CollisionShape3D.shape is not BoxShape3D — MTR-GEO-1 AC-MTR-GEO-1.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(20.0, box.size.x, "T-63_mutation_tease_floor_box_size_x — expected 20.0 — MTR-GEO-1 AC-MTR-GEO-1.3")
	_assert_eq_float(1.0, box.size.y, "T-63_mutation_tease_floor_box_size_y — expected 1.0 — MTR-GEO-1 AC-MTR-GEO-1.3")
	_assert_eq_float(10.0, box.size.z, "T-63_mutation_tease_floor_box_size_z — expected 10.0 — MTR-GEO-1 AC-MTR-GEO-1.3")

	root.free()


# ---------------------------------------------------------------------------
# T-64: MutationTeaseFloor top surface world Y in [-0.1, 0.1] (floor at corridor level)
#        Formula: node.position.y + col.position.y + (box.size.y * 0.5)
#        Confirmed: 0 + (-0.5) + 0.5 = 0.0 — at corridor level.
# Spec: MTR-GEO-1 (AC-MTR-GEO-1.4)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t64_mutation_tease_floor_top_surface_y() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")
	if floor_node == null:
		_fail_test(
			"T-64_mutation_tease_floor_exists_for_top_surface",
			"MutationTeaseFloor not found — cannot compute top surface Y — MTR-GEO-1 AC-MTR-GEO-1.4"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"T-64_mutation_tease_floor_box_shape_available",
			"MutationTeaseFloor CollisionShape3D or BoxShape3D not found — cannot compute top surface Y — MTR-GEO-1 AC-MTR-GEO-1.4"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	var pos_y: float = (floor_node as Node3D).position.y
	# Formula: node.position.y + col.position.y + (box.size.y * 0.5)
	# Confirmed: 0 + (-0.5) + 0.5 = 0.0 — at corridor level.
	var top_surface_y: float = pos_y + col.position.y + (box.size.y * 0.5)

	_assert_true(
		top_surface_y >= -0.1 and top_surface_y <= 0.1,
		"T-64_mutation_tease_floor_top_surface_y_in_range",
		"MutationTeaseFloor top surface world Y = " + str(top_surface_y) + " (node.y=" + str(pos_y) + " col.y=" + str(col.position.y) + " half_y=" + str(box.size.y * 0.5) + "), expected in [-0.1, 0.1] — MTR-GEO-1 AC-MTR-GEO-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-65: MutationTeasePlatform — exists as StaticBody3D; position.x ≈ 0 ±2.0;
#        BoxShape3D size (4, 1, 6) exact
# Spec: MTR-GEO-2 (AC-MTR-GEO-2.1, 2.2, 2.3)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t65_mutation_tease_platform_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var platform: Node = root.get_node_or_null("MutationTeasePlatform")
	_assert_true(
		platform != null,
		"T-65_mutation_tease_platform_exists",
		"MutationTeasePlatform node not found in scene — MTR-GEO-2 AC-MTR-GEO-2.1"
	)
	if platform == null:
		root.free()
		return

	_assert_true(
		platform is StaticBody3D,
		"T-65_mutation_tease_platform_is_static_body3d",
		"MutationTeasePlatform is " + platform.get_class() + ", expected StaticBody3D — MTR-GEO-2 AC-MTR-GEO-2.1"
	)

	var pos: Vector3 = (platform as Node3D).position
	_assert_true(
		abs(pos.x) <= 2.0,
		"T-65_mutation_tease_platform_position_x",
		"MutationTeasePlatform.position.x = " + str(pos.x) + ", expected 0 ±2.0 — MTR-GEO-2 AC-MTR-GEO-2.2"
	)

	var col: CollisionShape3D = _get_collision_shape(platform)
	_assert_true(
		col != null,
		"T-65_mutation_tease_platform_has_collision_shape",
		"MutationTeasePlatform has no CollisionShape3D child — MTR-GEO-2 AC-MTR-GEO-2.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-65_mutation_tease_platform_collision_shape_is_box",
		"MutationTeasePlatform CollisionShape3D.shape is not BoxShape3D — MTR-GEO-2 AC-MTR-GEO-2.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(4.0, box.size.x, "T-65_mutation_tease_platform_box_size_x — expected 4.0 — MTR-GEO-2 AC-MTR-GEO-2.3")
	_assert_eq_float(1.0, box.size.y, "T-65_mutation_tease_platform_box_size_y — expected 1.0 — MTR-GEO-2 AC-MTR-GEO-2.3")
	_assert_eq_float(6.0, box.size.z, "T-65_mutation_tease_platform_box_size_z — expected 6.0 — MTR-GEO-2 AC-MTR-GEO-2.3")

	root.free()


# ---------------------------------------------------------------------------
# T-66: MutationTeasePlatform top surface world Y in [0.5, 1.5] (elevated above corridor)
#        Formula: node.position.y + col.position.y + (box.size.y * 0.5)
#        Confirmed: 0 + 0.3 + 0.5 = 0.8 — elevated above corridor level.
# Spec: MTR-GEO-2 (AC-MTR-GEO-2.4)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t66_mutation_tease_platform_top_surface_y() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var platform: Node = root.get_node_or_null("MutationTeasePlatform")
	if platform == null:
		_fail_test(
			"T-66_mutation_tease_platform_exists_for_top_surface",
			"MutationTeasePlatform not found — cannot compute top surface Y — MTR-GEO-2 AC-MTR-GEO-2.4"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(platform)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"T-66_mutation_tease_platform_box_shape_available",
			"MutationTeasePlatform CollisionShape3D or BoxShape3D not found — cannot compute top surface Y — MTR-GEO-2 AC-MTR-GEO-2.4"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	var pos_y: float = (platform as Node3D).position.y
	# Formula: node.position.y + col.position.y + (box.size.y * 0.5)
	# Confirmed: 0 + 0.3 + 0.5 = 0.8 — elevated above corridor level.
	var top_surface_y: float = pos_y + col.position.y + (box.size.y * 0.5)

	_assert_true(
		top_surface_y >= 0.5 and top_surface_y <= 1.5,
		"T-66_mutation_tease_platform_top_surface_y_in_range",
		"MutationTeasePlatform top surface world Y = " + str(top_surface_y) + " (node.y=" + str(pos_y) + " col.y=" + str(col.position.y) + " half_y=" + str(box.size.y * 0.5) + "), expected in [0.5, 1.5] — MTR-GEO-2 AC-MTR-GEO-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-67: EnemyMutationTease — node exists; get_scene_file_path() contains "enemy_infection_3d.tscn"
# Spec: MTR-ENC-1 (AC-MTR-ENC-1.1, 1.2)
# ---------------------------------------------------------------------------
func test_t67_enemy_mutation_tease_exists_and_scene_path() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy: Node = root.get_node_or_null("EnemyMutationTease")
	_assert_true(
		enemy != null,
		"T-67_enemy_mutation_tease_exists",
		"EnemyMutationTease node not found in scene — MTR-ENC-1 AC-MTR-ENC-1.1"
	)
	if enemy == null:
		root.free()
		return

	# AC-MTR-ENC-1.2: scene file path must contain "enemy_infection_3d.tscn"
	# get_scene_file_path() returns empty string for non-instanced nodes; treat that as failure.
	var scene_path: String = enemy.get_scene_file_path()
	_assert_true(
		scene_path != "" and scene_path.contains("enemy_infection_3d.tscn"),
		"T-67_enemy_mutation_tease_scene_path",
		"EnemyMutationTease.get_scene_file_path() = '" + scene_path + "', must contain 'enemy_infection_3d.tscn' — MTR-ENC-1 AC-MTR-ENC-1.2"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-68: EnemyMutationTease.position.y > MutationTeasePlatform.position.y
#        (enemy above platform node origin — mirrors T-35/T-36 pattern)
#        Confirmed: 1.3 > 0.0 — enemy is above platform origin.
# Spec: MTR-ENC-1 (AC-MTR-ENC-1.3)
# ---------------------------------------------------------------------------
func test_t68_enemy_mutation_tease_above_platform_origin() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy: Node = root.get_node_or_null("EnemyMutationTease")
	var platform: Node = root.get_node_or_null("MutationTeasePlatform")

	if enemy == null:
		_fail_test(
			"T-68_enemy_mutation_tease_exists_for_y_check",
			"EnemyMutationTease not found — cannot verify Y above platform — MTR-ENC-1 AC-MTR-ENC-1.3"
		)
		root.free()
		return

	if platform == null:
		_fail_test(
			"T-68_mutation_tease_platform_exists_for_y_check",
			"MutationTeasePlatform not found — cannot verify enemy Y above platform origin — MTR-ENC-1 AC-MTR-ENC-1.3"
		)
		root.free()
		return

	var enemy_y: float = (enemy as Node3D).position.y
	var platform_y: float = (platform as Node3D).position.y

	_assert_true(
		enemy_y > platform_y,
		"T-68_enemy_mutation_tease_y_gt_platform_origin_y",
		"EnemyMutationTease.position.y (" + str(enemy_y) + ") must be > MutationTeasePlatform.position.y (" + str(platform_y) + ") — enemy must be above platform node origin — MTR-ENC-1 AC-MTR-ENC-1.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-69: MutationTeaseFloor right edge <= FusionFloor left edge
#        Right edge = node.position.x + col.position.x + (box.size.x / 2.0)
#        Left edge  = node.position.x + col.position.x - (box.size.x / 2.0)
#        Confirmed: 0+0+10 = 10.0 <= 22.5+0-12.5 = 10.0 — zones exactly adjacent.
#        Uses <= (not <) because zones share a boundary at exactly X=10.0.
# Spec: MTR-FLOW-1 (AC-MTR-FLOW-1.1)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t69_mutation_tease_floor_right_edge_le_fusion_floor_left_edge() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var tease_floor: Node = root.get_node_or_null("MutationTeaseFloor")
	var fusion_floor: Node = root.get_node_or_null("FusionFloor")

	if tease_floor == null:
		_fail_test(
			"T-69_mutation_tease_floor_exists_for_flow",
			"MutationTeaseFloor not found — cannot compute right edge — MTR-FLOW-1 AC-MTR-FLOW-1.1"
		)
		root.free()
		return

	if fusion_floor == null:
		_fail_test(
			"T-69_fusion_floor_exists_for_flow",
			"FusionFloor not found — cannot compute left edge — MTR-FLOW-1 AC-MTR-FLOW-1.1"
		)
		root.free()
		return

	var tease_col: CollisionShape3D = _get_collision_shape(tease_floor)
	if tease_col == null or not (tease_col.shape is BoxShape3D):
		_fail_test(
			"T-69_mutation_tease_floor_box_shape_for_right_edge",
			"MutationTeaseFloor has no BoxShape3D — cannot compute right edge — MTR-FLOW-1 AC-MTR-FLOW-1.1"
		)
		root.free()
		return

	var fusion_col: CollisionShape3D = _get_collision_shape(fusion_floor)
	if fusion_col == null or not (fusion_col.shape is BoxShape3D):
		_fail_test(
			"T-69_fusion_floor_box_shape_for_left_edge",
			"FusionFloor has no BoxShape3D — cannot compute left edge — MTR-FLOW-1 AC-MTR-FLOW-1.1"
		)
		root.free()
		return

	var tease_box: BoxShape3D = tease_col.shape as BoxShape3D
	var fusion_box: BoxShape3D = fusion_col.shape as BoxShape3D

	var tease_x: float = (tease_floor as Node3D).position.x
	var fusion_x: float = (fusion_floor as Node3D).position.x

	# col X offsets read dynamically to survive future scene edits
	var tease_right_edge: float = tease_x + tease_col.position.x + (tease_box.size.x / 2.0)
	var fusion_left_edge: float = fusion_x + fusion_col.position.x - (fusion_box.size.x / 2.0)

	# Zones are exactly adjacent at X=10.0; use <= not < (see spec zone adjacency note)
	_assert_true(
		tease_right_edge <= fusion_left_edge,
		"T-69_mutation_tease_floor_right_edge_le_fusion_floor_left_edge",
		"MutationTeaseFloor right edge (" + str(tease_right_edge) + " = " + str(tease_x) + " + col.x(" + str(tease_col.position.x) + ") + half_x(" + str(tease_box.size.x / 2.0) + ")) must be <= FusionFloor left edge (" + str(fusion_left_edge) + " = " + str(fusion_x) + " + col.x(" + str(fusion_col.position.x) + ") - half_x(" + str(fusion_box.size.x / 2.0) + ")) — tease zone must precede fusion zone — MTR-FLOW-1 AC-MTR-FLOW-1.1"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-70: EnemyMutationTease name is distinct from EnemyFusionA, EnemyFusionB, EnemyMiniBoss
#        Uses node.name (not get_path()) — get_path() returns empty NodePath for nodes not
#        added to a SceneTree in headless mode. See CHECKPOINTS.md [mini_boss_encounter]
#        Implementation and NFR-6.
# Spec: MTR-FLOW-2 (AC-MTR-FLOW-2.1, 2.2, 2.3, 2.4)
# ---------------------------------------------------------------------------
func test_t70_enemy_mutation_tease_name_distinct_from_other_enemies() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_tease: Node = root.get_node_or_null("EnemyMutationTease")
	var enemy_fusion_a: Node = root.get_node_or_null("EnemyFusionA")
	var enemy_fusion_b: Node = root.get_node_or_null("EnemyFusionB")
	var enemy_boss: Node = root.get_node_or_null("EnemyMiniBoss")

	# AC-MTR-FLOW-2.1: all four nodes must be present
	_assert_true(
		enemy_tease != null,
		"T-70_enemy_mutation_tease_exists_for_distinctness",
		"EnemyMutationTease not found — cannot verify name distinctness — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)
	_assert_true(
		enemy_fusion_a != null,
		"T-70_enemy_fusion_a_exists_for_distinctness",
		"EnemyFusionA not found — cannot verify name distinctness — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)
	_assert_true(
		enemy_fusion_b != null,
		"T-70_enemy_fusion_b_exists_for_distinctness",
		"EnemyFusionB not found — cannot verify name distinctness — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)
	_assert_true(
		enemy_boss != null,
		"T-70_enemy_mini_boss_exists_for_distinctness",
		"EnemyMiniBoss not found — cannot verify name distinctness — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)

	if enemy_tease == null or enemy_fusion_a == null or enemy_fusion_b == null or enemy_boss == null:
		root.free()
		return

	# Use node.name — headless-safe; get_path() returns empty for non-tree nodes (NFR-6)
	var tease_name: String = enemy_tease.name
	var fusion_a_name: String = enemy_fusion_a.name
	var fusion_b_name: String = enemy_fusion_b.name
	var boss_name: String = enemy_boss.name

	# AC-MTR-FLOW-2.2: EnemyMutationTease.name != EnemyFusionA.name
	_assert_true(
		tease_name != fusion_a_name,
		"T-70_enemy_mutation_tease_name_ne_fusion_a_name",
		"EnemyMutationTease.name ('" + tease_name + "') must not equal EnemyFusionA.name ('" + fusion_a_name + "') — MTR-FLOW-2 AC-MTR-FLOW-2.2"
	)

	# AC-MTR-FLOW-2.3: EnemyMutationTease.name != EnemyFusionB.name
	_assert_true(
		tease_name != fusion_b_name,
		"T-70_enemy_mutation_tease_name_ne_fusion_b_name",
		"EnemyMutationTease.name ('" + tease_name + "') must not equal EnemyFusionB.name ('" + fusion_b_name + "') — MTR-FLOW-2 AC-MTR-FLOW-2.3"
	)

	# AC-MTR-FLOW-2.4: EnemyMutationTease.name != EnemyMiniBoss.name
	_assert_true(
		tease_name != boss_name,
		"T-70_enemy_mutation_tease_name_ne_mini_boss_name",
		"EnemyMutationTease.name ('" + tease_name + "') must not equal EnemyMiniBoss.name ('" + boss_name + "') — MTR-FLOW-2 AC-MTR-FLOW-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-71: MutationTeasePlatform.position.y >= MutationTeaseFloor.position.y
#        (platform node origin is not below floor node origin)
#        Confirmed: 0.0 >= 0.0 — both at world Y=0.
# Spec: MTR-GEO-2 (AC-MTR-GEO-2.5)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t71_mutation_tease_platform_y_ge_floor_y() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var platform: Node = root.get_node_or_null("MutationTeasePlatform")
	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")

	if platform == null:
		_fail_test(
			"T-71_mutation_tease_platform_exists_for_y_comparison",
			"MutationTeasePlatform not found — cannot verify platform.y >= floor.y — MTR-GEO-2 AC-MTR-GEO-2.5"
		)
		root.free()
		return

	if floor_node == null:
		_fail_test(
			"T-71_mutation_tease_floor_exists_for_y_comparison",
			"MutationTeaseFloor not found — cannot verify platform.y >= floor.y — MTR-GEO-2 AC-MTR-GEO-2.5"
		)
		root.free()
		return

	var platform_y: float = (platform as Node3D).position.y
	var floor_y: float = (floor_node as Node3D).position.y

	_assert_true(
		platform_y >= floor_y,
		"T-71_mutation_tease_platform_y_ge_mutation_tease_floor_y",
		"MutationTeasePlatform.position.y (" + str(platform_y) + ") must be >= MutationTeaseFloor.position.y (" + str(floor_y) + ") — platform must not be embedded below floor node origin — MTR-GEO-2 AC-MTR-GEO-2.5"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-72: Traceability stub — collision_mask for MutationTeaseFloor
#        collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
#        This function passes unconditionally to document the traceability gap.
#        Consistent with T-43 NOTE and T-44 NOTE patterns in the existing test suite.
# Spec: MTR-GEO-1 (AC-MTR-GEO-1.5) — traceability stub only
# ---------------------------------------------------------------------------
func test_t72_collision_mask_note() -> void:
	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
	_pass_test("T-72_collision_mask_note_see_T25")


# ===========================================================================
# ADVERSARIAL TESTS — ADV-MTR-01 through ADV-MTR-06
# ===========================================================================

# ---------------------------------------------------------------------------
# ADV-MTR-01: MutationTeaseFloor BoxShape3D non-zero extents
#
# Vulnerability probed: T-63 asserts EXACT values (20, 1, 10) for MutationTeaseFloor's
# BoxShape3D. If T-63 short-circuits before the size assertions — e.g. the
# position.x guard fails because the node was moved — a BoxShape3D with all-zero
# dimensions (the Godot 4 default for a newly assigned shape) is never caught.
# A zero-size BoxShape3D provides no collision surface: the player falls through
# the floor silently.
#
# ADV-MTR-01 asserts the non-zero invariant independently of any position check
# or exact-value assertion: size.x > 0, size.y > 0, size.z > 0.
#
# Distinct from T-63: T-63 asserts exact values (20, 1, 10); ADV-MTR-01 asserts
# only the non-zero invariant. Both are needed.
#
# Spec ref: MTR-GEO-1 AC-MTR-GEO-1.3
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mtr_01_mutation_tease_floor_box_nonzero_extents() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")
	if floor_node == null:
		_fail_test(
			"ADV-MTR-01_mutation_tease_floor_box_nonzero_extents",
			"MutationTeaseFloor node not found — cannot verify BoxShape3D non-zero extents"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-MTR-01_mutation_tease_floor_box_nonzero_extents",
			"MutationTeaseFloor has no BoxShape3D CollisionShape3D — shape may be uninitialized or default"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D

	_assert_true(
		box.size.x > 0.0,
		"ADV-MTR-01_mutation_tease_floor_box_size_x_gt_0",
		"MutationTeaseFloor BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 — zero-width floor provides no collision surface on the X axis — MTR-GEO-1 AC-MTR-GEO-1.3"
	)

	_assert_true(
		box.size.y > 0.0,
		"ADV-MTR-01_mutation_tease_floor_box_size_y_gt_0",
		"MutationTeaseFloor BoxShape3D size.y = " + str(box.size.y) + ", must be > 0 — zero-height floor has no solid thickness; player may clip through — MTR-GEO-1 AC-MTR-GEO-1.3"
	)

	_assert_true(
		box.size.z > 0.0,
		"ADV-MTR-01_mutation_tease_floor_box_size_z_gt_0",
		"MutationTeaseFloor BoxShape3D size.z = " + str(box.size.z) + ", must be > 0 — zero-depth floor provides no collision surface on the Z axis — MTR-GEO-1 AC-MTR-GEO-1.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MTR-02: MutationTeasePlatform BoxShape3D non-zero extents
#
# Vulnerability probed: T-65 asserts EXACT values (4, 1, 6) for MutationTeasePlatform's
# BoxShape3D. If T-65 short-circuits before the size assertions, a BoxShape3D with
# all-zero dimensions is never caught. A zero-size platform provides no collision
# surface: the enemy spawned above it falls through silently.
#
# ADV-MTR-02 asserts the non-zero invariant independently of any position check
# or exact-value assertion: size.x > 0, size.y > 0, size.z > 0.
#
# Distinct from T-65: T-65 asserts exact values (4, 1, 6); ADV-MTR-02 asserts
# only the non-zero invariant. Both are needed.
#
# Spec ref: MTR-GEO-2 AC-MTR-GEO-2.3
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mtr_02_mutation_tease_platform_box_nonzero_extents() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var platform: Node = root.get_node_or_null("MutationTeasePlatform")
	if platform == null:
		_fail_test(
			"ADV-MTR-02_mutation_tease_platform_box_nonzero_extents",
			"MutationTeasePlatform node not found — cannot verify BoxShape3D non-zero extents"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(platform)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-MTR-02_mutation_tease_platform_box_nonzero_extents",
			"MutationTeasePlatform has no BoxShape3D CollisionShape3D — shape may be uninitialized or default"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D

	_assert_true(
		box.size.x > 0.0,
		"ADV-MTR-02_mutation_tease_platform_box_size_x_gt_0",
		"MutationTeasePlatform BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 — zero-width platform provides no collision surface on the X axis — MTR-GEO-2 AC-MTR-GEO-2.3"
	)

	_assert_true(
		box.size.y > 0.0,
		"ADV-MTR-02_mutation_tease_platform_box_size_y_gt_0",
		"MutationTeasePlatform BoxShape3D size.y = " + str(box.size.y) + ", must be > 0 — zero-height platform has no solid thickness; enemy will fall through — MTR-GEO-2 AC-MTR-GEO-2.3"
	)

	_assert_true(
		box.size.z > 0.0,
		"ADV-MTR-02_mutation_tease_platform_box_size_z_gt_0",
		"MutationTeasePlatform BoxShape3D size.z = " + str(box.size.z) + ", must be > 0 — zero-depth platform provides no collision surface on the Z axis — MTR-GEO-2 AC-MTR-GEO-2.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MTR-03: EnemyMutationTease.position.y > 0 (enemy not embedded in floor at Y=0 or below)
#
# Vulnerability probed: T-68 asserts EnemyMutationTease.position.y > MutationTeasePlatform.position.y.
# If MutationTeasePlatform is accidentally placed at Y=-2.0 and EnemyMutationTease at Y=-1.0,
# T-68 passes (-1.0 > -2.0) but the enemy is embedded below the world floor plane (Y < 0).
# ADV-MTR-03 is an absolute lower-bound guard: enemy Y must be > 0 regardless of platform Y.
#
# Distinct from T-68: T-68 is relational (enemy Y vs platform Y); ADV-MTR-03 is absolute
# (enemy Y vs world floor plane at Y=0).
#
# Spec ref: MTR-ENC-1 AC-MTR-ENC-1.4
# ---------------------------------------------------------------------------
func test_adv_mtr_03_enemy_mutation_tease_y_above_world_floor() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy: Node = root.get_node_or_null("EnemyMutationTease")
	if enemy == null:
		_fail_test(
			"ADV-MTR-03_enemy_mutation_tease_y_above_world_floor",
			"EnemyMutationTease not found — cannot verify Y > 0 — MTR-ENC-1 AC-MTR-ENC-1.4"
		)
		root.free()
		return

	var enemy_y: float = (enemy as Node3D).position.y

	_assert_true(
		enemy_y > 0.0,
		"ADV-MTR-03_enemy_mutation_tease_y_gt_0",
		"EnemyMutationTease.position.y = " + str(enemy_y) + ", must be > 0 — enemy is embedded in or below the world floor plane (Y=0) — MTR-ENC-1 AC-MTR-ENC-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MTR-04: All four enemy node names are pairwise distinct strings, AND each
#             matches its exact expected name (catches Godot auto-dedup renames like "@2")
#
# Vulnerability probed: T-70 asserts EnemyMutationTease.name differs from the other three.
# It does not assert the exact expected name for each node. If Godot auto-renames
# "EnemyMutationTease" to "EnemyMutationTease@2" due to a scene authoring duplicate,
# get_node_or_null("EnemyMutationTease") returns null (node not found) — causing T-70
# to fail at the guard. But a subtle case: if a different node is found under the
# expected path with an auto-renamed name, the distinctness assertions may still pass
# while the actual name is wrong.
#
# ADV-MTR-04 asserts the exact expected strings for all four names AND checks all six
# pairwise combinations for distinctness, following the ADV-MBA-08 pattern.
#
# Uses node.name (not get_path()) — headless-safe per NFR-6.
#
# Spec ref: MTR-FLOW-2 AC-MTR-FLOW-2.1; Appendix B ADV-MTR-04
# ---------------------------------------------------------------------------
func test_adv_mtr_04_all_enemy_node_names_distinct_and_exact() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_tease: Node = root.get_node_or_null("EnemyMutationTease")
	var enemy_fusion_a: Node = root.get_node_or_null("EnemyFusionA")
	var enemy_fusion_b: Node = root.get_node_or_null("EnemyFusionB")
	var enemy_boss: Node = root.get_node_or_null("EnemyMiniBoss")

	if enemy_tease == null or enemy_fusion_a == null or enemy_fusion_b == null or enemy_boss == null:
		_fail_test(
			"ADV-MTR-04_all_enemy_node_names_distinct",
			"One or more of EnemyMutationTease / EnemyFusionA / EnemyFusionB / EnemyMiniBoss not found — cannot verify name distinctness (node may have been renamed/duplicated in scene)"
		)
		root.free()
		return

	var tease_name: String = enemy_tease.name
	var fusion_a_name: String = enemy_fusion_a.name
	var fusion_b_name: String = enemy_fusion_b.name
	var boss_name: String = enemy_boss.name

	# Assert each name is the exact expected string (catches Godot auto-dedup renames like "@2")
	_assert_true(
		tease_name == "EnemyMutationTease",
		"ADV-MTR-04_tease_node_name_is_EnemyMutationTease",
		"EnemyMutationTease.name = '" + tease_name + "', expected 'EnemyMutationTease' — node may have been auto-renamed by Godot (duplicate name in scene) — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)

	_assert_true(
		fusion_a_name == "EnemyFusionA",
		"ADV-MTR-04_fusion_a_node_name_is_EnemyFusionA",
		"EnemyFusionA.name = '" + fusion_a_name + "', expected 'EnemyFusionA' — node may have been auto-renamed by Godot — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)

	_assert_true(
		fusion_b_name == "EnemyFusionB",
		"ADV-MTR-04_fusion_b_node_name_is_EnemyFusionB",
		"EnemyFusionB.name = '" + fusion_b_name + "', expected 'EnemyFusionB' — node may have been auto-renamed by Godot — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)

	_assert_true(
		boss_name == "EnemyMiniBoss",
		"ADV-MTR-04_boss_node_name_is_EnemyMiniBoss",
		"EnemyMiniBoss.name = '" + boss_name + "', expected 'EnemyMiniBoss' — node may have been auto-renamed by Godot — MTR-FLOW-2 AC-MTR-FLOW-2.1"
	)

	# Assert all six pairwise combinations are mutually distinct
	_assert_true(
		tease_name != fusion_a_name,
		"ADV-MTR-04_tease_name_ne_fusion_a_name",
		"EnemyMutationTease.name ('" + tease_name + "') == EnemyFusionA.name ('" + fusion_a_name + "') — duplicate node names cause get_node_or_null shadowing — MTR-FLOW-2"
	)

	_assert_true(
		tease_name != fusion_b_name,
		"ADV-MTR-04_tease_name_ne_fusion_b_name",
		"EnemyMutationTease.name ('" + tease_name + "') == EnemyFusionB.name ('" + fusion_b_name + "') — duplicate node names cause get_node_or_null shadowing — MTR-FLOW-2"
	)

	_assert_true(
		tease_name != boss_name,
		"ADV-MTR-04_tease_name_ne_boss_name",
		"EnemyMutationTease.name ('" + tease_name + "') == EnemyMiniBoss.name ('" + boss_name + "') — duplicate node names cause get_node_or_null shadowing — MTR-FLOW-2"
	)

	_assert_true(
		fusion_a_name != fusion_b_name,
		"ADV-MTR-04_fusion_a_name_ne_fusion_b_name",
		"EnemyFusionA.name ('" + fusion_a_name + "') == EnemyFusionB.name ('" + fusion_b_name + "') — duplicate node names cause get_node_or_null shadowing"
	)

	_assert_true(
		fusion_a_name != boss_name,
		"ADV-MTR-04_fusion_a_name_ne_boss_name",
		"EnemyFusionA.name ('" + fusion_a_name + "') == EnemyMiniBoss.name ('" + boss_name + "') — duplicate node names cause get_node_or_null shadowing"
	)

	_assert_true(
		fusion_b_name != boss_name,
		"ADV-MTR-04_fusion_b_name_ne_boss_name",
		"EnemyFusionB.name ('" + fusion_b_name + "') == EnemyMiniBoss.name ('" + boss_name + "') — duplicate node names cause get_node_or_null shadowing"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MTR-05: MutationTeaseFloor.position.x within [-12, 12] (gross zone bounds check)
#
# Vulnerability probed: T-63 asserts position.x ≈ 0 ±1.0 (tight tolerance). If MutationTeaseFloor
# is accidentally placed at X=50 (in the fusion zone or beyond) during a scene refactor,
# T-63 catches this. But if T-63 short-circuits before the position.x check (e.g. the node is
# not a StaticBody3D and T-63 returns early), a grossly misplaced floor is never reported by
# position. ADV-MTR-05 is a single-focus wider bounds check that survives T-63 short-circuits.
#
# The ±12.0 m bound is wider than the tease zone (X: -10 to 10) but narrower than the next zone
# (FusionFloor at X=22.5). Any floor placement in [-12, 12] is consistent with the tease zone
# extent; outside that range the floor is in a different zone entirely.
#
# Distinct from T-63: T-63 asserts ±1.0 m (tight, node-origin centered); ADV-MTR-05 asserts
# ±12.0 m (gross zone boundary — catches floor placed in wrong zone entirely).
#
# Spec ref: MTR-GEO-1 AC-MTR-GEO-1.2; Appendix B ADV-MTR-05
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mtr_05_mutation_tease_floor_position_x_in_zone_bounds() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")
	if floor_node == null:
		_fail_test(
			"ADV-MTR-05_mutation_tease_floor_position_x_in_zone_bounds",
			"MutationTeaseFloor not found — cannot verify position.x zone bounds"
		)
		root.free()
		return

	var pos_x: float = (floor_node as Node3D).position.x

	_assert_true(
		pos_x >= -12.0 and pos_x <= 12.0,
		"ADV-MTR-05_mutation_tease_floor_x_in_zone_bounds",
		"MutationTeaseFloor.position.x = " + str(pos_x) + ", must be in [-12.0, 12.0] — floor is placed outside the mutation tease zone bounds; may be in an adjacent zone — MTR-GEO-1 AC-MTR-GEO-1.2"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MTR-06: MutationTeasePlatform top surface Y > MutationTeaseFloor top surface Y
#
# Vulnerability probed: T-71 asserts MutationTeasePlatform.position.y >= MutationTeaseFloor.position.y
# (node origin comparison). A node origin comparison is necessary but not sufficient. Consider a
# scenario where both nodes have Y=0 (node origins equal, T-71 passes with >=), but the platform
# CollisionShape3D Y offset is set to -0.5 (matching the floor's pattern instead of +0.3). In that
# case, the platform top surface = 0 + (-0.5) + 0.5 = 0.0, equal to the floor top surface of 0.0.
# The platform is not elevated above the floor — the tease visual fails — yet T-71 passes.
#
# ADV-MTR-06 computes actual top-surface Y for both nodes dynamically (using col.position.y and
# box.size.y read at runtime, not hardcoded) and asserts platform top surface > floor top surface.
# Expected: 0.8 > 0.0.
#
# Distinct from T-66 and T-71: T-66 asserts platform top surface Y in [0.5, 1.5]; T-71 asserts
# node origin Y comparison; ADV-MTR-06 asserts the platform-vs-floor top-surface relational
# invariant — a completely separate property.
#
# Spec ref: MTR-GEO-2; Appendix B ADV-MTR-06
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mtr_06_platform_top_surface_y_gt_floor_top_surface_y() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var platform: Node = root.get_node_or_null("MutationTeasePlatform")
	var floor_node: Node = root.get_node_or_null("MutationTeaseFloor")

	if platform == null:
		_fail_test(
			"ADV-MTR-06_platform_top_surface_y_gt_floor_top_surface_y",
			"MutationTeasePlatform not found — cannot compute platform top surface Y"
		)
		root.free()
		return

	if floor_node == null:
		_fail_test(
			"ADV-MTR-06_platform_top_surface_y_gt_floor_top_surface_y",
			"MutationTeaseFloor not found — cannot compute floor top surface Y"
		)
		root.free()
		return

	var platform_col: CollisionShape3D = _get_collision_shape(platform)
	if platform_col == null or not (platform_col.shape is BoxShape3D):
		_fail_test(
			"ADV-MTR-06_platform_top_surface_y_gt_floor_top_surface_y",
			"MutationTeasePlatform has no BoxShape3D — cannot compute platform top surface Y"
		)
		root.free()
		return

	var floor_col: CollisionShape3D = _get_collision_shape(floor_node)
	if floor_col == null or not (floor_col.shape is BoxShape3D):
		_fail_test(
			"ADV-MTR-06_platform_top_surface_y_gt_floor_top_surface_y",
			"MutationTeaseFloor has no BoxShape3D — cannot compute floor top surface Y"
		)
		root.free()
		return

	var platform_box: BoxShape3D = platform_col.shape as BoxShape3D
	var floor_box: BoxShape3D = floor_col.shape as BoxShape3D

	var platform_node_y: float = (platform as Node3D).position.y
	var floor_node_y: float = (floor_node as Node3D).position.y

	# Formula: node.position.y + col.position.y + (box.size.y * 0.5)
	# col Y offsets read dynamically — not hardcoded — to survive future scene edits.
	# Confirmed: platform = 0 + 0.3 + 0.5 = 0.8; floor = 0 + (-0.5) + 0.5 = 0.0
	var platform_top: float = platform_node_y + platform_col.position.y + (platform_box.size.y * 0.5)
	var floor_top: float = floor_node_y + floor_col.position.y + (floor_box.size.y * 0.5)

	_assert_true(
		platform_top > floor_top,
		"ADV-MTR-06_platform_top_surface_y_gt_floor_top_surface_y",
		"MutationTeasePlatform top surface Y (" + str(platform_top) + " = node.y(" + str(platform_node_y) + ") + col.y(" + str(platform_col.position.y) + ") + half_y(" + str(platform_box.size.y * 0.5) + ")) must be > MutationTeaseFloor top surface Y (" + str(floor_top) + " = node.y(" + str(floor_node_y) + ") + col.y(" + str(floor_col.position.y) + ") + half_y(" + str(floor_box.size.y * 0.5) + ")) — platform must be elevated above corridor floor for the visual tease to work — MTR-GEO-2"
	)

	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_mutation_tease_room.gd ---")
	_pass_count = 0
	_fail_count = 0

	# T-63: MutationTeaseFloor geometry — type, position.x ±1.0, BoxShape3D (20,1,10) exact (MTR-GEO-1)
	test_t63_mutation_tease_floor_geometry()

	# T-64: MutationTeaseFloor top surface world Y in [-0.1, 0.1] (MTR-GEO-1)
	test_t64_mutation_tease_floor_top_surface_y()

	# T-65: MutationTeasePlatform geometry — type, position.x ±2.0, BoxShape3D (4,1,6) exact (MTR-GEO-2)
	test_t65_mutation_tease_platform_geometry()

	# T-66: MutationTeasePlatform top surface world Y in [0.5, 1.5] (MTR-GEO-2)
	test_t66_mutation_tease_platform_top_surface_y()

	# T-67: EnemyMutationTease exists; scene path contains "enemy_infection_3d.tscn" (MTR-ENC-1)
	test_t67_enemy_mutation_tease_exists_and_scene_path()

	# T-68: EnemyMutationTease.position.y > MutationTeasePlatform.position.y (MTR-ENC-1)
	test_t68_enemy_mutation_tease_above_platform_origin()

	# T-69: MutationTeaseFloor right edge <= FusionFloor left edge (MTR-FLOW-1)
	test_t69_mutation_tease_floor_right_edge_le_fusion_floor_left_edge()

	# T-70: EnemyMutationTease name distinct from EnemyFusionA/B/MiniBoss (MTR-FLOW-2)
	test_t70_enemy_mutation_tease_name_distinct_from_other_enemies()

	# T-71: MutationTeasePlatform.position.y >= MutationTeaseFloor.position.y (MTR-GEO-2)
	test_t71_mutation_tease_platform_y_ge_floor_y()

	# T-72: Traceability stub — collision_mask covered by T-25 (MTR-GEO-1 stub)
	test_t72_collision_mask_note()

	# ADV-MTR-01: MutationTeaseFloor BoxShape3D non-zero extents (independent of T-63 exact values)
	test_adv_mtr_01_mutation_tease_floor_box_nonzero_extents()

	# ADV-MTR-02: MutationTeasePlatform BoxShape3D non-zero extents (independent of T-65 exact values)
	test_adv_mtr_02_mutation_tease_platform_box_nonzero_extents()

	# ADV-MTR-03: EnemyMutationTease.position.y > 0 (absolute ground-plane guard)
	test_adv_mtr_03_enemy_mutation_tease_y_above_world_floor()

	# ADV-MTR-04: All four enemy names pairwise distinct + exact expected strings
	test_adv_mtr_04_all_enemy_node_names_distinct_and_exact()

	# ADV-MTR-05: MutationTeaseFloor.position.x in [-12, 12] (gross zone bounds check)
	test_adv_mtr_05_mutation_tease_floor_position_x_in_zone_bounds()

	# ADV-MTR-06: MutationTeasePlatform top surface Y > MutationTeaseFloor top surface Y
	test_adv_mtr_06_platform_top_surface_y_gt_floor_top_surface_y()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
