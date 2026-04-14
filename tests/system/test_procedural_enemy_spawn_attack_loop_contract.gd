#
# test_procedural_enemy_spawn_attack_loop_contract.gd
#
# Primary behavioral contract tests for M10-01 procedural enemy spawn + attack loop.
# Spec: project_board/specs/procedural_enemy_spawn_attack_loop_spec.md
# Ticket: project_board/10_milestone_10_procedural_enemies_in_level/in_progress/01_spec_procedural_enemy_spawn_attack_loop.md
#
# Requirement traceability:
# - R1 -> PESAL-T-01..05
# - R2 -> PESAL-T-06..09
# - R3 -> PESAL-T-10..12
# - R4 -> PESAL-T-13..16
# - R5 -> PESAL-T-17..19
# - R6 -> PESAL-T-20..22
#

extends "res://tests/utils/test_utils.gd"

const _VisualSelectorTest = preload("res://tests/scripts/system/test_runtime_enemy_visual_variant_selector.gd")
const _StubRng = _VisualSelectorTest._StubRng

const ASSEMBLER_PATH: String = "res://scripts/system/run_scene_assembler.gd"
const ROOM_CHAIN_GENERATOR_PATH: String = "res://scripts/system/room_chain_generator.gd"
const SELECTOR_PATH: String = "res://scripts/system/enemy_visual_variant_selector.gd"
const ROOM_COMBAT_01_PATH: String = "res://scenes/rooms/room_combat_01.tscn"
const ROOM_COMBAT_02_PATH: String = "res://scenes/rooms/room_combat_02.tscn"
const MODEL_REGISTRY_JSON_PATH: String = "res://asset_generation/python/model_registry.json"
const GENERATED_ENEMY_SCENE_DIR: String = "res://scenes/enemies/generated/"
const ENEMY_SPAWN_PREFIX: String = "EnemySpawn_"
const ENEMY_SPAWN_Z_TOLERANCE: float = 0.01
const SELECTOR_STRESS_ITERATIONS: int = 64
const ATTACK_SCRIPT_PATHS: Array[String] = [
	"res://scripts/enemy/acid_spitter_ranged_attack.gd",
	"res://scripts/enemy/adhesion_bug_lunge_attack.gd",
	"res://scripts/enemy/carapace_husk_attack.gd",
	"res://scripts/enemy/claw_crawler_attack.gd",
]

var _pass_count: int = 0
var _fail_count: int = 0


func _load_script_source(path: String) -> String:
	if not ResourceLoader.exists(path):
		return ""
	var script_res: GDScript = load(path) as GDScript
	if script_res == null:
		return ""
	return script_res.source_code


func _instantiate_scene(path: String) -> Node:
	if not ResourceLoader.exists(path):
		return null
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func _read_json(path: String) -> Dictionary:
	if not FileAccess.file_exists(path):
		return {}
	var file: FileAccess = FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if not (parsed is Dictionary):
		return {}
	return parsed as Dictionary


func _selector_instance() -> Object:
	if not ResourceLoader.exists(SELECTOR_PATH):
		return null
	var gds: GDScript = load(SELECTOR_PATH) as GDScript
	if gds == null or not gds.can_instantiate():
		return null
	return gds.new()


func _call_selector(inst: Object, family: String, manifest: Dictionary, rng: Variant = null) -> Dictionary:
	if inst == null or not inst.has_method("resolve_spawn_visual_variant"):
		return {}
	var out: Variant = inst.call("resolve_spawn_visual_variant", family, manifest, rng)
	if not (out is Dictionary):
		return {}
	return out as Dictionary


func _combat_room_paths() -> Array[String]:
	return [ROOM_COMBAT_01_PATH, ROOM_COMBAT_02_PATH]


func _scene_path_for_variant_id(variant_id: String) -> String:
	return GENERATED_ENEMY_SCENE_DIR + variant_id + ".tscn"


