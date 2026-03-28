# test_logging.gd
#
# Tests for the common logging utility.
#

class_name LoggingTests
extends "res://tests/utils/test_utils.gd"

var _pass_count: int = 0
var _fail_count: int = 0
var _logging_class = load("res://scripts/system/logging.gd")

func test_logging_trace_function_exists() -> void:
	_assert_true(_logging_class.has_method("trace"), "logging_trace_function_exists")

func test_logging_debug_function_exists() -> void:
	_assert_true(_logging_class.has_method("debug"), "logging_debug_function_exists")

func test_logging_info_function_exists() -> void:
	_assert_true(_logging_class.has_method("info"), "logging_info_function_exists")

func test_logging_warn_function_exists() -> void:
	_assert_true(_logging_class.has_method("warn"), "logging_warn_function_exists")

func test_logging_error_function_exists() -> void:
	_assert_true(_logging_class.has_method("error"), "logging_error_function_exists")

func test_logging_trace_can_be_called() -> void:
	# Test that calling trace doesn't crash
	_logging_class.trace("test trace message")
	_pass("logging_trace_can_be_called")

func test_logging_debug_can_be_called() -> void:
	_logging_class.debug("test debug message")
	_pass("logging_debug_can_be_called")

func test_logging_info_can_be_called() -> void:
	_logging_class.info("test info message")
	_pass("logging_info_can_be_called")

func test_logging_warn_can_be_called() -> void:
	_logging_class.warn("test warn message")
	_pass("logging_warn_can_be_called")

func test_logging_error_can_be_called() -> void:
	_logging_class.error("test error message")
	_pass("logging_error_can_be_called")

func run_all() -> int:
	print("--- test_logging.gd ---")
	_pass_count = 0
	_fail_count = 0

	test_logging_trace_function_exists()
	test_logging_debug_function_exists()
	test_logging_info_function_exists()
	test_logging_warn_function_exists()
	test_logging_error_function_exists()

	test_logging_trace_can_be_called()
	test_logging_debug_can_be_called()
	test_logging_info_can_be_called()
	test_logging_warn_can_be_called()
	test_logging_error_can_be_called()

	print("")
	print("  Results: " + str(_pass_count) + " passed, " + str(_fail_count) + " failed")
	return _fail_count