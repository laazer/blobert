#
# test_death_animation_playthrough.gd
#
# Primary behavioral tests: death animation completes before enemy root is queued
# for deletion; collision cleared during death; one variant per enemy family.
#
# Spec: project_board/specs/death_animation_playthrough_spec.md
# Traceability: DAP-1.1, DAP-1.2, DAP-1.8, DAP-NF2
#

extends "res://tests/utils/test_utils.gd"

const SCENE_BASE := "res://scenes/enemies/generated/"

# DAP-1.8 — at least one variant per family (four scenes).
const FAMILY_SCENE_SUFFIXES: Array[String] = [
	"adhesion_bug_animated_00",
	"acid_spitter_animated_00",
	"claw_crawler_animated_00",
	"carapace_husk_animated_00",
]

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


# DAP-1.1 — queue_free (queued for deletion) only after Death animation completes;
# not while Death is still playing.
func test_dap_11_queue_free_after_death_finishes_not_while_playing() -> void:
	const NAME := "DAP-1.1 — queue_free only after Death completes (not during play)"
	for suf in FAMILY_SCENE_SUFFIXES:
		var path := _scene_path(suf)
		var setup := _add_generated_with_real_esm(path)
		if not setup.get("ok", false):
			_fail(NAME + " [" + suf + "]", str(setup.get("reason", "?")))
			continue
		var inst: CharacterBody3D = setup["inst"] as CharacterBody3D
		var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
		var ap: AnimationPlayer = setup["ap"] as AnimationPlayer
		var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
		if not eac._ready_ok:
			_fail(NAME + " [" + suf + "]", "EnemyAnimationController not ready (_ready_ok false)")
			_cleanup_setup(setup)
			continue
		esm.apply_death_event()
		eac._physics_process(0.016)
		_assert_eq_string("Death", str(ap.current_animation), NAME + " [" + suf + "] — Death is current clip after first tick")
		var steps_while_playing: int = 0
		var early_queue: bool = false
		while ap.is_playing() and steps_while_playing < 4000:
			if inst.is_queued_for_deletion():
				early_queue = true
				break
			ap.advance(1.0 / 60.0)
			steps_while_playing += 1
		_assert_false(
			early_queue,
			NAME + " [" + suf + "] — must not queue_free while Death is still playing"
		)
		_assert_false(
			ap.is_playing() and steps_while_playing >= 4000,
			NAME + " [" + suf + "] — Death clip did not finish within step budget"
		)
		# After natural end of clip, implementation SHALL queue_free the enemy root.
		_assert_true(
			inst.is_queued_for_deletion(),
			NAME + " [" + suf + "] — enemy root queued for deletion after Death completes"
		)
		_cleanup_setup(setup)


# DAP-1.2 — collision_layer and collision_mask 0 for CharacterBody3D while death sequence active.
func test_dap_12_collision_cleared_after_death_starts() -> void:
	const NAME := "DAP-1.2 — collision_layer and collision_mask 0 after death starts"
	var path := _scene_path(FAMILY_SCENE_SUFFIXES[0])
	var setup := _add_generated_with_real_esm(path)
	if not setup.get("ok", false):
		_fail(NAME, str(setup.get("reason", "?")))
		return
	var inst: CharacterBody3D = setup["inst"] as CharacterBody3D
	var eac: EnemyAnimationController = setup["eac"] as EnemyAnimationController
	var esm: EnemyStateMachine = setup["esm"] as EnemyStateMachine
	if not eac._ready_ok:
		_fail(NAME, "EnemyAnimationController not ready")
		_cleanup_setup(setup)
		return
	esm.apply_death_event()
	eac._physics_process(0.016)
	_assert_eq_int(0, inst.collision_layer, NAME + " — collision_layer")
	_assert_eq_int(0, inst.collision_mask, NAME + " — collision_mask")
	_cleanup_setup(setup)


func run_all() -> int:
	print("--- test_death_animation_playthrough.gd ---")
	_pass_count = 0
	_fail_count = 0
	test_dap_11_queue_free_after_death_finishes_not_while_playing()
	test_dap_12_collision_cleared_after_death_starts()
	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
