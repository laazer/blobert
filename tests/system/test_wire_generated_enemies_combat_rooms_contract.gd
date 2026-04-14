#
# test_wire_generated_enemies_combat_rooms_contract.gd
#
# Primary behavioral contract tests for:
# project_board/10_milestone_10_procedural_enemies_in_level/in_progress/02_wire_generated_enemies_combat_rooms.md
#
# Requirement traceability:
# - R1 -> WGER-T-01..05
# - R2 -> WGER-T-06..09
# - R3 -> WGER-T-10..12
# - R4 -> WGER-T-13..15
# - R5 -> WGER-T-16..18
#

extends "res://tests/utils/test_utils.gd"

const ASSEMBLER_PATH: String = "res://scripts/system/run_scene_assembler.gd"
const SELECTOR_PATH: String = "res://scripts/system/enemy_visual_variant_selector.gd"
const REGISTRY_PATH: String = "res://asset_generation/python/model_registry.json"
const GENERATED_DIR: String = "res://scenes/enemies/generated/"
const COMBAT_ROOM_PATHS: Array[String] = [
	"res://scenes/rooms/room_combat_01.tscn",
	"res://scenes/rooms/room_combat_02.tscn",
]
const EXPECTED_M10_FAMILIES: Array[String] = ["acid", "adhesion", "carapace", "claw"]
const SELECTOR_STRESS_ITERATIONS: int = 64

var _pass_count: int = 0
var _fail_count: int = 0


class _StubRng extends RefCounted:
	var _seq: Array[int]
	var _i: int = 0

	func _init(seq: Array[int]) -> void:
		_seq = seq

	func randi_range(min_value: int, max_value: int) -> int:
		if _seq.is_empty():
			return min_value
		var raw: int = _seq[_i % _seq.size()]
		_i += 1
		return clampi(raw, min_value, max_value)


func _load_source(path: String) -> String:
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
	var f: FileAccess = FileAccess.open(path, FileAccess.READ)
	if f == null:
		return {}
	var parsed: Variant = JSON.parse_string(f.get_as_text())
	if not (parsed is Dictionary):
		return {}
	return parsed as Dictionary


func _selector_instance() -> Object:
	if not ResourceLoader.exists(SELECTOR_PATH):
		return null
	var selector_script: GDScript = load(SELECTOR_PATH) as GDScript
	if selector_script == null or not selector_script.can_instantiate():
		return null
	return selector_script.new()


func _call_selector(inst: Object, family: String, manifest: Dictionary, rng: Variant = null) -> Dictionary:
	if inst == null or not inst.has_method("resolve_spawn_visual_variant"):
		return {}
	var out: Variant = inst.call("resolve_spawn_visual_variant", family, manifest, rng)
	if not (out is Dictionary):
		return {}
	return out as Dictionary


func _deep_copy_dict(input: Dictionary) -> Dictionary:
	return input.duplicate(true)


func _normalize_family(raw_family: String) -> String:
	if raw_family.begins_with("acid"):
		return "acid"
	if raw_family.begins_with("adhesion"):
		return "adhesion"
	if raw_family.begins_with("carapace"):
		return "carapace"
	if raw_family.begins_with("claw"):
		return "claw"
	return raw_family


func _all_room_declarations() -> Array[Dictionary]:
	var out: Array[Dictionary] = []
	for room_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			continue
		var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", null)
		if declarations_variant is Array:
			var declarations: Array = declarations_variant as Array
			for entry in declarations:
				if entry is Dictionary:
					out.append(entry as Dictionary)
		room.free()
	return out


func test_wger_t_01_pool_references_combat_rooms_with_declarations() -> void:
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(not src.is_empty(), "WGER-T-01_assembler_script_loads")
	for room_path in COMBAT_ROOM_PATHS:
		_assert_true(src.find(room_path) >= 0, "WGER-T-01_pool_contains_" + room_path.get_file())
		var room: Node = _instantiate_scene(room_path)
		_assert_true(room != null, "WGER-T-01_room_instantiates_" + room_path.get_file())
		if room != null:
			_assert_true(room.has_meta("enemy_spawn_declarations"), "WGER-T-01_room_has_declarations_meta_" + room_path.get_file())
			room.free()


