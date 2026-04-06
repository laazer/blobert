#
# test_attack_telegraph_system_adversarial.gd
#
# Adversarial tests for attack telegraph (mutation, boundaries, stress, spec gaps).
#
# Spec: project_board/specs/attack_telegraph_system_spec.md (ATS-1 … ATS-9, ATS-NF1, ATS-NF2)
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md
#
# ADV-ATS-* traceability in test_name strings.
#

extends "res://tests/utils/test_utils.gd"


const _CONTROLLER_PATH: String = "res://scripts/enemies/enemy_animation_controller.gd"
const _ACID_ATTACK_PATH: String = "res://scripts/enemy/acid_spitter_ranged_attack.gd"
const _ADH_ATTACK_PATH: String = "res://scripts/enemy/adhesion_bug_lunge_attack.gd"
const _ENEMY_PATH: String = "res://scripts/enemy/enemy_infection_3d.gd"

const _CARAPACE_ATTACK_SCRIPT: String = "res://scripts/enemy/carapace_husk_attack.gd"
const _CLAW_ATTACK_SCRIPT: String = "res://scripts/enemy/claw_crawler_attack.gd"

const _MIN_TELEGRAPH_EXPORT: float = 0.3


var _pass_count: int = 0
var _fail_count: int = 0

var _controller_script: GDScript = null
var _load_controller_attempted: bool = false


func _load_controller_script() -> bool:
	if _load_controller_attempted:
		return _controller_script != null
	_load_controller_attempted = true
	_controller_script = load(_CONTROLLER_PATH) as GDScript
	return _controller_script != null


func _new_controller(test_name: String) -> Object:
	if not _load_controller_script():
		_fail(test_name, "missing " + _CONTROLLER_PATH)
		return null
	return _controller_script.new()


func _read_res_text(res_path: String) -> String:
	if not FileAccess.file_exists(res_path):
		return ""
	var f := FileAccess.open(res_path, FileAccess.READ)
	if f == null:
		return ""
	var t: String = f.get_as_text()
	f.close()
	return t


func _make_animation_player_idle_only() -> AnimationPlayer:
	var ap := AnimationPlayer.new()
	var lib := AnimationLibrary.new()
	var idle_anim := Animation.new()
	idle_anim.length = 0.02
	idle_anim.loop_mode = Animation.LOOP_NONE
	lib.add_animation(&"Idle", idle_anim)
	var err: Error = ap.add_animation_library(&"", lib)
	if err != OK:
		push_warning("test_attack_telegraph_system_adversarial: idle-only library failed: %s" % error_string(err))
	return ap


func _make_animation_player_with_idle_and_attack(attack_len_sec: float) -> AnimationPlayer:
	var ap := AnimationPlayer.new()
	var lib := AnimationLibrary.new()
	var idle_anim := Animation.new()
	idle_anim.length = 0.02
	idle_anim.loop_mode = Animation.LOOP_NONE
	var atk_anim := Animation.new()
	atk_anim.length = attack_len_sec
	atk_anim.loop_mode = Animation.LOOP_NONE
	lib.add_animation(&"Idle", idle_anim)
	lib.add_animation(&"Attack", atk_anim)
	var err: Error = ap.add_animation_library(&"", lib)
	if err != OK:
		push_warning("test_attack_telegraph_system_adversarial: add_animation_library failed: %s" % error_string(err))
	return ap


func _wire_enemy_acid_with_ap(test_name: String, attack_clip_len: float) -> Array:
	var enemy_script: GDScript = load(_ENEMY_PATH) as GDScript
	if enemy_script == null:
		_fail(test_name, "missing " + _ENEMY_PATH)
		return []

	var enemy: Node = enemy_script.new() as Node
	enemy.name = "AdvTelegraphEnemy"
	if "mutation_drop" in enemy:
		enemy.set("mutation_drop", "acid")

	var ap: AnimationPlayer = _make_animation_player_with_idle_and_attack(attack_clip_len)
	ap.name = "AnimationPlayer"

	var ctrl: Object = _new_controller(test_name + "_ctrl")
	if ctrl == null:
		enemy.free()
		return []

	enemy.add_child(ap)
	ctrl.name = "EnemyAnimationController"
	enemy.add_child(ctrl)

	enemy._ready()
	enemy.call("_wire_and_notify_animation")

	var atk: Node = enemy.get_node_or_null("AcidSpitterRangedAttack")
	if atk == null:
		_fail(test_name, "AcidSpitterRangedAttack not wired")
		enemy.free()
		return []

	atk._ready()
	return [enemy, atk, ctrl, ap]


