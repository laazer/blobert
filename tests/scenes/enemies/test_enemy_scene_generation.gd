#
# test_enemy_scene_generation.gd
#
# Primary behavioral tests for headless enemy scene generation and level placement.
# Verifies generated .tscn structure (node hierarchy, metadata, properties) and
# level modification (4 family enemies present, old Enemy/Enemy2 removed, positions).
#
# Ticket: project_board/5_milestone_5_procedural_enemy_generation/in_progress/first_4_families_in_level.md
# Spec:   project_board/specs/first_4_families_in_level_spec.md
# Stage:  TEST_DESIGN (red-phase — tests skip or fail until implementation is complete)
#
# SKIP pattern: tests that require a live SceneTree use the pattern from test_3d_scene.gd.
# Tests that require generated .tscn files that do not yet exist skip gracefully (print SKIP).
#
# Test IDs: FESG-1 through FESG-32

extends "res://tests/utils/test_utils.gd"

const GENERATED_BASE: String = "res://scenes/enemies/generated/"
const LEVEL_PATH: String = "res://scenes/levels/sandbox/test_movement_3d.tscn"
const POSITION_TOL: float = 0.01

# Canonical list of the 12 expected generated scene basenames (AC-TEST-1.3)
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

# Expected mutation mapping per spec table in FESG-GEN-3
const EXPECTED_FAMILY: Dictionary = {
	"acid_spitter_animated_00": "acid_spitter",
	"acid_spitter_animated_01": "acid_spitter",
	"acid_spitter_animated_02": "acid_spitter",
	"adhesion_bug_animated_00": "adhesion_bug",
	"adhesion_bug_animated_01": "adhesion_bug",
	"adhesion_bug_animated_02": "adhesion_bug",
	"carapace_husk_animated_00": "carapace_husk",
	"carapace_husk_animated_01": "carapace_husk",
	"carapace_husk_animated_02": "carapace_husk",
	"claw_crawler_animated_00": "claw_crawler",
	"claw_crawler_animated_01": "claw_crawler",
	"claw_crawler_animated_02": "claw_crawler",
}

const EXPECTED_MUTATION: Dictionary = {
	"acid_spitter_animated_00": "acid",
	"acid_spitter_animated_01": "acid",
	"acid_spitter_animated_02": "acid",
	"adhesion_bug_animated_00": "adhesion",
	"adhesion_bug_animated_01": "adhesion",
	"adhesion_bug_animated_02": "adhesion",
	"carapace_husk_animated_00": "carapace",
	"carapace_husk_animated_01": "carapace",
	"carapace_husk_animated_02": "carapace",
	"claw_crawler_animated_00": "claw",
	"claw_crawler_animated_01": "claw",
	"claw_crawler_animated_02": "claw",
}

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
# FESG-1: Generated directory has exactly 12 .tscn files
# Spec: AC-GEN-2.1, AC-TEST-1.1
# ---------------------------------------------------------------------------
func test_fesg_1_generated_dir_has_12_scenes() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-1 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var dir := DirAccess.open(GENERATED_BASE)
	var count: int = 0
	dir.list_dir_begin()
	while true:
		var entry: String = dir.get_next()
		if entry == "":
			break
		if not dir.current_is_dir() and entry.ends_with(".tscn"):
			count += 1
	dir.list_dir_end()
	_assert_eq_int(12, count, "FESG-1 — scenes/enemies/generated/ contains exactly 12 .tscn files, got " + str(count))


# ---------------------------------------------------------------------------
# FESG-2: All 12 generated scenes are loadable (non-null load)
# Spec: AC-GEN-2.2, FESG-TEST-1 table
# ---------------------------------------------------------------------------
func test_fesg_2_all_generated_scenes_loadable() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-2 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var path: String = GENERATED_BASE + basename + ".tscn"
		var packed: PackedScene = load(path) as PackedScene
		_assert_true(
			packed != null,
			"FESG-2 — " + path + " loads without returning null"
		)
		if packed != null:
			var inst: Node = packed.instantiate()
			_assert_true(
				inst != null,
				"FESG-2 — " + path + " instantiates without returning null"
			)
			if inst != null:
				inst.free()


