#
# Structural checks for M11 manual verification sandbox scenes (split layout).

extends "res://tests/utils/test_utils.gd"

const _HUB_PATH: String = "res://scenes/levels/sandbox/m11_verification_3d.tscn"
const _BASE_PATH: String = "res://scenes/levels/sandbox/m11_sandbox_base_3d.tscn"
const _CONTROLLER_SCRIPT: String = "res://scripts/levels/m11_verification_controller_3d.gd"
const _DRC_SCRIPT: String = "res://scripts/system/death_restart_coordinator.gd"

const _SECTION_SCENES: Array[String] = [
	"res://scenes/levels/sandbox/m11_verification_core_3d.tscn",
	"res://scenes/levels/sandbox/m11_verification_infection_3d.tscn",
	"res://scenes/levels/sandbox/m11_verification_claw_3d.tscn",
	"res://scenes/levels/sandbox/m11_verification_acid_3d.tscn",
	"res://scenes/levels/sandbox/m11_verification_carapace_3d.tscn",
	"res://scenes/levels/sandbox/m11_verification_adhesion_3d.tscn",
]

var _pass_count: int = 0
var _fail_count: int = 0


func _assert_scene_loads(scene_path: String, label: String) -> Node:
	var packed: PackedScene = load(scene_path) as PackedScene
	_assert_true(packed != null, "%s_loads" % label)
	if packed == null:
		return null
	var root: Node = packed.instantiate()
	_assert_true(root != null, "%s_instantiates" % label)
	return root


func _assert_has_sandbox_base(root: Node, label: String) -> void:
	var base: Node = root.get_node_or_null("SandboxBase")
	_assert_true(base != null, "%s_has_sandbox_base" % label)
	if base == null:
		return
	_assert_true(base.get_node_or_null("Player3D") != null, "%s_base_has_player" % label)
	_assert_true(base.get_node_or_null("DeathRestartCoordinator") != null, "%s_base_has_drc" % label)


func test_m11_base_has_death_restart_wired() -> void:
	var root: Node = _assert_scene_loads(_BASE_PATH, "m11_base")
	if root == null:
		return
	var drc: Node = root.get_node_or_null("DeathRestartCoordinator")
	_assert_true(drc != null, "m11_base_has_death_restart_coordinator")
	if drc != null:
		var script_res: Resource = drc.get_script()
		if script_res != null:
			_assert_eq_str(script_res.resource_path, _DRC_SCRIPT, "m11_base_drc_script_path")
		_assert_eq_str(str(drc.get("player")), "../Player3D", "m11_base_drc_player_path")
	root.free()


func test_m11_hub_lists_section_scenes() -> void:
	var text: String = FileAccess.get_file_as_string(_HUB_PATH)
	_assert_true(text.find("m11_verification_core_3d.tscn") != -1, "m11_hub_lists_core")
	_assert_true(text.find("m11_verification_infection_3d.tscn") != -1, "m11_hub_lists_infection")
	_assert_true(text.find("m11_verification_adhesion_3d.tscn") != -1, "m11_hub_lists_adhesion")


func test_m11_section_scenes_load_with_controller() -> void:
	for scene_path in _SECTION_SCENES:
		var short: String = scene_path.get_file().trim_suffix(".tscn")
		var root: Node = _assert_scene_loads(scene_path, short)
		if root == null:
			continue
		_assert_has_sandbox_base(root, short)
		var controller: Node = root.get_node_or_null("M11VerificationController")
		_assert_true(controller != null, "%s_has_controller" % short)
		if controller != null:
			var script_res: Resource = controller.get_script()
			if script_res != null:
				_assert_eq_str(script_res.resource_path, _CONTROLLER_SCRIPT, "%s_controller_script" % short)
		root.free()


func test_m11_infection_scene_disables_auto_seed() -> void:
	var path: String = "res://scenes/levels/sandbox/m11_verification_infection_3d.tscn"
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		_fail("m11_infection_load", "could not load infection scene")
		return
	var root: Node = packed.instantiate()
	var controller: Node = root.get_node_or_null("M11VerificationController")
	_assert_true(controller != null, "m11_infection_has_controller")
	if controller != null:
		_assert_false(bool(controller.get("auto_seed_slot_a")), "m11_infection_auto_seed_off")
	root.free()


func test_m11_adhesion_scene_has_despawn_wall() -> void:
	var path: String = "res://scenes/levels/sandbox/m11_verification_adhesion_3d.tscn"
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		_fail("m11_adhesion_load", "could not load adhesion scene")
		return
	var root: Node = packed.instantiate()
	_assert_true(root.get_node_or_null("AdhesionWall") != null, "m11_adhesion_has_wall")
	root.free()


func run_all() -> int:
	_pass_count = 0
	_fail_count = 0
	test_m11_base_has_death_restart_wired()
	test_m11_hub_lists_section_scenes()
	test_m11_section_scenes_load_with_controller()
	test_m11_infection_scene_disables_auto_seed()
	test_m11_adhesion_scene_has_despawn_wall()
	return _fail_count
