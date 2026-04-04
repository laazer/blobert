# test_enemy_damage_animation_wiring.gd
#
# Damage reaction: EnemyInfection3D.play_damage_hit_animation() → Hit clip via
# EnemyAnimationController; gameplay wiring in PlayerController3D + InfectionInteractionHandler.

class_name EnemyDamageAnimationWiringTests
extends "res://tests/utils/test_utils.gd"


var _pass_count: int = 0
var _fail_count: int = 0


func _pass(name: String) -> void:
	_pass_count += 1
	print("  PASS: ", name)


func _fail(name: String, detail: String) -> void:
	_fail_count += 1
	push_error("  FAIL: " + name + " — " + detail)


func run_all() -> int:
	print("--- test_enemy_damage_animation_wiring.gd ---")
	test_play_damage_skips_when_dead_no_crash()
	test_player_source_wires_damage_animation()
	test_handler_source_wires_damage_animation_after_infect()
	print("")
	print("  Results: ", _pass_count, " passed, ", _fail_count, " failed")
	return _fail_count


func test_play_damage_skips_when_dead_no_crash() -> void:
	const NAME := "DDA-01 — play_damage_hit_animation when dead is a no-op (no crash)"
	var packed: PackedScene = load("res://scenes/enemy/enemy_infection_3d.tscn") as PackedScene
	if packed == null:
		_fail(NAME, "load enemy_infection_3d failed")
		return
	var enemy: EnemyInfection3D = packed.instantiate() as EnemyInfection3D
	if enemy == null:
		_fail(NAME, "instantiate failed")
		return
	var st: SceneTree = Engine.get_main_loop() as SceneTree
	if st == null or st.root == null:
		enemy.free()
		_fail(NAME, "no SceneTree")
		return
	st.root.add_child(enemy)
	enemy.get_esm().apply_death_event()
	enemy.play_damage_hit_animation()
	st.root.remove_child(enemy)
	enemy.free()
	_pass(NAME)


func test_player_source_wires_damage_animation() -> void:
	const NAME := "DDA-02 — PlayerController3D calls play_damage_hit_animation on chunk path"
	var path := "res://scripts/player/player_controller_3d.gd"
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		_fail(NAME, "could not read " + path)
		return
	var src := f.get_as_text()
	if not src.contains("play_damage_hit_animation()"):
		_fail(NAME, "expected play_damage_hit_animation() in player controller")
		return
	_pass(NAME)


func test_handler_source_wires_damage_animation_after_infect() -> void:
	const NAME := "DDA-03 — InfectionInteractionHandler calls play_damage_hit_animation after infect"
	var path := "res://scripts/infection/infection_interaction_handler.gd"
	var f := FileAccess.open(path, FileAccess.READ)
	if f == null:
		_fail(NAME, "could not read " + path)
		return
	var src := f.get_as_text()
	var idx := src.find("apply_infection_event()")
	if idx < 0:
		_fail(NAME, "apply_infection_event not found")
		return
	var window := src.substr(idx, mini(200, src.length() - idx))
	if not window.contains("play_damage_hit_animation()"):
		_fail(NAME, "expected play_damage_hit_animation near apply_infection_event")
		return
	_pass(NAME)