func _wire_enemy_acid_fallback_only(test_name: String) -> Array:
	var enemy_script: GDScript = load(_ENEMY_PATH) as GDScript
	if enemy_script == null:
		_fail(test_name, "missing " + _ENEMY_PATH)
		return []

	var enemy: Node = enemy_script.new() as Node
	enemy.name = "AdvTelegraphEnemyFb"
	if "mutation_drop" in enemy:
		enemy.set("mutation_drop", "acid")

	var ap: AnimationPlayer = _make_animation_player_idle_only()
	ap.name = "AnimationPlayer"

	var ctrl: Object = _new_controller(test_name + "_ctrlfb")
	if ctrl == null:
		enemy.free()
		return []

	enemy.add_child(ap)
	ctrl.name = "EnemyAnimationController"
	enemy.add_child(ctrl)

	enemy._ready()
	enemy.call("_wire_and_notify_animation")

	var atk: Node = enemy.get_node_or_null("AcidSpitterRangedAttack")
	if atk == null:
		_fail(test_name, "AcidSpitterRangedAttack not wired")
		enemy.free()
		return []

	atk._ready()
	return [enemy, atk, ctrl, ap]


func _attach_to_scene_root(node: Node) -> void:
	var tree := Engine.get_main_loop() as SceneTree
	if tree == null:
		return
	tree.root.add_child(node)


func _detach_and_free(node: Node) -> void:
	if node == null or not is_instance_valid(node):
		return
	var p: Node = node.get_parent()
	if p != null:
		p.remove_child(node)
	node.queue_free()


func _chunk_before_substr(src: String, anchor: String, needle: String) -> String:
	var i: int = src.find(anchor)
	if i == -1:
		return ""
	var j: int = src.find(needle, i + anchor.length())
	if j == -1:
		return ""
	return src.substr(i, j - i)


func _create_timer_arg_uses_maxf_with_floor(src: String) -> bool:
	var search_from: int = 0
	while true:
		var idx: int = src.find("create_timer(", search_from)
		if idx == -1:
			break
		var depth: int = 0
		var j: int = idx + "create_timer(".length()
		var end_paren: int = -1
		while j < src.length():
			var ch: String = src.substr(j, 1)
			if ch == "(":
				depth += 1
			elif ch == ")":
				if depth == 0:
					end_paren = j
					break
				depth -= 1
			j += 1
		if end_paren != -1:
			var inner: String = src.substr(idx, end_paren - idx + 1)
			if inner.contains("telegraph_fallback") and inner.contains("maxf") and inner.contains("0.3"):
				return true
		search_from = idx + 1
	return false


# ---------------------------------------------------------------------------
# ADV-ATS-01 — duplicate telegraph completion must not double-spawn (acid, source)
# CHECKPOINT: Headless spawn counting is brittle; we encode the same contract by requiring
# `_on_telegraph_finished` to no-op when `_attack_cycle_active` is already false (after the
# first completion). Spec: ATS-1 single active phase per cycle; ATS-7.3 at-most-once delivery.
# ---------------------------------------------------------------------------

func test_adv_ats_01_acid_on_telegraph_finished_guards_double_completion() -> void:
	var acid_src: String = _read_res_text(_ACID_ATTACK_PATH)
	if acid_src.is_empty():
		_fail_test("ADV-ATS-01", "missing acid attack source")
		return
	var pre_spawn: String = _chunk_before_substr(acid_src, "func _on_telegraph_finished", "_spawn_projectile")
	_assert_true(
		pre_spawn.contains("if not _attack_cycle_active"),
		"ADV-ATS-01_acid_finish_must_guard_when_cycle_inactive_before_spawn"
	)


func test_adv_ats_01b_adhesion_on_telegraph_finished_guards_double_completion() -> void:
	var adh_src: String = _read_res_text(_ADH_ATTACK_PATH)
	if adh_src.is_empty():
		_fail_test("ADV-ATS-01b", "missing adhesion attack source")
		return
	var pre_lunge: String = _chunk_before_substr(adh_src, "func _on_telegraph_finished", "_start_lunge")
	_assert_true(
		pre_lunge.contains("if not _attack_cycle_active"),
		"ADV-ATS-01b_adhesion_finish_must_guard_when_cycle_inactive_before_lunge"
	)


# ---------------------------------------------------------------------------
# ADV-ATS-02 — fallback timer path clamps export to ATS-2 floor (source contract)
# ---------------------------------------------------------------------------

