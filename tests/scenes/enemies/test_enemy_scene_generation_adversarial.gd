#
# test_enemy_scene_generation_adversarial.gd
#
# Adversarial tests probing edge cases and regression surfaces in generated enemy
# scenes and level placement. Verifies properties that are easy to silently break:
# exact file counts, shape non-zero size, hurtbox shape resource isolation,
# family name correctness, mutation coverage, and enemy position above floor.
#
# Ticket: project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md
# Spec:   project_board/specs/first_4_families_in_level_spec.md (FESG-TEST-2)
# Stage:  TEST_DESIGN (red-phase — tests skip or fail until implementation is complete)
#
# Test IDs: ADV-FESG-1 through ADV-FESG-16

extends "res://tests/utils/test_utils.gd"

const GENERATED_BASE: String = "res://scenes/enemies/generated/"
const LEVEL_PATH: String = "res://scenes/levels/sandbox/test_movement_3d.tscn"
const POSITION_TOL: float = 0.001

const GENERATED_BASENAMES: Array = [
	"acid_spitter_animated_00",
	"acid_spitter_animated_01",
	"acid_spitter_animated_02",
	"adhesion_bug_animated_00",
	"adhesion_bug_animated_01",
	"adhesion_bug_animated_02",
	"carapace_husk_animated_00",
	"carapace_husk_animated_01",
	"carapace_husk_animated_02",
	"claw_crawler_animated_00",
	"claw_crawler_animated_01",
	"claw_crawler_animated_02",
]

const LEVEL_ENEMY_NAMES: Array = [
	"AdhesionBugEnemy",
	"AcidSpitterEnemy",
	"ClawCrawlerEnemy",
	"CarapaceHuskEnemy",
]

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _generated_dir_exists() -> bool:
	var dir := DirAccess.open(GENERATED_BASE)
	return dir != null


func _load_generated(basename: String) -> Node:
	var path: String = GENERATED_BASE + basename + ".tscn"
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func _load_level() -> Node:
	var packed: PackedScene = load(LEVEL_PATH) as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


# ---------------------------------------------------------------------------
# ADV-FESG-1: Generated directory has NO extra .tscn files (count == 12, not more)
# Spec: AC-GEN-2.1; regression guard against accidental extra outputs
# ---------------------------------------------------------------------------
func test_adv_fesg_1_no_extra_tscn_files() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-1 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var dir := DirAccess.open(GENERATED_BASE)
	var tscn_files: Array = []
	dir.list_dir_begin()
	while true:
		var entry: String = dir.get_next()
		if entry == "":
			break
		if not dir.current_is_dir() and entry.ends_with(".tscn"):
			tscn_files.append(entry)
	dir.list_dir_end()
	var count: int = tscn_files.size()
	_assert_true(
		count == 12,
		"ADV-FESG-1 — scenes/enemies/generated/ has exactly 12 .tscn files (not more, not fewer), got: " + str(count) + " — files: " + str(tscn_files)
	)


