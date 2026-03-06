# test_logging.gd
#
# Tests for the common logging utility.
#

class_name LoggingTests
extends Object

var _pass_count: int = 0
var _fail_count: int = 0

func _pass(test_name: String) -> void:
	_pass_count += 1
	print("  PASS: " + test_name)

func _fail(test_name: String, message: String) -> void:
	_fail_count += 1
	print("  FAIL: " + test_name + " — " + message)

func _assert_true(condition: bool, test_name: String) -> void:
	if condition:
		_pass(test_name)
	else:
		_fail(test_name, "expected true, got false")

func test_logging_log_function_exists() -> void:
	_assert_true(Logging.has_method("log"), "logging_log_function_exists")

func test_logging_debug_function_exists() -> void:
	_assert_true(Logging.has_method("debug"), "logging_debug_function_exists")

func test_logging_info_function_exists() -> void:
	_assert_true(Logging.has_method("info"), "logging_info_function_exists")

func test_logging_warn_function_exists() -> void:
	_assert_true(Logging.has_method("warn"), "logging_warn_function_exists")

func test_logging_error_function_exists() -> void:
	_assert_true(Logging.has_method("error"), "logging_error_function_exists")

func run_all() -> int:
	print("--- test_logging.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_logging_log_function_exists()
	test_logging_debug_function_exists()
	test_logging_info_function_exists()
	test_logging_warn_function_exists()
	test_logging_error_function_exists()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count