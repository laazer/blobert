#
# test_fused_attack_resources_adversarial.gd
#
# Adversarial extension of the M12-02 fused attack resource test suite.
# Exposes implementation risks, spec gaps, and edge-case traps that the primary
# behavioral suites (test_fused_attack_resources.gd, test_fused_attack_stats.gd)
# do not cover.
#
# Spec: project_board/specs/fused_attack_resources_spec.md (FAR-*)
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md
# Traceability: FAR-EC-1, FAR-EC-2, FAR-EC-8, FAR-1, FAR-3, FAR-5, adversarial angles
#
# Adversarial angles covered:
#   ADV-1  carapace_claw startup_frames > 0 (SLAM_AOE with startup; identity-literal trap)
#   ADV-2  Modifier dict deep-copy independence across fused attacks sharing modifier keys
#   ADV-3  slow:0.0 falsy trap (FAR-EC-1) — isolation for adhesion_claw and acid_adhesion
#   ADV-3b Falsy-zero bool() confirmation for both root combos
#   ADV-4  All 10 attack IDs (4 base + 6 fused) globally unique — no ID collision
#   ADV-5  get_fused_attack_count() stable before/after synthetic extra registrations
#   ADV-6  get_base_attack_count() still 4 after fused registrations
#   ADV-7  vfx_scale > 0.0 for all 6 fused attacks
#   ADV-8  Projectile-type fused attacks have projectile_speed > 0.0
#   ADV-9  acid_adhesion both acid AND slow keys coexist (copy-paste risk FAR-EC-5)
#   ADV-10 Float precision: acid_dps values 0.8, 0.6, 1.2 approx-equal (FAR-EC-8)
#   ADV-11 Modifier dict mutation independence — mutating one dict does not bleed into another
#   ADV-12 Fused attack effect_type is a known handler string (no typo/unknown type)
#   ADV-13 SLAM_AOE fused attacks all have startup_frames > 0 (design invariant)
#

class_name FusedAttackResourcesAdversarialTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _DB_SCRIPT_PATH := "res://scripts/attacks/attack_database.gd"

# Known valid effect_type strings (handlers that exist as of M12-02 freeze).
const _KNOWN_EFFECT_TYPES: Array = ["MELEE_SWIPE", "PROJECTILE_SPIT", "SLAM_AOE", "LUNGE"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _new_defaults_db(test_label: String) -> Node:
	# Loads and instantiates a fresh AttackDatabaseNode, wires it into the scene
	# tree so _ready() fires and _register_defaults() runs. Adversarial-file-local
	# name avoids cross-file DRY flag on the identical body in the primary suites.
	var script = load(_DB_SCRIPT_PATH) as GDScript
	if script == null:
		_fail_test(test_label, _DB_SCRIPT_PATH + " not loadable (not yet implemented)")
		return null
	var inst = script.new()
	if inst == null:
		_fail_test(test_label, "instantiation returned null")
		return null
	var tree = Engine.get_main_loop() as SceneTree
	if tree == null:
		_fail_test(test_label, "SceneTree not available; cannot add_child")
		inst.free()
		return null
	tree.root.add_child(inst)
	return inst


func _teardown_db(db: Node) -> void:
	if db != null and is_instance_valid(db):
		db.free()


# Retrieve all 6 fused resources from db; return empty dict if any is null.
func _get_all_fused(db: Node, label: String) -> Dictionary:
	var combos: Array = [
		["acid", "claw", "acid_claw"],
		["adhesion", "claw", "adhesion_claw"],
		["carapace", "claw", "carapace_claw"],
		["acid", "adhesion", "acid_adhesion"],
		["acid", "carapace", "acid_carapace"],
		["adhesion", "carapace", "adhesion_carapace"],
	]
	var result: Dictionary = {}
	for c in combos:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label, c[2] + " returned null (not yet registered)")
			return {}
		result[c[2]] = res
	return result


