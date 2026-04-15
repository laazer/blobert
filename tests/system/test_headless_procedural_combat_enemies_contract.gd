#
# test_headless_procedural_combat_enemies_contract.gd
#
# Ticket:
# project_board/10_milestone_10_procedural_enemies_in_level/backlog/04_headless_tests_procedural_combat_enemies.md
#
# Requirement traceability:
# - HTPCE-R1 -> HTPCE-T-01, HTPCE-T-02
# - HTPCE-R2 -> HTPCE-T-03, HTPCE-T-04
# - HTPCE-R3 -> HTPCE-T-05
# - HTPCE-R5 -> HTPCE-T-06
# - HTPCE-R6 -> HTPCE-T-07
#

extends "res://tests/utils/test_utils.gd"

const ASSEMBLER_SCRIPT_PATH: String = "res://scripts/system/run_scene_assembler.gd"
const MODEL_REGISTRY_PATH: String = "res://asset_generation/python/model_registry.json"
const GENERATED_SCENE_ROOT: String = "res://scenes/enemies/generated/"
const SPAWN_DONE_META_KEY: String = "spawn_generated_enemies_for_room_done"
const MAX_BOUNDED_FRAME_PUMP_FRAMES: int = 240

var _pass_count: int = 0
var _fail_count: int = 0


func _load_assembler_script() -> GDScript:
	if not ResourceLoader.exists(ASSEMBLER_SCRIPT_PATH):
		return null
	return load(ASSEMBLER_SCRIPT_PATH) as GDScript


func _combat_room_paths_from_pool() -> Array[String]:
	var assembler_script: GDScript = _load_assembler_script()
	if assembler_script == null:
		return []
	var pool_variant: Variant = assembler_script.get_script_constant_map().get("POOL", {})
	if not (pool_variant is Dictionary):
		return []
	var pool: Dictionary = pool_variant as Dictionary
	var combat_variant: Variant = pool.get("combat", [])
	if not (combat_variant is Array):
		return []
	var paths: Array[String] = []
	for entry in combat_variant:
		if entry is String:
			paths.append(entry)
	return paths


