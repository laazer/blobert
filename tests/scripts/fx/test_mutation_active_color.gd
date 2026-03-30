#
# test_mutation_active_color.gd
#
# Primary behavioral tests for fusion active color feedback.
# The player mesh tints bright orange + emission while is_fusion_active() == true,
# reverts to baseline green when fusion ends.
#
# Test IDs: MAC-1 through MAC-9
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

const _SVS_PATH := "res://scripts/fx/slime_visual_state.gd"

# Create a wired SlimeVisualState with a real in-memory mesh and material.
# Returns a Dictionary with keys: svs, mesh, mat
func _make_wired() -> Dictionary:
	var SlimeVisualState: GDScript = load(_SVS_PATH)
	var svs: Object = SlimeVisualState.new()
	var mesh := MeshInstance3D.new()
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.4, 0.9, 0.6, 1.0)
	mesh.material_override = mat
	var duped := mat.duplicate() as StandardMaterial3D
	mesh.material_override = duped
	svs.set("_mesh", mesh)
	svs.set("_material", duped)
	svs.set("_mesh_ready", true)
	svs.set("_current_tinted", false)
	return {"svs": svs, "mesh": mesh, "mat": duped}


# Minimal player stub with is_fusion_active() returning a configurable bool.
class PlayerStub extends Object:
	var fusion_active: bool = false
	func is_fusion_active() -> bool:
		return fusion_active


func _cleanup(d: Dictionary) -> void:
	d["svs"].free()
	d["mesh"].free()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

# MAC-1: COLOR_BASELINE constant has correct value
func test_mac_1_color_baseline() -> void:
	var script: GDScript = load(_SVS_PATH)
	var cmap: Dictionary = script.get_script_constant_map()
	if not cmap.has("COLOR_BASELINE"):
		_fail("MAC-1", "COLOR_BASELINE constant not declared in SlimeVisualState")
		return
	_assert_true(
		cmap["COLOR_BASELINE"] == Color(0.4, 0.9, 0.6, 1.0),
		"MAC-1 — COLOR_BASELINE == Color(0.4, 0.9, 0.6, 1.0); got " + str(cmap["COLOR_BASELINE"])
	)


# MAC-2: COLOR_MUTATION_TINT constant has correct value
func test_mac_2_color_tint() -> void:
	var script: GDScript = load(_SVS_PATH)
	var cmap: Dictionary = script.get_script_constant_map()
	if not cmap.has("COLOR_MUTATION_TINT"):
		_fail("MAC-2", "COLOR_MUTATION_TINT constant not declared in SlimeVisualState")
		return
	_assert_true(
		cmap["COLOR_MUTATION_TINT"] == Color(1.0, 0.15, 0.0, 1.0),
		"MAC-2 — COLOR_MUTATION_TINT == Color(1.0, 0.15, 0.0, 1.0); got " + str(cmap["COLOR_MUTATION_TINT"])
	)


# MAC-3: is_fusion_active() method exists on PlayerController3D
func test_mac_3_player_has_is_fusion_active() -> void:
	var script: GDScript = load("res://scripts/player/player_controller_3d.gd")
	var methods: Array = script.get_script_method_list()
	var found := false
	for m in methods:
		if m["name"] == "is_fusion_active":
			found = true
			break
	_assert_true(found, "MAC-3 — PlayerController3D must declare is_fusion_active()")


# MAC-4: When is_fusion_active() == true, _process() sets albedo to COLOR_MUTATION_TINT
func test_mac_4_tint_when_fusion_active() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)

	d["svs"].call("_process", 0.016)

	var cmap: Dictionary = load(_SVS_PATH).get_script_constant_map()
	_assert_true(
		d["mat"].albedo_color == cmap["COLOR_MUTATION_TINT"],
		"MAC-4 — albedo_color should be COLOR_MUTATION_TINT when fusion active; got " + str(d["mat"].albedo_color)
	)
	player.free()
	_cleanup(d)


# MAC-5: When is_fusion_active() == false, _process() keeps albedo at COLOR_BASELINE
func test_mac_5_baseline_when_fusion_inactive() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	player.fusion_active = false
	d["svs"].set("_player", player)

	d["svs"].call("_process", 0.016)

	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"MAC-5 — albedo_color should stay COLOR_BASELINE when fusion inactive; got " + str(d["mat"].albedo_color)
	)
	player.free()
	_cleanup(d)


