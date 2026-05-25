#
# test_attack_resource_adversarial.gd
#
# Adversarial edge-case tests for AttackResource data model.
# Spec: project_board/specs/attack_resource_spec.md — Section 8 (EC-1 through EC-14)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/04_attack_resource.md (T3)
#
# Tests are RED until implementation creates scripts/attacks/attack_resource.gd.
# Each test targets a specific weakness, boundary, or assumption gap that the
# primary suite (test_attack_resource.gd) does not cover.
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _SCRIPT_PATH := "res://scripts/attacks/attack_resource.gd"


func _load_script() -> GDScript:
	return load(_SCRIPT_PATH) as GDScript


func _make(test_label: String) -> Resource:
	var script := _load_script()
	if script == null:
		_fail_test(test_label, _SCRIPT_PATH + " not loadable")
		return null
	var inst = script.new()
	if inst == null:
		_fail_test(test_label, "instantiation returned null")
		return null
	return inst


# ---------------------------------------------------------------------------
# EC-1: Negative damage — Resource stores the value; no error
# ---------------------------------------------------------------------------

func test_ec01_negative_damage() -> void:
	var r = _make("EC-01")
	if r == null:
		return
	r.damage = -5.0
	_assert_eq_float(-5.0, r.damage, "EC-01_negative_damage_stored")

func test_ec01_large_negative_damage() -> void:
	var r = _make("EC-01b")
	if r == null:
		return
	r.damage = -999999.0
	_assert_eq_float(-999999.0, r.damage, "EC-01_large_negative_damage")


# ---------------------------------------------------------------------------
# EC-2: Zero cooldown — no artificial minimum
# ---------------------------------------------------------------------------

func test_ec02_zero_cooldown() -> void:
	var r = _make("EC-02")
	if r == null:
		return
	r.cooldown = 0.0
	_assert_eq_float(0.0, r.cooldown, "EC-02_zero_cooldown")

func test_ec02_tiny_cooldown() -> void:
	var r = _make("EC-02b")
	if r == null:
		return
	r.cooldown = 0.001
	_assert_eq_float(0.001, r.cooldown, "EC-02_tiny_cooldown_0001")

func test_ec02_negative_cooldown() -> void:
	var r = _make("EC-02c")
	if r == null:
		return
	r.cooldown = -1.0
	_assert_eq_float(-1.0, r.cooldown, "EC-02_negative_cooldown")


# ---------------------------------------------------------------------------
# EC-3: Empty attack_name — empty string is valid default
# ---------------------------------------------------------------------------

func test_ec03_empty_attack_name() -> void:
	var r = _make("EC-03")
	if r == null:
		return
	_assert_eq_string("", r.attack_name, "EC-03_default_empty_name")
	r.attack_name = ""
	_assert_eq_string("", r.attack_name, "EC-03_explicit_empty_name")


# ---------------------------------------------------------------------------
# EC-4: Unknown effect_type — Resource accepts any string
# ---------------------------------------------------------------------------

func test_ec04_unknown_effect_type() -> void:
	var r = _make("EC-04")
	if r == null:
		return
	r.effect_type = "UNKNOWN_TYPE"
	_assert_eq_string("UNKNOWN_TYPE", r.effect_type, "EC-04_unknown_type_stored")

func test_ec04_empty_effect_type() -> void:
	var r = _make("EC-04b")
	if r == null:
		return
	_assert_eq_string("", r.effect_type, "EC-04_empty_default")
	r.effect_type = ""
	_assert_eq_string("", r.effect_type, "EC-04_empty_set")

func test_ec04_whitespace_effect_type() -> void:
	var r = _make("EC-04c")
	if r == null:
		return
	r.effect_type = "   "
	_assert_eq_string("   ", r.effect_type, "EC-04_whitespace_only")

func test_ec04_special_chars_effect_type() -> void:
	var r = _make("EC-04d")
	if r == null:
		return
	r.effect_type = "TYPE-WITH_SYMBOLS!@#$%"
	_assert_eq_string("TYPE-WITH_SYMBOLS!@#$%", r.effect_type, "EC-04_special_chars")


# ---------------------------------------------------------------------------
# EC-5: Empty modifiers — default state, .get() returns fallback
# ---------------------------------------------------------------------------

