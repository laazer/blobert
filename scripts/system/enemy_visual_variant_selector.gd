extends RefCounted
class_name EnemyVisualVariantSelector


func resolve_spawn_visual_variant(family: String, manifest: Dictionary, rng: Variant = null) -> Dictionary:
	if family.is_empty():
		return _fail("family is required")
	if not manifest.has("enemies"):
		return _fail("manifest missing enemies map")
	var enemies_variant: Variant = manifest.get("enemies")
	if not (enemies_variant is Dictionary):
		return _fail("manifest enemies must be a dictionary")
	var enemies: Dictionary = enemies_variant as Dictionary
	if not enemies.has(family):
		return _fail("family not found in manifest: %s" % family)
	var family_entry_variant: Variant = enemies.get(family)
	if not (family_entry_variant is Dictionary):
		return _fail("family entry must be a dictionary")
	var family_entry: Dictionary = family_entry_variant as Dictionary
	if not family_entry.has("versions"):
		return _fail("family entry missing versions list")
	var versions_variant: Variant = family_entry.get("versions")
	if not (versions_variant is Array):
		return _fail("versions must be an array")
	var versions: Array = versions_variant as Array

	var eligible: Array[Dictionary] = []
	var id_to_path: Dictionary = {}
	for raw in versions:
		if not (raw is Dictionary):
			return _fail("version entry must be a dictionary")
		var version: Dictionary = raw as Dictionary
		var validation_error: String = _validate_version_record(version)
		if not validation_error.is_empty():
			return _fail(validation_error)
		var version_id: String = version.get("id")
		var version_path: String = version.get("path")
		if id_to_path.has(version_id):
			var existing_path: String = str(id_to_path.get(version_id, ""))
			if existing_path != version_path:
				return _fail("duplicate variant id with conflicting path: %s" % version_id)
			return _fail("duplicate variant id detected: %s" % version_id)
		id_to_path[version_id] = version_path
		if bool(version.get("in_use")) and not bool(version.get("draft")):
			eligible.append(version)

	if eligible.is_empty():
		return _fail("no eligible in-use non-draft variants for family: %s" % family)
	if eligible.size() == 1:
		var selected_only: Dictionary = eligible[0]
		return _success(str(selected_only.get("id", "")), str(selected_only.get("path", "")))

	var idx: int = _pick_index(eligible.size(), rng)
	var selected: Dictionary = eligible[idx]
	return _success(str(selected.get("id", "")), str(selected.get("path", "")))


func _validate_version_record(version: Dictionary) -> String:
	if not version.has("id"):
		return "version entry missing id"
	if not version.has("path"):
		return "version entry missing path"
	if not version.has("draft"):
		return "version entry missing draft"
	if not version.has("in_use"):
		return "version entry missing in_use"

	var id_variant: Variant = version.get("id")
	var path_variant: Variant = version.get("path")
	var draft_variant: Variant = version.get("draft")
	var in_use_variant: Variant = version.get("in_use")
	if not (id_variant is String) or str(id_variant).is_empty():
		return "version id must be a non-empty string"
	if not (path_variant is String) or str(path_variant).is_empty():
		return "version path must be a non-empty string"
	if not (draft_variant is bool):
		return "version draft must be bool"
	if not (in_use_variant is bool):
		return "version in_use must be bool"
	return ""


func _pick_index(size: int, rng: Variant) -> int:
	if size <= 1:
		return 0
	if rng != null and rng.has_method("randi_range"):
		var picked: int = int(rng.call("randi_range", 0, size - 1))
		return clampi(picked, 0, size - 1)
	var fallback_rng := RandomNumberGenerator.new()
	fallback_rng.randomize()
	return fallback_rng.randi_range(0, size - 1)


func _success(variant_id: String, path: String) -> Dictionary:
	return {"ok": true, "variant_id": variant_id, "path": path}


func _fail(error_message: String) -> Dictionary:
	return {"ok": false, "error": error_message, "path": ""}
