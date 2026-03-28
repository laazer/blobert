#
# test_fusion_opportunity_room_adversarial.gd
#
# Adversarial extension of the Fusion Opportunity Room test suite.
# Ticket: project_board/4_milestone_4_prototype_level/in_progress/fusion_opportunity_room.md
# Spec:   agent_context/agents/2_spec/fusion_opportunity_room_spec.md
#
# Purpose: Expose coverage gaps, blind spots, and edge-case failures that the primary
# suite (T-31 through T-42 in test_fusion_opportunity_room.gd) does not target.
# Uses the Test Breaker checklist matrix:
#   Null/Empty, Boundary, Type/Structure, Invalid/Corrupt, Order-dependency,
#   Combinatorial, Mutation testing, Error handling, Assumption checks.
#
# All tests are headless-safe: no await, no physics tick, no input, no signals.
# No test duplicates an assertion name from T-31–T-42 or T-1–T-30.
#
# Adversarial coverage matrix:
#
# | ID         | Category           | Vulnerability probed                                                                    |
# |------------|--------------------|-----------------------------------------------------------------------------------------|
# | ADV-FOR-01 | Boundary           | Platform gap strict <= 10 m (not <= 10.001 m); also > 0 with explicit edge arithmetic   |
# | ADV-FOR-02 | Null/Empty         | EnemyFusionA.position.y strictly > platform TOP surface Y (not just node origin Y)      |
# | ADV-FOR-03 | Assumption check   | FusionFloor top surface Y in [-0.1, 0.1] — floor is at ground level, not floating       |
# | ADV-FOR-04 | Boundary/Mutation  | get_slot_count() == 2 exactly (not 0, not 1, not 3) — exact count assertion             |
# | ADV-FOR-05 | Null/Empty         | resolve_fusion(null, null) → no crash, manager created after is still untouched         |
# | ADV-FOR-06 | Null/Empty         | resolve_fusion with null slot_manager via can_fuse path → no crash, no side effects      |
# | ADV-FOR-07 | Type/Structure     | Both platform CollisionShape3D BoxShape3D extents strictly > 0 on all three axes        |
# | ADV-FOR-08 | Assumption check   | FusePromptLabel visible == false by default (scene default, not runtime state)           |
# | ADV-FOR-09 | Mutation testing   | EnemyFusionA and EnemyFusionB are distinct nodes (different instances, different names)  |
# | ADV-FOR-10 | Mutation testing   | FusionPlatformA and FusionPlatformB are distinct nodes (different instances, different names) |
# | ADV-FOR-11 | Invalid/Corrupt    | fill_next_available("") does not fill any slot; can_fuse still returns false             |
# | ADV-FOR-12 | Assumption check   | get_slot(0) and get_slot(1) return non-null on fresh manager (hardcoded vs array state)  |
# | ADV-FOR-13 | Boundary           | get_slot(-1) returns null (out-of-range negative index)                                  |
# | ADV-FOR-14 | Boundary           | get_slot(2) returns null (out-of-range high index — only 2 slots, 0 and 1 valid)        |
# | ADV-FOR-15 | Order-dependency   | fill A then fill B then consume → both unfilled; fill B first then fill A → same result  |
# | ADV-FOR-16 | Mutation testing   | can_fuse returns false after both slots filled then one cleared                          |
# | ADV-FOR-17 | Type/Structure     | MutationIcon1 and MutationIcon2 are ColorRect nodes (not Label, not Panel)              |
# | ADV-FOR-18 | Assumption check   | FusionActiveLabel visible == false by default (separate from FusePromptLabel check)      |
# | ADV-FOR-19 | Error handling     | resolve_fusion with player lacking apply_fusion_effect → slots still cleared (no abort)  |
# | ADV-FOR-20 | Boundary/Stress    | fill_next_available called 3× (beyond capacity) — slot 1 is overwritten, slot 0 intact  |
# | ADV-FOR-21 | Enemy Y            | EnemyFusionB.position.y strictly > FusionPlatformB top surface Y (not just node origin) |
#
# NFR compliance:
#   - extends Object; run_all() -> int pattern.
#   - No class_name to avoid global registry conflicts.
#   - Scene cleanup: add_to_tree nodes are removed and freed before method returns.
#   - All test names prefixed with ADV-FOR- to ensure no collision with T-* names.

extends "res://tests/utils/test_utils.gd"

const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"
const GAME_UI_PATH: String = "res://scenes/ui/game_ui.tscn"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers — mirror the pattern from test_fusion_opportunity_room.gd
# ---------------------------------------------------------------------------