func test_ec05_empty_modifiers_get_default() -> void:
	var r = _make("EC-05")
	if r == null:
		return
	_assert_eq_int(0, r.modifiers.size(), "EC-05_empty_size")
	_assert_eq(-1, r.modifiers.get("any_key", -1), "EC-05_get_returns_default")
	_assert_false(r.modifiers.has("nonexistent"), "EC-05_has_false")


# ---------------------------------------------------------------------------
# EC-6: Large modifier dictionary (100+ keys) — no crash
# ---------------------------------------------------------------------------

func test_ec06_large_modifier_dictionary() -> void:
	var r = _make("EC-06")
	if r == null:
		return
	var big_dict := {}
	for i in range(150):
		big_dict["key_" + str(i)] = float(i)
	r.modifiers = big_dict
	_assert_eq_int(150, r.modifiers.size(), "EC-06_150_keys_stored")
	_assert_eq_float(0.0, r.modifiers["key_0"], "EC-06_first_key")
	_assert_eq_float(149.0, r.modifiers["key_149"], "EC-06_last_key")


# ---------------------------------------------------------------------------
# EC-7: Nested modifier values — Resource stores them (not recommended)
# ---------------------------------------------------------------------------

func test_ec07_nested_modifier_dict() -> void:
	var r = _make("EC-07")
	if r == null:
		return
	r.modifiers = {
		"combo": {"hits": 2, "delay": 0.1},
	}
	_assert_true(r.modifiers["combo"] is Dictionary, "EC-07_nested_is_dict")
	_assert_eq(2, r.modifiers["combo"]["hits"], "EC-07_nested_int_value")
	_assert_eq_float(0.1, r.modifiers["combo"]["delay"], "EC-07_nested_float_value")

func test_ec07_deeply_nested_modifier() -> void:
	var r = _make("EC-07b")
	if r == null:
		return
	r.modifiers = {
		"level1": {
			"level2": {
				"level3": {
					"deep_value": 42,
				},
			},
		},
	}
	var l1 = r.modifiers["level1"]
	_assert_true(l1 is Dictionary, "EC-07_depth1_is_dict")
	var l2 = l1["level2"]
	_assert_true(l2 is Dictionary, "EC-07_depth2_is_dict")
	var l3 = l2["level3"]
	_assert_true(l3 is Dictionary, "EC-07_depth3_is_dict")
	_assert_eq(42, l3["deep_value"], "EC-07_depth3_value")

func test_ec07_modifier_array_value() -> void:
	var r = _make("EC-07c")
	if r == null:
		return
	r.modifiers = {"hit_sequence": [1.0, 2.0, 3.0]}
	_assert_true(r.modifiers["hit_sequence"] is Array, "EC-07_array_value_stored")
	_assert_eq_int(3, r.modifiers["hit_sequence"].size(), "EC-07_array_size")


# ---------------------------------------------------------------------------
# EC-8: Duplicate attack_ids — no uniqueness enforcement
# ---------------------------------------------------------------------------

func test_ec08_duplicate_attack_ids() -> void:
	var r1 = _make("EC-08_a")
	if r1 == null:
		return
	var r2 = _make("EC-08_b")
	if r2 == null:
		return
	r1.attack_id = 101
	r2.attack_id = 101
	_assert_eq_int(101, r1.attack_id, "EC-08_r1_id")
	_assert_eq_int(101, r2.attack_id, "EC-08_r2_id")
	_assert_true(r1 != r2, "EC-08_different_instances")


# ---------------------------------------------------------------------------
# EC-9: Unknown knockback_direction — Resource stores it
# ---------------------------------------------------------------------------

func test_ec09_unknown_knockback_direction() -> void:
	var r = _make("EC-09")
	if r == null:
		return
	r.knockback_direction = "diagonal"
	_assert_eq_string("diagonal", r.knockback_direction, "EC-09_diagonal_stored")

func test_ec09_empty_knockback_direction() -> void:
	var r = _make("EC-09b")
	if r == null:
		return
	r.knockback_direction = ""
	_assert_eq_string("", r.knockback_direction, "EC-09_empty_kd")


# ---------------------------------------------------------------------------
# EC-10: Color boundary and HDR values
# ---------------------------------------------------------------------------