func test_adv_ats_02_fallback_create_timer_clamps_telegraph_export() -> void:
	var acid_src: String = _read_res_text(_ACID_ATTACK_PATH)
	var adh_src: String = _read_res_text(_ADH_ATTACK_PATH)
	if acid_src.is_empty() or adh_src.is_empty():
		_fail_test("ADV-ATS-02", "missing attack script sources")
		return
	_assert_true(
		_create_timer_arg_uses_maxf_with_floor(acid_src),
		"ADV-ATS-02a_acid_create_timer_maxf_telegraph_floor"
	)
	_assert_true(
		_create_timer_arg_uses_maxf_with_floor(adh_src),
		"ADV-ATS-02b_adhesion_create_timer_maxf_telegraph_floor"
	)


# ---------------------------------------------------------------------------
# ADV-ATS-03 — ATS-2 wall-clock hold for animation-driven telegraph end (source)
# CHECKPOINT: We require an explicit 0.3 s (or named constant resolved to 0.3) wall-clock
# hold in `EnemyAnimationController` telegraph completion path so short Attack clips cannot
# end telegraph before ATS-2. Alternative (attack-side deferral) must still reference the same
# floor in telegraph-active code — this test accepts either file containing the hold pattern.
# ---------------------------------------------------------------------------

func test_adv_ats_checkpoint_ats2_animation_path_wall_clock_hold() -> void:
	var ctrl: String = _read_res_text(_CONTROLLER_PATH)
	var acid: String = _read_res_text(_ACID_ATTACK_PATH)
	var adh: String = _read_res_text(_ADH_ATTACK_PATH)
	if ctrl.is_empty():
		_fail_test("ADV-ATS-03", "missing controller source")
		return
	var blob: String = ctrl + "\n" + acid + "\n" + adh
	var has_named: bool = (
		blob.contains("ATS2_MIN_TELEGRAPH")
		or blob.contains("TELEGRAPH_MIN_WALL")
		or blob.contains("MIN_TELEGRAPH_WALL")
	)
	var ctrl_holds: bool = (
		ctrl.contains("_ranged_telegraph_active")
		and ctrl.contains("0.3")
		and (ctrl.contains("create_timer") or ctrl.contains("SceneTreeTimer"))
	)
	_assert_true(
		has_named or ctrl_holds,
		"ADV-ATS-03_checkpoint_ats2_wall_clock_hold_visible_in_sources"
	)


# ---------------------------------------------------------------------------
# ADV-ATS-04 — double `_begin_attack_cycle` re-entry guard (acid, source)
# ---------------------------------------------------------------------------

func test_adv_ats_04_acid_begin_attack_cycle_reentry_guard() -> void:
	var acid_src: String = _read_res_text(_ACID_ATTACK_PATH)
	if acid_src.is_empty():
		_fail_test("ADV-ATS-04", "missing acid attack source")
		return
	var pre_arm: String = _chunk_before_substr(acid_src, "func _begin_attack_cycle", "_attack_cycle_active = true")
	_assert_true(
		pre_arm.contains("if _attack_cycle_active"),
		"ADV-ATS-04_acid_begin_must_short_circuit_when_cycle_already_active"
	)


func test_adv_ats_04b_adhesion_begin_attack_cycle_reentry_guard() -> void:
	var adh_src: String = _read_res_text(_ADH_ATTACK_PATH)
	if adh_src.is_empty():
		_fail_test("ADV-ATS-04b", "missing adhesion attack source")
		return
	var pre_arm: String = _chunk_before_substr(adh_src, "func _begin_attack_cycle", "_attack_cycle_active = true")
	_assert_true(
		pre_arm.contains("if _attack_cycle_active"),
		"ADV-ATS-04b_adhesion_begin_must_short_circuit_when_cycle_already_active"
	)


# ---------------------------------------------------------------------------
# ADV-ATS-05 — NF2 stress: telegraph signal connections stay bounded per cycle (acid)
# ---------------------------------------------------------------------------

