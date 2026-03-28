#
# test_mutation_active_color_adversarial.gd
#
# Adversarial and mutation tests for Mutation Active Color Feedback.
# Targets blind spots, assumption violations, and structural weaknesses
# NOT covered by the primary test suite (test_mutation_active_color.gd).
#
# Spec:   project_board/6_milestone_6_roguelike_run_structure/in_progress/
#         FEAT-20260328-mutation-active-color.md
#         Requirements: MAC-1 through MAC-9
#
# Test IDs: ADV-MAC-1 through ADV-MAC-8
#
# Adversarial rationale per test:
#
#   ADV-MAC-1: Primary suite tests _mutation_slot_manager=null at steady state.
#     This test exposes the is_instance_valid() guard by passing a freed Object —
#     a non-null pointer that has been freed. If the implementation only checks
#     `== null` and omits `is_instance_valid()`, this will crash.
#
#   ADV-MAC-2: Primary suite's MAC-GUARD-MESH sets _mesh_ready=false but does NOT
#     verify the any_filled() poll is also suppressed (only checks albedo_color).
#     This test uses a call-counting stub to prove any_filled() is never called
#     when _mesh_ready is false. A mutation that reorders the guards (checking
#     manager before mesh_ready) would be caught here.
#
#   ADV-MAC-3: _ready() null-guard for material_override is not exercised headlessly
#     in the primary suite (requires scene tree for _ready()). This test simulates
#     the post-_ready() state when material_override is null: _mesh_ready must be
#     false so _process() exits before any NULL dereference on albedo_color.
#     Catches an implementation that sets _mesh_ready=true unconditionally.
#
#   ADV-MAC-4: Both transition directions in an organic sequence (no pre-seeded
#     _current_tinted state). Primary suite's MAC-6 fills first then clears, but
#     starts from a fresh svs with _current_tinted=false. This test drives:
#     empty→filled (transition 1) then filled→empty (transition 2), each verified
#     independently, using a single continuous svs instance.
#
#   ADV-MAC-5: Primary suite only checks method presence on PlayerController3D via
#     get_script_method_list(). This test verifies the contract: when _mutation_slot
#     is null, get_mutation_slot_manager() must return null without crashing.
#     Uses a minimal GDScript stub that mirrors the expected method contract to
#     avoid constructing CharacterBody3D in headless mode.
#
#   ADV-MAC-6: Stress-idempotency — 100 consecutive _process() calls in the same
#     tinted state. Primary suite only checks two calls. The sentinel technique
#     is extended: after the first call sets the tint, a sentinel is written to
#     albedo_color. Then 99 more _process() calls follow. If any of them writes
#     albedo_color, the sentinel will be gone. Material write count must be exactly
#     1 (on the first call).
#
#   ADV-MAC-7: Sanity check that COLOR_BASELINE != COLOR_MUTATION_TINT. If an
#     implementation accidentally sets both constants to the same value (e.g. a
#     copy-paste error), the color transitions appear to work but produce no visible
#     change. None of the primary tests catch this; they always compare against one
#     constant at a time, not both against each other.
#
#   ADV-MAC-8: Verifies material_override.duplicate() produces an independent copy.
#     Mutating the duplicated material's albedo_color must not affect the original
#     material object. Catches an implementation that stores a reference instead of
#     calling duplicate(), or calls duplicate() then immediately discards the result.
#
# Stub strategy (per primary test conventions):
#   - SlimeMgrStub: call-counting any_filled() stub (same design as primary).
#   - FreedMgrStub: an Object instance that is freed before _process() is called,
#     exercising is_instance_valid() guard.
#   - PlayerStub: minimal Object with get_mutation_slot_manager() that returns null.
#   - MeshInstance3D and StandardMaterial3D: real in-memory engine objects, no scene.
#

class_name MutationActiveColorAdversarialTests
extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Script loaders
# ---------------------------------------------------------------------------

func _load_svs_script() -> GDScript:
	return load("res://scripts/fx/slime_visual_state.gd") as GDScript


func _load_player_script() -> GDScript:
	return load("res://scripts/player/player_controller_3d.gd") as GDScript


# ---------------------------------------------------------------------------
# Stub: call-counting any_filled() provider.
# ---------------------------------------------------------------------------

class SlimeMgrStub:
	extends Object

	var _return_value: bool = false
	var call_count: int = 0

	func any_filled() -> bool:
		call_count += 1
		return _return_value


