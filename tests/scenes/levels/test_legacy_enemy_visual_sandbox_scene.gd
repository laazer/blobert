#
# test_legacy_enemy_visual_sandbox_scene.gd
#
# Contract tests for duplicate sandbox with legacy default enemy visuals (no generated GLB overrides).
# Spec:   project_board/specs/sandbox_scene_legacy_external_enemy_visuals_spec.md (SLEEV-1..4)
# Ticket: project_board/maintenance/in_progress/sandbox_scene_legacy_external_enemy_visuals.md
#
# Headless: ResourceLoader + PackedScene.instantiate + property reads + optional .tscn text scan.
# Red phase: scene file missing or wrong — load/structure tests fail until Implementation adds the duplicate.
#

extends "res://tests/utils/test_utils.gd"

const LEGACY_SCENE_PATH: String = "res://scenes/levels/sandbox/test_movement_3d_legacy_enemy_visual.tscn"

const LEGACY_MAIN_SUBSTR: String = "test_movement_3d_legacy_enemy_visual"

# SLEEV-3.1 — must not appear as ext_resource targets in the legacy level file.
const FORBIDDEN_GLB_PATHS: PackedStringArray = [
	"res://assets/enemies/generated_glb/adhesion_bug_animated_00.glb",
	"res://assets/enemies/generated_glb/acid_spitter_animated_00.glb",
	"res://assets/enemies/generated_glb/claw_crawler_animated_00.glb",
	"res://assets/enemies/generated_glb/carapace_husk_animated_00.glb",
]

# SLEEV-2.2 — top-level child names and order (matches test_movement_3d.tscn).
const EXPECTED_ROOT_CHILD_NAMES: PackedStringArray = [
	"SceneVariantController",
	"InfectionInteractionHandler",
	"WorldEnvironment",
	"DirectionalLight3D",
	"Floor",
	"SpawnPosition",
	"AdhesionBugEnemy",
	"AcidSpitterEnemy",
	"ClawCrawlerEnemy",
	"CarapaceHuskEnemy",
	"InfectionUI",
	"RespawnZone",
	"Player3D",
]

const POS_TOL: float = 1e-3

var _pass_count: int = 0
var _fail_count: int = 0


func _read_text_fs(fs_path: String) -> String:
	var f: FileAccess = FileAccess.open(fs_path, FileAccess.READ)
	if f == null:
		return ""
	var text: String = f.get_as_text()
	f.close()
	return text


func _res_to_fs(res_path: String) -> String:
	return ProjectSettings.globalize_path(res_path)


func _parse_run_main_scene_value(project_source: String) -> String:
	for line in project_source.split("\n"):
		var t: String = line.strip_edges()
		if t.begins_with("run/main_scene="):
			var eq: int = t.find("=")
			if eq < 0:
				return ""
			var rest: String = t.substr(eq + 1).strip_edges()
			if rest.begins_with("\"") and rest.ends_with("\"") and rest.length() >= 2:
				return rest.substr(1, rest.length() - 2)
			return rest
	return ""


func _load_legacy_root() -> Node:
	# Caller must ensure file exists (run_all gates on SLEEV-1.1) to avoid duplicate FAIL lines.
	var packed: PackedScene = ResourceLoader.load(LEGACY_SCENE_PATH) as PackedScene
	if packed == null:
		_fail_test("SLEEV-1.2_pack_load", "ResourceLoader.load returned null: " + LEGACY_SCENE_PATH)
		return null
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail_test("SLEEV-1.2_instantiate", "instantiate() returned null: " + LEGACY_SCENE_PATH)
		return null
	return inst


func test_sleev_1_load_instantiate_root_node3d() -> void:
	var root: Node = _load_legacy_root()
	if root == null:
		return
	_assert_true(root is Node3D, "SLEEV-1.2_root_is_node3d", "root type is " + root.get_class())
	root.free()


func test_sleev_2_root_name_and_child_order() -> void:
	var root: Node = _load_legacy_root()
	if root == null:
		return
	_assert_true(root.name != "TestMovement3D", "SLEEV-2.1_root_not_test_movement_3d", "root name is \"" + str(root.name) + "\"")
	_assert_eq_int(EXPECTED_ROOT_CHILD_NAMES.size(), root.get_child_count(), "SLEEV-2.2_child_count")
	if EXPECTED_ROOT_CHILD_NAMES.size() != root.get_child_count():
		root.free()
		return
	for i in range(EXPECTED_ROOT_CHILD_NAMES.size()):
		var ch: Node = root.get_child(i)
		var want: String = String(EXPECTED_ROOT_CHILD_NAMES[i])
		_assert_eq_string(want, ch.name, "SLEEV-2.2_child_order_" + str(i) + "_" + want)
	root.free()


func test_sleev_2_floor_collision_mask_parity() -> void:
	var root: Node = _load_legacy_root()
	if root == null:
		return
	var floor_body: Node = root.get_node_or_null("Floor")
	if floor_body == null:
		_fail_test("SLEEV-2.3_floor_exists", "Floor missing")
		root.free()
		return
	var mask: int = int(floor_body.get("collision_mask"))
	_assert_eq_int(3, mask, "SLEEV-2.3_floor_collision_mask")
	root.free()


