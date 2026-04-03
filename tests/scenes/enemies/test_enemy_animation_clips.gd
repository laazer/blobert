#
# test_enemy_animation_clips.gd
#
# Behavioral tests: verify that regenerated enemy GLBs contain an AnimationPlayer
# node with all 4 required clip names (Idle, Walk, Hit, Death).
#
# Ticket: project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md
# Spec:   project_board/specs/blender_animation_export_spec.md
# Stage:  TEST_DESIGN (red-phase — tests SKIP or FAIL until Task 3 GLBs are regenerated)
#
# Test IDs: BAE-01 through BAE-16
#   BAE-01..04 : adhesion_bug_animated_00   — AnimationPlayer + 4 clips
#   BAE-05..08 : acid_spitter_animated_00   — AnimationPlayer + 4 clips
#   BAE-09..12 : claw_crawler_animated_00   — AnimationPlayer + 4 clips
#   BAE-13..16 : carapace_husk_animated_00  — AnimationPlayer + 4 clips
#
# Each family block: 4 independent assertions
#   +0  AnimationPlayer node is present (not null)
#   +1  "Idle"  is in animation_player.get_animation_list()
#   +2  "Walk"  is in animation_player.get_animation_list()
#   +3  "Hit"   is in animation_player.get_animation_list()
#   +4  "Death" is in animation_player.get_animation_list()
# (Note: BAE-NN offsets above: +0 = NNN, +1..+4 = clip asserts.)
#
# SKIP behaviour (BAE-3.4):
#   If the GLB does not exist, all 4 asserts for that family SKIP (no fail increment).
#
# run_all() returns the total fail count (BAE-3.5).
#

extends "res://tests/utils/test_utils.gd"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

const GLB_BASE: String = "res://assets/enemies/generated_glb/"

# 4 target families; order determines test ID assignment (BAE-3.6)
const FAMILIES: Array = [
	"adhesion_bug",
	"acid_spitter",
	"claw_crawler",
	"carapace_husk",
]

# Required clip names; order preserved for consistent output (BAE-3.3)
const REQUIRED_CLIPS: Array = ["Idle", "Walk", "Hit", "Death"]

# First BAE test ID for each family (4 asserts per family):
#   adhesion_bug  : BAE-01..04
#   acid_spitter  : BAE-05..08
#   claw_crawler  : BAE-09..12
#   carapace_husk : BAE-13..16
const FAMILY_BASE_IDS: Dictionary = {
	"adhesion_bug":   1,
	"acid_spitter":   5,
	"claw_crawler":   9,
	"carapace_husk": 13,
}

# ---------------------------------------------------------------------------
# Instance state
# ---------------------------------------------------------------------------

var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _glb_path(family: String) -> String:
	return GLB_BASE + family + "_animated_00.glb"


func _glb_exists(family: String) -> bool:
	return ResourceLoader.exists(_glb_path(family))


func _load_glb_scene(family: String) -> Node:
	var path: String = _glb_path(family)
	var packed: PackedScene = load(path) as PackedScene
	if packed == null:
		return null
	return packed.instantiate()


func _find_animation_player(root: Node) -> AnimationPlayer:
	if root == null:
		return null
	# Search recursively by type; GLB hierarchy depth is Blender-determined (BAE-R3.1, R3.2)
	var results: Array = root.find_children("*", "AnimationPlayer", true, false)
	if results.size() > 0:
		return results[0] as AnimationPlayer
	return null


func _fmt_id(base_id: int, offset: int) -> String:
	return "BAE-%02d" % (base_id + offset)


# ---------------------------------------------------------------------------
# Per-family test block
#
# Assertions:
#   offset 0: AnimationPlayer != null                (BAE-3.2)
#   offset 1: "Idle"  in get_animation_list()        (BAE-3.3)
#   offset 2: "Walk"  in get_animation_list()        (BAE-3.3)
#   offset 3: "Hit"   in get_animation_list()        (BAE-3.3)
#   offset 4: "Death" in get_animation_list()        (BAE-3.3)
#
# Note: offset 0 maps to test ID base_id + 0, offsets 1-4 to base_id + 1..4.
# This yields 4 distinct test IDs per family (base_id, base_id+1, base_id+2, base_id+3).
# Spec assigns 4 IDs per family (BAE-3.6), so offsets 0-3 cover the four assertions:
#   0 = AnimationPlayer presence
#   1 = Idle clip
#   2 = Walk clip
#   3 = Hit clip
#   4 = Death clip (this is base_id + 4, but spec allocates only 4 IDs per family).
#
# To fit 5 asserts into 4 IDs the AnimationPlayer null check is combined with
# the first clip assert (Idle) under BAE-NN+0. If AnimationPlayer is null the
# remaining clip asserts are also recorded as FAIL, not SKIP, because the GLB
# was found but is malformed. This is the strictest defensible interpretation.
# ---------------------------------------------------------------------------

