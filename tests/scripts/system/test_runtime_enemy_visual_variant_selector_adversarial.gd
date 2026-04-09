#
# test_runtime_enemy_visual_variant_selector_adversarial.gd
#
# Adversarial coverage for M9-RSEVV runtime visual variant selection.
# Focus: malformed metadata, fail-closed invariants, order/sequence robustness,
# and deterministic stress behavior under injected RNG streams.
#

extends "res://tests/utils/test_utils.gd"

const SELECTOR_PATH: String = "res://scripts/system/enemy_visual_variant_selector.gd"
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


func _call_selector(inst: Object, family: String, manifest: Variant, rng: Variant = null) -> Dictionary:
	if inst == null:
		return {}
	if not inst.has_method(SELECTOR_METHOD):
		return {}
	var out: Variant = inst.call(SELECTOR_METHOD, family, manifest, rng)
	if not (out is Dictionary):
		return {}
	return out as Dictionary


func _assert_fail_closed(out: Dictionary, test_prefix: String) -> void:
	_assert_false(bool(out.get("ok", true)), test_prefix + "_non_success")
	_assert_true(
		str(out.get("path", "")).is_empty(),
		test_prefix + "_no_path",
		"fail-closed result must not expose selected path"
	)
	_assert_true(
		not str(out.get("error", "")).is_empty(),
		test_prefix + "_error_present",
		"fail-closed result must include deterministic error reason"
	)


func _manifest_with_malformed_entries() -> Dictionary:
	return {
		"schema_version": 1,
		"enemies": {
			"acid_spitter": {
				"versions": [
					# Missing draft key
					{
						"id": "acid_spitter_animated_00",
						"path": "animated_exports/acid_spitter_animated_00.glb",
						"in_use": true,
					},
					# Wrong type for in_use
					{
						"id": "acid_spitter_animated_01",
						"path": "animated_exports/acid_spitter_animated_01.glb",
						"draft": false,
						"in_use": "true",
					},
					# Wrong type for draft
					{
						"id": "acid_spitter_animated_02",
						"path": "animated_exports/acid_spitter_animated_02.glb",
						"draft": 0,
						"in_use": true,
					},
					# Missing path
					{
						"id": "acid_spitter_animated_03",
						"draft": false,
						"in_use": true,
					},
				]
			}
		}
	}


func _manifest_duplicate_ids_conflict() -> Dictionary:
	return {
		"schema_version": 1,
		"enemies": {
			"acid_spitter": {
				"versions": [
					{
						"id": "acid_spitter_animated_dup",
						"path": "animated_exports/acid_spitter_animated_00.glb",
						"draft": false,
						"in_use": true,
					},
					{
						"id": "acid_spitter_animated_dup",
						"path": "animated_exports/acid_spitter_animated_99.glb",
						"draft": false,
						"in_use": true,
					},
				]
			}
		}
	}


func _manifest_two_eligible_plus_noise() -> Dictionary:
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
			}
		}
	}


func test_rsevv_adv_01_manifest_wrong_top_level_shape_fails_closed() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-ADV-01_selector_missing", "selector missing/invalid")
		return
	var out: Dictionary = _call_selector(inst, "acid_spitter", {"schema_version": 1}, _StubRng.new([0]))
	if out.is_empty():
		_fail("RSEVV-ADV-01_non_dictionary_output", "selector returned empty/non-dictionary result")
		return
	_assert_fail_closed(out, "RSEVV-ADV-01_fail_closed")


func test_rsevv_adv_02_unknown_family_fails_closed_without_cross_family_fallback() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-ADV-02_selector_missing", "selector missing/invalid")
		return
	var out: Dictionary = _call_selector(inst, "nonexistent_family", _manifest_two_eligible_plus_noise(), _StubRng.new([0]))
	if out.is_empty():
		_fail("RSEVV-ADV-02_non_dictionary_output", "selector returned empty/non-dictionary result")
		return
	_assert_fail_closed(out, "RSEVV-ADV-02_fail_closed")