func _extract_marker3d_spawn_indices(room: Node) -> Array[int]:
	var indices: Array[int] = []
	if room == null:
		return indices
	for child in room.get_children():
		if not (child is Marker3D):
			continue
		var marker: Marker3D = child as Marker3D
		if not marker.name.begins_with(ENEMY_SPAWN_PREFIX):
			continue
		var suffix: String = marker.name.substr(ENEMY_SPAWN_PREFIX.length())
		if suffix.is_valid_int():
			indices.append(int(suffix))
	indices.sort()
	return indices


func _deep_copy_dict(input: Dictionary) -> Dictionary:
	return input.duplicate(true)


func test_pesal_t_01_combat_rooms_are_declared_by_run_scene_assembler_pool() -> void:
	var src: String = _load_script_source(ASSEMBLER_PATH)
	_assert_true(not src.is_empty(), "PESAL-T-01_assembler_script_loads", "run_scene_assembler.gd missing")
	_assert_true(src.find("room_combat_01.tscn") >= 0, "PESAL-T-01_pool_contains_room_combat_01")
	_assert_true(src.find("room_combat_02.tscn") >= 0, "PESAL-T-01_pool_contains_room_combat_02")


func test_pesal_t_02_room_local_spawn_declaration_contract_exists() -> void:
	# CHECKPOINT assumption (strictest defensible): room-local declaration key is "enemy_spawn_declarations".
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-02_room_instantiates_" + room_path, "could not instantiate room")
			continue
		var has_meta_contract: bool = room.has_meta("enemy_spawn_declarations")
		_assert_true(
			has_meta_contract,
			"PESAL-T-02_room_has_enemy_spawn_declarations_meta_" + room_path,
			"combat room must expose room-local enemy declaration contract"
		)
		room.free()


func test_pesal_t_03_visual_selection_filters_in_use_non_draft() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-03_selector_instantiates", "selector unavailable")
		return
	var manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	var result: Dictionary = _call_selector(selector, "carapace_husk", manifest, _StubRng.new([0]))
	if result.is_empty():
		_fail("PESAL-T-03_selector_returns_dictionary", "selector returned empty/non-dictionary")
		return
	_assert_true(bool(result.get("ok", false)), "PESAL-T-03_selector_success_for_family")
	_assert_eq_string("carapace_husk_animated_00", str(result.get("variant_id", "")), "PESAL-T-03_non_draft_in_use_variant_selected")


func test_pesal_t_04_zero_eligible_variants_fail_closed() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-04_selector_instantiates", "selector unavailable")
		return
	var manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	var result: Dictionary = _call_selector(selector, "spider", manifest, _StubRng.new([0]))
	if result.is_empty():
		_fail("PESAL-T-04_selector_returns_dictionary", "selector returned empty/non-dictionary")
		return
	_assert_false(bool(result.get("ok", true)), "PESAL-T-04_fail_closed")
	_assert_eq_string("", str(result.get("path", "")), "PESAL-T-04_no_path_on_failure")
	_assert_true(not str(result.get("error", "")).is_empty(), "PESAL-T-04_has_failure_reason")


func test_pesal_t_05_no_hardcoded_enemy_instances_in_combat_rooms() -> void:
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-05_room_instantiates_" + room_path, "could not instantiate room")
			continue
		for child in room.get_children():
			var child_name: String = str(child.name)
			var is_spawn_anchor: bool = child_name.begins_with(ENEMY_SPAWN_PREFIX)
			var is_entry_or_exit: bool = child_name == "Entry" or child_name == "Exit"
			var looks_like_embedded_enemy: bool = child_name.begins_with("Enemy") and not is_spawn_anchor and not is_entry_or_exit
			_assert_false(
				looks_like_embedded_enemy,
				"PESAL-T-05_no_embedded_enemy_child_" + room_path + "_" + child_name,
				"combat room must not carry embedded authoritative enemy nodes; procedural spawn is canonical"
			)
		room.free()


func test_pesal_t_06_enemy_spawn_anchor_indices_contiguous() -> void:
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-06_room_instantiates_" + room_path, "could not instantiate room")
			continue
		var indices: Array[int] = _extract_marker3d_spawn_indices(room)
		for i in range(indices.size()):
			var expected: int = i + 1
			_assert_eq_int(expected, indices[i], "PESAL-T-06_contiguous_index_" + room_path + "_" + str(expected))
		room.free()


