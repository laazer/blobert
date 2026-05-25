#
# test_attack_resource.gd
#
# Behavioral tests for the AttackResource data model (Godot Resource).
# Spec: project_board/specs/attack_resource_spec.md (ATK-01 through ATK-09)
# Ticket: project_board/11_milestone_11_base_mutation_attacks/in_progress/04_attack_resource.md
#

class_name AttackResourceTests
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


# -- ATK-01: Class declaration, instantiation, Resource identity --

func test_atk01_instantiation() -> void:
	var script := _load_script()
	if script == null:
		_fail_test("ATK-01_load", _SCRIPT_PATH + " not loadable")
		return
	var r = script.new()
	_assert_true(r != null, "ATK-01_instantiate")
	_assert_true(r is Resource, "ATK-01_is_resource")
	_assert_true(is_instance_of(r, Resource), "ATK-01_is_instance_of_resource")


# -- ATK-02: Identity property defaults --

func test_atk02_identity_defaults() -> void:
	var r = _make("ATK-02")
	if r == null:
		return
	_assert_eq_int(0, r.attack_id, "ATK-02_attack_id_default")
	_assert_eq_string("", r.attack_name, "ATK-02_attack_name_default")
	_assert_eq_string("", r.description, "ATK-02_description_default")


func test_atk02_identity_assignable() -> void:
	var r = _make("ATK-02_assign")
	if r == null:
		return
	r.attack_id = 42
	r.attack_name = "Test Attack"
	r.description = "A test"
	_assert_eq_int(42, r.attack_id, "ATK-02_attack_id_set")
	_assert_eq_string("Test Attack", r.attack_name, "ATK-02_attack_name_set")
	_assert_eq_string("A test", r.description, "ATK-02_description_set")


# -- ATK-03: Effect type --

func test_atk03_effect_type_default() -> void:
	var r = _make("ATK-03_default")
	if r == null:
		return
	_assert_eq_string("", r.effect_type, "ATK-03_effect_type_default")


func test_atk03_effect_type_known_values() -> void:
	var r = _make("ATK-03_known")
	if r == null:
		return
	for val in ["MELEE_SWIPE", "PROJECTILE_SPIT", "SLAM_AOE", "LUNGE"]:
		r.effect_type = val
		_assert_eq_string(val, r.effect_type, "ATK-03_set_" + val)


func test_atk03_effect_type_extensibility() -> void:
	var r = _make("ATK-03_ext")
	if r == null:
		return
	r.effect_type = "FUTURE_BEAM"
	_assert_eq_string("FUTURE_BEAM", r.effect_type, "ATK-03_arbitrary_string_accepted")


# -- ATK-04: Core combat parameter defaults --

func test_atk04_combat_defaults() -> void:
	var r = _make("ATK-04")
	if r == null:
		return
	_assert_eq_float(1.0, r.damage, "ATK-04_damage_default")
	_assert_eq_float(0.8, r.cooldown, "ATK-04_cooldown_default")
	_assert_eq_float(1.5, r.attack_range, "ATK-04_attack_range_default")
	_assert_eq_int(0, r.startup_frames, "ATK-04_startup_frames_default")
	_assert_eq_float(0.0, r.knockback_magnitude, "ATK-04_knockback_magnitude_default")
	_assert_eq_string("away", r.knockback_direction, "ATK-04_knockback_direction_default")


func test_atk04_combat_assignable() -> void:
	var r = _make("ATK-04_assign")
	if r == null:
		return
	r.damage = 5.5
	r.cooldown = 2.0
	r.attack_range = 10.0
	r.startup_frames = 4
	r.knockback_magnitude = 200.0
	r.knockback_direction = "toward"
	_assert_eq_float(5.5, r.damage, "ATK-04_damage_set")
	_assert_eq_float(2.0, r.cooldown, "ATK-04_cooldown_set")
	_assert_eq_float(10.0, r.attack_range, "ATK-04_attack_range_set")
	_assert_eq_int(4, r.startup_frames, "ATK-04_startup_frames_set")
	_assert_eq_float(200.0, r.knockback_magnitude, "ATK-04_knockback_magnitude_set")
	_assert_eq_string("toward", r.knockback_direction, "ATK-04_knockback_direction_set")