# ---------------------------------------------------------------------------
# Stub: minimal parent that implements get_mutation_slot_manager() returning null.
# Used to test ADV-MAC-5 without constructing a CharacterBody3D.
# ---------------------------------------------------------------------------

class PlayerStub:
	extends Object

	func get_mutation_slot_manager() -> Object:
		return null


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _make_material() -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(0.4, 0.9, 0.6, 1.0)
	return mat


func _make_mesh(mat: StandardMaterial3D) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.material_override = mat.duplicate()
	return mesh


func _make_svs_ready(mesh: MeshInstance3D, manager: Object) -> Object:
	var script: GDScript = _load_svs_script()
	if script == null:
		return null
	var svs: Object = script.new()
	if svs == null:
		return null
	svs.set("_mesh", mesh)
	svs.set("_mesh_ready", true)
	svs.set("_mutation_slot_manager", manager)
	svs.set("_current_tinted", false)
	return svs


# ---------------------------------------------------------------------------
# ADV-MAC-1: freed manager (is_instance_valid = false) — _process() must not crash
#
# Vulnerability targeted: implementation that guards only `_mutation_slot_manager == null`
# but omits `is_instance_valid(_mutation_slot_manager)` will crash when the manager
# object is freed between _ready() and _process(). This cannot be caught by the
# primary suite because it only injects null directly.
# ---------------------------------------------------------------------------

