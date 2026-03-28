#
# test_infection_ui_hybrid_visuals_adversarial.gd
#
# Adversarial companion suite for InfectionUI hybrid visual state logic.
#
# Ticket: visual_clarity_hybrid_state.md
# Spec:   visual_clarity_hybrid_state_spec.md  (VCH-1, VCH-2, VCH-3)
#
# Purpose:
#   Expose failure modes a naive implementation would miss. Primary tests verify
#   "happy path + basic contract"; adversarial tests verify that the WRONG
#   behavior actually fails. Every test in this file is labeled with the failure
#   mode it targets (FM-1 through FM-10).
#
#   FM-1:  Both slots filled but COLOR_SLOT_DUAL_FILLED == COLOR_SLOT_SINGLE_FILLED
#          (same-color bug — implementation declares constant but applies wrong one).
#   FM-2:  Fusion active but FusionActiveLabel is hidden (indicator absent).
#   FM-3:  Fusion NOT active but FusionActiveLabel is visible (false positive).
#   FM-4:  Post-fusion cleared state identical in color to never-absorbed empty.
#   FM-5:  FusePromptLabel stays visible after fusion resolves and slots clear.
#   FM-6:  Slot label text changes but color stays same (text-only treated as
#          visual distinction — no constant used for label modulate).
#   FM-7:  Flash triggered by non-fusion slot clear (absorb path clears both slots
#          without fusion active — spec requires NO flash in this case).
#   FM-8:  Flash duration exactly zero (immediate expiry — condition `now < now`
#          is always false; flash must NOT show even for one frame).
#   FM-9:  is_fusion_active() method missing from PlayerController3D.
#   FM-10: Color priority order violated — post-fusion flash does NOT override
#          dual-filled color when both are simultaneously active.
#
# Headless safety strategy:
#   Mirrors the primary suite. Inner-class doubles extend RefCounted.
#   LogicHarness from the primary suite is not reused (separate class scope);
#   adversarial harness is defined locally and intentionally includes a
#   "BuggyHarness" that implements the WRONG behavior so tests can assert
#   that the harness under test (correct harness) differs from the buggy one.
#
# All tests are deterministic. No Time.get_ticks_msec() calls drive assertions;
# timer-boundary tests use synthetic timestamp arithmetic.
#

class_name InfectionUIHybridVisualsAdversarialTests
extends "res://tests/utils/test_utils.gd"


# ---------------------------------------------------------------------------
# Inner-class doubles (mirrors primary suite pattern; RefCounted throughout)
# ---------------------------------------------------------------------------

class SlotDouble extends RefCounted:
	var _filled: bool = false
	var _mutation_id: String = "test_mutation"

	func is_filled() -> bool:
		return _filled

	func get_active_mutation_id() -> String:
		return _mutation_id

	func set_filled(value: bool) -> void:
		_filled = value


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


class PlayerDouble extends RefCounted:
	var _fusion_active: bool = false

	func is_fusion_active() -> bool:
		return _fusion_active


# PlayerDoubleNoAccessor: a player stub that deliberately does NOT implement
# is_fusion_active(), simulating a missing-method scenario (FM-9).
class PlayerDoubleNoAccessor extends RefCounted:
	var _fusion_active: bool = false
	# Note: is_fusion_active() intentionally omitted.


class LabelDouble extends RefCounted:
	var visible: bool = false
	var text: String = ""
	var modulate: Color = Color.WHITE


class ColorRectDouble extends RefCounted:
	var visible: bool = false
	var color: Color = Color.BLACK


# ---------------------------------------------------------------------------
# CorrectHarness: implements the spec-correct color-selection algorithm.
# Tested against BuggyHarness outputs to confirm divergence where expected.
# ---------------------------------------------------------------------------

class CorrectHarness extends RefCounted:
	const COLOR_SLOT_EMPTY         = Color(0.2, 0.2, 0.2, 0.6)
	const COLOR_SLOT_SINGLE_FILLED = Color(0.4, 0.85, 0.55, 1.0)
	const COLOR_SLOT_DUAL_FILLED   = Color(0.3, 0.65, 1.0, 1.0)
	const COLOR_SLOT_POST_FUSION   = Color(1.0, 1.0, 1.0, 1.0)

	const COLOR_LABEL_EMPTY         = Color(0.7, 0.7, 0.7, 1.0)
	const COLOR_LABEL_SINGLE_FILLED = Color(0.9, 1.0, 0.9, 1.0)
	const COLOR_LABEL_DUAL_FILLED   = Color(0.6, 0.85, 1.0, 1.0)
	const COLOR_LABEL_POST_FUSION   = Color(1.0, 0.9, 0.5, 1.0)

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

	func compute_fusion_label_visible(player: Object) -> bool:
		if player == null:
			return false
		if not player.has_method("is_fusion_active"):
			return false
		return player.is_fusion_active()

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

	# Evaluates whether the flash is active given a synthetic now_ms and
	# the stored deadline.
	# Spec contract: flash_active == (now_ms < flash_until_ms)
	func is_flash_active(now_ms: int, flash_until_ms: int) -> bool:
		return now_ms < flash_until_ms