func test_atk04_knockback_direction_values() -> void:
	var r = _make("ATK-04_kd")
	if r == null:
		return
	for val in ["away", "toward", "none"]:
		r.knockback_direction = val
		_assert_eq_string(val, r.knockback_direction, "ATK-04_kd_" + val)


# -- ATK-05: Projectile parameters --

func test_atk05_projectile_defaults() -> void:
	var r = _make("ATK-05")
	if r == null:
		return
	_assert_eq_float(0.0, r.projectile_speed, "ATK-05_projectile_speed_default")
	_assert_eq_float(2.0, r.projectile_lifetime, "ATK-05_projectile_lifetime_default")


func test_atk05_projectile_assignable() -> void:
	var r = _make("ATK-05_assign")
	if r == null:
		return
	r.projectile_speed = 300.0
	r.projectile_lifetime = 5.0
	_assert_eq_float(300.0, r.projectile_speed, "ATK-05_projectile_speed_set")
	_assert_eq_float(5.0, r.projectile_lifetime, "ATK-05_projectile_lifetime_set")


# -- ATK-06: Visual feedback properties --

func test_atk06_visual_defaults() -> void:
	var r = _make("ATK-06")
	if r == null:
		return
	_assert_eq_float(1.0, r.color.r, "ATK-06_color_r_default")
	_assert_eq_float(1.0, r.color.g, "ATK-06_color_g_default")
	_assert_eq_float(1.0, r.color.b, "ATK-06_color_b_default")
	_assert_eq_float(1.0, r.color.a, "ATK-06_color_a_default")
	_assert_eq_float(1.0, r.vfx_scale, "ATK-06_vfx_scale_default")


func test_atk06_visual_assignable() -> void:
	var r = _make("ATK-06_assign")
	if r == null:
		return
	r.color = Color(0.5, 0.3, 0.7, 0.9)
	r.vfx_scale = 2.5
	_assert_eq_float(0.5, r.color.r, "ATK-06_color_r_set")
	_assert_eq_float(0.3, r.color.g, "ATK-06_color_g_set")
	_assert_eq_float(0.7, r.color.b, "ATK-06_color_b_set")
	_assert_eq_float(0.9, r.color.a, "ATK-06_color_a_set")
	_assert_eq_float(2.5, r.vfx_scale, "ATK-06_vfx_scale_set")


# -- ATK-07: Modifiers dictionary --

func test_atk07_modifiers_default() -> void:
	var r = _make("ATK-07_default")
	if r == null:
		return
	_assert_true(r.modifiers is Dictionary, "ATK-07_modifiers_is_dict")
	_assert_eq_int(0, r.modifiers.size(), "ATK-07_modifiers_empty")


func test_atk07_modifiers_set_get() -> void:
	var r = _make("ATK-07_setget")
	if r == null:
		return
	r.modifiers["acid_on_hit"] = true
	r.modifiers["acid_duration"] = 2.0
	r.modifiers["acid_dps"] = 0.3
	_assert_true(r.modifiers["acid_on_hit"] == true, "ATK-07_bool_value")
	_assert_eq_float(2.0, r.modifiers["acid_duration"], "ATK-07_float_value")
	_assert_eq_float(0.3, r.modifiers["acid_dps"], "ATK-07_float_value_2")


func test_atk07_modifiers_get_nonexistent() -> void:
	var r = _make("ATK-07_nokey")
	if r == null:
		return
	var fallback = r.modifiers.get("nonexistent_key", -999)
	_assert_eq(-999, fallback, "ATK-07_get_returns_default")


func test_atk07_modifiers_coexist() -> void:
	var r = _make("ATK-07_coexist")
	if r == null:
		return
	r.modifiers = {
		"acid_on_hit": true,
		"acid_duration": 2.0,
		"slow": 0.7,
		"slow_duration": 2.0,
		"weaken": true,
	}
	_assert_eq_int(5, r.modifiers.size(), "ATK-07_five_keys")
	_assert_true(r.modifiers["acid_on_hit"] == true, "ATK-07_coexist_acid")
	_assert_eq_float(0.7, r.modifiers["slow"], "ATK-07_coexist_slow")
	_assert_true(r.modifiers["weaken"] == true, "ATK-07_coexist_weaken")