func test_ec10_transparent_color() -> void:
	var r = _make("EC-10a")
	if r == null:
		return
	r.color = Color(0, 0, 0, 0)
	_assert_eq_float(0.0, r.color.r, "EC-10_transparent_r")
	_assert_eq_float(0.0, r.color.g, "EC-10_transparent_g")
	_assert_eq_float(0.0, r.color.b, "EC-10_transparent_b")
	_assert_eq_float(0.0, r.color.a, "EC-10_transparent_a")

func test_ec10_hdr_color() -> void:
	var r = _make("EC-10b")
	if r == null:
		return
	r.color = Color(2.0, -1.0, 0.5)
	_assert_eq_float(2.0, r.color.r, "EC-10_hdr_r")
	_assert_eq_float(-1.0, r.color.g, "EC-10_hdr_negative_g")
	_assert_eq_float(0.5, r.color.b, "EC-10_hdr_b")


# ---------------------------------------------------------------------------
# EC-11: Zero attack_range — valid for self-only attacks
# ---------------------------------------------------------------------------

func test_ec11_zero_attack_range() -> void:
	var r = _make("EC-11")
	if r == null:
		return
	r.attack_range = 0.0
	_assert_eq_float(0.0, r.attack_range, "EC-11_zero_range")

func test_ec11_negative_attack_range() -> void:
	var r = _make("EC-11b")
	if r == null:
		return
	r.attack_range = -10.0
	_assert_eq_float(-10.0, r.attack_range, "EC-11_negative_range")


# ---------------------------------------------------------------------------
# EC-12: Projectile speed 0 on PROJECTILE_SPIT — data inconsistency allowed
# ---------------------------------------------------------------------------

func test_ec12_stationary_projectile() -> void:
	var r = _make("EC-12")
	if r == null:
		return
	r.effect_type = "PROJECTILE_SPIT"
	r.projectile_speed = 0.0
	_assert_eq_string("PROJECTILE_SPIT", r.effect_type, "EC-12_type_projectile")
	_assert_eq_float(0.0, r.projectile_speed, "EC-12_speed_zero")


# ---------------------------------------------------------------------------
# EC-13: Negative startup_frames
# ---------------------------------------------------------------------------

func test_ec13_negative_startup_frames() -> void:
	var r = _make("EC-13")
	if r == null:
		return
	r.startup_frames = -1
	_assert_eq_int(-1, r.startup_frames, "EC-13_negative_startup")

func test_ec13_huge_startup_frames() -> void:
	var r = _make("EC-13b")
	if r == null:
		return
	r.startup_frames = 99999
	_assert_eq_int(99999, r.startup_frames, "EC-13_huge_startup")


# ---------------------------------------------------------------------------
# EC-14: duplicate() then modify copy — original unchanged
# ---------------------------------------------------------------------------

func test_ec14_duplicate_modifier_independence() -> void:
	var r = _make("EC-14")
	if r == null:
		return
	r.modifiers = {"poison": true, "poison_duration": 3.0}
	var dup = r.duplicate()
	dup.modifiers["poison"] = false
	dup.modifiers["new_key"] = "injected"
	_assert_true(r.modifiers.get("poison", false) == true, "EC-14_orig_poison_unchanged")
	_assert_false(r.modifiers.has("new_key"), "EC-14_orig_no_new_key")
	_assert_eq_int(2, r.modifiers.size(), "EC-14_orig_size_unchanged")

func test_ec14_duplicate_scalar_independence() -> void:
	var r = _make("EC-14b")
	if r == null:
		return
	r.damage = 10.0
	r.cooldown = 2.0
	r.attack_name = "Original"
	r.color = Color(1, 0, 0)
	var dup = r.duplicate()
	dup.damage = 999.0
	dup.cooldown = 0.0
	dup.attack_name = "Mutated"
	dup.color = Color(0, 1, 0)
	_assert_eq_float(10.0, r.damage, "EC-14_orig_damage_intact")
	_assert_eq_float(2.0, r.cooldown, "EC-14_orig_cooldown_intact")
	_assert_eq_string("Original", r.attack_name, "EC-14_orig_name_intact")
	_assert_eq_float(1.0, r.color.r, "EC-14_orig_color_r_intact")
	_assert_eq_float(0.0, r.color.g, "EC-14_orig_color_g_intact")


# ---------------------------------------------------------------------------
# ADV-01: Extremely large values — no overflow or crash
# ---------------------------------------------------------------------------