func test_pesal_t_07_enemy_spawn_anchor_z_is_zero_when_present() -> void:
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-07_room_instantiates_" + room_path, "could not instantiate room")
			continue
		for child in room.get_children():
			if not (child is Marker3D):
				continue
			var marker: Marker3D = child as Marker3D
			if not marker.name.begins_with(ENEMY_SPAWN_PREFIX):
				continue
			_assert_true(
				absf(marker.position.z) <= ENEMY_SPAWN_Z_TOLERANCE,
				"PESAL-T-07_anchor_z_zero_" + room_path + "_" + marker.name,
				"EnemySpawn marker z must be 0.0 (+/-%.2f)" % ENEMY_SPAWN_Z_TOLERANCE
			)
		room.free()


func test_pesal_t_08_fallback_midpoint_contract_is_wired_in_assembler() -> void:
	var src: String = _load_script_source(ASSEMBLER_PATH)
	_assert_true(src.find(ENEMY_SPAWN_PREFIX) >= 0, "PESAL-T-08_assembler_references_enemy_spawn_anchor_prefix")
	_assert_true(src.find("(Entry.x + Exit.x)") >= 0 or src.find("Entry") >= 0 and src.find("Exit") >= 0, "PESAL-T-08_assembler_references_entry_exit_for_fallback")


func test_pesal_t_09_entry_exit_reserved_not_spawn_prefix() -> void:
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-09_room_instantiates_" + room_path, "could not instantiate room")
			continue
		_assert_true(room.has_node("Entry"), "PESAL-T-09_has_entry_" + room_path)
		_assert_true(room.has_node("Exit"), "PESAL-T-09_has_exit_" + room_path)
		room.free()


func test_pesal_t_10_room_chain_generator_remains_enemy_spawn_free() -> void:
	var src: String = _load_script_source(ROOM_CHAIN_GENERATOR_PATH)
	_assert_true(not src.is_empty(), "PESAL-T-10_room_chain_generator_loads")
	_assert_true(src.find(ENEMY_SPAWN_PREFIX) < 0, "PESAL-T-10_no_enemy_spawn_anchor_logic_in_generator")
	_assert_true(src.find("resolve_spawn_visual_variant") < 0, "PESAL-T-10_no_visual_variant_selection_in_generator")
	_assert_true(src.find("EnemyInfection3D") < 0, "PESAL-T-10_no_enemy_node_coupling_in_generator")


func test_pesal_t_11_assembler_keeps_canonical_sequence_contract() -> void:
	var src: String = _load_script_source(ASSEMBLER_PATH)
	_assert_true(src.find("\"intro\"") >= 0, "PESAL-T-11_sequence_has_intro")
	_assert_true(src.find("\"combat\", \"combat\"") >= 0, "PESAL-T-11_sequence_has_two_combat_slots")
	_assert_true(src.find("\"mutation_tease\"") >= 0, "PESAL-T-11_sequence_has_mutation_tease")
	_assert_true(src.find("\"boss\"") >= 0, "PESAL-T-11_sequence_has_boss")


func test_pesal_t_12_generated_scene_existence_validation_seam_present() -> void:
	var src: String = _load_script_source(ASSEMBLER_PATH)
	_assert_true(src.find("scenes/enemies/generated/") >= 0, "PESAL-T-12_assembler_references_generated_scene_directory")
	_assert_true(src.find("ResourceLoader.exists") >= 0, "PESAL-T-12_assembler_checks_generated_scene_existence")


