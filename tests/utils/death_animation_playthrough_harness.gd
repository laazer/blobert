#
# death_animation_playthrough_harness.gd
#
# Shared setup helpers for death animation playthrough tests (primary, adversarial,
# infection). Spec: project_board/specs/death_animation_playthrough_spec.md
#

extends RefCounted
class_name DeathAnimationPlaythroughHarness

const SCENE_BASE := "res://scenes/enemies/generated/"


static func scene_path(suffix: String) -> String:
	return SCENE_BASE + suffix + ".tscn"


static func add_generated_with_real_esm(scene_path: String) -> Dictionary:
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


static func cleanup_setup(setup: Dictionary) -> void:
	var inst: Node = setup.get("inst", null) as Node
	var st: SceneTree = setup.get("st", null) as SceneTree
	if inst != null and is_instance_valid(inst):
		if st != null and st.root != null and inst.get_parent() == st.root:
			st.root.remove_child(inst)
		inst.free()


# No SceneTree parent so _inventory exists before _process (same as test_soft_death_and_restart).
static func new_handler_ready() -> Node:
	var handler_script: GDScript = load("res://scripts/infection/infection_interaction_handler.gd") as GDScript
	if handler_script == null:
		return null
	var handler: Node = handler_script.new() as Node
	if handler == null:
		return null
	handler._ready()
	return handler
