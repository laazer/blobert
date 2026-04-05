#
# test_fusion_opportunity_room.gd
#
# Behavioral tests for the Fusion Opportunity Room zone within containment_hall_01.tscn.
# Spec: agent_context/agents/2_spec/fusion_opportunity_room_spec.md
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/fusion_opportunity_room.md
#
# All tests are headless-safe: no physics tick, no await, no input simulation, no signals.
# Red phase: any scene node, script, or scene file that does not yet exist will produce
# explicit FAIL messages. Green phase: all assertions pass after implementation.
#
# Spec requirement traceability:
#   T-31  → FUSE-GEO-1 (AC-FUSE-GEO-1.1, 1.2, 1.3) — FusionFloor origin + exact shape
#   T-32  → FUSE-GEO-2 (AC-FUSE-GEO-2.1, 2.2, 2.3, 2.4) — FusionPlatformA exact shape + top surface Y
#   T-33  → FUSE-GEO-3 (AC-FUSE-GEO-3.1, 3.2, 3.3, 3.4) — FusionPlatformB exact shape + top surface Y
#   T-34  → FUSE-GEO-4 (AC-FUSE-GEO-4.1, 4.2, 4.3) — Platform gap > 0 and <= 10 m, approx 9 m
#   T-35  → FUSE-ENC-1 (AC-FUSE-ENC-1.3, 1.7) — EnemyFusionA scene path + Y above platform guard
#   T-36  → FUSE-ENC-1 (AC-FUSE-ENC-1.6, 1.8) — EnemyFusionB scene path + Y above platform guard
#   T-37  → FUSE-WIRE-1 (AC-FUSE-WIRE-1.2) — InfectionInteractionHandler has_method guard
#   T-38  → FUSE-WIRE-1 (AC-FUSE-WIRE-1.3, 1.4) — slot manager non-null + get_slot_count == 2
#   T-39  → FUSE-WIRE-2 (AC-FUSE-WIRE-2.1 through 2.4) — can_fuse gate (pure unit, FOR traceability)
#   T-40  → FUSE-WIRE-2 (AC-FUSE-WIRE-2.5 through 2.7) — resolve_fusion side effects (pure unit)
#   T-41  → FUSE-HUD-1 (AC-FUSE-HUD-1.1 through 1.7) — HUD nodes present in game_ui.tscn
#   T-42  → FUSE-HUD-1 (AC-FUSE-HUD-1.8 through 1.11) — HUD node sizes, viewport bounds, visibility
#          Viewport bounds use get_global_rect() (MAINT-HCSI HCSI-6) so reparenting under a scaled HUD root stays meaningful.
#
# NOTE: collision_mask assertions for FusionFloor/PlatformA/PlatformB are already covered by T-25
# in test_containment_hall_01.gd. Enemy position assertions (±0.1 m) are already covered by T-24.
# InfectionInteractionHandler node existence and script path are already covered by T-9 and T-16.
# FusionResolver can_fuse and resolve_fusion logic is already covered in tests/fusion/test_fusion_resolver.gd.
# T-39 and T-40 are additive traceability tests using distinct test names (T-39_* / T-40_*).
# T-41 and T-42 use distinct test names (T-41_* / T-42_*) to avoid collision with test_player_hud_layout.gd.
#
# NFR compliance:
#   - No class_name to avoid conflicts with other test classes.
#   - extends Object; run_all() -> int pattern.
#   - Scene cleanup: any root added to the scene tree is removed and freed before the method returns.

extends "res://tests/utils/test_utils.gd"

const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"
const GAME_UI_PATH: String = "res://scenes/ui/game_ui.tscn"

# Position tolerance used for platform-level checks.
const POS_TOL: float = 0.5
const POS_TOL_X_NARROW: float = 1.0

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


