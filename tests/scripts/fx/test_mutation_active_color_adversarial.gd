#
# test_mutation_active_color_adversarial.gd
#
# Adversarial tests for fusion active color feedback.
# Covers guard paths, state transitions, ready-order bug regression,
# and material duplication independence.
#
# Test IDs: ADV-MAC-1 through ADV-MAC-9
#

extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0


const _SVS_PATH := "res://scripts/fx/slime_visual_state.gd"

class PlayerStub extends Object:
	var fusion_active: bool = false
	func is_fusion_active() -> bool:
		return fusion_active


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


func _cleanup(d: Dictionary) -> void:
	d["svs"].free()
	d["mesh"].free()


# ---------------------------------------------------------------------------
# ADV-MAC-1: Freed player reference — is_instance_valid guard must not crash
# ---------------------------------------------------------------------------

func test_adv_mac_1_freed_player_no_crash() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	d["svs"].set("_player", player)
	player.free()  # free before _process runs

	d["svs"].call("_process", 0.016)  # must not crash

	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-1 — albedo_color must not change when player is freed"
	)
	_cleanup(d)


# ---------------------------------------------------------------------------
# ADV-MAC-2: _mesh_ready=false suppresses is_fusion_active() poll
# ---------------------------------------------------------------------------

class _CountingPlayerStub extends Object:
	var fusion_active: bool = false
	var poll_count: int = 0
	func is_fusion_active() -> bool:
		poll_count += 1
		return fusion_active


func test_adv_mac_2_mesh_not_ready_suppresses_poll() -> void:
	var d := _make_wired()
	d["svs"].set("_mesh_ready", false)
	var player := _CountingPlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)

	d["svs"].call("_process", 0.016)

	_assert_true(player.poll_count == 0, "ADV-MAC-2 — is_fusion_active() must not be called when _mesh_ready is false")
	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-2b — albedo_color must remain baseline when _mesh_ready is false"
	)
	player.free()
	_cleanup(d)


# ---------------------------------------------------------------------------
# ADV-MAC-3: null material guard — _mesh_ready=false prevents null deref
# ---------------------------------------------------------------------------

func test_adv_mac_3_null_material_no_crash() -> void:
	var SlimeVisualState: GDScript = load(_SVS_PATH)
	var svs: Object = SlimeVisualState.new()
	var mesh := MeshInstance3D.new()
	# material_override intentionally left null
	svs.set("_mesh", mesh)
	svs.set("_material", null)
	svs.set("_mesh_ready", false)  # must be false when material is null
	var player := PlayerStub.new()
	player.fusion_active = true
	svs.set("_player", player)

	svs.call("_process", 0.016)  # must not crash

	_assert_true(mesh.material_override == null, "ADV-MAC-3 — material_override must remain null")
	player.free()
	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-4: Organic bidirectional sequence (inactive→active→inactive)
# ---------------------------------------------------------------------------

func test_adv_mac_4_bidirectional_sequence() -> void:
	var d := _make_wired()
	var player := PlayerStub.new()
	player.fusion_active = false
	d["svs"].set("_player", player)

	var cmap: Dictionary = load(_SVS_PATH).get_script_constant_map()

	# Step 1: inactive — baseline
	d["svs"].call("_process", 0.016)
	_assert_true(d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0), "ADV-MAC-4a — step1 baseline; got " + str(d["mat"].albedo_color))

	# Step 2: active — tint
	player.fusion_active = true
	d["svs"].call("_process", 0.016)
	_assert_true(d["mat"].albedo_color == cmap["COLOR_MUTATION_TINT"], "ADV-MAC-4b — step2 tint; got " + str(d["mat"].albedo_color))

	# Step 3: inactive again — revert
	player.fusion_active = false
	d["svs"].call("_process", 0.016)
	_assert_true(d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0), "ADV-MAC-4c — step3 revert; got " + str(d["mat"].albedo_color))

	player.free()
	_cleanup(d)


# ---------------------------------------------------------------------------
# ADV-MAC-5: player without is_fusion_active() — no crash, no color change
# ---------------------------------------------------------------------------

func test_adv_mac_5_player_missing_method_no_crash() -> void:
	var d := _make_wired()
	var bare := Object.new()  # no is_fusion_active() method
	d["svs"].set("_player", bare)
	d["mat"].albedo_color = Color(0.4, 0.9, 0.6, 1.0)

	d["svs"].call("_process", 0.016)  # must not crash

	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-5 — no color change when player lacks is_fusion_active()"
	)
	bare.free()
	_cleanup(d)