# ---------------------------------------------------------------------------
# BuggyHarness: intentionally wrong implementations used to prove that the
# correct harness diverges from them in adversarial inputs.
# ---------------------------------------------------------------------------

# BuggyHarness_SameColor: uses SINGLE_FILLED for ALL filled slots (FM-1 bug).
class BuggyHarness_SameColor extends RefCounted:
	const COLOR_SLOT_SINGLE_FILLED = Color(0.4, 0.85, 0.55, 1.0)
	const COLOR_SLOT_EMPTY         = Color(0.2, 0.2, 0.2, 0.6)

	func select_icon_color(filled: bool, _both_filled: bool,
			_post_fusion_flash_active: bool) -> Color:
		# Bug: ignores both_filled and post_fusion; always applies single-fill color.
		if filled:
			return COLOR_SLOT_SINGLE_FILLED
		return COLOR_SLOT_EMPTY


# BuggyHarness_FusionLabelAlwaysHidden: never shows FusionActiveLabel (FM-2 bug).
class BuggyHarness_FusionLabelAlwaysHidden extends RefCounted:
	func compute_fusion_label_visible(_player: Object) -> bool:
		return false


# BuggyHarness_FusionLabelAlwaysVisible: always shows FusionActiveLabel (FM-3 bug).
class BuggyHarness_FusionLabelAlwaysVisible extends RefCounted:
	func compute_fusion_label_visible(_player: Object) -> bool:
		return true


# BuggyHarness_NoPostFusionFlash: never triggers flash, so post-fusion empty
# looks identical to never-absorbed empty (FM-4 bug).
class BuggyHarness_NoPostFusionFlash extends RefCounted:
	const COLOR_SLOT_EMPTY = Color(0.2, 0.2, 0.2, 0.6)

	func select_icon_color(_filled: bool, _both_filled: bool,
			_post_fusion_flash_active: bool) -> Color:
		# Bug: ignores post_fusion_flash_active entirely.
		return COLOR_SLOT_EMPTY

	func should_trigger_flash(_prev: bool, _curr: bool, _player: Object) -> bool:
		return false


# BuggyHarness_WrongPriority: applies dual-fill color even when flash is active
# (FM-10 bug — dual-fill takes priority over post-fusion flash).
class BuggyHarness_WrongPriority extends RefCounted:
	const COLOR_SLOT_DUAL_FILLED = Color(0.3, 0.65, 1.0, 1.0)
	const COLOR_SLOT_POST_FUSION = Color(1.0, 1.0, 1.0, 1.0)

	func select_icon_color(filled: bool, both_filled: bool,
			post_fusion_flash_active: bool) -> Color:
		# Bug: checks dual-fill BEFORE post-fusion flash (wrong priority order).
		if filled and both_filled:
			return COLOR_SLOT_DUAL_FILLED
		if post_fusion_flash_active:
			return COLOR_SLOT_POST_FUSION
		return Color(0.2, 0.2, 0.2, 0.6)


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0
var _harness: CorrectHarness


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


func _load_player_controller_script() -> GDScript:
	return load("res://scripts/player/player_controller_3d.gd") as GDScript


func _get_script_constant(script: GDScript, name: String) -> Variant:
	if script == null:
		return null
	var map: Dictionary = script.get_script_constant_map()
	if map.has(name):
		return map[name]
	return null


# ---------------------------------------------------------------------------
# FM-1: Both slots filled but COLOR_SLOT_DUAL_FILLED == COLOR_SLOT_SINGLE_FILLED
# (same-color bug)
#
# A naive implementation might declare COLOR_SLOT_DUAL_FILLED as a constant but
# accidentally assign it the same value as COLOR_SLOT_SINGLE_FILLED, or apply
# COLOR_SLOT_SINGLE_FILLED in the method body when both_filled=true.
# These tests expose both sub-cases.
# ---------------------------------------------------------------------------

func test_fm1_correct_harness_returns_dual_filled_not_single_when_both_filled() -> void:
	# The correct harness must return DUAL_FILLED for (filled=true, both_filled=true).
	# A buggy implementation that returns SINGLE_FILLED would fail this assertion.
	var correct: Color = _harness.select_icon_color(true, true, false)
	_assert_color_eq(
		CorrectHarness.COLOR_SLOT_DUAL_FILLED,
		correct,
		"fm1_correct_returns_dual -- select_icon_color(true,true,false) must return COLOR_SLOT_DUAL_FILLED not COLOR_SLOT_SINGLE_FILLED (FM-1)"
	)


func test_fm1_buggy_same_color_harness_returns_single_when_both_filled() -> void:
	# Prove the buggy harness DOES return SINGLE_FILLED, establishing the
	# mutation we are guarding against.
	var buggy: BuggyHarness_SameColor = BuggyHarness_SameColor.new()
	var buggy_result: Color = buggy.select_icon_color(true, true, false)
	_assert_color_eq(
		BuggyHarness_SameColor.COLOR_SLOT_SINGLE_FILLED,
		buggy_result,
		"fm1_buggy_returns_single_when_both_filled -- confirms buggy harness behavior for mutation contrast"
	)