func test_wger_t_02_declaration_schema_requires_enemy_family_and_int_bounds() -> void:
	for room_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("WGER-T-02_room_instantiates_" + room_path.get_file(), "room missing")
			continue
		var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", null)
		_assert_true(declarations_variant is Array, "WGER-T-02_declarations_array_" + room_path.get_file())
		if declarations_variant is Array:
			var declarations: Array = declarations_variant as Array
			for i in range(declarations.size()):
				var entry_variant: Variant = declarations[i]
				_assert_true(entry_variant is Dictionary, "WGER-T-02_entry_dictionary_%s_%d" % [room_path.get_file(), i])
				if not (entry_variant is Dictionary):
					continue
				var entry: Dictionary = entry_variant as Dictionary
				_assert_true(entry.has("enemy_family"), "WGER-T-02_entry_has_enemy_family_%s_%d" % [room_path.get_file(), i])
				_assert_false(entry.has("enemy_id"), "WGER-T-02_entry_has_no_enemy_id_%s_%d" % [room_path.get_file(), i])
				_assert_true(entry.has("min_count"), "WGER-T-02_entry_has_min_count_%s_%d" % [room_path.get_file(), i])
				_assert_true(entry.has("max_count"), "WGER-T-02_entry_has_max_count_%s_%d" % [room_path.get_file(), i])
				if entry.has("min_count"):
					_assert_true(entry.get("min_count") is int, "WGER-T-02_min_count_int_%s_%d" % [room_path.get_file(), i])
				if entry.has("max_count"):
					_assert_true(entry.get("max_count") is int, "WGER-T-02_max_count_int_%s_%d" % [room_path.get_file(), i])
				if entry.has("min_count") and entry.has("max_count") and entry.get("min_count") is int and entry.get("max_count") is int:
					var min_count: int = entry["min_count"]
					var max_count: int = entry["max_count"]
					_assert_true(min_count >= 0 and min_count <= max_count, "WGER-T-02_min_max_valid_%s_%d" % [room_path.get_file(), i])
		room.free()


func test_wger_t_03_m10_families_are_covered_across_combat_rooms() -> void:
	# CHECKPOINT assumption: snake_case family names (e.g. acid_spitter) satisfy M10 shorthand families (acid).
	var seen: Dictionary = {}
	for family in EXPECTED_M10_FAMILIES:
		seen[family] = false
	for entry in _all_room_declarations():
		var family_raw: String = str(entry.get("enemy_family", ""))
		var normalized: String = _normalize_family(family_raw)
		if seen.has(normalized):
			seen[normalized] = true
	for family in EXPECTED_M10_FAMILIES:
		_assert_true(bool(seen.get(family, false)), "WGER-T-03_family_covered_" + family)


func test_wger_t_04_declared_variants_resolve_to_generated_tscn_assets() -> void:
	var selector: Object = _selector_instance()
	var manifest: Dictionary = _read_json(REGISTRY_PATH)
	_assert_true(selector != null, "WGER-T-04_selector_instantiates")
	_assert_true(not manifest.is_empty(), "WGER-T-04_manifest_loads")
	if selector == null or manifest.is_empty():
		return
	for entry in _all_room_declarations():
		var family: String = str(entry.get("enemy_family", ""))
		var out: Dictionary = _call_selector(selector, family, manifest, _StubRng.new([0]))
		_assert_true(bool(out.get("ok", false)), "WGER-T-04_selector_ok_" + family)
		if not bool(out.get("ok", false)):
			continue
		var variant_id: String = str(out.get("variant_id", ""))
		var scene_path: String = GENERATED_DIR + variant_id + ".tscn"
		_assert_true(scene_path.begins_with(GENERATED_DIR), "WGER-T-04_scene_in_canonical_root_" + family)
		_assert_true(ResourceLoader.exists(scene_path), "WGER-T-04_generated_scene_exists_" + family)


func test_wger_t_05_declaration_order_is_deterministic_across_instantiations() -> void:
	for room_path in COMBAT_ROOM_PATHS:
		var room_a: Node = _instantiate_scene(room_path)
		var room_b: Node = _instantiate_scene(room_path)
		_assert_true(room_a != null and room_b != null, "WGER-T-05_room_double_instantiates_" + room_path.get_file())
		if room_a == null or room_b == null:
			if room_a != null:
				room_a.free()
			if room_b != null:
				room_b.free()
			continue
		var a: Variant = room_a.get_meta("enemy_spawn_declarations", null)
		var b: Variant = room_b.get_meta("enemy_spawn_declarations", null)
		_assert_eq(a, b, "WGER-T-05_declaration_meta_deterministic_" + room_path.get_file())
		room_a.free()
		room_b.free()