func test_pesal_t_13_attack_defaults_match_family_contract() -> void:
	var acid_script: GDScript = load("res://scripts/enemy/acid_spitter_ranged_attack.gd") as GDScript
	var adhesion_script: GDScript = load("res://scripts/enemy/adhesion_bug_lunge_attack.gd") as GDScript
	var carapace_script: GDScript = load("res://scripts/enemy/carapace_husk_attack.gd") as GDScript
	var claw_script: GDScript = load("res://scripts/enemy/claw_crawler_attack.gd") as GDScript
	_assert_true(acid_script != null, "PESAL-T-13_acid_script_loads")
	_assert_true(adhesion_script != null, "PESAL-T-13_adhesion_script_loads")
	_assert_true(carapace_script != null, "PESAL-T-13_carapace_script_loads")
	_assert_true(claw_script != null, "PESAL-T-13_claw_script_loads")
	if acid_script == null or adhesion_script == null or carapace_script == null or claw_script == null:
		return
	var acid: Object = acid_script.new()
	var adhesion: Object = adhesion_script.new()
	var carapace: Object = carapace_script.new()
	var claw: Object = claw_script.new()
	_assert_eq_float(8.0, float(acid.get("attack_range")), "PESAL-T-13_acid_attack_range_default")
	_assert_eq_float(3.0, float(acid.get("cooldown_seconds")), "PESAL-T-13_acid_cooldown_default")
	_assert_eq_float(3.0, float(adhesion.get("attack_range")), "PESAL-T-13_adhesion_attack_range_default")
	_assert_eq_float(2.0, float(adhesion.get("cooldown_seconds")), "PESAL-T-13_adhesion_cooldown_default")
	_assert_eq_float(6.0, float(carapace.get("attack_range")), "PESAL-T-13_carapace_attack_range_default")
	_assert_eq_float(4.0, float(carapace.get("cooldown_seconds")), "PESAL-T-13_carapace_cooldown_default")
	_assert_eq_float(2.0, float(claw.get("attack_range")), "PESAL-T-13_claw_attack_range_default")
	_assert_eq_float(1.2, float(claw.get("cooldown_seconds")), "PESAL-T-13_claw_cooldown_default")


func test_pesal_t_14_attack_scripts_require_player_group_and_dead_gate() -> void:
	for script_path in ATTACK_SCRIPT_PATHS:
		var src: String = _load_script_source(script_path)
		_assert_true(src.find("get_first_node_in_group(\"player\")") >= 0, "PESAL-T-14_player_group_lookup_" + script_path)
		_assert_true(src.find("== \"dead\"") >= 0, "PESAL-T-14_dead_state_gate_" + script_path)


func test_pesal_t_15_weakened_and_infected_do_not_auto_block_attack() -> void:
	for script_path in ATTACK_SCRIPT_PATHS:
		var src: String = _load_script_source(script_path)
		_assert_true(src.find("\"weakened\"") < 0, "PESAL-T-15_no_weakened_block_" + script_path)
		_assert_true(src.find("\"infected\"") < 0, "PESAL-T-15_no_infected_block_" + script_path)


func test_pesal_t_16_enemy_state_machine_has_canonical_lowercase_states() -> void:
	var src: String = _load_script_source("res://scripts/enemy/enemy_state_machine.gd")
	_assert_true(src.find("STATE_WEAKENED: String = \"weakened\"") >= 0, "PESAL-T-16_state_weakened_lowercase")
	_assert_true(src.find("STATE_INFECTED: String = \"infected\"") >= 0, "PESAL-T-16_state_infected_lowercase")
	_assert_true(src.find("STATE_DEAD: String = \"dead\"") >= 0, "PESAL-T-16_state_dead_lowercase")


func test_pesal_t_17_each_combat_family_has_eligible_generated_scene() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-17_selector_instantiates", "selector unavailable")
		return
	var manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	for family in ["acid_spitter", "adhesion_bug", "carapace_husk", "claw_crawler"]:
		var out: Dictionary = _call_selector(selector, family, manifest, _StubRng.new([0]))
		if out.is_empty():
			_fail("PESAL-T-17_selector_result_dict_" + family, "empty/non-dictionary output")
			continue
		_assert_true(bool(out.get("ok", false)), "PESAL-T-17_selector_ok_" + family, "family must resolve to at least one eligible variant")
		var variant_id: String = str(out.get("variant_id", ""))
		var scene_path: String = _scene_path_for_variant_id(variant_id)
		_assert_true(ResourceLoader.exists(scene_path), "PESAL-T-17_generated_scene_exists_" + family, "missing generated scene: " + scene_path)


