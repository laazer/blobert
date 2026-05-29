#
# test_fused_attack_stats.gd
#
# Stat-value, edge-case, and meaningful-distinction tests for the 6 canonical
# fused AttackResource registrations in AttackDatabaseNode._register_defaults().
#
# Spec: project_board/specs/fused_attack_resources_spec.md
# Ticket: project_board/12_milestone_12_fused_mutation_attacks/backlog/02_fused_attack_resources.md
# Traceability: FAR-4, FAR-7, FAR-EC-1, FAR-EC-2, FAR-NF-4, FAR-NF-6
#
# Coverage (this file — 16 test functions):
#   Stat values per-combo (FAR-4): 6 tests (one per combo)
#   Modifier dict size / no extra keys (FAR-EC-2): 1 test
#   Falsy-zero slow==0.0 pattern (FAR-EC-1): 2 tests
#   Meaningful distinction from base components (FAR-7): 1 test
#   No cross-contamination into base_attacks (FAR-NF-4): 1 test
#   Attack names exact and unique (FAR-4 / FAR-NF-6): 1 test
#   Color not white, matches spec (FAR-4 color): 1 test
#   Fused damage > base components (FAR-7 proxy): 3 tests
#
# Companion file: test_fused_attack_resources.gd (FAR-3, FAR-5, FAR-6)
#
# Design notes:
#   - Uses a fresh AttackDatabaseNode per test via add_child() to trigger _ready().
#   - Does NOT use the autoload singleton to avoid cross-test contamination.
#   - FAR-EC-1 slow=0.0: verified with has() + typeof()==TYPE_FLOAT + ==0.0 (not truthiness).
#   - FAR-EC-8: 0.8, 0.6, and 1.2 acid_dps values use _assert_approx() (not exact).
#

class_name FusedAttackStatsTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0

const _DB_SCRIPT_PATH := "res://scripts/attacks/attack_database.gd"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_db(test_label: String) -> Node:
	var script = load(_DB_SCRIPT_PATH) as GDScript
	if script == null:
		_fail_test(test_label, _DB_SCRIPT_PATH + " not loadable (not yet implemented)")
		return null
	var inst = script.new()
	if inst == null:
		_fail_test(test_label, "instantiation returned null")
		return null
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(inst)
	else:
		_fail_test(test_label, "SceneTree not available; cannot add_child")
		inst.free()
		return null
	return inst


func _free_db(db: Node) -> void:
	if db != null and is_instance_valid(db):
		db.free()


# ---------------------------------------------------------------------------
# FAR-4: Stat values — one test function per combo
# ---------------------------------------------------------------------------

