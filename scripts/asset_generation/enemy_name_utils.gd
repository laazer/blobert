class_name EnemyNameUtils
extends RefCounted


static func extract_family_name(file_name: String) -> String:
	var parts := file_name.split("_")
	# Remove trailing numeric variant index
	if parts.size() >= 2 and parts[-1].is_valid_int():
		parts.remove_at(parts.size() - 1)
	# Remove all "animated" segments (any position)
	var i := parts.size() - 1
	while i >= 0:
		if parts[i] == "animated":
			parts.remove_at(i)
		i -= 1
	return "_".join(parts)