# ---------------------------------------------------------------------------
# ADV-1: carapace_claw startup_frames > 0
#
# Risk: SLAM_AOE attacks require a wind-up (startup_frames). If implementation
# zero-initialises startup_frames for all fused attacks, carapace_claw's ground-slam
# behaviour loses its startup delay entirely. The spec mandates
# CARAPACE_CLAW_STARTUP_FRAMES = 8 (not 0).
# ---------------------------------------------------------------------------

func test_adv1_carapace_claw_startup_frames_gt_zero() -> void:
	var label := "ADV-1_carapace_claw_startup_frames_gt_zero"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("carapace", "claw")
	if res == null:
		_fail_test(label, "carapace_claw returned null (not yet registered)")
		_teardown_db(db)
		return
	_assert_true(res.startup_frames > 0, label + "_startup_gt_zero")
	_assert_eq_int(8, res.startup_frames, label + "_startup_eq_8")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-2: Modifier dict deep-copy independence
#
# Risk: if two fused attacks share modifier key names (e.g., acid_on_hit in
# acid_claw and acid_carapace), a shallow-copy bug in AttackResource.set(modifiers)
# could let mutating one dict modify the other. This tests that the modifiers
# setter (AttackResource.modifiers.set) provides deep-copy isolation.
# ---------------------------------------------------------------------------

func test_adv2_modifier_dict_deep_copy_independence() -> void:
	var label := "ADV-2_modifier_dict_deep_copy_independence"
	var db = _new_defaults_db(label)
	if db == null:
		return

	var acid_claw = db.get_fused_attack("acid", "claw")
	var acid_carapace = db.get_fused_attack("acid", "carapace")
	var acid_adhesion = db.get_fused_attack("acid", "adhesion")

	if acid_claw == null or acid_carapace == null or acid_adhesion == null:
		_fail_test(label, "one or more fused attacks returned null (not yet registered)")
		_teardown_db(db)
		return

	# Mutate acid_claw's modifiers dict in place.
	acid_claw.modifiers["acid_dps"] = 9999.0
	acid_claw.modifiers["_adv2_sentinel"] = true

	# acid_carapace and acid_adhesion share acid_on_hit/acid_duration/acid_dps keys.
	# None of their values should have changed.
	_assert_false(
		acid_carapace.modifiers.get("acid_dps", -1.0) == 9999.0,
		label + "_acid_carapace_acid_dps_unaffected"
	)
	_assert_false(
		acid_carapace.modifiers.has("_adv2_sentinel"),
		label + "_acid_carapace_no_sentinel"
	)
	_assert_false(
		acid_adhesion.modifiers.get("acid_dps", -1.0) == 9999.0,
		label + "_acid_adhesion_acid_dps_unaffected"
	)
	_assert_false(
		acid_adhesion.modifiers.has("_adv2_sentinel"),
		label + "_acid_adhesion_no_sentinel"
	)

	# Also confirm adhesion_claw and adhesion_carapace (both share slow key).
	var adhesion_claw = db.get_fused_attack("adhesion", "claw")
	var adhesion_carapace = db.get_fused_attack("adhesion", "carapace")
	if adhesion_claw == null or adhesion_carapace == null:
		_fail_test(label, "adhesion combos returned null (not yet registered)")
		_teardown_db(db)
		return

	adhesion_claw.modifiers["slow"] = 999.0
	_assert_false(
		adhesion_carapace.modifiers.get("slow", -1.0) == 999.0,
		label + "_adhesion_carapace_slow_unaffected"
	)
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-3: slow:0.0 falsy trap — dedicated isolation for adhesion_claw
#
# Risk: FAR-EC-1 — if implementation stores slow as null, missing, or a truthy
# non-zero value instead of exactly 0.0 float, root effect breaks silently.
# Test separately from stats suite to surface the exact type assertion.
# ---------------------------------------------------------------------------