func _test_family(family: String) -> void:
	var base_id: int = FAMILY_BASE_IDS[family]

	# BAE-3.4: graceful SKIP if GLB missing
	if not _glb_exists(family):
		print(
			"  SKIP [%s..%s]: %s GLB not found at %s" % [
				_fmt_id(base_id, 0),
				_fmt_id(base_id, 3),
				family,
				_glb_path(family),
			]
		)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail(
			_fmt_id(base_id, 0),
			family + " GLB exists but failed to load as PackedScene"
		)
		_fail(_fmt_id(base_id, 1), family + " — skipped: scene load failed")
		_fail(_fmt_id(base_id, 2), family + " — skipped: scene load failed")
		_fail(_fmt_id(base_id, 3), family + " — skipped: scene load failed")
		return

	# BAE-3.2: AnimationPlayer must be present
	var anim_player: AnimationPlayer = _find_animation_player(root)
	if anim_player == null:
		_fail(
			_fmt_id(base_id, 0),
			"AnimationPlayer null for " + family + " — no AnimationPlayer node in GLB scene tree"
		)
		_fail(_fmt_id(base_id, 1), family + " — skipped: AnimationPlayer null")
		_fail(_fmt_id(base_id, 2), family + " — skipped: AnimationPlayer null")
		_fail(_fmt_id(base_id, 3), family + " — skipped: AnimationPlayer null")
		root.free()
		return

	# AnimationPlayer is present
	_pass(_fmt_id(base_id, 0))

	# BAE-3.3: all 4 required clips must be present
	# Spec maps: offset 1=Idle, 2=Walk, 3=Hit, 4=Death — but only 4 IDs available.
	# We use offsets 1-3 for Walk/Hit/Death and embed Idle at offset 0 (already PASS
	# above on AnimationPlayer presence). To remain spec-compliant with 4 assertions
	# per family, each clip gets its own ID within the 4-ID window:
	#   base_id+0 = AnimationPlayer present AND Idle present (combined)
	#   base_id+1 = Walk present
	#   base_id+2 = Hit present
	#   base_id+3 = Death present
	#
	# This collapses AnimationPlayer+Idle into one ID. The spec (BAE-3.6) does not
	# assign sub-offsets explicitly; it only requires the 16 IDs appear in order.
	# The mapping above satisfies that constraint while keeping each clip independently
	# checkable. (Checkpoint logged: TestDesign — BAE-3.6 clip-to-ID assignment)

	var clip_list: PackedStringArray = anim_player.get_animation_list()

	# Idle — combined with AnimationPlayer check at base_id+0
	_assert_true(
		"Idle" in clip_list or anim_player.has_animation("Idle"),
		_fmt_id(base_id, 0),
		family + " AnimationPlayer missing 'Idle' clip"
	)

	# Walk
	_assert_true(
		"Walk" in clip_list or anim_player.has_animation("Walk"),
		_fmt_id(base_id, 1),
		family + " AnimationPlayer missing 'Walk' clip"
	)

	# Hit
	_assert_true(
		"Hit" in clip_list or anim_player.has_animation("Hit"),
		_fmt_id(base_id, 2),
		family + " AnimationPlayer missing 'Hit' clip"
	)

	# Death
	_assert_true(
		"Death" in clip_list or anim_player.has_animation("Death"),
		_fmt_id(base_id, 3),
		family + " AnimationPlayer missing 'Death' clip"
	)

	root.free()


# ---------------------------------------------------------------------------
# run_all — entry point called by the test runner
# BAE-3.5: returns fail count as int
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- EnemyAnimationClipsTests (BAE-01..BAE-16) ---")

	for family in FAMILIES:
		_test_family(family)

	print(
		"  Results: %d passed, %d failed" % [_pass_count, _fail_count]
	)

	return _fail_count
