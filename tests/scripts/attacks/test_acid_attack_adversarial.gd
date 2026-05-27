#
# test_acid_attack_adversarial.gd
#
# Adversarial edge-case, boundary, mutation, and stress tests for the acid
# mutation attack. Extends test_acid_attack.gd with weaknesses, blind spots,
# and gaps the primary coverage misses.
#
# Spec: project_board/specs/acid_player_attack_spec.md (APA-1..APA-7, EC-1..EC-18)
# Ticket: M11-09
#
# Tests marked EXPECTED FAIL will fail until acid implementation is complete.
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Mock inner classes
# ---------------------------------------------------------------------------

class MockEnemy extends Node3D:
	var damage_taken: Array = []
	var acid_calls: Array = []
	var poison_calls: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})

	func apply_acid(duration: float, dps: float) -> void:
		acid_calls.append({"duration": duration, "dps": dps})

	func apply_poison(duration: float, dps: float) -> void:
		poison_calls.append({"duration": duration, "dps": dps})

	func get_base_state() -> int:
		return current_state

	func set_base_state(state: int) -> void:
		current_state = state

	func is_dead() -> bool:
		return is_dead_flag


class DyingEnemy extends Node3D:
	## Enemy killed by projectile damage — exposes gap where _apply_modifiers
	## may still fire apply_acid on a just-killed enemy.
	var damage_taken: Array = []
	var acid_calls: Array = []
	var current_state: int = 0
	var is_dead_flag: bool = false
	var current_hp: float = 0.5

	func take_damage(damage: float, knockback: Vector3) -> void:
		if is_dead_flag:
			return
		damage_taken.append({"damage": damage, "knockback": knockback})
		current_hp = maxf(0.0, current_hp - damage)
		if current_hp <= 0.0:
			is_dead_flag = true

	func apply_acid(duration: float, dps: float) -> void:
		if is_dead_flag:
			return
		acid_calls.append({"duration": duration, "dps": dps})

	func get_base_state() -> int:
		return current_state

	func is_dead() -> bool:
		return is_dead_flag


class NoMethodTarget extends Node3D:
	## Bare target with take_damage but no apply_acid, no get_base_state.
	var damage_taken: Array = []

	func take_damage(damage: float, knockback: Vector3) -> void:
		damage_taken.append({"damage": damage, "knockback": knockback})


class MockParent extends Node3D:
	var _facing: float = 1.0
	func get_facing_sign() -> float:
		return _facing


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_acid_resource() -> AttackResource:
	var r = AttackResource.new()
	r.attack_id = 2
	r.attack_name = "Acid Spit"
	r.description = "Ranged acid projectile."
	r.effect_type = "PROJECTILE_SPIT"
	r.damage = 1.0
	r.cooldown = 2.0
	r.attack_range = 0.0
	r.startup_frames = 0
	r.knockback_magnitude = 0.0
	r.knockback_direction = "none"
	r.projectile_speed = 8.0
	r.projectile_lifetime = 2.0
	r.color = Color.CHARTREUSE
	r.vfx_scale = 1.0
	r.modifiers = {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	return r


func _make_resource(overrides: Dictionary = {}) -> AttackResource:
	var r = AttackResource.new()
	r.startup_frames = 0
	for key in overrides:
		r.set(key, overrides[key])
	return r


func _build_scene(label: String, enemies: Array = [], pos: Vector3 = Vector3.ZERO, facing: float = 1.0) -> Dictionary:
	var parent = MockParent.new()
	parent._facing = facing
	var result = AttackExecutorHarness.build_scene(parent, enemies, pos)
	if result.is_empty():
		_fail_test(label, "executor not loadable")
	return result


func _teardown(scene: Dictionary) -> void:
	AttackExecutorHarness.teardown_scene(scene)


var _projectile_log: Array = []

func _reset_projectile_log() -> void:
	_projectile_log = []

func _connect_projectile_signal(executor: Node) -> void:
	_reset_projectile_log()
	executor.connect("projectile_fired", func(p, r): _projectile_log.append({"projectile": p, "resource": r}))


func _make_projectile_in_tree(mods: Dictionary = {}, dmg: float = 1.0) -> Dictionary:
	var root = Node3D.new()
	var proj = PlayerProjectile3D.new()
	proj.damage = dmg
	proj.speed = 8.0
	proj.knockback_magnitude = 0.0
	proj.knockback_direction = "none"
	proj.modifiers = mods
	proj.direction_x = 1.0
	root.add_child(proj)
	var tree = Engine.get_main_loop() as SceneTree
	if tree:
		tree.root.add_child(root)
	return {"root": root, "projectile": proj}


# ---------------------------------------------------------------------------
# Null & Empty: Degenerate modifier dictionaries
# ---------------------------------------------------------------------------

func test_adv_acid_on_hit_false_explicit() -> void:
	## Explicit false must NOT trigger acid, even though the key exists.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_false_key", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": false, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV_acid_false_no_apply")
	enemy.free()
	executor.free()


func test_adv_empty_modifiers_no_acid() -> void:
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_empty_mods", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	executor._apply_modifiers(enemy, {})
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV_empty_mods_no_acid")
	enemy.free()
	executor.free()


func test_adv_missing_acid_duration_uses_fallback() -> void:
	## acid_on_hit: true but no acid_duration → fallback to 2.0
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_no_dur", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": true}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_no_dur_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(2.0, enemy.acid_calls[0]["duration"], "ADV_no_dur_fallback_2")
	enemy.free()
	executor.free()


