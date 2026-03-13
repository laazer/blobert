# logging.gd
#
# Common logging utility for consistent output with caller context.
# Use Logging.trace(message) instead of print() for traceable logs.

extends Node

var _dummy = 0  # Ensure the script can be instantiated for autoload

static func trace(message: String) -> void:
	var stack = get_stack()
	if stack.size() > 1:
		var caller = stack[1]
		var file_name = "unknown"
		var line = -1
		if caller.has("file") and caller.file is String:
			file_name = caller.file.get_file()
		if caller.has("line"):
			line = caller.line
		print("[%s:%d] %s" % [file_name, line, message])
	else:
		print("[unknown] %s" % message)

static func debug(message: String) -> void:
	trace("DEBUG: " + message)

static func info(message: String) -> void:
	trace("INFO: " + message)

static func warn(message: String) -> void:
	trace("WARN: " + message)

static func error(message: String) -> void:
	trace("ERROR: " + message)