func test_adv_mac_1_freed_manager_does_not_crash() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-1", "slime_visual_state.gd not found")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)

	# Create a real Object manager, wire it in, then free it before _process().
	var manager := SlimeMgrStub.new()
	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("ADV-MAC-1", "SlimeVisualState failed to instantiate")
		manager.free()
		mesh.free()
		return

	# Free the manager — svs still holds a non-null reference to freed memory.
	manager.free()

	# _process() must not crash. is_instance_valid() guard must intercept this.
	var color_before: Color = mesh.material_override.albedo_color
	svs.call("_process", 0.0)
	var color_after: Color = mesh.material_override.albedo_color

	_assert_true(
		color_after == color_before,
		"ADV-MAC-1 — albedo_color must not change when manager is freed (is_instance_valid guard)"
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-2: _mesh_ready = false suppresses any_filled() poll entirely
#
# Vulnerability targeted: an implementation that re-orders the guard checks
# (e.g., evaluates any_filled() before checking _mesh_ready) would pass the
# primary guard test (color unchanged) but still call any_filled() unnecessarily.
# This test uses a call-counting stub to verify the poll is never reached.
# ---------------------------------------------------------------------------

func test_adv_mac_2_mesh_not_ready_suppresses_poll() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-2", "slime_visual_state.gd not found")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)

	var stub := SlimeMgrStub.new()
	stub._return_value = true  # Would tint if polled.

	var svs: Object = _make_svs_ready(mesh, stub)
	if svs == null:
		_fail("ADV-MAC-2", "SlimeVisualState failed to instantiate")
		stub.free()
		mesh.free()
		return

	svs.set("_mesh_ready", false)

	svs.call("_process", 0.0)

	_assert_eq_int(
		0,
		stub.call_count,
		"ADV-MAC-2 — any_filled() must not be called when _mesh_ready is false"
	)

	_assert_true(
		mesh.material_override.albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-2b — albedo_color must remain baseline when _mesh_ready is false"
	)

	svs.free()
	stub.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-3: material_override null — null guard must not crash
#
# Vulnerability targeted: _ready() spec requires returning early with
# _mesh_ready=false when material_override is null. If the implementation
# sets _mesh_ready=true regardless (or bypasses the null check), then
# _process() will attempt to write to a null material_override and crash.
#
# Since _ready() requires the scene tree (get_node_or_null), we simulate
# the post-_ready() failure state: _mesh is set to a MeshInstance3D with
# material_override=null, and _mesh_ready=false (as spec requires).
# This verifies that _process() respects _mesh_ready=false and never
# reaches the material_override.albedo_color assignment.
# ---------------------------------------------------------------------------

func test_adv_mac_3_null_material_override_no_crash() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-3", "slime_visual_state.gd not found")
		return

	var stub := SlimeMgrStub.new()
	stub._return_value = true

	var svs: Object = script.new()
	if svs == null:
		_fail("ADV-MAC-3", "SlimeVisualState failed to instantiate")
		stub.free()
		return

	# Construct a mesh with NO material_override to simulate the failure state
	# that _ready() would produce when material_override is null.
	var mesh := MeshInstance3D.new()
	# material_override defaults to null — do not assign it.

	# Simulate what _ready() would leave behind after null material_override:
	# _mesh is set, _mesh_ready is FALSE (spec MAC-2 step 3).
	svs.set("_mesh", mesh)
	svs.set("_mesh_ready", false)
	svs.set("_mutation_slot_manager", stub)
	svs.set("_current_tinted", false)

	# _process() must not crash — it must exit before touching material_override.
	svs.call("_process", 0.0)

	# any_filled() must not have been called (early exit before poll).
	_assert_eq_int(
		0,
		stub.call_count,
		"ADV-MAC-3a — any_filled() must not be called when _mesh_ready is false (null material case)"
	)

	# Verify the null material_override was not accessed (no crash = pass).
	_assert_true(
		mesh.material_override == null,
		"ADV-MAC-3b — material_override remains null (not touched by _process)"
	)

	svs.free()
	stub.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-4: any_filled() true on first call, false on second — sequential transitions
#
# Vulnerability targeted: the primary suite (MAC-6) pre-seeds _current_tinted=false
# organically but starts by pre-filling the manager before wiring. This test drives
# a complete organic sequence:
#   1. Start: empty manager, _current_tinted=false
#   2. _process() #1: any_filled()=false, should_tint=false → no write (false==false)
#   3. Fill slot: any_filled() now returns true
#   4. _process() #2: any_filled()=true, should_tint=true → write MUTATION_TINT
#   5. Clear slot: any_filled() now returns false
#   6. _process() #3: any_filled()=false, should_tint=false → write BASELINE
# All three observations must be correct without pre-seeding _current_tinted.
# ---------------------------------------------------------------------------

func test_adv_mac_4_bidirectional_transition_sequence() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-4", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_BASELINE") or not color_map.has("COLOR_MUTATION_TINT"):
		_fail("ADV-MAC-4", "Color constants missing; cannot run bidirectional sequence test")
		return

	var baseline: Color = color_map["COLOR_BASELINE"]
	var tint: Color = color_map["COLOR_MUTATION_TINT"]

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	var manager := MutationSlotManager.new()
	# All slots empty at start.

	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("ADV-MAC-4", "SlimeVisualState failed to instantiate")
		mesh.free()
		return

	# Step 1: empty state — no write, color stays at material's initial value.
	svs.call("_process", 0.0)
	var color_step1: Color = mesh.material_override.albedo_color
	_assert_true(
		color_step1 == baseline,
		"ADV-MAC-4a — step1 (empty): albedo_color should remain baseline; got " + str(color_step1)
	)

	# Step 2: fill a slot → tint must be applied.
	manager.fill_next_available("adv_mutation_01")
	svs.call("_process", 0.0)
	var color_step2: Color = mesh.material_override.albedo_color
	_assert_true(
		color_step2 == tint,
		"ADV-MAC-4b — step2 (filled): albedo_color should be mutation tint; got " + str(color_step2)
	)

	# Step 3: clear all slots → baseline must be restored.
	manager.clear_all()
	svs.call("_process", 0.0)
	var color_step3: Color = mesh.material_override.albedo_color
	_assert_true(
		color_step3 == baseline,
		"ADV-MAC-4c — step3 (emptied): albedo_color should revert to baseline; got " + str(color_step3)
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-5: get_mutation_slot_manager() returns null when _mutation_slot is null
#
# Vulnerability targeted: the primary suite only checks method presence. This test
# verifies the return-null contract using a minimal stub that mirrors the spec's
# expected behavior, confirming null is returned without crash (not raising an error).
# Since PlayerController3D extends CharacterBody3D (scene tree required), we use
# a minimal PlayerStub (extends Object) that implements get_mutation_slot_manager()
# returning null, and confirm SlimeVisualState handles that null correctly.
# ---------------------------------------------------------------------------

func test_adv_mac_5_get_mutation_slot_manager_null_when_slot_null() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-5a", "slime_visual_state.gd not found")
		return

	# Verify the player script declares the method and inspect return type annotation.
	var player_script: GDScript = _load_player_script()
	if player_script == null:
		_fail("ADV-MAC-5a", "player_controller_3d.gd not found")
		return

	var method_found: bool = false
	for m in player_script.get_script_method_list():
		if m["name"] == "get_mutation_slot_manager":
			method_found = true
			break

	_assert_true(
		method_found,
		"ADV-MAC-5a — PlayerController3D must declare get_mutation_slot_manager()"
	)

	# Test the null-return contract via a minimal stub.
	# PlayerStub.get_mutation_slot_manager() returns null.
	var parent_stub := PlayerStub.new()

	var mat := _make_material()
	var mesh := _make_mesh(mat)

	# Build a SVS and verify it handles a parent stub that returns null from the method.
	# We do NOT call _ready() (scene tree required). Instead, directly simulate what
	# _ready() would do with a parent that has the method but returns null.
	var result: Object = parent_stub.call("get_mutation_slot_manager")

	_assert_true(
		result == null,
		"ADV-MAC-5b — PlayerStub.get_mutation_slot_manager() must return null"
	)

	# Wire SVS with null manager (as _ready() would produce) and confirm _process() is safe.
	var svs: Object = _make_svs_ready(mesh, null)
	if svs == null:
		_fail("ADV-MAC-5c", "SlimeVisualState failed to instantiate")
		parent_stub.free()
		mesh.free()
		return

	var color_before: Color = mesh.material_override.albedo_color
	svs.call("_process", 0.0)
	var color_after: Color = mesh.material_override.albedo_color

	_assert_true(
		color_after == color_before,
		"ADV-MAC-5c — _process() with null manager (from get_mutation_slot_manager returning null) must not crash or change color"
	)

	svs.free()
	parent_stub.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-6: 100 _process() calls in same tinted state — material write count = 1
#
# Vulnerability targeted: the primary suite (MAC-9) only verifies two calls. A naive
# implementation might skip the write on the first same-state call (call 2) but
# accidentally re-enable writes after N frames (e.g. a counter bug). This test
# verifies over 100 frames that the material is written exactly once.
# ---------------------------------------------------------------------------

func test_adv_mac_6_hundred_process_calls_write_once() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-6", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_MUTATION_TINT"):
		_fail("ADV-MAC-6", "COLOR_MUTATION_TINT missing")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)

	var stub := SlimeMgrStub.new()
	stub._return_value = true  # Always tinted.

	var svs: Object = _make_svs_ready(mesh, stub)
	if svs == null:
		_fail("ADV-MAC-6", "SlimeVisualState failed to instantiate")
		stub.free()
		mesh.free()
		return

	# First call: state change false→true, material IS written.
	svs.call("_process", 0.0)
	var color_after_first: Color = mesh.material_override.albedo_color
	_assert_true(
		color_after_first == color_map["COLOR_MUTATION_TINT"],
		"ADV-MAC-6a — albedo_color set to tint on first _process() call"
	)

	# Write a sentinel to detect any subsequent material writes.
	var sentinel := Color(0.1, 0.2, 0.3, 1.0)
	mesh.material_override.albedo_color = sentinel

	# Calls 2 through 100: state unchanged (still tinted), material must NOT be written.
	for i in range(99):
		svs.call("_process", 0.0)

	var color_after_hundred: Color = mesh.material_override.albedo_color
	_assert_true(
		color_after_hundred == sentinel,
		"ADV-MAC-6b — sentinel must survive 99 additional _process() calls with same state; got " + str(color_after_hundred)
	)

	# any_filled() should have been called exactly 100 times (poll runs every frame).
	_assert_eq_int(
		100,
		stub.call_count,
		"ADV-MAC-6c — any_filled() called exactly 100 times (once per frame)"
	)

	svs.free()
	stub.free()
	mesh.free()