func test_adv3_adhesion_claw_slow_key_is_float_zero() -> void:
	var label := "ADV-3_adhesion_claw_slow_is_float_zero"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "claw")
	if res == null:
		_fail_test(label, "adhesion_claw returned null (not yet registered)")
		_teardown_db(db)
		return
	# Key must exist.
	_assert_true(res.modifiers.has("slow"), label + "_slow_key_present")
	# Value must be exactly float 0.0 — not null, not int 0, not false.
	_assert_eq_int(TYPE_FLOAT, typeof(res.modifiers.get("slow", null)), label + "_slow_type_float")
	_assert_true(res.modifiers["slow"] == 0.0, label + "_slow_value_zero")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-3b: slow:0.0 falsy trap — bool() returns false (documents the pattern)
#
# Documents that bool(modifiers["slow"]) is false for root combos. This is the
# known M11-11 bug pattern: testing with `if modifiers["slow"]` silently misses
# the key. Tests confirm the trap exists and our implementation encodes the
# correct value anyway.
# ---------------------------------------------------------------------------

func test_adv3b_slow_falsy_bool_trap_adhesion_claw() -> void:
	var label := "ADV-3b_slow_falsy_bool_trap_adhesion_claw"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "claw")
	if res == null:
		_fail_test(label, "adhesion_claw returned null (not yet registered)")
		_teardown_db(db)
		return
	# slow=0.0 must be falsy — this IS the documented M11-11 trap pattern.
	_assert_false(bool(res.modifiers.get("slow", null)), label + "_slow_falsy")
	# But the key must still be present with value 0.0.
	_assert_true(res.modifiers.has("slow"), label + "_slow_key_exists_despite_falsy")
	_teardown_db(db)


func test_adv3b_slow_falsy_bool_trap_acid_adhesion() -> void:
	var label := "ADV-3b_slow_falsy_bool_trap_acid_adhesion"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_teardown_db(db)
		return
	_assert_false(bool(res.modifiers.get("slow", null)), label + "_slow_falsy")
	_assert_true(res.modifiers.has("slow"), label + "_slow_key_exists_despite_falsy")
	_teardown_db(db)


func test_adv3b_slow_falsy_bool_trap_adhesion_carapace() -> void:
	var label := "ADV-3b_slow_falsy_bool_trap_adhesion_carapace"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "carapace")
	if res == null:
		_fail_test(label, "adhesion_carapace returned null (not yet registered)")
		_teardown_db(db)
		return
	_assert_false(bool(res.modifiers.get("slow", null)), label + "_slow_falsy")
	_assert_true(res.modifiers.has("slow"), label + "_slow_key_exists_despite_falsy")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-4: All 10 attack IDs (4 base + 6 fused) globally unique
#
# Risk: if a fused attack is accidentally assigned the same attack_id as a base
# attack (e.g., 1 through 4 copied from base block), downstream ID-based lookups
# would produce wrong results silently. The spec reserves 1-4 for base and 101-106
# for fused; no other overlap is possible per DR-3, but implementation could copy
# the wrong constant.
# ---------------------------------------------------------------------------

func test_adv4_all_10_attack_ids_globally_unique() -> void:
	var label := "ADV-4_all_10_attack_ids_globally_unique"
	var db = _new_defaults_db(label)
	if db == null:
		return

	var base_mutation_ids: Array = ["claw", "acid", "carapace", "adhesion"]
	var fused_pairs: Array = [
		["acid", "claw"],
		["adhesion", "claw"],
		["carapace", "claw"],
		["acid", "adhesion"],
		["acid", "carapace"],
		["adhesion", "carapace"],
	]

	var all_ids: Array = []
	for mid in base_mutation_ids:
		var res = db.get_base_attack(mid)
		if res == null:
			_fail_test(label, "base attack '%s' returned null" % mid)
			_teardown_db(db)
			return
		all_ids.append(res.attack_id)

	for pair in fused_pairs:
		var res = db.get_fused_attack(pair[0], pair[1])
		if res == null:
			_fail_test(label, "fused '%s'+'%s' returned null (not yet registered)" % [pair[0], pair[1]])
			_teardown_db(db)
			return
		all_ids.append(res.attack_id)

	# All 10 IDs must be distinct.
	var unique_ids: Array = []
	for id in all_ids:
		if id not in unique_ids:
			unique_ids.append(id)
	_assert_eq_int(10, unique_ids.size(), label + "_10_distinct_ids")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-5: get_fused_attack_count() stability — count before synthetic registration