# MAC-6: Transition from active→inactive reverts color to baseline
func test_mac_6_transition_active_to_inactive() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)
	d["svs"].call("_process", 0.016)

	player.fusion_active = false
	d["svs"].call("_process", 0.016)

	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"MAC-6 — color must revert to COLOR_BASELINE after fusion ends; got " + str(d["mat"].albedo_color)
	)
	player.free()
	_cleanup(d)


# MAC-7: Transition from inactive→active applies tint
func test_mac_7_transition_inactive_to_active() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	player.fusion_active = false
	d["svs"].set("_player", player)
	d["svs"].call("_process", 0.016)
	var before: Color = d["mat"].albedo_color

	player.fusion_active = true
	d["svs"].call("_process", 0.016)
	var after: Color = d["mat"].albedo_color

	var cmap: Dictionary = load(_SVS_PATH).get_script_constant_map()
	_assert_true(before != cmap["COLOR_MUTATION_TINT"], "MAC-7a — color before fusion must not be tint")
	_assert_true(after == cmap["COLOR_MUTATION_TINT"], "MAC-7b — color after fusion must be tint; got " + str(after))
	player.free()
	_cleanup(d)


# MAC-8: _current_tinted starts false
func test_mac_8_current_tinted_initial_false() -> void:
	var SlimeVisualState: GDScript = load(_SVS_PATH)
	var svs: Object = SlimeVisualState.new()
	_assert_false(svs.get("_current_tinted"), "MAC-8 — _current_tinted must be false at construction")
	svs.free()


# MAC-9: Material write skipped when state unchanged (idempotency)
class _CountingMat extends StandardMaterial3D:
	var write_count: int = 0
	func _set(prop: StringName, val: Variant) -> bool:
		if prop == &"albedo_color":
			write_count += 1
		return false  # let normal setter run


func test_mac_9_no_redundant_write() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)

	# First call — state changes (false→true), write happens
	d["svs"].call("_process", 0.016)
	var color_after_first: Color = d["mat"].albedo_color

	# Second call — same state, no write should occur
	# Use sentinel: manually set a different color, call _process, color must stay
	var sentinel := Color(0.1, 0.2, 0.3, 1.0)
	d["mat"].albedo_color = sentinel
	d["svs"].call("_process", 0.016)

	_assert_true(
		d["mat"].albedo_color == sentinel,
		"MAC-9 — second _process() with same state must not overwrite material; got " + str(d["mat"].albedo_color)
	)
	player.free()
	_cleanup(d)


# MAC-GUARD-MESH: _process() no-ops when _mesh_ready is false
func test_mac_guard_mesh_not_ready() -> void:
	var d := _make_wired()
	d["svs"].set("_mesh_ready", false)
	var player := PlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)
	d["mat"].albedo_color = Color(0.4, 0.9, 0.6, 1.0)

	d["svs"].call("_process", 0.016)

	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"MAC-GUARD-MESH — albedo_color must not change when _mesh_ready is false"
	)
	player.free()
	_cleanup(d)


# MAC-GUARD-PLAYER: _process() no-ops when _player is null
func test_mac_guard_player_null() -> void:
	var d := _make_wired()
	d["svs"].set("_player", null)
	d["mat"].albedo_color = Color(0.4, 0.9, 0.6, 1.0)

	d["svs"].call("_process", 0.016)

	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"MAC-GUARD-PLAYER — albedo_color must not change when _player is null"
	)
	_cleanup(d)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_active_color.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_mac_1_color_baseline()
	test_mac_2_color_tint()
	test_mac_3_player_has_is_fusion_active()
	test_mac_4_tint_when_fusion_active()
	test_mac_5_baseline_when_fusion_inactive()
	test_mac_6_transition_active_to_inactive()
	test_mac_7_transition_inactive_to_active()
	test_mac_8_current_tinted_initial_false()
	test_mac_9_no_redundant_write()
	test_mac_guard_mesh_not_ready()
	test_mac_guard_player_null()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
