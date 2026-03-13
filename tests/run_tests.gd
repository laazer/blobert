# run_tests.gd
#
# Top-level headless test runner for the blobert project.
#
# Usage:
#   godot --headless --path /path/to/blobert -s tests/run_tests.gd
#
# Exit codes:
#   0  — all test suites passed
#   1  — one or more tests failed
#
# Adding a new suite:
#   Create any file under tests/ whose name starts with "test_".
#   It will be discovered and run automatically.
#   The file must define "func run_all() -> int:".

extends SceneTree

# Preload so LoggingTests is registered before run_tests.gd is loaded.
const _LOGGING_TESTS: GDScript = preload("res://tests/scripts/system/test_logging.gd")


func _collect_test_files(dir_path: String, results: Array[String]) -> void:
	var dir := DirAccess.open(dir_path)
	if dir == null:
		return
	dir.list_dir_begin()
	while true:
		var entry := dir.get_next()
		if entry == "":
			break
		if dir.current_is_dir():
			if not entry.begins_with("."):
				_collect_test_files(dir_path + "/" + entry, results)
		elif entry.begins_with("test_") and entry.ends_with(".gd"):
			results.append(dir_path + "/" + entry)
	dir.list_dir_end()


func _initialize() -> void:
	print("=== blobert headless test runner ===")
	print("")

	var suites: Array[String] = []
	_collect_test_files("res://tests", suites)
	suites.sort()

	var total_failures: int = 0

	for path in suites:
		var script: GDScript = load(path)
		if script == null or not script.can_instantiate():
			push_error("RUNNER ERROR: could not load " + path)
			quit(1)
			return
		total_failures += script.new().run_all()

	print("")
	if total_failures == 0:
		print("=== ALL TESTS PASSED ===")
	else:
		print("=== FAILURES: " + str(total_failures) + " test(s) failed ===")

	quit(1 if total_failures > 0 else 0)