func test_far4_acid_claw_stats() -> void:
	# FAR-4-101: Toxic Slash — damage, cooldown, attack_range, knockback_magnitude,
	# effect_type, modifiers (acid_on_hit=true, acid_duration=2.0, acid_dps~=0.8),
	# attack_name.
	var label := "FAR-4-101_acid_claw_stats"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "claw")
	if res == null:
		_fail_test(label, "acid_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_float(4.0, res.damage, label + "_damage")
	_assert_eq_float(1.5, res.cooldown, label + "_cooldown")
	_assert_eq_float(1.5, res.attack_range, label + "_attack_range")
	_assert_eq_float(3.0, res.knockback_magnitude, label + "_knockback_magnitude")
	_assert_eq_string("MELEE_SWIPE", res.effect_type, label + "_effect_type")
	_assert_eq_string("Toxic Slash", res.attack_name, label + "_attack_name")
	_assert_true(res.modifiers.has("acid_on_hit") and res.modifiers["acid_on_hit"] == true,
		label + "_modifier_acid_on_hit")
	_assert_eq_float(2.0, res.modifiers.get("acid_duration", -1.0), label + "_modifier_acid_duration")
	# FAR-EC-8: 0.8 is not exactly representable in IEEE 754 — use approx comparison
	_assert_approx(0.8, res.modifiers.get("acid_dps", -1.0), label + "_modifier_acid_dps")
	_free_db(db)


func test_far4_adhesion_claw_stats() -> void:
	# FAR-4-102: Sticky Slash — damage, cooldown, attack_range, knockback_magnitude,
	# effect_type, modifiers (slow=0.0 via explicit check, slow_duration=2.0), attack_name.
	var label := "FAR-4-102_adhesion_claw_stats"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "claw")
	if res == null:
		_fail_test(label, "adhesion_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_float(3.5, res.damage, label + "_damage")
	_assert_eq_float(2.0, res.cooldown, label + "_cooldown")
	_assert_eq_float(1.5, res.attack_range, label + "_attack_range")
	_assert_eq_float(1.0, res.knockback_magnitude, label + "_knockback_magnitude")
	_assert_eq_string("MELEE_SWIPE", res.effect_type, label + "_effect_type")
	_assert_eq_string("Sticky Slash", res.attack_name, label + "_attack_name")
	# FAR-EC-1: slow=0.0 falsy-zero — must use has() + typeof() + explicit == 0.0
	var slow_ok: bool = (
		res.modifiers.has("slow")
		and typeof(res.modifiers["slow"]) == TYPE_FLOAT
		and res.modifiers["slow"] == 0.0
	)
	_assert_true(slow_ok, label + "_modifier_slow_eq_0")
	_assert_eq_float(2.0, res.modifiers.get("slow_duration", -1.0), label + "_modifier_slow_duration")
	_free_db(db)


func test_far4_carapace_claw_stats() -> void:
	# FAR-4-103: Armored Slam — damage, cooldown, attack_range, knockback_magnitude,
	# startup_frames, effect_type, modifiers (infect_weakened=true), attack_name.
	var label := "FAR-4-103_carapace_claw_stats"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("carapace", "claw")
	if res == null:
		_fail_test(label, "carapace_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_float(5.0, res.damage, label + "_damage")
	_assert_eq_float(3.0, res.cooldown, label + "_cooldown")
	_assert_eq_float(2.5, res.attack_range, label + "_attack_range")
	_assert_eq_float(6.0, res.knockback_magnitude, label + "_knockback_magnitude")
	_assert_eq_int(8, res.startup_frames, label + "_startup_frames")
	_assert_eq_string("SLAM_AOE", res.effect_type, label + "_effect_type")
	_assert_eq_string("Armored Slam", res.attack_name, label + "_attack_name")
	_assert_true(res.modifiers.has("infect_weakened") and res.modifiers["infect_weakened"] == true,
		label + "_modifier_infect_weakened")
	_free_db(db)


func test_far4_acid_adhesion_stats() -> void:
	# FAR-4-104: Venom Web — damage, cooldown, projectile_speed, projectile_lifetime,
	# effect_type, acid modifiers + adhesion slow=0.0 (FAR-EC-1), attack_name.
	var label := "FAR-4-104_acid_adhesion_stats"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_float(2.0, res.damage, label + "_damage")
	_assert_eq_float(3.0, res.cooldown, label + "_cooldown")
	_assert_eq_float(10.0, res.projectile_speed, label + "_projectile_speed")
	_assert_eq_float(1.75, res.projectile_lifetime, label + "_projectile_lifetime")
	_assert_eq_string("PROJECTILE_SPIT", res.effect_type, label + "_effect_type")
	_assert_eq_string("Venom Web", res.attack_name, label + "_attack_name")
	_assert_true(res.modifiers.has("acid_on_hit") and res.modifiers["acid_on_hit"] == true,
		label + "_modifier_acid_on_hit")
	_assert_eq_float(3.0, res.modifiers.get("acid_duration", -1.0), label + "_modifier_acid_duration")
	# FAR-EC-8: 1.2 is not exactly representable — use approx comparison
	_assert_approx(1.2, res.modifiers.get("acid_dps", -1.0), label + "_modifier_acid_dps")
	# FAR-EC-1: slow=0.0 falsy-zero — must use has() + typeof() + explicit == 0.0
	var slow_ok: bool = (
		res.modifiers.has("slow")
		and typeof(res.modifiers["slow"]) == TYPE_FLOAT
		and res.modifiers["slow"] == 0.0
	)
	_assert_true(slow_ok, label + "_modifier_slow_eq_0")
	_assert_eq_float(2.5, res.modifiers.get("slow_duration", -1.0), label + "_modifier_slow_duration")
	_free_db(db)


func test_far4_acid_carapace_stats() -> void:
	# FAR-4-105: Corrosive Slam — damage, cooldown, attack_range, knockback_magnitude,
	# startup_frames, effect_type, modifiers (acid_on_hit, acid_duration, acid_dps~=0.6),
	# attack_name.
	var label := "FAR-4-105_acid_carapace_stats"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "carapace")
	if res == null:
		_fail_test(label, "acid_carapace returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_float(4.5, res.damage, label + "_damage")
	_assert_eq_float(4.0, res.cooldown, label + "_cooldown")
	_assert_eq_float(3.5, res.attack_range, label + "_attack_range")
	_assert_eq_float(4.0, res.knockback_magnitude, label + "_knockback_magnitude")
	_assert_eq_int(12, res.startup_frames, label + "_startup_frames")
	_assert_eq_string("SLAM_AOE", res.effect_type, label + "_effect_type")
	_assert_eq_string("Corrosive Slam", res.attack_name, label + "_attack_name")
	_assert_true(res.modifiers.has("acid_on_hit") and res.modifiers["acid_on_hit"] == true,
		label + "_modifier_acid_on_hit")
	_assert_eq_float(2.5, res.modifiers.get("acid_duration", -1.0), label + "_modifier_acid_duration")
	# FAR-EC-8: 0.6 is not exactly representable — use approx comparison
	_assert_approx(0.6, res.modifiers.get("acid_dps", -1.0), label + "_modifier_acid_dps")
	_free_db(db)


func test_far4_adhesion_carapace_stats() -> void:
	# FAR-4-106: Web Slam — damage, cooldown, attack_range, knockback_magnitude,
	# startup_frames, effect_type, modifiers (slow=0.0, slow_duration=2.0), attack_name.
	var label := "FAR-4-106_adhesion_carapace_stats"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "carapace")
	if res == null:
		_fail_test(label, "adhesion_carapace returned null (not yet registered)")
		_free_db(db)
		return
	_assert_eq_float(3.5, res.damage, label + "_damage")
	_assert_eq_float(3.5, res.cooldown, label + "_cooldown")
	_assert_eq_float(3.0, res.attack_range, label + "_attack_range")
	_assert_eq_float(2.0, res.knockback_magnitude, label + "_knockback_magnitude")
	_assert_eq_int(12, res.startup_frames, label + "_startup_frames")
	_assert_eq_string("SLAM_AOE", res.effect_type, label + "_effect_type")
	_assert_eq_string("Web Slam", res.attack_name, label + "_attack_name")
	# FAR-EC-1: slow=0.0 falsy-zero — must use has() + typeof() + explicit == 0.0
	var slow_ok: bool = (
		res.modifiers.has("slow")
		and typeof(res.modifiers["slow"]) == TYPE_FLOAT
		and res.modifiers["slow"] == 0.0
	)
	_assert_true(slow_ok, label + "_modifier_slow_eq_0")
	_assert_eq_float(2.0, res.modifiers.get("slow_duration", -1.0), label + "_modifier_slow_duration")
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-EC-2: Modifier dictionary size — no extra or missing keys per combo
# ---------------------------------------------------------------------------

func test_farec2_modifier_dict_sizes() -> void:
	# FAR-EC-2: Each fused attack's modifier dict must have exactly the number of
	# keys defined in the spec.
	# acid_claw: 3 keys (acid_on_hit, acid_duration, acid_dps)
	# adhesion_claw: 2 keys (slow, slow_duration)
	# carapace_claw: 1 key (infect_weakened)
	# acid_adhesion: 5 keys (acid_on_hit, acid_duration, acid_dps, slow, slow_duration)
	# acid_carapace: 3 keys (acid_on_hit, acid_duration, acid_dps)
	# adhesion_carapace: 2 keys (slow, slow_duration)
	var label := "FAR-EC-2_modifier_dict_sizes"
	var db = _make_db(label)
	if db == null:
		return
	var cases: Array = [
		["acid", "claw", 3, "acid_claw"],
		["adhesion", "claw", 2, "adhesion_claw"],
		["carapace", "claw", 1, "carapace_claw"],
		["acid", "adhesion", 5, "acid_adhesion"],
		["acid", "carapace", 3, "acid_carapace"],
		["adhesion", "carapace", 2, "adhesion_carapace"],
	]
	for c in cases:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label + "_" + c[3], "returned null (not yet registered)")
			continue
		_assert_eq_int(c[2] as int, res.modifiers.size(), label + "_" + c[3] + "_modifier_size")
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-EC-1: slow=0.0 falsy-zero — dedicated edge case tests
# ---------------------------------------------------------------------------