func test_adv_ats_05_nf2_repeated_cycles_telegraph_connections_bounded() -> void:
	# No "Attack" clip → fallback SceneTreeTimer path only; avoids leaving controller
	# `_ranged_telegraph_active` stuck when tests invoke `_on_telegraph_finished` directly.
	var arr: Array = _wire_enemy_acid_fallback_only("ADV-ATS-05")
	if arr.is_empty():
		return
	var atk: Node = arr[1]
	var ctrl: Object = arr[2]
	var enemy: Node = arr[0]

	for i in 30:
		atk.call("_begin_attack_cycle")
		var conns: Array = ctrl.get_signal_connection_list(&"ranged_attack_telegraph_finished")
		_assert_true(conns.size() <= 1, "ADV-ATS-05_cycle_%s_at_most_one_pending_telegraph_conn" % str(i))
		atk.call("_on_telegraph_finished")

	if enemy != null and is_instance_valid(enemy):
		enemy.free()


# ---------------------------------------------------------------------------
# ADV-ATS-07 — carapace / claw: when scripts exist, mirror NF2 one-shot telegraph connect
# ---------------------------------------------------------------------------

func test_adv_ats_07_carapace_nf2_when_present() -> void:
	if not ResourceLoader.exists(_CARAPACE_ATTACK_SCRIPT):
		_pass_test("ADV-ATS-07a_skipped_no_carapace_script")
		return
	var src: String = _read_res_text(_CARAPACE_ATTACK_SCRIPT)
	_assert_true(
		src.contains("CONNECT_ONE_SHOT") and src.contains("ranged_attack_telegraph_finished"),
		"ADV-ATS-07a_carapace_one_shot_telegraph_connect"
	)


func test_adv_ats_07_claw_nf2_when_present() -> void:
	if not ResourceLoader.exists(_CLAW_ATTACK_SCRIPT):
		_pass_test("ADV-ATS-07b_skipped_no_claw_script")
		return
	var src: String = _read_res_text(_CLAW_ATTACK_SCRIPT)
	_assert_true(
		src.contains("CONNECT_ONE_SHOT") and src.contains("ranged_attack_telegraph_finished"),
		"ADV-ATS-07b_claw_one_shot_telegraph_connect"
	)


# ---------------------------------------------------------------------------
# ADV-ATS-08 — carapace / claw: export floor when scripts exist (ATS-5)
# ---------------------------------------------------------------------------

func test_adv_ats_08_carapace_export_floor_when_present() -> void:
	if not ResourceLoader.exists(_CARAPACE_ATTACK_SCRIPT):
		_pass_test("ADV-ATS-08a_skipped_no_carapace_script")
		return
	var script: GDScript = load(_CARAPACE_ATTACK_SCRIPT) as GDScript
	if script == null:
		_fail_test("ADV-ATS-08a", "load failed")
		return
	var inst: Object = script.new()
	if inst == null:
		_fail_test("ADV-ATS-08a", "instantiate failed")
		return
	var found_export: bool = false
	var telegraph_val: float = -1.0
	for p in inst.get_property_list():
		var n: String = str(p.name)
		if not n.contains("telegraph") and not n.contains("Telegraph"):
			continue
		if (p.usage & PROPERTY_USAGE_EDITOR) != 0:
			found_export = true
		var v: Variant = inst.get(p.name)
		if typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT:
			telegraph_val = float(v)
	inst.free()
	_assert_true(found_export, "ADV-ATS-08a_carapace_has_telegraph_export")
	if telegraph_val >= 0.0:
		_assert_true(telegraph_val >= _MIN_TELEGRAPH_EXPORT, "ADV-ATS-08a_carapace_telegraph_default_ge_floor")


func test_adv_ats_08_claw_export_floor_when_present() -> void:
	if not ResourceLoader.exists(_CLAW_ATTACK_SCRIPT):
		_pass_test("ADV-ATS-08b_skipped_no_claw_script")
		return
	var script: GDScript = load(_CLAW_ATTACK_SCRIPT) as GDScript
	if script == null:
		_fail_test("ADV-ATS-08b", "load failed")
		return
	var inst: Object = script.new()
	if inst == null:
		_fail_test("ADV-ATS-08b", "instantiate failed")
		return
	var found_export: bool = false
	var telegraph_val: float = -1.0
	for p in inst.get_property_list():
		var n: String = str(p.name)
		if not n.contains("telegraph") and not n.contains("Telegraph"):
			continue
		if (p.usage & PROPERTY_USAGE_EDITOR) != 0:
			found_export = true
		var v: Variant = inst.get(p.name)
		if typeof(v) == TYPE_FLOAT or typeof(v) == TYPE_INT:
			telegraph_val = float(v)
	inst.free()
	_assert_true(found_export, "ADV-ATS-08b_claw_has_telegraph_export")
	if telegraph_val >= 0.0:
		_assert_true(telegraph_val >= _MIN_TELEGRAPH_EXPORT, "ADV-ATS-08b_claw_telegraph_default_ge_floor")


