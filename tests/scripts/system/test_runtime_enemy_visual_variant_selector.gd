#
# test_runtime_enemy_visual_variant_selector.gd
#
# Primary behavioral tests for M9-RSEVV runtime visual variant selection.
# Ticket: project_board/9_milestone_9_enemy_player_model_visual_polish/in_progress/08_runtime_spawn_random_enemy_visual_variant.md
#
# Contract assumptions (checkpointed in scoped log):
# - Selector module path: res://scripts/system/enemy_visual_variant_selector.gd
# - Selector API: resolve_spawn_visual_variant(family: String, manifest: Dictionary, rng := null) -> Dictionary
# - Return shape:
#   - success: {"ok": true, "path": <String>, "variant_id": <String>}
#   - fail-closed: {"ok": false, "error": <String>}
#
# Requirement traceability:
# - RSEVV-F1  -> RSEVV-T-01, RSEVV-T-03, RSEVV-T-06
# - RSEVV-F2  -> RSEVV-T-02, RSEVV-T-04
# - RSEVV-F3  -> RSEVV-T-05
# - RSEVV-F4  -> RSEVV-T-07
# - RSEVV-F5  -> RSEVV-T-04
# - RSEVV-NF1 -> RSEVV-T-06

extends "res://tests/utils/test_utils.gd"

const SELECTOR_PATH: String = "res://scripts/system/enemy_visual_variant_selector.gd"
const PROCEDURAL_CHOKEPOINT_SCRIPT_PATH: String = "res://scripts/system/run_scene_assembler.gd"
const SELECTOR_METHOD: String = "resolve_spawn_visual_variant"

var _pass_count: int = 0
var _fail_count: int = 0


class _StubRng extends RefCounted:
	var _seq: Array[int]
	var _idx: int = 0

	func _init(seq: Array[int]) -> void:
		_seq = seq

	func randi_range(min_value: int, max_value: int) -> int:
		if _seq.is_empty():
			return min_value
		var raw: int = _seq[_idx % _seq.size()]
		_idx += 1
		if raw < min_value:
			return min_value
		if raw > max_value:
			return max_value
		return raw


func _selector_instance() -> Object:
	if not ResourceLoader.exists(SELECTOR_PATH):
		return null
	var gds: GDScript = load(SELECTOR_PATH) as GDScript
	if gds == null:
		return null
	if not gds.can_instantiate():
		return null
	return gds.new()


func _call_selector(
	inst: Object,
	family: String,
	manifest: Dictionary,
	rng: Variant = null
) -> Dictionary:
	if inst == null:
		return {}
	if not inst.has_method(SELECTOR_METHOD):
		return {}
	var out: Variant = inst.call(SELECTOR_METHOD, family, manifest, rng)
	if not (out is Dictionary):
		return {}
	return out as Dictionary


func _manifest_two_eligible_with_noise() -> Dictionary:
	return {
		"schema_version": 1,
		"enemies": {
			"acid_spitter": {
				"versions": [
					{
						"id": "acid_spitter_animated_00",
						"path": "animated_exports/acid_spitter_animated_00.glb",
						"draft": false,
						"in_use": true,
					},
					{
						"id": "acid_spitter_animated_01",
						"path": "animated_exports/acid_spitter_animated_01.glb",
						"draft": false,
						"in_use": true,
					},
					{
						"id": "acid_spitter_animated_02",
						"path": "animated_exports/acid_spitter_animated_02.glb",
						"draft": true,
						"in_use": true,
					},
					{
						"id": "acid_spitter_animated_03",
						"path": "animated_exports/acid_spitter_animated_03.glb",
						"draft": false,
						"in_use": false,
					},
				]
			},
			"adhesion_bug": {
				"versions": [
					{
						"id": "adhesion_bug_animated_00",
						"path": "animated_exports/adhesion_bug_animated_00.glb",
						"draft": false,
						"in_use": true,
					}
				]
			}
		}
	}