func test_adv_missing_acid_dps_uses_fallback() -> void:
	## acid_on_hit: true but no acid_dps → fallback to DEFAULT_ACID_DPS (0.2)
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_no_dps", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": true, "acid_duration": 3.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_no_dps_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(0.2, enemy.acid_calls[0]["dps"], "ADV_no_dps_fallback_0_2")
	enemy.free()
	executor.free()


func test_adv_projectile_empty_modifiers_no_acid() -> void:
	## Projectile with empty modifiers must not apply acid.
	var ps = _make_projectile_in_tree({})
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV_proj_empty_mods")
	enemy.free()
	(ps["root"] as Node).free()


func test_adv_projectile_acid_on_hit_false() -> void:
	## Projectile with acid_on_hit: false must not apply acid.
	var mods := {"acid_on_hit": false, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(mods)
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV_proj_false_no_acid")
	enemy.free()
	(ps["root"] as Node).free()


# ---------------------------------------------------------------------------
# Boundary: Zero/negative damage, extreme values
# ---------------------------------------------------------------------------

func test_adv_zero_damage_acid_still_applies() -> void:
	## damage=0 on the resource; acid modifier is independent of direct damage.
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods, 0.0)
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(1, enemy.damage_taken.size(), "ADV_zero_dmg_hit")
	if enemy.damage_taken.size() > 0:
		_assert_eq_float(0.0, enemy.damage_taken[0]["damage"], "ADV_zero_dmg_val")
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_zero_dmg_acid_applied")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


func test_adv_huge_duration_accepted() -> void:
	## Stress: very large duration must be accepted by EnemyEffectTracker.
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 999.0, 1.0)
	_assert_true(tracker.has_active_dot("acid"), "ADV_huge_dur_accepted")
	_assert_eq_float(999.0, tracker._active_dots["acid"]["remaining_duration"], "ADV_huge_dur_val")
	tracker.free()


func test_adv_huge_dps_accepted() -> void:
	## Stress: very large DPS must be accepted.
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 9999.0)
	_assert_eq_float(9999.0, tracker._active_dots["acid"]["dps"], "ADV_huge_dps_val")
	tracker.free()


func test_adv_near_zero_duration_accepted() -> void:
	## Just above zero (0.001s) should be accepted.
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 0.001, 1.0)
	_assert_true(tracker.has_active_dot("acid"), "ADV_tiny_dur_accepted")
	tracker.free()


func test_adv_cooldown_exactly_2s() -> void:
	var acid = _make_acid_resource()
	_assert_eq_float(2.0, acid.cooldown, "ADV_cd_exact_2")
	_assert_true(acid.cooldown > 0.0, "ADV_cd_positive")


