#
# test_light_skill_check_adversarial.gd
#
# Adversarial extension of the Light Skill Check test suite.
# Ticket:  project_board/4_milestone_4_prototype_level/in_progress/light_skill_check.md
# Spec:    agent_context/agents/2_spec/light_skill_check_spec.md
#
# Purpose: Expose coverage gaps, blind spots, and edge-case failures that the primary
# suite (T-43 through T-52 in test_light_skill_check.gd) does not target.
# Uses the Test Breaker checklist matrix:
#   Null/Empty, Boundary, Type/Structure, Assumption checks, Mutation testing.
#
# All tests are headless-safe: no await, no physics tick, no input, no signals.
# No test duplicates an assertion name from T-43–T-52 or T-1–T-42.
#
# Adversarial coverage matrix:
#
# | ID          | Category         | Vulnerability probed                                                                         |
# |-------------|------------------|----------------------------------------------------------------------------------------------|
# | ADV-SKC-01  | Assumption check | SkillCheckFloorBase top surface Y < -1.0 — confirms pit floor, not corridor level            |
# | ADV-SKC-02  | Boundary         | RespawnZone BoxShape3D size.x >= 20 — wide enough to catch falls across zone width           |
# | ADV-SKC-03  | Boundary         | RespawnZone BoxShape3D size.y >= 6 — deep enough from corridor to pit                        |
# | ADV-SKC-04  | Assumption check | RespawnZone CollisionShape3D local Y offset < 0 — zone is below corridor level               |
# | ADV-SKC-05  | Boundary         | SpawnPosition position.y in [0, 3] — not in pit and not floating                             |
# | ADV-SKC-06  | Mutation testing | SkillCheckPlatform3 size.x > SkillCheckPlatform1 size.x — landing pad is wider               |
# | ADV-SKC-07  | Null/Empty       | All three platforms have non-zero extents: size.x > 0 and size.z > 0                         |
# | ADV-SKC-08  | Boundary/Spacing | P2.x - P1.x >= 3 m AND P3.x - P2.x >= 3 m — minimum platform center-to-center spacing       |
#
# NFR compliance:
#   - extends Object; run_all() -> int pattern.
#   - No class_name to avoid global registry conflicts.
#   - Scene cleanup: root.free() called before each test method returns.
#   - All test names prefixed with ADV-SKC- to ensure no collision with T-* assertion names.
#   - collision_mask not retested; covered by T-25 in test_containment_hall_01.gd.

extends Object

const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers — mirror the pattern from test_light_skill_check.gd
# ---------------------------------------------------------------------------

