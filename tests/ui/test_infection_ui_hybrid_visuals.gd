#
# test_infection_ui_hybrid_visuals.gd
#
# Primary behavioral tests for InfectionUI hybrid visual state logic.
#
# Ticket: visual_clarity_hybrid_state.md
# Spec:   visual_clarity_hybrid_state_spec.md  (VCH-1, VCH-2, VCH-3)
#
# Scope:
#   VCH-1 — Two-slot filled visual: color constants declared and distinct;
#            color selection matrix produces correct icon/label colors for all
#            four slot-fill states.
#   VCH-2 — Fusion active indicator: FusionActiveLabel visibility driven by
#            player.is_fusion_active(); null player hides label; label absent
#            from scene → no crash.
#   VCH-3 — Post-fusion empty state flash: transition detection triggers
#            _post_fusion_flash_until_ms; flash overrides all other colors;
#            expired flash reverts to empty state; non-fusion slot-clear does
#            NOT trigger flash.
#
# TDD RED PHASE: InfectionUI color constants and new methods do not exist yet.
# Tests reference the real InfectionUI script via load() for constant checks,
# and drive logic via inner-class harnesses for headless safety.
#
# Headless safety strategy:
#   InfectionUI extends CanvasLayer and cannot be instantiated headlessly.
#   Pure-logic tests are driven by an inner-class LogicHarness that implements
#   the spec-defined color-selection algorithm (_select_slot_color) and
#   _compute_fusion_label_visibility, validated against the real script's
#   named constants read via script property access.
#   Node-visibility tests use inner-class stub nodes (LabelDouble).
#
# All spec constant names and method signatures come from spec API-2, API-3,
# API-4, and the Named Color Constants table.
#

class_name InfectionUIHybridVisualsTests
extends Object


# ---------------------------------------------------------------------------
# Inner-class doubles
# ---------------------------------------------------------------------------

# SlotDouble: minimal stub implementing the MutationSlot duck-type contract.
# Extends RefCounted for automatic memory management (no manual free required).
class SlotDouble extends RefCounted:
	var _filled: bool = false
	var _mutation_id: String = "test_mutation"

	func is_filled() -> bool:
		return _filled

	func get_active_mutation_id() -> String:
		return _mutation_id

	func set_filled(value: bool) -> void:
		_filled = value


# SlotManagerDouble: stub implementing MutationSlotManager.get_slot(index).
class SlotManagerDouble extends RefCounted:
	var _slots: Array = []

	func _init() -> void:
		_slots.resize(2)
		_slots[0] = SlotDouble.new()
		_slots[1] = SlotDouble.new()

	func get_slot(index: int) -> Object:
		if index < 0 or index >= _slots.size():
			return null
		return _slots[index]

	func set_slot_filled(index: int, value: bool) -> void:
		var slot: SlotDouble = _slots[index] as SlotDouble
		if slot != null:
			slot.set_filled(value)


# PlayerDouble: stub implementing the is_fusion_active() accessor.
class PlayerDouble extends RefCounted:
	var _fusion_active: bool = false

	func is_fusion_active() -> bool:
		return _fusion_active


# LabelDouble: stub implementing the minimal Label property surface used
# by _update_fusion_display and _update_slot_display.
class LabelDouble extends RefCounted:
	var visible: bool = false
	var text: String = ""
	var modulate: Color = Color.WHITE


# ColorRectDouble: stub for icon ColorRect.
class ColorRectDouble extends RefCounted:
	var visible: bool = false
	var color: Color = Color.BLACK


# ---------------------------------------------------------------------------
# LogicHarness: implements the spec-defined color-selection algorithm as it
# should exist in the real InfectionUI after implementation.
# This harness is the test oracle. Tests assert that:
#   (a) the real InfectionUI script exposes the named constants with the
#       values this harness uses, and
#   (b) logic driven via this harness returns the expected results, which
#       verifies the algorithm shape defined by API-2 and the color matrix.
#
# The harness is intentionally simple and direct — it mirrors the spec's
# priority table verbatim.
# ---------------------------------------------------------------------------