# ---------------------------------------------------------------------------
# State machine edge cases
# ---------------------------------------------------------------------------

func test_adv_acid_state_99_base_duration() -> void:
	## Enemy with bogus state value (99) should NOT trigger WEAKENED doubling.
	## EXPECTED FAIL until WEAKENED doubling is implemented.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_state_99", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 99
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_state_99_applied")
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "ADV_state_99_base_dur")
	enemy.free()
	executor.free()


func test_adv_acid_state_negative_base_duration() -> void:
	## Enemy with negative state (-1) should get base duration.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_state_neg", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = -1
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "ADV_state_neg_base_dur")
	else:
		_fail_test("ADV_state_neg", "acid not applied")
	enemy.free()
	executor.free()


func test_adv_dead_enemy_projectile_killed_by_hit() -> void:
	## Projectile damage kills enemy (hp=0.5, damage=1.0). Then _apply_modifiers
	## still runs. DyingEnemy.apply_acid guards on is_dead_flag → no acid.
	## This verifies the real-world gap: is _apply_modifiers guarded against dead?
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var enemy = DyingEnemy.new()
	enemy.current_hp = 0.5
	ps["projectile"]._on_body_entered(enemy)
	_assert_true(enemy.is_dead_flag, "ADV_dead_proj_confirmed")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV_dead_proj_no_acid")
	enemy.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


func test_adv_dead_enemy_executor_path() -> void:
	## Dead enemy via executor path — acid should not apply on dead target.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_dead_exec", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.is_dead_flag = true
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	# Gap: current _apply_modifiers does NOT check is_dead(). MockEnemy.apply_acid
	# doesn't guard either. This exposes that _apply_modifiers should check death.
	# With real EnemyBase, apply_acid guards. With mock, acid_calls will be 1.
	# Test documents the gap: mocks hide the death guard in EnemyBase.apply_acid.
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_dead_exec_acid_applied_mock_gap")
	enemy.free()
	executor.free()


func test_adv_weakened_to_infected_mid_dot() -> void:
	## Duration is set at application time and not re-evaluated during ticks.
	## Apply acid to WEAKENED (6.0s), then transition to INFECTED.
	## DoT should continue with original 6.0s duration.
	## EXPECTED FAIL until WEAKENED doubling is implemented.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_mid_dot_state", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	if enemy.acid_calls.size() > 0:
		var applied_dur: float = enemy.acid_calls[0]["duration"]
		_assert_eq_float(6.0, applied_dur, "ADV_mid_dot_applied_6")
	else:
		_fail_test("ADV_mid_dot_state", "acid not applied")
	# Transition to INFECTED — DoT parameters already locked in
	enemy.current_state = 2
	# Verify apply_acid was only called once (duration set at apply-time)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_mid_dot_once")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# Projectile-specific: consumed flag, multiple bodies
# ---------------------------------------------------------------------------

func test_adv_projectile_second_body_after_consumed() -> void:
	## After consuming on first hit, second body_entered is ignored.
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var e1 = MockEnemy.new()
	var e2 = MockEnemy.new()
	ps["projectile"]._on_body_entered(e1)
	_assert_true(ps["projectile"]._consumed, "ADV_consumed_first")
	_assert_eq_int(1, e1.damage_taken.size(), "ADV_e1_hit")
	ps["projectile"]._on_body_entered(e2)
	_assert_eq_int(0, e2.damage_taken.size(), "ADV_e2_blocked")
	_assert_eq_int(0, e2.acid_calls.size(), "ADV_e2_no_acid")
	e1.free()
	e2.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


func test_adv_projectile_consumed_set_before_body_entered() -> void:
	## Manually set _consumed before any body_entered call → no-op.
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	ps["projectile"]._consumed = true
	var enemy = MockEnemy.new()
	ps["projectile"]._on_body_entered(enemy)
	_assert_eq_int(0, enemy.damage_taken.size(), "ADV_preconsumed_no_dmg")
	_assert_eq_int(0, enemy.acid_calls.size(), "ADV_preconsumed_no_acid")
	enemy.free()
	(ps["root"] as Node).free()