func test_adv01_extreme_damage() -> void:
	var r = _make("ADV-01")
	if r == null:
		return
	r.damage = 999999.0
	_assert_eq_float(999999.0, r.damage, "ADV-01_extreme_damage")

func test_adv01_extreme_knockback() -> void:
	var r = _make("ADV-01b")
	if r == null:
		return
	r.knockback_magnitude = 1e18
	_assert_true(r.knockback_magnitude > 1e17, "ADV-01_huge_knockback_stored")

func test_adv01_extreme_projectile_speed() -> void:
	var r = _make("ADV-01c")
	if r == null:
		return
	r.projectile_speed = 1e12
	_assert_true(r.projectile_speed > 1e11, "ADV-01_huge_proj_speed")


# ---------------------------------------------------------------------------
# ADV-02: Negative knockback_magnitude
# ---------------------------------------------------------------------------

func test_adv02_negative_knockback() -> void:
	var r = _make("ADV-02")
	if r == null:
		return
	r.knockback_magnitude = -10.0
	_assert_eq_float(-10.0, r.knockback_magnitude, "ADV-02_negative_kb")


# ---------------------------------------------------------------------------
# ADV-03: Default constructor produces valid resource (no null exports)
# ---------------------------------------------------------------------------

func test_adv03_default_no_null_exports() -> void:
	var r = _make("ADV-03")
	if r == null:
		return
	_assert_true(r.attack_name != null, "ADV-03_name_not_null")
	_assert_true(r.description != null, "ADV-03_desc_not_null")
	_assert_true(r.effect_type != null, "ADV-03_effect_not_null")
	_assert_true(r.knockback_direction != null, "ADV-03_kd_not_null")
	_assert_true(r.modifiers != null, "ADV-03_modifiers_not_null")
	_assert_true(r.color != null, "ADV-03_color_not_null")
	_assert_true(r.modifiers is Dictionary, "ADV-03_modifiers_is_dict")
	_assert_true(r.attack_name is String, "ADV-03_name_is_string")
	_assert_true(r.effect_type is String, "ADV-03_effect_is_string")
	_assert_true(r.knockback_direction is String, "ADV-03_kd_is_string")


# ---------------------------------------------------------------------------
# ADV-04: Property type coercion — int vs float boundaries
# ---------------------------------------------------------------------------

func test_adv04_int_assigned_to_float_prop() -> void:
	var r = _make("ADV-04a")
	if r == null:
		return
	r.damage = 5
	_assert_true(r.damage is float or r.damage == 5, "ADV-04_int_to_float_damage")
	_assert_eq_float(5.0, r.damage, "ADV-04_int_coerced_to_5.0")

func test_adv04_zero_int_to_float() -> void:
	var r = _make("ADV-04b")
	if r == null:
		return
	r.cooldown = 0
	_assert_eq_float(0.0, r.cooldown, "ADV-04_zero_int_to_float")

func test_adv04_attack_id_stays_int() -> void:
	var r = _make("ADV-04c")
	if r == null:
		return
	r.attack_id = 999
	_assert_eq_int(999, r.attack_id, "ADV-04_id_int")
	_assert_true(r.attack_id is int, "ADV-04_id_is_int")

func test_adv04_startup_frames_stays_int() -> void:
	var r = _make("ADV-04d")
	if r == null:
		return
	r.startup_frames = 60
	_assert_eq_int(60, r.startup_frames, "ADV-04_startup_int")
	_assert_true(r.startup_frames is int, "ADV-04_startup_is_int")


# ---------------------------------------------------------------------------
# ADV-05: Modifier mutation after clearing — set → clear → re-set
# ---------------------------------------------------------------------------

func test_adv05_modifier_clear_and_repopulate() -> void:
	var r = _make("ADV-05")
	if r == null:
		return
	r.modifiers = {"acid_on_hit": true, "acid_duration": 2.0}
	_assert_eq_int(2, r.modifiers.size(), "ADV-05_initial_size")
	r.modifiers = {}
	_assert_eq_int(0, r.modifiers.size(), "ADV-05_cleared_size")
	r.modifiers = {"slow": 0.5}
	_assert_eq_int(1, r.modifiers.size(), "ADV-05_repopulated_size")
	_assert_eq_float(0.5, r.modifiers["slow"], "ADV-05_repopulated_value")