func test_wger_t_06_enemy_spawn_markers_are_marker3d_and_contiguous() -> void:
	for room_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("WGER-T-06_room_instantiates_" + room_path.get_file(), "room missing")
			continue
		var indices: Array[int] = []
		for child in room.get_children():
			if not (child is Marker3D):
				continue
			var marker: Marker3D = child as Marker3D
			if not marker.name.begins_with("EnemySpawn_"):
				continue
			var suffix: String = marker.name.substr("EnemySpawn_".length())
			_assert_true(suffix.is_valid_int(), "WGER-T-06_anchor_index_numeric_%s_%s" % [room_path.get_file(), marker.name])
			if suffix.is_valid_int():
				indices.append(int(suffix))
		indices.sort()
		for i in range(indices.size()):
			_assert_eq_int(i + 1, indices[i], "WGER-T-06_anchor_contiguous_%s_%d" % [room_path.get_file(), i + 1])
		room.free()


func test_wger_t_07_enemy_spawn_markers_respect_lane_z_zero() -> void:
	for room_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(room_path)
		if room == null:
			_fail("WGER-T-07_room_instantiates_" + room_path.get_file(), "room missing")
			continue
		for child in room.get_children():
			if child is Marker3D and (child as Marker3D).name.begins_with("EnemySpawn_"):
				var marker: Marker3D = child as Marker3D
				_assert_true(absf(marker.position.z) <= 0.01, "WGER-T-07_lane_z_zero_%s_%s" % [room_path.get_file(), marker.name])
		room.free()


func test_wger_t_08_fallback_is_present_and_deterministic_when_no_anchors() -> void:
	var assembler_script: GDScript = load(ASSEMBLER_PATH) as GDScript
	_assert_true(assembler_script != null and assembler_script.can_instantiate(), "WGER-T-08_assembler_instantiable")
	if assembler_script == null or not assembler_script.can_instantiate():
		return
	var assembler: Object = assembler_script.new()
	var room: Node = _instantiate_scene(COMBAT_ROOM_PATHS[0])
	_assert_true(room is Node3D, "WGER-T-08_room_node3d")
	if not (room is Node3D):
		return
	for child in room.get_children():
		if child is Marker3D and (child as Marker3D).name.begins_with("EnemySpawn_"):
			(child as Node).queue_free()
	var pos_a: Variant = assembler.call("_compute_room_enemy_spawn_fallback", room)
	var pos_b: Variant = assembler.call("_compute_room_enemy_spawn_fallback", room)
	_assert_eq(pos_a, pos_b, "WGER-T-08_fallback_deterministic_same_room_state")
	room.free()


func test_wger_t_09_entry_exit_are_reserved_and_present() -> void:
	for room_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(room_path)
		_assert_true(room != null, "WGER-T-09_room_instantiates_" + room_path.get_file())
		if room == null:
			continue
		_assert_true(room.has_node("Entry"), "WGER-T-09_has_entry_" + room_path.get_file())
		_assert_true(room.has_node("Exit"), "WGER-T-09_has_exit_" + room_path.get_file())
		room.free()


func test_wger_t_10_generated_enemy_scenes_use_enemyinfection3d_or_strict_wrapper() -> void:
	for scene_path in COMBAT_ROOM_PATHS:
		# Resolve through declarations to enforce room-authoritative source of what can spawn.
		var room: Node = _instantiate_scene(scene_path)
		if room == null:
			_fail("WGER-T-10_room_instantiates_" + scene_path.get_file(), "room missing")
			continue
		var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", [])
		if declarations_variant is Array:
			var selector: Object = _selector_instance()
			var manifest: Dictionary = _read_json(REGISTRY_PATH)
			for entry_variant in declarations_variant:
				if not (entry_variant is Dictionary):
					continue
				var family: String = str((entry_variant as Dictionary).get("enemy_family", ""))
				var out: Dictionary = _call_selector(selector, family, manifest, _StubRng.new([0]))
				if not bool(out.get("ok", false)):
					_fail("WGER-T-10_selector_resolves_" + family, "failed to resolve family")
					continue
				var variant_id: String = str(out.get("variant_id", ""))
				var generated_scene: PackedScene = load(GENERATED_DIR + variant_id + ".tscn") as PackedScene
				_assert_true(generated_scene != null, "WGER-T-10_generated_scene_loads_" + family)
				if generated_scene == null:
					continue
				var enemy_node: Node = generated_scene.instantiate()
				_assert_true(
					enemy_node is EnemyInfection3D or enemy_node.has_method("get_esm"),
					"WGER-T-10_runtime_compat_enemyinfection3d_" + family
				)
				enemy_node.free()
		room.free()