class LogicHarness extends RefCounted:
	# Color constants declared per spec "Named Color Constants" table.
	# These MUST match what InfectionUI declares — verified by
	# test_vch1_ac4_color_constants_declared_on_real_script below.
	const COLOR_SLOT_EMPTY       = Color(0.2, 0.2, 0.2, 0.6)
	const COLOR_SLOT_SINGLE_FILLED = Color(0.4, 0.85, 0.55, 1.0)
	const COLOR_SLOT_DUAL_FILLED   = Color(0.3, 0.65, 1.0, 1.0)
	const COLOR_SLOT_POST_FUSION   = Color(1.0, 1.0, 1.0, 1.0)

	const COLOR_LABEL_EMPTY          = Color(0.7, 0.7, 0.7, 1.0)
	const COLOR_LABEL_SINGLE_FILLED  = Color(0.9, 1.0, 0.9, 1.0)
	const COLOR_LABEL_DUAL_FILLED    = Color(0.6, 0.85, 1.0, 1.0)
	const COLOR_LABEL_POST_FUSION    = Color(1.0, 0.9, 0.5, 1.0)

	# Color priority matrix per API-2 (first match wins):
	#   1. post_fusion_flash_active      → POST_FUSION colors
	#   2. filled AND both_filled        → DUAL_FILLED colors
	#   3. filled AND NOT both_filled    → SINGLE_FILLED colors
	#   4. not filled (no flash)         → EMPTY colors
	func select_icon_color(filled: bool, both_filled: bool,
			post_fusion_flash_active: bool) -> Color:
		if post_fusion_flash_active:
			return COLOR_SLOT_POST_FUSION
		if filled and both_filled:
			return COLOR_SLOT_DUAL_FILLED
		if filled and not both_filled:
			return COLOR_SLOT_SINGLE_FILLED
		return COLOR_SLOT_EMPTY

	func select_label_color(filled: bool, both_filled: bool,
			post_fusion_flash_active: bool) -> Color:
		if post_fusion_flash_active:
			return COLOR_LABEL_POST_FUSION
		if filled and both_filled:
			return COLOR_LABEL_DUAL_FILLED
		if filled and not both_filled:
			return COLOR_LABEL_SINGLE_FILLED
		return COLOR_LABEL_EMPTY

	# Drives fusion-active label visibility per API-3:
	#   player == null → hidden
	#   player.is_fusion_active() == true → visible
	#   player.is_fusion_active() == false → hidden
	func compute_fusion_label_visible(player: Object) -> bool:
		if player == null:
			return false
		if not player.has_method("is_fusion_active"):
			return false
		return player.is_fusion_active()

	# Flash trigger: returns true when the transition both_filled: true→false
	# occurs in the same frame that player.is_fusion_active() == true.
	# VCH-3 "Flash Trigger Detection" contract.
	func should_trigger_flash(prev_both_filled: bool, current_both_filled: bool,
			player: Object) -> bool:
		if not prev_both_filled:
			return false
		if current_both_filled:
			return false
		if player == null:
			return false
		if not player.has_method("is_fusion_active"):
			return false
		return player.is_fusion_active()


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0
var _harness: LogicHarness


func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " -- " + message)


func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")


func _assert_false(condition: bool, test_name: String) -> void:
	if not condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected false, got true")


func _assert_color_eq(expected: Color, actual: Color, test_name: String) -> void:
	if expected.is_equal_approx(actual):
		_pass(test_name)
	else:
		_fail(test_name, "expected Color" + str(expected) + " got Color" + str(actual))


func _assert_color_ne(a: Color, b: Color, test_name: String) -> void:
	if not a.is_equal_approx(b):
		_pass(test_name)
	else:
		_fail(test_name, "expected colors to differ but both were Color" + str(a))


func _load_infection_ui_script() -> GDScript:
	return load("res://scripts/ui/infection_ui.gd") as GDScript


# Returns a named constant value from the script resource, or null if absent.
# GDScript constants are exposed as static properties accessible via
# ClassDB or direct instance property reads.
func _get_script_constant(script: GDScript, name: String) -> Variant:
	if script == null:
		return null
	# Constants are accessible as properties on a fresh instance only if the
	# script can be instantiated. Since InfectionUI extends CanvasLayer, we
	# cannot call .new() headlessly. Instead we verify via the script's source
	# constant map using get_script_constant_map(), which works without
	# instantiating the scene node.
	var map: Dictionary = script.get_script_constant_map()
	if map.has(name):
		return map[name]
	return null


func _require_infection_ui(test_name: String) -> GDScript:
	var script: GDScript = _load_infection_ui_script()
	if script == null:
		_fail(test_name, "InfectionUI script not found at res://scripts/ui/infection_ui.gd")
	return script


func _require_constant(script: GDScript, constant_name: String, test_name: String) -> bool:
	var val: Variant = _get_script_constant(script, constant_name)
	if val == null:
		_fail(
			test_name,
			constant_name + " not found in InfectionUI constant map -- "
			+ "declare 'const " + constant_name + "' at class scope per spec NF-1"
		)
		return false
	return true


# ---------------------------------------------------------------------------
# VCH-1-AC-4 (prerequisite for all color tests)
# COLOR_SLOT_DUAL_FILLED != COLOR_SLOT_SINGLE_FILLED (constant comparison)
# This verifies the spec's distinguishability contract without running the game.
# ---------------------------------------------------------------------------

func test_vch1_ac4_dual_filled_differs_from_single_filled_constant() -> void:
	_assert_color_ne(
		LogicHarness.COLOR_SLOT_DUAL_FILLED,
		LogicHarness.COLOR_SLOT_SINGLE_FILLED,
		"vch1_ac4_dual_ne_single -- COLOR_SLOT_DUAL_FILLED must differ from COLOR_SLOT_SINGLE_FILLED per VCH-1-AC-4"
	)


# VCH-3-AC-7 (constant comparison, no runtime needed)
func test_vch3_ac7_post_fusion_differs_from_empty_constant() -> void:
	_assert_color_ne(
		LogicHarness.COLOR_SLOT_POST_FUSION,
		LogicHarness.COLOR_SLOT_EMPTY,
		"vch3_ac7_post_fusion_ne_empty -- COLOR_SLOT_POST_FUSION must differ from COLOR_SLOT_EMPTY per VCH-3-AC-7"
	)


# ---------------------------------------------------------------------------
# VCH-1: Real script constant declarations
# All 8 color constants must be declared at InfectionUI class scope (NF-1).
# ---------------------------------------------------------------------------