# ---------------------------------------------------------------------------
# ADV-06: Modifier key collision — overwriting existing key
# ---------------------------------------------------------------------------

func test_adv06_modifier_key_overwrite() -> void:
	var r = _make("ADV-06")
	if r == null:
		return
	r.modifiers["damage_mult"] = 2.0
	r.modifiers["damage_mult"] = 3.0
	_assert_eq_float(3.0, r.modifiers["damage_mult"], "ADV-06_overwrite")
	_assert_eq_int(1, r.modifiers.size(), "ADV-06_single_key_after_overwrite")

func test_adv06_modifier_type_change_on_same_key() -> void:
	var r = _make("ADV-06b")
	if r == null:
		return
	r.modifiers["flex"] = true
	r.modifiers["flex"] = 42
	r.modifiers["flex"] = "now_a_string"
	_assert_eq_string("now_a_string", r.modifiers["flex"], "ADV-06_type_changed")


# ---------------------------------------------------------------------------
# ADV-07: Very long string values — no truncation
# ---------------------------------------------------------------------------

func test_adv07_long_attack_name() -> void:
	var r = _make("ADV-07")
	if r == null:
		return
	var long_name := ""
	for i in range(1000):
		long_name += "A"
	r.attack_name = long_name
	_assert_eq_int(1000, r.attack_name.length(), "ADV-07_1000_char_name")

func test_adv07_long_description() -> void:
	var r = _make("ADV-07b")
	if r == null:
		return
	var long_desc := ""
	for i in range(5000):
		long_desc += "X"
	r.description = long_desc
	_assert_eq_int(5000, r.description.length(), "ADV-07_5000_char_desc")


# ---------------------------------------------------------------------------
# ADV-08: Multiple independent instances don't share state
# ---------------------------------------------------------------------------

func test_adv08_instance_isolation() -> void:
	var r1 = _make("ADV-08a")
	if r1 == null:
		return
	var r2 = _make("ADV-08b")
	if r2 == null:
		return
	r1.damage = 100.0
	r1.attack_name = "Instance1"
	r1.modifiers = {"key1": true}
	r2.damage = 200.0
	r2.attack_name = "Instance2"
	r2.modifiers = {"key2": false}
	_assert_eq_float(100.0, r1.damage, "ADV-08_r1_damage")
	_assert_eq_float(200.0, r2.damage, "ADV-08_r2_damage")
	_assert_eq_string("Instance1", r1.attack_name, "ADV-08_r1_name")
	_assert_eq_string("Instance2", r2.attack_name, "ADV-08_r2_name")
	_assert_false(r1.modifiers.has("key2"), "ADV-08_r1_no_key2")
	_assert_false(r2.modifiers.has("key1"), "ADV-08_r2_no_key1")


# ---------------------------------------------------------------------------
# ADV-09: vfx_scale edge values
# ---------------------------------------------------------------------------

func test_adv09_zero_vfx_scale() -> void:
	var r = _make("ADV-09a")
	if r == null:
		return
	r.vfx_scale = 0.0
	_assert_eq_float(0.0, r.vfx_scale, "ADV-09_zero_vfx")

func test_adv09_negative_vfx_scale() -> void:
	var r = _make("ADV-09b")
	if r == null:
		return
	r.vfx_scale = -2.0
	_assert_eq_float(-2.0, r.vfx_scale, "ADV-09_negative_vfx")

func test_adv09_extreme_vfx_scale() -> void:
	var r = _make("ADV-09c")
	if r == null:
		return
	r.vfx_scale = 99999.0
	_assert_eq_float(99999.0, r.vfx_scale, "ADV-09_huge_vfx")


# ---------------------------------------------------------------------------
# ADV-10: Negative projectile_lifetime
# ---------------------------------------------------------------------------

func test_adv10_negative_projectile_lifetime() -> void:
	var r = _make("ADV-10")
	if r == null:
		return
	r.projectile_lifetime = -1.0
	_assert_eq_float(-1.0, r.projectile_lifetime, "ADV-10_negative_lifetime")

func test_adv10_zero_projectile_lifetime() -> void:
	var r = _make("ADV-10b")
	if r == null:
		return
	r.projectile_lifetime = 0.0
	_assert_eq_float(0.0, r.projectile_lifetime, "ADV-10_zero_lifetime")