func test_rsevv_t_01_selector_module_exists_and_instantiates() -> void:
	_assert_true(
		ResourceLoader.exists(SELECTOR_PATH),
		"RSEVV-T-01_selector_module_exists",
		"Expected selector module at " + SELECTOR_PATH
	)
	var inst: Object = _selector_instance()
	_assert_true(inst != null, "RSEVV-T-01_selector_instantiates", "Selector script could not instantiate")
	if inst != null:
		_assert_true(
			inst.has_method(SELECTOR_METHOD),
			"RSEVV-T-01_selector_method_exists",
			"Selector missing method " + SELECTOR_METHOD
		)


func test_rsevv_t_02_same_family_can_resolve_different_visuals() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-T-02_same_family_can_resolve_different_visuals", "selector missing/invalid")
		return

	var manifest: Dictionary = _manifest_two_eligible_with_noise()
	var rng := _StubRng.new([0, 1])

	var first: Dictionary = _call_selector(inst, "acid_spitter", manifest, rng)
	var second: Dictionary = _call_selector(inst, "acid_spitter", manifest, rng)
	if first.is_empty() or second.is_empty():
		_fail("RSEVV-T-02_same_family_can_resolve_different_visuals", "selector returned empty/non-dictionary result")
		return

	_assert_true(bool(first.get("ok", false)), "RSEVV-T-02_first_call_ok", "first selection must succeed")
	_assert_true(bool(second.get("ok", false)), "RSEVV-T-02_second_call_ok", "second selection must succeed")
	_assert_true(
		str(first.get("path", "")) != str(second.get("path", "")),
		"RSEVV-T-02_distinct_paths_across_consecutive_spawns",
		"Expected different visual paths across two consecutive same-family spawns under deterministic RNG [0,1]"
	)


func test_rsevv_t_03_draft_and_not_in_use_never_selected() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-T-03_draft_and_not_in_use_never_selected", "selector missing/invalid")
		return

	var manifest: Dictionary = _manifest_two_eligible_with_noise()
	var rng := _StubRng.new([0, 1, 1, 0, 1, 0])

	for i in range(6):
		var out: Dictionary = _call_selector(inst, "acid_spitter", manifest, rng)
		if out.is_empty():
			_fail("RSEVV-T-03_result_dict_" + str(i), "selector returned empty/non-dictionary result")
			continue
		_assert_true(bool(out.get("ok", false)), "RSEVV-T-03_ok_" + str(i), "selection should succeed")
		var path: String = str(out.get("path", ""))
		_assert_false(
			path.ends_with("_02.glb"),
			"RSEVV-T-03_no_draft_selection_" + str(i),
			"draft version path selected: " + path
		)
		_assert_false(
			path.ends_with("_03.glb"),
			"RSEVV-T-03_no_not_in_use_selection_" + str(i),
			"not-in-use version path selected: " + path
		)


func test_rsevv_t_04_seeded_rng_produces_repeatable_sequence() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-T-04_seeded_rng_produces_repeatable_sequence", "selector missing/invalid")
		return

	var manifest: Dictionary = _manifest_two_eligible_with_noise()
	var seq_a: PackedStringArray = []
	var seq_b: PackedStringArray = []
	var rng_a := _StubRng.new([1, 0, 1, 1, 0])
	var rng_b := _StubRng.new([1, 0, 1, 1, 0])

	for _i in range(5):
		var out_a: Dictionary = _call_selector(inst, "acid_spitter", manifest, rng_a)
		var out_b: Dictionary = _call_selector(inst, "acid_spitter", manifest, rng_b)
		if out_a.is_empty() or out_b.is_empty():
			_fail("RSEVV-T-04_non_dictionary_output", "selector returned empty/non-dictionary result")
			return
		seq_a.append(str(out_a.get("path", "")))
		seq_b.append(str(out_b.get("path", "")))

	_assert_eq(seq_a, seq_b, "RSEVV-T-04_repeatable_sequence_under_same_rng_stream")