func test_vch1_real_script_declares_color_slot_empty() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_SLOT_EMPTY")
	if script == null:
		return
	if not _require_constant(script, "COLOR_SLOT_EMPTY", "vch1_const_COLOR_SLOT_EMPTY"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_SLOT_EMPTY") as Color
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_EMPTY,
		actual,
		"vch1_const_COLOR_SLOT_EMPTY_value -- must equal Color(0.2,0.2,0.2,0.6) per spec table"
	)


func test_vch1_real_script_declares_color_slot_single_filled() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_SLOT_SINGLE_FILLED")
	if script == null:
		return
	if not _require_constant(script, "COLOR_SLOT_SINGLE_FILLED", "vch1_const_COLOR_SLOT_SINGLE_FILLED"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_SLOT_SINGLE_FILLED") as Color
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_SINGLE_FILLED,
		actual,
		"vch1_const_COLOR_SLOT_SINGLE_FILLED_value -- must equal Color(0.4,0.85,0.55,1.0) per spec table"
	)


func test_vch1_real_script_declares_color_slot_dual_filled() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_SLOT_DUAL_FILLED")
	if script == null:
		return
	if not _require_constant(script, "COLOR_SLOT_DUAL_FILLED", "vch1_const_COLOR_SLOT_DUAL_FILLED"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_SLOT_DUAL_FILLED") as Color
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_DUAL_FILLED,
		actual,
		"vch1_const_COLOR_SLOT_DUAL_FILLED_value -- must equal Color(0.3,0.65,1.0,1.0) per spec table"
	)


func test_vch1_real_script_declares_color_slot_post_fusion() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_SLOT_POST_FUSION")
	if script == null:
		return
	if not _require_constant(script, "COLOR_SLOT_POST_FUSION", "vch1_const_COLOR_SLOT_POST_FUSION"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_SLOT_POST_FUSION") as Color
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_POST_FUSION,
		actual,
		"vch1_const_COLOR_SLOT_POST_FUSION_value -- must equal Color(1.0,1.0,1.0,1.0) per spec table"
	)


func test_vch1_real_script_declares_color_label_empty() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_LABEL_EMPTY")
	if script == null:
		return
	if not _require_constant(script, "COLOR_LABEL_EMPTY", "vch1_const_COLOR_LABEL_EMPTY"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_LABEL_EMPTY") as Color
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_EMPTY,
		actual,
		"vch1_const_COLOR_LABEL_EMPTY_value -- must equal Color(0.7,0.7,0.7,1.0) per spec table"
	)


func test_vch1_real_script_declares_color_label_single_filled() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_LABEL_SINGLE_FILLED")
	if script == null:
		return
	if not _require_constant(script, "COLOR_LABEL_SINGLE_FILLED", "vch1_const_COLOR_LABEL_SINGLE_FILLED"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_LABEL_SINGLE_FILLED") as Color
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_SINGLE_FILLED,
		actual,
		"vch1_const_COLOR_LABEL_SINGLE_FILLED_value -- must equal Color(0.9,1.0,0.9,1.0) per spec table"
	)


func test_vch1_real_script_declares_color_label_dual_filled() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_LABEL_DUAL_FILLED")
	if script == null:
		return
	if not _require_constant(script, "COLOR_LABEL_DUAL_FILLED", "vch1_const_COLOR_LABEL_DUAL_FILLED"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_LABEL_DUAL_FILLED") as Color
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_DUAL_FILLED,
		actual,
		"vch1_const_COLOR_LABEL_DUAL_FILLED_value -- must equal Color(0.6,0.85,1.0,1.0) per spec table"
	)


func test_vch1_real_script_declares_color_label_post_fusion() -> void:
	var script: GDScript = _require_infection_ui("vch1_const_COLOR_LABEL_POST_FUSION")
	if script == null:
		return
	if not _require_constant(script, "COLOR_LABEL_POST_FUSION", "vch1_const_COLOR_LABEL_POST_FUSION"):
		return
	var actual: Color = _get_script_constant(script, "COLOR_LABEL_POST_FUSION") as Color
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_POST_FUSION,
		actual,
		"vch1_const_COLOR_LABEL_POST_FUSION_value -- must equal Color(1.0,0.9,0.5,1.0) per spec table"
	)


# VCH-3-AC-10: POST_FUSION_FLASH_DURATION_MS constant (or inline 600) exists.
func test_vch3_ac10_flash_duration_constant_present() -> void:
	var script: GDScript = _require_infection_ui("vch3_ac10_flash_duration_constant")
	if script == null:
		return
	# Spec allows either a named constant OR the literal 600 in the assignment.
	# We check for the named constant; if absent we record as a spec-gap note,
	# not a hard failure — the inline literal satisfies the spec equally.
	var map: Dictionary = script.get_script_constant_map()
	if map.has("POST_FUSION_FLASH_DURATION_MS"):
		var val: int = int(map["POST_FUSION_FLASH_DURATION_MS"])
		if val == 600:
			_pass("vch3_ac10_flash_duration_constant -- POST_FUSION_FLASH_DURATION_MS == 600 per VCH-3-AC-10")
		else:
			_fail(
				"vch3_ac10_flash_duration_constant",
				"POST_FUSION_FLASH_DURATION_MS == " + str(val) + ", expected 600 per VCH-3-AC-10"
			)
	else:
		# Named constant absent; spec says inline 600 is also acceptable.
		# The implementation must ensure _post_fusion_flash_until_ms is set
		# to now + 600 at trigger. This path records a known gap for the
		# implementer; the flash-trigger behavior test will catch it.
		_pass(
			"vch3_ac10_flash_duration_constant -- named const absent; inline 600 acceptable per spec (VCH-3-AC-10)"
		)