# -- ATK-08: Serialization (duplicate round-trip) --

func test_atk08_duplicate_preserves() -> void:
	var r = _make("ATK-08_dup")
	if r == null:
		return
	r.attack_id = 101
	r.attack_name = "Claw Swipe"
	r.description = "Quick melee swipe at close range"
	r.effect_type = "MELEE_SWIPE"
	r.damage = 2.0
	r.cooldown = 0.8
	r.attack_range = 1.5
	r.startup_frames = 2
	r.knockback_magnitude = 100.0
	r.knockback_direction = "away"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color(0.8, 0.2, 0.1)
	r.vfx_scale = 1.0
	r.modifiers = {"test_key": 42}

	var dup = r.duplicate()
	_assert_true(dup != null, "ATK-08_dup_not_null")
	_assert_true(dup is Resource, "ATK-08_dup_is_resource")
	_assert_eq_int(101, dup.attack_id, "ATK-08_dup_attack_id")
	_assert_eq_string("Claw Swipe", dup.attack_name, "ATK-08_dup_attack_name")
	_assert_eq_string("Quick melee swipe at close range", dup.description, "ATK-08_dup_description")
	_assert_eq_string("MELEE_SWIPE", dup.effect_type, "ATK-08_dup_effect_type")
	_assert_eq_float(2.0, dup.damage, "ATK-08_dup_damage")
	_assert_eq_float(0.8, dup.cooldown, "ATK-08_dup_cooldown")
	_assert_eq_float(1.5, dup.attack_range, "ATK-08_dup_attack_range")
	_assert_eq_int(2, dup.startup_frames, "ATK-08_dup_startup_frames")
	_assert_eq_float(100.0, dup.knockback_magnitude, "ATK-08_dup_knockback_mag")
	_assert_eq_string("away", dup.knockback_direction, "ATK-08_dup_knockback_dir")
	_assert_eq_float(0.0, dup.projectile_speed, "ATK-08_dup_proj_speed")
	_assert_eq_float(2.0, dup.projectile_lifetime, "ATK-08_dup_proj_lifetime")
	_assert_eq_float(0.8, dup.color.r, "ATK-08_dup_color_r")
	_assert_eq_float(0.2, dup.color.g, "ATK-08_dup_color_g")
	_assert_eq_float(0.1, dup.color.b, "ATK-08_dup_color_b")
	_assert_eq_float(1.0, dup.vfx_scale, "ATK-08_dup_vfx_scale")
	_assert_eq(42, dup.modifiers.get("test_key", null), "ATK-08_dup_modifier")
	_assert_true(dup != r, "ATK-08_dup_not_same_ref")


func test_atk08_duplicate_independence() -> void:
	var r = _make("ATK-08_indep")
	if r == null:
		return
	r.attack_id = 200
	r.attack_name = "Original"
	r.modifiers = {"key": "original"}
	var dup = r.duplicate()
	dup.attack_id = 999
	dup.attack_name = "Modified"
	dup.modifiers["key"] = "changed"
	_assert_eq_int(200, r.attack_id, "ATK-08_orig_id_unchanged")
	_assert_eq_string("Original", r.attack_name, "ATK-08_orig_name_unchanged")


# -- ATK-09: Four example attack configurations --

func _configure_claw_swipe(r: Resource) -> void:
	r.attack_id = 101
	r.attack_name = "Claw Swipe"
	r.description = "Quick melee swipe at close range"
	r.effect_type = "MELEE_SWIPE"
	r.damage = 2.0
	r.cooldown = 0.8
	r.attack_range = 1.5
	r.startup_frames = 2
	r.knockback_magnitude = 100.0
	r.knockback_direction = "away"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color(0.8, 0.2, 0.1)
	r.vfx_scale = 1.0
	r.modifiers = {}


