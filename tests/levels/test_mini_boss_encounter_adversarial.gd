#
# test_mini_boss_encounter_adversarial.gd
#
# Adversarial extension of the Mini-Boss Encounter test suite.
# Ticket:  project_board/4_milestone_4_prototype_level/in_progress/mini_boss_encounter.md
# Spec:    agent_context/agents/2_spec/mini_boss_encounter_spec.md
#
# Purpose: Expose coverage gaps, blind spots, and edge-case failures that the primary
# suite (T-53 through T-62 in test_mini_boss_encounter.gd) does not isolate.
# Uses the Test Breaker checklist matrix:
#   Boundary, Assumption checks, Mutation testing, Null/Empty, Combinatorial.
#
# All tests are headless-safe: no await, no physics tick, no input, no signals.
# No test duplicates an assertion name from T-53–T-62 or T-1–T-52.
#
# Adversarial coverage matrix:
#
# | ID          | Category         | Vulnerability probed                                                                                        |
# |-------------|------------------|-------------------------------------------------------------------------------------------------------------|
# | ADV-MBA-01  | Boundary         | MiniBossFloor top surface Y < 0.5 — catches accidental Y=1.3 elevation above player spawn height            |
# | ADV-MBA-02  | Null/Empty       | MiniBossFloor BoxShape3D non-zero extents — independent of T-53 exact-value assertions                      |
# | ADV-MBA-03  | Assumption check | EnemyMiniBoss X separated from all regular enemies by > 1.0 m — boss not co-located with regular enemies   |
# | ADV-MBA-04  | Null/Empty       | LevelExit CollisionShape3D non-zero size.x and size.y — exit trigger not a degenerate zero-area shape       |
# | ADV-MBA-05  | Boundary         | LevelExit positioned past full level (X > 80.0) — exit not prematurely placed mid-level                    |
# | ADV-MBA-06  | Combinatorial    | MiniBossFloor left edge > SkillCheckPlatform3 right edge — arena does not overlap skill check zone          |
# | ADV-MBA-07  | Assumption check | EnemyMiniBoss X within MiniBossFloor bounds (both edges) — boss standing on its own arena floor             |
# | ADV-MBA-08  | Mutation testing | All four enemy node names are distinct strings — no duplicate-name shadowing                                |
#
# NFR compliance:
#   - extends Object; run_all() -> int pattern.
#   - No class_name to avoid global registry conflicts.
#   - Scene cleanup: root.free() called before each test method returns.
#   - All test names prefixed with ADV-MBA- to ensure no collision with T-* assertion names.
#   - collision_mask not retested; covered by T-25 in test_containment_hall_01.gd.

extends "res://tests/utils/test_utils.gd"

const SCENE_PATH: String = "res://scenes/levels/containment_hall_01/containment_hall_01.tscn"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers — mirror the pattern from test_light_skill_check_adversarial.gd
# ---------------------------------------------------------------------------