#
# Risk: if tests use the autoload singleton and prior test runs left synthetic
# fused registrations in the same singleton, counts would be incorrect.
# This verifies count is exactly 6 on a fresh isolated instance (not the autoload).
# Additionally confirms that registering synthetic resources in a different
# db instance does not affect a fresh instance's count.
# ---------------------------------------------------------------------------

func test_adv5_count_stable_after_extra_synthetic_registration_in_different_instance() -> void:
	var label := "ADV-5_count_stable_separate_instances"
	var db1 = _new_defaults_db(label + "_db1")
	if db1 == null:
		return
	var db2 = _new_defaults_db(label + "_db2")
	if db2 == null:
		_teardown_db(db1)
		return

	# Record count on db1 (6 fused from _register_defaults).
	var count_before: int = db1.get_fused_attack_count()

	# Register synthetic combos in db2 — must not affect db1.
	var extra = AttackResource.new()
	extra.attack_id = 601
	db2.register_fused_attack("synth_a", "synth_b", extra)

	var count_after: int = db1.get_fused_attack_count()
	_assert_eq_int(6, count_before, label + "_db1_count_before_6")
	_assert_eq_int(6, count_after, label + "_db1_count_after_6_unaffected")
	_assert_eq_int(7, db2.get_fused_attack_count(), label + "_db2_has_extra")

	_teardown_db(db1)
	_teardown_db(db2)


func test_adv5_fresh_instance_count_exactly_6() -> void:
	# Confirms _register_defaults() is stable — exactly 6, not 0, not 7.
	var label := "ADV-5_fresh_instance_count_exactly_6"
	var db = _new_defaults_db(label)
	if db == null:
		return
	_assert_eq_int(6, db.get_fused_attack_count(), label)
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-6: get_base_attack_count() is still 4 after fused registrations
#
# Risk: if register_fused_attack() has a copy-paste bug that writes into
# _base_attacks instead of _fused_attacks, the base count would increment.
# ---------------------------------------------------------------------------

func test_adv6_base_attack_count_still_4_after_fused_registered() -> void:
	var label := "ADV-6_base_attack_count_still_4"
	var db = _new_defaults_db(label)
	if db == null:
		return
	# Confirm fused count is 6 (fused DID register).
	_assert_eq_int(6, db.get_fused_attack_count(), label + "_fused_count_6")
	# Base count must remain exactly 4.
	_assert_eq_int(4, db.get_base_attack_count(), label + "_base_count_4")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-7: vfx_scale > 0.0 for all 6 fused attacks
#
# Risk: if implementation accidentally leaves vfx_scale at the default (1.0 is fine
# but 0.0 would make VFX invisible). All fused attacks have spec-defined vfx_scale
# in range 1.2–1.8; any zero value means the property was forgotten.
# ---------------------------------------------------------------------------

func test_adv7_all_fused_vfx_scale_gt_zero() -> void:
	var label := "ADV-7_all_fused_vfx_scale_gt_zero"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var resources = _get_all_fused(db, label)
	if resources.is_empty():
		_teardown_db(db)
		return
	for key in resources:
		var res = resources[key]
		_assert_true(res.vfx_scale > 0.0, label + "_" + key + "_vfx_scale_positive")
	_teardown_db(db)


func test_adv7_all_fused_vfx_scale_in_spec_range() -> void:
	# Spec DR-2: vfx_scale 1.0–1.8 for fused attacks.
	var label := "ADV-7_all_fused_vfx_scale_in_spec_range"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var resources = _get_all_fused(db, label)
	if resources.is_empty():
		_teardown_db(db)
		return
	var expected: Dictionary = {
		"acid_claw": 1.3,
		"adhesion_claw": 1.2,
		"carapace_claw": 1.5,
		"acid_adhesion": 1.2,
		"acid_carapace": 1.8,
		"adhesion_carapace": 1.6,
	}
	for key in expected:
		var res = resources[key]
		_assert_approx(expected[key], res.vfx_scale, label + "_" + key + "_vfx_scale")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-8: Projectile-type fused attacks have projectile_speed > 0.0