# ---------------------------------------------------------------------------
# ADV-11: Combinatorial edge — all-zero combat config
# ---------------------------------------------------------------------------

func test_adv11_all_zero_combat() -> void:
	var r = _make("ADV-11")
	if r == null:
		return
	r.damage = 0.0
	r.cooldown = 0.0
	r.attack_range = 0.0
	r.startup_frames = 0
	r.knockback_magnitude = 0.0
	r.projectile_speed = 0.0
	r.projectile_lifetime = 0.0
	r.vfx_scale = 0.0
	_assert_eq_float(0.0, r.damage, "ADV-11_zero_damage")
	_assert_eq_float(0.0, r.cooldown, "ADV-11_zero_cooldown")
	_assert_eq_float(0.0, r.attack_range, "ADV-11_zero_range")
	_assert_eq_int(0, r.startup_frames, "ADV-11_zero_startup")
	_assert_eq_float(0.0, r.knockback_magnitude, "ADV-11_zero_kb")
	_assert_eq_float(0.0, r.projectile_speed, "ADV-11_zero_proj_spd")
	_assert_eq_float(0.0, r.projectile_lifetime, "ADV-11_zero_proj_life")
	_assert_eq_float(0.0, r.vfx_scale, "ADV-11_zero_vfx")


# ---------------------------------------------------------------------------
# ADV-12: Combinatorial — all-negative combat config
# ---------------------------------------------------------------------------

func test_adv12_all_negative_combat() -> void:
	var r = _make("ADV-12")
	if r == null:
		return
	r.damage = -1.0
	r.cooldown = -1.0
	r.attack_range = -1.0
	r.startup_frames = -1
	r.knockback_magnitude = -1.0
	r.projectile_speed = -1.0
	r.projectile_lifetime = -1.0
	r.vfx_scale = -1.0
	_assert_eq_float(-1.0, r.damage, "ADV-12_neg_damage")
	_assert_eq_float(-1.0, r.cooldown, "ADV-12_neg_cooldown")
	_assert_eq_float(-1.0, r.attack_range, "ADV-12_neg_range")
	_assert_eq_int(-1, r.startup_frames, "ADV-12_neg_startup")
	_assert_eq_float(-1.0, r.knockback_magnitude, "ADV-12_neg_kb")
	_assert_eq_float(-1.0, r.projectile_speed, "ADV-12_neg_proj_spd")
	_assert_eq_float(-1.0, r.projectile_lifetime, "ADV-12_neg_proj_life")
	_assert_eq_float(-1.0, r.vfx_scale, "ADV-12_neg_vfx")


# ---------------------------------------------------------------------------
# ADV-13: Determinism — same config, identical results across instances
# ---------------------------------------------------------------------------

func test_adv13_deterministic_defaults() -> void:
	var r1 = _make("ADV-13a")
	if r1 == null:
		return
	var r2 = _make("ADV-13b")
	if r2 == null:
		return
	_assert_eq_float(r1.damage, r2.damage, "ADV-13_same_damage")
	_assert_eq_float(r1.cooldown, r2.cooldown, "ADV-13_same_cooldown")
	_assert_eq_float(r1.attack_range, r2.attack_range, "ADV-13_same_range")
	_assert_eq_int(r1.startup_frames, r2.startup_frames, "ADV-13_same_startup")
	_assert_eq_float(r1.knockback_magnitude, r2.knockback_magnitude, "ADV-13_same_kb")
	_assert_eq_string(r1.knockback_direction, r2.knockback_direction, "ADV-13_same_kd")
	_assert_eq_float(r1.vfx_scale, r2.vfx_scale, "ADV-13_same_vfx")
	_assert_eq_int(r1.modifiers.size(), r2.modifiers.size(), "ADV-13_same_mod_size")


# ---------------------------------------------------------------------------
# ADV-14: Modifier with numeric string key — not confused with int
# ---------------------------------------------------------------------------

func test_adv14_numeric_string_modifier_key() -> void:
	var r = _make("ADV-14")
	if r == null:
		return
	r.modifiers["123"] = "numeric_key"
	_assert_eq("numeric_key", r.modifiers.get("123", null), "ADV-14_numeric_str_key")