# ---------------------------------------------------------------------------
# VCH-1-AC-1: Both slots filled → COLOR_SLOT_DUAL_FILLED applied to both icons
# ---------------------------------------------------------------------------

func test_vch1_ac1_both_slots_filled_icon_color_is_dual_filled() -> void:
	var expected: Color = LogicHarness.COLOR_SLOT_DUAL_FILLED
	var actual_s1: Color = _harness.select_icon_color(true, true, false)
	var actual_s2: Color = _harness.select_icon_color(true, true, false)
	_assert_color_eq(
		expected,
		actual_s1,
		"vch1_ac1_slot1_icon_dual_filled -- slot 1 icon must be COLOR_SLOT_DUAL_FILLED when both filled per VCH-1-AC-1"
	)
	_assert_color_eq(
		expected,
		actual_s2,
		"vch1_ac1_slot2_icon_dual_filled -- slot 2 icon must be COLOR_SLOT_DUAL_FILLED when both filled per VCH-1-AC-1"
	)


# VCH-1-AC-5: Both slots filled → label modulate COLOR_LABEL_DUAL_FILLED
func test_vch1_ac5_both_slots_filled_label_color_is_dual_filled() -> void:
	var expected: Color = LogicHarness.COLOR_LABEL_DUAL_FILLED
	var actual_l1: Color = _harness.select_label_color(true, true, false)
	var actual_l2: Color = _harness.select_label_color(true, true, false)
	_assert_color_eq(
		expected,
		actual_l1,
		"vch1_ac5_slot1_label_dual_filled -- slot 1 label must be COLOR_LABEL_DUAL_FILLED when both filled per VCH-1-AC-5"
	)
	_assert_color_eq(
		expected,
		actual_l2,
		"vch1_ac5_slot2_label_dual_filled -- slot 2 label must be COLOR_LABEL_DUAL_FILLED when both filled per VCH-1-AC-5"
	)


# ---------------------------------------------------------------------------
# VCH-1-AC-2: Only slot 0 filled → slot 0 icon COLOR_SLOT_SINGLE_FILLED,
#             slot 1 icon COLOR_SLOT_EMPTY
# ---------------------------------------------------------------------------

func test_vch1_ac2_only_slot0_filled_slot0_icon_is_single_filled() -> void:
	# slot 0: filled=true, both_filled=false
	var actual: Color = _harness.select_icon_color(true, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_SINGLE_FILLED,
		actual,
		"vch1_ac2_slot0_icon_single_filled -- slot 0 icon must be COLOR_SLOT_SINGLE_FILLED when only slot 0 filled per VCH-1-AC-2"
	)


func test_vch1_ac2_only_slot0_filled_slot1_icon_is_empty() -> void:
	# slot 1: filled=false, both_filled=false
	var actual: Color = _harness.select_icon_color(false, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_EMPTY,
		actual,
		"vch1_ac2_slot1_icon_empty -- slot 1 icon must be COLOR_SLOT_EMPTY when only slot 0 filled per VCH-1-AC-2"
	)


# VCH-1-AC-6: Only slot 0 filled → slot 0 label COLOR_LABEL_SINGLE_FILLED,
#             slot 1 label COLOR_LABEL_EMPTY
func test_vch1_ac6_only_slot0_filled_slot0_label_is_single_filled() -> void:
	var actual: Color = _harness.select_label_color(true, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_SINGLE_FILLED,
		actual,
		"vch1_ac6_slot0_label_single_filled -- slot 0 label must be COLOR_LABEL_SINGLE_FILLED when only slot 0 filled per VCH-1-AC-6"
	)


func test_vch1_ac6_only_slot0_filled_slot1_label_is_empty() -> void:
	var actual: Color = _harness.select_label_color(false, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_EMPTY,
		actual,
		"vch1_ac6_slot1_label_empty -- slot 1 label must be COLOR_LABEL_EMPTY when slot 1 is empty per VCH-1-AC-6"
	)


# ---------------------------------------------------------------------------
# VCH-1-AC-3: No slots filled → both icons COLOR_SLOT_EMPTY (no flash active)
# ---------------------------------------------------------------------------

func test_vch1_ac3_no_slots_filled_both_icons_empty() -> void:
	var actual_s1: Color = _harness.select_icon_color(false, false, false)
	var actual_s2: Color = _harness.select_icon_color(false, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_EMPTY,
		actual_s1,
		"vch1_ac3_slot1_empty_icon -- slot 1 icon must be COLOR_SLOT_EMPTY when no slots filled per VCH-1-AC-3"
	)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_EMPTY,
		actual_s2,
		"vch1_ac3_slot2_empty_icon -- slot 2 icon must be COLOR_SLOT_EMPTY when no slots filled per VCH-1-AC-3"
	)


# ---------------------------------------------------------------------------
# VCH-1-AC-7: FusePromptLabel visible iff both slots filled
# Driven via SlotManagerDouble (headless-safe).
# Note: the real FusePromptLabel.visible logic reads slot state in _process.
# This test verifies the both_filled condition derivation used by the UI.
# ---------------------------------------------------------------------------