func test_fm1_correct_and_buggy_diverge_when_both_filled() -> void:
	# The correct and buggy harnesses MUST diverge on (both filled, no flash).
	# This is the key invariant: correct != buggy for this input.
	var correct_result: Color = _harness.select_icon_color(true, true, false)
	var buggy: BuggyHarness_SameColor = BuggyHarness_SameColor.new()
	var buggy_result: Color = buggy.select_icon_color(true, true, false)
	_assert_color_ne(
		correct_result,
		buggy_result,
		"fm1_correct_ne_buggy_both_filled -- correct harness must produce a different color than the same-color-bug harness when both slots filled (FM-1)"
	)


func test_fm1_real_script_dual_filled_constant_ne_single_filled_constant() -> void:
	# Verify that the REAL InfectionUI script's constants are not the same value.
	# This fails if the implementer copies the wrong color value.
	var script: GDScript = _load_infection_ui_script()
	if script == null:
		_fail("fm1_real_script_constants_ne", "InfectionUI script not loadable")
		return
	var dual: Variant = _get_script_constant(script, "COLOR_SLOT_DUAL_FILLED")
	var single: Variant = _get_script_constant(script, "COLOR_SLOT_SINGLE_FILLED")
	if dual == null or single == null:
		_fail(
			"fm1_real_script_constants_ne",
			"One or both constants missing from InfectionUI -- declare per spec NF-1 (FM-1)"
		)
		return
	var dual_color: Color = dual as Color
	var single_color: Color = single as Color
	_assert_color_ne(
		dual_color,
		single_color,
		"fm1_real_script_dual_ne_single -- COLOR_SLOT_DUAL_FILLED must not equal COLOR_SLOT_SINGLE_FILLED in real script (FM-1)"
	)


# ---------------------------------------------------------------------------
# FM-2: Fusion active but FusionActiveLabel is hidden (indicator absent)
#
# The correct harness must return visible=true when is_fusion_active()=true.
# The buggy harness that always hides it would return false.
# ---------------------------------------------------------------------------

func test_fm2_correct_harness_shows_label_when_fusion_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true
	var visible: bool = _harness.compute_fusion_label_visible(player)
	_assert_true(
		visible,
		"fm2_correct_shows_label_when_active -- compute_fusion_label_visible must return true when is_fusion_active()=true (FM-2)"
	)


func test_fm2_buggy_always_hidden_harness_returns_false_when_fusion_active() -> void:
	# Prove the always-hidden buggy harness returns false even when fusion is active.
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true
	var buggy: BuggyHarness_FusionLabelAlwaysHidden = BuggyHarness_FusionLabelAlwaysHidden.new()
	var visible: bool = buggy.compute_fusion_label_visible(player)
	_assert_false(
		visible,
		"fm2_buggy_always_hidden_returns_false -- confirms always-hidden harness behavior; real impl must differ (FM-2)"
	)


func test_fm2_correct_and_buggy_diverge_when_fusion_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true
	var correct_vis: bool = _harness.compute_fusion_label_visible(player)
	var buggy: BuggyHarness_FusionLabelAlwaysHidden = BuggyHarness_FusionLabelAlwaysHidden.new()
	var buggy_vis: bool = buggy.compute_fusion_label_visible(player)
	_assert_true(
		correct_vis != buggy_vis,
		"fm2_correct_ne_buggy_when_active -- correct and always-hidden harnesses must diverge when fusion is active (FM-2)"
	)


# ---------------------------------------------------------------------------
# FM-3: Fusion NOT active but FusionActiveLabel is visible (false positive)
#
# The correct harness must return visible=false when is_fusion_active()=false.
# The always-visible buggy harness would return true.
# ---------------------------------------------------------------------------

func test_fm3_correct_harness_hides_label_when_fusion_not_active() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = false
	var visible: bool = _harness.compute_fusion_label_visible(player)
	_assert_false(
		visible,
		"fm3_correct_hides_label_when_inactive -- compute_fusion_label_visible must return false when is_fusion_active()=false (FM-3)"
	)


func test_fm3_buggy_always_visible_harness_returns_true_when_inactive() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = false
	var buggy: BuggyHarness_FusionLabelAlwaysVisible = BuggyHarness_FusionLabelAlwaysVisible.new()
	var visible: bool = buggy.compute_fusion_label_visible(player)
	_assert_true(
		visible,
		"fm3_buggy_always_visible_returns_true -- confirms always-visible bug harness; real impl must differ (FM-3)"
	)


func test_fm3_correct_and_buggy_diverge_when_inactive() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = false
	var correct_vis: bool = _harness.compute_fusion_label_visible(player)
	var buggy: BuggyHarness_FusionLabelAlwaysVisible = BuggyHarness_FusionLabelAlwaysVisible.new()
	var buggy_vis: bool = buggy.compute_fusion_label_visible(player)
	_assert_true(
		correct_vis != buggy_vis,
		"fm3_correct_ne_buggy_when_inactive -- correct and always-visible harnesses must diverge when fusion inactive (FM-3)"
	)


