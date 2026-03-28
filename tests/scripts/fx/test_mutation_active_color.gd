#
# test_mutation_active_color.gd
#
# Primary behavioral tests for Mutation Active Color Feedback.
# Verifies SlimeVisualState color constants, _process() poll logic,
# transition behavior, idempotency, and accessor on PlayerController3D.
#
# Spec:   project_board/6_milestone_6_roguelike_run_structure/in_progress/
#         FEAT-20260328-mutation-active-color.md
#         Requirements: MAC-1, MAC-4, MAC-6, MAC-7, MAC-8, MAC-9
#
# Test IDs: MAC-1 through MAC-9
#
# Stub strategy (per CHECKPOINTS.md Spec Agent note):
#   - MeshInstance3D: real in-memory engine object (MeshInstance3D.new()), no scene tree.
#   - StandardMaterial3D: real in-memory engine object (StandardMaterial3D.new()).
#   - MutationSlotManager: real RefCounted instance loaded from script.
#   - SlimeMgrStub: minimal GDScript Object with a call-counted any_filled() for
#     idempotency and poll-count tests (MAC-9). This is a true external; stubbing it
#     to count calls is valid per mock policy.
#   - SlimeVisualState: loaded script, members wired via set() to bypass scene tree
#     _ready(). _process(delta) called directly.
#
# Spec gaps reported to Spec Agent:
#   - GAP-1: MAC-6-AC-7 states "any_filled() is called exactly once per _process()
#     invocation when state HAS changed." This is unobservable from outside without a
#     stub. The stub below (SlimeMgrStub) satisfies this by counting calls. However,
#     the spec's MAC-9-AC-5 says "no test instantiates a .tscn file" but does not
#     explicitly permit call-count stubs. Resolving conservatively: the stub is a
#     plain Object (no scene), consistent with the existing test patterns in the
#     mutation test suite.
#   - GAP-2: MAC-6-AC-8 has a subtle conflict: "any_filled() is called exactly once
#     per invocation when state has NOT changed." But the spec's _process() sequence
#     (step 3) evaluates should_tint THEN checks equality. The poll always occurs
#     before the equality check, so any_filled() IS called even when state hasn't
#     changed (step 4 returns early, but after step 3). Test MAC-9 verifies:
#     two calls to _process() with same state → any_filled() called twice (once per
#     call), albedo_color written once (first call was a transition from initial false).
#     This interpretation is conservative and consistent with MAC-6 spec step 3-4.
#

class_name MutationActiveColorTests
extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Script loaders
# ---------------------------------------------------------------------------

func _load_svs_script() -> GDScript:
	return load("res://scripts/fx/slime_visual_state.gd") as GDScript


func _load_msm_script() -> GDScript:
	return load("res://scripts/mutation/mutation_slot_manager.gd") as GDScript


func _load_player_script() -> GDScript:
	return load("res://scripts/player/player_controller_3d.gd") as GDScript


# ---------------------------------------------------------------------------
# Stub: minimal any_filled() provider with call counter.
# Used for poll-count verification (MAC-9 idempotency).
# Extends Object (not Node, not RefCounted) — pure plain object.
# ---------------------------------------------------------------------------

class SlimeMgrStub:
	extends Object

	var _return_value: bool = false
	var call_count: int = 0

	func any_filled() -> bool:
		call_count += 1
		return _return_value


# ---------------------------------------------------------------------------
# Helpers: build a minimal in-memory mesh with a duplicated material and wire
# a SlimeVisualState instance as if _ready() had run successfully.
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
	# Construct SlimeVisualState and manually set private members to the
	# post-_ready() wired state, bypassing scene tree dependency.
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
# MAC-1: COLOR_BASELINE constant has correct value
# Spec: MAC-1-AC-1
# ---------------------------------------------------------------------------

func test_mac_1_color_baseline_value() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-1", "slime_visual_state.gd not found; implement per MAC-1 spec")
		return

	if not script.get_script_constant_map().has("COLOR_BASELINE"):
		_fail("MAC-1", "COLOR_BASELINE constant not declared in SlimeVisualState")
		return

	var baseline: Color = script.get_script_constant_map()["COLOR_BASELINE"]
	var expected := Color(0.4, 0.9, 0.6, 1.0)
	_assert_true(
		baseline == expected,
		"MAC-1 — COLOR_BASELINE == Color(0.4, 0.9, 0.6, 1.0); got " + str(baseline)
	)


# ---------------------------------------------------------------------------
# MAC-2: COLOR_MUTATION_TINT constant has correct value
# Spec: MAC-1-AC-2
# ---------------------------------------------------------------------------