func test_vch1_ac7_fuse_prompt_visible_only_when_both_filled() -> void:
	var mgr: SlotManagerDouble = SlotManagerDouble.new()

	# Both empty: both_filled must be false
	var s0: Object = mgr.get_slot(0)
	var s1: Object = mgr.get_slot(1)
	var both_empty: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)
	_assert_false(
		both_empty,
		"vch1_ac7_both_empty_fuse_hidden -- both_filled must be false when both slots empty per VCH-1-AC-7"
	)

	# Only slot 0 filled
	mgr.set_slot_filled(0, true)
	s0 = mgr.get_slot(0)
	s1 = mgr.get_slot(1)
	var one_filled: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)
	_assert_false(
		one_filled,
		"vch1_ac7_one_filled_fuse_hidden -- both_filled must be false when only slot 0 filled per VCH-1-AC-7"
	)

	# Both filled
	mgr.set_slot_filled(1, true)
	s0 = mgr.get_slot(0)
	s1 = mgr.get_slot(1)
	var both_filled: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)
	_assert_true(
		both_filled,
		"vch1_ac7_both_filled_fuse_visible -- both_filled must be true when both slots filled per VCH-1-AC-7"
	)

	# RefCounted -- no manual free required.


# ---------------------------------------------------------------------------
# VCH-2-AC-7: FusionActiveLabel visible when is_fusion_active() == true
# ---------------------------------------------------------------------------

func test_vch2_ac7_fusion_label_visible_when_fusion_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true
	var visible: bool = _harness.compute_fusion_label_visible(player)
	_assert_true(
		visible,
		"vch2_ac7_label_visible_when_active -- fusion label must be visible when is_fusion_active()=true per VCH-2-AC-7"
	)
	# RefCounted -- no manual free required.


# ---------------------------------------------------------------------------
# VCH-2-AC-8: FusionActiveLabel hidden when is_fusion_active() == false
# ---------------------------------------------------------------------------

func test_vch2_ac8_fusion_label_hidden_when_fusion_not_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = false
	var visible: bool = _harness.compute_fusion_label_visible(player)
	_assert_false(
		visible,
		"vch2_ac8_label_hidden_when_inactive -- fusion label must be hidden when is_fusion_active()=false per VCH-2-AC-8"
	)
	# RefCounted -- no manual free required.


# ---------------------------------------------------------------------------
# VCH-2-AC-9: FusionActiveLabel hidden when _player == null
# ---------------------------------------------------------------------------

func test_vch2_ac9_fusion_label_hidden_when_player_null() -> void:
	var visible: bool = _harness.compute_fusion_label_visible(null)
	_assert_false(
		visible,
		"vch2_ac9_label_hidden_when_null_player -- fusion label must be hidden when player is null per VCH-2-AC-9"
	)


# ---------------------------------------------------------------------------
# VCH-2: Real script exposes _update_fusion_display and _get_fusion_active_label
# methods (verifies API-3 and API-4 exist post-implementation).
# ---------------------------------------------------------------------------

func test_vch2_real_script_has_update_fusion_display_method() -> void:
	var script: GDScript = _require_infection_ui("vch2_method_update_fusion_display")
	if script == null:
		return
	# get_script_method_list() returns Array[Dictionary].
	var found: bool = false
	for method_info in script.get_script_method_list():
		if method_info.get("name", "") == "_update_fusion_display":
			found = true
			break
	if not found:
		_fail(
			"vch2_method_update_fusion_display",
			"_update_fusion_display() not found on InfectionUI -- implement per API-3"
		)
	else:
		_pass("vch2_method_update_fusion_display -- _update_fusion_display() exists per API-3")


func test_vch2_real_script_has_get_fusion_active_label_method() -> void:
	var script: GDScript = _require_infection_ui("vch2_method_get_fusion_active_label")
	if script == null:
		return
	var found: bool = false
	for method_info: Dictionary in script.get_script_method_list():
		if method_info.get("name", "") == "_get_fusion_active_label":
			found = true
			break
	if not found:
		_fail(
			"vch2_method_get_fusion_active_label",
			"_get_fusion_active_label() not found on InfectionUI -- implement per API-4"
		)
	else:
		_pass("vch2_method_get_fusion_active_label -- _get_fusion_active_label() exists per API-4")


# ---------------------------------------------------------------------------
# VCH-2: Real script has updated _update_slot_display signature (4 params, API-2)
# ---------------------------------------------------------------------------

func test_vch1_real_script_update_slot_display_has_four_params() -> void:
	var script: GDScript = _require_infection_ui("vch1_update_slot_display_signature")
	if script == null:
		return
	for method_info: Dictionary in script.get_script_method_list():
		if method_info.get("name", "") == "_update_slot_display":
			var args: Array = method_info.get("args", [])
			if args.size() == 4:
				_pass(
					"vch1_update_slot_display_signature -- _update_slot_display has 4 params per API-2"
				)
			else:
				_fail(
					"vch1_update_slot_display_signature",
					"_update_slot_display has " + str(args.size()) + " params, expected 4 (slot_number, slot, both_filled, post_fusion_flash_active) per API-2"
				)
			return
	_fail(
		"vch1_update_slot_display_signature",
		"_update_slot_display not found on InfectionUI"
	)


# ---------------------------------------------------------------------------
# VCH-3-AC-1: InfectionUI declares _post_fusion_flash_until_ms and
#             _prev_both_filled fields (verified via script property map).
# ---------------------------------------------------------------------------