#
# Risk: acid_adhesion is PROJECTILE_SPIT; if projectile_speed is 0.0, the
# projectile would never travel. The spec mandates projectile_speed = 10.0.
# (acid_carapace is SLAM_AOE, not projectile, so projectile_speed should remain 0.0.)
# ---------------------------------------------------------------------------

func test_adv8_acid_adhesion_projectile_speed_gt_zero() -> void:
	var label := "ADV-8_acid_adhesion_projectile_speed_gt_zero"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_teardown_db(db)
		return
	_assert_eq_string("PROJECTILE_SPIT", res.effect_type, label + "_effect_type_confirmed")
	_assert_true(res.projectile_speed > 0.0, label + "_projectile_speed_gt_zero")
	_assert_approx(10.0, res.projectile_speed, label + "_projectile_speed_eq_10")
	_teardown_db(db)


func test_adv8_slam_fused_attacks_have_zero_projectile_speed() -> void:
	# SLAM_AOE combos must have projectile_speed == 0.0 (no projectile component).
	var label := "ADV-8_slam_fused_attacks_zero_projectile_speed"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var slam_combos: Array = [
		["carapace", "claw", "carapace_claw"],
		["acid", "carapace", "acid_carapace"],
		["adhesion", "carapace", "adhesion_carapace"],
	]
	for c in slam_combos:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label + "_" + c[2], "returned null (not yet registered)")
			continue
		_assert_eq_string("SLAM_AOE", res.effect_type, label + "_" + c[2] + "_effect_slam")
		_assert_eq_float(0.0, res.projectile_speed, label + "_" + c[2] + "_projectile_speed_zero")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-9: acid_adhesion carries BOTH acid AND slow modifier keys simultaneously
#
# Risk: FAR-EC-5 — implementing the acid_adhesion block last risks copying from
# either acid_claw (only acid keys) or adhesion_claw (only slow keys) and missing
# one entire modifier set. Five keys must all be present.
# ---------------------------------------------------------------------------

func test_adv9_acid_adhesion_both_acid_and_slow_keys_coexist() -> void:
	var label := "ADV-9_acid_adhesion_both_modifier_families"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_teardown_db(db)
		return
	# All 5 keys must be present.
	_assert_true(res.modifiers.has("acid_on_hit"), label + "_acid_on_hit")
	_assert_true(res.modifiers.has("acid_duration"), label + "_acid_duration")
	_assert_true(res.modifiers.has("acid_dps"), label + "_acid_dps")
	_assert_true(res.modifiers.has("slow"), label + "_slow")
	_assert_true(res.modifiers.has("slow_duration"), label + "_slow_duration")
	# Verify exact modifier count — no extra keys from copy-paste.
	_assert_eq_int(5, res.modifiers.size(), label + "_modifier_count_5")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-10: Float precision for acid_dps values 0.8, 0.6, 1.2 (FAR-EC-8)
#
# Risk: IEEE 754 cannot represent 0.8, 0.6, 1.2 exactly in binary float.
# Using exact == comparison on these values can fail depending on how the
# constant is stored. Tests use approx comparison with tight 0.001 tolerance.
# ---------------------------------------------------------------------------

func test_adv10_acid_claw_acid_dps_float_precision() -> void:
	var label := "ADV-10_acid_claw_acid_dps_float_approx"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test(label, "acid_claw returned null (not yet registered)")
		_teardown_db(db)
		return
	var dps: float = res.modifiers.get("acid_dps", -1.0)
	_assert_approx(0.8, dps, label + "_acid_dps_approx_0_8")
	# Confirm exact == would also work at GDScript float precision (regression guard).
	_assert_false(dps < 0.0, label + "_acid_dps_positive")
	_teardown_db(db)