func test_pesal_t_18_anchor_discovery_or_fallback_is_testable_headless() -> void:
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-18_room_instantiates_" + room_path, "could not instantiate room")
			continue
		var anchors: Array[int] = _extract_marker3d_spawn_indices(room)
		var has_entry: bool = room.has_node("Entry")
		var has_exit: bool = room.has_node("Exit")
		_assert_true(
			(not anchors.is_empty()) or (has_entry and has_exit),
			"PESAL-T-18_anchor_or_fallback_preconditions_" + room_path,
			"room must have EnemySpawn_* anchors or Entry/Exit fallback inputs"
		)
		room.free()


func test_pesal_t_19_dead_state_attack_suppression_is_encoded_per_family() -> void:
	test_pesal_t_14_attack_scripts_require_player_group_and_dead_gate()


func test_pesal_t_20_selector_with_seeded_rng_is_deterministic() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-20_selector_instantiates", "selector unavailable")
		return
	var manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	var rng_a := _StubRng.new([0, 0, 0, 0])
	var rng_b := _StubRng.new([0, 0, 0, 0])
	var seq_a: PackedStringArray = []
	var seq_b: PackedStringArray = []
	for _i in range(4):
		var out_a: Dictionary = _call_selector(selector, "carapace_husk", manifest, rng_a)
		var out_b: Dictionary = _call_selector(selector, "carapace_husk", manifest, rng_b)
		seq_a.append(str(out_a.get("variant_id", "")))
		seq_b.append(str(out_b.get("variant_id", "")))
	_assert_eq(seq_a, seq_b, "PESAL-T-20_same_rng_stream_same_sequence")


func test_pesal_t_21_missing_family_fails_without_crash() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-21_selector_instantiates", "selector unavailable")
		return
	var manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	var out: Dictionary = _call_selector(selector, "nonexistent_family", manifest, _StubRng.new([0]))
	_assert_false(bool(out.get("ok", true)), "PESAL-T-21_fail_closed_missing_family")
	_assert_true(not str(out.get("error", "")).is_empty(), "PESAL-T-21_error_present_missing_family")


func test_pesal_t_22_spawn_failure_log_context_seam_present() -> void:
	var src: String = _load_script_source(ASSEMBLER_PATH)
	_assert_true(src.find("room") >= 0, "PESAL-T-22_logging_mentions_room_context")
	_assert_true(src.find("family") >= 0, "PESAL-T-22_logging_mentions_family_context")
	_assert_true(src.find("error") >= 0 or src.find("warning") >= 0, "PESAL-T-22_logging_mentions_failure_reason")


func test_pesal_t_23_selector_rejects_corrupt_manifest_shapes() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-23_selector_instantiates", "selector unavailable")
		return
	var malformed_inputs: Array[Dictionary] = [
		{},
		{"enemies": []},
		{"enemies": {"carapace_husk": []}},
		{"enemies": {"carapace_husk": {"versions": "not-an-array"}}},
	]
	for idx in range(malformed_inputs.size()):
		var out: Dictionary = _call_selector(selector, "carapace_husk", malformed_inputs[idx], _StubRng.new([0]))
		_assert_false(bool(out.get("ok", true)), "PESAL-T-23_fail_closed_corrupt_manifest_" + str(idx))
		_assert_true(not str(out.get("error", "")).is_empty(), "PESAL-T-23_error_message_corrupt_manifest_" + str(idx))