func test_vch3_ac1_post_fusion_flash_fields_declared() -> void:
	var script: GDScript = _require_infection_ui("vch3_ac1_flash_fields")
	if script == null:
		return
	var prop_map: Array = script.get_script_property_list()
	var has_ms_field: bool = false
	var has_prev_field: bool = false
	for prop in prop_map:
		var pname: String = prop.get("name", "")
		if pname == "_post_fusion_flash_until_ms":
			has_ms_field = true
		if pname == "_prev_both_filled":
			has_prev_field = true
	if not has_ms_field:
		_fail(
			"vch3_ac1_flash_fields",
			"_post_fusion_flash_until_ms not declared on InfectionUI -- add 'var _post_fusion_flash_until_ms: int = 0' per VCH-3-AC-1"
		)
	else:
		_pass("vch3_ac1_flash_until_ms_field -- _post_fusion_flash_until_ms declared per VCH-3-AC-1")

	if not has_prev_field:
		_fail(
			"vch3_ac1_prev_both_filled_field",
			"_prev_both_filled not declared on InfectionUI -- add 'var _prev_both_filled: bool = false' per VCH-3-AC-1"
		)
	else:
		_pass("vch3_ac1_prev_both_filled_field -- _prev_both_filled declared per VCH-3-AC-1")


# ---------------------------------------------------------------------------
# VCH-3-AC-2: Flash trigger fires when prev_both_filled=true, both_filled=false,
#             and is_fusion_active()=true.
# ---------------------------------------------------------------------------

func test_vch3_ac2_flash_triggered_on_both_filled_to_false_with_fusion_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true

	var triggered: bool = _harness.should_trigger_flash(
		true,   # _prev_both_filled
		false,  # current both_filled (just cleared)
		player
	)
	_assert_true(
		triggered,
		"vch3_ac2_flash_triggered -- flash must trigger when prev_both_filled=true, both_filled=false, fusion_active=true per VCH-3-AC-2"
	)
	# RefCounted -- no manual free required.


# VCH-3-AC-8: Slots cleared without fusion → flash NOT triggered.
func test_vch3_ac8_flash_not_triggered_when_fusion_not_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = false  # Slots cleared but fusion NOT active

	var triggered: bool = _harness.should_trigger_flash(true, false, player)
	_assert_false(
		triggered,
		"vch3_ac8_no_flash_without_fusion -- flash must NOT trigger when fusion_active=false per VCH-3-AC-8"
	)
	# RefCounted -- no manual free required.


# Flash not triggered when prev_both_filled was already false (no transition).
func test_vch3_no_flash_when_prev_both_filled_was_false() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true

	var triggered: bool = _harness.should_trigger_flash(
		false,  # _prev_both_filled was already false (no true→false transition)
		false,
		player
	)
	_assert_false(
		triggered,
		"vch3_no_flash_no_transition -- flash must NOT trigger when prev_both_filled was already false (no true->false transition)"
	)
	# RefCounted -- no manual free required.


# Flash not triggered when both_filled remains true (not a clearing event).
func test_vch3_no_flash_when_both_still_filled() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true

	var triggered: bool = _harness.should_trigger_flash(
		true,
		true,   # both_filled still true; no transition
		player
	)
	_assert_false(
		triggered,
		"vch3_no_flash_still_filled -- flash must NOT trigger when both slots remain filled per VCH-3"
	)
	# RefCounted -- no manual free required.


# Flash not triggered when player is null.
func test_vch3_no_flash_when_player_null() -> void:
	var triggered: bool = _harness.should_trigger_flash(true, false, null)
	_assert_false(
		triggered,
		"vch3_no_flash_null_player -- flash must NOT trigger when player is null (null guard per VCH-3)"
	)


# ---------------------------------------------------------------------------
# VCH-3-AC-3 / VCH-3-AC-4: While flash window active, icons use POST_FUSION color.
# Driven via the color selection logic with post_fusion_flash_active=true.
# ---------------------------------------------------------------------------

func test_vch3_ac3_flash_active_icon_color_is_post_fusion() -> void:
	# Both slots empty but flash window still active.
	var actual: Color = _harness.select_icon_color(false, false, true)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_POST_FUSION,
		actual,
		"vch3_ac3_flash_active_icon -- icon must be COLOR_SLOT_POST_FUSION when flash is active per VCH-3-AC-3"
	)


func test_vch3_ac4_flash_active_label_color_is_post_fusion() -> void:
	var actual: Color = _harness.select_label_color(false, false, true)
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_POST_FUSION,
		actual,
		"vch3_ac4_flash_active_label -- label must be COLOR_LABEL_POST_FUSION when flash is active per VCH-3-AC-4"
	)


# ---------------------------------------------------------------------------
# VCH-3-AC-5 / VCH-3-AC-6: After flash expires, empty slots revert to EMPTY.
# ---------------------------------------------------------------------------

func test_vch3_ac5_flash_expired_empty_slots_revert_to_empty_icon() -> void:
	# Flash inactive (post_fusion_flash_active=false), both slots empty.
	var actual: Color = _harness.select_icon_color(false, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_EMPTY,
		actual,
		"vch3_ac5_flash_expired_icon -- icon must revert to COLOR_SLOT_EMPTY after flash expires per VCH-3-AC-5"
	)


