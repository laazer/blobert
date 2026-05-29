#
# test_acid_claw_database_registration.gd
#
# AttackDatabase registration tests for the acid+claw fusion attack.
# Verifies all 13 field assertions (AC-5a through AC-5l, AC-5o) covering the
# normative M12-04 stat block: attack_id=101, name="Venomous Shred",
# effect_type="MELEE_SWIPE_COMBO", combo_hits=3, damage=1.8, cooldown=2.0,
# range=1.2, knockback=80.0, and modifier keys.
#
# Spec: project_board/specs/acid_claw_fusion_attack_spec.md
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/in_progress/04_acid_claw_fusion_attack.md
# Traceability: AC-5 (AC-5a through AC-5l, AC-5o), AC-DD-1
#
# NOTE: Tests will be RED until implementation updates attack_database.gd
# to register acid_claw with MELEE_SWIPE_COMBO and the normative M12-04 stats.
#
# Companion file: test_acid_claw_combo_attack.gd (AC-1..AC-4, AC-6, non-regression)
#

class_name AcidClawDatabaseRegistrationTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers — delegate to shared harness to avoid cross-file DRY violation
# ---------------------------------------------------------------------------

func _make_db(test_label: String) -> Node:
	return AttackDatabaseHarness.make_db(test_label, _fail_test)


func _free_db(db: Node) -> void:
	AttackDatabaseHarness.free_db(db)


# ---------------------------------------------------------------------------
# AC-5: AttackDatabase registration for acid_claw (normative M12-04 stat block)
# ---------------------------------------------------------------------------

func test_ac5a_acid_claw_damage_1_8() -> void:
	# AC-5a: damage == 1.8 (supersedes M12-02 placeholder 4.0)
	var db = _make_db("AC-5a")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5a", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_float(1.8, res.damage, "AC-5a_damage_1_8")
	_free_db(db)


func test_ac5b_acid_claw_cooldown_2_0() -> void:
	# AC-5b: cooldown == 2.0 (supersedes M12-02 placeholder 1.5)
	var db = _make_db("AC-5b")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5b", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_float(2.0, res.cooldown, "AC-5b_cooldown_2_0")
	_free_db(db)


func test_ac5c_acid_claw_range_1_2() -> void:
	# AC-5c: attack_range == 1.2 (supersedes M12-02 placeholder 1.5)
	var db = _make_db("AC-5c")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5c", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_float(1.2, res.attack_range, "AC-5c_range_1_2")
	_free_db(db)


func test_ac5d_acid_claw_knockback_80_0() -> void:
	# AC-5d: knockback_magnitude == 80.0 (normative — do not reduce; supersedes M12-02 placeholder 3.0)
	var db = _make_db("AC-5d")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5d", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_float(80.0, res.knockback_magnitude, "AC-5d_knockback_80")
	_free_db(db)


func test_ac5e_acid_claw_effect_type_melee_swipe_combo() -> void:
	# AC-5e: effect_type == "MELEE_SWIPE_COMBO" (supersedes M12-02 placeholder "MELEE_SWIPE")
	var db = _make_db("AC-5e")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5e", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_string("MELEE_SWIPE_COMBO", res.effect_type, "AC-5e_effect_type_combo")
	_free_db(db)


func test_ac5f_acid_claw_combo_hits_3() -> void:
	# AC-5f: combo_hits == 3
	var db = _make_db("AC-5f")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5f", "acid_claw not registered")
		_free_db(db)
		return
	var combo_hits = res.get("combo_hits")
	_assert_true(combo_hits != null, "AC-5f_combo_hits_field_exists")
	if combo_hits != null:
		_assert_eq_int(3, combo_hits, "AC-5f_combo_hits_3")
	_free_db(db)


func test_ac5g_acid_claw_attack_id_101() -> void:
	# AC-5g: attack_id == 101 (unchanged from M12-02)
	var db = _make_db("AC-5g")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5g", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_int(101, res.attack_id, "AC-5g_id_101")
	_free_db(db)


func test_ac5h_acid_claw_name_venomous_shred() -> void:
	# AC-5h: attack_name == "Venomous Shred" (supersedes M12-02 "Toxic Slash")
	var db = _make_db("AC-5h")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5h", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_string("Venomous Shred", res.attack_name, "AC-5h_name_venomous_shred")
	_free_db(db)