func test_mac_2_color_mutation_tint_value() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-2", "slime_visual_state.gd not found; implement per MAC-1 spec")
		return

	if not script.get_script_constant_map().has("COLOR_MUTATION_TINT"):
		_fail("MAC-2", "COLOR_MUTATION_TINT constant not declared in SlimeVisualState")
		return

	var tint: Color = script.get_script_constant_map()["COLOR_MUTATION_TINT"]
	var expected := Color(0.8, 0.2, 0.9, 1.0)
	_assert_true(
		tint == expected,
		"MAC-2 — COLOR_MUTATION_TINT == Color(0.8, 0.2, 0.9, 1.0); got " + str(tint)
	)


# ---------------------------------------------------------------------------
# MAC-3: get_mutation_slot_manager() on PlayerController3D returns the set object
# Spec: MAC-4-AC-3
# Note: PlayerController3D extends CharacterBody3D (a Node); we cannot construct it
# safely outside the scene tree without a crash in headless physics.
# Resolving conservatively: verify the method exists by script inspection and
# verify MutationSlotManager is loadable. Full wiring is an integration concern.
# See CHECKPOINTS.md GAP-3 below.
# Spec gap: GAP-3 — PlayerController3D.new() in headless mode initializes physics
# internals and may hang or crash (confirmed by CLAUDE.md: do not use --check-only,
# CharacterBody3D requires scene tree). Test is limited to method presence assertion.
# ---------------------------------------------------------------------------

func test_mac_3_get_mutation_slot_manager_method_exists() -> void:
	var script: GDScript = _load_player_script()
	if script == null:
		_fail("MAC-3", "player_controller_3d.gd not found")
		return

	# Inspect the script source for the method declaration without instantiating.
	var method_found: bool = false
	for m in script.get_script_method_list():
		if m["name"] == "get_mutation_slot_manager":
			method_found = true
			break

	_assert_true(
		method_found,
		"MAC-3 — PlayerController3D must declare get_mutation_slot_manager(); method not found"
	)


# ---------------------------------------------------------------------------
# MAC-4: When any_filled() = true, _process() sets albedo to COLOR_MUTATION_TINT
# Spec: MAC-6-AC-1, ticket AC-2
# ---------------------------------------------------------------------------