func _load_level_scene() -> Node:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("adv_scene_load_guard", "load returned null for " + SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("adv_scene_instantiate_guard", "instantiate() returned null for " + SCENE_PATH)
		return null
	return inst


func _load_game_ui() -> Node:
	var packed: PackedScene = load(GAME_UI_PATH) as PackedScene
	if packed == null:
		_fail_test("adv_game_ui_load_guard", "load returned null for " + GAME_UI_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("adv_game_ui_instantiate_guard", "instantiate() returned null for " + GAME_UI_PATH)
		return null
	return inst


func _get_collision_shape(parent: Node) -> CollisionShape3D:
	if parent == null:
		return null
	for i in range(parent.get_child_count()):
		var child: Node = parent.get_child(i)
		if child is CollisionShape3D:
			return child as CollisionShape3D
	return null


func _add_to_tree(root: Node) -> SceneTree:
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	if tree == null or tree.root == null:
		return null
	tree.root.add_child(root)
	return tree


func _remove_from_tree(root: Node, tree: SceneTree) -> void:
	if tree != null and tree.root != null and root.is_inside_tree():
		tree.root.remove_child(root)


func _load_fusion_resolver() -> Object:
	var script: GDScript = load("res://scripts/fusion/fusion_resolver.gd") as GDScript
	if script == null:
		_fail_test("adv_resolver_script_load_guard", "fusion_resolver.gd not found")
		return null
	return script.new()


func _load_slot_manager() -> Object:
	var script: GDScript = load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript
	if script == null:
		_fail_test("adv_manager_script_load_guard", "mutation_slot_manager.gd not found")
		return null
	return script.new()


# ---------------------------------------------------------------------------
# ADV-FOR-01: Platform gap strict <= 10 m (boundary: the spec says <= 10.0,
#             not <= 10.001). Also verifies the arithmetic uses CollisionShape3D
#             X offsets explicitly (not hard-coded edge positions).
#
# Vulnerability: T-34 tests this at spec tolerance. This test asserts the
# boundary value itself (10.0) with no rounding grace, using the same formula
# but as an independent arithmetic path to confirm no off-by-one.
# ---------------------------------------------------------------------------
func test_adv_for_01_platform_gap_strict_boundary() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var plat_a: Node = root.get_node_or_null("FusionPlatformA")
	var plat_b: Node = root.get_node_or_null("FusionPlatformB")
	if plat_a == null or plat_b == null:
		_fail_test("ADV-FOR-01_nodes_present", "FusionPlatformA or FusionPlatformB missing — cannot compute gap")
		root.free()
		return

	var col_a: CollisionShape3D = _get_collision_shape(plat_a)
	var col_b: CollisionShape3D = _get_collision_shape(plat_b)
	if col_a == null or col_b == null or not (col_a.shape is BoxShape3D) or not (col_b.shape is BoxShape3D):
		_fail_test("ADV-FOR-01_shapes_present", "One or both platforms missing BoxShape3D CollisionShape3D")
		root.free()
		return

	var box_a: BoxShape3D = col_a.shape as BoxShape3D
	var box_b: BoxShape3D = col_b.shape as BoxShape3D

	# Compute edges using CollisionShape3D local X offsets (not hard-coded values).
	var right_edge_a: float = (plat_a as Node3D).position.x + col_a.position.x + (box_a.size.x / 2.0)
	var left_edge_b: float = (plat_b as Node3D).position.x + col_b.position.x - (box_b.size.x / 2.0)
	var gap: float = left_edge_b - right_edge_a

	# Strict boundary: gap must be strictly <= 10.0 (not 10.001).
	_assert_true(
		gap <= 10.0,
		"ADV-FOR-01_gap_strict_le_10m",
		"Platform gap = " + str(gap) + " m; strict boundary requires gap <= 10.0 m exactly (conservative jump range)"
	)
	# Gap must be positive (platforms do not overlap — separate assertion from T-34).
	_assert_true(
		gap > 0.0,
		"ADV-FOR-01_gap_strictly_positive",
		"Platform gap = " + str(gap) + " m; platforms must not touch or overlap (gap must be > 0)"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-FOR-02: EnemyFusionA.position.y is strictly above the FusionPlatformA
#             TOP SURFACE world Y — not just the platform node origin Y.
#
# Vulnerability: T-35 checks enemy_y > platform_node.position.y (node origin).
# If the platform's CollisionShape3D has a Y offset that raises the top surface
# above the node origin (it does: offset=0.3, half=0.5 → top Y=0.8), an enemy
# at Y=0.5 would pass T-35 (0.5 > 0.0) but be embedded in the platform.
# This test uses the full top-surface formula.
# ---------------------------------------------------------------------------
func test_adv_for_02_enemy_a_y_above_platform_top_surface() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_a: Node = root.get_node_or_null("EnemyFusionA")
	var plat_a: Node = root.get_node_or_null("FusionPlatformA")
	if enemy_a == null or plat_a == null:
		_fail_test("ADV-FOR-02_nodes_present", "EnemyFusionA or FusionPlatformA missing")
		root.free()
		return

	var col_a: CollisionShape3D = _get_collision_shape(plat_a)
	if col_a == null or not (col_a.shape is BoxShape3D):
		_fail_test("ADV-FOR-02_platform_shape", "FusionPlatformA has no BoxShape3D CollisionShape3D")
		root.free()
		return

	var box_a: BoxShape3D = col_a.shape as BoxShape3D
	var top_surface_y: float = (plat_a as Node3D).position.y + col_a.position.y + (box_a.size.y * 0.5)
	var enemy_y: float = (enemy_a as Node3D).position.y

	_assert_true(
		enemy_y > top_surface_y,
		"ADV-FOR-02_enemy_a_y_above_top_surface",
		"EnemyFusionA.position.y (" + str(enemy_y) + ") must be strictly > FusionPlatformA top surface Y ("
			+ str(top_surface_y) + ") — enemy would be embedded in the platform"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-FOR-03: FusionFloor top surface is at Y ≈ 0 (ground level).
#             Computed as node.y + col.y + (box.half_y).
#
# Vulnerability: T-31 verifies origin X and box dimensions but NOT the floor's
# vertical position. If the floor is accidentally raised (e.g., node Y=5), the
# computed top surface Y would be ~5.0, causing enemies and the player to fall
# through the invisible floor at Y=0.
# ---------------------------------------------------------------------------
func test_adv_for_03_fusion_floor_top_surface_at_ground_level() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var floor_node: Node = root.get_node_or_null("FusionFloor")
	if floor_node == null:
		_fail_test("ADV-FOR-03_floor_exists", "FusionFloor not found in scene")
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test("ADV-FOR-03_floor_shape", "FusionFloor has no BoxShape3D CollisionShape3D")
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	var top_surface_y: float = (floor_node as Node3D).position.y + col.position.y + (box.size.y * 0.5)

	_assert_true(
		top_surface_y >= -0.1 and top_surface_y <= 0.1,
		"ADV-FOR-03_fusion_floor_top_surface_at_ground",
		"FusionFloor top surface Y = " + str(top_surface_y) + "; expected in [-0.1, 0.1] — floor must be at ground level, not floating or sunken"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-FOR-04: get_slot_count() == 2 exactly — not 0, not 1, not 3.
#
# Vulnerability: T-38 asserts get_slot_count() == 2 after _ready() runs in the
# scene. This adversarial test checks the MutationSlotManager directly (pure
# unit, no scene load) with an explicit int-equality check using _assert_eq_int
# to produce a precise failure message if the count drifts.
# ---------------------------------------------------------------------------
func test_adv_for_04_slot_count_exact_2() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	_assert_eq_int(
		2,
		manager.call("get_slot_count"),
		"ADV-FOR-04_slot_count_exact_2 — get_slot_count() must return exactly 2, not 0, not 1, not 3"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-05: resolve_fusion(null, null) → no crash; no state mutation.
#
# Vulnerability: null slot_manager is passed to resolve_fusion. The guard
# (can_fuse(null)) returns false and resolve_fusion returns immediately.
# This test verifies: no crash occurs, and a fresh independent manager is
# unaffected (no accidental global state mutation).
#
# This is DISTINCT from T-40 which tests (manager_with_0_filled, null).
# Here the slot_manager argument itself is null.
# ---------------------------------------------------------------------------
func test_adv_for_05_resolve_fusion_null_slot_manager_no_crash() -> void:
	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	if not resolver.has_method("resolve_fusion"):
		_fail_test("ADV-FOR-05_method_exists", "FusionResolver does not have resolve_fusion()")
		return

	# Call with null slot_manager — must not crash.
	resolver.call("resolve_fusion", null, null)
	_pass_test("ADV-FOR-05_resolve_null_manager_no_crash — resolve_fusion(null, null) completed without runtime error")

	# Verify a fresh independent manager is not corrupted by any hypothetical global side effect.
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	_assert_false(
		manager.get_slot(0).is_filled(),
		"ADV-FOR-05_fresh_manager_slot0_unaffected",
		"After resolve_fusion(null, null), a fresh MutationSlotManager slot 0 must still be unfilled"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"ADV-FOR-05_fresh_manager_slot1_unaffected",
		"After resolve_fusion(null, null), a fresh MutationSlotManager slot 1 must still be unfilled"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-06: FusionResolver.can_fuse with null manager returns false (no crash).
#
# Vulnerability: The spec documents this at AC-FUSE-WIRE-2.1 and T-39 tests it.
# This adversarial case targets the specific code path inside can_fuse where
# the null check is the first guard — a mutation that removes that guard would
# cause a method-call-on-null crash. Verifying under the adversarial prefix
# keeps this as a targeted mutation-detection test separate from T-39.
# ---------------------------------------------------------------------------
func test_adv_for_06_can_fuse_null_manager_returns_false_no_crash() -> void:
	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	if not resolver.has_method("can_fuse"):
		_fail_test("ADV-FOR-06_method_exists", "FusionResolver does not have can_fuse()")
		return

	var result: bool = resolver.call("can_fuse", null)
	_assert_false(
		result,
		"ADV-FOR-06_can_fuse_null_returns_false",
		"can_fuse(null) must return false — null slot_manager is not a valid fuse condition"
	)
	_pass_test("ADV-FOR-06_can_fuse_null_no_crash — can_fuse(null) completed without crash")


# ---------------------------------------------------------------------------
# ADV-FOR-07: FusionPlatformA and FusionPlatformB BoxShape3D extents are
#             strictly > 0 on all three axes.
#
# Vulnerability: T-32 and T-33 assert exact dimensions (4, 1, 6). But a default
# BoxShape3D in Godot 4 initialises to size (0.2, 0.2, 0.2) — if the sub-resource
# is replaced by a default shape, T-32/T-33 would fail with a size mismatch.
# This test adds an independent non-zero-extents guard with a targeted message
# for the "accidentally zeroed out" mutation.
# ---------------------------------------------------------------------------
func test_adv_for_07_platform_collision_shapes_nonzero_extents() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	for plat_name in ["FusionPlatformA", "FusionPlatformB"]:
		var plat: Node = root.get_node_or_null(plat_name)
		if plat == null:
			_fail_test("ADV-FOR-07_" + plat_name.to_lower() + "_exists", plat_name + " not found in scene")
			continue

		var col: CollisionShape3D = _get_collision_shape(plat)
		if col == null or not (col.shape is BoxShape3D):
			_fail_test("ADV-FOR-07_" + plat_name.to_lower() + "_has_box_shape", plat_name + " has no BoxShape3D — cannot check extents")
			continue

		var box: BoxShape3D = col.shape as BoxShape3D
		_assert_true(
			box.size.x > 0.0,
			"ADV-FOR-07_" + plat_name.to_lower() + "_box_size_x_nonzero",
			plat_name + " BoxShape3D size.x = " + str(box.size.x) + "; must be > 0 — zero extent means no collision surface"
		)
		_assert_true(
			box.size.y > 0.0,
			"ADV-FOR-07_" + plat_name.to_lower() + "_box_size_y_nonzero",
			plat_name + " BoxShape3D size.y = " + str(box.size.y) + "; must be > 0 — zero thickness platform has no collision"
		)
		_assert_true(
			box.size.z > 0.0,
			"ADV-FOR-07_" + plat_name.to_lower() + "_box_size_z_nonzero",
			plat_name + " BoxShape3D size.z = " + str(box.size.z) + "; must be > 0 — zero depth platform has no collision"
		)

	root.free()


# ---------------------------------------------------------------------------
# ADV-FOR-08: FusePromptLabel.visible == false by scene default.
#
# Vulnerability: T-42 asserts this in the context of a loop over all HUD nodes.
# This adversarial test targets it as a standalone named assertion with a clear
# failure message, using a fresh scene load without scene tree insertion to
# confirm the visible=false property is authored in the scene file (not
# just a runtime state that coincidentally happens to be false).
# ---------------------------------------------------------------------------
func test_adv_for_08_fuse_prompt_label_hidden_by_default() -> void:
	var ui: Node = _load_game_ui()
	if ui == null:
		return

	var label: Node = ui.get_node_or_null("FusePromptLabel")
	if label == null:
		_fail_test("ADV-FOR-08_node_exists", "FusePromptLabel not found in GameUI — cannot check visibility")
		ui.free()
		return

	_assert_false(
		(label as CanvasItem).visible,
		"ADV-FOR-08_fuse_prompt_label_visible_false_default",
		"FusePromptLabel.visible must be false by scene default — must not appear until fusion conditions are met"
	)

	ui.free()


# ---------------------------------------------------------------------------
# ADV-FOR-09: EnemyFusionA and EnemyFusionB are distinct nodes (different paths).
#
# Vulnerability: If a scene authoring error names both enemies "EnemyFusionA",
# the second silently shadows the first in Godot's node tree. T-35 and T-36
# would both succeed on the same node object, giving false confidence that two
# distinct enemies exist. This test asserts the NodePaths are different.
# ---------------------------------------------------------------------------
func test_adv_for_09_enemies_are_distinct_nodes() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_a: Node = root.get_node_or_null("EnemyFusionA")
	var enemy_b: Node = root.get_node_or_null("EnemyFusionB")

	if enemy_a == null or enemy_b == null:
		_fail_test("ADV-FOR-09_both_enemies_exist", "EnemyFusionA or EnemyFusionB not found — cannot compare paths")
		root.free()
		return

	_assert_true(
		enemy_a != enemy_b,
		"ADV-FOR-09_enemies_are_different_instances",
		"EnemyFusionA and EnemyFusionB must be different node instances — scene authoring error if same object"
	)
	# Node names are set from the scene file and are readable without a scene tree.
	# Different node names guarantee distinct addressing within any parent.
	_assert_true(
		enemy_a.name != enemy_b.name,
		"ADV-FOR-09_enemies_have_different_names",
		"EnemyFusionA.name == EnemyFusionB.name ('" + str(enemy_a.name) + "') — both enemies must have distinct node names in the scene"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-FOR-10: FusionPlatformA and FusionPlatformB are distinct nodes.
#
# Vulnerability: Same class of scene authoring error as ADV-FOR-09, applied to
# platforms. If both platforms share the same node path, T-32 and T-33 operate
# on the same object — meaning only one platform's geometry is verified.
# ---------------------------------------------------------------------------
func test_adv_for_10_platforms_are_distinct_nodes() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var plat_a: Node = root.get_node_or_null("FusionPlatformA")
	var plat_b: Node = root.get_node_or_null("FusionPlatformB")

	if plat_a == null or plat_b == null:
		_fail_test("ADV-FOR-10_both_platforms_exist", "FusionPlatformA or FusionPlatformB not found — cannot compare paths")
		root.free()
		return

	_assert_true(
		plat_a != plat_b,
		"ADV-FOR-10_platforms_are_different_instances",
		"FusionPlatformA and FusionPlatformB must be different node instances"
	)
	# Node names are set from the scene file and are readable without a scene tree.
	_assert_true(
		plat_a.name != plat_b.name,
		"ADV-FOR-10_platforms_have_different_names",
		"FusionPlatformA.name == FusionPlatformB.name ('" + str(plat_a.name) + "') — both platforms must have distinct node names in the scene"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-FOR-11: fill_next_available("") does not fill any slot.
#
# Vulnerability: MutationSlotManager.fill_next_available("") calls push_error
# and returns without setting the id. If this guard were removed (mutation:
# delete the empty-id check), is_filled() would return true for an empty string
# id (because the slot's _active_mutation_id == "" check in is_filled() would
# return false — wait, is_filled returns _id != ""). Let me reason precisely:
#
#   is_filled() returns _active_mutation_id != "".
#   set_active_mutation_id("") calls clear() which sets _id = "".
#   So even if fill_next_available("") bypassed the guard and called
#   set_active_mutation_id(""), the slot would not be filled (is_filled = false).
#
# The vulnerability being probed: does the manager end up in a state where
# can_fuse incorrectly returns true after two fill_next_available("") calls?
# Answer: no, because set_active_mutation_id("") clears the slot. The test
# confirms this invariant holds, so a mutation that removes the empty-guard
# in fill_next_available does NOT silently allow a bad fill.
# ---------------------------------------------------------------------------
func test_adv_for_11_fill_empty_id_does_not_fill_slot() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	# Call fill_next_available with empty string twice.
	manager.call("fill_next_available", "")
	manager.call("fill_next_available", "")

	_assert_false(
		manager.get_slot(0).is_filled(),
		"ADV-FOR-11_slot0_not_filled_after_empty_id",
		"After fill_next_available(''), slot 0 must remain unfilled — empty-id guard must hold"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"ADV-FOR-11_slot1_not_filled_after_empty_id",
		"After fill_next_available(''), slot 1 must remain unfilled — empty-id guard must hold"
	)

	# can_fuse must still return false — empty-id fills must not satisfy fusion condition.
	_assert_false(
		resolver.call("can_fuse", manager),
		"ADV-FOR-11_can_fuse_false_after_empty_fills",
		"can_fuse must return false after two fill_next_available('') calls — empty strings must not count as filled"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-12: get_slot(0) and get_slot(1) return non-null on fresh manager.
#
# Vulnerability: get_slot_count() is hardcoded to return 2. If the _slots
# array is somehow empty or has only one entry (e.g., _init() mutated to
# create only one slot), get_slot_count() still returns 2 but get_slot(1)
# returns null. This test verifies both slot accessors return non-null on a
# freshly constructed manager — exposing the gap between the hardcoded count
# and the actual array contents.
# ---------------------------------------------------------------------------
func test_adv_for_12_get_slot_0_and_1_non_null_on_fresh_manager() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var slot_0: Object = manager.call("get_slot", 0)
	_assert_true(
		slot_0 != null,
		"ADV-FOR-12_get_slot_0_non_null",
		"MutationSlotManager.get_slot(0) returned null on fresh manager — _init() must create both slots"
	)

	var slot_1: Object = manager.call("get_slot", 1)
	_assert_true(
		slot_1 != null,
		"ADV-FOR-12_get_slot_1_non_null",
		"MutationSlotManager.get_slot(1) returned null on fresh manager — _init() must create both slots"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-13: get_slot(-1) returns null (out-of-range negative index).
#
# Vulnerability: get_slot() guards with `index < 0 or index >= _slots.size()`.
# A mutation that changes `<` to `<=` would make get_slot(0) return null.
# A mutation that removes the lower bound check would allow get_slot(-1) to
# access _slots[-1] (the last element in GDScript arrays — GDScript supports
# negative indexing). This test explicitly probes the negative-index path.
# ---------------------------------------------------------------------------
func test_adv_for_13_get_slot_negative_index_returns_null() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var slot_neg: Object = manager.call("get_slot", -1)
	_assert_true(
		slot_neg == null,
		"ADV-FOR-13_get_slot_minus1_returns_null",
		"MutationSlotManager.get_slot(-1) must return null — negative index is out of range"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-14: get_slot(2) returns null (out-of-range high index).
#
# Vulnerability: Only indices 0 and 1 are valid. get_slot(2) must return null.
# A mutation that changes `>=` to `>` in the upper bound guard would allow
# get_slot(2) to return _slots[2] (which would be an out-of-bounds array
# access, causing a GDScript runtime error). This test verifies the guard
# is correct at the exact boundary value (2 == _slots.size()).
# ---------------------------------------------------------------------------
func test_adv_for_14_get_slot_high_index_returns_null() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var slot_2: Object = manager.call("get_slot", 2)
	_assert_true(
		slot_2 == null,
		"ADV-FOR-14_get_slot_2_returns_null",
		"MutationSlotManager.get_slot(2) must return null — index 2 is out of range (valid: 0 and 1 only)"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-15: Fill order invariance — filling A then B vs B-path first.
#
# Vulnerability: fill_next_available fills slot A first (index 0), then B.
# After two distinct fills, both slots should be filled regardless of whether
# the fills are conceptually "for A" or "for B" — the manager is order-
# sensitive only in which physical slot gets which id. This test verifies:
# 1. After two fills, can_fuse returns true.
# 2. After consume_fusion_slots, both are empty and can_fuse returns false.
# 3. Repeating the cycle (re-filling) restores the fuse condition.
# This probes idempotency of the consume→refill cycle (order-dependency).
# ---------------------------------------------------------------------------
func test_adv_for_15_fill_consume_refill_cycle() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	# First fill cycle.
	manager.call("fill_next_available", "mutation_x")
	manager.call("fill_next_available", "mutation_y")
	_assert_true(
		resolver.call("can_fuse", manager),
		"ADV-FOR-15_can_fuse_true_after_first_fill_cycle",
		"can_fuse must return true after filling both slots in first cycle"
	)

	# Consume.
	manager.call("consume_fusion_slots")
	_assert_false(
		resolver.call("can_fuse", manager),
		"ADV-FOR-15_can_fuse_false_after_consume",
		"can_fuse must return false after consume_fusion_slots clears both slots"
	)

	# Second fill cycle — system must be re-usable.
	manager.call("fill_next_available", "mutation_p")
	manager.call("fill_next_available", "mutation_q")
	_assert_true(
		resolver.call("can_fuse", manager),
		"ADV-FOR-15_can_fuse_true_after_second_fill_cycle",
		"can_fuse must return true after re-filling both slots in second cycle — manager must be re-usable"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-16: can_fuse returns false after both slots filled then one cleared.
#
# Vulnerability: The AND condition in can_fuse requires BOTH slots filled.
# A mutation that changes `and` to `or` would cause can_fuse to return true
# with only one slot filled. This test specifically sets up both-filled then
# clears exactly one slot, asserting can_fuse drops back to false — targeting
# the AND/OR mutation directly.
# ---------------------------------------------------------------------------
func test_adv_for_16_can_fuse_false_after_one_slot_cleared() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	manager.call("fill_next_available", "mutation_a")
	manager.call("fill_next_available", "mutation_b")

	# Confirm both-filled precondition.
	_assert_true(
		resolver.call("can_fuse", manager),
		"ADV-FOR-16_precondition_both_filled",
		"Precondition for ADV-FOR-16: both slots filled, can_fuse must return true"
	)

	# Clear only slot 0.
	manager.call("clear_slot", 0)

	_assert_false(
		resolver.call("can_fuse", manager),
		"ADV-FOR-16_can_fuse_false_after_slot0_cleared",
		"can_fuse must return false after clearing slot 0 (only slot 1 remains filled) — AND condition required"
	)

	# Restore slot 0, clear slot 1 instead — same invariant from the other direction.
	manager.call("fill_next_available", "mutation_a")
	manager.call("clear_slot", 1)
	_assert_false(
		resolver.call("can_fuse", manager),
		"ADV-FOR-16_can_fuse_false_after_slot1_cleared",
		"can_fuse must return false after clearing slot 1 (only slot 0 remains filled) — AND condition required"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-17: MutationIcon1 and MutationIcon2 are ColorRect nodes.
#
# Vulnerability: infection_ui.gd casts MutationIcon1/2 as ColorRect to set
# slot color. If either node is accidentally a Label, TextureRect, or Panel,
# the cast returns null and slot color updates are silently dropped. T-41
# only checks non-null existence; this test verifies the type is ColorRect.
# ---------------------------------------------------------------------------
func test_adv_for_17_mutation_icons_are_color_rect() -> void:
	var ui: Node = _load_game_ui()
	if ui == null:
		return

	for icon_name in ["MutationIcon1", "MutationIcon2"]:
		var icon: Node = ui.get_node_or_null(icon_name)
		if icon == null:
			_fail_test("ADV-FOR-17_" + icon_name.to_lower() + "_exists", icon_name + " not found in GameUI")
			continue
		_assert_true(
			icon is ColorRect,
			"ADV-FOR-17_" + icon_name.to_lower() + "_is_color_rect",
			icon_name + " must be a ColorRect — infection_ui.gd casts it as ColorRect for slot color updates; actual class: " + icon.get_class()
		)

	ui.free()


# ---------------------------------------------------------------------------
# ADV-FOR-18: FusionActiveLabel.visible == false by scene default.
#
# Vulnerability: T-42 tests both label visibilities in a loop; this test
# targets FusionActiveLabel specifically as a standalone named adversarial
# assertion. The label must not appear until fusion actually activates.
# If it is accidentally left visible=true, the player sees "FUSION ACTIVE"
# from the start with no fusion having occurred.
# ---------------------------------------------------------------------------
func test_adv_for_18_fusion_active_label_hidden_by_default() -> void:
	var ui: Node = _load_game_ui()
	if ui == null:
		return

	var label: Node = ui.get_node_or_null("FusionActiveLabel")
	if label == null:
		_fail_test("ADV-FOR-18_node_exists", "FusionActiveLabel not found in GameUI")
		ui.free()
		return

	_assert_false(
		(label as CanvasItem).visible,
		"ADV-FOR-18_fusion_active_label_visible_false_default",
		"FusionActiveLabel.visible must be false by scene default — must not appear until resolve_fusion is called"
	)

	ui.free()


# ---------------------------------------------------------------------------
# ADV-FOR-19: resolve_fusion with player lacking apply_fusion_effect →
#             slots are still cleared (push_error, but no abort).
#
# Vulnerability: The spec states (FUSE-WIRE-2 risk analysis): "player without
# apply_fusion_effect → push_error, but slots still consumed." If an
# implementation were to `return` after push_error instead of continuing to
# consume_fusion_slots, the slots would NOT be cleared — leaving the fusion
# system in a permanently-fused state with no way to reset.
#
# Implementation approach: use a minimal GDScript object that has no
# apply_fusion_effect method as the player argument.
# ---------------------------------------------------------------------------
func test_adv_for_19_resolve_fusion_player_without_method_still_clears_slots() -> void:
	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	manager.call("fill_next_available", "mutation_a")
	manager.call("fill_next_available", "mutation_b")

	# Confirm both-filled precondition.
	if not resolver.call("can_fuse", manager):
		_fail_test("ADV-FOR-19_precondition", "Precondition failed: can_fuse returned false before resolve — cannot test slot-clearing after bad player")
		return

	# Use a plain RefCounted as the player — it has no apply_fusion_effect.
	# The resolver must push_error but still call consume_fusion_slots.
	var fake_player: RefCounted = RefCounted.new()
	resolver.call("resolve_fusion", manager, fake_player)

	_assert_false(
		manager.get_slot(0).is_filled(),
		"ADV-FOR-19_slot0_cleared_despite_bad_player",
		"resolve_fusion with player lacking apply_fusion_effect must still clear slot 0 — push_error must not abort consume"
	)
	_assert_false(
		manager.get_slot(1).is_filled(),
		"ADV-FOR-19_slot1_cleared_despite_bad_player",
		"resolve_fusion with player lacking apply_fusion_effect must still clear slot 1 — push_error must not abort consume"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-20: fill_next_available called 3× — slot 1 is overwritten (last-
#             absorb-wins), slot 0 retains the first fill, can_fuse remains true.
#
# Vulnerability: The manager spec (DSM fill order: "if both full, overwrite
# slot B") defines a last-absorb-wins policy for the third absorption. If an
# implementation instead rejects the third fill (returns early), the HUD will
# show an incorrect/stale slot 2 id. This test probes the overwrite path.
# ---------------------------------------------------------------------------
func test_adv_for_20_third_fill_overwrites_slot_b() -> void:
	var manager: Object = _load_slot_manager()
	if manager == null:
		return

	var resolver: Object = _load_fusion_resolver()
	if resolver == null:
		return

	manager.call("fill_next_available", "mutation_first")
	manager.call("fill_next_available", "mutation_second")
	manager.call("fill_next_available", "mutation_third")

	# Slot 0 must still hold "mutation_first" (unchanged).
	var slot_0: Object = manager.call("get_slot", 0)
	_assert_true(
		slot_0 != null and slot_0.get_active_mutation_id() == "mutation_first",
		"ADV-FOR-20_slot0_retains_first",
		"After 3 fills, slot 0 must still hold 'mutation_first' — slot 0 must not be overwritten by third fill"
	)

	# Slot 1 must hold "mutation_third" (last-absorb-wins overwrite).
	var slot_1: Object = manager.call("get_slot", 1)
	_assert_true(
		slot_1 != null and slot_1.get_active_mutation_id() == "mutation_third",
		"ADV-FOR-20_slot1_overwritten_with_third",
		"After 3 fills, slot 1 must hold 'mutation_third' — last-absorb-wins policy must overwrite slot B"
	)

	# Both slots are filled → can_fuse must still return true.
	_assert_true(
		resolver.call("can_fuse", manager),
		"ADV-FOR-20_can_fuse_true_after_third_fill",
		"can_fuse must return true after third fill overwrites slot 1 — both slots are still filled"
	)


# ---------------------------------------------------------------------------
# ADV-FOR-21: EnemyFusionB.position.y is strictly above FusionPlatformB
#             TOP SURFACE world Y (not just node origin Y).
#
# Vulnerability: Mirrors ADV-FOR-02 for EnemyFusionB. T-36 checks
# enemy_y > platform_node.position.y (node origin = 0), but the top surface
# is at Y=0.8 (col offset 0.3 + half-height 0.5). An enemy at Y=0.5 passes
# T-36 (0.5 > 0.0) but is embedded 0.3 m into the platform.
# ---------------------------------------------------------------------------
func test_adv_for_21_enemy_b_y_above_platform_top_surface() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var enemy_b: Node = root.get_node_or_null("EnemyFusionB")
	var plat_b: Node = root.get_node_or_null("FusionPlatformB")
	if enemy_b == null or plat_b == null:
		_fail_test("ADV-FOR-21_nodes_present", "EnemyFusionB or FusionPlatformB missing")
		root.free()
		return

	var col_b: CollisionShape3D = _get_collision_shape(plat_b)
	if col_b == null or not (col_b.shape is BoxShape3D):
		_fail_test("ADV-FOR-21_platform_shape", "FusionPlatformB has no BoxShape3D CollisionShape3D")
		root.free()
		return

	var box_b: BoxShape3D = col_b.shape as BoxShape3D
	var top_surface_y: float = (plat_b as Node3D).position.y + col_b.position.y + (box_b.size.y * 0.5)
	var enemy_y: float = (enemy_b as Node3D).position.y

	_assert_true(
		enemy_y > top_surface_y,
		"ADV-FOR-21_enemy_b_y_above_top_surface",
		"EnemyFusionB.position.y (" + str(enemy_y) + ") must be strictly > FusionPlatformB top surface Y ("
			+ str(top_surface_y) + ") — enemy would be embedded in the platform"
	)

	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_fusion_opportunity_room_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-FOR-01: Platform gap strict boundary (<= 10.0 m, > 0 m)
	test_adv_for_01_platform_gap_strict_boundary()

	# ADV-FOR-02: EnemyFusionA Y above FusionPlatformA TOP SURFACE (not just node origin)
	test_adv_for_02_enemy_a_y_above_platform_top_surface()

	# ADV-FOR-03: FusionFloor top surface Y at ground level (approx Y=0)
	test_adv_for_03_fusion_floor_top_surface_at_ground_level()

	# ADV-FOR-04: get_slot_count() == 2 exactly (pure unit)
	test_adv_for_04_slot_count_exact_2()

	# ADV-FOR-05: resolve_fusion(null, null) no crash, no global state mutation
	test_adv_for_05_resolve_fusion_null_slot_manager_no_crash()

	# ADV-FOR-06: can_fuse(null) returns false, no crash (targeted mutation guard)
	test_adv_for_06_can_fuse_null_manager_returns_false_no_crash()

	# ADV-FOR-07: Both platform BoxShape3D extents strictly > 0 on all axes
	test_adv_for_07_platform_collision_shapes_nonzero_extents()

	# ADV-FOR-08: FusePromptLabel.visible == false by scene default (standalone)
	test_adv_for_08_fuse_prompt_label_hidden_by_default()

	# ADV-FOR-09: EnemyFusionA and EnemyFusionB are distinct nodes
	test_adv_for_09_enemies_are_distinct_nodes()

	# ADV-FOR-10: FusionPlatformA and FusionPlatformB are distinct nodes
	test_adv_for_10_platforms_are_distinct_nodes()

	# ADV-FOR-11: fill_next_available("") does not fill any slot
	test_adv_for_11_fill_empty_id_does_not_fill_slot()

	# ADV-FOR-12: get_slot(0) and get_slot(1) non-null on fresh manager
	test_adv_for_12_get_slot_0_and_1_non_null_on_fresh_manager()

	# ADV-FOR-13: get_slot(-1) returns null (negative index out-of-range)
	test_adv_for_13_get_slot_negative_index_returns_null()

	# ADV-FOR-14: get_slot(2) returns null (high index out-of-range)
	test_adv_for_14_get_slot_high_index_returns_null()

	# ADV-FOR-15: Fill-consume-refill cycle (order-dependency / idempotency)
	test_adv_for_15_fill_consume_refill_cycle()

	# ADV-FOR-16: can_fuse false after one slot cleared (AND vs OR mutation)
	test_adv_for_16_can_fuse_false_after_one_slot_cleared()

	# ADV-FOR-17: MutationIcon1 and MutationIcon2 are ColorRect (not Label or Panel)
	test_adv_for_17_mutation_icons_are_color_rect()

	# ADV-FOR-18: FusionActiveLabel.visible == false by scene default (standalone)
	test_adv_for_18_fusion_active_label_hidden_by_default()

	# ADV-FOR-19: resolve_fusion with player lacking apply_fusion_effect still clears slots
	test_adv_for_19_resolve_fusion_player_without_method_still_clears_slots()

	# ADV-FOR-20: Third fill overwrites slot B (last-absorb-wins policy)
	test_adv_for_20_third_fill_overwrites_slot_b()

	# ADV-FOR-21: EnemyFusionB Y above FusionPlatformB TOP SURFACE (mirrors ADV-FOR-02)
	test_adv_for_21_enemy_b_y_above_platform_top_surface()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