func test_sleev_3_enemy_runtime_parity() -> void:
	var root: Node = _load_legacy_root()
	if root == null:
		return
	var specs: Array[Dictionary] = [
		{"name": "AdhesionBugEnemy", "mutation": "adhesion", "pos": Vector3(4, 1, 0)},
		{"name": "AcidSpitterEnemy", "mutation": "acid", "pos": Vector3(-4, 1, 0)},
		{"name": "ClawCrawlerEnemy", "mutation": "claw", "pos": Vector3(8, 1, 0)},
		{"name": "CarapaceHuskEnemy", "mutation": "carapace", "pos": Vector3(-8, 1, 0)},
	]
	for s in specs:
		var n: String = s["name"]
		var enemy: Node = root.get_node_or_null(n)
		if enemy == null:
			_fail_test("SLEEV-3_enemy_" + n, "node missing")
			continue
		_assert_true(enemy is EnemyInfection3D, "SLEEV-3_type_" + n, "expected EnemyInfection3D, got " + enemy.get_class())
		var interp: int = int(enemy.get("physics_interpolation_mode"))
		_assert_eq_int(1, interp, "SLEEV-3_physics_interp_" + n)
		var md: String = str(enemy.get("mutation_drop"))
		_assert_eq_string(String(s["mutation"]), md, "SLEEV-3_mutation_drop_" + n)
		var ms: Variant = enemy.get("model_scene")
		_assert_true(ms == null, "SLEEV-3.4_model_scene_null_" + n, "model_scene should be unset (null)")
		var origin: Vector3 = (enemy as Node3D).transform.origin
		_assert_vec3_near(origin, s["pos"] as Vector3, POS_TOL, "SLEEV-3_transform_" + n)
	root.free()


func test_sleev_3_tscn_no_forbidden_glb_ext_resource() -> void:
	var fs_path: String = _res_to_fs(LEGACY_SCENE_PATH)
	var src: String = _read_text_fs(fs_path)
	if src == "":
		_fail_test("SLEEV-3.1_tscn_scan_read", "empty or unreadable: " + fs_path)
		return
	for p in FORBIDDEN_GLB_PATHS:
		var hit: bool = src.find(p) >= 0
		_assert_false(hit, "SLEEV-3.1_no_ext_path_" + p.get_file(), "forbidden GLB path still referenced in .tscn")


func test_sleev_3_tscn_no_model_scene_override() -> void:
	var fs_path: String = _res_to_fs(LEGACY_SCENE_PATH)
	var src: String = _read_text_fs(fs_path)
	if src == "":
		_fail_test("SLEEV-3.2_tscn_model_scan_read", "empty or unreadable: " + fs_path)
		return
	var has_override: bool = src.find("model_scene =") >= 0
	_assert_false(has_override, "SLEEV-3.2_no_model_scene_line", "legacy level .tscn must not set model_scene on instances")


func test_sleev_3_tscn_no_glb_ext_resource_lines() -> void:
	# No `.glb` in any `[ext_resource]` line on the level file (generated meshes come from enemy scene).
	var fs_path: String = _res_to_fs(LEGACY_SCENE_PATH)
	var src: String = _read_text_fs(fs_path)
	if src == "":
		_fail_test("SLEEV-3_glb_ext_lines_read", "empty or unreadable: " + fs_path)
		return
	for line in src.split("\n"):
		var t: String = line.strip_edges()
		if not t.begins_with("[ext_resource"):
			continue
		if t.find(".glb") >= 0:
			_fail_test("SLEEV-3_no_glb_ext_resource", "ext_resource references .glb: " + t)
			return
	_pass("SLEEV-3_no_glb_ext_resource")


func test_sleev_4_main_scene_not_legacy_duplicate() -> void:
	# SLEEV-4.1 + non-regression: run/main_scene must not point at the legacy sandbox.
	# SLEEV-4.2 (exact main_scene target) defers to repo policy; ADV-PRS-19 locks procedural_run as entry — do not require test_movement_3d here.
	var fs_path: String = _res_to_fs("res://project.godot")
	var src: String = _read_text_fs(fs_path)
	if src == "":
		_fail_test("SLEEV-4_read_project", "could not read project.godot")
		return
	var main_val: String = _parse_run_main_scene_value(src)
	if main_val == "":
		_fail_test("SLEEV-4_parse_main_scene", "run/main_scene= not found in project.godot")
		return
	var lower: String = main_val.to_lower()
	_assert_false(
		LEGACY_MAIN_SUBSTR in lower,
		"SLEEV-4.1_main_not_legacy",
		"run/main_scene must not reference legacy sandbox; got: " + main_val
	)


func run_all() -> int:
	print("--- test_legacy_enemy_visual_sandbox_scene.gd ---")
	_pass_count = 0
	_fail_count = 0

	if not FileAccess.file_exists(_res_to_fs(LEGACY_SCENE_PATH)):
		_fail_test("SLEEV-1.1_file_exists", "expected file at " + LEGACY_SCENE_PATH)
		print("")
		print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
		return _fail_count

	test_sleev_1_load_instantiate_root_node3d()
	test_sleev_2_root_name_and_child_order()
	test_sleev_2_floor_collision_mask_parity()
	test_sleev_3_enemy_runtime_parity()
	test_sleev_3_tscn_no_forbidden_glb_ext_resource()
	test_sleev_3_tscn_no_model_scene_override()
	test_sleev_3_tscn_no_glb_ext_resource_lines()
	test_sleev_4_main_scene_not_legacy_duplicate()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