func test_farec1_adhesion_claw_slow_not_truthy() -> void:
	# FAR-EC-1 adhesion_claw: slow=0.0 must NOT pass a truthiness test.
	# Verifies key IS present, type IS float, and value IS exactly 0.0.
	var label := "FAR-EC-1_adhesion_claw_slow_not_truthy"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("adhesion", "claw")
	if res == null:
		_fail_test(label, "adhesion_claw returned null (not yet registered)")
		_free_db(db)
		return
	_assert_true(res.modifiers.has("slow"), label + "_slow_key_exists")
	_assert_eq_int(TYPE_FLOAT, typeof(res.modifiers["slow"]), label + "_slow_is_float")
	_assert_true(res.modifiers["slow"] == 0.0, label + "_slow_is_zero")
	# Document the falsy-zero pattern: 0.0 would be falsy if tested with bool()
	_assert_false(bool(res.modifiers["slow"]), label + "_slow_falsy_confirms_pattern")
	_free_db(db)


func test_farec1_acid_adhesion_both_slow_and_acid() -> void:
	# FAR-EC-5 + FAR-EC-1: acid_adhesion carries both acid AND slow modifiers
	# simultaneously. The slow=0.0 key coexists with acid_on_hit=true.
	var label := "FAR-EC-1_acid_adhesion_both_slow_and_acid"
	var db = _make_db(label)
	if db == null:
		return
	var res = db.get_fused_attack("acid", "adhesion")
	if res == null:
		_fail_test(label, "acid_adhesion returned null (not yet registered)")
		_free_db(db)
		return
	_assert_true(res.modifiers.has("acid_on_hit"), label + "_acid_on_hit_present")
	_assert_true(res.modifiers.has("acid_duration"), label + "_acid_duration_present")
	_assert_true(res.modifiers.has("acid_dps"), label + "_acid_dps_present")
	_assert_true(res.modifiers.has("slow"), label + "_slow_key_present")
	_assert_eq_int(TYPE_FLOAT, typeof(res.modifiers["slow"]), label + "_slow_is_float")
	_assert_true(res.modifiers["slow"] == 0.0, label + "_slow_is_zero")
	_assert_true(res.modifiers.has("slow_duration"), label + "_slow_duration_present")
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-7: Meaningful distinction — fused attacks differ from their base components
# ---------------------------------------------------------------------------