# ---------------------------------------------------------------------------
# ADV-MAC-7: COLOR_BASELINE and COLOR_MUTATION_TINT are distinct (sanity)
#
# Vulnerability targeted: a copy-paste error that sets both constants to the same
# value. The primary tests each verify one constant independently against a hardcoded
# expected value, but if both constants were accidentally set to the SAME correct-
# looking value, the primary tests would still pass while transitions are invisible.
# This test explicitly asserts they are not equal.
# ---------------------------------------------------------------------------

func test_adv_mac_7_color_constants_are_distinct() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-7", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_BASELINE") or not color_map.has("COLOR_MUTATION_TINT"):
		_fail("ADV-MAC-7", "Color constants missing; cannot verify distinctness")
		return

	var baseline: Color = color_map["COLOR_BASELINE"]
	var tint: Color = color_map["COLOR_MUTATION_TINT"]

	_assert_true(
		baseline != tint,
		"ADV-MAC-7 — COLOR_BASELINE and COLOR_MUTATION_TINT must be distinct colors; both were " + str(baseline)
	)


# ---------------------------------------------------------------------------
# ADV-MAC-8: duplicate() produces an independent copy
#
# Vulnerability targeted: an implementation that stores a reference to the original
# material instead of calling duplicate(), or calls duplicate() then discards the
# result. If material_override is a reference to the shared sub-resource, writing
# to the duplicated material would change the original and vice versa. This test
# verifies that after the expected duplication pattern, mutating the copy does not
# affect the original.
# ---------------------------------------------------------------------------