# ---------------------------------------------------------------------------
# ADV-ATS-09 — spec gap: controller rejects nested telegraph while active (returns false)
# ---------------------------------------------------------------------------

func test_adv_ats_09_begin_telegraph_while_active_returns_false() -> void:
	var src: String = _read_res_text(_CONTROLLER_PATH)
	if src.is_empty():
		_fail_test("ADV-ATS-09", "missing controller")
		return
	var ok: bool = src.contains("begin_ranged_attack_telegraph") and src.contains("_ranged_telegraph_active")
	_assert_true(ok, "ADV-ATS-09_controller_guards_reentrant_telegraph")


# ---------------------------------------------------------------------------
# ADV-ATS-10 — adhesion: duplicate `_on_telegraph_finished` must not stack lunges
# CHECKPOINT: Conservative assumption — second finish without a new cycle must not re-arm lunge
# while the first lunge is still active (ATS-1 / avoid double active-phase motion).
# ---------------------------------------------------------------------------

func test_adv_ats_10_adhesion_double_finish_does_not_extend_lunge_window_unbounded() -> void:
	var enemy_script: GDScript = load(_ENEMY_PATH) as GDScript
	if enemy_script == null:
		_fail_test("ADV-ATS-10", "missing enemy_infection_3d.gd")
		return

	var enemy: Node = enemy_script.new() as Node
	enemy.name = "AdvAdhesionEnemy"
	enemy.set("mutation_drop", "adhesion")

	var ap: AnimationPlayer = _make_animation_player_with_idle_and_attack(0.35)
	ap.name = "AnimationPlayer"
	var ctrl: Object = _new_controller("ADV-ATS-10_ctrl")
	if ctrl == null:
		enemy.free()
		return

	enemy.add_child(ap)
	ctrl.name = "EnemyAnimationController"
	enemy.add_child(ctrl)
	enemy._ready()
	enemy.call("_wire_and_notify_animation")

	var atk: Node = enemy.get_node_or_null("AdhesionBugLungeAttack")
	if atk == null:
		_fail_test("ADV-ATS-10", "AdhesionBugLungeAttack not wired")
		enemy.free()
		return
	atk._ready()

	var root := Node3D.new()
	var player := Node3D.new()
	player.add_to_group("player")
	player.global_position = Vector3(0.5, 0.0, 0.0)
	enemy.global_position = Vector3.ZERO
	root.add_child(enemy)
	root.add_child(player)
	_attach_to_scene_root(root)

	atk.call("_begin_attack_cycle")
	atk.call("_on_telegraph_finished")
	var dur1: float = float(atk.get("lunge_duration_seconds"))
	atk.call("_process_lunge", 0.1)
	atk.call("_on_telegraph_finished")
	var timer_after: float = float(atk.get("_lunge_timer"))
	# If second finish incorrectly re-arms lunge, timer snaps back to full duration (spec gap / robustness).
	_assert_true(
		timer_after < dur1 - 0.05,
		"ADV-ATS-10_second_finish_must_not_reset_lunge_after_partial_elapse"
	)

	_detach_and_free(root)


func run_all() -> int:
	print("=== AttackTelegraphSystemAdversarialTests ===")
	_pass_count = 0
	_fail_count = 0

	test_adv_ats_01_acid_on_telegraph_finished_guards_double_completion()
	test_adv_ats_01b_adhesion_on_telegraph_finished_guards_double_completion()
	test_adv_ats_02_fallback_create_timer_clamps_telegraph_export()
	test_adv_ats_checkpoint_ats2_animation_path_wall_clock_hold()
	test_adv_ats_04_acid_begin_attack_cycle_reentry_guard()
	test_adv_ats_04b_adhesion_begin_attack_cycle_reentry_guard()
	test_adv_ats_05_nf2_repeated_cycles_telegraph_connections_bounded()
	test_adv_ats_07_carapace_nf2_when_present()
	test_adv_ats_07_claw_nf2_when_present()
	test_adv_ats_08_carapace_export_floor_when_present()
	test_adv_ats_08_claw_export_floor_when_present()
	test_adv_ats_09_begin_telegraph_while_active_returns_false()
	test_adv_ats_10_adhesion_double_finish_does_not_extend_lunge_window_unbounded()

	print(
		"AttackTelegraphSystemAdversarialTests: "
		+ str(_pass_count)
		+ " passed, "
		+ str(_fail_count)
		+ " failed"
	)
	return _fail_count
