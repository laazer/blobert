#
# test_death_animation_playthrough_adversarial.gd
#
# Adversarial stress: double lifecycle events, missing clips, freed AnimationPlayer,
# handler/input bursts, concurrent signal fan-out, mini-boss naming.
#
# Spec: project_board/specs/death_animation_playthrough_spec.md
# Traceability: DAP-1.3, DAP-1.4, DAP-1.5, DAP-1.7, DAP-2.1, DAP-2.2, DAP-NF2
#

extends "res://tests/utils/test_utils.gd"

# RefCounted signal bus — user-added Node signals did not fire under headless test runner.
class _CompletionRelay extends RefCounted:
	signal death_completion_pulse()


const SCENE_BASE := "res://scenes/enemies/generated/"

var _pass_count: int = 0
var _fail_count: int = 0


func _scene_path(suffix: String) -> String:
	return SCENE_BASE + suffix + ".tscn"


func _add_generated_with_real_esm(scene_path: String) -> Dictionary:
	if not ResourceLoader.exists(scene_path):
		return {"ok": false, "reason": "missing scene: " + scene_path}
	var packed: PackedScene = load(scene_path) as PackedScene
	if packed == null:
		return {"ok": false, "reason": "PackedScene null"}
	var inst: CharacterBody3D = packed.instantiate() as CharacterBody3D
	if inst == null:
		return {"ok": false, "reason": "instantiate null"}
	var ctrl: Node = inst.get_node_or_null("EnemyAnimationController")
	var ap: AnimationPlayer = inst.get_node_or_null("AnimationPlayer") as AnimationPlayer
	if ctrl == null or ap == null:
		inst.free()
		return {"ok": false, "reason": "missing AnimationPlayer or EnemyAnimationController"}
	var eac: EnemyAnimationController = ctrl as EnemyAnimationController
	var esm := EnemyStateMachine.new()
	eac.setup(esm)
	var st: SceneTree = Engine.get_main_loop() as SceneTree
	if st == null or st.root == null:
		inst.free()
		return {"ok": false, "reason": "no SceneTree root"}
	st.root.add_child(inst)
	if eac.has_method("_ready"):
		eac._ready()
	return {
		"ok": true,
		"inst": inst,
		"eac": eac,
		"ap": ap,
		"esm": esm,
		"st": st,
	}


func _cleanup_setup(setup: Dictionary) -> void:
	var inst: Node = setup.get("inst", null) as Node
	var st: SceneTree = setup.get("st", null) as SceneTree
	if inst != null and is_instance_valid(inst):
		if st != null and st.root != null and inst.get_parent() == st.root:
			st.root.remove_child(inst)
		inst.free()


func _new_handler_ready() -> Node:
	var handler_script: GDScript = load("res://scripts/infection/infection_interaction_handler.gd") as GDScript
	if handler_script == null:
		return null
	var handler: Node = handler_script.new() as Node
	if handler == null:
		return null
	handler._ready()
	return handler


# DAP-2.2 + idempotent ESM — double apply_death_event before physics must not switch to Hit.
func test_adv_double_apply_death_hit_suppressed() -> void:
	# CHECKPOINT — execution plan task 3 (double death / idempotent lifecycle)
	const NAME := "ADV — double apply_death_event; trigger_hit must not override Death (DAP-2.2)"
	var path := _scene_path("adhesion_bug_animated_00")
	var setup := _add_generated_with_real_esm(path)
	if not setup.get("ok", false):
		_fail(NAME, str(setup.get("reason", "?")))
		return
	var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
	var ap: AnimationPlayer = setup["ap"] as AnimationPlayer
	var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
	if not eac._ready_ok:
		_fail(NAME, "controller not ready")
		_cleanup_setup(setup)
		return
	esm.apply_death_event()
	esm.apply_death_event()
	eac._physics_process(0.016)
	eac.trigger_hit_animation()
	eac._physics_process(0.016)
	_assert_eq_string("Death", str(ap.current_animation), NAME + " — still Death after hit attempt")
	_cleanup_setup(setup)