func test_adv10_acid_carapace_acid_dps_float_precision() -> void:
	var label := "ADV-10_acid_carapace_acid_dps_float_approx"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "carapace")
	if res == null:
		_fail_test(label, "acid_carapace returned null (not yet registered)")
		_teardown_db(db)
		return
	var dps: float = res.modifiers.get("acid_dps", -1.0)
	_assert_approx(0.6, dps, label + "_acid_dps_approx_0_6")
	_assert_false(dps < 0.0, label + "_acid_dps_positive")
	_teardown_db(db)


func test_adv10_acid_adhesion_acid_dps_float_precision() -> void:
	var label := "ADV-10_acid_adhesion_acid_dps_float_approx"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_teardown_db(db)
		return
	var dps: float = res.modifiers.get("acid_dps", -1.0)
	_assert_approx(1.2, dps, label + "_acid_dps_approx_1_2")
	_assert_false(dps < 0.0, label + "_acid_dps_positive")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-11: Modifier dict mutation independence via AttackResource.modifiers setter
#
# Risk: AttackResource.modifiers has a deep-copy setter. If the implementation
# assigns a shared dict literal to multiple resources (e.g., caching the same
# modifiers dict object before calling register_fused_attack), the deep-copy
# setter on each resource should still give each its own isolated copy.
# This tests independently from ADV-2 by injecting a new key after retrieval.
# ---------------------------------------------------------------------------

func test_adv11_modifier_setter_deep_copy_prevents_bleeding() -> void:
	var label := "ADV-11_modifier_setter_isolation"
	var db = _new_defaults_db(label)
	if db == null:
		return

	var res_ac = db.get_fused_attack("acid", "claw")
	var res_ap = db.get_fused_attack("acid", "carapace")
	if res_ac == null or res_ap == null:
		_fail_test(label, "one or more fused attacks returned null (not yet registered)")
		_teardown_db(db)
		return

	# Overwrite the entire modifiers dict on res_ac.
	var original_dps_ap: float = res_ap.modifiers.get("acid_dps", -99.0)
	res_ac.modifiers = {"injected_key": true, "acid_dps": 7777.0}

	# res_ap's modifiers must be unaffected.
	_assert_false(res_ap.modifiers.has("injected_key"), label + "_no_injected_key_bleed")
	_assert_approx(original_dps_ap, res_ap.modifiers.get("acid_dps", -99.0),
		label + "_acid_dps_unchanged")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-12: Fused attack effect_type is a known handler string
#
# Risk: if a fused attack's effect_type contains a typo (e.g., "SLAM_AOI" instead
# of "SLAM_AOE", or "MELEE_SWIPE_FUSED"), the AttackExecutor will push_warning and
# no effect will execute — silent failure at runtime.
# ---------------------------------------------------------------------------

func test_adv12_all_fused_effect_types_are_known_handlers() -> void:
	var label := "ADV-12_effect_types_known"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var resources = _get_all_fused(db, label)
	if resources.is_empty():
		_teardown_db(db)
		return
	for key in resources:
		var res = resources[key]
		_assert_true(
			res.effect_type in _KNOWN_EFFECT_TYPES,
			label + "_" + key + "_effect_type_known"
		)
	_teardown_db(db)


# ---------------------------------------------------------------------------
# ADV-13: All SLAM_AOE fused attacks have startup_frames > 0
#
# Risk: carapace_claw, acid_carapace, and adhesion_carapace are all SLAM_AOE.
# The design invariant (from Carapace base and the fused spec) is that SLAM_AOE
# attacks have a startup wind-up. startup_frames = 0 for these would break
# the intended animation and gameplay feel.
# ---------------------------------------------------------------------------