func test_rsevv_t_05_single_eligible_version_has_parity() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-T-05_single_eligible_version_has_parity", "selector missing/invalid")
		return

	var manifest: Dictionary = {
		"schema_version": 1,
		"enemies": {
			"adhesion_bug": {
				"versions": [
					{
						"id": "adhesion_bug_animated_00",
						"path": "animated_exports/adhesion_bug_animated_00.glb",
						"draft": false,
						"in_use": true,
					},
					{
						"id": "adhesion_bug_animated_01",
						"path": "animated_exports/adhesion_bug_animated_01.glb",
						"draft": true,
						"in_use": true,
					}
				]
			}
		}
	}
	var rng := _StubRng.new([1, 0, 1, 0])
	var first: String = ""
	for i in range(4):
		var out: Dictionary = _call_selector(inst, "adhesion_bug", manifest, rng)
		if out.is_empty():
			_fail("RSEVV-T-05_non_dictionary_output_" + str(i), "selector returned empty/non-dictionary result")
			return
		_assert_true(bool(out.get("ok", false)), "RSEVV-T-05_ok_" + str(i), "selection should succeed")
		var path: String = str(out.get("path", ""))
		if i == 0:
			first = path
		_assert_eq_string(first, path, "RSEVV-T-05_stable_single_version_" + str(i))


func test_rsevv_t_06_empty_eligible_set_fails_closed() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-T-06_empty_eligible_set_fails_closed", "selector missing/invalid")
		return

	var manifest: Dictionary = {
		"schema_version": 1,
		"enemies": {
			"claw_crawler": {
				"versions": [
					{"id": "claw_crawler_animated_00", "path": "animated_exports/claw_crawler_animated_00.glb", "draft": true, "in_use": true},
					{"id": "claw_crawler_animated_01", "path": "animated_exports/claw_crawler_animated_01.glb", "draft": false, "in_use": false},
				]
			}
		}
	}

	var out: Dictionary = _call_selector(inst, "claw_crawler", manifest, _StubRng.new([0]))
	if out.is_empty():
		_fail("RSEVV-T-06_non_dictionary_output", "selector returned empty/non-dictionary result")
		return
	_assert_false(bool(out.get("ok", true)), "RSEVV-T-06_returns_non_success")
	_assert_true(
		str(out.get("path", "")) == "",
		"RSEVV-T-06_no_path_on_failure",
		"fail-closed output must not include selectable path"
	)
	_assert_true(
		not str(out.get("error", "")).is_empty(),
		"RSEVV-T-06_failure_includes_error_detail",
		"fail-closed output must expose deterministic failure reason"
	)


func test_rsevv_t_07_run_scene_assembler_uses_selector_seam() -> void:
	if not ResourceLoader.exists(PROCEDURAL_CHOKEPOINT_SCRIPT_PATH):
		_fail("RSEVV-T-07_run_scene_assembler_script_exists", "Missing script: " + PROCEDURAL_CHOKEPOINT_SCRIPT_PATH)
		return
	var script_res: GDScript = load(PROCEDURAL_CHOKEPOINT_SCRIPT_PATH) as GDScript
	if script_res == null:
		_fail("RSEVV-T-07_run_scene_assembler_loads", "Could not load " + PROCEDURAL_CHOKEPOINT_SCRIPT_PATH)
		return
	var src: String = script_res.source_code
	_assert_true(
		src.find(SELECTOR_PATH) >= 0,
		"RSEVV-T-07_assembler_references_selector_module",
		"run_scene_assembler.gd must reference shared selector module"
	)
	_assert_true(
		src.find(SELECTOR_METHOD) >= 0,
		"RSEVV-T-07_assembler_calls_selector_method",
		"run_scene_assembler.gd must call " + SELECTOR_METHOD + " at spawn choke point"
	)


func run_all() -> int:
	print("--- test_runtime_enemy_visual_variant_selector.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_rsevv_t_01_selector_module_exists_and_instantiates()
	test_rsevv_t_02_same_family_can_resolve_different_visuals()
	test_rsevv_t_03_draft_and_not_in_use_never_selected()
	test_rsevv_t_04_seeded_rng_produces_repeatable_sequence()
	test_rsevv_t_05_single_eligible_version_has_parity()
	test_rsevv_t_06_empty_eligible_set_fails_closed()
	test_rsevv_t_07_run_scene_assembler_uses_selector_seam()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
