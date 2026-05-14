#
# test_player_export_animation_controller_clip_hint.gd
#
# Unit tests for PlayerExportAnimationController3D.clip_base_for_state().
#

extends "res://tests/utils/test_utils.gd"

const _PLAYER_EXPORT_ANIM: GDScript = preload(
	"res://scripts/player/player_export_animation_controller_3d.gd"
)

var _pass_count: int = 0
var _fail_count: int = 0


func test_clip_floor_below_threshold_is_idle() -> void:
	var got: String = _PLAYER_EXPORT_ANIM.clip_base_for_state(true, 0.05, 0.12)
	_assert_eq_string("idle", got, "floor_slow_idle")


func test_clip_floor_above_threshold_is_move() -> void:
	var got: String = _PLAYER_EXPORT_ANIM.clip_base_for_state(true, 0.2, 0.12)
	_assert_eq_string("move", got, "floor_fast_move")


func test_clip_air_is_jump() -> void:
	var got: String = _PLAYER_EXPORT_ANIM.clip_base_for_state(false, 0.0, 0.12)
	_assert_eq_string("jump", got, "air_jump")


func test_clip_floor_negative_speed_uses_abs() -> void:
	var got: String = _PLAYER_EXPORT_ANIM.clip_base_for_state(true, -0.2, 0.12)
	_assert_eq_string("move", got, "floor_neg_move")


func run_all() -> int:
	print("--- test_player_export_animation_controller_clip_hint.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_clip_floor_below_threshold_is_idle()
	test_clip_floor_above_threshold_is_move()
	test_clip_air_is_jump()
	test_clip_floor_negative_speed_uses_abs()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