func test_ac5i_acid_claw_modifier_acid_on_hit_true() -> void:
	# AC-5i: modifiers["acid_on_hit"] == true
	var db = _make_db("AC-5i")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5i", "acid_claw not registered")
		_free_db(db)
		return
	_assert_true(
		res.modifiers.has("acid_on_hit") and res.modifiers["acid_on_hit"] == true,
		"AC-5i_acid_on_hit_true"
	)
	_free_db(db)


func test_ac5j_acid_claw_modifier_acid_duration_2_5() -> void:
	# AC-5j: modifiers["acid_duration"] == 2.5 (supersedes M12-02 placeholder 2.0)
	var db = _make_db("AC-5j")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5j", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_float(2.5, res.modifiers.get("acid_duration", -1.0), "AC-5j_acid_duration_2_5")
	_free_db(db)


func test_ac5k_acid_claw_modifier_acid_dps_0_4() -> void:
	# AC-5k: modifiers["acid_dps"] ~= 0.4 (supersedes M12-02 placeholder ~0.8)
	var db = _make_db("AC-5k")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5k", "acid_claw not registered")
		_free_db(db)
		return
	_assert_approx(0.4, res.modifiers.get("acid_dps", -1.0), "AC-5k_acid_dps_0_4")
	_free_db(db)


func test_ac5l_acid_claw_modifier_combo_frame_interval_6() -> void:
	# AC-5l: modifiers["combo_frame_interval"] == 6
	var db = _make_db("AC-5l")
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test("AC-5l", "acid_claw not registered")
		_free_db(db)
		return
	_assert_eq_int(6, res.modifiers.get("combo_frame_interval", -1), "AC-5l_combo_frame_interval_6")
	_free_db(db)


func test_ac5o_other_fused_attacks_unchanged() -> void:
	# AC-5o: Other 5 fused registrations are unchanged (spot check effect_type)
	var db = _make_db("AC-5o")
	if db == null:
		return
	var adhesion_claw = db.get_fused_attack("adhesion", "claw")
	var carapace_claw = db.get_fused_attack("carapace", "claw")
	var acid_adhesion = db.get_fused_attack("acid", "adhesion")
	var acid_carapace = db.get_fused_attack("acid", "carapace")
	var adhesion_carapace = db.get_fused_attack("adhesion", "carapace")
	if adhesion_claw != null:
		_assert_eq_string("MELEE_SWIPE", adhesion_claw.effect_type, "AC-5o_adhesion_claw_type_unchanged")
	if carapace_claw != null:
		_assert_eq_string("SLAM_AOE", carapace_claw.effect_type, "AC-5o_carapace_claw_type_unchanged")
	if acid_adhesion != null:
		_assert_eq_string("PROJECTILE_SPIT", acid_adhesion.effect_type, "AC-5o_acid_adhesion_type_unchanged")
	if acid_carapace != null:
		_assert_eq_string("SLAM_AOE", acid_carapace.effect_type, "AC-5o_acid_carapace_type_unchanged")
	if adhesion_carapace != null:
		_assert_eq_string("SLAM_AOE", adhesion_carapace.effect_type, "AC-5o_adhesion_carapace_type_unchanged")
	_free_db(db)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AcidClawDatabaseRegistrationTests ===")

	test_ac5a_acid_claw_damage_1_8()
	test_ac5b_acid_claw_cooldown_2_0()
	test_ac5c_acid_claw_range_1_2()
	test_ac5d_acid_claw_knockback_80_0()
	test_ac5e_acid_claw_effect_type_melee_swipe_combo()
	test_ac5f_acid_claw_combo_hits_3()
	test_ac5g_acid_claw_attack_id_101()
	test_ac5h_acid_claw_name_venomous_shred()
	test_ac5i_acid_claw_modifier_acid_on_hit_true()
	test_ac5j_acid_claw_modifier_acid_duration_2_5()
	test_ac5k_acid_claw_modifier_acid_dps_0_4()
	test_ac5l_acid_claw_modifier_combo_frame_interval_6()
	test_ac5o_other_fused_attacks_unchanged()

	print("AcidClawDatabaseRegistrationTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