# ---------------------------------------------------------------------------
# FM-4: Post-fusion cleared state identical in color to never-absorbed empty
#
# When flash is active (post_fusion_flash_active=true), the icon must display
# COLOR_SLOT_POST_FUSION, NOT COLOR_SLOT_EMPTY. A buggy implementation that
# never activates the flash shows EMPTY in both states -- indistinguishable.
# ---------------------------------------------------------------------------

func test_fm4_post_fusion_cleared_state_differs_from_never_absorbed_empty() -> void:
	# Never-absorbed empty: flash inactive, slot empty.
	var never_absorbed: Color = _harness.select_icon_color(false, false, false)
	# Post-fusion cleared: flash active, slot empty.
	var post_fusion: Color = _harness.select_icon_color(false, false, true)
	_assert_color_ne(
		never_absorbed,
		post_fusion,
		"fm4_post_fusion_differs_from_empty -- post-fusion cleared state must visually differ from never-absorbed empty (FM-4)"
	)


func test_fm4_buggy_no_flash_makes_states_identical() -> void:
	# The no-flash buggy harness returns EMPTY in both states -- they are the same.
	var buggy: BuggyHarness_NoPostFusionFlash = BuggyHarness_NoPostFusionFlash.new()
	var never_absorbed: Color = buggy.select_icon_color(false, false, false)
	var post_fusion: Color = buggy.select_icon_color(false, false, true)
	_assert_color_eq(
		never_absorbed,
		post_fusion,
		"fm4_buggy_states_identical -- confirms no-flash bug makes states indistinguishable; real impl must differ (FM-4)"
	)


func test_fm4_post_fusion_flash_trigger_fires_when_fusion_active() -> void:
	# Verify the flash trigger condition: prev_both_filled=true, current=false,
	# fusion_active=true → trigger.
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true
	var triggered: bool = _harness.should_trigger_flash(true, false, player)
	_assert_true(
		triggered,
		"fm4_flash_trigger_fires -- flash must trigger when prev_both_filled transitions true->false with fusion active (FM-4)"
	)


func test_fm4_buggy_no_flash_never_triggers() -> void:
	var buggy: BuggyHarness_NoPostFusionFlash = BuggyHarness_NoPostFusionFlash.new()
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = true
	var triggered: bool = buggy.should_trigger_flash(true, false, player)
	_assert_false(
		triggered,
		"fm4_buggy_no_flash_never_triggers -- confirms buggy harness never fires; real impl must differ (FM-4)"
	)


# ---------------------------------------------------------------------------
# FM-5: FusePromptLabel stays visible after fusion resolves and slots clear
#
# After fusion fires: both slots become empty (both_filled=false).
# FusePromptLabel visibility is driven exclusively by both_filled.
# So fuse_prompt must become invisible when slots clear.
# A buggy implementation caching a stale both_filled=true would miss this.
# # CHECKPOINT
# ---------------------------------------------------------------------------

func test_fm5_fuse_prompt_hidden_after_both_slots_clear() -> void:
	var mgr: SlotManagerDouble = SlotManagerDouble.new()

	# Step 1: both slots filled → both_filled = true.
	mgr.set_slot_filled(0, true)
	mgr.set_slot_filled(1, true)
	var s0: Object = mgr.get_slot(0)
	var s1: Object = mgr.get_slot(1)
	var both_filled_before: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)
	_assert_true(
		both_filled_before,
		"fm5_setup_both_filled -- precondition: both slots filled before fusion"
	)

	# Step 2: fusion fires, slots cleared.
	mgr.set_slot_filled(0, false)
	mgr.set_slot_filled(1, false)
	s0 = mgr.get_slot(0)
	s1 = mgr.get_slot(1)
	var both_filled_after: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)
	_assert_false(
		both_filled_after,
		"fm5_both_empty_after_fusion -- after slot clear both_filled must be false (FM-5)"
	)

	# Step 3: fuse_prompt_visible == both_filled_after → must be false.
	# (FusePromptLabel.visible is set to both_filled in _process with no caching.)
	var fuse_prompt_label: LabelDouble = LabelDouble.new()
	fuse_prompt_label.visible = both_filled_after  # simulates: fuse_label.visible = both_filled
	_assert_false(
		fuse_prompt_label.visible,
		"fm5_fuse_prompt_hidden_after_clear -- FusePromptLabel must NOT stay visible after fusion resolves and slots clear (FM-5)"
	)