# ---------------------------------------------------------------------------
# ADV-MAC-6: 100 _process() calls — material write only on state change
# ---------------------------------------------------------------------------

func test_adv_mac_6_hundred_calls_write_once() -> void:
	var d := _make_wired()
	var player := _CountingPlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)

	# First call — state changes, write happens
	d["svs"].call("_process", 0.016)
	var cmap: Dictionary = load(_SVS_PATH).get_script_constant_map()
	_assert_true(d["mat"].albedo_color == cmap["COLOR_MUTATION_TINT"], "ADV-MAC-6a — first call applies tint")

	# 99 more calls — same state, sentinel must survive
	var sentinel := Color(0.1, 0.2, 0.3, 1.0)
	d["mat"].albedo_color = sentinel
	for i in range(99):
		d["svs"].call("_process", 0.016)

	_assert_true(d["mat"].albedo_color == sentinel, "ADV-MAC-6b — sentinel survives 99 more calls; got " + str(d["mat"].albedo_color))
	_assert_true(player.poll_count == 100, "ADV-MAC-6c — is_fusion_active() called 100 times; got " + str(player.poll_count))

	player.free()
	_cleanup(d)


# ---------------------------------------------------------------------------
# ADV-MAC-7: COLOR_BASELINE and COLOR_MUTATION_TINT are distinct
# ---------------------------------------------------------------------------

func test_adv_mac_7_colors_are_distinct() -> void:
	var cmap: Dictionary = load(_SVS_PATH).get_script_constant_map()
	_assert_true(
		cmap["COLOR_BASELINE"] != cmap["COLOR_MUTATION_TINT"],
		"ADV-MAC-7 — COLOR_BASELINE and COLOR_MUTATION_TINT must be distinct"
	)


# ---------------------------------------------------------------------------
# ADV-MAC-8: duplicate() produces an independent copy
# ---------------------------------------------------------------------------

func test_adv_mac_8_duplicate_independence() -> void:
	var mesh := MeshInstance3D.new()
	var original_mat := StandardMaterial3D.new()
	original_mat.albedo_color = Color(0.4, 0.9, 0.6, 1.0)
	mesh.material_override = original_mat.duplicate()

	_assert_true(
		mesh.material_override != original_mat,
		"ADV-MAC-8a — duplicated material must be a different object"
	)
	_assert_true(
		mesh.material_override.albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-8b — duplicate starts with same albedo_color"
	)

	mesh.material_override.albedo_color = Color(1.0, 0.15, 0.0, 1.0)

	_assert_true(
		original_mat.albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-8c — writing to duplicate must not change original; got " + str(original_mat.albedo_color)
	)
	_assert_true(
		mesh.material_override.albedo_color == Color(1.0, 0.15, 0.0, 1.0),
		"ADV-MAC-8d — duplicate must reflect the write; got " + str(mesh.material_override.albedo_color)
	)
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-9: Lazy player resolution — Godot ready-order regression
# Children get _ready() before parents, so _player may be null at _ready() time.
# _process() must pick up the player on the next frame.
# ---------------------------------------------------------------------------

func test_adv_mac_9_lazy_player_resolution() -> void:
	var d := _make_wired()
	# Start with null player — simulates state right after _ready() before parent is ready
	d["svs"].set("_player", null)

	# First _process() with null player — no-op
	d["svs"].call("_process", 0.016)
	_assert_true(
		d["mat"].albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-9a — null player: no color change"
	)

	# Now inject a player with fusion active (simulates parent becoming ready)
	var player := PlayerStub.new()
	player.fusion_active = true
	d["svs"].set("_player", player)

	# Next _process() — should apply tint now
	d["svs"].call("_process", 0.016)
	var cmap: Dictionary = load(_SVS_PATH).get_script_constant_map()
	_assert_true(
		d["mat"].albedo_color == cmap["COLOR_MUTATION_TINT"],
		"ADV-MAC-9b — after player injection, tint must apply; got " + str(d["mat"].albedo_color)
	)

	player.free()
	_cleanup(d)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_active_color_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_adv_mac_1_freed_player_no_crash()
	test_adv_mac_2_mesh_not_ready_suppresses_poll()
	test_adv_mac_3_null_material_no_crash()
	test_adv_mac_4_bidirectional_sequence()
	test_adv_mac_5_player_missing_method_no_crash()
	test_adv_mac_6_hundred_calls_write_once()
	test_adv_mac_7_colors_are_distinct()
	test_adv_mac_8_duplicate_independence()
	test_adv_mac_9_lazy_player_resolution()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