func test_wger_t_11_spawned_instances_expose_enemy_family_and_mutation_drop() -> void:
	for generated_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(generated_path)
		if room == null:
			continue
		var declarations: Variant = room.get_meta("enemy_spawn_declarations", [])
		var selector: Object = _selector_instance()
		var manifest: Dictionary = _read_json(REGISTRY_PATH)
		if declarations is Array:
			for entry_variant in declarations:
				if not (entry_variant is Dictionary):
					continue
				var family: String = str((entry_variant as Dictionary).get("enemy_family", ""))
				var out: Dictionary = _call_selector(selector, family, manifest, _StubRng.new([0]))
				if not bool(out.get("ok", false)):
					continue
				var variant_id: String = str(out.get("variant_id", ""))
				var instance: Node = _instantiate_scene(GENERATED_DIR + variant_id + ".tscn")
				_assert_true(instance != null, "WGER-T-11_generated_instance_created_" + family)
				if instance == null:
					continue
				_assert_true(instance.has_meta("enemy_family"), "WGER-T-11_has_enemy_family_meta_" + family)
				_assert_true(instance.has_meta("mutation_drop"), "WGER-T-11_has_mutation_drop_meta_" + family)
				instance.free()
		room.free()


func test_wger_t_12_generated_instances_keep_collision_and_animation_roots() -> void:
	var generated_paths: Array[String] = []
	for file_path in [
		"acid_spitter_animated_00.tscn",
		"adhesion_bug_animated_00.tscn",
		"carapace_husk_animated_00.tscn",
		"claw_crawler_animated_00.tscn",
	]:
		generated_paths.append(GENERATED_DIR + file_path)
	for scene_path in generated_paths:
		var node: Node = _instantiate_scene(scene_path)
		_assert_true(node != null, "WGER-T-12_scene_instantiates_" + scene_path.get_file())
		if node == null:
			continue
		_assert_true(node.get_node_or_null("CollisionShape3D") != null, "WGER-T-12_collision_shape_present_" + scene_path.get_file())
		var anim_player: AnimationPlayer = node.get_node_or_null("AnimationPlayer") as AnimationPlayer
		_assert_true(anim_player != null, "WGER-T-12_animation_player_present_" + scene_path.get_file())
		if anim_player != null:
			_assert_true(not str(anim_player.root_node).is_empty(), "WGER-T-12_animation_root_bound_" + scene_path.get_file())
		node.free()


func test_wger_t_13_sequence_contract_is_unchanged() -> void:
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(src.find("\"intro\"") >= 0, "WGER-T-13_has_intro")
	_assert_true(src.find("\"combat\", \"combat\"") >= 0, "WGER-T-13_has_two_combats")
	_assert_true(src.find("\"mutation_tease\"") >= 0, "WGER-T-13_has_mutation_tease")
	_assert_true(src.find("\"boss\"") >= 0, "WGER-T-13_has_boss")


func test_wger_t_14_spawn_wiring_runs_on_standard_ready_path() -> void:
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(src.find("func _ready()") >= 0, "WGER-T-14_ready_exists")
	_assert_true(src.find("_rsm.apply_event(\"start_run\")") >= 0, "WGER-T-14_ready_starts_run")


func test_wger_t_15_failures_are_isolated_with_room_family_reason_logging() -> void:
	var src: String = _load_source(ASSEMBLER_PATH)
	_assert_true(src.find("push_warning") >= 0 or src.find("push_error") >= 0, "WGER-T-15_has_failure_logging")
	_assert_true(src.find("room") >= 0, "WGER-T-15_log_mentions_room")
	_assert_true(src.find("family") >= 0, "WGER-T-15_log_mentions_family")
	_assert_true(src.find("error") >= 0 or src.find("failed") >= 0, "WGER-T-15_log_mentions_reason")


func test_wger_t_16_seeded_selector_is_deterministic() -> void:
	var selector: Object = _selector_instance()
	var manifest: Dictionary = _read_json(REGISTRY_PATH)
	_assert_true(selector != null and not manifest.is_empty(), "WGER-T-16_selector_and_manifest_ready")
	if selector == null or manifest.is_empty():
		return
	var rng_a := _StubRng.new([0, 1, 0, 1, 1, 0])
	var rng_b := _StubRng.new([0, 1, 0, 1, 1, 0])
	var seq_a: PackedStringArray = []
	var seq_b: PackedStringArray = []
	for _i in range(16):
		seq_a.append(str(_call_selector(selector, "carapace_husk", manifest, rng_a).get("variant_id", "")))
		seq_b.append(str(_call_selector(selector, "carapace_husk", manifest, rng_b).get("variant_id", "")))
	_assert_eq(seq_a, seq_b, "WGER-T-16_seeded_determinism")