# DAP-2.1 — spam _physics_process while latched; Death clip must not be replaced by state dispatch.
func test_adv_physics_spam_while_death_latched_no_dispatch() -> void:
	const NAME := "ADV — many _physics_process ticks during Death do not restart or switch clip (DAP-2.1)"
	var path := _scene_path("acid_spitter_animated_00")
	var setup := _add_generated_with_real_esm(path)
	if not setup.get("ok", false):
		_fail(NAME, str(setup.get("reason", "?")))
		return
	var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
	var ap: AnimationPlayer = setup["ap"] as AnimationPlayer
	var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
	if not eac._ready_ok:
		_fail(NAME, "controller not ready")
		_cleanup_setup(setup)
		return
	esm.apply_death_event()
	eac._physics_process(0.016)
	var broke: bool = false
	for _i in 500:
		eac._physics_process(0.016)
		if str(ap.current_animation) != "Death":
			broke = true
			break
		if not ap.is_playing():
			break
	_assert_false(broke, NAME + " — current_animation stayed Death under spam")
	_cleanup_setup(setup)


# DAP-1.7 variant — AnimationPlayer freed after death latch; controller must not touch dangling ref.
func test_adv_freed_animation_player_after_death_tick_no_crash() -> void:
	# CHECKPOINT — freed nodes / completion callbacks (planning + spec DAP-1.7)
	const NAME := "ADV — free AnimationPlayer after Death starts; controller pumps do not crash (DAP-1.7)"
	var path := _scene_path("claw_crawler_animated_00")
	var setup := _add_generated_with_real_esm(path)
	if not setup.get("ok", false):
		_fail(NAME, str(setup.get("reason", "?")))
		return
	var inst: CharacterBody3D = setup["inst"] as CharacterBody3D
	var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
	var ap: AnimationPlayer = setup["ap"] as AnimationPlayer
	var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
	var st: SceneTree = setup["st"] as SceneTree
	if not eac._ready_ok:
		_fail(NAME, "controller not ready")
		_cleanup_setup(setup)
		return
	esm.apply_death_event()
	eac._physics_process(0.016)
	var p: Node = ap.get_parent()
	if p != null:
		p.remove_child(ap)
	ap.free()
	for _i in 200:
		eac._physics_process(0.016)
	if inst.get_parent() == st.root:
		st.root.remove_child(inst)
	inst.free()
	_pass(NAME + " — completed without engine errors from dangling player")


# Strip Death from libraries — exposes hang / missing-completion when clip absent (spec DAP-2 risk).
func test_adv_missing_death_clip_no_crash_under_spam() -> void:
	# CHECKPOINT — missing Death clip / completion edge (spec DAP-2 + planning dependency)
	const NAME := "ADV — Death clip removed; controller spam does not crash (missing-clip robustness)"
	var path := _scene_path("carapace_husk_animated_00")
	var setup := _add_generated_with_real_esm(path)
	if not setup.get("ok", false):
		_fail(NAME, str(setup.get("reason", "?")))
		return
	var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
	var ap: AnimationPlayer = setup["ap"] as AnimationPlayer
	var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
	if not eac._ready_ok:
		_fail(NAME, "controller not ready")
		_cleanup_setup(setup)
		return
	for lib_key in ap.get_animation_library_list():
		var lib: AnimationLibrary = ap.get_animation_library(lib_key)
		if lib != null and lib.has_animation("Death"):
			lib.remove_animation("Death")
	esm.apply_death_event()
	# First tick: play("Death") errors once when clip missing; latch still engages (DAP-2 risk).
	eac._physics_process(0.016)
	for _i in 1999:
		eac._physics_process(0.016)
	_cleanup_setup(setup)
	_pass(NAME + " — spam complete (policy for queue_free when clip missing is implementation-defined)")


# DAP-1.3 stress — rapid body_entered while dead must never emit chunk_attached.
func test_adv_chunk_body_entered_burst_while_dead() -> void:
	const NAME := "ADV — burst body_entered on dead enemy — zero chunk_attached (DAP-1.3)"
	var packed: PackedScene = load("res://scenes/enemy/enemy_infection_3d.tscn") as PackedScene
	if packed == null:
		_fail(NAME, "load enemy_infection_3d failed")
		return
	var enemy: EnemyInfection3D = packed.instantiate() as EnemyInfection3D
	if enemy == null:
		_fail(NAME, "instantiate failed")
		return
	var st: SceneTree = Engine.get_main_loop() as SceneTree
	if st == null or st.root == null:
		enemy.free()
		_fail(NAME, "no tree")
		return
	var emissions: Array = [0]
	enemy.chunk_attached.connect(func(_c: RigidBody3D) -> void:
		emissions[0] = int(emissions[0]) + 1
	)
	st.root.add_child(enemy)
	var esm: EnemyStateMachine = enemy.get_esm()
	esm.apply_death_event()
	var area: Area3D = enemy.get_node_or_null("InteractionArea") as Area3D
	if area == null:
		st.root.remove_child(enemy)
		enemy.free()
		_fail(NAME, "InteractionArea missing")
		return
	for _i in 40:
		var chunk := RigidBody3D.new()
		chunk.add_to_group("chunk")
		area.body_entered.emit(chunk)
		chunk.free()
	_assert_eq_int(0, int(emissions[0]), NAME + " — emission count")
	st.root.remove_child(enemy)
	enemy.free()


