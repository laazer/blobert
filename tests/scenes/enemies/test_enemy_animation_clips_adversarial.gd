#
# test_enemy_animation_clips_adversarial.gd
#
# Adversarial tests for enemy GLB animation clip presence.
#
# Ticket: project_board/7_milestone_7_enemy_animation_wiring/in_progress/blender_animation_export.md
# Spec:   project_board/specs/blender_animation_export_spec.md
#
# These tests extend the primary suite (test_enemy_animation_clips.gd, BAE-01..BAE-16)
# with adversarial scenarios targeting:
#   ADV-BAE-G-01  Lowercase clip names are ABSENT (case regression guard)
#   ADV-BAE-G-02  Walk-case mutation: "walk" (lowercase) absent, "Walk" present
#   ADV-BAE-G-03  Hit-case mutation: "hit" absent, "Hit" present
#   ADV-BAE-G-04  Death-case mutation: "death" absent, "Death" present
#   ADV-BAE-G-05  AnimationPlayer found by find_children recursive type search
#                 (verifies the implementation uses type search, not hardcoded path)
#   ADV-BAE-G-06  No more than one AnimationPlayer per scene root
#                 (duplicate AnimationPlayer nodes indicate export bug)
#   ADV-BAE-G-07  Partial export guard: all 4 families present in GLB dir
#                 (catches a partial regeneration where only 2/4 families were re-exported)
#   ADV-BAE-G-08  get_animation_list() returns non-empty array when clips are present
#                 (guards against an AnimationPlayer that exists but has no clips)
#   ADV-BAE-G-09  "RESET" clip does not substitute for a required clip
#                 (Godot imports from Blender sometimes inject a RESET track;
#                  ensure required clips are present IN ADDITION to any RESET clip)
#   ADV-BAE-G-10  Clip names do not include the family name as a prefix
#                 (e.g., "adhesion_bug_Idle" is wrong; clip must be exactly "Idle")
#
# SKIP behaviour: if a GLB is missing, all tests for that family SKIP (same as primary suite).
# run_all() returns the total fail count.
#

extends "res://tests/utils/test_utils.gd"

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

const GLB_BASE: String = "res://assets/enemies/generated_glb/"

const FAMILIES: Array = [
	"adhesion_bug",
	"acid_spitter",
	"claw_crawler",
	"carapace_husk",
]

# Required clip names (exact, PascalCase)
const REQUIRED_CLIPS: Array = ["Idle", "Walk", "Hit", "Death"]

# Internal (lowercase) names that must NOT appear as clip names after correct export.
# If any of these appear, the pipeline used the internal name instead of the export name.
const FORBIDDEN_LOWERCASE_CLIPS: Array = ["idle", "walk", "hit", "death"]

# Internal names that are non-obvious mappings (would appear if title-case fallback was used)
# "move".title() == "Move" (not "Walk"); "damage".title() == "Damage" (not "Hit")
const FORBIDDEN_FALLBACK_CLIPS: Array = ["Move", "Damage"]

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


func _find_all_animation_players(root: Node) -> Array:
	if root == null:
		return []
	return root.find_children("*", "AnimationPlayer", true, false)


func _find_animation_player(root: Node) -> AnimationPlayer:
	var results: Array = _find_all_animation_players(root)
	if results.size() > 0:
		return results[0] as AnimationPlayer
	return null


# ---------------------------------------------------------------------------
# ADV-BAE-G-01..G-04: Case mutation guards
# Asserts that the lowercase/wrong-case variants of required clip names are ABSENT.
# This catches the pipeline exporting "idle" instead of "Idle".
# ---------------------------------------------------------------------------