# Load game_ui.tscn. Returns null and records failure when absent.
func _load_game_ui() -> Node:
	var packed: PackedScene = load(GAME_UI_PATH) as PackedScene
	if packed == null:
		_fail_test("game_ui_load_guard", "ResourceLoader.load returned null for " + GAME_UI_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("game_ui_instantiate_guard", "instantiate() returned null for " + GAME_UI_PATH)
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


# Add a node to the scene tree for _ready() propagation; returns the tree used.
# Caller must call _remove_from_tree(root, tree) after assertions.
func _add_to_tree(root: Node) -> SceneTree:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return null
	tree.root.add_child(root)
	return tree


func _remove_from_tree(root: Node, tree: SceneTree) -> void:
	if tree != null and tree.root != null and root.is_inside_tree():
		tree.root.remove_child(root)


# ---------------------------------------------------------------------------
# T-31: FusionFloor geometry — origin X ≈ 22.5 ±1.0; BoxShape3D size (25, 1, 10)
# Spec: FUSE-GEO-1 (AC-FUSE-GEO-1.1, 1.2, 1.3)
# NOTE: collision_mask is already asserted by T-25 in test_containment_hall_01.gd.
# ---------------------------------------------------------------------------
func test_t31_fusion_floor_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var floor_node: Node = root.get_node_or_null("FusionFloor")
	_assert_true(
		floor_node != null,
		"T-31_fusion_floor_exists",
		"FusionFloor node not found in scene — FUSE-GEO-1 AC-FUSE-GEO-1.1"
	)
	if floor_node == null:
		root.free()
		return

	_assert_true(
		floor_node is StaticBody3D,
		"T-31_fusion_floor_is_static_body3d",
		"FusionFloor is " + floor_node.get_class() + ", expected StaticBody3D — FUSE-GEO-1 AC-FUSE-GEO-1.1"
	)

	var pos: Vector3 = (floor_node as Node3D).position
	_assert_true(
		abs(pos.x - 22.5) <= 1.0,
		"T-31_fusion_floor_position_x",
		"FusionFloor.position.x = " + str(pos.x) + ", expected 22.5 ±1.0 — FUSE-GEO-1 AC-FUSE-GEO-1.2"
	)

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	_assert_true(
		col != null,
		"T-31_fusion_floor_has_collision_shape",
		"FusionFloor has no CollisionShape3D child — FUSE-GEO-1 AC-FUSE-GEO-1.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-31_fusion_floor_collision_shape_is_box",
		"FusionFloor CollisionShape3D.shape is not BoxShape3D — FUSE-GEO-1 AC-FUSE-GEO-1.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(25.0, box.size.x, "T-31_fusion_floor_box_size_x — expected 25.0 — FUSE-GEO-1 AC-FUSE-GEO-1.3")
	_assert_eq_float(1.0, box.size.y, "T-31_fusion_floor_box_size_y — expected 1.0 — FUSE-GEO-1 AC-FUSE-GEO-1.3")
	_assert_eq_float(10.0, box.size.z, "T-31_fusion_floor_box_size_z — expected 10.0 — FUSE-GEO-1 AC-FUSE-GEO-1.3")

	root.free()


# ---------------------------------------------------------------------------
# T-32: FusionPlatformA geometry — position.x ≈ 15 ±0.5; BoxShape3D size (4,1,6); top surface Y in [0.5, 1.2]
# Spec: FUSE-GEO-2 (AC-FUSE-GEO-2.1, 2.2, 2.3, 2.4)
# ---------------------------------------------------------------------------
func test_t32_fusion_platform_a_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var plat: Node = root.get_node_or_null("FusionPlatformA")
	_assert_true(
		plat != null,
		"T-32_fusion_platform_a_exists",
		"FusionPlatformA node not found in scene — FUSE-GEO-2 AC-FUSE-GEO-2.1"
	)
	if plat == null:
		root.free()
		return

	_assert_true(
		plat is StaticBody3D,
		"T-32_fusion_platform_a_is_static_body3d",
		"FusionPlatformA is " + plat.get_class() + ", expected StaticBody3D — FUSE-GEO-2 AC-FUSE-GEO-2.1"
	)

	var pos: Vector3 = (plat as Node3D).position
	_assert_true(
		abs(pos.x - 15.0) <= POS_TOL,
		"T-32_fusion_platform_a_position_x",
		"FusionPlatformA.position.x = " + str(pos.x) + ", expected 15.0 ±" + str(POS_TOL) + " — FUSE-GEO-2 AC-FUSE-GEO-2.2"
	)

	var col: CollisionShape3D = _get_collision_shape(plat)
	_assert_true(
		col != null,
		"T-32_fusion_platform_a_has_collision_shape",
		"FusionPlatformA has no CollisionShape3D child — FUSE-GEO-2 AC-FUSE-GEO-2.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-32_fusion_platform_a_collision_shape_is_box",
		"FusionPlatformA CollisionShape3D.shape is not BoxShape3D — FUSE-GEO-2 AC-FUSE-GEO-2.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(4.0, box.size.x, "T-32_fusion_platform_a_box_size_x — expected 4.0 — FUSE-GEO-2 AC-FUSE-GEO-2.3")
	_assert_eq_float(1.0, box.size.y, "T-32_fusion_platform_a_box_size_y — expected 1.0 — FUSE-GEO-2 AC-FUSE-GEO-2.3")
	_assert_eq_float(6.0, box.size.z, "T-32_fusion_platform_a_box_size_z — expected 6.0 — FUSE-GEO-2 AC-FUSE-GEO-2.3")

	# Top surface world Y = node.position.y + col.position.y + (box.size.y * 0.5)
	var top_surface_y: float = pos.y + col.position.y + (box.size.y * 0.5)
	_assert_true(
		top_surface_y >= 0.5 and top_surface_y <= 1.2,
		"T-32_fusion_platform_a_top_surface_y_in_range",
		"FusionPlatformA top surface Y = " + str(top_surface_y) + ", expected in [0.5, 1.2] — FUSE-GEO-2 AC-FUSE-GEO-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-33: FusionPlatformB geometry — position.x ≈ 28 ±0.5; BoxShape3D size (4,1,6); top surface Y in [0.5, 1.2]
# Spec: FUSE-GEO-3 (AC-FUSE-GEO-3.1, 3.2, 3.3, 3.4)
# ---------------------------------------------------------------------------
func test_t33_fusion_platform_b_geometry() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var plat: Node = root.get_node_or_null("FusionPlatformB")
	_assert_true(
		plat != null,
		"T-33_fusion_platform_b_exists",
		"FusionPlatformB node not found in scene — FUSE-GEO-3 AC-FUSE-GEO-3.1"
	)
	if plat == null:
		root.free()
		return

	_assert_true(
		plat is StaticBody3D,
		"T-33_fusion_platform_b_is_static_body3d",
		"FusionPlatformB is " + plat.get_class() + ", expected StaticBody3D — FUSE-GEO-3 AC-FUSE-GEO-3.1"
	)

	var pos: Vector3 = (plat as Node3D).position
	_assert_true(
		abs(pos.x - 28.0) <= POS_TOL,
		"T-33_fusion_platform_b_position_x",
		"FusionPlatformB.position.x = " + str(pos.x) + ", expected 28.0 ±" + str(POS_TOL) + " — FUSE-GEO-3 AC-FUSE-GEO-3.2"
	)

	var col: CollisionShape3D = _get_collision_shape(plat)
	_assert_true(
		col != null,
		"T-33_fusion_platform_b_has_collision_shape",
		"FusionPlatformB has no CollisionShape3D child — FUSE-GEO-3 AC-FUSE-GEO-3.3"
	)
	if col == null:
		root.free()
		return

	_assert_true(
		col.shape != null and col.shape is BoxShape3D,
		"T-33_fusion_platform_b_collision_shape_is_box",
		"FusionPlatformB CollisionShape3D.shape is not BoxShape3D — FUSE-GEO-3 AC-FUSE-GEO-3.3"
	)
	if not (col.shape is BoxShape3D):
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_eq_float(4.0, box.size.x, "T-33_fusion_platform_b_box_size_x — expected 4.0 — FUSE-GEO-3 AC-FUSE-GEO-3.3")
	_assert_eq_float(1.0, box.size.y, "T-33_fusion_platform_b_box_size_y — expected 1.0 — FUSE-GEO-3 AC-FUSE-GEO-3.3")
	_assert_eq_float(6.0, box.size.z, "T-33_fusion_platform_b_box_size_z — expected 6.0 — FUSE-GEO-3 AC-FUSE-GEO-3.3")

	var top_surface_y: float = pos.y + col.position.y + (box.size.y * 0.5)
	_assert_true(
		top_surface_y >= 0.5 and top_surface_y <= 1.2,
		"T-33_fusion_platform_b_top_surface_y_in_range",
		"FusionPlatformB top surface Y = " + str(top_surface_y) + ", expected in [0.5, 1.2] — FUSE-GEO-3 AC-FUSE-GEO-3.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-34: Platform gap reachability — gap > 0 m and <= 10 m; approx 9.0 m ±0.5
# Spec: FUSE-GEO-4 (AC-FUSE-GEO-4.1, 4.2, 4.3)
# Gap = (PlatformB.left_edge) - (PlatformA.right_edge), using CollisionShape3D X offsets and box half-widths.
# ---------------------------------------------------------------------------
func test_t34_platform_gap_reachability() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var plat_a: Node = root.get_node_or_null("FusionPlatformA")
	var plat_b: Node = root.get_node_or_null("FusionPlatformB")

	if plat_a == null or plat_b == null:
		_fail_test(
			"T-34_platform_gap_nodes_exist",
			"FusionPlatformA or FusionPlatformB not found — cannot compute gap — FUSE-GEO-4"
		)
		root.free()
		return

	var col_a: CollisionShape3D = _get_collision_shape(plat_a)
	var col_b: CollisionShape3D = _get_collision_shape(plat_b)

	if col_a == null or col_b == null or not (col_a.shape is BoxShape3D) or not (col_b.shape is BoxShape3D):
		_fail_test(
			"T-34_platform_gap_shapes_exist",
			"FusionPlatformA or FusionPlatformB has missing or non-BoxShape3D CollisionShape3D — FUSE-GEO-4"
		)
		root.free()
		return

	var box_a: BoxShape3D = col_a.shape as BoxShape3D
	var box_b: BoxShape3D = col_b.shape as BoxShape3D

	var pos_ax: float = (plat_a as Node3D).position.x
	var pos_bx: float = (plat_b as Node3D).position.x

	# Compute edges including CollisionShape3D local X offsets.
	var right_edge_a: float = pos_ax + col_a.position.x + (box_a.size.x / 2.0)
	var left_edge_b: float = pos_bx + col_b.position.x - (box_b.size.x / 2.0)
	var gap: float = left_edge_b - right_edge_a

	_assert_true(
		gap > 0.0,
		"T-34_platform_gap_is_positive",
		"Platform gap = " + str(gap) + " m, must be > 0 (platforms must not overlap) — FUSE-GEO-4 AC-FUSE-GEO-4.1"
	)
	_assert_true(
		gap <= 10.0,
		"T-34_platform_gap_le_10m",
		"Platform gap = " + str(gap) + " m, must be <= 10.0 m (conservative jump range) — FUSE-GEO-4 AC-FUSE-GEO-4.2"
	)
	_assert_true(
		abs(gap - 9.0) <= 0.5,
		"T-34_platform_gap_approx_9m",
		"Platform gap = " + str(gap) + " m, expected 9.0 ±0.5 m (right_edge_A=" + str(right_edge_a) + " left_edge_B=" + str(left_edge_b) + ") — FUSE-GEO-4 AC-FUSE-GEO-4.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-35: EnemyFusionA — scene file path contains "enemy_infection_3d.tscn";
#        position.y is above FusionPlatformA.position.y
# Spec: FUSE-ENC-1 (AC-FUSE-ENC-1.3, 1.7)
# NOTE: exact position (±0.1 m) is already covered by T-24. This test adds
#       scene-path verification and the Y-above-platform guard.
# ---------------------------------------------------------------------------
func test_t35_enemy_fusion_a_scene_path_and_y_guard() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_a: Node = root.get_node_or_null("EnemyFusionA")
	_assert_true(
		enemy_a != null,
		"T-35_enemy_fusion_a_exists",
		"EnemyFusionA node not found in scene — FUSE-ENC-1 AC-FUSE-ENC-1.1"
	)
	if enemy_a == null:
		root.free()
		return

	var scene_path: String = enemy_a.get_scene_file_path()
	_assert_true(
		scene_path.contains("enemy_infection_3d.tscn"),
		"T-35_enemy_fusion_a_scene_path",
		"EnemyFusionA.get_scene_file_path() = '" + scene_path + "', must contain 'enemy_infection_3d.tscn' — FUSE-ENC-1 AC-FUSE-ENC-1.3"
	)

	var plat_a: Node = root.get_node_or_null("FusionPlatformA")
	_assert_true(
		plat_a != null,
		"T-35_enemy_fusion_a_platform_ref_exists",
		"FusionPlatformA not found; cannot verify Y-above-platform guard — FUSE-ENC-1 AC-FUSE-ENC-1.7"
	)
	if plat_a != null:
		var enemy_y: float = (enemy_a as Node3D).position.y
		var platform_y: float = (plat_a as Node3D).position.y
		_assert_true(
			enemy_y > platform_y,
			"T-35_enemy_fusion_a_y_above_platform",
			"EnemyFusionA.position.y (" + str(enemy_y) + ") must be > FusionPlatformA.position.y (" + str(platform_y) + ") — FUSE-ENC-1 AC-FUSE-ENC-1.7"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-36: EnemyFusionB — scene file path contains "enemy_infection_3d.tscn";
#        position.y is above FusionPlatformB.position.y
# Spec: FUSE-ENC-1 (AC-FUSE-ENC-1.6, 1.8)
# NOTE: exact position (±0.1 m) is already covered by T-24.
# ---------------------------------------------------------------------------
func test_t36_enemy_fusion_b_scene_path_and_y_guard() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_b: Node = root.get_node_or_null("EnemyFusionB")
	_assert_true(
		enemy_b != null,
		"T-36_enemy_fusion_b_exists",
		"EnemyFusionB node not found in scene — FUSE-ENC-1 AC-FUSE-ENC-1.4"
	)
	if enemy_b == null:
		root.free()
		return

	var scene_path: String = enemy_b.get_scene_file_path()
	_assert_true(
		scene_path.contains("enemy_infection_3d.tscn"),
		"T-36_enemy_fusion_b_scene_path",
		"EnemyFusionB.get_scene_file_path() = '" + scene_path + "', must contain 'enemy_infection_3d.tscn' — FUSE-ENC-1 AC-FUSE-ENC-1.6"
	)

	var plat_b: Node = root.get_node_or_null("FusionPlatformB")
	_assert_true(
		plat_b != null,
		"T-36_enemy_fusion_b_platform_ref_exists",
		"FusionPlatformB not found; cannot verify Y-above-platform guard — FUSE-ENC-1 AC-FUSE-ENC-1.8"
	)
	if plat_b != null:
		var enemy_y: float = (enemy_b as Node3D).position.y
		var platform_y: float = (plat_b as Node3D).position.y
		_assert_true(
			enemy_y > platform_y,
			"T-36_enemy_fusion_b_y_above_platform",
			"EnemyFusionB.position.y (" + str(enemy_y) + ") must be > FusionPlatformB.position.y (" + str(platform_y) + ") — FUSE-ENC-1 AC-FUSE-ENC-1.8"
		)

	root.free()


# ---------------------------------------------------------------------------
# T-37: InfectionInteractionHandler has_method("get_mutation_slot_manager") guard
# Spec: FUSE-WIRE-1 (AC-FUSE-WIRE-1.2)
# NOTE: Node existence (T-9) and script path (T-16) are already covered in
# test_containment_hall_01.gd. This test adds only the method-presence guard.
# ---------------------------------------------------------------------------
func test_t37_infection_interaction_handler_has_method_guard() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var handler: Node = root.get_node_or_null("InfectionInteractionHandler")
	if handler == null:
		_fail_test(
			"T-37_handler_has_method_guard",
			"InfectionInteractionHandler node not found (already covered by T-9; re-reported here for FUSE-WIRE-1 traceability)"
		)
		root.free()
		return

	_assert_true(
		handler.has_method("get_mutation_slot_manager"),
		"T-37_handler_has_method_get_mutation_slot_manager",
		"InfectionInteractionHandler does not have method get_mutation_slot_manager() — FUSE-WIRE-1 AC-FUSE-WIRE-1.2"
	)

	root.free()


# ---------------------------------------------------------------------------
# T-38: InfectionInteractionHandler.get_mutation_slot_manager() returns non-null;
#        get_slot_count() == 2 (requires _ready() to run — scene added to tree)
# Spec: FUSE-WIRE-1 (AC-FUSE-WIRE-1.3, 1.4)
# NFR-4: root is removed from tree and freed before method returns.
# ---------------------------------------------------------------------------
func test_t38_slot_manager_non_null_and_slot_count_2() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var tree: SceneTree = _add_to_tree(root)
	if tree == null:
		_fail_test(
			"T-38_tree_available",
			"Engine.get_main_loop() did not return a SceneTree or tree.root is null — cannot add scene for _ready() propagation"
		)
		root.free()
		return

	var handler: Node = root.get_node_or_null("InfectionInteractionHandler")
	if handler == null:
		_fail_test(
			"T-38_handler_exists_in_tree",
			"InfectionInteractionHandler not found after adding scene to tree — FUSE-WIRE-1 AC-FUSE-WIRE-1.3"
		)
		_remove_from_tree(root, tree)
		root.free()
		return

	if not handler.has_method("get_mutation_slot_manager"):
		_fail_test(
			"T-38_handler_method_present",
			"InfectionInteractionHandler does not have get_mutation_slot_manager() — prerequisite for FUSE-WIRE-1 AC-FUSE-WIRE-1.3"
		)
		_remove_from_tree(root, tree)
		root.free()
		return

	# In Godot headless mode _ready() may not fire automatically from add_child alone.
	# Explicitly propagate _ready() on the handler to ensure _slot_manager is initialised.
	if handler.has_method("_ready"):
		handler._ready()

	var slot_manager: Object = handler.call("get_mutation_slot_manager")
	_assert_true(
		slot_manager != null,
		"T-38_slot_manager_non_null",
		"get_mutation_slot_manager() returned null — _ready() may not have run or _slot_manager not initialised — FUSE-WIRE-1 AC-FUSE-WIRE-1.3"
	)
	if slot_manager == null:
		_remove_from_tree(root, tree)
		root.free()
		return

	_assert_true(
		slot_manager.has_method("get_slot_count"),
		"T-38_slot_manager_has_get_slot_count",
		"MutationSlotManager returned by get_mutation_slot_manager() does not have get_slot_count() — FUSE-WIRE-1 AC-FUSE-WIRE-1.4"
	)
	if slot_manager.has_method("get_slot_count"):
		var count: int = slot_manager.call("get_slot_count")
		_assert_eq_int(2, count, "T-38_slot_manager_slot_count_is_2 — expected 2, got " + str(count) + " — FUSE-WIRE-1 AC-FUSE-WIRE-1.4")

	_remove_from_tree(root, tree)
	root.free()


# ---------------------------------------------------------------------------
# T-39: FusionResolver.can_fuse gate logic — FOR traceability
#        can_fuse(null) → false; both_empty → false; one_filled → false; both_filled → true
# Spec: FUSE-WIRE-2 (AC-FUSE-WIRE-2.1 through 2.4)
# Pure unit test — no scene load required. Uses FusionResolver and MutationSlotManager directly.
# NOTE: Comprehensive edge cases are already covered in tests/fusion/test_fusion_resolver.gd.
#       These assertions provide FOR spec traceability under distinct T-39_* names.
# ---------------------------------------------------------------------------
func test_t39_fusion_resolver_can_fuse_gate() -> void:
	var resolver_script: GDScript = load("res://scripts/fusion/fusion_resolver.gd") as GDScript
	if resolver_script == null:
		_fail_test(
			"T-39_resolver_script_exists",
			"fusion_resolver.gd not found at res://scripts/fusion/fusion_resolver.gd — FUSE-WIRE-2"
		)
		return

	var resolver: Object = resolver_script.new()
	if resolver == null:
		_fail_test("T-39_resolver_instantiates", "FusionResolver.new() returned null — FUSE-WIRE-2")
		return

	if not resolver.has_method("can_fuse"):
		_fail_test(
			"T-39_can_fuse_method_exists",
			"FusionResolver does not have can_fuse() — FUSE-WIRE-2 AC-FUSE-WIRE-2.1"
		)
		return

	# AC-FUSE-WIRE-2.1: can_fuse(null) returns false.
	_assert_false(
		resolver.call("can_fuse", null),
		"T-39_can_fuse_null_returns_false",
		"can_fuse(null) must return false — FUSE-WIRE-2 AC-FUSE-WIRE-2.1"
	)

	var manager_script: GDScript = load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript
	if manager_script == null:
		_fail_test(
			"T-39_manager_script_exists",
			"mutation_slot_manager.gd not found — cannot continue T-39 — FUSE-WIRE-2"
		)
		return

	# AC-FUSE-WIRE-2.2: can_fuse with fresh manager (both slots empty) returns false.
	var manager_empty: Object = manager_script.new()
	_assert_false(
		resolver.call("can_fuse", manager_empty),
		"T-39_can_fuse_both_empty_returns_false",
		"can_fuse(manager_with_0_filled) must return false — FUSE-WIRE-2 AC-FUSE-WIRE-2.2"
	)

	# AC-FUSE-WIRE-2.3: can_fuse with only one slot filled returns false.
	var manager_one: Object = manager_script.new()
	manager_one.fill_next_available("mutation_a")
	_assert_false(
		resolver.call("can_fuse", manager_one),
		"T-39_can_fuse_one_filled_returns_false",
		"can_fuse(manager_with_1_filled) must return false — FUSE-WIRE-2 AC-FUSE-WIRE-2.3"
	)

	# AC-FUSE-WIRE-2.4: can_fuse with both slots filled returns true.
	var manager_both: Object = manager_script.new()
	manager_both.fill_next_available("mutation_a")
	manager_both.fill_next_available("mutation_b")
	_assert_true(
		resolver.call("can_fuse", manager_both),
		"T-39_can_fuse_both_filled_returns_true",
		"can_fuse(manager_with_both_filled) must return true — FUSE-WIRE-2 AC-FUSE-WIRE-2.4"
	)
	# resolver and manager instances are RefCounted — auto-freed when they go out of scope.


# ---------------------------------------------------------------------------
# T-40: FusionResolver.resolve_fusion side effects — FOR traceability
#        0_filled → no side effects; both_filled + null player → slots cleared
# Spec: FUSE-WIRE-2 (AC-FUSE-WIRE-2.5 through 2.7)
# Pure unit test — no scene load required.
# NOTE: Comprehensive resolve_fusion tests are in tests/fusion/test_fusion_resolver.gd.
#       These assertions provide FOR spec traceability under distinct T-40_* names.
# ---------------------------------------------------------------------------
func test_t40_fusion_resolver_resolve_fusion_side_effects() -> void:
	var resolver_script: GDScript = load("res://scripts/fusion/fusion_resolver.gd") as GDScript
	if resolver_script == null:
		_fail_test(
			"T-40_resolver_script_exists",
			"fusion_resolver.gd not found — FUSE-WIRE-2"
		)
		return

	var resolver: Object = resolver_script.new()
	if resolver == null:
		_fail_test("T-40_resolver_instantiates", "FusionResolver.new() returned null — FUSE-WIRE-2")
		return

	if not resolver.has_method("resolve_fusion"):
		_fail_test(
			"T-40_resolve_fusion_method_exists",
			"FusionResolver does not have resolve_fusion() — FUSE-WIRE-2 AC-FUSE-WIRE-2.5"
		)
		return

	var manager_script: GDScript = load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript
	if manager_script == null:
		_fail_test(
			"T-40_manager_script_exists",
			"mutation_slot_manager.gd not found — cannot continue T-40 — FUSE-WIRE-2"
		)
		return

	# AC-FUSE-WIRE-2.5: resolve_fusion with 0 slots filled — slots remain unchanged (both still empty).
	var manager_zero: Object = manager_script.new()
	resolver.call("resolve_fusion", manager_zero, null)
	_assert_false(
		manager_zero.get_slot(0).is_filled(),
		"T-40_resolve_no_op_slot0_unchanged",
		"resolve_fusion with 0 slots filled must not change slot 0 — FUSE-WIRE-2 AC-FUSE-WIRE-2.5"
	)
	_assert_false(
		manager_zero.get_slot(1).is_filled(),
		"T-40_resolve_no_op_slot1_unchanged",
		"resolve_fusion with 0 slots filled must not change slot 1 — FUSE-WIRE-2 AC-FUSE-WIRE-2.5"
	)

	# AC-FUSE-WIRE-2.6 + 2.7: resolve_fusion with both slots filled and null player → both slots cleared; no crash.
	var manager_both: Object = manager_script.new()
	manager_both.fill_next_available("mutation_a")
	manager_both.fill_next_available("mutation_b")

	# Call with null player — must not raise a runtime error (null player is an explicitly supported path).
	resolver.call("resolve_fusion", manager_both, null)

	_assert_false(
		manager_both.get_slot(0).is_filled(),
		"T-40_resolve_both_filled_slot0_cleared",
		"resolve_fusion with both_filled + null player must clear slot 0 — FUSE-WIRE-2 AC-FUSE-WIRE-2.6"
	)
	_assert_false(
		manager_both.get_slot(1).is_filled(),
		"T-40_resolve_both_filled_slot1_cleared",
		"resolve_fusion with both_filled + null player must clear slot 1 — FUSE-WIRE-2 AC-FUSE-WIRE-2.6"
	)
	# AC-FUSE-WIRE-2.7: if we reached here without a crash, null player path is safe.
	_pass_test("T-40_resolve_null_player_no_crash — null player path completed without runtime error — FUSE-WIRE-2 AC-FUSE-WIRE-2.7")
	# resolver and manager instances are RefCounted — auto-freed when they go out of scope.


# ---------------------------------------------------------------------------
# T-41: GameUI scene contains required HUD nodes — all non-null
# Spec: FUSE-HUD-1 (AC-FUSE-HUD-1.1 through 1.7)
# Loads game_ui.tscn directly without scene tree insertion (existence check only).
# NOTE: test names use T-41_ prefix to avoid collision with test_player_hud_layout.gd
#       which uses T-6.4_, bonus_*, adv-* naming conventions.
# ---------------------------------------------------------------------------
func test_t41_game_ui_hud_nodes_exist() -> void:
	var ui: Node = _load_game_ui()
	if ui == null:
		return

	# AC-FUSE-HUD-1.1: GameUI root is a CanvasLayer named "GameUI".
	_assert_true(
		ui is CanvasLayer,
		"T-41_game_ui_root_is_canvas_layer",
		"game_ui.tscn root is " + ui.get_class() + ", expected CanvasLayer — FUSE-HUD-1 AC-FUSE-HUD-1.1"
	)
	_assert_true(
		ui.name == "GameUI",
		"T-41_game_ui_root_name_is_gameui",
		"game_ui.tscn root name is '" + str(ui.name) + "', expected 'GameUI' — FUSE-HUD-1 AC-FUSE-HUD-1.1"
	)

	# AC-FUSE-HUD-1.2 through 1.7: all six HUD nodes present.
	var required_nodes: Array[String] = [
		"FusePromptLabel",
		"FusionActiveLabel",
		"MutationSlot1Label",
		"MutationSlot2Label",
		"MutationIcon1",
		"MutationIcon2",
	]
	for node_name in required_nodes:
		var node: Node = ui.get_node_or_null(node_name)
		_assert_true(
			node != null,
			"T-41_" + node_name.to_lower() + "_exists",
			node_name + " not found in GameUI — FUSE-HUD-1"
		)

	ui.free()


# ---------------------------------------------------------------------------
# T-42: GameUI HUD nodes have non-zero size, are within 3200×1880 viewport,
#        and FusePromptLabel/FusionActiveLabel have visible == false by default
# Spec: FUSE-HUD-1 (AC-FUSE-HUD-1.8 through 1.11)
# Requires scene tree insertion so that offset_* and get_global_rect() are valid on Control nodes.
# NFR-4: ui is removed from tree and freed before method returns.
# ---------------------------------------------------------------------------
func test_t42_game_ui_hud_node_sizes_viewport_and_visibility() -> void:
	var ui: Node = _load_game_ui()
	if ui == null:
		return

	var tree: SceneTree = _add_to_tree(ui)
	if tree == null:
		_fail_test(
			"T-42_tree_available",
			"Engine.get_main_loop() did not return SceneTree — cannot add GameUI for offset checks"
		)
		ui.free()
		return

	# All six nodes to check for non-zero size and viewport bounds.
	var hud_nodes: Array[String] = [
		"FusePromptLabel",
		"FusionActiveLabel",
		"MutationSlot1Label",
		"MutationSlot2Label",
		"MutationIcon1",
		"MutationIcon2",
	]

	const GLOBAL_VP_TOL: float = 1.0

	for node_name in hud_nodes:
		var node: Control = ui.get_node_or_null(node_name) as Control
		if node == null:
			_fail_test(
				"T-42_" + node_name.to_lower() + "_found_for_size_check",
				node_name + " not found in GameUI — cannot check size — FUSE-HUD-1 AC-FUSE-HUD-1.8"
			)
			continue

		# AC-FUSE-HUD-1.8: non-zero design-space size (scene offset_* — HCSI-2 authoring space).
		var width: float = node.offset_right - node.offset_left
		var height: float = node.offset_bottom - node.offset_top
		_assert_true(
			width > 0.0,
			"T-42_" + node_name.to_lower() + "_width_nonzero",
			node_name + " width (offset_right - offset_left) = " + str(width) + ", must be > 0 — FUSE-HUD-1 AC-FUSE-HUD-1.8"
		)
		_assert_true(
			height > 0.0,
			"T-42_" + node_name.to_lower() + "_height_nonzero",
			node_name + " height (offset_bottom - offset_top) = " + str(height) + ", must be > 0 — FUSE-HUD-1 AC-FUSE-HUD-1.8"
		)

		# AC-FUSE-HUD-1.9 (+ HCSI-6): default-layout visibility in transformed global space (not raw offset caps).
		var gr: Rect2 = node.get_global_rect()
		_assert_true(
			gr.position.x >= -GLOBAL_VP_TOL,
			"T-42_" + node_name.to_lower() + "_global_left_ge_0",
			node_name + " global rect min x = " + str(gr.position.x) + " — FUSE-HUD-1 AC-FUSE-HUD-1.9 / HCSI-6"
		)
		_assert_true(
			gr.position.y >= -GLOBAL_VP_TOL,
			"T-42_" + node_name.to_lower() + "_global_top_ge_0",
			node_name + " global rect min y = " + str(gr.position.y) + " — FUSE-HUD-1 AC-FUSE-HUD-1.9 / HCSI-6"
		)
		_assert_true(
			gr.end.x <= 3200.0 + GLOBAL_VP_TOL,
			"T-42_" + node_name.to_lower() + "_global_right_le_3200",
			node_name + " global rect max x = " + str(gr.end.x) + " — FUSE-HUD-1 AC-FUSE-HUD-1.9 / HCSI-6"
		)
		_assert_true(
			gr.end.y <= 1880.0 + GLOBAL_VP_TOL,
			"T-42_" + node_name.to_lower() + "_global_bottom_le_1880",
			node_name + " global rect max y = " + str(gr.end.y) + " — FUSE-HUD-1 AC-FUSE-HUD-1.9 / HCSI-6"
		)

	# AC-FUSE-HUD-1.10: FusePromptLabel.visible == false by scene default.
	var fuse_prompt: Control = ui.get_node_or_null("FusePromptLabel") as Control
	if fuse_prompt != null:
		_assert_false(
			fuse_prompt.visible,
			"T-42_fuse_prompt_label_visible_false_default",
			"FusePromptLabel.visible must be false by scene default — FUSE-HUD-1 AC-FUSE-HUD-1.10"
		)

	# AC-FUSE-HUD-1.11: FusionActiveLabel.visible == false by scene default.
	var fusion_active: Control = ui.get_node_or_null("FusionActiveLabel") as Control
	if fusion_active != null:
		_assert_false(
			fusion_active.visible,
			"T-42_fusion_active_label_visible_false_default",
			"FusionActiveLabel.visible must be false by scene default — FUSE-HUD-1 AC-FUSE-HUD-1.11"
		)

	_remove_from_tree(ui, tree)
	ui.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_fusion_opportunity_room.gd ---")
	_pass_count = 0
	_fail_count = 0

	# T-31: FusionFloor geometry (FUSE-GEO-1)
	test_t31_fusion_floor_geometry()

	# T-32: FusionPlatformA geometry (FUSE-GEO-2)
	test_t32_fusion_platform_a_geometry()

	# T-33: FusionPlatformB geometry (FUSE-GEO-3)
	test_t33_fusion_platform_b_geometry()

	# T-34: Platform gap reachability (FUSE-GEO-4)
	test_t34_platform_gap_reachability()

	# T-35: EnemyFusionA scene path + Y-above-platform guard (FUSE-ENC-1)
	test_t35_enemy_fusion_a_scene_path_and_y_guard()

	# T-36: EnemyFusionB scene path + Y-above-platform guard (FUSE-ENC-1)
	test_t36_enemy_fusion_b_scene_path_and_y_guard()

	# T-37: InfectionInteractionHandler has_method guard (FUSE-WIRE-1)
	test_t37_infection_interaction_handler_has_method_guard()

	# T-38: Slot manager non-null + slot count == 2 (FUSE-WIRE-1, requires tree)
	test_t38_slot_manager_non_null_and_slot_count_2()

	# T-39: FusionResolver.can_fuse gate — FOR traceability (FUSE-WIRE-2, pure unit)
	test_t39_fusion_resolver_can_fuse_gate()

	# T-40: FusionResolver.resolve_fusion side effects — FOR traceability (FUSE-WIRE-2, pure unit)
	test_t40_fusion_resolver_resolve_fusion_side_effects()

	# T-41: GameUI HUD nodes present (FUSE-HUD-1)
	test_t41_game_ui_hud_nodes_exist()

	# T-42: GameUI HUD node sizes, viewport bounds, default visibility (FUSE-HUD-1)
	test_t42_game_ui_hud_node_sizes_viewport_and_visibility()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