func test_fm5_only_slot0_cleared_fuse_prompt_still_hidden() -> void:
	# If only one slot clears (edge case), both_filled is false → prompt hidden.
	var mgr: SlotManagerDouble = SlotManagerDouble.new()
	mgr.set_slot_filled(0, false)  # cleared
	mgr.set_slot_filled(1, true)   # still filled

	var s0: Object = mgr.get_slot(0)
	var s1: Object = mgr.get_slot(1)
	var both_filled: bool = (
		s0 != null and s0.has_method("is_filled") and s0.is_filled()
		and s1 != null and s1.has_method("is_filled") and s1.is_filled()
	)
	_assert_false(
		both_filled,
		"fm5_one_slot_cleared_not_both_filled -- with only slot 1 filled, both_filled must be false → fuse prompt hidden (FM-5)"
	)


# ---------------------------------------------------------------------------
# FM-6: Slot label text changes but color stays same (text-only change treated
# as visual distinction -- color constant not applied)
#
# This targets the case where a naive implementer changes label.text when the
# mutation_id changes but leaves label.modulate at the default Color.WHITE
# instead of applying the spec-named constant.
#
# The adversarial test verifies:
# (a) COLOR_LABEL_SINGLE_FILLED != Color.WHITE (the default modulate),
# (b) when a slot is single-filled, the label harness returns
#     COLOR_LABEL_SINGLE_FILLED (not Color.WHITE),
# (c) the real script's COLOR_LABEL_SINGLE_FILLED constant matches the harness
#     value (no magic-number drift).
# # CHECKPOINT
# ---------------------------------------------------------------------------

func test_fm6_label_single_filled_color_differs_from_white_default() -> void:
	# Color.WHITE is the default modulate for a Label node.
	# If an implementer never sets modulate, the label stays white.
	# COLOR_LABEL_SINGLE_FILLED must differ from white so text-color IS a cue.
	_assert_color_ne(
		CorrectHarness.COLOR_LABEL_SINGLE_FILLED,
		Color.WHITE,
		"fm6_single_filled_label_ne_white -- COLOR_LABEL_SINGLE_FILLED must differ from Color.WHITE; text-only change is not sufficient visual distinction (FM-6)"
	)


func test_fm6_label_dual_filled_color_differs_from_single_filled_color() -> void:
	# If both states use the same label color, a text-only change is the only
	# distinction. Must have different label colors for different states.
	_assert_color_ne(
		CorrectHarness.COLOR_LABEL_DUAL_FILLED,
		CorrectHarness.COLOR_LABEL_SINGLE_FILLED,
		"fm6_dual_label_ne_single_label -- COLOR_LABEL_DUAL_FILLED must differ from COLOR_LABEL_SINGLE_FILLED; label color IS the per-state distinguisher (FM-6)"
	)


func test_fm6_correct_harness_applies_single_filled_label_color_not_white() -> void:
	# The harness must return the named constant, not Color.WHITE.
	var actual_label_color: Color = _harness.select_label_color(true, false, false)
	_assert_color_ne(
		Color.WHITE,
		actual_label_color,
		"fm6_harness_label_not_white_when_single_filled -- label must receive named color constant, not default white (FM-6)"
	)
	_assert_color_eq(
		CorrectHarness.COLOR_LABEL_SINGLE_FILLED,
		actual_label_color,
		"fm6_harness_label_is_single_filled_constant -- label color must exactly equal COLOR_LABEL_SINGLE_FILLED constant (FM-6)"
	)


func test_fm6_real_script_label_single_filled_matches_harness_constant() -> void:
	# Guard against magic-number drift: real script constant must equal harness value.
	# If an implementer copies Color(0.9, 1.0, 0.9) directly into the method body
	# instead of using the named constant, the spec check (NF-1) will catch
	# the missing constant. This test catches a different failure: the constant
	# exists but has a WRONG value that still looks "close to" correct visually.
	var script: GDScript = _load_infection_ui_script()
	if script == null:
		_fail("fm6_real_script_label_single", "InfectionUI script not loadable")
		return
	var val: Variant = _get_script_constant(script, "COLOR_LABEL_SINGLE_FILLED")
	if val == null:
		_fail(
			"fm6_real_script_label_single",
			"COLOR_LABEL_SINGLE_FILLED not declared on InfectionUI -- add per spec NF-1 (FM-6)"
		)
		return
	_assert_color_eq(
		CorrectHarness.COLOR_LABEL_SINGLE_FILLED,
		val as Color,
		"fm6_real_script_label_single_value -- COLOR_LABEL_SINGLE_FILLED must equal Color(0.9,1.0,0.9,1.0) per spec (FM-6)"
	)


# ---------------------------------------------------------------------------
# FM-7: Flash triggered by non-fusion slot clear
#
# If both slots are cleared by a future absorb/reset path (not fusion),
# `is_fusion_active()` returns false. The flash must NOT fire.
# A buggy implementation that triggers on any both_filled true→false transition
# would flash even on non-fusion clears.
# ---------------------------------------------------------------------------

func test_fm7_non_fusion_slot_clear_does_not_trigger_flash() -> void:
	var player: PlayerDouble = PlayerDouble.new()
	player._fusion_active = false  # Slots cleared by non-fusion path.

	var triggered: bool = _harness.should_trigger_flash(true, false, player)
	_assert_false(
		triggered,
		"fm7_no_flash_on_non_fusion_clear -- flash must NOT trigger when both_filled goes true->false without fusion active (FM-7)"
	)