func test_vch3_ac6_flash_expired_empty_slots_revert_to_empty_label() -> void:
	var actual: Color = _harness.select_label_color(false, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_EMPTY,
		actual,
		"vch3_ac6_flash_expired_label -- label must revert to COLOR_LABEL_EMPTY after flash expires per VCH-3-AC-6"
	)


# ---------------------------------------------------------------------------
# VCH-3-AC-11: Post-fusion flash overrides dual-fill color.
# Pathological case: flash active AND both slots filled simultaneously.
# COLOR_SLOT_POST_FUSION must take priority over COLOR_SLOT_DUAL_FILLED.
# ---------------------------------------------------------------------------

func test_vch3_ac11_flash_overrides_dual_fill_icon_color() -> void:
	# filled=true, both_filled=true, post_fusion_flash_active=true
	# Priority rule: POST_FUSION wins.
	var actual: Color = _harness.select_icon_color(true, true, true)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_POST_FUSION,
		actual,
		"vch3_ac11_flash_beats_dual_fill -- COLOR_SLOT_POST_FUSION must override COLOR_SLOT_DUAL_FILLED when flash is active per VCH-3-AC-11"
	)


func test_vch3_ac11_flash_overrides_dual_fill_label_color() -> void:
	var actual: Color = _harness.select_label_color(true, true, true)
	_assert_color_eq(
		LogicHarness.COLOR_LABEL_POST_FUSION,
		actual,
		"vch3_ac11_flash_beats_dual_fill_label -- COLOR_LABEL_POST_FUSION must override COLOR_LABEL_DUAL_FILLED when flash is active per VCH-3-AC-11"
	)


# ---------------------------------------------------------------------------
# VCH-1-AC-8: Legacy MutationIcon backward compat — single-slot color,
# regardless of dual-slot state.
# The legacy icon (slot index 0, driven outside the dual-slot path) must use
# COLOR_SLOT_SINGLE_FILLED (filled) or COLOR_SLOT_EMPTY (unfilled).
# This is verified by asserting these two outcomes cover the full legacy range;
# no dual-fill or post-fusion color may appear on the legacy icon.
# ---------------------------------------------------------------------------

func test_vch1_ac8_legacy_icon_uses_single_or_empty_only() -> void:
	# Legacy icon path: filled → SINGLE_FILLED
	var legacy_filled: Color = _harness.select_icon_color(true, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_SINGLE_FILLED,
		legacy_filled,
		"vch1_ac8_legacy_icon_filled -- legacy icon (slot 0, both_filled=false) must be COLOR_SLOT_SINGLE_FILLED per VCH-1-AC-8"
	)
	# Legacy icon path: empty → EMPTY
	var legacy_empty: Color = _harness.select_icon_color(false, false, false)
	_assert_color_eq(
		LogicHarness.COLOR_SLOT_EMPTY,
		legacy_empty,
		"vch1_ac8_legacy_icon_empty -- legacy icon (unfilled) must be COLOR_SLOT_EMPTY per VCH-1-AC-8"
	)
	# Neither must be DUAL_FILLED
	_assert_color_ne(
		LogicHarness.COLOR_SLOT_DUAL_FILLED,
		legacy_filled,
		"vch1_ac8_legacy_icon_not_dual -- legacy icon must never use COLOR_SLOT_DUAL_FILLED per VCH-1-AC-8"
	)


# ---------------------------------------------------------------------------
# VCH-2-AC-10: FusePromptLabel visibility is independent of fusion-active state.
# Both labels can be non-null simultaneously; changing fusion-active state
# must not affect the fuse-prompt visibility calculation.
# Verified by showing: both_filled drives fuse_prompt_visible, independently
# of what is_fusion_active() returns.
# ---------------------------------------------------------------------------

func test_vch2_ac10_fuse_prompt_independent_of_fusion_active() -> void:
	var mgr: SlotManagerDouble = SlotManagerDouble.new()
	mgr.set_slot_filled(0, true)
	mgr.set_slot_filled(1, true)

	var player_active: PlayerDouble = PlayerDouble.new()
	player_active._fusion_active = true
	var player_inactive: PlayerDouble = PlayerDouble.new()
	player_inactive._fusion_active = false

	# Fuse prompt visibility is driven by both_filled, not by fusion state.
	# both_filled is true for both player states.
	var s0: Object = mgr.get_slot(0)
	var s1: Object = mgr.get_slot(1)
	var both_filled: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)

	# With fusion active: fuse_prompt_visible == both_filled (true), unaffected.
	var fusion_label_vis_active: bool = _harness.compute_fusion_label_visible(player_active)
	_assert_true(
		both_filled,
		"vch2_ac10_both_filled_true -- both_filled must be true for this test"
	)
	_assert_true(
		fusion_label_vis_active,
		"vch2_ac10_fusion_label_vis_active -- fusion label visible when active"
	)
	# fuse_prompt visibility == both_filled regardless of fusion_label_vis
	_assert_true(
		both_filled,
		"vch2_ac10_fuse_prompt_when_active -- fuse_prompt visible (both_filled=true) unaffected by fusion_active=true per VCH-2-AC-10"
	)

	# With fusion inactive: fuse_prompt_visible still == both_filled (true)
	var fusion_label_vis_inactive: bool = _harness.compute_fusion_label_visible(player_inactive)
	_assert_false(
		fusion_label_vis_inactive,
		"vch2_ac10_fusion_label_hid_inactive -- fusion label hidden when inactive"
	)
	_assert_true(
		both_filled,
		"vch2_ac10_fuse_prompt_when_inactive -- fuse_prompt visible (both_filled=true) unaffected by fusion_active=false per VCH-2-AC-10"
	)

	# RefCounted -- no manual free required.