# DAP-1.4 + DAP-1.5 — absorb and infect both active same tick on dead target.
func test_adv_absorb_and_infect_same_process_dead_target() -> void:
	# CHECKPOINT — double input / stale overlap (execution plan task 3)
	const NAME := "ADV — absorb+infect same _process on dead ESM — no inventory change, state dead"
	var handler: Node = _new_handler_ready()
	if handler == null:
		_fail(NAME, "handler init failed")
		return
	var esm := EnemyStateMachine.new()
	esm.apply_death_event()
	handler.set_target_esm(esm, null)
	var inv: Variant = handler.get_mutation_inventory()
	if inv == null or not inv.has_method("get_granted_count"):
		handler.free()
		_fail(NAME, "inventory missing get_granted_count")
		return
	var before: int = inv.get_granted_count()
	Input.action_press("absorb")
	Input.action_press("infect")
	handler._process(0.0)
	Input.action_release("absorb")
	Input.action_release("infect")
	var after: int = inv.get_granted_count()
	_assert_eq_int(before, after, NAME + " — granted_count")
	_assert_eq_string("dead", esm.get_state(), NAME + " — ESM state")
	handler.free()


# Mini-boss name uses same death contract as regular enemy (planning checkpoint).
func test_adv_mini_boss_name_death_queue_after_animation() -> void:
	# CHECKPOINT — mini-boss / scaled instances same rules (planning run-2026-04-04)
	const NAME := "ADV — EnemyMiniBoss name: queue_free after Death completes (DAP-1.1 / planning)"
	var path := _scene_path("adhesion_bug_animated_00")
	var setup := _add_generated_with_real_esm(path)
	if not setup.get("ok", false):
		_fail(NAME, str(setup.get("reason", "?")))
		return
	var inst: CharacterBody3D = setup["inst"] as CharacterBody3D
	var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
	var ap: AnimationPlayer = setup["ap"] as AnimationPlayer
	var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
	inst.name = "EnemyMiniBoss"
	if not eac._ready_ok:
		_fail(NAME, "controller not ready")
		_cleanup_setup(setup)
		return
	esm.apply_death_event()
	eac._physics_process(0.016)
	var steps: int = 0
	while ap.is_playing() and steps < 4000:
		if inst.is_queued_for_deletion():
			_fail(NAME, "queued for deletion while Death still playing")
			_cleanup_setup(setup)
			return
		ap.advance(1.0 / 60.0)
		steps += 1
	_assert_true(inst.is_queued_for_deletion(), NAME + " — queued after Death completes")
	_cleanup_setup(setup)


# Concurrent signal fan-out: multiple connections each receive every emit — implementer must guard free.
func test_adv_animation_finished_duplicate_connections_double_emit_delivers_four() -> void:
	# CHECKPOINT — concurrent signals / idempotent completion handler (execution plan task 3)
	const NAME := "ADV — completion relay two listeners × two emits = four callbacks (idempotency pressure)"
	var relay := _CompletionRelay.new()
	var hits: Array = [0]
	relay.death_completion_pulse.connect(func() -> void:
		hits[0] = int(hits[0]) + 1
	)
	relay.death_completion_pulse.connect(func() -> void:
		hits[0] = int(hits[0]) + 1
	)
	relay.death_completion_pulse.emit()
	relay.death_completion_pulse.emit()
	if int(hits[0]) == 4:
		_pass(NAME + " — four callbacks document multi-listener fan-out")
	else:
		_fail(NAME, "expected 4 callback invocations, got " + str(hits[0]))


func run_all() -> int:
	print("--- test_death_animation_playthrough_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0
	test_adv_double_apply_death_hit_suppressed()
	test_adv_physics_spam_while_death_latched_no_dispatch()
	test_adv_freed_animation_player_after_death_tick_no_crash()
	test_adv_missing_death_clip_no_crash_under_spam()
	test_adv_chunk_body_entered_burst_while_dead()
	test_adv_absorb_and_infect_same_process_dead_target()
	test_adv_mini_boss_name_death_queue_after_animation()
	test_adv_animation_finished_duplicate_connections_double_emit_delivers_four()
	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