func test_adv_projectile_bare_target_consumed_on_wall() -> void:
	## body without take_damage → projectile consumed (wall collision despawn, ADHA-5).
	var ps = _make_projectile_in_tree({"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0})
	var bare = Node3D.new()
	ps["projectile"]._on_body_entered(bare)
	_assert_true(ps["projectile"]._consumed, "ADV_bare_consumed_on_wall")
	bare.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


func test_adv_projectile_no_apply_acid_skipped_silently() -> void:
	## Target has take_damage but no apply_acid → acid modifier silently skipped.
	var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	var ps = _make_projectile_in_tree(acid_mods)
	var target = NoMethodTarget.new()
	ps["projectile"]._on_body_entered(target)
	_assert_true(ps["projectile"]._consumed, "ADV_no_method_consumed")
	_assert_eq_int(1, target.damage_taken.size(), "ADV_no_method_dmg")
	_pass_test("ADV_no_method_no_crash")
	target.free()
	var root = ps["root"] as Node
	if is_instance_valid(root):
		root.free()


# ---------------------------------------------------------------------------
# Non-stacking / Refresh edge cases
# ---------------------------------------------------------------------------

func test_adv_refresh_dps_change_last_write_wins() -> void:
	## First apply at DPS=1.0, refresh at DPS=2.5 → last-write wins.
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	_assert_eq_float(1.0, tracker._active_dots["acid"]["dps"], "ADV_refresh_dps_first")
	tracker.add_dot("acid", 3.0, 2.5)
	_assert_eq_float(2.5, tracker._active_dots["acid"]["dps"], "ADV_refresh_dps_last_wins")
	tracker.free()


func test_adv_refresh_weakened_then_normal_duration() -> void:
	## First apply when WEAKENED (6.0s), re-apply when NORMAL (3.0s).
	## Verifies duration is set per-application, not retained from first.
	## EXPECTED FAIL until WEAKENED doubling is implemented.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_weak_norm", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	enemy.current_state = 1
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(6.0, enemy.acid_calls[0]["duration"], "ADV_weak_norm_first_6")
	enemy.current_state = 0
	executor._apply_modifiers(enemy, mods)
	if enemy.acid_calls.size() > 1:
		_assert_eq_float(3.0, enemy.acid_calls[1]["duration"], "ADV_weak_norm_second_3")
	else:
		_fail_test("ADV_weak_norm", "second apply not recorded")
	enemy.free()
	executor.free()


func test_adv_acid_poison_independent_tracking() -> void:
	## Acid and poison coexist with independent durations and DPS.
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	tracker.add_dot("poison", 5.0, 0.3)
	_assert_true(tracker.has_active_dot("acid"), "ADV_coexist_acid")
	_assert_true(tracker.has_active_dot("poison"), "ADV_coexist_poison")
	_assert_eq_float(3.0, tracker._active_dots["acid"]["remaining_duration"], "ADV_acid_dur")
	_assert_eq_float(5.0, tracker._active_dots["poison"]["remaining_duration"], "ADV_poison_dur")
	_assert_eq_float(1.0, tracker._active_dots["acid"]["dps"], "ADV_acid_dps")
	_assert_eq_float(0.3, tracker._active_dots["poison"]["dps"], "ADV_poison_dps")
	tracker.free()


func test_adv_stop_all_effects_clears_acid() -> void:
	## Verifies death path: stop_all_effects removes acid DoT.
	var tracker = EnemyEffectTracker.new()
	tracker.add_dot("acid", 3.0, 1.0)
	_assert_true(tracker.has_active_dot("acid"), "ADV_stop_pre")
	tracker.stop_all_effects()
	_assert_false(tracker.has_active_dot("acid"), "ADV_stop_post")
	tracker.free()


# ---------------------------------------------------------------------------
# Registration edge cases
# ---------------------------------------------------------------------------

func test_adv_double_acid_registration_last_wins() -> void:
	## Double registration of "acid" → last-write-wins (dictionary overwrite).
	var db = AttackDatabaseNode.new()
	var r1 = _make_resource({"damage": 1.0, "effect_type": "PROJECTILE_SPIT"})
	var r2 = _make_resource({"damage": 99.0, "effect_type": "PROJECTILE_SPIT"})
	db.register_base_attack("acid", r1)
	db.register_base_attack("acid", r2)
	_assert_eq_float(99.0, db.get_base_attack("acid").damage, "ADV_double_reg_last_wins")
	_assert_eq_int(1, db.get_base_attack_count(), "ADV_double_reg_count")
	db.free()


func test_adv_acid_registration_does_not_affect_claw() -> void:
	## Adding acid must not corrupt existing claw entry.
	var db = AttackDatabaseNode.new()
	var claw = _make_resource({"damage": 3.0, "effect_type": "MELEE_SWIPE", "cooldown": 0.8})
	var acid = _make_resource({"damage": 1.0, "effect_type": "PROJECTILE_SPIT", "cooldown": 2.0})
	db.register_base_attack("claw", claw)
	db.register_base_attack("acid", acid)
	_assert_eq_float(3.0, db.get_base_attack("claw").damage, "ADV_claw_intact_dmg")
	_assert_eq_float(0.8, db.get_base_attack("claw").cooldown, "ADV_claw_intact_cd")
	_assert_eq_float(1.0, db.get_base_attack("acid").damage, "ADV_acid_dmg")
	_assert_eq_int(2, db.get_base_attack_count(), "ADV_two_entries")
	db.free()


func test_adv_get_nonexistent_returns_null() -> void:
	var db = AttackDatabaseNode.new()
	var result = db.get_base_attack("nonexistent")
	_assert_true(result == null, "ADV_nonexistent_null")
	db.free()


# ---------------------------------------------------------------------------
# Concurrency / Order: Executor active-flag, multi-modifier interaction
# ---------------------------------------------------------------------------

func test_adv_active_flag_blocks_acid_projectile() -> void:
	## _is_active on executor blocks execute_attack dispatch entirely.
	var scene = _build_scene("ADV_active_acid", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	var executor = scene["executor"]
	executor.set("_is_active", true)
	_connect_projectile_signal(executor)
	executor.execute_attack(_make_acid_resource())
	_assert_eq_int(0, _projectile_log.size(), "ADV_active_no_projectile")
	executor.set("_is_active", false)
	_teardown(scene)


func test_adv_executor_acid_and_poison_both_apply() -> void:
	## Modifiers with both acid_on_hit and poison → both fire independently.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_both_mods", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0,
				 "poison": true, "poison_duration": 5.0, "poison_dps": 0.3}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_both_acid")
	_assert_eq_int(1, enemy.poison_calls.size(), "ADV_both_poison")
	enemy.free()
	executor.free()


func test_adv_projectile_acid_and_poison_both_apply() -> void:
	## Same test on projectile path: acid + poison both fire.
	var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0,
				 "poison": true, "poison_duration": 5.0, "poison_dps": 0.3}
	var ps = _make_projectile_in_tree(mods)
	var enemy = MockEnemy.new()
	ps["projectile"]._apply_modifiers(enemy)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_proj_both_acid")
	_assert_eq_int(1, enemy.poison_calls.size(), "ADV_proj_both_poison")
	enemy.free()
	(ps["root"] as Node).free()


# ---------------------------------------------------------------------------
# Mutation testing: truthy values in modifiers
# ---------------------------------------------------------------------------

func test_adv_acid_on_hit_integer_truthy() -> void:
	## acid_on_hit: 1 (int) — GDScript Dictionary.get() returns 1, which is truthy.
	## Tests whether implementation breaks if value isn't strict bool true.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_int_truthy", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": 1, "acid_duration": 3.0, "acid_dps": 1.0}
	executor._apply_modifiers(enemy, mods)
	_assert_eq_int(1, enemy.acid_calls.size(), "ADV_int_truthy_acid_applied")
	enemy.free()
	executor.free()


func test_adv_acid_duration_as_int() -> void:
	## acid_duration: 3 (int, not float) — GDScript should handle implicit cast.
	var executor = AttackExecutorHarness.make_executor()
	if executor == null:
		_fail_test("ADV_int_dur", "executor not loadable")
		return
	var enemy = MockEnemy.new()
	var mods := {"acid_on_hit": true, "acid_duration": 3, "acid_dps": 1}
	executor._apply_modifiers(enemy, mods)
	if enemy.acid_calls.size() > 0:
		_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "ADV_int_dur_3")
		_assert_eq_float(1.0, enemy.acid_calls[0]["dps"], "ADV_int_dps_1")
	else:
		_fail_test("ADV_int_dur", "acid not applied")
	enemy.free()
	executor.free()


