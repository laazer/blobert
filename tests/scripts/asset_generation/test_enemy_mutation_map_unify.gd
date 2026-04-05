#
# test_enemy_mutation_map_unify.gd
#
# Behavioral contracts for single-source MUTATION_BY_FAMILY.
# Spec: project_board/maintenance/in_progress/enemy_mutation_map_unify.md (EMU-*)
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _MAP_PATH := "res://scripts/asset_generation/enemy_mutation_map.gd"
const _GEN_PATH := "res://scripts/asset_generation/generate_enemy_scenes.gd"
const _LOAD_PATH := "res://scripts/asset_generation/load_assets.gd"
const _AG_ROOT := "res://scripts/asset_generation"

const _PRELOAD_SNIPPET := "const EnemyMutationMap = preload(\"res://scripts/asset_generation/enemy_mutation_map.gd\")"


func _collect_gd_files(dir_path: String, results: Array[String]) -> void:
	var dir := DirAccess.open(dir_path)
	if dir == null:
		return
	dir.list_dir_begin()
	while true:
		var entry := dir.get_next()
		if entry == "":
			break
		if dir.current_is_dir():
			if not entry.begins_with("."):
				_collect_gd_files(dir_path.path_join(entry), results)
		elif entry.ends_with(".gd"):
			results.append(dir_path.path_join(entry))
	dir.list_dir_end()


func _count_mutation_by_family_literal_sites() -> Dictionary:
	var paths: Array[String] = []
	_collect_gd_files(_AG_ROOT, paths)
	var hit_paths: Array[String] = []
	for fp in paths:
		var text := FileAccess.get_file_as_string(fp)
		if text.contains("const MUTATION_BY_FAMILY := {"):
			hit_paths.append(fp)
	return {"count": hit_paths.size(), "paths": hit_paths}


func _canonical_mutation_map() -> Dictionary:
	if not ResourceLoader.exists(_MAP_PATH):
		return {}
	var script: GDScript = load(_MAP_PATH) as GDScript
	if script == null:
		return {}
	var cmap: Dictionary = script.get_script_constant_map()
	if not cmap.has("MUTATION_BY_FAMILY"):
		return {}
	var d: Variant = cmap["MUTATION_BY_FAMILY"]
	if typeof(d) != TYPE_DICTIONARY:
		return {}
	return d


func test_emu_mod_1_canonical_file_exists() -> void:
	_assert_true(
		ResourceLoader.exists(_MAP_PATH),
		"EMU-MOD-1_file_exists",
		"enemy_mutation_map.gd must exist at %s" % _MAP_PATH
	)


func test_emu_mod_1_exports_dictionary_constant() -> void:
	if not ResourceLoader.exists(_MAP_PATH):
		_fail("EMU-MOD-1_exports", "enemy_mutation_map.gd missing (EMU-MOD-1)")
		return
	var script: GDScript = load(_MAP_PATH) as GDScript
	if script == null:
		_fail("EMU-MOD-1_exports", "failed to load enemy_mutation_map.gd")
		return
	var cmap: Dictionary = script.get_script_constant_map()
	if not cmap.has("MUTATION_BY_FAMILY"):
		_fail("EMU-MOD-1_exports", "MUTATION_BY_FAMILY constant missing on canonical script")
		return
	var d: Variant = cmap["MUTATION_BY_FAMILY"]
	if typeof(d) != TYPE_DICTIONARY:
		_fail("EMU-MOD-1_exports", "MUTATION_BY_FAMILY is not a Dictionary")
		return
	_assert_true(
		(d as Dictionary).size() > 0,
		"EMU-MOD-1_nonempty",
		"MUTATION_BY_FAMILY must be non-empty"
	)


func test_emu_mod_1_representative_entries() -> void:
	var d := _canonical_mutation_map()
	if d.is_empty():
		_fail("EMU-MOD-1_entries", "canonical map unavailable (missing script or constant)")
		return
	_assert_true(
		d.get("mutation_clown", "") == "random",
		"EMU-MOD-1_mutation_clown",
		"mutation_clown must map to random; got %s" % str(d.get("mutation_clown", "<missing>"))
	)
	_assert_true(
		d.get("acid_spitter", "") == "acid",
		"EMU-MOD-1_acid_spitter",
		"acid_spitter must map to acid; got %s" % str(d.get("acid_spitter", "<missing>"))
	)


func test_emu_sem_1_unknown_family_lookup() -> void:
	var d := _canonical_mutation_map()
	if d.is_empty():
		_fail("EMU-SEM-1", "canonical map unavailable")
		return
	_assert_true(
		d.get("totally_fake_family", "unknown") == "unknown",
		"EMU-SEM-1_unknown_family",
		"absent key must resolve via .get(..., \"unknown\")"
	)