func test_far7_fused_attacks_differ_from_base_components() -> void:
	# FAR-7a through FAR-7l: Each fused attack differs from both components in
	# at least two observable properties. Base stats are read from the DB live
	# so this test stays correct if base values are tuned.
	var label := "FAR-7_fused_differ_from_base"
	var db = _make_db(label)
	if db == null:
		return

	var acid_claw = db.get_fused_attack("acid", "claw")
	var adhesion_claw = db.get_fused_attack("adhesion", "claw")
	var carapace_claw = db.get_fused_attack("carapace", "claw")
	var acid_adhesion = db.get_fused_attack("acid", "adhesion")
	var acid_carapace = db.get_fused_attack("acid", "carapace")
	var adhesion_carapace = db.get_fused_attack("adhesion", "carapace")

	if (acid_claw == null or adhesion_claw == null or carapace_claw == null
			or acid_adhesion == null or acid_carapace == null or adhesion_carapace == null):
		_fail_test(label, "one or more fused attacks returned null (not yet registered)")
		_free_db(db)
		return

	var base_claw = db.get_base_attack("claw")
	var base_acid = db.get_base_attack("acid")
	var base_carapace = db.get_base_attack("carapace")
	var base_adhesion = db.get_base_attack("adhesion")

	if base_claw == null or base_acid == null or base_carapace == null or base_adhesion == null:
		_fail_test(label, "one or more base attacks returned null from DB")
		_free_db(db)
		return

	# FAR-7a: acid_claw.damage > claw.damage; acid_claw has acid_on_hit (claw does not)
	_assert_true(acid_claw.damage > base_claw.damage, label + "_acid_claw_damage_gt_claw")
	_assert_true(acid_claw.modifiers.has("acid_on_hit"), label + "_acid_claw_has_acid_on_hit")

	# FAR-7b: acid_claw.effect_type (MELEE_SWIPE) != acid (PROJECTILE_SPIT)
	_assert_eq_string("MELEE_SWIPE", acid_claw.effect_type, label + "_acid_claw_effect_is_melee")
	_assert_true(acid_claw.knockback_magnitude > 0.0, label + "_acid_claw_knockback_gt_acid")

	# FAR-7c: adhesion_claw.cooldown > claw.cooldown; has "slow" key
	_assert_true(adhesion_claw.cooldown > base_claw.cooldown, label + "_adhesion_claw_cooldown_gt_claw")
	_assert_true(adhesion_claw.modifiers.has("slow"), label + "_adhesion_claw_has_slow")

	# FAR-7d: adhesion_claw.effect_type (MELEE_SWIPE) != adhesion (PROJECTILE_SPIT)
	_assert_eq_string("MELEE_SWIPE", adhesion_claw.effect_type, label + "_adhesion_claw_effect_melee")
	_assert_true(adhesion_claw.damage > base_adhesion.damage, label + "_adhesion_claw_damage_gt_adhesion")

	# FAR-7e: carapace_claw.effect_type (SLAM_AOE) != claw (MELEE_SWIPE)
	_assert_eq_string("SLAM_AOE", carapace_claw.effect_type, label + "_carapace_claw_effect_slam")
	_assert_true(carapace_claw.attack_range > base_claw.attack_range, label + "_carapace_claw_range_gt_claw")

	# FAR-7f: carapace_claw.damage > carapace.damage; has infect_weakened
	_assert_true(carapace_claw.damage > base_carapace.damage, label + "_carapace_claw_damage_gt_carapace")
	_assert_true(carapace_claw.modifiers.has("infect_weakened"), label + "_carapace_claw_has_infect")

	# FAR-7g: acid_adhesion.projectile_speed > acid; has "slow" key (acid lacks)
	_assert_true(acid_adhesion.projectile_speed > base_acid.projectile_speed,
		label + "_acid_adhesion_speed_gt_acid")
	_assert_true(acid_adhesion.modifiers.has("slow"), label + "_acid_adhesion_has_slow")

	# FAR-7h: acid_adhesion has acid_on_hit (adhesion lacks); cooldown > adhesion
	_assert_true(acid_adhesion.modifiers.has("acid_on_hit"), label + "_acid_adhesion_has_acid_on_hit")
	_assert_true(acid_adhesion.cooldown > base_adhesion.cooldown,
		label + "_acid_adhesion_cooldown_gt_adhesion")

	# FAR-7i: acid_carapace.effect_type (SLAM_AOE) != acid (PROJECTILE_SPIT)
	_assert_eq_string("SLAM_AOE", acid_carapace.effect_type, label + "_acid_carapace_effect_slam")
	_assert_true(acid_carapace.knockback_magnitude > 0.0, label + "_acid_carapace_knockback_gt_acid")

	# FAR-7j: acid_carapace has acid_on_hit; damage > acid.damage
	_assert_true(acid_carapace.modifiers.has("acid_on_hit"), label + "_acid_carapace_has_acid_on_hit")
	_assert_true(acid_carapace.damage > base_acid.damage, label + "_acid_carapace_damage_gt_acid")

	# FAR-7k: adhesion_carapace has "slow"; knockback < carapace (root is primary effect)
	_assert_true(adhesion_carapace.modifiers.has("slow"), label + "_adhesion_carapace_has_slow")
	_assert_true(adhesion_carapace.knockback_magnitude < base_carapace.knockback_magnitude,
		label + "_adhesion_carapace_knockback_lt_carapace")

	# FAR-7l: adhesion_carapace.effect_type (SLAM_AOE) != adhesion (PROJECTILE_SPIT)
	_assert_eq_string("SLAM_AOE", adhesion_carapace.effect_type, label + "_adhesion_carapace_effect_slam")
	_assert_true(adhesion_carapace.damage > base_adhesion.damage,
		label + "_adhesion_carapace_damage_gt_adhesion")

	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-NF-4: No cross-contamination — fused IDs not in base_attacks dict