# ---------------------------------------------------------------------------
# ADV-FESG-2: Collision shape is not zero-size (fallback produces valid shape)
# Spec: AC-GEN-4.1, AC-GEN-4.3; guards against zero-AABB fallback producing degenerate shape
# ---------------------------------------------------------------------------
func test_adv_fesg_2_collision_shape_not_zero_size() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-2 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-2", basename + ".tscn failed to load")
			continue
		var col_node: Node = inst.get_node_or_null("CollisionShape3D")
		if col_node == null:
			_fail_test("ADV-FESG-2", basename + " — no CollisionShape3D found")
			inst.free()
			continue
		var shape: Shape3D = (col_node as CollisionShape3D).shape
		if shape == null:
			_fail_test("ADV-FESG-2", basename + " — CollisionShape3D.shape is null")
			inst.free()
			continue
		if shape is BoxShape3D:
			_assert_true(
				(shape as BoxShape3D).size != Vector3.ZERO,
				"ADV-FESG-2 — " + basename + " BoxShape3D.size != Vector3.ZERO"
			)
		elif shape is CapsuleShape3D:
			_assert_true(
				(shape as CapsuleShape3D).radius > 0.0,
				"ADV-FESG-2 — " + basename + " CapsuleShape3D.radius > 0"
			)
			_assert_true(
				(shape as CapsuleShape3D).height > 0.0,
				"ADV-FESG-2 — " + basename + " CapsuleShape3D.height > 0"
			)
		else:
			# Any other non-null shape type is acceptable — just confirm non-null (already done above)
			_pass("ADV-FESG-2 — " + basename + " shape is non-null and non-degenerate (type: " + shape.get_class() + ")")
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-3: Hurtbox shape is a distinct resource instance from root CollisionShape3D shape
# Spec: AC-TSCN-3.10; shared resource instance causes physics collision bugs
# Note: both shapes are newly created (no resource_path); identity check uses != operator
# ---------------------------------------------------------------------------
func test_adv_fesg_3_hurtbox_shape_is_duplicate() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-3 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-3", basename + ".tscn failed to load")
			continue
		var col_node: Node = inst.get_node_or_null("CollisionShape3D")
		var hurtbox_col: Node = inst.get_node_or_null("Hurtbox/CollisionShape3D")
		if col_node == null or hurtbox_col == null:
			_fail_test("ADV-FESG-3", basename + " — CollisionShape3D or Hurtbox/CollisionShape3D missing")
			inst.free()
			continue
		var root_shape: Shape3D = (col_node as CollisionShape3D).shape
		var hurtbox_shape: Shape3D = (hurtbox_col as CollisionShape3D).shape
		if root_shape == null or hurtbox_shape == null:
			_fail_test("ADV-FESG-3", basename + " — one or both shapes are null")
			inst.free()
			continue
		# The hurtbox shape must be a DIFFERENT object instance (result of .duplicate(true))
		_assert_true(
			root_shape != hurtbox_shape,
			"ADV-FESG-3 — " + basename + " Hurtbox shape is a distinct resource instance from root CollisionShape3D shape"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-4: enemy_id matches filename (basename without extension)
# Spec: AC-GEN-3.3; guards against enemy_id set to wrong value
# ---------------------------------------------------------------------------
func test_adv_fesg_4_enemy_id_matches_filename() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-4 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-4", basename + ".tscn failed to load")
			continue
		_assert_eq_string(
			basename,
			str(inst.get("enemy_id")),
			"ADV-FESG-4 — " + basename + " enemy_id == '" + basename + "'"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-5: No generated scene has mutation_drop == "unknown"
# Spec: AC-GEN-3.4 (inverse); MUTATION_BY_FAMILY must cover all 4 families
# ---------------------------------------------------------------------------
func test_adv_fesg_5_no_unknown_mutation_drop() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-5 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-5", basename + ".tscn failed to load")
			continue
		var mutation: String = str(inst.get("mutation_drop"))
		_assert_true(
			mutation != "unknown",
			"ADV-FESG-5 — " + basename + " mutation_drop is not 'unknown', got: '" + mutation + "'"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-6: enemy_family does not contain the substring "animated"
# Spec: AC-GEN-3.1; EnemyNameUtils must strip "animated" token
# ---------------------------------------------------------------------------
func test_adv_fesg_6_family_name_extraction_strips_animated() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-6 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-6", basename + ".tscn failed to load")
			continue
		var family: String = str(inst.get("enemy_family"))
		_assert_false(
			family.contains("animated"),
			"ADV-FESG-6 — " + basename + " enemy_family does not contain 'animated', got: '" + family + "'"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-7: enemy_family does not end with _00, _01, or _02
# Spec: AC-GEN-3.1; EnemyNameUtils must strip numeric variant suffix
# ---------------------------------------------------------------------------
func test_adv_fesg_7_family_name_extraction_strips_variant_index() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-7 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-7", basename + ".tscn failed to load")
			continue
		var family: String = str(inst.get("enemy_family"))
		_assert_false(
			family.ends_with("_00") or family.ends_with("_01") or family.ends_with("_02"),
			"ADV-FESG-7 — " + basename + " enemy_family does not end with variant index, got: '" + family + "'"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-8: Level has exactly all 4 family enemies, no duplicates, none missing
# Spec: AC-LEVEL-1.2 through AC-LEVEL-1.5; guards against partial placement
# ---------------------------------------------------------------------------
func test_adv_fesg_8_all_four_families_present_in_level() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("ADV-FESG-8", "level scene failed to load")
		return
	var found_count: int = 0
	for name in LEVEL_ENEMY_NAMES:
		var enemy: Node = root.get_node_or_null(name)
		if enemy != null:
			found_count += 1
		_assert_true(
			enemy != null,
			"ADV-FESG-8 — level has '" + name + "' (all 4 families must be present)"
		)
	_assert_eq_int(
		4,
		found_count,
		"ADV-FESG-8 — level has exactly 4 family enemies, got " + str(found_count)
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-FESG-9: Level has no node named "Enemy" (old node was removed)
# Spec: AC-LEVEL-1.6; regression guard against re-adding old node
# ---------------------------------------------------------------------------
func test_adv_fesg_9_level_no_node_named_enemy() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("ADV-FESG-9", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("Enemy") == null,
		"ADV-FESG-9 — level has no node named 'Enemy' (old node must be removed)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-FESG-10: Level has no node named "Enemy2" (old node was removed)
# Spec: AC-LEVEL-1.7; regression guard against re-adding old node
# ---------------------------------------------------------------------------
func test_adv_fesg_10_level_no_node_named_enemy2() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("ADV-FESG-10", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("Enemy2") == null,
		"ADV-FESG-10 — level has no node named 'Enemy2' (old node must be removed)"
	)
	root.free()


# ---------------------------------------------------------------------------
# ADV-FESG-11: Visual node is a Node3D (not a plain Node or wrong type)
# Spec: AC-TSCN-3.1; Visual must be Node3D not bare Node
# ---------------------------------------------------------------------------
func test_adv_fesg_11_generated_scene_visual_is_node3d() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-11 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-11", basename + ".tscn failed to load")
			continue
		var visual: Node = inst.get_node_or_null("Visual")
		if visual == null:
			_fail_test("ADV-FESG-11", basename + " — Visual node missing")
			inst.free()
			continue
		_assert_true(
			visual is Node3D,
			"ADV-FESG-11 — " + basename + " Visual is Node3D (not plain Node)"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-12: AttackOrigin position is approx Vector3(0.6, 0.0, 0.0)
# Spec: AC-TSCN-3.4; guards against position typo or wrong axis
# ---------------------------------------------------------------------------
func test_adv_fesg_12_generated_scene_attack_origin_position() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-12 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-12", basename + ".tscn failed to load")
			continue
		var node: Node = inst.get_node_or_null("AttackOrigin")
		if node == null:
			_fail_test("ADV-FESG-12", basename + " — AttackOrigin missing")
			inst.free()
			continue
		_assert_vec3_near(
			(node as Marker3D).position,
			Vector3(0.6, 0.0, 0.0),
			POSITION_TOL,
			"ADV-FESG-12 — " + basename + " AttackOrigin.position approx Vector3(0.6, 0.0, 0.0)"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-13: ChunkAttachPoint position is approx Vector3(0.0, 0.0, 0.2)
# Spec: AC-TSCN-3.5; guards against position typo or wrong axis
# ---------------------------------------------------------------------------
func test_adv_fesg_13_generated_scene_chunk_attach_point_position() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-13 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-13", basename + ".tscn failed to load")
			continue
		var node: Node = inst.get_node_or_null("ChunkAttachPoint")
		if node == null:
			_fail_test("ADV-FESG-13", basename + " — ChunkAttachPoint missing")
			inst.free()
			continue
		_assert_vec3_near(
			(node as Marker3D).position,
			Vector3(0.0, 0.0, 0.2),
			POSITION_TOL,
			"ADV-FESG-13 — " + basename + " ChunkAttachPoint.position approx Vector3(0.0, 0.0, 0.2)"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-14: Each generated scene root has get_base_state() method (EnemyBase script present)
# Spec: AC-TSCN-1.4; verifies script attachment resulted in full EnemyBase API
# ---------------------------------------------------------------------------
func test_adv_fesg_14_generated_scene_has_get_base_state() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-14 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-14", basename + ".tscn failed to load")
			continue
		_assert_true(
			inst.has_method("get_base_state"),
			"ADV-FESG-14 — " + basename + " root.has_method('get_base_state') is true"
		)
		inst.free()


# ---------------------------------------------------------------------------
# ADV-FESG-15: All 4 level enemies have position.y > 0.0 (above the floor)
# Spec: AC-LEVEL-1.12; guards against enemy placed at Y=0 or below
# Tests instantiation-time position only (no physics run)
# ---------------------------------------------------------------------------
func test_adv_fesg_15_level_enemies_above_floor() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("ADV-FESG-15", "level scene failed to load")
		return
	for name in LEVEL_ENEMY_NAMES:
		var enemy: Node = root.get_node_or_null(name)
		if enemy == null:
			_fail_test("ADV-FESG-15", name + " not found in level")
			continue
		_assert_true(
			(enemy as Node3D).position.y > 0.0,
			"ADV-FESG-15 — " + name + ".position.y > 0.0 (above floor), got: " + str((enemy as Node3D).position.y)
		)
	root.free()


# ---------------------------------------------------------------------------
# ADV-FESG-16: All 12 generated scenes have source_glb meta set to a .glb path
# Spec: AC-TSCN-2.4; verifies source provenance metadata is always written
# ---------------------------------------------------------------------------
func test_adv_fesg_16_all_12_scenes_have_source_glb_meta() -> void:
	if not _generated_dir_exists():
		print("  SKIP: ADV-FESG-16 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("ADV-FESG-16", basename + ".tscn failed to load")
			continue
		_assert_true(
			inst.has_meta("source_glb"),
			"ADV-FESG-16 — " + basename + " has_meta('source_glb') is true"
		)
		if inst.has_meta("source_glb"):
			var glb_val: String = str(inst.get_meta("source_glb"))
			_assert_true(
				glb_val.ends_with(".glb"),
				"ADV-FESG-16 — " + basename + " source_glb ends with '.glb', got: '" + glb_val + "'"
			)
		inst.free()


# ---------------------------------------------------------------------------
# Public entry point — AC-TEST-2.1, AC-TEST-2.4
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_enemy_scene_generation_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_fesg_1_no_extra_tscn_files()
	test_adv_fesg_2_collision_shape_not_zero_size()
	test_adv_fesg_3_hurtbox_shape_is_duplicate()
	test_adv_fesg_4_enemy_id_matches_filename()
	test_adv_fesg_5_no_unknown_mutation_drop()
	test_adv_fesg_6_family_name_extraction_strips_animated()
	test_adv_fesg_7_family_name_extraction_strips_variant_index()
	test_adv_fesg_8_all_four_families_present_in_level()
	test_adv_fesg_9_level_no_node_named_enemy()
	test_adv_fesg_10_level_no_node_named_enemy2()
	test_adv_fesg_11_generated_scene_visual_is_node3d()
	test_adv_fesg_12_generated_scene_attack_origin_position()
	test_adv_fesg_13_generated_scene_chunk_attach_point_position()
	test_adv_fesg_14_generated_scene_has_get_base_state()
	test_adv_fesg_15_level_enemies_above_floor()
	test_adv_fesg_16_all_12_scenes_have_source_glb_meta()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