# ---------------------------------------------------------------------------
# Visual distinction: Color property edge cases
# ---------------------------------------------------------------------------

func test_adv_acid_color_not_equal_to_claw_color() -> void:
	## Acid Color.CHARTREUSE must be distinct from Claw Color.ORANGE_RED.
	_assert_true(Color.CHARTREUSE != Color.ORANGE_RED, "ADV_acid_claw_colors_differ")


func test_adv_executor_projectile_color_set() -> void:
	## EXPECTED FAIL until color-set logic is implemented in _handle_projectile_spit.
	## Verifies _handle_projectile_spit sets projectile.color = resource.color.
	var scene = _build_scene("ADV_color_set", [], Vector3.ZERO, 1.0)
	if scene.is_empty():
		return
	_connect_projectile_signal(scene["executor"])
	scene["executor"].execute_attack(_make_acid_resource())
	if _projectile_log.size() > 0:
		var proj = _projectile_log[0]["projectile"]
		var proj_color = proj.get("color")
		if proj_color != null:
			_assert_true(proj_color == Color.CHARTREUSE, "ADV_proj_color_chartreuse")
			_assert_true(proj_color != Color.WHITE, "ADV_proj_color_not_default")
		else:
			_fail_test("ADV_color_set", "color property missing on projectile")
	else:
		_fail_test("ADV_color_set", "no projectile spawned")
	_teardown(scene)


