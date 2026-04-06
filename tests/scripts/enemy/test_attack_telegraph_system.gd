#
# test_attack_telegraph_system.gd
#
# Primary behavioral tests for enemy attack telegraph (wind-up before active phase).
#
# Spec: project_board/specs/attack_telegraph_system_spec.md (ATS-1 … ATS-9, ATS-NF1, ATS-NF2)
# Ticket: project_board/8_milestone_8_enemy_attacks/in_progress/attack_telegraph_system.md
#
# Test IDs: T-ATS-01 … T-ATS-24 (traceability in test_name strings)
# Adversarial: `test_attack_telegraph_system_adversarial.gd` (ADV-ATS-*)
#
# Notes:
# - Wall-clock ≥ 0.3 s (ATS-2) is partially encoded via default export floors; full
#   wall-clock integration depends on SceneTree timers or real-time delays and is
#   deferred to implementation + Test Breaker adversarial cases where applicable.
# - SceneTree node injection: run_tests.gd invokes suites from SceneTree._initialize().
#   Node.get_tree() is unreliable on freshly added nodes during that callback; integration
#   tests that need get_tree() are avoided here (spawn path is covered indirectly via T-04
#   ordering + export/NF2 contracts). Implementation + Test Breaker add full-tree cases.
#

class_name AttackTelegraphSystemTests
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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _count_acid_projectiles_under(node: Node) -> int:
	var n: int = 0
	for c in node.get_children():
		if str(c.get_class()) == "AcidProjectile3D":
			n += 1
		n += _count_acid_projectiles_under(c)
	return n


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
		push_warning("test_attack_telegraph_system: add_animation_library failed: %s" % error_string(err))
	return ap


func _wire_enemy_acid_with_ap(
	test_name: String,
	attack_clip_len: float
) -> Array:
	var enemy_script: GDScript = load(_ENEMY_PATH) as GDScript
	if enemy_script == null:
		_fail(test_name, "missing " + _ENEMY_PATH)
		return []

	var enemy: Node = enemy_script.new() as Node
	enemy.name = "TestEnemyInfection3D"
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


func _export_float_default(script: GDScript, prop_name: String) -> float:
	var inst: Object = script.new()
	if inst == null:
		return -1.0
	for p in inst.get_property_list():
		if str(p.name) != prop_name:
			continue
		var v: Variant = inst.get(prop_name)
		inst.free()
		if typeof(v) == TYPE_FLOAT:
			return v as float
		if typeof(v) == TYPE_INT:
			return float(v as int)
		return -1.0
	inst.free()
	return -1.0


func _script_has_export_named(script: GDScript, substr: String) -> bool:
	var src: String = script.source_code
	return src.contains("@export") and src.contains(substr)


func _file_contains(path: String, needle: String) -> bool:
	if not FileAccess.file_exists(path):
		return false
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		return false
	var text: String = f.get_as_text()
	f.close()
	return text.contains(needle)


# ---------------------------------------------------------------------------
# T-ATS-05 / ATS-5 — exported telegraph tuning (acid + adhesion)
# ---------------------------------------------------------------------------

func test_t_ats_05_acid_export_default_ge_min_floor() -> void:
	var script: GDScript = load(_ACID_ATTACK_PATH) as GDScript
	if script == null:
		_fail_test("T-ATS-05a", "missing acid_spitter_ranged_attack.gd")
		return
	var v: float = _export_float_default(script, "telegraph_fallback_seconds")
	_assert_true(v >= _MIN_TELEGRAPH_EXPORT, "T-ATS-05a_acid_telegraph_fallback_seconds_default_ge_0p3")


func test_t_ats_05_adhesion_export_default_ge_min_floor() -> void:
	var script: GDScript = load(_ADH_ATTACK_PATH) as GDScript
	if script == null:
		_fail_test("T-ATS-05b", "missing adhesion_bug_lunge_attack.gd")
		return
	var v: float = _export_float_default(script, "telegraph_fallback_seconds")
	_assert_true(v >= _MIN_TELEGRAPH_EXPORT, "T-ATS-05b_adhesion_telegraph_fallback_seconds_default_ge_0p3")