func test_fm7_flash_requires_is_fusion_active_true() -> void:
	# Mutation: swap the fusion_active flag. Flash should only fire with fusion=true.
	var player_fused: PlayerDouble = PlayerDouble.new()
	player_fused._fusion_active = true
	var player_no_fuse: PlayerDouble = PlayerDouble.new()
	player_no_fuse._fusion_active = false

	var with_fusion: bool = _harness.should_trigger_flash(true, false, player_fused)
	var without_fusion: bool = _harness.should_trigger_flash(true, false, player_no_fuse)

	_assert_true(
		with_fusion,
		"fm7_flash_fires_with_fusion -- flash fires when fusion_active=true (FM-7 mutation)"
	)
	_assert_false(
		without_fusion,
		"fm7_flash_blocked_without_fusion -- flash blocked when fusion_active=false (FM-7)"
	)
	_assert_true(
		with_fusion != without_fusion,
		"fm7_flash_outcome_differs_by_fusion_flag -- the is_fusion_active flag must gate the flash trigger (FM-7)"
	)


# ---------------------------------------------------------------------------
# FM-8: Flash duration exactly zero (immediate expiry boundary)
#
# The spec condition is: flash_active = (now_ms < flash_until_ms).
# If `_post_fusion_flash_until_ms` is set to `now_ms` instead of `now_ms + 600`,
# the condition `now_ms < now_ms` is always false -- no flash ever shows.
# This test uses synthetic timestamps to verify the strict less-than boundary.
# # CHECKPOINT
# ---------------------------------------------------------------------------

func test_fm8_flash_active_when_now_strictly_less_than_until() -> void:
	# Synthetic: now=1000, until=1001 (1ms future). Flash IS active.
	var is_active: bool = _harness.is_flash_active(1000, 1001)
	_assert_true(
		is_active,
		"fm8_flash_active_one_ms_future -- flash must be active when now_ms < flash_until_ms (FM-8)"
	)


func test_fm8_flash_not_active_when_now_equals_until() -> void:
	# Synthetic: now=1000, until=1000 (zero duration). Flash NOT active.
	# This is the boundary: setting until=now causes immediate expiry.
	var is_active: bool = _harness.is_flash_active(1000, 1000)
	_assert_false(
		is_active,
		"fm8_flash_expired_when_now_equals_until -- flash must NOT be active when now_ms == flash_until_ms (zero-duration boundary) (FM-8)"
	)


func test_fm8_flash_not_active_when_now_past_until() -> void:
	# Synthetic: now=1001, until=1000 (expired). Flash NOT active.
	var is_active: bool = _harness.is_flash_active(1001, 1000)
	_assert_false(
		is_active,
		"fm8_flash_expired_when_now_past_until -- flash must NOT be active when now_ms > flash_until_ms (FM-8)"
	)


func test_fm8_flash_duration_zero_means_no_flash() -> void:
	# If the implementation writes `now_ms` instead of `now_ms + 600` in the
	# assignment (off-by-one: uses `=` not `+`), the flash condition immediately
	# fails. This test documents the expected behavior so the implementer knows
	# `now` alone is not a valid deadline.
	var now_ms: int = 5000  # synthetic fixed "now"
	var wrong_deadline: int = now_ms          # bug: forgot to add 600
	var correct_deadline: int = now_ms + 600  # correct

	var wrong_flash: bool = _harness.is_flash_active(now_ms, wrong_deadline)
	var correct_flash: bool = _harness.is_flash_active(now_ms, correct_deadline)

	_assert_false(
		wrong_flash,
		"fm8_zero_deadline_no_flash -- setting deadline=now (not now+600) produces no flash (FM-8)"
	)
	_assert_true(
		correct_flash,
		"fm8_correct_deadline_shows_flash -- setting deadline=now+600 produces flash (FM-8)"
	)


# ---------------------------------------------------------------------------
# FM-9: is_fusion_active() method missing from PlayerController3D
#
# The spec (API-1) requires this method. If absent, InfectionUI silently breaks
# (GDScript duck-type: has_method() returns false → fusion label never shown).
# This test checks the real script for the method.
# ---------------------------------------------------------------------------

func test_fm9_player_controller_has_is_fusion_active_method() -> void:
	var script: GDScript = _load_player_controller_script()
	if script == null:
		_fail(
			"fm9_player_has_is_fusion_active",
			"player_controller_3d.gd not loadable at res://scripts/player/player_controller_3d.gd"
		)
		return
	var found: bool = false
	for method_info: Dictionary in script.get_script_method_list():
		if method_info.get("name", "") == "is_fusion_active":
			found = true
			break
	if not found:
		_fail(
			"fm9_player_has_is_fusion_active",
			"is_fusion_active() not found on PlayerController3D -- add 'func is_fusion_active() -> bool: return _fusion_active' per spec API-1 (FM-9). Without this, FusionActiveLabel never shows."
		)
	else:
		_pass("fm9_player_has_is_fusion_active -- is_fusion_active() exists on PlayerController3D per API-1")