func test_pesal_t_24_selector_rejects_mutated_version_records() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-24_selector_instantiates", "selector unavailable")
		return
	var base_manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	if base_manifest.is_empty():
		_fail("PESAL-T-24_base_manifest_reads", "model_registry.json missing or invalid")
		return

	var missing_key_variants: Array[String] = ["id", "path", "draft", "in_use"]
	for key_name in missing_key_variants:
		var mutated: Dictionary = _deep_copy_dict(base_manifest)
		var enemies: Dictionary = mutated.get("enemies", {})
		var family_entry: Dictionary = enemies.get("carapace_husk", {})
		var versions: Array = family_entry.get("versions", [])
		if versions.is_empty():
			_fail("PESAL-T-24_versions_available_" + key_name, "carapace_husk versions missing in registry")
			continue
		var first_version: Dictionary = versions[0]
		first_version.erase(key_name)
		versions[0] = first_version
		family_entry["versions"] = versions
		enemies["carapace_husk"] = family_entry
		mutated["enemies"] = enemies
		var out_missing: Dictionary = _call_selector(selector, "carapace_husk", mutated, _StubRng.new([0]))
		_assert_false(bool(out_missing.get("ok", true)), "PESAL-T-24_fail_closed_missing_" + key_name)

	# CHECKPOINT conservative assumption: duplicate variant IDs (even with same path) are invalid and must fail closed.
	var dup_mutated: Dictionary = _deep_copy_dict(base_manifest)
	var dup_enemies: Dictionary = dup_mutated.get("enemies", {})
	var dup_family_entry: Dictionary = dup_enemies.get("carapace_husk", {})
	var dup_versions: Array = dup_family_entry.get("versions", [])
	if dup_versions.size() >= 1:
		var first_copy: Dictionary = (dup_versions[0] as Dictionary).duplicate(true)
		dup_versions.append(first_copy)
		dup_family_entry["versions"] = dup_versions
		dup_enemies["carapace_husk"] = dup_family_entry
		dup_mutated["enemies"] = dup_enemies
		var dup_out: Dictionary = _call_selector(selector, "carapace_husk", dup_mutated, _StubRng.new([0]))
		_assert_false(bool(dup_out.get("ok", true)), "PESAL-T-24_fail_closed_duplicate_variant_id")
		_assert_true(str(dup_out.get("error", "")).find("duplicate") >= 0, "PESAL-T-24_duplicate_variant_reports_duplicate_error")
	else:
		_fail("PESAL-T-24_duplicate_variant_setup", "carapace_husk versions unexpectedly empty")


func test_pesal_t_25_room_declaration_schema_rejects_invalid_bounds() -> void:
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-25_room_instantiates_" + room_path, "could not instantiate room")
			continue
		var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", null)
		if declarations_variant == null:
			_fail("PESAL-T-25_room_has_enemy_spawn_declarations_meta_" + room_path, "missing enemy_spawn_declarations metadata")
			room.free()
			continue
		_assert_true(declarations_variant is Array, "PESAL-T-25_declarations_array_type_" + room_path)
		if declarations_variant is Array:
			var declarations: Array = declarations_variant as Array
			for idx in range(declarations.size()):
				var entry_variant: Variant = declarations[idx]
				_assert_true(entry_variant is Dictionary, "PESAL-T-25_entry_dictionary_" + room_path + "_" + str(idx))
				if not (entry_variant is Dictionary):
					continue
				var entry: Dictionary = entry_variant as Dictionary
				_assert_true(entry.has("enemy_family"), "PESAL-T-25_entry_has_enemy_family_" + room_path + "_" + str(idx))
				_assert_false(entry.has("enemy_id"), "PESAL-T-25_entry_has_no_enemy_id_" + room_path + "_" + str(idx))
				_assert_true(entry.has("min_count"), "PESAL-T-25_entry_has_min_count_" + room_path + "_" + str(idx))
				_assert_true(entry.has("max_count"), "PESAL-T-25_entry_has_max_count_" + room_path + "_" + str(idx))
				var enemy_family: String = str(entry.get("enemy_family", "")).strip_edges()
				_assert_true(not enemy_family.is_empty(), "PESAL-T-25_enemy_family_non_empty_" + room_path + "_" + str(idx))
				var min_count: int = int(entry.get("min_count", -1))
				var max_count: int = int(entry.get("max_count", -1))
				_assert_true(min_count >= 0, "PESAL-T-25_min_count_non_negative_" + room_path + "_" + str(idx))
				_assert_true(max_count >= 0, "PESAL-T-25_max_count_non_negative_" + room_path + "_" + str(idx))
				_assert_true(min_count <= max_count, "PESAL-T-25_min_lte_max_" + room_path + "_" + str(idx))
		room.free()