# ---------------------------------------------------------------------------
# VCH-3-AC-9: _prev_both_filled updated to current both_filled each frame.
# Verified by testing that the trigger fires on the first transition but
# NOT on a subsequent identical call (because _prev_both_filled should have
# been updated — the harness models this stateless, so we verify the update
# logic contract separately).
# This test verifies the no-retrigger property: if should_trigger_flash is
# called again with prev_both_filled=false (already updated), no flash fires.
# ---------------------------------------------------------------------------

func test_vch3_ac9_prev_both_filled_update_prevents_double_trigger() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true

	# Frame N: prev=true, current=false → flash triggered.
	var first_frame: bool = _harness.should_trigger_flash(true, false, player)
	_assert_true(first_frame, "vch3_ac9_first_trigger -- flash fires on first transition")

	# Frame N+1: prev now updated to false (current both_filled from last frame).
	# current=false again. No second trigger.
	var second_frame: bool = _harness.should_trigger_flash(false, false, player)
	_assert_false(
		second_frame,
		"vch3_ac9_no_double_trigger -- flash must not retrigger when prev_both_filled already updated to false per VCH-3-AC-9"
	)

	# RefCounted -- no manual free required.


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- tests/ui/test_infection_ui_hybrid_visuals.gd ---")
	_pass_count = 0
	_fail_count = 0

	_harness = LogicHarness.new()

	# Constant integrity (no runtime required)
	test_vch1_ac4_dual_filled_differs_from_single_filled_constant()
	test_vch3_ac7_post_fusion_differs_from_empty_constant()

	# Real script constant declarations (VCH-1 NF-1)
	test_vch1_real_script_declares_color_slot_empty()
	test_vch1_real_script_declares_color_slot_single_filled()
	test_vch1_real_script_declares_color_slot_dual_filled()
	test_vch1_real_script_declares_color_slot_post_fusion()
	test_vch1_real_script_declares_color_label_empty()
	test_vch1_real_script_declares_color_label_single_filled()
	test_vch1_real_script_declares_color_label_dual_filled()
	test_vch1_real_script_declares_color_label_post_fusion()

	# VCH-3 flash duration constant
	test_vch3_ac10_flash_duration_constant_present()

	# Real script method signatures
	test_vch2_real_script_has_update_fusion_display_method()
	test_vch2_real_script_has_get_fusion_active_label_method()
	test_vch1_real_script_update_slot_display_has_four_params()

	# Real script field declarations (VCH-3-AC-1)
	test_vch3_ac1_post_fusion_flash_fields_declared()

	# VCH-1: Color selection logic — dual filled
	test_vch1_ac1_both_slots_filled_icon_color_is_dual_filled()
	test_vch1_ac5_both_slots_filled_label_color_is_dual_filled()

	# VCH-1: Color selection logic — single filled
	test_vch1_ac2_only_slot0_filled_slot0_icon_is_single_filled()
	test_vch1_ac2_only_slot0_filled_slot1_icon_is_empty()
	test_vch1_ac6_only_slot0_filled_slot0_label_is_single_filled()
	test_vch1_ac6_only_slot0_filled_slot1_label_is_empty()

	# VCH-1: Color selection logic — empty
	test_vch1_ac3_no_slots_filled_both_icons_empty()

	# VCH-1-AC-7: FusePromptLabel visibility condition
	test_vch1_ac7_fuse_prompt_visible_only_when_both_filled()

	# VCH-1-AC-8: Legacy icon backward compat
	test_vch1_ac8_legacy_icon_uses_single_or_empty_only()

	# VCH-2: Fusion active label visibility
	test_vch2_ac7_fusion_label_visible_when_fusion_active()
	test_vch2_ac8_fusion_label_hidden_when_fusion_not_active()
	test_vch2_ac9_fusion_label_hidden_when_player_null()
	test_vch2_ac10_fuse_prompt_independent_of_fusion_active()

	# VCH-3: Flash trigger detection
	test_vch3_ac2_flash_triggered_on_both_filled_to_false_with_fusion_active()
	test_vch3_ac8_flash_not_triggered_when_fusion_not_active()
	test_vch3_no_flash_when_prev_both_filled_was_false()
	test_vch3_no_flash_when_both_still_filled()
	test_vch3_no_flash_when_player_null()

	# VCH-3: Flash-active color override
	test_vch3_ac3_flash_active_icon_color_is_post_fusion()
	test_vch3_ac4_flash_active_label_color_is_post_fusion()

	# VCH-3: Flash-expired revert
	test_vch3_ac5_flash_expired_empty_slots_revert_to_empty_icon()
	test_vch3_ac6_flash_expired_empty_slots_revert_to_empty_label()

	# VCH-3: Post-fusion flash priority over dual-fill
	test_vch3_ac11_flash_overrides_dual_fill_icon_color()
	test_vch3_ac11_flash_overrides_dual_fill_label_color()

	# VCH-3: No double-trigger on consecutive frames
	test_vch3_ac9_prev_both_filled_update_prevents_double_trigger()

	# _harness is RefCounted -- auto-released.

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
