# enemy_root_script_resolver.gd
#
# Single source of truth for which root script path to attach to generated enemy scenes.
# REQ-ESEG-1 / REQ-ESEG-2 — see project_board/maintenance/in_progress/enemy_script_extension_and_scene_generator.md
extends RefCounted

const EnemyNameUtils = preload("res://scripts/asset_generation/enemy_name_utils.gd")

const BASE_ENEMY_SCRIPT_PATH := "res://scripts/enemies/enemy_base.gd"
const GENERATED_ENEMY_SCRIPT_DIR := "res://scripts/enemies/generated/"


func _is_glb_basename_style(file_stem: String) -> bool:
	var parts := file_stem.split("_")
	if not parts.is_empty() and parts[-1].is_valid_int():
		return true
	for p in parts:
		if p == "animated":
			return true
	return false


func _stem_is_safe_for_override_file(stem: String) -> bool:
	if stem.is_empty():
		return false
	if stem.contains("..") or stem.contains("/") or stem.contains("\\"):
		return false
	return true


func resolve_enemy_root_script_path(family_name: String) -> String:
	var stem := family_name
	if _is_glb_basename_style(family_name):
		stem = EnemyNameUtils.extract_family_name(family_name)
	if not _stem_is_safe_for_override_file(stem):
		return BASE_ENEMY_SCRIPT_PATH
	var override_path := "%s%s.gd" % [GENERATED_ENEMY_SCRIPT_DIR, stem]
	if ResourceLoader.exists(override_path):
		return override_path
	return BASE_ENEMY_SCRIPT_PATH