func test_wger_t_17_missing_family_is_non_crashing_and_actionable() -> void:
	var selector: Object = _selector_instance()
	var manifest: Dictionary = _read_json(REGISTRY_PATH)
	var out: Dictionary = _call_selector(selector, "nonexistent_family", manifest, _StubRng.new([0]))
	_assert_false(bool(out.get("ok", true)), "WGER-T-17_missing_family_fail_closed")
	_assert_true(not str(out.get("error", "")).is_empty(), "WGER-T-17_missing_family_has_actionable_error")


func test_wger_t_18_traceability_suite_covers_r1_to_r5() -> void:
	# Meta assertion ensuring this file preserves explicit AC traceability naming.
	var src: String = _load_source("res://tests/system/test_wire_generated_enemies_combat_rooms_contract.gd")
	for marker in ["R1 ->", "R2 ->", "R3 ->", "R4 ->", "R5 ->"]:
		_assert_true(src.find(marker) >= 0, "WGER-T-18_traceability_marker_" + marker)


func test_wger_t_19_declaration_enemy_family_is_non_empty_string() -> void:
	# CHECKPOINT conservative assumption: empty/whitespace enemy_family is invalid and must be treated as malformed.
	for room_path in COMBAT_ROOM_PATHS:
		var room: Node = _instantiate_scene(room_path)
		_assert_true(room != null, "WGER-T-19_room_instantiates_" + room_path.get_file())
		if room == null:
			continue
		var declarations_variant: Variant = room.get_meta("enemy_spawn_declarations", [])
		_assert_true(declarations_variant is Array, "WGER-T-19_declarations_array_" + room_path.get_file())
		if declarations_variant is Array:
			var declarations: Array = declarations_variant as Array
			for i in range(declarations.size()):
				var entry_variant: Variant = declarations[i]
				_assert_true(entry_variant is Dictionary, "WGER-T-19_entry_dictionary_%s_%d" % [room_path.get_file(), i])
				if not (entry_variant is Dictionary):
					continue
				var family: String = str((entry_variant as Dictionary).get("enemy_family", "")).strip_edges()
				_assert_true(not family.is_empty(), "WGER-T-19_enemy_family_non_empty_%s_%d" % [room_path.get_file(), i])
		room.free()


func test_wger_t_20_selector_rejects_corrupt_manifest_shapes() -> void:
	var selector: Object = _selector_instance()
	_assert_true(selector != null, "WGER-T-20_selector_instantiates")
	if selector == null:
		return
	var malformed_inputs: Array[Dictionary] = [
		{},
		{"enemies": []},
		{"enemies": {"carapace_husk": []}},
		{"enemies": {"carapace_husk": {"versions": "not-an-array"}}},
		{"enemies": {"carapace_husk": {"versions": [123]}}},
	]
	for i in range(malformed_inputs.size()):
		var out: Dictionary = _call_selector(selector, "carapace_husk", malformed_inputs[i], _StubRng.new([0]))
		_assert_false(bool(out.get("ok", true)), "WGER-T-20_fail_closed_corrupt_manifest_%d" % i)
		_assert_true(not str(out.get("error", "")).is_empty(), "WGER-T-20_has_error_corrupt_manifest_%d" % i)


func test_wger_t_21_selector_rejects_mutated_version_record_types() -> void:
	var selector: Object = _selector_instance()
	var manifest: Dictionary = _read_json(REGISTRY_PATH)
	_assert_true(selector != null and not manifest.is_empty(), "WGER-T-21_selector_and_manifest_ready")
	if selector == null or manifest.is_empty():
		return
	var type_mutations: Array = [
		{"key": "id", "value": 1},
		{"key": "path", "value": 77},
		{"key": "draft", "value": "false"},
		{"key": "in_use", "value": "true"},
	]
	for mutation in type_mutations:
		var mutated: Dictionary = _deep_copy_dict(manifest)
		var enemies: Dictionary = mutated.get("enemies", {})
		var family_entry: Dictionary = enemies.get("carapace_husk", {})
		var versions: Array = family_entry.get("versions", [])
		_assert_true(not versions.is_empty(), "WGER-T-21_versions_exist_for_mutation_%s" % str(mutation.get("key", "")))
		if versions.is_empty():
			continue
		var first_version: Dictionary = versions[0]
		first_version[str(mutation.get("key", ""))] = mutation.get("value")
		versions[0] = first_version
		family_entry["versions"] = versions
		enemies["carapace_husk"] = family_entry
		mutated["enemies"] = enemies
		var out: Dictionary = _call_selector(selector, "carapace_husk", mutated, _StubRng.new([0]))
		_assert_false(bool(out.get("ok", true)), "WGER-T-21_fail_closed_mutation_%s" % str(mutation.get("key", "")))
		_assert_true(not str(out.get("error", "")).is_empty(), "WGER-T-21_has_error_mutation_%s" % str(mutation.get("key", "")))