func test_pesal_t_26_selector_determinism_under_stress_repeated_calls() -> void:
	var selector: Object = _selector_instance()
	if selector == null:
		_fail("PESAL-T-26_selector_instantiates", "selector unavailable")
		return
	var manifest: Dictionary = _read_json(MODEL_REGISTRY_JSON_PATH)
	var rng_a := _StubRng.new([0, 1, 0, 1, 1, 0, 0, 1])
	var rng_b := _StubRng.new([0, 1, 0, 1, 1, 0, 0, 1])
	var seq_a: PackedStringArray = []
	var seq_b: PackedStringArray = []
	for _i in range(SELECTOR_STRESS_ITERATIONS):
		seq_a.append(str(_call_selector(selector, "carapace_husk", manifest, rng_a).get("variant_id", "")))
		seq_b.append(str(_call_selector(selector, "carapace_husk", manifest, rng_b).get("variant_id", "")))
	_assert_eq(
		seq_a,
		seq_b,
		"PESAL-T-26_stress_same_rng_stream_same_%d_call_sequence" % SELECTOR_STRESS_ITERATIONS
	)


func test_pesal_t_27_no_embedded_enemy_nodes_by_type_or_metadata() -> void:
	# Strict PESAL-T-05 hardening:
	# Name-based checks can be bypassed by embedding enemy roots with non-Enemy names.
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-27_room_instantiates_" + room_path, "could not instantiate room")
			continue
		for child in room.get_children():
			var child_name: String = str(child.name)
			var is_spawn_anchor: bool = child_name.begins_with(ENEMY_SPAWN_PREFIX)
			var is_entry_or_exit: bool = child_name == "Entry" or child_name == "Exit"
			if is_spawn_anchor or is_entry_or_exit:
				continue
			var is_enemy_runtime_node: bool = child is EnemyInfection3D or child is EnemyBase
			var carries_enemy_metadata: bool = child.has_meta("enemy_family") or child.has_meta("mutation_drop")
			_assert_false(
				is_enemy_runtime_node or carries_enemy_metadata,
				"PESAL-T-27_no_embedded_enemy_runtime_node_" + room_path + "_" + child_name,
				"combat room must remain procedural-only; embedded enemy runtime nodes/metadata are forbidden"
			)
		room.free()


func test_pesal_t_28_declaration_rejects_enemy_identity_alias_fields() -> void:
	# Arbitration hardening: declaration identity must stay enemy_family-only.
	# These alias keys can silently reintroduce enemy_id-like coupling.
	var forbidden_identity_aliases: Array[String] = [
		"enemyId",
		"enemy_id",
		"enemy_type",
		"enemy_variant_id",
		"enemy_scene_path",
	]
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("PESAL-T-28_room_instantiates_" + room_path, "could not instantiate room")
			continue
		var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", null)
		_assert_true(declarations_variant is Array, "PESAL-T-28_declarations_array_type_" + room_path)
		if declarations_variant is Array:
			var declarations: Array = declarations_variant as Array
			for idx in range(declarations.size()):
				if not (declarations[idx] is Dictionary):
					continue
				var entry: Dictionary = declarations[idx] as Dictionary
				for forbidden_key in forbidden_identity_aliases:
					_assert_false(
						entry.has(forbidden_key),
						"PESAL-T-28_no_identity_alias_%s_%s_%d" % [forbidden_key, room_path, idx],
						"declaration must identify enemies only via enemy_family"
					)
		room.free()