# ---------------------------------------------------------------------------
# FESG-3: adhesion_bug_animated_00 enemy_id correct
# Spec: AC-GEN-3.3, AC-TSCN-2 table
# ---------------------------------------------------------------------------
func test_fesg_3_adhesion_bug_00_enemy_id() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-3 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("adhesion_bug_animated_00")
	if inst == null:
		_fail_test("FESG-3", "adhesion_bug_animated_00.tscn failed to load or instantiate")
		return
	_assert_eq_string(
		"adhesion_bug_animated_00",
		str(inst.get("enemy_id")),
		"FESG-3 — adhesion_bug_animated_00.tscn root.enemy_id == 'adhesion_bug_animated_00'"
	)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-4: adhesion_bug_animated_00 enemy_family correct
# Spec: AC-GEN-3.1, AC-TSCN-2.5
# ---------------------------------------------------------------------------
func test_fesg_4_adhesion_bug_00_enemy_family() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-4 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("adhesion_bug_animated_00")
	if inst == null:
		_fail_test("FESG-4", "adhesion_bug_animated_00.tscn failed to load or instantiate")
		return
	_assert_eq_string(
		"adhesion_bug",
		str(inst.get("enemy_family")),
		"FESG-4 — adhesion_bug_animated_00.tscn root.enemy_family == 'adhesion_bug'"
	)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-5: adhesion_bug_animated_00 mutation_drop correct
# Spec: AC-GEN-3.2, AC-TSCN-2.6
# ---------------------------------------------------------------------------
func test_fesg_5_adhesion_bug_00_mutation_drop() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-5 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("adhesion_bug_animated_00")
	if inst == null:
		_fail_test("FESG-5", "adhesion_bug_animated_00.tscn failed to load or instantiate")
		return
	_assert_eq_string(
		"adhesion",
		str(inst.get("mutation_drop")),
		"FESG-5 — adhesion_bug_animated_00.tscn root.mutation_drop == 'adhesion'"
	)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-6: acid_spitter_animated_00 mutation_drop correct
# Spec: AC-GEN-3.2, mutation mapping table
# ---------------------------------------------------------------------------
func test_fesg_6_acid_spitter_00_mutation_drop() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-6 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("acid_spitter_animated_00")
	if inst == null:
		_fail_test("FESG-6", "acid_spitter_animated_00.tscn failed to load or instantiate")
		return
	_assert_eq_string(
		"acid",
		str(inst.get("mutation_drop")),
		"FESG-6 — acid_spitter_animated_00.tscn root.mutation_drop == 'acid'"
	)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-7: claw_crawler_animated_00 mutation_drop correct
# Spec: AC-GEN-3.2, mutation mapping table
# ---------------------------------------------------------------------------
func test_fesg_7_claw_crawler_00_mutation_drop() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-7 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("claw_crawler_animated_00")
	if inst == null:
		_fail_test("FESG-7", "claw_crawler_animated_00.tscn failed to load or instantiate")
		return
	_assert_eq_string(
		"claw",
		str(inst.get("mutation_drop")),
		"FESG-7 — claw_crawler_animated_00.tscn root.mutation_drop == 'claw'"
	)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-8: carapace_husk_animated_00 mutation_drop correct
# Spec: AC-GEN-3.2, mutation mapping table
# ---------------------------------------------------------------------------
func test_fesg_8_carapace_husk_00_mutation_drop() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-8 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("carapace_husk_animated_00")
	if inst == null:
		_fail_test("FESG-8", "carapace_husk_animated_00.tscn failed to load or instantiate")
		return
	_assert_eq_string(
		"carapace",
		str(inst.get("mutation_drop")),
		"FESG-8 — carapace_husk_animated_00.tscn root.mutation_drop == 'carapace'"
	)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-9: Each generated scene has a CollisionShape3D with non-null shape