func test_t_ats_05_scripts_export_telegraph_field() -> void:
	var acid: GDScript = load(_ACID_ATTACK_PATH) as GDScript
	var adh: GDScript = load(_ADH_ATTACK_PATH) as GDScript
	if acid == null or adh == null:
		_fail_test("T-ATS-05c", "missing attack scripts")
		return
	_assert_true(
		_script_has_export_named(acid, "telegraph_fallback_seconds"),
		"T-ATS-05c_acid_has_export_telegraph_fallback_seconds"
	)
	_assert_true(
		_script_has_export_named(adh, "telegraph_fallback_seconds"),
		"T-ATS-05c_adhesion_has_export_telegraph_fallback_seconds"
	)


# ---------------------------------------------------------------------------
# T-ATS-04 — no projectile / no lunge-hit path during telegraph
# ---------------------------------------------------------------------------

func test_t_ats_04_acid_no_projectile_before_telegraph_completes() -> void:
	var arr: Array = _wire_enemy_acid_with_ap("T-ATS-04a", 0.35)
	if arr.is_empty():
		return
	var enemy: Node = arr[0]
	var atk: Node = arr[1]

	var root := Node3D.new()
	root.name = "TelegraphTestRoot"
	var player := Node3D.new()
	player.name = "Player"
	player.add_to_group("player")
	player.global_position = Vector3(2.0, 0.0, 0.0)
	enemy.global_position = Vector3.ZERO
	root.add_child(enemy)
	root.add_child(player)
	_attach_to_scene_root(root)

	atk.call("_begin_attack_cycle")
	var nproj: int = _count_acid_projectiles_under(root)
	_assert_true(nproj == 0, "T-ATS-04a_no_AcidProjectile3D_before_telegraph_callback")

	_detach_and_free(root)


func test_t_ats_04_adhesion_no_lunge_during_telegraph() -> void:
	var enemy_script: GDScript = load(_ENEMY_PATH) as GDScript
	if enemy_script == null:
		_fail_test("T-ATS-04b", "missing enemy_infection_3d.gd")
		return

	var enemy: Node = enemy_script.new() as Node
	enemy.name = "TestEnemyAdhesion"
	enemy.set("mutation_drop", "adhesion")

	var ap: AnimationPlayer = _make_animation_player_with_idle_and_attack(0.35)
	ap.name = "AnimationPlayer"
	var ctrl: Object = _new_controller("T-ATS-04b_ctrl")
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
		_fail_test("T-ATS-04b", "AdhesionBugLungeAttack not wired")
		enemy.free()
		return
	atk._ready()

	var root := Node3D.new()
	var player := Node3D.new()
	player.add_to_group("player")
	player.global_position = Vector3(1.0, 0.0, 0.0)
	enemy.global_position = Vector3.ZERO
	root.add_child(enemy)
	root.add_child(player)
	_attach_to_scene_root(root)

	atk.call("_begin_attack_cycle")
	var writes_vel: bool = atk.call("enemy_writes_velocity_x_this_frame") as bool
	_assert_true(not writes_vel, "T-ATS-04b_no_lunge_velocity_gate_during_telegraph")

	_detach_and_free(root)


# ---------------------------------------------------------------------------
# T-ATS-03 / T-ATS-7 — Attack telegraph begins with Attack clip; completion signal hooks
# ---------------------------------------------------------------------------

func test_t_ats_07_attack_clip_and_telegraph_signal_wired() -> void:
	var arr: Array = _wire_enemy_acid_with_ap("T-ATS-07a", 0.35)
	if arr.is_empty():
		return
	var atk: Node = arr[1]
	var ctrl: Object = arr[2]
	var ap: AnimationPlayer = arr[3]

	atk.call("_begin_attack_cycle")
	var base: String = str(ap.current_animation).get_file()
	_assert_true(base == "Attack", "T-ATS-07a_Attack_clip_current_after_telegraph_begin")

	var conns: Array = ctrl.get_signal_connection_list(&"ranged_attack_telegraph_finished")
	_assert_true(conns.size() >= 1, "T-ATS-07a_telegraph_completion_signal_connected")

	var enemy: Node = atk.get_parent()
	if enemy != null and is_instance_valid(enemy):
		enemy.free()


# ---------------------------------------------------------------------------
# T-ATS-01 — two-phase structure (telegraph then active) observable
# ---------------------------------------------------------------------------