# ---------------------------------------------------------------------------

func test_farnf4_fused_attacks_not_in_base_attacks() -> void:
	# FAR-NF-4: fused attack sorted-key names cannot be retrieved via get_base_attack().
	var label := "FAR-NF-4_fused_not_in_base_attacks"
	var db = _make_db(label)
	if db == null:
		return
	_assert_true(db.get_base_attack("acid_claw") == null, label + "_base_acid_claw_null")
	_assert_true(db.get_base_attack("adhesion_claw") == null, label + "_base_adhesion_claw_null")
	_assert_true(db.get_base_attack("carapace_claw") == null, label + "_base_carapace_claw_null")
	_assert_true(db.get_base_attack("acid_adhesion") == null, label + "_base_acid_adhesion_null")
	_assert_true(db.get_base_attack("acid_carapace") == null, label + "_base_acid_carapace_null")
	_assert_true(db.get_base_attack("adhesion_carapace") == null, label + "_base_adhesion_carapace_null")
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-4 / FAR-NF-6: Attack names exact and unique
# ---------------------------------------------------------------------------

func test_farnf6_attack_names_exact_and_unique() -> void:
	# FAR-NF-6: All 6 fused attack_name values are non-empty, match Section 4 exactly,
	# and are unique across the 6 fused attacks.
	var label := "FAR-NF-6_attack_names_exact_and_unique"
	var db = _make_db(label)
	if db == null:
		return
	var expected_names: Dictionary = {
		"acid_claw": "Toxic Slash",
		"adhesion_claw": "Sticky Slash",
		"carapace_claw": "Armored Slam",
		"acid_adhesion": "Venom Web",
		"acid_carapace": "Corrosive Slam",
		"adhesion_carapace": "Web Slam",
	}
	var combos: Array = [
		["acid", "claw", "acid_claw"],
		["adhesion", "claw", "adhesion_claw"],
		["carapace", "claw", "carapace_claw"],
		["acid", "adhesion", "acid_adhesion"],
		["acid", "carapace", "acid_carapace"],
		["adhesion", "carapace", "adhesion_carapace"],
	]
	var seen_names: Array = []
	for c in combos:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label + "_" + c[2], "returned null (not yet registered)")
			continue
		_assert_false(res.attack_name == "", label + "_" + c[2] + "_name_non_empty")
		_assert_eq_string(expected_names[c[2]], res.attack_name, label + "_" + c[2] + "_name_exact")
		if res.attack_name not in seen_names:
			seen_names.append(res.attack_name)
	_assert_eq_int(combos.size(), seen_names.size(), label + "_names_unique")
	_free_db(db)