func _pass_test(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail_test(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " -- " + message)


func _assert_true(condition: bool, test_name: String, fail_msg: String = "expected true, got false") -> void:
	if condition:
		_pass_test(test_name)
	else:
		_fail_test(test_name, fail_msg)


func _load_level_scene() -> Node:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("adv_skc_scene_load_guard", "load returned null for " + SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("adv_skc_scene_instantiate_guard", "instantiate() returned null for " + SCENE_PATH)
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


# ---------------------------------------------------------------------------
# ADV-SKC-01: SkillCheckFloorBase top surface Y < -1.0
#
# Vulnerability probed: The node name "SkillCheckFloorBase" may be misread as
# the walkable floor of the skill check zone (at corridor level Y≈0). If any
# scene edit accidentally elevates this node (e.g. CollisionShape3D Y offset
# changed from -4.5 to 0), the top surface becomes +0.5 — passing T-43's
# position.x bounds but falsely placing the "pit floor" at corridor level.
# T-43 asserts box dimensions and position.x but delegates the pit-floor
# confirmation to the top-surface Y formula. This test makes the mutation
# that flips the CollisionShape3D Y offset explicit and independently guarded.
#
# Distinct from T-43: T-43 is a compound test covering existence + type +
# position.x + box size + top surface Y. ADV-SKC-01 is a single-focus
# adversarial assertion on the pit-floor invariant alone, with a diagnostic
# message that prints the actual computed top surface Y, making regressions
# immediately actionable.
#
# Spec ref: SKC-GEO-1 AC-SKC-GEO-1.4
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_skc_01_floor_base_top_surface_y_is_pit_floor() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("SkillCheckFloorBase")
	if floor_node == null:
		_fail_test(
			"ADV-SKC-01_floor_base_top_surface_y_lt_minus_1",
			"SkillCheckFloorBase node not found — cannot verify pit floor top surface Y"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-SKC-01_floor_base_top_surface_y_lt_minus_1",
			"SkillCheckFloorBase has no BoxShape3D CollisionShape3D — cannot compute top surface Y"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	var node_y: float = (floor_node as Node3D).position.y
	var top_surface_y: float = node_y + col.position.y + (box.size.y * 0.5)

	_assert_true(
		top_surface_y < -1.0,
		"ADV-SKC-01_floor_base_top_surface_y_lt_minus_1",
		"SkillCheckFloorBase top surface Y = " + str(top_surface_y) + " (node.y=" + str(node_y) + " col.y=" + str(col.position.y) + " box.half_y=" + str(box.size.y * 0.5) + "), must be < -1.0 — confirms pit floor, not corridor level — SKC-GEO-1 AC-SKC-GEO-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-02: RespawnZone BoxShape3D size.x >= 20
#
# Vulnerability probed: The RespawnZone currently has a BoxShape3D size.x of
# 130 m — far exceeding the 20 m lower bound. T-49 asserts size.x >= 20 as
# part of a compound test that also checks node type, script, NodePath, size.y,
# and col Y offset. If T-49 short-circuits on an earlier assertion failure (e.g.
# script name check fails), the size.x >= 20 assertion is never reached.
# ADV-SKC-02 isolates the width check in a single-focus test so that a scene
# edit that shrinks the BoxShape3D width (e.g. from 130 to 15) fails this test
# independently, regardless of any other RespawnZone property.
#
# Distinct from T-49: T-49 is a compound test; ADV-SKC-02 is a focused
# width-only mutation guard. If a future edit changes only the box dimensions,
# this test will catch it even if T-49 exits early due to an unrelated failure.
#
# Spec ref: SKC-RETRY-1 AC-SKC-RETRY-1.5
# ---------------------------------------------------------------------------
func test_adv_skc_02_respawn_zone_box_size_x_ge_20() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	if zone == null:
		_fail_test(
			"ADV-SKC-02_respawn_zone_box_size_x_ge_20",
			"RespawnZone node not found — cannot verify BoxShape3D size.x"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(zone)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-SKC-02_respawn_zone_box_size_x_ge_20",
			"RespawnZone has no BoxShape3D CollisionShape3D — cannot verify size.x"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(
		box.size.x >= 20.0,
		"ADV-SKC-02_respawn_zone_box_size_x_ge_20",
		"RespawnZone BoxShape3D size.x = " + str(box.size.x) + ", must be >= 20.0 — wide enough to catch falls across skill check zone (X: 39–55 = 16 m) — SKC-RETRY-1 AC-SKC-RETRY-1.5"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-03: RespawnZone BoxShape3D size.y >= 6
#
# Vulnerability probed: The zone's Y depth must span from at least corridor
# level (Y=0) to the pit floor (Y≈-4.0). A BoxShape3D with size.y = 5 centered
# at Y=-5 would cover Y=-7.5 to Y=-2.5 — missing the corridor level entirely
# and failing to catch bodies that fall only 1–2 m. The 6 m lower bound ensures
# the zone's upper edge (center.y + half_y = -5 + 3 = -2) is high enough to
# catch a body at Y≈-2, with margin for the corridor entry at Y=0. T-49 asserts
# this as part of a compound test; ADV-SKC-03 isolates it as a depth-only guard.
#
# Distinct from T-49: See ADV-SKC-02 rationale — single-focus mutation guard.
#
# Spec ref: SKC-RETRY-1 AC-SKC-RETRY-1.6
# ---------------------------------------------------------------------------
func test_adv_skc_03_respawn_zone_box_size_y_ge_6() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	if zone == null:
		_fail_test(
			"ADV-SKC-03_respawn_zone_box_size_y_ge_6",
			"RespawnZone node not found — cannot verify BoxShape3D size.y"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(zone)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-SKC-03_respawn_zone_box_size_y_ge_6",
			"RespawnZone has no BoxShape3D CollisionShape3D — cannot verify size.y"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	_assert_true(
		box.size.y >= 6.0,
		"ADV-SKC-03_respawn_zone_box_size_y_ge_6",
		"RespawnZone BoxShape3D size.y = " + str(box.size.y) + ", must be >= 6.0 — deep enough to catch falls from corridor (Y=0) to pit floor (top surface Y=-4.0) — SKC-RETRY-1 AC-SKC-RETRY-1.6"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-04: RespawnZone CollisionShape3D local Y offset < 0
#
# Vulnerability probed: If the CollisionShape3D local Y offset is accidentally
# reset to 0 or set positive (e.g. Y=1), the zone center is at or above corridor
# level. A body falling from Y=0 would exit the zone immediately rather than
# being caught mid-fall. With the box centered at Y=0 and size.y=8, the zone
# spans Y=-4 to Y=4 — this would catch falls but also fire on bodies that are
# simply standing on the corridor floor at Y=0, causing accidental respawns.
# With Y=-5 (current value), the zone spans Y=-9 to Y=-1, catching only bodies
# that have already fallen 1 m below corridor level. T-49 asserts this in a
# compound test; ADV-SKC-04 isolates the Y-center-below-corridor invariant.
#
# Distinct from T-49: Single-focus adversarial assertion on the Y-offset sign.
#
# Spec ref: SKC-RETRY-1 AC-SKC-RETRY-1.7
# ---------------------------------------------------------------------------
func test_adv_skc_04_respawn_zone_col_y_offset_is_negative() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var zone: Node = root.get_node_or_null("RespawnZone")
	if zone == null:
		_fail_test(
			"ADV-SKC-04_respawn_zone_col_y_offset_lt_zero",
			"RespawnZone node not found — cannot verify CollisionShape3D local Y offset"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(zone)
	if col == null:
		_fail_test(
			"ADV-SKC-04_respawn_zone_col_y_offset_lt_zero",
			"RespawnZone has no CollisionShape3D child — cannot verify local Y offset"
		)
		root.free()
		return

	_assert_true(
		col.position.y < 0.0,
		"ADV-SKC-04_respawn_zone_col_y_offset_lt_zero",
		"RespawnZone CollisionShape3D local Y offset = " + str(col.position.y) + ", must be < 0.0 — zone center must be below corridor level to avoid catching bodies standing on corridor floor — SKC-RETRY-1 AC-SKC-RETRY-1.7"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-05: SpawnPosition position.y in [0, 3]
#
# Vulnerability probed: T-50 asserts position.y >= 0 and position.y <= 3 in a
# compound test that also checks node existence, type, and position.x. If the
# scene accidentally sets SpawnPosition.y to -0.1 (barely below corridor level),
# the player would spawn slightly in the ground — potentially triggering physics
# jitter or falling through thin geometry. Similarly, if y > 3 (e.g. y=5 due to
# copy-paste from an elevated spawn marker), the player drops 4+ m on every
# respawn. ADV-SKC-05 focuses exclusively on the Y-range bound, making the
# corridor-height-respawn invariant independently testable.
#
# Distinct from T-50: T-50 is a compound test; ADV-SKC-05 is a Y-range-only
# mutation guard, not repeating the x < 35 assertion or the Marker3D type check.
#
# Spec ref: SKC-RETRY-2 AC-SKC-RETRY-2.3, AC-SKC-RETRY-2.4
# ---------------------------------------------------------------------------
func test_adv_skc_05_spawn_position_y_in_corridor_range() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var spawn: Node = root.get_node_or_null("SpawnPosition")
	if spawn == null:
		_fail_test(
			"ADV-SKC-05_spawn_position_y_in_corridor_range",
			"SpawnPosition node not found — cannot verify respawn Y height"
		)
		root.free()
		return

	var pos: Vector3 = (spawn as Node3D).position

	_assert_true(
		pos.y >= 0.0,
		"ADV-SKC-05_spawn_position_y_ge_0",
		"SpawnPosition.position.y = " + str(pos.y) + ", must be >= 0.0 — player must not spawn in the pit — SKC-RETRY-2 AC-SKC-RETRY-2.3"
	)

	_assert_true(
		pos.y <= 3.0,
		"ADV-SKC-05_spawn_position_y_le_3",
		"SpawnPosition.position.y = " + str(pos.y) + ", must be <= 3.0 — player must not spawn floating above corridor level — SKC-RETRY-2 AC-SKC-RETRY-2.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-06: SkillCheckPlatform3 BoxShape3D size.x > SkillCheckPlatform1 BoxShape3D size.x
#
# Vulnerability probed: T-46 asserts P3 is wider than both P1 and P2 in a
# compound test that also checks P3's existence, type, position, dimensions,
# and top surface Y. If P3 is accidentally resized to 4 m (same as P1/P2), T-46
# catches this — but only if none of the earlier assertions in T-46 short-circuit
# first. ADV-SKC-06 isolates the P3-wider-than-P1 comparison as a standalone
# adversarial check, making it independently discoverable.
#
# Additionally, this test uses the raw box size comparison (not going through
# the compound T-46 logic) so it remains valid even if the T-46 node-existence
# guard returns early for an unrelated failure.
#
# Distinct from T-46: T-46 is compound; ADV-SKC-06 is a focused P3>P1 width
# comparison. T-46 also checks P3 vs P2; ADV-SKC-06 only checks P3 vs P1 to
# target the most likely regression (P3 accidentally given the same 4 m width
# as all other platforms).
#
# Spec ref: SKC-GEO-4 AC-SKC-GEO-4.8
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_skc_06_platform3_wider_than_platform1() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var plat3: Node = root.get_node_or_null("SkillCheckPlatform3")

	if plat1 == null or plat3 == null:
		_fail_test(
			"ADV-SKC-06_platform3_wider_than_platform1",
			"SkillCheckPlatform1 or SkillCheckPlatform3 not found — cannot compare widths"
		)
		root.free()
		return

	var col1: CollisionShape3D = _get_collision_shape(plat1)
	var col3: CollisionShape3D = _get_collision_shape(plat3)

	if col1 == null or not (col1.shape is BoxShape3D):
		_fail_test(
			"ADV-SKC-06_platform3_wider_than_platform1",
			"SkillCheckPlatform1 has no BoxShape3D — cannot compare widths"
		)
		root.free()
		return

	if col3 == null or not (col3.shape is BoxShape3D):
		_fail_test(
			"ADV-SKC-06_platform3_wider_than_platform1",
			"SkillCheckPlatform3 has no BoxShape3D — cannot compare widths"
		)
		root.free()
		return

	var box1: BoxShape3D = col1.shape as BoxShape3D
	var box3: BoxShape3D = col3.shape as BoxShape3D

	_assert_true(
		box3.size.x > box1.size.x,
		"ADV-SKC-06_platform3_wider_than_platform1",
		"SkillCheckPlatform3 BoxShape3D size.x (" + str(box3.size.x) + ") must be > SkillCheckPlatform1 BoxShape3D size.x (" + str(box1.size.x) + ") — P3 is the landing pad and must be wider than the approach platforms — SKC-GEO-4 AC-SKC-GEO-4.8"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-07: All three platforms have non-zero extents (size.x > 0 AND size.z > 0)
#
# Vulnerability probed: If a BoxShape3D is assigned to a CollisionShape3D
# without setting its size (e.g. reset to default in the Godot inspector), the
# size defaults to Vector3(0.2, 0.2, 0.2) in Godot 4 — a near-zero shape that
# provides no actual collision surface and is effectively invisible to physics.
# A player would fall straight through it. The primary tests (T-44, T-45, T-46)
# assert EXACT box dimensions (4×1×6, 4×1×6, 8×1×6) which would also fail —
# but only if the test reaches the _assert_eq_float calls. If any earlier guard
# in T-44/T-45/T-46 short-circuits (e.g. node not found), the zero-size check
# is silently skipped. ADV-SKC-07 asserts non-zero extents for all three
# platforms in a single, minimal, independently runnable test.
#
# Also covers the Z axis: T-43 through T-52 assert exact size.z values but a
# future mutation could set size.z=0 while keeping size.x correct, making the
# platform a flat line with no Z-axis collision — a player drifting in Z
# during a jump would fall through the platform.
#
# Distinct from T-44/T-45/T-46: Those tests assert exact values; this test
# asserts only the non-zero invariant, which is the minimal safety bar. Both
# categories of assertion are needed: exact-value catches accidental resize to
# wrong-but-non-zero values; non-zero catches default/uninitialized shapes.
#
# Spec ref: SKC-GEO-2 AC-SKC-GEO-2.3; SKC-GEO-3 AC-SKC-GEO-3.3; SKC-GEO-4 AC-SKC-GEO-4.3
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_skc_07_all_platforms_have_nonzero_extents() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var platform_names: Array = ["SkillCheckPlatform1", "SkillCheckPlatform2", "SkillCheckPlatform3"]

	for pname in platform_names:
		var plat: Node = root.get_node_or_null(pname)
		if plat == null:
			_fail_test(
				"ADV-SKC-07_" + pname + "_nonzero_extents",
				pname + " node not found — cannot verify non-zero extents"
			)
			continue

		var col: CollisionShape3D = _get_collision_shape(plat)
		if col == null or not (col.shape is BoxShape3D):
			_fail_test(
				"ADV-SKC-07_" + pname + "_nonzero_extents",
				pname + " has no BoxShape3D CollisionShape3D — cannot verify non-zero extents"
			)
			continue

		var box: BoxShape3D = col.shape as BoxShape3D

		_assert_true(
			box.size.x > 0.0,
			"ADV-SKC-07_" + pname + "_size_x_gt_0",
			pname + " BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 — zero-width platform provides no collision surface on the X axis"
		)

		_assert_true(
			box.size.z > 0.0,
			"ADV-SKC-07_" + pname + "_size_z_gt_0",
			pname + " BoxShape3D size.z = " + str(box.size.z) + ", must be > 0 — zero-depth platform provides no collision surface on the Z axis; player drifting in Z during a jump would fall through"
		)

	root.free()


# ---------------------------------------------------------------------------
# ADV-SKC-08: Platform X minimum spacing — P2.x - P1.x >= 3 m AND P3.x - P2.x >= 3 m
#
# Vulnerability probed: T-51 asserts the same center-to-center spacing in a
# compound test that also checks the strict ordering (P1.x < P2.x < P3.x).
# If T-51 reaches its spacing assertions only after confirming ordering passes,
# a scene where P1 and P2 happen to satisfy P1.x < P2.x but are only 2 m apart
# (e.g. P1 at X=39, P2 at X=41) would fail the spacing assertion — but the
# ordering assertion would still pass. ADV-SKC-08 isolates the minimum-spacing
# invariant in a dedicated test, exposing the "bunched-together platform" failure
# mode without relying on the ordering assertions to have run first.
#
# The 3 m lower bound is per spec SKC-PLACE-1: with P3 having a half-width of
# 4 m, any center-to-center spacing < 4 m between P2 and P3 would cause their
# bounding boxes to overlap geometrically. The 3 m bound is conservative; it
# documents the minimum physically meaningful spacing. Values in [3, 4) overlap
# by box geometry but are still separated at the collision shape level (the
# platforms are positioned relative to world origin, not each other).
#
# Distinct from T-51: T-51 is a compound ordering+spacing test; ADV-SKC-08
# focuses only on the minimum-spacing assertion and provides a diagnostic
# message that prints all three X positions for easy regression diagnosis.
#
# Spec ref: SKC-PLACE-1 AC-SKC-PLACE-1.3, AC-SKC-PLACE-1.4
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_skc_08_platform_minimum_x_spacing() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var plat1: Node = root.get_node_or_null("SkillCheckPlatform1")
	var plat2: Node = root.get_node_or_null("SkillCheckPlatform2")
	var plat3: Node = root.get_node_or_null("SkillCheckPlatform3")

	if plat1 == null or plat2 == null or plat3 == null:
		_fail_test(
			"ADV-SKC-08_platform_minimum_x_spacing",
			"One or more of SkillCheckPlatform1/2/3 not found — cannot verify minimum X spacing"
		)
		root.free()
		return

	var p1x: float = (plat1 as Node3D).position.x
	var p2x: float = (plat2 as Node3D).position.x
	var p3x: float = (plat3 as Node3D).position.x

	_assert_true(
		p2x - p1x >= 3.0,
		"ADV-SKC-08_p2_minus_p1_ge_3m",
		"SkillCheckPlatform2.x (" + str(p2x) + ") - SkillCheckPlatform1.x (" + str(p1x) + ") = " + str(p2x - p1x) + " m, must be >= 3.0 m — platforms bunched together make gaps physically meaningless — SKC-PLACE-1 AC-SKC-PLACE-1.3"
	)

	_assert_true(
		p3x - p2x >= 3.0,
		"ADV-SKC-08_p3_minus_p2_ge_3m",
		"SkillCheckPlatform3.x (" + str(p3x) + ") - SkillCheckPlatform2.x (" + str(p2x) + ") = " + str(p3x - p2x) + " m, must be >= 3.0 m — platforms bunched together make gaps physically meaningless — SKC-PLACE-1 AC-SKC-PLACE-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_light_skill_check_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-SKC-01: SkillCheckFloorBase top surface Y is pit floor (< -1.0), not corridor level
	test_adv_skc_01_floor_base_top_surface_y_is_pit_floor()

	# ADV-SKC-02: RespawnZone BoxShape3D size.x >= 20 (wide enough to catch falls)
	test_adv_skc_02_respawn_zone_box_size_x_ge_20()

	# ADV-SKC-03: RespawnZone BoxShape3D size.y >= 6 (deep enough from corridor to pit)
	test_adv_skc_03_respawn_zone_box_size_y_ge_6()

	# ADV-SKC-04: RespawnZone CollisionShape3D local Y offset < 0 (zone is below corridor level)
	test_adv_skc_04_respawn_zone_col_y_offset_is_negative()

	# ADV-SKC-05: SpawnPosition position.y in [0, 3] (not in pit, not floating)
	test_adv_skc_05_spawn_position_y_in_corridor_range()

	# ADV-SKC-06: SkillCheckPlatform3 size.x > SkillCheckPlatform1 size.x (landing pad wider)
	test_adv_skc_06_platform3_wider_than_platform1()

	# ADV-SKC-07: All three platforms have non-zero extents (size.x > 0 and size.z > 0)
	test_adv_skc_07_all_platforms_have_nonzero_extents()

	# ADV-SKC-08: P2.x - P1.x >= 3 m AND P3.x - P2.x >= 3 m (minimum center-to-center spacing)
	test_adv_skc_08_platform_minimum_x_spacing()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
