#
# test_mini_boss_encounter.gd
#
# Behavioral tests for the Mini-Boss Encounter zone within containment_hall_01.tscn.
# Spec: agent_context/agents/2_spec/mini_boss_encounter_spec.md
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/mini_boss_encounter.md
#
# All tests are headless-safe: no physics tick, no await, no input simulation, no signals.
# Red phase: any scene node absent or geometry wrong will produce explicit FAIL messages.
# Green phase: all assertions pass after scene is authored to spec.
#
# Spec requirement traceability:
#   T-53  → MBA-GEO-1 (AC-MBA-GEO-1.1, 1.2, 1.3, 1.4) + MBA-GEO-3 (AC-MBA-GEO-3.1)
#             MiniBossFloor type, X ±1.0, BoxShape3D (25,1,10) exact, size.x >= 25,
#             top surface world Y in [-0.1, 0.1]
#   T-54  → MBA-GEO-1 (AC-MBA-GEO-1.4 dedicated)
#             MiniBossFloor top surface at corridor level — computed world Y in [-0.1, 0.1]
#   T-55  → MBA-BOSS-1 (AC-MBA-BOSS-1.1, 1.2, 1.3, 1.4) + MBA-BOSS-3 (AC-MBA-BOSS-3.1, 3.2)
#             EnemyMiniBoss exists, scene path, X in [55,80], Y > 0,
#             InfectionInteractionHandler.has_method("set_target_esm")
#   T-56  → MBA-FLOW-1 (AC-MBA-FLOW-1.1)
#             EnemyMiniBoss.x > SkillCheckPlatform3.x
#   T-57  → MBA-BOSS-2 (AC-MBA-BOSS-2.1, 2.2, 2.3, 2.4)
#             EnemyMiniBoss path distinct from EnemyFusionA/B and EnemyMutationTease
#   T-58  → MBA-GEO-2 (AC-MBA-GEO-2.1, 2.2, 2.3)
#             ExitFloor exists as StaticBody3D, position.x > MiniBossFloor.x, BoxShape3D non-zero
#   T-59  → MBA-FLOW-2 (AC-MBA-FLOW-2.1, 2.2, 2.3)
#             LevelExit Area3D, position.x > ExitFloor.x, CollisionShape3D non-zero BoxShape3D
#   T-60  → MBA-FLOW-3 (AC-MBA-FLOW-3.1, 3.2, 3.3)
#             LevelExit script source_code contains "level_complete"; fallback has_method
#   T-61  → MBA-FLOW-1 + MBA-GEO-2 (AC-MBA-FLOW-1.1, AC-MBA-GEO-2.2)
#             Level flow ordering: MiniBossFloor.x > SkillCheckPlatform3.x; ExitFloor.x > MiniBossFloor.x
#   T-62  → MBA-FLOW-4 (AC-MBA-FLOW-4.1)
#             ExitFloor.x > MiniBossFloor right edge (computed including col X offset)
#
# NOTE: collision_mask == 3 for all StaticBody3D nodes is already covered by T-25 in
# test_containment_hall_01.gd. No collision_mask assertion is made in this file.
#
# NFR compliance:
#   - No class_name to avoid global registry conflicts.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: root.free() called before each test method returns.
#   - No test name duplicates any T-1 through T-52 assertion name.

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
# T-53: MiniBossFloor — exists as StaticBody3D; position.x ≈ 67.5 ±1.0;
#        BoxShape3D size (25, 1, 10) exact; size.x >= 25 (MBA-GEO-3);
#        top surface world Y in [-0.1, 0.1]
# Spec: MBA-GEO-1 (AC-MBA-GEO-1.1, 1.2, 1.3, 1.4) + MBA-GEO-3 (AC-MBA-GEO-3.1)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t53_mini_boss_floor_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MiniBossFloor")
	_assert_true(
		floor_node != null,
		"T-53_mini_boss_floor_exists",
		"MiniBossFloor node not found in scene — MBA-GEO-1 AC-MBA-GEO-1.1"
	)
	if floor_node == null:
		root.free()
		return

	_assert_true(
		floor_node is StaticBody3D,
		"T-53_mini_boss_floor_is_static_body3d",
		"MiniBossFloor is " + floor_node.get_class() + ", expected StaticBody3D — MBA-GEO-1 AC-MBA-GEO-1.1"
	)

	var pos: Vector3 = (floor_node as Node3D).position
	_assert_true(
		abs(pos.x - 67.5) <= 1.0,
		"T-53_mini_boss_floor_position_x",
		"MiniBossFloor.position.x = " + str(pos.x) + ", expected 67.5 ±1.0 — MBA-GEO-1 AC-MBA-GEO-1.2"
	)

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	_assert_true(
		col != null,
		"T-53_mini_boss_floor_has_collision_shape",
		"MiniBossFloor has no CollisionShape3D child — MBA-GEO-1 AC-MBA-GEO-1.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-53_mini_boss_floor_collision_shape_is_box",
		"MiniBossFloor CollisionShape3D.shape is not BoxShape3D — MBA-GEO-1 AC-MBA-GEO-1.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(25.0, box.size.x, "T-53_mini_boss_floor_box_size_x — expected 25.0 — MBA-GEO-1 AC-MBA-GEO-1.3")
	_assert_eq_float(1.0, box.size.y, "T-53_mini_boss_floor_box_size_y — expected 1.0 — MBA-GEO-1 AC-MBA-GEO-1.3")
	_assert_eq_float(10.0, box.size.z, "T-53_mini_boss_floor_box_size_z — expected 10.0 — MBA-GEO-1 AC-MBA-GEO-1.3")

	# MBA-GEO-3: arena width threshold >= 25 m (inline per NFR-5)
	_assert_true(
		box.size.x >= 25.0,
		"T-53_mini_boss_floor_box_size_x_ge_25",
		"MiniBossFloor box.size.x = " + str(box.size.x) + ", must be >= 25.0 m (arena width threshold) — MBA-GEO-3 AC-MBA-GEO-3.1"
	)

	# Top surface world Y = node.position.y + col.position.y + (box.size.y * 0.5)
	var top_surface_y: float = pos.y + col.position.y + (box.size.y * 0.5)
	_assert_true(
		top_surface_y >= -0.1 and top_surface_y <= 0.1,
		"T-53_mini_boss_floor_top_surface_y_in_range",
		"MiniBossFloor top surface Y = " + str(top_surface_y) + ", expected in [-0.1, 0.1] (corridor level) — MBA-GEO-1 AC-MBA-GEO-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-54: MiniBossFloor top surface at corridor level — computed world Y in [-0.1, 0.1]
#        Dedicated top-surface test: verifies formula node.y + col.y + box.half_y ∈ [-0.1, 0.1]
# Spec: MBA-GEO-1 (AC-MBA-GEO-1.4 dedicated assertion)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t54_mini_boss_floor_top_surface_corridor_level() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MiniBossFloor")
	if floor_node == null:
		_fail_test(
			"T-54_mini_boss_floor_exists_for_top_surface",
			"MiniBossFloor not found — cannot compute top surface Y — MBA-GEO-1 AC-MBA-GEO-1.4"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"T-54_mini_boss_floor_box_shape_available",
			"MiniBossFloor CollisionShape3D or BoxShape3D not found — cannot compute top surface Y — MBA-GEO-1 AC-MBA-GEO-1.4"
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
		"T-54_mini_boss_floor_top_surface_y_at_corridor_level",
		"MiniBossFloor top surface world Y = " + str(top_surface_y) + " (node.y=" + str(pos_y) + " col.y=" + str(col.position.y) + " half_y=" + str(box.size.y * 0.5) + "), expected in [-0.1, 0.1] — MBA-GEO-1 AC-MBA-GEO-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-55: EnemyMiniBoss — node exists; get_scene_file_path() contains "enemy_infection_3d.tscn";
#        position.x in [55, 80]; position.y > 0.0 (not embedded in floor).
#        Also covers MBA-BOSS-3: InfectionInteractionHandler.has_method("set_target_esm")
# Spec: MBA-BOSS-1 (AC-MBA-BOSS-1.1, 1.2, 1.3, 1.4) + MBA-BOSS-3 (AC-MBA-BOSS-3.1, 3.2)
# ---------------------------------------------------------------------------
func test_t55_enemy_mini_boss_placement_and_handler_method() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy: Node = root.get_node_or_null("EnemyMiniBoss")
	_assert_true(
		enemy != null,
		"T-55_enemy_mini_boss_exists",
		"EnemyMiniBoss node not found in scene — MBA-BOSS-1 AC-MBA-BOSS-1.1"
	)
	if enemy == null:
		root.free()
		return

	# AC-MBA-BOSS-1.2: scene file path check
	var scene_path: String = enemy.get_scene_file_path()
	_assert_true(
		scene_path != "" and scene_path.contains("enemy_infection_3d.tscn"),
		"T-55_enemy_mini_boss_scene_path",
		"EnemyMiniBoss.get_scene_file_path() = '" + scene_path + "', must contain 'enemy_infection_3d.tscn' — MBA-BOSS-1 AC-MBA-BOSS-1.2"
	)

	var pos: Vector3 = (enemy as Node3D).position

	# AC-MBA-BOSS-1.3: position.x in [55, 80]
	_assert_true(
		pos.x >= 55.0 and pos.x <= 80.0,
		"T-55_enemy_mini_boss_position_x_in_zone",
		"EnemyMiniBoss.position.x = " + str(pos.x) + ", expected in [55.0, 80.0] (mini-boss zone bounds) — MBA-BOSS-1 AC-MBA-BOSS-1.3"
	)

	# AC-MBA-BOSS-1.4: position.y > 0 (not embedded in floor geometry)
	_assert_true(
		pos.y > 0.0,
		"T-55_enemy_mini_boss_position_y_above_floor",
		"EnemyMiniBoss.position.y = " + str(pos.y) + ", must be > 0.0 (not embedded in floor) — MBA-BOSS-1 AC-MBA-BOSS-1.4"
	)

	# MBA-BOSS-3 (inline per NFR-6): InfectionInteractionHandler has set_target_esm
	# AC-MBA-BOSS-3.1: node exists (reference check — primary coverage by T-9)
	var handler: Node = root.get_node_or_null("InfectionInteractionHandler")
	_assert_true(
		handler != null,
		"T-55_infection_interaction_handler_exists",
		"InfectionInteractionHandler not found — cannot verify set_target_esm wiring — MBA-BOSS-3 AC-MBA-BOSS-3.1"
	)
	if handler != null:
		# AC-MBA-BOSS-3.2: has_method("set_target_esm")
		_assert_true(
			handler.has_method("set_target_esm"),
			"T-55_infection_interaction_handler_has_set_target_esm",
			"InfectionInteractionHandler does not have method set_target_esm() — required for EnemyMiniBoss wiring — MBA-BOSS-3 AC-MBA-BOSS-3.2"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-56: EnemyMiniBoss after skill check — EnemyMiniBoss.position.x > SkillCheckPlatform3.position.x
# Spec: MBA-FLOW-1 (AC-MBA-FLOW-1.1)
# ---------------------------------------------------------------------------
func test_t56_enemy_mini_boss_after_skill_check() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy: Node = root.get_node_or_null("EnemyMiniBoss")
	var platform3: Node = root.get_node_or_null("SkillCheckPlatform3")

	if enemy == null:
		_fail_test(
			"T-56_enemy_mini_boss_exists_for_flow",
			"EnemyMiniBoss not found — cannot verify boss comes after skill check — MBA-FLOW-1 AC-MBA-FLOW-1.1"
		)
		root.free()
		return

	if platform3 == null:
		_fail_test(
			"T-56_skill_check_platform3_exists_for_flow",
			"SkillCheckPlatform3 not found — cannot verify boss comes after skill check — MBA-FLOW-1 AC-MBA-FLOW-1.1"
		)
		root.free()
		return

	var enemy_x: float = (enemy as Node3D).position.x
	var p3x: float = (platform3 as Node3D).position.x

	_assert_true(
		enemy_x > p3x,
		"T-56_enemy_mini_boss_x_greater_than_skill_check_platform3_x",
		"EnemyMiniBoss.position.x (" + str(enemy_x) + ") must be > SkillCheckPlatform3.position.x (" + str(p3x) + ") — boss must come after skill check zone — MBA-FLOW-1 AC-MBA-FLOW-1.1"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-57: EnemyMiniBoss distinct node path — get_path() differs from EnemyFusionA,
#        EnemyFusionB, and EnemyMutationTease paths
# Spec: MBA-BOSS-2 (AC-MBA-BOSS-2.1, 2.2, 2.3, 2.4)
# ---------------------------------------------------------------------------
func test_t57_enemy_mini_boss_distinct_path() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_boss: Node = root.get_node_or_null("EnemyMiniBoss")
	var enemy_fusion_a: Node = root.get_node_or_null("EnemyFusionA")
	var enemy_fusion_b: Node = root.get_node_or_null("EnemyFusionB")
	var enemy_tease: Node = root.get_node_or_null("EnemyMutationTease")

	# AC-MBA-BOSS-2.1: all four nodes present
	_assert_true(
		enemy_boss != null,
		"T-57_enemy_mini_boss_exists_for_path_check",
		"EnemyMiniBoss not found — cannot verify distinct path — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)
	_assert_true(
		enemy_fusion_a != null,
		"T-57_enemy_fusion_a_exists_for_path_check",
		"EnemyFusionA not found — cannot verify distinct path — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)
	_assert_true(
		enemy_fusion_b != null,
		"T-57_enemy_fusion_b_exists_for_path_check",
		"EnemyFusionB not found — cannot verify distinct path — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)
	_assert_true(
		enemy_tease != null,
		"T-57_enemy_mutation_tease_exists_for_path_check",
		"EnemyMutationTease not found — cannot verify distinct path — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)

	if enemy_boss == null or enemy_fusion_a == null or enemy_fusion_b == null or enemy_tease == null:
		root.free()
		return

	var boss_path: String = String(enemy_boss.get_path())
	var fusion_a_path: String = String(enemy_fusion_a.get_path())
	var fusion_b_path: String = String(enemy_fusion_b.get_path())
	var tease_path: String = String(enemy_tease.get_path())

	# AC-MBA-BOSS-2.2: boss path != EnemyFusionA path
	_assert_true(
		boss_path != fusion_a_path,
		"T-57_enemy_mini_boss_path_ne_fusion_a",
		"EnemyMiniBoss path '" + boss_path + "' must not equal EnemyFusionA path '" + fusion_a_path + "' — MBA-BOSS-2 AC-MBA-BOSS-2.2"
	)

	# AC-MBA-BOSS-2.3: boss path != EnemyFusionB path
	_assert_true(
		boss_path != fusion_b_path,
		"T-57_enemy_mini_boss_path_ne_fusion_b",
		"EnemyMiniBoss path '" + boss_path + "' must not equal EnemyFusionB path '" + fusion_b_path + "' — MBA-BOSS-2 AC-MBA-BOSS-2.3"
	)

	# AC-MBA-BOSS-2.4: boss path != EnemyMutationTease path
	_assert_true(
		boss_path != tease_path,
		"T-57_enemy_mini_boss_path_ne_mutation_tease",
		"EnemyMiniBoss path '" + boss_path + "' must not equal EnemyMutationTease path '" + tease_path + "' — MBA-BOSS-2 AC-MBA-BOSS-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-58: ExitFloor — exists as StaticBody3D; position.x > MiniBossFloor.position.x;
#        BoxShape3D non-zero extents (size.x > 0, size.y > 0, size.z > 0)
# Spec: MBA-GEO-2 (AC-MBA-GEO-2.1, 2.2, 2.3)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t58_exit_floor_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var exit_floor: Node = root.get_node_or_null("ExitFloor")
	_assert_true(
		exit_floor != null,
		"T-58_exit_floor_exists",
		"ExitFloor node not found in scene — MBA-GEO-2 AC-MBA-GEO-2.1"
	)
	if exit_floor == null:
		root.free()
		return

	_assert_true(
		exit_floor is StaticBody3D,
		"T-58_exit_floor_is_static_body3d",
		"ExitFloor is " + exit_floor.get_class() + ", expected StaticBody3D — MBA-GEO-2 AC-MBA-GEO-2.1"
	)

	# AC-MBA-GEO-2.2: position.x > MiniBossFloor.position.x
	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	if mini_boss_floor == null:
		_fail_test(
			"T-58_mini_boss_floor_exists_for_exit_floor_comparison",
			"MiniBossFloor not found — cannot verify ExitFloor.x > MiniBossFloor.x — MBA-GEO-2 AC-MBA-GEO-2.2"
		)
	else:
		var exit_x: float = (exit_floor as Node3D).position.x
		var boss_floor_x: float = (mini_boss_floor as Node3D).position.x
		_assert_true(
			exit_x > boss_floor_x,
			"T-58_exit_floor_x_greater_than_mini_boss_floor_x",
			"ExitFloor.position.x (" + str(exit_x) + ") must be > MiniBossFloor.position.x (" + str(boss_floor_x) + ") — MBA-GEO-2 AC-MBA-GEO-2.2"
		)

	# AC-MBA-GEO-2.3: BoxShape3D non-degenerate
	var col: CollisionShape3D = _get_collision_shape(exit_floor)
	_assert_true(
		col != null,
		"T-58_exit_floor_has_collision_shape",
		"ExitFloor has no CollisionShape3D child — MBA-GEO-2 AC-MBA-GEO-2.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-58_exit_floor_collision_shape_is_box",
		"ExitFloor CollisionShape3D.shape is not BoxShape3D — MBA-GEO-2 AC-MBA-GEO-2.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(
		box.size.x > 0.0,
		"T-58_exit_floor_box_size_x_nonzero",
		"ExitFloor BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 (non-degenerate floor) — MBA-GEO-2 AC-MBA-GEO-2.3"
	)
	_assert_true(
		box.size.y > 0.0,
		"T-58_exit_floor_box_size_y_nonzero",
		"ExitFloor BoxShape3D size.y = " + str(box.size.y) + ", must be > 0 (non-degenerate floor) — MBA-GEO-2 AC-MBA-GEO-2.3"
	)
	_assert_true(
		box.size.z > 0.0,
		"T-58_exit_floor_box_size_z_nonzero",
		"ExitFloor BoxShape3D size.z = " + str(box.size.z) + ", must be > 0 (non-degenerate floor) — MBA-GEO-2 AC-MBA-GEO-2.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-59: LevelExit — exists as Area3D; position.x > ExitFloor.position.x;
#        CollisionShape3D present with BoxShape3D non-zero extents
# Spec: MBA-FLOW-2 (AC-MBA-FLOW-2.1, 2.2, 2.3)
# ---------------------------------------------------------------------------
func test_t59_level_exit_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	_assert_true(
		level_exit != null,
		"T-59_level_exit_exists",
		"LevelExit node not found in scene — MBA-FLOW-2 AC-MBA-FLOW-2.1"
	)
	if level_exit == null:
		root.free()
		return

	_assert_true(
		level_exit is Area3D,
		"T-59_level_exit_is_area3d",
		"LevelExit is " + level_exit.get_class() + ", expected Area3D — MBA-FLOW-2 AC-MBA-FLOW-2.1"
	)

	# AC-MBA-FLOW-2.2: position.x > ExitFloor.position.x
	var exit_floor: Node = root.get_node_or_null("ExitFloor")
	if exit_floor == null:
		_fail_test(
			"T-59_exit_floor_exists_for_level_exit_comparison",
			"ExitFloor not found — cannot verify LevelExit.x > ExitFloor.x — MBA-FLOW-2 AC-MBA-FLOW-2.2"
		)
	else:
		var level_exit_x: float = (level_exit as Node3D).position.x
		var exit_floor_x: float = (exit_floor as Node3D).position.x
		_assert_true(
			level_exit_x > exit_floor_x,
			"T-59_level_exit_x_greater_than_exit_floor_x",
			"LevelExit.position.x (" + str(level_exit_x) + ") must be > ExitFloor.position.x (" + str(exit_floor_x) + ") — MBA-FLOW-2 AC-MBA-FLOW-2.2"
		)

	# AC-MBA-FLOW-2.3: CollisionShape3D with non-zero BoxShape3D
	var col: CollisionShape3D = _get_collision_shape(level_exit)
	_assert_true(
		col != null,
		"T-59_level_exit_has_collision_shape",
		"LevelExit has no CollisionShape3D child — MBA-FLOW-2 AC-MBA-FLOW-2.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-59_level_exit_collision_shape_is_box",
		"LevelExit CollisionShape3D.shape is not BoxShape3D — MBA-FLOW-2 AC-MBA-FLOW-2.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(
		box.size.x > 0.0,
		"T-59_level_exit_box_size_x_nonzero",
		"LevelExit BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 (trigger large enough to detect player) — MBA-FLOW-2 AC-MBA-FLOW-2.3"
	)
	_assert_true(
		box.size.y > 0.0,
		"T-59_level_exit_box_size_y_nonzero",
		"LevelExit BoxShape3D size.y = " + str(box.size.y) + ", must be > 0 (trigger large enough to detect player) — MBA-FLOW-2 AC-MBA-FLOW-2.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-60: LevelExit script — source_code contains "level_complete".
#        Fallback: if source_code is empty/null in headless mode, assert
#        has_method("_on_body_entered") as a proxy for correct script compilation.
# Spec: MBA-FLOW-3 (AC-MBA-FLOW-3.1, 3.2, 3.3)
# ---------------------------------------------------------------------------
func test_t60_level_exit_script_contains_level_complete() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	if level_exit == null:
		_fail_test(
			"T-60_level_exit_exists_for_script_check",
			"LevelExit not found — cannot inspect script source — MBA-FLOW-3 AC-MBA-FLOW-3.1"
		)
		root.free()
		return

	# AC-MBA-FLOW-3.1: script is non-null
	var script_obj: Script = level_exit.get_script() as Script
	_assert_true(
		script_obj != null,
		"T-60_level_exit_has_script",
		"LevelExit has no script attached — MBA-FLOW-3 AC-MBA-FLOW-3.1"
	)
	if script_obj == null:
		root.free()
		return

	# AC-MBA-FLOW-3.2 + 3.3: check source_code; fallback to has_method if empty
	var source: String = script_obj.source_code
	if source != null and source != "":
		# Primary path: source_code is accessible — assert it contains "level_complete"
		_assert_true(
			source.contains("level_complete"),
			"T-60_level_exit_script_source_contains_level_complete",
			"LevelExit script source_code does not contain 'level_complete' — MBA-FLOW-3 AC-MBA-FLOW-3.3"
		)
	else:
		# Fallback path: headless mode compiled the script; source_code is empty.
		# Proxy: the method _on_body_entered must exist, confirming correct script was compiled.
		print("  NOTE: T-60 — LevelExit script.source_code is empty in headless mode; using has_method fallback — MBA-FLOW-3 AC-MBA-FLOW-3.2 fallback")
		_assert_true(
			level_exit.has_method("_on_body_entered"),
			"T-60_level_exit_has_method_on_body_entered_fallback",
			"LevelExit.has_method('_on_body_entered') returned false — script with 'level_complete' path did not compile correctly (source_code was empty) — MBA-FLOW-3 AC-MBA-FLOW-3.3 fallback"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-61: Level flow ordering — MiniBossFloor.position.x > SkillCheckPlatform3.position.x;
#        ExitFloor.position.x > MiniBossFloor.position.x
# Spec: MBA-FLOW-1 + MBA-GEO-2 (AC-MBA-FLOW-1.1, AC-MBA-GEO-2.2)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t61_level_flow_ordering() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	var skill_check_p3: Node = root.get_node_or_null("SkillCheckPlatform3")
	var exit_floor: Node = root.get_node_or_null("ExitFloor")

	# AC-MBA-FLOW-1.1: MiniBossFloor.x > SkillCheckPlatform3.x (boss zone after skill check)
	if mini_boss_floor == null:
		_fail_test(
			"T-61_mini_boss_floor_exists_for_flow_ordering",
			"MiniBossFloor not found — cannot verify level flow ordering — MBA-FLOW-1"
		)
	elif skill_check_p3 == null:
		_fail_test(
			"T-61_skill_check_platform3_exists_for_flow_ordering",
			"SkillCheckPlatform3 not found — cannot verify boss zone comes after skill check — MBA-FLOW-1 AC-MBA-FLOW-1.1"
		)
	else:
		var boss_floor_x: float = (mini_boss_floor as Node3D).position.x
		var p3x: float = (skill_check_p3 as Node3D).position.x
		_assert_true(
			boss_floor_x > p3x,
			"T-61_mini_boss_floor_x_greater_than_skill_check_platform3_x",
			"MiniBossFloor.position.x (" + str(boss_floor_x) + ") must be > SkillCheckPlatform3.position.x (" + str(p3x) + ") — boss zone must come after skill check zone — MBA-FLOW-1 AC-MBA-FLOW-1.1"
		)

	# AC-MBA-GEO-2.2: ExitFloor.x > MiniBossFloor.x (exit floor after boss arena)
	if mini_boss_floor == null:
		_fail_test(
			"T-61_mini_boss_floor_exists_for_exit_floor_ordering",
			"MiniBossFloor not found — cannot verify ExitFloor comes after boss arena — MBA-GEO-2"
		)
	elif exit_floor == null:
		_fail_test(
			"T-61_exit_floor_exists_for_ordering",
			"ExitFloor not found — cannot verify ExitFloor comes after boss arena — MBA-GEO-2 AC-MBA-GEO-2.2"
		)
	else:
		var exit_x: float = (exit_floor as Node3D).position.x
		var boss_floor_x: float = (mini_boss_floor as Node3D).position.x
		_assert_true(
			exit_x > boss_floor_x,
			"T-61_exit_floor_x_greater_than_mini_boss_floor_x",
			"ExitFloor.position.x (" + str(exit_x) + ") must be > MiniBossFloor.position.x (" + str(boss_floor_x) + ") — exit floor must come after boss arena — MBA-GEO-2 AC-MBA-GEO-2.2"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-62: ExitFloor after arena — ExitFloor.position.x > MiniBossFloor right edge
#        Right edge = MiniBossFloor.position.x + col.position.x + (box.size.x / 2.0)
#        col.position.x is read dynamically (not hardcoded) to survive future scene edits.
# Spec: MBA-FLOW-4 (AC-MBA-FLOW-4.1)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_t62_exit_floor_after_mini_boss_arena_right_edge() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	var exit_floor: Node = root.get_node_or_null("ExitFloor")

	if mini_boss_floor == null:
		_fail_test(
			"T-62_mini_boss_floor_exists_for_right_edge",
			"MiniBossFloor not found — cannot compute arena right edge — MBA-FLOW-4 AC-MBA-FLOW-4.1"
		)
		root.free()
		return

	if exit_floor == null:
		_fail_test(
			"T-62_exit_floor_exists_for_right_edge_check",
			"ExitFloor not found — cannot verify it starts after boss arena ends — MBA-FLOW-4 AC-MBA-FLOW-4.1"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(mini_boss_floor)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"T-62_mini_boss_floor_box_shape_for_right_edge",
			"MiniBossFloor CollisionShape3D or BoxShape3D not found — cannot compute right edge — MBA-FLOW-4 AC-MBA-FLOW-4.1"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	var boss_floor_x: float = (mini_boss_floor as Node3D).position.x
	# Right edge formula reads col.position.x dynamically (NFR risk mitigation)
	var right_edge: float = boss_floor_x + col.position.x + (box.size.x / 2.0)
	var exit_x: float = (exit_floor as Node3D).position.x

	_assert_true(
		exit_x > right_edge,
		"T-62_exit_floor_x_greater_than_mini_boss_floor_right_edge",
		"ExitFloor.position.x (" + str(exit_x) + ") must be > MiniBossFloor right edge (" + str(right_edge) + " = " + str(boss_floor_x) + " + col.x(" + str(col.position.x) + ") + half_x(" + str(box.size.x / 2.0) + ")) — exit must start after arena ends — MBA-FLOW-4 AC-MBA-FLOW-4.1"
	)

	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_mini_boss_encounter.gd ---")
	_pass_count = 0
	_fail_count = 0

	# T-53: MiniBossFloor geometry + arena width threshold (MBA-GEO-1, MBA-GEO-3)
	test_t53_mini_boss_floor_geometry()

	# T-54: MiniBossFloor top surface at corridor level — dedicated assertion (MBA-GEO-1)
	test_t54_mini_boss_floor_top_surface_corridor_level()

	# T-55: EnemyMiniBoss placement + InfectionInteractionHandler method guard (MBA-BOSS-1, MBA-BOSS-3)
	test_t55_enemy_mini_boss_placement_and_handler_method()

	# T-56: EnemyMiniBoss after skill check zone (MBA-FLOW-1)
	test_t56_enemy_mini_boss_after_skill_check()

	# T-57: EnemyMiniBoss distinct node path (MBA-BOSS-2)
	test_t57_enemy_mini_boss_distinct_path()

	# T-58: ExitFloor geometry (MBA-GEO-2)
	test_t58_exit_floor_geometry()

	# T-59: LevelExit Area3D geometry + CollisionShape3D (MBA-FLOW-2)
	test_t59_level_exit_geometry()

	# T-60: LevelExit script contains "level_complete" (MBA-FLOW-3)
	test_t60_level_exit_script_contains_level_complete()

	# T-61: Level flow ordering (MBA-FLOW-1, MBA-GEO-2)
	test_t61_level_flow_ordering()

	# T-62: ExitFloor positioned after MiniBossFloor right edge (MBA-FLOW-4)
	test_t62_exit_floor_after_mini_boss_arena_right_edge()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