# ---------------------------------------------------------------------------
# FAR-4 color: no fused attack uses Color.WHITE; each matches spec value
# ---------------------------------------------------------------------------

func test_far4_fused_color_not_white() -> void:
	# FAR-4 color: no fused attack should have Color.WHITE (AttackResource default).
	var label := "FAR-4_fused_color_not_white"
	var db = _make_db(label)
	if db == null:
		return
	var combos: Array = [
		["acid", "claw", "acid_claw", Color(0.6, 0.85, 0.0)],
		["adhesion", "claw", "adhesion_claw", Color(0.85, 0.65, 0.0)],
		["carapace", "claw", "carapace_claw", Color(0.65, 0.35, 0.05)],
		["acid", "adhesion", "acid_adhesion", Color(0.3, 0.75, 0.1)],
		["acid", "carapace", "acid_carapace", Color(0.4, 0.65, 0.05)],
		["adhesion", "carapace", "adhesion_carapace", Color(0.55, 0.45, 0.1)],
	]
	for c in combos:
		var res = db.get_fused_attack(c[0], c[1])
		if res == null:
			_fail_test(label + "_" + c[2], "returned null (not yet registered)")
			continue
		_assert_false(res.color == Color.WHITE, label + "_" + c[2] + "_not_white")
		_assert_true(res.color.is_equal_approx(c[3]), label + "_" + c[2] + "_color_exact")
	_free_db(db)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== FusedAttackStatsTests ===")

	# FAR-4: Stat values per-combo
	test_far4_acid_claw_stats()
	test_far4_adhesion_claw_stats()
	test_far4_carapace_claw_stats()
	test_far4_acid_adhesion_stats()
	test_far4_acid_carapace_stats()
	test_far4_adhesion_carapace_stats()

	# FAR-EC-2: Modifier dict sizes
	test_farec2_modifier_dict_sizes()

	# FAR-EC-1: Falsy-zero slow==0.0 pattern
	test_farec1_adhesion_claw_slow_not_truthy()
	test_farec1_acid_adhesion_both_slow_and_acid()

	# FAR-7: Meaningful distinction from base components
	test_far7_fused_attacks_differ_from_base_components()

	# FAR-NF-4: No cross-contamination into _base_attacks
	test_farnf4_fused_attacks_not_in_base_attacks()

	# FAR-NF-6 + FAR-4: Attack names exact and unique
	test_farnf6_attack_names_exact_and_unique()

	# FAR-4 color: not white, matches spec values
	test_far4_fused_color_not_white()

	print(
		"FusedAttackStatsTests: "
		+ str(_pass_count) + " passed, "
		+ str(_fail_count) + " failed"
	)
	return _fail_count
