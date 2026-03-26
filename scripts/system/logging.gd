# logging.gd
#
# Common logging utility for consistent output with caller context.
# Use Logging.trace(message) instead of print() for traceable logs.

extends Node

var _dummy = 0  # Ensure the script can be instantiated for autoload

static func _log(message: String, depth: int) -> void:
	var stack = get_stack()
	if stack.size() > depth:
		var caller = stack[depth]
		var file_name = "unknown"
		var line = -1
		if caller.has("source") and caller["source"] is String:
			file_name = caller["source"].get_file()
		if caller.has("line"):
			line = caller.line
		print("[%s:%d] %s" % [file_name, line, message])
	else:
		print("[unknown] %s" % message)

static func trace(message: String) -> void:
	_log(message, 1)

static func debug(message: String) -> void:
	_log("DEBUG: " + message, 2)

static func info(message: String) -> void:
	_log("INFO: " + message, 2)

static func warn(message: String) -> void:
	_log("WARN: " + message, 2)

static func error(message: String) -> void:
	_log("ERROR: " + message, 2)