func test_mac_4_process_sets_tint_when_filled() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-4", "slime_visual_state.gd not found")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	var manager := MutationSlotManager.new()
	manager.fill_next_available("test_mutation_01")

	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("MAC-4", "SlimeVisualState failed to instantiate")
		return

	svs.call("_process", 0.0)

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_MUTATION_TINT"):
		_fail("MAC-4", "COLOR_MUTATION_TINT constant missing; cannot verify color")
		svs.free()
		mesh.free()
		return

	var expected_tint: Color = color_map["COLOR_MUTATION_TINT"]
	var actual: Color = mesh.material_override.albedo_color

	_assert_true(
		actual == expected_tint,
		"MAC-4 — albedo_color should be COLOR_MUTATION_TINT when slot filled; got " + str(actual)
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# MAC-5: When any_filled() = false, _process() sets albedo to COLOR_BASELINE
# Spec: MAC-6-AC-2 (via transition) + initial state; ticket AC-1
# Drive from tinted state back to baseline to confirm revert.
# ---------------------------------------------------------------------------

func test_mac_5_process_sets_baseline_when_empty() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-5", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_BASELINE") or not color_map.has("COLOR_MUTATION_TINT"):
		_fail("MAC-5", "Color constants missing; cannot verify baseline revert")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	# Start tinted so we can observe the revert.
	mesh.material_override.albedo_color = color_map["COLOR_MUTATION_TINT"]

	var manager := MutationSlotManager.new()
	# All slots empty — any_filled() returns false.

	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("MAC-5", "SlimeVisualState failed to instantiate")
		return

	# Pre-seed _current_tinted = true so the equality guard doesn't suppress the write.
	svs.set("_current_tinted", true)

	svs.call("_process", 0.0)

	var expected_baseline: Color = color_map["COLOR_BASELINE"]
	var actual: Color = mesh.material_override.albedo_color

	_assert_true(
		actual == expected_baseline,
		"MAC-5 — albedo_color should revert to COLOR_BASELINE when slots empty; got " + str(actual)
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# MAC-6: Transitioning from filled→empty reverts color to baseline
# Spec: MAC-6-AC-2, ticket AC-4
# ---------------------------------------------------------------------------

func test_mac_6_filled_to_empty_transition_reverts_to_baseline() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-6", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_BASELINE") or not color_map.has("COLOR_MUTATION_TINT"):
		_fail("MAC-6", "Color constants missing")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	var manager := MutationSlotManager.new()
	manager.fill_next_available("test_mutation_01")

	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("MAC-6", "SlimeVisualState failed to instantiate")
		return

	# First process: fills a slot → should tint.
	svs.call("_process", 0.0)
	var after_fill: Color = mesh.material_override.albedo_color

	# Clear all slots — mutation expired.
	manager.clear_all()

	# Second process: no slots filled → should revert.
	svs.call("_process", 0.0)
	var after_clear: Color = mesh.material_override.albedo_color

	_assert_true(
		after_fill == color_map["COLOR_MUTATION_TINT"],
		"MAC-6a — color should be tint after fill; got " + str(after_fill)
	)
	_assert_true(
		after_clear == color_map["COLOR_BASELINE"],
		"MAC-6b — color should revert to baseline after clear; got " + str(after_clear)
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# MAC-7: Transitioning from empty→filled applies tint
# Spec: MAC-6-AC-1, ticket AC-2
# ---------------------------------------------------------------------------

func test_mac_7_empty_to_filled_transition_applies_tint() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-7", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_MUTATION_TINT"):
		_fail("MAC-7", "COLOR_MUTATION_TINT missing")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	var manager := MutationSlotManager.new()
	# Slots start empty.

	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("MAC-7", "SlimeVisualState failed to instantiate")
		return

	# First process: no slots filled → no color write (initial state matches).
	svs.call("_process", 0.0)
	var after_empty: Color = mesh.material_override.albedo_color

	# Now fill a slot.
	manager.fill_next_available("test_mutation_01")

	# Second process: slot filled → should tint.
	svs.call("_process", 0.0)
	var after_fill: Color = mesh.material_override.albedo_color

	_assert_true(
		after_fill == color_map["COLOR_MUTATION_TINT"],
		"MAC-7 — color should be mutation tint after slot filled; got " + str(after_fill)
	)
	# Verify the color did actually change (not already tinted before).
	_assert_true(
		after_empty != color_map["COLOR_MUTATION_TINT"],
		"MAC-7b — color before fill should not be tint; got " + str(after_empty)
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# MAC-8: _current_tinted is false initially
# Spec: MAC-7-AC-1 (_current_tinted init), MAC-6 initial state
# ---------------------------------------------------------------------------

func test_mac_8_current_tinted_false_on_construction() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-8", "slime_visual_state.gd not found")
		return

	var svs: Object = script.new()
	if svs == null:
		_fail("MAC-8", "SlimeVisualState failed to instantiate")
		return

	var current_tinted = svs.get("_current_tinted")

	_assert_true(
		current_tinted != null,
		"MAC-8a — _current_tinted member must be declared (got null)"
	)

	if current_tinted != null:
		_assert_false(
			current_tinted,
			"MAC-8b — _current_tinted must be false at construction"
		)

	svs.free()


# ---------------------------------------------------------------------------
# MAC-9: Idempotency — material write skipped when state unchanged
# Spec: MAC-6-AC-3, MAC-6-AC-4, MAC-8-AC-2
# Strategy: call _process() twice with same any_filled() result.
# Verify: albedo_color is set on the first call (state change: false→true),
# and the stub's call_count increments each frame (poll always runs),
# but albedo_color is NOT re-written on the second call (same state).
# We detect "not re-written" by patching the material color between the two
# _process() calls and observing it is unchanged on the second call.
# ---------------------------------------------------------------------------

func test_mac_9_material_write_skipped_when_state_unchanged() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-9", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_MUTATION_TINT") or not color_map.has("COLOR_BASELINE"):
		_fail("MAC-9", "Color constants missing")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)

	# Use the call-counting stub to verify poll behavior.
	var stub := SlimeMgrStub.new()
	stub._return_value = true  # Slots filled.

	var svs: Object = _make_svs_ready(mesh, stub)
	if svs == null:
		_fail("MAC-9", "SlimeVisualState failed to instantiate")
		stub.free()
		mesh.free()
		return

	# First _process() call: _current_tinted is false, any_filled() returns true.
	# State changes false→true, so material IS written.
	svs.call("_process", 0.0)
	var count_after_first: int = stub.call_count
	var color_after_first: Color = mesh.material_override.albedo_color

	_assert_eq_int(
		1,
		count_after_first,
		"MAC-9a — any_filled() called exactly once on first _process()"
	)
	_assert_true(
		color_after_first == color_map["COLOR_MUTATION_TINT"],
		"MAC-9b — albedo_color set to tint on first _process() (state changed); got " + str(color_after_first)
	)

	# Mutate the color directly to a sentinel to detect if _process() writes it again.
	var sentinel := Color(0.0, 0.0, 0.0, 1.0)
	mesh.material_override.albedo_color = sentinel

	# Second _process() call: _current_tinted is now true, any_filled() still true.
	# State unchanged → no material write → sentinel should survive.
	svs.call("_process", 0.0)
	var count_after_second: int = stub.call_count
	var color_after_second: Color = mesh.material_override.albedo_color

	_assert_eq_int(
		2,
		count_after_second,
		"MAC-9c — any_filled() called once more on second _process() (poll always runs)"
	)
	_assert_true(
		color_after_second == sentinel,
		"MAC-9d — albedo_color NOT rewritten on second _process() when state unchanged; got " + str(color_after_second)
	)

	svs.free()
	stub.free()
	mesh.free()