# ---------------------------------------------------------------------------
# Determinism: repeated identical runs
# ---------------------------------------------------------------------------

func test_adv_repeated_acid_identical_output() -> void:
	for trial in range(3):
		var acid_mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
		var ps = _make_projectile_in_tree(acid_mods)
		var enemy = MockEnemy.new()
		enemy.current_state = 0
		ps["projectile"]._on_body_entered(enemy)
		_assert_eq_int(1, enemy.damage_taken.size(), "ADV_determ_dmg_" + str(trial))
		_assert_eq_int(1, enemy.acid_calls.size(), "ADV_determ_acid_" + str(trial))
		if enemy.acid_calls.size() > 0:
			_assert_eq_float(3.0, enemy.acid_calls[0]["duration"], "ADV_determ_dur_" + str(trial))
		enemy.free()
		var root = ps["root"] as Node
		if is_instance_valid(root):
			root.free()


func test_adv_repeated_weakened_identical_output() -> void:
	## EXPECTED FAIL until WEAKENED doubling is implemented.
	for trial in range(3):
		var executor = AttackExecutorHarness.make_executor()
		if executor == null:
			_fail_test("ADV_determ_weak_" + str(trial), "executor not loadable")
			continue
		var enemy = MockEnemy.new()
		enemy.current_state = 1
		var mods := {"acid_on_hit": true, "acid_duration": 3.0, "acid_dps": 1.0}
		executor._apply_modifiers(enemy, mods)
		if enemy.acid_calls.size() > 0:
			_assert_eq_float(6.0, enemy.acid_calls[0]["duration"], "ADV_determ_weak_" + str(trial))
		else:
			_fail_test("ADV_determ_weak_" + str(trial), "acid not applied")
		enemy.free()
		executor.free()


# ---------------------------------------------------------------------------
# Stress: Rapid refresh, large batch DoT
# ---------------------------------------------------------------------------