func test_t_ats_01_attack_scripts_define_telegraph_callbacks() -> void:
	var acid: GDScript = load(_ACID_ATTACK_PATH) as GDScript
	var adh: GDScript = load(_ADH_ATTACK_PATH) as GDScript
	if acid == null or adh == null:
		_fail_test("T-ATS-01", "missing scripts")
		return
	_assert_true(acid.source_code.contains("_begin_attack_cycle"), "T-ATS-01_acid_has_begin_attack_cycle")
	_assert_true(acid.source_code.contains("_on_telegraph_finished"), "T-ATS-01_acid_has_on_telegraph_finished")
	_assert_true(adh.source_code.contains("_begin_attack_cycle"), "T-ATS-01_adhesion_has_begin_attack_cycle")
	_assert_true(adh.source_code.contains("_on_telegraph_finished"), "T-ATS-01_adhesion_has_on_telegraph_finished")


# ---------------------------------------------------------------------------
# T-ATS-08 — carapace + claw attack entry scripts (implementation adds)
# ---------------------------------------------------------------------------

func test_t_ats_08_carapace_attack_script_exists() -> void:
	_assert_true(
		ResourceLoader.exists(_CARAPACE_ATTACK_SCRIPT),
		"T-ATS-08_carapace_husk_attack_script_exists"
	)


func test_t_ats_08_claw_attack_script_exists() -> void:
	_assert_true(
		ResourceLoader.exists(_CLAW_ATTACK_SCRIPT),
		"T-ATS-08_claw_crawler_attack_script_exists"
	)


# ---------------------------------------------------------------------------
# ATS-NF2 — one-shot connect for telegraph completion (acid + adhesion sources)
# ---------------------------------------------------------------------------

func test_t_ats_nf2_one_shot_connect_on_telegraph_signal() -> void:
	_assert_true(
		_file_contains(_ACID_ATTACK_PATH, "CONNECT_ONE_SHOT")
		and _file_contains(_ACID_ATTACK_PATH, "ranged_attack_telegraph_finished"),
		"T-ATS-NF2_acid_uses_one_shot_telegraph_connect"
	)
	_assert_true(
		_file_contains(_ADH_ATTACK_PATH, "CONNECT_ONE_SHOT")
		and _file_contains(_ADH_ATTACK_PATH, "ranged_attack_telegraph_finished"),
		"T-ATS-NF2_adhesion_uses_one_shot_telegraph_connect"
	)


# ---------------------------------------------------------------------------
# T-ATS-06 / ATS-8 — EnemyNameUtils family slugs for four prototype families
# ---------------------------------------------------------------------------

func test_t_ats_06_four_family_slugs_extractable() -> void:
	_assert_eq(
		"acid_spitter",
		EnemyNameUtils.extract_family_name("acid_spitter_animated_00"),
		"T-ATS-06_acid_spitter_slug"
	)
	_assert_eq(
		"adhesion_bug",
		EnemyNameUtils.extract_family_name("adhesion_bug_animated_00"),
		"T-ATS-06_adhesion_bug_slug"
	)
	_assert_eq(
		"carapace_husk",
		EnemyNameUtils.extract_family_name("carapace_husk_animated_00"),
		"T-ATS-06_carapace_husk_slug"
	)
	_assert_eq(
		"claw_crawler",
		EnemyNameUtils.extract_family_name("claw_crawler_animated_01"),
		"T-ATS-06_claw_crawler_slug"
	)


# ---------------------------------------------------------------------------
# Spec gaps / questions for Spec Agent (non-failing notes printed once)
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("=== AttackTelegraphSystemTests ===")
	_pass_count = 0
	_fail_count = 0

	test_t_ats_05_acid_export_default_ge_min_floor()
	test_t_ats_05_adhesion_export_default_ge_min_floor()
	test_t_ats_05_scripts_export_telegraph_field()

	test_t_ats_01_attack_scripts_define_telegraph_callbacks()

	test_t_ats_04_acid_no_projectile_before_telegraph_completes()
	test_t_ats_04_adhesion_no_lunge_during_telegraph()

	test_t_ats_07_attack_clip_and_telegraph_signal_wired()

	test_t_ats_06_four_family_slugs_extractable()

	test_t_ats_08_carapace_attack_script_exists()
	test_t_ats_08_claw_attack_script_exists()

	test_t_ats_nf2_one_shot_connect_on_telegraph_signal()

	print(
		"AttackTelegraphSystemTests: "
		+ str(_pass_count)
		+ " passed, "
		+ str(_fail_count)
		+ " failed"
	)
	return _fail_count
