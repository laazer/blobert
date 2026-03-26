#
# test_player_controller_preload_path.gd
#
# Regression test for bug: missing movement_simulation.gd script path.
# Ticket: project_board/bugfix/in_progress/missing-movement-simulation-path.md
#
# Test IDs covered:
#   BUG-MMSP-01
#
# Spec references:
#   Requirement BUG-MMSP-2: Regression test for correct preload path
#   AC-1: load() returns non-null
#   AC-2: source_code contains "res://scripts/movement/movement_simulation.gd"
#   AC-3: source_code does NOT contain "res://scripts/movement_simulation.gd"
#   AC-4: gracefully skips if source_code is empty (exported build)
#
# Expected pass/fail state at time of writing:
#   Against HEAD (committed, wrong path): BUG-MMSP-01 sub-assertions AC-2 and
#   AC-3 FAIL (red phase). This is intentional — the test is a regression guard.
#   Against the working-tree fix (correct path, once committed): all assertions
#   PASS (green).
#

extends Object


var _pass_count: int = 0
var _fail_count: int = 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)


func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)


# ---------------------------------------------------------------------------
# BUG-MMSP-01
# Spec: BUG-MMSP-2, AC-1 through AC-4
# Purpose: Verify that player_controller_3d.gd preloads MovementSimulation
#          using the correct path (with "movement/" subdirectory), and that
#          the wrong path (without subdirectory) is absent from source.
#          This test would have caught the original bug.
# Input: load("res://scripts/player/player_controller_3d.gd")
# Assertions:
#   AC-1: Returned GDScript is non-null (file exists and parses without error).
#   AC-2: source_code contains "res://scripts/movement/movement_simulation.gd".
#   AC-3: source_code does NOT contain "res://scripts/movement_simulation.gd"
#         (the bad path, missing the "movement/" subdirectory).
#   AC-4: If source_code is empty (exported/stripped build), print SKIP and
#         return zero failures — do not falsely fail.
# Edge: The test uses load(), not preload(), so that a future recurrence of the
#       wrong path would produce a null return (load failure) rather than a
#       parse-time error that crashes the test runner itself.
# ---------------------------------------------------------------------------

func test_bug_mmsp_01_player_controller_has_correct_preload_path() -> void:
	# AC-1: File must load without error.
	var script: GDScript = load("res://scripts/player/player_controller_3d.gd") as GDScript
	if script == null:
		_fail(
			"BUG-MMSP-01 AC-1",
			"load('res://scripts/player/player_controller_3d.gd') returned null; "
			+ "file missing or parse error (wrong preload path may have caused this)"
		)
		return

	_pass("BUG-MMSP-01 AC-1 — player_controller_3d.gd loads non-null")

	var src: String = script.source_code

	# AC-4: Graceful skip in exported builds where source is stripped.
	if src == "":
		print("  SKIP: BUG-MMSP-01 AC-2/AC-3 — source_code empty (exported/stripped build); "
			+ "path assertions inconclusive")
		return

	# AC-2: Correct path must be present.
	if src.contains("res://scripts/movement/movement_simulation.gd"):
		_pass("BUG-MMSP-01 AC-2 — correct path 'res://scripts/movement/movement_simulation.gd' "
			+ "is present in player_controller_3d.gd")
	else:
		_fail(
			"BUG-MMSP-01 AC-2",
			"expected 'res://scripts/movement/movement_simulation.gd' in source_code but it is absent"
		)

	# AC-3: Wrong path must be absent. This is the direct regression assertion.
	# The bad path "res://scripts/movement_simulation.gd" omits the "movement/" subdirectory.
	# Note: the contains() check for the bad path must not accidentally match the
	# correct path. The bad path ends with ".gd" and lacks the intermediate "movement/"
	# segment, so a simple contains() is safe here — the correct path always contains
	# "movement/movement_simulation.gd" while the bad path is "movement_simulation.gd"
	# at the scripts/ level.
	if src.contains("res://scripts/movement_simulation.gd"):
		_fail(
			"BUG-MMSP-01 AC-3",
			"bad path 'res://scripts/movement_simulation.gd' (missing 'movement/' subdirectory) "
			+ "is present in player_controller_3d.gd — regression detected"
		)
	else:
		_pass("BUG-MMSP-01 AC-3 — bad path 'res://scripts/movement_simulation.gd' "
			+ "is absent from player_controller_3d.gd")


# ---------------------------------------------------------------------------
# Public entry point (required by run_tests.gd auto-discovery)
# ---------------------------------------------------------------------------

func run_all() -> int:
	print("--- test_player_controller_preload_path.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_bug_mmsp_01_player_controller_has_correct_preload_path()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count
