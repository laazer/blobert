# logging.gd
#
# Common logging utility for consistent output with caller context.
# Use Logging.log(message) instead of print() for traceable logs.

class_name Logging

static func log(message: String) -> void:
	var stack = get_stack()
	if stack.size() > 1:
		var caller = stack[1]
		var file_name = caller.file.get_file()  # Get just the filename
		print("[%s:%d] %s" % [file_name, caller.line, message])
	else:
		print("[unknown] %s" % message)

static func debug(message: String) -> void:
	log("DEBUG: " + message)

static func info(message: String) -> void:
	log("INFO: " + message)

static func warn(message: String) -> void:
	log("WARN: " + message)

static func error(message: String) -> void:
	log("ERROR: " + message)