# Spec: AC-GEN-4.1, AC-TSCN-3.3
# ---------------------------------------------------------------------------
func test_fesg_9_generated_scene_has_collision_shape() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-9 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-9", basename + ".tscn failed to load — cannot check CollisionShape3D")
			continue
		var col: Node = inst.get_node_or_null("CollisionShape3D")
		_assert_true(
			col != null,
			"FESG-9 — " + basename + " has CollisionShape3D direct child"
		)
		if col != null:
			_assert_true(
				col is CollisionShape3D,
				"FESG-9 — " + basename + " CollisionShape3D child is instance of CollisionShape3D"
			)
			_assert_true(
				(col as CollisionShape3D).shape != null,
				"FESG-9 — " + basename + " CollisionShape3D.shape is not null"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-10: Each generated scene has a Visual node (Node3D)
# Spec: AC-TSCN-3.1
# ---------------------------------------------------------------------------
func test_fesg_10_generated_scene_has_visual_node() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-10 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-10", basename + ".tscn failed to load")
			continue
		var visual: Node = inst.get_node_or_null("Visual")
		_assert_true(
			visual != null,
			"FESG-10 — " + basename + " has Visual child"
		)
		if visual != null:
			_assert_true(
				visual is Node3D,
				"FESG-10 — " + basename + " Visual is Node3D"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-11: Each generated scene has Visual/Model node
# Spec: AC-TSCN-3.2
# ---------------------------------------------------------------------------
func test_fesg_11_generated_scene_has_visual_model() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-11 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-11", basename + ".tscn failed to load")
			continue
		var model: Node = inst.get_node_or_null("Visual/Model")
		_assert_true(
			model != null,
			"FESG-11 — " + basename + " has Visual/Model child"
		)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-12: Each generated scene has a Hurtbox (Area3D)
# Spec: AC-TSCN-3.7
# ---------------------------------------------------------------------------
func test_fesg_12_generated_scene_has_hurtbox() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-12 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-12", basename + ".tscn failed to load")
			continue
		var hurtbox: Node = inst.get_node_or_null("Hurtbox")
		_assert_true(
			hurtbox != null,
			"FESG-12 — " + basename + " has Hurtbox child"
		)
		if hurtbox != null:
			_assert_true(
				hurtbox is Area3D,
				"FESG-12 — " + basename + " Hurtbox is Area3D"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-13: Each generated scene has Hurtbox/CollisionShape3D
# Spec: AC-TSCN-3.8
# ---------------------------------------------------------------------------
func test_fesg_13_generated_scene_has_hurtbox_collision() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-13 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-13", basename + ".tscn failed to load")
			continue
		var hurtbox_col: Node = inst.get_node_or_null("Hurtbox/CollisionShape3D")
		_assert_true(
			hurtbox_col != null,
			"FESG-13 — " + basename + " has Hurtbox/CollisionShape3D"
		)
		if hurtbox_col != null:
			_assert_true(
				(hurtbox_col as CollisionShape3D).shape != null,
				"FESG-13 — " + basename + " Hurtbox/CollisionShape3D.shape is not null"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-14: Each generated scene has AttackOrigin (Marker3D)
# Spec: AC-TSCN-3.4
# ---------------------------------------------------------------------------
func test_fesg_14_generated_scene_has_attack_origin() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-14 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-14", basename + ".tscn failed to load")
			continue
		var node: Node = inst.get_node_or_null("AttackOrigin")
		_assert_true(
			node != null,
			"FESG-14 — " + basename + " has AttackOrigin child"
		)
		if node != null:
			_assert_true(
				node is Marker3D,
				"FESG-14 — " + basename + " AttackOrigin is Marker3D"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-15: Each generated scene has ChunkAttachPoint (Marker3D)
# Spec: AC-TSCN-3.5
# ---------------------------------------------------------------------------
func test_fesg_15_generated_scene_has_chunk_attach_point() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-15 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-15", basename + ".tscn failed to load")
			continue
		var node: Node = inst.get_node_or_null("ChunkAttachPoint")
		_assert_true(
			node != null,
			"FESG-15 — " + basename + " has ChunkAttachPoint child"
		)
		if node != null:
			_assert_true(
				node is Marker3D,
				"FESG-15 — " + basename + " ChunkAttachPoint is Marker3D"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-16: Each generated scene has PickupAnchor (Marker3D)
# Spec: AC-TSCN-3.6
# ---------------------------------------------------------------------------
func test_fesg_16_generated_scene_has_pickup_anchor() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-16 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-16", basename + ".tscn failed to load")
			continue
		var node: Node = inst.get_node_or_null("PickupAnchor")
		_assert_true(
			node != null,
			"FESG-16 — " + basename + " has PickupAnchor child"
		)
		if node != null:
			_assert_true(
				node is Marker3D,
				"FESG-16 — " + basename + " PickupAnchor is Marker3D"
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-17: Each generated scene has VisibleOnScreenNotifier3D
# Spec: AC-TSCN-3.9
# ---------------------------------------------------------------------------
func test_fesg_17_generated_scene_has_notifier() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-17 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-17", basename + ".tscn failed to load")
			continue
		var node: Node = inst.get_node_or_null("VisibleOnScreenNotifier3D")
		_assert_true(
			node != null,
			"FESG-17 — " + basename + " has VisibleOnScreenNotifier3D child"
		)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-18: Each generated scene root is a CharacterBody3D
# Spec: AC-TSCN-1.1
# ---------------------------------------------------------------------------
func test_fesg_18_generated_scene_root_is_character_body() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-18 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-18", basename + ".tscn failed to load")
			continue
		_assert_true(
			inst is CharacterBody3D,
			"FESG-18 — " + basename + " root is CharacterBody3D"
		)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-19: Each generated scene root has enemy_base.gd script attached
# Spec: AC-TSCN-1.3
# ---------------------------------------------------------------------------
func test_fesg_19_generated_scene_root_has_enemy_base_script() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-19 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-19", basename + ".tscn failed to load")
			continue
		var script_res: Resource = inst.get_script()
		_assert_true(
			script_res != null,
			"FESG-19 — " + basename + " root.get_script() is not null"
		)
		if script_res != null:
			_assert_true(
				script_res.resource_path.ends_with("enemy_base.gd"),
				"FESG-19 — " + basename + " script path ends with 'enemy_base.gd', got: " + script_res.resource_path
			)
		inst.free()


# ---------------------------------------------------------------------------
# FESG-20: Meta values match property values on adhesion_bug_animated_00
# Spec: AC-TSCN-2.1, AC-TSCN-2.2, AC-TSCN-2.3
# ---------------------------------------------------------------------------
func test_fesg_20_generated_scene_meta_matches_property() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-20 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	var inst: Node = _load_generated("adhesion_bug_animated_00")
	if inst == null:
		_fail_test("FESG-20", "adhesion_bug_animated_00.tscn failed to load")
		return
	_assert_true(
		inst.has_meta("enemy_family"),
		"FESG-20 — adhesion_bug_animated_00 has meta 'enemy_family'"
	)
	if inst.has_meta("enemy_family"):
		_assert_eq_string(
			str(inst.get_meta("enemy_family")),
			str(inst.get("enemy_family")),
			"FESG-20 — get_meta('enemy_family') == enemy_family property"
		)
	_assert_true(
		inst.has_meta("enemy_id"),
		"FESG-20 — adhesion_bug_animated_00 has meta 'enemy_id'"
	)
	if inst.has_meta("enemy_id"):
		_assert_eq_string(
			str(inst.get_meta("enemy_id")),
			str(inst.get("enemy_id")),
			"FESG-20 — get_meta('enemy_id') == enemy_id property"
		)
	_assert_true(
		inst.has_meta("mutation_drop"),
		"FESG-20 — adhesion_bug_animated_00 has meta 'mutation_drop'"
	)
	if inst.has_meta("mutation_drop"):
		_assert_eq_string(
			str(inst.get_meta("mutation_drop")),
			str(inst.get("mutation_drop")),
			"FESG-20 — get_meta('mutation_drop') == mutation_drop property"
		)
	inst.free()


# ---------------------------------------------------------------------------
# FESG-21: Level scene loads and instantiates without error
# Spec: AC-LEVEL-1.1
# ---------------------------------------------------------------------------
func test_fesg_21_level_loads() -> void:
	var packed: PackedScene = load(LEVEL_PATH) as PackedScene
	if packed == null:
		_fail_test("FESG-21", "load('" + LEVEL_PATH + "') returned null")
		return
	var inst: Node = packed.instantiate()
	_assert_true(
		inst != null,
		"FESG-21 — test_movement_3d.tscn instantiates without error"
	)
	if inst != null:
		inst.free()


# ---------------------------------------------------------------------------
# FESG-22: Level has AdhesionBugEnemy node
# Spec: AC-LEVEL-1.2
# ---------------------------------------------------------------------------
func test_fesg_22_level_has_adhesion_bug_enemy() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-22", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("AdhesionBugEnemy") != null,
		"FESG-22 — level has AdhesionBugEnemy node"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-23: Level has AcidSpitterEnemy node
# Spec: AC-LEVEL-1.3
# ---------------------------------------------------------------------------
func test_fesg_23_level_has_acid_spitter_enemy() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-23", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("AcidSpitterEnemy") != null,
		"FESG-23 — level has AcidSpitterEnemy node"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-24: Level has ClawCrawlerEnemy node
# Spec: AC-LEVEL-1.4
# ---------------------------------------------------------------------------
func test_fesg_24_level_has_claw_crawler_enemy() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-24", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("ClawCrawlerEnemy") != null,
		"FESG-24 — level has ClawCrawlerEnemy node"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-25: Level has CarapaceHuskEnemy node
# Spec: AC-LEVEL-1.5
# ---------------------------------------------------------------------------
func test_fesg_25_level_has_carapace_husk_enemy() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-25", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("CarapaceHuskEnemy") != null,
		"FESG-25 — level has CarapaceHuskEnemy node"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-26: Level no longer has old Enemy / Enemy2 nodes
# Spec: AC-LEVEL-1.6, AC-LEVEL-1.7
# ---------------------------------------------------------------------------
func test_fesg_26_level_enemy_old_nodes_removed() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-26", "level scene failed to load")
		return
	_assert_true(
		root.get_node_or_null("Enemy") == null,
		"FESG-26 — level does not have old 'Enemy' node"
	)
	_assert_true(
		root.get_node_or_null("Enemy2") == null,
		"FESG-26 — level does not have old 'Enemy2' node"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-27: AdhesionBugEnemy position is approx Vector3(4.0, 1.0, 0.0)
# Spec: AC-LEVEL-1.13
# ---------------------------------------------------------------------------
func test_fesg_27_level_adhesion_bug_position() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-27", "level scene failed to load")
		return
	var enemy: Node = root.get_node_or_null("AdhesionBugEnemy")
	if enemy == null:
		_fail_test("FESG-27", "AdhesionBugEnemy not found in level")
		root.free()
		return
	_assert_vec3_near(
		(enemy as Node3D).position,
		Vector3(4.0, 1.0, 0.0),
		POSITION_TOL,
		"FESG-27 — AdhesionBugEnemy.position approx Vector3(4.0, 1.0, 0.0)"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-28: AcidSpitterEnemy position is approx Vector3(-4.0, 1.0, 0.0)
# Spec: AC-LEVEL-1.14
# ---------------------------------------------------------------------------
func test_fesg_28_level_acid_spitter_position() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-28", "level scene failed to load")
		return
	var enemy: Node = root.get_node_or_null("AcidSpitterEnemy")
	if enemy == null:
		_fail_test("FESG-28", "AcidSpitterEnemy not found in level")
		root.free()
		return
	_assert_vec3_near(
		(enemy as Node3D).position,
		Vector3(-4.0, 1.0, 0.0),
		POSITION_TOL,
		"FESG-28 — AcidSpitterEnemy.position approx Vector3(-4.0, 1.0, 0.0)"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-29: ClawCrawlerEnemy position is approx Vector3(0.0, 1.0, 4.0)
# Spec: AC-LEVEL-1.15
# ---------------------------------------------------------------------------
func test_fesg_29_level_claw_crawler_position() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-29", "level scene failed to load")
		return
	var enemy: Node = root.get_node_or_null("ClawCrawlerEnemy")
	if enemy == null:
		_fail_test("FESG-29", "ClawCrawlerEnemy not found in level")
		root.free()
		return
	_assert_vec3_near(
		(enemy as Node3D).position,
		Vector3(8.0, 1.0, 0.0),
		POSITION_TOL,
		"FESG-29 — ClawCrawlerEnemy.position approx Vector3(8.0, 1.0, 0.0)"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-30: CarapaceHuskEnemy position is approx Vector3(-8.0, 1.0, 0.0)
# Spec: AC-LEVEL-1.16
# ---------------------------------------------------------------------------
func test_fesg_30_level_carapace_husk_position() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-30", "level scene failed to load")
		return
	var enemy: Node = root.get_node_or_null("CarapaceHuskEnemy")
	if enemy == null:
		_fail_test("FESG-30", "CarapaceHuskEnemy not found in level")
		root.free()
		return
	_assert_vec3_near(
		(enemy as Node3D).position,
		Vector3(-8.0, 1.0, 0.0),
		POSITION_TOL,
		"FESG-30 — CarapaceHuskEnemy.position approx Vector3(-8.0, 1.0, 0.0)"
	)
	root.free()


# ---------------------------------------------------------------------------
# FESG-31: All 4 level enemies instance enemy_infection_3d.tscn
# Spec: AC-LEVEL-1.8 through AC-LEVEL-1.11
# ---------------------------------------------------------------------------
func test_fesg_31_level_enemies_use_infection_scene() -> void:
	var root: Node = _load_level()
	if root == null:
		_fail_test("FESG-31", "level scene failed to load")
		return
	for name in ["AdhesionBugEnemy", "AcidSpitterEnemy", "ClawCrawlerEnemy", "CarapaceHuskEnemy"]:
		var enemy: Node = root.get_node_or_null(name)
		if enemy == null:
			_fail_test("FESG-31", name + " not found in level")
			continue
		_assert_true(
			enemy.get_scene_file_path().contains("enemy_infection_3d.tscn"),
			"FESG-31 — " + name + ".get_scene_file_path() contains 'enemy_infection_3d.tscn', got: " + enemy.get_scene_file_path()
		)
	root.free()


# ---------------------------------------------------------------------------
# FESG-32: Each generated scene root has exactly 9 direct children
# Spec: AC-TSCN-3.11
# Updated from 7 to 9 after AnimationPlayer and EnemyAnimationController were
# added as direct children of the scene root (M7-ACS AC-1.3, AC-1.4).
# Children: Visual, CollisionShape3D, AnimationPlayer, EnemyAnimationController,
#           AttackOrigin, ChunkAttachPoint, PickupAnchor, Hurtbox,
#           VisibleOnScreenNotifier3D (9 total).
# ---------------------------------------------------------------------------
func test_fesg_32_generated_scene_child_count() -> void:
	if not _generated_dir_exists():
		print("  SKIP: FESG-32 — res://scenes/enemies/generated/ does not exist yet (implementation pending)")
		return
	for basename in GENERATED_BASENAMES:
		var inst: Node = _load_generated(basename)
		if inst == null:
			_fail_test("FESG-32", basename + ".tscn failed to load")
			continue
		var count: int = inst.get_child_count()
		_assert_eq_int(
			9,
			count,
			"FESG-32 — " + basename + " root has exactly 9 direct children, got " + str(count)
		)
		inst.free()


# ---------------------------------------------------------------------------
# Public entry point — AC-TEST-1.1, AC-TEST-1.5
# ---------------------------------------------------------------------------
func run_all() -> int:
	print("--- test_enemy_scene_generation.gd ---")
	_pass_count = 0
	_fail_count = 0

	# Generator output count and loadability
	test_fesg_1_generated_dir_has_12_scenes()
	test_fesg_2_all_generated_scenes_loadable()

	# Per-family metadata: enemy_id, enemy_family, mutation_drop
	test_fesg_3_adhesion_bug_00_enemy_id()
	test_fesg_4_adhesion_bug_00_enemy_family()
	test_fesg_5_adhesion_bug_00_mutation_drop()
	test_fesg_6_acid_spitter_00_mutation_drop()
	test_fesg_7_claw_crawler_00_mutation_drop()
	test_fesg_8_carapace_husk_00_mutation_drop()

	# Node structure — loops over all 12 scenes
	test_fesg_9_generated_scene_has_collision_shape()
	test_fesg_10_generated_scene_has_visual_node()
	test_fesg_11_generated_scene_has_visual_model()
	test_fesg_12_generated_scene_has_hurtbox()
	test_fesg_13_generated_scene_has_hurtbox_collision()
	test_fesg_14_generated_scene_has_attack_origin()
	test_fesg_15_generated_scene_has_chunk_attach_point()
	test_fesg_16_generated_scene_has_pickup_anchor()
	test_fesg_17_generated_scene_has_notifier()
	test_fesg_18_generated_scene_root_is_character_body()
	test_fesg_19_generated_scene_root_has_enemy_base_script()

	# Metadata/property consistency
	test_fesg_20_generated_scene_meta_matches_property()

	# Level placement
	test_fesg_21_level_loads()
	test_fesg_22_level_has_adhesion_bug_enemy()
	test_fesg_23_level_has_acid_spitter_enemy()
	test_fesg_24_level_has_claw_crawler_enemy()
	test_fesg_25_level_has_carapace_husk_enemy()
	test_fesg_26_level_enemy_old_nodes_removed()
	test_fesg_27_level_adhesion_bug_position()
	test_fesg_28_level_acid_spitter_position()
	test_fesg_29_level_claw_crawler_position()
	test_fesg_30_level_carapace_husk_position()
	test_fesg_31_level_enemies_use_infection_scene()

	# Child count contract
	test_fesg_32_generated_scene_child_count()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