# ---------------------------------------------------------------------------
# ADV-15: Reassign entire modifiers dict — old references invalidated
# ---------------------------------------------------------------------------

func test_adv15_modifiers_reassign() -> void:
	var r = _make("ADV-15")
	if r == null:
		return
	var old_dict := {"old_key": 1}
	r.modifiers = old_dict
	_assert_eq(1, r.modifiers["old_key"], "ADV-15_before_reassign")
	r.modifiers = {"new_key": 2}
	_assert_false(r.modifiers.has("old_key"), "ADV-15_old_key_gone")
	_assert_eq(2, r.modifiers["new_key"], "ADV-15_new_key_present")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackResourceAdversarialTests ===")

	# EC-01: Negative damage
	test_ec01_negative_damage()
	test_ec01_large_negative_damage()
	# EC-02: Zero/tiny/negative cooldown
	test_ec02_zero_cooldown()
	test_ec02_tiny_cooldown()
	test_ec02_negative_cooldown()
	# EC-03: Empty attack_name
	test_ec03_empty_attack_name()
	# EC-04: Unknown / empty / whitespace / special effect_type
	test_ec04_unknown_effect_type()
	test_ec04_empty_effect_type()
	test_ec04_whitespace_effect_type()
	test_ec04_special_chars_effect_type()
	# EC-05: Empty modifiers .get() fallback
	test_ec05_empty_modifiers_get_default()
	# EC-06: Large modifier dictionary
	test_ec06_large_modifier_dictionary()
	# EC-07: Nested / deep / array modifier values
	test_ec07_nested_modifier_dict()
	test_ec07_deeply_nested_modifier()
	test_ec07_modifier_array_value()
	# EC-08: Duplicate attack_ids
	test_ec08_duplicate_attack_ids()
	# EC-09: Unknown / empty knockback_direction
	test_ec09_unknown_knockback_direction()
	test_ec09_empty_knockback_direction()
	# EC-10: Color boundary and HDR
	test_ec10_transparent_color()
	test_ec10_hdr_color()
	# EC-11: Zero / negative attack_range
	test_ec11_zero_attack_range()
	test_ec11_negative_attack_range()
	# EC-12: Projectile speed 0 on PROJECTILE_SPIT
	test_ec12_stationary_projectile()
	# EC-13: Negative / huge startup_frames
	test_ec13_negative_startup_frames()
	test_ec13_huge_startup_frames()
	# EC-14: duplicate() independence (modifiers + scalars)
	test_ec14_duplicate_modifier_independence()
	test_ec14_duplicate_scalar_independence()
	# ADV-01: Extreme values
	test_adv01_extreme_damage()
	test_adv01_extreme_knockback()
	test_adv01_extreme_projectile_speed()
	# ADV-02: Negative knockback
	test_adv02_negative_knockback()
	# ADV-03: Default constructor no null exports
	test_adv03_default_no_null_exports()
	# ADV-04: Int/float coercion
	test_adv04_int_assigned_to_float_prop()
	test_adv04_zero_int_to_float()
	test_adv04_attack_id_stays_int()
	test_adv04_startup_frames_stays_int()
	# ADV-05: Modifier clear and repopulate
	test_adv05_modifier_clear_and_repopulate()
	# ADV-06: Modifier key collision / type change
	test_adv06_modifier_key_overwrite()
	test_adv06_modifier_type_change_on_same_key()
	# ADV-07: Long strings
	test_adv07_long_attack_name()
	test_adv07_long_description()
	# ADV-08: Instance isolation
	test_adv08_instance_isolation()
	# ADV-09: vfx_scale edge values
	test_adv09_zero_vfx_scale()
	test_adv09_negative_vfx_scale()
	test_adv09_extreme_vfx_scale()
	# ADV-10: Negative/zero projectile_lifetime
	test_adv10_negative_projectile_lifetime()
	test_adv10_zero_projectile_lifetime()
	# ADV-11: All-zero combat
	test_adv11_all_zero_combat()
	# ADV-12: All-negative combat
	test_adv12_all_negative_combat()
	# ADV-13: Deterministic defaults
	test_adv13_deterministic_defaults()
	# ADV-14: Numeric string modifier key
	test_adv14_numeric_string_modifier_key()
	# ADV-15: Modifier dict reassignment
	test_adv15_modifiers_reassign()

	print("AttackResourceAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