func test_atk09_claw_swipe() -> void:
	var r = _make("ATK-09_claw")
	if r == null:
		return
	_configure_claw_swipe(r)
	_assert_eq_int(101, r.attack_id, "ATK-09_claw_id")
	_assert_eq_string("Claw Swipe", r.attack_name, "ATK-09_claw_name")
	_assert_eq_string("Quick melee swipe at close range", r.description, "ATK-09_claw_desc")
	_assert_eq_string("MELEE_SWIPE", r.effect_type, "ATK-09_claw_effect")
	_assert_eq_float(2.0, r.damage, "ATK-09_claw_damage")
	_assert_eq_float(0.8, r.cooldown, "ATK-09_claw_cooldown")
	_assert_eq_float(1.5, r.attack_range, "ATK-09_claw_range")
	_assert_eq_int(2, r.startup_frames, "ATK-09_claw_startup")
	_assert_eq_float(100.0, r.knockback_magnitude, "ATK-09_claw_kb_mag")
	_assert_eq_string("away", r.knockback_direction, "ATK-09_claw_kb_dir")
	_assert_eq_float(0.0, r.projectile_speed, "ATK-09_claw_proj_spd")
	_assert_eq_float(2.0, r.projectile_lifetime, "ATK-09_claw_proj_life")
	_assert_eq_float(0.8, r.color.r, "ATK-09_claw_color_r")
	_assert_eq_float(0.2, r.color.g, "ATK-09_claw_color_g")
	_assert_eq_float(0.1, r.color.b, "ATK-09_claw_color_b")
	_assert_eq_float(1.0, r.vfx_scale, "ATK-09_claw_vfx")
	_assert_eq_int(0, r.modifiers.size(), "ATK-09_claw_no_modifiers")


func test_atk09_acid_spit() -> void:
	var r = _make("ATK-09_acid")
	if r == null:
		return
	r.attack_id = 102
	r.attack_name = "Acid Spit"
	r.description = "Ranged acid projectile with DOT"
	r.effect_type = "PROJECTILE_SPIT"
	r.damage = 1.5
	r.cooldown = 1.2
	r.attack_range = 15.0
	r.startup_frames = 0
	r.knockback_magnitude = 50.0
	r.knockback_direction = "away"
	r.projectile_speed = 250.0
	r.projectile_lifetime = 2.0
	r.color = Color(0.2, 0.8, 0.1)
	r.vfx_scale = 1.0
	r.modifiers = {"acid_on_hit": true, "acid_duration": 2.0, "acid_dps": 0.3}

	_assert_eq_int(102, r.attack_id, "ATK-09_acid_id")
	_assert_eq_string("Acid Spit", r.attack_name, "ATK-09_acid_name")
	_assert_eq_string("PROJECTILE_SPIT", r.effect_type, "ATK-09_acid_effect")
	_assert_eq_float(1.5, r.damage, "ATK-09_acid_damage")
	_assert_eq_float(1.2, r.cooldown, "ATK-09_acid_cooldown")
	_assert_eq_float(15.0, r.attack_range, "ATK-09_acid_range")
	_assert_eq_float(250.0, r.projectile_speed, "ATK-09_acid_proj_spd")
	_assert_eq_float(50.0, r.knockback_magnitude, "ATK-09_acid_kb_mag")
	_assert_eq_float(0.2, r.color.r, "ATK-09_acid_color_r")
	_assert_eq_float(0.8, r.color.g, "ATK-09_acid_color_g")
	_assert_eq_float(0.1, r.color.b, "ATK-09_acid_color_b")
	_assert_true(r.modifiers.get("acid_on_hit", false) == true, "ATK-09_acid_mod_on_hit")
	_assert_eq_float(2.0, r.modifiers.get("acid_duration", 0.0), "ATK-09_acid_mod_duration")
	_assert_eq_float(0.3, r.modifiers.get("acid_dps", 0.0), "ATK-09_acid_mod_dps")