func test_pesal_t_29_fallback_midpoint_is_exact_and_z_zero_without_anchors() -> void:
	var assembler_script: GDScript = load(ASSEMBLER_PATH) as GDScript
	_assert_true(assembler_script != null and assembler_script.can_instantiate(), "PESAL-T-29_assembler_instantiable")
	if assembler_script == null or not assembler_script.can_instantiate():
		return
	var assembler: Object = assembler_script.new()
	for room_path in _combat_room_paths():
		var room: Node = _instantiate_scene(room_path)
		_assert_true(room is Node3D, "PESAL-T-29_room_node3d_" + room_path)
		if not (room is Node3D):
			continue
		for child in room.get_children():
			if child is Marker3D and (child as Marker3D).name.begins_with(ENEMY_SPAWN_PREFIX):
				(child as Node).queue_free()
		var entry: Node3D = room.get_node_or_null("Entry") as Node3D
		var exit_node: Node3D = room.get_node_or_null("Exit") as Node3D
		_assert_true(entry != null and exit_node != null, "PESAL-T-29_entry_exit_present_" + room_path)
		if entry == null or exit_node == null:
			room.free()
			continue
		var expected_mid_x: float = (entry.position.x + exit_node.position.x) * 0.5
		var expected_y: float = maxf(entry.position.y, exit_node.position.y)
		var fallback: Variant = assembler.call("_compute_room_enemy_spawn_fallback", room)
		_assert_true(fallback is Vector3, "PESAL-T-29_fallback_vector3_" + room_path)
		if fallback is Vector3:
			var fallback_vec: Vector3 = fallback as Vector3
			_assert_true(absf(fallback_vec.x - expected_mid_x) <= 0.001, "PESAL-T-29_fallback_midpoint_x_" + room_path)
			_assert_true(absf(fallback_vec.y - expected_y) <= 0.001, "PESAL-T-29_fallback_y_uses_max_marker_y_" + room_path)
			_assert_true(absf(fallback_vec.z) <= 0.001, "PESAL-T-29_fallback_z_zero_" + room_path)
		room.free()


func run_all() -> int:
	print("--- test_procedural_enemy_spawn_attack_loop_contract.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_pesal_t_01_combat_rooms_are_declared_by_run_scene_assembler_pool()
	test_pesal_t_02_room_local_spawn_declaration_contract_exists()
	test_pesal_t_03_visual_selection_filters_in_use_non_draft()
	test_pesal_t_04_zero_eligible_variants_fail_closed()
	test_pesal_t_05_no_hardcoded_enemy_instances_in_combat_rooms()
	test_pesal_t_06_enemy_spawn_anchor_indices_contiguous()
	test_pesal_t_07_enemy_spawn_anchor_z_is_zero_when_present()
	test_pesal_t_08_fallback_midpoint_contract_is_wired_in_assembler()
	test_pesal_t_09_entry_exit_reserved_not_spawn_prefix()
	test_pesal_t_10_room_chain_generator_remains_enemy_spawn_free()
	test_pesal_t_11_assembler_keeps_canonical_sequence_contract()
	test_pesal_t_12_generated_scene_existence_validation_seam_present()
	test_pesal_t_13_attack_defaults_match_family_contract()
	test_pesal_t_14_attack_scripts_require_player_group_and_dead_gate()
	test_pesal_t_15_weakened_and_infected_do_not_auto_block_attack()
	test_pesal_t_16_enemy_state_machine_has_canonical_lowercase_states()
	test_pesal_t_17_each_combat_family_has_eligible_generated_scene()
	test_pesal_t_18_anchor_discovery_or_fallback_is_testable_headless()
	test_pesal_t_19_dead_state_attack_suppression_is_encoded_per_family()
	test_pesal_t_20_selector_with_seeded_rng_is_deterministic()
	test_pesal_t_21_missing_family_fails_without_crash()
	test_pesal_t_22_spawn_failure_log_context_seam_present()
	test_pesal_t_23_selector_rejects_corrupt_manifest_shapes()
	test_pesal_t_24_selector_rejects_mutated_version_records()
	test_pesal_t_25_room_declaration_schema_rejects_invalid_bounds()
	test_pesal_t_26_selector_determinism_under_stress_repeated_calls()
	test_pesal_t_27_no_embedded_enemy_nodes_by_type_or_metadata()
	test_pesal_t_28_declaration_rejects_enemy_identity_alias_fields()
	test_pesal_t_29_fallback_midpoint_is_exact_and_z_zero_without_anchors()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