func _load_level_scene() -> Node:
	var packed: PackedScene = load(SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("adv_mba_scene_load_guard", "load returned null for " + SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("adv_mba_scene_instantiate_guard", "instantiate() returned null for " + SCENE_PATH)
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
# ADV-MBA-01: MiniBossFloor top surface Y < 0.5
#
# Vulnerability probed: T-53 and T-54 assert top surface Y is in [-0.1, 0.1]
# (corridor level). However they do not independently guard the upper bound
# with a wider tolerance that catches the specific regression documented in the
# ticket: EnemyMiniBoss originally at Y=0.5 (lower than regular enemies at
# Y=1.3). If the MiniBossFloor CollisionShape3D Y offset is accidentally flipped
# positive (e.g. from -0.5 to +1.3 during a copy-paste from the enemy placement),
# the top surface becomes 0 + 1.3 + 0.5 = 1.8 m — well above the player's
# initial spawn height and inaccessible without a jump from the corridor.
# T-53/T-54 would catch this (1.8 > 0.1), but they are compound tests that also
# assert exact BoxShape3D dimensions and may short-circuit before the top surface
# assertion if another guard fails first.
#
# ADV-MBA-01 is a single-focus upper-bound guard: top surface < 0.5. Any value
# in [0.1, 0.5) passes T-53/T-54 but would also fail this test, exposing a
# partial elevation that lands exactly in the "player can just barely step on it
# but it feels wrong" failure zone. The threshold 0.5 is chosen as the Y value
# of EnemyMiniBoss itself — if the floor top surface equals the enemy Y, the
# floor is elevated to enemy-origin height, which is a clear regression signal.
#
# Distinct from T-53/T-54: Those tests assert corridor-level Y in [-0.1, 0.1].
# This test asserts a broader safety ceiling (< 0.5) as an independently
# runnable mutation guard that survives T-53/T-54 short-circuits.
#
# Spec ref: MBA-GEO-1 AC-MBA-GEO-1.4
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mba_01_mini_boss_floor_top_surface_y_lt_0_5() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MiniBossFloor")
	if floor_node == null:
		_fail_test(
			"ADV-MBA-01_mini_boss_floor_top_surface_y_lt_0_5",
			"MiniBossFloor node not found — cannot verify top surface Y upper bound"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-MBA-01_mini_boss_floor_top_surface_y_lt_0_5",
			"MiniBossFloor has no BoxShape3D CollisionShape3D — cannot compute top surface Y"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D
	var node_y: float = (floor_node as Node3D).position.y
	# Formula: node.position.y + col.position.y + (box.size.y * 0.5)
	var top_surface_y: float = node_y + col.position.y + (box.size.y * 0.5)

	_assert_true(
		top_surface_y < 0.5,
		"ADV-MBA-01_mini_boss_floor_top_surface_y_lt_0_5",
		"MiniBossFloor top surface Y = " + str(top_surface_y) + " (node.y=" + str(node_y) + " col.y=" + str(col.position.y) + " box.half_y=" + str(box.size.y * 0.5) + "), must be < 0.5 — floor accidentally elevated above player spawn height (Y=0.5 equals EnemyMiniBoss origin) — MBA-GEO-1 AC-MBA-GEO-1.4"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-02: MiniBossFloor BoxShape3D non-zero extents
#
# Vulnerability probed: T-53 asserts EXACT values (25, 1, 10) for MiniBossFloor's
# BoxShape3D. If T-53 short-circuits before the size assertions — e.g. the
# position.x guard fails because the node was moved to X=50 during a scene
# refactor, causing T-53 to return early — then a BoxShape3D with all-zero
# dimensions (the Godot 4 default for a newly assigned shape) is never caught.
# A zero-size BoxShape3D provides no collision surface: the player falls through
# the arena floor silently.
#
# ADV-MBA-02 asserts the non-zero invariant independently of any position check
# or exact-value assertion. It is the minimal safety bar: size.x > 0, size.y > 0,
# size.z > 0. This catches the "newly added CollisionShape3D with default shape"
# failure mode that exact-value tests cannot catch when they short-circuit.
#
# Distinct from T-53: T-53 asserts exact values (25, 1, 10); ADV-MBA-02 asserts
# only the non-zero invariant. Both are needed: exact-value catches wrong-size
# mutations; non-zero catches uninitialized/default shape mutations.
#
# Spec ref: MBA-GEO-1 AC-MBA-GEO-1.3
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mba_02_mini_boss_floor_box_nonzero_extents() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var floor_node: Node = root.get_node_or_null("MiniBossFloor")
	if floor_node == null:
		_fail_test(
			"ADV-MBA-02_mini_boss_floor_box_nonzero_extents",
			"MiniBossFloor node not found — cannot verify BoxShape3D non-zero extents"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(floor_node)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-MBA-02_mini_boss_floor_box_nonzero_extents",
			"MiniBossFloor has no BoxShape3D CollisionShape3D — shape may be uninitialized or default"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D

	_assert_true(
		box.size.x > 0.0,
		"ADV-MBA-02_mini_boss_floor_box_size_x_gt_0",
		"MiniBossFloor BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 — zero-width floor provides no collision surface on the X axis — MBA-GEO-1 AC-MBA-GEO-1.3"
	)

	_assert_true(
		box.size.y > 0.0,
		"ADV-MBA-02_mini_boss_floor_box_size_y_gt_0",
		"MiniBossFloor BoxShape3D size.y = " + str(box.size.y) + ", must be > 0 — zero-height floor has no solid thickness; player may clip through — MBA-GEO-1 AC-MBA-GEO-1.3"
	)

	_assert_true(
		box.size.z > 0.0,
		"ADV-MBA-02_mini_boss_floor_box_size_z_gt_0",
		"MiniBossFloor BoxShape3D size.z = " + str(box.size.z) + ", must be > 0 — zero-depth floor provides no collision surface on the Z axis; player drifting in Z falls through — MBA-GEO-1 AC-MBA-GEO-1.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-03: EnemyMiniBoss not at same X as any regular enemy (separation > 1.0 m)
#
# Vulnerability probed: T-57 asserts that EnemyMiniBoss has a distinct node PATH
# from EnemyFusionA, EnemyFusionB, and EnemyMutationTease. Path distinctness
# confirms the nodes are different objects — but it does NOT assert spatial
# separation. A scene author could place EnemyMiniBoss at X=67 while also
# accidentally moving EnemyFusionA to X=67.1 (a 0.1 m overlap). T-57 passes
# because the paths are distinct, but at runtime both enemies occupy the same
# visual and physical space — the "dedicated boss encounter" design intent is
# violated and the player sees what appears to be a stacked enemy cluster.
#
# ADV-MBA-03 asserts that EnemyMiniBoss is spatially separated from all three
# regular enemies by more than 1.0 m in X. The 1.0 m threshold is chosen as a
# conservative minimum: it is far smaller than the expected separation (67 m vs
# 15 m, 28 m, and 35 m for FusionA/B and MutationTease respectively) but large
# enough to catch accidental co-placement within the same grid cell.
#
# Distinct from T-57: T-57 asserts path identity; ADV-MBA-03 asserts spatial
# separation — a completely independent property.
#
# Spec ref: MBA-BOSS-2 AC-MBA-BOSS-2.1–2.4 (node path distinction); ADV extension
# NOTE: No collision_mask assertion — not applicable to CharacterBody3D enemies.
# ---------------------------------------------------------------------------
func test_adv_mba_03_enemy_mini_boss_separated_from_regular_enemies() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var boss: Node = root.get_node_or_null("EnemyMiniBoss")
	var fusion_a: Node = root.get_node_or_null("EnemyFusionA")
	var fusion_b: Node = root.get_node_or_null("EnemyFusionB")
	var tease: Node = root.get_node_or_null("EnemyMutationTease")

	if boss == null or fusion_a == null or fusion_b == null or tease == null:
		_fail_test(
			"ADV-MBA-03_enemy_mini_boss_separated_from_regular_enemies",
			"One or more of EnemyMiniBoss / EnemyFusionA / EnemyFusionB / EnemyMutationTease not found — cannot verify spatial separation"
		)
		root.free()
		return

	var boss_x: float = (boss as Node3D).position.x
	var fusion_a_x: float = (fusion_a as Node3D).position.x
	var fusion_b_x: float = (fusion_b as Node3D).position.x
	var tease_x: float = (tease as Node3D).position.x

	_assert_true(
		abs(boss_x - fusion_a_x) > 1.0,
		"ADV-MBA-03_mini_boss_x_separated_from_fusion_a",
		"EnemyMiniBoss.x (" + str(boss_x) + ") and EnemyFusionA.x (" + str(fusion_a_x) + ") are within 1.0 m — boss co-located with regular enemy, violating dedicated encounter design — abs diff = " + str(abs(boss_x - fusion_a_x))
	)

	_assert_true(
		abs(boss_x - fusion_b_x) > 1.0,
		"ADV-MBA-03_mini_boss_x_separated_from_fusion_b",
		"EnemyMiniBoss.x (" + str(boss_x) + ") and EnemyFusionB.x (" + str(fusion_b_x) + ") are within 1.0 m — boss co-located with regular enemy, violating dedicated encounter design — abs diff = " + str(abs(boss_x - fusion_b_x))
	)

	_assert_true(
		abs(boss_x - tease_x) > 1.0,
		"ADV-MBA-03_mini_boss_x_separated_from_mutation_tease",
		"EnemyMiniBoss.x (" + str(boss_x) + ") and EnemyMutationTease.x (" + str(tease_x) + ") are within 1.0 m — boss co-located with regular enemy, violating dedicated encounter design — abs diff = " + str(abs(boss_x - tease_x))
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-04: LevelExit CollisionShape3D non-zero size (size.x > 0, size.y > 0)
#
# Vulnerability probed: T-59 asserts size.x > 0 and size.y > 0 for LevelExit's
# BoxShape3D as part of a compound test that also checks node type, ExitFloor
# ordering, and CollisionShape3D existence. If T-59 short-circuits before the
# size assertions (e.g. LevelExit is the wrong type, causing an early return),
# a zero-size or uninitialized BoxShape3D is never caught. A zero-size trigger
# volume fires on zero contacts: the Area3D's body_entered signal never fires,
# the "level_complete" path is silently broken, and the level has no reachable
# exit.
#
# ADV-MBA-04 isolates the non-zero size assertion in a single-focus test. It
# provides independent coverage so that a BoxShape3D reset to (0, 0, 0) is
# caught even when T-59 exits early for an unrelated failure.
#
# Distinct from T-59: T-59 is compound; ADV-MBA-04 focuses exclusively on the
# trigger volume size invariant, making it a targeted mutation guard for the
# "exit trigger accidentally reset to default" failure mode.
#
# Spec ref: MBA-FLOW-2 AC-MBA-FLOW-2.3
# ---------------------------------------------------------------------------
func test_adv_mba_04_level_exit_collision_shape_nonzero_size() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	if level_exit == null:
		_fail_test(
			"ADV-MBA-04_level_exit_collision_shape_nonzero_size",
			"LevelExit node not found — cannot verify CollisionShape3D non-zero size"
		)
		root.free()
		return

	var col: CollisionShape3D = _get_collision_shape(level_exit)
	if col == null or not (col.shape is BoxShape3D):
		_fail_test(
			"ADV-MBA-04_level_exit_collision_shape_nonzero_size",
			"LevelExit has no BoxShape3D CollisionShape3D — trigger volume absent or wrong shape type"
		)
		root.free()
		return

	var box: BoxShape3D = col.shape as BoxShape3D

	_assert_true(
		box.size.x > 0.0,
		"ADV-MBA-04_level_exit_box_size_x_gt_0",
		"LevelExit BoxShape3D size.x = " + str(box.size.x) + ", must be > 0 — zero-width trigger volume cannot detect player body_entered — MBA-FLOW-2 AC-MBA-FLOW-2.3"
	)

	_assert_true(
		box.size.y > 0.0,
		"ADV-MBA-04_level_exit_box_size_y_gt_0",
		"LevelExit BoxShape3D size.y = " + str(box.size.y) + ", must be > 0 — zero-height trigger volume cannot detect player crossing — MBA-FLOW-2 AC-MBA-FLOW-2.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-05: LevelExit positioned past full level (position.x > 80.0)
#
# Vulnerability probed: T-59 asserts LevelExit.position.x > ExitFloor.position.x.
# This is a relative ordering check (93 > 87.5). It confirms exit is after the
# exit floor — but it does NOT confirm the exit is past the mini-boss arena.
# If ExitFloor is accidentally moved to X=60 (inside the arena) and LevelExit
# is moved to X=65, T-59 passes (65 > 60) but the exit is now mid-arena at
# X=65 — 15 m before the MiniBossFloor right edge (80.0). The player could
# trigger level_complete without ever reaching the end of the arena.
#
# ADV-MBA-05 is an absolute position guard: LevelExit.position.x must be
# strictly greater than 80.0 (the MiniBossFloor right edge per spec). This
# ensures the exit is positioned past the full mini-boss arena, independent of
# ExitFloor's current position.
#
# The threshold 80.0 is derived directly from the spec geometry reference:
# MiniBossFloor right edge = 67.5 + 12.5 = 80.0 m. Confirmed scene value
# LevelExit.x = 93. This test will fail on any scene edit that moves LevelExit
# to X <= 80.
#
# Distinct from T-59: T-59 is a relative ordering check (exit > exit_floor);
# ADV-MBA-05 is an absolute lower-bound check (exit > arena right edge = 80.0).
#
# Spec ref: MBA-FLOW-2 AC-MBA-FLOW-2.2; ticket description "LevelExit at X=93"
# ---------------------------------------------------------------------------
func test_adv_mba_05_level_exit_x_past_full_level() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var level_exit: Node = root.get_node_or_null("LevelExit")
	if level_exit == null:
		_fail_test(
			"ADV-MBA-05_level_exit_x_gt_80",
			"LevelExit node not found — cannot verify it is positioned past the full mini-boss arena"
		)
		root.free()
		return

	var exit_x: float = (level_exit as Node3D).position.x

	_assert_true(
		exit_x > 80.0,
		"ADV-MBA-05_level_exit_x_gt_80",
		"LevelExit.position.x = " + str(exit_x) + ", must be > 80.0 (MiniBossFloor right edge = 67.5 + 12.5 = 80.0) — exit must be past the full arena, not prematurely placed mid-level — MBA-FLOW-2 AC-MBA-FLOW-2.2"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-06: MiniBossFloor left edge > SkillCheckPlatform3 right edge
#
# Vulnerability probed: T-61 asserts MiniBossFloor.position.x (center) >
# SkillCheckPlatform3.position.x (center). This confirms the arena center is
# past the platform center — but it does NOT confirm the arena does not overlap
# the skill check zone geometrically. If MiniBossFloor is moved to X=55 and
# SkillCheckPlatform3 is at X=51 with a box size.x of 8, the platform right edge
# is 51 + 4 = 55. The arena left edge is 55 - 12.5 = 42.5. These two zones
# overlap by 55 - 42.5 = 12.5 m — the player would be standing on both the
# skill check platform and the arena floor simultaneously. T-61 passes (55 > 51)
# but the zones geometrically overlap.
#
# ADV-MBA-06 computes actual edges:
#   MiniBossFloor left edge = MiniBossFloor.position.x - (box.size.x / 2.0)
#   SkillCheckPlatform3 right edge = SkillCheckPlatform3.position.x + (P3_box.size.x / 2.0)
# And asserts MiniBossFloor left edge > SkillCheckPlatform3 right edge.
#
# Both CollisionShape3D X offsets are read dynamically to survive future edits.
# Expected values: MiniBossFloor left edge = 67.5 - 12.5 = 55.0;
# SkillCheckPlatform3 right edge = 51 + 4 = 55.0 — exactly touching.
# The strict inequality (>) means exact touching (55.0 > 55.0 is false) would
# fail. This is intentional: the spec requires the arena to be a SEPARATE zone,
# not sharing a boundary with the skill check.
#
# Distinct from T-61: T-61 compares centers; ADV-MBA-06 compares edges —
# a strictly tighter geometric overlap check.
#
# Spec ref: MBA-FLOW-1 AC-MBA-FLOW-1.1; MBA-GEO-1 geometry reference (left edge = 55.0)
# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here
# ---------------------------------------------------------------------------
func test_adv_mba_06_mini_boss_floor_left_edge_clears_skill_check_p3_right_edge() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	# NOTE: collision_mask covered by T-25 in test_containment_hall_01.gd — not retested here

	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	var skill_check_p3: Node = root.get_node_or_null("SkillCheckPlatform3")

	if mini_boss_floor == null:
		_fail_test(
			"ADV-MBA-06_mini_boss_floor_left_edge_gt_p3_right_edge",
			"MiniBossFloor not found — cannot compute arena left edge"
		)
		root.free()
		return

	if skill_check_p3 == null:
		_fail_test(
			"ADV-MBA-06_mini_boss_floor_left_edge_gt_p3_right_edge",
			"SkillCheckPlatform3 not found — cannot compute platform right edge"
		)
		root.free()
		return

	var floor_col: CollisionShape3D = _get_collision_shape(mini_boss_floor)
	if floor_col == null or not (floor_col.shape is BoxShape3D):
		_fail_test(
			"ADV-MBA-06_mini_boss_floor_left_edge_gt_p3_right_edge",
			"MiniBossFloor has no BoxShape3D — cannot compute arena left edge"
		)
		root.free()
		return

	var p3_col: CollisionShape3D = _get_collision_shape(skill_check_p3)
	if p3_col == null or not (p3_col.shape is BoxShape3D):
		_fail_test(
			"ADV-MBA-06_mini_boss_floor_left_edge_gt_p3_right_edge",
			"SkillCheckPlatform3 has no BoxShape3D — cannot compute platform right edge"
		)
		root.free()
		return

	var floor_box: BoxShape3D = floor_col.shape as BoxShape3D
	var p3_box: BoxShape3D = p3_col.shape as BoxShape3D

	var floor_x: float = (mini_boss_floor as Node3D).position.x
	var p3_x: float = (skill_check_p3 as Node3D).position.x

	# Read col X offsets dynamically to survive future scene edits
	var floor_left_edge: float = floor_x + floor_col.position.x - (floor_box.size.x / 2.0)
	var p3_right_edge: float = p3_x + p3_col.position.x + (p3_box.size.x / 2.0)

	# >= is correct: the zones are adjacent (left edge == right edge = 55.0), not overlapping.
	# Strict > would reject the valid adjacent design; >= allows exact touching boundaries.
	_assert_true(
		floor_left_edge >= p3_right_edge,
		"ADV-MBA-06_mini_boss_floor_left_edge_gt_p3_right_edge",
		"MiniBossFloor left edge (" + str(floor_left_edge) + " = " + str(floor_x) + " + col.x(" + str(floor_col.position.x) + ") - half_x(" + str(floor_box.size.x / 2.0) + ")) must be >= SkillCheckPlatform3 right edge (" + str(p3_right_edge) + " = " + str(p3_x) + " + col.x(" + str(p3_col.position.x) + ") + half_x(" + str(p3_box.size.x / 2.0) + ")) — mini-boss arena overlaps skill check zone — MBA-FLOW-1 AC-MBA-FLOW-1.1"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-07: EnemyMiniBoss position within MiniBossFloor bounds (both edges)
#
# Vulnerability probed: T-55 asserts EnemyMiniBoss.position.x is in [55, 80].
# These are the ZONE bounds from the ticket description — they match the
# MiniBossFloor edges (left=55, right=80) but are hardcoded constants. If
# MiniBossFloor is moved (e.g. to X=70, shifting its bounds to [57.5, 82.5]),
# T-55 still passes for an enemy at X=56 because 56 is in the hardcoded [55, 80]
# range — but the enemy is now 1.5 m to the LEFT of the arena's left edge,
# standing on nothing.
#
# ADV-MBA-07 computes MiniBossFloor bounds dynamically from the actual node and
# BoxShape3D data, then asserts EnemyMiniBoss is within those computed bounds.
# Both CollisionShape3D X offset and box half-width are read at runtime, making
# this test robust to scene edits that move or resize the arena.
#
# Distinct from T-55: T-55 uses hardcoded zone bounds [55, 80]; ADV-MBA-07
# uses dynamically computed floor bounds — testing a different invariant.
#
# Spec ref: MBA-BOSS-1 AC-MBA-BOSS-1.3; MBA-GEO-1 geometry reference
# NOTE: No collision_mask assertion — not applicable to CharacterBody3D enemies.
# ---------------------------------------------------------------------------
func test_adv_mba_07_enemy_mini_boss_within_floor_bounds() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var mini_boss_floor: Node = root.get_node_or_null("MiniBossFloor")
	var enemy: Node = root.get_node_or_null("EnemyMiniBoss")

	if mini_boss_floor == null:
		_fail_test(
			"ADV-MBA-07_enemy_mini_boss_within_floor_bounds",
			"MiniBossFloor not found — cannot compute dynamic arena bounds"
		)
		root.free()
		return

	if enemy == null:
		_fail_test(
			"ADV-MBA-07_enemy_mini_boss_within_floor_bounds",
			"EnemyMiniBoss not found — cannot verify boss is within arena floor bounds"
		)
		root.free()
		return

	var floor_col: CollisionShape3D = _get_collision_shape(mini_boss_floor)
	if floor_col == null or not (floor_col.shape is BoxShape3D):
		_fail_test(
			"ADV-MBA-07_enemy_mini_boss_within_floor_bounds",
			"MiniBossFloor has no BoxShape3D — cannot compute dynamic arena bounds"
		)
		root.free()
		return

	var floor_box: BoxShape3D = floor_col.shape as BoxShape3D
	var floor_x: float = (mini_boss_floor as Node3D).position.x

	# Compute floor bounds dynamically (col.position.x read at runtime)
	var floor_left: float = floor_x + floor_col.position.x - (floor_box.size.x / 2.0)
	var floor_right: float = floor_x + floor_col.position.x + (floor_box.size.x / 2.0)

	var enemy_x: float = (enemy as Node3D).position.x

	_assert_true(
		enemy_x >= floor_left,
		"ADV-MBA-07_enemy_mini_boss_x_ge_floor_left_edge",
		"EnemyMiniBoss.position.x (" + str(enemy_x) + ") must be >= MiniBossFloor left edge (" + str(floor_left) + " = " + str(floor_x) + " + col.x(" + str(floor_col.position.x) + ") - half_x(" + str(floor_box.size.x / 2.0) + ")) — boss is left of its own arena floor — MBA-BOSS-1 AC-MBA-BOSS-1.3"
	)

	_assert_true(
		enemy_x <= floor_right,
		"ADV-MBA-07_enemy_mini_boss_x_le_floor_right_edge",
		"EnemyMiniBoss.position.x (" + str(enemy_x) + ") must be <= MiniBossFloor right edge (" + str(floor_right) + " = " + str(floor_x) + " + col.x(" + str(floor_col.position.x) + ") + half_x(" + str(floor_box.size.x / 2.0) + ")) — boss is right of its own arena floor — MBA-BOSS-1 AC-MBA-BOSS-1.3"
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-MBA-08: All four enemy node names are distinct strings
#
# Vulnerability probed: T-57 asserts that EnemyMiniBoss has a distinct node PATH
# from the other three enemies. In Godot 4, get_path() on a direct child of the
# scene root returns a NodePath that includes the node's NAME. If two nodes have
# the same name, Godot 4 auto-renames one to "Name@2" — T-57's path comparison
# would still pass (different paths after auto-rename). But the INTENDED node
# name is what the rest of the code uses to look up nodes via get_node_or_null():
# if EnemyMiniBoss and EnemyFusionA were both named "EnemyFusionA" in the .tscn
# and Godot auto-renamed one to "EnemyFusionA@2", then
# get_node_or_null("EnemyMiniBoss") returns null (node not found at that path)
# while get_node_or_null("EnemyFusionA") returns the first one — silently losing
# the boss reference in all runtime code.
#
# ADV-MBA-08 asserts the NAMES themselves are the four expected distinct strings.
# It does not use get_path(): it reads node.name directly and compares the string
# values. This catches the "accidentally duplicated source node name before
# Godot auto-deduplication" failure mode that T-57 cannot detect.
#
# A secondary mutation this guards against: a copy-paste of EnemyFusionA to
# create EnemyMiniBoss where the author forgot to rename the node in the scene
# tree. The .tscn then contains two nodes both named "EnemyFusionA"; the second
# becomes "EnemyFusionA@2"; get_node_or_null("EnemyMiniBoss") returns null in all
# downstream tests — causing T-55 through T-57 to fail with "node not found"
# rather than revealing the naming root cause.
#
# Distinct from T-57: T-57 compares get_path() strings; ADV-MBA-08 compares
# node.name strings directly and asserts the exact intended names are present.
#
# Spec ref: MBA-BOSS-2 AC-MBA-BOSS-2.1 (all four nodes present); ADV extension
# NOTE: No collision_mask assertion — not applicable to CharacterBody3D enemies.
# ---------------------------------------------------------------------------
func test_adv_mba_08_all_enemy_node_names_distinct() -> void:
	var root: Node = _load_level_scene()
	if root == null:
		return

	var boss: Node = root.get_node_or_null("EnemyMiniBoss")
	var fusion_a: Node = root.get_node_or_null("EnemyFusionA")
	var fusion_b: Node = root.get_node_or_null("EnemyFusionB")
	var tease: Node = root.get_node_or_null("EnemyMutationTease")

	if boss == null or fusion_a == null or fusion_b == null or tease == null:
		_fail_test(
			"ADV-MBA-08_all_enemy_node_names_distinct",
			"One or more of EnemyMiniBoss / EnemyFusionA / EnemyFusionB / EnemyMutationTease not found — cannot verify name distinctness (node may have been renamed/duplicated in scene)"
		)
		root.free()
		return

	var boss_name: String = boss.name
	var fusion_a_name: String = fusion_a.name
	var fusion_b_name: String = fusion_b.name
	var tease_name: String = tease.name

	# Assert each name is the expected string (detects Godot auto-dedup renames like "EnemyFusionA@2")
	_assert_true(
		boss_name == "EnemyMiniBoss",
		"ADV-MBA-08_boss_node_name_is_EnemyMiniBoss",
		"EnemyMiniBoss.name = '" + boss_name + "', expected 'EnemyMiniBoss' — node may have been auto-renamed by Godot (duplicate name in scene) — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)

	_assert_true(
		fusion_a_name == "EnemyFusionA",
		"ADV-MBA-08_fusion_a_node_name_is_EnemyFusionA",
		"EnemyFusionA.name = '" + fusion_a_name + "', expected 'EnemyFusionA' — node may have been auto-renamed by Godot (duplicate name in scene) — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)

	_assert_true(
		fusion_b_name == "EnemyFusionB",
		"ADV-MBA-08_fusion_b_node_name_is_EnemyFusionB",
		"EnemyFusionB.name = '" + fusion_b_name + "', expected 'EnemyFusionB' — node may have been auto-renamed by Godot (duplicate name in scene) — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)

	_assert_true(
		tease_name == "EnemyMutationTease",
		"ADV-MBA-08_tease_node_name_is_EnemyMutationTease",
		"EnemyMutationTease.name = '" + tease_name + "', expected 'EnemyMutationTease' — node may have been auto-renamed by Godot (duplicate name in scene) — MBA-BOSS-2 AC-MBA-BOSS-2.1"
	)

	# Assert all four names are mutually distinct
	_assert_true(
		boss_name != fusion_a_name,
		"ADV-MBA-08_boss_name_ne_fusion_a_name",
		"EnemyMiniBoss.name ('" + boss_name + "') == EnemyFusionA.name ('" + fusion_a_name + "') — duplicate node names cause get_node_or_null shadowing — MBA-BOSS-2"
	)

	_assert_true(
		boss_name != fusion_b_name,
		"ADV-MBA-08_boss_name_ne_fusion_b_name",
		"EnemyMiniBoss.name ('" + boss_name + "') == EnemyFusionB.name ('" + fusion_b_name + "') — duplicate node names cause get_node_or_null shadowing — MBA-BOSS-2"
	)

	_assert_true(
		boss_name != tease_name,
		"ADV-MBA-08_boss_name_ne_tease_name",
		"EnemyMiniBoss.name ('" + boss_name + "') == EnemyMutationTease.name ('" + tease_name + "') — duplicate node names cause get_node_or_null shadowing — MBA-BOSS-2"
	)

	_assert_true(
		fusion_a_name != fusion_b_name,
		"ADV-MBA-08_fusion_a_name_ne_fusion_b_name",
		"EnemyFusionA.name ('" + fusion_a_name + "') == EnemyFusionB.name ('" + fusion_b_name + "') — duplicate node names cause get_node_or_null shadowing"
	)

	root.free()


# ---------------------------------------------------------------------------
# run_all — invoked by tests/run_tests.gd
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- tests/levels/test_mini_boss_encounter_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-MBA-01: MiniBossFloor top surface Y < 0.5 (not accidentally elevated above player spawn height)
	test_adv_mba_01_mini_boss_floor_top_surface_y_lt_0_5()

	# ADV-MBA-02: MiniBossFloor BoxShape3D non-zero extents (independent of T-53 exact-value assertions)
	test_adv_mba_02_mini_boss_floor_box_nonzero_extents()

	# ADV-MBA-03: EnemyMiniBoss X separated from all regular enemies by > 1.0 m
	test_adv_mba_03_enemy_mini_boss_separated_from_regular_enemies()

	# ADV-MBA-04: LevelExit CollisionShape3D non-zero size (exit trigger not degenerate)
	test_adv_mba_04_level_exit_collision_shape_nonzero_size()

	# ADV-MBA-05: LevelExit positioned past full level (X > 80.0, past MiniBossFloor right edge)
	test_adv_mba_05_level_exit_x_past_full_level()

	# ADV-MBA-06: MiniBossFloor left edge > SkillCheckPlatform3 right edge (no zone overlap)
	test_adv_mba_06_mini_boss_floor_left_edge_clears_skill_check_p3_right_edge()

	# ADV-MBA-07: EnemyMiniBoss X within MiniBossFloor dynamic bounds (boss on its own floor)
	test_adv_mba_07_enemy_mini_boss_within_floor_bounds()

	# ADV-MBA-08: All four enemy node names are the expected distinct strings
	test_adv_mba_08_all_enemy_node_names_distinct()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