func test_wger_t_22_selector_reports_missing_family_with_actionable_context() -> void:
	var selector: Object = _selector_instance()
	var manifest: Dictionary = _read_json(REGISTRY_PATH)
	_assert_true(selector != null and not manifest.is_empty(), "WGER-T-22_selector_and_manifest_ready")
	if selector == null or manifest.is_empty():
		return
	var out: Dictionary = _call_selector(selector, "  ", manifest, _StubRng.new([0]))
	_assert_false(bool(out.get("ok", true)), "WGER-T-22_blank_family_fail_closed")
	_assert_true(not str(out.get("error", "")).is_empty(), "WGER-T-22_blank_family_has_error")


func test_wger_t_23_selector_determinism_under_stress_repeated_calls() -> void:
	var selector: Object = _selector_instance()
	var manifest: Dictionary = _read_json(REGISTRY_PATH)
	_assert_true(selector != null and not manifest.is_empty(), "WGER-T-23_selector_and_manifest_ready")
	if selector == null or manifest.is_empty():
		return
	var rng_a := _StubRng.new([0, 1, 0, 1, 1, 0, 0, 1])
	var rng_b := _StubRng.new([0, 1, 0, 1, 1, 0, 0, 1])
	var seq_a: PackedStringArray = []
	var seq_b: PackedStringArray = []
	for _i in range(SELECTOR_STRESS_ITERATIONS):
		seq_a.append(str(_call_selector(selector, "carapace_husk", manifest, rng_a).get("variant_id", "")))
		seq_b.append(str(_call_selector(selector, "carapace_husk", manifest, rng_b).get("variant_id", "")))
	_assert_eq(seq_a, seq_b, "WGER-T-23_stress_seeded_determinism_%d_calls" % SELECTOR_STRESS_ITERATIONS)


func run_all() -> int:
	print("--- test_wire_generated_enemies_combat_rooms_contract.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_wger_t_01_pool_references_combat_rooms_with_declarations()
	test_wger_t_02_declaration_schema_requires_enemy_family_and_int_bounds()
	test_wger_t_03_m10_families_are_covered_across_combat_rooms()
	test_wger_t_04_declared_variants_resolve_to_generated_tscn_assets()
	test_wger_t_05_declaration_order_is_deterministic_across_instantiations()
	test_wger_t_06_enemy_spawn_markers_are_marker3d_and_contiguous()
	test_wger_t_07_enemy_spawn_markers_respect_lane_z_zero()
	test_wger_t_08_fallback_is_present_and_deterministic_when_no_anchors()
	test_wger_t_09_entry_exit_are_reserved_and_present()
	test_wger_t_10_generated_enemy_scenes_use_enemyinfection3d_or_strict_wrapper()
	test_wger_t_11_spawned_instances_expose_enemy_family_and_mutation_drop()
	test_wger_t_12_generated_instances_keep_collision_and_animation_roots()
	test_wger_t_13_sequence_contract_is_unchanged()
	test_wger_t_14_spawn_wiring_runs_on_standard_ready_path()
	test_wger_t_15_failures_are_isolated_with_room_family_reason_logging()
	test_wger_t_16_seeded_selector_is_deterministic()
	test_wger_t_17_missing_family_is_non_crashing_and_actionable()
	test_wger_t_18_traceability_suite_covers_r1_to_r5()
	test_wger_t_19_declaration_enemy_family_is_non_empty_string()
	test_wger_t_20_selector_rejects_corrupt_manifest_shapes()
	test_wger_t_21_selector_rejects_mutated_version_record_types()
	test_wger_t_22_selector_reports_missing_family_with_actionable_context()
	test_wger_t_23_selector_determinism_under_stress_repeated_calls()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