func test_rsevv_adv_03_malformed_status_metadata_is_rejected_fail_closed() -> void:
	# CHECKPOINT
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-ADV-03_selector_missing", "selector missing/invalid")
		return
	var out: Dictionary = _call_selector(inst, "acid_spitter", _manifest_with_malformed_entries(), _StubRng.new([0, 1]))
	if out.is_empty():
		_fail("RSEVV-ADV-03_non_dictionary_output", "selector returned empty/non-dictionary result")
		return
	_assert_fail_closed(out, "RSEVV-ADV-03_fail_closed")


func test_rsevv_adv_04_duplicate_variant_ids_with_conflicting_paths_fail_closed() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-ADV-04_selector_missing", "selector missing/invalid")
		return
	var out: Dictionary = _call_selector(inst, "acid_spitter", _manifest_duplicate_ids_conflict(), _StubRng.new([1]))
	if out.is_empty():
		_fail("RSEVV-ADV-04_non_dictionary_output", "selector returned empty/non-dictionary result")
		return
	_assert_fail_closed(out, "RSEVV-ADV-04_fail_closed")


func test_rsevv_adv_05_rng_out_of_range_values_are_clamped_and_never_leak_ineligible() -> void:
	var inst: Object = _selector_instance()
	if inst == null:
		_fail("RSEVV-ADV-05_selector_missing", "selector missing/invalid")
		return
	var manifest: Dictionary = _manifest_two_eligible_plus_noise()
	var rng := _StubRng.new([-100, 999, -5, 42, 0, 1, 5000, -999])
	for i in range(16):
		var out: Dictionary = _call_selector(inst, "acid_spitter", manifest, rng)
		if out.is_empty():
			_fail("RSEVV-ADV-05_non_dictionary_output_" + str(i), "selector returned empty/non-dictionary result")
			return
		_assert_true(bool(out.get("ok", false)), "RSEVV-ADV-05_ok_" + str(i), "selection should succeed")
		var path: String = str(out.get("path", ""))
		_assert_false(
			path.ends_with("_02.glb") or path.ends_with("_03.glb"),
			"RSEVV-ADV-05_no_ineligible_leak_" + str(i),
			"ineligible draft/not-in-use variant selected: " + path
		)


func test_rsevv_adv_06_stress_500_selections_remain_deterministic_for_same_rng_stream() -> void:
	var inst_a: Object = _selector_instance()
	var inst_b: Object = _selector_instance()
	if inst_a == null or inst_b == null:
		_fail("RSEVV-ADV-06_selector_missing", "selector missing/invalid")
		return
	var manifest: Dictionary = _manifest_two_eligible_plus_noise()
	var seq_template: Array[int] = [0, 1, 1, 0, 0, 1, 1, 0]
	var rng_a := _StubRng.new(seq_template)
	var rng_b := _StubRng.new(seq_template)
	var trace_a: PackedStringArray = []
	var trace_b: PackedStringArray = []
	for _i in range(500):
		var out_a: Dictionary = _call_selector(inst_a, "acid_spitter", manifest, rng_a)
		var out_b: Dictionary = _call_selector(inst_b, "acid_spitter", manifest, rng_b)
		if out_a.is_empty() or out_b.is_empty():
			_fail("RSEVV-ADV-06_non_dictionary_output", "selector returned empty/non-dictionary result")
			return
		trace_a.append(str(out_a.get("variant_id", out_a.get("path", ""))))
		trace_b.append(str(out_b.get("variant_id", out_b.get("path", ""))))
	_assert_eq(trace_a, trace_b, "RSEVV-ADV-06_repeatable_stress_trace")


func run_all() -> int:
	print("--- test_runtime_enemy_visual_variant_selector_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_rsevv_adv_01_manifest_wrong_top_level_shape_fails_closed()
	test_rsevv_adv_02_unknown_family_fails_closed_without_cross_family_fallback()
	test_rsevv_adv_03_malformed_status_metadata_is_rejected_fail_closed()
	test_rsevv_adv_04_duplicate_variant_ids_with_conflicting_paths_fail_closed()
	test_rsevv_adv_05_rng_out_of_range_values_are_clamped_and_never_leak_ineligible()
	test_rsevv_adv_06_stress_500_selections_remain_deterministic_for_same_rng_stream()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