func test_atk09_carapace_slam() -> void:
	var r = _make("ATK-09_carapace")
	if r == null:
		return
	r.attack_id = 103
	r.attack_name = "Carapace Slam"
	r.description = "Heavy charge into ground slam"
	r.effect_type = "SLAM_AOE"
	r.damage = 35.0
	r.cooldown = 4.0
	r.attack_range = 6.0
	r.startup_frames = 6
	r.knockback_magnitude = 22.0
	r.knockback_direction = "away"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color(0.6, 0.4, 0.2)
	r.vfx_scale = 1.5
	r.modifiers = {}

	_assert_eq_int(103, r.attack_id, "ATK-09_carapace_id")
	_assert_eq_string("Carapace Slam", r.attack_name, "ATK-09_carapace_name")
	_assert_eq_string("SLAM_AOE", r.effect_type, "ATK-09_carapace_effect")
	_assert_eq_float(35.0, r.damage, "ATK-09_carapace_damage")
	_assert_eq_float(4.0, r.cooldown, "ATK-09_carapace_cooldown")
	_assert_eq_float(6.0, r.attack_range, "ATK-09_carapace_range")
	_assert_eq_int(6, r.startup_frames, "ATK-09_carapace_startup")
	_assert_eq_float(22.0, r.knockback_magnitude, "ATK-09_carapace_kb_mag")
	_assert_eq_string("away", r.knockback_direction, "ATK-09_carapace_kb_dir")
	_assert_eq_float(1.5, r.vfx_scale, "ATK-09_carapace_vfx")
	_assert_eq_float(0.6, r.color.r, "ATK-09_carapace_color_r")
	_assert_eq_float(0.4, r.color.g, "ATK-09_carapace_color_g")
	_assert_eq_float(0.2, r.color.b, "ATK-09_carapace_color_b")
	_assert_eq_int(0, r.modifiers.size(), "ATK-09_carapace_no_modifiers")


func test_atk09_adhesion_lunge() -> void:
	var r = _make("ATK-09_adhesion")
	if r == null:
		return
	r.attack_id = 104
	r.attack_name = "Adhesion Lunge"
	r.description = "Short dash forward with root on hit"
	r.effect_type = "LUNGE"
	r.damage = 0.0
	r.cooldown = 2.0
	r.attack_range = 3.0
	r.startup_frames = 0
	r.knockback_magnitude = 0.0
	r.knockback_direction = "none"
	r.projectile_speed = 0.0
	r.projectile_lifetime = 2.0
	r.color = Color(0.9, 0.7, 0.2)
	r.vfx_scale = 1.0
	r.modifiers = {"root_duration": 0.5}

	_assert_eq_int(104, r.attack_id, "ATK-09_adhesion_id")
	_assert_eq_string("Adhesion Lunge", r.attack_name, "ATK-09_adhesion_name")
	_assert_eq_string("LUNGE", r.effect_type, "ATK-09_adhesion_effect")
	_assert_eq_float(0.0, r.damage, "ATK-09_adhesion_damage")
	_assert_eq_float(2.0, r.cooldown, "ATK-09_adhesion_cooldown")
	_assert_eq_float(3.0, r.attack_range, "ATK-09_adhesion_range")
	_assert_eq_float(0.0, r.knockback_magnitude, "ATK-09_adhesion_kb_mag")
	_assert_eq_string("none", r.knockback_direction, "ATK-09_adhesion_kb_dir")
	_assert_eq_float(0.9, r.color.r, "ATK-09_adhesion_color_r")
	_assert_eq_float(0.7, r.color.g, "ATK-09_adhesion_color_g")
	_assert_eq_float(0.2, r.color.b, "ATK-09_adhesion_color_b")
	_assert_eq_float(0.5, r.modifiers.get("root_duration", 0.0), "ATK-09_adhesion_mod_root")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackResourceTests ===")

	# ATK-01
	test_atk01_instantiation()
	# ATK-02
	test_atk02_identity_defaults()
	test_atk02_identity_assignable()
	# ATK-03
	test_atk03_effect_type_default()
	test_atk03_effect_type_known_values()
	test_atk03_effect_type_extensibility()
	# ATK-04
	test_atk04_combat_defaults()
	test_atk04_combat_assignable()
	test_atk04_knockback_direction_values()
	# ATK-05
	test_atk05_projectile_defaults()
	test_atk05_projectile_assignable()
	# ATK-06
	test_atk06_visual_defaults()
	test_atk06_visual_assignable()
	# ATK-07
	test_atk07_modifiers_default()
	test_atk07_modifiers_set_get()
	test_atk07_modifiers_get_nonexistent()
	test_atk07_modifiers_coexist()
	# ATK-08
	test_atk08_duplicate_preserves()
	test_atk08_duplicate_independence()
	# ATK-09
	test_atk09_claw_swipe()
	test_atk09_acid_spit()
	test_atk09_carapace_slam()
	test_atk09_adhesion_lunge()

	print("AttackResourceTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