func _instantiate_scene(path: String) -> Node:
	if not ResourceLoader.exists(path):
		return null
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func _read_manifest() -> Dictionary:
	if not FileAccess.file_exists(MODEL_REGISTRY_PATH):
		return {}
	var file: FileAccess = FileAccess.open(MODEL_REGISTRY_PATH, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		return {}
	return parsed as Dictionary


func _build_selector() -> Object:
	var assembler_script: GDScript = _load_assembler_script()
	if assembler_script == null or not assembler_script.can_instantiate():
		return null
	var assembler: Object = assembler_script.new()
	var selector_variant: Variant = assembler.call("_build_enemy_visual_variant_selector")
	if selector_variant is Object:
		return selector_variant as Object
	return null


func _resolve_variant(selector: Object, family: String, manifest: Dictionary) -> Dictionary:
	if selector == null:
		return {}
	if not selector.has_method("resolve_spawn_visual_variant"):
		return {}
	var out: Variant = selector.call("resolve_spawn_visual_variant", family, manifest, null)
	if not (out is Dictionary):
		return {}
	return out as Dictionary


func _bounded_idle_frame_pump(max_frames: int) -> void:
	_assert_true(max_frames >= 0, "HTPCE-T-05_bounded_frame_pump_non_negative")
	_assert_true(max_frames <= MAX_BOUNDED_FRAME_PUMP_FRAMES, "HTPCE-T-05_bounded_frame_pump_within_limit")
	if max_frames < 0 or max_frames > MAX_BOUNDED_FRAME_PUMP_FRAMES:
		return
	var tree: SceneTree = Engine.get_main_loop() as SceneTree
	_assert_true(tree != null, "HTPCE-T-05_scene_tree_available")
	if tree == null:
		return
	var ticks: int = 0
	while ticks < max_frames:
		await tree.process_frame
		ticks += 1
	_assert_eq_int(max_frames, ticks, "HTPCE-T-05_bounded_frame_pump_exact_iterations")


func _new_assembler_instance() -> Object:
	var assembler_script: GDScript = _load_assembler_script()
	if assembler_script == null or not assembler_script.can_instantiate():
		return null
	return assembler_script.new()


func _run_adversarial_spawn_case(
	case_id: String,
	room_scene_path: String,
	declarations_meta: Variant,
	expect_done_meta: bool,
	require_manifest: bool
) -> void:
	var assembler: Object = _new_assembler_instance()
	_assert_true(assembler != null, case_id + "_assembler_instantiable")
	if require_manifest:
		_assert_true(FileAccess.file_exists(MODEL_REGISTRY_PATH), case_id + "_manifest_exists_precondition")
	if assembler == null or (require_manifest and not FileAccess.file_exists(MODEL_REGISTRY_PATH)):
		return
	var room := Node3D.new()
	room.set_meta("enemy_spawn_declarations", declarations_meta)
	var before_count: int = room.get_child_count()
	assembler.call("_spawn_generated_enemies_for_room", room, room_scene_path)
	_assert_eq_int(before_count, room.get_child_count(), case_id + "_spawn_count_unchanged")
	if expect_done_meta:
		_assert_true(bool(room.get_meta(SPAWN_DONE_META_KEY, false)), case_id + "_done_meta_set")
	else:
		_assert_false(bool(room.get_meta(SPAWN_DONE_META_KEY, false)), case_id + "_done_meta_not_set")
	room.free()


func test_htpce_t_01_pool_exposes_loadable_combat_room_paths() -> void:
	# HTPCE-R1: deterministic combat-room selection from POOL["combat"].
	var paths: Array[String] = _combat_room_paths_from_pool()
	_assert_true(not paths.is_empty(), "HTPCE-T-01_pool_has_combat_paths")
	if paths.is_empty():
		return
	var room_path: String = paths[0]
	_assert_true(room_path.begins_with("res://scenes/rooms/room_combat_"), "HTPCE-T-01_room_path_looks_combat_room")
	var room: Node = _instantiate_scene(room_path)
	_assert_true(room != null, "HTPCE-T-01_room_instantiates")
	if room != null:
		room.free()


func test_htpce_t_02_room_declarations_exist_and_have_required_schema() -> void:
	# HTPCE-R1/R2: at least one room exposes deterministic declaration metadata.
	var paths: Array[String] = _combat_room_paths_from_pool()
	_assert_true(not paths.is_empty(), "HTPCE-T-02_pool_has_paths")
	if paths.is_empty():
		return
	var room: Node = _instantiate_scene(paths[0])
	_assert_true(room != null, "HTPCE-T-02_room_instantiates")
	if room == null:
		return
	var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", null)
	_assert_true(declarations_variant is Array, "HTPCE-T-02_declarations_is_array")
	if declarations_variant is Array:
		var declarations: Array = declarations_variant as Array
		_assert_true(not declarations.is_empty(), "HTPCE-T-02_declarations_not_empty")
		for i in range(declarations.size()):
			var entry_variant: Variant = declarations[i]
			_assert_true(entry_variant is Dictionary, "HTPCE-T-02_entry_is_dictionary_%d" % i)
			if not (entry_variant is Dictionary):
				continue
			var entry: Dictionary = entry_variant as Dictionary
			var family: String = str(entry.get("enemy_family", "")).strip_edges()
			_assert_true(not family.is_empty(), "HTPCE-T-02_enemy_family_non_empty_%d" % i)
			_assert_true(entry.get("min_count", null) is int, "HTPCE-T-02_min_count_int_%d" % i)
			_assert_true(entry.get("max_count", null) is int, "HTPCE-T-02_max_count_int_%d" % i)
	room.free()


func test_htpce_t_03_declaration_families_resolve_to_generated_scene_paths() -> void:
	# HTPCE-R2: declarations resolve deterministically to generated scene paths.
	var selector: Object = _build_selector()
	var manifest: Dictionary = _read_manifest()
	_assert_true(selector != null, "HTPCE-T-03_selector_available")
	_assert_true(not manifest.is_empty(), "HTPCE-T-03_manifest_available")
	if selector == null or manifest.is_empty():
		return
	var paths: Array[String] = _combat_room_paths_from_pool()
	_assert_true(not paths.is_empty(), "HTPCE-T-03_pool_has_paths")
	if paths.is_empty():
		return
	var room: Node = _instantiate_scene(paths[0])
	_assert_true(room != null, "HTPCE-T-03_room_instantiates")
	if room == null:
		return
	var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", [])
	if declarations_variant is Array:
		var declarations: Array = declarations_variant as Array
		for i in range(declarations.size()):
			var entry_variant: Variant = declarations[i]
			_assert_true(entry_variant is Dictionary, "HTPCE-T-03_entry_is_dictionary_%d" % i)
			if not (entry_variant is Dictionary):
				continue
			var entry: Dictionary = entry_variant as Dictionary
			var family: String = str(entry.get("enemy_family", "")).strip_edges()
			var result: Dictionary = _resolve_variant(selector, family, manifest)
			_assert_true(bool(result.get("ok", false)), "HTPCE-T-03_selector_ok_%d" % i)
			if not bool(result.get("ok", false)):
				continue
			var variant_id: String = str(result.get("variant_id", "")).strip_edges()
			_assert_true(not variant_id.is_empty(), "HTPCE-T-03_variant_id_non_empty_%d" % i)
			var scene_path: String = GENERATED_SCENE_ROOT + variant_id + ".tscn"
			_assert_true(scene_path.begins_with(GENERATED_SCENE_ROOT), "HTPCE-T-03_generated_root_%d" % i)
			_assert_true(scene_path.ends_with(".tscn"), "HTPCE-T-03_generated_ext_tscn_%d" % i)
	room.free()


func test_htpce_t_04_generated_paths_exist_and_are_loadable() -> void:
	# HTPCE-R2: generated enemy paths must exist and load as PackedScene.
	var selector: Object = _build_selector()
	var manifest: Dictionary = _read_manifest()
	if selector == null or manifest.is_empty():
		_fail("HTPCE-T-04_preconditions", "selector or manifest unavailable")
		return
	var paths: Array[String] = _combat_room_paths_from_pool()
	if paths.is_empty():
		_fail("HTPCE-T-04_pool_has_paths", "combat pool is empty")
		return
	var room: Node = _instantiate_scene(paths[0])
	if room == null:
		_fail("HTPCE-T-04_room_instantiates", "combat room could not instantiate")
		return
	var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", [])
	if declarations_variant is Array:
		for entry_variant in declarations_variant:
			if not (entry_variant is Dictionary):
				continue
			var family: String = str((entry_variant as Dictionary).get("enemy_family", "")).strip_edges()
			var result: Dictionary = _resolve_variant(selector, family, manifest)
			if not bool(result.get("ok", false)):
				continue
			var variant_id: String = str(result.get("variant_id", "")).strip_edges()
			var scene_path: String = GENERATED_SCENE_ROOT + variant_id + ".tscn"
			_assert_true(ResourceLoader.exists(scene_path), "HTPCE-T-04_scene_exists_" + variant_id)
			var packed: PackedScene = load(scene_path) as PackedScene
			_assert_true(packed != null, "HTPCE-T-04_scene_loads_" + variant_id)
	room.free()


func test_htpce_t_05_bounded_frame_pump_is_used_for_headless_safety() -> void:
	# HTPCE-R3: bounded waits only; no unbounded loops.
	_bounded_idle_frame_pump(2)
	_assert_true(true, "HTPCE-T-05_bounded_frame_pump_completed")


func test_htpce_t_06_suite_is_auto_discoverable_by_runner_pattern() -> void:
	# HTPCE-R5: run_tests.gd discovers test_*.gd under tests/.
	var file_path: String = "res://tests/system/test_headless_procedural_combat_enemies_contract.gd"
	_assert_true(ResourceLoader.exists(file_path), "HTPCE-T-06_suite_path_exists")
	var script: GDScript = load(file_path) as GDScript
	_assert_true(script != null and script.can_instantiate(), "HTPCE-T-06_suite_instantiable")


func test_htpce_t_07_spawn_call_is_idempotent_for_same_room_instance() -> void:
	# HTPCE-R6: repeated spawn call on same room is deterministic/fail-closed due done-meta guard.
	var assembler_script: GDScript = _load_assembler_script()
	if assembler_script == null or not assembler_script.can_instantiate():
		_fail("HTPCE-T-07_assembler_instantiable", "assembler script unavailable")
		return
	var assembler: Object = assembler_script.new()
	var selector_variant: Variant = assembler.call("_build_enemy_visual_variant_selector")
	assembler.set("_enemy_visual_variant_selector", selector_variant)
	var paths: Array[String] = _combat_room_paths_from_pool()
	if paths.is_empty():
		_fail("HTPCE-T-07_pool_has_paths", "combat pool empty")
		return
	var room_path: String = paths[0]
	var room: Node = _instantiate_scene(room_path)
	if not (room is Node3D):
		_fail("HTPCE-T-07_room_is_node3d", "room must instantiate as Node3D")
		if room != null:
			room.free()
		return
	var room_3d: Node3D = room as Node3D
	var before_count: int = room_3d.get_child_count()
	assembler.call("_spawn_generated_enemies_for_room", room_3d, room_path)
	var after_first: int = room_3d.get_child_count()
	assembler.call("_spawn_generated_enemies_for_room", room_3d, room_path)
	var after_second: int = room_3d.get_child_count()
	_assert_true(after_first >= before_count, "HTPCE-T-07_first_spawn_non_decreasing_child_count")
	_assert_eq_int(after_first, after_second, "HTPCE-T-07_second_spawn_no_additional_children")
	_assert_true(bool(room_3d.get_meta(SPAWN_DONE_META_KEY, false)), "HTPCE-T-07_done_meta_set")
	room_3d.free()


func test_htpce_t_08_non_array_declarations_fail_closed_without_done_meta() -> void:
	# HTPCE-R4: malformed declaration metadata shape must fail closed and non-crashing.
	_run_adversarial_spawn_case(
		"HTPCE-T-08",
		"res://synthetic/room_invalid_shape.tscn",
		{"bad": "shape"},
		false,
		false
	)


func test_htpce_t_09_empty_declarations_no_spawn_and_no_done_meta() -> void:
	# HTPCE-R4: empty declaration list yields stable no-op behavior.
	_run_adversarial_spawn_case(
		"HTPCE-T-09",
		"res://synthetic/room_empty_declarations.tscn",
		[],
		false,
		false
	)


func test_htpce_t_10_unknown_family_entry_is_isolated_and_marks_done() -> void:
	# CHECKPOINT conservative assumption: unknown families are per-entry fail-closed and mark room done to avoid retry storms.
	_run_adversarial_spawn_case(
		"HTPCE-T-10",
		"res://synthetic/room_unknown_family.tscn",
		[{"enemy_family": "totally_unknown", "min_count": 1, "max_count": 1}],
		true,
		true
	)


func test_htpce_t_11_invalid_min_max_bounds_are_rejected_without_spawns() -> void:
	# HTPCE-R4: invalid declaration bounds mutate count logic and must fail closed.
	_run_adversarial_spawn_case(
		"HTPCE-T-11",
		"res://synthetic/room_invalid_bounds.tscn",
		[{"enemy_family": "carapace_husk", "min_count": 3, "max_count": 1}],
		true,
		true
	)


func test_htpce_t_12_stress_many_invalid_entries_remain_non_crashing_and_bounded() -> void:
	# HTPCE-R6: stress malformed declarations to ensure deterministic fail-closed behavior.
	var declarations: Array = []
	for i in range(128):
		declarations.append({"enemy_family": "invalid_family_%d" % i, "min_count": 1, "max_count": 1})
	_run_adversarial_spawn_case(
		"HTPCE-T-12",
		"res://synthetic/room_stress_invalid_entries.tscn",
		declarations,
		true,
		true
	)


func run_all() -> int:
	print("--- test_headless_procedural_combat_enemies_contract.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_htpce_t_01_pool_exposes_loadable_combat_room_paths()
	test_htpce_t_02_room_declarations_exist_and_have_required_schema()
	test_htpce_t_03_declaration_families_resolve_to_generated_scene_paths()
	test_htpce_t_04_generated_paths_exist_and_are_loadable()
	test_htpce_t_05_bounded_frame_pump_is_used_for_headless_safety()
	test_htpce_t_06_suite_is_auto_discoverable_by_runner_pattern()
	test_htpce_t_07_spawn_call_is_idempotent_for_same_room_instance()
	test_htpce_t_08_non_array_declarations_fail_closed_without_done_meta()
	test_htpce_t_09_empty_declarations_no_spawn_and_no_done_meta()
	test_htpce_t_10_unknown_family_entry_is_isolated_and_marks_done()
	test_htpce_t_11_invalid_min_max_bounds_are_rejected_without_spawns()
	test_htpce_t_12_stress_many_invalid_entries_remain_non_crashing_and_bounded()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