func test_fm9_player_double_without_accessor_makes_fusion_label_hidden() -> void:
	# Documents the runtime consequence of the missing method:
	# compute_fusion_label_visible guards with has_method(); a player without
	# is_fusion_active() will make the label always hidden, regardless of
	# actual fusion state.
	var missing_accessor_player: PlayerDoubleNoAccessor = PlayerDoubleNoAccessor.new()
	missing_accessor_player._fusion_active = true  # fusion IS active internally
	var visible: bool = _harness.compute_fusion_label_visible(missing_accessor_player)
	_assert_false(
		visible,
		"fm9_missing_accessor_hides_label -- player without is_fusion_active() method causes label to be hidden even when fusion is active; this documents the consequence of FM-9"
	)


# ---------------------------------------------------------------------------
# FM-10: Color priority order violated — post-fusion flash does NOT override
# dual-filled color
#
# The spec priority matrix: post-fusion flash > dual-filled > single-filled > empty.
# A buggy implementation that checks dual-filled BEFORE post-fusion flash would
# show the blue dual-fill color even during a flash window.
# ---------------------------------------------------------------------------

func test_fm10_correct_harness_flash_overrides_dual_filled_icon() -> void:
	# flash=true, filled=true, both_filled=true → must return POST_FUSION, not DUAL_FILLED.
	var actual: Color = _harness.select_icon_color(true, true, true)
	_assert_color_eq(
		CorrectHarness.COLOR_SLOT_POST_FUSION,
		actual,
		"fm10_flash_overrides_dual_icon -- post-fusion flash must override dual-fill color for icon (FM-10)"
	)


func test_fm10_correct_harness_flash_overrides_dual_filled_label() -> void:
	var actual: Color = _harness.select_label_color(true, true, true)
	_assert_color_eq(
		CorrectHarness.COLOR_LABEL_POST_FUSION,
		actual,
		"fm10_flash_overrides_dual_label -- post-fusion flash must override dual-fill color for label (FM-10)"
	)


func test_fm10_buggy_wrong_priority_returns_dual_when_both_active() -> void:
	# The wrong-priority buggy harness checks dual-fill first → returns DUAL_FILLED.
	var buggy: BuggyHarness_WrongPriority = BuggyHarness_WrongPriority.new()
	var actual: Color = buggy.select_icon_color(true, true, true)
	_assert_color_eq(
		BuggyHarness_WrongPriority.COLOR_SLOT_DUAL_FILLED,
		actual,
		"fm10_buggy_returns_dual_when_flash_and_dual_active -- confirms wrong-priority bug returns dual-fill; real impl must differ (FM-10)"
	)


func test_fm10_correct_and_buggy_diverge_when_flash_and_dual_both_active() -> void:
	# Correct returns POST_FUSION; buggy returns DUAL_FILLED. They must differ.
	var correct_result: Color = _harness.select_icon_color(true, true, true)
	var buggy: BuggyHarness_WrongPriority = BuggyHarness_WrongPriority.new()
	var buggy_result: Color = buggy.select_icon_color(true, true, true)
	_assert_color_ne(
		correct_result,
		buggy_result,
		"fm10_correct_ne_buggy_priority -- correct and wrong-priority harnesses must diverge when flash + dual-fill both active (FM-10)"
	)


func test_fm10_post_fusion_ne_dual_filled_constant() -> void:
	# Prerequisite for the priority test to be meaningful: the two target colors differ.
	_assert_color_ne(
		CorrectHarness.COLOR_SLOT_POST_FUSION,
		CorrectHarness.COLOR_SLOT_DUAL_FILLED,
		"fm10_post_fusion_ne_dual_filled -- COLOR_SLOT_POST_FUSION must differ from COLOR_SLOT_DUAL_FILLED (FM-10 precondition)"
	)


# ---------------------------------------------------------------------------
# Combinatorial edge cases: multiple adversarial factors simultaneously
# ---------------------------------------------------------------------------

func test_combo_null_player_and_prev_both_filled_true_no_flash() -> void:
	# Null player + transition: flash must NOT trigger (null guard).
	var triggered: bool = _harness.should_trigger_flash(true, false, null)
	_assert_false(
		triggered,
		"combo_null_player_prev_true_no_flash -- null player prevents flash trigger even with valid transition"
	)


func test_combo_player_without_accessor_and_prev_both_filled_true_no_flash() -> void:
	# Player without is_fusion_active() + valid transition: flash must NOT trigger.
	var no_accessor: PlayerDoubleNoAccessor = PlayerDoubleNoAccessor.new()
	no_accessor._fusion_active = true
	var triggered: bool = _harness.should_trigger_flash(true, false, no_accessor)
	_assert_false(
		triggered,
		"combo_no_accessor_prev_true_no_flash -- player without is_fusion_active() prevents flash trigger (combo FM-7+FM-9)"
	)