# ---------------------------------------------------------------------------
# Bonus — AC-3 from ticket: both slots filled = same tint as one slot filled
# Spec: MAC-6-AC-9, ticket AC-3
# ---------------------------------------------------------------------------

func test_mac_bonus_two_slots_filled_same_as_one_slot() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-BONUS", "slime_visual_state.gd not found")
		return

	var color_map: Dictionary = script.get_script_constant_map()
	if not color_map.has("COLOR_MUTATION_TINT"):
		_fail("MAC-BONUS", "COLOR_MUTATION_TINT missing")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	var manager := MutationSlotManager.new()
	manager.fill_next_available("mutation_a")
	manager.fill_next_available("mutation_b")
	# Both slots filled now.

	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("MAC-BONUS", "SlimeVisualState failed to instantiate")
		mesh.free()
		return

	svs.call("_process", 0.0)

	var actual: Color = mesh.material_override.albedo_color
	_assert_true(
		actual == color_map["COLOR_MUTATION_TINT"],
		"MAC-BONUS — albedo_color must be COLOR_MUTATION_TINT when both slots filled; got " + str(actual)
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# Guard: _process() early exit when _mesh_ready is false
# Spec: MAC-6-AC-5
# ---------------------------------------------------------------------------

func test_mac_guard_mesh_not_ready_skips_process() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-GUARD-MESH", "slime_visual_state.gd not found")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)
	var manager := MutationSlotManager.new()
	manager.fill_next_available("test_mutation_01")

	# Wire normally but force _mesh_ready = false.
	var svs: Object = _make_svs_ready(mesh, manager)
	if svs == null:
		_fail("MAC-GUARD-MESH", "SlimeVisualState failed to instantiate")
		mesh.free()
		return
	svs.set("_mesh_ready", false)

	var color_before: Color = mesh.material_override.albedo_color
	svs.call("_process", 0.0)
	var color_after: Color = mesh.material_override.albedo_color

	_assert_true(
		color_after == color_before,
		"MAC-GUARD-MESH — albedo_color must not change when _mesh_ready is false"
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# Guard: _process() early exit when _mutation_slot_manager is null
# Spec: MAC-6-AC-6
# ---------------------------------------------------------------------------

func test_mac_guard_null_manager_skips_process() -> void:
	var script: GDScript = _load_svs_script()
	if script == null:
		_fail("MAC-GUARD-MGR", "slime_visual_state.gd not found")
		return

	var mat := _make_material()
	var mesh := _make_mesh(mat)

	# Wire mesh but leave manager null.
	var svs: Object = _make_svs_ready(mesh, null)
	if svs == null:
		_fail("MAC-GUARD-MGR", "SlimeVisualState failed to instantiate")
		mesh.free()
		return

	var color_before: Color = mesh.material_override.albedo_color
	svs.call("_process", 0.0)
	var color_after: Color = mesh.material_override.albedo_color

	_assert_true(
		color_after == color_before,
		"MAC-GUARD-MGR — albedo_color must not change when _mutation_slot_manager is null"
	)

	svs.free()
	mesh.free()


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_mutation_active_color.gd ---")
	_pass_count = 0
	_fail_count = 0

	# MAC-1: COLOR_BASELINE value
	test_mac_1_color_baseline_value()

	# MAC-2: COLOR_MUTATION_TINT value
	test_mac_2_color_mutation_tint_value()

	# MAC-3: get_mutation_slot_manager() method presence on PlayerController3D
	test_mac_3_get_mutation_slot_manager_method_exists()

	# MAC-4: _process() sets tint when slot filled
	test_mac_4_process_sets_tint_when_filled()

	# MAC-5: _process() sets baseline when slots empty
	test_mac_5_process_sets_baseline_when_empty()

	# MAC-6: filled→empty transition reverts color
	test_mac_6_filled_to_empty_transition_reverts_to_baseline()

	# MAC-7: empty→filled transition applies tint
	test_mac_7_empty_to_filled_transition_applies_tint()

	# MAC-8: _current_tinted is false at construction
	test_mac_8_current_tinted_false_on_construction()

	# MAC-9: material write skipped when state unchanged (idempotency)
	test_mac_9_material_write_skipped_when_state_unchanged()

	# Bonus: two slots filled = same color as one slot filled (ticket AC-3)
	test_mac_bonus_two_slots_filled_same_as_one_slot()

	# Guards: early-exit cases
	test_mac_guard_mesh_not_ready_skips_process()
	test_mac_guard_null_manager_skips_process()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
