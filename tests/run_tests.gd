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
#   1. Create tests/<group>/test_<name>.gd as "class_name <Name>Tests extends Object"
#      with a "func run_all() -> int:" entry point.
#   2. Add the path to the SUITES array below in the appropriate group.

extends SceneTree

# Preload so LoggingTests is registered before run_tests.gd is loaded.
const _LOGGING_TESTS: GDScript = preload("res://tests/system/test_logging.gd")

const SUITES: Array[String] = [
	# --- movement ---
	"res://tests/movement/test_movement_simulation.gd",
	"res://tests/movement/test_movement_simulation_adversarial.gd",
	"res://tests/movement/test_jump_simulation.gd",
	"res://tests/movement/test_jump_simulation_adversarial.gd",
	"res://tests/movement/test_wall_cling_simulation.gd",
	"res://tests/movement/test_wall_cling_simulation_adversarial.gd",

	# --- camera ---
	"res://tests/camera/test_camera_follow.gd",
	"res://tests/camera/test_camera_follow_adversarial.gd",

	# --- chunk ---
	"res://tests/chunk/test_chunk_detach_simulation.gd",
	"res://tests/chunk/test_chunk_detach_simulation_adversarial.gd",
	"res://tests/chunk/test_chunk_recall_simulation.gd",
	"res://tests/chunk/test_chunk_recall_simulation_adversarial.gd",
	"res://tests/chunk/test_chunk_enemy_collision.gd",

	# --- player ---
	"res://tests/player/test_base_physics_entity_3d.gd",
	"res://tests/player/test_hp_reduction_simulation.gd",
	"res://tests/player/test_hp_reduction_simulation_adversarial.gd",
	"res://tests/player/test_human_playable_core.gd",
	"res://tests/player/test_human_playable_core_adversarial.gd",

	# --- enemy ---
	"res://tests/enemy/test_enemy_state_machine.gd",
	"res://tests/enemy/test_enemy_state_machine_adversarial.gd",
	"res://tests/enemy/test_weakening_system.gd",
	"res://tests/enemy/test_weakening_system_adversarial.gd",

	# --- infection ---
	"res://tests/infection/test_infection_ui.gd",
	"res://tests/infection/test_infection_interaction.gd",
	"res://tests/infection/test_infection_interaction_adversarial.gd",
	"res://tests/infection/test_infection_state_fx.gd",
	"res://tests/infection/test_infection_state_fx_adversarial.gd",
	"res://tests/infection/test_infection_state_fx_mutation_edge_cases.gd",
	"res://tests/infection/test_infection_state_fx_3d.gd",

	# --- ui ---
	"res://tests/ui/test_hp_and_chunk_hud.gd",
	"res://tests/ui/test_hp_and_chunk_hud_adversarial.gd",
	"res://tests/ui/test_input_hints.gd",
	"res://tests/ui/test_input_hints_adversarial.gd",
	"res://tests/ui/test_wall_cling_visual_readability.gd",
	"res://tests/ui/test_wall_cling_visual_readability_adversarial.gd",
	# test_wall_cling_visual_readability_mutation_specs.gd excluded: Color.distance_to() is not valid in Godot 4.6

	# --- scene ---
	"res://tests/scene/test_3d_scene.gd",
	"res://tests/scene/test_scene_state_machine.gd",
	"res://tests/scene/test_scene_state_machine_adversarial.gd",
	"res://tests/scene/test_scene_state_integration_3d.gd",

	# --- system ---
	"res://tests/system/test_detach_recall_fx.gd",
	"res://tests/system/test_detach_recall_fx_adversarial.gd",
	"res://tests/system/test_mutation_slot_system_single.gd",
	"res://tests/system/test_mutation_slot_system_single_adversarial.gd",
	"res://tests/system/test_logging.gd",
]


func _initialize() -> void:
	print("=== blobert headless test runner ===")
	print("")

	var total_failures: int = 0

	for path in SUITES:
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