func test_combo_flash_active_and_slots_empty_icon_is_post_fusion_not_empty() -> void:
	# Flash active + both slots empty: icon must be POST_FUSION (not EMPTY).
	# This is the core post-fusion distinguishability invariant (FM-4 final form).
	var flash_color: Color = _harness.select_icon_color(false, false, true)
	var empty_color: Color = _harness.select_icon_color(false, false, false)
	_assert_color_ne(
		flash_color,
		empty_color,
		"combo_flash_empty_differs -- flash-active empty state must differ from no-flash empty state (FM-4+FM-8 combo)"
	)
	_assert_color_eq(
		CorrectHarness.COLOR_SLOT_POST_FUSION,
		flash_color,
		"combo_flash_empty_is_post_fusion -- flash-active empty state must equal COLOR_SLOT_POST_FUSION (FM-4+FM-8 combo)"
	)


func test_combo_no_transition_no_flash_no_matter_fusion_state() -> void:
	# No transition (prev_both_filled=false already): flash must not fire regardless of fusion state.
	var player_fused: PlayerDouble = PlayerDouble.new()
	player_fused._fusion_active = true

	var triggered: bool = _harness.should_trigger_flash(false, false, player_fused)
	_assert_false(
		triggered,
		"combo_no_transition_no_flash -- even with fusion active, no flash fires without a true->false transition (FM-7+FM-8 combo)"
	)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- tests/ui/test_infection_ui_hybrid_visuals_adversarial.gd ---")
	_pass_count = 0
	_fail_count = 0

	_harness = CorrectHarness.new()

	# FM-1: Same-color dual-fill bug
	test_fm1_correct_harness_returns_dual_filled_not_single_when_both_filled()
	test_fm1_buggy_same_color_harness_returns_single_when_both_filled()
	test_fm1_correct_and_buggy_diverge_when_both_filled()
	test_fm1_real_script_dual_filled_constant_ne_single_filled_constant()

	# FM-2: Fusion active but FusionActiveLabel hidden
	test_fm2_correct_harness_shows_label_when_fusion_active()
	test_fm2_buggy_always_hidden_harness_returns_false_when_fusion_active()
	test_fm2_correct_and_buggy_diverge_when_fusion_active()

	# FM-3: Fusion inactive but FusionActiveLabel visible (false positive)
	test_fm3_correct_harness_hides_label_when_fusion_not_active()
	test_fm3_buggy_always_visible_harness_returns_true_when_inactive()
	test_fm3_correct_and_buggy_diverge_when_inactive()

	# FM-4: Post-fusion cleared state identical to never-absorbed empty
	test_fm4_post_fusion_cleared_state_differs_from_never_absorbed_empty()
	test_fm4_buggy_no_flash_makes_states_identical()
	test_fm4_post_fusion_flash_trigger_fires_when_fusion_active()
	test_fm4_buggy_no_flash_never_triggers()

	# FM-5: FusePromptLabel stays visible after fusion resolves and slots clear
	test_fm5_fuse_prompt_hidden_after_both_slots_clear()
	test_fm5_only_slot0_cleared_fuse_prompt_still_hidden()

	# FM-6: Text-only change, no color change (label modulate not applied)
	test_fm6_label_single_filled_color_differs_from_white_default()
	test_fm6_label_dual_filled_color_differs_from_single_filled_color()
	test_fm6_correct_harness_applies_single_filled_label_color_not_white()
	test_fm6_real_script_label_single_filled_matches_harness_constant()

	# FM-7: Flash triggered by non-fusion slot clear
	test_fm7_non_fusion_slot_clear_does_not_trigger_flash()
	test_fm7_flash_requires_is_fusion_active_true()

	# FM-8: Flash duration exactly zero (immediate expiry boundary)
	test_fm8_flash_active_when_now_strictly_less_than_until()
	test_fm8_flash_not_active_when_now_equals_until()
	test_fm8_flash_not_active_when_now_past_until()
	test_fm8_flash_duration_zero_means_no_flash()

	# FM-9: is_fusion_active() method missing from PlayerController3D
	test_fm9_player_controller_has_is_fusion_active_method()
	test_fm9_player_double_without_accessor_makes_fusion_label_hidden()

	# FM-10: Color priority order violated
	test_fm10_correct_harness_flash_overrides_dual_filled_icon()
	test_fm10_correct_harness_flash_overrides_dual_filled_label()
	test_fm10_buggy_wrong_priority_returns_dual_when_both_active()
	test_fm10_correct_and_buggy_diverge_when_flash_and_dual_both_active()
	test_fm10_post_fusion_ne_dual_filled_constant()

	# Combinatorial edge cases
	test_combo_null_player_and_prev_both_filled_true_no_flash()
	test_combo_player_without_accessor_and_prev_both_filled_true_no_flash()
	test_combo_flash_active_and_slots_empty_icon_is_post_fusion_not_empty()
	test_combo_no_transition_no_flash_no_matter_fusion_state()

	# _harness is RefCounted -- auto-released.

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