func test_emu_qa_1_single_dict_literal_under_asset_generation() -> void:
	var info: Dictionary = _count_mutation_by_family_literal_sites()
	var count: int = int(info.get("count", -1))
	var hit_paths: Array = info.get("paths", []) as Array
	_assert_true(
		count == 1,
		"EMU-QA-1_single_literal",
		"exactly one const MUTATION_BY_FAMILY := { under scripts/asset_generation/; got %d at %s"
		% [count, str(hit_paths)]
	)
	if count == 1 and hit_paths.size() == 1:
		var p: String = str(hit_paths[0])
		_assert_true(
			p.ends_with("enemy_mutation_map.gd"),
			"EMU-QA-1_literal_location",
			"literal must live in enemy_mutation_map.gd; got %s" % p
		)


func test_emu_con_1_consumers_contain_preload_snippet() -> void:
	var gen := FileAccess.get_file_as_string(_GEN_PATH)
	var lod := FileAccess.get_file_as_string(_LOAD_PATH)
	_assert_true(
		gen.contains(_PRELOAD_SNIPPET),
		"EMU-CON-1_preload_generate",
		"generate_enemy_scenes.gd must include EnemyMutationMap preload line"
	)
	_assert_true(
		lod.contains(_PRELOAD_SNIPPET),
		"EMU-CON-1_preload_load_assets",
		"load_assets.gd must include EnemyMutationMap preload line"
	)


func test_emu_con_1_consumers_have_no_local_mutation_dict_literal() -> void:
	var gen := FileAccess.get_file_as_string(_GEN_PATH)
	var lod := FileAccess.get_file_as_string(_LOAD_PATH)
	_assert_true(
		not gen.contains("const MUTATION_BY_FAMILY := {"),
		"EMU-CON-1_no_local_dict_generate",
		"generate_enemy_scenes.gd must not declare a local MUTATION_BY_FAMILY dict literal"
	)
	_assert_true(
		not lod.contains("const MUTATION_BY_FAMILY := {"),
		"EMU-CON-1_no_local_dict_load_assets",
		"load_assets.gd must not declare a local MUTATION_BY_FAMILY dict literal"
	)


func test_emu_con_1_consumers_resolve_same_dictionary_as_canonical() -> void:
	var canonical := _canonical_mutation_map()
	if canonical.is_empty():
		_fail("EMU-SSOT_ref", "canonical map unavailable")
		return

	var gen_script: GDScript = load(_GEN_PATH) as GDScript
	var load_script: GDScript = load(_LOAD_PATH) as GDScript
	if gen_script == null or load_script == null:
		_fail("EMU-SSOT_ref", "failed to load consumer scripts")
		return

	var gen_c: Dictionary = gen_script.get_script_constant_map()
	var load_c: Dictionary = load_script.get_script_constant_map()
	if not gen_c.has("EnemyMutationMap"):
		_fail("EMU-SSOT_ref_generate", "generate_enemy_scenes.gd missing EnemyMutationMap preload const")
		return
	if not load_c.has("EnemyMutationMap"):
		_fail("EMU-SSOT_ref_load_assets", "load_assets.gd missing EnemyMutationMap preload const")
		return

	var gen_sub: GDScript = gen_c["EnemyMutationMap"] as GDScript
	var load_sub: GDScript = load_c["EnemyMutationMap"] as GDScript
	if gen_sub == null or load_sub == null:
		_fail("EMU-SSOT_ref_type", "EnemyMutationMap const must be a GDScript")
		return

	var gen_map: Variant = gen_sub.get_script_constant_map().get("MUTATION_BY_FAMILY", {})
	var load_map: Variant = load_sub.get_script_constant_map().get("MUTATION_BY_FAMILY", {})
	if typeof(gen_map) != TYPE_DICTIONARY or typeof(load_map) != TYPE_DICTIONARY:
		_fail("EMU-SSOT_ref_maps", "MUTATION_BY_FAMILY missing on EnemyMutationMap script")
		return
	var gdict: Dictionary = gen_map
	var ldict: Dictionary = load_map
	if gdict.is_empty() or ldict.is_empty():
		_fail("EMU-SSOT_ref_maps", "Could not resolve MUTATION_BY_FAMILY through EnemyMutationMap")
		return

	_assert_true(
		is_same(gdict, canonical),
		"EMU-SSOT_generate_same_ref",
		"generate_enemy_scenes must use canonical MUTATION_BY_FAMILY dictionary reference"
	)
	_assert_true(
		is_same(ldict, canonical),
		"EMU-SSOT_load_assets_same_ref",
		"load_assets must use canonical MUTATION_BY_FAMILY dictionary reference"
	)
	_assert_true(
		is_same(gdict, ldict),
		"EMU-SSOT_both_consumers_same_ref",
		"both consumers must share the same dictionary instance"
	)


func run_all() -> int:
	print("--- test_enemy_mutation_map_unify.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_emu_mod_1_canonical_file_exists()
	test_emu_mod_1_exports_dictionary_constant()
	test_emu_mod_1_representative_entries()
	test_emu_sem_1_unknown_family_lookup()
	test_emu_qa_1_single_dict_literal_under_asset_generation()
	test_emu_con_1_consumers_contain_preload_snippet()
	test_emu_con_1_consumers_have_no_local_mutation_dict_literal()
	test_emu_con_1_consumers_resolve_same_dictionary_as_canonical()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
