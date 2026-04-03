#
# test_enemy_scene_animation_wiring.gd
#
# Verifies generated enemy .tscn files wire root AnimationPlayer clips from the GLB
# and that EnemyAnimationController reaches _ready_ok when added to the scene tree.
#
# Spec: project_board/specs/wire_animations_to_generated_scenes_spec.md
# Test IDs: WAGS-01 .. WAGS-12 (one per generated scene path)
#

extends "res://tests/utils/test_utils.gd"

const SCENE_BASE := "res://scenes/enemies/generated/"
const FAMILIES: Array[String] = [
	"adhesion_bug",
	"acid_spitter",
	"claw_crawler",
	"carapace_husk",
]
const VARIANT_SUFFIXES: Array[String] = ["_animated_00", "_animated_01", "_animated_02"]
const REQUIRED_CLIPS: Array[String] = ["Idle", "Walk", "Hit", "Death"]

var _pass_count: int = 0
var _fail_count: int = 0


func _scene_path(family: String, variant_suffix: String) -> String:
	return SCENE_BASE + family + variant_suffix + ".tscn"


func _list_all_scene_paths() -> Array[String]:
	var out: Array[String] = []
	for family in FAMILIES:
		for suf in VARIANT_SUFFIXES:
			out.append(_scene_path(family, suf))
	return out


func _clip_set(anim_player: AnimationPlayer) -> Dictionary:
	var d := {}
	for n in anim_player.get_animation_list():
		d[str(n)] = true
	return d


func _assert_scene_wiring(scene_path: String, test_prefix: String) -> void:
	if not ResourceLoader.exists(scene_path):
		_fail(test_prefix + " — load", "missing: " + scene_path)
		return
	var packed: PackedScene = load(scene_path) as PackedScene
	if packed == null:
		_fail(test_prefix + " — pack", "PackedScene null: " + scene_path)
		return
	var inst: Node = packed.instantiate()
	if inst == null:
		_fail(test_prefix + " — inst", "instantiate null: " + scene_path)
		return

	var ap: AnimationPlayer = inst.get_node_or_null("AnimationPlayer") as AnimationPlayer
	_assert_true(ap != null, test_prefix + " — root AnimationPlayer", "no root AnimationPlayer: " + scene_path)
	if ap == null:
		inst.free()
		return

	var clip_names := _clip_set(ap)
	for clip in REQUIRED_CLIPS:
		_assert_true(
			clip_names.has(clip),
			test_prefix + " — clip " + clip,
			"missing clip '%s' in %s; has %s" % [clip, scene_path, str(ap.get_animation_list())]
		)

	var ctrl: Node = inst.get_node_or_null("EnemyAnimationController")
	_assert_true(ctrl != null, test_prefix + " — controller node", scene_path)
	if ctrl == null:
		inst.free()
		return

	var stub: Node = ctrl.get_node_or_null("GeneratedEnemyEsmStub")
	_assert_true(stub != null, test_prefix + " — stub child", scene_path)

	var st: SceneTree = Engine.get_main_loop() as SceneTree
	if st == null or st.root == null:
		_fail(test_prefix + " — tree", "no SceneTree root")
		inst.free()
		return

	st.root.add_child(inst)

	var eac: EnemyAnimationController = ctrl as EnemyAnimationController
	_assert_true(eac != null, test_prefix + " — controller class", scene_path)
	if eac == null:
		st.root.remove_child(inst)
		inst.free()
		return

	# _ready() is normally deferred; run once now so _ready_ok matches runtime after first frame.
	eac._ready()

	_assert_true(
		eac.animation_player != null,
		test_prefix + " — controller.animation_player",
		scene_path
	)
	_assert_true(
		eac._ready_ok,
		test_prefix + " — controller._ready_ok",
		scene_path + " (dependencies unresolved)"
	)
	st.root.remove_child(inst)
	inst.free()


func run_all() -> int:
	print("--- test_enemy_scene_animation_wiring.gd ---")
	_pass_count = 0
	_fail_count = 0

	var idx := 0
	for path in _list_all_scene_paths():
		idx += 1
		_assert_scene_wiring(path, "WAGS-%02d" % idx)

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