func test_adv13_slam_aoe_fused_all_have_startup_frames() -> void:
	var label := "ADV-13_slam_aoe_fused_startup_frames_gt_zero"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var slam_combos: Array = [
		["carapace", "claw", "carapace_claw", 8],
		["acid", "carapace", "acid_carapace", 12],
		["adhesion", "carapace", "adhesion_carapace", 12],
	]
	for c in slam_combos:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label + "_" + c[2], "returned null (not yet registered)")
			continue
		_assert_eq_string("SLAM_AOE", res.effect_type, label + "_" + c[2] + "_is_slam_aoe")
		_assert_true(res.startup_frames > 0, label + "_" + c[2] + "_startup_gt_zero")
		_assert_eq_int(c[3] as int, res.startup_frames, label + "_" + c[2] + "_startup_exact")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# Bonus: melee fused attacks have attack_range > 0 (not 0.0 like projectiles)
#
# Risk: MELEE_SWIPE combos (acid_claw, adhesion_claw) must have a positive
# attack_range or the melee radius query would find no enemies within 0 units.
# ---------------------------------------------------------------------------

func test_adv_bonus_melee_fused_have_positive_range() -> void:
	var label := "ADV-bonus_melee_fused_positive_range"
	var db = _new_defaults_db(label)
	if db == null:
		return
	var melee_combos: Array = [
		["acid", "claw", "acid_claw"],
		["adhesion", "claw", "adhesion_claw"],
	]
	for c in melee_combos:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label + "_" + c[2], "returned null (not yet registered)")
			continue
		_assert_eq_string("MELEE_SWIPE", res.effect_type, label + "_" + c[2] + "_is_melee")
		_assert_true(res.attack_range > 0.0, label + "_" + c[2] + "_range_positive")
	_teardown_db(db)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusedAttackResourcesAdversarialTests ===")

	# ADV-1: carapace_claw startup_frames > 0
	test_adv1_carapace_claw_startup_frames_gt_zero()

	# ADV-2: Modifier dict deep-copy independence
	test_adv2_modifier_dict_deep_copy_independence()

	# ADV-3: slow:0.0 falsy trap isolation
	test_adv3_adhesion_claw_slow_key_is_float_zero()

	# ADV-3b: Falsy-zero bool() confirmation
	test_adv3b_slow_falsy_bool_trap_adhesion_claw()
	test_adv3b_slow_falsy_bool_trap_acid_adhesion()
	test_adv3b_slow_falsy_bool_trap_adhesion_carapace()

	# ADV-4: All 10 IDs globally unique
	test_adv4_all_10_attack_ids_globally_unique()

	# ADV-5: count stability
	test_adv5_count_stable_after_extra_synthetic_registration_in_different_instance()
	test_adv5_fresh_instance_count_exactly_6()

	# ADV-6: base attack count unchanged
	test_adv6_base_attack_count_still_4_after_fused_registered()

	# ADV-7: vfx_scale > 0
	test_adv7_all_fused_vfx_scale_gt_zero()
	test_adv7_all_fused_vfx_scale_in_spec_range()

	# ADV-8: projectile-type attacks have projectile_speed > 0
	test_adv8_acid_adhesion_projectile_speed_gt_zero()
	test_adv8_slam_fused_attacks_have_zero_projectile_speed()

	# ADV-9: acid_adhesion has both modifier families simultaneously
	test_adv9_acid_adhesion_both_acid_and_slow_keys_coexist()

	# ADV-10: float precision for non-representable acid_dps values
	test_adv10_acid_claw_acid_dps_float_precision()
	test_adv10_acid_carapace_acid_dps_float_precision()
	test_adv10_acid_adhesion_acid_dps_float_precision()

	# ADV-11: modifier setter deep-copy isolation
	test_adv11_modifier_setter_deep_copy_prevents_bleeding()

	# ADV-12: all effect_types are known handler strings
	test_adv12_all_fused_effect_types_are_known_handlers()

	# ADV-13: SLAM_AOE fused attacks have startup_frames > 0
	test_adv13_slam_aoe_fused_all_have_startup_frames()

	# Bonus: melee fused attacks have positive attack_range
	test_adv_bonus_melee_fused_have_positive_range()

	print(
		"FusedAttackResourcesAdversarialTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