func test_adv_rapid_refresh_ten_times() -> void:
	## Apply acid 10 times in quick succession; only last-write state persists.
	var tracker = EnemyEffectTracker.new()
	for i in range(10):
		tracker.add_dot("acid", 3.0, float(i) + 0.1)
	_assert_true(tracker.has_active_dot("acid"), "ADV_rapid_10_active")
	_assert_eq_float(3.0, tracker._active_dots["acid"]["remaining_duration"], "ADV_rapid_10_dur")
	_assert_eq_float(9.1, tracker._active_dots["acid"]["dps"], "ADV_rapid_10_last_dps")
	_assert_eq_float(0.0, tracker._active_dots["acid"]["elapsed_since_tick"], "ADV_rapid_10_tick_reset")
	tracker.free()


func test_adv_many_different_dots_coexist() -> void:
	## 20 different DoT effect names should all coexist.
	var tracker = EnemyEffectTracker.new()
	for i in range(20):
		tracker.add_dot("effect_" + str(i), 3.0, 1.0)
	for i in range(20):
		_assert_true(tracker.has_active_dot("effect_" + str(i)), "ADV_many_dots_" + str(i))
	tracker.free()


# ---------------------------------------------------------------------------
# Assumption checks: DEFAULT_ACID_DPS constant
# ---------------------------------------------------------------------------

func test_adv_default_acid_dps_constant_match() -> void:
	## Both AttackExecutor and PlayerProjectile3D must agree on DEFAULT_ACID_DPS.
	_assert_eq_float(AttackExecutor.DEFAULT_ACID_DPS, PlayerProjectile3D.DEFAULT_ACID_DPS,
		"ADV_dps_constant_sync")


func test_adv_default_acid_dps_is_fallback_not_primary() -> void:
	## The acid resource uses explicit acid_dps=1.0, not DEFAULT_ACID_DPS=0.2.
	var acid = _make_acid_resource()
	var resource_dps: float = acid.modifiers.get("acid_dps", 0.0)
	_assert_true(resource_dps != AttackExecutor.DEFAULT_ACID_DPS,
		"ADV_explicit_dps_not_fallback")
	_assert_eq_float(1.0, resource_dps, "ADV_explicit_dps_1")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AcidAttackAdversarialTests ===")

	test_adv_acid_on_hit_false_explicit()
	test_adv_empty_modifiers_no_acid()
	test_adv_missing_acid_duration_uses_fallback()
	test_adv_missing_acid_dps_uses_fallback()
	test_adv_projectile_empty_modifiers_no_acid()
	test_adv_projectile_acid_on_hit_false()

	test_adv_zero_damage_acid_still_applies()
	test_adv_huge_duration_accepted()
	test_adv_huge_dps_accepted()
	test_adv_near_zero_duration_accepted()
	test_adv_cooldown_exactly_2s()

	test_adv_acid_state_99_base_duration()
	test_adv_acid_state_negative_base_duration()
	test_adv_dead_enemy_projectile_killed_by_hit()
	test_adv_dead_enemy_executor_path()
	test_adv_weakened_to_infected_mid_dot()

	test_adv_projectile_second_body_after_consumed()
	test_adv_projectile_consumed_set_before_body_entered()
	test_adv_projectile_bare_target_consumed_on_wall()
	test_adv_projectile_no_apply_acid_skipped_silently()

	test_adv_refresh_dps_change_last_write_wins()
	test_adv_refresh_weakened_then_normal_duration()
	test_adv_acid_poison_independent_tracking()
	test_adv_stop_all_effects_clears_acid()

	test_adv_double_acid_registration_last_wins()
	test_adv_acid_registration_does_not_affect_claw()
	test_adv_get_nonexistent_returns_null()

	test_adv_active_flag_blocks_acid_projectile()
	test_adv_executor_acid_and_poison_both_apply()
	test_adv_projectile_acid_and_poison_both_apply()

	test_adv_acid_on_hit_integer_truthy()
	test_adv_acid_duration_as_int()

	test_adv_acid_color_not_equal_to_claw_color()
	test_adv_executor_projectile_color_set()

	test_adv_repeated_acid_identical_output()
	test_adv_repeated_weakened_identical_output()

	test_adv_rapid_refresh_ten_times()
	test_adv_many_different_dots_coexist()

	test_adv_default_acid_dps_constant_match()
	test_adv_default_acid_dps_is_fallback_not_primary()

	print("AcidAttackAdversarialTests: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