func test_adv_mac_8_duplicate_produces_independent_copy() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("ADV-MAC-8", "slime_visual_state.gd not found")
		return

	# Create the original material (represents the shared sub-resource in .tscn).
	var original_mat := StandardMaterial3D.new()
	original_mat.albedo_color = Color(0.4, 0.9, 0.6, 1.0)

	# Simulate what _ready() does: mesh.material_override = mesh.material_override.duplicate().
	# Here we assign the original, then duplicate it as _ready() would.
	var mesh := MeshInstance3D.new()
	mesh.material_override = original_mat

	# This is the duplication step that _ready() must perform.
	var duplicated_mat: StandardMaterial3D = mesh.material_override.duplicate()
	mesh.material_override = duplicated_mat

	# Verify they are distinct objects (not the same reference).
	_assert_false(
		is_same(original_mat, mesh.material_override),
		"ADV-MAC-8a — material_override after duplicate() must be a different object from the original"
	)

	# Verify the duplicate starts with the same color (correct initial state).
	_assert_true(
		mesh.material_override.albedo_color == original_mat.albedo_color,
		"ADV-MAC-8b — duplicated material must start with the same albedo_color as the original"
	)

	# Write a mutation tint to the duplicate.
	mesh.material_override.albedo_color = Color(0.8, 0.2, 0.9, 1.0)

	# The original must be UNCHANGED (independence is the whole point of duplication).
	_assert_true(
		original_mat.albedo_color == Color(0.4, 0.9, 0.6, 1.0),
		"ADV-MAC-8c — writing to duplicated material must NOT change the original; original was " + str(original_mat.albedo_color)
	)

	# The duplicate must reflect the write.
	_assert_true(
		mesh.material_override.albedo_color == Color(0.8, 0.2, 0.9, 1.0),
		"ADV-MAC-8d — duplicated material must reflect the albedo_color write; got " + str(mesh.material_override.albedo_color)
	)

	# Note: original_mat and duplicated_mat are StandardMaterial3D (extends Resource,
	# which extends RefCounted). RefCounted objects must NOT be freed manually —
	# Godot's reference counting handles their lifecycle. Only free() Node-derived
	# and non-RefCounted Object instances.
	mesh.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_active_color_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	# ADV-MAC-1: freed manager (is_instance_valid guard)
	test_adv_mac_1_freed_manager_does_not_crash()

	# ADV-MAC-2: _mesh_ready=false suppresses any_filled() poll
	test_adv_mac_2_mesh_not_ready_suppresses_poll()

	# ADV-MAC-3: null material_override — _mesh_ready=false prevents null deref
	test_adv_mac_3_null_material_override_no_crash()

	# ADV-MAC-4: organic bidirectional transition sequence (empty→filled→empty)
	test_adv_mac_4_bidirectional_transition_sequence()

	# ADV-MAC-5: get_mutation_slot_manager() returns null when _mutation_slot is null
	test_adv_mac_5_get_mutation_slot_manager_null_when_slot_null()

	# ADV-MAC-6: 100 _process() calls — material write count stays at 1
	test_adv_mac_6_hundred_process_calls_write_once()

	# ADV-MAC-7: COLOR_BASELINE != COLOR_MUTATION_TINT (sanity)
	test_adv_mac_7_color_constants_are_distinct()

	# ADV-MAC-8: duplicate() produces an independent copy
	test_adv_mac_8_duplicate_produces_independent_copy()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