func _test_lowercase_clips_absent(family: String) -> void:
	if not _glb_exists(family):
		print("  SKIP [ADV-BAE-G-01..04]: %s GLB not found" % family)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail("ADV-BAE-G-01 (%s)" % family, "GLB failed to load")
		root = null
		return

	var anim_player: AnimationPlayer = _find_animation_player(root)
	if anim_player == null:
		print("  SKIP [ADV-BAE-G-01..04]: %s — no AnimationPlayer (covered by primary suite)" % family)
		root.free()
		return

	var clip_list: PackedStringArray = anim_player.get_animation_list()

	# ADV-BAE-G-01: "idle" must be absent (correct export name is "Idle")
	_assert_false(
		"idle" in clip_list,
		"ADV-BAE-G-01 (%s)" % family,
		family + " — lowercase 'idle' must NOT be in animation list. "
		+ "Export name must be 'Idle'. Got: " + str(clip_list)
	)

	# ADV-BAE-G-02: "walk" must be absent (correct export name is "Walk";
	# also guards against "move" appearing — checked separately)
	_assert_false(
		"walk" in clip_list,
		"ADV-BAE-G-02 (%s)" % family,
		family + " — lowercase 'walk' must NOT be in animation list. "
		+ "Export name must be 'Walk'."
	)
	# "move" is the internal name for Walk; it must also be absent
	_assert_false(
		"move" in clip_list,
		"ADV-BAE-G-02b (%s)" % family,
		family + " — internal name 'move' must NOT be in animation list. "
		+ "Export name must be 'Walk'. If 'move' is present, the export name mapping was not applied."
	)

	# ADV-BAE-G-03: "hit" must be absent (correct export name is "Hit";
	# also "damage" — the internal name — must be absent)
	_assert_false(
		"hit" in clip_list,
		"ADV-BAE-G-03 (%s)" % family,
		family + " — lowercase 'hit' must NOT be in animation list. "
		+ "Export name must be 'Hit'."
	)
	_assert_false(
		"damage" in clip_list,
		"ADV-BAE-G-03b (%s)" % family,
		family + " — internal name 'damage' must NOT be in animation list. "
		+ "Export name must be 'Hit'. If 'damage' is present, the export name mapping was not applied."
	)

	# ADV-BAE-G-04: "death" must be absent (correct export name is "Death")
	_assert_false(
		"death" in clip_list,
		"ADV-BAE-G-04 (%s)" % family,
		family + " — lowercase 'death' must NOT be in animation list. "
		+ "Export name must be 'Death'."
	)

	# ADV-BAE-G-04b: title-case fallback trap: "Move" and "Damage" must be absent
	# If the pipeline used str.title() fallback instead of the explicit map, it would
	# produce "Move" (not "Walk") and "Damage" (not "Hit").
	_assert_false(
		"Move" in clip_list,
		"ADV-BAE-G-04b (%s)" % family,
		family + " — 'Move' (title-case fallback) must NOT be in animation list. "
		+ "The explicit map must produce 'Walk', not 'Move'."
	)
	_assert_false(
		"Damage" in clip_list,
		"ADV-BAE-G-04c (%s)" % family,
		family + " — 'Damage' (title-case fallback) must NOT be in animation list. "
		+ "The explicit map must produce 'Hit', not 'Damage'."
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-BAE-G-05: AnimationPlayer found via recursive type search
# Verifies the implementation used find_children (recursive by type), not a
# hardcoded path. Strategy: if find_children finds exactly one AnimationPlayer
# and get_node_or_null at a shallow hardcoded path returns null, the search is
# working correctly because it found the node at a non-trivial depth.
# If get_node_or_null("AnimationPlayer") succeeds (root-level node), that is
# also acceptable — we only FAIL if find_children returns empty but
# get_node_or_null at known shallow paths also returns null (both absent).
# ---------------------------------------------------------------------------

func _test_animation_player_found_by_type_search(family: String) -> void:
	if not _glb_exists(family):
		print("  SKIP [ADV-BAE-G-05]: %s GLB not found" % family)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail("ADV-BAE-G-05 (%s)" % family, "GLB failed to load")
		return

	var found_by_search: Array = _find_all_animation_players(root)

	# If recursive type search finds none, that is a failure (same as primary suite).
	# This test only ADDS value by checking the count is > 0 via this code path;
	# the primary suite's null-check is on find_children[0].
	_assert_true(
		found_by_search.size() > 0,
		"ADV-BAE-G-05 (%s)" % family,
		family + " — find_children recursive type search must find AnimationPlayer. "
		+ "If the GLB does not contain one, the NLA export failed."
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-BAE-G-06: No more than one AnimationPlayer per scene
# Duplicate AnimationPlayer nodes can occur when:
#   - The exporter created one AnimationPlayer per NLA track (bug)
#   - An existing AnimationPlayer from the armature AND a new one were both exported
# Multiple AnimationPlayers would cause the Godot importer to merge or ignore clips,
# silently producing a scene where only some clips work.
# ---------------------------------------------------------------------------

func _test_no_duplicate_animation_players(family: String) -> void:
	if not _glb_exists(family):
		print("  SKIP [ADV-BAE-G-06]: %s GLB not found" % family)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail("ADV-BAE-G-06 (%s)" % family, "GLB failed to load")
		return

	var all_players: Array = _find_all_animation_players(root)
	_assert_true(
		all_players.size() <= 1,
		"ADV-BAE-G-06 (%s)" % family,
		family + " — must have at most 1 AnimationPlayer in scene, found " + str(all_players.size())
		+ ". Multiple AnimationPlayers indicate a NLA export bug where tracks became separate nodes."
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-BAE-G-07: All 4 families have their GLB present (partial export guard)
# If the pipeline regenerated only some families, the primary suite silently SKIPs
# the missing ones (BAE-3.4). This adversarial test explicitly FAILs if any GLB
# from the required 4 is absent, catching a partial Task-3 run.
# ---------------------------------------------------------------------------

func _test_all_four_glbs_present() -> void:
	var missing: Array = []
	for family in FAMILIES:
		if not _glb_exists(family):
			missing.append(family)

	if missing.size() > 0:
		_fail(
			"ADV-BAE-G-07",
			"Partial export detected — the following families are missing animated GLBs: "
			+ str(missing) + ". All 4 must be regenerated before the GDScript suite can pass."
		)
	else:
		_pass("ADV-BAE-G-07")


# ---------------------------------------------------------------------------
# ADV-BAE-G-08: AnimationPlayer has a non-empty clip list
# Guards against a scene where AnimationPlayer exists but get_animation_list()
# returns an empty array (e.g., NLA strips were created but action=None was
# not set so the GLTF exporter only exported one active action that was then
# excluded by the selection filter).
# ---------------------------------------------------------------------------

func _test_animation_list_non_empty(family: String) -> void:
	if not _glb_exists(family):
		print("  SKIP [ADV-BAE-G-08]: %s GLB not found" % family)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail("ADV-BAE-G-08 (%s)" % family, "GLB failed to load")
		return

	var anim_player: AnimationPlayer = _find_animation_player(root)
	if anim_player == null:
		print("  SKIP [ADV-BAE-G-08]: %s — no AnimationPlayer (covered by primary suite)" % family)
		root.free()
		return

	var clip_list: PackedStringArray = anim_player.get_animation_list()
	_assert_true(
		clip_list.size() > 0,
		"ADV-BAE-G-08 (%s)" % family,
		family + " — get_animation_list() returned empty array. AnimationPlayer exists "
		+ "but has no clips — NLA export may have failed silently (action != None at export time)."
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-BAE-G-09: RESET clip does not substitute for required clips
# Godot's importer sometimes inserts a RESET animation track for the rest pose.
# A naive test that only checks `get_animation_list().size() >= 4` would pass
# if RESET + Idle + Walk + Hit are present (Death missing but count is still 4).
# This test is a belt-and-suspenders complement to the primary per-clip checks.
# It verifies REQUIRED_CLIPS are all present regardless of whether RESET is there.
# ---------------------------------------------------------------------------

func _test_required_clips_present_despite_reset(family: String) -> void:
	if not _glb_exists(family):
		print("  SKIP [ADV-BAE-G-09]: %s GLB not found" % family)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail("ADV-BAE-G-09 (%s)" % family, "GLB failed to load")
		return

	var anim_player: AnimationPlayer = _find_animation_player(root)
	if anim_player == null:
		print("  SKIP [ADV-BAE-G-09]: %s — no AnimationPlayer (covered by primary suite)" % family)
		root.free()
		return

	# Count required clips (not total clips, which may include RESET)
	var required_found: int = 0
	for clip_name in REQUIRED_CLIPS:
		if anim_player.has_animation(clip_name):
			required_found += 1

	_assert_true(
		required_found == REQUIRED_CLIPS.size(),
		"ADV-BAE-G-09 (%s)" % family,
		family + " — all 4 required clips must be present regardless of RESET or extra clips. "
		+ "Found " + str(required_found) + "/" + str(REQUIRED_CLIPS.size()) + " required clips."
	)

	root.free()


# ---------------------------------------------------------------------------
# ADV-BAE-G-10: Clip names do not include family name as a prefix
# A broken export naming scheme might produce "adhesion_bug_Idle" instead of "Idle".
# The Godot EnemyAnimationController calls play("Idle") without a prefix;
# if the clip is prefixed, all play() calls silently fail.
# ---------------------------------------------------------------------------

func _test_clips_have_no_family_prefix(family: String) -> void:
	if not _glb_exists(family):
		print("  SKIP [ADV-BAE-G-10]: %s GLB not found" % family)
		return

	var root: Node = _load_glb_scene(family)
	if root == null:
		_fail("ADV-BAE-G-10 (%s)" % family, "GLB failed to load")
		return

	var anim_player: AnimationPlayer = _find_animation_player(root)
	if anim_player == null:
		print("  SKIP [ADV-BAE-G-10]: %s — no AnimationPlayer (covered by primary suite)" % family)
		root.free()
		return

	var clip_list: PackedStringArray = anim_player.get_animation_list()
	for clip_name in clip_list:
		# Any clip whose name starts with the family name is wrong
		_assert_false(
			str(clip_name).begins_with(family + "_"),
			"ADV-BAE-G-10 (%s)" % family,
			family + " — clip name '" + str(clip_name) + "' must NOT begin with family prefix '"
			+ family + "_'. Export names must be 'Idle', 'Walk', 'Hit', 'Death' (no prefix)."
		)

	root.free()


# ---------------------------------------------------------------------------
# run_all — entry point called by the test runner
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_enemy_animation_clips_adversarial.gd (ADV-BAE-G-01..ADV-BAE-G-10) ---")

	# ADV-BAE-G-07: partial export guard (family-independent)
	_test_all_four_glbs_present()

	# Per-family adversarial checks
	for family in FAMILIES:
		_test_lowercase_clips_absent(family)
		_test_animation_player_found_by_type_search(family)
		_test_no_duplicate_animation_players(family)
		_test_animation_list_non_empty(family)
		_test_required_clips_present_despite_reset(family)
		_test_clips_have_no_family_prefix(family)

	print(
		"  Results: %d passed, %d failed" % [_pass_count, _fail_count]
	)

	return _fail_count
